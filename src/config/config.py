import os

# eth node rpc request
ETH_RPC_URL = os.environ.get('ETH_RPC_URL', 'http://localhost:8545')
ETH_RPC_TIMEOUT = 10

# mining MCB 
MINING_ROUND = os.environ.get('MINING_ROUND', 'XIA')
MAX_PATCH_NUM = os.environ.get('MAX_PATCH_NUM', 100)
WAIT_TIMEOUT = os.environ.get('WAIT_TIMEOUT', 600)
MIN_PAY_AMOUNT = os.environ.get('MIN_PAY_AMOUNT', 1)
PAY_ALL = os.environ.get('PAY_ALL', False)

# db
DB_URL = os.environ.get('DB_URL', '')
DB_ECHO = os.environ.get('DB_ECHO', False)

# gas price
GAS_LEVEL = os.environ.get('GAS_LEVEL', 'fast')
ETH_GAS_URL = os.environ.get('ETH_GAS_URL', 'https://ethgasstation.info/api/ethgasAPI.json')

# payer account
PAYER_ADDRESS = os.environ.get('PAYER_ADDRESS', '')
PAYER_KEY = os.environ.get('PAYER_KEY', '')

# contract address
DISPERSE_ADDRESS = os.environ.get('DISPERSE_ADDRESS', '0xD152f549545093347A162Dce210e7293f1452150')
MCB_TOKEN_ADDRESS = os.environ.get('MCB_TOKEN_ADDRESS', '0x4e352cf164e64adcbad318c3a1e222e9eba4ce42')
CHAINLINK_ETH_USD_ADDRESS = os.environ.get('CHAINLINK_ETH_USD_ADDRESS', '0xF79D6aFBb6dA890132F9D7c355e3015f15F3406F')
CHAINLINK_BTC_USD_ADDRESS = os.environ.get('CHAINLINK_BTC_USD_ADDRESS', '0xF5fff180082d6017036B771bA883025c654BC935')

# reward mature
MATURE_CONFIRM = os.environ.get('MATURE_CONFIRM', 100)
MATURE_CHECKPOINT_INTERVAL = os.environ.get('MATURE_CHECKPOINT_INTERVAL', 300)


# watcher
WATCHER_CHECK_INTERVAL = os.environ.get('WATCHER_CHECK_INTERVAL', 3) # 3 sec

# XIA
XIA_SHARE_TOKEN_ADDRESS = os.environ.get('XIA_SHARE_TOKEN_ADDRESS', '0xAe694FB9DCD1E6195519c0056B2aB19380B26FF2')
XIA_REBALANCE_HARD_FORK_BLOCK_NUMBER = os.environ.get('XIA_REBALANCE_HARD_FORK_BLOCK_NUMBER', 10471250)

# SHANG
SHANG_REWARD_LINK_POOL_BLOCK_NUMBER =  os.environ.get('SHANG_REWARD_LINK_POOL_BLOCK_NUMBER', 10676500)
SHANG_REWARD_BTC_POOL_BLOCK_NUMBER =  os.environ.get('SHANG_REWARD_BTC_POOL_BLOCK_NUMBER', 11000000)

# ZHOU
ZHOU_BEGIN_BLOCK_NUMBER =  os.environ.get('ZHOU_BEGIN_BLOCK_NUMBER', 10727500)
ZHOU_M = 2
ZHOU_N = 102500

ZHOU_REWARD_BTC_POOL_BLOCK_NUMBER =  os.environ.get('ZHOU_REWARD_BTC_POOL_BLOCK_NUMBER', 11000000)
ZHOU_REWARD_COMP_POOL_BLOCK_NUMBER =  os.environ.get('ZHOU_REWARD_COMP_POOL_BLOCK_NUMBER', 11000000)
ZHOU_REWARD_LEND_POOL_BLOCK_NUMBER =  os.environ.get('ZHOU_REWARD_LEND_POOL_BLOCK_NUMBER', 11000000)
ZHOU_REWARD_SNX_POOL_BLOCK_NUMBER =  os.environ.get('ZHOU_REWARD_SNX_POOL_BLOCK_NUMBER', 11000000)

# pepetual
ETH_PERPETUAL_ADDRESS = os.environ.get('ETH_PERPETUAL_ADDRESS', '0x220a9f0dd581cbc58fcfb907de0454cbf3777f76')
ETH_PERP_SHARE_TOKEN_ADDRESS = os.environ.get('ETH_PERP_SHARE_TOKEN_ADDRESS', '0xAe694FB9DCD1E6195519c0056B2aB19380B26FF2')
ETH_PERPETUAL_INVERSE = os.environ.get('ETH_PERPETUAL_INVERSE', True)
ETH_PERPETUAL_POSITION_TOPIC = os.environ.get('ETH_PERPETUAL_POSITION_TOPIC', '0xe763e57e3bd855c6028a13805d580b19a2403f388a7e9be7233d487a61a5abe5')

