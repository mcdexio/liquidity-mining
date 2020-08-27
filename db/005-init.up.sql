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


/* comp contract info */ 
INSERT INTO perp_share_amm_proxy_maps (perp_addr, share_addr, amm_addr, proxy_addr) VALUES ('0xfa203e643d1fddc5d8b91253ea23b3bd826cae9e', '0x9ec63850650bc7aec297ba023f0c1650cbbd6958', '0x5378b0388ef594f0c2eb194504aee2b48d1eac18', '0x69f3ebb9f14f7048e675443fb6375f9d48d8a9d6');

/* lend contract info */ 
INSERT INTO perp_share_amm_proxy_maps (perp_addr, share_addr, amm_addr, proxy_addr) VALUES ('0xd48c88a18bfa81486862c6d1d172a39f1365e8ac', '0x3d4b40ca0f98fcce38aa1704cbdf134496c261e8', '0xbe83943d5ca2d66fb7ba3a8d4a983782f31a42dc', '0xd8642327b919295fe2733a73de1d2355b589cb04');

/* snx contract info */ 
INSERT INTO perp_share_amm_proxy_maps (perp_addr, share_addr, amm_addr, proxy_addr) VALUES ('0x4cc89906db523af7c3bb240a959be21cb812b434', '0xf377810bffc83df177d7f992a8807943ea0a286f', '0x942df696cd1995ba2eab710d168b2d9cee53b52c', '0x298badda419eece0abe86fedc2f0677a7e8e35a2');

update mining_rounds set pool_supply = '[{"name": "ETH_PERP", "supply": 153750, "type": 1},{"name": "LINK_PERP", "supply": 153750, "type": 1},{"name": "COMP_PERP", "supply": 153750, "type": 1},{"name": "LEND_PERP", "supply": 153750, "type": 1},{"name": "SNX_PERP", "supply": 153750, "type": 1},{"name":"UNISWAP_MCB_ETH", "supply": 51250, "type": 2}]' where round='ZHOU';