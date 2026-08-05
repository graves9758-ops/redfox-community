# Douyin Similar Account Recommender / douyin-similar-account

---

## Overview

A benchmark account matching tool for Douyin creators. Using the RedFox Index, it intelligently recommends benchmark accounts and top-tier accounts, providing deep analysis of commonalities, differences, and optimization suggestions—helping creators pinpoint their niche, replicate proven strategies, and plan growth trajectories.

**Core Value**

- **Dual-group smart recommendations**: Delivers both "Benchmark Accounts" (5 closest above your RedFox Index—directly copy their playbooks) and "Top Accounts" (Top 5 by RedFox Index in the same category—mature models to chase).
- **RedFox Index gap quantification**: Every benchmark/top account displays its RedFox Index and the index gap, making the distance clear at a glance.
- **Deep analysis report**: Automatically summarizes commonalities, difference analysis, and provides actionable optimization suggestions.
- **Subscription push**: Subscribe to similar account update notifications, pushed daily at 19:00, with customizable frequency and time.

**Intended Users**

- 📝 **Douyin creators** — Find benchmark accounts in your niche to learn content strategies and operational tactics.
- 🛍️ **Brand / ad operators** — Screen high-match Douyin accounts for ad placement and business collaborations.
- 🏢 **MCN / content teams** — Analyze niche landscapes at scale and plan differentiated directions for matrix accounts.
- 🌱 **New account launchers** — Reference benchmark account growth paths to reduce launch trial-and-error costs.

---

## Features

### Core Capabilities

- **Smart query**: Search by Douyin nickname or Douyin ID—automatically identifies the input type.
- **Account data display**: Show basic account info, RedFox Index, follower count, view data, and recent works for the queried account.
- **Benchmark account recommendations**: Recommend the 5 closest same-niche accounts with higher RedFox Index—directly copy their operational playbooks.
- **Top account recommendations**: Recommend the Top 5 accounts by RedFox Index in the same category—mature models to reference and chase.
- **Deep analysis**: Automatically summarize commonalities and differences, providing actionable optimization suggestions.
- **Subscription push**: At the end of each query result, support subscribing to similar account update notifications with customizable frequency and time.

### Highlights

- **RedFox Index quantification**: Every account displays its RedFox Index and index gap, quantifying the benchmarking distance.
- **Multi-dimension recommendation reasons**: Covering content theme focus, viral work title quotes, publishing cadence, engagement rate, follower scale, and more.
- **Self-account pinned first**: The benchmark table's first row is your own account (bold), enabling intuitive comparison.
- **Multi-input flexibility**: Flexible queries by nickname or Douyin ID, with automatic Chinese-input detection.

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
| Search by nickname | "Find similar Douyin accounts for 一乐店长" | Automatic nickname match, outputting both benchmark and top account recommendations |
| Search by Douyin ID | "Find similar accounts for Douyin ID geng970616" | Precise ID-based query |
| Competitor benchmarking | "Analyze competitor accounts in my niche for me" | Output deep analysis report: commonalities, differences, and optimization suggestions |

### Output Example

After querying, you will receive the following structured analysis:

**Account Basic Info**: Nickname, Douyin ID, followers, total likes, RedFox Index, past-7-day metrics, and recent works

**✨ Benchmark Accounts (5 closest above your RedFox Index)**: Your account pinned first in bold for intuitive comparison

| Account | Followers | Total Likes | 7-Day Engagement | RedFox Index | Index Gap | Recommendation Reason |
| … | … | … | … | … | … | Multi-dimension analysis: content focus, viral quotes, cadence, engagement rate, etc. |

**✨ Top Accounts (Top 5 by RedFox Index in same category)**: Mature models to pursue

**📊 Deep Analysis**: Commonalities + Difference Analysis + Optimization Suggestions

---


---

## Use Cases

| Scenario | Role | Example question | Benefit |
| -------- | ---- | ---------------- | ------- |
| New account launch reference | New Douyin operator | "I just started a Douyin account—find me peer benchmarks at a similar stage" | Quickly find copyable operational models; lower launch trial-and-error costs |
| Content topic optimization | Douyin content operator | "My account traffic has been low lately—show me how top accounts in my niche are doing" | Analyze top benchmark viral patterns to break through content bottlenecks |
| Ad placement selection | Brand marketing manager | "Find food-niche Douyin accounts suitable for ad placement" | Precisely select placement accounts; improve ad ROI |
| Competitive analysis | MCN operations staff | "Analyze the food-niche Douyin competitive landscape for me" | Stay on top of competitor dynamics; discover differentiated opportunities |

---

## Important Data Notes

- Data is sourced from the RedFox data platform; the displayed data retrieval time may differ from real-time figures.
- The RedFox Index is updated weekly; if no works were published during the statistical period, the index may be 0.
- Engagement rates exceeding 100% are flagged as data anomalies and will not be output.
- Recommendation reasons follow an 8-level dimension standard; when the queried account's RedFox Index is 0, a "Learning Points Summary" mode is used instead.
> 💼 另外红狐配套全量数据库可提供完整详实数据，如需了解采购方案，可前往红狐hub[企业服务](https://redfox.hk/dashboard/enterprise)对接咨询

---
