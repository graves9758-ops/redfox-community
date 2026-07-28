# X(Twitter)作品搜索 - 执行工作流

## Step 0: 鉴权前置检查

1. 检查用户是否已配置 API Key（环境变量 `REDFOX_API_KEY` 或 `~/.openclaw/openclaw.json` 中配置）
2. 未配置 → 引导用户前往 [红狐hub](https://redfox.hk/settings/api-keys?source=github) 获取并配置：
   ```
   ⚠️ 未检测到 API Key，请先完成鉴权：
   1. 前往 https://redfox.hk/settings/api-keys?source=github 获取 API Key
   2. 设置环境变量 REDFOX_API_KEY 或在 ~/.openclaw/openclaw.json 中配置
   3. 配置完成后重新发起搜索
   ```
3. 已配置 → 进入 Step 1

---

## Step 1: 解析用户输入

### 1.1 提取搜索参数

从用户消息中提取以下信息：

| 字段 | 提取规则 | 默认值 |
|------|---------|--------|
| keyword | 用户消息中的搜索关键词，去除非关键词的废话 | 必需，缺失则追问 |
| searchType | 根据语义识别：热门/Top → `"Top"`，最新/Latest → `"Latest"`，图片/视频/媒体 → `"Media"`，用户/找人/账号 → `"People"`，列表 → `"Lists"` | `"Top"` |
| cursor | 用户提到"下一页""继续""还有吗"时，使用上次返回的 nextCursor | `null`（首次搜索） |

### 1.2 searchType 语义映射表

| 用户表述（部分） | 映射值 |
|---------|--------|
| 热门、热度、最火、Top | `"Top"` |
| 最新、最近、Latest、新发布 | `"Latest"` |
| 图片、视频、媒体、Media、照片 | `"Media"` |
| 用户、账号、找人、People、博主 | `"People"` |
| 列表、Lists | `"Lists"` |

### 1.3 输入验证

1. keyword 为空或无实际搜索关键词 → 提示用户：
   ```
   请告诉我你想搜索什么关键词？例如："搜一下X上关于'AI'的推文"
   ```
2. searchType 不在上述 5 种值中 → 默认使用 `"Top"`
3. 用户未指定 searchType → 默认使用 `"Top"`

---

## Step 2: 执行数据采集

> ⛔ 所有接口调用必须在请求体中携带 `source` 字段，值为 `"X(Twitter)作品搜索-GitHub"`

### 2.1 构建请求

**请求头**：
```
Content-Type: application/json
REDFOX_API_KEY: {用户配置的API Key}
```

**请求体**：
```json
{
  "keyword": "{用户输入的关键词}",
  "searchType": "{Top|Latest|Media|People|Lists}",
  "cursor": "{分页游标，首次为null}",
  "source": "X(Twitter)作品搜索-GitHub"
}
```

### 2.2 发送请求

- **接口地址**：`POST https://redfox.hk/story/api/x/search`
- **超时设置**：30 秒
- **重试策略**：失败时重试 1 次

### 2.3 响应处理

检查 `code` 字段：
- `code === 2000` → 请求成功，进入 Step 3
- `code !== 2000` → 请求失败，输出 `msg` 中的错误信息给用户
- 网络错误/超时 → 提示："搜索请求超时，请稍后再试"

---

## Step 3: 数据结构化

### 3.1 字段映射表

| 原始字段 | 输出字段 | 格式转换 |
|---------|---------|---------|
| tweetId | 推文ID | 保持原样 |
| text | 推文正文 | 截取前 80 字，超出加"..." |
| text | 推文链接 | 从 text 中正则提取 `https://t.co/...` 链接，无则显示 "—" |
| createdAt | 发布时间 | 保持原样（如 "Fri May 22 07:45:42 +0000 2026"） |
| language | 语言 | 保持原样 |
| likeCount | 点赞 | 数字格式化（见 3.2） |
| retweetCount | 转发 | 数字格式化 |
| replyCount | 回复 | 数字格式化 |
| quoteCount | 引用 | 数字格式化 |
| bookmarkCount | 收藏 | 数字格式化 |
| viewCount | 浏览 | 数字格式化（原始为字符串，需转数字后格式化） |
| user.displayName | 作者昵称 | 保持原样 |
| user.username | 用户名 | 格式化为 `@username` |
| user.followers | 粉丝数 | 数字格式化 |
| user.verified | 认证 | `true` → "✅"，`false` → 不显示 |
| user.location | 所在地 | 保持原样，空则不显示 |
| medias[].type | 媒体类型 | `video` → "📹 视频"，`photo` → "🖼️ 图片" |
| medias[].coverUrl | 封面图 | 保持原样（可点击链接） |
| medias[].durationMillis | 视频时长 | 毫秒 → 分:秒格式（如 43282ms → "0:43"），图片时为 null 不显示 |
| medias[].variants | 视频地址 | 取最高码率 mp4 的 url 作为视频链接 |

### 3.2 数字格式化规则

```
function formatNumber(num):
  if num == null → "—"
  num = parseInt(num)  // viewCount 可能是字符串
  if num < 10000 → 原数（如 8523）
  if num < 100000000 → num/10000 保留1位小数 + "w"（如 1.5w、92.5w）
  if num >= 100000000 → num/100000000 保留1位小数 + "亿"（如 2.3亿）
```

### 3.3 推文排序

保持接口返回的原始顺序（已按 searchType 排序），不做二次排序。

---

## Step 4: 输出结果

### 4.1 输出格式

**表格前先输出数据说明**：

```
> 💡 数据说明：
> - ✅ 表示该账号已通过 X 平台认证
> - 作者列和推文链接列均为 X 平台外链，境内网络可能无法直接访问
```

所有推文以 Markdown 表格形式展示，每页 20 条，包含以下列：

| # | 推文内容 | 作者 | 推文链接 | 👍 点赞 | 🔁 转发 | 💬 回复 | 👁️ 浏览 | 时间 |
|---|---------|------|---------|---------|---------|---------|---------|------|
| {序号} | {正文前80字}... | [{作者昵称}](https://x.com/{username}) {✅} | [链接]({tcoUrl}) | {likeCount} | {retweetCount} | {replyCount} | {viewCount} | {发布时间短格式} |

**列说明**：
- 推文内容：截取 text 前 80 字，超出加 "..."；含媒体时末尾追加 📹 或 🖼️ 标记
- 作者：显示为可点击的 X 主页链接，认证用户追加 ✅
- 推文链接：从 text 中提取第一个 `https://t.co/...` 短链接，以 Markdown 链接渲染，无则显示 "—"
- 浏览量：`null` 时显示 "—"
- 时间：简化为 `YYYY-MM-DD` 格式（仅日期）
- 数字按 3.2 规则格式化

### 4.2 翻页处理

- 搜索结果返回后，检查 `data.tweets` 数组长度
- **长度为 20** → 在结果末尾展示翻页提示：
  ```
  📄 还有更多推文。回复「下一页」继续查看。
  ```
- **长度 < 20** → 不展示翻页提示，表示已是最后一页
- 翻页时使用 `data.nextCursor` 作为 `cursor` 参数重新请求

### 4.3 未找到数据时的降级逻辑

1. `data.tweets` 为空数组 → 告知用户：
   ```
   未找到与"{keyword}"相关的推文。建议：
   - 尝试更通用的关键词
   - 减少限定词
   - 更换搜索类型（如从"{currentType}"改为其他类型）
   ```
2. 接口返回错误 → 透传 `msg` 内容给用户
3. 网络超时 → 提示"搜索请求超时，请稍候再试"

### 4.4 搜索类型中文显示

在结果开头标注当前使用的搜索类型：
```
🔍 搜索关键词：{keyword}  |  类型：{searchType中文}
```

---

## 接口参考

### 接口地址

| 接口名称 | 请求方式 | 接口地址 |
|---------|---------|----------|
| X(Twitter)搜索 | POST | https://redfox.hk/story/api/x/search |

### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|---------|------|------|------|
| keyword | string | 是 | 搜索关键字 |
| searchType | string | 否 | 搜索类型，默认 Top。可选：Top（热门）、Latest（最新）、Media（媒体）、People（用户）、Lists（列表） |
| cursor | string | 否 | 分页游标，首次不传，后续从上一次返回结果中获取 |
| source | string | 是 | 接口来源标识，固定值：`"X(Twitter)作品搜索-GitHub"` |

### 响应结构

| 字段名 | 类型 | 说明 |
|---------|------|------|
| code | integer | 响应状态码，2000 表示成功 |
| msg | string | 响应消息 |
| data.nextCursor | string | 下一页游标，用于翻页查询 |
| data.prevCursor | string | 上一页游标 |
| data.tweets | array | 推文列表 |
| data.tweets[].tweetId | string | 推文ID |
| data.tweets[].text | string | 推文正文内容 |
| data.tweets[].createdAt | string | 推文发布时间 |
| data.tweets[].language | string | 推文语言 |
| data.tweets[].likeCount | integer | 点赞数 |
| data.tweets[].retweetCount | integer | 转推数 |
| data.tweets[].replyCount | integer | 回复数 |
| data.tweets[].quoteCount | integer | 引用推文数 |
| data.tweets[].bookmarkCount | integer | 收藏数 |
| data.tweets[].viewCount | string | 浏览量 |
| data.tweets[].username | string | 推文作者用户名 |
| data.tweets[].user.avatar | string | 用户头像URL |
| data.tweets[].user.displayName | string | 用户显示名称 |
| data.tweets[].user.followers | integer | 粉丝数 |
| data.tweets[].user.verified | boolean | 是否已认证 |
| data.tweets[].user.location | string | 用户所在地 |
| data.tweets[].medias | array | 媒体附件列表 |
| data.tweets[].medias[].type | string | 媒体类型：video 或 photo |
| data.tweets[].medias[].coverUrl | string | 媒体封面图URL |
| data.tweets[].medias[].durationMillis | integer | 视频时长（毫秒），图片时为 null |
| data.tweets[].medias[].variants | array | 视频清晰度列表（含播放地址），图片时为空 |

### 数据范围

| 数据类型 | 获取范围 | 说明 |
|---------|---------|------|
| 推文列表 | 每次最多 20 条 | 通过翻页获取更多 |
| 搜索类型 | Top / Latest / Media / People / Lists | 默认 Top 热门排序 |

### 降级处理

当未找到目标数据时：
1. 提示用户"未找到与'{关键词}'相关的推文，请尝试更换关键词或调整搜索类型"
2. 建议用户尝试更通用的关键词、减少限定词或改用其他搜索类型
