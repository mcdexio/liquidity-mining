from web3 import Web3

from lib.contract import Contract
from lib.address import Address
from lib.wad import Wad


class ERC20Token(Contract):
    abi = Contract._load_abi(__name__, '../abi/ERC20Token.abi')
    registry = {}

    def __init__(self, web3: Web3, address: Address):
        assert(isinstance(web3, Web3))
        assert(isinstance(address, Address))

        self.web3 = web3
        self.address = address
        self.contract = self._get_contract(web3, self.abi, address)

    def total_supply(self) -> Wad:
        return Wad(self.contract.functions.totalSupply().call())

    def balance_of(self, address: Address) -> Wad:
        assert(isinstance(address, Address))

        return Wad(self.contract.functions.balanceOf(address.address).call())

    def allowance(self, address: Address, guy: Address) -> Wad:
        assert(isinstance(address, Address))
        assert(isinstance(guy, Address))

        return Wad(self.contract.functions.allowance(address.address, guy.address).call())

    def transfer(self, address: Address, value: Wad, user: Address):
        assert(isinstance(address, Address))
        assert(isinstance(value, Wad))

        tx_hash = self.contract.functions.transfer(address.address, value.value).transact({'from': user.address})
        tx_receipt = self.web3.eth.waitForTransactionReceipt(tx_hash)
        #self.logger.info(tx_receipt)
        return tx_receipt

    def transfer_from(self, from_address: Address, to_address: Address, value: Wad):
        assert(isinstance(from_address, Address))
        assert(isinstance(to_address, Address))
        assert(isinstance(value, Wad))

        tx_hash = self.contract.functions.transferFrom(from_address.address, to_address.address, value.value).transact()
        tx_receipt = self.web3.eth.waitForTransactionReceipt(tx_hash)
        #self.logger.info(tx_receipt)
        return tx_receipt

    def approve(self, address: Address, user: Address, limit: Wad = Wad(2**256 - 1)):
        assert(isinstance(address, Address))
        assert(isinstance(limit, Wad))
        tx_hash = self.contract.functions.approve(address.address, limit.value).transact({'from': user.address})
        tx_receipt = self.web3.eth.waitForTransactionReceipt(tx_hash)
        #self.logger.info(tx_receipt)
        return tx_receipt