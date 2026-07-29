# 短视频下载器 / video-downloader

---

## 简介

贴上短视频链接就能拿到无水印下载直链，抖音、小红书、快手、B站、YouTube、Instagram 等十多个平台都认，视频和图文都能下载，复制到浏览器就能保存。不用装插件、不用开会员，贴一个链接搞定一个视频，不会让你折腾半天还下载到带水印的版本。

**核心价值**

- **贴链即得不费劲**：贴上分享链接就能拿到无水印下载直链，一个链接搞定，不用到处找工具。
- **视频干净无水印**：返回的都是无水印视频，收藏、剪辑、二次创作都能直接拿去用。
- **十多个平台全覆盖**：抖音、小红书、快手、视频号、B站、YouTube、Instagram、X、TikTok、Threads、Facebook、Vimeo，手机分享链接和电脑网页链接都能识别。
- **图文也能下载**：除了视频，图文帖子里的所有图片也能一并下载保存，按序号自动命名。
- **开箱即用零门槛**：不需要任何配置，贴上链接就能下载，进度条实时显示，大文件也不怕。

**适用对象**

- 🎬 **创作者 / 剪辑师** — 快速保存各平台上的视频素材，用于二次创作
- 📚 **内容收藏者** — 把喜欢的视频、图文备份到本地，不怕原帖被删
- 🔍 **运营 / 研究者** — 下载竞品或热点内容，慢慢分析

---

## 功能特性

### 核心功能

- **视频解析**：粘贴任意支持平台的视频链接，一键解析出无水印视频下载链接。
- **图文下载**：支持图文类型内容，自动下载所有图片并按序号命名。
- **跨平台支持**：覆盖抖音、小红书、快手、视频号、B站、YouTube、Instagram、X、TikTok、Threads、Facebook、Vimeo 等十多个主流平台。
- **链接自适应**：手机分享短链、电脑网页链接等多种格式都能自动识别。
- **进度显示**：下载过程有进度条和百分比，大文件也不怕。

### 支持平台

| 平台 | 链接格式示例 |
|------|-------------|
| 🎵 抖音 | `https://v.douyin.com/xxxx` |
| 📕 小红书 | `http://xhslink.com/xxx` |
| 📱 快手 | `https://v.kuaishou.com/xxxx` |
| 📺 视频号 | `https://weixin.qq.com/sph/xxxx` |
| 📺 B站 | `https://b23.tv/xxxx` |
| ▶️ YouTube | `https://youtu.be/xxx` |
| 📷 Instagram | `https://www.instagram.com/p/xxx` |
| 🐦 X (Twitter) | `https://x.com/xxx/status/xxx` |
| 🎵 TikTok | `https://www.tiktok.com/@xxx/video/xxx` |
| 🧵 Threads | `https://www.threads.net/@xxx/post/xxx` |
| 📘 Facebook | `https://www.facebook.com/xxx/videos/xxx` |
| 🎬 Vimeo | `https://vimeo.com/xxxxx` |

---

## 密钥获取与安全说明

- 本技能需要使用环境变量：`REDFOX_API_KEY`。
- `REDFOX_API_KEY` 由 [红狐 hub](https://redfox.hk/settings/api-keys?source=github) (`https://redfox.hk`) 提供。
- 请前往 [红狐 hub](https://redfox.hk?source=github) 注册账号，获取 `REDFOX_API_KEY`。
- 配置设备环境变量 `REDFOX_API_KEY` 后使用本技能。
- 在提供密钥前，请先确认密钥来源、可用范围、有效期及是否支持重置/撤销。
- 禁止在代码、提示词、日志或输出文件中硬编码/明文暴露密钥。

---

## 使用指南

直接用自然语言描述需求，无需记忆命令。

### 常用说法速查

| 意图 | 示例话术 | 效果 |
| ---- | -------- | ---- |
| 下载抖音视频 | 「下载这个视频 https://v.douyin.com/xxxxxx/」 | 解析链接并下载无水印视频 |
| 保存小红书内容 | 「帮我把这条小红书存下来 http://xhslink.com/xxx」 | 解析后下载视频或图文 |
| 下载 YouTube 视频 | 「下载这条 YouTube 视频 https://youtu.be/xxx」 | 解析并下载视频文件 |
| 保存 Instagram 帖子 | 「把这个 IG 帖子存下来 https://www.instagram.com/p/xxx」 | 解析并下载视频或图文 |

### 输出示例

解析完成后，你将收到如下格式的结果：

> ✅ 下载完成！
>
> 📱 平台：抖音
> 📝 标题：视频标题
> 🎬 类型：Video
>
> 文件已保存到 ~/Downloads/QoderVideos/视频标题.mp4 (12.3 MB)

---

## 使用场景

| 场景 | 角色 | 示例问法 | 收益 |
| ---- | ---- | -------- | ---- |
| 素材收集 | 剪辑师 | 「下载这条抖音视频」 | 快速拿到无水印素材，直接进剪辑流程 |
| 内容备份 | 收藏者 | 「保存这个小红书帖子」 | 原帖删除也不怕，本地永久留存 |
| 热点分析 | 运营 | 「把这个爆款视频下下来」 | 离线反复观看，拆解爆款逻辑 |
| 跨平台存档 | 研究者 | 「下载这几个平台的视频」 | 十多个平台都能下载，一个工具搞定 |
