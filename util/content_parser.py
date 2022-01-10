import json


def parse_url(item):
    return {'url': item['link'], 'text': item['text']}


def parse_emotion(item):
    return {'id': item['text'], 'description': item['c']}


def parse_image(item):
    if item['type'] == '3':
        return item['origin_src']
    if item['type'] == '11':
        return item['static']
    if item['type'] == '20':
        return item['src']


def parse_video(item):
    return {'url': item['link'], 'cover_picture_url': item['src']}


def parse(data):
    parsed_data = []
    for item in data:
        if item['type'] == ('0' or '4' or '9'):
            parsed_data.append({'type': 'text', 'content': item['text']})
        if item['type'] == '1':
            parsed_data.append({'type': 'url', 'content': parse_url(item)})
        if item['type'] == '2':
            parsed_data.append({'type': 'emotion', 'content': parse_emotion(item)})
        if item['type'] == ('3' or '11' or '20'):
            parsed_data.append({'type': 'image', 'content': parse_image(item)})
        if item['type'] == '5':
            parsed_data.append({'type': 'video', 'content': parse_video(item)})
        if item['type'] == '10':
            parsed_data.append({'type': 'audio', 'content': item['voice_md5']})
    return json.dumps(parsed_data)
