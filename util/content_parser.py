import json
from urllib.parse import unquote


def purify_url(url):
    if url.startswith('http://tieba.baidu.com/p/'):
        return url.split('?share=9105&fr=share')[0]
    return unquote(url.split('checkurl?url=')[-1].split('&meta=1&urlrefer=')[0])


def parse_url(item):
    return {'url': purify_url(item['link']), 'text': item['text']}


def parse_emoticon(item):
    return {'id': item['text'], 'description': item['c']}


def parse_image(item):
    if item['type'] == '3':  # 一般图片
        try:
            if item['origin_src'].startswith('\/\/tb2.bdstatic.com'):  # 无法解释
                return 'http:' + item['origin_src']
            return item['origin_src']
        except KeyError:
            # 一些固定资源（如预设的“神来一句”）没有origin_src
            return item['cdn_src_active'].split('&')[0].split('=')[-1]  # 切掉末尾的参数，再切掉c.tieba.baidu.com域名，否则返回的内容没有意义
    if item['type'] == '11':  # 奇怪的大表情
        return item['static']
    if item['type'] == '16':  # 奇怪的涂鸦
        return item['graffiti_info']['url']
    if item['type'] == '20':  # 奇怪的可编辑大表情，类似“神来一句”
        return item['src']


def parse_username(item):
    return {'text': item['text'], 'user_id': item['uid']}


def parse_video(item):
    return purify_url(item['text'])


def parse(data):
    parsed_data = []
    for item in data:
        if item['type'] == '0' or item['type'] == '9':  # 0是一般文本，9是“电话号码”（连续数字），一律按纯文本处理即可
            parsed_data.append({'type': 'text', 'content': item['text']})
        if item['type'] == '1':
            parsed_data.append({'type': 'url', 'content': parse_url(item)})
        if item['type'] == '2':
            parsed_data.append({'type': 'emoticon', 'content': parse_emoticon(item)})
        if item['type'] == '3' or item['type'] == '11' or item['type'] == '20':
            parsed_data.append({'type': 'image', 'content': parse_image(item)})
        if item['type'] == '4':
            parsed_data.append({'type': 'username', 'content': parse_username(item)})
        if item['type'] == '5':
            parsed_data.append({'type': 'video', 'content': parse_video(item)})
        if item['type'] == '10':
            parsed_data.append({'type': 'audio', 'content': item['voice_md5']})
    return json.dumps(parsed_data, ensure_ascii=False)
