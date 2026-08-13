# Weibo Hot Search / weibo-hot-search

---

## Introduction

Open it and see Weibo's current trending topics at a glance — titles, rankings, and creative inspiration analysis all in one place. One click to jump to related posts. You get the freshly updated leaderboard, not stale cached data.

**Core Value**

- **Always Up-to-Date**: Fetches the current Weibo trending topics every time you open it — only the latest rankings.
- **Clear Ranking View**: Displays trending topics from rank 1 to N with heat indicators, so hotness is instantly visible.
- **One-Click Search**: Every trending topic comes with a Weibo search link, tap to explore related posts and discussions.
- **Inspiration & Insights**: Auto-categorizes trending topics, extracts content angles with creative suggestions and risk alerts.

**Who It's For**

- 📊 **Content operators / Sentiment monitoring** — Quickly grasp Weibo's current trending topics and public opinion trends
- 🎬 **Creators / Influencers** — Identify hot topics for content inspiration and optimal publishing timing
- 🏢 **Brand / PR** — Monitor whether brand-related topics are trending

---

## Features

### Core Capabilities

- **Trending Leaderboard**: Fetch Weibo's current trending topics, one-stop overview of platform-wide hotspots.
- **Ranked Display**: Trending topics displayed by rank with heat scores.
- **One-Click Search**: Each trending topic includes a `https://s.weibo.com/weibo?q=` search link for instant access.
- **Inspiration Analysis**: Categorizes trending topics by domain, extracts content angles with risk alerts.

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
| View hot search | "Weibo trending" / "What's hot today" | Fetches the current Weibo trending topics |
| Check specific rank | "What's the #1 trending topic" | Find a topic by its rank |
| Subscribe daily push | "Confirm subscription" | Creates a scheduled task to push daily at 09:00 AM |

### Output Example

> 🔥 Weibo Trending Topics — **50 topics**:

| # | Topic | Heat |
|---|-------|------|
| 1 | [Major event sparks discussion](https://s.weibo.com/weibo?q=...) | 305.2w |
| 2 | [Celebrity responds to controversy](https://s.weibo.com/weibo?q=...) | 198.5w |
| 3 | [Movie box office breaks 100M](https://s.weibo.com/weibo?q=...) | 126.3w |

> �� Subscribe to daily push for "**Weibo Trends**"? Receive the latest trending topics automatically at 09:00 AM daily.

---

## Use Cases

| Scenario | Role | Example | Benefit |
| -------- | ---- | ------- | ------- |
| Hotspot monitoring | Content operator | "What's trending on Weibo today" | Instantly grasp platform-wide hotspots |
| Content ideation | Creator | "Show me what's trending" | Follow hot topics to decide content direction |
| Sentiment tracking | PR | "Is our brand trending" | Quickly detect brand-related mentions |
