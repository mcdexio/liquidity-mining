INSERT INTO watchers (id, initial_block_number, synced_block_number) VALUES (2, 10418546, 10418545);
INSERT INTO watchers (id, initial_block_number, synced_block_number) VALUES (3, 10625000, 10624999);
INSERT INTO mining_rounds (round, begin_block_number, end_block_number, supply, release_per_block, watcher_id) VALUES ('SHANG', 10625000, 10727499, 205000, 2, 3);


ALTER TABLE immature_mining_rewards ADD COLUMN pool_name text;
UPDATE immature_mining_rewards  SET pool_name = 'ETH_PERP';

ALTER TABLE immature_mining_reward_summaries ADD COLUMN pool_name text;
UPDATE immature_mining_reward_summaries  SET pool_name = 'ETH_PERP';

ALTER TABLE mature_mining_rewards ADD COLUMN pool_name text;
UPDATE mature_mining_rewards  SET pool_name = 'ETH_PERP';

ALTER TABLE mature_mining_reward_checkpoints ADD COLUMN pool_name text;
UPDATE mature_mining_reward_checkpoints  SET pool_name = 'ETH_PERP';