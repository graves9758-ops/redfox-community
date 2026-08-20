# API 接口参考

所有接口统一规范：
- **Host**: `https://redfox.hk`
- **Method**: `POST`
- **Content-Type**: `application/json`
- **认证头**: `REDFOX-API-KEY` + `X-API-Key`（值均为 `$REDFOX_API_KEY`）
- **成功状态码**: `code: 2000`

---

## 1. 抖音（广域库）

**Path**: `/story/api/dy/data/searchWork`

**请求体**:
```json
{"keyword": "关键词", "pageNum": 1, "pageSize": 20}
```
- `keyword`: 搜索关键词（必填，匹配作品正文）
- `pageNum`: 页码，从1开始，默认1
- `pageSize`: 每页大小，默认10，最大50

**响应**: `data.list[]`，另有 `data.total`（总记录数）
| 字段 | 类型 | 说明 |
|------|------|------|
| videoId | String | 作品ID |
| content | String | 作品正文/描述 |
| videoType | String | 0=普通视频, 68=图集, 63=直播录屏等 |
| duration | Integer | 时长（毫秒） |
| publishTime | String | 发布时间 |
| coverUrl | String | 封面链接 |
| opusUrl | String | 作品链接 |
| imageUrlList | Array | 图片列表（图文作品） |
| tagList | Array | 话题列表 |
| likeCount | Integer | 点赞数 |
| commentCount | Integer | 评论数 |
| shareCount | Integer | 分享数 |
| collectCount | Integer | 收藏数 |
| authorUid | String | 作者ID |
| authorName | String | 作者昵称 |
| authorAvatarUrl | String | 作者头像 |
| authorShortId | String | 作者抖音short_id |
| authorUniqueId | String | 作者抖音unique_id |
| authorSecUid | String | 作者sec_uid |

**URL 构造**: `opusUrl` 即为完整链接

---

## 2. 小红书（优质库）

**Path**: `/story/api/xhsUser/searchArticle`

**请求体**:
```json
{"keyword": "关键词", "offset": 0, "sortType": "0"}
```
- `sortType`: `0`=默认, `2`=最新, `4`=最热
- `offset`: 从0开始，每页+20

**响应**: `data.list[]`
| 字段 | 类型 | 说明 |
|------|------|------|
| workId | String | 作品ID |
| workTitle | String | 标题 |
| workDesc | String | 内容 |
| coverUrl | String | 封面图 |
| workUrl | String | 作品链接 |
| workPublishTime | String | 发布时间 |
| accountNickname | String | 作者昵称 |
| accountUserid | String | 作者ID |
| workLikedCount | Integer | 点赞数 |
| workCommentsCount | Integer | 评论数 |
| workCollectedCount | Integer | 收藏数 |
| workSharedCount | Integer | 转发数 |
| workType | String | video/normal |

**URL 构造**: `workUrl` 即为完整链接

---

## 3. 公众号（广域库）

**Path**: `/story/api/gzh/data/searchArticle`

**请求体**:
```json
{"keyword": "关键词", "offset": 0, "sortType": "0"}
```
- `sortType`: `0`=默认, `2`=最新, `4`=最热
- `offset`: 从0开始，每页+20

**响应**: `data.list[]`
| 字段 | 类型 | 说明 |
|------|------|------|
| title | String | 标题 |
| summary | String | 摘要 |
| content | String | 正文HTML |
| workUrl | String | 文章链接 |
| coverUrl | String | 封面链接 |
| publishTime | String | 发布时间 |
| readCount | Integer | 阅读数 |
| likeCount | Integer | 点赞数 |
| watchCount | Integer | 在看数 |
| commentCount | Integer | 评论数 |
| collectCount | Integer | 收藏数 |
| shareCount | Integer | 分享数 |
| author | String | 账号昵称 |
| isOriginal | Integer | 1=原创 |
| orderNum | Integer | 0=头条 |
| originalAuthor | String | 原创作者 |
| authorAvatarUrl | String | 头像链接 |
| workUuid | String | 作品ID |

---

## 4. B站（优质库）

**Path**: `/story/api/bili/data/workSearch`

**请求体**:
```json
{"keyword": "关键词", "page": "1", "pageSize": 20, "order": "time"}
```
- `order`: `time`=最新, `play`=播放数, `like`=点赞, `comment`=评论, `favorite`=收藏

