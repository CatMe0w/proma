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
    id numeric not null,
    username text,
    nickname text,
    avatar text not null,
    exp numeric not null)''')
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

    soup = BeautifulSoup(content, 'html.parser')
    # 此处必须使用html.parser而非lxml：原始HTML将所有帖子内容注释，lxml会直接丢弃这些包含HTML的注释块
    comments = soup.find_all(text=lambda text: isinstance(text, Comment))
    thread_list_html = comments[40]
    thread_list_soup = BeautifulSoup(thread_list_html, 'lxml')

    reply_num_html = thread_list_soup.find_all('span', class_='threadlist_rep_num')
    reply_nums = []
    for reply_num in reply_num_html:
        reply_nums.append(reply_num.text)

    title_html = thread_list_soup.find_all('a', class_='j_th_tit')
    titles = []
    thread_ids = []
    for title in title_html:
        titles.append(title.text)
        thread_ids.append(title['href'].strip('/p/'))

    username_html = soup.find_all('a', class_='frs-author-name')
    usernames = []
    for username in username_html:
        username = username['data-field'].strip('{\"un":\"').split('\",\"id')[0]
        usernames.append(username)

    thread_entry_html = thread_list_soup.find_all('li', class_='j_thread_list')
    is_goods = []
    for is_good in thread_entry_html:
        data_field = json.loads(is_good['data-field'])
        is_goods.append(int(data_field['is_good']))

# 获取帖子内容

# 补完user表

# 补完post表
# 正文一列采用web端作为数据源，其余采用移动端
