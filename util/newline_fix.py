# Deprecated
def fix(html, content):
    content_queued = []
    for item in content:
        if item['type'] == 'text' and item['content'] == '\n':
            continue
        if item['type'] == 'text' and '\n' in item['content']:
            content_queued.append(item['content'])
    if not content_queued:
        return content

    split_html = [_ for _ in html.descendants]
    br_count = 0
    br_index = [0]
    for (text, count) in zip(split_html, range(len(split_html))):
        if text.name == 'br' and count == len(split_html) - 1:
            br_count += 1
            br_index.append(br_count)
            break
        if text.name != 'br':
            if br_count != 0:
                br_index.append(br_count)
                if text.name:
                    br_index.append(-1)
            if br_index[-1] == -1 and br_count == 0:
                br_index.append(0)
            br_count = 0
        else:
            br_count += 1
    iter_index = iter(br_index)

    split_content = [_.split('\n') for _ in content_queued]
    for split_text in split_content:
        pivot = -1
        for text in split_text:
            try:
                iter_next = next(iter_index)
            except StopIteration:
                break
            # print(iter_next)
            if iter_next == -1:
                break
            if iter_next == 0:
                pivot = 0
                continue
            if text == '':
                text += iter_next * '\n'
                pivot += 1
            else:
                split_text.insert(pivot + 1, iter_next * '\n')
                pivot += 2
            # print(split_text)
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
        if item['type'] == 'text' and item['content'] == '\n':
            continue
        if item['type'] == 'text' and '\n' in item['content']:
            item['content'] = next(iter_parsed_content)

    return content
