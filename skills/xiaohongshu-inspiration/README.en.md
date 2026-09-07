# Xiaohongshu Content Inspiration Expert / xiaohongshu-inspiration

---

## Introduction

One Skill covers the entire Xiaohongshu (RedNote) topic inspiration pipeline — from finding viral notes and tracking leaderboards to benchmarking accounts. Powered by RedFox's daily-collected Xiaohongshu viral library (notes with 1,000+ interactions, updated daily), it helps you find your next topic fast.

**Core Value**

- **Data-driven topic ideas**: Every recommendation comes from a daily-updated viral library — hot notes, leaderboards, and benchmark accounts are all backed by real interaction data, no more guesswork.
- **All-in-one pipeline**: Six capabilities in one entry point — viral note search, bulk data export, daily leaderboards, low-follower viral mining, and account benchmarking — no more piecing together tools.
- **Small-creator friendly**: Dedicatedly surfaces dark-horse notes with under 5,000 followers yet 500+ likes — viral samples a brand-new account can actually copy.
- **One-click report export**: Results can be exported as Excel spreadsheets and visual page reports, easy to view, share, and review in a browser.

**Who It's For**

- 📝 **Xiaohongshu creators** — Track viral content, find topics, and learn from dark-horse plays to lock in your next content direction.
- 📊 **Content operators** — Leaderboard tracking and bulk data pulls for data-driven topic planning.
- 🏢 **Brands / MCN agencies** — Find benchmark accounts and track niche rankings to make informed partnership and placement decisions.

---

## Features

### Core Features

- **Keyword viral note search**: Search viral notes by keyword (inclusion threshold: 1,000+ interactions), ranked by a three-dimensional score of relevance, popularity, and recency, with keyword expansion suggestions.
- **Bulk note data export**: Bulk-retrieve note data by keyword + date range + sort order (within the last 30 days), exportable as Excel spreadsheets and visual page reports.
- **Daily viral TOP50**: Query the daily "breakout notes" leaderboard — measured by interaction growth from day 2 to day 3 after publishing — with viral pattern analysis.
- **Low-follower viral mining**: Discover TOP50 dark-horse notes with under 5,000 followers and 500+ likes, with viral pattern analysis — great for topic ideas and title-writing techniques.
- **Account leaderboards**: Query daily / weekly / monthly account TOP50 leaderboards (weighted scoring of total followers plus follower, like, favorite, share, and comment growth within the period), covering 25 standard niches.
- **Benchmark account recommendations**: Enter an account ID or "niche + follower count + tier" to get same-tier benchmarks (similar follower counts, plays you can copy directly) and higher-tier role models (3-5x followers, worth studying and chasing).

---

## API Key Acquisition & Security

- This skill requires the environment variable: `REDFOX_API_KEY`.
- `REDFOX_API_KEY` is provided by [RedFoxHub](https://redfox.hk/settings/api-keys?souce=github) (`https://redfox.hk`).
- Please register at [RedFoxHub](https://redfox.hk?souce=github) to obtain your `REDFOX_API_KEY`.
- Configure the `REDFOX_API_KEY` environment variable on your device before using this skill.
- Before providing a key, confirm its source, scope of use, validity period, and whether it supports reset/revocation.
- Never hard-code or expose keys in plain text in code, prompts, logs, or output files.

---

## Usage Guide

Just describe what you need in natural language — no commands to memorize.

### Common Phrases

| Intent | Example | Result |
| --- | --- | --- |
| Search viral notes | "Search viral notes about mascara" | Viral note recommendations ranked by three-dimensional score + keyword expansion suggestions |
| Bulk data export | "Get August outfit note data and export to Excel" | Bulk note data for a custom date range + Excel / visual report |
| Daily viral leaderboard | "What are today's viral notes?" | TOP50 breakout leaderboard by interaction growth + viral pattern analysis |
| Mine low-follower virals | "Find viral notes from small accounts" | TOP50 dark-horse notes from low-follower accounts + pattern analysis |
| Check account leaderboard | "Xiaohongshu beauty daily leaderboard TOP50" | Niche account leaderboard + composite score + visual report |
| Find benchmark accounts | "Cooking niche, 3,000 followers, amateur — recommend benchmarks" | Same-tier benchmarks + higher-tier role models |

### Output Examples

**Keyword viral note search**: Query date range note + data table (note title / author / interactions / publish date / relevance / popularity / recency / total score) + recommended niche directions.

**Account leaderboard**: Leaderboard table (rank / account name / composite score / total followers / new notes, followers, likes, comments, favorites, shares) + ranking algorithm explanation + downloadable visual report.

**Benchmark account recommendations**: Same-tier benchmark table (account name / followers / 30-day interactions / recommendation reason) + higher-tier role model table + analysis summary.

---

## Use Cases

| Scenario | Role | Example Question | Benefit |
| --- | --- | --- | --- |
| Daily topic inspiration | Xiaohongshu creator | "What are today's viral notes?" | Daily TOP50 + pattern analysis to lock in topic directions fast |
| Niche research | Content operator | "Search viral notes about mascara" | Three-dimensional ranking + keyword expansion to map niche hotspots |
| New account growth | Beginner creator | "Find some low-follower viral notes to learn from" | Dark-horse samples under 5,000 followers — a growth path you can copy |
| Bulk data collection | Brand / MCN | "Export August outfit note data" | Bulk data + Excel / visual report, easy for team review |
| Account benchmarking & partnerships | Brand / MCN | "Find benchmark accounts in the beauty niche" | Same-tier benchmarks + higher-tier role models for both learning and placement |

---

## Important Data Notes

- Data covers **yesterday through 30 days ago**; today's data is not yet included. Interaction counts are as of ingestion time, not real-time.
- Update schedule: viral note search updates yesterday's data at 7:00 AM daily; the daily viral leaderboard updates at 19:00; low-follower virals update at 19:30; account leaderboards update daily at 19:00 (daily), Mondays at 15:00 (weekly), and the 1st of each month at 9:00 (monthly).
- Leaderboard lookback limits: 7 days for daily, 3 weeks for weekly, 3 months for monthly.
