#!/usr/bin/env python
import json
import logging
import requests
import datetime
from flask import Flask, abort
from web3 import Web3, HTTPProvider

import settings

# Init
logging.basicConfig(level=logging.INFO)

ETHERSCAN_API_URLS = {
    1: 'https://api.etherscan.io/api',
    3: 'http://ropsten.etherscan.io/api',
    4: 'http://rinkeby.etherscan.io/api',
}

DB = {
    'START_TIME': datetime.datetime.now(),
    'LAST_BLOCK': 0,
    'ETHERSCAN_API_URL': None
}

GETH_URL = 'http://localhost:%s' % settings.ETH_RPC_PORT

app = Flask(__name__)

w3_http_provider = HTTPProvider(GETH_URL, request_kwargs={'timeout': settings.ETH_RPC_TIMEOUT})
w3_client = Web3(w3_http_provider)


def get_eth_net_version(provider):
    result = json.loads(provider.make_request('net_version', []))
    version = result.get('result')
    if not version:
        logging.error('Error getting ethereum network version. Using main net as default')
        return 1

    return int(version)


def get_etherscan_api_url(version):
    url = ETHERSCAN_API_URLS.get(version)

    if not url:
        raise BaseException('Unsupported ethereum network')

    logging.info('Detect ethereum network version "{version}" and Etherscan API url "{url}"'.format(version=version,
                                                                                                    url=url))
    return url


def get_etherscan_highest_block(url):
    request_params = {'module': 'proxy',
                      'action': 'eth_blockNumber',
                      'apikey': settings.ETHERSCAN_API_KEY}

    data = requests.get(url, params=request_params).json()
    highest_block = int(data.get('result'), 0)

    return highest_block


def get_eth_sync_diff(w3, ethercan_api_url):
    highest_block = get_etherscan_highest_block(ethercan_api_url)
    current_block = w3.eth.blockNumber
    sync_diff = highest_block - current_block

    return current_block, sync_diff


# Flask routes
@app.route("/healthz")
def liveness():
    try:
        if not DB['ETHERSCAN_API_URL']:
            DB['ETHERSCAN_API_URL'] = get_etherscan_api_url(get_eth_net_version(w3_http_provider))

        current_block, sync_diff = get_eth_sync_diff(w3_client, DB['ETHERSCAN_API_URL'])
    except Exception as exc:
        logging.error(exc)
        return 'ignore'

    if sync_diff >= settings.ETH_MAX_SYNC_DIFF and current_block == DB['LAST_BLOCK']:
        logging.error('Node not syncing. Diff: %s' % sync_diff)
        abort(500)

    DB['LAST_BLOCK'] = current_block

    logging.info('Node is synced')

    return 'ok'
