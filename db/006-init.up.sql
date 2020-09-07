INSERT INTO watchers (id, initial_block_number, synced_block_number) VALUES (5, 10830000, 10829999);

INSERT INTO mining_rounds (round, begin_block_number, end_block_number, supply, release_per_block, watcher_id, start_time, end_time, pool_supply) 
    VALUES ('QIN', 10830000, 10932499, 205000, 2, 5, '2020-09-09', '2020-09-26', '[{"name": "ETH_PERP", "supply": 123000, "type": 1},{"name": "LINK_PERP", "supply": 7687.5, "type": 1},{"name": "COMP_PERP", "supply": 7687.5, "type": 1},{"name": "LEND_PERP", "supply": 7687.5, "type": 1},{"name": "SNX_PERP", "supply": 7687.5, "type": 1},{"name":"UNISWAP_MCB_ETH", "supply": 51250, "type": 2}]');
