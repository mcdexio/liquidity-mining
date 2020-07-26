import logging
import json
import pkg_resources

import eth_utils
from web3 import Web3
from .address import Address


class Contract:
    logger = logging.getLogger()

    @staticmethod
    def _get_contract(web3: Web3, abi: list, address: Address):
        assert(isinstance(web3, Web3))
        assert(isinstance(abi, list))
        assert(isinstance(address, Address))

        code = web3.eth.getCode(address.address)
        if (code == "0x") or (code == "0x0") or (code == b"\x00") or (code is None):
            raise Exception(f"No contract found at {address}")

        return web3.eth.contract(address=address.address, abi=abi)

    @staticmethod
    def _load_abi(package, resource) -> list:
        return json.loads(pkg_resources.resource_string(package, resource))
