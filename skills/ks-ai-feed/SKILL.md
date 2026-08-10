---
name: ks-ai-feed
description: 快手AI内容日报生成工具。每日自动扫描快手平台AI创作内容，按播放量筛选爆款视频并智能聚类，生成深色主题HTML日报（含封面图、互动数据、视频直链），同步输出AI情报洞察（热度TOP话题、起量信号、核心达人、推荐调查方向）。当用户需要AI快手日报、快手爆款、AI快手热点、快手AI内容、快手AI视频、快手情报时使用。触发词：AI快手日报、快手爆款、快手AI热点、快手情报、快手AI视频。
---

# AI快手信息源

## 📝 简介

每日自动扫描快手平台AI创作内容，按播放量筛选爆款视频、智能聚类生成深色主题HTML日报，同步输出基于智能情报调查员方法论的AI情报洞察。


## ✨ 功能特性

| 功能模块 | 能力描述 | 核心价值 |
|---------|---------|----------|
| 爆款发现 | 按播放量筛选快手AI热门视频 | 精准定位高热度内容 |
| 智能聚类 | 从内容中自动识别话题方向 | 每日热点一目了然 |
| AI情报洞察 | 热度TOP话题、起量信号、达人分析、推荐调查方向 | 深度洞察流量趋势 |
| 可视化日报 | 深色HTML日报，含封面图、互动数据、视频直链 | 直观浏览与跳转 |
| 一键订阅 | `--subscribe` 开启每日自动产出 | 持续追踪不遗漏 |
| 图片兼容 | 防盗链代理 + HEIF/HEIC 自动转JPG | 封面图稳定展示 |

## 🔑 鉴权

