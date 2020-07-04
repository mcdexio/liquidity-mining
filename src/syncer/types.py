

class SyncerInterface:
    """A pure interface for the watcher's plugins.
    """

    def sync(self, watcher_id: int, block_number: int, block_hash: str, db_session):
        """sync with a specific block

        The Watcher syncs data in order. Watcher is responsible for maintaining the state of the database sesion.
        The syncer MUST NOT commit/abort the session.

        Args:
            watcher_id (int): the id of the watcher
            block_number (int): the block number
            block_hash (string): the block hash
            db_session (orm.Session): the database session for the sync
        """
        pass

    def rollback(self, watcher_id:int, block_number:int, db_session):
        """rollback the data of some block

        The Syncer should delete all data after the `block_number`.
        Watcher is responsible for maintaining the state of the database sesion.The syncer MUST NOT commit/abort 
        the session.

        Args:
            watcher_id (int): the id of the watcher
            block_number (int): the block number of the data need to rollback to
            db_session (orm.Session): the database session for the sync
        """
        pass
