# WeChat Channels Content Search / wechat-channels-crawler

---

## Overview

Enter a keyword to search for trending content on WeChat Channels, presented in a structured table with engagement data including likes, comments, shares, and saves—helping you quickly understand how different content categories are performing on the platform.

**Core Value**

- **Instant search**: Enter any content keyword and immediately receive a list of trending works sorted by relevance, newest, most likes, or most saves.
- **Comprehensive data**: Each result shows the author, likes, comments, shares, saves, and a clickable link to the original video.
- **Continuous tracking**: Subscribe to keywords of interest and receive daily push notifications with the latest trending data—never miss a trend.

**Intended Users**

- 🎬 **Content creators** — Track trending content in your niche on WeChat Channels for data-driven topic and creative inspiration.
- 🏢 **MCN / brand operators** — Quickly gauge the popularity and top-performing content for a specific category on WeChat Channels.
- 📊 **Growth / marketing teams** — Gain keyword-based content trend insights to inform campaign and topic strategy.

---

## Features

### Core Capabilities

- **Trending Search**: Keyword-based search for WeChat Channels popular content — precisely discover high-engagement works.
- **Multi-Dimensional Sorting**: Sort by relevance, newest, most likes, or most saves to switch perspectives on demand.
- **Smart Expansion**: Automatically expands generic keywords into niche directions, avoiding skewed results from broad search terms.
- **Clickable Links**: Work titles output as hyperlinks — one click to the original WeChat Channels video.
- **Subscription Push**: Subscribe to keywords after a search for daily automated updates with the latest trending content.

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

| Intent                          | Example phrase                                              | Result                                                                |
| ------------------------------- | ----------------------------------------------------------- | --------------------------------------------------------------------- |
| Search trending content         | "Latest food content on WeChat Channels"                    | Queries "food," returns a trending content table                      |
| Sort by popularity              | "Most liked workplace fashion videos on WeChat Channels"    | Sorts by most likes, displays high-engagement content                 |
| Find newest content              | "Search for latest travel videos on WeChat Channels"        | Sorts by newest, displays recently published works                    |
| Casual conversational search    | "What funny videos are trending on WeChat Channels?"        | Auto-extracts "funny," returns trending works                         |
| View next page                  | Select "Next page" after the table appears                  | Continues displaying the next page of results (up to 50)              |
| Subscribe to daily updates      | Select "Subscribe" after a search                           | Daily push at 10:00 AM with the latest trending content for that keyword |

### Output Example

After a search, you'll see a table like this (illustrative):

| #   | Work Title                                 | Author         | Likes  | Comments | Shares | Saves  | Published |
| --- | ------------------------------------------ | -------------- | ------ | -------- | ------ | ------ | --------- |
| 1   | Let me show you how to make this dish…     | FoodieA        | 305.2w | 7.1w     | 51.0w  | 14.7w  | 07-22     |
| 2   | Travel vlog: A spontaneous weekend trip…   | TravelBloggerB | 158.3w | 3.2w     | 22.1w  | 8.5w   | 07-21     |

(20 results shown by default; when there are more, you'll be prompted to view the next page.)

---

## Use Cases

| Scenario               | Role            | Example question                                                              | Benefit                                                                   |
| ---------------------- | --------------- | ----------------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| Topic research         | Content creator | "What food content is trending on WeChat Channels lately?"                    | Quickly pinpoint high-engagement directions, reduce blind trial-and-error |
| Competitive monitoring | Brand operator  | "Check the viral performance of the baby & maternity category on WeChat Channels" | Understand top content formats, inform campaign strategy                  |
| Trend tracking         | Marketing team  | "Is comedy content still popular on WeChat Channels?"                         | Judge niche heat by data, adjust direction in time                        |
| Daily monitoring       | Individual user | "Push me daily updates on travel trending content"                            | Subscribe once and receive automatic updates—never miss a trend           |

---
