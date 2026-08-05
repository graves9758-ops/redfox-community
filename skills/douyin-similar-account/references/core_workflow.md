# 抖音相似账号推荐 - 核心工作流程

## 操作步骤

### 步骤1：接收用户输入，解析参数

**输入方式：抖音账号昵称或抖音号**
- 用户输入示例："帮我查'一乐店长'的相似账号"或"查抖音号geng970616的相似账号"
- 参数：account_id（自动识别昵称和抖音号）

### 步骤2：调用脚本查询对标账号

```
# 按抖音号或昵称查询（自动识别）
python scripts/douyin_similar_account.py --account_id "一乐店长"
python scripts/douyin_similar_account.py --account_id "geng970616"
```

**查询流程：** 一步调用 `/dyUser/querySimilarAccounts` 接口：
- 含中文输入 → 使用 `accountName` 参数
- 非中文输入 → 使用 `accountId` 参数
- 接口一次性返回 currentAccount + benchmarkAccounts + topAccounts

API接口：POST https://redfox.hk/story/api/dyUser/querySimilarAccounts

### 步骤3：按标准模版输出结果

> **强制约束：脚本输出的完整文本即为最终结果，AI必须原样呈现，禁止任何形式的摘要、改写、增减、重组或二次加工。不得在脚本输出前后添加任何额外的总结、解读或评论。**

**输出顺序**：
1. 当前账号基本信息+红狐指数+近期作品
2. 开场白（只显示有数据的组）
3. 对标账号表格（有数据才展示，本账号置首行）
4. 头部账号表格（有数据才展示）
5. 深度分析：共通点 + 差异分析 + 优化建议（有数据才展示）
6. 数据说明：数据更新时间 + 红狐指数说明

**输出格式示例**：

```
**查询账号基本信息**

- 账号名称：[一乐店长](https://www.douyin.com/user/83267142382)
- 抖音号：geng970616
- 账号ID（uid）：83267142382
- 简介：娱乐主播日常全随机 ...
- 性别：男
- 地区：河南南阳
- IP属地：北京
- 粉丝数：373.9w
- 总获赞数：1.2亿
- 作品总数：1238
- 红狐指数：843.2
- 近7天发布数：5
- 近7天互动量：56.6w
- 最近作品发布：2026-06-03 11:01:46

**近期作品**

| 作品标题 | 点赞数 | 评论数 | 分享数 | 总互动数 | 发布时间 |
| --- | --- | --- | --- | --- | --- |
| [标题](作品链接) | 30w | 1.5w | 8000 | 33.3w | 2026-05-20 12:00:00 |

✨ 为你匹配到【对标账号（5个）】和【头部账号（5个）】的2组推荐，可按需参考：

👉【对标账号（6个）】（红狐指数向上最近的账号，可直接复制玩法）

| 账号名称 | 粉丝数 | 总获赞 | 近7天互动 | 红狐指数 | 指数差距 | 推荐理由 |
| --- | --- | --- | --- | --- | --- | --- |
| **[一乐店长](账号链接)** | 373.9w | 1.2亿 | 56.6w | 843.2 | 本账号 | 「**本账号**」 |
| [老赫晨](账号链接) | 404.7w | 2976.7w | 23.5w | 843.6 | +0.4 | 持续更新（近7天1条），短视频/中等深度<br>粉丝404.7w，总获赞2976.7w<br>红狐指数843.6，高出你0.4点 |

👉【头部账号（5个）】（同分类红狐指数倒序前5，模式成熟可追赶）

| 账号名称 | 粉丝数 | 总获赞 | 近7天互动 | 红狐指数 | 指数差距 | 推荐理由 |
| --- | --- | --- | --- | --- | --- | --- |
| [陈伯(全能王)](账号链接) | 1634.2w | 1597.8w | 72.3w | 983.9 | +140.7 | 持续更新（近7天3条），短视频/中等深度<br>粉丝1634.2w，总获赞1597.8w<br>红狐指数983.9，高出你140.7点 |

**深度分析**

📌 **共通点**
- 更新节奏：同赛道账号平均近7天6条，保持稳定更新
- 粉丝量级：相似账号平均粉丝659.8w，处于同一发展阶段
- 红狐指数：相似账号平均891.8

📊 **差异分析**
- 红狐指数差距：对标账号平均843.7，比你高0.5点
- 头部差距：头部标杆最高红狐指数983.9，比你高140.7点
- 更新节奏差异：部分对标账号日更（近7天18条），高频更新是流量基础

💡 **优化建议**
1. **提升更新频率**：互动量最高的对标账号近7天发布7条，建议保持稳定更新节奏

*数据更新时间：2026-06-02 01:58:32*
*红狐指数：每周更新，若统计周期内账号未发布作品，红狐指数可能为0。*
```



