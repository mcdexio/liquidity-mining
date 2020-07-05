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

CREATE MATERIALIZED VIEW token_balances AS
SELECT
  watcher_id,
  token,
  holder,
  SUM(amount) AS balance
FROM
  token_events
GROUP BY
  watcher_id,
  token,
  holder;

CREATE UNIQUE INDEX idx_token_balances_token_holder ON token_balances (token, holder);

CREATE TABLE immature_mining_rewards (
  block_number int,
  mining_round text,
  holder text,
  mcb_balance numeric(78, 18) NOT NULL,
  PRIMARY KEY (block_number, mining_round, holder)
);

CREATE MATERIALIZED VIEW immature_mining_reward_summaries AS
SELECT
  mining_round,
  holder,
  SUM(mcb_balance) AS mcb_balance
FROM
  immature_mining_rewards
GROUP BY
  mining_round,
  holder;

CREATE UNIQUE INDEX idx_immature_mining_reward_summaries_mining_round_holder ON immature_mining_reward_summaries (mining_round, holder);

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
  trasaction_nonce int NOT NULL,
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

CREATE MATERIALIZED VIEW payment_summaries AS
SELECT
  holder,
  SUM(amount) AS paid_amount
FROM
  payments
GROUP BY
  holder;

CREATE UNIQUE INDEX idx_payment_summaries_holder ON payment_summaries (holder);

CREATE TABLE round_payments (
  id serial PRIMARY KEY,
  mining_round text NOT NULL,
  holder text NOT NULL,
  amount numeric(78, 18) NOT NULL,
  payment_id int NOT NULL,
  FOREIGN KEY (payment_id) REFERENCES payments (id)
);

CREATE MATERIALIZED VIEW round_payment_summaries AS
SELECT
  mining_round,
  holder,
  SUM(amount) AS paid_amount
FROM
  round_payments
GROUP BY
  mining_round,
  holder;

CREATE UNIQUE INDEX idx_round_payment_summaries_mining_round_holder ON round_payment_summaries (mining_round, holder);

INSERT INTO watchers (id, initial_block_number, synced_block_number) VALUES (1, 10289334, 10289333);
INSERT INTO mining_rounds (round, begin_block_number, end_block_number, supply, release_per_block, watcher_id) VALUES ('XIA', 10420000, 10620000, 410000, 2, 1);
