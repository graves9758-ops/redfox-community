---
name: wechat-similar-account
description: 公众号创作者对标账号匹配工具，基于3层加权匹配体系（核心基础40%+运营变现35%+数据特征25%）推荐对标账号和头部账号。当用户需要公众号账号推荐、公众号对标、起号参考、账号投放选择时使用。触发词：公众号对标、相似账号、对标推荐、起号参考、账号匹配。
---

# 公众号相似账号推荐

## 简介

公众号相似账号推荐是一款专为公众号创作者设计的智能对标匹配工具，帮助用户快速找到可参考的对标账号和可追赶的头部标杆。

通过简单的名称或ID输入，你可以：
- 📊 查询账号基本信息 + 近5篇文章数据
- 🎯 匹配同阶对标账号（可直接复制玩法）
- 🚀 推荐高阶标杆账号（模式成熟可追赶）
- 📈 基于3层加权体系生成个性化推荐理由

适用于公众号创作者、内容运营、账号投放决策等需要对标参考的场景。基于 [RedFox](https://redfox.hk/?source=github) 数据平台提供支持。

## 功能特性

### 🎯 核心功能
- **🔍 智能查询**：支持按公众号名称、公众号ID、账号分类三种方式查询
- **📊 账号诊断**：展示查询账号的基本信息、红狐指数、阅读数据及近5篇文章
- **🎯 同阶对标**：推荐阅读数最接近的同赛道账号，可直接复制运营玩法
- **🚀 高阶标杆**：推荐阅读数3-5倍的成熟账号，模式可参考追赶

### ✨ 特色亮点
- **⚖️ 3层加权匹配**：核心基础(40%) + 运营变现(35%) + 数据特征(25%)，推荐结果科学可落地
- **💡 7维度推荐理由**：涵盖爆文标题引用、发文时段规律、分享传播力、互动率等，数据稀疏时自动补充红狐指数/近7天互动等维度
- **🔄 订阅推送**：支持订阅对标账号推送，每日更新最新数据
- **📱 多输入方式**：名称/ID/分类灵活查询，组合查询更精准

## 一键安装

### 前置条件
- Python 3.x 运行环境（仅依赖标准库，无需 pip install）
- 红狐Hub API Key（前往 [RedFox 官网](https://redfox.hk/?source=github) 注册获取，新用户赠送免费积分）

### 获取 API Key
1. 访问 [红狐Hub 官网](https://redfox.hk/?source=github) 了解服务详情
2. 前往 [注册页面](https://redfox.hk/login?source=github) 注册账号
3. **新注册用户将获赠免费积分**，可立即开始使用 API 服务
4. 注册登录后，在个人中心获取 API Key，格式为 `ak_xxxxxxxx`

### 配置 API Key
`REDFOX_API_KEY` 从环境变量获取。若未设置，Agent 应主动帮用户配置：

| 系统 | 配置方式 | 验证命令 |
| --- | --- | --- |
| Windows | `[Environment]::SetEnvironmentVariable("REDFOX_API_KEY", "<值>", "User")` | `echo %REDFOX_API_KEY%` |
| macOS/Linux | `echo 'export REDFOX_API_KEY=<值>' >> ~/.zshrc && source ~/.zshrc` | `echo $REDFOX_API_KEY` |

> 配置后需重启终端生效，确保换一个 skill 也能读取到。

### 环境变量配置

| 变量名 | 必填 | 说明 |
| --- | --- | --- |
| `REDFOX_API_KEY` | 是 | 红狐Hub API 访问密钥，格式 `ak_xxxxxxxx` |

## 使用指南

### 基础使用

#### 1. 按名称查询
告诉助手你想查询的公众号名称：

> 用户：帮我查"科技前沿"的对标账号
>
> 助手：调用脚本 `python scripts/wechat_similar_accountr.py --account_name "科技前沿"`，按模板输出结果

#### 2. 按ID查询
提供公众号ID进行精准查询：

> 用户：帮我查公众号ID为gh_xxx的对标
>
> 助手：调用脚本 `python scripts/wechat_similar_accountr.py --account_id "gh_xxx"`，按模板输出结果

#### 3. 按分类查询
指定账号分类查找对标：

> 用户：推荐科技数码类的对标账号
>
> 助手：调用脚本 `python scripts/wechat_similar_accountr.py --account_type "科技数码"`，按模板输出结果

### 高级使用

#### 4. 组合查询
同时指定名称和分类，查询更精准：

```bash
python scripts/wechat_similar_accountr.py --account_name "科技前沿" --account_type "科技数码"
```

#### 5. 按分类查询注意事项
红狐数据 平台的分类体系与自然语言存在差异，`--account_type` 查询成功率较低。当用户以自然语言分类（如「风景」「情感」）查询时，应：
1. 查找该领域代表性公众号（如「风景」→「中国国家地理」，「情感」→「夜听」）
2. 使用 `--account_name "代表性名称"` 执行查询
3. 从返回结果的「账号分类」字段确认平台内部归类

### 命令速查

| 命令 | 功能 |
|------|------|
| `--account_name "名称"` | 按公众号名称查询 |
| `--account_id "ID"` | 按公众号ID查询 |
| `--account_type "分类"` | 按账号分类查询 |

### 输出流程

详细的核心工作流程（输入解析、脚本调用、输出模板、无数据处理、对标匹配规则等）请参考 [references/core_workflow.md](references/core_workflow.md)。

**输出顺序**：
1. 查询账号基本信息 + 近5篇文章
2. 开场白（只显示有数据的组）
3. 同阶对标表格（有数据才展示）
4. 高阶标杆表格（有数据才展示）
5. 分析总结（有数据才展示）
6. **订阅服务（必须输出，无论有无数据）**
7. **企业采购引导（必须输出，无论有无数据）**

## 使用场景

### 场景一：新号起号参考
**角色**：公众号新手运营

**需求**：刚创建公众号，不知道怎么定位和选题

**使用方式**：
1. 输入自己的公众号名称或分类
2. 查看同阶对标账号的内容方向和更新节奏
3. 复制对标账号的运营策略

**预期收益**：快速找到可复制的运营模式，降低起号试错成本

---

### 场景二：内容选题优化
**角色**：公众号内容运营

**需求**：内容遇到瓶颈，需要参考同赛道优秀账号的选题方向

**使用方式**：
1. 查询自己账号的对标推荐
2. 分析高阶标杆的爆文特征和内容风格
3. 调整自身选题策略

**预期收益**：突破内容瓶颈，提升文章阅读和互动数据

---

### 场景三：账号投放决策
**角色**：品牌营销经理

**需求**：选择合适的公众号进行广告投放

**使用方式**：
1. 按分类查询目标赛道的公众号
2. 对比同阶和高阶账号的数据表现
3. 评估互动率和用户画像匹配度

**预期收益**：精准选择投放账号，提高投放ROI

---

### 场景四：竞品分析
**角色**：MCN 运营人员

**需求**：了解竞品账号的运营策略和数据表现

**使用方式**：
1. 查询竞品账号的对标推荐
2. 分析同赛道账号的差异化定位
3. 发现市场空白机会

**预期收益**：掌握竞品动态，发现差异化竞争机会

## 项目架构

### 目录结构

```
wechat-similar-account/
├── scripts/
│   └── wechat_similar_accountr.py   # 核心脚本：调用API查询对标账号并格式化输出
├── references/
│   └── core_workflow.md              # 核心工作流程：操作步骤、输出模板、匹配规则
├── SKILL.md                          # 技能描述文件
└── README.md                         # 项目说明文档
```

### 技术栈

| 组件 | 说明 |
| --- | --- |
| **运行环境** | Python 3.x |
| **依赖** | Python 标准库（json、argparse、os、urllib、platform、re） |
| **数据源** | 红狐数据 API（https://redfox.hk?source=github） |
| **API 接口** | POST https://redfox.hk/story/api/gzhUser/querySimilarAccounts |

### 核心模块说明

| 模块 | 职责 |
| --- | --- |
| `query_similar_accounts()` | 调用 红狐数据 API 查询对标账号和头部账号（API返回 currentAccount + benchmarkAccounts + topAccounts） |
| `format_output()` | 格式化完整文本输出，包含查询账号信息、对标表格、分析总结 |
| `generate_recommendation_reason()` | 基于3层加权匹配体系生成推荐理由，支持7个维度的组合输出 |
| `_analyze_publish_schedule()` | 从文章 publishTime 推断固定发文时段（如"早间7点固定发文""晚间时段为主"） |
| `_extract_top_article()` | 提取最高阅读文章标题，输出"爆文「标题…」达均阅X.X倍" |
| `_calc_interaction_rate()` | 计算互动率，超过100%判定为数据异常不输出 |
| `_calc_share_rate()` | 计算分享率=分享数/阅读数，反映内容传播力 |
| `calc_seven_day_reads()` | 计算近7天阅读数（从works累加clicksCount，works为空返回0；interactiveCountSeven是互动量非阅读量，不可混用） |

### API 响应结构

API (`POST /gzhUser/querySimilarAccounts`) **返回以下字段**：
- `currentAccount`：查询账号的基本信息及近5篇文章数据（works字段）
- `benchmarkAccounts`：同阶对标账号列表
- `topAccounts`：高阶标杆账号列表

脚本直接从 `currentAccount` 获取查询账号信息和 works 数据。当 `currentAccount` 为空时（如按分类查询未命中具体账号），从 benchmarkAccounts + topAccounts 中按 accountName/accountId 匹配。

### 关键字段说明

| 字段 | 说明 |
| --- | --- |
| `articleCountSeven` | 近7天文章发布数，currentAccount可能不含此字段，此时从works数量推断 |
| `interactiveCountSeven` | 近7天**互动量**（非阅读量），不可作为阅读数使用 |
| `avgReadCount` | 平均阅读数，可能为 null，此时需从 works 中计算 effective_avg |
| `clicksCount` | 文章阅读数，最大值为 100001（10w+ 封顶值） |
| `redfoxIndex` | 红狐指数，账号综合质量评分 |
| `works` | 近期文章列表，包含 title/clicksCount/likeCount/commentCount/watchCount/interactiveCount/shareCount/publishTime/workUrl 等 |

### 推荐理由生成维度

| 优先级 | 维度 | 数据来源 | 示例 |
| --- | --- | --- | --- |
| 1 | 爆文洞察 + 内容主题聚焦 | works + effective_avg | 同赛道近7天3篇爆文，全聚焦于**亲子育儿教育**/**健康养生** |
| 2 | 爆文标题引用 | works中最高阅读文章 | 爆文「**女性最佳绝经期…**」达均阅2.4倍 |
| 3 | 更新节奏 + 内容策略 + 发文时段 | articleCountSeven + works | 日更高产，图文深度/中等深度内容，早间7点固定发文 |
| 4 | 互动率 + 分享率 | works中互动/分享/阅读数据 | 互动率3.2%，分享率5.1%，内容传播力强 |
| 5 | 近7天互动数 | interactiveCountSeven | 近7天互动49.8w，用户活跃度可参考 |
| 6 | 红狐指数阶段定位 | redfoxIndex + accountType | 红狐指数932，账号综合质量在「**文摘精选**」赛道中表现突出 |
| 7 | 数据稀疏补充 | 多维度兜底 | 内容方向：亲子育儿/健康养生，近7天发文5篇 |

**关键机制**：
- `effective_avg` = max(avgReadCount, works阅读均值)，当 avgReadCount 为 null 时仍可判断爆文
- 互动率超过100%判定为数据异常，不输出
- 各维度间自动去重，避免同一条信息重复输出

## 常见问答

### 安装相关问题

**Q1: 提示 "未找到 REDFOX_API_KEY 配置" 怎么办？**

A: 请按以下步骤配置：
1. 访问 https://redfox.hk?source=github 注册账号并获取 API Key
2. Windows 用户在 PowerShell 执行：`[Environment]::SetEnvironmentVariable("REDFOX_API_KEY", "<你的API Key>", "User")`
3. macOS/Linux 用户执行：`echo 'export REDFOX_API_KEY=<你的API Key>' >> ~/.zshrc` 然后 `source ~/.zshrc`
4. 重启终端后生效

**Q2: 需要安装额外的 Python 依赖吗？**

A: 不需要。脚本仅使用 Python 标准库（json、argparse、os、urllib、re 等），无需 pip install 任何包。

---

### 使用相关问题

**Q3: 查询不到账号数据怎么办？**

A: 请确认账号名称或ID输入是否正确。如账号为新号或近期发文较少，可能暂时无法获取完整数据，建议稍后重试。

**Q4: 支持哪些查询方式？**

A: 支持三种方式：
- 按公众号名称：`--account_name "名称"`
- 按公众号ID：`--account_id "gh_xxx"`
- 按账号分类：`--account_type "科技数码"`
- 也支持组合查询，如同时指定名称和分类

**Q5: 同阶对标和高阶标杆有什么区别？**

A: 同阶对标的阅读数与查询账号最接近，可直接复制玩法；高阶标杆的阅读数是查询账号的3-5倍，运营模式更成熟，适合追赶学习。

**Q6: 按分类查询无结果怎么办？**

A: 红狐数据 平台的分类体系与自然语言存在差异，建议使用该领域代表性公众号名称查询。例如「风景」→「中国国家地理」，「情感」→「夜听」。

---

### 故障排除

**Q7: API 请求返回 HTTP 错误怎么办？**

A: 请检查以下几点：
1. 确认 API Key 是否正确且未过期
2. 确认网络可以正常访问 https://redfox.hk/?source=github
3. 检查 API Key 是否有足够的积分余额

**Q8: 输出结果中某些字段为空或为0？**

A: 这是正常现象，说明该账号在对应数据维度上暂无数据记录。脚本会自动处理为"暂无"或"0"展示。

---

### 获取帮助

如有其他问题，可通过以下方式获取帮助：
- 📧 访问 [红狐数据 官网](https://redfox.hk/?source=github) 了解更多
