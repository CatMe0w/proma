import json
import logging


def parse_image(url):
    return 'https://imgsrc.baidu.com/forum/pic/item/' + url.split('/')[-1]


def parse_html(html, flag_bad_client):
    parsed_data = []
    is_initial = True
    for item in html.contents:
        if not item.name or item.get('class') == ['edit_font_normal'] or (item.name == 'span' and item.get('class') is None):  # 纯文本
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

        elif item.name == 'strong':  # 加粗
            _ = parse_html(item, flag_bad_client)  # 递归一下，加粗和红字可能嵌套了其他的标签，下同
            for _item in _:
                if _item['type'] == 'text':
                    _item['type'] = 'text_bold'
                elif _item['type'] == 'text_red':
                    _item['type'] = 'text_bold_red'
                parsed_data.append(_item)

        elif item.name == 'span' and item.get('class') == ['edit_font_color']:  # 红字
            _ = parse_html(item, flag_bad_client)
            for _item in _:
                if _item['type'] == 'text':
                    _item['type'] = 'text_red'
                elif _item['type'] == 'text_bold':
                    _item['type'] = 'text_bold_red'
                parsed_data.append(_item)

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

        elif item.get('class') == ['save_face_post'] \
                or item.get('class') == ['summary'] or item.get('class') == ['refer_url'] \
                or item.get('class') == ['post_bubble_top'] or item.get('class') == ['pic_src_wrapper'] \
                or item.get('class') == ['album_pb_comment_container']:  # 每行依次是：挽尊卡、转发帖子、奇怪的回复气泡、图贴
            return None

        elif item.name == 'embed':  # Flash音乐播放器，丢弃
            pass

        else:
            logging.warning('Unhandled element: {}'.format(item))
        is_initial = False
    if parsed_data[0] == {'type': 'text', 'content': ''}:
        parsed_data.pop(0)
    return parsed_data


def parse_and_fix(html, content_db, flag_bad_client):
    for item in content_db:
        if item['type'] == 'video' or item['type'] == 'audio' or item['type'] == 'album':
            return None  # 含有以上类型则无需修复

    parsed_data = parse_html(html, flag_bad_client)
    if parsed_data is None:
        return None

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
                if 'qw_cat_' not in content_db:  # 预设神来一句在移动端的格式是image，在网页端是emoticon，排除这个情况以避免过多的无效warning
                    logging.warning('extra_data exhausted. Using existed db data. db data: {} parsed web data: {}'.format(content_db, parsed_data))
                return None

    try:
        _ = next(iter_extra_data)
    except StopIteration:
        pass
    else:
        logging.warning('extra_data has something left. Using existed db data. db data: {} parsed web data: {}, next: {}'.format(content_db, parsed_data, _))
        return None

    return json.dumps(parsed_data, ensure_ascii=False)
