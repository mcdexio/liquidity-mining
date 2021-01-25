INSERT INTO watchers (id, initial_block_number, synced_block_number) VALUES (6, 10932500, 10932499);
INSERT INTO watchers (id, initial_block_number, synced_block_number) VALUES (104, 10886275, 10886274);

INSERT INTO mining_rounds (round, begin_block_number, end_block_number, supply, release_per_block, watcher_id, start_time, end_time, pool_supply) 
    VALUES ('HAN', 10932500, 11034999, 20500, 0.2, 6, '2020-09-26', '2020-10-11', '[{"name":"UNISWAP_MCB_USDC", "supply": 20500, "type": 2},{"name":"UNISWAP_MCB_ETH", "supply": 20500, "type": 2}]');


update mining_rounds SET end_block_number=11137499  WHERE round='HAN';
update mining_rounds SET supply = 41000  WHERE round='HAN';
update mining_rounds SET end_time = '2020-10-26'  WHERE round='HAN';
update mining_rounds set pool_supply = '[{"name":"UNISWAP_MCB_USDC", "supply": 41000, "type": 2},{"name":"UNISWAP_MCB_ETH", "supply": 41000, "type": 2}]' where round='HAN';


update mining_rounds SET end_block_number=11342499  WHERE round='HAN';
update mining_rounds SET supply = 82000  WHERE round='HAN';
update mining_rounds SET end_time = '2020-11-28'  WHERE round='HAN';
update mining_rounds set pool_supply = '[{"name":"UNISWAP_MCB_USDC", "supply": 82000, "type": 2},{"name":"UNISWAP_MCB_ETH", "supply": 82000, "type": 2}]' where round='HAN';


update mining_rounds SET end_block_number=11547499  WHERE round='HAN';
update mining_rounds SET supply = 123000  WHERE round='HAN';
update mining_rounds SET end_time = '2020-12-28'  WHERE round='HAN';
update mining_rounds set pool_supply = '[{"name":"UNISWAP_MCB_USDC", "supply": 123000, "type": 2},{"name":"UNISWAP_MCB_ETH", "supply": 123000, "type": 2}]' where round='HAN';

update mining_rounds SET end_block_number=11752499  WHERE round='HAN';
update mining_rounds SET supply = 164000  WHERE round='HAN';
update mining_rounds SET end_time = '2021-01-28'  WHERE round='HAN';
update mining_rounds set pool_supply = '[{"name":"UNISWAP_MCB_USDC", "supply": 164000, "type": 2},{"name":"UNISWAP_MCB_ETH", "supply": 164000, "type": 2}]' where round='HAN';


update mining_rounds SET end_block_number=11957499  WHERE round='HAN';
update mining_rounds SET supply = 205000  WHERE round='HAN';
update mining_rounds SET end_time = '2021-02-28'  WHERE round='HAN';
update mining_rounds set pool_supply = '[{"name":"UNISWAP_MCB_USDC", "supply": 205000, "type": 2},{"name":"UNISWAP_MCB_ETH", "supply": 205000, "type": 2}]' where round='HAN';