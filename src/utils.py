import time
import logging

from web3 import HTTPProvider, Web3
from web3.middleware import construct_sign_and_send_raw_middleware, geth_poa_middleware
from typing import List, Tuple, Dict

import config
from model.db import db_engine
from syncer.erc20 import ERC20Tracer
from watcher import Watcher



def sync_extradata(extra_data: str, end_block_number: int, watcher_id: int,  share_tokens: List[str]):
    logger = logging.getLogger()
    logger.info(f'start sync extra_data:{extra_data},  end_block_number:{end_block_number},  watcher_id:{watcher_id},  share_token:{",".join(share_tokens)}')

    web3 = Web3(HTTPProvider(endpoint_uri=config.ETH_RPC_URL,
                             request_kwargs={"timeout": config.ETH_RPC_TIMEOUT}))
    web3.middleware_onion.inject(geth_poa_middleware, layer=0)

    syncers = []
    for share_token in share_tokens:
        share_token_tracer = ERC20Tracer(share_token, web3, end_block_number)
        syncers.append(share_token_tracer)
    watcher = Watcher(watcher_id, syncers, web3, db_engine, end_block_number)
    while True:
        synced = watcher.sync()
        if synced < 0:
            time.sleep(config.WATCHER_CHECK_INTERVAL)
        elif synced == 0:
            return