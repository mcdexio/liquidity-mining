
import logging
import logging.config
from web3 import Web3
from decimal import Decimal
from sqlalchemy import func

import config
from contract.erc20 import ERC20Token
from lib.address import Address
from model.orm import TokenEvent, TokenBalance

from .types import SyncerInterface


class ERC20Tracer(SyncerInterface):
    """Sync the balance of ERC20 tokens by parsing the ERC20 events"""

    def __init__(self, token_address, web3):
        
        self._token_address = token_address.lower()
        # contract
        self._erc20_token = ERC20Token(
            web3=web3, address=Address(token_address))
        self._erc20_decimals = self._erc20_token.decimals
        self._logger = logging.getLogger()
        config.LOG_CONFIG["handlers"]["file_handler"]["filename"] = config.SYNCER_LOGPATH
        logging.config.dictConfig(config.LOG_CONFIG)
    

    def _add_token_event(self, watcher_id, block_number, transaction_hash, token_address, event_index, transfer_type, holder, amount, db_session):
        token_event = TokenEvent()
        token_event.watcher_id = watcher_id
        token_event.block_number = block_number
        token_event.transaction_hash = transaction_hash
        token_event.token = token_address
        token_event.event_index = event_index
        token_event.holder = holder
        if transfer_type == 'from':
            amount = -amount
        token_event.amount = amount
        db_session.add(token_event)

        # update token_balances table, simulated materialized view
        token_balance_item = db_session.query(TokenBalance)\
            .filter(TokenBalance.holder == holder)\
            .filter(TokenBalance.token == token_address)\
                .first()
        if token_balance_item is None:
            token_balance_item = TokenBalance()
            token_balance_item.watcher_id = watcher_id
            token_balance_item.token = token_address
            token_balance_item.holder = holder
            token_balance_item.balance = amount
        else:
            token_balance_item.balance += amount
        db_session.add(token_balance_item)
        
    def sync(self, watcher_id, block_number, block_hash, db_session):
        """Sync data"""

        transfer_filter = self._erc20_token.contract.events.Transfer().createFilter(
            fromBlock=Web3.toHex(block_number), toBlock=Web3.toHex(block_number))
        all_filter_events = transfer_filter.get_all_entries()
        self._logger(f'sync erc20 event, block_number:{block_number}, events:{len(all_filter_events)}')
        for row in all_filter_events:
            transfer_info = row.args
            from_addr = transfer_info.get('from')
            to_addr = transfer_info.get('to')
            amount = Decimal(transfer_info.get('value'))/Decimal(10**self._erc20_decimals)
            cur_block_number = row.blockNumber
            cur_transaction_hash = row.transactionHash
            event_index = row.logIndex

            if from_addr == '0x0000000000000000000000000000000000000000':
                transfer_type = 'to'
                holder = to_addr
                self._add_token_event(watcher_id, cur_block_number, cur_transaction_hash,
                                      self._token_address, event_index, transfer_type, holder, amount, db_session)
            elif to_addr == '0x0000000000000000000000000000000000000000':
                transfer_type = 'from'
                holder = from_addr
                self._add_token_event(watcher_id, cur_block_number, cur_transaction_hash,
                                      self._token_address, event_index, transfer_type, holder, amount, db_session)
            else:
                transfer_type = 'from'
                holder = from_addr
                self._add_token_event(watcher_id, cur_block_number, cur_transaction_hash,
                                      self._token_address, event_index, transfer_type, holder, amount, db_session)

                transfer_type = 'to'
                holder = to_addr
                self._add_token_event(watcher_id, cur_block_number, cur_transaction_hash,
                                      self._token_address, event_index, transfer_type, holder, amount, db_session)

    def rollback(self, watcher_id, block_number, db_session):
        """delete data after block_number"""
        self._logger(f'rollback erc20 block_number back to {block_number}')
        items = db_session.query(TokenEvent)\
            .filter(TokenEvent.block_number >= block_number)\
            .group_by(TokenEvent.token, TokenEvent.holder)\
            .with_entities(
                TokenEvent.token,
                TokenEvent.holder,
                func.sum(TokenEvent.amount).label('amount')
        ).all()
        for item in items:
            # update token_balances table
            token_balance_item = db_session.query(TokenBalance)\
                .filter(TokenBalance.holder == item.holder)\
                .filter(TokenBalance.token == item.token)\
                    .first()
            if token_balance_item is None:
                self._logger.error(f'opps, update token_balance error, can not find item:{item}')
            else:
                token_balance_item.balance -= item.amount
                db_session.add(token_balance_item)
        
        db_session.query(TokenEvent).filter(TokenEvent.token == self._token_address).filter(TokenEvent.watcher_id == watcher_id).\
            filter(TokenEvent.block_number >= block_number).delete()
 
        
