---
name: wechat-top-account
description: 公众号热门账号推荐快速获取微信公众号综合实力排行榜TOP50，支持按日榜/周榜/月榜及垂直领域筛选，展示综合评分以及详细数据。支持深度分析单个账号、导出HTML可视化报告、订阅日/周/月榜推送。当用户需要查询公众号实力排行、按时间或领域筛选、查看互动指标、获取榜单解读、导出图表或接收定期推送时使用。
---

# 公众号热门账号推荐

## 简介

公众号热门账号推荐是一款微信公众号综合实力排行查询工具，帮助用户快速获取同赛道头部账号的阅读与互动数据，支撑运营对标与竞品跟踪。

通过对话或命令行，你可以：

- 📊 查询 23 个垂直分类的 TOP50 榜单，支持日榜、周榜、月榜切换
- 📈 查看综合评分（满分 100）及发布数、阅读分布、点赞、在看、转发等指标
- 🔍 获取内容生态、热点影响、蓝海赛道三类数据解读
- 📄 导出 HTML 可视化报告（支持图片/PDF）
- 🔔 订阅日/周/月榜，按更新时间自动推送

适用于公众号运营者、MCN 机构、品牌营销人员及需跟踪公众号竞争格局的内容团队。

## 功能特性

### 🎯 核心功能

- **📊 多维排行查询**：按日榜、周榜、月榜查询 23 个分类 TOP50，输入关键词自动匹配分类
- **📈 综合评分体系**：基于阅读、点赞、在看、转发等指标计算综合评分，满分 100
- **🔍 深度分析**：提供内容生态变化、热点影响力量化、蓝海赛道挖掘三种解读视角
- **📄 HTML 报告**：生成可视化榜单页面，支持导出图片和 PDF
- **🔔 定时订阅**：支持订阅日榜、周榜、月榜，按更新时间自动推送

### ✨ 特色亮点

- **⚡ 定时更新**：日榜每日 17:30、周榜每周一 17:30、月榜每月 3 日 23:00 自动刷新
- **📅 有限回溯**：日榜近 7 天、周榜近 3 周、月榜近 3 个月，超出范围自动调整并提示
- **🔗 数据一致**：榜单表格与 HTML 报告共用同一 API，顺序与内容完全一致
- **🔒 API 接入**：通过红狐Hub API Key 调用

## 鉴权

### 获取 API Key

