# Kuaishou Account Works / kuaishou-account-works

---

## Overview

A Kuaishou work query tool covering both account work lists and single work details. Get complete engagement data—views, likes, comments, collects, shares—in one go to fully understand target accounts and viral work performance.

**Core Value**

- **Dual-scenario coverage**: Pull a full work list by account or drill into a single work's details—one tool, two needs.
- **Full data dimensions**: Views, likes, comments, collects, shares, forwards, duration, cover images, and video links—all available at a glance.
- **Paginated browsing**: Up to 50 items per page with multi-page navigation, so no content gets missed.

**Intended Users**

- 🔍 **Content creators** — Analyze competitor account work structures, drill into viral hits, and study viral patterns.
- 📊 **Operations / data analysts** — Track account posting frequency and traffic trends; precisely monitor individual work performance.
- 🏢 **Brands / MCNs** — Screen partner creator performance and evaluate the real value of individual collaborations.
- 🛒 **E-commerce product selectors** — Review the latest works from product-promoting accounts to match promotion strategies.

---

## Features

### Core Capabilities

- **Dual-ID query**: Locate accounts by platform display ID or profile link ID—works with either input.
- **Account work list**: Accurately match all visible works of an account, displayed in reverse chronological order.
- **Single work detail**: Query the complete data of a single work by its ID to uncover metrics behind viral hits.
- **Full engagement data**: Views, likes, comments, collects, shares, forwards, duration—assess work performance comprehensively.
- **Paginated browsing**: Up to 50 items per page; browse page by page without missing large volumes of content.
- **Direct work access**: Output cover images and video links for quick viewing or downloading.

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

Simply describe your query needs in natural language—no commands to memorize.

### Quick Reference

| Intent | Example phrase | Result |
| -------- | ---------------------------- | -------- |
| Query work list by account | "Show me the Kuaishou works of People's Daily" | Returns all works with views, likes, and other data, sorted by time |
| Query work list by ID | "Search Kuaishou works for kwaiId rmrbxmtzx" | Locates the account by its platform display ID and returns the work list |
| Query single work detail | "Show me the data for this Kuaishou work, ID is xxx" | Returns complete engagement data and content info for that work |
| Dive into viral hits | "Analyze the metrics of this viral work" | Checks all indicators of a single work to aid review and topic research |
| Browse more pages | "Next page" | Continues viewing subsequent works without missing any content |

### Output Example

After querying an account's work list, you receive a formatted data table:

| # | Title | Views | Likes | Comments | Collects | Published |
|---|---------|--------|--------|--------|--------|---------|
| 1 | [Work Title](video link) | 65.5w | 1.2w | 305 | 8.7w | 2026-07-29 21:46:58 |

Each work includes title, author, follower count, views/likes/comments/collects/shares/forwards, duration, cover image, and video link, with pagination support.

---

## Use Cases

| Scenario | Role | Example question | Benefit |
| -------- | -------- | -------- | -------- |
| Competitor account research | Content creator | "Show me what this account has posted recently" | Understand competitor posting frequency, content direction, and data performance |
| Viral work review | Operations / data analyst | "Show me the detailed data on this viral work" | Extract all metrics from a single hit to distill viral patterns |
| Creator evaluation | Brand / MCN | "Pull this creator's work list and show me the data" | Quickly assess a partner creator's content quality and audience engagement |
| Product selection reference | E-commerce product selector | "Show me recent work data for this product-promoting account" | Understand product-promotion content strategy to aid selection decisions |

---

## Important Data Notes

Data refreshes daily at **06:00**, reflecting a snapshot of the database as of the previous day.

---
