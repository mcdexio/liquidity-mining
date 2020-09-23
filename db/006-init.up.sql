INSERT INTO watchers (id, initial_block_number, synced_block_number) VALUES (5, 10830000, 10829999);

INSERT INTO mining_rounds (round, begin_block_number, end_block_number, supply, release_per_block, watcher_id, start_time, end_time, pool_supply) 
    VALUES ('QIN', 10830000, 10932499, 205000, 2, 5, '2020-09-10', '2020-09-27', '[{"name": "ETH_PERP", "supply": 82000, "type": 1},{"name": "LINK_PERP", "supply": 5125, "type": 1},{"name": "COMP_PERP", "supply": 5125, "type": 1},{"name": "LEND_PERP", "supply": 5125, "type": 1},{"name": "SNX_PERP", "supply": 5125, "type": 1},{"name":"UNISWAP_MCB_ETH", "supply": 102500, "type": 2}]');


ALTER TABLE mining_rounds ALTER COLUMN supply TYPE FLOAT;
ALTER TABLE mining_rounds ALTER COLUMN release_per_block TYPE FLOAT;

ALTER TABLE mining_rounds alter COLUMN supply TYPE double precision ;
ALTER TABLE mining_rounds alter COLUMN release_per_block TYPE double precision;

update mining_rounds set supply = 36340 where round='QIN';
update mining_rounds set release_per_block = 0.2 where round='QIN';
update mining_rounds set pool_supply = '[{"name": "ETH_PERP", "supply": 14536, "type": 1},{"name": "LINK_PERP", "supply": 908.5, "type": 1},{"name": "COMP_PERP", "supply": 908.5, "type": 1},{"name": "LEND_PERP", "supply": 908.5, "type": 1},{"name": "SNX_PERP", "supply": 908.5, "type": 1},{"name":"UNISWAP_MCB_ETH", "supply": 18170, "type": 2}]' where round='QIN';