# Douyin Account Video Batch Downloader / douyin-video-downloader

---

## Introduction

Enter a Douyin ID to automatically fetch the account's recent videos, parse watermark-free download links, and batch download them to your local device.

**Core Value**

- **Watermark-Free Links**: Parsed video and image links are free of Douyin watermarks, ready for re-editing or backup.
- **Efficient Batch Processing**: One Douyin ID handles the entire workflow — fetching, parsing, and downloading.
- **Flexible Filtering**: Filter by publish date range or browse page by page to find exactly what you need.

**Who Is It For**

- 🎬 **Content Creators** — Save and study competitors' best content frame by frame.
- 📦 **Operations / MCN** — Batch back up creator collaborations and run quick due diligence.
- 🎓 **Learners** — Download tutorial videos for offline, anytime rewatching.

---

## Features

### Core Features

- **Video Fetching**: Retrieve an account's recent videos by Douyin ID, including titles, engagement data, and video links.
- **Link Parsing**: Parse watermark-free download links for each video, cover image, and audio track.
- **Batch Download**: Download all videos and images to your local device in one go.
- **Pagination**: Browse more videos page by page, up to 50 items per page.
- **Date Filtering**: Filter videos by publish date range, with natural language support (e.g., "last week", "July videos").
- **Multi-Account Support**: Process multiple Douyin IDs at once.

---

## API Key Acquisition & Security

- This skill requires the environment variable: `REDFOX_API_KEY`.
- `REDFOX_API_KEY` is provided by [RedFoxHub](https://redfox.hk/settings/api-keys?source=github) (`https://redfox.hk`).
- Please visit [RedFoxHub](https://redfox.hk?source=github) to register and obtain your `REDFOX_API_KEY`.
- Configure the `REDFOX_API_KEY` environment variable on your device before using this skill.
- Before providing a key, verify its source, scope, validity period, and whether it supports reset/revocation.
- Never hardcode or expose the key in plain text in code, prompts, logs, or output files.

---

## Usage Guide

Just describe what you need in natural language — no commands to memorize.

### Quick Reference

| Intent                           | Example                                                | Result                                          |
| -------------------------------- | ------------------------------------------------------ | ----------------------------------------------- |
| Download one account's videos    | "Download Fish688688's Douyin videos"                  | Fetch videos and parse download links           |
| Batch download multiple accounts | "Download videos from Fish688688 and YuZhouXiaoLi1220" | Process multiple accounts in sequence           |
| Filter by time                   | "Download this account's July videos"                  | Auto-recognize date range for precise filtering |
| Browse more                      | "Show me the next page"                                | Flip to the next page of videos                 |

### Output Example

After parsing, you'll see a video table like this (illustrative):

| #   | Date  | Video               | Likes | Comments | Saves | Shares | Downloads                   |
| --- | ----- | ------------------- | ----- | -------- | ----- | ------ | --------------------------- |
| 1   | 07-28 | [Video Title](link) | 5.2k  | 67       | 689   | 5.8k   | 🎬Video · 🖼Cover · 🎵Audio |

Below the table, you'll see how many videos are downloadable and how many failed, with an option to batch download them all.

---

## Use Cases

| Scenario              | Role               | Example Request                                              | Benefit                                                                |
| --------------------- | ------------------ | ------------------------------------------------------------ | ---------------------------------------------------------------------- |
| Competitor analysis   | Creator / Director | "Download this competitor's videos for frame-by-frame study" | Offline review of shooting and editing techniques                      |
| Content backup        | Blogger / Operator | "Back up all my account's videos locally"                    | Protect against platform deletion or account issues                    |
| Creator due diligence | MCN / Brand        | "Pull all of this creator's videos for review"               | Quick assessment of content style and performance before collaboration |
| Tutorial archiving    | Learner            | "Download this tutorial account's videos for later"          | No internet needed — rewatch anytime                                   |

---