**无对标/头部数据情况**（账号已找到但无对标推荐）：
```
当前未查询到相关对标账号数据。可能原因：1) 抖音号或名称输入有误；2) 暂无相关对标数据。
建议：确认抖音号/名称是否正确后重新查询。
```

**数值格式化**：< 10000 直接展示原值，>= 10000 格式化为 "X.Xw"，>= 100000000 格式化为 "X.X亿"

**推荐理由**：严格参考下方「推荐理由生成维度」章节的8级维度标准与内容进行输出，不得自行扩展解读或增加额外维度

### 步骤4：输出结果

脚本直接输出格式化结果，AI必须将脚本输出原样完整展示，不得摘要、改写、增减、重组或添加额外评论。

## API响应字段映射

接口 `/dyUser/querySimilarAccounts` 返回的抖音专用字段与输出内容的对应关系：

### currentAccount（当前账号）

| API字段 | 类型 | 输出用途 |
|---------|------|---------|
| nickname | String | 账号名称 |
| accountId | String | 抖音号，用于基本信息 |
| uid | String | 账号标识，用于基本信息和构造主页链接 |
| avatarUrl | String | 头像链接 |
| signature | String | 账号简介 |
| gender | String | 性别 |
| age | Integer | 年龄 |
| province / city | String | 地区 |
| ipLocation | String | IP属地 |
| followerCount | Integer | 粉丝数 |
| awemeCount | Integer | 作品总数 |
| totalFavorited | Long | 总获赞数 |
| crawlTime | String | 数据更新时间 |
| redfoxIndex | Double | 红狐指数 |
| works | List | 近7天作品列表 |

### benchmarkAccounts / topAccounts（对标/头部账号）

| API字段 | 类型 | 输出用途 |
|---------|------|---------|
| nickname | String | 账号名称，用于表格和标题 |
| url | String | 账号链接，用于Markdown超链接 |
| followerCount | Integer | 粉丝数，用于基本信息和表格 |
| uid | String | 账号标识 |
| awemeCount | Integer | 作品总数 |
| totalFavorited | Long | 总获赞数，用于基本信息和推荐理由 |
| awemeCountSeven | Integer | 近7天发布数，用于更新节奏分析 |
| interactiveCountSeven | Integer | 近7天互动量，用于表格和互动分析 |
| interactiveCountThirty | Integer | 近30天互动数 |
| lastAwemeCreateTime | String | 最近作品发布时间 |
| redfoxIndex | Double | 红狐指数，用于表格和指数对比 |
| works[].title | String | 作品标题，用于作品表格和主题分析 |
| works[].playCount | Integer | 播放量，用于作品表格和互动率/点赞率计算 |
| works[].diggCount | Integer | 点赞数，用于点赞率计算 |
| works[].commentCount | Integer | 评论数，用于作品表格 |
| works[].shareCount | Integer | 分享数，用于作品表格 |
| works[].interactiveCount | Integer | 总互动数，用于互动率计算 |
| works[].createTime | String | 发布时间，用于时段分析 |
| works[].workUrl | String | 作品链接，用于Markdown超链接 |
| works[].coverUrl | String | 封面链接，用于内容策略分析 |
| works[].desc | String | 作品正文，用于主题分析 |

## 对标匹配规则

对标匹配由API服务端完成，返回规则如下：

### 对标账号（benchmarkAccounts）
- 匹配逻辑：同分类中红狐指数向上最近的5个账号
- 特点：指数接近，运营阶段相似，玩法可直接复制

### 头部账号（topAccounts）
- 匹配逻辑：同分类中红狐指数倒序前5
- 特点：同赛道顶尖账号，运营模式成熟，适合追赶学习

## 输出格式规范

1. 查询账号基本信息和所有表格中的【账号名称】需添加跳转链接，统一使用 `secUid` 构造 `https://www.douyin.com/user/{secUid}`；若 `secUid` 为空，则回退使用 `uid` 构造 `https://www.douyin.com/user/{uid}`
2. 表格中【推荐理由】需分多行展示（用 `<br>` 换行），且「」内的内容需加粗
3. 深度分析包含三部分：共通点、差异分析、优化建议，按需输出
4. 对标/头部账号表格列顺序：账号名称 | 粉丝数 | 总获赞 | 近7天互动 | 红狐指数 | 指数差距 | 推荐理由
5. 对标账号表格第一行为本账号（加粗显示），指数差距列显示"本账号"，推荐理由为「**本账号**」，总数=对标账号数+1
6. 指数差距列：本账号显示"本账号"，其他账号显示"+X.X"（高出查询账号）或"-X.X"（低于查询账号），无数据时显示"-"
7. 对标账号和头部账号数量如实展示，不人为补全
8. 末尾统一输出数据说明：
   - `*数据更新时间：{crawlTime}*`（取currentAccount.crawlTime）
   - `*红狐指数：每周更新，若统计周期内账号未发布作品，红狐指数可能为0。*`

