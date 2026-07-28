# Xiaohongshu Top Account Tracker / xiaohongshu-top-account

---

## Overview

Want to know which Xiaohongshu accounts are hottest and gaining followers the fastest? Just say a category to check daily, weekly, or monthly TOP 50 rankings across 25 niches including beauty, food, travel, parenting, and fitness. Rankings are updated daily, and a visual report is generated automatically.

**Core Value**

- **Comprehensive rankings** — Daily/weekly/monthly cycles, all categories or niche-specific, TOP 50 accounts at a glance.
- **Accurate niche matching** — Say "food" and it auto-matches to the gourmet niche; say "fitness" and it locks onto sports & exercise. Fuzzy keywords work too.
- **Visual & exportable reports** — Automatically generates a polished HTML report with one-click PDF/image export; account names link directly to their profiles.
- **Hands-free subscriptions** — Set up daily/weekly/monthly push notifications and rankings come to you automatically.

**Intended Users**

- 📊 **Brand / MCN operators** — Quickly identify top creators in each niche for collaboration and investment decisions.
- 📝 **Xiaohongshu creators** — Stay up to date on top accounts in your niche and find benchmarks to learn from.
- 🔍 **Content researchers** — Compare account performance across niches and cycles to spot platform traffic trends.

---

## Features

### Core Capabilities

- **Ranking queries**: Check daily, weekly, or monthly TOP 50 — default display shows TOP 20, ask to see the full list.
- **Niche filtering**: Supports 25 niches (beauty, food, travel, parenting, fitness, etc.) with automatic name matching.
- **Visual reports**: Each query auto-generates an HTML report; account names are clickable links to their profiles, with PDF export support.
- **Scheduled subscriptions**: Set a push cycle (daily/weekly/monthly) and rankings are delivered on schedule.
- **History lookback**: Daily rankings go back 7 days, weekly 3 weeks, monthly 3 months.

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

Simply describe what you need in natural language—no commands to memorize.

### Quick Reference

| Intent | Example phrase | Result |
|--------|---------------|--------|
| Daily all-category ranking | "Xiaohongshu latest daily ranking" | Returns yesterday's all-category TOP 20 account ranking |
| Weekly niche ranking | "Food weekly ranking" | Returns last week's gourmet niche TOP 20 |
| Monthly ranking | "Beauty monthly ranking" | Returns last month's cosmetics niche TOP 20 |
| View full list | "Show all 50" | Expands the complete TOP 50 ranking and delivers the report |
| Download report | "Download report" | Generates and delivers an HTML visual report file |
| Subscribe to push | "Subscribe to daily ranking" | Sets up daily scheduled ranking push notifications |

### Output Example

After a query you receive a structured ranking table including rank, account name (clickable to profile), composite score, total followers, new notes/followers/likes/comments/saves/shares, along with an HTML report file.

---

## Use Cases

| Scenario | Role | Example question | Benefit |
|----------|------|-----------------|---------|
| Creator screening | Brand / MCN | "Travel niche daily ranking—who's gaining followers fast?" | Quickly identify collaboration targets backed by data |
| Competitor tracking | Creator / ops | "Subscribe to beauty niche weekly ranking" | Receive regular updates on top accounts in your niche |
| Trend insights | Content research | "Compare food and fitness monthly rankings" | Cross-niche data comparison to spot traffic trends |
| Report export | Data analysis | "Check all-category monthly ranking and export report" | Get a shareable HTML report file |

---
