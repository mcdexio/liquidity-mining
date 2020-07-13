import logging
import logging.config
from sqlalchemy import func
from web3 import Web3
from decimal import Decimal, getcontext, ROUND_DOWN

from contract.erc20 import ERC20Token
from lib.address import Address
from lib.wad import Wad
from model.orm import ImmatureMiningReward, TokenEvent, ImmatureMiningRewardSummary, TokenBalance, PerpShareAmmProxyMap
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
        self._rebalance_hard_fork_block_number = config.REBALANCE_HARD_FORK_BLOCK_NUMBER

        self._logger = logging.getLogger()

    def _get_token_map(self, db_session):
        token_map = {}
        token_map[self._share_token_address] = {}
        item = db_session.query(PerpShareAmmProxyMap)\
            .filter(PerpShareAmmProxyMap.share_addr == self._share_token_address)\
            .first()
        if item is not None:
            token_map[self._share_token_address] = {
                'perp_addr': item.perp_addr,
                'amm_addr': item.amm_addr,
                'amm_proxy_addr': item.proxy_addr,
            }
        return token_map

    def _get_effective_share_info(self, share_token_items, total_share_token_amount, db_session):
        effective_share_dict = {}
        position_holder_dict = {}
        share_token_dict = {}
        total_effective_share_amount = Decimal(0)
        for item in share_token_items:
            share_token_dict[item.holder] = item.amount
           
        token_map = self._get_token_map(db_session)
        perp_addr = token_map[self._share_token_address].get('perp_addr')
        amm_proxy_addr = token_map[self._share_token_address].get('amm_proxy_addr')
        position_items = db_session.query(TokenBalance)\
            .filter(TokenBalance.token == perp_addr)\
            .all()
        for item in position_items:
            position_holder_dict[item.holder] = item.balance
        amm_position = position_holder_dict[amm_proxy_addr]

        for holder, holder_position_in_margin_account in position_holder_dict.items():
            holder_share_token_amount = share_token_dict.get(holder)
            if holder_share_token_amount == Decimal(0):
                continue
            holder_position_in_amm = Wad.from_number(amm_position) * Wad.from_number(holder_share_token_amount) / Wad.from_number(total_share_token_amount)
            holder_portfolio_position = holder_position_in_amm + Wad.from_number(holder_position_in_margin_account)
            imbalance_rate = abs(holder_portfolio_position / holder_position_in_amm)
            if imbalance_rate <= Decimal(0.1):
                holder_effective_share = holder_share_token_amount
            elif imbalance_rate >= Decimal(0.9):
                holder_effective_share = holder_share_token_amount * Decimal(0.1)
            else:
                holder_effective_share = holder_share_token_amount * (Decimal(89/80) - imbalance_rate * Decimal(9/8))
            effective_share_dict[holder] = holder_effective_share
            total_effective_share_amount += holder_effective_share
        return effective_share_dict, total_effective_share_amount


    def sync(self, watcher_id, block_number, block_hash, db_session):
        """Sync data"""
        if block_number < self._begin_block or block_number > self._end_block:
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

        # get all immature summary items
        immature_summary_dict = {}
        immature_summary_items = db_session.query(ImmatureMiningRewardSummary)\
            .filter(ImmatureMiningRewardSummary.mining_round == self._mining_round)\
            .all()
        for item in immature_summary_items:
            immature_summary_dict[item.holder] = item    

        share_token_items = db_session.query(TokenEvent)\
            .filter(TokenEvent.token == self._share_token_address)\
            .filter(TokenEvent.block_number <= block_number)\
            .group_by(TokenEvent.holder)\
            .with_entities(
                TokenEvent.holder,
                func.sum(TokenEvent.amount).label('amount')
        ).all()
        self._logger.info(f'sync mining reward, block_number:{block_number}, holders:{len(share_token_items)}')
        
        # check rebalance_hard_fork block number 
        if block_number >= self._rebalance_hard_fork_block_number:
            effective_share_dict, total_effective_share_amount = self._get_effective_share_info(share_token_items, total_share_token_amount, db_session)

        for item in share_token_items:
            holder = item.holder
            if block_number >= self._rebalance_hard_fork_block_number:
                holder_effective_share_amount = effective_share_dict.get(holder, Decimal(0))
                wad_reward = Wad.from_number(self._reward_per_block) * Wad.from_number(holder_effective_share_amount) / Wad.from_number(total_effective_share_amount)
                reward = Decimal(str(wad_reward))
            else:
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
            if holder not in immature_summary_dict.keys():
                immature_summary_item = ImmatureMiningRewardSummary()
                immature_summary_item.mining_round = self._mining_round
                immature_summary_item.holder = holder
                immature_summary_item.mcb_balance = reward
            else:
                immature_summary_item = immature_summary_dict[holder]
                immature_summary_item.mcb_balance += reward
            db_session.add(immature_summary_item)

    def rollback(self, watcher_id, block_number, db_session):
        """delete data after block_number"""
        self._logger.info(f'rollback immature_mining_reward block_number back to {block_number}')
        items = db_session.query(ImmatureMiningReward)\
            .filter(ImmatureMiningReward.block_number > block_number)\
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
            ImmatureMiningReward.block_number > block_number).delete()