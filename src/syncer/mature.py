from sqlalchemy import desc, func
import logging
import logging.config
from decimal import Decimal

import config
from model.orm import (ImmatureMiningReward, MatureMiningReward,
                       MatureMiningRewardCheckpoint)
from watcher import Watcher

from .types import SyncerInterface


class MatureChecker(SyncerInterface):
    """Checking, then convert immature token into mature token
    """

    def __init__(self, mature_confirm_number, checkpoint_interval_number, mining_round):
        self._mature_confirm_number = mature_confirm_number
        self._checkpoint_interval_number = checkpoint_interval_number
        self._mining_round = mining_round

        self._logger = logging.getLogger()    

    def _get_mature_mining_reward_latest_block_number(self, db_session):
        latest_block_number = 0
        result = db_session.query(MatureMiningReward)\
            .filter(MatureMiningReward.mining_round == self._mining_round)\
            .order_by(desc(MatureMiningReward.block_number))\
            .with_entities(
                MatureMiningReward.block_number
        ).first()
        if result:
            latest_block_number = result.block_number
        return latest_block_number

    def _get_mature_mining_reward_checkpoint_latest_block_number(self, db_session):
        latest_block_number = 0
        result = db_session.query(MatureMiningRewardCheckpoint)\
            .filter(MatureMiningRewardCheckpoint.mining_round == self._mining_round)\
            .order_by(desc(MatureMiningRewardCheckpoint.block_number))\
            .with_entities(
                MatureMiningRewardCheckpoint.block_number
        ).first()
        if result:
            latest_block_number = result.block_number
        return latest_block_number



    def sync(self, watcher_id, block_number, block_hash, db_session):
        """Sync data"""
        latest_block_number = block_number
        mature_latest_block_number = self._get_mature_mining_reward_latest_block_number(
            db_session)
        if (latest_block_number - mature_latest_block_number) < self._mature_confirm_number:
            # not meet mature requirements
            self._logger.info(f'latest_block_number:{latest_block_number}, mature_block_number:{mature_latest_block_number}, no mature block, waiting...')
            return

        # get all mature summary items
        mature_mining_reward_dict = {}
        mature_mining_reward_items = db_session.query(MatureMiningReward)\
            .filter(MatureMiningReward.mining_round == self._mining_round)\
            .all()
        for item in mature_mining_reward_items:
            mature_mining_reward_dict[item.holder] = item    

        addup_begin_block_number = mature_latest_block_number
        addup_end_block_number = latest_block_number - self._mature_confirm_number
        items = db_session.query(ImmatureMiningReward)\
            .filter(ImmatureMiningReward.mining_round == self._mining_round)\
            .filter(ImmatureMiningReward.block_number <= addup_end_block_number)\
            .filter(ImmatureMiningReward.block_number > addup_begin_block_number)\
            .group_by(ImmatureMiningReward.pool_name, ImmatureMiningReward.holder)\
            .with_entities(
                ImmatureMiningReward.pool_name, 
                ImmatureMiningReward.holder,
                func.sum(ImmatureMiningReward.mcb_balance).label('amount')
            )\
            .all()
        for item in items:
            holder = item.holder
            if holder not in mature_mining_reward_dict.keys():
                mature_mining_reward = MatureMiningReward()
                mature_mining_reward.pool_name = item.pool_name
                mature_mining_reward.block_number = addup_end_block_number
                mature_mining_reward.mining_round = self._mining_round
                mature_mining_reward.holder = holder
                mature_mining_reward.mcb_balance = item.amount
            else:
                mature_mining_reward = mature_mining_reward_dict[holder]
                mature_mining_reward.block_number = addup_end_block_number
                mature_mining_reward.mcb_balance += item.amount
            db_session.add(mature_mining_reward)

        # save checkpoint
        checkpoint_latest_block_number = self._get_mature_mining_reward_checkpoint_latest_block_number(
            db_session)
        if (addup_end_block_number - checkpoint_latest_block_number) >= self._checkpoint_interval_number:
            self._logger.info(f'save checkpoint block_number:{addup_end_block_number}')
            # check last round checkpoint block_number
            result = db_session.query(MatureMiningRewardCheckpoint)\
                .order_by(desc(MatureMiningRewardCheckpoint.block_number))\
                .with_entities(
                    MatureMiningRewardCheckpoint.block_number
            ).first()
            if result and addup_end_block_number <= result.block_number:
                self._logger.info(f'no need save checkpoint block_number:{addup_end_block_number}, last round checkpoint number:{result.block_number}')
                return
            items = db_session.query(MatureMiningReward).filter(
                MatureMiningReward.block_number == addup_end_block_number).all()
            for item in items:
                checkpoint_item = MatureMiningRewardCheckpoint()
                checkpoint_item.pool_name = item.pool_name
                checkpoint_item.block_number = item.block_number
                checkpoint_item.mining_round = item.mining_round
                checkpoint_item.holder = item.holder
                checkpoint_item.mcb_balance = item.mcb_balance
                db_session.add(checkpoint_item)

    def rollback(self, watcher_id, block_number, db_session):
        """delete data after block_number"""
        mature_latest_block_number = self._get_mature_mining_reward_latest_block_number(
            db_session)
        checkpoint_latest_block_number = self._get_mature_mining_reward_checkpoint_latest_block_number(
            db_session)
        if mature_latest_block_number <= block_number:
            # mature_mining_reward record before block_number, no need rollback
            self._logger.info(f'no need rollback, mature_block_number < rollback_block_number')
            return
        else:
            db_session.query(MatureMiningReward)\
                .filter(MatureMiningReward.block_number > block_number)\
                .filter(MatureMiningReward.mining_round == self._mining_round)\
                .delete(synchronize_session=False)

            if checkpoint_latest_block_number > block_number:
                db_session.query(MatureMiningRewardCheckpoint)\
                    .filter(MatureMiningRewardCheckpoint.block_number > block_number)\
                    .filter(MatureMiningRewardCheckpoint.mining_round == self._mining_round)\
                    .delete(synchronize_session=False)

            # get correct latest checkpoint block number once again
            checkpoint_latest_block_number = self._get_mature_mining_reward_checkpoint_latest_block_number(
                db_session)
            # rollback mature_mining_reward record to latest correct checkpoint
            self._logger.info(f'mining round {self._mining_round}, rollback mature_mining_reward block_number from {mature_latest_block_number} to {checkpoint_latest_block_number}')
            items = db_session.query(MatureMiningRewardCheckpoint)\
                .filter(MatureMiningRewardCheckpoint.mining_round == self._mining_round)\
                .filter(MatureMiningRewardCheckpoint.block_number == checkpoint_latest_block_number)\
                .all()
            for item in items:
                mature_mining_reward = MatureMiningReward()
                mature_mining_reward.pool_name = item.pool_name
                mature_mining_reward.block_number = item.block_number
                mature_mining_reward.mining_round = item.mining_round
                mature_mining_reward.holder = item.holder
                mature_mining_reward.mcb_balance = item.mcb_balance
                db_session.add(mature_mining_reward)