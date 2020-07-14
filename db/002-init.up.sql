CREATE TABLE perp_share_amm_proxy_maps (
  perp_addr text NOT NULL,
  share_addr text NOT NULL,
  amm_addr text NOT NULL,
  proxy_addr text NOT NULL,
  PRIMARY KEY (perp_addr, share_addr, amm_addr, proxy_addr),
);

CREATE TABLE position_events (
  block_number int,
  transaction_hash text,
  event_index int,
  perpetual_address text NOT NULL,
  holder text NOT NULL,
  amount numeric(78, 18) NOT NULL,
  /* positive or negative */
  watcher_id int NOT NULL,
  PRIMARY KEY (block_number, transaction_hash, event_index, perpetual_address, holder),
  FOREIGN KEY (watcher_id) REFERENCES watchers (id)
);

CREATE TABLE position_balances (
  perpetual_address text NOT NULL,
  holder text NOT NULL,
  balance numeric(78, 18) NOT NULL,
  block_number int,
  watcher_id int NOT NULL,
  PRIMARY KEY (perpetual_address, holder),
  FOREIGN KEY (watcher_id) REFERENCES watchers (id)
);

INSERT INTO perp_share_amm_proxy_maps (perp_addr, share_addr, amm_addr, proxy_addr) VALUES ('0x220a9f0dd581cbc58fcfb907de0454cbf3777f76', '0xae694fb9dcd1e6195519c0056b2ab19380b26ff2', '0xaaac8434217575643b2d2ab6f12ce8600c625520', '0x05c363d2b9afc36b070fe2c61711280edc214678');