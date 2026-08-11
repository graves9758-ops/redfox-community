---
name: wechat-fastest-growing
description: 每日账号推荐速览直接对接官方最具“黑马体质”的阅读增长榜单，按日期查看公众号阅读增长率TOP榜。每个作者只展示最高阅读那篇，标题做成可点击链接，一秒直达原文。
version: 1.0.0
---

# 公众号黑马账号推荐

## 简介

公众号黑马账号推荐是一款面向内容运营与新媒体研究的**阅读增长率排行**查询工具，通过脚本拉取官方榜单数据，帮助用户快速发现近期阅读量增速快的公众号与代表作。

通过本 Skill，你可以：

- 📊 **同作者爆文 vs 最低阅读文对比**：针对同一个账号，对比其“爆文”和“最低阅读文”在选题、标题、切入点上的差异。直接告诉你可以复制的具体打法。
- 📈 **高增长账号类型分析**：分析近期高增长账号的赛道分布和共同策略，判断当下真实流量风向，并给出哪些能迁移到其他平台的建议。

适用于公众号运营找高增长对标、编辑选题复盘、研究者观察赛道热度等角色。


## 功能特性

### 🎯 核心功能

- **📊 增长率榜单**：按日期查询公众号阅读增长率排行数据（脚本输出 Markdown 表格）
- **🔗 可点击标题**：表格中标题已为原文链接，便于跳转核对
- **📌 指标说明**：榜单含「综合评分指数」等字段；公式与加权定义见 [references/core_workflow.md](references/core_workflow.md)
- **📈 增长分析**：基于**同一份脚本输出**完成三点输出（爆文表、作品类型表、300–500 字总结），字段与条数上限以核心流程为准

### ✨ 特色亮点

- **⏰ 日期语义**：支持口语化「最新/昨天」与指定日；`rankDate` 支持 `"yesterday"`、`"today"`、`"YYYY-MM-DD"`（映射与默认规则见核心流程）
- **🔒 数据真实性**：强制走 `scripts/fetch_growth_rank.py`；**脚本 stdout 须原样展示**，不得改写或重排表格
- **📅 查询窗口**：仅支持**最近 30 天内**的 `rankDate`；查最新时若昨日无数据会**自动向前追溯**（逐天查询，找到即停，见核心流程）

## 一键安装

### 前置条件

- Python 3.8 及以上版本
- `requests` 库：`pip install requests`
- 红狐Hub API Key，格式 `ak_xxxxxxxx`

### 安装方式

#### SkillHub

