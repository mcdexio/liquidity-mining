from decimal import Decimal

from sqlalchemy import func, select, union_all
from sqlalchemy.orm import joinedload, sessionmaker

from model.db import db_engine
from model.orm import (ImmatureMiningRewardSummary, MatureMiningReward,
                       RoundPaymentSummary, Watcher)


def _get_fields(obj, ignores=[]):
    fields = {}
    for field in [x for x in dir(obj) if not x.startswith('_') and x != 'metadata' and x not in ignores]:
        data = obj.__getattribute__(field)
        fields[field] = data
    return fields


def get_watchers():
    """get watcher inforamtion

    Returns:
        List[model.orm.Watcher]: wathers joined with its rounds. 
    """
    Session = sessionmaker(bind=db_engine)
    session = Session()
    watchers = session.query(Watcher).options(
        joinedload(Watcher.mining_rounds)).all()
    result = []
    for w in watchers:
        result.append(_get_fields(w))
        result[-1]['mining_rounds'] = [_get_fields(
            r, ['watcher', 'watcher_id']) for r in w.mining_rounds]

    return result


def get_user_rewards(user_address: str):
    """get the reward balances of user

    Args:
        user_address (str): the ETH address of the user

    Returns:
        Dict[round][balance]: balances info
    """
    Session = sessionmaker(bind=db_engine)
    session = Session()
    holder = user_address.lower()
    q1 = session.query(ImmatureMiningRewardSummary)\
        .filter(ImmatureMiningRewardSummary.holder == holder)\
        .group_by(ImmatureMiningRewardSummary.mining_round)\
        .with_entities(
            ImmatureMiningRewardSummary.mining_round.label('mining_round'),
            func.sum(ImmatureMiningRewardSummary.mcb_balance).label('immature_balance')).all()

    q2 = session.query(MatureMiningReward)\
        .filter(MatureMiningReward.holder == holder)\
        .with_entities(
            MatureMiningReward.mining_round.label('mining_round'),
            MatureMiningReward.mcb_balance.label('mature_balance')).all()

    q3 = session.query(RoundPaymentSummary)\
        .filter(RoundPaymentSummary.holder == holder)\
        .with_entities(
            RoundPaymentSummary.mining_round.label('mining_round'),
            RoundPaymentSummary.paid_amount.label('paid_amount')).all()

    rewards = {}
    for i in q1:
        if i.mining_round not in rewards:
            rewards[i.mining_round] = dict(immature_balance=Decimal(
                0), mature_balance=Decimal(0), paid_amount=Decimal(0))
        rewards[i.mining_round]['immature_balance'] = i.immature_balance
    for i in q2:
        if i.mining_round not in rewards:
            rewards[i.mining_round] = dict(immature_balance=Decimal(
                0), mature_balance=Decimal(0), paid_amount=Decimal(0))
        rewards[i.mining_round]['mature_balance'] = i.mature_balance
    for i in q3:
        if i.mining_round not in rewards:
            rewards[i.mining_round] = dict(immature_balance=Decimal(
                0), mature_balance=Decimal(0), paid_amount=Decimal(0))
        rewards[i.mining_round]['paid_amount'] = i.paid_amount

    return rewards
