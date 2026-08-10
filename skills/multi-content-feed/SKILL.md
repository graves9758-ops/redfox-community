---
name: multi-content-feed
description: "全网内容出海信息源 — 每日扫描全平台(公众号/抖音/视频号/小红书/快手/B站)内容出海爆款作品,按点赞量筛选Top50,智能聚类题材方向后生成包含平台标签、封面、互动数据与创作洞察的HTML日报。支持按平台、关键词、时间范围定向查询。⚠️数据每日15:00更新前一天数据,目标日期无数据时必须先告知用户并等待确认后才能调用接口,禁止自动获取。当用户需要内容出海日报、内容出海爆款、内容出海热点、内容出海创作趋势或自定义查询时使用。"
---

# 全网内容出海信息源

## 简介

**全网内容出海信息源**是一款专为内容出海创作者设计的全平台爆款内容追踪工具,参考AI-B站信息源的功能和样式设计。

通过红狐Hub API (`queryContentExportTop`),你可以:
- 📊 每日自动扫描全平台(公众号/抖音/视频号/小红书/快手/B站)内容出海Top50作品
- 🏷️ 基于API返回的`topic`字段智能聚类题材方向
- 📈 生成包含平台标签、封面图、互动数据与创作洞察的可视化HTML日报
- 🔍 支持按平台、关键词、时间范围定向查询

适用于内容出海创作者、运营人员、MCN机构等需要把握全平台内容出海流量风口的场景。

> ⚠️ **重要**:数据每日15:00更新前一天数据,目标日期无数据时**禁止自动调用接口**,必须先告知用户并等待确认。
>
> ⛔ **输出规范**:日报生成后,对话回复**必须严格按照输出模板输出 md 内容**,禁止任何自由发挥、省略或口语化文字。详见 [references/core_workflow.md](references/core_workflow.md) 中的终端输出格式规范。

## 功能特性

### 🎯 核心功能

| 功能模块 | 能力描述 | 核心价值 |
|---------|---------|----------|
| 📊 爆款发现 | 从全平台内容出海中按点赞量获取Top50作品 | 精准定位各平台高热度内容 |
| 🏷️ 题材聚类 | 基于API返回的topic字段自动聚类,题材分类完全由数据决定 | 无需预定义关键词,动态归类 |
| 🌐 全平台覆盖 | 支持公众号/抖音/视频号/小红书/快手/B站 6大平台 | 一站式获取全平台数据 |
| 🔍 智能查询 | 默认查询全平台,可按关键词和平台定向查询 | 灵活覆盖任意细分方向 |
| 📈 创作洞察 | 分析各平台内容风格、跨平台题材对比、平台差异化策略 | 深度挖掘平台特征与创作规律 |
| 🎨 可视化日报 | 白色主题HTML,平台标签+封面图+互动数据+作品直链 | 直观展示每日热点 |
| 🔔 一键订阅 | `--subscribe` 开启每日自动产出 | 日报自动攒在本地文件夹 |

### ✨ 特色亮点

- **⚡ 智能日期判断**:脚本内置 `DATA_UPDATE_HOUR = 15` 常量,调用接口前自动检测目标日期是否在无数据区间
- **🌐 全平台适配**:API返回各平台Top50,公众号按阅读数排序,其余按点赞数排序;作品链接直接使用API返回的url字段
- **🏷️ 平台标签**:HTML日报中每条作品展示彩色平台标签(公众号绿/抖音黑/小红书红等)
- **🔒 安全可靠**:API Key通过环境变量 `REDFOX_API_KEY` 获取,禁止硬编码

## 一键安装

### 前置条件

- Python 3 运行环境
- 已注册红狐Hub账号并获取 API Key

### 安装步骤

#### 1. 获取 API Key