1. 前往 [SkillHub](https://skillhub.cn)
2. 搜索 **wechat-fastest-growing** 或 **公众号黑马账号推荐**
3. 按平台指引完成安装（支持对话安装或本地 Zip 导入）

#### ClawHub

1. 前往 [ClawHub](https://clawhub.ai)
2. 搜索 **wechat-fastest-growing** 或 **公众号黑马账号推荐**
3. 可使用 CLI：`openclaw skills install wechat-fastest-growing` 或 `clawhub install wechat-fastest-growing`，或下载 skill 包本地导入

#### 方式二：命令行独立使用

无需安装技能包，配置好 API Key 后可直接运行脚本：

```bash
pip install requests
python scripts/fetch_growth_rank.py --rankDate yesterday
```

安装完成后，访问 [红狐 Hub](https://redfox.hk/?source=github)网站 [登录](https://redfox.hk/login?source=github) 注册并获取 API Key（新用户获赠免费积分），配置环境变量 `REDFOX_API_KEY`（见下方），重启终端即可在对话中发起查询。

### 环境变量配置

| 变量名 | 必填 | 说明 |
|---|---|---|
| `REDFOX_API_KEY` | 是 | 红狐 Hub API 访问密钥，格式 `ak_xxxxxxxx` |
| `COZE_REDFOX_API_7633629455969337344` | 否 | 兼容旧变量名（脚本自动回退读取） |

**macOS / Linux**：

```bash
echo 'export REDFOX_API_KEY=<你的apikey>' >> ~/.zshrc
source ~/.zshrc
```

**Windows**（PowerShell）：

```powershell
[Environment]::SetEnvironmentVariable("REDFOX_API_KEY", "<你的apikey>", "User")
```

配置后需重启终端。验证：`echo $REDFOX_API_KEY`（macOS/Linux）或 `echo %REDFOX_API_KEY%`（Windows）。

> **三级回退机制**：脚本读取 API Key 时，按 环境变量 → shell 配置文件（~/.bashrc / ~/.zshrc / ~/.bash_profile / ~/.profile）→ 提示用户配置 的顺序自动获取，无需显式传入。

## 鉴权

### 获取 API Key

1. 访问 [红狐Hub 官网](https://redfox.hk?source=github) 了解服务详情
2. 前往 [注册页面](https://redfox.hk/login?source=github) 注册账号
3. **新注册用户将获赠免费积分**，可立即开始使用 API 服务
4. 注册登录后，在个人中心获取 API Key，格式为 `ak_xxxxxxxx`

### 配置 API Key

- `REDFOX_API_KEY` 从环境变量获取，格式 `ak_xxxxxxxx`
- 脚本支持三级回退读取：环境变量 → shell 配置文件自动探测 → 提示手动配置
- 推荐通过环境变量持久化配置（详见上方 [环境变量配置](#环境变量配置)）

## 使用指南


### 基础使用

#### 1. 发起增长榜查询

在对话中说明日期需求（可省略，默认查昨日）：

> 用户：公众号增长榜
>
> 助手：已按核心流程使用 `rankDate="yesterday"`拉取；以下为脚本输出的完整表格（原样）。…

#### 2. 查看榜单结果

助手运行 `scripts/fetch_growth_rank.py`，将 **stdout 全文原样** 展示（Markdown 表格不得省略、不得自行重算或替换为「摘要表」）。脚本失败或无数据时如实说明，**禁止虚构排名或阅读数**。

#### 3. 增长趋势分析（按需）

当用户需要「特点、规律、为什么增长快」等解读时，在已展示的真实榜单基础上，按核心流程完成 **3 块输出**（爆文分析表 ≤5 条、作品类型分析表 ≤5 条、总结 300–500 字）。

### 高级使用

#### 1. 指定日期与参数

根据用户说法确定 `rankDate`。日期超出最近 30 天时说明不支持，**不得编造**榜单。

> 用户：看下 3 月 15 号的增长榜
>
> 助手：使用 `rankDate="2026-03-15"` 调用脚本；以下为 stdout 原样表格。…

#### 2. 命令行直接拉榜

在项目目录执行（参数名与取值须一致）：

```bash
python scripts/fetch_growth_rank.py --rankDate "<yesterday|today|YYYY-MM-DD>"
```

#### 3. 结构化增长解读

> 用户：最近哪些号增长快，有什么共性？
>
> 助手：先输出脚本榜单（原样），再按核心流程给出两张分析表与一段总结。…

#### 4. 遵循核心流程硬性约束

执行榜单获取与增长分析前，须打开并遵循 [references/core_workflow.md](references/core_workflow.md)（用户意图 → `rankDate` → 脚本参数 → 三点分析）。不得跳过其中的硬性约束。

### 常用命令速查

| 用户说法 / 命令 | 功能 |
|---|---|
| 「最新 / 今日 / 公众号增长榜」 | `rankDate` 按核心流程映射（多为 `yesterday`） |
| 「昨天 / 指定某日期的增长榜」 | `rankDate` 为 `YYYY-MM-DD` 或规则允许的别名 |
| 「增长趋势 / 特点 / 规律」 | 脚本表格原样 + 核心流程规定的 3 段分析 |
| `python scripts/fetch_growth_rank.py --rankDate yesterday` | 命令行拉取昨日增长榜 |

## 使用场景

### 场景一：找高增长对标

**角色**：公众号运营

**需求**：想看近期阅读量增速快的账号与代表作

**使用方式**：

1. 按日期跑脚本拉取增长榜
2. 原样展示表格，点击标题跳转原文核对
3. 可选追问增长特点与共性分析

**预期收益**：快速锁定对标账号与爆款选题方向

---

### 场景二：选题与复盘

**角色**：内容编辑

**需求**：结合榜单看爆款标题与账号策略

**使用方式**：

1. 拉取指定日或「最新」增长榜
2. 按核心流程输出爆文分析表与作品类型表
3. 阅读 300–500 字总结提炼规律

**预期收益**：为下一轮选题提供可验证的数据参考

---

### 场景三：指定日复盘

**角色**：分析师 / 管理者

**需求**：核对某一天的增长排行是否异常

**使用方式**：

1. 使用 `rankDate="YYYY-MM-DD"` 查询（注意 30 天窗口）
2. 对比综合评分指数与阅读、互动指标
3. 对异常条目跳转原文二次核实

**预期收益**：发现单日数据波动与潜在运营动作

---

### 场景四：赛道观察

**角色**：研究者

**需求**：粗看哪些账号在增速榜上集中出现

**使用方式**：

1. 连续多日拉榜，观察重复出现的账号
2. 先看原样榜单，需要时再要结构化分析
3. 结合作品类型表归纳赛道内容形态

**预期收益**：把握赛道热度迁移与内容形态变化

## 项目架构

### 目录结构

```
wechat-fastest-growing/
├── SKILL.md                          # 产品说明文档
├── references/
│   ├── core_workflow.md              # 标准流程、公式、分析字段与硬性约束
│   └── api-spec.md                   # 红狐 Hub API 参数与响应说明
└── scripts/
    └── fetch_growth_rank.py          # 调用 API 获取榜单并输出 Markdown 表格
```

### 技术栈

| 项目 | 说明 |
|---|---|
| 运行环境 | Python 3.8+ |
| 核心依赖 | `requests`（其余为标准库） |
| 数据来源 | 红狐 Hub API（`getGzhCozeSkillDataRaise`） |
| 部署方式 | SkillHub / ClawHub / 命令行脚本 |

### 核心模块

| 模块 | 职责 |
|---|---|
| `fetch_growth_rank.py` | 解析 `rankDate`、调用 红狐 Hub API、输出 Markdown 榜单表格（标题为可点击链接） |
| `core_workflow.md` | 用户意图映射、`rankDate` 规则、stdout 原样约束、三点分析模板与条数上限 |
| `api-spec.md` | 接口地址、鉴权、请求参数与字段说明 |


## 常见问答

### 安装相关问题

**Q1：未检测到 API Key 怎么办？**

按 [一键安装](#一键安装) 注册 红狐Hub 并配置 `REDFOX_API_KEY`。新注册用户有免费积分。

**Q2：如何验证配置已生效？**

执行 `echo $REDFOX_API_KEY`（macOS/Linux）或 `echo %REDFOX_API_KEY%`（Windows），确认输出为 `ak_` 开头。若未生效，重启终端。

**Q3：支持哪些部署方式？**

支持 SkillHub、ClawHub 平台安装，也可直接运行 `scripts/fetch_growth_rank.py` 独立调用。

---

### 使用相关问题

**Q4：`rankDate` 支持哪些写法？**

支持 `"yesterday"`、`"today"`、`"YYYY-MM-DD"`。口语「最新/增长榜」等多映射为 `yesterday`；数据为空时自动向前一天追溯，逐天查询直到找到有数据的日期，找到后立即停止（见核心流程）。

**Q5：可以查询多久以前的数据？**

仅支持**最近 30 天**内；超出范围脚本会报错，请勿让模型编造榜单。

**Q6：增长分析包含哪些内容？**

在用户需要解读时：爆文分析表（≤5 条）、作品类型分析表（≤5 条）、300–500 字总结；均须基于脚本真实输出，不得幻觉。

**Q7：表格里的「综合评分指数」怎么算？**

公式：8 + 2 × ((加权值/阅读数 - 0.2) / 0.8)，范围 8–10；加权值 = 转发×10×0.35 + 在看×5×0.25 + 点赞×2×0.15 + 阅读×1×0.25。详见 [core_workflow.md](references/core_workflow.md)。

---

### 故障排除

**Q8：脚本返回空数据或失败？**

确认 `REDFOX_API_KEY` 有效、日期在 30 天窗口内。查看脚本 stderr 错误信息，勿用模型补齐排行。

---

### 安全与许可

**Q9：API Key 如何保管？**

`REDFOX_API_KEY` 仅通过环境变量读取，请勿写入代码仓库或公开分享。

**Q10：数据使用边界？**

榜单仅以脚本成功输出为准；引用外链与标题时遵守平台与版权规范，不对未经验证的数据做夸大承诺。

## 核心工作流程

完整流程**必须先读取** [references/core_workflow.md](references/core_workflow.md) 并遵循其中的规则、脚本路径与输出约束；正文以下为提纲与召回用说明。

输出格式、用户意图映射、脚本参数、三点分析字段与注意事项详见 [references/core_workflow.md](references/core_workflow.md)。

执行任务时须严格遵循，包括但不限于：

- 必须调用 `scripts/fetch_growth_rank.py`，禁止模型自行生成榜单
- 脚本 stdout Markdown 表格须**原样**呈现
- 增长解读的三表一条数、字数上限以核心流程为准

## 注意事项

- **数据**：榜单仅以脚本成功输出为准；不可用模型幻觉补齐排行、阅读量或链接
- **输出**：标题列已为可点击链接，勿改成纯文本以免丢跳转
- **日期**：仅支持最近 30 天内查询；「最新」场景下昨日无数据时回退前天
- **合规**：遵守平台与版权规范；不对未经验证的数据做夸大或虚假效果承诺
