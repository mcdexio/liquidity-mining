INSERT INTO watchers (id, initial_block_number, synced_block_number) VALUES (4, 10727500, 10727499);

INSERT INTO mining_rounds (round, begin_block_number, end_block_number, supply, release_per_block, watcher_id, start_time, end_time, pool_supply) 
    VALUES ('ZHOU', 10727500, 10829999, 205000, 2, 4, '2020-08-25', '2020-09-09', '[{"name": "ETH_PERP", "supply": 153750, "type": 1}, {"name": "LINK_PERP", "supply": 153750, "type": 1}, {"name":"UNISWAP_MCB_ETH", "supply": 51250, "type": 2}]');



CREATE TABLE theory_mining_rewards (
  pool_type text,
  mining_round text,
  holder text,
  mcb_balance numeric(78, 18) NOT NULL,
  PRIMARY KEY (pool_type, mining_round, holder)
);