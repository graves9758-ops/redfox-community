# Weibo User Posts Search / weibo-post-search

---

## Introduction

Enter a Weibo profile URL or user ID to fetch that user's latest posts. Post content, reposts, comments, likes, and publish time at a glance — one click to the original post.

**Core Value**

- **One-click user feed**: Enter a profile link or UID to instantly pull the user's latest posts — no need to scroll through the Weibo app.
- **Clean data layout**: Five key metrics (content, reposts, comments, likes, publish time) presented in a clear table.
- **Pagination on demand**: Want to browse more? Just say "next page" to fetch older posts.

**Who It's For**

- 🔍 **Content operators / Competitive analysis** — Quickly check a target user's recent output and posting frequency
- 📊 **Sentiment monitoring** — Track a specific user's activity and catch key updates
- 🎯 **Creator research** — Study content style and engagement levels of similar creators

---

## Features

### Core Capabilities

- **User Query**: Enter a Weibo profile URL or UID to fetch the user's latest posts.
- **Pagination**: Browse multiple pages of results to explore more historical posts.

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
| Query user posts | "Check posts from https://weibo.com/1784473157" | Extracts UID and displays results |
| Direct UID input | "Show latest Weibo posts for 1784473157" | Queries directly by UID |
| Pagination | "Next page" / "Previous page" | Navigate through results |

### Output Example

After a query, you'll receive results in this format:

> 📊 **中国新闻网** — **9 posts** found (Page 1):

| # | Post | Reposts | Comments | Likes | Time |
|---|------|---------|----------|-------|------|
| 1 | [Today's sharing...](https://weibo.com/1784473157/5112...) | 120 | 305 | 1.2w | 2025-07-10 14:30:25 |
| 2 | [A weekend at the beach...](https://weibo.com/1784473157/5112...) | 89 | 156 | 5.6k | 2025-07-09 10:15:30 |

> 📄 Page **1**. Reply "next page" to continue browsing.

---

## Use Cases

| Scenario | Role | Example | Benefit |
| -------- | ---- | ------- | ------- |
| Creator tracking | Content operator | "Check this user's recent Weibo posts" | Quickly understand target creator's recent output |
| Competitive analysis | Creator | "Show me what similar creators are posting" | Study content direction and engagement of peers |
| User monitoring | PR / Monitoring | "Check what this user posted recently" | Track specific user's latest activity |
