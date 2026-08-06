---
name: tiktok-home-downloader
description: TikTok主页视频批量提取 — 输入TikTok主页链接/handle，自动拉取账号主页全部作品并解析无水印下载链接，支持批量一键下载到本地。适用场景：竞品账号内容拆解与逐帧学习、收藏喜欢的创作者全部作品避免被删、批量搬运素材二次剪辑创作、保存自己账号作品做本地备份防丢失、课程/教程类视频离线囤货反复看、甲方要求提供无水印源文件、达人合作前快速拉取对方作品做背调分析。触发词：TikTok主页下载、TikTok视频下载、TikTok批量下载、TikTok无水印下载、下载TikTok作品、TikTok账号视频提取、TikTok主页视频批量提取、TikTok去水印、TikTok视频备份、竞品视频下载。
---

# TikTok 主页视频批量提取

> 输入 TikTok 主页链接 → 拉取主页作品列表 → 解析下载链接 → 一键下载到本地

---

## 简介

TikTok 账号主页视频批量提取工具。只需提供 TikTok 账号主页链接，自动拉取该账号主页作品列表，逐条解析无水印视频下载直链，支持一键批量下载到本地。

**适用对象**

- 🎬 **内容创作者** — 收藏学习竞品账号的优质内容，逐帧拆解拍摄与剪辑技巧。
- 📦 **运营 / MCN** — 批量备份达人合作作品，快速完成背调分析。
- 🎓 **知识学习者** — 离线囤积教程类视频，随时反复观看。

---

## 功能特性

| 功能 | 说明 |
| ---- | ---- |
| 📋 作品拉取 | 通过主页链接/handle 获取账号主页作品（标题、互动数据、作品链接） |
| 🔗 链接解析 | 逐条获取视频无水印下载直链 |
| 📥 批量下载 | 一键下载全部作品到本地 `output/` 目录 |
| 📊 数据展示 | Markdown 表格 / JSON 双格式输出，含播放量等完整互动数据 |
| 📄 分页翻页 | 支持翻页查看更多作品 |
| 📅 日期筛选 | 可按作品发布时间挑选 |
| ⚡ 速率保护 | 内置请求间隔，避免触发频率限制 |

---

## 使用指南

### 鉴权（使用前必读）

本技能调用 redfox.hk 接口，需要先获取 API Key。

