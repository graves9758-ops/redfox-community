# API接口规范

## 接口信息

- **接口地址**：`https://redfox.hk/story/api/cozeSkill/getWxDataByCategoryAndTime`
- **请求方法**：GET
- **Content-Type**：application/json

## 认证方式

| 参数 | 说明 |
|------|------|
| X-API-KEY | API密钥，从环境变量 `REDFOX_API_KEY` 获取，未设置则自动从 shell 配置文件（`~/.zshrc`、`~/.bash_profile` 等）读取 |

## 请求头

```
Content-Type: application/json
X-API-KEY: <your_api_key>
```

## 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| type | string | 是 | 分类名称（标准23分类之一） |
| source | string | 是 | 数据来源，固定值："公众号10w+阅读文章推荐-GitHub" |
| startDate | string | 是 | 开始日期，格式：YYYY-MM-DD |
| endDate | string | 是 | 结束日期，格式：YYYY-MM-DD |

## 标准分类列表

共23个标准分类：
- 人文资讯、知识百科、健康养生、时尚潮流、美食餐饮、乐活生活
- 旅游出行、搞笑幽默、情感心理、体育娱乐、美容美体、文摘精选
- 民生资讯、财富理财、科技数码、创投商业、汽车交通、房产楼市
- 职场发展、教育考试、学术研究、企业品牌、总排名

## 请求示例

### 1. 查询总排名（昨日数据）

```
GET https://redfox.hk/story/api/cozeSkill/getWxDataByCategoryAndTime?type=总排名&source=公众号10w+阅读文章推荐-GitHub&startDate=2026-05-13&endDate=2026-05-14
```

### 2. 查询科技数码分类

```
GET https://redfox.hk/story/api/cozeSkill/getWxDataByCategoryAndTime?type=科技数码&source=公众号10w+阅读文章推荐-GitHub&startDate=2026-05-13&endDate=2026-05-14
```

### 3. 查询财富理财分类

```
GET https://redfox.hk/story/api/cozeSkill/getWxDataByCategoryAndTime?type=财富理财&source=公众号10w+阅读文章推荐-GitHub&startDate=2026-05-10&endDate=2026-05-14
```

## 响应数据结构

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "tenWReadingRank": [
      {
        "accountId": "zepinghongguan",
        "clicksCount": "10w+",
        "commentCount": "3",
        "content": "文章内容摘要...",
        "coverUrl": "https://...",
        "fans": "100w+",
        "interactiveCount": "3413",
        "likeCount": "606",
        "orderNum": 0,
        "oriUrl": "https://mp.weixin.qq.com/s?...",
        "originalFlag": 1,
        "photoId": "...",
        "publicTime": "2026-04-15 00:01:14",
        "shareCount": "2613",
        "summary": "摘要内容",
        "thumbnail": "https://...",
        "title": "文章标题",
        "type": "财富",
        "userHeadUrl": "https://...",
        "userName": "作者名称",
        "watchCount": "191"
      }
    ]
  }
}
```

## 数据字段说明

| 字段名 | 说明 |
|--------|------|
| accountId | 公众号ID |
| clicksCount | 阅读数（如：10w+、5w+） |
| commentCount | 评论数 |
| content | 文章内容摘要 |
| coverUrl | 封面图URL |
| fans | 粉丝数 |
| interactiveCount | 互动数 |
| likeCount | 点赞数 |
| oriUrl | 文章原文链接 |
| publicTime | 发布时间 |
| shareCount | 分享数 |
| summary | 摘要 |
| title | 文章标题 |
| type | 文章分类 |
| userName | 作者名称 |

## 时间参数规则

### 重要规则

1. **所有时间参数都是必传的**：
   - `startDate`：必须传入，格式为 YYYY-MM-DD
   - `endDate`：必须传入，格式为 YYYY-MM-DD

2. **时间参数示例**（假设今天是 2026-05-14）：
   - 查询昨天数据：`startDate=2026-05-13&endDate=2026-05-14`
   - 查询前天数据：`startDate=2026-05-12&endDate=2026-05-13`
   - 查询近5天：`startDate=2026-05-10&endDate=2026-05-14`

3. **数据同步时间**：
   - 数据库每日下午 18:30 同步前一日数据
   - 到 19:30 推送时，昨天的数据已完全同步

4. **时间建议**：
   - 用户主动查询"今日文章"：使用前天数据（更稳妥）
   - 订阅推送（19:30）：使用昨天数据（已同步完成）
