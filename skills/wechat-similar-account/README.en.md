# WeChat Official Account Benchmarking Tool / wechat-similar-account

---

## Overview

A benchmark account matching tool for WeChat Official Account creators. Using a 3-tier weighted matching system (Core Fundamentals 40% + Operations & Monetization 35% + Data Characteristics 25%), it intelligently recommends peer benchmark accounts and top-tier aspirational accounts—helping creators pinpoint their niche, replicate proven strategies, and plan growth trajectories.

**Core Value**

- **Dual-group smart recommendations**: Delivers both "Peer Benchmarks" (copyable playbooks) and "Top Aspirationals" (mature models to chase) in a single query, meeting needs at every growth stage.
- **3-tier weighted matching**: Core fundamentals (niche/tags/content format/audience profile) + Operations & monetization (cadence/traffic/private domain/revenue) + Data characteristics (engagement structure/viral patterns/resource endowments)—scientifically grounded and actionable.
- **7-dimension recommendation reasons**: Each recommended account comes with detailed analysis spanning viral insights, content focus, publishing cadence, engagement rate, and share rate—with automatic fallback to RedFox Index when data is sparse.
- **Subscription push**: Subscribe to benchmark account push notifications with daily data updates to continuously track niche dynamics.

**Intended Users**

- 📝 **WeChat Official Account creators** — Find benchmark accounts in your niche to learn content strategies and operational tactics.
- 🛍️ **Brand / ad operators** — Screen high-match accounts for advertising placements and business collaborations.
- 🏢 **MCN / content teams** — Analyze niche landscapes at scale and plan differentiated directions for matrix accounts.
- 🌱 **New account launchers** — Reference peer benchmark growth paths to reduce launch trial-and-error costs.

---

## Features

### Core Capabilities

- **Smart query**: Search by account name, account ID, or account category—also supports combined queries for precise targeting.
- **Account diagnostics**: Display basic account info, RedFox Index, readership data, and the latest 5 articles for the queried account.
- **Peer benchmark recommendations**: Recommend same-niche accounts with the closest readership numbers—directly copy their operational playbooks.
- **Top aspirational recommendations**: Recommend mature accounts with 3–5× your readership—reference their operational models to catch up.

### Highlights

- **3-tier weighted matching system**: Core fundamentals (40%) + Operations & monetization (35%) + Data characteristics (25%), covering every dimension from content positioning to revenue model.
- **7-dimension personalized reasons**: Covering viral title quotes, publishing schedule patterns, share virality, engagement rate, and more—with automatic fallback when data is sparse.
- **Subscription push**: Subscribe to benchmark account push notifications with daily updated data.
- **Multi-input flexibility**: Flexible queries by name / ID / category, with combined queries for greater precision.

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
| Search by account name | "Find benchmark accounts for TechFrontier" | Precise name match, outputting both peer benchmarks and top aspirationals |
| Search by account ID | "Find benchmarks for account ID gh_xxx" | Precise ID-based query |
| Explore by category | "Recommend benchmark accounts in the tech-digital category" | Category-based query to explore niche landscape |

### Output Example

After querying, you will receive the following structured analysis:

**Account Basic Info**: Account name, ID, category, RedFox Index, average reads, past-7-day metrics, and the latest 5 articles

**✨ Peer Benchmarks (5)**: Accounts closest to your readership level—directly reference their content strategy

| Account | RedFox Index | Avg Reads | 7-Day Reads | 7-Day Posts | Recommendation Reason |
| … | … | … | … | … | Multi-dimension analysis: viral insights, content focus, cadence, engagement rate, etc. |

**✨ Top Aspirationals (5)**: Top-tier accounts with 3–5× your readership—mature models to pursue

---

> 💼 RedFox also offers a comprehensive full-scale database with detailed data. For enterprise procurement plans, visit RedFox Hub [Enterprise Services](https://redfox.hk/dashboard/enterprise) for consultation.

---

## Use Cases

| Scenario | Role | Example question | Benefit |
| -------- | ---- | ---------------- | ------- |
| New account launch reference | New account operator | "I just created an account—find me peer benchmarks at a similar stage" | Quickly find copyable operational models; lower launch trial-and-error costs |
| Content topic optimization | Account content operator | "My reads have plateaued—show me how top accounts in my niche are performing" | Analyze top aspirational viral patterns to break through content bottlenecks |
| Ad placement selection | Brand marketing manager | "Find tech-digital accounts with 10k+ reads for ad placement" | Precisely filter placement accounts by niche and readership; improve ad ROI |
| Competitive analysis | MCN operations staff | "Analyze the parenting niche competitive landscape for me" | Stay on top of competitor dynamics; discover differentiated opportunities |

---

## Important Data Notes

- Data is sourced from the RedFox data platform; the displayed data retrieval time may differ from real-time figures.
- Recommended account metrics (reads, engagement, etc.) are based on platform data; engagement counts should not be used as read counts.
- When searching by category, the platform's classification system may differ from natural language; using a representative account name for lookup is recommended.
- Maximum displayed read count is 100,001 (10w+ cap); actual readership may be higher.

---
