import argparse
import time
import logging

from sqlalchemy.orm import sessionmaker
from web3 import HTTPProvider, Web3
from web3.middleware import construct_sign_and_send_raw_middleware, geth_poa_middleware

import config
from model.db import db_engine
from model.orm import MiningRound
from syncer.erc20 import ERC20Tracer
from syncer.position import PositionTracer
from syncer.mature import MatureChecker
from syncer.rewards import ShareMining
from watcher import Watcher

MINING_ROUND = 'SHANG'

def create_watcher():
    web3 = Web3(HTTPProvider(endpoint_uri=config.ETH_RPC_URL,
                             request_kwargs={"timeout": config.ETH_RPC_TIMEOUT}))
    web3.middleware_onion.inject(geth_poa_middleware, layer=0)
    Session = sessionmaker(bind=db_engine)
    session = Session()
    mining_round = session.query(MiningRound).filter(
        MiningRound.round == MINING_ROUND).one()
    session.rollback()

    eth_perp_share_token_tracer = ERC20Tracer(config.SHANG_ETH_PERP_SHARE_TOKEN_ADDRESS, web3, mining_round.end_block_number)
    uniswap_mcb_share_token_tracer = ERC20Tracer(config.UNISWAP_MCB_ETH_SHARE_TOKEN_ADDRESS, web3, mining_round.end_block_number)
    position_tracer = PositionTracer(config.PERPETUAL_ADDRESS, config.PERPETUAL_INVERSE, web3, mining_round.end_block_number)
    miner = ShareMining(mining_round.begin_block_number, mining_round.end_block_number, mining_round.release_per_block,
                         MINING_ROUND, config.SHANG_ETH_PERP_SHARE_TOKEN_ADDRESS, config.UNISWAP_MCB_ETH_SHARE_TOKEN_ADDRESS)
    mature_checker = MatureChecker(
        config.MATURE_CONFIRM, config.MATURE_CHECKPOINT_INTERVAL, MINING_ROUND)

    syncers = [eth_perp_share_token_tracer, uniswap_mcb_share_token_tracer, position_tracer, miner, mature_checker]
    return Watcher(mining_round.watcher_id, syncers, web3, db_engine, mining_round.end_block_number)

def serv():
    watcher = create_watcher()
    while True:
        synced = watcher.sync()
        if synced < 0:
            time.sleep(config.WATCHER_CHECK_INTERVAL)
        elif synced == 0:
            return

def sync_extradata(extra_data: str, end_block_number: int, watcher_id: int,  share_token: str):
    logger = logging.getLogger()
    logger.info(f'start sync extra_data:{extra_data},  end_block_number:{end_block_number},  watcher_id:{watcher_id},  share_token:{share_token}')

    web3 = Web3(HTTPProvider(endpoint_uri=config.ETH_RPC_URL,
                             request_kwargs={"timeout": config.ETH_RPC_TIMEOUT}))
    web3.middleware_onion.inject(geth_poa_middleware, layer=0)

    share_token_tracer = ERC20Tracer(share_token, web3, end_block_number)
    syncers = [share_token_tracer]
    watcher = Watcher(watcher_id, syncers, web3, db_engine, end_block_number)
    while True:
        synced = watcher.sync()
        if synced < 0:
            time.sleep(config.WATCHER_CHECK_INTERVAL)
        elif synced == 0:
            return

def rollback(synced_block_number: int):
    watcher = create_watcher()
    watcher.rollback(synced_block_number)

def main():
    parser = argparse.ArgumentParser(
        description='MCDEX Liquidity mining: Round SHANG')

    parser.add_argument('--extradata', dest='extradata', metavar='EXTRA_DATA', action='store', type=str, default='uniswap_mcb_share',
                        help='extra new data for calculate liquidity mining reward')
    parser.add_argument('--rollback', dest='rollback', metavar='SYNCED_BLOCK', action='store', type=int,
                        help='rollback the watcher to SYNCED_BLOCK')

    args = parser.parse_args()
    if args.rollback is not None:
        rollback(args.rollback)
    elif args.extradata is not None:
        if args.extradata == 'uniswap_mcb_share':
            # calculate shang reward need sync uniswap mcb share event
            end_block_number = 10624999  #xia end number
            watcher_id = 2
            share_token = config.UNISWAP_MCB_ETH_SHARE_TOKEN_ADDRESS
            sync_extradata(args.extradata, end_block_number, watcher_id, share_token)
    else:
        serv()

if __name__ == "__main__":
    main()
