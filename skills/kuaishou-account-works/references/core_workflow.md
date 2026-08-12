# Core Workflow

## 工作流程

根据用户诉求二选一：**按账号查作品列表** 走场景 A，**查单条作品详情** 走场景 B。

---

### 场景 A：按账号查询作品列表（queryWorkList）

#### Step 1：调用列表查询脚本

```bash
python3 ~/.workbuddy/skills/kuaishou-account-works/scripts/search_ks_work.py --kwai-id "<kwaiId>" [--page 页码] [--size 每页条数]
# 或
python3 ~/.workbuddy/skills/kuaishou-account-works/scripts/search_ks_work.py --threex-id "<主页链接id>" [--page 页码] [--size 每页条数]
```

**参数说明：**

| 参数 | 必填 | 含义 |
|------|------|------|
| `--kwai-id` | 二选一 | 快手账号平台展示 id（如 `rmrbxmtzx`，账号搜索接口返回） |
| `--threex-id` | 二选一 | 快手账号主页链接 id（如 `3x4wxhrrzefrq4y`） |
| `--page` | 否 | 页码，从 1 开始（默认：1） |
| `--size` | 否 | 每页条数（默认：20，最大 50） |

脚本以 JSON 格式输出：

| 字段 | 说明 |
|------|------|
| `articles` | 该账号的作品列表（按发布时间倒序） |
| `page` | 当前页码 |
| `size` | 每页条数 |
| `has_next` | 是否有下一页（true/false） |
| `total` | 本次返回条数 |

每条作品字段：

| 字段 | 说明 |
|------|------|
| `title` | 作品标题（caption） |
| `author` | 账号昵称（nickname） |
| `author_fans` | 作者粉丝数 |
| `play_count` | 播放数（viewCount） |
| `like_count` | 点赞数（likeCount） |
| `comment_count` | 评论数（commentCount） |
| `collect_count` | 收藏数（collectCount） |
| `share_count` | 分享数（shareCount） |
| `forward_count` | 转发数（forwardCount） |
| `duration` | 视频时长（毫秒） |
| `work_url` | 视频 URL（videoUrl） |
| `cover_url` | 封面 URL（coverUrl） |
| `publish_time` | 发布时间（YYYY-MM-DD HH:MM:SS） |
| `publish_date` | 发布日期（YYYY-MM-DD） |
| `work_id` | 作品 ID（photoId） |
| `work_type` | 作品类型（workType） |

#### Step 2：判断结果并展示

##### 情况 A1：articles 数量 > 0（查询到作品）

**A1-1. 告知用户查询范围**

> 📊 账号「**{author}**」查询到 **N 条**作品（按发布时间倒序 | 第 {page} 页），以下是详细数据：

**A1-2. 渲染 Markdown 表格（⚠️ 必须逐条输出，条数必须与 A1-1 中 N 一致，一条不漏）**

```markdown
| # | 作品标题 | 播放数 | 点赞数 | 评论数 | 收藏数 | 发布时间 |
|---|---------|--------|--------|--------|--------|---------|
| 1 | [标题文字](work_url) | 65.5w | 1.2w | 305 | 8.7w | 2026-07-29 21:46:58 |
```

**数字格式化规则：**
- `< 10000`：原始数字（如 `320`）
- `≥ 10000`：`x.xw` 格式（如 `1.2w`）

**标题规则：** `[标题](work_url)`；标题完整展示，严禁截断；标题为空时显示 `-`；标题中的 `|` 字符已由脚本自动转义为 `\|`，避免破坏表格列分隔

**A1-3. 翻页提示（⚠️ 紧接在 A1-2 之后，不可省略，每次必须输出）**

- 若 `has_next` 为 true：
> 📄 当前第 **{page}** 页。回复「下一页」继续查看。

- 若 `has_next` 为 false（当前页不足 size 条或为空，已是最后一页）：
> 📄 当前第 **{page}** 页，已无更多数据。

**⚠️ A1-1~A1-3 缺一不可，必须在同一轮输出中连续完成。**

**A1-4. 附加价值提示（可选，用于用户没有明确诉求时引导）**

若用户在做账号对标/选题研究，可补充输出：

> 💡 该账号作品平均播放 {avg_play}、平均点赞 {avg_like}，近 7 天发布 {recent_count} 条。需要我进一步分析评论区口碑或下载高赞视频吗？

##### 情况 A2：articles 数量 = 0（无匹配结果）

> 😔 抱歉，未查询到该账号的作品数据。
> 💡 建议尝试：核对账号 id 是否正确（kwaiId / threeXId）、确认该账号是否为快手账号、或通过账号名称重新搜索（kuaishou-account-search skill）。

**⚠️ 输出 A2 后结束本轮展示。**

---

### 场景 B：查询单条作品详情（queryWorkDetail）

#### Step 1：调用详情查询脚本

```bash
python3 ~/.workbuddy/skills/kuaishou-account-works/scripts/search_ks_detail.py "<photoId>"
```

**参数说明：**

| 参数 | 必填 | 含义 |
|------|------|------|
| `photo_id` | 是 | 作品 ID（photoId，列表接口返回的 `work_id` 加密 ID） |

> 💡 **photoId 来源**：关键词搜索（kuaishou-keyword-search 的 `work_id` 字段）或账号作品列表（本 skill 场景 A 的 `work_id` 字段）的输出直接可用。若用户给的是作品分享链接，提取链接中的 photoId 后再调用；无法提取时提示用户直接提供作品 ID。

#### Step 2：展示作品详情

> 📊 作品「**{title}**」详情如下：

```markdown
| 项目 | 数据 |
|------|------|
| 作品标题 | [标题文字](work_url) |
| 作者 | 人民日报（粉丝 6973.9w） |
| 播放数 | 111.0w |
| 点赞数 | 3.1w |
| 评论数 | 79 |
| 收藏数 | 35 |
| 分享数 | 569 |
| 转发数 | 0 |
| 视频时长 | 74.0 秒 |
| 发布时间 | 2026-07-29 16:33:15 |
| 作品类型 | 1（视频） |
```

**数字格式化规则：**
- `< 10000`：原始数字（如 `320`）
- `≥ 10000`：`x.xw` 格式（如 `1.2w`）
- **时长**：毫秒转秒显示，保留 1 位小数（如 `73948ms` → `74.0 秒`）

#### Step 3：后续引导（可选）

> 💡 需要我进一步分析这条作品的评论区口碑（kuaishou-comment）或下载视频吗？

#### Step 4：无结果情况

> 😔 抱歉，未查询到该作品详情。
> 💡 建议尝试：核对作品 ID 是否正确（photoId 为列表接口返回的加密 ID），或确认该作品是否仍可见。