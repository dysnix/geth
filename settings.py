import os

# How long waiting before check after start (in seconds)
START_WAIT_TIME = int(os.environ.get('START_WAIT_TIME', 120))

# Ethereum
ETH_RPC_PORT = int(os.environ.get('ETH_RPC_PORT', 8545))
ETH_RPC_TIMEOUT = int(os.environ.get('ETH_RPC_TIMEOUT', 30))
ETH_MAX_SYNC_DIFF = int(os.environ.get('ETH_MAX_SYNC_DIFF', 50))
ETHERSCAN_API_KEY = os.environ.get('ETHERSCAN_API_KEY')


try:
    from local_settings import *
except ImportError:
    pass
