
from sqlalchemy.orm import sessionmaker


class SyncerInterface:
    """A pure interface for the watcher's plugins.
    """
    def sync(watcher_id, block_number, block_hash, db_session):
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

    def rollback(watcher_id, block_number, db_session):
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


class Watcher:
    """
        A Watcher watches and syncs with the blockchain's state.
        The Watcher deals with the rollback of the blockchain, providing a realtime
        data of the blockchain.
    """

    def __init__(self, watcher_id, syncers):
        """initializer of Watcher

        Args:
            watcher_id
            syncers (list): a list of SyncerInterface.
        """
        self._watcher_id = watcher_id
        self._syncers = syncers


    def sync(self):
        """
        Sync with the blockchain. The watcher may sync forward or rollback by comparing its block hash with
        the data from node's API
        """

    def rollback(self, block_number):
        pass

