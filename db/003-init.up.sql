INSERT INTO watchers (id, initial_block_number, synced_block_number) VALUES (2, 10418546, 10418545);
INSERT INTO watchers (id, initial_block_number, synced_block_number) VALUES (3, 10625000, 10624999);
ALTER TABLE mining_rounds ADD COLUMN start_time timestamp, ADD COLUMN end_time timestamp, ADD COLUMN pool_supply text;
UPDATE mining_rounds SET start_time = '2020-07-08', end_time = '2020-08-09', pool_supply = '{"ETH_PERP": 410000}' WHERE round = 'XIA';

INSERT INTO mining_rounds (round, begin_block_number, end_block_number, supply, release_per_block, watcher_id, start_time, end_time, pool_supply) VALUES ('SHANG', 10625000, 10727499, 205000, 2, 3, '2020-08-09', '2020-08-23', '{"ETH_PERP": 153750,"UNISWAP_MCB_ETH": 51250}');


ALTER TABLE immature_mining_rewards ADD COLUMN pool_name text;
UPDATE immature_mining_rewards  SET pool_name = 'ETH_PERP';
ALTER TABLE immature_mining_rewards DROP CONSTRAINT immature_mining_rewards_pkey;
ALTER TABLE immature_mining_rewards ADD CONSTRAINT immature_mining_rewards_pkey PRIMARY KEY (block_number, mining_round, holder, pool_name);

ALTER TABLE immature_mining_reward_summaries ADD COLUMN pool_name text;
UPDATE immature_mining_reward_summaries  SET pool_name = 'ETH_PERP';
ALTER TABLE immature_mining_reward_summaries DROP CONSTRAINT immature_mining_reward_summaries_pkey;
ALTER TABLE immature_mining_reward_summaries ADD CONSTRAINT immature_mining_reward_summaries_pkey PRIMARY KEY (mining_round, holder, pool_name);

ALTER TABLE mature_mining_rewards ADD COLUMN pool_name text;
UPDATE mature_mining_rewards  SET pool_name = 'ETH_PERP';
ALTER TABLE mature_mining_rewards DROP CONSTRAINT mature_mining_rewards_pkey;
ALTER TABLE mature_mining_rewards ADD CONSTRAINT mature_mining_rewards_pkey PRIMARY KEY (mining_round, holder, pool_name);

ALTER TABLE mature_mining_reward_checkpoints ADD COLUMN pool_name text;
UPDATE mature_mining_reward_checkpoints  SET pool_name = 'ETH_PERP';
ALTER TABLE mature_mining_reward_checkpoints DROP CONSTRAINT mature_mining_reward_checkpoints_pkey;
ALTER TABLE mature_mining_reward_checkpoints ADD CONSTRAINT mature_mining_reward_checkpoints_pkey PRIMARY KEY (mining_round, block_number, holder, pool_name);

ALTER TABLE round_payments ADD COLUMN pool_name text;
UPDATE round_payments  SET pool_name = 'ETH_PERP';

ALTER TABLE round_payment_summaries ADD COLUMN pool_name text;
UPDATE round_payment_summaries  SET pool_name = 'ETH_PERP';
ALTER TABLE round_payment_summaries DROP CONSTRAINT round_payment_summaries_pkey;
ALTER TABLE round_payment_summaries ADD CONSTRAINT round_payment_summaries_pkey PRIMARY KEY (mining_round, holder, pool_name);
