
import logging
import logging.config
from web3 import Web3
from decimal import Decimal
from sqlalchemy import desc

import config
from contract.perpetual import Perpetual, PositionSide
from lib.address import Address
from model import PositionEvent, PositionBalance

from .types import SyncerInterface
from hexbytes import HexBytes
from eth_utils import big_endian_to_int

class PositionTracer(SyncerInterface):
    """Sync account's position balance"""

    def __init__(self, perpetual_address, inverse, web3):
        
        self._perpetual_address = perpetual_address.lower()
        self._inverse = inverse
        # contract
        self._perpetual = Perpetual(
            web3=web3, address=Address(perpetual_address))
        self._logger = logging.getLogger()
    
    def _add_position_account_event(self, watcher_id, block_number, transaction_hash, event_index, holder, side, amount, db_session):
        position_event = PositionEvent()
        position_event.watcher_id = watcher_id
        position_event.block_number = block_number
        position_event.transaction_hash = transaction_hash
        position_event.token = self._perpetual_address
        position_event.event_index = event_index
        position_event.holder = holder
        if (self._inverse and side == PositionSide.LONG) or \
            (self._inverse is False and side == PositionSide.SHORT):
            amount = -amount
        position_event.amount = amount
        db_session.add(position_event)

        # update position_balances table
        position_balance_item = db_session.query(PositionBalance)\
            .filter(PositionBalance.holder == holder)\
            .filter(PositionBalance.perpetual_address == self._perpetual_address)\
                .first()
        if position_balance_item is None:
            position_balance_item = PositionBalance()
            position_balance_item.watcher_id = watcher_id
            position_balance_item.perpetual_address = self._perpetual_address
            position_balance_item.holder = holder
            position_balance_item.balance = amount
        else:
            position_balance_item.balance = amount
        db_session.add(position_balance_item)
        
    def sync(self, watcher_id, block_number, block_hash, db_session):
        """Sync data"""

        transfer_filter = self._perpetual.contract.events.UpdatePositionAccount().createFilter(
            fromBlock=Web3.toHex(block_number), toBlock=Web3.toHex(block_number))
        all_filter_events = transfer_filter.get_all_entries()
        self._logger.info(f'sync erc20 event, block_number:{block_number}, events:{len(all_filter_events)}')
        for row in all_filter_events:
            account_info = row.args
            holder = account_info.get('trader')
            margin_account = account_info.get('account')
            position_side = PositionSide(margin_account.get('side'))
            position_size = margin_account.get('size')
            cur_block_number = row.blockNumber
            cur_transaction_hash = row.transactionHash
            event_index = row.logIndex
            self._add_position_account_event(watcher_id, cur_block_number, cur_transaction_hash, event_index,
                                             holder, position_side, position_size, db_session)


    def rollback(self, watcher_id, block_number, db_session):
        """delete data after block_number"""
        self._logger.info(f'rollback erc20 block_number back to {block_number}')
        items = db_session.query(PositionBalance)\
            .filter(PositionBalance.block_number > block_number)\
            .filter(PositionBalance.perpetual_address == self._perpetual_address)\
            .filter(PositionBalance.watcher_id == watcher_id)\
            .all()
        for item in items:
            # update position_balances table
            position_event = db_session.query(PositionEvent)\
                .filter(PositionEvent.holder == item.holder)\
                .filter(PositionEvent.perpetual_address == item.perpetual_address)\
                .filter(PositionEvent.block_number <= block_number)\
                .order_by(desc(PositionEvent.block_number))\
                .first()
            if position_event is None:
                item.delete()
            else:
                item.balance = position_event.amount
                db_session.add(item)
        
        db_session.query(PositionEvent).filter(PositionEvent.perpetual_address == self._perpetual_address).filter(PositionBalance.watcher_id == watcher_id).\
            filter(PositionEvent.block_number > block_number).delete()

    def test_pos(self):
        event_filter_params = {
            'topics': ['0xe763e57e3bd855c6028a13805d580b19a2403f388a7e9be7233d487a61a5abe5'],
            'address': ['0x220a9f0DD581cbc58fcFb907De0454cBF3777f76'],
            'fromBlock': 10455630,
            'toBlock': 10455638,
        }
        logs = self._perpetual.web3.eth.getLogs(event_filter_params)
        for log in logs:
            parsed = {}
            parsed['blockNumber'] = log['blockNumber']
            parsed['blockHash'] = log['blockHash']
            parsed['transactionIndex'] = log['transactionIndex']
            parsed['transactionHash'] = log['transactionHash']
            parsed['trader'] = log['topics'][1]
            data = HexBytes(log['data'])
            if len(data) != 32 * 8:
                raise Exception(f'malformed event: {parsed}')
            parsed['side'] = big_endian_to_int(data[32*0:32*1])
            parsed['size'] = big_endian_to_int(data[32*1:32*2])
            parsed['entryValue'] = big_endian_to_int(data[32*2:32*3])
            parsed['entrySocialLoss'] = big_endian_to_int(data[32*3:32*4])
            parsed['entryFundingLoss'] = big_endian_to_int(data[32*4:32*5])
            parsed['cashBalance'] = big_endian_to_int(data[32*5:32*6])
            parsed['perpetualTotalSize'] = big_endian_to_int(data[32*6:32*7])
            parsed['price'] = big_endian_to_int(data[32*7:32*8])
            print(parsed)