**响应**: `data.workList[]`
| 字段 | 类型 | 说明 |
|------|------|------|
| bvId | String | BV号 |
| title | String | 标题 |
| description | String | 描述 |
| duration | Integer | 时长（秒） |
| picUrl | String | 封面 |
| created | String | 发布时间 |
| author | String | 作者 |
| authorId | String | 作者ID |
| firstType | String | 一级分类 |
| secondType | String | 二级分类 |
| playCount | Integer | 播放数 |
| likeCount | Integer | 点赞数 |
| favoriteCount | Integer | 收藏数 |
| commentCount | Integer | 评论数 |
| shareCount | Integer | 分享数 |
| videoReview | Integer | 弹幕数 |
| coinCount | Integer | 投币数 |
| interactionQuantity | Integer | 互动数 |
| tagNames | Array | 标签 |

**URL 构造**: `https://www.bilibili.com/video/{bvId}`

---

## 5. 快手（广域库）

**Path**: `/story/api/ksAllData/searchWork`

**请求体**:
```json
{"keyword": "关键词", "page": 1, "size": 20, "sort": "综合"}
```
- `sort`: `综合`/`最新`/`最多点赞`/`最多收藏`
- `size`: 最大50

**响应**: `data.list[]`
| 字段 | 类型 | 说明 |
|------|------|------|
| photoId | String | 作品ID |
| caption | String | 标题 |
| nickname | String | 作者 |
| headUrl | String | 头像 |
| coverUrl | String | 封面 |
| videoUrl | String | 视频URL |
| publishTime | String | 发布时间 |
| duration | Integer | 时长（毫秒） |
| viewCount | Integer | 播放数 |
| likeCount | Integer | 点赞数 |
| commentCount | Integer | 评论数 |
| collectCount | Integer | 收藏数 |
| shareCount | Integer | 分享数 |
| forwardCount | Integer | 转发数 |
| authorFans | Integer | 粉丝数 |

**URL 构造**: `https://www.kuaishou.com/short-video/{photoId}`

---

## 6. 视频号（广域库）

**Path**: `/story/api/sphAllData/searchWork`

**请求体**:
```json
{"keyword": "关键词", "page": 1, "size": 20, "sort": "综合"}
```
- `sort`: `综合`/`最新`/`最多点赞`/`最多收藏`

**响应**: `data.list[]`
| 字段 | 类型 | 说明 |
|------|------|------|
| description | String | 作品描述 |
| nickname | String | 账号昵称 |
| headUrl | String | 头像 |
| coverUrl | String | 封面 |
| thumbUrl | String | 缩略图 |
| videoUrl | String | 视频URL |
| publishTime | String | 发布时间 |
| videoDuration | String | 时长（秒） |
| likeCount | Integer | 点赞数 |
| commentCount | Integer | 评论数 |
| forwardCount | Integer | 转发数 |
| favCount | Integer | 收藏数 |
| topic | String | 话题JSON数组 |
| width/height | Integer | 分辨率 |

---

## 7. 今日头条（实时）

**Path**: `/story/api/toutiao/searchWork`

**请求体**:
```json
{"keyword": "关键词", "offset": "0"}
```
- `offset`: 从"0"开始，每页+1

**响应**: `data[]`（注意：data 是数组，非对象）
| 字段 | 类型 | 说明 |
|------|------|------|
| opusId | String | 作品ID |
| opusUrl | String | 作品链接 |
| title | String | 标题 |
| nickname | String | 作者昵称 |
| uid | String | 作者UID |
| publishTime | String | 秒级时间戳 |
| commentNum | Integer | 评论数 |
| hasNext | Boolean | 是否有下一页 |
| pageCount | Integer | 每页条数 |

---

## 8. TikTok

**Path**: `/story/api/tiktok/ability/searchVideo`

**请求体**:
```json
{"keyword": "关键词", "offset": "0", "count": "20", "sortType": "0", "publishTime": "0", "region": "US"}
```
- `sortType`: `0`=相关度, `1`=最多点赞
- `publishTime`: `0`=不限, `1`=一天内, `7`=一周, `30`=一月, `90`=三月, `180`=半年
- `region`: ISO 3166-1 alpha-2 代码，默认 `US`

