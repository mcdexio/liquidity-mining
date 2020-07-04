from sqlalchemy import (DECIMAL, TIMESTAMP, Column, ForeignKey, Integer,
                        String, Table)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

from .db import db_engine

Base = declarative_base()


class MiningRound(Base):
    __tablename__ = 'mining_rounds'

    round = Column(String, primary_key=True)
    begin_block_number = Column(Integer)
    end_block_number = Column(Integer)
    watcher_id = Column(Integer)


class Watcher(Base):
    __tablename__ = "watchers"

    id = Column(Integer, primary_key=True)
    initial_block_number = Column(Integer)
    synced_block_number = Column(Integer)


class WatcherBlock(Base):
    __tablename__ = 'watcher_blocks'

    watcher_id = Column(Integer, primary_key=True)
    block_number = Column(Integer, primary_key=True)
    block_hash = Column(String)


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
    __table__ = Table("token_balances", Base.metadata,
                      autoload=True, autoload_with=db_engine)
    __mapper_args__ = {
        'primary_key': [__table__.c.token, __table__.c.holder]
    }
#    watcher_id = Column(Integer)
#    token = Column(String)
#    holder = Column(String)
#    balance = Column(DECIMAL(78, 18))


class ImmatureMiningReward(Base):
    __tablename__ = "immature_mining_rewards"

    block_number = Column(Integer, primary_key=True)
    mining_round = Column(String, primary_key=True)
    holder = Column(String, primary_key=True)
    mcb_balance = Column(DECIMAL(78, 18))


class ImmatureMiningRewardSummary(Base):
    __table__ = Table("immature_mining_reward_summaries",
                      Base.metadata, autoload=True, autoload_with=db_engine)
    __mapper_args__ = {
        'primary_key': [__table__.c.mining_round, __table__.c.holder]
    }

    # mining_round = Column(String)
    # holder = Column(String)
    # mcb_balance = Column(DECIMAL(78, 18))


class MatureMiningReward(Base):
    __tablename__ = "mature_mining_reward"

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
    INIT = "INIT"
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    CANCELED = "CANCELED"

    id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_nonce = Column(Integer)
    transaction_data = Column(String)
    transaction_hash = Column(String, nullable=True)
    status = Column(String, nullable=True)

    payments = relationship("Payment")

    def transaction_status(self, code):
        status = [self.INIT, self.PENDING,
                  self.SUCCESS, self.FAILED, self.CANCELED]
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
    round_payments = relationship('RoundPayment')


class PaymentSummary(Base):
    __table__ = Table("payment_summaries", Base.metadata,
                      autoload=True, autoload_with=db_engine)
    __mapper_args__ = {
        'primary_key': [__table__.c.holder]
    }

    # holder = Column(String)
    # paid_amount = Column(DECIMAL(78, 18))


class RoundPayment(Base):
    __tablename__ = "round_payments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    mining_round = Column(String)
    holder = Column(String)
    amount = Column(DECIMAL(78, 18))
    payment_id = Column(Integer, ForeignKey('payments.id'))
    payment = relationship("Payment", back_populates="round_payments")


class RoundPaymentSummary(Base):
    __table__ = Table("round_payment_summaries", Base.metadata,
                      autoload=True, autoload_with=db_engine)
    __mapper_args__ = {
        'primary_key': [__table__.c.mining_round, __table__.c.holder]
    }

    # mining_round = Column(String)
    # holder = Column(String)
    # paid_amount = Column(DECIMAL(78, 18))