前往 [红狐Hub 官网](https://redfox.hk/) 注册,登录后在个人中心获取,格式为 `ak_xxxxxxxx`。新注册用户获赠免费积分。

#### 2. 配置环境变量

**macOS/Linux**:
```bash
echo 'export REDFOX_API_KEY=ak_xxxxxxxx' >> ~/.zshrc
source ~/.zshrc
```

**Windows**(PowerShell):
```powershell
[Environment]::SetEnvironmentVariable("REDFOX_API_KEY", "ak_xxxxxxxx", "User")
```
配置后需**重启终端**使环境变量生效。

#### 3. 验证配置

```bash
# macOS/Linux
echo $REDFOX_API_KEY

# Windows
echo %REDFOX_API_KEY%
```

### 环境变量配置

| 变量名 | 必填 | 说明 |
|--------|------|------|
| `REDFOX_API_KEY` | 是 | 红狐Hub API访问密钥,通过 `X-API-KEY` 请求头鉴权 |

## 使用指南

### 基础使用

#### 1. 生成最新日报

```bash
python3 assets/daily_report.py --latest
```

**执行流程**:
1. 自动计算最新可用日期(15:00规则)
2. 查询全平台Top50(公众号+抖音+视频号+小红书+快手+B站)
3. 题材聚类+生成HTML日报
4. 自动浏览器打开

> ⚠️ **日期预检规则**:若目标日期无数据,必须先告知用户并等待确认后才能执行。

#### 2. 查询指定日期

```bash
python3 assets/daily_report.py --date 2026-06-10
```

历史日期已有数据,无需确认,直接查询。

#### 3. 按关键词查询

```bash
python3 assets/daily_report.py --keyword "品牌出海" --latest
```

### 高级使用

#### 1. 查询指定平台

```bash
# 仅查小红书和抖音
python3 assets/daily_report.py --platforms "3,1" --latest

# 仅查公众号
python3 assets/daily_report.py --platforms "0" --latest
```

**平台编号**:0=公众号, 1=抖音, 2=视频号, 3=小红书, 4=快手, 6=B站

#### 2. 自定义时间范围

```bash
python3 assets/daily_report.py \
  --start-time "2026-06-10 08:00:00" \
  --end-time "2026-06-15 20:00:00"
```

#### 3. 使用缓存数据

```bash
python3 assets/daily_report.py --from-cache
```

从 `~/.workbuddy/cache/content_export_top_data.json` 加载,缓存有效期1小时,不扣积分。

#### 4. 开启每日订阅

```bash
python3 assets/daily_report.py --subscribe
```

日报自动保存至 `~/Downloads/QoderReports/`,文件名:`内容出海日报_YYYY-MM-DD.html`。

### 常用命令速查

| 命令 | 功能 |
|------|------|
| `--latest` | 自动使用最新有数据的日期,跳过无数据区间 |
| `--date YYYY-MM-DD` | 指定日期查询(历史日期无需确认) |
| `--keyword "关键词"` | 搜索关键词(模糊匹配标题或用户名称) |
| `--platforms "0,1,3"` | 指定平台,逗号分隔(默认全平台) |
| `--from-cache` | 使用缓存数据,不扣积分 |
| `--subscribe` | 开启每日订阅 |
| `--unsubscribe` | 关闭每日订阅 |
| `--start-time / --end-time` | 自定义时间范围 |
| `--output-dir` | 自定义输出目录 |
| `--api-key` | 指定API Key |

## 使用场景

### 场景一:内容出海创作者选题参考

**角色**:内容出海创作者

**需求**:了解全平台内容出海市场的热门题材和爆款趋势,指导选题决策

**使用方式**:
1. 每日执行 `--latest` 获取最新日报
2. 分析题材聚类结果,关注新兴起量信号
3. 参考爆款标题特征和题材趋势报告

**预期收益**:精准把握全平台流量风口,提升选题命中率

---

### 场景二:运营团队竞品监控

**角色**:内容出海运营/MCN机构

**需求**:追踪竞品账号在各平台的表现,分析爆款内容特征

**使用方式**:
1. 使用 `--keyword` 定向查询竞品关键词
2. 使用 `--platforms` 关注核心平台
3. 开启 `--subscribe` 每日自动攒日报

**预期收益**:及时掌握竞品动态,优化自身运营策略

---

### 场景三:内容趋势分析

**角色**:内容策划/数据分析师

**需求**:分析全平台内容出海的内容趋势,为内容规划提供数据支撑

**使用方式**:
1. 结合 `--start-time` 和 `--end-time` 分析时间范围数据
2. 利用创作趋势分析深度挖掘规律
3. 关注跨题材对比建议,发现题材融合机会

**预期收益**:产出结构化趋势报告,支撑内容战略决策

## 项目架构

### 目录结构

```
multi-content-feed/
├── SKILL.md                      # Skill主文档(本文件)
├── scripts/                      # 脚本源码
│   └── playlet_xhs_daily.py      # 日报生成脚本(开发版)
├── assets/                       # Skill运行时资源
│   ├── daily_report.py           # 日报生成脚本(运行时使用)
│   └── default_cover.png         # 默认封面图(加载失败时的fallback)
└── references/                   # 参考文档
    ├── core_workflow.md          # 核心执行流程、格式模板、日期判断逻辑
    └── examples.md               # 使用示例与常见用法组合
```

### 技术栈

| 组件 | 技术 | 说明 |
|------|------|------|
| 运行环境 | Python 3 | 脚本语言 |
| 数据源 | 红狐Hub API | `X-API-KEY` 请求头鉴权 |
| API端点 | `https://redfox.hk/story/api/parseWork/queryContentExportTop` | POST请求 |
| 支持平台 | 0=公众号, 1=抖音, 2=视频号, 3=小红书, 4=快手, 6=B站 | 每个平台Top50 |
| 排序规则 | 公众号按readCount倒序,其余按likeCount倒序 | API内置排序 |
| 数据存储 | JSON缓存 | `~/.workbuddy/cache/content_export_top_data.json` |
| 输出格式 | HTML + 终端Markdown | 白色主题,平台彩色标签 |
| 输出目录 | `~/Downloads/QoderReports` | 可自定义 |

### 核心模块说明

| 模块 | 文件 | 职责 |
|------|------|------|
| API调用 | `fetch_content_export_top()` | 调用queryContentExportTop接口,解析platformGroups,去重排序 |
| 题材聚类 | `cluster_by_topic()` | 基于API返回的topic字段自动聚类 |
| HTML生成 | `generate_html_report()` | 白色主题日报,平台标签+互动数据为0时隐藏 |
| 日期计算 | `calculate_latest_date()` | 15:00规则自动推算可用日期 |
| 缓存管理 | `load_cache()`/`save_cache()` | 1小时有效期,基于photoId去重 |

### 数据流转

```
用户请求 → 日期预检(15:00规则) → 用户确认
  ↓
API调用(queryContentExportTop全平台+去重+排序)
  ↓
题材聚类(基于topic字段自动归类)
  ↓
HTML日报生成 + 终端摘要输出
  ↓
深度分析(漏斗结构,3个层级)
```

## 常见问答

### 安装相关问题

**Q1: 安装时提示 "未找到 REDFOX_API_KEY 环境变量" 怎么办?**

A: 请按以下步骤检查:
1. 确认 API Key 已正确配置(Windows: `[Environment]::SetEnvironmentVariable("REDFOX_API_KEY", "ak_xxx", "User")`)
2. 配置后需**重启终端**使环境变量生效
3. 验证: `echo %REDFOX_API_KEY%` 应输出你的Key值

**Q2: API Key 如何获取?**

A: 前往 [红狐Hub 官网](https://redfox.hk/) 注册账号,登录后在个人中心获取,格式为 `ak_xxxxxxxx`。新注册用户获赠免费积分。

---

### 使用相关问题

**Q3: 数据多久更新一次?**

A: 每日15:00更新前一天的数据。
- 15:00前:最新可用日期 = 前天(T-2)
- 15:00后:最新可用日期 = 昨天(T-1)

**Q4: 查询不到数据怎么办?**

A: 可能原因:
1. 目标日期尚无数据(未到15:00更新时间)
2. API Key权限不足或积分耗尽
3. 网络连接问题

建议先使用 `--from-cache` 检查缓存,或换一个日期尝试。

---

### 故障排除

**Q5: Windows PowerShell 执行报 UnicodeEncodeError?**

A: 脚本输出包含emoji,需设置UTF-8编码:
```powershell
$env:PYTHONIOENCODING='utf-8'
python assets/daily_report.py --latest
```

**Q6: HTML日报中图片加载失败?**

A: 脚本已内置fallback机制,加载失败时自动显示默认封面图(`assets/default_cover.png`)。部分封面图URL使用HEIF格式,脚本会自动转换为JPG格式提高兼容性。

---

### 安全与许可

**Q7: 数据安全如何保障?**

A:
- API Key仅通过环境变量获取,禁止硬编码
- 数据来源唯一:仅使用红狐Hub API,禁止自主采集
- 缓存文件存储在本地 `~/.workbuddy/cache/`

## 📚 参考文档

- [core_workflow.md](references/core_workflow.md) — 核心执行流程、输出格式模板、日期判断逻辑、字段映射、参数说明
- [examples.md](references/examples.md) — 使用示例与常见用法组合
