import datetime
import json
import logging
import logging.config
import requests
import math
from decimal import Decimal
from sqlalchemy import desc

from web3 import Web3, HTTPProvider
from eth_account import Account
from web3.middleware import construct_sign_and_send_raw_middleware, geth_poa_middleware

import config
from lib.address import Address
from lib.contract import Contract
from lib.wad import Wad
from contract.disperse import Disperse
from contract.erc20 import ERC20Token
from model import DBSession, PaymentTransaction, Payment, RoundPayment, PaymentSummary, RoundPaymentSummary, MatureMiningReward

class Payer:
    def __init__(self):
        self._logger = logging.getLogger()
        config.LOG_CONFIG["handlers"]["file_handler"]["filename"] = config.PAYER_LOGPATH
        logging.config.dictConfig(config.LOG_CONFIG)

        self._web3 = Web3(HTTPProvider(endpoint_uri=config.ETH_RPC_URL,
                        request_kwargs={"timeout": config.ETH_RPC_TIMEOUT}))
        self._web3.middleware_onion.inject(geth_poa_middleware, layer=0)
        self._gas_price = self._web3.toWei(50, "gwei")
        self._get_gas_price()
        self._payer_account = None

        # contract
        self._disperse = Disperse(
            web3=self._web3, address=Address(config.DISPERSE_ADDRESS))
        self._MCBToken = ERC20Token(
            web3=self._web3, address=Address(config.MCB_TOKEN_ADDRESS))

    def _get_gas_price(self):
        try:
            resp = requests.get(config.ETH_GAS_URL, timeout=60)
            if resp.status_code / 100 == 2:
                rsp = json.loads(resp.content)
                self._gas_price = self._web3.toWei(
                    rsp.get(config.GAS_LEVEL) / 10, "gwei")
                self._logger.info(f"new gas price: {self._gas_price}")
        except Exception as e:
            self._logger.fatal(f"get gas price error {e}")

    def _check_account_from_key(self):
        try:
            account = Account()
            acct = account.from_key(config.PAYER_KEY)
            self._web3.middleware_onion.add(
                construct_sign_and_send_raw_middleware(acct))
            self._payer_account = Address(acct.address)
        except:
            self._logger.fatal(f"Account {config.PAYER_ADDRESS} register key error")
            return False
        return True

    def _restore_pending_data(self):
        db_session = DBSession()
        transaction = db_session.query(PaymentTransaction)\
            .filter_by(status = PaymentTransaction.PENDING).first()
        data = json.loads(transaction.transaction_data)
        amounts = []
        for i in range(len(data["amounts"])):
            amounts.append(Decimal(data["amounts"][i]))
            self._logger.info(f'miner {data["miners"][i].lower()} unpaid rewards {data["amounts"][i]}')
        data["amounts"] = amounts

        return data

    def _check_pending_transactions(self) -> bool:
        db_session = DBSession()
        pending_transactions = db_session.query(PaymentTransaction)\
            .filter_by(status = PaymentTransaction.PENDING).all()
        for transaction in pending_transactions:
            try:
                tx_receipt = self._web3.eth.waitForTransactionReceipt(transaction.transaction_hash, timeout=config.WAIT_TIMEOUT)
                data = json.loads(transaction.transaction_data)
                amounts = []
                for amount in data["amounts"]:
                    amounts.append(Decimal(amount))
                self._save_payments_info(tx_receipt, data["miners"], amounts)
            except Exception as e:
                self._logger.fatal(
                    f"get trasaction fail! tx_hash:{transaction.transaction_hash}, err:{e}")
                return False

        return True

    def _save_payment_transaction(self, tx_hash, miners, amounts):
        amounts_str = []
        for amount in amounts:
            amounts_str.append(str(amount))
        db_session = DBSession()
        try:
            pt = PaymentTransaction()
            data = {
                "miners": miners,
                "amounts": amounts_str,
            }
            pt.transaction_data = json.dumps(data)
            pt.transaction_hash = tx_hash
            # 0: failed, 1: success, 2: pending
            pt.transaction_status(2)
            db_session.add(pt)
            db_session.commit()
        except Exception as e:
            self._logger.warning(f'save payment transaction fail! err:{e}')
        finally:
            db_session.rollback()

    def _save_payments_info(self, tx_receipt, miners, amounts):
        db_session = DBSession()
        try:
            # update transaction status
            pt = db_session.query(PaymentTransaction)\
                .filter_by(transaction_hash=self._web3.toHex(tx_receipt["transactionHash"])).first()
            pt.transaction_status(tx_receipt["status"])
            db_session.add(pt)

            # save payments
            if pt.status == PaymentTransaction.SUCCESS:
                miner_payments = db_session.query(PaymentSummary).all()
                miner_round_payments = db_session.query(RoundPaymentSummary).all()

                payments_map = {}
                for payment in miner_payments:
                    payments_map[payment.holder] = payment
                round_payments_map = {}
                for round_payment in miner_round_payments:
                    round_payments_map[round_payment.holder] = round_payment
                for i in range(len(miners)):
                    # save payments
                    p = Payment()
                    p.holder = miners[i].lower()
                    p.amount = amounts[i]
                    p.pay_time = datetime.datetime.utcnow()
                    p.transaction_id = pt.id
                    db_session.add(p)

                    # save round payments
                    rp = RoundPayment()
                    rp.mining_round = config.MINING_ROUND
                    rp.holder = miners[i].lower()
                    rp.amount = amounts[i]
                    rp.transaction_id = pt.id
                    db_session.add(rp)

                    # update payment summaries
                    payment_summary = payments_map.get(p.holder)
                    if payment_summary is not None:
                        payment_summary.paid_amount += p.amount
                    else:
                        payment_summary = PaymentSummary()
                        payment_summary.holder = p.holder
                        payment_summary.paid_amount = p.amount
                    db_session.add(payment_summary)
                    # update round payment summaries
                    round_payment_summary = round_payments_map.get(p.holder)
                    if round_payment_summary is not None:
                        round_payment_summary.paid_amount += p.amount
                    else:
                        round_payment_summary = RoundPaymentSummary()
                        round_payment_summary.mining_round = rp.mining_round
                        round_payment_summary.holder = rp.holder
                        round_payment_summary.paid_amount = rp.amount
                    db_session.add(round_payment_summary)
            else:
                self._logger.warning(
                    f"transaction not success! tx_receipt:{tx_receipt}")

            db_session.commit()
        except Exception as e:
            self._logger.warning(f'save payment info fail! err:{e}')
            # raise exception for _check_pending_transactions
            raise
        finally:
            db_session.rollback()

    def _get_miner_unpaid_reward(self):
        db_session = DBSession()
        items = db_session.query(MatureMiningReward)\
                        .outerjoin(RoundPaymentSummary, MatureMiningReward.holder == RoundPaymentSummary.holder)\
                        .filter(MatureMiningReward.mining_round == config.MINING_ROUND)\
                        .with_entities(MatureMiningReward.holder, MatureMiningReward.mcb_balance, RoundPaymentSummary.paid_amount)\
                        .all()

        result = {
            "miners": [],
            "amounts": [],
        }
        for item in items:
            unpaid = item.mcb_balance
            if item.paid_amount is not None:
                unpaid = item.mcb_balance - item.paid_amount
            if unpaid >= Decimal(config.MIN_PAY_AMOUNT):
                result["miners"].append(self._web3.toChecksumAddress(item.holder))
                result["amounts"].append(unpaid)
                self._logger.info(f'miner {item.holder} unpaid rewards {unpaid}')
        return result

    def run(self):
        if self._check_account_from_key() is False:
            return
        
        # approve MCB token to disperse for multiple transaction
        if self._MCBToken.allowance(self._payer_account, self._disperse.address) == Wad(0):
            self._MCBToken.approve(self._disperse.address, self._payer_account)

        # restore pending transaction if need
        # unpaid_rewards = self._restore_pending_data()

        # check pending transactions
        if self._check_pending_transactions() is False:
            return
        
        # get all miners unpaid rewards
        unpaid_rewards = self._get_miner_unpaid_reward()
        miners_count = len(unpaid_rewards["miners"])
        if miners_count == 0:
            self._logger.info(f"no miner need to be payed")
            return

        total_amount = Decimal(0)
        for reward in unpaid_rewards['amounts']:
            total_amount += reward

        self._logger.info(f"total_amount: {total_amount*(Decimal(10)**18)}")
        admin_input = input("yes or no: ")
        if admin_input != "yes":
            self._logger.info(f"input is {admin_input}. payer stop!")
            return

        # get gas price for transaction
        self._get_gas_price()
        # send MCB to all accounts
        for i in range(math.ceil(miners_count/config.MAX_PATCH_NUM)):
            start_idx = i*config.MAX_PATCH_NUM
            end_idx = min((i+1)*config.MAX_PATCH_NUM, miners_count)
            self._logger.info(f"miners count: {miners_count}, send from {start_idx} to {end_idx}")

            miners = unpaid_rewards["miners"][start_idx:end_idx]
            amounts = unpaid_rewards["amounts"][start_idx:end_idx]
            try:
                tx_hash = self._disperse.disperse_token(self._MCBToken.address, miners, amounts,
                    self._payer_account, self._gas_price)
                self._save_payment_transaction(self._web3.toHex(tx_hash), miners, amounts)
            except Exception as e:
                self._logger.fatal(f"disperse transaction fail! Exception:{e}")
                continue

            try:
                tx_receipt = self._web3.eth.waitForTransactionReceipt(tx_hash, timeout=config.WAIT_TIMEOUT)
                self._save_payments_info(tx_receipt, miners, amounts)
            except Exception as e:
                self._logger.fatal(
                    f"get trasaction receipt fail! tx_hash:{tx_hash}, err:{e}")
                continue

        return