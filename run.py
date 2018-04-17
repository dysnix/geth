#!/usr/bin/env python
import os
import re
import logging
import platform
from flask import Flask, abort

import requests
from web3 import Web3, HTTPProvider
import settings

ETHEREUM = "eth"
BITCOIN = "bitcoin"

NODE_TYPES_MAP = {
    r'^(.*)-geth-\d+-.*$': ETHEREUM,
    r'^(.*)-bitcoin-\d+-.*$': BITCOIN
}

ETHERSCAN_API_URLS = {
    1: 'https://api.etherscan.io/api',
    3: 'http://ropsten.etherscan.io/api',
    4: 'http://rinkeby.etherscan.io/api',
}

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)


def get_service_params():
    result = None
    node_type = None

    hostname = platform.node()

    for r in NODE_TYPES_MAP.keys():
        result = re.search(r, hostname)
        if result:
            node_type = NODE_TYPES_MAP[r]
            break

    if not node_type:
        raise BaseException('Error detect crypto-currency node type')

    logging.info('Detected crypto-currency node %s' % node_type)

    if node_type == ETHEREUM:
        service_env_name = "%s_GETH_SERVICE_PORT_RPC" % result.group(1).upper().replace('-', '_')
    else:
        raise BaseException('Node type %s is unsupported' % node_type)

    service_port = os.environ.get(service_env_name)

    if not service_port:
        raise BaseException('Error getting service %s port' % node_type)

    logging.info('Detected {node} service port {port}'.format(node=node_type, port=service_port))

    url = 'http://localhost:%s' % service_port

    return node_type, url


def get_etherscan_highest_block(url):
    request_params = {'module': 'proxy',
                      'action': 'eth_blockNumber',
                      'apikey': settings.ETHERSCAN_API_KEY}

    response = requests.get(get_etherscan_highest_block, params=request_params)
    response_json = response.json()
    highest_block_hex = response_json.get('result')
    highest_block = int(highest_block_hex, 0)

    return highest_block


def get_etherscan_api_url(version):
    url = ETHERSCAN_API_URLS.get(version)
    if not url:
        raise BaseException('Unsupported ethereum network')

    return url


def get_eth_sync_diff(w3):
    ethercan_api_url = get_etherscan_api_url(int(w3.net.version))

    highest_block = get_etherscan_highest_block(ethercan_api_url)
    current_block = w3.eth.blockNumber

    return highest_block - current_block


def get_node_status(node_type, service_url):
    if node_type == ETHEREUM:
        w3_http_provider = HTTPProvider(service_url, request_kwargs={'timeout': settings.ETH_RPC_TIMEOUT})
        w3_client = Web3(w3_http_provider)
        sync_diff = get_eth_sync_diff(w3_client)
        if sync_diff >= settings.ETH_MAX_SYNC_DIFF:
            logging.error('Node un-synced. Diff: %s' % sync_diff)
            return False
    else:
        raise BaseException('Unsupported node type %s' % node_type)

    return True


node_type, service_url = get_service_params()


@app.route("/healthz")
def liveness():
    if not get_node_status(node_type, service_url):
        abort(500)

    return 'ok'
