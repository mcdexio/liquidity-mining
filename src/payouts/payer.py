import argparse
import logging
import logging.config
import time
import toml
import json
import requests
import threading

from web3 import Web3, HTTPProvider, middleware
from eth_account import Account
from web3.middleware import construct_sign_and_send_raw_middleware, geth_poa_middleware


from lib.address import Address
from lib.wad import Wad
from model.init_db import init_db
from contract.ERC20Token import ERC20Token

class Payer:
    logger = logging.getLogger()

    def __init__(self, args: list, **kwargs):
        parser = argparse.ArgumentParser(prog='liquidity-mining-payer')
        parser.add_argument("--config", help="config path", default="./config.toml", type=str)
        self.arguments = parser.parse_args(args)

        self.config = toml.load(self.arguments.config)
        logging.config.dictConfig(self.config['logging'])
        self.payer_accounts = []
        self.payer_account_keys = []
        self.web3 = kwargs['web3'] if 'web3' in kwargs else Web3(HTTPProvider(endpoint_uri=f"http://{self.config['rpc']['host']}:{self.config['rpc']['port']}",
                                                                              request_kwargs={"timeout": self.config['rpc']['timeout']}))
        self.web3.middleware_onion.inject(geth_poa_middleware, layer=0)
        self.gas_price = self.web3.toWei(10, "gwei")
        self.gas_level = ''
        self.eth_gas_url = ''
        self.set_gas_info()

        init_db(self.config['db'])

        # contract 
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

    def _check_account_from_key(self, private_key):
        try:
            account = Account()
            acct = account.from_key(private_key)
            self.web3.middleware_onion.add(construct_sign_and_send_raw_middleware(acct))
        except:
            return False
        return True

    def _check_payer_accounts(self):
        if len(self.config.get("accounts", [])) == 0 :
            self.logger.fatal(f"set account for keeper transact")
            return False
        for user_account in self.config["accounts"]:
            private_key = user_account.get("private_key", "")
            if private_key == "":
                return False

            # check account with key
            if self._check_account_from_key(private_key) is False:
                self.logger.exception(f"Account {user_account['address']} register key error")
                return False
            else:
                self.payer_accounts.append(Address(user_account["address"]))
                self.payer_account_keys.append(private_key)
            
        return True

    def run(self):
        # get all mature_mining_rewards

        # get gas price 

        # get transaction nonce

        # send MCB to all accounts

        # check transaction
        return