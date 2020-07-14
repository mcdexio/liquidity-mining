from web3 import Web3

from lib.address import Address
from lib.contract import Contract
from lib.wad import Wad
from enum import Enum

class PositionSide(Enum):
     FLAT = 0
     SHORT = 1
     LONG = 2

class Status(Enum):
     NORMAL = 0
     SETTLING = 1
     SETTLED = 2

class MarginAccount():
    def __init__(self, side: int, size: int, entry_value: int, entry_social_loss: int, entry_funding_loss: int, cash_balance: int):
        assert(isinstance(side, int))
        assert(isinstance(size, int))
        assert(isinstance(entry_value, int))
        assert(isinstance(entry_social_loss, int))
        assert(isinstance(entry_funding_loss, int))

        self.side = PositionSide(side)
        self.size = Wad(size)
        self.entry_value = Wad(entry_value)
        self.entry_social_loss = Wad(entry_social_loss)
        self.entry_funding_loss = Wad(entry_funding_loss)
        self.cash_balance = Wad(cash_balance)

class Liquidate:
    def __init__(self, price: int, amount: int):
        assert(isinstance(price, int))
        assert(isinstance(amount, int))

        self.price = Wad(price)
        self.amount = Wad(amount)

class Perpetual(Contract):
    abi = Contract._load_abi(__name__, '../abi/Perpetual.abi')

    def __init__(self, web3: Web3, address: Address):
        assert(isinstance(web3, Web3))
        assert(isinstance(address, Address))

        self.web3 = web3
        self.address = address
        self.contract = self._get_contract(web3, self.abi, address)

    def total_accounts(self) -> int:
        return self.contract.functions.totalAccounts().call()

    def status(self) -> Status:
        return Status(self.contract.functions.status().call())

    def accounts(self, account_id: int) -> Address:
        return Address(self.contract.functions.accountList(account_id).call())

    def getMarginAccount(self, address: Address) -> MarginAccount:
        margin_account = self.contract.functions.getMarginAccount(address.address).call()
        return MarginAccount(margin_account[0], margin_account[1], margin_account[2], margin_account[3], margin_account[4], margin_account[5])