**响应**: `data[]`（注意：data 是数组）
| 字段 | 类型 | 说明 |
|------|------|------|
| workId | String | 作品ID |
| content | String | 作品描述 |
| mediaType | String | video/photo |
| publishTime | Integer | 秒级时间戳 |
| shareLink | String | 分享链接 |
| authorData.userName | String | 作者昵称 |
| authorData.userHandle | String | 作者handle |
| authorData.fansCount | Integer | 粉丝数 |
| authorData.avatarImage | String | 头像 |
| statsData.viewCount | Integer | 播放数 |
| statsData.likeCount | Integer | 点赞数 |
| statsData.commentTotal | Integer | 评论数 |
| statsData.shareTotal | Integer | 分享数 |
| statsData.favoriteCount | Integer | 收藏数 |
| statsData.repostTotal | Integer | 转载数 |
| videoData.coverImage | String | 封面 |
| videoData.playAddress | String | 播放地址 |
| videoData.downloadNoMarkAddress | String | 无水印下载 |
| videoData.playDuration | Integer | 时长（毫秒） |

---

## 9. Instagram

**Path**: `/story/api/ins/search`

**请求体**:
```json
{"keyword": "关键词"}
```
- 可选 `paginationToken` 翻页

**响应**: `data.items[]`
| 字段 | 类型 | 说明 |
|------|------|------|
| mediaId | String | 媒体ID |
| code | String | 短码（拼接链接用） |
| captionText | String | 正文 |
| captionHashtags | Array | 标签 |
| mediaFormat | String | video/image/album |
| mediaType | Integer | 1=图片,2=视频,8=轮播 |
| imageUrl | String | 封面图 |
| thumbnailUrl | String | 缩略图 |
| videoUrl | String | 视频URL（图片时为null） |
| videoDuration | Double | 时长（秒） |
| playCount | Integer | 播放数 |
| likeCount | Integer | 点赞数 |
| commentCount | Integer | 评论数 |
| shareCount | Integer | 分享数 |
| takenAt | Integer | 秒级时间戳 |
| takenAtDate | String | ISO 8601 时间 |
| user.username | String | 用户名 |
| user.fullName | String | 显示名 |
| user.followerCount | Integer | 粉丝数 |
| user.profilePicUrl | String | 头像 |
| user.isVerified | Boolean | 是否认证 |

**URL 构造**: `https://www.instagram.com/p/{code}/`

---

## 10. X (Twitter)

**Path**: `/story/api/x/search`

**请求体**:
```json
{"keyword": "关键词", "searchType": "Top"}
```
- `searchType`: `Top`/`Latest`/`Media`/`People`/`Lists`
- `cursor`: 翻页游标

**响应**: `data.tweets[]`
| 字段 | 类型 | 说明 |
|------|------|------|
| tweetId | String | 推文ID |
| text | String | 正文内容 |
| createdAt | String | 发布时间 |
| language | String | 语言 |
| likeCount | Integer | 点赞数 |
| retweetCount | Integer | 转推数 |
| replyCount | Integer | 回复数 |
| quoteCount | Integer | 引用数 |
| bookmarkCount | Integer | 收藏数 |
| viewCount | String | 浏览量 |
| username | String | 作者用户名 |
| user.displayName | String | 显示名 |
| user.followers | Integer | 粉丝数 |
| user.avatar | String | 头像 |
| user.verified | Boolean | 是否认证 |
| medias[] | Array | 媒体附件 |
| medias[].type | String | video/photo |
| medias[].coverUrl | String | 媒体封面 |
| medias[].variants[] | Array | 视频清晰度列表 |

**URL 构造**: `https://x.com/{username}/status/{tweetId}`

---

## 11. YouTube

**Path**: `/story/api/youtube/searchVideo`

**请求体**:
```json
{"searchQuery": "关键词"}
```
- 注意参数名为 `searchQuery` 而非 `keyword`
- 可选 `continuationToken` 翻页

**响应**: `data.videos[]`
| 字段 | 类型 | 说明 |
|------|------|------|
| videoId | String | 视频ID |
| title | String | 标题 |
| description | String | 描述 |
| author | String | 频道名 |
| channelId | String | 频道ID |
| duration | String | 时长（如 "35:38"） |
| publishedTime | String | 发布时间 |
| viewCount | Integer | 播放量 |
| thumbnails[] | Array | 缩略图 |
| thumbnails[].url | String | 缩略图URL |

**URL 构造**: `https://www.youtube.com/watch?v={videoId}`
