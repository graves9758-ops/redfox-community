# Video Downloader / video-downloader

---

## Introduction

Paste a short video link and get watermark-free download URLs instantly — Douyin, Xiaohongshu, Kuaishou, Bilibili, YouTube, Instagram, and 12+ platforms all recognized. Videos and image posts can all be downloaded. Copy the link into your browser to save. No plugins, no subscriptions — one link does it all, and you won't end up with a watermarked version.

**Core Value**

- **Paste and go**: paste a share link and get watermark-free download URLs right away — one link does it all, no need to hunt for different tools.
- **Clean, watermark-free**: every returned video is watermark-free, ready for collecting, editing, or remixing.
- **12+ platforms covered**: Douyin, Xiaohongshu, Kuaishou, WeChat Channels, Bilibili, YouTube, Instagram, X, TikTok, Threads, Facebook, Vimeo — mobile share links and desktop web links all recognized.
- **Image posts too**: beyond videos, all images in a post can be downloaded and saved together with sequential naming.
- **Paste and download with progress**: after configuring your API Key, paste a link and download. Progress bar shown in real time, even for large files.

**Who Is It For**

- 🎬 **Creators / Editors** — quickly save video clips from any platform for secondary creation
- 📚 **Content Collectors** — back up favorite videos and image posts locally, safe from deleted content
- 🔍 **Operators / Researchers** — download competitor or trending content for analysis

---

## Features

### Core Features

- **Video Parsing**: paste a video link from any supported platform to parse out watermark-free download URLs.
- **Image Download**: supports image-type posts, automatically downloads all images with sequential naming.
- **Cross-Platform Support**: covers Douyin, Xiaohongshu, Kuaishou, WeChat Channels, Bilibili, YouTube, Instagram, X, TikTok, Threads, Facebook, Vimeo, and more.
- **Link Auto-Detection**: mobile share links, desktop web links, and various formats are all auto-recognized.
- **Progress Display**: download progress bar and percentage shown in real time, even for large files.

### Supported Platforms

| Platform | Link Format Example |
|----------|-------------------|
| 🎵 Douyin | `https://v.douyin.com/xxxx` |
| 📕 Xiaohongshu | `http://xhslink.com/xxx` |
| 📱 Kuaishou | `https://v.kuaishou.com/xxxx` |
| 📺 WeChat Channels | `https://weixin.qq.com/sph/xxxx` |
| 📺 Bilibili | `https://b23.tv/xxxx` |
| ▶️ YouTube | `https://youtu.be/xxx` |
| 📷 Instagram | `https://www.instagram.com/p/xxx` |
| 🐦 X (Twitter) | `https://x.com/xxx/status/xxx` |
| 🎵 TikTok | `https://www.tiktok.com/@xxx/video/xxx` |
| 🧵 Threads | `https://www.threads.net/@xxx/post/xxx` |
| 📘 Facebook | `https://www.facebook.com/xxx/videos/xxx` |
| 🎬 Vimeo | `https://vimeo.com/xxxxx` |

---

## API Key & Security

- This skill requires the environment variable: `REDFOX_API_KEY`.
- `REDFOX_API_KEY` is provided by [RedFoxHub](https://redfox.hk/settings/api-keys?source=github) (`https://redfox.hk`).
- Please register at [RedFoxHub](https://redfox.hk?source=github) to obtain your `REDFOX_API_KEY`.
- Configure the `REDFOX_API_KEY` environment variable on your device before using this skill.
- Before providing your key, confirm its source, scope, validity period, and whether it can be reset/revoked.
- Never hardcode or expose the key in code, prompts, logs, or output files.

---

## Usage Guide

Just describe what you want in natural language — no commands to memorize.

### Quick Reference

| Intent | Example | Result |
| ------ | ------- | ------ |
| Download a Douyin video | "Download this video https://v.douyin.com/xxxxxx/" | Parses the link and downloads the watermark-free video |
| Save a Xiaohongshu post | "Help me save this post http://xhslink.com/xxx" | Parses and downloads video or images |
| Download a YouTube video | "Download this YouTube video https://youtu.be/xxx" | Parses and downloads the video file |
| Save an Instagram post | "Save this IG post https://www.instagram.com/p/xxx" | Parses and downloads video or images |

### Output Example

After parsing, you will receive a result like:

> ✅ Download complete!
>
> 📱 Platform: Douyin
> 📝 Title: Video title
> 🎬 Type: Video
>
> File saved to ~/Downloads/QoderVideos/video_title.mp4 (12.3 MB)

---

## Use Cases

| Scenario | Role | Example | Benefit |
| -------- | ---- | ------- | ------- |
| Material collection | Editor | "Download this Douyin video" | Get watermark-free footage, straight into your editing workflow |
| Content backup | Collector | "Save this Xiaohongshu post" | Keep it locally forever, even if the original is deleted |
| Trend analysis | Operator | "Download this viral video" | Watch offline repeatedly and break down what makes it viral |
| Cross-platform archiving | Researcher | "Download videos from these platforms" | 12+ platforms supported, one tool does it all |
