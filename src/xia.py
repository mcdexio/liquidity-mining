import time
from web3 import Web3
from watcher import Watcher

from model.orm import engine

WATCHER_ID = 1

def sync_server():
    web3 = Web3(Web3.HTTPProvider('http://server10.jy.mcarlo.com:8645'))
    watcher = Watcher(WATCHER_ID, [], web3, engine)

    watcher.sync()


sync_server()