前往 [红狐hub](https://redfox.hk/settings/api-keys?source=github) 获取 API Key。

```bash
# 环境变量配置（推荐）
export REDFOX_API_KEY=ak_你的密钥

# Windows PowerShell
$env:REDFOX_API_KEY="ak_你的密钥"
```

### secUserId 获取方式（账号标识获取指南）

secUserId 是 TikTok 内部用于标识账号的字符串，固定以 `MS4w` 开头（如 `MS4wLjABAAAA...`，通常 40~60 个字符）。当主页链接 / handle 无法解析（如网络受限、页面反爬）时，提供 secUserId 可直接查询。获取方式如下：

**方法一：手机 App 分享链接（最简单，推荐）**

1. 打开手机 TikTok App，搜索并进入目标账号主页
2. 点右上角「···」或分享图标 → 选择「分享」→ 点击「复制链接」
3. 粘贴出来检查：分享链接中带有 `sec_uid=MS4w...` 参数，形如：
   `https://www.tiktok.com/@xxx?sec_uid=MS4wLjABAAAA...&...`
4. 把完整分享链接直接提供给技能即可，技能会自动提取其中的 secUserId

> ⚠️ **注意：分享链接必须带有 `sec_uid=MS4w...` 参数**。普通主页链接（如 `https://www.tiktok.com/@tiktok`，链接中不含 `sec_uid=` 参数）需要访问 TikTok 页面才能解析，可能因网络受限或反爬而失败；带 `sec_uid` 参数的分享链接则可以直接查询，成功率最高。

**方法二：浏览器开发者工具一键提取**

1. 打开账号主页后按 `F12` 打开开发者工具
2. 切换到 **Console（控制台）** 标签页
3. 粘贴以下代码并回车，会直接打印出该账号的 secUserId：

```javascript
JSON.parse(document.getElementById('__UNIVERSAL_DATA_FOR_REHYDRATION__').textContent).__DEFAULT_SCOPE__['webapp.user-detail'].userInfo.user.secUid
```

**常见问题**

- **复制的 secUserId 不完整？** 请确认以 `MS4w` 开头且整串完整复制，中途截断会查询失败。
- **分享链接里没有 `sec_uid=` 参数？** 说明复制的不是标准分享链接，请重新通过「分享 → 复制链接」获取，或改用方法二。

> 核心执行流程、数据规则与接口说明详见 `references/core_workflow.md`

### 一键安装

本技能为标准 Skill 文件包，兼容所有支持 Skill 机制的 AI Agent 平台。

| 平台 | 安装方式 |
| ---- | ---- |
| Qoder | 将本技能目录放入 `.qoder/skills/` 后重启 |
| OpenClaw | 将本技能目录放入对应 skills 目录后重启 |
| WorkBuddy | 将本技能目录放入对应 skills 目录后重启 |
| Codex | 将本技能目录放入对应 skills 目录后重启 |
| Claude Code | 将本技能目录放入 `~/.claude/skills/` 后重启 |

### CLI 命令行

```bash
# 基础用法：拉取作品并解析下载链接（不下载文件）
python3 "$SKILL_PATH/scripts/tiktok-home-downloader.py" --account "https://www.tiktok.com/@tiktok"

# 也可以直接输入 @handle
python3 "$SKILL_PATH/scripts/tiktok-home-downloader.py" --account "@tiktok"

# 下载视频到本地
python3 "$SKILL_PATH/scripts/tiktok-home-downloader.py" --account "@tiktok" --download

# 指定下载目录
python3 "$SKILL_PATH/scripts/tiktok-home-downloader.py" --account "@tiktok" --download --output-dir ./my_videos

# JSON 格式输出
python3 "$SKILL_PATH/scripts/tiktok-home-downloader.py" --account "@tiktok" --json

# 多账号（逗号分隔）
python3 "$SKILL_PATH/scripts/tiktok-home-downloader.py" --accounts "@tiktok,@khaby.lame" --download

# 指定每页作品数量（默认10，最多50）
python3 "$SKILL_PATH/scripts/tiktok-home-downloader.py" --account "@tiktok" --count 20 --download

# 翻页查看更多作品
python3 "$SKILL_PATH/scripts/tiktok-home-downloader.py" --account "@tiktok" --page 2

# 按日期范围筛选作品
python3 "$SKILL_PATH/scripts/tiktok-home-downloader.py" --account "@tiktok" --date-start 2026-07-01 --date-end 2026-07-31

# 组合使用：第2页 + 日期过滤 + 下载
python3 "$SKILL_PATH/scripts/tiktok-home-downloader.py" --account "@tiktok" --page 2 --count 20 --date-start 2026-06-01 --download
```

### 参数说明

| 参数 | 说明 |
| ---- | ---- |
| `--account` | 单个 TikTok 账号（主页链接 / secUserId） |
| `--accounts` | 多个 TikTok 账号，逗号分隔 |
| `--count` | 每页作品数量（默认10，最多50） |
| `--page` | 页码（默认1） |
| `--date-start` | 起始日期 YYYY-MM-DD |
| `--date-end` | 结束日期 YYYY-MM-DD |
| `--download` | 下载视频文件到本地 |
| `--output-dir` | 下载目录（默认 `output/`） |
| `--json` | JSON 格式输出 |
| `--rate-limit` | 请求间隔秒数（默认 1.0） |
| `--api-key` | 指定 API Key |

### 依赖

| 依赖 | 安装命令 |
| ---- | ---- |
| `requests` | `pip3 install requests` |

---

## TikTok 账号输入要求

作品拉取接口通过 `secUserId` 查询。脚本支持三种输入，会自动解析：

1. **主页链接**（推荐）：如 `https://www.tiktok.com/@tiktok`，脚本会自动从页面解析出账号标识
2. **@handle**：如 `@tiktok`、`@khaby.lame`，即主页链接中 `@` 后面的部分
3. **secUserId**：`MS4w` 开头的长串，可直接使用

**重要：** 若用户只输入账号名称（如"甲亢哥""Khaby Lame"）而未提供主页链接或 handle，必须提示：

> "TikTok 账号名称存在多个重名情况，请提供准确的**TikTok 主页链接**（如 https://www.tiktok.com/@tiktok）或主页 URL 中的 **handle**（如 @tiktok）以便精准查询。"

> **handle** 是 TikTok 账号主页链接中 `@` 后面的部分，非中文昵称。

**注意：** 若用户输入的是单条视频链接（链接中含 `/video/`），需提示本技能用于提取账号主页全部作品，请改为提供账号主页链接。

**重要：** 若用户输入的 secUserId 不正确（不以 `MS4w` 开头、长度过短或格式错误），必须将「[secUserId 获取方式](#secuserid-获取方式账号标识获取指南)」章节的完整获取指引返回给用户，引导用户按方法重新获取后再查询，不要直接报错结束。

**重要：** 若用户提供的是普通主页链接（如 `https://www.tiktok.com/@tiktok`，链接中不含 `sec_uid=` 参数）或 @handle，必须提示用户：

> "分享链接需要带上 `sec_uid=MS4w...` 参数：请在手机 TikTok App 中进入该账号主页 →「分享」→「复制链接」，带 `sec_uid` 参数的分享链接可以直接查询，成功率更高。"

原因：普通主页链接 / handle 需要访问 TikTok 页面解析账号标识，可能因网络受限或反爬失败；带 `sec_uid=MS4w...` 参数的分享链接无需访问页面即可直接查询。

---

## 常见问题

**Q：如何获取 API Key？**
A：前往 [redfox.hk](https://redfox.hk/settings/api-keys?source=github) 注册获取。

**Q：下载的视频有水印吗？**
A：无水印。解析后的视频直链已去除 TikTok 水印。

**Q：支持哪些账号输入格式？**
A：支持三种：① 主页链接（如 `https://www.tiktok.com/@tiktok`）；② @handle（如 `@tiktok`）；③ secUserId（`MS4w` 开头的长串）。

**Q：为什么主页链接解析失败？**
A：部分地区的 TikTok 页面存在访问限制或反爬，脚本无法从页面提取账号标识。此时可让账号本人在主页"分享→复制链接"重新提供，或直接提供 secUserId。

**Q：为什么提示「调用频率超限」？**
A：请求过快触发了限流。可增加 `--rate-limit 2.0` 延长间隔。

**Q：图文作品能下载吗？**
A：可以。图文作品（photo 类型）会自动下载首张无水印图片，格式为 JPG/PNG/WebP。