## API接口详情

### 接口：查询抖音对标账号

**接口地址：** `POST https://redfox.hk/story/api/dyUser/querySimilarAccounts`

**认证方式：** 请求头 `X-API-KEY`（ak_xxx格式）

**积分消费：** resourceId: `/story/api/dyUser/querySimilarAccounts`

**请求参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| accountId | String | 条件必填 | 抖音账号ID（支持unique_id、short_id、uid任一匹配），与accountName二选一 |
| accountName | String | 条件必填 | 抖音账号名称，根据名称查询并匹配对标账号，与accountId二选一 |
| source | String | 否 | 来源标识，用于调用次数限制 |

> **两种查询模式：**
> 1. **传入accountId**：通过账号ID查询该账号信息并匹配对标账号
> 2. **传入accountName**：通过账号名称查询该账号信息并匹配对标账号

**请求示例（通过账号ID查询）：**
```json
{
  "accountId": "dy_example123",
  "source": "coze"
}
```

**请求示例（通过账号名称查询）：**
```json
{
  "accountName": "一乐店长",
  "source": "coze"
}
```

**响应字段说明：**

| 字段路径 | 类型 | 说明 |
|---------|------|------|
| data.currentAccount | DyUserInfoVO | 当前账号信息 |
| data.benchmarkAccounts | List\<DySimilarAccountDetailVO\> | 对标账号列表（红狐指数向上最近的5个） |
| data.topAccounts | List\<DySimilarAccountDetailVO\> | 头部账号列表（同分类红狐指数倒序前5） |

**当前账号信息（DyUserInfoVO）：**

| 字段 | 类型 | 说明 |
|------|------|------|
| nickname | String | 账号名 |
| avatarUrl | String | 头像链接 |
| signature | String | 账号简介 |
| accountId | String | 账号平台展示id（unique_id优先，备选short_id） |
| uid | String | uid |
| secUid | String | 加密用户标识，用于构造抖音主页链接（统一使用secUid，secUid为空时回退uid） |
| gender | String | 性别 |
| age | Integer | 年龄 |
| country | String | 地域-国家 |
| province | String | 地域-省 |
| city | String | 地域-市 |
| ipLocation | String | IP属地-省 |
| followerCount | Integer | 平台粉丝数 |
| awemeCount | Integer | 总发布作品数 |
| totalFavorited | Long | 总点赞数 |
| crawlTime | String | 账号更新时间 |
| redfoxIndex | Double | 红狐指数 |
| works | List\<DyWorkVO\> | 近7天作品列表 |
| similarAccounts | List\<DySimilarAccountVO\> | 相似账号列表 |

**对标/头部账号详情（DySimilarAccountDetailVO）：**

| 字段 | 类型 | 说明 |
|------|------|------|
| nickname | String | 账号名 |
| url | String | 账号链接 |
| followerCount | Integer | 粉丝数 |
| uid | String | 账号标识（uid） |
| secUid | String | 加密用户标识，用于构造抖音主页链接（统一使用secUid，secUid为空时回退uid） |
| awemeCount | Integer | 作品总数 |
| totalFavorited | Long | 总获赞数 |
| awemeCountSeven | Integer | 近7天发作品数 |
| interactiveCountSeven | Integer | 近7天作品互动量 |
| interactiveCountThirty | Integer | 近30天互动数 |
| lastAwemeCreateTime | String | 最近作品发布时间 |
| redfoxIndex | Double | 红狐指数 |
| works | List\<DyWorkVO\> | 近7天作品列表 |

**作品信息（DyWorkVO）：**

| 字段 | 类型 | 说明 |
|------|------|------|
| awemeId | String | 作品ID |
| title | String | 作品标题（取正文首行） |
| coverUrl | String | 作品封面链接 |
| desc | String | 作品正文 |
| createTime | String | 发布时间 |
| diggCount | Integer | 点赞数 |
| commentCount | Integer | 评论数 |
| shareCount | Integer | 分享数 |
| playCount | Integer | 播放数 |
| interactiveCount | Integer | 总互动数 |
| workUrl | String | 作品链接 |

**错误码：**

| code | 说明 |
|------|------|
| 200 / 2000 | 成功（实际返回2000） |
| 4001 | 参数错误/未找到账号 |
| 500 | 业务异常，具体原因见msg字段 |

**常见业务错误：**

