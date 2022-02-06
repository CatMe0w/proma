import json
import random
import requests

API_URL = 'http://127.0.0.1:9090'
PROXY_GROUP_NAME = 'Proxies'

response = requests.get(API_URL + '/proxies')
proxies = json.loads(response.text)['proxies'][PROXY_GROUP_NAME]['all']

requests.put(API_URL + '/proxies/' + PROXY_GROUP_NAME, data='{"name":"DIRECT"}')


def switch_proxy():
    next_proxy = random.choice(proxies)
    requests.put(API_URL + '/proxies/' + PROXY_GROUP_NAME, data='{"name":' + next_proxy + '}')
    requests.delete(API_URL + '/connections')
