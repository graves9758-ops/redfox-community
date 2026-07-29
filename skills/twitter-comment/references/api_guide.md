# X作品评论分析 API 接口指南

> 红狐 API `x/tweetComments` 接口调用规范与字段说明，供 Agent 与开发者排查问题时参考。

---

## 1. 接口概览

| 项目 | 内容 |
|------|------|
| 接口地址 | `https://redfox.hk/story/api/x/tweetComments` |
| 请求方式 | POST |
| 请求头 | `Content-Type: application/json` + `X-API-Key: {REDFOX_API_KEY}` |
| 认证方式 | Header `X-API-Key`，值从环境变量 `REDFOX_API_KEY` 获取 |
| 成功响应码 | 响应体 `code` 统一为 `2000`（非 HTTP 标准 200） |
| 积分消耗 | 每次调用消耗一次积分（含翻页；返回空数据同样扣除） |
| 超时设置 | 脚本内置 30 秒超时 |

---

## 2. 请求参数

```json
{
  "tweetId": "2082020241089945714",
  "cursor": "<可选，翻页游标>",
  "source": "X(Twitter)作品评论分析-GitHub"
}
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| tweetId | String | 是 | 推文ID（链接中 `/status/` 后的纯数字） |
| cursor | String | 否 | 翻页游标，首页不传；从上一次响应 `data.cursor` 获取 |
| source | String | 否 | 调用来源标识 |

---

## 3. 响应结构

### 顶层结构

```json
{
  "code": 2000,
  "msg": "成功",
  "data": {
    "tweetId": "...",
    "content": "...",
    "author": { ... },
    "threadReplies": [ ... ],
    "cursor": "..."
  }
}
```

### data（推文详情）关键字段

| 字段 | 类型 | 说明 |
|------|------|------|
| tweetId | String | 推文ID |
| content / text | String | 推文正文（content 可能截断，text 为全文） |
| createdAt | String | 发布时间（Twitter 原生格式，脚本转北京时间） |
| likeCount / retweetCount / replyCount / quoteCount / bookmarkCount | Number | 点赞/转发/回复/引用/收藏数 |
| viewCount | String | 浏览量 |
| language | String | 推文语种 |
| author | Object | 作者信息（displayName / username / userId / avatar / verified / followers） |
| medias | Array | 媒体列表（视频含 coverUrl、variants 多码率直链） |
| threadReplies | Array | 一级评论列表（单页约 30~40 条，服务端控制） |
| cursor | String | 下一页游标；为空表示无下一页 |

### threadReplies 单条评论关键字段

| 字段 | 类型 | 说明 |
|------|------|------|
| author | Object | 评论者信息（同上结构） |
| content / text | String | 评论内容 |
| likeCount / retweetCount / replyCount / quoteCount / bookmarkCount | Number | 互动数据 |
| viewCount | String | 浏览量 |
| tweetId | String | 评论自身的推文ID（可拼评论直达链接） |
| createdAt | String | 评论时间（脚本转北京时间） |

---

## 4. 脚本输出结构（stdout JSON）

脚本 `tweet_comment_search.py` 对响应做归一化后输出：

```json
{
  "work_detail": {
    "tweet_id": "...", "content": "...", "text": "...",
    "created_at": "2026-07-28 16:28:02",
    "like_count": 543, "retweet_count": 153, "reply_count": 77,
    "quote_count": 18, "bookmark_count": 80, "view_count": "31773",
    "language": "en",
    "author_name": "...", "author_username": "...", "author_uid": "...",
    "author_avatar": "...", "author_verified": true, "author_followers": 0,
    "medias": [], "cursor": "..."
  },
  "total_count": 77,
  "total_fetched": 35,
  "has_next": true,
  "cursor": "<下一页游标>",
  "comments": [
    {
      "user_name": "...", "username": "...", "user_id": "...",
      "avatar": "...", "verified": false, "followers": 0,
      "content": "...",
      "like_count": 15, "retweet_count": 7, "reply_count": 0,
      "quote_count": 0, "bookmark_count": 0, "view_count": "152",
      "tweet_id": "...", "create_time": "2026-07-28 16:42:57"
    }
  ]
}
```

| 字段 | 说明 |
|------|------|
| work_detail | 推文详情（归一化后） |
| total_count | 评论总数（取推文 reply_count；翻页时可能为 0，以首页为准） |
| total_fetched | 本次实际获取的一级评论条数 |
| has_next | 是否有下一页（cursor 非空即 true） |
| cursor | 下一页游标（Agent 从对话上下文中读取，用于翻页） |
| comments | 归一化评论列表 |

⚠️ 所有时间字段已由脚本 `_parse_time` 统一转换为北京时间（UTC+8），格式 `YYYY-MM-DD HH:MM:SS`。

---

## 5. 已知接口特性与坑位

| 特性 | 说明 |
|------|------|
| 成功码为 2000 | 校验响应体 `code == 2000`，不可依赖 HTTP status 200 |
| 单页条数不固定 | 约 30~40 条，由服务端控制，无法通过参数指定 |
| 翻页 total_count 可能为 0 | 评论总数以首页返回值为准 |
| 相邻页可能重复 | X 会话时间线特性，展示时可按用户名+内容去重 |
| followers 常为 0 | 接口暂未返回评论者真实粉丝数 |
| 空数据也扣积分 | 任何调用（含失败重试）均消耗积分，调用前须确认必要性 |
| 二级评论不支持 | 仅返回一级评论，嵌套回复不展开 |


