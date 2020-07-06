/*
 PosgreSQL tables
 */

CREATE TABLE watchers (
  id int PRIMARY KEY,
  initial_block_number int NOT NULL,
  synced_block_number int
);

CREATE TABLE watcher_blocks (
  watcher_id int,
  block_number int,
  block_hash text NOT NULL,
  PRIMARY KEY (watcher_id, block_number),
  FOREIGN KEY (watcher_id) REFERENCES watchers (id)
);

CREATE TABLE mining_rounds (
  round text PRIMARY KEY,
  begin_block_number int NOT NULL,
  end_block_number int NOT NULL,
  supply int NOT NULL,
  release_per_block int NOT NULL,
  watcher_id int NOT NULL,
  FOREIGN KEY (watcher_id) REFERENCES watchers (id)
);

CREATE TABLE token_events (
  block_number int,
  transaction_hash text,
  event_index int,
  token text NOT NULL,
  holder text NOT NULL,
  amount numeric(78, 18) NOT NULL,
  /* positive or negative */
  watcher_id int NOT NULL,
  PRIMARY KEY (block_number, transaction_hash, event_index, token, holder),
  FOREIGN KEY (watcher_id) REFERENCES watchers (id)
);

CREATE TABLE token_balances (
  token text NOT NULL,
  holder text NOT NULL,
  balance numeric(78, 18) NOT NULL,
  watcher_id int NOT NULL,
  PRIMARY KEY (token, holder),
  FOREIGN KEY (watcher_id) REFERENCES watchers (id)
);

CREATE TABLE immature_mining_rewards (
  block_number int,
  mining_round text,
  holder text,
  mcb_balance numeric(78, 18) NOT NULL,
  PRIMARY KEY (block_number, mining_round, holder)
);

CREATE TABLE immature_mining_reward_summaries (
  mining_round text,
  holder text,
  mcb_balance numeric(78, 18) NOT NULL,
  PRIMARY KEY (mining_round, holder)
);

CREATE TABLE mature_mining_rewards (
  mining_round text,
  holder text,
  block_number int NOT NULL,
  mcb_balance numeric(78, 18) NOT NULL,
  PRIMARY KEY (mining_round, holder)
);

CREATE TABLE mature_mining_reward_checkpoints (
  mining_round text,
  block_number int,
  holder text,
  mcb_balance numeric(78, 18) NOT NULL,
  PRIMARY KEY (mining_round, block_number, holder)
);

CREATE TABLE payment_transactions (
  id serial PRIMARY KEY,
  transaction_nonce int NOT NULL,
  transaction_data text NOT NULL,
  transaction_hash text,
  status text NOT NULL
);

CREATE TABLE payments (
  id serial PRIMARY KEY,
  holder text NOT NULL,
  amount numeric(78, 18) NOT NULL,
  pay_time timestamp NOT NULL,
  transaction_id int NOT NULL,
  FOREIGN KEY (transaction_id) REFERENCES payment_transactions (id)
);

CREATE TABLE payment_summaries (
  holder text NOT NULL,
  paid_amount numeric(78, 18) NOT NULL,
  PRIMARY KEY (holder)
);

CREATE TABLE round_payments (
  id serial PRIMARY KEY,
  mining_round text NOT NULL,
  holder text NOT NULL,
  amount numeric(78, 18) NOT NULL,
  transaction_id int NOT NULL,
  FOREIGN KEY (transaction_id) REFERENCES payment_transactions (id)
);

CREATE TABLE round_payment_summaries (
  mining_round text NOT NULL,
  holder text NOT NULL,
  paid_amount numeric(78, 18) NOT NULL,
  PRIMARY KEY (mining_round, holder)
);

INSERT INTO watchers (id, initial_block_number, synced_block_number) VALUES (1, 10289334, 10289333);
INSERT INTO mining_rounds (round, begin_block_number, end_block_number, supply, release_per_block, watcher_id) VALUES ('XIA', 10420000, 10624999, 410000, 2, 1);
