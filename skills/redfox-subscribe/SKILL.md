---
name: redfox-subscribe
display_name: 订阅中心
display_name_en: Subscription Hub
description: 红狐订阅中心 — 统一管理全部可订阅内容源：账号追踪、AI 日报、行业日报、热榜推送。用户说「我要订阅」时展示分组菜单并引导完成订阅；「我的订阅」汇总当前所有定时推送任务；支持一键取消订阅。当用户想要订阅日报、追踪账号更新、管理推送任务、查看或取消已有订阅时使用。触发词：订阅、我要订阅、订阅中心、我的订阅、取消订阅、日报订阅、推送管理、定时推送。
description_zh: 红狐订阅中心，统一管理账号追踪、AI日报、行业日报、热榜推送等全部可订阅内容源，支持订阅、查询、取消。
description_en: RedFox subscription hub — unified entry for all subscribable feeds: account tracking, AI daily digests, industry feeds and hot-trend pushes. Subscribe, list and cancel in one place.
category: data
version: 1.0.0
author: 红狐数据
---

# 订阅中心

红狐生态的统一订阅入口：汇总全部可订阅内容源（账号追踪 / AI 日报 / 行业日报 / 热榜推送），帮用户完成订阅、查看已有订阅、取消订阅。

---

## 角色与职责（Agent 必须遵守）

本 skill 是**路由中心**，自身不创建定时任务、不调用数据 API：

- 订阅/取消的**具体执行由目标 skill 自己的订阅流程完成**，各 skill 的订阅机制（自动化任务、`schedule_create`、脚本 `--subscribe` 参数等）一律以其自身 SKILL.md 为准
- 本 skill 只负责四件事：**展示菜单、理解意图、路由到目标 skill、汇总订阅状态**
- 禁止在本 skill 里内联任何数据拉取逻辑；禁止替目标 skill 编造订阅参数

---

## 可订阅内容源总表

> 推送时间为各 skill 的默认约定，以目标 skill 的 SKILL.md 为准。

### 一、账号追踪

| 内容源 | 目标 skill | 默认推送 | 说明 |
|---|---|---|---|
| 抖音账号作品追踪 | `douyin-subscribe` | 每日 9:00 | 最多 20 个抖音号，每日作品 HTML 报告 |
| 公众号文章追踪 | `gzh-subscribe` | 每日 6:00 | 盯梢竞对/同类/关注公众号的文章推送 |

### 二、AI 日报（每日扫描 AI 相关内容，聚类生成日报）

| 内容源 | 目标 skill | 说明 |
|---|---|---|
| 抖音 AI 日报 | `douyin-ai-feed` | 抖音 AI 作品互动量榜单 |
| 公众号 AI 日报 | `gzh-ai-feed` | AI 公众号热门文章 |
| 小红书 AI 日报 | `xiaohongshu-ai-feed` | AI 相关热门笔记 |
| 视频号 AI 日报 | `wechat-channels-ai-feed` | 视频号 AI 作品 |
| 快手 AI 日报 | `ks-ai-feed` | 快手 AI 作品 |
| B站 AI 日报 | `bili-ai-feed` | B站 AI 视频 |

### 三、行业日报

| 内容源 | 目标 skill | 说明 |
|---|---|---|
| 文旅日报（抖音/小红书/公众号/B站） | `cultural-tourism-douyin-feed` / `cultural-tourism-xiaohongshu-feed` / `cultural-tourism-wechat-feed` / `cultural-tourism-bilibili-feed` | 每日 17 点更新前一天数据，按平台任选 |
| 短剧日报（抖音/小红书/公众号/B站） | `playlet-douyin-feed` / `playlet-xiaohongshu-feed` / `playlet-wechat-feed` / `playlet-bili-feed` | 短剧行业热门内容 |
| A股舆情 | `stock-feed` | 小红书/抖音/公众号三平台股市舆情 |

### 四、热榜与爆款推送

| 内容源 | 目标 skill | 推送频率 | 说明 |
|---|---|---|---|
| 抖音热榜 | `douyin-hot-trend` | 每小时 | 热点事件 + 热度值 |
| 全网热搜聚合 | `trending-hub` | 每小时 | 抖音/微博/B站/快手/知乎/头条/百度 7 平台 |
| 抖音每日最热 TOP50 | `douyin-daily-hot` | 每日 | 支持赛道分类 |
| 公众号 10w+ 热文 | `wechat-10w-hot` | 每日 | 全领域 10w+ 文章 |
| 公众号原创热门 | `wechat-original-hot` | 每日 | 原创热门文章 |

---

## 工作流程

### 场景 1：「我要订阅」

1. **展示分组菜单**：按上表四大类分组展示（同类合并，不要把 20+ 个源平铺），每项标注推送频率；问用户想订哪一类/哪几个
2. **用户选择后，路由到目标 skill**：
   - 先读目标 skill 的 SKILL.md，**优先使用其自带的订阅机制**（如 `douyin-subscribe` 的自动化任务流程、`douyin-ai-feed` 的 `--subscribe` 参数）
   - 若目标 skill 没有订阅入口，Agent 使用当前平台的定时任务能力创建每日任务（dsh：`schedule_create` + `every_seconds`；Qoder：`automation_update` / schedule），prompt 中写明「执行 <skill-name> 技能，生成今日报告」
3. **完成后告知用户**：订阅的内容、推送时间、如何取消（「对我说取消 XX 订阅即可」）

### 场景 2：「我的订阅」

1. **列出当前生效的定时任务**（按平台能力）：
   - dsh：`schedule_list`
   - Qoder：`automation_update mode=list` / schedule 任务列表
   - 脚本级订阅：按目标 skill 文档检查其订阅状态
2. **汇总表展示**：订阅内容 / 推送频率 / 关联的任务标识
3. 若没有任何订阅，引导用户浏览订阅菜单

### 场景 3：「取消订阅」

1. 从现有任务中定位目标（按内容/名称匹配，歧义时向用户确认）
2. 执行取消：
   - dsh：`schedule_delete`
   - Qoder：删除对应自动化任务
   - 脚本级：走目标 skill 的 `--unsubscribe` 或其取消流程
3. 告知取消结果；若该任务内还有其他订阅内容（如多账号），只移除对应项并保留任务

---

## 交互规则

- **静默执行**：中间步骤（读 SKILL.md、查询任务列表、创建/删除任务）不向用户输出过程提示，只展示最终结果
- **高频确认**：订阅每小时级推送（热榜类）前，明确告知推送频率并征得确认
- **账号类订阅**（如抖音号追踪）需要用户提供具体账号时，按其目标 skill 的要求索取（如抖音号而非昵称）
- 用户描述模糊时（如「订阅 AI 日报」没说平台），列出 AI 日报类的 6 个平台供其选择，不要自行假设
