# Bilibili Video Downloader / bilibili-video-downloader

---

## Overview

Paste a Bilibili video link and get a watermark-free direct download link in one click. Supports single or batch link processing with automatic Bilibili video link recognition and validation.

**Core Value**

- **Paste and go**: Get watermark-free download links instantly by pasting the URL—no extra tools or manual steps required.
- **Batch processing**: Submit multiple links at once; each is processed individually with a final success/failure summary.
- **Smart validation**: Automatically identifies Bilibili video link formats and prompts you to re-enter non-Bilibili links, avoiding wasted effort.

**Intended Users**

- 🎬 **Content creators** — Quickly grab watermark-free footage and jump straight into editing.
- 📦 **Video collectors** — Save your favorite Bilibili videos locally for permanent access.
- 📊 **Operations analysts** — Watch viral videos offline and break down content strategies.

---

## Features

### Core Capabilities

- **Watermark-free direct links**: Returned video download links are watermark-free and ready to use.
- **Batch parsing**: Submit multiple links in one go—each is processed individually with a results summary.
- **Smart link validation**: Automatically recognizes www.bilibili.com web links and b23.tv short links, with instant prompts for non-Bilibili links.
- **Direct results**: Download links and cover images are returned immediately after parsing—copy to your browser or download tool to save.

---

## API Key Acquisition & Security

- This skill requires the environment variable: `REDFOX_API_KEY`.
- `REDFOX_API_KEY` is issued by [RedFoxHub](https://redfox.hk/settings/api-keys?source=github) (`https://redfox.hk`).
- Register at [RedFoxHub](https://redfox.hk?source=github) to obtain `REDFOX_API_KEY`.
- Configure `REDFOX_API_KEY` on your device before using this skill.
- Before providing your key, confirm its source, scope, validity period, and whether it can be reset or revoked.
- Do not hard-code or expose keys in plain text in code, prompts, logs, or output files.

---

## Usage Guide

Simply describe your needs in natural language—no commands to memorize.

### Quick Reference

| Intent | Example Phrase | Result |
|--------|---------------|--------|
| Download a single video | "Download this video https://www.bilibili.com/video/BVxxxxxx" | Parse the link and return a watermark-free direct download link |
| Batch download | "Download these videos link1 link2 link3" | Process each link and summarize results |
| Save a video | "Help me save this Bilibili video" | Guide you to paste the link, then return the download link after parsing |

### Output Example

After submitting a Bilibili video link, you will receive results in the following format:

```
Description: <video title>

| Item | Details |
| --- | --- |
| Video | Download link |
| Cover | View cover |

> ⚠️ The video download link is valid for approximately 5 minutes. Please copy and open it in your browser or download it immediately!
```

---

## Use Cases

| Scenario | Role | Example Question | Benefit |
|----------|------|-----------------|---------|
| Asset collection | Video editor | "Download this Bilibili video" | Quickly get watermark-free footage ready for editing |
| Content backup | Collector | "Save this Bilibili video" | Permanent local copy even if the original is deleted |
| Viral analysis | Operations | "Download this viral video for me" | Watch offline and break down viral content logic |
