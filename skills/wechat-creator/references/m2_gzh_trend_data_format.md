# 公众号爆款数据格式说明

## 数据来源

**接口**: 红狐数据 - 公众号爆款文章搜索
**URL**: `https://redfox.hk/story/api/gzh/search/hotArticleNew`
**API Key**: 从环境变量 `REDFOX_API_KEY` 读取（请勿在文档中硬编码真实 Key）

---

## API 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| keyword | string | 是 | 搜索关键词（多个关键词用英文逗号分隔，最多5个，总长度不超过200字符） |
| startDate | string | 是 | 开始日期，格式 yyyy-MM-dd（最长为最近30天） |
| endDate | string | 是 | 结束日期，格式 yyyy-MM-dd |
| source | string | 是 | 固定值：<见脚本> |

---

## API 返回字段说明

### 成功响应结构

```json
{
  "code": 2000,
  "msg": "成功",
  "data": {
    "articles": [
      {
        "id": "1623044070",
        "title": "职场没必要过度纠结的8件事，想开瞬间轻松",
        "author": "智联招聘",
        "url": "https://mp.weixin.qq.com/s?...",
        "imageUrl": "https://mmbiz.qpic.cn/...",
        "summary": "混迹职场越久越发明白...",
        "clicksCount": 19530,
        "watchCount": 40,
        "likeCount": 134,
        "commentsCount": 6,
        "publicTime": "2026-05-25 12:00:00",
        "popularityScore": 2.0,
        "recencyScore": 2.0,
        "relevanceScore": 7.21,
        "totalScore": 11.21,
        "sourceUsernickname": null,
        "publicTagInfo": null
      }
    ]
  }
}
```

### 文章字段详解

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 文章唯一标识 |
| title | string | 文章标题 |
| author | string | 公众号名称 |
| url | string | 文章链接（可跳转阅读原文） |
| imageUrl | string/null | 封面图片链接 |
| summary | string | 文章摘要/描述 |
| clicksCount | integer | 阅读数 |
| watchCount | integer | 在看数 |
| likeCount | integer | 点赞数 |
| commentsCount | integer | 评论数 |
| publicTime | string | 发布时间，格式 yyyy-MM-dd HH:mm:ss |
| popularityScore | float | 热度评分 |
| recencyScore | float | 时效评分 |
| relevanceScore | float | 相关度评分 |
| totalScore | float | 总评分 |
| sourceUsernickname | string/null | 来源用户昵称 |
| publicTagInfo | string/null | 标签信息（JSON字符串） |

---

## 时间范围自动拓展逻辑

当用户未指定时间范围时，脚本会自动处理：

1. **默认查询近7天**
2. **数据不足时自动拓展**：如果近7天数据少于10条，自动拓展至近30天
3. **用户指定时间则不拓展**：如果用户指定了 `--start-date`，按指定时间查询，不会自动拓展

---

## 关键词使用规范

### 多关键词规则
- 多个关键词用**英文逗号**分隔
- 最多支持 **5个** 关键词
- 总长度不超过 **200字符**

### 示例
```bash
# 单关键词
python scripts/fetch_gzh_trends.py --keyword "职场"

# 多关键词
python scripts/fetch_gzh_trends.py --keyword "职场,跳槽,辞职"

# 推荐实体类关键词组合（Step 0 提炼）
python scripts/fetch_gzh_trends.py --keyword "公众号,AI技能,爆款,效率工具"
```

---

## 输出格式

### Markdown 表格格式

| 序号 | 标题 | 作者 | **阅读数** | 在看 | 点赞 | 评论 |
|------|------|------|---------|------|------|------|
| 1 | [职场没必要过度纠结的8件事](文章链接) | 智联招聘 | **19530** | 40 | 134 | 6 |

### 字段说明

- **标题**：可点击跳转原文（Markdown链接格式）
- **作者**：公众号名称
- **阅读数**：加粗显示，强调传播范围
- **在看数**：反映内容深度与收藏价值
- **点赞数**：反映情绪共鸣程度
- **评论数**：反映话题性与互动效果

---

## 数据分析维度

### 1. 阅读数（clicksCount）
- **含义**：内容传播范围与吸引力
- **高阅读**：标题吸引、内容有价值、推送时间佳
- **分析要点**：观察阅读数与标题风格的关联

### 2. 在看数（watchCount）
- **含义**：内容深度与收藏价值
- **高在看**：干货密度高、实用性强、值得反复阅读
- **分析要点**：观察在看数与内容类型的关联

### 3. 点赞数（likeCount）
- **含义**：情绪共鸣程度
- **高点赞**：观点犀利、表达精准、引发认同
- **分析要点**：观察点赞数与观点表达的关联

### 4. 评论数（commentsCount）
- **含义**：话题性与互动引导效果
- **高评论**：观点有争议、结尾抛出问题、引发讨论
- **分析要点**：观察评论数与互动话术的关联

---

## 注意事项

1. **数据去重**：API可能返回重复数据，脚本会按 `id` 字段去重
2. **空标题处理**：如果标题为空，使用 `summary` 字段前30字符替代
3. **时间限制**：最长查询范围为最近30天
4. **自动拓展提示**：当自动拓展至30天时，会在输出中提示用户

---

## 更新记录

- 2026-06-01: 接口替换为红狐数据API，适配新的返回字段结构
