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

# get thread list
Path("./proma-raw/threads").mkdir(parents=True, exist_ok=True)

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

# get posts
Path("./proma-raw/posts").mkdir(parents=True, exist_ok=True)
Path("./proma-raw/comments").mkdir(parents=True, exist_ok=True)

# fix up user table
