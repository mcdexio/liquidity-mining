from web3 import Web3

from lib.contract import Contract
from lib.address import Address
from lib.wad import Wad


class Disperse(Contract):
    abi = Contract._load_abi(__name__, '../abi/disperse.abi')
    registry = {}

    def __init__(self, web3: Web3, address: Address):
        assert(isinstance(web3, Web3))
        assert(isinstance(address, Address))

        self.web3 = web3
        self.address = address
        self.contract = self._get_contract(web3, self.abi, address)

    def disperse_ether(self, addresses: list, amounts: list, user: Address, nonce:int, gasPrice: int):
        total_amount = 0
        amounts_toWei = []
        for amount in amounts:
            amount_toWei = self.web3.toWei(amount, 'ether')
            amounts_toWei.append(amount_toWei)
            total_amount += amount_toWei
        tx_hash = self.contract.functions.disperseEther(addresses, amounts).transact({
            'from': user.address,
            'value': self.web3.toHex(total_amount),
            'gasPrice': gasPrice,
            'nonce': nonce
        })
        return tx_hash

    def disperse_token(self, token: Address, addresses: list, amounts: list, user: Address, nonce: int, gasPrice: int):
        amounts_toWad = []
        for amount in amounts:
            amounts_toWad.append(Wad.from_number(amount).value)
        tx_hash = self.contract.functions.disperseToken(token.address, addresses, amounts_toWad).transact({
            'from': user.address,
            'gasPrice': gasPrice,
            'nonce': nonce
        })
        return tx_hash
    