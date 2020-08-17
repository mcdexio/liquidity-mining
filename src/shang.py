import argparse
import time
import logging

from sqlalchemy.orm import sessionmaker
from web3 import HTTPProvider, Web3
from web3.middleware import construct_sign_and_send_raw_middleware, geth_poa_middleware
from typing import List, Tuple, Dict

import config
from model.db import db_engine
from model.orm import MiningRound
from syncer.erc20 import ERC20Tracer
from syncer.chainlink import LinkPriceTracer
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

    # eth perp contract
    eth_perp_share_token_tracer = ERC20Tracer(config.ETH_PERP_SHARE_TOKEN_ADDRESS, web3, mining_round.end_block_number)
    eth_perp_position_tracer = PositionTracer(config.ETH_PERPETUAL_ADDRESS, config.ETH_PERPETUAL_INVERSE, config.ETH_PERPETUAL_POSITION_TOPIC, web3, mining_round.end_block_number)

    # uniswap contract
    uniswap_mcb_share_token_tracer = ERC20Tracer(config.UNISWAP_MCB_ETH_SHARE_TOKEN_ADDRESS, web3, mining_round.end_block_number)

    # link perp contract
    link_perp_share_token_tracer = ERC20Tracer(config.LINK_PERP_SHARE_TOKEN_ADDRESS, web3, mining_round.end_block_number)
    link_perp_position_tracer = PositionTracer(config.LINK_PERPETUAL_ADDRESS, config.LINK_PERPETUAL_INVERSE, config.LINK_PERPETUAL_POSITION_TOPIC, web3, mining_round.end_block_number)

    # btc perp contract
    btc_perp_share_token_tracer = ERC20Tracer(config.BTC_PERP_SHARE_TOKEN_ADDRESS, web3, mining_round.end_block_number)
    chainlink_btc_price_tracer = LinkPriceTracer(config.CHAINLINK_BTC_USD_ADDRESS, web3)
    btc_perp_position_tracer = PositionTracer(config.BTC_PERPETUAL_ADDRESS, config.BTC_PERPETUAL_INVERSE, config.BTC_PERPETUAL_POSITION_TOPIC, web3, mining_round.end_block_number)

    miner = ShareMining(mining_round.begin_block_number, mining_round.end_block_number, mining_round.release_per_block,
                         MINING_ROUND)
    mature_checker = MatureChecker(
        config.MATURE_CONFIRM, config.MATURE_CHECKPOINT_INTERVAL, MINING_ROUND)

    syncers = [eth_perp_share_token_tracer, eth_perp_position_tracer, uniswap_mcb_share_token_tracer,
            link_perp_share_token_tracer, link_perp_position_tracer,
            btc_perp_share_token_tracer, chainlink_btc_price_tracer, btc_perp_position_tracer,
            miner, mature_checker]

    return Watcher(mining_round.watcher_id, syncers, web3, db_engine, mining_round.end_block_number)

def serv():
    watcher = create_watcher()
    while True:
        synced = watcher.sync()
        if synced < 0:
            time.sleep(config.WATCHER_CHECK_INTERVAL)
        elif synced == 0:
            return

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
            
def sync_link_price(extra_data: str, end_block_number: int, watcher_id: int,  tokens: List[str]):
    logger = logging.getLogger()
    logger.info(f'start sync extra_data:{extra_data},  end_block_number:{end_block_number},  watcher_id:{watcher_id},  share_token:{",".join(tokens)}')

    web3 = Web3(HTTPProvider(endpoint_uri=config.ETH_RPC_URL,
                             request_kwargs={"timeout": config.ETH_RPC_TIMEOUT}))
    web3.middleware_onion.inject(geth_poa_middleware, layer=0)

    syncers = []
    for token in tokens:
        chainlink_price_tracer = LinkPriceTracer(token, web3)
        syncers.append(chainlink_price_tracer)
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

    parser.add_argument('--extradata', dest='extradata', metavar='EXTRA_DATA', action='store', type=str,
                        help='extra new data for calculate liquidity mining reward')
    parser.add_argument('--rollback', dest='rollback', metavar='SYNCED_BLOCK', action='store', type=int,
                        help='rollback the watcher to SYNCED_BLOCK')

    args = parser.parse_args()
    if args.rollback is not None:
        rollback(args.rollback)
    elif args.extradata is not None:
        # cmd tool, only use for recover out of sync data, end_block_number should be config
        if args.extradata == 'uniswap_mcb_share':
            # calculate shang reward need sync uniswap mcb share event
            end_block_number = 10624999  #xia end number
            watcher_id = 2
            share_tokens = [config.UNISWAP_MCB_ETH_SHARE_TOKEN_ADDRESS]
            sync_extradata(args.extradata, end_block_number, watcher_id, share_tokens)
        elif args.extradata == 'link_btc_perp':
            # sync link and btc share token event and position event
            end_block_number = 10624999  #shang tmp number
            watcher_id = 101
            share_tokens = [config.LINK_PERP_SHARE_TOKEN_ADDRESS, config.BTC_PERP_SHARE_TOKEN_ADDRESS]
            sync_extradata(args.extradata, end_block_number, watcher_id, share_tokens)
        elif args.extradata == 'link_price':
            # sync link price
            end_block_number = 10724999  #shang tmp number
            watcher_id = 102
            tokens = [config.CHAINLINK_BTC_USD_ADDRESS]
            sync_link_price(args.extradata, end_block_number, watcher_id, tokens)
        elif args.extradata == 'mcb_token':
            end_block_number = 10727499  #shang end number
            watcher_id = 103
            share_tokens = [config.MCB_TOKEN_ADDRESS]
            sync_extradata(args.extradata, end_block_number, watcher_id, share_tokens)
    else:
        serv()

if __name__ == "__main__":
    main()
