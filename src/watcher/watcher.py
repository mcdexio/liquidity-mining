
import logging
import logging.config
import traceback
from typing import List

from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker
from web3 import Web3
from web3.types import BlockData

import config
from model.orm import Watcher as DBWatcher
from model.orm import WatcherBlock
from syncer.types import SyncerInterface


class Watcher:
    """
        A Watcher watches and syncs with the blockchain's state.
        The Watcher deals with the rollback of the blockchain, providing a realtime
        data of the blockchain.
    """

    def __init__(self, watcher_id: int, syncers: List[SyncerInterface], web3: Web3, db_engine: Engine, end_block_number:int=-1):
        """initializer of Watcher

        Args:
            watcher_id
            syncers (list): a list of SyncerInterface.
        """
        self._watcher_id = watcher_id
        self._syncers = syncers
        self._web3 = web3
        self._Session = sessionmaker(bind=db_engine)
        self._logger = logging.getLogger()
        self._end_block_number = end_block_number
        config.LOG_CONFIG["handlers"]["file_handler"]["filename"] = config.WATCHER_LOGPATH
        logging.config.dictConfig(config.LOG_CONFIG)


    def sync(self) -> int:
        """
        Sync with the blockchain. The watcher may sync forward or rollback by comparing its block hash with
        the data from node's API
        Returns:
            positive number: the synced block number
            zero: reach the end of the watcher
            negative: error
        """
        result = -1
        db_session = self._Session()
        try:
            db_watcher = db_session.query(DBWatcher).filter(
                DBWatcher.id == self._watcher_id).with_for_update().one()
            synced_block_number = db_watcher.synced_block_number
            # rollback
            while synced_block_number >= db_watcher.initial_block_number:
                watcher_block = db_session.query(WatcherBlock).filter(WatcherBlock.watcher_id == self._watcher_id).filter(
                    WatcherBlock.block_number == synced_block_number).one()
                block = self._web3.eth.getBlock(synced_block_number)
                block_hash = block.hash.hex()
                if watcher_block.block_hash == block_hash:
                    break
                self._logger.warning('rollback block[%d] old_hash[%s] new_hash[%s]', watcher_block.block_number, watcher_block.block_hash, block_hash)
                synced_block_number -= 1

            if synced_block_number != db_watcher.synced_block_number:
                self._rollback(db_watcher, synced_block_number, db_session)
            to_sync = synced_block_number + 1
            if self._end_block_number > 0 and to_sync > self._end_block_number + config.MATURE_CONFIRM:
                self._logger.warning('reach end of the watcher: end block[%d], synced block[%d]', self._end_block_number, synced_block_number)
                return 0
            if to_sync <= self._web3.eth.blockNumber:
                new_block = self._web3.eth.getBlock(to_sync)
                self._sync(db_watcher, new_block, db_session)
                result = to_sync
            db_session.commit()
            if result:
                self._logger.info('sync block[%d] hash[%s]', new_block.number, new_block.hash)
        except:
            result = -1
            self._logger.warning('sync error', exec_info=1, stack_info=1)
        finally:
            db_session.rollback()
        return result

    def rollback(self, synced_block_number: int) -> int:
        """force to rollback the database

        Args:
            synced_block_number (int): rollback the block after synced_block_number

        Returns:
            int: new synced_block_number if success, otherwise -1
        """
        db_session = self._Session()
        result = -1
        try:
            db_watcher = db_session.query(DBWatcher).filter(
                DBWatcher.id == self._watcher_id).with_for_update().one()
            if synced_block_number < db_watcher.synced_block_number:
                self._rollback(db_watcher, synced_block_number, db_session)
                result = 0
            else:
                self._logger.warning(
                    "rollback error:synced_block_number[%d] is larger than db[%d]", synced_block_number, db_watcher.synced_block_number)
            db_session.commit()
        except:
            self._logger.warning('rollback error', exec_info=1, stack_info=1)
        finally:
            db_session.rollback()
        return result

    def _sync(self, db_watcher: DBWatcher, block: BlockData, db_session):
        db_watcher.synced_block_number = block.number
        block_hash = block.hash.hex()
        watcher_block = WatcherBlock(
            watcher_id=self._watcher_id, block_number=block.number, block_hash=block_hash)
        db_session.add(watcher_block)
        for syncer in self._syncers:
            syncer.sync(self._watcher_id, block.number, block_hash, db_session)

    def _rollback(self, db_watcher: DBWatcher, synced_block_number: int, db_session):
        db_watcher.synced_block_number = synced_block_number
        db_session.query(WatcherBlock).filter(WatcherBlock.watcher_id == self._watcher_id).filter(
            WatcherBlock.block_number > synced_block_number).delete()
        for syncer in self._syncers:
            syncer.rollback(self._watcher_id, synced_block_number, db_session)
