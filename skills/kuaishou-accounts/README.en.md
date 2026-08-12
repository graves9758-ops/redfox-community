# Kuaishou Account Search / kuaishou-account-search

---

## Overview

Search for Kuaishou accounts by name with fuzzy matching. Instantly retrieve account nickname, avatar, bio, and `kwaiId` — the `kwaiId` can be directly used to query that account's full work list.

**Core Value**

- **Search by name**: Enter account name keywords to search — no need for exact IDs. Just type "人民日报" to find your target account.
- **Complete account profile**: Get nickname, avatar, cover image, and bio at a glance to quickly assess account positioning.
- **Seamless work query handoff**: The returned `kwaiId` can be directly passed to the work query skill for instant work list retrieval.
- **Paginated browsing**: Up to 50 results per page with multi-page support — never miss accounts with similar names.

**Target Users**

- 🔍 **Content creators** — Search for accounts in your niche and quickly identify benchmark targets.
- 📊 **Operations / data analysts** — Quickly locate target accounts and obtain their `kwaiId` for downstream work analysis.
- 🏢 **Brands / MCNs** — Screen potential partner influencers and evaluate account influence.

---

## Features

### Core Features

- **Fuzzy name search**: Search accounts by keyword — supports flexible queries like "人民日报" or "美食".
- **kwaiId retrieval**: Each account returns its platform display ID, ready for work list queries.
- **Complete account profile**: Nickname, avatar, cover image, and bio at a glance for quick account assessment.
- **Paginated browsing**: Up to 50 results per page with sequential browsing support.

---

## API Key Acquisition & Security

- This skill requires the environment variable: `REDFOX_API_KEY`.
- `REDFOX_API_KEY` is issued by [RedFoxHub](https://redfox.hk/settings/api-keys?source=github) (`https://redfox.hk`).
- Register at [RedFoxHub](https://redfox.hk?source=github) to obtain `REDFOX_API_KEY`.
- Configure `REDFOX_API_KEY` on your device before using this skill.
- Before providing your key, confirm its source, scope, validity period, and whether it supports reset/revocation.
- Do not hardcode or expose the key in plain text within code, prompts, logs, or output files.

---

## Usage Guide

Simply describe your needs in natural language — no commands to memorize.

### Quick Reference

| Intent | Example Query | Result |
| -------- | ---------------------------- | -------- |
| Search by name | "Search for Kuaishou accounts named 人民日报" | Returns matching accounts with nickname, kwaiId, and bio |
| Find influencers | "Find Kuaishou food bloggers for me" | Searches accounts by keyword, returns kwaiId and profile info |
| Get kwaiId | "Look up this blogger's kwaiId" | Returns the target account's platform display ID |
| Browse more pages | "Next page" | Continue viewing more search results |

### Example Output

After searching for "人民日报", you'll receive a formatted account list:

| # | Nickname | kwaiId | Bio |
|---|---------|--------|---------|
| 1 | 人民日报 | rmrbxmtzx | 参与、沟通、记录时代。 |
| 2 | 人民日报国际 | lingshichapd | 敬请关注"人民日报国际"... |

Each account includes nickname, kwaiId, bio, avatar, and cover image. The kwaiId can be directly used to query that account's work list.

---

## Use Cases

| Scenario | Role | Example Query | Benefit |
| -------- | -------- | -------- | -------- |
| Benchmark account discovery | Content Creator | "Search for Kuaishou accounts in my niche" | Quickly identify benchmark targets and get kwaiId for work analysis |
| Influencer screening | Brand / MCN | "Find Kuaishou beauty influencers for me" | Batch search by keyword to efficiently screen collaboration candidates |
| Account info lookup | Operations / Data Analyst | "Look up this Kuaishou account's details" | Get complete account profile including nickname, avatar, and bio |

---

## Data Notes

Data updates daily at **06:00 AM**, reflecting the snapshot from the previous day in the broad database.

---

## Related Capabilities

The retrieved `kwai_id` can be directly used with the **kuaishou-work-query** skill to query that account's work list.
