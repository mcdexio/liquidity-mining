
import logging
from web3 import Web3
from decimal import Decimal

import config
from contract.chainlink import ChainLink, CHAINLINK_DECIMALS
from lib.address import Address
from model import ChainLinkPriceEvent

from .types import SyncerInterface


class ETHPriceTracer(SyncerInterface):
    """Sync the balance of ERC20 tokens by parsing the ERC20 events"""

    def __init__(self, chain_link_address, web3):
        
        self._chain_link_address = chain_link_address.lower()
        # contract
        self._chain_link = ChainLink(
            web3=web3, address=Address(chain_link_address))
        self._logger = logging.getLogger()
    
    def _add_price_event(self, watcher_id, block_number, transaction_hash, chain_link_address, event_index, price, db_session):
        price_event = ChainLinkPriceEvent()
        price_event.watcher_id = watcher_id
        price_event.block_number = block_number
        price_event.transaction_hash = transaction_hash
        price_event.chain_link_address = chain_link_address
        price_event.event_index = event_index
        price_event.price = price

        db_session.add(price_event)
        
    def sync(self, watcher_id, block_number, block_hash, db_session):
        """Sync data"""

        price_updated_filter = self._chain_link.contract.events.AnswerUpdated().createFilter(
            fromBlock=Web3.toHex(block_number), toBlock=Web3.toHex(block_number))
        all_filter_events = price_updated_filter.get_all_entries()
        self._logger.info(f'sync chain link eth price event, block_number:{block_number}, events:{len(all_filter_events)}')
        for row in all_filter_events:
            price_info = row.args
            current_price = Decimal(price_info.get('current'))*Decimal(CHAINLINK_DECIMALS)
            cur_block_number = row.blockNumber
            cur_transaction_hash = row.transactionHash
            event_index = row.logIndex

            self._add_price_event(watcher_id, cur_block_number, cur_transaction_hash,
                                      self._chain_link_address, event_index, current_price, db_session)

    def rollback(self, watcher_id, block_number, db_session):
        """delete data after block_number"""
        self._logger.info(f'rollback chainlink block_number back to {block_number}')
        
        db_session.query(ChainLinkPriceEvent).filter(ChainLinkPriceEvent.chain_link_address == self._chain_link_address).filter(ChainLinkPriceEvent.watcher_id == watcher_id).\
            filter(ChainLinkPriceEvent.block_number > block_number).delete(synchronize_session=False)
        
