import json
import random
import requests

USE_CLASH = True
PROXIES = {
    "http": 'http://127.0.0.1:7890',
    "https": 'http://127.0.0.1:7890'
}
CLASH_API_URL = 'http://127.0.0.1:9090'
PROXY_GROUP_NAME = 'Proxies'

if USE_CLASH:
    response = requests.get(CLASH_API_URL + '/proxies')
    proxies = json.loads(response.text)['proxies'][PROXY_GROUP_NAME]['all']
    proxies.pop(0)  # remove DIRECT

    requests.put(CLASH_API_URL + '/proxies/' + PROXY_GROUP_NAME, data='{"name":"DIRECT"}')


def switch_proxy():
    next_proxy = proxies.pop(random.randint(0, len(proxies) - 1))
    data = '{"name":"' + next_proxy + '"}'
    requests.put(CLASH_API_URL + '/proxies/' + PROXY_GROUP_NAME, data=data.encode('utf-8'))
    requests.delete(CLASH_API_URL + '/connections')
