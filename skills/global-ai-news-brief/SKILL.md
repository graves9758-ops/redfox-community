---
name: global-ai-news-brief
description: 全球AI新闻简报 — 一个关键词同时搜索抖音、小红书、公众号、B站、快手、视频号、今日头条、TikTok、Instagram、X(Twitter)、YouTube 共 11 大平台，跨平台聚合后由 AI 生成智能摘要、热点聚类、舆情分析和深度解读报告，输出终端表格 + 交互式 HTML 报告。包含详细信息源列表，适用于各种AI agent进行社媒资讯分析。当用户需要新闻搜索、舆情分析、热点追踪、跨平台情报对比、资讯聚合、新闻解读、全网搜索、事件追踪、行业情报时使用。触发词：新闻情报、全网搜索、舆情分析、热点追踪、新闻解读、资讯聚合、跨平台分析、事件追踪、行业情报、news brief、global news。
---

# 全球AI新闻简报

输入一个关键词，同时发起 11 大平台搜索请求，跨平台聚合数据后由 AI 生成深度情报报告。

## 覆盖平台

| # | 平台 | 接口路径 | 搜索参数 | 排序选项 |
|---|------|---------|---------|---------|
| 1 | 抖音 | `/story/api/dy/data/searchWork` | keyword, pageNum, pageSize | — |
| 2 | 小红书 | `/story/api/xhsUser/searchArticle` | keyword, offset, sortType | 0=默认/2=最新/4=最热 |
| 3 | 公众号 | `/story/api/gzh/data/searchArticle` | keyword, offset, sortType | 0=默认/2=最新/4=最热 |
| 4 | B站 | `/story/api/bili/data/workSearch` | keyword, page, pageSize, order | time/play/like/comment/favorite |
| 5 | 快手 | `/story/api/ksAllData/searchWork` | keyword, page, size, sort | 综合/最新/最多点赞/最多收藏 |
| 6 | 视频号 | `/story/api/sphAllData/searchWork` | keyword, sort, page, size | 综合/最新/最多点赞/最多收藏 |
| 7 | 今日头条 | `/story/api/toutiao/searchWork` | keyword, offset | — |
| 8 | TikTok | `/story/api/tiktok/ability/searchVideo` | keyword, offset, count, sortType, publishTime, region | 0=相关度/1=最多点赞 |
| 9 | Instagram | `/story/api/ins/search` | keyword, paginationToken | — |
| 10 | X(Twitter) | `/story/api/x/search` | keyword, searchType, cursor | Top/Latest/Media |
| 11 | YouTube | `/story/api/youtube/searchVideo` | searchQuery, continuationToken | — |

> 所有接口 Host: `https://redfox.hk`，Method: `POST`，Content-Type: `application/json`，鉴权方式见下方「🔑 鉴权」。
> 详细请求/响应字段见 [api-reference.md](api-reference.md)。

## 🔑 鉴权

### 获取 API Key

