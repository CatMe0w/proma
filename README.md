# proma

中文版请见[这里](https://github.com/CatMe0w/proma/blob/master/README_zh.md)。

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
|content|text||JSON format|
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
|content|text||JSON format|
|time|text|not null|UTC+8, yyyy-MM-dd HH:mm|
|post_id|numeric|not null, foreign key references `post(id)`||

## License

[MIT License](https://opensource.org/licenses/MIT)
