# WeChat Official Account Subscription Tracker / gzh-subscribe

---

## Introduction

Your content radar for WeChat Official Accounts. Subscribe to competitor, peer, and followed accounts, and automatically fetch their latest articles every morning at 6 AM. Each article is presented in a clean table showing publish date, author, title, summary, read count, like count, and the original link — with a one-click visual daily report.

**Core Value**

- **Newsletter-style subscription**: Subscribe to Official Accounts just like a newsletter, up to 20 accounts, organized into three groups: Competitors / Peers / Followed.
- **Punctual daily delivery**: Enable the scheduled task once, and a curated daily report is generated and opened in your browser at 06:00 every morning — reading Official Accounts like checking email.
- **Key metrics at a glance**: Publish date, title, summary, read count, and like count in one table, with one-click access to the original article.
- **Dual reading modes**: Real-time tables in the terminal, plus a visual daily report ideal for sharing and archiving.

**Who It's For**

- 📊 **Brand / Marketing Operators** — Keep an eye on competitor accounts and stay on top of their topics and moves.
- ✍️ **Content Creators** — Track peer accounts and industry leaders for continuous topic inspiration and writing references.
- 🔍 **Industry Researchers** — Archive daily articles from followed accounts as daily reports for easy review.

---

## Features

### Core Capabilities

- **Subscription management**: Add, remove, and list subscriptions for up to 20 Official Accounts; account IDs accept three formats (account / wxId / bizInfo) — any one of them works.
- **Three-group organization**: "Competitors" to watch rivals, "Peers" to find inspiration, "Followed" to track industry leaders; the daily report is grouped accordingly.
- **Daily article fetching**: Pull the latest articles from all subscribed accounts in one go, including title, author, summary, read count, like count, publish time, and original link.
- **Visual daily report**: Automatically generates a polished report page, organized by group and opened in your browser — ready for sharing and archiving.
- **Automatic daily delivery**: Enable the 06:00 daily push with one command to generate the report automatically every day; cancel anytime.

---

## API Key Acquisition & Security

- This skill requires the environment variable: `REDFOX_API_KEY`.
- `REDFOX_API_KEY` is provided by [RedFoxHub](https://redfox.hk/settings/api-keys?source=github) (`https://redfox.hk`).
- Please visit [RedFoxHub](https://redfox.hk?source=github) to register an account and obtain your `REDFOX_API_KEY`.
- Configure the `REDFOX_API_KEY` environment variable on your device before using this skill.
- Before providing your API key, please confirm its source, scope of access, validity period, and whether it supports reset/revocation.
- Do not hardcode or expose the API key in plain text in code, prompts, logs, or output files.

---

## Usage Guide

Just describe what you need in natural language — no commands to memorize.

### Common Phrases Cheat Sheet

| Intent                 | Example Phrase                                                                                          | Result                                                            |
| ---------------------- | ------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------- |
| Subscribe to an account | "Subscribe me to the RedFox Data Official Account, ID redfoxdata1, under Followed accounts"            | Added to your subscription list, ready for fetching anytime       |
| View subscriptions     | "Show me which Official Accounts I've subscribed to"                                                    | Lists all subscribed accounts by group                            |
| Fetch articles         | "Pull the latest articles from my subscribed accounts"                                                  | Shows the latest articles and metrics in a terminal table         |
| Generate daily report  | "Generate today's Official Account daily report for me"                                                 | Generates the visual daily report and opens it in your browser    |
| Automatic daily push   | "Turn on the 6 AM daily Official Account push"                                                          | Installs a scheduled task that generates and opens the report daily |
| Unsubscribe            | "Unsubscribe RedFox Data"                                                                               | Removes the account from your subscription list                   |

### Output Example

After fetching, the terminal table lists each article by account with publish date, author, title, summary, read count, like count, and original link. A visual daily report is also generated, organized into Competitors / Peers / Followed groups — ideal for sharing and archiving.

---

## Use Cases

| Scenario              | Role                    | Example Question                                                                  | Benefit                                                                      |
| --------------------- | ----------------------- | --------------------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| Morning briefing      | Content operator        | "Turn on the 6 AM automatic Official Account push"                                | Receive a daily article report from subscribed accounts, like checking email |
| Competitor monitoring | Brand / Marketing       | "Add competitor accounts to the Competitors group and show what they posted yesterday" | See all competitor articles with read and like counts on one screen          |
| Close following       | Creator                 | "Add top industry accounts to Followed and tell me as soon as they publish"       | Industry leaders' updates are shown first, so you never miss a new article   |
| Content repurposing   | Advanced creator        | "Give me today's fetched article data so I can summarize and rewrite it"          | Fetched results can be fed to AI for summarizing, rewriting, and archiving   |

---

## Important Data Notes

- Data comes from the RedFox wide-coverage database with broad account coverage; it is updated on a T+1 basis, fetching articles from the previous day and the last 7 days.
- The subscription limit is 20 Official Accounts; each fetch consumes data quota based on the number of subscriptions, so enabling the automatic daily push is recommended over frequent manual fetches.
- If the account ID is confirmed correct but still cannot be found in the wide-coverage database, contact RedFox Data for customized support: redfoxdata@proton.me.

---
