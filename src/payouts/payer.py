import argparse
import datetime
import json
import logging
import logging.config
import threading

import requests
import toml
from eth_account import Account
from sqlalchemy import desc
from sqlalchemy.orm import sessionmaker
from web3 import HTTPProvider, Web3
from web3.middleware import (construct_sign_and_send_raw_middleware,
                             geth_poa_middleware)

import config
from contract.disperse import Disperse
from contract.erc20 import ERC20Token
from lib.address import Address
from lib.wad import Wad
from model.db import DBSession
from model.orm import Payment, PaymentSummary, PaymentTransaction, RoundPayment


class Payer:
    logger = logging.getLogger("payer")

    def __init__(self, args: list, **kwargs):

        self.web3 = kwargs['web3'] if 'web3' in kwargs else Web3(HTTPProvider(endpoint_uri=config.RPC_URL,
                                                                              request_kwargs={"timeout": config.RPC_TIMEOUT}))
        self.web3.middleware_onion.inject(geth_poa_middleware, layer=0)
        self.gas_price = self.web3.toWei(10, "gwei")
        self.get_gas_price()
        self.nonce = 0
        # init payer transaction nonce
        self.init_payer_nonce()

        # contract
        self.disperse = Disperse(
            web3=self.web3, address=Address(config.DISPERSE_ADDRESS))
        self.MCBToken = ERC20Token(
            web3=self.web3, address=Address(config.MCB_TOKEN_ADDRESS))

    def get_gas_price(self):
        try:
            resp = requests.get(config.ETH_GAS_URL, timeout=5)
            if resp.status_code / 100 == 2:
                rsp = json.loads(resp.content)
                self.gas_price = self.web3.toWei(
                    rsp.get(config.GAS_LEVEL) / 10, "gwei")
                self.logger.info(f"new gas price: {self.gas_price}")
        except Exception as e:
            self.logger.fatal(f"get gas price error {e}")

    def init_payer_nonce(self):
        db_session = DBSession()
        latest_transaction = db_session.query(PaymentTransaction).order_by(
            desc(PaymentTransaction.transaction_nonce)).first()
        if latest_transaction is None:
            count = self.web3.eth.eth_getTransactionCount(config.PAYER_ADDRESS)
            self.nonce = count+1
        else:
            self.nonce = latest_transaction.transaction_nonce+1

    def _check_account_from_key(self):
        try:
            account = Account()
            acct = account.from_key(config.PAYER_KEY)
            self.web3.middleware_onion.add(
                construct_sign_and_send_raw_middleware(acct))
        except:
            self.logger.fatal(f"Account {config.PAYER_KEY} register key error")
            return False
        return True

    def check_pending_transactions(self) -> bool:
        stats = [PaymentTransaction.INIT, PaymentTransaction.PENDING]

        db_session = DBSession()
        pending_transactions = db_session.query(PaymentTransaction)\
            .filter(PaymentTransaction.status.in_(stats)).all()
        for transaction in pending_transactions:
            try:
                self.web3.eth.waitForTransactionReceipt(
                    transaction.transaction_hash, timeout=config.WAIT_TIMEOUT)
            except Exception as e:
                self.logger.fatal(
                    f"get trasaction fail! tx_hash:{transaction.transaction_hash}, err:{e}")
                return False

        return True

    def save_payment_transaction(self, tx_hash, miners, amounts):
        db_session = DBSession()
        try:
            pt = PaymentTransaction()
            pt.transaction_nonce = self.nonce
            data = {
                "miners": miners,
                "amounts": amounts,
            }
            pt.transaction_data = json.dumps(data)
            pt.transaction_hash = tx_hash
            pt.transaction_status(0)
            db_session.add(pt)
            db_session.commit()
        except Exception as e:
            self.logger.warning(f'save payment transaction fail! err:{e}')
        finally:
            db_session.rollback()

    def save_payments_info(self, tx_receipt, miners, amounts):
        db_session = DBSession()
        # update transaction status
        try:
            pt = db_session.query(PaymentTransaction)\
                .filter_by(transaction_hash=tx_receipt["transactionHash"]).first()
            pt.transaction_status(tx_receipt["status"])
            db_session.add(pt)

            # save payments
            if pt.status == PaymentTransaction.SUCCESS:
                for i in range(len(miners)):
                    p = Payment()
                    p.holder = miners[i]
                    p.amount = amounts[i]
                    p.pay_time = datetime.datetime.utcnow()
                    p.transaction_id = pt.id
                    db_session.add(p)
                    db_session.execute(
                        "refresh materialized view payment_summaries")

                    rp = RoundPayment()
                    rp.mining_round = config.MINING_ROUND
                    rp.holder = miners[i]
                    rp.amount = amounts[i]
                    rp.payment_id = p.id
                    db_session.execute(
                        "refresh materialized view round_payment_summaries")
            else:
                self.logger.warning(
                    f"transaction not success! tx_receipt:{tx_receipt}")

            db_session.commit()
        except Exception as e:
            self.logger.warning(f'save payment info fail! err:{e}')
        finally:
            db_session.rollback()

    def run(self):
        # check pending transactions
        if self.check_pending_transactions() is False:
            return

        # get all miners mature_mining_rewards
        db_session = DBSession()
        miner_rewards = db_session.query(PaymentSummary).all()
        if len(miner_rewards) == 0:
            self.logger.info(f"no miner need to be payed")
            return

        # get gas price for transaction
        self.get_gas_price()

        self.nonce = self.nonce+1
        # send MCB to all accounts
        miners = []
        amounts = []
        for miner_reward in miner_rewards:
            miners.append(miner_reward.holder)
            amounts.append(miner_reward.paid_amount)

        try:
            tx_hash = self.disperse.disperse_token(self.MCBToken.address.address, miners, amounts,
                                                   config.PAYER_ADDRESS, self.nonce, self.gas_price)
            self.save_payment_transaction(tx_hash, miners, amounts)
        except Exception as e:
            self.logger.fatal(f"disperse transaction fail! Exception:{e}")
            return

        try:
            tx_receipt = self.web3.eth.waitForTransactionReceipt(
                tx_hash, timeout=config.WAIT_TIMEOUT)
            self.save_payments_info(tx_receipt, miners, amounts)
        except Exception as e:
            self.logger.fatal(
                f"get trasaction receipt fail! tx_hash:{tx_hash}, err:{e}")
            return

        return
