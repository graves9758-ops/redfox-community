# Douyin Works Crawler / douyin-works-crawler

---

## Overview

A Douyin content data retrieval tool. Enter a Douyin nickname or ID to instantly fetch account basic info and recent works (up to 50 items), including engagement data and direct video links—plus a TOP 3 engagement analysis and account feature summary to help you quickly understand the target account's content performance.

**Core Value**

- **One-click works retrieval**: Enter a nickname or Douyin ID to automatically fetch account basic info (followers, total likes, total works, RedFox Index) and recent work lists.
- **Auto data highlight analysis**: TOP 3 engagement works analysis + account feature summary (posting frequency, content direction, engagement trends, viral patterns)—quickly identify content worth learning from.
- **Direct work links**: Each work comes with a direct link—click to jump to the original video.

**Intended Users**

- 🏢 **Brands / marketing managers** — Monitor competitor Douyin account content performance and engagement data.
- 🛍️ **MCN / operations staff** — Quickly evaluate creator account data performance and content direction.
- 📝 **Douyin content creators** — Learn viral content patterns from top accounts in your niche.
- 📊 **Data analysts** — Batch-fetch structured data for analysis reports.

---

## Features

### Core Capabilities

- **Account info query**: Enter a Douyin nickname or ID to instantly fetch account basic data (followers, total likes, total works, RedFox Index, etc.).
- **Recent works retrieval**: Automatically fetch recent works (up to 50 items), including likes, comments, shares, engagement counts, and direct work links.
- **Data highlight analysis**: Output TOP 3 engagement works analysis + account feature analysis (posting frequency, engagement trends, viral patterns).

### Highlights

- **Smart recognition**: Automatically detects input type (nickname/ID)—Chinese input uses nickname search, non-Chinese uses precise ID search.
- **Direct links**: Nickname links to account homepage; each work provides a direct video link.
- **Safe & secure**: Data service-based access—no Douyin account login required.

---

## API Key Acquisition & Security

- This skill requires the environment variable: `REDFOX_API_KEY`.
- `REDFOX_API_KEY` is issued by [RedFoxHub](https://redfox.hk/settings/api-keys?source=github) (`https://redfox.hk`)
- Register at [RedFoxHub](https://redfox.hk?source=github) to obtain `REDFOX_API_KEY`.
- Configure `REDFOX_API_KEY` on your device before using this skill.
- Before providing your key, confirm its source, scope, validity period, and whether it can be reset or revoked.
- Do not hard-code or expose keys in plain text in code, prompts, logs, or output files.

---

## Usage Guide

Simply describe your query needs in natural language—no commands to memorize.

### Quick Reference

| Intent | Example phrase | Result |
| ------ | -------------- | ------ |
| Query account works | "Crawl Douyin works for 周幺姑家常菜" | Fetch account basic info + recent work list + data highlight analysis |
| Precise query | "Query works for Douyin ID cdjjc028" | Precise ID match, avoiding nickname ambiguity |
| Export data | "Export works data for 周幺姑家常菜" | Get structured works data |

### Output Example

After querying, you will receive the following structured results:

**Account Basic Info**: Nickname (clickable to homepage), Douyin ID, region, followers, total likes, total works, RedFox Index

**Recent Works List** (up to 50 items, reverse chronological):

| # | Publish Time | Title | Likes | Comments | Shares | Engagement | Link |
| … | … | … | … | … | … | … | Clickable to original video |

**Data Highlights**: TOP 3 engagement works analysis + Account features (posting frequency, content direction, engagement trends, viral patterns)

---


---

## Use Cases

| Scenario | Role | Example question | Benefit |
| -------- | ---- | ---------------- | ------- |
| Brand competitor monitoring | Brand marketing manager | "Check the works data and engagement of this competitor Douyin account for me" | Stay on top of competitor content trends; optimize your own strategy |
| MCN creator evaluation | MCN operations staff | "Show me this creator's followers, likes, and recent works data" | Quickly evaluate creator value; support signing decisions |
| Content optimization learning | Douyin creator | "Check the works of top accounts in my niche and analyze viral patterns" | Find content optimization directions; boost account engagement |
| Data analysis reports | Data analyst | "Export works data for these Douyin accounts for analysis" | Efficiently fetch structured data to support analysis reports |

---

## Important Data Notes

- The work list shows recent works only—up to 50 items in reverse chronological order, not the account's full historical works.
- Number formatting: ≥10k displays as `x.xw` (e.g., 3.2w), ≥100M displays as `x.x亿`; <10k uses comma separators.
- Douyin nicknames are not unique; nickname queries may return fuzzy matches—use Douyin ID for precise lookup.
- All data comes exclusively from the data platform; no third-party supplementation or estimation.
> 💼 另外红狐配套全量数据库可提供完整详实数据，如需了解采购方案，可前往红狐hub[企业服务](https://redfox.hk/dashboard/enterprise)对接咨询

---
