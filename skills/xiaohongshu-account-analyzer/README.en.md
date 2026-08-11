# Xiaohongshu Account Deep Analysis / xiaohongshu-account-analyzer

---

## Overview

Deep-dive analysis of Xiaohongshu (REDnote) accounts, delivering a seven-dimension quantitative scoring diagnostic report with a visual HTML export — giving you a clear picture of account health, commercial value, and optimization opportunities.

**Core Value**

- Seven-dimension quantitative scoring (out of 100), covering positioning, followers, content topics, cover design, viral post ability, engagement, and posting consistency
- Auto-recommends 2–5 similar accounts for benchmarking, helping you identify gaps and learnable strategies
- One-click generation of a styled HTML report ready for export and sharing
- Multi-account comparison for batch evaluation of creator portfolios

**Who It's For**

- 👤 Xiaohongshu Creators — diagnose your own account, uncover positioning ambiguity and content direction issues
- 🏢 MCN Operators — batch-evaluate signed creators, identify high-potential accounts and those needing support
- 📈 Brands — screen collaboration candidates, assess commercial value and follower quality
- 🔍 Competitive Analysts — deconstruct competitor account strategies and discover actionable tactics

---

## Features

### Core Features

- Seven-dimension diagnostic scoring: Account Positioning, Follower Profile & Needs, Content Topic System, Cover Style, Viral Post Ability, Engagement Scale, Posting Consistency
- Lifecycle analysis: determine the account's current development stage
- Action prescription: deliver actionable optimization recommendations based on diagnostic results
- Similar account recommendations: suggest 2–5 comparable accounts
- Multi-account comparison: side-by-side analysis across multiple accounts
- HTML report generation: visual diagnostic report ready for export and sharing

---

## API Key Acquisition & Security

- This skill requires the environment variable: `REDFOX_API_KEY`.
- `REDFOX_API_KEY` is provided by [RedFoxHub](https://redfox.hk/settings/api-keys?source=github) (`https://redfox.hk`).
- Please visit [RedFoxHub](https://redfox.hk?source=github) to register an account and obtain your `REDFOX_API_KEY`.
- Configure the environment variable `REDFOX_API_KEY` on your device before using this skill.
- Before providing your key, please verify its source, available scope, validity period, and whether it supports reset/revocation.
- Never hardcode or expose API keys in plaintext within code, prompts, logs, or output files.

---

## Usage

Describe your needs in natural language — no commands to memorize.

### Quick Reference

| Intent | Example Prompt | Result |
| ------ | -------------- | ------ |
| Single account diagnosis | Analyze Xiaohongshu account 26112666886 | Seven-dimension diagnostic report, similar account recommendations, HTML report |
| Multi-account comparison | Compare accounts ID1 and ID2 | Individual reports + cross-comparison summary + comparison HTML |
| Analyze a similar account | Reply "1" to select a recommended account | Full diagnostic analysis of the selected account |

---

## Use Cases

| Scenario | Role | Example Prompt | Benefit |
| -------- | ---- | -------------- | ------- |
| Self-diagnosis | Xiaohongshu Creator | Help me diagnose my account | Get a seven-dimension score and targeted optimization advice |
| MCN batch evaluation | MCN Operator | Compare these signed creators for me | Identify high-potential accounts and those needing support |
| Brand influencer screening | Brand Marketer | Evaluate this influencer's commercial value | Inform collaboration and ad placement decisions |
| Competitor analysis | Strategist / Operator | Analyze this competitor's account strategy | Discover actionable strategies and exploitable gaps |

---

## Important Data Notes

- Analysis is based on the most recent 30 days of data for timeliness
- `gmtCreate` is the timestamp when RedFox data system first indexed the account, NOT the account's registration date on Xiaohongshu
