# Douyin Follower Growth Rankings / douyin-rise-ranking

---

## Introduction

A specialized tool for Douyin follower growth data, tracking real-time follower increase rankings across all categories. Supports daily/weekly/monthly time dimensions and 27 vertical category filters, with automated growth trend analysis and hotspot impact quantification reports.

**Core Value**

- Multi-dimensional rankings: Daily, weekly, and monthly granularity for daily monitoring and long-term review
- 27 vertical categories: Precise filtering from food to gaming
- Smart trend analysis: Automated TOP50 growth trend analysis with quantified hotspot impact
- Scheduled subscription push: One-click subscription, data delivered on schedule

**Target Users**

- 📱 Content Creators — Discover trending topics and content inspiration
- 🏢 Brand Marketers — Track competitor growth in your niche
- 📊 MCN Agencies — Monitor creator growth data at scale
- 🎯 Advertisers — Identify high-potential accounts for collaboration

---

## Features

### Core Features

- Multi-dimensional rankings: Daily, weekly, and monthly views for different operational cycles
- 27 category filters: Precise selection from food, tech, beauty, and more
- Smart trend analysis: TOP50 growth trend analysis with hotspot impact quantification
- Scheduled subscription push: One-click subscription for automated delivery
- Clickable account links: Direct links to account profiles for quick access

### Highlights

- Real-time updates: Daily at 18:00, weekly every Monday 18:00, monthly on the 3rd at 18:00
- Visual presentation: Gold/Silver/Bronze medals for TOP3 with clear growth metrics
- Deep insights: Two-stage analysis covering growth trends and hotspot impact
- Secure: API Key only, no account credentials needed

---

## API Key Acquisition & Security

- This skill requires the environment variable: `REDFOX_API_KEY`
- `REDFOX_API_KEY` is provided by [RedFoxHub](https://redfox.hk/settings/api-keys?source=github) (`https://redfox.hk?source=github`)
- Please visit [RedFoxHub](https://redfox.hk?source=github) to register and obtain your `REDFOX_API_KEY`
- Configure the `REDFOX_API_KEY` environment variable on your device before using this skill
- Before providing your key, verify its source, scope, validity period, and whether it supports reset/revocation
- Never hardcode or expose your key in code, prompts, logs, or output files

---

## Usage Guide

Simply describe your needs in natural language — no commands to memorize.

### Quick Reference

| Intent          | Example                                        | Result                                               |
| --------------- | ---------------------------------------------- | ---------------------------------------------------- |
| Daily ranking   | Show me food category Douyin follower rankings | TOP20 daily ranking with trend analysis              |
| Weekly ranking  | Tech category follower growth this week        | Auto-selects weekly ranking for the tech category    |
| Monthly ranking | Beauty category follower growth this month     | Auto-selects monthly ranking for the beauty category |
| Keyword search  | Pet category rankings                          | Auto-matches the Animals category                    |
| View more       | Show more                                      | Displays remaining TOP21-50 data                     |
| Subscribe       | Subscribe to daily ranking                     | Automated scheduled delivery                         |

### Subscription

After each query, subscription options are displayed. Reply with a number 1-5:

1️⃣ Subscribe Daily — Delivered daily at 18:00
2️⃣ Subscribe Weekly — Delivered every Monday at 18:00
3️⃣ Subscribe Monthly — Delivered on the 3rd at 18:00
4️⃣ Subscribe All — Daily + Weekly + Monthly
5️⃣ No Subscription

Natural language commands like "subscribe daily" are also supported.

### Available Categories

All, Personal Talent, Lifestyle Vlog, Wealth & Finance, ACG, Home & Decor, Education, Skits, Tech, Travel, Food, Beauty, Animals, Parenting, Automotive, Relationships, Agriculture, Health & Medicine, Fashion, Dance, Appearance, Humanities, Music, Film & TV, Fitness, Sports, Celebrities, Gaming (27 total)

### Keyword Auto-Matching

| Keyword                         | Matched Category |
| ------------------------------- | ---------------- |
| Phone / Computer / AI           | Tech             |
| Food / Cooking / Restaurant     | Food             |
| Fashion / Outfit / Trend        | Fashion          |
| Fitness / Sports / Weight Loss  | Fitness          |
| Skincare / Makeup / Beauty      | Beauty           |
| Gaming / Esports / Mobile Games | Gaming           |
| Pet / Cat / Dog                 | Animals          |
| Dance                           | Dance            |
| Singing / Music                 | Music            |

---

## Use Cases

| Scenario              | Role                    | Example Query                              | Benefit                                      |
| --------------------- | ----------------------- | ------------------------------------------ | -------------------------------------------- |
| Competitor Monitoring | Brand Marketing Manager | Show me this week's food category rankings | Identify industry trends, optimize marketing |
| Content Inspiration   | Douyin Creator          | Which education accounts are growing fast  | Discover trending content angles             |
| Creator Management    | MCN Operations          | Monthly beauty category TOP50              | Data-driven creator management               |
| Account Selection     | Advertiser              | High-growth mid-tier tech accounts         | Precise targeting, higher ROI                |

---

## Data Notes

| Ranking Type | Lookback Range | Update Time                                 |
| ------------ | -------------- | ------------------------------------------- |
| Daily        | Last 7 days    | Daily at 18:00 (previous day)               |
| Weekly       | Last 3 weeks   | Every Monday at 18:00 (previous week)       |
| Monthly      | Last 3 months  | 3rd of each month at 18:00 (previous month) |

Default display shows TOP20 with growth analysis. Reply "Show more" for the remaining 30 entries (TOP50 total). Out-of-range date queries are automatically adjusted to the nearest available date.
