from sqlalchemy import desc, func

from lib.wad import Wad
from model.orm import (ImmatureMiningReward, MatureMiningReward,
                       MatureMiningRewardCheckpoint)
from watcher import Watcher

from .types import SyncerInterface


class MatureCheck(SyncerInterface):
    """Checking, then convert immature token into mature token
    """

    def __init__(self, begin_block, end_block, mature_confirm_number, checkpoint_interval_number, mining_round):
        self.begin_block = begin_block
        self.end_block = end_block
        self.mature_confirm_number = mature_confirm_number
        self.checkpoint_interval_number = checkpoint_interval_number
        self.mining_round = mining_round

    def _get_immature_mining_reward_latest_block_number(self, db_session):
        latest_block_number = 0
        result = db_session.query(ImmatureMiningReward)\
            .filter(ImmatureMiningReward.mining_round == self.mining_round)\
            .order_by(desc(ImmatureMiningReward.block_number))\
            .with_entities(
                ImmatureMiningReward.block_number
        ).first()
        if result is not None:
            latest_block_number = result.block_number
        return latest_block_number

    def _get_mature_mining_reward_latest_block_number(self, db_session):
        latest_block_number = 0
        result = db_session.query(MatureMiningReward)\
            .filter(MatureMiningReward.mining_round == self.mining_round)\
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
            .filter(MatureMiningRewardCheckpoint.mining_round == self.mining_round)\
            .order_by(desc(MatureMiningRewardCheckpoint.block_number))\
            .with_entities(
                MatureMiningReward.block_number
        ).first()
        if result:
            latest_block_number = result.block_number
        return latest_block_number

    def sync(self, watcher_id, block_number, block_hash, db_session):
        """Sync data"""
        immature_latest_block_number = self._get_immature_mining_reward_latest_block_number(
            db_session)
        mature_latest_block_number = self._get_mature_mining_reward_latest_block_number(
            db_session)
        if (immature_latest_block_number - mature_latest_block_number) < self.mature_confirm_number:
            # not meet mature requirements
            return

        addup_begin_block_number = mature_latest_block_number
        addup_end_block_number = immature_latest_block_number - self.mature_confirm_number

        items = db_session.query(ImmatureMiningReward)\
            .filter(ImmatureMiningReward.mining_round == self.mining_round)\
            .filter(ImmatureMiningReward.block_number <= addup_end_block_number)\
            .filter(ImmatureMiningReward.block_number > addup_begin_block_number)\
            .group_by(ImmatureMiningReward.holder)\
            .with_entities(
                ImmatureMiningReward.holder,
                func.sum(ImmatureMiningReward.mcb_balance).label('amount')
        )\
            .all()
        for item in items:
            holder = item.holder
            mature_mining_reward = db_session.query(MatureMiningReward).filter(
                MatureMiningReward.holder == holder).first()
            if mature_mining_reward is None:
                mature_mining_reward = MatureMiningReward()
                mature_mining_reward.block_number = addup_end_block_number
                mature_mining_reward.mining_round = self.mining_round
                mature_mining_reward.holder = holder
                mature_mining_reward.mcb_balance = item.amount
            else:
                mature_mining_reward.block_number = addup_end_block_number
                mature_mining_reward.mcb_balance = item.amount

            db_session.add(mature_mining_reward)

        # save checkpoint
        checkpoint_latest_block_number = self._get_mature_mining_reward_checkpoint_latest_block_number(
            db_session)
        if (addup_end_block_number - checkpoint_latest_block_number) >= self.checkpoint_interval_number:
            items = db_session.query(MatureMiningReward).filter(
                MatureMiningReward.block_number == addup_end_block_number).all()
            for item in items:
                checkpoint_item = MatureMiningRewardCheckpoint()
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
        if mature_latest_block_number < block_number:
            # mature_mining_reward record before block_number, no need rollback
            return
        else:
            db_session.query(MatureMiningReward).filter(
                MatureMiningReward.block_number >= block_number).delete()
            if checkpoint_latest_block_number >= block_number:
                db_session.query(MatureMiningRewardCheckpoint).filter(
                    MatureMiningRewardCheckpoint.block_number >= block_number).delete()

            # get correct latest checkpoint block number once again
            checkpoint_latest_block_number = self._get_mature_mining_reward_checkpoint_latest_block_number(
                db_session)
            # rollback mature_mining_reward record to latest correct checkpoint
            items = db_session.query(MatureMiningRewardCheckpoint)\
                .filter(MatureMiningRewardCheckpoint.mining_round == self.mining_round)\
                .filter(MatureMiningRewardCheckpoint.block_number == checkpoint_latest_block_number)\
                .all()
            for item in items:
                mature_mining_reward = MatureMiningReward()
                mature_mining_reward.block_number = item.block_number
                mature_mining_reward.mining_round = item.mining_round
                mature_mining_reward.holder = item.holder
                mature_mining_reward.mcb_balance = item.mcb_balance
                db_session.add(mature_mining_reward)
