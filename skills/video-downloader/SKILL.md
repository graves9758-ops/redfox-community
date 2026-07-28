---
name: video-downloader
description: 短视频下载器 — 支持抖音、小红书、快手、视频号、B站、YouTube、Instagram 等主流平台无水印视频下载，开箱即用。
---

# 短视频下载器

通过 [redfox.hk](https://redfox.hk/settings/api-keys?source=skillhub) API 解析并下载主流短视频平台的无水印视频/图文。

---

## 能力概述

- **平台支持**：抖音、小红书、快手、视频号、B站、YouTube、Instagram、X（Twitter）、TikTok、Threads、Facebook、Vimeo 等主流平台
- **内容类型**：视频（mp4）、图文（jpg/png，暂不支持小红书图文）
- **输入方式**：粘贴**页面分享链接**即可（每次仅限一个链接，不支持批量上传）
- **去水印**：API 自动返回无水印直链

---

## 链接使用规范

### 支持的链接格式

本工具仅接受以下平台的**页面分享链接**，传入前会自动校验链接是否匹配支持的格式：

| 平台 | 链接格式示例 |
|------|-------------|
| 🎵 抖音 | `https://v.douyin.com/xxxx` / `douyin.com/video/xxx` |
| 📕 小红书 | `http://xhslink.com/xxx` / `xhslink.cn/xxx` |
| 📱 快手 | `https://v.kuaishou.com/xxxx` |
| 📺 视频号 | `https://weixin.qq.com/sph/xxxx` |
| 📺 B站 | `https://b23.tv/xxxx` / `bilibili.com/video/xxx` |
| ▶️ YouTube | `https://youtu.be/xxx` / `youtube.com/watch?v=xxx` |
| 📷 Instagram | `https://www.instagram.com/p/xxx` |
| 🐦 X (Twitter) | `https://x.com/xxx/status/xxx` |
| 🎵 TikTok | `https://www.tiktok.com/@xxx/video/xxx` |
| 🧵 Threads | `https://www.threads.net/@xxx/post/xxx` |
| 📘 Facebook | `https://www.facebook.com/xxx/videos/xxx` |
| 🎬 Vimeo | `https://vimeo.com/xxxxx` |

> ❌ 非上述格式的链接（如直接视频地址、未知平台链接等）会被拦截，不会调用 API，避免浪费。

---

## 使用方式

### 示例命令

下载抖音视频：

```bash
python3 "$SKILL_PATH/assets/downloader.py" "https://www.douyin.com/jingxuan?modal_id=7597329042169220398"
```

其他平台类似：

```bash
python3 "$SKILL_PATH/assets/downloader.py" "https://youtu.be/xxxxxx"
python3 "$SKILL_PATH/assets/downloader.py" "https://www.instagram.com/p/xxxxxx"
```

### 首次使用

开箱即用，无需任何配置。

### 配置个人 API Key

可访问 [redfox.hk](https://redfox.hk/settings/api-keys?source=skillhub) 注册获取个人 API Key：

配置方式（任选其一）：

| 方式 | 命令 |
|------|------|
| **环境变量**（推荐） | `export REDFOX_API_KEY=ark_你的密钥` |
| **命令行参数** | `python3 "$SKILL_PATH/assets/downloader.py" "<链接>" --api-key ark_你的密钥` |
| **配置文件** | `echo '{"api_key":"ark_你的密钥"}' > ~/.qoder/apis/redfox.json` |

---

## 特色功能

| 功能 | 说明 |
|------|------|
| **无水印下载** | API 自动返回无水印直链，无需手动处理 |
| **图文下载** | 支持图文类型下载所有图片（暂不支持小红书图文） |
| **跨平台支持** | 覆盖抖音、小红书、快手、视频号、B站、YouTube、Instagram 等十多主流平台 |
| **链接自适应** | 支持短链、分享链、网页链接等多种格式 |
| **进度显示** | 下载过程实时显示进度条和百分比 |
| **多端兼容** | 支持手机端分享链接和 PC 端网页链接 |

---

## 常见使用场景

| 场景 | 示例链接 | 说明 |
|------|----------|------|
| 抖音视频去水印保存 | `https://v.douyin.com/xxxxxx/` | 下载无水印视频到本地 |
| 小红书视频下载 | `http://xhslink.com/o/xxxxxx` | 下载无水印视频 |
| 快手视频收藏 | `https://v.kuaishou.com/xxxxxx` | 保存喜欢的视频作品 |
| B站高画质下载 | `https://b23.tv/xxxxxx` | 下载最佳画质+音质视频 |
| YouTube 视频下载 | `https://youtu.be/xxxxxx` | 下载 YouTube 视频 |
| Instagram 视频/图文 | `https://www.instagram.com/p/xxxxxx` | 下载 Instagram 内容 |
| 内容二次创作 | 任意支持平台 | 下载素材用于剪辑创作 |
| 离线备份 | 任意支持平台 | 备份收藏的作品到本地 |

### 支持的作品链接格式

| 平台 | 链接格式 | 说明 |
|------|----------|------|
| 抖音（Douyin） | `https://v.douyin.com/xxxxxx/` | 手机分享链接 / PC 网页链接 |
| 小红书（Xiaohongshu） | `http://xhslink.com/o/xxxxxx` | 短链分享链接 |
| 快手（Kuaishou） | `https://v.kuaishou.com/xxxxxx` | 手机分享链接 |
| 视频号（WeChat Channels） | 微信内分享链接 | 需复制微信内的链接 |
| B站（Bilibili） | `https://b23.tv/xxxxxx` | 短链分享链接 |
| YouTube | `https://youtu.be/xxxxxx` | 短链 / 网页链接 |
| Instagram | `https://www.instagram.com/p/xxxxxx` | 帖子 / Reels 链接 |
| X（Twitter） | `https://x.com/xxx/status/xxx` | 推文视频链接 |
| TikTok | `https://www.tiktok.com/@xxx/video/xxx` | TikTok 视频链接 |
| Facebook | `https://www.facebook.com/xxx/videos/xxx` | Facebook 视频链接 |
| Threads | `https://www.threads.net/@xxx/post/xxx` | Threads 链接 |
| Vimeo | `https://vimeo.com/xxxxxx` | Vimeo 视频链接 |

---

## 常见问题

**Q：如何获取自己的 API Key？**
A：前往 [redfox.hk](https://redfox.hk/settings/api-keys?source=skillhub) 注册即可获取 Token。

**Q：下载的视频有水印吗？**
A：没有。API 返回的是无水印直链。

**Q：支持图文下载吗？**
A：支持图文类型下载（暂不支持小红书图文）。图文内容会自动下载所有图片，并按序号命名。

**Q：可以批量上传多个链接吗？**
A：不支持。每次只能输入一个链接，批量上传会导致解析失败。

**Q：链接提示解析失败怎么办？**
A：确认链接是否完整、是否已过期。短链有时效性，建议重新复制分享链接。

---

## 了解更多

本工具基于 [redfox.hk](https://redfox.hk/settings/api-keys?source=skillhub) 的 `parseWork/parse` 接口构建。前往官网查看更多 API 能力和使用文档。