| msg | 场景 |
|-----|------|
| 今日调用次数已达上限，请明日再试 | source标识对应的每日调用次数已达上限 |

## 核心模块说明

| 模块 | 职责 |
| --- | --- |
| `query_similar_accounts()` | 调用 /dyUser/querySimilarAccounts 接口，支持accountId和accountName两种查询方式，返回currentAccount+benchmarkAccounts+topAccounts |
| `format_output()` | 格式化完整文本输出，包含当前账号信息、对标表格、头部表格、深度分析 |
| `generate_recommendation_reason()` | 基于多维度生成推荐理由，涵盖红狐指数对比、爆品引用、更新节奏、互动率等 |
| `generate_analysis_summary()` | 基于共通点、差异分析、优化建议三维输出深度分析 |

## 推荐理由生成维度

推荐理由由多个维度按优先级组合输出，数据稀疏时自动降级补充：

| 优先级 | 维度 | 数据来源 | 示例 |
| --- | --- | --- | --- |
| 1 | 内容主题聚焦 | works + effective_avg | 近7天3条爆品，聚焦于**美食教程**/**家常菜** |
| 2 | 爆品标题引用 | works中最高播放作品 | 爆品「**红烧肉的秘诀…**」达均播2.4倍 |
| 3 | 与查询账号播放倍数对比 | 查询账号 + 对标账号均播 | 均播约为你的3.2倍，模式成熟可追赶 |
| 4 | 更新节奏+近7天发布量+内容策略 | awemeCountSeven + works | 日更高产（近7天10条），短视频/深度解析 |
| 5 | 互动率+点赞率 | works中互动/点赞/播放数据 | 互动率8.5%，点赞率5.2%，用户粘性强 |
| 6 | 粉丝量级+总获赞+红狐指数对比 | followerCount + totalFavorited + redfoxIndex | 粉丝5w，总获赞200w，红狐指数843.6，高出你0.4点 |
| 7 | 数据稀疏补充 | 多维度兜底 | 内容方向：美食教程/家常菜，近7天发布5条 |
| 8 | 结论兜底 | 赛道+均播+7天互动 | 同赛道账号，均播5.2w，可参考运营策略 |

**关键机制**：
- `effective_avg` 计算：从 works 中计算 `effective_avg = max(works播放均值, ...)` 作为爆品判断基准
- 互动率超过100%判定为数据异常，不输出
- 点赞率分级描述：>=5%用户粘性极强，>=3%用户粘性强，1%-3%粘性尚可
- 播放倍数对比：>=3倍模式成熟可追赶，>=1.5倍策略可参考，0.7-1.3倍玩法可直接复制
- 红狐指数对比：显示对标账号与查询账号的指数差距
- 各维度间自动去重，避免同一条信息重复输出

**输出约束**：
- 推荐理由必须严格按上述8级维度标准生成，仅使用对应数据来源和描述模板
- 禁止自行扩展解读、增加额外维度或改写标准话术
- 脚本输出的推荐理由即为最终结果，AI展示时直接呈现，不做二次加工

**红狐指数为0时的推荐理由**：
当查询账号的红狐指数为0时，推荐理由走「学习点总结」模式（`_generate_learning_point_reason`），基于账号数据、内容数据、更新节奏、整体内容策略定位等总结该账号的值得学习点，输出格式不同于标准8级维度：

| 维度 | 数据来源 | 示例 |
| --- | --- | --- |
| 同赛道+爆品/内容聚焦+路径可复制 | works互动数据 + content_themes | 同赛道近7天2篇爆文，全聚焦于历史人物/历史事件，路径可复制 |
| 更新节奏+内容策略定位 | awemeCountSeven + works | 日更高产（近7天7条），短视频/深度解析 |
| 互动/点赞数据亮点 | works中互动/点赞/播放数据 | 互动率8.5% |
| 粉丝量级+总获赞 | followerCount + totalFavorited | 粉丝5w，总获赞200w |
| 近7天互动 | interactiveCountSeven | 近7天互动284.0w |
| 数据稀疏补充 | 多维度兜底 | 内容方向：美食教程/家常菜，近7天发布5条 |
| 结论兜底 | 赛道+粉丝+7天互动 | 同赛道对标账号，运营策略可参考 |

## 订阅服务

查询结果末尾自动输出订阅服务提示，文案如下：
```
是否订阅「{查询账号昵称}」的相似账号最新信息推送？

1. 每日下午19点推送最新数据。可自行选择推送频率和时间~
2. 暂不需要
> 💼 另外红狐配套全量数据库可提供完整详实数据，如需了解采购方案，可前往红狐hub[企业服务](https://redfox.hk/dashboard/enterprise)对接咨询
```
