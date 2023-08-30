# proma

中文版请见[这里](https://github.com/CatMe0w/proma/blob/master/README_zh.md)。

**This project is no longer active.**

I've been away from Tieba for a while and have no plans to go back.

Maintaining such a scraper project requires a sustained commitment to catch up with upstream changes.

It may be still working as you read this line of text, but it will likely to be broken in the distant future.

As of this writing (August 2023), I recommend using https://github.com/Starry-OvO/aiotieba . This is probably the most powerful toolkit for Tieba and the guys behind this project rocks. Make sure to check it out.

However, you still are welcome to fork under the terms of the MIT license.

---

_To forethink._

A tool to extract all threads, posts and comments of a forum of Baidu Tieba.

## Install dependencies

Python 3 is required.

`pip3 install beautifulsoup4 requests pytz lxml`

## Usage

`python3 main.py <tieba_name>`

Check the notes below before running.

## Notes

### Stages

In order to obtain the most complete data possible, `proma` gets data from both mobile app APIs and desktop websites. 

`proma` runs in the following order:

- Stage 1: Getting thread lists from desktop websites

- Stage 2: Getting posts and comments from mobile APIs

- Stage 3: Fixing lost album threads from desktop websites

- Stage 4: Fixing lost data of posts from desktop websites

Due to Baidu's extremely strict anti-bot rules, it's highly recommended to use a proxy pool for requests of desktop websites.

### Proxies

We use [Clash](https://github.com/Dreamacro/clash) to provide a proxy pool for requests of desktop websites.

Check `util.clash_control` and edit Clash’s endpoint addresses and other arguments if necessary.

__Note: You must start a Clash instance manually in advance of running `proma`.__

If you don’t want to use proxy, set `USE_CLASH` to `False` in `util.clash_control`.

### Download non-text content

See https://github.com/CatMe0w/proma_takeout , a standalone tool to download images.

### Project Ex Nihilo data

All tags, releases, and GitHub Actions workflows in this repository are a part of Project Ex Nihilo, a project that archives all data of a specific forum.

Therefore, these data are not a part of this project. They are kept in order to provide an unbiased source of the data.

If you wish to use, clone or fork this repository, please ignore or remove these data.

## File structures

`proma-raw/`: Raw HTML and JSON files of every page

`proma.db`: SQLite database of parsed data

`proma.log`: Log file

## Database structures

`user`

|Key|Type|Constraint|Note|
|-|-|-|-|
|id|numeric|primary key, not null|Internal unique ID of a user|
|username|text||Username can be empty or null since ~2017|
|nickname|text|||
|avatar|text|not null|Unique ID of a user avatar (profile picture)|

`thread`

|Key|Type|Constraint|Note|
|-|-|-|-|
|id|numeric|primary key, not null||
|title|text|not null||
|user_id|numeric|not null, foreign key references `user(id)`||
|reply_num|numeric|not null||
|is_good|numeric|not null||

`post`

|Key|Type|Constraint|Note|
|-|-|-|-|
|id|numeric|primary key, not null||
|floor|numeric|not null||
|user_id|numeric|not null, foreign key references `user(id)`||
|content|text||JSON format, see below|
|time|text|not null|UTC+8, yyyy-MM-dd HH:mm|
|comment_num|numeric|not null||
|signature|text||Link of an image|
|tail|text||Usually the device type of the user|
|thread_id|numeric|not null, foreign key references `thread(id)`||

`comment`

|Key|Type|Constraint|Note|
|-|-|-|-|
|id|numeric|primary key, not null||
|user_id|numeric|not null, foreign key references `user(id)`||
|content|text||JSON format, see below|
|time|text|not null|UTC+8, yyyy-MM-dd HH:mm|
|post_id|numeric|not null, foreign key references `post(id)`||

### `content` format example

This is an example of a `content` which contains all possible fields.

```
[
    {
        "type": "text",
        "content": "some plaintext\n"
    },
    {
        "type": "text",
        "content": "some plaintext\n\nwith multiple newlines\n"
    },
    {
        "type": "text_red",
        "content": "some plaintext but red\n"
    },
    {
        "type": "text_bold",
        "content": "some plaintext but bold\n"
    },
    {
        "type": "text_bold_red",
        "content": "some plaintext but bold and red\n"
    },
    {
        "type": "emoticon",
        "content": {
            "id": "image_emoticon25",
            "description": "滑稽"
        }
    },
    {
        "type": "username",
        "content": {
            "text": "@贴吧吧主小管家",
            "user_id": "167570067"
        }
    },
    {
        "type": "url",
        "content": {
            "url": "https://www.example.com/",
            "text": "https://www.example.com/"
        }
    },
    {
        "type": "image",
        "content": "https://imgsrc.baidu.com/forum/pic/item/1f7150dfb48f8c54f1e3359f2d292df5e0fe7f74.jpg"
    },
    {
        "type": "video",
        "content": "https://(snip)"
    },
    {
        "type": "audio",
        "content": "(snip)"
    }
]
```

## License

[MIT License](https://opensource.org/licenses/MIT)
