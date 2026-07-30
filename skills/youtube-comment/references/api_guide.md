# YouTube视频评论分析 API 接口指南

> 红狐 API `youtube/videoComments` 接口调用规范与字段说明，供 Agent 与开发者排查问题时参考。

---

## 1. 接口概览

| 项目 | 内容 |
|------|------|
| 接口地址 | `https://redfox.hk/story/api/youtube/videoComments` |
| 请求方式 | POST |
| 请求头 | `Content-Type: application/json` + `REDFOX_API_KEY: {REDFOX_API_KEY}` |
| 认证方式 | Header `REDFOX_API_KEY`，值从环境变量 `REDFOX_API_KEY` 获取 |
| 成功响应码 | 响应体 `code` 统一为 `2000`（非 HTTP 标准 200） |
| 积分消耗 | 每次调用消耗一次积分（含翻页；返回空数据同样扣除） |
| 超时设置 | 脚本内置 30 秒超时 |

---

## 2. 请求参数

```json
{
  "videoId": "sa8AzBK4dao",
  "sortBy": "top",
  "languageCode": "zh-CN",
  "countryCode": "US",
  "continuationToken": null,
  "source": "YouTube视频评论分析-GitHub"
}
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| videoId | String | 是 | 视频ID（链接中 `v=` 或 `/shorts/` 或 `youtu.be/` 后面的部分） |
| sortBy | String | 否 | 评论排序方式，默认 `"top"`（热门），可选 `"newest"`（最新） |
| languageCode | String | 否 | 评论显示语言偏好，默认 `"zh-CN"`，可选 `"en-US"`、`"ja-JP"`、`"ko-KR"` 等 |
| countryCode | String | 否 | 地区代码，默认 `"US"`，可选 `"JP"`、`"GB"` 等 |
| continuationToken | String | 否 | 翻页令牌，从上一次响应 `data.continuationToken` 获取；首页传 null 或不传 |
| source | String | 否 | 调用来源标识，固定值 `"YouTube视频评论分析-GitHub"` |

---

## 3. 响应结构

### 顶层结构

```json
{
  "code": 2000,
  "msg": "成功",
  "data": {
    "comments": [
      {
        "author": {
          "avatarUrl": "...",
          "channelId": "UC4nXYHM9ZOof76zJTjsey9w",
          "channelUrl": "https://www.youtube.com/@qwe800417",
          "displayName": "@qwe800417",
          "isCreator": false,
          "isVerified": false
        },
        "commentId": "Ugw_bDGOGdrK634jh5B4AaABAg",
        "content": "截图还以为林志颖",
        "likeCount": "6",
        "publishedTime": "4年前",
        "replyCount": "0"
      }
    ],
    "continuationToken": null
  }
}
```

### data 关键字段

| 字段 | 类型 | 说明 |
|------|------|------|
| videoId | String | 视频ID |







| comments | Array | 一级评论列表（单页约 30~40 条，服务端控制） |
| continuationToken | String | 下一页翻页令牌；为空表示无下一页 |

### comments 单条评论关键字段

| 字段 | 类型 | 说明 |
|------|------|------|
| author | Object | 评论者信息（同上结构） |
| content / text | String | 评论内容 |
| likeCount / retweetCount / replyCount / quoteCount / bookmarkCount | Number | 互动数据 |

| videoId | String | 评论自身的视频ID（可拼评论直达链接） |
| createdAt | String | 评论时间（脚本转北京时间） |

---

## 4. 脚本输出结构（stdout JSON）

脚本 `youtube_comment_search.py` 对响应做归一化后输出：

```json
{
  "video_id": "sa8AzBK4dao",
  "total_fetched": 35,
  "has_next": true,
  "continuation_token": "...",
  "comments": [
    {
      "display_name": "@qwe800417",
      "channel_id": "UC4nXYHM9ZOof76zJTjsey9w",
      "channel_url": "https://www.youtube.com/@qwe800417",
      "avatar_url": "https://yt3.ggpht.com/...",
      "is_creator": false,
      "is_verified": false,
      "comment_id": "Ugw_bDGOGdrK634jh5B4AaABAg",
      "content": "截图还以为林志颖",
      "like_count": 6,
      "published_time": "4年前",
      "reply_count": 0
    }
  ]
}
```

| 字段 | 说明 |
|------|------|
| video_id | 查询的视频ID |
| total_fetched | 本次实际获取的一级评论条数 |
| has_next | 是否有下一页（continuationToken 非空即 true） |
| continuation_token | 下一页翻页令牌（Agent 从对话上下文中读取，用于翻页） |
| comments | 归一化评论列表 |

⚠️ YouTube API 返回的评论时间为相对时间格式（如"4年前"），脚本不做时区转换。
## 5. 已知接口特性与坑位

| 特性 | 说明 |
|------|------|
| 成功码为 2000 | 校验响应体 `code == 2000`，不可依赖 HTTP status 200 |
| 单页条数不固定 | 由服务端控制，无法通过参数指定 |
| 无评论总数 | API 不返回 total_count，仅知当前页获取条数 |
| 时间为相对格式 | `publishedTime` 返回相对时间（如"4年前"），非绝对时间戳 |
| 空数据也扣积分 | 任何调用（含失败重试）均消耗积分，调用前须确认必要性 |
| 二级评论不支持 | 仅返回一级评论，嵌套回复不展开 |

