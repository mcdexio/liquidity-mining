import argparse
import time

from sqlalchemy.orm import sessionmaker
from web3 import HTTPProvider, Web3

import config
from model.db import db_engine
from model.orm import MiningRound
from syncer.erc20 import ERC20Tracer
from syncer.mature import MatureChecker
from syncer.rewards import ShareMining
from watcher import Watcher

MINING_ROUND = 'XIA'

def create_watcher():
    web3 = Web3(HTTPProvider(endpoint_uri=config.ETH_RPC_URL,
                             request_kwargs={"timeout": config.ETH_RPC_TIMEOUT}))

    Session = sessionmaker(bind=db_engine)
    session = Session()
    mining_round = session.query(MiningRound).filter(
        MiningRound.round == MINING_ROUND).one()
    session.rollback()

    share_token_tracer = ERC20Tracer(config.XIA_SHARE_TOKEN_ADDRESS, web3)
    miner = ShareMining(mining_round.begin_block, mining_round.end_block,
                        mining_round.reward_per_block, config.XIA_SHARE_TOKEN_ADDRESS, MINING_ROUND)
    mature_checker = MatureChecker(
        config.MATURE_CONFIRM, config.MATURE_CHECKPOINT_INTERVAL, MINING_ROUND)

    syncers = [share_token_tracer, miner, mature_checker]
    return Watcher(mining_round.watcher_id, syncers, web3, db_engine)


def serv():
    watcher = create_watcher()
    while True:
        synced = watcher.sync()
        if not synced:
            time.sleep(3)


def rollback(synced_block_number: int):
    watcher = create_watcher()
    watcher.rollback(synced_block_number)


def main():
    parser = argparse.ArgumentParser(
        description='MCDEX Liquidity mining: Round XIA')

    parser.add_argument('--rollback', dest='rollback', metavar='SYNCED_BLOCK', action='store', type=int,
                        help='rollback the watcher to SYNCED_BLOCK')

    args = parser.parse_args()
    if args.rollback is not None:
        rollback(args.rollback)
    else:
        serv()


if __name__ == "__main__":
    main()
