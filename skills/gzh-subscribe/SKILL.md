---
name: gzh-subscribe
description: 微信公众号文章订阅 — 每天 6 点，盯梢竞对、同类、关注账号，一份你订阅的公众号文章推送。
---

# 公众号订阅追踪

你的公众号内容雷达。订阅竞对、同类和关注账号，自动抓取每日发文，以清晰的表格形式展示：发文日期、作者、标题、简介、阅读数、点赞数、发文链接，一键生成 HTML 日报。

---

## 首次使用

**首次使用需先配置 API Key**

前往 [redfox.hk](https://redfox.hk/settings/api-keys?source=github) 注册获取 API Key，三种配置方式任选其一：

| 配置方式 | 说明 | 命令 |
|----------|------|------|
| **环境变量**（推荐） | 设置一次，全局生效 | `export REDFOX_API_KEY=ak_你的密钥` |
| **命令行参数** | 临时使用 | `python3 "$SKILL_PATH/assets/subscribe.py" fetch --api-key ak_你的密钥` |
| **配置文件** | 持久化存储 | `echo '{"api_key":"ak_你的密钥"}' > ~/.qoder/apis/redfox.json` |

配置完成后，即可使用：

```bash
# 1. 添加订阅（需提供账号 ID，支持三种格式）
# 以「红狐数据」公众号为例：
python3 "$SKILL_PATH/assets/subscribe.py" add "红狐数据" --id "redfoxdata1" --category "关注账号"

# 也可用 wxId 或 bizInfo 格式
python3 "$SKILL_PATH/assets/subscribe.py" add "红狐数据" --id "gh_53301f7745f3"
python3 "$SKILL_PATH/assets/subscribe.py" add "红狐数据" --id "MzY4ODI4ODc2MA=="

# 2. 拉取发文
python3 "$SKILL_PATH/assets/subscribe.py" fetch

# 3. 生成并打开日报
python3 "$SKILL_PATH/assets/subscribe.py" report
```

HTML 日报保存在 `~/Downloads/QoderGzhReports/` 目录，自动在浏览器中打开。

---

## 后续使用

| 配置方式 | 说明 | 命令 |
|----------|------|------|
| **环境变量**（推荐） | 设置一次，全局生效 | `export REDFOX_API_KEY=ak_你的密钥` |
| **命令行参数** | 临时使用 | `python3 "$SKILL_PATH/assets/subscribe.py" fetch --api-key ak_你的密钥` |
| **配置文件** | 持久化存储 | `echo '{"api_key":"ak_你的密钥"}' > ~/.qoder/apis/redfox.json` |

---

## 功能特点

- **收件箱式订阅**：像订阅 Newsletter 一样订阅公众号，最多 20 个，需提供账号 ID（支持 account / wxId / bizInfo 三种格式）
- **每日 6 点准时推送**：一键安装定时任务，每天早上一份精排日报，自动打开浏览器（广域库 T+1，拉取昨天及近 7 天发文）
- **三类分组管理**：「竞对账号」盯对手、「同类账号」找灵感、「关注账号」追大神
- **关键数据一屏尽览**：发文日期、标题、简介、阅读数、点赞数，原文链接一键直达
- **终端 + 日报双模式**：命令行实时查表，HTML 日报适合分享存档

> **数据覆盖说明**：本 Skill 基于红狐广域库，覆盖范围更广。
> 如在广域库中仍搜不到目标账号，可联系红狐数据获取定制支持：
> **redfoxdata@proton.me**

---

## 适用场景

### 每日晨报
开启 `--subscribe`，每天 06:00 自动拉取所有订阅公众号的发文，
生成 HTML 日报并自动打开浏览器。像收邮件一样，每天早上收到一份
专属的公众号文章推送。

### 竞对监控
把竞品公众号加入「竞对账号」分类，随时 `fetch` 一屏看完他们的
最新发文——标题、简介、阅读数、点赞数、文章链接，表格一目了然。

### 特别关注
把行业大号、灵感来源加入「关注账号」分类，日报中优先展示，
有新发文第一时间掌握动态。

### 内容加工
拉取到的文章数据可以配合 LLM 进一步使用：
- **摘要改写**：喂给 LLM 生成自定义摘要或分析观点
- **风格仿写**：模仿目标公众号的文风输出学习笔记
- **数据沉淀**：日报 HTML 可导出为 PDF / Markdown 存档

---

## 使用方式

### 管理订阅

> **账号 ID 说明**：新接口基于红狐广域库，必须提供账号 ID 才能查询。
> 支持以下三种格式（三选一即可），以「红狐数据」公众号为例：
>
> - **account** — 公众号标识，最容易获取，如 `redfoxdata1`
> - **wxId** — 微信号，格式 `gh_` 开头，仅限**自己的公众号后台**查看，如 `gh_53301f7745f3`
> - **bizInfo** — 文章链接中的 biz 编码，通过**手机端默认浏览器**打开任意文章，从链接地址中提取，如 `MzY4ODI4ODc2MA==`
>
> 三种格式提供任意一种即可，推荐优先使用 account 格式。

```bash
# 添加订阅（账号名称 + 账号 ID 均为必填）
python3 "$SKILL_PATH/assets/subscribe.py" add "公众号名称" --id "redfoxdata1" --category "竞对账号"

# 支持三种账号 ID 格式
python3 "$SKILL_PATH/assets/subscribe.py" add "公众号名称" --id "gh_53301f7745f3"
python3 "$SKILL_PATH/assets/subscribe.py" add "公众号名称" --id "MzY4ODI4ODc2MA=="

# 取消订阅（支持用名称或 ID）
python3 "$SKILL_PATH/assets/subscribe.py" remove "公众号名称"
python3 "$SKILL_PATH/assets/subscribe.py" remove "WebNotes"

# 查看所有订阅
python3 "$SKILL_PATH/assets/subscribe.py" list
```

### 拉取发文

```bash
# 拉取所有订阅公众号的最新发文
python3 "$SKILL_PATH/assets/subscribe.py" fetch

# 指定日期
python3 "$SKILL_PATH/assets/subscribe.py" fetch --date 2026-05-26

# 仅查看终端表格（不生成日报）
python3 "$SKILL_PATH/assets/subscribe.py" fetch --no-report
```

### 生成日报

```bash
# 生成今日 HTML 日报
python3 "$SKILL_PATH/assets/subscribe.py" report

# 指定日期和输出目录
python3 "$SKILL_PATH/assets/subscribe.py" report --date 2026-05-26 --output-dir ~/Desktop
```

### 每日自动推送

```bash
# 开启每日 06:00 自动推送
python3 "$SKILL_PATH/assets/subscribe.py" --subscribe

# 取消每日自动推送
python3 "$SKILL_PATH/assets/subscribe.py" --unsubscribe
```

### 参数说明

| 命令 | 参数 | 说明 |
|------|------|------|
| `add` | `accountName` | 公众号名称（必填） |
| | `--id` | 账号 ID（必填），支持 account / wxId / bizInfo |
| | `--category` | 分类标签：竞对账号 / 同类账号 / 关注账号 |
| `remove` | `identifier` | 公众号名称 或 公众号 ID |
| `list` | — | 列出所有订阅 |
| `fetch` | `--date` | 指定日期 YYYY-MM-DD（默认今天） |
| | `--no-report` | 仅终端展示，不生成日报 |
| `report` | `--date` | 指定日期 YYYY-MM-DD（默认今天） |
| | `--output-dir` | 输出目录（默认 ~/Downloads/QoderGzhReports） |
| 全局 | `--api-key` | 指定 API Key |
| | `--subscribe` | 安装每日定时任务（06:00） |
| | `--unsubscribe` | 卸载定时任务 |

### 依赖安装

| 依赖 | 安装命令 |
|------|----------|
| `requests` | `pip3 install requests` |

---

## 常见问题

**Q：账号 ID 是什么？支持哪些格式？**
A：本 Skill 使用红狐广域库，**必须提供账号 ID** 才能查询。支持三种格式（三选一即可）：
- **account**：公众号标识，最容易获取（如 `redfoxdata1`）
- **wxId**：微信号，格式 `gh_` 开头，仅限**自己的公众号后台**查看（如 `gh_53301f7745f3`）
- **bizInfo**：文章链接中的 biz 编码，通过**手机端默认浏览器**打开任意文章，从链接地址中提取（如 `MzY4ODI4ODc2MA==`）

提供其中任意一种即可，推荐优先使用 account 格式。

**Q：最多能订阅多少个公众号？**
A：最多 20 个。这是保证 API 调用效率和合理使用的上限。

**Q：拉取频率有限制吗？**
A：每次 fetch 按订阅数消耗 API 额度。建议开启每日自动推送，而非频繁手动拉取。

**Q：日报存在哪？**
A：默认 `~/Downloads/QoderGzhReports/`，文件名格式 `公众号日报_2026-05-27.html`。

**Q：怎么自定义日报样式？**
A：修改 `$SKILL_PATH/assets/report_template.html` 中的 CSS 变量即可换色、换字体。

**Q：分类标签有什么用？**
A：日报中会按分类分组展示（竞对账号、同类账号、关注账号），便于快速区分不同目的的订阅。不指定分类则统一归入「关注账号」。

**Q：和 RSS 阅读器有什么区别？**
A：专为微信公众号设计。微信没有 RSS，本 Skill 直接获取公众号发文数据，还能看到阅读数、点赞数等微信独有的互动指标。

**Q：文章内容可以改写或仿写吗？**
A：日报展示的是标题+简介+数据。如需对文章做摘要改写或风格仿写，可将拉取到的数据配合 LLM 进一步处理。

**Q：额度用完了怎么办？**
A：前往 [redfox.hk](https://redfox.hk/settings/api-keys?source=github) 注册获取 API Token。

**Q：为什么有些公众号查不到？**
A：本 Skill 使用红狐**广域库**，覆盖范围较广。如确认账号 ID 正确但仍查不到，请联系红狐数据获取定制支持：**redfoxdata@proton.me**。

---

## 获取方式

本 Skill 可在以下平台找到：

- [SkillHub](https://skillhub.cn)
- [ClawHub](https://clawhub.com)
- [GitHub](https://github.com)
- [GitHub](https://github.com)