LINK_PERPETUAL_ADDRESS = os.environ.get('LINK_PERPETUAL_ADDRESS', '0xa04197e5f7971e7aef78cf5ad2bc65aac1a967aa')
LINK_PERP_SHARE_TOKEN_ADDRESS = os.environ.get('LINK_PERP_SHARE_TOKEN_ADDRESS', '0xd78ba1d99dbbc4eba3b206c9c67a08879b6ec79b')
LINK_PERPETUAL_INVERSE = os.environ.get('LINK_PERPETUAL_INVERSE', True)
LINK_PERPETUAL_POSITION_TOPIC = os.environ.get('LINK_PERPETUAL_POSITION_TOPIC', '0xe763e57e3bd855c6028a13805d580b19a2403f388a7e9be7233d487a61a5abe5')

BTC_PERPETUAL_ADDRESS = os.environ.get('BTC_PERPETUAL_ADDRESS', '0xe3c29ce0c36863fd682f1afe464781df6bebaa0a')
BTC_PERP_SHARE_TOKEN_ADDRESS = os.environ.get('BTC_PERP_SHARE_TOKEN_ADDRESS', '0xdcd1aa80661756c9d92317115e356f5bde26977b')
BTC_PERPETUAL_INVERSE = os.environ.get('BTC_PERPETUAL_INVERSE', False)
BTC_PERPETUAL_POSITION_TOPIC = os.environ.get('BTC_PERPETUAL_POSITION_TOPIC', '0xe763e57e3bd855c6028a13805d580b19a2403f388a7e9be7233d487a61a5abe5')

COMP_PERPETUAL_ADDRESS = os.environ.get('COMP_PERPETUAL_ADDRESS', '0xfa203e643d1fddc5d8b91253ea23b3bd826cae9e')
COMP_PERP_SHARE_TOKEN_ADDRESS = os.environ.get('COMP_PERP_SHARE_TOKEN_ADDRESS', '0x9ec63850650bc7aec297ba023f0c1650cbbd6958')
COMP_PERPETUAL_INVERSE = os.environ.get('COMP_PERPETUAL_INVERSE', True)
COMP_PERPETUAL_POSITION_TOPIC = os.environ.get('COMP_PERPETUAL_POSITION_TOPIC', '0xe763e57e3bd855c6028a13805d580b19a2403f388a7e9be7233d487a61a5abe5')

LEND_PERPETUAL_ADDRESS = os.environ.get('LEND_PERPETUAL_ADDRESS', '0xd48c88a18bfa81486862c6d1d172a39f1365e8ac')
LEND_PERP_SHARE_TOKEN_ADDRESS = os.environ.get('LEND_PERP_SHARE_TOKEN_ADDRESS', '0x3d4b40ca0f98fcce38aa1704cbdf134496c261e8')
LEND_PERPETUAL_INVERSE = os.environ.get('LEND_PERPETUAL_INVERSE', True)
LEND_PERPETUAL_POSITION_TOPIC = os.environ.get('LEND_PERPETUAL_POSITION_TOPIC', '0xe763e57e3bd855c6028a13805d580b19a2403f388a7e9be7233d487a61a5abe5')

SNX_PERPETUAL_ADDRESS = os.environ.get('SNX_PERPETUAL_ADDRESS', '0x4cc89906db523af7c3bb240a959be21cb812b434')
SNX_PERP_SHARE_TOKEN_ADDRESS = os.environ.get('SNX_PERP_SHARE_TOKEN_ADDRESS', '0xf377810bffc83df177d7f992a8807943ea0a286f')
SNX_PERPETUAL_INVERSE = os.environ.get('SNX_PERPETUAL_INVERSE', True)
SNX_PERPETUAL_POSITION_TOPIC = os.environ.get('SNX_PERPETUAL_POSITION_TOPIC', '0xe763e57e3bd855c6028a13805d580b19a2403f388a7e9be7233d487a61a5abe5')

# UNISWAP_MCB/ETH
UNISWAP_MCB_ETH_SHARE_TOKEN_ADDRESS = os.environ.get('UNISWAP_MCB_ETH_SHARE_TOKEN_ADDRESS', '0x10cfa744c77f1cb9a77fa418ac4a1b6ec62bcce4')

# log
PAYER_LOGPATH = os.environ.get('PAYER_LOGPATH', './log/payer.log')
WATCHER_LOGPATH = os.environ.get('WATCHER_LOGPATH', './log/watcher.log')

LOG_CONFIG = {
    "version": 1,
    "disable_existing_loggers": True,
    "formatters": {
        "simple": {
            "format": "%(asctime)s %(levelname)-7s - %(message)s - [%(filename)s:%(lineno)d:%(funcName)s]",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "simple",
            "stream": "ext://sys.stdout",
        },
        "file_handler": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "simple",
            "filename": "",
            "maxBytes": 104857600, # 100MB
            "backupCount": 7,
            "encoding": "utf8"
        },
    },
    "root": {
        "level": "DEBUG",
        "handlers": ["console"],
    }
}