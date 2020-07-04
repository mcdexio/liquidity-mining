
from web3 import Web3
from web3.types import BlockData
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker
from orm import Watcher as DBWatcher, WatcherBlock
from typing import List
from syncer import SyncerInterface
import logging
import traceback


class Watcher:
    """
        A Watcher watches and syncs with the blockchain's state.
        The Watcher deals with the rollback of the blockchain, providing a realtime
        data of the blockchain.
    """

    def __init__(self, watcher_id: int, syncers: List[SyncerInterface], web3: Web3, dbEngine: Engine):
        """initializer of Watcher

        Args:
            watcher_id
            syncers (list): a list of SyncerInterface.
        """
        self._watcher_id = watcher_id
        self._syncers = syncers
        self._web3 = web3
        self._Session = sessionmaker(bind=dbEngine, autoflush=False)
        self._logger = logging.getLogger('watcher')

    def sync(self)->int:
        """
        Sync with the blockchain. The watcher may sync forward or rollback by comparing its block hash with
        the data from node's API
        Returns the number of block synced.
        """
        result = 0
        db_session = self._Session()
        try:
            db_watcher = db_session.query(DBWatcher).filter(DBWatcher.id==self._watcher_id).with_for_update().one()
            synced_block_number = db_watcher.synced_block_number
            # rollback
            while synced_block_number >= db_watcher.initial_block_number:
                watcher_block = db_session.query(WatcherBlock).filter(WatcherBlock.watcher_id==self._watcher_id).filter(WatcherBlock.block_number==synced_block_number).one()
                block = self._web3.eth.getBlock(synced_block_number)
                block_hash = block.hash.hex()
                if watcher_block.block_hash == block_hash:
                    break
                synced_block_number -= 1

            if synced_block_number != db_watcher.synced_block_number:
                self._rollback(synced_block_number, db_session, db_watcher)
            to_sync = synced_block_number + 1
            if to_sync <= self._web3.eth.blockNumber:
                new_block = self._web3.eth.getBlock(to_sync)
                self._sync(db_watcher, new_block, db_session)
                result = 1
            db_session.commit()
        except Exception as e:
            result = 0
            self._logger.warning('sync exception:%s', traceback.format_exception(e))
        finally:
            db_session.rollback()
        return result

    def rollback(self, block_number):
        pass

    def _sync(self, db_watcher:DBWatcher, block:BlockData, db_session:Session):
        db_watcher.synced_block_number = block.number
        block_hash = block.hash.hex()
        watcher_block = WatcherBlock(watcher_id=self._watcher_id, block_number=block.number, block_hash=block_hash)
        db_session.add(watcher_block)
        for syncer in self._syncers:
            syncer.sync(self._watcher_id, block.number, block_hash, db_session)

    def _rollback(self, db_watcher:DBWatcher, block_number:int, db_session:Session):

        pass
