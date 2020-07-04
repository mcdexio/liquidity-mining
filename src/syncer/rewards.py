from web3 import Web3

from .syncer import SyncerInterface
from orm import ImmatureMiningReward

from lib.address import Address
from lib.wad import Wad
from watcher import Watcher
from contract.ERC20Token import ERC20Token



"""
    block_number = Column(Integer, primary_key=True)
    mining_round = Column(String, primary_key=True)
    holder = Column(String, primary_key=True)
    mcb_balance = Column(DECIMAL(78, 18))

"""

class ShareMining(SyncerInterface):
    """Mining according to the balance of the share token.

    reward_i = reward_per_block * (share_token_balance_i / (share_token_total_supply) )
    """
    def __init__(self, begin_block, end_block, reward_per_block, share_token_address, round):
        
        pass

    def sync(self, watcher_id, block_number, block_hash, db_session):
        """Sync data"""
        pass


    def rollback(self, watcher_id, block_number, db_session):
        """delete data after block_number"""
        db_session.query(ImmatureMiningReward).filter(ImmatureMiningReward.block_number >= block_number).delete()
