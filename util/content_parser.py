def parse_text(item):
    parsed_item = {}
    return parsed_item


def parse_url(item):
    parsed_item = {}
    return parsed_item


def parse_emotion(item):
    parsed_item = {}
    return parsed_item


def parse_image(item):
    parsed_item = {}
    return parsed_item


def parse_video(item):
    parsed_item = {}
    return parsed_item


def parse_audio(item):
    parsed_item = {}
    return parsed_item


def parse(data):
    parsed_data = []
    for item in data:
        if item['type'] == '0' or '4' or '9':
            parsed_data.append({'type': 'text', 'content': parse_text(item)})
        if item['type'] == '1':
            parsed_data.append({'type': 'url', 'content': parse_url(item)})
        if item['type'] == '2':
            parsed_data.append({'type': 'emotion', 'content': parse_emotion(item)})
        if item['type'] == '3' or '11' or '20':
            parsed_data.append({'type': 'image', 'content': parse_image(item)})
        if item['type'] == '5':
            parsed_data.append({'type': 'video', 'content': parse_video(item)})
        if item['type'] == '10':
            parsed_data.append({'type': 'audio', 'content': parse_audio(item)})
    return parsed_data
