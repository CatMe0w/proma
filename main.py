import json
import pytz
import sqlite3
import time
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
    user_id numeric not null,
    reply_num numeric not null,
    is_good numeric not null,
    foreign key(user_id) references user(id))''')
db.execute('''
    create table post(
    id numeric primary key not null,
    floor numeric not null,
    user_id numeric not null,
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
    user_id numeric not null,
    content text,
    time text not null,
    post_id numeric not null,
    foreign key(user_id) references user(id),
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

    soup = BeautifulSoup(content, 'html.parser')  # lxml在不同操作系统上的行为可能不一致
    comments = soup.find_all(text=lambda text: isinstance(text, Comment))
    if page == 1:
        soup = BeautifulSoup(comments[-3], 'html.parser')
    else:
        soup = BeautifulSoup(comments[-12], 'html.parser')

    thread_entry_html = soup.find_all('li', class_='j_thread_list')
    thread_entries = []
    for thread_entry in thread_entry_html:
        data_field = json.loads(thread_entry['data-field'])
        thread_entries.append(data_field)

    title_html = soup.find_all('a', class_='j_th_tit')
    for title, i in zip(title_html, range(len(title_html))):
        thread_entries[i].update({'title': title.contents[0]})

    user_id_html = soup.find_all('span', class_='tb_icon_author')
    for user_id, i in zip(user_id_html, range(len(user_id_html))):
        user_id_dict = json.loads(user_id['data-field'])
        thread_entries[i].update(user_id_dict)

    for thread_entry in thread_entries:
        if thread_entry['author_name'] == '':
            thread_entry['author_name'] = None

        if thread_entry['is_good'] is True:
            is_good = 1
        else:
            is_good = 0

        db.execute('insert or ignore into user values (?,?,?,?)', (
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
            is_good
        ))
    conn.commit()

# 获取帖子内容
thread_ids = [_[0] for _ in db.execute('select id from thread')]

for thread_id in thread_ids:
    # 获取一个帖子里的所有楼层
    pseudo_page = 1
    next_page_post_id = None
    while True:
        while True:
            try:
                response = crawler.get_post_mobile(thread_id, pseudo_page, next_page_post_id)
                post_data = json.loads(response.content)
                if post_data['error_code'] != '0':
                    raise ValueError
            except (ValueError, UnicodeDecodeError):
                print('Bad response, wait for 30s.')
                time.sleep(30)
            else:
                break

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
            db.execute('insert or ignore into post values (?,?,?,?,?,?,?,?)', (
                # Why "or ignore": next_page_post_id这一楼层自身会重复出现一次
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
            if post['sub_post_number'] != '0':
                has_comment_post_ids.append(post['id'])
        for post_id in has_comment_post_ids:
            current_page = 1
            while True:
                while True:
                    try:
                        response = crawler.get_comment_mobile(thread_id, post_id, current_page)
                        comment_data = json.loads(response.content)
                        if comment_data['error_code'] != '0':
                            raise ValueError
                    except (ValueError, UnicodeDecodeError):
                        print('Bad response, wait for 30s.')
                        time.sleep(30)
                    else:
                        break

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
                        # Why "or ignore": 若某next_page_post_id存在楼中楼，则这些楼中楼也会重复
                        comment['id'],
                        comment['author']['id'],
                        content_parser.parse(comment['content']),
                        comment_time,
                        comment_data['post']['id']
                    ))
                conn.commit()
                if current_page == int(comment_data['page']['total_page']):
                    break
                else:
                    current_page += 1

        if post_data['page']['has_more'] == '1':
            next_page_post_id = post_data['post_list'][-1]['id']
            pseudo_page += 1
        else:
            break

# 补完post表
# 正文一列采用web端作为数据源，其余采用移动端
