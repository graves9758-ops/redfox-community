# 核心技能逻辑

> 本文件为 douyin-works-crawler 技能的完整执行逻辑参考，SKILL.md 通过引用本文件获取详细规则。

---

## 1. 数据来源

**唯一数据源：红狐数据API**

### 1.1 查询接口

| 配置项 | 值 |
|--------|-----|
| 接口地址 | `POST https://redfox.hk/story/api/dyData/queryUserWithWorks` |
| 认证 | 请求头 `X-API-KEY`（环境变量 `REDFOX_API_KEY`，格式 `ak_xxx`） |
| 积分 | 是（resourceId: `/story/api/dyData/queryUserWithWorks`） |

**请求参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `accountId` | String | 否* | 抖音号/uid（支持 unique_id、short_id、uid 任一匹配） |
| `accountName` | String | 否* | 作者/账号名 |
| `source` | String | 否 | 调用来源（默认：抖音作品抓取-GitHub） |

> *accountId和accountName至少传一个

> **查询精准度提醒：** 抖音昵称不唯一，使用accountName可能返回首个模糊匹配账号。若需精准查询，建议使用accountId（抖音号）。

**响应字段：**

- 账号级：nickname / accountId / uniqueId / uid / secUid / province / city / ipLocation / followerCount / awemeCount / totalFavorited / redfoxIndex
- 作品级（workList，近期作品数据，最多50条，按发布时间倒序）：title / likeCount / commentCount / shareCount / interactiveCount / publishTime / url

**数据范围说明：**

- API返回的 `workList` 为**近期作品数据，最多50条**，按发布时间倒序排列
- 实际返回数量取决于账号发布频率，通常为 1~50 条
- `awemeCount` 字段为账号历史作品**总数**，workList中的数量可能小于该值
- 若账号近期无作品或暂无数据，workList 为空列表


## 2. 查询未命中处理

当查询未找到目标账号时，**严禁联网搜索**，按以下流程处理：

1. **匹配到错误账号** → 提示："昵称查询返回的是「[实际匹配的昵称]」，非您要找的账号。请提供目标账号的**抖音号**进行精准查询。"
2. **未查询到账号** → 输出提示信息：

```
未查询到当前账号的相关信息，请检查输入的抖音号或昵称是否正确。
建议使用抖音号进行精准查询，或稍后再试。
```

### 降级策略

API调用失败（如积分不足、网络异常）时明确告知用户错误原因，**严禁联网搜索、严禁从第三方渠道估算或补充API未返回的字段**。

---

## 3. 输出模板

**使用说明：** 严格按模板输出，不可省略章节。数据来源于API，如实展示。

**数字格式规范：** ≥1万用 `w`（如 3.2w），≥1亿用 `亿`（如 1.5亿），<1万用千分位逗号（如 8,642）。

**链接列格式：** 有url时显示 `[链接](url)`，无url时显示 `-`。

**昵称链接格式：** 昵称字段使用 `[nickname](https://www.douyin.com/user/{secUid})` 格式，secUid 为空时显示纯文本。

```markdown
## 🎬 [nickname] - 抖音作品数据

### 账号基础信息

| 昵称 | 抖音号 | UID | 地域 | 粉丝数 | 获赞 | 作品总数 | 红狐指数 |
|------|--------|-----|------|--------|------|---------|---------|
| [nickname](https://www.douyin.com/user/[secUid]) | [accountId] | [uid] | [province·city] | [followerCount] | [totalFavorited] | [awemeCount] | [redfoxIndex] |

---

### 近期作品（共[N]条）

| # | 发布时间 | 标题 | 点赞 | 评论 | 分享 | 互动 | 链接 |
|---|---------|------|------|------|------|------|------|
| 1 | [publishTime] | [title] | [likeCount] | [commentCount] | [shareCount] | [interactiveCount] | [链接](url) / - |

> 作品列表为近期作品数据，最多50条（按发布时间倒序），账号历史作品总数为 [awemeCount] 条。

---

### 数据亮点

#### 互动量TOP3

🥇 **[title]**（互动[interactiveCount]）
> [根据账号数据、作品内容、内容定位等总结该作品值得学习点]

🥈 **[title]**（互动[interactiveCount]）
> [根据账号数据、作品内容、内容定位等总结该作品值得学习点]

🥉 **[title]**（互动[interactiveCount]）
> [根据账号数据、作品内容、内容定位等总结该作品值得学习点]


#### 账号特征分析

- **更新频率：** [基于近期作品发布间隔分析]
- **内容方向：** [基于作品标题关键词归纳内容赛道]
- **互动表现：** [基于互动数据整体趋势分析]
- **爆款特征：** [基于TOP3作品共性总结]

---

### 数据说明

- **数据范围：** 近期作品数据，最多50条，按发布时间倒序
- **作品链接：** 接口返回url字段，提供作品直达链接；url为空时显示"-"
- **数字格式：** ≥1万显示为x.xw（如3.2w），≥1亿显示为x.x亿，<1万用千分位逗号
- **数据来源：** 红狐数据API

*爬取时间：[YYYY-MM-DD HH:mm]*
> 💼 另外红狐配套全量数据库可提供完整详实数据，如需了解采购方案，可前往红狐hub[企业服务](https://redfox.hk/dashboard/enterprise)对接咨询
```

---

## 4. 脚本调用

> ⚠️ **单次调用原则：** 每次查询仅执行一次脚本调用，使用默认的 `markdown` 输出即可获得完整格式化报告，**禁止重复调用（如先json再markdown）以避免浪费API积分**。

**查询账号作品：**
```bash
python3 scripts/douyin_works_fetcher.py --account "抖音名称或抖音号"
```


**参数说明：**

| 参数 | 说明 |
|------|------|
| `--account` | 抖音昵称或抖音号（自动识别：含中文→昵称，非中文→抖音号） |
| `--output` | 输出格式：`markdown`（默认）/ `json` |

**自动识别逻辑：**
- 输入含中文 → 使用 `accountName` 参数查询（昵称模糊匹配）
- 输入非中文 → 使用 `accountId` 参数查询（抖音号精准匹配）

---

## 5. 注意事项

- 🔌 **唯一数据源：** 所有数据仅从红狐API获取，不使用第三方渠道补充或估算
- 📊 **数据范围：** 近期作品数据，最多50条，非账号全部历史作品
- 🔢 **数字格式：** ≥1万显示为 `x.xw`（如3.2w），≥1亿显示为 `x.x亿`，<1万用千分位逗号（如8,642）
- 🔗 **作品链接：** 接口返回url字段，表格中显示为 `[链接](url)`，无url时显示 `-`
- ❌ **未查询到账号：** API返回空数据时，输出提示信息引导用户使用抖音号精准查询，**严禁联网搜索、严禁生成无依据报告**
- ❌ **昵称匹配到错误账号：** 提示用户当前匹配结果非目标账号，引导提供抖音号重新查询，**严禁联网搜索**
- ✅ **如实输出：** 作品数量如实展示