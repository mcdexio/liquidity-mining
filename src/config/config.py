# eth node rpc request
ETH_RPC_URL = "http://localhost:8545"
ETH_RPC_TIMEOUT = 10

# mining MCB 
MINING_ROUND = "XIA"
MAX_PATCH_NUM = 100
WAIT_TIMEOUT = 600

# db
DB_URL = "postgres://postgres:postgres@localhost/postgres?sslmode=disable"
DB_ECHO = True

# gas price
GAS_LEVEL = "fast"
ETH_GAS_URL = "https://ethgasstation.info/api/ethgasAPI.json"

# payer account
PAYER_ADDRESS = ""
PAYER_KEY = ""

# contract address
DISPERSE_ADDRESS = "0xD152f549545093347A162Dce210e7293f1452150"
MCB_TOKEN_ADDRESS = "0x0000000000000000000000000000000000000000"

# reward mature
MATURE_CONFIRM = 100
MATURE_CHECKPOINT_INTERVAL = 300

# XIA
XIA_SHARE_TOKEN_ADDRESS = "0xAe694FB9DCD1E6195519c0056B2aB19380B26FF2"

# log
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
        "handlers": ["console", "file_handler"],
    }
}