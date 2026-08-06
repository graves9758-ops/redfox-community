# WeChat Subscription Tracker / gzh-subscribe

---

## Overview

Your public account content radar. Subscribe to competitors, peers, and followed accounts — auto-fetch daily posts with clear table display and visualized daily report.

**Core Value**

- **Inbox-Style Subscription**: Subscribe to public accounts like newsletters, up to 20, name-only (WeChat ID optional)
- **Daily 6 AM Delivery**: One-click cron setup for automated curated daily reports, auto-opens in browser
- **Three-Category Grouping**: Competitors for tracking rivals, Peers for inspiration, Favorites for following experts
- **Key Metrics at a Glance**: Publish date, title, summary, reads, likes — article link one-click away

**Target Users**

- 🏢 **Competitive Monitors** — Track competitor posts and stay informed
- 📝 **Content Creators** — Follow industry leaders for creative inspiration
- 🔍 **Researchers** — Subscribe to focused accounts for daily aggregation

---

## Features

### Core Features

- Subscribe by account name (WeChat ID optional), up to 20 accounts
- Three categories (Competitors / Peers / Favorites), grouped in daily reports
- Daily 06:00 scheduled fetch, auto-generates visualized report and opens browser
- Terminal table display: publish date, title, summary, reads, likes in clear format
- Date backtrack support to review historical posts
- Fetched data works with LLMs for summary rewriting and style imitation

---

## API Key Acquisition & Security

- This skill requires the environment variable: `REDFOX_API_KEY`.
- `REDFOX_API_KEY` is provided by [RedFoxHub](https://redfox.hk/settings/api-keys?source=github) (`https://redfox.hk`).
- Visit [RedFoxHub](https://redfox.hk?source=github) to register and obtain your `REDFOX_API_KEY`.
- Configure the device environment variable `REDFOX_API_KEY` before using this skill.
- Before providing your key, verify its origin, scope, validity period, and whether reset/revocation is supported.
- Never hardcode or expose the key in code, prompts, logs, or output files.

---

## Usage

Manage your subscriptions in natural language — no commands to memorize.

### Quick Reference

| Intent | Example | Result |
|--------|---------|--------|
| Add subscription | "Subscribe to QbitAI public account" | Adds account to watchlist |
| Competitor tracking | "Add XX account to competitor monitoring" | Categorized as competitor, prioritized in reports |
| View posts | "Fetch today's posts from my subscriptions" | Retrieves all subscribed accounts' daily posts |
| View report | "Generate today's subscription daily report" | Fetches posts and generates visualized report |
| Enable push | "Push public account daily report every morning" | Installs cron job for 06:00 auto-push |
| Remove subscription | "Unsubscribe from XX account" | Removes from watchlist |

---

## Use Cases

| Scenario | Role | Example Query | Benefit |
|----------|------|--------------|---------|
| Morning briefing | Product manager | "What did my subscribed accounts post today?" | One-screen overview of all subscriptions |
| Competitor monitoring | Marketing ops | "What are competitor accounts posting lately?" | Track strategies, adjust responses timely |
| Inspiration gathering | Content creator | "Any new articles from industry leaders today?" | Follow top accounts for topic ideas |
| Content processing | Researcher | "Export this batch of article data for analysis" | Combine with LLMs for rewriting and style imitation |
