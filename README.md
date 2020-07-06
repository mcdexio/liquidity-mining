# Liquidity Mining of MCDEX

## Mining Rounds

### 1. XIA(夏) (Jul. 8th ~ Aug. 8th)

- Total Supply: 410,000 MCB
- Release: 2 MCB / Block
- Begin Block: 10,420,000
- End Block: 10,624,999

#### Distribution

1. The mining rewards are calculated in every block.
   
2. Each AMM gets the mining rewards according to the USD value of its `MaginBalance` .  
   
   Reward for AMM_i: 
   
   `Reward_AMM_i = MaginBalance_USD_i / SUM(MaginBalance_USD_j) * 2`

3. The liquidity providers (LPs) of the AMM_i get the mining rewards according to their balances of the AMM_i's share token.
   
   Reward for the LP_k of AMM_i: 
   
   `Reward_LP_k = Share_Token_Balance_k / Total_Share_Token_Supply * Reward_AMM_i`


#### AMM List

* ETH-PERP
  * Perpetaul AMM: [0xaaac8434217575643b2d2ab6f12ce8600c625520](https://etherscan.io/address/0xaaac8434217575643b2d2ab6f12ce8600c625520)
  * Share Token: [0xAe694FB9DCD1E6195519c0056B2aB19380B26FF2](https://etherscan.io/token/0xAe694FB9DCD1E6195519c0056B2aB19380B26FF2)

## Features
1. Trace the share token balances by ERC20 events
2. Calculate and save the holders' mining reward
3. Pay MCB to the holders
4. API for querying data


## Usage

### Install Dependences
```
$ apt-get install postgresql
$ pip3 install -r requirements.txt
```

### Edit Configure

Edit the `src/config/config.py`:
-  `ETH_RPC_URL`: Etherume HTTP API URL.
-  `DB_URL`:  Postgresql URL

### Run Watcher
```
$ python3 xia.py
```

### Use Tool
```
$ python3 tool.py
```