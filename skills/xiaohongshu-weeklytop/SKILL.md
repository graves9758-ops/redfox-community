---
name: xiaohongshu-weeklytop
description: 专注于小红书平台的内容趋势分析，基于近7天热门笔记TOP50深度洞察，支持24个垂直领域分类查询、冷门爆款挖掘及每日订阅推送。创作者可查询小红书热门内容、分析爆款笔记、了解各领域趋势或获取创作灵感。
---

# 小红书七日爆款笔记

## 简介

**一句话定位**：专为内容创作者与运营人员设计的小红书七日爆款笔记工具，一键获取垂直领域热门笔记与深度分析。

**核心价值**：
- 解决「不知道当下什么内容火、为什么火」的选题难题
- 提供七日爆款笔记 + 智能分析 + 可选 HTML 报告，支撑复盘与创作决策
- 支持关键词自动匹配 24 个垂直分类（原"综合杂项"已归类到"综合全部"），降低查询门槛

**适用对象**：品牌方、MCN 机构、小红书博主、内容运营、增长团队

**技术基础**：Python 3 + RedFox 小红书数据 API，数据每日 19:00 更新

---

## 功能特性

### 🎯 核心功能

| 功能 | 说明 |
|------|------|
| 📊 近日热榜查询 |按分类查询热门笔记，覆盖美妆、穿搭、美食、家居等24个垂直领域，快速掌握当下流量风向 |
| 📈 七日热门分析 | 基于近7天各分类TOP50热门笔记的深度洞察，从流行趋势、热门话题深度分析、实用价值等维度拆解爆款共性 |
| 🔍 形式规律对比 | 自动识别高质量封面、情绪共鸣点、实用价值、紧跟热点等爆款要素，提炼可复用的创作范式 |
| 📁 创作建议输出 | 基于分析结果，提供可执行的选题方向、差异化策略、高维作品拆解建议 |
| 🔔 订阅推送 | 定时推送最新趋势分析报告，持续跟踪赛道热点，不错过任何一个流量机会 |

### ✨ 特色亮点

- **⚡ 数据一致**：七日爆款笔记表格与 HTML 页面使用相同数据源与排序逻辑，排名完全一致
- **📱 分页展示**：首次展示 TOP20，回复「查看更多」可加载剩余数据
- **🎯 冷门爆款**：聚焦低粉高互动笔记，适合挖掘可对标样本
- **🔒 零配置调用**：Agent 执行时自动判断查询日期，无需手动维护

---

## 鉴权

### 获取 API Key

