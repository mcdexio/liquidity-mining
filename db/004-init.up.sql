CREATE TABLE chain_link_price_events (
  block_number int,
  transaction_hash text,
  event_index int,
  chain_link_address text NOT NULL,
  price numeric(78, 18) NOT NULL,
  watcher_id int NOT NULL,
  PRIMARY KEY (block_number, transaction_hash, event_index, chain_link_address),
  FOREIGN KEY (watcher_id) REFERENCES watchers (id)
);

/* link contract info */ 
INSERT INTO perp_share_amm_proxy_maps (perp_addr, share_addr, amm_addr, proxy_addr) VALUES ('0xa04197e5f7971e7aef78cf5ad2bc65aac1a967aa', '0xd78ba1d99dbbc4eba3b206c9c67a08879b6ec79b', '0x7230d622d067d9c30154a750dbd29c035ba7605a', '0x694baa24d46530e46bcd39b1f07943a2bddb01e6');

/* btc contract info */ 
INSERT INTO perp_share_amm_proxy_maps (perp_addr, share_addr, amm_addr, proxy_addr) VALUES ('0xe3c29ce0c36863fd682f1afe464781df6bebaa0a ', '0xdcd1aa80661756c9d92317115e356f5bde26977b', '0x028fb01ffafe25e278ebb467f69bd79a928cf25e', '0xc32e180d105034c1abaf6604d74efcce6578e3f2');

/*INSERT INTO watchers (id, initial_block_number, synced_block_number) VALUES (101, 10637097, 10637096);*/