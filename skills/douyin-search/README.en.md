# Douyin Content Search / douyin-search

---

## Overview

Enter a keyword to search for trending viral content on Douyin, presented in a structured table with engagement data including likes, comments, shares, and saves—helping you quickly understand how different content categories are performing on the platform.

**Core Value**

- **Instant search**: Enter any content keyword and immediately receive a list of viral works sorted by like count.
- **Comprehensive data**: Each result shows the author, likes, comments, shares, saves, and a clickable link to the original work.
- **Continuous tracking**: Subscribe to keywords of interest and receive daily push notifications with the latest trending data—never miss a trend.

**Intended Users**

- 📝 **Content creators** — Track viral content in your niche for data-driven topic and creative inspiration.
- 🏢 **MCN / brand operators** — Quickly gauge the popularity and top-performing content for a specific category on Douyin.
- 📊 **Growth / marketing teams** — Gain keyword-based content trend insights to inform ad placement and topic strategy.

---

## Features

### Core Capabilities

- **Viral Search**: Keyword-based search for Douyin viral works — precisely discover high-engagement content.
- **Date Filtering**: Filter by date range to pinpoint popular content within a specific timeframe.
- **Smart Expansion**: Automatically broadens generic keywords into 10 niche terms, avoiding skewed search results.
- **Hot Recommendations**: Recommends trending works and topics when no results found — never leave empty-handed.
- **Clickable Links**: Work titles output as hyperlinks — one click to the original Douyin video.
- **Subscription Push**: Subscribe to keywords for daily automated updates with the latest viral trends.

### Highlights

- **Generalization for guaranteed hits**: No need for precise keywords—casual, conversational input still yields effective results, lowering the learning curve.
- **One-click subscription**: No extra steps—search, subscribe, and receive daily push notifications to stay on top of trend changes.
- **Clickable data**: Every work title in the table links directly to the original Douyin page for deeper inspection.

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

Simply describe the content category you want to explore in natural language—no fixed commands to memorize.

### Quick Reference

| Intent                           | Example phrase                                         | Result                                                                |
| -------------------------------- | ------------------------------------------------------ | --------------------------------------------------------------------- |
| Search viral content by category | "Today's trending food content"                        | Auto-generalizes to "food," returns a viral content table             |
| Check a niche's performance      | "Is travel content popular on Douyin?"                 | Queries "travel," displays results sorted by likes                    |
| Casual conversational search     | "Funny videos seem hot lately"                         | Auto-extracts "funny," returns trending works                         |
| Filter by date range             | "Travel content from May 30 to June 2"                 | Parses date range, returns viral works from that period                |
| View all results                 | Select "View all" after the table appears              | Continues displaying remaining data (up to 50)                        |
| Subscribe to daily updates       | Select "Subscribe" after a search                      | Daily push at 10:00 AM with the latest viral content for that keyword |

### Output Example

After a search, you'll see a table like this (illustrative):

| #   | Work Title                                       | Author         | Likes  | Comments | Shares | Saves  | Published   |
| --- | ------------------------------------------------ | -------------- | ------ | -------- | ------ | ------ | ----------- |
| 1   | [Let me show you how to make this dish…](link)   | FoodieA        | 305.2w | 7.1w     | 51.0w  | 14.7w  | 06-01 19:55 |
| 2   | [Travel vlog: A spontaneous weekend trip…](link) | TravelBloggerB | 158.3w | 3.2w     | 22.1w  | 8.5w   | 05-30 15:30 |

(20 results shown by default; when there are more, you'll be prompted to view all.)

---

## Use Cases

| Scenario               | Role            | Example question                                                         | Benefit                                                                   |
| ---------------------- | --------------- | ------------------------------------------------------------------------ | ------------------------------------------------------------------------- |
| Topic research         | Content creator | "What food content is trending on Douyin lately?"                        | Quickly pinpoint high-engagement directions, reduce blind trial-and-error |
| Competitive monitoring | Brand operator  | "Check the viral performance of the baby & maternity category on Douyin" | Understand top content formats, inform ad strategy                        |
| Trend tracking         | Marketing team  | "Is comedy content still popular on Douyin?"                             | Judge niche heat by data, adjust direction in time                        |
| Daily monitoring       | Individual user | "Push me daily updates on travel viral content"                          | Subscribe once and receive automatic updates—never miss a trend           |

---
