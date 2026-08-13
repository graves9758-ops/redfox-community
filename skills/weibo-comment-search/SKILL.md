---
name: weibo-comment-search
description: 微博评论分析工具。输入微博博文链接即可获取一级评论数据，支持分页浏览和四维情感分析（积极/负面/需求/竞品）。当用户需要查看微博评论、分析评论舆情、了解用户反馈时使用。触发词：微博评论、博文评论、评论查询、评论分析、看评论。
---

# 微博评论分析

## 📝 简介

微博评论分析工具，输入微博博文链接，即可查看该博文的一级评论数据，支持分页浏览和 AI 情感分析。在对话中展示当前页全部评论及 AI 总结分析，同时生成包含当前页数据和总结的交互式 HTML 报告。

## ✨ 功能特性

| 功能模块 | 能力描述 | 核心价值 |
|---------|---------|---------|
| 评论查询 | 输入微博博文链接查询评论 | 一键查看任意博文的评论 |
| 分页浏览 | 支持多页结果浏览 | 逐页探索更多评论 |
| AI 总结 | 四维情感分析（积极/负面/需求/竞品） | 快速了解评论舆情全貌 |
| HTML 报告 | 深色主题交互式报告 | 离线保存/分享分析结果 |

## 🔑 鉴权

### 获取 API Key

