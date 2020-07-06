import logging
import logging.config
from sqlalchemy import func
from web3 import Web3
from decimal import Decimal

from contract.erc20 import ERC20Token
from lib.address import Address
from model.orm import ImmatureMiningReward, TokenEvent, ImmatureMiningRewardSummary, TokenBalance
from watcher import Watcher

import config
from .types import SyncerInterface


class ShareMining(SyncerInterface):
    """Mining according to the balance of the share token.

    reward_i = reward_per_block * (share_token_balance_i / (share_token_total_supply) )
    """

    def __init__(self, begin_block, end_block, reward_per_block, share_token_address, mining_round):
        self._begin_block = begin_block
        self._end_block = end_block
        self._reward_per_block = reward_per_block
        self._share_token_address = share_token_address.lower()
        self._mining_round = mining_round

        self._logger = logging.getLogger()
        config.LOG_CONFIG["handlers"]["file_handler"]["filename"] = config.SYNCER_LOGPATH
        logging.config.dictConfig(config.LOG_CONFIG)

    def sync(self, watcher_id, block_number, block_hash, db_session):
        """Sync data"""
        result = db_session.query(TokenBalance)\
            .filter(TokenBalance.token == self._share_token_address)\
            .with_entities(
                func.sum(TokenBalance.balance).label('amount')
        ).first()   
        total_share_token_amount = Decimal(result.amount)

        items = db_session.query(TokenEvent)\
            .filter(TokenEvent.token == self._share_token_address)\
            .filter(TokenEvent.block_number <= block_number)\
            .group_by(TokenEvent.holder)\
            .with_entities(
                TokenEvent.holder,
                func.sum(TokenEvent.amount).label('amount')
        ).all()
        self._logger(f'sync mining reward, block_number:{block_number}, holders:{len(items)}')
        for item in items:
            holder = item.holder
            holder_share_token_amount = Decimal(item.amount)
            reward = self._reward_per_block * holder_share_token_amount / total_share_token_amount

            immature_mining_reward = ImmatureMiningReward()
            immature_mining_reward.block_number = block_number
            immature_mining_reward.mining_round = self._mining_round
            immature_mining_reward.holder = holder
            immature_mining_reward.mcb_balance = reward
            db_session.add(immature_mining_reward)

    def rollback(self, watcher_id, block_number, db_session):
        """delete data after block_number"""
        self._logger(f'rollback immature_mining_reward block_number back to {block_number}')
        items = db_session.query(ImmatureMiningReward)\
            .filter(ImmatureMiningReward.block_number >= block_number)\
            .group_by(ImmatureMiningReward.mining_round, ImmatureMiningReward.holder)\
            .with_entities(
                ImmatureMiningReward.mining_round,
                ImmatureMiningReward.holder,
                func.sum(ImmatureMiningReward.mcb_balance).label('mcb_balance')
        ).all()
        for item in items:
            # update immature_mining_reward_summaries table
            summary_item = db_session.query(ImmatureMiningRewardSummary)\
                .filter(ImmatureMiningRewardSummary.holder == item.holder)\
                .filter(ImmatureMiningRewardSummary.mining_round == item.mining_round)\
                    .first()
            if summary_item is None:
                self._logger.error(f'opps, update immature_mining_reward_summaries error, can not find item:{item}')
            else:
                summary_item.mcb_balance -= item.mcb_balance
                db_session.add(summary_item)

        db_session.query(ImmatureMiningReward).filter(
            ImmatureMiningReward.block_number >= block_number).delete()