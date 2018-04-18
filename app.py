#!/usr/bin/env python
import os
import re
import json
import datetime
import logging
import platform
from flask import Flask, abort

import requests
from web3 import Web3, HTTPProvider
import settings

GETH_POD_HOSTNAME_REGEX = r'^(.*)-geth-\d+-.*$'

ETHERSCAN_API_URLS = {
    1: 'https://api.etherscan.io/api',
    3: 'http://ropsten.etherscan.io/api',
    4: 'http://rinkeby.etherscan.io/api',
}


def get_geth_url():
    result = re.search(GETH_POD_HOSTNAME_REGEX, platform.node())

    if not result:
        logging.warning('Geth pod not found. Using default port 8545.')
        return 'http://localhost:8545'

    service_env_name = "%s_GETH_SERVICE_PORT_RPC" % result.group(1).upper().replace('-', '_')
    service_port = os.environ.get(service_env_name)

    if not service_port:
        logging.warning('Geth service port not detected. Using default port 8545.')
        return 'http://localhost:8545'

    url = 'http://localhost:%s' % service_port
    logging.info('Detected geth by url %s' % url)

    return url


def get_eth_net_version(w3):
    result = json.loads(w3.currentProvider.make_request('net_version', []))
    version = result.get('result')
    if not version:
        raise BaseException('Error getting ethereum version')

    return int(version)


def get_etherscan_api_url(version):
    url = ETHERSCAN_API_URLS.get(version)
    if not url:
        raise BaseException('Unsupported ethereum network')

    logging.info(
        'Detect ethereum network version "{version}" and Etherscan API url "{url}"'.format(version=version, url=url))
    return url


def get_etherscan_highest_block(url):
    request_params = {'module': 'proxy',
                      'action': 'eth_blockNumber',
                      'apikey': settings.ETHERSCAN_API_KEY}

    response = requests.get(url, params=request_params)
    response_json = response.json()
    highest_block_hex = response_json.get('result')
    highest_block = int(highest_block_hex, 0)

    return highest_block


def get_eth_sync_diff(w3, ethercan_api_url):
    highest_block = get_etherscan_highest_block(ethercan_api_url)
    current_block = w3.eth.blockNumber
    sync_diff = highest_block - current_block

    if sync_diff < 0:
        return current_block, 0

    return current_block, sync_diff


# Init
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

w3_client = Web3(HTTPProvider(get_geth_url(), request_kwargs={'timeout': settings.ETH_RPC_TIMEOUT}))
ethercan_api_url = get_etherscan_api_url(get_eth_net_version(w3_client))

start_current_block, start_sync_diff = get_eth_sync_diff(w3_client, ethercan_api_url)

DB = {
    'START_TIME': datetime.datetime.now(),
    'LAST_BLOCK': start_current_block
}

logging.info('Checker started. Last geth block: {last_block}. Sync diff: {sync_diff}'.format(
    last_block=start_current_block,
    sync_diff=start_sync_diff)
)


@app.route("/healthz")
def liveness():
    if datetime.datetime.now() - DB['START_TIME'] <= datetime.timedelta(seconds=settings.START_WAIT_TIME):
        logging.info('Waiting start time period (%s sec), passing check' % settings.START_WAIT_TIME)
        return 'starting...'

    current_block, sync_diff = get_eth_sync_diff(w3_client, ethercan_api_url)

    if sync_diff and current_block == DB['LAST_BLOCK']:
        logging.error('Node not syncing. Diff: %s' % sync_diff)
        abort(500)

    DB['LAST_BLOCK'] = current_block

    logging.info('Node is synced')
    return 'ok'
