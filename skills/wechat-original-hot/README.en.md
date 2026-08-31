# WeChat Original Viral Articles / wechat-original-hot

---

## Introduction

Quickly find original viral articles on WeChat Official Accounts — get creative inspiration and stay on top of content trends.

**Core Value**

Continuously indexes daily original viral WeChat Official Account articles across the web, updated daily at 19:30 with yesterday's data. Query high-read original articles by 21 track categories and date range. Quickly find quality original benchmarks in each niche, reference peer hot content ideas with ease — a one-stop solution for daily topic research.

**Who It's For**

- 📝 WeChat editors / operators — Find topics and benchmarks
- 📊 Content planners — Filter original viral rankings by category
- 📈 Operations leads — Review by specific date + PDF export

---

## Core Capabilities

- **Original viral articles by category**: 21 track categories with colloquial terms auto-mapped to standard names for precise original viral discovery
- **Flexible time filtering**: Query by specific date or default to the past 7 days with "recent / latest"
- **One-click ranking page**: Auto-generates an HTML ranking page exportable to PDF after each table output
- **Niche subscription push**: Subscribe by track for daily 19:30 pushes of latest original viral data

### Highlights

- **Rankings only**: Outputs original viral article data only — no auto-generated viral pattern analysis or writing advice
- **Honest data timing**: "Latest available date" differs before vs after 19:30 — fixed messaging explains this
- **Low-volume niches**: When a track has too few results, prompts to switch category or widen the time range

---

## API Key Acquisition & Security

- This skill requires the environment variable: `REDFOX_API_KEY`.
- `REDFOX_API_KEY` is provided by [RedFoxHub](https://redfox.hk/settings/api-keys?source=github) (`https://redfox.hk`).
- Register at [RedFoxHub](https://redfox.hk?source=github) to obtain your `REDFOX_API_KEY`.
- Configure `REDFOX_API_KEY` as a device environment variable before using this skill.
- Before providing your key, confirm its source, available scope, validity period, and whether reset/revocation is supported.
- Do not hard-code or expose the key in plaintext in code, prompts, logs, or output files.

---

## Usage Guide

Describe what you need in plain language — no fixed commands to memorize.

### Quick phrase reference

| What you say                                                                   | What you get                                                  |
| ------------------------------------------------------------------------------ | ------------------------------------------------------------- |
| "Latest original viral articles", "today's originals", "viral recommendations" | Overall Top 20 table + data note + subscription prompt + HTML |
| "Tech / health / finance… original viral articles"                             | Matched category Top 20 + HTML                                |
| "May 3 original viral articles", "yesterday's viral posts"                     | Query by date + table + HTML                                  |
| "Recent / latest original hot articles"                                        | Default past 7 days Top 20                                    |

### Sample output

💡 **Data note**

WeChat original article recommendations update daily at 19:30 with yesterday's data. The data below is a snapshot at fetch time and may differ from real-time figures.

📊 **Original viral article recommendations**

| #   | Author           | Title                 | Reads |
| --- | ---------------- | --------------------- | ----- |
| 1   | [Author A](link) | [Article title](link) | 10w+  |
| 2   | [Author B](link) | [Article title](link) | 10w+  |
| …   | …                | …                     | …     |

50 viral original hot articles found; showing first 20.

📬 **Subscription**

Subscribe to a specific niche? We support subscriptions across 21 track categories.

1️⃣ Subscribe — Daily push of latest WeChat original articles at 19:30
2️⃣ Not now — This query only

---

## Use Cases

| Scenario              | Role               | Example question                         | Benefit                                       |
| --------------------- | ------------------ | ---------------------------------------- | --------------------------------------------- |
| Daily original topics | WeChat editor      | "Latest original viral articles"         | Latest original hot samples + shareable HTML  |
| Niche benchmarking    | Content planner    | "Tech original viral articles"           | Top ranking filtered by category              |
| Date-specific review  | Operations lead    | "May 3 original viral articles"          | Original viral list for that day + PDF export |
| Subscription push     | Regular ops rhythm | "Subscribe to finance original articles" | Daily scheduled original viral pushes         |

---

## Important data notes

### Update schedule and lookback

| Query type           | Update time                       | Lookback     | Default range |
| -------------------- | --------------------------------- | ------------ | ------------- |
| Original viral query | Daily 19:30 — previous day's data | Past 30 days | Past 7 days   |

### Supported niches (21)

Humanities & news, knowledge encyclopedia, health & wellness, fashion, food & dining, lifestyle, travel, humor, emotions & psychology, sports & entertainment, beauty, digest picks, wealth & finance, tech & digital, venture & business, automotive, real estate, career development, education & exams, academic research, corporate brands

### Data freshness

- Data is a **snapshot at fetch time** — may differ from live read counts
- "Latest available date" differs before vs after 19:30
- When a niche returns fewer than 10 articles, prompts to extend to 30 days or view the overall ranking

---
