CREATE TABLE perp_share_amm_proxy_maps (
  perp_addr text NOT NULL,
  share_addr text NOT NULL,
  amm_addr text NOT NULL,
  proxy_addr text NOT NULL,
  PRIMARY KEY (perp_addr, share_addr, amm_addr, proxy_addr),
);

INSERT INTO perp_share_amm_proxy_maps (perp_addr, share_addr, amm_addr, proxy_addr) VALUES ('0x220a9f0dd581cbc58fcfb907de0454cbf3777f76', '0xae694fb9dcd1e6195519c0056b2ab19380b26ff2', '0xaaac8434217575643b2d2ab6f12ce8600c625520', '0x05c363d2b9afc36b070fe2c61711280edc214678');