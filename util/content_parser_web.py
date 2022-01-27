import json


def parse_image(url):
    return 'https://imgsrc.baidu.com/forum/pic/item/' + url.split('/')[-1]


def parse_and_fix(html, content_db):
    for item in content_db:
        if item['type'] == 'video' or item['type'] == 'audio' or item['type'] == 'album':
            return None  # 含有以上类型的正文，不处理

    parsed_data = []
    is_initial = True
    for item in html.contents:
        if not item.name:
            if is_initial:
                parsed_data.append({'type': 'text', 'content': item.string.lstrip()})
                is_initial = False
            elif parsed_data[-1]['type'] == 'text':
                parsed_data[-1]['content'] += item.string
            else:
                parsed_data.append({'type': 'text', 'content': item.string})
        if item.name == 'br':
            if parsed_data[-1]['type'] == 'text':
                parsed_data[-1]['content'] += '\n'
            else:
                parsed_data.append({'type': 'text', 'content': '\n'})
        if item.name == 'strong':
            parsed_data.append({'type': 'text_bold', 'content': item.string})
        if item.name == 'span':
            if item['class'] == 'edit_font_color':
                parsed_data.append({'type': 'text_red', 'content': item.string})
        if item.name == 'img':
            if item['class'] == 'BDE_Image' or item['class'] == 'BDE_Meme' or item['class'] == 'BDE_Graffiti':
                parsed_data.append({'type': 'image', 'content': parse_image(item['src'])})
            elif item['class'] == 'BDE_Smiley3':
                parsed_data.append({'type': 'image', 'content': item['src']})
            elif item['class'] == 'BDE_Smiley':
                parsed_data.append({'type': 'emoticon', 'content': None})  # 不实现，下同，将通过移动端数据修复
        if item.name == 'a':
            if item.get('class') == 'at':
                parsed_data.append({'type': 'username', 'content': None})
            elif item.get('class') == 'j-no-opener-url':
                parsed_data.append({'type': 'url', 'content': None})
            else:
                if parsed_data[-1]['type'] == 'text':
                    parsed_data[-1]['content'] += item.string
                else:
                    parsed_data.append({'type': 'text', 'content': item.string})

    extra_data = []
    for item in content_db:
        if item['type'] == 'emoticon' or item['type'] == 'username' or item['type'] == 'url':
            extra_data.append(item)
    iter_extra_data = iter(extra_data)
    for item in parsed_data:
        if item['type'] == 'emoticon' or item['type'] == 'username' or item['type'] == 'url':
            item['content'] = next(iter_extra_data)['content']

    return json.dumps(parsed_data, ensure_ascii=False)