前往 [redfox.hk/login](https://www.redfox.hk/login) 注册获取 API Token,然后配置:

| 方式 | 命令 |
|------|------|
| 环境变量(推荐) | `export REDFOX_API_KEY=ak_你的密钥` |
| 命令行参数 | `--api-key ak_你的密钥` |
| 配置文件 | `echo '{"api_key":"ak_你的密钥"}' > ~/.qoder/apis/redfox.json` |

## 🔌 API 接口规范

### 批量查询接口

**接口地址**: `POST https://redfox.hk/story/api/parseWork/queryKsAiMsgs/batch`

**请求头**:
```
X-API-Key: ak_你的API密钥
Content-Type: application/json
```

**请求体**:
```json
{
  "keywords": ["AI", "人工智能", "大模型", "GPT", "Agent", "AI绘画", "AI教程"],
  "pageNum": 1,
  "pageSize": 200,
  "source": "AI快手信息源-GitHub",
  "startTime": "2026-06-16 00:00:00",  // 可选
  "endTime": "2026-06-16 23:59:59"      // 可选
}
```

**参数说明**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `keywords` | Array | ✅ | 关键词数组,支持多关键词批量查询 |
| `pageNum` | Number | ✅ | 页码,从1开始 |
| `pageSize` | Number | ✅ | 每页条数,默认200 |
| `source` | String | ✅ | 来源标识 |
| `startTime` | String | ❌ | 开始时间 `YYYY-MM-DD HH:mm:ss` |
| `endTime` | String | ❌ | 结束时间 `YYYY-MM-DD HH:mm:ss` |

**性能优势**:
- ✅ 一次请求传入所有关键词,减少85%+ API调用
- ✅ 自动去重合并,数据更全面
- ✅ 超时时间30秒,适配大批量数据

## 📊 数据更新规则

- **更新时间**：每日 15:00 更新前一天的数据
- **可查询日期**：仅可查询已更新数据的日期（昨天及之前）
- **数据不可用时**：脚本自动判断目标日期是否已有数据，若尚未更新则提示用户并询问是否查询最新可用日期

## 🔧 使用方式

```bash
# 生成今日爆款日报（含情报洞察）
python3 "$SKILL_PATH/assets/daily_report.py"

# 自定义关注方向
python3 "$SKILL_PATH/assets/daily_report.py" --keywords "AI教程,AI绘画,ChatGPT,AI工具"

# 查看历史某天
python3 "$SKILL_PATH/assets/daily_report.py" --date 2026-06-10

# 订阅 / 取消订阅
python3 "$SKILL_PATH/assets/daily_report.py" --subscribe
python3 "$SKILL_PATH/assets/daily_report.py" --unsubscribe
```

> 依赖：`pip3 install requests`

> ⚠️ **Windows 用户注意**：命令中的 `python3` 需替换为 `python`，`pip3` 替换为 `pip`。

生成的 HTML 日报保存在 `~/Downloads/QoderReports/`。终端同步输出分类视频表格 + AI情报洞察。

### 预览服务

1. 运行 `daily_report.py` 时加 `--no-open` 参数
2. **单独启动预览服务**（后台运行）：
   ```bash
   python3 "$SKILL_PATH/assets/preview_server.py"
   ```
3. 调用 RunPreview，**必须使用 HTML 文件直链地址**：`http://127.0.0.1:8766/{HTML文件名}`

> ⚠️ **RunPreview 必须使用 HTML 文件直链地址**（如 `http://127.0.0.1:8766/AI快手日报_2026-06-16_150715.html`），不可使用根路径 `http://127.0.0.1:8766`，根路径的 302 重定向会导致空白页面。

> 内置服务同时提供：静态 HTML 文件服务 + `/api/search` 搜索代理 + `/api/img` 图片代理（绕过快手防盗链）。

## 核心参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--keywords` | 关注的话题方向，逗号分隔 | `AI,人工智能,大模型,GPT,Agent,AI绘画,AI教程` |
| `--count` | 扫描视频数量 | `200` |
| `--date` | 指定日期，`YYYY-MM-DD` 或范围 `YYYY-MM-DD~YYYY-MM-DD` | 今天 |
| `--output-dir` | 输出目录 | `~/Downloads/QoderReports` |
| `--api-key` | 指定 API Key | — |
| `--subscribe` | 开启每日订阅 | — |
| `--unsubscribe` | 关闭每日订阅 | — |
| `--no-open` | 不自动打开浏览器 | — |

## 🧠 AI情报洞察

基于智能情报调查员方法论，在每日快手爆款内容聚类后同步生成：

| 洞察模块 | 内容 | 价值 |
|---------|------|------|
| 热度TOP话题 | 占比、条数、头部视频 | 快速掌握当日风向 |
| 新兴起量信号 | 低占比高互动的潜力话题 | 提前捕捉流量风口 |
| 核心达人 | 高产+高互动作者 | 锁定关键创作者 |
| 推荐调查方向 | 场景+引擎组合+搜索关键词 | 一键进入深度调查 |
| 跨平台对比建议 | 同步关注其他平台同话题 | 全网视角消除偏差 |

详细调查策略见 [engine-strategy.md](references/engine-strategy.md)、[investigation-modes.md](references/investigation-modes.md)、[investigation-templates.md](references/investigation-templates.md)。

## 📋 固定输出模式

每次运行日报后，终端与对话输出**必须**遵循以下结构化格式：

```markdown
## AI快手信息源 · {日期} 日报

**扫描 {N} 条热门视频，聚类 {M} 个分类**

---

### 分类概览

| 分类 | 数量 | 占比 | 亮点 |
|------|------|------|------|
| #{分类名} | {N}条 | {X}% | 头部视频亮点描述 |

---

### AI情报洞察报告

**一、新兴起量信号**

- 🔥 **#{话题}** — 仅{N}条但均互动{X}+，描述

**二、核心达人**

| 达人 | 作品数 | 总赞 | 亮点 |
|------|--------|------|------|
| @{作者} | {N}条 | {X}w | 描述 |

**三、推荐调查方向**

| 话题 | 调查场景 | 推荐引擎 | 搜索关键词 |
|------|---------|---------|-----------|
| #{话题} | {场景} | 引擎组合 | 关键词1 / 关键词2 |

**四、跨平台对比建议**

- **{话题}** — 建议同步关注抖音、B站、小红书同话题热度

---

**日报地址**：{HTML文件绝对路径}

**预览地址**：http://127.0.0.1:8766/{HTML文件名}
```

> 以上格式为**强制规范**，所有字段不可省略。若某模块无数据则标注"暂无"。

> **必须执行**：日报输出完成后，按以下步骤启动预览：
> 1. 后台启动预览服务：`python3 "$SKILL_PATH/assets/preview_server.py"`
> 2. 调用 RunPreview，使用 HTML 文件直链地址 `http://127.0.0.1:8766/{HTML文件名}`（不可用根路径）

## 其他资源

- [engine-strategy.md](references/engine-strategy.md) — 引擎选择策略、独有能力与高级搜索方法
- [investigation-modes.md](references/investigation-modes.md) — 四种调查模式的搜索策略编排与输出模板
- [investigation-templates.md](references/investigation-templates.md) — 调查报告完整模板集
