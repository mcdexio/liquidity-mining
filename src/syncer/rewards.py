from .types import SyncerInterface 

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
        pass
