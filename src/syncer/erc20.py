from .syncer import SyncerInterface

class ERC20Tracer(SyncerInterface):
    """Sync the balance of ERC20 tokens by parsing the ERC20 events"""

    def __init__(self, token_address):
        self._token_address = token_address
        

    def sync(self, watcher_id, block_number, block_hash, db_session):
        """Sync data"""
        pass


    def rollback(self, watcher_id, block_number, db_session):
        """delete data after block_number"""
        pass





    

