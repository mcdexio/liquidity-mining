from web3 import Web3

from lib.contract import Contract
from lib.address import Address
from lib.wad import Wad

CHAINLINK_DECIMALS = 10**10


class ChainLink(Contract):
    abi = Contract._load_abi(__name__, '../abi/chainlink.abi')
    registry = {}

    def __init__(self, web3: Web3, address: Address):
        assert(isinstance(web3, Web3))
        assert(isinstance(address, Address))

        self.web3 = web3
        self.address = address
        self.contract = self._get_contract(web3, self.abi, address)

    def latestAnswer(self):
        price = self.contract.functions.latestAnswer().call()*CHAINLINK_DECIMALS
        return price

    