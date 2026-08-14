---
name: bilibili-portfolio-search
description: B站账号作品列表实时查询工具。根据B站UP主的UID获取该UP主发布的最新视频作品列表，支持游标翻页浏览更多作品。当用户想查看某个B站UP主的作品列表、B站账号视频、UP主投稿列表时使用。
---

# B站搜账号下作品集

## 📝 简介

B站账号作品列表实时查询工具，根据B站UP主的UID获取该UP主最新发布的视频作品列表，返回实时数据（非缓存/历史数据）。支持游标翻页浏览更多作品。

## ✨ 功能特性

| 功能模块 | 能力描述 | 核心价值 |
|---------|---------|---------|
| 实时查询 | 输入UID实时获取UP主作品列表 | 获取非缓存的实时数据 |
| 游标翻页 | 支持cursor游标逐页浏览 | 深入浏览UP主更多作品 |
| 数据排序 | 返回结果按播放量降序排列 | 快速定位爆款作品 |

## 🚀 一键安装

### 前置条件

- 已获取红狐 hub 的 API Key（`REDFOX_API_KEY`）

### 获取 API Key

请前往 [红狐hub](https://redfox.hk/settings/api-keys?source=github) 获取 API KEY

### 配置 API Key

方案1: 以 Qoder 为例，将 REDFOX_API_KEY 添加到 `~/.openclaw/openclaw.json` 中：

```bash
{ "env": { "REDFOX_API_KEY": "ak_xxxx..." } }
```

方案2: 终端配置

```bash
export REDFOX_API_KEY="ak_xxxx..."
```

## 📖 使用指南

直接用自然语言描述需求即可，例如：

- 「查一下UP主 946974 的作品列表」
- 「帮我看看这个B站账号的视频：bilibili.com/space/12345678」
- 「翻页，看下一页作品」

## 🔄 工作流程

> 核心执行流程详见 `references/core_workflow.md`