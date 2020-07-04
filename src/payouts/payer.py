import argparse
import logging
import logging.config
import datetime
import toml
import json
import requests
import threading

from sqlalchemy import desc

from web3 import Web3, HTTPProvider
from eth_account import Account
from web3.middleware import construct_sign_and_send_raw_middleware, geth_poa_middleware


from lib.address import Address
from lib.wad import Wad
from model.init_db import init_db
from contract.disperse import Disperse
from contract.erc20 import ERC20Token
from model import model

class Payer:
    logger = logging.getLogger()

    def __init__(self, args: list, **kwargs):
        parser = argparse.ArgumentParser(prog='liquidity-mining-payer')
        parser.add_argument("--config", help="config path", default="./config.toml", type=str)
        self.arguments = parser.parse_args(args)

        self.config = toml.load(self.arguments.config)
        logging.config.dictConfig(self.config['logging'])
        self.payer_account = Address(self.config['account']['address'])
        self.web3 = kwargs['web3'] if 'web3' in kwargs else Web3(HTTPProvider(endpoint_uri=f"http://{self.config['rpc']['host']}:{self.config['rpc']['port']}",
                                                                              request_kwargs={"timeout": self.config['rpc']['timeout']}))
        self.web3.middleware_onion.inject(geth_poa_middleware, layer=0)
        self.gas_price = self.web3.toWei(10, "gwei")
        self.gas_level = ''
        self.eth_gas_url = ''
        self.set_gas_info()
        self.nonce = 0
        # init db
        init_db(self.config['db'])
        # init payer transaction nonce
        self.init_payer_nonce()

        # contract 
        self.disperse = Disperse(web3=self.web3, address=Address(self.config['contracts']['disperse']))
        self.MCBToken = ERC20Token(web3=self.web3, address=Address(self.config['contracts']['MCB_token']))


    def set_gas_info(self):
        if self.web3 is None or self.config.get('gas', None) is None:
            return
        try:
            self.gas_level = self.config['gas'].get('gas_level')
            self.eth_gas_url = self.config['gas'].get('eth_gas_url')
        except Exception as e:
            self.logger.fatal(f"parse gas config error {e}")

    def get_gas_price(self):
        try:
            resp = requests.get(self.eth_gas_url, timeout=5)
            if resp.status_code / 100 == 2:
                rsp = json.loads(resp.content)
                self.gas_price = self.web3.toWei(rsp.get(self.gas_level) / 10, "gwei")
                self.logger.info(f"new gas price: {self.gas_price}")
        except Exception as e:
            self.logger.fatal(f"get gas price error {e}")

    def init_payer_nonce(self):
        latest_transaction = model.Session.query(model.PaymentTransaction).order_by(desc(model.PaymentTransaction.transaction_nonce)).first()
        if latest_transaction is None:
            count = self.web3.eth.eth_getTransactionCount(self.payer_account.address)
            self.nonce = count+1
        else:
            self.nonce = latest_transaction.transaction_nonce+1

    def _check_account_from_key(self, private_key):
        try:
            account = Account()
            acct = account.from_key(private_key)
            self.web3.middleware_onion.add(construct_sign_and_send_raw_middleware(acct))
        except:
            return False
        return True

    def _check_payer_account(self):
        private_key = self.config["account"].get("private_key", "")
        if private_key == "":
            return False

        # check account with key
        if self._check_account_from_key(private_key) is False:
            self.logger.exception(f"Account {self.config['account'].get('address')} register key error")
            return False
            
        return True

    def check_pending_transactions(self) -> bool:
        stats = [model.PaymentTransaction.INIT, model.PaymentTransaction.PENDING]

        pending_transactions = model.Session.query(model.PaymentTransaction)\
            .filter(model.PaymentTransaction.status.in_(stats)).all()
        for transaction in pending_transactions:
            try:
                self.web3.eth.waitForTransactionReceipt(transaction.transaction_hash, timeout=self.config['rpc']['wait_timeout'])
            except Exception as e:
                self.logger.fatal(f"get trasaction fail! tx_hash:{transaction.transaction_hash}, err:{e}")
                return False

        return True

    def save_payment_transaction(self, tx_hash, miners, amounts):
        pt = model.PaymentTransaction()
        pt.transaction_nonce = self.nonce
        data = {
            "miners": miners,
            "amounts": amounts,
        }
        pt.transaction_data = json.dumps(data)
        pt.transaction_hash = tx_hash
        pt.transaction_status(0)
        model.Session.add(pt)
        model.Session.commit()

    def save_payments_info(self, tx_receipt, miners, amounts):
        # update transaction status
        pt = model.Session.query(model.PaymentTransaction)\
            .filter_by(transaction_hash = tx_receipt["transactionHash"]).first()
        pt.transaction_status(tx_receipt["status"])
        model.Session.add(pt)

        # save payments
        if pt.status == model.PaymentTransaction.SUCCESS:
            for i in range(len(miners)):
                p = model.Payment()
                p.holder = miners[i]
                p.amount = amounts[i]
                p.pay_time = datetime.datetime.utcnow()
                p.transaction_id = pt.id
                model.Session.add(p)
                model.Session.execute("refresh materialized view payment_summaries")

                rp = model.RoundPayment()
                rp.mining_round = self.config["mining"]["round"]
                rp.holder = miners[i]
                rp.amount = amounts[i]
                rp.payment_id = p.id
                model.Session.execute("refresh materialized view round_payment_summaries")
        else:
            self.logger.fatal(f"transaction not success! tx_receipt:{tx_receipt}")

        model.Session.commit()

    def run(self):
        # check pending transactions
        if self.check_pending_transactions() is False:
            return
        
        # get all miners mature_mining_rewards
        miner_rewards = model.Session.query(model.PaymentSummary).all()
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
                self.payer_account, self.nonce, self.gas_price)
            self.save_payment_transaction(tx_hash, miners, amounts)
        except Exception as e:
            self.logger.fatal(f"disperse transaction fail! Exception:{e}")
            return

        try:
            tx_receipt = self.web3.eth.waitForTransactionReceipt(tx_hash, timeout=self.config['rpc']['wait_timeout'])
            self.save_payments_info(tx_receipt, miners, amounts)
        except Exception as e:
            self.logger.fatal(f"get trasaction receipt fail! tx_hash:{tx_hash}, err:{e}")
            return
        
        return