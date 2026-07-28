# 公众号爆款数据格式说明

## 概览

本文档定义了公众号爆款封面数据查询脚本 `fetch_explosive_covers.py` 的输入输出格式规范。

**接口地址**：`POST https://redfox.hk/story/api/gzh/search/hotArticleNew`

## 输入格式

### 脚本参数

```bash
python3 scripts/fetch_explosive_covers.py --keyword <关键词> [选项]
```

| 参数 | 必填 | 说明 | 默认值 |
|------|------|------|--------|
| `--keyword` | 是 | 搜索关键词（支持多个，逗号分隔，空字符串查全站热门） | - |
| `--start-date` | 否 | 开始日期，格式 yyyy-MM-dd | 不传（接口自行决定） |
| `--end-date` | 否 | 结束日期，格式 yyyy-MM-dd | 不传（接口自行决定） |
| `--max-items` | 否 | 最多展示文章数量 | 20 |
| `--output-format` | 否 | 输出格式：text、json 或 markdown | json |
| `--output-file` | 否 | 输出文件路径 | 不输出文件 |
| `--debug` | 否 | 调试模式 | False |

## 输出格式

### 文章数据字段

每篇文章（`articles` 数组中的对象）包含以下字段：

#### 文章基本信息

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `id` | string | 文章ID（唯一标识） |
| `title` | string | 文章标题（可能为空，需从 summary 提取） |
| `summary` | string | 文章摘要/正文片段 |
| `publicTime` | string | 发布时间（格式：YYYY-MM-DD HH:MM:SS） |
| `url` | string | 文章链接（完整URL） |

#### 作者信息

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `author` | string | 公众号名称/作者名 |

#### 互动数据

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `clicksCount` | int | 阅读数 |
| `watchCount` | int | 在看数 |
| `likeCount` | int | 点赞数 |
| `shareCount` | int | 分享数 |
| `commentsCount` | int | 评论数 |

#### 封面图

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `imageUrl` | string | 封面图URL（旧接口字段名为 `coverUrl`） |

#### 评分字段（用于排序）

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `totalScore` | float | 总分（用于排序） |
| `relevanceScore` | float | 相关性评分 |
| `popularityScore` | float | 热度评分 |
| `recencyScore` | float | 时效评分 |

#### ⚠️ 新接口缺失字段

以下字段在旧接口（getWxCozeSkillData）中存在，**hotArticleNew 接口不返回**：

| 缺失字段 | 说明 | 影响 |
|----------|------|------|
| `userName` | 公众号名称 | 已改为 `author` 字段 |
| `photoId` | 文章旧ID | 已改为 `id` 字段 |
| `oriUrl` | 文章旧链接 | 已改为 `url` 字段 |
| `accountId` | 公众号账号ID | 无法拼接二维码链接 |
| `userHeadUrl` | 作者头像 | 无法展示作者头像 |

### JSON 输出示例

```json
{
  "keyword": "职场",
  "articles": [
    {
      "id": "abc123",
      "title": "职场新人必知的10个技巧",
      "summary": "刚入职场的你是否感到迷茫...",
      "author": "职场达人",
      "publicTime": "2026-07-20 10:30:00",
      "url": "https://mp.weixin.qq.com/s/xxxxx",
      "imageUrl": "https://mmbiz.qpic.cn/mmbiz_jpg/...",
      "clicksCount": 58000,
      "watchCount": 320,
      "totalScore": 85.5,
      "relevanceScore": 8.2,
      "popularityScore": 7.5,
      "recencyScore": 6.0
    }
  ],
  "latestHotArticles": [],
  "hotTopics": [
    { "name": "职场晋升", "count": 120 }
  ],
  "relatedSearches": ["职场沟通", "职场穿搭"]
}
```

## 关于封面图

新接口（hotArticleNew）封面图字段名为 `imageUrl`，旧接口为 `coverUrl`，脚本已做双字段兑容处理。

## 使用注意事项

### 数据获取原则

1. **必须调用脚本查询**：不能使用其他方式查询或直接搜索网络资讯
2. **必须等待脚本执行完成**：获取返回结果后才能进行后续步骤
3. **必须展示完整数据列表**：不能跳过或询问用户

### 字段说明

1. **标题提取**：如果 `title` 字段为空，从 `summary` 字段提取前30个字符作为标题
2. **作者名称**：使用 `author` 字段
3. **阅读数格式**：整数，脚本中格式化为 `1.0w` 形式（≥10000时）
4. **文章链接**：使用 `url` 字段
