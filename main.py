import math
import json
import sqlite3
import util.crawler as crawler
from pathlib import Path
from bs4 import BeautifulSoup, Comment

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
    create table user(
    id numeric not null,
    username text,
    nickname text,
    avatar text not null)''')
db.execute('''
    create table thread(
    id numeric not null,
    title text not null,
    user_id text not null,
    reply_num numeric not null,
    is_good numeric not null,
    foreign key(user_id) references user(id))''')
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
conn.commit()

# 获取帖子目录
# 帖子目录（吧主页）仅采集web端
Path("./proma-raw/thread_lists").mkdir(parents=True, exist_ok=True)

for page in range(1, MAX_PAGE + 1):
    pn_param = (page - 1) * 50
    params = (
        ('kw', TIEBA_NAME),
        ('ie', 'utf-8'),
        ('pn', str(pn_param)),
    )

    print("Current page: threads, {} of {}".format(page, MAX_PAGE))
    response = crawler.nice_get('https://tieba.baidu.com/f', headers=crawler.STANDARD_HEADERS, params=params)

    content = response.content
    with open('./proma-raw/thread_lists/{}.html'.format(page), 'wb') as f:
        f.write(content)

    soup = BeautifulSoup(content, 'lxml')
    comments = soup.find_all(text=lambda text: isinstance(text, Comment))

    thread_entry_html = soup.find_all('li', class_='j_thread_list')
    thread_entries = []
    for thread_entry in thread_entry_html:
        data_field = json.loads(thread_entry['data-field'])
        thread_entries.append(data_field)

    title_html = soup.find_all('a', class_='j_th_tit')
    for title, i in zip(title_html, range(len(title_html))):
        thread_entries[i].update({'title': title})

    user_id_html = soup.find_all('span', class_='tb_icon_author')
    for user_id, i in zip(user_id_html, range(len(user_id_html))):
        user_id_dict = json.loads(user_id['data-field'])
        thread_entries[i].update(user_id_dict)

    for thread_entry in thread_entries:
        db.execute('insert into user values (?,?,?,?)', (
            thread_entry['user_id'],
            thread_entry['author_name'],
            thread_entry['author_nickname'],
            thread_entry['author_portrait']
        ))
        db.execute('insert into thread values (?,?,?,?,?)', (
            thread_entry['id'],
            thread_entry['title'],
            thread_entry['user_id'],
            thread_entry['reply_num'],
            thread_entry['is_good']
        ))
    conn.commit()

# 获取帖子内容
thread_ids = [_[0] for _ in db.execute('select id from thread')]

next_page_post_id = None
pseudo_page = 1
for thread_id in thread_ids:
    response = crawler.get_post_web(thread_id, pseudo_page, next_page_post_id)
    post_data = json.loads(response.content)

    # 获取楼中楼
    has_comment_posts = []
    for post in post_data['post_list']:
        if post['sub_post_number'] != 0:
            page = math.ceil(int(post['sub_post_number']) / 10)
            has_comment_post = {'id': post['id'], 'page': str(page)}
            has_comment_posts.append(has_comment_post)
    for post_id in has_comment_posts:
        response = crawler.get_comment_mobile(thread_id, post_id, page)

    next_page_post_id = post_data['post_list'][-1]['id']
    pseudo_page += 1

# 补完user表

# 补完post表
# 正文一列采用web端作为数据源，其余采用移动端
