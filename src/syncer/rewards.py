import logging
import logging.config
from sqlalchemy import func
from web3 import Web3
from decimal import Decimal, getcontext, ROUND_DOWN

from contract.erc20 import ERC20Token
from lib.address import Address
from lib.wad import Wad
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

    def sync(self, watcher_id, block_number, block_hash, db_session):
        """Sync data"""
        if block_number < self._begin_block or block_number >self._end_block:
            self._logger.info(f'block_number {block_number} not in mining window!')
            return
        
        result = db_session.query(TokenBalance)\
            .filter(TokenBalance.token == self._share_token_address)\
            .with_entities(
                func.sum(TokenBalance.balance)
        ).first()
        if result[0] is None:
            self._logger.error(f'opps, token_balance is empty!')
            return
        total_share_token_amount = result[0]

        items = db_session.query(TokenEvent)\
            .filter(TokenEvent.token == self._share_token_address)\
            .filter(TokenEvent.block_number <= block_number)\
            .group_by(TokenEvent.holder)\
            .with_entities(
                TokenEvent.holder,
                func.sum(TokenEvent.amount).label('amount')
        ).all()
        self._logger.info(f'sync mining reward, block_number:{block_number}, holders:{len(items)}')
        for item in items:
            holder = item.holder
            holder_share_token_amount = Decimal(item.amount)
            wad_reward = Wad.from_number(self._reward_per_block) * Wad.from_number(holder_share_token_amount) / Wad.from_number(total_share_token_amount)
            reward = Decimal(str(wad_reward))

            immature_mining_reward = ImmatureMiningReward()
            immature_mining_reward.block_number = block_number
            immature_mining_reward.mining_round = self._mining_round
            immature_mining_reward.holder = holder
            immature_mining_reward.mcb_balance = reward
            db_session.add(immature_mining_reward)

            # update immature_mining_reward_summaries table, simulated materialized view
            immature_summary_item = db_session.query(ImmatureMiningRewardSummary)\
                .filter(ImmatureMiningRewardSummary.mining_round == self._mining_round)\
                .filter(ImmatureMiningRewardSummary.holder == holder)\
                    .first()
            if immature_summary_item is None:
                immature_summary_item = ImmatureMiningRewardSummary()
                immature_summary_item.mining_round = self._mining_round
                immature_summary_item.holder = holder
                immature_summary_item.mcb_balance = reward
            else:
                immature_summary_item.balance += reward
            db_session.add(immature_summary_item)

    def rollback(self, watcher_id, block_number, db_session):
        """delete data after block_number"""
        self._logger.info(f'rollback immature_mining_reward block_number back to {block_number}')
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