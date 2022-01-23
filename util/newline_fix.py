def fix(html, content):
    content_queued = []
    for item in content:
        if item['type'] == 'text' and '\n' in item['content']:
            content_queued.append(item['content'])

    split_html = [_ for _ in html.descendants]
    br_count = 0
    br_index = []
    for (text, insertion_count) in zip(split_html, range(len(split_html))):
        if text.name == 'br' and insertion_count == len(split_html) - 1:
            br_count += 1
            br_index.append(br_count)
            break
        if text.name != 'br':
            if br_count != 0:
                br_index.append(br_count)
            br_count = 0
        else:
            br_count += 1
    iter_index = iter(br_index)

    split_content = [_.split('\n') for _ in content_queued]
    for split_text in split_content:
        max_insertion = 0
        for text in split_text:
            if text:
                max_insertion += 1
        if split_text[0] == '':
            max_insertion += 1
        if split_text[-1] == '':
            max_insertion += 1
        max_insertion -= 1

        pivot = 0
        insertion_count = 0
        for text in split_text:
            if insertion_count == max_insertion:
                break
            if text == '' and pivot == 0:
                split_text[0] = next(iter_index) * '\n'
                pivot += 1
                insertion_count += 1
            else:
                split_text.insert(pivot + 1, next(iter_index) * '\n')
                pivot += 2
                insertion_count += 1
        if split_text[-1] == '':
            split_text.remove('')

    parsed_content = []
    for text in range(len(split_content)):
        _ = ''
        for item in range(len(split_content[text])):
            _ += split_content[text][item]
        parsed_content.append(_)

    iter_parsed_content = iter(parsed_content)
    for item in content:
        if item['type'] == 'text' and '\n' in item['content']:
            item['content'] = next(iter_parsed_content)

    return content
