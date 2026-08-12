---
name: kuaishou-text-extract
description: 快手视频提文案工具。通过快手视频链接提取视频口播文案，自动完成「提交任务+轮询结果」，返回完整文案与带时间戳的分句，支持任务ID续查。当用户需要提取快手视频文案、获取口播稿、转写视频文字稿、复制爆款视频脚本时使用。触发词：视频提文案、提取文案、口播文案、视频文字稿、文案提取、转写视频、爆款脚本。
---
# 快手视频提文案

## 📝 简介

通过快手视频链接提取口播文案（ASR 转写），脚本自动完成「提交任务 → 轮询 → 取结果」两步流程，返回完整文案与带时间戳的分句，支持任务 ID 续查。

## ✨ 功能特性

| 功能模块 | 能力描述 | 核心价值 |
|---------|---------|---------|
| 一键提文案 | 提交视频链接自动完成提交+轮询 | 口播稿一键转文字 |
| 完整文案 | 返回全部片段拼接的完整文案 text | 直接复刻选题脚本 |
| 时间戳分句 | 带时间戳的分句数组（text/start/end） | 字幕/剪辑精准定位 |
| 任务续查 | 支持 --task-id 查询已有任务结果 | 中途超时可续查不丢任务 |
| 状态兼容 | 兼容 succeeded/failed/processing 等多状态 | 轮询过程稳定可靠 |

## 🎯 适用对象

- 🔍 **内容创作者** — 复刻爆款视频的口播脚本，拆解选题结构。
- 📊 **运营 / 数据分析** — 快速转写视频内容，评估文案质量。
- 🎬 **剪辑 / 字幕** — 用时间戳分句快速生成字幕稿。

## 🔑 鉴权

### 获取 API Key
1. 访问 [红狐Hub 官网](https://redfox.hk/?source=github) 了解服务详情
2. 前往 [注册页面](https://redfox.hk/login?source=github) 注册账号
3. **新注册用户将获赠免费积分**，可立即开始使用 API 服务
4. 注册登录后，在个人中心获取 API Key，格式为 `ak_xxxxxxxx`

### 配置 API Key
- `REDFOX_API_KEY` 从环境变量获取，格式 `ak_xxxxxxxx`
- 若未设置，提示用户自行配置：`export REDFOX_API_KEY=<你的apikey>`；若用户不会配置，Agent应主动帮用户设置：
  - **macOS/Linux**：将 `export REDFOX_API_KEY=<值>` 追加到 `~/.zshrc`（zsh）或 `~/.bashrc`（bash），然后 `source` 对应文件使其全局生效
  - **Windows**：使用 `[Environment]::SetEnvironmentVariable("REDFOX_API_KEY", "<值>", "User")` 设置用户级永久环境变量（需重启终端生效）
  - 配置完成后应验证：`echo $REDFOX_API_KEY`（macOS/Linux）或 `echo %REDFOX_API_KEY%`（Windows），确保换一个skill也能读取到


## 🔄 使用指南

通过快手视频链接提取口播文案，自动完成「提交任务 → 轮询 → 取结果」流程，返回完整文案与带时间戳的分句，支持任务 ID 续查。

> 详细执行步骤、参数说明与输出格式详见 `references/core_workflow.md`

---

## 📂 相关文件

| 路径 | 用途 |
|------|------|
| `scripts/extract_ks_text.py` | 视频提文案脚本 |
| `references/core_workflow.md` | 核心执行流程与输出规范 |
| `README.md` | 完整接口说明与返回字段文档 |