请前往 [红狐hub](https://redfox.hk/settings/api-keys?source=github) 获取 API KEY

### 配置 API Key

方案1: 以 Qoder 为例，将 REDFOX_API_KEY 添加到 `~/.openclaw/openclaw.json` 中：

```bash
{ "env": { "REDFOX_API_KEY": "ak_xxxx..." } }
```

方案2: 终端配置

```bash
export REDFOX_API_KEY="ak_xxxx..."
```

## 🔄 工作流程

### Step 1：理解用户意图，提取 opusId

**1. 从微博博文链接中提取 opusId**

- 若用户提供了博文链接（如 `https://weibo.com/1784473157/R8X4f2lnq`），从中提取 opusId（`R8X4f2lnq`）
- 若用户直接提供了 opusId，直接使用
- 若用户意图模糊（如"帮我查下评论"），主动询问：「请提供微博博文链接」
- 不得在用户未提供链接时擅自猜测并调用脚本
- 若用户在上一轮对话中查询过某博文的评论，且本轮输入模糊（如"下一页"、"评论分析"），沿用上一轮的 opusId

**2. 识别页码参数**

- 用户提到"下一页"、"第2页" → 对应页码，同时使用上一轮返回的 max_cursor
- 用户提到"上一页" → 当前页 - 1
- 未提及页码 → 默认第 1 页

### Step 2：调用查询脚本（自动生成 HTML）

**⚠️ 每次调用仅请求一页数据（一次 API 请求），不可擅自发起多次调用拉取多页。**

**脚本每次调用自动生成 HTML 报告**（含 `{{PLACEHOLDER}}` 占位符，未回填分析数据）。终端展示与 HTML 基于**同一次 API 调用**，确保数据一致。

```bash
python3 ~/.agents/skills/weibo-comment-search/scripts/weibo_comment_search.py "<博文链接或opusId>" [--page 页码] [--cursor 游标] [--output-dir 目录]
```

**参数说明：**

| 参数 | 说明 | 默认值 |
|------|------|--------|
| input | 微博博文链接或 opusId | — |
| `--page` | 页码，从1开始 | `1` |
| `--cursor` | 翻页游标（首页为 0，后续从返回的 max_cursor 传入） | `0` |
| `--no-html` | 跳过 HTML 报告生成 | — |
| `--output-dir` | HTML 输出目录 | `~/Downloads/QoderReports` |

脚本以 JSON 格式输出：

| 字段 | 说明 |
|------|------|
| `opus_id` | 博文 opusId |
| `comments` | 评论列表 |
| `max_cursor` | 下一页游标 |
| `has_next` | 是否有下一页（true/false） |
| `page` | 当前页码 |
| `html_path` | 生成的 HTML 报告路径（含占位符，待回填） |

每条评论字段：

| 字段 | 说明 |
|------|------|
| `nickname` | 用户昵称 |
| `uid` | 用户 uid |
| `user_url` | 用户主页链接（`https://weibo.com/{uid}`） |
| `content` | 评论内容 |
| `comment_like_num` | 点赞数（原始数字） |
| `comment_like_num_fmt` | 点赞数（格式化后） |
| `create_time` | 发布时间 |

> **注意：** HTML 报告此时仅含评论原始数据，分析占位符（`{{PLACEHOLDER}}`）待用户确认后回填。

### Step 3：判断结果并展示

#### 情况 A：comments 数量 > 0（有评论）

**A1. 告知用户查询范围**

> 📊 博文 `{opus_id}` 查询到 **N 条**评论（第 {page} 页），以下是详细数据：

**A2. 渲染 Markdown 表格（全部展示）**

```markdown
| # | 用户 | 评论内容 | 点赞 | 发布时间 |
|---|------|----------|------|----------|
| 1 | [nickname](https://weibo.com/uid) | 评论内容 | 305 | 2025-07-10 14:30:25 |
```

**格式规则：**
- 用户昵称渲染为超链接：`[nickname](user_url)`，跳转到用户主页
- 点赞数 `< 10000` 原始数字，`≥ 10000` 显示 `x.xw`
- 发布时间完整展示年月日时分秒
- 评论内容超过 50 字截断并加 `...`，内容为空时显示 `-`
- ⚠️ 当前页全部评论均需展示，不得截断

**A3. AI 评论总结（⚠️ 每次查询（含翻页）必须输出）**

**首页**：基于当前页获取到的全部评论，进行四维情感分析。

**翻页后**：基于**目前已获取的所有页面累计数据**进行综合分析，而非仅分析当前单页。分析时需标注累计总条数。

**分析前需理解微博热点话题背景**（热搜事件、粉丝文化、明星动态、社会议题语境）。

> ## 📈 评论总结分析（基于 {total} 条评论）
>
> ### ✅ 积极评价（{positive_ratio}%）
> - {要点1}
> - {要点2}
> - ...
>
> ### ⚠️ 负面评价（{negative_ratio}%）
> - {要点1}
> - {要点2}
> - ...
>
> ### 💡 用户需求（{demand_ratio}%）
> - {要点1}
> - {要点2}
> - ...
>
> ### 🔍 竞品对比舆情（{competitor_ratio}%）
> - {仅当评论中提及竞品时输出，否则输出「未提及竞品」}
> - {竞品名称}：{舆情要点}

**分析要求：**
- 每条要点需引用代表评论（截取关键词/短语）
- 百分比为提及该类型评论的数量占总评论数的比例
- 积极/负面/需求/竞品四类占比总和可能超过 100%（一条评论可能同时包含多类信息）
- **必须理解微博语境**：识别粉丝话术（如"抱走""纯路人""yyds""打call"等）、热门话题背景、明星相关舆情

**A4. 翻页提示（⚠️ 紧接在 A3 之后，每次必须输出）**

- 若 `has_next` 为 true：
> 📄 当前第 **{page}** 页。回复「下一页」继续查看。

- 若 `has_next` 为 false：
> 📄 当前第 **{page}** 页，已无更多数据。

**⚠️ A1~A4 必须在同一轮输出中连续完成，不可省略任何一步。**

A4 输出完毕后，**询问用户是否需要生成 HTML 可视化报告**：

> 📊 是否需要生成 HTML 可视化报告？

**若用户回复「是」「需要」「生成」「html」等确认词**，则执行以下步骤（**无需重新调用脚本**，HTML 文件已在 Step 2 生成）：

**① 回填 AI 分析结果到 HTML**

调用 `backfill_html.py` 将 AI 分析结果回填到 HTML 中的 `{{PLACEHOLDER}}` 占位符：

```bash
python3 ~/.agents/skills/weibo-comment-search/scripts/backfill_html.py "<html_path>" --analysis-json '{
  "positive_ratio": <正整数>,
  "negative_ratio": <正整数>,
  "demand_ratio": <正整数>,
  "competitor_ratio": <正整数>,
  "positive_summary": "<ul><li>要点1</li><li>要点2</li>...</ul>",
  "negative_summary": "<ul><li>要点1</li><li>要点2</li>...</ul>",
  "demand_summary": "<ul><li>要点1</li><li>要点2</li>...</ul>",
  "competitor_summary": "<ul><li>要点1</li><li>要点2</li>...</ul>"
}'
```

**JSON 字段说明：**

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `positive_ratio` | int | 积极评价占比（纯数字，不含%） | `45` |
| `negative_ratio` | int | 负面评价占比 | `30` |
| `demand_ratio` | int | 用户需求占比 | `15` |
| `competitor_ratio` | int | 竞品对比占比 | `15` |
| `positive_summary` | string | 积极评价摘要（HTML 格式 `<ul><li>...</li></ul>`） | 见示例 |
| `negative_summary` | string | 负面评价摘要 | 同上 |
| `demand_summary` | string | 用户需求摘要 | 同上 |
| `competitor_summary` | string | 竞品对比摘要 | 同上 |

**注意：** JSON 字符串参数包含双引号，Bash 中使用单引号包裹，内部双引号需转义 `\"`。若内容含单引号则用 stdin 方式传入：`echo '...' | python3 backfill_html.py "<html_path>"`

**② 打开 HTML 报告：**

```bash
open "<html_path>"
```

#### 情况 B：comments 数量 = 0（无评论）

**B1. 提示**

> 😔 该博文暂无评论数据。

### Step 4：翻页处理

当用户回复「下一页」「上一页」「第 N 页」时：

1. 沿用 Step 1 中提取的 opusId
2. 使用上一轮返回的 `max_cursor` 作为新的 `--cursor`
3. 计算新页码
4. 重新调用脚本（**与 Step 2 一致，自动生成 HTML**）：`python3 .../weibo_comment_search.py "<opusId>" --page <page> --cursor <cursor>`
5. **完整执行 Step 3 的 A1~A4**，其中：
   - A1/A2：仅展示当前页数据（展示范围不变）
   - **A3 评论分析：基于目前已获取的所有页面累计数据（第 1 页至当前页）进行综合分析**，标题中 {total} 为累计总条数
6. A4 后询问用户是否需要生成当前页 HTML（同 Step 3 末尾流程，**无需重新调用脚本**）

### Step 5：错误处理

| 错误类型 | 处理方式 |
|---------|---------|
| 无 API Key | 提示配置 REDFOX_API_KEY，给出配置指引 |
| 博文链接无效 | 提示「无法提取 opusId，请检查博文链接是否正确」 |
| 接口返回错误 | 显示错误码和错误信息 |
| 获取 0 条评论 | 提示「该博文暂无评论」并建议检查博文是否存在或已删除 |
| 网络请求超时 | 提示「网络请求超时，请稍后重试」 |

---

## 📋 依赖

```bash
# 脚本使用 urllib（Python 标准库），无需额外安装依赖
```

---

## 🎯 使用示例

**示例 1：查看指定博文的评论**
```
用户：查看微博 https://weibo.com/1784473157/R8X4f2lnq 的评论
助手：调用脚本（自动生成HTML） → 展示全部评论 + AI总结 → 询问是否需要HTML → 用户确认 → backfill → open
```

**示例 2：通过 opusId 查询**
```
用户：R8X4f2lnq 这篇博文的评论怎么样
助手：提取 opusId → 调用脚本 → 展示分析 → 询问是否需要HTML
```

**示例 3：翻页**
```
用户：下一页
助手：调用脚本 page=2 cursor=xxx → 展示第2页 + AI累计分析 → 询问是否需要当前页HTML
```
