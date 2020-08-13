
import logging
import logging.config
from web3 import Web3
from decimal import Decimal
from sqlalchemy import desc

from contract.perpetual import Perpetual, PositionSide
from lib.address import Address
from lib.wad import Wad, DECIMALS
from model import PositionEvent, PositionBalance

from .types import SyncerInterface
from hexbytes import HexBytes
from eth_utils import big_endian_to_int

class PositionTracer(SyncerInterface):
    """Sync account's position balance"""

    def __init__(self, perpetual_address, inverse, perpetual_position_topic, web3, end_block):
        
        self._perpetual_address = web3.toChecksumAddress(perpetual_address)
        self._inverse = inverse
        self._perpetual_position_topic = perpetual_position_topic
        self._end_block = end_block
        # contract
        self._perpetual = Perpetual(
            web3=web3, address=Address(self._perpetual_address))
        self._logger = logging.getLogger()
    
    def _add_position_account_event(self, watcher_id, block_number, transaction_hash, event_index, holder, side, amount, db_session):
        position_event = PositionEvent()
        position_event.watcher_id = watcher_id
        position_event.block_number = block_number
        position_event.transaction_hash = transaction_hash
        position_event.perpetual_address = self._perpetual_address.lower()
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
            .filter(PositionBalance.perpetual_address == self._perpetual_address.lower())\
            .first()
        if position_balance_item is None:
            position_balance_item = PositionBalance()
            position_balance_item.watcher_id = watcher_id
            position_balance_item.perpetual_address = self._perpetual_address.lower()
            position_balance_item.holder = holder
            position_balance_item.balance = amount
            position_balance_item.block_number = block_number
        else:
            position_balance_item.watcher_id = watcher_id
            position_balance_item.block_number = block_number
            position_balance_item.balance = amount
        db_session.add(position_balance_item)
        
    def sync(self, watcher_id, block_number, block_hash, db_session):
        """Sync data"""
        if block_number > self._end_block:
            self._logger.info(f'syncer position block_number {block_number} > mining window end block number!')
            return
            
        position_events = self._parse_perpetual_update_position_event_logs(block_number)
        self._logger.info(f'sync position event, block_number:{block_number}, events:{len(position_events)}')
        for event in position_events:
            holder = event.get('trader')
            position_side = PositionSide(event.get('side'))
            position_size = Decimal(event.get('size'))/Decimal(10**DECIMALS)
            cur_block_number = event.get('blockNumber')
            cur_transaction_hash = event.get('transactionHash')
            event_index = event.get('logIndex')
            self._add_position_account_event(watcher_id, cur_block_number, cur_transaction_hash, event_index,
                                             holder, position_side, position_size, db_session)


    def rollback(self, watcher_id, block_number, db_session):
        """delete data after block_number"""
        self._logger.info(f'rollback position block_number back to {block_number}')
        items = db_session.query(PositionBalance)\
            .filter(PositionBalance.block_number > block_number)\
            .filter(PositionBalance.perpetual_address == self._perpetual_address.lower())\
            .all()
        for item in items:
            # update position_balances table
            position_event = db_session.query(PositionEvent)\
                .filter(PositionEvent.holder == item.holder)\
                .filter(PositionEvent.perpetual_address == item.perpetual_address)\
                .filter(PositionEvent.block_number <= block_number)\
                .order_by(desc(PositionEvent.block_number), desc(PositionEvent.event_index))\
                .first()
            if position_event is None:
                db_session.delete(item)
            else:
                item.balance = position_event.amount
                item.block_number = position_event.block_number
                db_session.add(item)
        
        db_session.query(PositionEvent).filter(PositionEvent.perpetual_address == self._perpetual_address.lower()).\
            filter(PositionEvent.block_number > block_number).delete(synchronize_session=False)

    ################################ NOTICE ######################################
    #                   position size is correct value                           #
    # cashBalance maybe not right(advise not to use it), get it from other event #
    ##############################################################################
    def _parse_perpetual_update_position_event_logs(self, block_number):
        event_filter_params = {
            'topics': [self._perpetual_position_topic],
            'address': [self._perpetual_address],
            'fromBlock': block_number,
            'toBlock': block_number,
        }
        event_data = []
        logs = self._perpetual.web3.eth.getLogs(event_filter_params)
        for log in logs:
            parsed = {}
            parsed['blockNumber'] = log['blockNumber']
            parsed['blockHash'] = log['blockHash']
            parsed['transactionIndex'] = log['transactionIndex']
            parsed['logIndex'] = log['logIndex']
            parsed['transactionHash'] = log['transactionHash'].hex()
            parsed['trader'] = '0x' + log['topics'][1].hex()[26:].lower()
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
            event_data.append(parsed)
        return event_data