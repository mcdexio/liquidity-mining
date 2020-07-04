import time
from web3 import Web3
from watcher import Watcher

from model.db import db_engine

WATCHER_ID = 1

def sync_server():
    web3 = Web3(Web3.HTTPProvider('http://server10.jy.mcarlo.com:8645'))
    watcher = Watcher(WATCHER_ID, [], web3, db_engine)

    watcher.sync()


sync_server()
