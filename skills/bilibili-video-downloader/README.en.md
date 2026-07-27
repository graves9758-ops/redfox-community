# Bilibili Video Downloader / bilibili-video-downloader

---

## Introduction

Paste a Bilibili video link and get a watermark-free download URL instantly. Copy it into your browser or download tool to save — both www.bilibili.com web links and b23.tv short links are supported, and you won't end up with a watermarked version.

**Core Value**

- **Paste and go**: paste a video link and get a video download URL right away — copy into your browser or download tool, no plugins or subscriptions needed.
- **Clean, watermark-free**: every returned video is watermark-free, ready for collecting or remixing.
- **Both link types recognized**: www.bilibili.com web links and b23.tv short links both work — mobile share links and desktop URLs alike.
- **Batch-friendly**: paste multiple links at once — each is parsed sequentially with a success/failure summary at the end, no need to go one by one.
- **Smart validation**: links from other platforms are detected and flagged immediately, so you don't waste a trip.
- **Results at a glance**: resource type, duration, download link, cover link, and full description are all laid out clearly so you know exactly what to copy.

**Who Is It For**

- 🎬 **Creators / Editors** — quickly save video clips from Bilibili for secondary creation
- 📚 **Content Collectors** — back up favorite Bilibili videos locally, safe from deleted posts
- 🔍 **Operators / Researchers** — download competitor or trending videos for analysis

---

## Features

### Core Features

- **Video Parsing**: paste a Bilibili video link to parse out the watermark-free video download URL.
- **Batch Parsing**: paste multiple links at once — each is parsed sequentially with a success/failure summary at the end.
- **Smart Validation**: automatically detects Bilibili video links — links from other platforms prompt a retry.
- **Complete Information**: displays resource type, duration, download link, cover link, and full description line by line without truncation.
- **Dual Link Support**: recognizes both www.bilibili.com web links and b23.tv short links.

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
| Download a Bilibili video | "Download this video https://www.bilibili.com/video/BVxxxxxx" | Parses the link and returns a direct video download URL |
| Batch download videos | "Download these videos link1 link2 link3" | Parses each link sequentially and summarizes success/failure counts |
| Save a Bilibili video | "Help me save this Bilibili video" | Prompts you to paste the link, then returns the download URL |

### Output Example

After parsing, you will receive a result like:

> ✅ Parsed successfully!
>
> 📝 Description: the full video caption shown in its entirety
>
> 🎬 Resources:
> type, duration, download link, and cover link listed one by one
>
> Copy the link into your browser or download tool to download.
>
> ⚠️ Video download links expire in about 5 minutes — copy to your browser and download immediately!

---

## Use Cases

| Scenario | Role | Example | Benefit |
| -------- | ---- | ------- | ------- |
| Material collection | Editor | "Download this Bilibili video" | Get watermark-free footage straight into your editing workflow |
| Content backup | Collector | "Save this Bilibili video" | Keep it locally forever, even if the original post is deleted |
| Trend analysis | Operator | "Download this viral video" | Watch offline repeatedly and break down what makes it viral |
