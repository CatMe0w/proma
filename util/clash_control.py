import json
import random
import requests

USE_CLASH = True  # Clash/代理池总开关
PROXIES = {
    "http": 'http://127.0.0.1:7890',
    "https": 'http://127.0.0.1:7890'
}  # HTTP代理地址
CLASH_API_URL = 'http://127.0.0.1:9090'  # Clash RESTful API地址
PROXY_GROUP_NAME = 'Proxies'  # Clash代理组名称；此外，请将此代理组的第一个节点设置为DIRECT，程序会首先使用直连，被限制后再使用代理

if USE_CLASH:
    response = requests.get(CLASH_API_URL + '/proxies')
    proxies = json.loads(response.text)['proxies'][PROXY_GROUP_NAME]['all']
    proxies.pop(0)  # remove DIRECT

    requests.put(CLASH_API_URL + '/proxies/' + PROXY_GROUP_NAME, data='{"name":"DIRECT"}')


def switch_proxy():
    next_proxy = proxies[random.randint(0, len(proxies) - 1)]
    data = '{"name":"' + next_proxy + '"}'
    requests.put(CLASH_API_URL + '/proxies/' + PROXY_GROUP_NAME, data=data.encode('utf-8'))
    requests.delete(CLASH_API_URL + '/connections')
