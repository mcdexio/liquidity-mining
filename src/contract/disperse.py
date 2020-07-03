from web3 import Web3

from lib.contract import Contract
from lib.address import Address
from lib.wad import Wad


class MCBToken(Contract):
    abi = Contract._load_abi(__name__, '../abi/disperse.abi')
    registry = {}

    def __init__(self, web3: Web3, address: Address):
        assert(isinstance(web3, Web3))
        assert(isinstance(address, Address))

        self.web3 = web3
        self.address = address
        self.contract = self._get_contract(web3, self.abi, address)

    def disperseEther(self, addresses: list, amounts: list, user: Address, gasPrice: int):
        total_amount = 0
        for amount in amounts:
            total_amount += amount
        total_amount_towei = self.web3.toWei(total_amount, 'ether')
        tx_hash = self.contract.functions.disperseEther(addresses, amounts).transact({
            'from': user.address,
            'value': self.web3.toHex(total_amount_towei),
            'gasPrice': gasPrice
        })
        tx_receipt = self.web3.eth.waitForTransactionReceipt(tx_hash)
        return tx_receipt

    def disperseToken(self, token: Address, addresses: list, amounts: list, user: Address, gasPrice: int):
        tx_hash = self.contract.functions.disperseToken(token.address, addresses, amounts).transact({
            'from': user.address,
            'gasPrice': gasPrice
        })
        tx_receipt = self.web3.eth.waitForTransactionReceipt(tx_hash)
        return tx_receipt
    