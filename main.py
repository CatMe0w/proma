import json
import pytz
import sqlite3
import util.crawler as crawler
import util.content_parser as content_parser
from pathlib import Path
from datetime import datetime
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
    id numeric primary key not null,
    username text,
    nickname text,
    avatar text not null)''')
db.execute('''
    create table thread(
    id numeric primary key not null,
    title text not null,
    user_id text not null,
    reply_num numeric not null,
    is_good numeric not null,
    foreign key(user_id) references user(id))''')
db.execute('''
    create table post(
    id numeric primary key not null,
    floor numeric not null,
    user_id text not null,
    content text,
    time text not null,
    comment_num numeric not null,
    signature text,
    thread_id numeric not null,
    foreign key(user_id) references user(id),
    foreign key(thread_id) references thread(id))''')
db.execute('''
    create table comment(
    id numeric primary key not null,
    user_id text not null,
    content text,
    time text not null,
    post_id numeric not null,
    foreign key(user_id) references user(id),
    foreign key(post_id) references post(id))''')
conn.commit()

# 获取帖子目录
for page in range(1, MAX_PAGE + 1):
    response = crawler.get_thread_list_mobile(TIEBA_NAME, page, MAX_PAGE)
    thread_list_data = json.loads(response.content)
    for user in thread_list_data['user_list']:
        db.execute('insert or ignore into user values (?,?,?,?)', (
            user['id'],
            user.get('name'),  # IP匿名用户没有name
            user['name_show'],
            user['portrait']  # XXX
        ))
    for thread in thread_list_data['thread_list']:
        db.execute('insert into post values (?,?,?,?,?)', (
            thread['id'],
            thread['title'],
            thread['author_id'],
            thread['reply_num'],
            thread['is_good']
        ))
    conn.commit()

# 获取帖子内容
thread_ids = [_[0] for _ in db.execute('select id from thread')]

next_page_post_id = None
pseudo_page = 1
for thread_id in thread_ids:
    response = crawler.get_post_mobile(thread_id, pseudo_page, next_page_post_id)
    post_data = json.loads(response.content)
    for user in post_data['user_list']:
        db.execute('insert or ignore into user values (?,?,?,?)', (
            user['id'],
            user.get('name'),  # IP匿名用户没有name
            user['name_show'],
            user['portrait']  # XXX
        ))
    for post in post_data['post_list']:
        post_time = datetime.fromtimestamp(
            int(post['time']),
            pytz.timezone('Asia/Shanghai')
        ).strftime("%Y-%m-%d %H:%M:%S")
        db.execute('insert into post values (?,?,?,?,?,?,?,?)', (
            post['id'],
            post['floor'],
            post['author_id'],
            content_parser.parse(post['content']),
            post_time,
            post['sub_post_number'],
            None,
            thread_id
        ))
    conn.commit()

    # 获取楼中楼
    has_comment_post_ids = []
    for post in post_data['post_list']:
        if post['sub_post_number'] != 0:
            has_comment_post_ids.append(post['id'])
    for post_id in has_comment_post_ids:
        current_page = 1
        while True:
            response = crawler.get_comment_mobile(thread_id, post_id, current_page)
            comment_data = json.loads(response.content)
            if not comment_data['subpost_list']:
                break  # 正常情况下，每页楼中楼有30条评论，但经常会出现小于30的情况，因此不推测楼中楼的实际页码，一直循环到没有评论为止
            for comment in comment_data['subpost_list']:
                db.execute('insert or ignore into user values (?,?,?,?)', (
                    comment['author']['id'],
                    comment['author']['name'],
                    comment['author']['name_show'],
                    comment['author']['portrait']  # XXX
                ))

                comment_time = datetime.fromtimestamp(
                    int(comment['time']),
                    pytz.timezone('Asia/Shanghai')
                ).strftime("%Y-%m-%d %H:%M:%S")
                db.execute('insert or ignore into comment values (?,?,?,?,?)', (
                    # Why "or ignore": next_page_post_id这一楼层自身会重复出现一次
                    comment['id'],
                    comment['author']['id'],
                    content_parser.parse(comment['content']),
                    comment_time,
                    comment_data['post']['id']
                ))
            conn.commit()
            current_page += 1

    next_page_post_id = post_data['post_list'][-1]['id']
    pseudo_page += 1

# 补完post表
# 正文一列采用web端作为数据源，其余采用移动端
