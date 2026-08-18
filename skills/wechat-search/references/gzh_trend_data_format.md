# 公众号趋势洞察数据格式说明

## 概览

本文档定义了公众号趋势洞察数据查询脚本 `fetch_gzh_trends.py` 的输入输出格式规范。

## 重要说明

**数据说明**：爆款文章范围为阅读数5000+以上的文章，每日早上7点更新昨日数据。文章互动数据截止为入库时间，不是实时数据，入库后互动数据可能持续增长。

**排序说明**：有关键词搜索时，根据相关性（满分10分）、热度（满分3分）、时效（满分2分）三个维度加权计算，总分共15分；全站热门/无关键词时，按阅读数排序。

## 接口信息

**请求地址**：`POST https://redfox.hk/story/api/gzh/search/hotArticle`

**请求头**：

```
Content-Type: application/json
X-API-Key: ak_xxxxxxxxxxxxxxxxx
```

## 输入格式

### 接口请求参数

```json
{
  "keyword": "AIGC,aigc创业",
  "startDate": "2026-04-14",
  "endDate": "2026-05-15"
}
```

| 参数        | 类型   | 必填 | 说明                             |
| ----------- | ------ | ---- | -------------------------------- |
| `keyword`   | string | 是   | 搜索关键词，多个关键词用逗号分隔 |
| `startDate` | string | 是   | 开始日期，格式 yyyy-MM-dd        |
| `endDate`   | string | 是   | 结束日期，格式 yyyy-MM-dd        |

### 脚本命令行参数

```bash
python scripts/fetch_gzh_trends.py --keyword <关键词> [选项]
```

| 参数              | 必填 | 说明                             | 默认值                |
| ----------------- | ---- | -------------------------------- | --------------------- |
| `--keyword`       | 是   | 搜索关键词，多个关键词用逗号分隔 | -                     |
| `--start-date`    | 否   | 开始日期，格式 yyyy-MM-dd        | 最近30天              |
| `--max-items`     | 否   | 最多展示数量                     | 10                    |
| `--output-format` | 否   | 输出格式：text、json 或 html     | html                  |
| `--output-file`   | 否   | 输出文件路径                     | 关键词\_趋势数据.html |
| `--debug`         | 否   | 调试模式，打印原始API响应        | False                 |

## 接口返回格式

### 返回结构

```json
{
  "code": 2000,
  "msg": "成功",
  "data": {
    "articles": [...],
    "latestHotArticles": [...],
    "hotTopics": [],
    "keyword": "AIGC,aigc创业",
    "pageNum": 1,
    "pageSize": 10,
    "relatedSearches": [],
    "tips": null,
    "total": 67
  }
}
```

### 返回字段说明

| 字段                     | 类型   | 说明                                                     |
| ------------------------ | ------ | -------------------------------------------------------- |
| `code`                   | int    | 状态码，2000表示成功                                     |
| `msg`                    | string | 状态消息                                                 |
| `data`                   | object | 数据对象                                                 |
| `data.articles`          | array  | 文章列表                                                 |
| `data.latestHotArticles` | array  | 最新热门文章列表                                         |
| `data.hotTopics`         | array  | 热门话题（接口返回，对话中不展示，使用固定赛道列表替代） |
| `data.keyword`           | string | 搜索关键词                                               |
| `data.pageNum`           | int    | 当前页码                                                 |
| `data.pageSize`          | int    | 每页数量                                                 |
| `data.relatedSearches`   | array  | 相关搜索（暂无数据）                                     |
| `data.tips`              | string | 提示信息                                                 |
| `data.total`             | int    | 总数量                                                   |

### 文章字段（articles数组元素）

| 字段名               | 类型   | 说明                                  |
| -------------------- | ------ | ------------------------------------- |
| `id`                 | string | 文章ID（唯一标识）                    |
| `title`              | string | 文章标题                              |
| `summary`            | string | 文章摘要/正文片段                     |
| `author`             | string | 公众号名称                            |
| `sourceUsernickname` | string | 来源用户昵称（可为null）              |
| `url`                | string | 文章链接                              |
| `imageUrl`           | string | 封面图片链接                          |
| `publicTime`         | string | 发布时间（格式：YYYY-MM-DD HH:MM:SS） |
| `likeCount`          | int    | 点赞数                                |
| `commentsCount`      | int    | 评论数（可为null）                    |
| `watchCount`         | int    | 在看数                                |
| `clicksCount`        | int    | 阅读数                                |
| `popularityScore`    | float  | 热度评分                              |
| `recencyScore`       | float  | 时效评分                              |
| `relevanceScore`     | float  | 相关性评分                            |
| `totalScore`         | float  | 总评分                                |
| `publicTagInfo`      | string | 标签信息（JSON字符串，可为null）      |

## 脚本输出格式

脚本会对接口返回数据进行标准化处理，输出简化后的字段结构。

### JSON 输出示例

```json
{
  "keyword": "职场",
  "total": 10,
  "items": [
    {
      "photoId": "1234567890",
      "title": "这些年我做过最正确的职场决定",
      "summary": "相信积累的力量，只要活得久，总会走到想到达的地方。",
      "accountId": "每日豆瓣",
      "accountName": "每日豆瓣",
      "fans": 0,
      "publicTime": "2024-05-14 07:59:54",
      "noteLink": "https://mp.weixin.qq.com/s?...",
      "authorLink": "https://open.weixin.qq.com/qr/code?username=每日豆瓣",
      "interactiveCount": 6040,
      "likeCount": 5139,
      "commentCount": 241,
      "watchCount": 660,
      "clicksCount": "100001",
      "dataScore": 34.53
    }
  ]
}
```

### 脚本输出字段说明

| 字段名             | 类型   | 说明                          |
| ------------------ | ------ | ----------------------------- |
| `photoId`          | string | 文章ID                        |
| `title`            | string | 文章标题                      |
| `summary`          | string | 文章摘要                      |
| `accountId`        | string | 公众号ID/名称                 |
| `accountName`      | string | 公众号名称                    |
| `fans`             | int    | 粉丝数（固定为0，接口未返回） |
| `publicTime`       | string | 发布时间                      |
| `noteLink`         | string | 文章链接                      |
| `authorLink`       | string | 作者二维码链接                |
| `interactiveCount` | int    | 互动总数（点赞+评论+在看）    |
| `likeCount`        | int    | 点赞数                        |
| `commentCount`     | int    | 评论数                        |
| `watchCount`       | int    | 在看数                        |
| `clicksCount`      | string | 阅读数                        |
| `dataScore`        | float  | 数据表现分数（0-100分）       |

## 数据评分规则

脚本对文章进行数据表现评分（0-100分），评分维度：

- 点赞权重 30%
- 评论权重 25%
- 在看权重 25%
- 分享权重 20%

使用对数缩放归一化，避免极值影响。

## HTML 输出格式

HTML输出采用卡片式布局，Grid自适应2-4列，每张卡片包含：

1. 序号标签
2. 文章标题（可点击跳转）
3. 作者信息 + 发布日期（作者可点击跳转）
4. 互动数 + 在看数 + 查看文章按钮

## 多关键词处理

- 支持多个关键词用逗号分隔
- 对每个关键词分别查询接口
- 合并所有查询结果
- 基于photoId去重，避免重复文章
- 按dataScore降序排序
