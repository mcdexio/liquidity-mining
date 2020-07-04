from sqlalchemy import func
from web3 import Web3

from contract.erc20 import ERC20Token
from lib.address import Address
from lib.wad import Wad
from model.orm import ImmatureMiningReward, TokenEvent
from watcher import Watcher

from .types import SyncerInterface


class ShareMining(SyncerInterface):
    """Mining according to the balance of the share token.

    reward_i = reward_per_block * (share_token_balance_i / (share_token_total_supply) )
    """

    def __init__(self, begin_block, end_block, reward_per_block, share_token_address, mining_round):
        self.begin_block = begin_block
        self.end_block = end_block
        self.reward_per_block = reward_per_block
        self.share_token_address = share_token_address.lower()
        self.mining_round = mining_round

    def sync(self, watcher_id, block_number, block_hash, db_session):
        """Sync data"""
        result = db_session.query(TokenEvent)\
            .filter(TokenEvent.token == self.share_token_address)\
            .filter(TokenEvent.block_number <= block_number)\
            .with_entities(
                func.sum(TokenEvent.amount).label('amount')
        ).first()
        total_share_token_amount = Wad(result.amount)

        items = db_session.query(TokenEvent)\
            .filter(TokenEvent.token == self.share_token_address)\
            .filter(TokenEvent.block_number <= block_number)\
            .group_by(TokenEvent.holder)\
            .with_entities(
                TokenEvent.holder,
                func.sum(TokenEvent.amount).label('amount')
        )\
            .all()
        for item in items:
            holder = item.holder
            holder_share_token_amount = Wad(item.amount)
            reward = self.reward_per_block * holder_share_token_amount / total_share_token_amount

            immature_mining_reward = ImmatureMiningReward()
            immature_mining_reward.block_number = block_number
            immature_mining_reward.mining_round = self.mining_round
            immature_mining_reward.holder = holder
            immature_mining_reward.mcb_balance = reward
            db_session.add(immature_mining_reward)

    def rollback(self, watcher_id, block_number, db_session):
        """delete data after block_number"""
        db_session.query(ImmatureMiningReward).filter(
            ImmatureMiningReward.block_number >= block_number).delete()
