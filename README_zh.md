# proma

_To forethink._

一个用于提取百度贴吧中，整个吧内所有帖子、楼层与楼中楼的工具。

## 安装依赖

需要 Python 3。

`pip3 install beautifulsoup4 requests pytz`

## 使用方法

`python3 main.py <贴吧名>`

在运行之前，请先阅读以下内容。

## 注意

### 阶段

为了获得尽可能完整的数据，`proma` 会同时从移动端 app 接口与电脑网页版获取数据。

`proma` 按以下顺序运行：

- 第一阶段：通过电脑网页版，获取所有帖子的目录

- 第二阶段：通过移动端接口，获取每个帖子的楼层与楼中楼

- 第三阶段：通过电脑网页版，修复丢失的图片帖子

- 第四阶段：通过电脑网页版，修复楼层中丢失的数据

由于百度极为严格的反机器人机制，强烈建议为电脑网页版的请求使用代理池。

### 代理

我们使用 [Clash](https://github.com/Dreamacro/clash) 为电脑网页版的请求提供代理池。

检查 `util.clash_control` 并视情况修改 Clash 的连接地址与其他参数。

__注意：必须在运行 `proma` 之前手动开启 Clash。__

若不希望使用代理，请将 `util.clash_control` 中的 `USE_CLASH` 改为 `False`。

## 文件结构

`proma-raw/`: 每个页面的原始 HTML 与 JSON

`proma.db`: 存有已解析数据的 SQLite 数据库

`proma.log`: 日志文件

## 数据库结构

`user`

|Key|Type|Constraint|Note|
|-|-|-|-|
|id|numeric|primary key, not null|用户的内部唯一 ID|
|username|text||自大约2017年起，username 可以为空或 null|
|nickname|text|||
|avatar|text|not null|用户头像的唯一 ID|

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
|content|text||JSON 格式|
|time|text|not null|UTC+8, yyyy-MM-dd HH:mm|
|comment_num|numeric|not null||
|signature|text||签名档，一个图片链接|
|tail|text||小尾巴，通常是用户的设备类型|
|thread_id|numeric|not null, foreign key references `thread(id)`||

`comment`

|Key|Type|Constraint|Note|
|-|-|-|-|
|id|numeric|primary key, not null||
|user_id|numeric|not null, foreign key references `user(id)`||
|content|text||JSON 格式|
|time|text|not null|UTC+8, yyyy-MM-dd HH:mm|
|post_id|numeric|not null, foreign key references `post(id)`||

## 开源许可

[MIT License](https://opensource.org/licenses/MIT)
