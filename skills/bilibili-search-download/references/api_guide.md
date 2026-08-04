# B站视频搜索与下载 API 接口指南

> 红狐 API `bili/data/workSearch` 与 `parseWork/videoDownload/bilibili` 接口调用规范与字段说明，供 Agent 与开发者排查问题时参考。

---

## 1. 接口概览

### 1.1 作品搜索接口

| 项目 | 内容 |
|------|------|
| 接口地址 | `https://redfox.hk/story/api/bili/data/workSearch` |
| 请求方式 | POST |
| 请求头 | `Content-Type: application/json` + `REDFOX_API_KEY: {REDFOX_API_KEY}` |
| 认证方式 | Header `REDFOX_API_KEY`，值从环境变量 `REDFOX_API_KEY` 获取 |
| 成功响应码 | 响应体 `code` 统一为 `2000`（非 HTTP 标准 200） |
| 积分消耗 | 每次调用消耗一次积分 |
| 超时设置 | 脚本内置 30 秒超时 |

### 1.2 视频下载接口

| 项目 | 内容 |
|------|------|
| 接口地址 | `https://redfox.hk/story/api/parseWork/videoDownload/bilibili` |
| 请求方式 | POST |
| 请求头 | `Content-Type: application/json` + `REDFOX_API_KEY: {REDFOX_API_KEY}` |
| 认证方式 | Header `REDFOX_API_KEY`，值从环境变量 `REDFOX_API_KEY` 获取 |
| 成功响应码 | 响应体 `code` 统一为 `2000`（非 HTTP 标准 200） |
| 积分消耗 | 每次调用消耗一次积分（每个视频链接独立计费） |
| 超时设置 | 脚本内置 60 秒超时 |

---

## 2. 作品搜索接口详情

### 2.1 请求参数

```json
{
  "keyword": "羽绒服",
  "page": "1",
  "pageSize": 10,
  "order": "time"
}
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| keyword | String | 是 | 搜索关键词 |
| page | String | 是 | 页码（字符串格式） |
| pageSize | Integer | 否 | 每页条数，默认 10，最大 50 |
| order | String | 否 | 排序方式：time=发布时间/play=播放数/like=点赞数/comment=评论数/favorite=收藏数，默认 time |

### 2.2 响应结构

```json
{
  "code": 2000,
  "msg": "成功",
  "data": {
    "workList": [
      {
        "bvId": "BV1n57e6kEtz",
        "title": "视频标题",
        "description": "视频描述",
        "duration": 16,
        "picUrl": "http://i0.hdslb.com/bfs/archive/xxx.jpg",
        "created": "2026-06-26 03:03:13",
        "author": "作者昵称",
        "authorId": "31701874",
        "firstType": "游戏",
        "secondType": "网络游戏",
        "playCount": 4,
        "likeCount": 12,
        "favoriteCount": 0,
        "commentCount": 0,
        "shareCount": 1,
        "videoReview": 0,
        "coinCount": 0,
        "interactionQuantity": 13,
        "tagNames": ["标签1", "标签2"]
      }
    ],
    "page": 1,
    "pageSize": 10,
    "total": 25117
  }
}
```

### 2.3 脚本输出结构（stdout JSON）

脚本 `bilibili_search.py` 对响应做归一化后输出：

```json
{
  "keyword": "羽绒服",
  "page": 1,
  "page_size": 10,
  "total": 25117,
  "works": [
    {
      "bv_id": "BV1n57e6kEtz",
      "title": "视频标题",
      "description": "视频描述",
      "author": "作者昵称",
      "author_id": "31701874",
      "duration": 16,
      "pic_url": "http://i0.hdslb.com/bfs/archive/xxx.jpg",
      "created": "2026-06-26 03:03:13",
      "first_type": "游戏",
      "second_type": "网络游戏",
      "play_count": 4,
      "like_count": 12,
      "favorite_count": 0,
      "comment_count": 0,
      "share_count": 1,
      "coin_count": 0,
      "video_review": 0,
      "interaction_quantity": 13,
      "tag_names": ["标签1", "标签2"],
      "video_url": "https://www.bilibili.com/video/BV1n57e6kEtz"
    }
  ]
}
```

---

## 3. 视频下载接口详情

### 3.1 请求参数

```json
{
  "url": "https://www.bilibili.com/video/BV1AmSSBMEqo/"
}
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| url | String | 是 | B站视频链接，格式如 `https://www.bilibili.com/video/BVxxxxxx/` |

### 3.2 响应结构

```json
{
  "code": 2000,
  "data": {
    "cover": "http://i0.hdslb.com/bfs/archive/xxx.jpg",
    "desc": "",
    "resources": [
      {
        "coverUrl": "http://i0.hdslb.com/bfs/archive/xxx.jpg",
        "downloadUrl": "https://upos-sz-estgcos.bilivideo.com/...",
        "durationSeconds": null,
        "type": "video"
      }
    ],
    "title": "视频标题",
    "videoUrl": "https://upos-sz-estgcos.bilivideo.com/..."
  },
  "msg": "成功"
}
```

### 3.3 resources 资源类型

| type 值 | 说明 |
|---------|------|
| video | 视频文件 |
| audio | 音频文件 |
| mp3 | MP3 音频 |
| image | 图片资源 |

### 3.4 脚本输出结构（stdout JSON）

脚本 `bilibili_download.py` 对响应做归一化后输出：

```json
{
  "total_requested": 2,
  "total_success": 2,
  "results": [
    {
      "request_url": "https://www.bilibili.com/video/BV1AmSSBMEqo/",
      "title": "视频标题",
      "cover": "http://i0.hdslb.com/bfs/archive/xxx.jpg",
      "desc": "",
      "video_url": "https://upos-sz-estgcos.bilivideo.com/...",
      "resources": [
        {
          "type": "video",
          "cover_url": "http://i0.hdslb.com/bfs/archive/xxx.jpg",
          "download_url": "https://upos-sz-estgcos.bilivideo.com/...",
          "duration_seconds": null
        }
      ]
    }
  ]
}
```

---

## 4. 已知接口特性与注意事项

| 特性 | 说明 |
|------|------|
| 成功码为 2000 | 校验响应体 `code == 2000`，不可依赖 HTTP status 200 |
| 下载链接时效 | 视频下载链接可能有时效性，建议获取后尽快下载 |
| 搜索翻页 | 通过调整 `page` 参数翻页，`total` 字段返回总数 |
| 批量下载 | 每个视频链接独立调用、独立计费 |
| 空结果 | 搜索无结果时 `workList` 为空数组，`total` 为 0 |
