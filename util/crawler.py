import time
import hashlib
import requests
from pathlib import Path

STANDARD_HEADERS = {
    'Connection': 'keep-alive',
    'Pragma': 'no-cache',
    'Cache-Control': 'no-cache',
    'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="96", "Google Chrome";v="96"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'DNT': '1',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-User': '?1',
    'Sec-Fetch-Dest': 'document',
    'Accept-Language': 'zh-CN,zh;q=0.9',
}


def nice_get(url, headers=None, params=None):
    while True:
        try:
            response = requests.get(url, headers=headers, params=params)
            if response.status_code is not 200:
                raise NotImplementedError
        except requests.exceptions.Timeout:
            print("Remote is not responding, sleep for 30s.")
            time.sleep(30)
            continue
        else:
            return response


def nice_post(url, data=None):
    while True:
        try:
            response = requests.post(url, data=data)
            if response.status_code is not 200:
                raise NotImplementedError
        except requests.exceptions.Timeout:
            print("Remote is not responding, sleep for 30s.")
            time.sleep(30)
            continue
        else:
            return response


# 以下函数用于从移动端接口获取数据
def add_sign(data):
    # 特别鸣谢 https://github.com/cnwangjihe/TiebaBackup
    _ = ""
    keys = sorted(data.keys())
    for key in keys:
        _ += key + "=" + data[key]
    sign = hashlib.md5((_ + 'tiebaclient!!!').encode('utf-8')).hexdigest().upper()
    data.update({"sign": str(sign)})
    return data


def get_post_mobile(thread_id, pseudo_page, post_id=None):
    # 获取帖子内容的移动端接口没有翻页参数，只能通过指定最后一层楼的post_id，来获取这一层楼往后的30层楼，以此达到翻页效果
    Path('./proma-raw/mobile/posts').mkdir(parents=True, exist_ok=True)
    print('Current page: posts, thread_id {}, page {}, using mobile api'.format(thread_id, pseudo_page))

    if post_id is None:
        data = {'kz': thread_id, '_client_version': '9.9.8.32'}
    else:
        data = {'kz': thread_id, 'pid': str(post_id), '_client_version': '9.9.8.32'}
    data_signed = add_sign(data)
    response = nice_post('https://tieba.baidu.com/c/f/pb/page', data=data_signed)
    with open('./proma-raw/mobile/posts/{}/{}.json'.format(thread_id, pseudo_page), 'wb') as f:
        f.write(response.content)
    return response


def get_comment_mobile(thread_id, post_id, page):
    Path('./proma-raw/mobile/comments').mkdir(parents=True, exist_ok=True)
    print('Current page: comments, thread_id {}, post_id {}, page {}, using mobile api'.format(thread_id, post_id, page))

    data = {'kz': thread_id, 'pid': str(post_id), 'pn': str(page), '_client_version': '9.9.8.32'}
    data_signed = add_sign(data)
    response = nice_post('https://tieba.baidu.com/c/f/pb/floor', data=data_signed)
    with open('./proma-raw/mobile/comments/{}/{}/{}.json'.format(thread_id, post_id, page), 'wb') as f:
        f.write(response.content)
    return response


# 以下函数用于从网页端（电脑版）获取数据
def get_post_web(thread_id, page):
    Path("./proma-raw/web/posts").mkdir(parents=True, exist_ok=True)
    print('Current page: posts, thread_id {}, page {}'.format(thread_id, page))

    params = (
        ('pn', str(page)),
    )
    response = nice_get('https://tieba.baidu.com/p/' + str(thread_id), headers=STANDARD_HEADERS, params=params)
    with open('./proma-raw/web/posts/{}/{}.json'.format(thread_id, page), 'wb') as f:
        f.write(response.content)
    return response


# 以下两个函数不一定用得上，移动端接口的数据完整性或许已经可以满足需求
def get_totalcomment_web(thread_id, page):
    # "totalComment"是在帖子加载时就立即发送的XHR，返回内容为这一页中，每一个楼中楼的前10条回复，格式为JSON
    Path("./proma-raw/web/totalcomments").mkdir(parents=True, exist_ok=True)
    print('Current page: totalComments, thread_id {}, page {}'.format(thread_id, page))

    params = (
        ('tid', str(thread_id)),
        ('pn', str(page)),
    )
    response = nice_get('https://tieba.baidu.com/p/totalComment', headers=STANDARD_HEADERS, params=params)
    with open('./proma-raw/web/totalcomments/{}/{}.json'.format(thread_id, page), 'wb') as f:
        f.write(response.content)
    return response


def get_comment_web(thread_id, post_id, page):
    # 获取特定楼中楼某一页的回复，格式为HTML
    Path("./proma-raw/web/comments").mkdir(parents=True, exist_ok=True)
    print('Current page: thread_id {}, post_id {}, page {}'.format(thread_id, post_id, page))

    params = (
        ('tid', str(thread_id)),
        ('pid', str(post_id)),
        ('pn', str(page)),
    )
    response = nice_get('https://tieba.baidu.com/p/comment', headers=STANDARD_HEADERS, params=params)
    with open('./proma-raw/web/comments/{}/{}/{}.html'.format(thread_id, post_id, page), 'wb') as f:
        f.write(response.content)
    return response