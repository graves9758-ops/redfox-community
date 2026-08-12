---
name: kuaishou-account-search
description: 快手账号搜索工具（广域库）。通过账号名称模糊搜索快手账号，返回 kwaiId、昵称、头像、简介等，kwaiId 可直接用于查询该账号作品列表。当用户需要按名称搜索快手账号、查找快手博主、定位达人账号、获取账号kwaiId时使用。触发词：快手账号搜索、查快手账号、找快手博主、账号名称搜索、搜快手达人。
---
# 快手账号搜索（广域库）

## 📝 简介

通过快手账号名称（profile.userName）模糊包含匹配搜索账号，快速定位目标账号并拿到 `kwaiId`，用于后续查询该账号的作品列表。

## ✨ 功能特性

| 功能模块 | 能力描述 | 核心价值 |
|---------|---------|---------|
| 名称模糊搜索 | 输入账号名称关键词即可搜索（如「人民日报」） | 无需精确 ID，输入名字即可定位 |
| 返回 kwaiId | 每个账号返回平台展示 id（kwaiId） | 直接用于 queryWorkList 查询作品 |
| 账号画像 | 昵称、头像、封面、简介一览无余 | 快速判断账号定位与内容方向 |
| 分页浏览 | 每页最多 50 条，支持多页翻看 | 同名/相似账号不遗漏 |

## 🎯 适用对象

- 🔍 **内容创作者** — 搜索同赛道账号，拆解对标账号。
- 📊 **运营 / 数据分析** — 快速定位目标账号并获取其 kwaiId。
- 🏢 **品牌 / MCN** — 筛查潜在合作达人账号。

## 🔑 鉴权

### 获取 API Key
1. 访问 [红狐Hub 官网](https://redfox.hk?source=github) 了解服务详情
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

通过快手账号名称模糊搜索定位目标账号，获取 `kwaiId` 后可直接用于查询该账号作品列表。

> 详细执行步骤、参数说明与输出格式详见 `references/core_workflow.md`

---

## ⏰ 数据时效说明

> 数据每日早上 **06:00** 更新（广域库快照）。

## 📂 相关文件

| 路径 | 用途 |
|------|------|
| `scripts/search_ks_user.py` | 账号搜索脚本（searchUser 接口） |
| `references/core_workflow.md` | 核心执行流程与输出规范 |
| `README.md` | 完整接口说明与返回字段文档 |
