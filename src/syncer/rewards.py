import logging
import logging.config
from sqlalchemy import func, desc
from web3 import Web3
from decimal import Decimal, getcontext, ROUND_DOWN

from contract.erc20 import ERC20Token
from lib.address import Address
from lib.wad import Wad
from model.orm import ImmatureMiningReward, TokenEvent, ImmatureMiningRewardSummary, TokenBalance
from model.orm import ChainLinkPriceEvent, PerpShareAmmProxyMap, PositionBalance, PositionEvent
from watcher import Watcher

import config
from .types import SyncerInterface


class ShareMining(SyncerInterface):
    """Mining according to the balance of the share token.

    reward_i = reward_per_block * (share_token_balance_i / (share_token_total_supply) )
    """

    def __init__(self, begin_block, end_block, reward_per_block, mining_round):
        self._begin_block = begin_block
        self._end_block = end_block
        self._reward_per_block = reward_per_block
        self._mining_round = mining_round

        self._eth_perp_share_token_address = config.ETH_PERP_SHARE_TOKEN_ADDRESS.lower()
        self._uniswap_mcb_share_token_address = config.UNISWAP_MCB_ETH_SHARE_TOKEN_ADDRESS.lower()
        self._mcb_token_address = config.MCB_TOKEN_ADDRESS.lower()
        self._xia_rebalance_hard_fork_block_number = config.XIA_REBALANCE_HARD_FORK_BLOCK_NUMBER
        self._shang_reward_link_pool_block_number = config.SHANG_REWARD_LINK_POOL_BLOCK_NUMBER
        self._shang_reward_btc_pool_block_number = config.SHANG_REWARD_BTC_POOL_BLOCK_NUMBER
        self._zhou_begin_block_number = config.ZHOU_BEGIN_BLOCK_NUMBER

        self._logger = logging.getLogger()

    def _get_token_map(self, share_token_address, db_session):
        token_map = {}
        token_map[share_token_address] = {}
        item = db_session.query(PerpShareAmmProxyMap)\
            .filter(PerpShareAmmProxyMap.share_addr == share_token_address)\
            .first()
        if item is not None:
            token_map[share_token_address] = {
                'perp_addr': item.perp_addr.strip(),
                'amm_addr': item.amm_addr.strip(),
                'amm_proxy_addr': item.proxy_addr.strip(),
            }
        return token_map

    def _get_effective_share_info(self, block_number, pool_share_token_address, share_token_items, total_share_token_amount, db_session):
        effective_share_dict = {}
        position_holder_dict = {}
        share_token_dict = {}
        total_effective_share_amount = Decimal(0)
        for item in share_token_items:
            share_token_dict[item.holder] = item.balance

        if block_number >= self._zhou_begin_block_number:
            # period from ZHOU, use encourage holder formula calc reward, pool_effective_usd_value is pool_usd_value
            effective_share_dict = share_token_dict
            total_effective_share_amount = total_share_token_amount
            return effective_share_dict, total_effective_share_amount

        token_map = self._get_token_map(pool_share_token_address, db_session)
        perp_addr = token_map[pool_share_token_address].get('perp_addr')
        amm_proxy_addr = token_map[pool_share_token_address].get('amm_proxy_addr')
        position_items = db_session.query(PositionBalance)\
            .filter(PositionBalance.perpetual_address == perp_addr)\
            .all()
        for item in position_items:
            position_holder_dict[item.holder] = item.balance
        amm_position = position_holder_dict.get(amm_proxy_addr, Decimal(0))

        for holder, holder_position_in_margin_account in position_holder_dict.items():
            holder_share_token_amount = share_token_dict.get(holder)
            if holder_share_token_amount == Decimal(0) or holder_share_token_amount is None:
                continue
            holder_position_in_amm = Wad.from_number(amm_position) * Wad.from_number(holder_share_token_amount) / Wad.from_number(total_share_token_amount)
            holder_portfolio_position = holder_position_in_amm + Wad.from_number(holder_position_in_margin_account)
            imbalance_rate = abs(holder_portfolio_position / holder_position_in_amm)
            imbalance_rate = Decimal(str(imbalance_rate))
            if self._mining_round == 'XIA':
                if imbalance_rate <= Decimal(0.1):
                    holder_effective_share = holder_share_token_amount
                elif imbalance_rate >= Decimal(0.9):
                    holder_effective_share = holder_share_token_amount * Decimal(0.1)
                else:
                    holder_effective_share = holder_share_token_amount * (Decimal(89/80) - imbalance_rate * Decimal(9/8))
            elif self._mining_round == 'SHANG':
                if imbalance_rate <= Decimal(0.2):
                    holder_effective_share = holder_share_token_amount
                elif imbalance_rate >= Decimal(0.9):
                    holder_effective_share = holder_share_token_amount * Decimal(0.1)
                else:
                    holder_effective_share = holder_share_token_amount * (Decimal(44/35) - imbalance_rate * Decimal(9/7))
            effective_share_dict[holder] = holder_effective_share
            total_effective_share_amount += holder_effective_share
        return effective_share_dict, total_effective_share_amount


    def _get_total_share_token_amount(self, share_token_address, db_session):
        result = db_session.query(TokenBalance)\
            .filter(TokenBalance.token == share_token_address)\
            .with_entities(
                func.sum(TokenBalance.balance)
        ).first()
        if result[0] is None:
            total_share_token_amount = 0
        else:
            total_share_token_amount = result[0]
        return total_share_token_amount

    def _get_share_token_items(self, share_token_address, db_session):
        share_token_items = db_session.query(TokenBalance)\
            .filter(TokenBalance.token == share_token_address)\
            .filter(TokenBalance.balance != Decimal(0))\
            .with_entities(
                TokenBalance.holder,
                TokenBalance.balance
        ).all()
        return share_token_items

    def _calculate_pool_reward(self, block_number, pool_name, pool_share_token_address, pool_reward_percent, db_session):
        total_share_token_amount = self._get_total_share_token_amount(pool_share_token_address, db_session)
        if total_share_token_amount == 0:
            self._logger.warning(f'opps, share_token {pool_share_token_address} total amount is zero!')
            return

        # get all immature summary items
        immature_summary_dict = {}
        immature_summary_items = db_session.query(ImmatureMiningRewardSummary)\
            .filter(ImmatureMiningRewardSummary.mining_round == self._mining_round)\
            .filter(ImmatureMiningRewardSummary.pool_name == pool_name)\
            .all()
        for item in immature_summary_items:
            immature_summary_dict[item.holder] = item    

        share_token_items = db_session.query(TokenBalance)\
            .filter(TokenBalance.token == pool_share_token_address)\
            .with_entities(
                TokenBalance.holder,
                TokenBalance.balance
        ).all()        
        self._logger.info(f'sync mining reward, block_number:{block_number}, holders:{len(share_token_items)}, share_token: {pool_share_token_address}')
        
        # amm pool ETH_PERP, use effective share after rebalance_hard_fork block number
        if pool_name == 'ETH_PERP' and block_number >= self._xia_rebalance_hard_fork_block_number:
            effective_share_dict, total_effective_share_amount = self._get_effective_share_info(block_number, pool_share_token_address, share_token_items, total_share_token_amount, db_session)

        for item in share_token_items:
            holder = item.holder
            if pool_name == 'ETH_PERP' and block_number >= self._xia_rebalance_hard_fork_block_number:
                holder_effective_share_amount = effective_share_dict.get(holder, Decimal(0))
                wad_reward = Wad.from_number(pool_reward_percent) * Wad.from_number(self._reward_per_block) * Wad.from_number(holder_effective_share_amount) / Wad.from_number(total_effective_share_amount)
                reward = Decimal(str(wad_reward))
            else:
                holder_share_token_amount = Decimal(item.balance)
                wad_reward = Wad.from_number(pool_reward_percent) * Wad.from_number(self._reward_per_block) * Wad.from_number(holder_share_token_amount) / Wad.from_number(total_share_token_amount)
                reward = Decimal(str(wad_reward))

            immature_mining_reward = ImmatureMiningReward()
            immature_mining_reward.block_number = block_number
            immature_mining_reward.pool_name = pool_name
            immature_mining_reward.mining_round = self._mining_round
            immature_mining_reward.holder = holder
            immature_mining_reward.mcb_balance = reward
            db_session.add(immature_mining_reward)

            # update immature_mining_reward_summaries table, simulated materialized view
            if holder not in immature_summary_dict.keys():
                immature_summary_item = ImmatureMiningRewardSummary()
                immature_summary_item.mining_round = self._mining_round
                immature_summary_item.pool_name = pool_name
                immature_summary_item.holder = holder
                immature_summary_item.mcb_balance = reward
            else:
                immature_summary_item = immature_summary_dict[holder]
                immature_summary_item.mcb_balance += reward
            db_session.add(immature_summary_item)


    def _get_chain_link_price(self, block_number, pool_name, db_session):
        if pool_name == 'BTC_PERP':
            link_price_address = config.CHAINLINK_BTC_USD_ADDRESS.lower()
        link_price_item = db_session.query(ChainLinkPriceEvent)\
            .filter(ChainLinkPriceEvent.chain_link_address == link_price_address)\
            .filter(ChainLinkPriceEvent.block_number <= block_number)\
            .order_by(desc(ChainLinkPriceEvent.block_number))\
            .first()
        if link_price_item is None:
            raise Exception('link price still not sync!')
        else:
            price = link_price_item.price
            return price

    def _get_pool_usd_value(self, block_number, pool_name, pool_share_token_address, inverse, db_session):
        amm_usd_value = Decimal(0)
        amm_position = Decimal(0)
        token_map = self._get_token_map(pool_share_token_address, db_session)
        perp_addr = token_map[pool_share_token_address].get('perp_addr')
        amm_proxy_addr = token_map[pool_share_token_address].get('amm_proxy_addr')
        amm_proxy_item = db_session.query(PositionBalance)\
            .filter(PositionBalance.perpetual_address == perp_addr)\
            .filter(PositionBalance.holder == amm_proxy_addr)\
            .first()
        if amm_proxy_item:
            amm_position = amm_proxy_item.balance
        if inverse:
            amm_usd_value = abs(Wad.from_number(amm_position))
        else:
            chain_link_price = self._get_chain_link_price(block_number, pool_name, db_session)
            # vanilla contract
            amm_usd_value = abs(Wad.from_number(amm_position) * Wad.from_number(chain_link_price))
        return amm_usd_value

    def _get_pool_value_info(self, block_number, pool_info, pool_reward_percent, db_session):
        pool_value_info = {}
        pools_total_effective_value = Wad(0)
        for pool_name, pool_share_token_address in pool_info.items():
            if pool_name not in pool_value_info.keys():
                pool_value_info[pool_name] = {}
            pool_value_info[pool_name]['pool_share_token_address'] = pool_share_token_address

            if pool_name in ('ETH_PERP', 'LINK_PERP', 'BTC_PERP'):
                pool_type = 'AMM'
                pool_value_info[pool_name]['pool_type'] = pool_type
                if pool_name == 'BTC_PERP':
                    pool_contract_inverse = False
                elif pool_name in ('ETH_PERP', 'LINK_PERP'):
                    pool_contract_inverse = True
            elif pool_name == 'UNISWAP_MCB_ETH':
                pool_type = 'UNISWAP'
                pool_value_info[pool_name]['pool_type'] = pool_type

            total_share_token_amount = self._get_total_share_token_amount(pool_share_token_address, db_session)
            pool_value_info[pool_name]['total_share_token_amount'] = total_share_token_amount

            share_token_items = self._get_share_token_items(pool_share_token_address, db_session)
            pool_value_info[pool_name]['share_token_items'] = share_token_items

            if pool_type == 'AMM' and block_number >= self._xia_rebalance_hard_fork_block_number:
                # pool_type is AMM, use effective share calc reward: 
                # 1) period XIA and block_number >=_xia_rebalance_hard_fork_block_number;
                # 2) period SHANG;
                # 3) FROM period ZHOU, effective share eq to holder share
                effective_share_dict, total_effective_share_amount = self._get_effective_share_info(block_number, pool_share_token_address, share_token_items, total_share_token_amount, db_session)
                pool_value_info[pool_name]['effective_share_dict'] = effective_share_dict
                pool_value_info[pool_name]['total_effective_share_amount'] = total_effective_share_amount
                pool_usd_value = self._get_pool_usd_value(block_number, pool_name, pool_share_token_address, pool_contract_inverse, db_session)
                if total_share_token_amount != 0:
                    pool_effective_usd_value = pool_usd_value * Wad.from_number(total_effective_share_amount) / Wad.from_number(total_share_token_amount)    
                else:
                    self._logger.warning(f'opps, pool:{pool_name}, share_token total amount is zero, skip it!')
                    pool_effective_usd_value = Wad(0)
                pool_value_info[pool_name]['pool_effective_usd_value'] = pool_effective_usd_value
                pools_total_effective_value +=  pool_effective_usd_value
            else:
                # include two case: 
                # 1) pool_type is UNISWAP;
                # 2) pool_type is AMM and block number before _xia_rebalance_hard_fork_block_number;
                pool_reward = Wad.from_number(pool_reward_percent) * Wad.from_number(self._reward_per_block)
                pool_value_info[pool_name]['pool_reward'] = pool_reward
        
        # update AMM pool reward
        if pool_type == 'AMM' and block_number >= self._xia_rebalance_hard_fork_block_number:
            for pool_name in pool_value_info.keys():
                pool_effective_usd_value = pool_value_info[pool_name]['pool_effective_usd_value']
                pool_reward = Wad.from_number(pool_reward_percent) * Wad.from_number(self._reward_per_block) * pool_effective_usd_value / Wad.from_number(pools_total_effective_value)
                pool_value_info[pool_name]['pool_reward'] = pool_reward

        return pool_value_info

    def _calculate_pools_reward(self, block_number, pool_info, pool_reward_percent, db_session):
        pool_value_info = self._get_pool_value_info(block_number, pool_info, pool_reward_percent, db_session)
        self._logger.info(f'sync mining reward, block_number:{block_number}, pools:{",".join(pool_info.keys())}')
        
        for pool_name in pool_value_info.keys():
            # get all immature summary items of pool_name
            immature_summary_dict = {}
            immature_summary_items = db_session.query(ImmatureMiningRewardSummary)\
                .filter(ImmatureMiningRewardSummary.mining_round == self._mining_round)\
                .filter(ImmatureMiningRewardSummary.pool_name == pool_name)\
                .all()
            for item in immature_summary_items:
                immature_summary_dict[item.holder] = item    

            total_share_token_amount = pool_value_info[pool_name]['total_share_token_amount']
            if total_share_token_amount == 0:
                self._logger.warning(f'opps, pool:{pool_name}, share_token total amount is zero, skip it!')
                continue

            share_token_items = pool_value_info[pool_name]['share_token_items']

            pool_type = pool_value_info[pool_name]['pool_type']
            pool_reward = pool_value_info[pool_name]['pool_reward']

            for item in share_token_items:
                holder = item.holder
                if item.balance == Decimal(0):
                    continue
                # amm pool, use effective share after xia_rebalance_hard_fork block number
                if pool_type == 'AMM' and block_number >= self._xia_rebalance_hard_fork_block_number:
                    total_effective_share_amount = pool_value_info[pool_name]['total_effective_share_amount']
                    holder_effective_share_amount = pool_value_info[pool_name]['effective_share_dict'].get(holder, Decimal(0))
                    wad_reward = pool_reward * Wad.from_number(holder_effective_share_amount) / Wad.from_number(total_effective_share_amount)
                    reward = Decimal(str(wad_reward))
                else:
                    holder_share_token_amount = Decimal(item.balance)
                    wad_reward = pool_reward * Wad.from_number(holder_share_token_amount) / Wad.from_number(total_share_token_amount)
                    reward = Decimal(str(wad_reward))

                immature_mining_reward = ImmatureMiningReward()
                immature_mining_reward.block_number = block_number
                immature_mining_reward.pool_name = pool_name
                immature_mining_reward.mining_round = self._mining_round
                immature_mining_reward.holder = holder
                immature_mining_reward.mcb_balance = reward
                db_session.add(immature_mining_reward)

                # update immature_mining_reward_summaries table, simulated materialized view
                if holder not in immature_summary_dict.keys():
                    immature_summary_item = ImmatureMiningRewardSummary()
                    immature_summary_item.mining_round = self._mining_round
                    immature_summary_item.pool_name = pool_name
                    immature_summary_item.holder = holder
                    immature_summary_item.mcb_balance = reward
                else:
                    immature_summary_item = immature_summary_dict[holder]
                    immature_summary_item.mcb_balance += reward
                db_session.add(immature_summary_item)


    def _get_holder_mcb_balance(self, db_session):
        holder_mcb_balance_dict = {}
        mcb_token_items = self._get_share_token_items(self._mcb_token_address, db_session)
        for item in mcb_token_items:
            holder_mcb_balance_dict[item.holder] = item.balance
        
        uniswap_pool_total_mcb_balance = holder_mcb_balance_dict.get(self._uniswap_mcb_share_token_address)
        uniswap_share_items = self._get_share_token_items(self._uniswap_mcb_share_token_address, db_session)
        uniswap_total_share_token_amount = self._get_total_share_token_amount(self._uniswap_mcb_share_token_address, db_session)
        if uniswap_total_share_token_amount != Decimal(0):            
            for item in uniswap_share_items:
                holder = item.holder
                holder_mcb_amount = uniswap_pool_total_mcb_balance * item.balance / uniswap_total_share_token_amount
                if holder not in holder_mcb_balance_dict.keys():
                    holder_mcb_balance_dict[holder] = holder_mcb_amount
                else:
                    holder_mcb_balance_dict[holder] += holder_mcb_amount
        return holder_mcb_balance_dict

    def _get_holder_reward_weight(self, block_number, pool_value_info, db_session):
        M = Decimal(2)
        N = Decimal(30)
        holder_amms_weight_dict = {}
        holder_amms_reward_dict = {}
        amms_total_reward = Decimal(0)
        holder_mcb_balance_dict = self._get_holder_mcb_balance(db_session)

        for pool_name in pool_value_info.keys():
            total_share_token_amount = pool_value_info[pool_name]['total_share_token_amount']
            if total_share_token_amount == 0:
                continue
            share_token_items = pool_value_info[pool_name]['share_token_items']
            pool_type = pool_value_info[pool_name]['pool_type']
            pool_reward = pool_value_info[pool_name]['pool_reward']
            amms_total_reward += pool_reward

            for item in share_token_items:
                holder = item.holder
                if item.balance == Decimal(0):
                    continue
                # amm pool, use effective share after xia_rebalance_hard_fork block number
                if pool_type == 'AMM' and block_number >= self._xia_rebalance_hard_fork_block_number:
                    total_effective_share_amount = pool_value_info[pool_name]['total_effective_share_amount']
                    holder_effective_share_amount = pool_value_info[pool_name]['effective_share_dict'].get(holder, Decimal(0))
                    wad_reward = pool_reward * Wad.from_number(holder_effective_share_amount) / Wad.from_number(total_effective_share_amount)
                    reward = Decimal(str(wad_reward))
                    if holder not in holder_amms_reward_dict:
                        holder_amms_reward_dict[holder] = reward
                    else:
                        holder_amms_reward_dict[holder] += reward
        
        for holder, reward in holder_amms_reward_dict.items():
            total_holder_reward_weight = Decimal(0)
            holder_reward_percent = reward / amms_total_reward
            holder_mcb_balance = holder_mcb_balance_dict.get(holder, Decimal(0))
            mcb_weight = holder_mcb_balance / ( reward * N)
            if mcb_weight < 1:
                reward_factor = mcb_weight + M
            else:
                reward_factor = Decimal(1) + M
            total_holder_reward_weight += holder_reward_percent * reward_factor

        for holder, reward in holder_amms_reward_dict.items():
            total_holder_reward_weight = Decimal(0)
            holder_mcb_balance = holder_mcb_balance_dict.get(holder, Decimal(0))
            mcb_weight = holder_mcb_balance / ( reward * N)
            if mcb_weight < 1:
                reward_factor = mcb_weight + M
            else:
                reward_factor = Decimal(1) + M
            holder_amms_weight_dict[holder] = reward_factor / total_holder_reward_weight

        return holder_amms_weight_dict

    def _calculate_pools_reward_from_zhou(self, block_number, pool_info, pool_reward_percent, db_session):
        pool_value_info = self._get_pool_value_info(block_number, pool_info, pool_reward_percent, db_session)
        self._logger.info(f'sync mining reward, block_number:{block_number}, pools:{",".join(pool_info.keys())}')
        
        holder_weight_dict = {}
        if block_number >= self._zhou_begin_block_number: 
            holder_weight_dict = self._get_holder_reward_weight(block_number, pool_value_info, db_session)

        for pool_name in pool_value_info.keys():
            # get all immature summary items of pool_name
            immature_summary_dict = {}
            immature_summary_items = db_session.query(ImmatureMiningRewardSummary)\
                .filter(ImmatureMiningRewardSummary.mining_round == self._mining_round)\
                .filter(ImmatureMiningRewardSummary.pool_name == pool_name)\
                .all()
            for item in immature_summary_items:
                immature_summary_dict[item.holder] = item    

            total_share_token_amount = pool_value_info[pool_name]['total_share_token_amount']
            if total_share_token_amount == 0:
                self._logger.warning(f'opps, pool:{pool_name}, share_token total amount is zero, skip it!')
                continue

            share_token_items = pool_value_info[pool_name]['share_token_items']
            pool_type = pool_value_info[pool_name]['pool_type']
            pool_reward = pool_value_info[pool_name]['pool_reward']

            for item in share_token_items:
                holder = item.holder
                if item.balance == Decimal(0):
                    continue
                # amm pool, use effective share after xia_rebalance_hard_fork block number
                if pool_type == 'AMM' and block_number >= self._xia_rebalance_hard_fork_block_number:
                    holder_weight = holder_weight_dict.get(holder, Decimal(1))
                    total_effective_share_amount = pool_value_info[pool_name]['total_effective_share_amount']
                    holder_effective_share_amount = pool_value_info[pool_name]['effective_share_dict'].get(holder, Decimal(0))
                    wad_reward = Wad.from_number(holder_weight) * pool_reward * Wad.from_number(holder_effective_share_amount) / Wad.from_number(total_effective_share_amount)
                    reward = Decimal(str(wad_reward))
                else:
                    holder_share_token_amount = Decimal(item.balance)
                    wad_reward = pool_reward * Wad.from_number(holder_share_token_amount) / Wad.from_number(total_share_token_amount)
                    reward = Decimal(str(wad_reward))

                immature_mining_reward = ImmatureMiningReward()
                immature_mining_reward.block_number = block_number
                immature_mining_reward.pool_name = pool_name
                immature_mining_reward.mining_round = self._mining_round
                immature_mining_reward.holder = holder
                immature_mining_reward.mcb_balance = reward
                db_session.add(immature_mining_reward)

                # update immature_mining_reward_summaries table, simulated materialized view
                if holder not in immature_summary_dict.keys():
                    immature_summary_item = ImmatureMiningRewardSummary()
                    immature_summary_item.mining_round = self._mining_round
                    immature_summary_item.pool_name = pool_name
                    immature_summary_item.holder = holder
                    immature_summary_item.mcb_balance = reward
                else:
                    immature_summary_item = immature_summary_dict[holder]
                    immature_summary_item.mcb_balance += reward
                db_session.add(immature_summary_item)

    def sync(self, watcher_id, block_number, block_hash, db_session):
        """Sync data"""
        if block_number < self._begin_block or block_number > self._end_block:
            self._logger.info(f'reward of mining_round: {self._mining_round}, block_number {block_number} not in mining window!')
            return

        if self._mining_round == 'XIA': 
            pool_info = {}
            pool_info['ETH_PERP'] = config.ETH_PERP_SHARE_TOKEN_ADDRESS.lower()
            amms_total_reward_percent = 1
            pool_reward_percent = amms_total_reward_percent  
            self._calculate_pools_reward(block_number, pool_info, pool_reward_percent, db_session)
        elif self._mining_round == 'SHANG':
            # amms_reward_percent = 0.75
            # pool_name = 'ETH_PERP'
            # pool_share_token_address = self._eth_perp_share_token_address
            # pool_reward_percent = amms_reward_percent
            # self._calculate_pool_reward(block_number, pool_name, pool_share_token_address, pool_reward_percent, db_session)
            
            # pool_name = 'UNISWAP_MCB_ETH'
            # pool_share_token_address = self._uniswap_mcb_share_token_address
            # uniswap_mcb_reward_percent = 0.25
            # pool_reward_percent = uniswap_mcb_reward_percent
            # self._calculate_pool_reward(block_number, pool_name, pool_share_token_address, pool_reward_percent, db_session)
            
            # AMM pools
            pool_info = {}
            pool_info['ETH_PERP'] = config.ETH_PERP_SHARE_TOKEN_ADDRESS.lower()
            if block_number >= self._shang_reward_link_pool_block_number:
                # add amm link pool reward
                pool_info['LINK_PERP'] = config.LINK_PERP_SHARE_TOKEN_ADDRESS.lower()
            if block_number >= self._shang_reward_btc_pool_block_number:
                # add amm btc pool reward
                pool_info['BTC_PERP'] = config.BTC_PERP_SHARE_TOKEN_ADDRESS.lower()
            amms_total_reward_percent = 0.75
            pool_reward_percent = amms_total_reward_percent            
            self._calculate_pools_reward(block_number, pool_info, pool_reward_percent, db_session)

            # UNISWAP pool
            pool_info = {}
            pool_info['UNISWAP_MCB_ETH'] = config.UNISWAP_MCB_ETH_SHARE_TOKEN_ADDRESS.lower()
            uniswap_mcb_reward_percent = 0.25
            pool_reward_percent = uniswap_mcb_reward_percent
            self._calculate_pools_reward(block_number, pool_info, pool_reward_percent, db_session)
        elif self._mining_round == 'ZHOU':
            # AMM pools
            pool_info = {}
            pool_info['ETH_PERP'] = config.ETH_PERP_SHARE_TOKEN_ADDRESS.lower()
            pool_info['LINK_PERP'] = config.LINK_PERP_SHARE_TOKEN_ADDRESS.lower()
            if block_number >= self._shang_reward_btc_pool_block_number:
                # add amm btc pool reward
                pool_info['BTC_PERP'] = config.BTC_PERP_SHARE_TOKEN_ADDRESS.lower()
            amms_total_reward_percent = 0.75
            pool_reward_percent = amms_total_reward_percent            
            self._calculate_pools_reward(block_number, pool_info, pool_reward_percent, db_session)

            # UNISWAP pool
            pool_info = {}
            pool_info['UNISWAP_MCB_ETH'] = config.UNISWAP_MCB_ETH_SHARE_TOKEN_ADDRESS.lower()
            uniswap_mcb_reward_percent = 0.25
            pool_reward_percent = uniswap_mcb_reward_percent
            self._calculate_pools_reward(block_number, pool_info, pool_reward_percent, db_session)

    def rollback(self, watcher_id, block_number, db_session):
        """delete data after block_number"""
        self._logger.info(f'rollback immature_mining_reward block_number back to {block_number}')
        items = db_session.query(ImmatureMiningReward)\
            .filter(ImmatureMiningReward.block_number > block_number)\
            .filter(ImmatureMiningReward.mining_round == self._mining_round)\
            .group_by(ImmatureMiningReward.pool_name, ImmatureMiningReward.holder, ImmatureMiningReward.mining_round)\
            .with_entities(
                ImmatureMiningReward.pool_name,
                ImmatureMiningReward.holder,
                ImmatureMiningReward.mining_round,
                func.sum(ImmatureMiningReward.mcb_balance).label('mcb_balance')
        ).all()
        for item in items:
            # update immature_mining_reward_summaries table
            summary_item = db_session.query(ImmatureMiningRewardSummary)\
                .filter(ImmatureMiningRewardSummary.holder == item.holder)\
                .filter(ImmatureMiningRewardSummary.pool_name == item.pool_name)\
                .filter(ImmatureMiningRewardSummary.mining_round == item.mining_round)\
                    .first()
            if summary_item is None:
                self._logger.error(f'opps, update immature_mining_reward_summaries error, can not find item:{item}')
            else:
                summary_item.mcb_balance -= item.mcb_balance
                db_session.add(summary_item)

        db_session.query(ImmatureMiningReward)\
            .filter(ImmatureMiningReward.block_number > block_number)\
            .filter(ImmatureMiningReward.mining_round == self._mining_round)\
                .delete(synchronize_session=False)