1. 访问 [红狐Hub 官网](https://redfox.hk/?source=github) 了解服务详情
2. 前往 [注册页面](https://redfox.hk/login?source=github) 注册账号
3. 新注册用户将获赠免费积分，可立即开始使用 API 服务
4. 注册登录后，在个人中心获取 API Key，格式为 `ak_xxxxxxxx`

### 配置 API Key

`REDFOX_API_KEY` 从环境变量获取，格式 `ak_xxxxxxxx`。

若未设置，提示用户自行配置：`export REDFOX_API_KEY=<你的apikey>`；若不会配置，Agent 可主动帮用户设置：

- **macOS/Linux**：将 `export REDFOX_API_KEY=<值>` 追加到 `~/.zshrc`（zsh）或 `~/.bashrc`（bash），然后 `source` 对应文件使其全局生效
- **Windows**：使用 `[Environment]::SetEnvironmentVariable("REDFOX_API_KEY", "<值>", "User")` 设置用户级永久环境变量（需重启终端生效）

配置完成后应验证：`echo $REDFOX_API_KEY`（macOS/Linux）或 `echo %REDFOX_API_KEY%`（Windows），确保换一个 skill 也能读取到。

---

## 一键安装

### 前置条件

- Python 3.8+
- 网络可访问 `redfox.hk` 数据 API
- 已安装 `requests` 库（`pip install requests`）
- 已配置 `REDFOX_API_KEY` 环境变量（参见上方「鉴权」章节）

### 安装方式

#### 方式一：WorkBuddy / Cursor Skills（推荐）

1. 将本 Skill 目录放置于 Skills 工作区（如 `~/.workbuddy/skills/xiaohongshu-weeklytop`）
2. 确保目录结构完整：`SKILL.md`、`references/`、`scripts/`
3. 在对话中直接触发，例如：
   - 「帮我查一下睫毛膏相关的爆款笔记」
   - 「最近小红书有什么热门内容」
   - 「查看穿搭领域七日热榜」

#### 方式二：命令行独立运行

```bash
# 进入 Skill 目录
cd xiaohongshu-weeklytop

# 获取榜单数据（JSON 输出）
python scripts/xhs_weekly_fetcher.py --keyword "睫毛膏" --top_n 50

# 生成 HTML 报告（从已获取的数据文件读取，不再调用API）
python scripts/gen_xhs_html.py --data_file "xhs_data.json" --category "化妆美容" --top 20
```

---

## 使用指南

> **执行约束（强制）**：Agent 执行本 Skill 时，**必须先完整阅读并严格遵循** [references/core_workflow.md](references/core_workflow.md) 中的调用 Key 说明、输出规范、操作步骤与注意事项。以下为基础用法摘要，详细流程以核心工作流文档为准。

### 基础使用

#### 1. 关键词查询爆款

> **用户**：帮我查一下睫毛膏相关的爆款笔记
>
> **助手**：自动匹配「化妆美容」分类 → 获取 TOP50 数据 → 输出七日爆款笔记 TOP20 → 七日分析 → 功能询问（HTML+订阅）

#### 2. 关键词未精确匹配（v2.0）

> **用户**：查一下洗浴中心相关的爆款
>
> **助手**：关键词未命中任何分类关键词 → **禁止直接查询** → 展示推荐相近分类（**1~3个**，按相关度，仅强相关不强凑） + "⚠️若无想要查询的分类，可前往 https://redfox.hk/apis/xiaohongshu/384C6W6B?source=github API文档查询更精确的作品~" 选项 → **等待用户确认分类**（确认后以指定分类重新查询）或选择"若无..."（**停止后续所有流程**）

#### 3. 泛领域热门查询

> **用户**：最近小红书有什么热门内容
>
> **助手**：使用「综合全部」分类 → 按标准三步输出完整结果

#### 4. 查看更多数据

> **用户**：查看更多
>
> **助手**：延续输出 TOP21 至末尾 → 如用户选择生成 HTML，从已获取数据文件读取完整数据重新生成

### 高级使用

#### 1. 指定日期查询

> **用户**：查看 2026-04-15 穿搭领域热榜
>
> **助手**：使用 `--rank_date "2026-04-15"` 查询指定日期数据

#### 2. 直接指定分类

```bash
python scripts/xhs_weekly_fetcher.py --category "时尚穿搭" --top_n 50
python scripts/gen_xhs_html.py --category "时尚穿搭" --top 50
```

#### 3. 订阅每日推送 / 生成 HTML

首次查询完成后，助手会展示功能询问：回复 `1` 订阅每日 19:30 推送，回复 `2` 生成小红书风格 HTML 文件包。HTML 生成后会自动在对话中预览展示（优先 `preview_url`，未正常展示则用 `open_result_view` 兜底），无需手动查找文件。

#### 4. 自定义 HTML 输出路径

```bash
python scripts/gen_xhs_html.py --data_file "xhs_data.json" --category "穿搭" --top 20 --output ./reports/小红书七日爆款笔记_穿搭.html
```

### 常用命令速查

| 命令 / 场景 | 功能 |
|-------------|------|
| `python scripts/xhs_weekly_fetcher.py --keyword "{词}" --top_n 50` | 获取榜单原始数据 |
| `python scripts/gen_xhs_html.py --data_file "{文件}" --category "{分类}" --top 20` | 首次生成 HTML（TOP20，从数据文件读取） |
| `python scripts/gen_xhs_html.py --data_file "{文件}" --category "{分类}" --top 50` | 查看更多后生成完整 HTML |
| 用户说「查看更多」 | 输出 TOP21+ |
| 用户回复 `1` / "订阅" | 订阅每日 19:30 推送 |
| 用户回复 `2` / "html" / "生成" | 生成 HTML 文件包 |

### 核心工作流引用

完整执行规范（输出格式、调用 Key、表格字段、数据一致性、订阅逻辑、使用示例等）见：

**→ [references/core_workflow.md](references/core_workflow.md)**

---

## 使用场景

### 场景一：博主选题灵感

**角色**：小红书新人博主

**需求**：了解同赛道当下什么内容容易爆

**使用方式**：
1. 输入赛道关键词（如「护肤」「穿搭」）
2. 查看七日爆款笔记 TOP20 与七日分析
3. 对标参考笔记的标题结构与内容特征

**预期收益**：快速找到可借鉴的选题方向，降低冷启动试错成本

---

### 场景二：品牌竞品监测

**角色**：品牌营销经理

**需求**：监测垂直领域爆款内容与趋势变化

**使用方式**：
1. 按产品/品类关键词查询（如「口红」「防晒」）
2. 分析最高互动作品的共性特征
3. 导出 HTML 报告供团队复盘

**预期收益**：掌握品类内容风向，优化投放与种草策略

---

### 场景三：MCN 达人运营复盘

**角色**：MCN 运营人员

**需求**：为旗下达人提供赛道热点参考

**使用方式**：
1. 按达人赛道查询七日热榜
2. 拆解爆款标题类型与发布规律
3. 订阅每日推送，持续跟踪热点

**预期收益**：提升达人内容策划效率，缩短选题讨论周期

---

### 场景四：增长团队数据洞察

**角色**：增长/数据分析同学

**需求**：获取可导出的结构化热榜报告

**使用方式**：
1. 查询目标分类完整 TOP50
2. 使用 HTML 页面导出 PDF/图片
3. 结合新增互动数据判断内容上升势头

**预期收益**：获得可分享、可归档的数据报告，支撑周报与策略会

---

## 项目架构

### 目录结构

```
xiaohongshu-weeklytop/
├── SKILL.md                      # Skill 入口与使用说明（本文件）
├── references/
│   └── core_workflow.md          # 核心执行流程与输出规范（Agent 必读）
└── scripts/
    ├── xhs_weekly_fetcher.py     # 榜单数据获取脚本
    └── gen_xhs_html.py           # HTML 可视化报告生成脚本
```

### 技术栈

| 项目 | 说明 |
|------|------|
| 运行环境 | Python 3.8+ |
| HTTP 请求 | `requests`（原生 Python） |
| 数据来源 | RedFox 小红书 Coze Skill API |
| 输出格式 | Markdown 表格 + 独立 HTML 文件 |
| 部署平台 | WorkBuddy / Cursor Agent Skills |

### 核心模块

| 模块 | 文件 | 职责 |
|------|------|------|
| 数据获取 | `xhs_weekly_fetcher.py` | 调用 API、分类匹配、日期判断、排序输出 |
| 报告生成 | `gen_xhs_html.py` | 从已获取的 JSON 数据文件渲染 HTML 页面，支持 PDF/图片导出 |
| 执行规范 | `core_workflow.md` | 定义输出格式、调用 Key、三步流程、功能询问等强制约束 |



### 数据更新规则

- **更新时间**：每天 19:00 更新昨日榜单
- **数据范围**：往前 7 天热门笔记 TOP50
- **分类覆盖**：24 个垂直领域（原"综合杂项"已归类到"综合全部"）
- **日期判断**：当前时间 ≥ 19:00 查昨日，< 19:00 查前天

---

## 常见问答

### 安装相关问题

**Q1: 脚本运行报错 `ModuleNotFoundError: requests`？**

A: 该依赖为标准 Python HTTP 库。请运行 `pip install requests` 安装。若在虚拟环境中运行，请确保已激活对应环境。

**Q2: 脚本提示「未找到 REDFOX_API_KEY」？**

A: 请按照上方「鉴权」章节完成 API Key 的获取和配置。确保环境变量 `REDFOX_API_KEY` 已正确设置且格式为 `ak_xxxxxxxx`。

**Q3: 如何将 Skill 添加到 Cursor / WorkBuddy？**

A: 将 `xiaohongshu-weeklytop` 文件夹放入 Skills 目录，Agent 会根据 `description` 自动匹配触发。对话中提及「小红书热门」「爆款笔记」等关键词即可调用。

---

### 使用相关问题

**Q4: 数据多久更新一次？**

A: 榜单数据每日 19:00 更新（更新的是昨日数据）。订阅推送时间为每日 19:30。

**Q5: 为什么有时查的是「前天」而不是「昨天」？**

A: 当日 19:00 之前，最新榜单尚未更新，系统自动查询前天数据。19:00 之后则查询昨日数据。详见 [core_workflow.md](references/core_workflow.md) 日期判断规则。


---

### 故障排除

**Q6: 七日爆款笔记表格与 HTML 数据不一致？**

A: HTML 生成时从已获取的 JSON 数据文件读取，与表格使用完全相同的原始数据。检查是否使用了不同的 `--top` 参数。

**Q7: API 请求失败或无数据？**

A: 按以下步骤排查：
1. 确认网络可访问  [红狐Hub 官网](https://redfox.hk/?source=github)
2. 检查 `--rank_date` 是否为有效日期
3. 尝试更换关键词或指定 `--category`
4. 19:00 前查询时，确认是否应使用前天日期

---

### 执行规范

**Q8: Agent 执行时必须遵守哪些规则？**

A: 必须完整遵循 [references/core_workflow.md](references/core_workflow.md)，包括但不限于：
- 调用 Key 说明（脚本参数与 top_n/top 取值规范）
- 三步输出顺序（七日爆款笔记 → 分析 → 功能询问）
- 禁止折叠输出、禁止输出除 HTML 外的文件
- 首次 TOP20 + 查看更多逻辑
- HTML 生成时从已获取数据文件读取，禁止再次调用 API
- HTML 生成后必须调用 preview_url 在对话中直接展示页面；若未正常展示则用 open_result_view 兜底
- 功能询问在分析之后立即展示，禁止跳过
