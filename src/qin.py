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

MINING_ROUND = 'QIN'

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

    # mcb token
    mcb_token_tracer = ERC20Tracer(config.MCB_TOKEN_ADDRESS, web3, mining_round.end_block_number)

    # link perp contract
    link_perp_share_token_tracer = ERC20Tracer(config.LINK_PERP_SHARE_TOKEN_ADDRESS, web3, mining_round.end_block_number)
    link_perp_position_tracer = PositionTracer(config.LINK_PERPETUAL_ADDRESS, config.LINK_PERPETUAL_INVERSE, config.LINK_PERPETUAL_POSITION_TOPIC, web3, mining_round.end_block_number)

    # comp perp contract
    comp_perp_share_token_tracer = ERC20Tracer(config.COMP_PERP_SHARE_TOKEN_ADDRESS, web3, mining_round.end_block_number)
    comp_perp_position_tracer = PositionTracer(config.COMP_PERPETUAL_ADDRESS, config.COMP_PERPETUAL_INVERSE, config.COMP_PERPETUAL_POSITION_TOPIC, web3, mining_round.end_block_number)

    # lend perp contract
    lend_perp_share_token_tracer = ERC20Tracer(config.LEND_PERP_SHARE_TOKEN_ADDRESS, web3, mining_round.end_block_number)
    lend_perp_position_tracer = PositionTracer(config.LEND_PERPETUAL_ADDRESS, config.LEND_PERPETUAL_INVERSE, config.LEND_PERPETUAL_POSITION_TOPIC, web3, mining_round.end_block_number)

    # snx perp contract
    snx_perp_share_token_tracer = ERC20Tracer(config.SNX_PERP_SHARE_TOKEN_ADDRESS, web3, mining_round.end_block_number)
    snx_perp_position_tracer = PositionTracer(config.SNX_PERPETUAL_ADDRESS, config.SNX_PERPETUAL_INVERSE, config.SNX_PERPETUAL_POSITION_TOPIC, web3, mining_round.end_block_number)

    # btc perp contract
    btc_perp_share_token_tracer = ERC20Tracer(config.BTC_PERP_SHARE_TOKEN_ADDRESS, web3, mining_round.end_block_number)
    chainlink_btc_price_tracer = LinkPriceTracer(config.CHAINLINK_BTC_USD_ADDRESS, web3)
    btc_perp_position_tracer = PositionTracer(config.BTC_PERPETUAL_ADDRESS, config.BTC_PERPETUAL_INVERSE, config.BTC_PERPETUAL_POSITION_TOPIC, web3, mining_round.end_block_number)

    miner = ShareMining(mining_round.begin_block_number, mining_round.end_block_number, mining_round.release_per_block,
                         MINING_ROUND)
    mature_checker = MatureChecker(
        config.MATURE_CONFIRM, config.MATURE_CHECKPOINT_INTERVAL, MINING_ROUND)

    syncers = [eth_perp_share_token_tracer, eth_perp_position_tracer, uniswap_mcb_share_token_tracer,
            mcb_token_tracer, link_perp_share_token_tracer, link_perp_position_tracer,
            comp_perp_share_token_tracer, comp_perp_position_tracer,
            lend_perp_share_token_tracer, lend_perp_position_tracer,
            snx_perp_share_token_tracer, snx_perp_position_tracer,
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

def rollback(synced_block_number: int):
    watcher = create_watcher()
    watcher.rollback(synced_block_number)

def main():
    parser = argparse.ArgumentParser(
        description='MCDEX Liquidity mining: Round QIN')

    parser.add_argument('--rollback', dest='rollback', metavar='SYNCED_BLOCK', action='store', type=int,
                        help='rollback the watcher to SYNCED_BLOCK')

    args = parser.parse_args()
    if args.rollback is not None:
        rollback(args.rollback)
    else:
        serv()

if __name__ == "__main__":
    main()
