# TikTok Home Video Downloader / tiktok-home-downloader

---

## Overview

Enter a TikTok profile link to automatically fetch the account's video list, resolve watermark-free download links, and batch download them locally in one click.

**Core Value**

- **Watermark-free direct links**: Resolved video links have TikTok watermarks removed, ready for re-editing or backup.
- **Batch efficiency**: One profile link input automatically completes the entire workflow of fetching, parsing, and downloading.
- **Flexible filtering**: Filter by publish date range and browse by page to precisely target content.

**Intended Users**

- 🎬 **Content creators** — Collect and study competitor content, analyzing shooting and editing techniques frame by frame.
- 📦 **Operations / MCN** — Batch backup influencer collaborations and quickly complete background research.
- 🎓 **Learners** — Offline hoard tutorial videos for repeated viewing anytime.

---

## Features

### Core Capabilities

- **Content fetching**: Retrieve a profile's videos via link, including titles, view counts, engagement data, and video links.
- **Link parsing**: Resolve watermark-free download links for each video, supporting both video and cover resources.
- **Batch download**: Download all videos locally in one click, supporting both video and photo posts.
- **Paginated browsing**: Browse more videos across pages, up to 50 per page.
- **Date filtering**: Precise filtering by publish date range, with natural language recognition (e.g., "last week", "July videos").
- **Multi-account support**: Process multiple TikTok accounts simultaneously in batch.

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
| ------ | -------------- | ------ |
| Download a single account's videos | "Help me download TikTok videos from https://www.tiktok.com/@tiktok" | Fetch profile videos and resolve download links |
| Batch download multiple accounts | "Download videos from both @tiktok and @khaby.lame" | Process multiple accounts sequentially |
| Filter by date | "Download this account's July videos" | Auto-detect date range, precise filtering |
| View more videos | "Continue to the next page" | Paginate for more videos |

### Account Input Formats

| Format | Example | Notes |
| ------ | ------- | ----- |
| Profile link | `https://www.tiktok.com/@tiktok` | Recommended; auto-resolves account identifier |
| @handle | `@tiktok` | The part after `@` in the profile URL |
| secUserId | `MS4wLjABxxxx...` | Can be used directly |

> Note: Please provide an **account profile link**, not a single video link (links containing `/video/`).

### How to Get secUserId

secUserId is TikTok's internal account identifier, always starting with `MS4w`. When a profile link cannot be resolved (e.g., network restrictions, anti-scraping), providing secUserId allows direct querying:

1. **Mobile App Share Link (Recommended)**: Open TikTok App → go to the profile → "Share" → "Copy Link". The share link contains the `sec_uid=MS4w...` parameter (e.g., `https://www.tiktok.com/@xxx?sec_uid=MS4wLjABAAAA...`). Send the full link to the skill directly.
2. **Developer Tools**: Press `F12` on the profile page → Console, execute: `JSON.parse(document.getElementById('__UNIVERSAL_DATA_FOR_REHYDRATION__').textContent).__DEFAULT_SCOPE__['webapp.user-detail'].userInfo.user.secUid` to print the secUserId.

> ⚠️ **The share link must include the `sec_uid=MS4w...` parameter**. Regular profile links (without `sec_uid=`) require page access to resolve and may fail; parameterized share links bypass this and have the highest success rate.

> If the provided secUserId is incorrectly formatted, the skill will automatically return the above guidance for re-acquisition.

### Output Example

After parsing, you'll see a table similar to the following (illustrative):

| # | Publish Date | Title | Views | Likes | Comments | Favorites | Shares | Download |
|---|-------------|-------|-------|-------|----------|-----------|--------|----------|
| 1 | 07-28 | [Title](link) | 88.9w | 5.7k | 274 | 322 | 20 | 🎬Video · 🖼Cover |

The table footer shows the count of downloadable and failed items, with a prompt for batch downloading to local storage.

---

## Use Cases

| Scenario | Role | Example Question | Benefit |
| -------- | ---- | ---------------- | ------- |
| Competitor content analysis | Creator / Editor | "Download this competitor's TikTok videos for frame-by-frame study" | Offline repeated viewing, deconstruct filming techniques |
| Content backup | Blogger / Operator | "Back up all my account's videos locally" | Prevent content loss from platform deletion or account issues |
| Influencer background check | MCN / Brand | "Pull all this influencer's content for review" | Quickly assess content style and performance before collaboration |
| Tutorial offline collection | Learner | "Download this tutorial account's videos for later study" | No internet needed, watch and learn anytime |

---
