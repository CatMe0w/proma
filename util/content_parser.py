import json
from urllib.parse import unquote


def purify_url(url):
    return unquote(url.split('checkurl?url=')[-1].split('&meta=1&urlrefer=')[0])


def parse_url(item):
    return {'url': purify_url(item['link']), 'text': item['text']}


def parse_emotion(item):
    return {'id': item['text'], 'description': item['c']}


def parse_image(item):
    if item['type'] == '3':
        try:
            return item['origin_src']
        except KeyError:
            # 一些固定资源（如预设的“神来一句”）没有origin_src
            return item['cdn_src_active'].split('&')[0].split('=')[-1]  # 切掉末尾的参数，再切掉c.tieba.baidu.com域名，否则返回的内容没有意义
    if item['type'] == '11':
        return item['static']
    if item['type'] == '20':
        return item['src']


def parse_username(item):
    return {'text': item['text'], 'user_id': item['uid']}


def parse_video(item):
    return purify_url(item['text'])


def parse(data):
    parsed_data = []
    for item in data:
        if item['type'] == '0' or item['type'] == '9':
            parsed_data.append({'type': 'text', 'content': item['text']})
        if item['type'] == '1':
            parsed_data.append({'type': 'url', 'content': parse_url(item)})
        if item['type'] == '2':
            parsed_data.append({'type': 'emotion', 'content': parse_emotion(item)})
        if item['type'] == '3' or item['type'] == '11' or item['type'] == '20':
            parsed_data.append({'type': 'image', 'content': parse_image(item)})
        if item['type'] == '4':
            parsed_data.append({'type': 'username', 'content': parse_username(item)})
        if item['type'] == '5':
            parsed_data.append({'type': 'video', 'content': parse_video(item)})
        if item['type'] == '10':
            parsed_data.append({'type': 'audio', 'content': item['voice_md5']})
    return json.dumps(parsed_data)
