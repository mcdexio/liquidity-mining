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


INSERT INTO perp_share_amm_proxy_maps (perp_addr, share_addr, amm_addr, proxy_addr) VALUES ('0x220a9f0dd581cbc58fcfb907de0454cbf3777f76', '0xae694fb9dcd1e6195519c0056b2ab19380b26ff2', '0xaaac8434217575643b2d2ab6f12ce8600c625520', '0x05c363d2b9afc36b070fe2c61711280edc214678');