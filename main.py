import hashlib
import time
import sqlite3
import requests
from pathlib import Path

TIEBA_NAME = ''
MAX_PAGE = 1

print('''
Starting proma

Target: {}
Max page: {}

Weigh anchor!
'''.format(TIEBA_NAME, MAX_PAGE))

conn = sqlite3.connect('proma.db')
db = conn.cursor()
db.execute('''
    create table thread(
    id numeric not null,
    title text not null,
    username text not null,
    reply_num numeric not null,
    is_good numeric not null)''')
db.execute('''
    create table post(
    id numeric not null,
    floor numeric not null,
    content text,
    time text not null,
    comment_num numeric not null,
    signature text,
    thread_id numeric not null,
    foreign key(thread_id) references thread(id))''')
db.execute('''
    create table comment(
    id numeric not null,
    username text not null,
    content text,
    time text not null,
    post_id numeric not null,
    foreign key(post_id) references post(id))''')
db.execute('''
    create table user(
    username text not null,
    nickname text,
    avatar text not null,
    exp numeric not null)''')
conn.commit()

# 获取帖子目录
# 帖子目录（吧主页）仅采集web端
Path("./proma-raw/web/threads").mkdir(parents=True, exist_ok=True)

headers = {
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

for i in range(1, MAX_PAGE + 1):
    pn_param = (i - 1) * 50
    params = (
        ('kw', TIEBA_NAME),
        ('ie', 'utf-8'),
        ('pn', str(pn_param)),
    )

    while True:
        try:
            print("Current page: threads, {} of {}".format(i, MAX_PAGE))
            response = requests.get('https://tieba.baidu.com/f', headers=headers, params=params)
        except requests.exceptions.Timeout:
            print("Remote is not responding, sleep for 30s.")
            time.sleep(30)
            continue
        else:
            break

    content = response.content
    with open('./proma-raw/threads/{}.html'.format(i), 'wb') as f:
        f.write(content)

# 获取帖子内容
Path("./proma-raw/mobile/posts").mkdir(parents=True, exist_ok=True)
Path("./proma-raw/mobile/comments").mkdir(parents=True, exist_ok=True)
Path("./proma-raw/web/posts").mkdir(parents=True, exist_ok=True)
Path("./proma-raw/web/totalcomments").mkdir(parents=True, exist_ok=True)
Path("./proma-raw/web/comments").mkdir(parents=True, exist_ok=True)


# 以下函数用于从移动端接口获取数据
def add_sign(data):
    # 特别鸣谢 https://github.com/cnwangjihe/TiebaBackup
    _ = ""
    keys = sorted(data.keys())
    for key in keys:
        _ += key + "=" + data[key]
    sign = hashlib.md5((_ + 'tiebaclient!!!').encode("utf-8")).hexdigest().upper()
    data.update({"sign": str(sign)})
    return data


def get_post_mobile(thread_id, pseudo_page, post_id=None):
    # 获取帖子内容的移动端接口没有翻页参数，只能通过指定最后一层楼的post_id，来获取这一层楼往后的30层楼，以此达到翻页效果
    if post_id is None:
        data = {'kz': thread_id, '_client_version': '9.9.8.32'}
    else:
        data = {'kz': thread_id, 'pid': str(post_id), '_client_version': '9.9.8.32'}
    data_signed = add_sign(data)
    resp = requests.post('https://tieba.baidu.com/c/f/pb/page', data=data_signed)
    with open('./proma-raw/mobile/posts/{}/{}.json'.format(thread_id, pseudo_page), 'wb') as f:
        f.write(resp.content)
    return resp


def get_comment_mobile(thread_id, post_id, page):
    data = {'kz': thread_id, 'pid': str(post_id), 'pn': str(page), '_client_version': '9.9.8.32'}
    data_signed = add_sign(data)
    resp = requests.post('https://tieba.baidu.com/c/f/pb/floor', data=data_signed)
    with open('./proma-raw/mobile/comments/{}/{}/{}.json'.format(thread_id, post_id, page), 'wb') as f:
        f.write(resp.content)
    return resp


# 以下函数用于从网页端（电脑版）获取数据
def get_post_web(thread_id, page):
    params = (
        ('pn', str(page)),
    )
    resp = requests.get('https://tieba.baidu.com/p/' + str(thread_id), headers=headers, params=params)
    with open('./proma-raw/web/posts/{}/{}.json'.format(thread_id, page), 'wb') as f:
        f.write(resp.content)
    return resp


def get_totalcomment_web(thread_id, page):
    # "totalComment"是在帖子加载时就立即发送的XHR，返回内容为这一页中，每一个楼中楼的前10条回复，格式为JSON
    params = (
        ('tid', str(thread_id)),
        ('pn', str(page)),
    )
    resp = requests.get('https://tieba.baidu.com/p/totalComment', headers=headers, params=params)
    with open('./proma-raw/web/totalcomments/{}/{}.json'.format(thread_id, page), 'wb') as f:
        f.write(resp.content)
    return resp


def get_comment_web(thread_id, post_id, page):
    # 获取特定楼中楼某一页的回复，格式为HTML
    params = (
        ('tid', str(thread_id)),
        ('pid', str(post_id)),
        ('pn', str(page)),
    )
    resp = requests.get('https://tieba.baidu.com/p/comment', headers=headers, params=params)
    with open('./proma-raw/web/comments/{}/{}/{}.json'.format(thread_id, post_id, page), 'wb') as f:
        f.write(resp.content)
    return resp

# 补完user表

# 补完post表
# 正文一列采用web端作为数据源，其余采用移动端
