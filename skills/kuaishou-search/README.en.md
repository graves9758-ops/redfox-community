# Kuaishou Work Search / kuaishou-search

---

## Overview

Search trending works on Kuaishou by keyword (broad database). Browse results with multi-dimensional sorting — see titles, authors, play counts, likes, comments, and saves at a glance. Click any title to jump directly to the original work, or extract video details and transcripts via work_id.

**Core Value**

- **Search and see instantly**: Enter any keyword and get a trending works list sorted by popularity.
- **Comprehensive data**: Each work displays play count, likes, comments, saves, video duration, and a clickable link, with publish time down to the second.
- **Multi-dimensional filtering**: Switch perspectives by sorting on general, latest, likes, and saves.
- **Video detail extraction**: Each work's work_id can be used with the kuaishou-video-extract skill to get video details and extract transcripts.
- **Stay updated**: Subscribe to keywords for daily push notifications — never miss a trend.

**Who It's For**

- 🔍 **Content Creators** — Track trending works in your niche for data-driven creative direction.
- 📊 **Operations / Data Analysts** — Quickly understand what's trending in any category on Kuaishou.
- 🏢 **Brands / MCNs** — Identify potential creator partners and evaluate work performance for campaign decisions.
- 🛒 **E-commerce Sellers** — Search product-related works in specific niches to find promotion angles.

---

## Features

### Core Features

- **Keyword Search**: Search trending Kuaishou works by keyword (broad database) and discover content in your target niche.
- **Multi-dimensional Sorting**: Four sorting options — General Ranking, Latest, Most Liked, Most Saved.
- **Pagination**: 20 results per page with multi-page browsing — never miss a work.
- **Clickable Links**: Work titles are hyperlinked for one-click access to the original page.
- **Video Detail Extraction**: Each work's work_id can be used with the kuaishou-video-extract skill to get video details and extract transcripts.
- **Subscription**: Subscribe to daily keyword push notifications for the latest works.

---

## API Key Acquisition & Security

- This skill requires the environment variable: `REDFOX_API_KEY`.
- `REDFOX_API_KEY` is provided by [RedFoxHub](https://redfox.hk/settings/api-keys?source=github) (`https://redfox.hk`).
- Visit [RedFoxHub](https://redfox.hk?source=github) to register and get your `REDFOX_API_KEY`.
- Configure your device's environment variable `REDFOX_API_KEY` before using this skill.
- Before providing your key, verify its source, scope, expiration, and whether reset/revoke is supported.
- Never hardcode or expose the key in plaintext within code, prompts, logs, or output files.

---

## Usage Guide

Just describe what you're looking for in natural language — no commands to memorize.

### Quick Reference

| Intent | Example | Effect |
| ------ | ------- | ------ |
| Search a topic | "Search food content" | Searches "food", sorted by likes |
| Specify sort | "Show me the most played World Cup works" | Searches "World Cup", sorted by likes |
| Switch sort | "Re-search by general ranking" | Switches to general ranking sort |
| Next page | "Next page" | Auto-increments page and shows the next 20 works |
| Extract video details | "Show video details for work #3" | Uses work_id with kuaishou-video-extract skill |
| Subscribe daily | "Confirm subscription" | Pushes latest works every day at 09:00 AM |

### Example Output

After searching, you'll see a table similar to:

| # | Title | Author | Plays | Likes | Comments | Saves | Publish Time |
|---|-------|--------|-------|-------|----------|-------|-------------|
| 1 | [Ronaldo arrives on Kuaishou…](link) | Ronaldo | 56.5m | 208.5k | 4,329 | 18.9k | 2026-06-12 18:18:42 |
| 2 | [Episode 52 \| Summer Crush…](link) | 茜二吨 | 23.1m | 332.0k | 6,236 | 58.9k | 2026-06-19 18:35:46 |

(Shows 20 works per page; prompts to browse next page when more are available.)

---

## Use Cases

| Scenario | Role | Example Query | Benefit |
| -------- | ---- | ------------- | ------- |
| Content Research | Content Creator | "What's trending in the food niche on Kuaishou?" | Quickly identify high-engagement directions |
| Competitor Monitoring | Brand Operator | "Check top performing works in the baby & mom category" | Understand content patterns to guide ad strategy |
| Trend Tracking | Marketing Team | "How popular is fitness content on Kuaishou?" | Evaluate category heat with data and adjust in time |
| Daily Following | Individual User | "Subscribe to travel works daily push" | Get automatic updates, never miss a trend |

---

## Data Notes

- Data is updated daily at **06:00 AM** — not a real-time query.
- Subscription pushes run daily at **09:00 AM**, delivering the latest works.
- Numbers ≥ 10,000 are displayed in `x.xk` / `x.xm` format (e.g. `12.5k`, `1.2w`) for easy reading.

---
