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