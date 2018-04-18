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
        raise BaseException('Geth pod not found')

    service_env_name = "%s_GETH_SERVICE_PORT_RPC" % result.group(1).upper().replace('-', '_')

    service_port = os.environ.get(service_env_name)

    if not service_port:
        raise BaseException('Error getting geth port')

    logging.info('Detected geth service port %s' % service_port)

    url = 'http://localhost:%s' % service_port

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
        return 0

    return sync_diff


def get_node_status(w3, ethercan_api_url):
    sync_diff = get_eth_sync_diff(w3, ethercan_api_url)
    if sync_diff >= settings.ETH_MAX_SYNC_DIFF:
        logging.error('Node un-synced. Diff: %s' % sync_diff)
        return False

    return True


# Init
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

w3_client = Web3(HTTPProvider(get_geth_url(), request_kwargs={'timeout': settings.ETH_RPC_TIMEOUT}))
ethercan_api_url = get_etherscan_api_url(get_eth_net_version(w3_client))

START_TIME = datetime.datetime.now()
LAST_CHECK_TIME = START_TIME
LAST_SYNC_DIFF = None


@app.route("/healthz")
def liveness():
    if datetime.datetime.now() - START_TIME <= datetime.timedelta(seconds=settings.START_WAIT_TIME):
        logging.info('Waiting start time period (%s sec), passing check' % settings.START_WAIT_TIME)
        return 'starting...'

    sync_diff = get_eth_sync_diff(w3_client, ethercan_api_url)

    if sync_diff == LAST_SYNC_DIFF and (datetime.datetime.now() - LAST_CHECK_TIME) >= settings.UPDATE_INTERVAL:
        abort(500)

    LAST_SYNC_DIFF = sync_diff
    LAST_CHECK_TIME = datetime.datetime.now()

    if not get_eth_sync_diff(w3_client, ethercan_api_url):
        abort(500)

    logging.info('Node is synced')
    return 'ok'
