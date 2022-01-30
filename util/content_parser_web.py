import json
import logging


def parse_image(url):
    return 'https://imgsrc.baidu.com/forum/pic/item/' + url.split('/')[-1]


def parse_and_fix(html, content_db, flag_bad_client):
    for item in content_db:
        if item['type'] == 'video' or item['type'] == 'audio' or item['type'] == 'album':
            return None  # 含有以上类型的正文，不处理

    parsed_data = []
    is_initial = True
    for item in html.contents:
        if not item.name:  # 纯文本
            if is_initial:
                parsed_data.append({'type': 'text', 'content': item.string.lstrip()})
            elif parsed_data[-1]['type'] == 'text':
                parsed_data[-1]['content'] += item.string
            else:
                parsed_data.append({'type': 'text', 'content': item.string})

        elif item.name == 'br':  # 换行符
            if parsed_data[-1]['type'] == 'text':
                parsed_data[-1]['content'] += '\n'
            else:
                parsed_data.append({'type': 'text', 'content': '\n'})

        elif item.name == 'strong':  # 加粗纯文本
            parsed_data.append({'type': 'text_bold', 'content': item.string})

        elif item.name == 'span' and item['class'] == ['edit_font_color']:  # 红字纯文本
            parsed_data.append({'type': 'text_red', 'content': item.string})

        elif item.name == 'img':
            if item['class'] == ['BDE_Image'] or item['class'] == ['BDE_Meme'] or item['class'] == ['BDE_Graffiti'] or item['class'] == ['BDE_Smiley2']:
                parsed_data.append({'type': 'image', 'content': parse_image(item['src'])})
            elif item['class'] == ['BDE_Smiley3'] or item['class'] == ['BDE_Colorful']:
                parsed_data.append({'type': 'image', 'content': item['src']})
            elif item['class'] == ['BDE_Smiley']:
                if item['src'].endswith('.gif') and flag_bad_client:
                    # 对于flag_bad_client为True的帖子，.gif格式的表情不会出现在移动端接口中，因此使用image type记录以避免StopIteration
                    parsed_data.append({'type': 'image', 'content': item['src']})
                else:
                    parsed_data.append({'type': 'emoticon', 'content': None})  # 不实现，下同，将通过移动端数据修复
            else:
                logging.critical('Unhandled element: {}'.format(item))

        elif item.name == 'a':
            if item.get('class') == ['at']:  # 用户名（at）
                parsed_data.append({'type': 'username', 'content': None})
            elif item.get('class') == ['j-no-opener-url']:  # 链接
                parsed_data.append({'type': 'url', 'content': None})
            else:
                if parsed_data[-1]['type'] == 'text':
                    parsed_data[-1]['content'] += item.string
                else:
                    parsed_data.append({'type': 'text', 'content': item.string})

        elif item.get('class') == ['save_face_post']:  # 挽尊卡
            parsed_data.append({'type': 'text', 'content': item.text})

        elif item.name == 'embed':  # Flash音乐播放器，丢弃
            pass

        elif item.get('class') == ['post_bubble_top'] or item.get('class') == ['pic_src_wrapper'] or item.get('class') == ['album_pb_comment_container']:
            return None
            # 直接放弃使用了奇怪气泡的帖子
            # 这个项目的复杂程度早已远超我的预料，若按计划，项目的规模绝不应该膨胀到现在这个状况
            # 随着需要专门处理的edge case不断增多，程序的鲁棒性也肉眼可见地暴跌
            # 使用了奇怪气泡的帖子大多都是回复，而且往往没有复杂的格式，再加上它们的数量非常少
            # 所以，对于这类帖子，直接保留原来数据库中的content吧
            #
            # 补充：追加pic_src_wrapper，即“通过百度相册上传”，无需修复；album_pb_comment_container，图贴相关，无需修复

        else:
            logging.critical('Unhandled element: {}'.format(item))
        is_initial = False

    if parsed_data[0] == {'type': 'text', 'content': ''}:
        parsed_data.pop(0)

    extra_data = []
    for item in content_db:
        if item['type'] == 'emoticon' or item['type'] == 'username' or item['type'] == 'url':
            extra_data.append(item)
    iter_extra_data = iter(extra_data)
    for item in parsed_data:
        if item['type'] == 'emoticon' or item['type'] == 'username' or item['type'] == 'url':
            try:
                item['content'] = next(iter_extra_data)['content']
            except StopIteration:
                logging.critical('extra_data exhausted. Using existed db data. db data: {} parsed web data: {}'.format(content_db, parsed_data))
                return None

    return json.dumps(parsed_data, ensure_ascii=False)
