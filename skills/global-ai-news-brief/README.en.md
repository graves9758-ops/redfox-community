# Global AI News Brief / global-ai-news-brief

---

## Introduction

Enter a keyword to search 11 major platforms at once — Douyin, Xiaohongshu, WeChat Official Accounts, Bilibili, Kuaishou, WeChat Channels, Toutiao, TikTok, Instagram, X(Twitter), and YouTube — then let AI aggregate the cross-platform data into smart summaries, topic clustering, sentiment analysis, and in-depth interpretation reports.

**Core Value**

- **One search, full coverage**: a single keyword searches all 11 platforms at once, no need to browse each one manually
- **Deep intelligence, not just listings**: AI automatically clusters hot subtopics, extracts key findings, and gauges public sentiment
- **Cross-platform comparison**: see differences in focus and interpretation across platforms at a glance
- **Dual presentation**: quick browsing via terminal tables + complete archive via visual report

**Who It's For**

- 📊 Market & sentiment analysts — quickly grasp the full picture and sentiment trends of an event
- ✍️ Content creators — collect multi-platform hot material in one go to support topic selection
- 📰 Media & industry researchers — gain deep insights through cross-platform comparison

---

## Features

### Core Features

- **Aggregated cross-platform search**: one keyword covers 11 major platforms (Douyin, Xiaohongshu, WeChat Official Accounts, Bilibili, Kuaishou, WeChat Channels, Toutiao, TikTok, Instagram, X(Twitter), YouTube); you can also limit the search to the 7 domestic platforms
- **Four-section in-depth report**: News Events (overview + timeline + subtopic clustering), News Interpretation (summary + key findings + sentiment + KOLs), cross-platform interpretation comparison, and raw data sources — presented in sequence
- **Smart sentiment analysis**: automatically calculates the positive/neutral/negative sentiment ratio across the web, extracts core consensus and controversy points, and identifies key opinion leaders
- **Cross-platform comparison matrix**: content volume, total engagement, sentiment tendency, focus, and representative opinions of each platform in one table
- **Visual report**: automatically generates and opens a visual page with platform tabs, sentiment dashboard, and comparison charts, while the terminal shows TOP 5 data tables per platform

---

## API Key Acquisition & Security

- This skill requires the environment variable: `REDFOX_API_KEY`.
- `REDFOX_API_KEY` is provided by [RedFoxHub](https://redfox.hk/settings/api-keys?source=github) (`https://redfox.hk`).
- Please register an account at [RedFoxHub](https://redfox.hk?source=github) to obtain `REDFOX_API_KEY`.
- Configure the `REDFOX_API_KEY` environment variable on your device before using this skill.
- Before providing a key, please verify its source, available scope, validity period, and whether it supports reset/revocation.
- Never hard-code or expose the key in plain text in code, prompts, logs, or output files.

---

## Usage Guide

Describe your needs in natural language — no commands to memorize.

### Quick Phrase Reference

| Intent                     | Example Phrase                                                  | Result                                                              |
| -------------------------- | --------------------------------------------------------------- | ------------------------------------------------------------------- |
| Cross-platform sentiment   | Look up the latest cross-platform buzz on "new energy vehicles" | Searches 11 platforms in parallel and outputs terminal tables + visual report |
| Event tracking             | Track all cross-platform information about "typhoon"            | Focuses on the timeline and spread path of the event                |
| Domestic platforms only    | Search "summer travel" on domestic platforms only               | Searches only the 7 domestic platforms: Douyin/Xiaohongshu/WeChat Official Accounts/Bilibili/Kuaishou/WeChat Channels/Toutiao |

### Output Example

A single search produces a complete in-depth intelligence report, including:

- **News Events**: event overview card, key timeline, hot subtopic clustering
- **News Interpretation**: 200-character core summary, 3-5 key findings, sentiment (positive/neutral/negative ratio), key opinion leaders
- **Platform Interpretation Tendencies**: cross-platform comparison matrix + sentiment comparison charts
- **Data Sources**: complete data per platform, including covers, titles, authors, engagement metrics, and original links

---

## Use Cases

| Scenario           | Role                              | Example Question                              | Benefit                                                    |
| ------------------ | --------------------------------- | --------------------------------------------- | ---------------------------------------------------------- |
| Hot topic tracking | Content creators, media staff     | Look up the cross-platform buzz on "new energy vehicles" | See all 11 platforms at once and quickly grasp the full picture |
| Sentiment analysis | Marketing & PR professionals      | Track cross-platform information about "typhoon"         | Get timelines, sentiment distribution, consensus and controversy points |
| Industry intelligence | Analysts & operations staff    | Search "summer travel" on domestic platforms only       | Cross-platform comparison matrix reveals focus differences |
