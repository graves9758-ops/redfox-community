# Weibo Comment Analysis / weibo-comment-search

---

## Introduction

Enter a Weibo post URL to view its comments at a glance — who commented, how many likes, and when it was posted. Click any username to jump directly to their Weibo profile. All data is freshly fetched from the platform, no stale cache.

**Core Value**

- **Fresh content, no lag**: Every query pulls the latest comments directly from the platform — only fresh data, no outdated archives.
- **User identity at a glance**: Commenter usernames are clickable, linking straight to their Weibo profiles for quick context.
- **Browse at will**: Massive comment threads support pagination — just say "next page" to keep exploring.

**Who It's For**

- 🔍 **Content operators / Competitive analysis** — Check user feedback on target posts and gauge engagement
- �� **Sentiment monitoring** — Track public opinion under specific posts, catch key comments early
- �� **Creator research** — Study follower comments and interaction levels

---

## Features

### Core Capabilities

- **Comment Query**: Enter a Weibo post URL or opusId to fetch first-level comments.
- **Pagination**: Browse multiple pages of results to explore more comments.

---

## API Key Acquisition & Security

- This skill requires the environment variable: `REDFOX_API_KEY`.
- `REDFOX_API_KEY` is provided by [RedFoxHub](https://redfox.hk/settings/api-keys?source=github).
- Visit [RedFoxHub](https://redfox.hk?source=github) to register and obtain your `REDFOX_API_KEY`.
- Configure the `REDFOX_API_KEY` environment variable on your device before using this skill.
- Before providing your key, confirm its source, scope, expiration, and whether it supports reset/revocation.
- Never hardcode or expose your key in plaintext within code, prompts, logs, or output files.

---

## Usage Guide

Just describe your need in plain language — no commands to memorize.

### Quick Reference

| Intent | Example | Effect |
| ------ | ------- | ------ |
| View comments | "Check comments on https://weibo.com/1784473157/R8X4f2lnq" | Extracts opusId and displays comments |
| Direct opusId | "Show comments for R8X4f2lnq" | Queries directly by opusId |
| Pagination | "Next page" / "Previous page" | Navigate through results |

### Output Example

After a query, you'll receive results in this format:

> 📊 Post `R8X4f2lnq` — **20 comments** found (Page 1):

| # | User | Comment | Likes | Time |
|---|------|---------|-------|------|
| 1 | [UserA](https://weibo.com/123456) | Well said, totally agree! | 305 | 2025-07-10 14:30:25 |
| 2 | [UserB](https://weibo.com/789012) | This post is very insightful... | 1.2k | 2025-07-10 12:15:30 |

> 📄 Page **1**. Reply "next page" to continue browsing.

---

## Use Cases

| Scenario | Role | Example | Benefit |
| -------- | ---- | ------- | ------- |
| Comment sentiment analysis | Content operator | "Check comments on this Weibo post" | Quickly understand user feedback on posts |
| Trending tracking | PR / Monitoring | "Check comment sentiment on this trending topic" | Monitor public opinion and user attitudes |
| Competitor comment research | Creator | "View comments on similar creators' posts" | Understand audience engagement with similar content |
