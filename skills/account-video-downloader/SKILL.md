***
name: account-video-downloader
description: 多平台账号主页视频提取器 — 输入平台名称和账号id/链接，自动拉取抖音/快手/B站/YouTube 四大平台主页作品，解析下载链接，支持批量下载。适用场景：竞品账号内容拆解与逐帧学习、收藏喜欢的创作者全部作品避免被删、批量搬运素材二次剪辑创作、保存自己账号作品做本地备份防丢失、课程/教程类视频离线囤货反复看、达人合作前快速拉取对方作品做背调分析。触发词：主页视频下载、批量下载视频、账号视频提取、快手主页下载、B站视频提取、YouTube频道下载、视频保存、无水印下载、竞品视频下载、博主视频备份。
--------------------------------------------------------------------------------------------------------------------------------------------------------

# 多平台账号主页视频提取器

> 输入平台 + 账号 → 拉取作品列表 → 解析下载链接 → 一键下载到本地

***

## 简介

多平台账号主页视频批量下载工具。支持 **抖音、快手、B站、YouTube** 四大平台，只需提供平台名称和账号标识，自动拉取该账号近期作品列表，逐条解析视频/图文下载直链，支持一键批量下载到本地。

***

## 功能特性

| 功能      | 说明                               |
| ------- | -------------------------------- |
| 📋 作品拉取 | 通过账号获取主页近期作品（标题、互动数据、作品链接）    |
| 🔗 链接解析 | 逐条调用解析接口，获取视频/图文下载直链              |
| 📥 批量下载 | 一键下载全部作品（视频+图文）到本地 `output/` 目录   |
| 📊 数据展示 | Markdown 表格 / JSON 双格式输出，含完整互动数据 |
| 📄 分页翻页 | 支持翻页查看更多作品                       |
| 📅 日期筛选 | 可按作品发布时间挑选                       |
| 🌐 多平台  | 一个工具覆盖抖音/快手/B站/YouTube 四大平台 |

***

## 支持平台

| --platform | 平台 | 账号标识 | 说明 |
|:---|:---|:---|:---|
| `douyin`   | 抖音 | 抖音号 | 如 `Fish688688` |
| `kuaishou` | 快手 | 快手号 | 如 `Fish688688` |
| `bilibili` | 哔哩哔哩 | 主页链接（accountUrl） | 如 `https://space.bilibili.com/123456` |
| `youtube` | YouTube | 频道 URL（channel） | 如 `https://www.youtube.com/@channel` |

---

## API 说明

本 Skill 调用 redfox.hk 接口，每个平台分两步：

| 步骤 | 接口路径 | 说明 |
|------|---------|------|
| 1. 拉取作品 | `POST /story/api/{platform}/...` | 根据账号标识获取作品列表 |
| 2. 解析下载 | `POST /story/api/parseWork/videoDownload/{platform}` | 根据作品链接获取下载直链 |

### 认证

