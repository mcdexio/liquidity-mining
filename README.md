# Liquidity Mining of MCDEX

## Mining Rounds

### 1. XIA(夏) (Jul. 8th ~ Aug. 8th)

- Total Supply: 410,000 MCB
- Release: 2 MCB / Block
- Begin Block: 10,420,000
- End Block: 10,624,999

### 2. SHANG(商)

- Total Supply: 205,000 MCB
- Release: 2 MCB / Block
- Begin Block: 10,625,000
- End Block: 10,727,499

### 3. ZHOU(周)

- Total Supply: 205,000 MCB
- Release: 2 MCB / Block
- Begin Block: 10,727,500
- End Block: 10,829,999

## Mining Reward Distribution Rules

1. The mining rewards are calculated in every block.

2. The LP_i's position in AMM:

```
Position_In_AMM_i = Share_Token_Balance_i / Total_Share_Token_Supply * Total_Position_In_AMM
```

3. The net position of LP_j' portfolio:

```
Portfolio_Position_i = Position_in_AMM_i + Positon_In_Margin_Account_i
```

4. The imbalance rate of LP_j's portfolio:

```
Imbalance_Rate_i = ABS(Portfolio_Position_i) / ABS(Position_in_AMM_i)
```

5. The mining effective share of LP_i:
```
Effective_Share_i = Share_Token_Balance_i    If Imbalance_Rate_i <= 10%
Effective_Share_i = Share_Token_Balance_i * (89/80 - Imbalance_Rate_i * 9/8)  if  10% <  Imbalance_Rate_i < 90%
Effective_Share_i = Share_Token_Balance_i * 0.1    If Imbalance_Rate_i >= 90%
```
It means that if the LP's imbalance rate is below 10%, he can still get the same mining reward with that of a fully balanced portfolio.

```
Invalid_Mining_Share_i = Share_Token_Balance_i  - Effective_Share_i 
```

6. The mining rewards of LP_i of AMM_j:

```
Reward_LP_j = Effective_Share_i / SUM(Effective_Share_k) * Reward_AMM_j
```

7. The AMM_j's total effective mining value:
```
Effective_Value_j = SUM(Effective_Share_k) / Total_Share_Token_Supply * AMM_Position_Size_In_USD_j
```

8. Distribute the mining rewards (2MCB/block) among the AMMs:
```
Reward_AMM_j = Effective_Value_j / SUM(Effective_Value_k) * 2MCB
```

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
