from sqlalchemy import (DECIMAL, TIMESTAMP, Column, ForeignKey, Integer,
                        String, Table)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

from .db import db_engine

Base = declarative_base()


class Watcher(Base):
    __tablename__ = "watchers"

    id = Column(Integer, primary_key=True)
    initial_block_number = Column(Integer)
    synced_block_number = Column(Integer)

    mining_rounds = relationship("MiningRound")
    watcher_blocks = relationship("WatcherBlock")


class MiningRound(Base):
    __tablename__ = 'mining_rounds'

    round = Column(String, primary_key=True)
    begin_block_number = Column(Integer)
    end_block_number = Column(Integer)
    release_per_block = Column(Integer)
    supply = Column(Integer)
    watcher_id = Column(Integer, ForeignKey('watchers.id'))


class WatcherBlock(Base):
    __tablename__ = 'watcher_blocks'

    watcher_id = Column(Integer, primary_key=True)
    block_number = Column(Integer, primary_key=True)
    block_hash = Column(String)
    watcher_id = Column(Integer, ForeignKey('watchers.id'))

    watcher = relationship(
        "Watcher", back_populates="watcher_blocks")


class TokenEvent(Base):
    __tablename__ = "token_events"

    block_number = Column(Integer, primary_key=True)
    transaction_hash = Column(String, primary_key=True)
    event_index = Column(Integer, primary_key=True)
    token = Column(String, primary_key=True)
    holder = Column(String, primary_key=True)
    amount = Column(DECIMAL(78, 18))
    watcher_id = Column(Integer)


class TokenBalance(Base):
    __tablename__ = "token_balances"

    token = Column(String, primary_key=True)
    holder = Column(String, primary_key=True)
    balance = Column(DECIMAL(78, 18))
    watcher_id = Column(Integer)



class ImmatureMiningReward(Base):
    __tablename__ = "immature_mining_rewards"

    block_number = Column(Integer, primary_key=True)
    mining_round = Column(String, primary_key=True)
    holder = Column(String, primary_key=True)
    mcb_balance = Column(DECIMAL(78, 18))


class ImmatureMiningRewardSummary(Base):
    __tablename__ = "immature_mining_reward_summaries"

    mining_round = Column(String, primary_key=True)
    holder = Column(String, primary_key=True)
    mcb_balance = Column(DECIMAL(78, 18))


class MatureMiningReward(Base):
    __tablename__ = "mature_mining_rewards"

    mining_round = Column(String, primary_key=True)
    holder = Column(String, primary_key=True)
    block_number = Column(Integer)
    mcb_balance = Column(DECIMAL(78, 18))


class MatureMiningRewardCheckpoint(Base):
    __tablename__ = "mature_mining_reward_checkpoints"
    mining_round = Column(String, primary_key=True)
    holder = Column(String, primary_key=True)
    block_number = Column(Integer, primary_key=True)
    mcb_balance = Column(DECIMAL(78, 18))


class PaymentTransaction(Base):
    __tablename__ = "payment_transactions"
    FAILED = "FAILED"
    SUCCESS = "SUCCESS"
    PENDING = "PENDING"

    id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_data = Column(String)
    transaction_hash = Column(String, nullable=True)
    status = Column(String, nullable=True)

    payments = relationship("Payment")
    round_payments = relationship('RoundPayment')

    # 0: failed, 1: success, 2: pending
    def transaction_status(self, code):
        status = [self.FAILED, self.SUCCESS, self.PENDING]
        self.status = status[code]


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    holder = Column(String)
    amount = Column(DECIMAL(78, 18))
    pay_time = Column(TIMESTAMP)
    transaction_id = Column(Integer, ForeignKey('payment_transactions.id'))
    payment_transaction = relationship(
        "PaymentTransaction", back_populates="payments")


class PaymentSummary(Base):
    __tablename__ = "payment_summaries"

    holder = Column(String, primary_key=True)
    paid_amount = Column(DECIMAL(78, 18))


class RoundPayment(Base):
    __tablename__ = "round_payments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    mining_round = Column(String)
    holder = Column(String)
    amount = Column(DECIMAL(78, 18))
    transaction_id = Column(Integer, ForeignKey('payment_transactions.id'))
    payment_transaction = relationship(
        "PaymentTransaction", back_populates="round_payments")


class RoundPaymentSummary(Base):
    __tablename__ = "round_payment_summaries"

    mining_round = Column(String, primary_key=True)
    holder = Column(String, primary_key=True)
    paid_amount = Column(DECIMAL(78, 18))


class PerpShareAmmProxyMap(Base):
    __tablename__ = "perp_share_amm_proxy_maps"

    perp_addr = Column(String, primary_key=True)
    share_addr = Column(String, primary_key=True)
    amm_addr = Column(String, primary_key=True)
    proxy_addr = Column(String, primary_key=True)