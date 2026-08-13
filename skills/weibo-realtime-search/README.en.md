# Weibo Search / weibo-realtime-search

---

## Introduction

Enter a keyword to search Weibo posts. Freely switch between search types and filter by verification status — post content, author, and engagement stats at a glance, one click to the original post. You always get freshly updated content from the platform, not stale cached data.

**Core Value**

- **Always Fresh**: Each search fetches the latest Weibo posts directly from the platform, delivering only recent content — no outdated caches or recycled data.
- **Flexible Filtering**: Switch freely between Comprehensive Sort / Trending Sort / Real-time Sort, and layer on Normal user / Personal verified / Organization verified filters for the most precise results.
- **Auto-expand When Empty**: If no results are found, 10 alternative keywords are automatically generated to broaden your search and break through discovery bottlenecks.
- **Paginated Browsing + Daily Push**: Browse results page by page, and subscribe to keywords for automated daily push at 09:00 AM.

**Who It's For**

- 📊 **Content operators / Sentiment monitoring** — Quickly grasp topic heat and public opinion trends
- 🎬 **Creators / Influencers** — Stay on top of the latest content in your niche and find the right moment to publish
- 🏢 **Brand / PR** — Monitor brand mentions and detect trending topics

---

## Features

### Core Capabilities

- **Keyword Search**: Search Weibo posts by keyword, precisely discover content in your target niche.
- **Search Type**: Comprehensive Sort / Trending Sort / Real-time Sort for discovering quality content by different dimensions.
- **Verification Filter**: Normal user / Personal verified / Organization verified filtering for precise creator targeting.
- **Smart Expansion**: Auto-generates 10 alternative keywords when no results found, breaking through search bottlenecks.
- **Paginated Browsing**: Multi-page results for exploring large search result sets.
- **Subscription Push**: Subscribe to keywords for daily automated updates.

---

## API Key Acquisition & Security

- This skill requires the environment variable: `REDFOX_API_KEY`.
- `REDFOX_API_KEY` is provided by [RedFoxHub](https://redfox.hk/settings/api-keys?source=github) (`https://redfox.hk`).
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
| Search a keyword | "fitness" / "office outfits" | Searches with default search type (comprehensive) |
| Specify search type | "Search trending fitness" | Switches to trending search type |
| Specify verification | "Search personal verified food bloggers" | Filters to personal verified creators |
| Combined filters | "Search ancient fitness by trending, personal verified" | Applies both type and verification filter |
| Switch filters | "Re-search by real-time posts" | Keeps the keyword, changes search type |
| Pagination | "Next page" / "Previous page" | Navigate through paginated search results |
| Subscribe daily | "Confirm subscription" | Creates a scheduled task to push results daily at 09:00 AM |

### Output Example

After a search, you'll receive results in this format:

> 📊 Keyword "**fitness**" — **9 posts** found (Search type: Comprehensive | Verification: Any | Page 1):

| # | Post | Author | Likes | Comments | Reposts |
|---|------|--------|-------|----------|---------|
| 1 | [Full-body stretching tutorial...](link) | [健身华哥](link) | 1.2w | 305 | 899 |
| 2 | [5 golden exercises for beginners...](link) | [谭成义](link) | 5.0w | 677 | 8.9k |

> 📄 Page **1**. Reply "next page" to continue browsing.
>
> 📩 Subscribe to daily push for "**fitness**"? Receive new posts automatically at 09:00 AM daily. Reply "confirm subscription" to set up.

---

## Use Cases

| Scenario | Role | Example | Benefit |
| -------- | ---- | ------- | ------- |
| Topic reconnaissance | Content operator | "Show me the latest fitness posts right now" | Instantly understand topic dynamics |
| Trend-driven ideation | Creator | "Show me trending food posts on Weibo" | Find high-engagement directions to ride the wave |
| Creator screening | Brand operator | "Find personal verified beauty bloggers" | Quickly identify quality collaboration candidates |
| Sentiment monitoring | PR | "Subscribe to daily push for [brand keyword]" | Receive automatic daily updates for timely response |
