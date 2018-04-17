import os

# InfluxDB
INFLUXDB_HOST = os.environ.get('INFLUXDB_HOST', 'influxdb-influxdb.monitoring')
INFLUXDB_PORT = int(os.environ.get('INFLUXDB_PORT', 8086))
INFLUXDB_DB_NAME = os.environ.get('INFLUXDB_DB_NAME', 'k8s')

# Update interval
UPDATE_INTERVAL = int(os.environ.get('UPDATE_INTERVAL', 60))

# Etherscan
ETH_RPC_TIMEOUT = int(os.environ.get('ETH_RPC_TIMEOUT', 30))
ETH_MAX_SYNC_DIFF = int(os.environ.get('ETH_MAX_SYNC_DIFF', 50))

try:
    from local_settings import *
except ImportError:
    pass