请前往 [红狐hub](https://redfox.hk/settings/api-keys?source=github) 获取 API KEY

### 配置 API Key

方案1: 以 OpenClaw 为例，将 REDFOX_API_KEY 添加到 `~/.openclaw/openclaw.json` 中：

```bash
{ "env": { "REDFOX_API_KEY": "ak_xxxx..." } }
```

方案2: 终端配置

```bash
export REDFOX_API_KEY="ak_xxxx..."
```

所有平台接口的请求头均携带 `REDFOX-API-KEY` + `X-API-Key`（值均为 `$REDFOX_API_KEY`），缺失时脚本报错退出并提示配置。

## 工作流程

### Step 1：关键词处理

- 用户输入的关键词直接作为搜索词
- 若输入含"达人""博主""KOL""网红""账号"等后缀，自动剥离后缀仅保留核心语义词
- 可询问用户是否需要指定平台范围（默认全部 11 个平台）

### Step 2：并行数据采集

使用脚本 [scripts/fetch_all.py](scripts/fetch_all.py) 一键并行采集（内部用线程池并发请求全部平台）：

```bash
python3 ~/.agents/skills/global-ai-news-brief/scripts/fetch_all.py "关键词" --pretty
```

- **前置条件**：环境变量 `REDFOX_API_KEY` 已设置（脚本会检测，缺失时报错退出）
- **默认行为**：并行请求全部 11 个平台，每个平台取首页数据（20条）
- **指定平台子集**：`--platforms douyin,xhs,gzh,bilibili,kuaishou,shipinhao,toutiao`（仅搜国内平台时用）
- **输出**：标准化 JSON 写入 `/tmp/news_intel_result.json`，同时在 stderr 打印各平台采集状态
- **容错**：单平台失败自动跳过，在结果的 `failedPlatforms` 字段中标注，不影响其他平台

输出 JSON 结构：

```
{
  keyword: string,          // 搜索关键词
  generatedAt: string,      // 生成时间
  platformCount: number,    // 成功平台数
  failedPlatforms: [],      // 失败平台列表 [{platform, error}]
  totalItems: number,       // 总内容条数
  totalEngagement: number,  // 总互动量（点赞+评论+分享+播放）
  results: {                // 按平台 key 分组
    douyin: { platform, count, total, items[] },
    ...
  }
}
```

每个 `items[]` 条目已由脚本标准化为统一结构（见 Step 3），Agent 直接读取 JSON 文件做分析即可，无需再处理各平台字段名差异。

### Step 3：数据标准化

将各平台返回数据统一为以下标准结构：

```
{
  platform: string,     // 平台名称
  title: string,        // 标题/描述首行
  content: string,      // 正文/描述
  author: string,       // 作者昵称
  url: string,          // 作品链接
  publishTime: string,  // 发布时间
  likes: number,        // 点赞数
  comments: number,     // 评论数
  shares: number,       // 分享/转发数
  views: number,        // 播放/阅读数
  collects: number,     // 收藏数
  followers: number,    // 作者粉丝数
  coverUrl: string,     // 封面图
  mediaType: string     // video/image/text
}
```

**字段映射要点**（处理各平台字段名差异）：

| 标准字段 | 抖音 | 小红书 | 公众号 | B站 | 快手 | 视频号 | 头条 | TikTok | Instagram | X | YouTube |
|---------|------|-------|-------|-----|-----|-------|------|--------|----------|---|---------|
| title | content | workTitle | title | title | caption | description | title | content | captionText | text | title |
| author | authorName | accountNickname | author | author | nickname | nickname | nickname | authorData.userName | user.fullName | user.displayName | author |
| likes | likeCount | workLikedCount | likeCount | likeCount | likeCount | likeCount | — | statsData.likeCount | likeCount | likeCount | — |
| comments | commentCount | workCommentsCount | commentCount | commentCount | commentCount | commentCount | commentNum | statsData.commentTotal | commentCount | replyCount | — |
| views | — | — | readCount | playCount | viewCount | — | — | statsData.viewCount | playCount | viewCount | viewCount |
| url | opusUrl | workUrl | workUrl | 拼接BV | 拼接photoId | — | opusUrl | shareLink | 拼接code | 拼接tweetId | 拼接videoId |

### Step 4：AI 智能分析与输出

对聚合后的全部数据执行分析，**严格按以下四个板块依次输出**（终端和 HTML 报告均遵循此顺序）：

---

#### 板块一：新闻事件

还原"发生了什么"——客观呈现事件全貌。

- **事件概述**：用 3-5 句话概括核心事件（谁、什么、何时、何地、影响范围）
- **关键事件时间线**：按发布时间排列关键节点，还原事件从萌芽到发酵的传播路径；排序规则：**最新时间在最上面（倒序）**，无明确日期的条目（如「海外长线」）排在最后
- **热点话题聚类**：将全部内容按主题自动聚类为 3-8 个热点话题，每个话题标注：
  - 主题名称
  - 涉及平台数
  - 代表内容 2-3 条（含标题、作者、平台、链接）

---

#### 板块二：新闻解读

AI 深度分析"意味着什么"——提炼洞察与判断。

- **核心摘要**：200 字以内的精炼总结，包含事件定性、影响评估、趋势预判
- **关键发现**：3-5 条核心洞察，每条包含论点 + 数据支撑
- **舆情风向**：
  - 全网情感分布：正面 / 中性 / 负面占比
  - 核心共识点（多数人认同的观点）
  - 核心争议点（分歧最大的议题）
- **大V观点（KOL）**：识别粉丝量 > 10000 或单条互动量 TOP 的作者，列出作者名、平台、粉丝数、代表观点；标题统一使用通俗说法「大V观点」，不使用「关键意见领袖」。账号名渲染为可点击链接跳转作者主页，主页链接拼接规则（从作品链接或接口字段提取作者 ID 拼接）：
  - X/Twitter：`https://x.com/{username}`（从作品 url `/status/` 前段提取）
  - TikTok：`https://www.tiktok.com/@{username}`（从作品 url `/@xxx/` 段提取）
  - Instagram：`https://www.instagram.com/{username}/`
  - B站：`https://space.bilibili.com/{mid}`（接口无 mid 时回退 `https://search.bilibili.com/all?keyword={作者名}`）
  - 公众号：`https://open.weixin.qq.com/qr/code?username={biz}`
  - 快手/小红书等无法提取作者 ID 的平台：回退平台搜索链接（如 `https://www.kuaishou.com/search/video?searchKey={作者名}`）
  - 视频号无公开主页链接：不渲染链接

---

#### 板块三：各平台不同的解读倾向

跨平台对比"各平台怎么看"——揭示平台差异化特征。

对每个有数据的平台分析以下维度：

| 分析维度 | 说明 |
|---------|------|
| 情感倾向 | 该平台正面/中性/负面比例，与全网均值对比 |
| 关注焦点 | 该平台用户最关注的子话题/角度（与其他平台的差异点） |
| 内容形态 | 以视频/图文/长文哪种为主 |
| 热度指标 | 内容条数、总互动量、平均互动量 |
| 代表声音 | 该平台互动量最高的 2-3 条内容及观点摘要 |

输出为**跨平台对比矩阵表**：

```markdown
| 平台 | 内容数 | 总互动 | 情感倾向 | 关注焦点 | 代表观点 |
|------|-------|-------|---------|---------|---------|
| 抖音 | 20 | 58000 | 正面65% | 事件现场视频 | "xxx" |
| 公众号 | 18 | 120000 | 中性55% | 深度分析文章 | "xxx" |
| X/Twitter | 15 | 9200 | 负面60% | 批评与讨论 | "xxx" |
```

---

#### 板块四：数据源

原始数据完整展示——按平台分段列出全部搜索结果。

**终端输出**：每个平台展示 TOP 5 表格：

```markdown
### 抖音 TOP 5

| # | 标题 | 作者 | 点赞 | 评论 | 分享 | 发布时间 | 链接 |
|---|------|------|------|------|------|---------|------|
| 1 | xxx | xxx | 8000 | 280 | 150 | 2026-05-20 | [查看](url) |
```

**HTML 报告**：每个平台一个可切换 Tab，展示该平台全部数据条目，含封面图、标题、作者、完整数据指标、原文链接。

**数据时间范围标注**：数据源标题（h2「四、数据源」）后以 .formula-note 小字标注实际数据时间范围，如「（数据时间范围：2026-07-20 ~ 2026-08-19 为主体近30天数据，含少量历史旧闻，最早 2024-07-02）」。计算规则：
- 解析全部条目的 publishTime（兼容三种格式：`YYYY-MM-DD...`、X/Twitter 的 `%a %b %d %H:%M:%S +0000 %Y`、相对时间 `N days/weeks/months ago`（以采集日为基准推算）），取最小/最大日期
- 口径：报告当前时间前 30 天为主体窗口，若 90% 以上条目落在此窗口，文案注明「主体近30天（起始日期 ~ 最晚日期）」；窗口外的更早条目计为「历史旧闻」，注明最早日期

### Step 5：HTML 报告生成

使用 [assets/report-template.html](assets/report-template.html) 模板生成交互式 HTML 报告，严格按四大板块组织：

1. **顶部概览**：subtitle 行展示搜索关键词、覆盖平台数、总内容条数、**数据时间范围（短格式「YYYY-MM-DD ~ YYYY-MM-DD」，长说明在数据源标题后）**；概览卡片区仅 4 张卡（覆盖平台/内容总数/总互动量/活跃平台）；生成时间只出现在页面底部 footer
2. **板块一 · 新闻事件**：事件概述卡片 + 垂直时间轴 + 热点话题标签云 + 热点话题详情卡片（.topic-list 网格 + .topic-card 卡片样式，卡头带蓝色小方块装饰 + 话题名 + 平台数，正文为项目符号列表）
3. **板块二 · 新闻解读**：核心摘要区 + 关键发现列表 + 舆情风向仪表盘（正面/中性/负面进度条）+ 大V观点卡片
4. **板块三 · 各平台解读倾向**：跨平台对比矩阵表 + 各平台情感对比柱状图（CSS 实现，标题后以 .formula-note 小字标注计算公式「互动量 = 点赞 + 评论 + 分享 + 播放」）+ 差异亮点
5. **板块四 · 数据源**：平台 Tab 切换器，每个 Tab 内展示该平台全部内容卡片（封面、标题、作者、指标、链接）。**Tab 排序规则：按平台互动量（点赞+评论+分享+播放）降序排列，互动量最高的平台排最前**；Tab 内条目保持接口返回原始顺序，不做二次排序

**封面展示规则**：

- 接口不返回封面的平台（如今日头条）：该平台所有卡片不渲染封面区域，直接从正文开始（生成时检测：平台内全部条目 coverUrl 为空即视为无封面平台）
- 其他平台封面为空时：渲染固定高度（180px）白色背景占位块，保证卡片高度统一
- 封面加载失败（onerror）：移除 src 保留白色占位块，不隐藏不塌陷

**对话输出**：报告中生成的所有关键标注必须同步展示在对话回复中，包括：
- 数据时间范围（短格式 + 主体占比/历史旧闻说明）
- 互动量计算公式口径：互动量 = 点赞 + 评论 + 分享 + 播放（接口不返回播放量的平台按 0 计）
- 各平台数据统计、互动排名、报告文件路径

HTML 文件保存到本 Skill 的 [output/](output/) 目录，文件名 `global-ai-news-brief-report-{keyword}-{date}.html`（目录不存在时先创建），用 `open` 命令打开。禁止保存到 /tmp 等临时目录。

## 错误处理

- 某个平台请求失败时跳过该平台并在报告中标注"数据暂不可用"
- 不阻断其他平台数据采集
- API 密钥缺失时提示用户设置 `REDFOX_API_KEY` 环境变量

## 使用示例

```
用户：帮我查一下"新能源汽车"最新的全网舆情
Agent：→ 并行搜索 11 平台 → 聚合数据 → AI 分析 → 输出终端表格 + HTML 报告

用户：追踪一下"台风"相关的全网信息
Agent：→ 同上流程，侧重时间线和事件追踪

用户：只看国内平台，搜一下"暑期旅游"
Agent：→ 仅搜索抖音/小红书/公众号/B站/快手/视频号/头条 7 个国内平台
```
