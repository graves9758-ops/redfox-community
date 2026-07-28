# TikTok Video Downloader / tiktok-video-downloader

---

## Introduction

Paste a TikTok video link and get a watermark-free download URL instantly. Copy it into your browser or download tool to save. Supports single or batch link parsing — non-TikTok links are automatically detected and the process terminates with a prompt to re-enter. Both www.tiktok.com web links and vm.tiktok.com short links are supported, and you won't end up with a watermarked version.

**Core Value**

- **Paste and go**: paste a video link and get a video download URL right away — copy into your browser or download tool, no plugins or subscriptions needed.
- **Batch parsing**: paste multiple TikTok video links at once (space-separated), parse them in sequence and get a summary of successes and failures at the end — no more repeating one by one.
- **Smart link validation**: automatically checks whether the input link is a TikTok video link; non-TikTok links are flagged with a prompt and the process terminates, requiring you to re-enter a valid link.
- **Clean, watermark-free**: every returned video is watermark-free, ready for collecting or remixing.
- **Both link types recognized**: www.tiktok.com web links and vm.tiktok.com short links both work — mobile share links and desktop URLs alike.
- **Results at a glance**: resource type, duration, download link, cover image, audio link, and full description are all laid out clearly so you know exactly what to copy.

**Who Is It For**

- 🎬 **Creators / Editors** — quickly save video clips from TikTok for secondary creation
- 📚 **Content Collectors** — back up favorite TikTok videos locally, safe from deleted posts
- 🔍 **Operators / Researchers** — download competitor or trending videos for analysis

---

## Features

### Core Features

- **Video Parsing**: paste a TikTok video link to parse out the watermark-free video download URL.
- **Batch Parsing**: paste multiple TikTok video links at once (space-separated), parse them one by one and get a summary of successes and failures at the end.
- **Link Validation**: automatically detects whether the input link is a TikTok video link; non-TikTok links are flagged and the process terminates, requiring you to re-enter a valid link.
- **Complete Information**: displays resource type, duration, download link, cover image, audio link, and full description line by line without truncation.
- **Dual Link Support**: recognizes both www.tiktok.com web links and vm.tiktok.com short links.
- **Link Expiry Reminder**: the download link returned after parsing is valid for approximately 5 minutes; users are reminded to copy and use it immediately.

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

Just describe what you want in natural language — no commands to memorize. When a valid TikTok video link is provided, parsing runs immediately without extra confirmation.

### Quick Reference

| Intent | Example | Result |
| ------ | ------- | ------ |
| Download a TikTok video | "Download this video https://www.tiktok.com/@user/video/xxxxx" | Parses the link and returns a direct video download URL |
| Batch download TikTok videos | "Download these videos link1 link2 link3" | Parses multiple links in sequence, returns download URLs and a summary |
| Save a TikTok video | "Help me save this TikTok video" | Prompts you to paste the link, then returns the download URL |

### Output Example

After parsing a single link, you will receive a result like:

> ✅ Parsed successfully!
>
> 📝 Description: the full video caption shown in its entirety
>
> 🎬 Resources:
> type, duration, download link, cover image, and audio link listed one by one
>
> Copy the link into your browser or download tool to download.
>
> ⚠️ The video download link is valid for approximately 5 minutes. Please copy it to your browser and download immediately!

When batch parsing, each link's results are shown in sequence, followed by a summary:

> 📋 Batch parsing complete
> ✓ Success: 3
> ✗ Failed: 1
>
> Copy the link into your browser or download tool to download.

If a non-TikTok link is entered, you will see a prompt:

> [✗] This is not a TikTok video link. Please enter a valid TikTok video link.
> Valid link format examples:
> https://www.tiktok.com/@user/video/xxxxx
> https://vm.tiktok.com/xxxxx/

---

## Use Cases

| Scenario | Role | Example | Benefit |
| -------- | ---- | ------- | ------- |
| Material collection | Editor | "Download this TikTok video" | Get watermark-free footage straight into your editing workflow |
| Batch material gathering | Editor | "Download these videos link1 link2 link3" | Parse multiple links at once and get all footage in one go |
| Content backup | Collector | "Save this TikTok video" | Keep it locally forever, even if the original video is deleted |
| Trend analysis | Operator | "Download this viral video" | Watch offline repeatedly and break down what makes it viral |
