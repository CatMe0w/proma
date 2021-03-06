import json
import sys
import pytz
import sqlite3
import time
import logging
import util.crawler as crawler
import util.content_parser_mobile as content_parser_mobile
import util.content_parser_web as content_parser_web
import util.album_fix as album_fix
from pathlib import Path
from datetime import datetime
from bs4 import BeautifulSoup, Comment


def main(tieba_name):
    logging.basicConfig(
        format='%(asctime)s [%(levelname)s] %(message)s',
        level=logging.INFO,
        handlers=[
            logging.FileHandler('proma.log', encoding='utf-8'),
            logging.StreamHandler()
        ])

    logging.info('''
    Starting proma
    
    Target: {}
    
    Weigh anchor!
    '''.format(tieba_name))

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
        tail text,
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
    logging.info('Stage 1: Getting thread lists')
    Path("./proma-raw/threads").mkdir(parents=True, exist_ok=True)

    max_page = 1
    page = 1
    while True:
        pn_param = (page - 1) * 50
        params = (
            ('kw', tieba_name),
            ('ie', 'utf-8'),
            ('pn', str(pn_param)),
        )

        logging.info("Current page: threads, {} of {}".format(page, max_page))
        response = crawler.nice_get('https://tieba.baidu.com/f', headers=crawler.STANDARD_HEADERS, params=params)

        content = response.content
        with open('./proma-raw/threads/{}.html'.format(page), 'wb') as f:
            f.write(content)

        # 获取正文的HTML
        soup = BeautifulSoup(content, 'html.parser')  # lxml在不同操作系统上的行为可能不一致
        comments = soup.find_all(text=lambda text: isinstance(text, Comment))
        if page == 1:
            soup = BeautifulSoup(comments[-3], 'lxml')  # 个别标题含有会使html.parser出错的字符串
            if not soup.get_text():
                soup = BeautifulSoup(comments[-2], 'lxml')  # 有时个别贴吧正文之后的空注释会少一个
        else:
            soup = BeautifulSoup(comments[-12], 'lxml')

        # 获取每个帖子的id、回复数、是否为精品
        thread_entry_html = soup.find_all('li', class_='j_thread_list')
        thread_entries = []
        for thread_entry in thread_entry_html:
            data_field = json.loads(thread_entry['data-field'])
            if data_field['id'] == 1:  # 去除“本吧吧主火热招募中”
                continue
            thread_entries.append(data_field)

        # 获取每个帖子的标题
        title_html = soup.find_all('a', class_='j_th_tit')
        if title_html[0]['title'] == '本吧吧主火热招募中，点击参加':  # 去除“本吧吧主火热招募中”
            title_html.pop(0)
        for title, i in zip(title_html, range(len(title_html))):
            thread_entries[i].update({'title': title['title']})

        # 获取每个帖子的user_id
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

            db.execute('insert or ignore into thread values (?,?,?,?,?)', (
                thread_entry['id'],
                thread_entry['title'],
                thread_entry['user_id'],
                thread_entry['reply_num'],
                is_good
            ))
        conn.commit()

        if page == 1:
            max_page = int(int(response.text.split('" class="last pagination-item')[0].split('&pn=')[-1]) / 50 + 1)  # 用soup搜索class有概率失败，弄个土办法
            logging.info('Max pages: {}'.format(max_page))
        if page == max_page:
            break
        else:
            page += 1
    logging.info('Finished getting thread lists')

    # 获取帖子内容
    logging.info('Stage 2: Getting posts & comments')
    thread_ids = [_[0] for _ in db.execute('select id from thread')]

    for thread_id in thread_ids:
        # 获取一个帖子里的所有楼层
        pseudo_page = 1
        prev_offset = -1  # 用于判断一个帖子是否无法翻页（包含损坏数据）
        next_page_post_id = None
        while True:
            while True:
                try:
                    response = crawler.get_post_mobile(thread_id, pseudo_page, next_page_post_id)
                    post_data = json.loads(response.content)
                    if post_data['error_code'] != '0':
                        raise ValueError
                except (ValueError, UnicodeDecodeError):
                    logging.warning('Bad response, wait for 5s.')
                    time.sleep(5)
                else:
                    break

            for user in post_data['user_list']:
                if user.get('name') == '':
                    user['name'] = None
                db.execute('insert or ignore into user values (?,?,?,?)', (
                    user['id'],
                    user.get('name'),  # IP匿名用户没有name
                    user['name_show'],
                    user['portrait']
                ))
            for post in post_data['post_list']:
                post_time = datetime.fromtimestamp(
                    int(post['time']),
                    pytz.timezone('Asia/Shanghai')
                ).strftime("%Y-%m-%d %H:%M:%S")
                db.execute('insert or ignore into post values (?,?,?,?,?,?,?,?,?)', (
                    # Why "or ignore": next_page_post_id这一楼层自身会重复出现一次
                    post['id'],
                    post['floor'],
                    post['author_id'],
                    content_parser_mobile.parse(post['content']),
                    post_time,
                    post['sub_post_number'],
                    None,
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
                            logging.warning('Bad response, wait for 5s.')
                            time.sleep(5)
                        else:
                            break

                    for comment in comment_data['subpost_list']:
                        if comment['author']['name'] == '':
                            comment['author']['name'] = None
                        db.execute('insert or ignore into user values (?,?,?,?)', (
                            comment['author']['id'],
                            comment['author']['name'],
                            comment['author']['name_show'],
                            comment['author']['portrait']
                        ))

                        comment_time = datetime.fromtimestamp(
                            int(comment['time']),
                            pytz.timezone('Asia/Shanghai')
                        ).strftime("%Y-%m-%d %H:%M:%S")
                        db.execute('insert or ignore into comment values (?,?,?,?,?)', (
                            # Why "or ignore": 若某next_page_post_id存在楼中楼，则这些楼中楼也会重复
                            comment['id'],
                            comment['author']['id'],
                            content_parser_mobile.parse(comment['content']),
                            comment_time,
                            comment_data['post']['id']
                        ))
                    conn.commit()
                    if current_page == int(comment_data['page']['total_page']):
                        break
                    if int(comment_data['page']['total_page']) == 0:
                        logging.warning('Malformed data received. Rate limit probably exceeded. Sleep for 30s.')
                        time.sleep(30)
                        continue
                    else:
                        current_page += 1

            if prev_offset == post_data['page']['offset']:
                logging.warning('Malformed data received. It seems this thread has corrupted data and it is impossible to get an intact copy.')
                break
            prev_offset = post_data['page']['offset']

            if int(post_data['page']['total_page']) > int(post_data['page']['current_page']):
                next_page_post_id = post_data['post_list'][-1]['id']
                pseudo_page += 1
            else:
                break
    logging.info('Finished getting posts & comments')

    # 修复图片帖子
    # 移动端接口获取的图片帖子内容为空
    logging.info('Stage 3: Fixing image posts')
    params = (
        ('kw', tieba_name),
        ('ie', 'utf-8'),
        ('tab', 'album'),
    )

    logging.info('Getting album catalog')
    Path('./proma-raw/albums').mkdir(parents=True, exist_ok=True)
    response = crawler.nice_get('https://tieba.baidu.com/f', headers=crawler.STANDARD_HEADERS, params=params)

    with open('./proma-raw/albums/catalog.html', 'wb') as f:
        f.write(response.content)

    soup = BeautifulSoup(response.content, 'html.parser')
    comments = soup.find_all(text=lambda text: isinstance(text, Comment))
    soup = BeautifulSoup(comments[-4], 'html.parser')

    albums = soup.find_all('a', class_='grbm_ele_a')
    for album in albums:
        thread_id = album['href'].strip('/p/')

        params = (
            ('kw', tieba_name),
            ('alt', 'jview'),
            ('rn', '200'),
            ('tid', str(thread_id)),
            ('pn', '1'),
            ('ps', '1'),
            ('pe', '1000'),
            ('info', '1'),
        )
        logging.info('Current page: albums, thread_id {}'.format(thread_id))
        while True:
            response = crawler.nice_get('https://tieba.baidu.com/photo/g/bw/picture/list', headers=crawler.STANDARD_HEADERS, params=params, encoding='gbk')
            if '<!DOCTYPE html>' not in response.text:  # 有极小概率返回HTML格式的404页面
                break
            else:
                logging.warning('Bad response, retrying.')
                continue
        with open('./proma-raw/albums/{}.json'.format(thread_id), 'wb') as f:
            f.write(response.content)

        db.execute('update post set content = ? where thread_id = ? and floor = 1', (
            album_fix.fix(response.content),
            thread_id
        ))
        conn.commit()
    logging.info('Finished fixing albums')

    # 补完post表
    # 通过web版补充移动端缺失的正文换行符、签名档、小尾巴（即“来自掌上百度”或“来自Android客户端”等）
    logging.info('Stage 4: Fixing posts')
    for thread_id in thread_ids:
        page = 1
        while True:
            response = crawler.get_post_web(thread_id, page)
            soup = BeautifulSoup(response.content, 'html.parser')
            max_page = int(soup.find_all('li', class_='l_reply_num')[0].get_text().strip('页').split('回复贴，共')[-1])

            posts = soup.find_all('div', class_='l_post')
            for post in posts:
                # 补充签名档和小尾巴
                post_id = post['data-pid']
                signature = post.find('img', class_='j_user_sign')
                if signature is not None:
                    signature = signature['src'].strip('?v=tbs')
                tail = post.find('span', class_='tail-info').get_text()
                if tail.endswith('楼'):
                    tail = None

                if tail == '来自手机贴吧':
                    flag_bad_client = True  # 见content_parser_web.py注释
                else:
                    flag_bad_client = False

                # 修复正文换行符、加粗与红字
                try:
                    content_db = json.loads(db.execute('select content from post where id = ?', (post_id,)).fetchall()[0][0])
                except IndexError:
                    logging.warning('Post {} not found in database, skipping.'.format(post_id))
                    continue
                content_web = post.find('div', class_='d_post_content')
                content_fixed = content_parser_web.parse_and_fix(content_web, content_db, flag_bad_client)
                if content_fixed is None:
                    db.execute('update post set signature = ?, tail = ? where id = ?', (
                        signature,
                        tail,
                        post_id
                    ))
                else:
                    db.execute('update post set content = ?, signature = ?, tail = ? where id = ?', (
                        content_fixed,
                        signature,
                        tail,
                        post_id
                    ))

            conn.commit()

            if page < max_page:
                page += 1
            else:
                break
    logging.info('Finished fixing posts')
    conn.close()
    logging.info('All done! Have fun!')


if __name__ == '__main__':
    if not sys.argv[1:]:
        print('Usage: python3 {} <tieba_name>'.format(sys.argv[0]))
        exit(1)
    main(str(sys.argv[1]))