1. 访问 [红狐Hub 官网](https://redfox.hk/?source=github) 了解服务详情
2. 前往 [注册页面](https://redfox.hk/login?source=github) 注册账号
3. **新注册用户将获赠免费积分**，可立即开始使用 API 服务
4. 注册登录后，在个人中心获取 API Key，格式为 `ak_xxxxxxxx`

### 配置 API Key

`REDFOX_API_KEY` 从环境变量获取，格式 `ak_xxxxxxxx`。脚本采用三级认证回退：

| 优先级 | 来源 | 说明 |
|---|---|---|
| 1 | 环境变量 `REDFOX_API_KEY` | 直接读取当前会话的环境变量 |
| 2 | Shell 配置文件 | 自动读取 `~/.zshrc` / `~/.bashrc` / `~/.bash_profile` / PowerShell Profile 中的配置 |
| 3 | 用户输入 | 若以上均未检测到，提示用户手动配置 |

**macOS / Linux**：

```bash
echo 'export REDFOX_API_KEY=<你的apikey>' >> ~/.zshrc
source ~/.zshrc
```

**Windows**（PowerShell）：

```powershell
[Environment]::SetEnvironmentVariable("REDFOX_API_KEY", "<你的apikey>", "User")
```

或将以下内容写入 PowerShell Profile：

```powershell
$env:REDFOX_API_KEY = "<你的apikey>"
```

配置后需重启终端。验证：`echo $REDFOX_API_KEY`（macOS/Linux）或 `$env:REDFOX_API_KEY`（Windows PowerShell）。

## 一键安装

### 前置条件

- Python 3.8 及以上版本
- `requests` 库：`pip install requests`
- 红狐Hub API Key，格式 `ak_xxxxxxxx`

### 安装方式

#### SkillHub

1. 前往 [SkillHub](https://skillhub.cn)
2. 搜索 **wechat-top-account** 或 **公众号热门账号推荐**
3. 安装说明

- 可通过「通过对话安装」方式安装
- 如未安装 SkillHub 商店，先安装商店再安装 skill
- 支持下载 Zip 包到本地，通过本地导入方式安装

#### ClawHub

1. 前往 [ClawHub](https://clawhub.ai)
2. 搜索 **wechat-top-account** 或 **公众号热门账号推荐**
3. 安装说明

- 支持使用 CLI 命令安装：`openclaw skills install wechat-top-account` 或 `clawhub install wechat-top-account`
- 支持下载 skill 包到本地并导入安装
- 安装成功后可在对应客户端直接使用

安装完成后，请先完成 [鉴权](#鉴权) 配置 API Key，重启终端即可在对话中发起查询。

#### 方式二：命令行独立使用

无需安装技能包，配置好 API Key 后可直接运行 `scripts/` 下脚本：

```bash
pip install requests
python scripts/gzh_growth_fetcher.py --list_categories
```

### 环境变量配置

| 变量名 | 必填 | 说明 |
|---|---|---|
| `REDFOX_API_KEY` | 是 | 红狐Hub API 访问密钥，格式 `ak_xxxxxxxx` |

详细获取与配置步骤见上方 [鉴权](#鉴权) 章节。

## 使用指南

### 基础使用

#### 1. 发起榜单查询

在对话中输入查询需求，系统自动识别榜单类型和分类：

> 用户：查询科技类公众号日榜
>
> 助手：输出科技数码分类日榜 TOP50 表格（含综合评分、阅读与互动指标），并附功能询问文案。

#### 2. 查看榜单结果

榜单数据直接输出，无需确认。每条结果包含排名、账号名称（可跳转）、综合评分、发布数/文章数、总阅读、头条阅读、最高阅读、总点赞、总在看、总转发。

> 用户：本周美食类公众号排名
>
> 助手：输出美食餐饮周榜 TOP50，标注数据时间周期与更新时间。

#### 3. 选择扩展功能

榜单输出后，可按需选择后续服务：

> 用户：1
>
> 助手：基于 TOP50 数据输出内容生态变化、热点影响、蓝海赛道三类分析。

回复 `1` 获取分析、`2` 生成 HTML 报告、`3` 或「订阅日/周/月榜」开启定时推送。

### 高级使用

#### 1. 指定分类与日期

通过 `--category` 或 `--keyword` 精确匹配分类，`--rank_date` 指定查询日期（超出范围自动调整）：

```bash
# 首次查询时必须同时保存到临时文件（唯一一次API调用）
python scripts/gzh_growth_fetcher.py --rank_type week --category "美食餐饮" --top_n 50 > /tmp/gzh_result.json 2>/dev/null
python scripts/gzh_growth_fetcher.py --rank_type month --keyword "财经" --rank_date 2026-04-01 --top_n 50 > /tmp/gzh_result.json 2>/dev/null
```

#### 2. 生成 HTML 可视化报告

用户选择 HTML 功能后，使用已保存的数据生成可导出图片/PDF 的页面（不调用API）：

```bash
python scripts/gen_gzh_html.py --input_json_file /tmp/gzh_result.json --top 50
```

#### 3. 获取深度分析解读

用户确认后，基于当前 TOP50 全量数据输出三段式分析：内容生态变化、热点影响力量化、蓝海赛道挖掘。

#### 4. 订阅定时推送

用户回复「订阅日榜」「订阅周榜」「订阅月榜」或「全部订阅」，系统将按对应更新时间推送最新榜单。

完整参数、输出模板与日期校验逻辑见 [核心工作流程](references/core_workflow.md)。

### 常用命令速查

| 命令 | 功能 |
|---|---|
| `python scripts/gzh_growth_fetcher.py --rank_type day --keyword "科技" --top_n 50 > /tmp/gzh_result.json 2>/dev/null` | 科技类日榜 TOP50（首次查询，同时保存文件） |
| `python scripts/gzh_growth_fetcher.py --rank_type week --category "美食餐饮" --top_n 50 > /tmp/gzh_result.json 2>/dev/null` | 美食餐饮周榜 TOP50（首次查询，同时保存文件） |
| `python scripts/gzh_growth_fetcher.py --rank_type month --keyword "财经" --top_n 50 > /tmp/gzh_result.json 2>/dev/null` | 财经类月榜 TOP50（首次查询，同时保存文件） |
| `python scripts/gzh_growth_fetcher.py --list_categories` | 列出全部可用分类 |
| `python scripts/gen_gzh_html.py --input_json_file /tmp/gzh_result.json --top 50` | 用预取数据生成 HTML（不调用API） |
| `python scripts/gzh_growth_fetcher.py --input_json_file /tmp/gzh_result.json` | 用预取数据重新分析（不调用API） |

## 使用场景

### 场景一：日常运营参考

**角色**：公众号运营者

**需求**：了解所属赛道头部账号的内容产出与互动表现

**使用方式**：

1. 查询所属分类日榜或周榜
2. 对比发布频率、单篇阅读与互动率
3. 选择分析功能提取内容策略参考

**预期收益**：明确对标账号，优化选题与发布节奏

---

### 场景二：竞品追踪

**角色**：品牌营销经理

**需求**：跟踪竞品公众号排名与互动变化

**使用方式**：

1. 按周查询竞品所在分类榜单
2. 关注排名波动与阅读/转发变化
3. 订阅周榜定时接收更新

**预期收益**：及时掌握竞品内容发力方向，调整自身策略

---

### 场景三：赛道研判

**角色**：内容创业者

**需求**：评估候选赛道的竞争度与阅读需求

**使用方式**：

1. 查询多个候选分类的月榜数据
2. 选择蓝海赛道分析功能
3. 对比上榜账号数量与平均阅读/评分

**预期收益**：选择竞争度低、需求旺盛的方向切入

---

### 场景四：定期数据汇报

**角色**：MCN 机构运营人员

**需求**：为内部复盘或客户汇报提供可视化数据

**使用方式**：

1. 订阅日榜和周榜保持数据更新
2. 按月导出 HTML 报告（图片/PDF）
3. 结合分析功能撰写复盘结论

**预期收益**：提升汇报效率，数据口径统一可追溯

## 项目架构

### 目录结构

```
wechat-top-account/
├── SKILL.md                      # 产品说明文档
├── references/
│   └── core_workflow.md          # 核心工作流程（模板、逻辑、步骤）
├── scripts/
│   ├── gzh_growth_fetcher.py     # 榜单数据抓取
│   └── gen_gzh_html.py           # HTML 可视化报告生成
└── assets/                       # 静态资源
```

### 技术栈

| 项目 | 说明 |
|---|---|
| 运行环境 | Python 3.8+ |
| 核心依赖 | `requests` |
| 数据来源 | 红狐Hub API |
| 部署方式 | SkillHub / ClawHub / 命令行脚本 |

### 核心模块

| 模块 | 职责 |
|---|---|
| `gzh_growth_fetcher.py` | 通过 红狐Hub API 获取榜单数据，支持关键词匹配分类、日期校验与三级认证回退 |
| `gen_gzh_html.py` | 将榜单数据渲染为可导出图片和 PDF 的 HTML 页面 |
| `core_workflow.md` | 输出格式模板、Checklist、日期计算逻辑、完整操作步骤 |

### 数据更新规则

| 榜单 | 更新时间 | 数据范围 |
|---|---|---|
| 日榜 | 每日 17:30 | 昨日数据，近 7 天 |
| 周榜 | 每周一 17:30 | 上周数据，近 3 周 |
| 月榜 | 每月 3 号 23:00 | 上月数据，近 3 个月 |

## 常见问答

### 安装相关问题

**Q1：未检测到 API Key 怎么办？**

按 [鉴权](#鉴权) 章节步骤注册 红狐Hub 并配置 `REDFOX_API_KEY` 环境变量。新注册用户有免费积分。

**Q2：如何验证配置已生效？**

执行 `echo $REDFOX_API_KEY`，确认输出格式为 `ak_xxxxxxxx`。若未生效，检查终端是否已重启。

**Q3：支持哪些部署方式？**

支持 SkillHub、ClawHub 平台安装，也可直接运行 `scripts/` 下 Python 脚本独立调用。

---

### 使用相关问题

**Q4：支持哪些分类？**

共 23 个分类：总排名、乐活生活、人文资讯、企业品牌、体育娱乐、健康养生、创投商业、学术研究、情感心理、房产楼市、搞笑幽默、教育考试、文摘精选、旅游出行、时尚潮流、民生资讯、汽车交通、知识百科、科技数码、美容美体、美食餐饮、职场发展、财富理财。

**Q5：数据可回溯多久？**

日榜近 7 天、周榜近 3 周、月榜近 3 个月。超出范围时系统自动调整至最近可用数据。

**Q6：榜单与 HTML 报告数据是否一致？**

两者共用同一 API 接口，数据完全一致。

**Q7：数据多久更新一次？**

日榜每日 17:30、周榜每周一 17:30、月榜每月 3 日 23:00 更新。

---

### 故障排除

**Q8：查询返回空数据？**

确认分类名称准确（可用 `--list_categories` 列出全部分类），检查查询日期在有效范围内。

**Q9：HTML 生成失败？**

确认已安装 `requests` 库且 API Key 有效，查看脚本错误输出定位原因。

---

### 安全与许可

**Q10：API Key 如何保管？**

`REDFOX_API_KEY` 仅通过环境变量读取，请勿写入代码仓库或公开分享。Key 泄露可能导致积分被消耗。

**Q11：数据来源与使用范围？**

榜单数据由 红狐Hub 平台提供，仅供运营分析、竞品跟踪等合法商业用途，请遵守平台服务条款。

## 核心工作流程

输出格式模板、数据校验规则、日期计算逻辑、操作步骤及使用示例详见 [references/core_workflow.md](references/core_workflow.md)。

执行任务时须严格遵循 core_workflow.md 中的：

- 格式优先级声明与分阶段输出规则
- 输出前必检 Checklist
- 榜单标准模板与按需输出模板
- 榜单类型判断与分类匹配规则
- 日榜 / 周榜 / 月榜日期校验逻辑
- 数据获取与格式化输出流程
- API 调用次数上限（同一轮查询仅允许 1 次 API 调用）

## 注意事项

- 热门账号推荐榜直接输出，无需确认；分析、HTML、订阅须用户选择后方可生成
- 榜单表格与 HTML 报告须使用同一数据源，禁止修改接口返回顺序
- **同一轮查询（榜单+分析+HTML）全过程只允许调用 1 次 API 接口**，首次获取数据时必须同时保存到临时文件，后续操作一律使用 `--input_json_file` 读取，禁止重复调用 API
- 未收到明确查询指令时，禁止自动调用脚本或输出榜单内容
- 禁止折叠输出
- 脚本输出的 `formatted_markdown` 字段已包含完整的标准模板格式，直接原样输出即可，禁止自行拼装或修改格式
