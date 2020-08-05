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

# reward mature
MATURE_CONFIRM = os.environ.get('MATURE_CONFIRM', 100)
MATURE_CHECKPOINT_INTERVAL = os.environ.get('MATURE_CHECKPOINT_INTERVAL', 300)
REBALANCE_HARD_FORK_BLOCK_NUMBER = os.environ.get('REBALANCE_HARD_FORK_BLOCK_NUMBER', 10471250)

# watcher
WATCHER_CHECK_INTERVAL = os.environ.get('WATCHER_CHECK_INTERVAL', 3) # 3 sec

# XIA
XIA_SHARE_TOKEN_ADDRESS = os.environ.get('XIA_SHARE_TOKEN_ADDRESS', '0xAe694FB9DCD1E6195519c0056B2aB19380B26FF2')

# SHANG
SHANG_ETH_PERP_SHARE_TOKEN_ADDRESS = os.environ.get('SHANG_ETH_PERP_SHARE_TOKEN_ADDRESS', '0xAe694FB9DCD1E6195519c0056B2aB19380B26FF2')


# pepetual
PERPETUAL_ADDRESS = os.environ.get('PERPETUAL_ADDRESS', '0x220a9f0dd581cbc58fcfb907de0454cbf3777f76')
PERPETUAL_INVERSE = os.environ.get('PERPETUAL_INVERSE', True)
PERPETUAL_POSITION_TOPIC = os.environ.get('PERPETUAL_POSITION_TOPIC', '0xe763e57e3bd855c6028a13805d580b19a2403f388a7e9be7233d487a61a5abe5')

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