前往 [红狐hub](https://redfox.hk/settings/api-keys?source=github) 获取 API Key，设为环境变量：

```bash
# macOS / Linux
export REDFOX_API_KEY=ak_你的密钥

# Windows PowerShell
$env:REDFOX_API_KEY="ak_你的密钥"
```

***

## 使用方式

### CLI 命令行

```bash
# 抖音：基础用法
python3 "$SKILL_PATH/scripts/main.py" --platform douyin --account "Fish688688"

# 快手：基础用法
python3 "$SKILL_PATH/scripts/main.py" --platform kuaishou --account "kwaiId"

# B站：拉取作品并解析下载链接（不下载文件）
python3 "$SKILL_PATH/scripts/main.py" --platform bilibili --account "https://space.bilibili.com/123456"

# YouTube：下载视频到本地
python3 "$SKILL_PATH/scripts/main.py" --platform youtube --account "https://www.youtube.com/@channel" --download

# YouTube：指定下载目录
python3 "$SKILL_PATH/scripts/main.py" --platform youtube --account "https://www.youtube.com/@channel" --download --output-dir ./my_videos

# 指定作品数量（默认10，最多50）
python3 "$SKILL_PATH/scripts/main.py" --platform bilibili --account "MID" --count 20 --download

# 翻页查看更多作品
python3 "$SKILL_PATH/scripts/main.py" --platform kuaishou --account "用户ID" --page 2

# 按日期范围筛选作品
python3 "$SKILL_PATH/scripts/main.py" --platform bilibili --account "MID" --date-start 2026-07-01 --date-end 2026-07-31

# 多账号（逗号分隔）
python3 "$SKILL_PATH/scripts/main.py" --platform bilibili --accounts "MID1,MID2" --download

# 组合使用：第2页 + 日期过滤 + 下载
python3 "$SKILL_PATH/scripts/main.py" --platform bilibili --account "MID" --page 2 --count 20 --date-start 2026-06-01 --download
```

### 参数说明

| 参数             | 说明                 |
| -------------- | ------------------ |
| `--platform`   | 目标平台（必填，见上表）       |
| `--account`    | 单个账号标识             |
| `--accounts`   | 多个账号标识，逗号分隔        |
| `--count`      | 拉取作品数量（默认10，最多50）  |
| `--page`       | 页码（默认1）            |
| `--date-start` | 起始日期 YYYY-MM-DD    |
| `--date-end`   | 结束日期 YYYY-MM-DD    |
| `--download`   | 下载视频文件到本地          |
| `--output-dir` | 下载目录（默认 `output/`） |
| `--json`       | JSON 格式输出          |
| `--rate-limit` | 请求间隔秒数（默认 1.0） |

### 依赖

| 依赖         | 安装命令                    |
| ---------- | ----------------------- |
| `requests` | `pip3 install requests` |

***

## 账号标识要求

不同平台对账号标识有不同要求，**必须提供各平台的唯一标识**：

| 平台 | 要求 | URL 支持 | 获取方式 |
|:---|:---|:---|:---|
| B站 | 主页链接（accountUrl） | ✅ 支持 | 直接复制个人空间页 URL |
| YouTube | 频道 URL（channel） | ✅ 支持 | 直接复制频道页 URL |
| 抖音 | 抖音号（uniqueName） | ❌ 不支持 | 抖音 APP → 目标主页 → 头像下方「抖音号：xxx」字段 |
| 快手 | 账号 ID（kwaiId） | ❌ 不支持 | 快手 APP → 目标主页 → 昵称下方显示的 ID |

> ⚠️ **抖音、快手不支持主页链接！** 如果用户粘贴了 URL，必须提示用户提供上述唯一标识。

**重要：** 若用户只输入账号名称而未提供唯一标识，必须提示用户提供准确的唯一标识。

> 📸 **抖音号获取方式：** 打开抖音 APP → 进入目标用户主页 → 在头像下方、粉丝数据下方可看到「抖音号：xxx」字段。若用户不确定抖音号在哪，可展示示意截图（红框标注「抖音号」位置）帮助用户定位。

***

## Agent 集成指南

### 触发词

* 主页视频下载 / 批量下载视频 / 账号视频提取
* 抖音下载 / 抖音视频提取 / 下载抖音作品
* B站视频提取 / B站视频下载 / 哔哩哔哩视频下载
* YouTube频道下载 / YouTube视频提取
* 帮我下载 xxx 的主页视频

### Agent 执行流程

```
Step 1: 确认用户意图、平台与账号标识
  - 从用户输入中识别目标平台（抖音/快手/B站/YouTube）
  - 若用户未明确平台，询问：「你想下载哪个平台的视频？」
  - 确认账号标识格式正确，若用户提供的是中文昵称，提示提供唯一 ID

Step 2: 识别用户输入的时间范围（如有）
  - 若用户提到了作品时间范围，自动识别并转换为 --date-start / --date-end：
    - "7.1~7.20" → --date-start 2026-07-01 --date-end 2026-07-20
    - "7月1日到7月20日" → --date-start 2026-07-01 --date-end 2026-07-20
    - "最近一周" → 当前日期往前推 7 天
    - "上个月" → 上个月 1 日到上个月最后一天
    - "7月份的作品" → --date-start 2026-07-01 --date-end 2026-07-31
  - 日期格式固定为 YYYY-MM-DD，年份默认为当前年份
  - 若用户要求"继续"/"下一页"，添加 --page N

Step 3: 调用脚本拉取作品 + 解析下载链接
  python3 "$SKILL_PATH/scripts/main.py" --platform <platform> --account "<id>"

Step 4: 展示结果 + 询问翻页
  - 展示 Markdown 表格，含可点击的作品链接和下载链接
  - 若有失败：提示「可能是用户已删除该视频，如需数据核查可联系工作人员邮箱 redfoxdata@proton.me 处理」
  - 若可翻页：告诉用户「还有更多作品，是否需要翻看下一页？」，输入下一页翻页
  - 提示用户支持按时间范围提取作品

Step 5: 询问用户是否需要批量下载
  - 使用 AskUserQuestion：「是否需要将能下载的视频批量下载到本地？」
  - 选项：「下载到本地」/「只看链接即可」

Step 6: 用户确认后执行下载
  python3 "$SKILL_PATH/scripts/main.py" --platform <platform> --account "<id>" --download
  - 告知用户文件保存路径
```

### Agent 输出规范

解析完成后按以下格式输出（自然语言风格，面向普通用户）。

#### ⛔ 强制规则：禁止简化输出

> **Agent 必须原样展示脚本返回的完整表格，禁止以下行为：**
>
> * ❌ 禁止删除或合并任何列（发布时间、作品、赞、评论、收藏、分享、资源下载 缺一不可）
>
> * ❌ 禁止省略翻页提示行
>
> * ❌ 禁止省略时间范围筛选提示（"💡 支持输入想提取的作品时间范围…"）
>
> * ❌ 禁止省略下载询问提示（"💾 需要将这 X 条作品批量下载到本地吗？"）
>
> * ❌ 禁止用「...」或摘要代替完整表格内容
>
> * ✅ 必须逐行展示所有作品的完整信息（含资源下载链接）

#### 输出模板

```markdown
## 📥 {平台}视频下载 — @账号名（粉丝: X）

当前是**第 1 页**，共 10 条作品 | 还有更多作品，输入 `--page 2` 翻看下一页

| # | 发布时间 | 作品 | 赞 | 评论 | 收藏 | 分享 | 资源下载 |
|---|----------|------|-----|------|------|------|------|
| 1 | 07-28 | [作品标题](链接) | 5.2k | 67 | 689 | 5.8k | [🎬视频](...) · [🖼封面](...) · [🎵音频](...) |
| 2 | 07-24 | [作品标题2](链接) | 3.1k | 22 | 136 | 865 | [🖼封面](...) |
| 3 | … | … | … | … | … | … | … |

**合计：** 10 条作品，8 条可下载，2 条下载失败

> ⚠️ 下载失败的视频可能是用户已删除该视频，如需数据核查可联系工作人员邮箱 **redfoxdata@proton.me** 处理。

> 💡 需要提取特定时间范围的作品？直接告诉我时间范围即可，如「7.1~7.20」「最近一周」

> 💾 需要将这 X 条作品批量下载到本地吗？直接告诉我即可。
```

平台名称会根据实际平台自动替换（快手 / B站 / YouTube）。

***

## 常见问题

**Q：如何获取 API Key？**
A：前往 [redfox.hk](https://redfox.hk/settings/api-keys?source=github) 注册获取。

**Q：下载的视频有水印吗？**
A：无水印。API 返回的视频/图文直链已去除平台水印。

**Q：图文作品能下载吗？**
A：可以。图文作品（幻灯片、相册类）会自动下载首张图片，格式为 JPG/PNG/WebP。

**Q：为什么提示「调用频率超限」？**
A：API 返回 code=3108 时表示请求过快触发了限流。可增加 `--rate-limit 2.0` 延长间隔。

**Q：支持哪些平台？**
A：抖音、快手、B站（哔哩哔哩）、YouTube 四大平台。

**Q：各平台账号标识从哪里获取？**
A：抖音需要抖音号（如 JCLjiangchenglan），快手需要账号 ID / kwaiId（账号名称下方），B站需要主页链接，YouTube 需要频道 URL。
