
from web3 import Web3
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker


class Watcher:
    """
        A Watcher watches and syncs with the blockchain's state.
        The Watcher deals with the rollback of the blockchain, providing a realtime
        data of the blockchain.
    """

    def __init__(self, watcher_id: int, syncers: list, web3: Web3, dbEngine: Engine):
        """initializer of Watcher

        Args:
            watcher_id
            syncers (list): a list of SyncerInterface.
        """
        self._watcher_id = watcher_id
        self._syncers = syncers
        self._web3 = web3
        self._Session = sessionmaker(bind=dbEngine)

    def sync(self):
        """
        Sync with the blockchain. The watcher may sync forward or rollback by comparing its block hash with
        the data from node's API
        """

    def rollback(self, block_number):
        pass
