import json


def fix(raw_content):
    original_picture_list = json.loads(raw_content.decode('gbk'))['data']['pic_list']
    parsed_picture_list = []
    for item in original_picture_list:
        parsed_picture_list.append({
            'url': 'https://imgsrc.baidu.com/forum/pic/item/' + item['pic_id'] + '.jpg',
            'description': item['descr']
        })
    parsed_data = [{'type': 'album', 'content': parsed_picture_list}]
    return json.dumps(parsed_data, ensure_ascii=False)
