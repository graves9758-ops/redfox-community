# WeChat Cover Design / wechat-cover

---

## Introduction

Based on daily collected **100K+** article data from across the web, this tool retrieves visual elements from explosive covers in the same niche, analyzes high-conversion visual patterns through AI, and generates cover design proposals that match your content and fit the platform's traffic aesthetics.

**Core Value**

- **Massive Sample Alignment**: Continuously collects explosive article covers daily, ensuring design proposals are data-driven rather than imagined.
- **Analyze First, Design Later**: Completes explosive cover style analysis and classification before outputting design proposals, making patterns clear and easy to choose.
- **Proposal + Image Generation All-in-One**: Each proposal includes image generation prompts; after selection, a 2.35:1 cover image can be generated directly.

**Target Users**

- ✍️ **WeChat Official Account Creators** — Stop struggling with cover design, use explosive patterns to boost article click rates.
- 📊 **Content Operators** — Quickly produce multiple cover proposals by niche keywords for efficient A/B testing.
- 🏢 **MCN / New Media Teams** — Batch propose covers for the same niche, building reusable visual templates.

---

## Features

### Core Features

- **Keyword-Driven**: Enter a niche or content keyword to automatically retrieve explosive cover data for that field.
- **7-Dimension Cover Analysis**: Analyzes each cover image across text content, main elements, color characteristics, composition layout, visual style, click appeal, and dimensions for deep pattern extraction.
- **Style Classification Summary**: Groups similar-style covers into categories, displaying representative covers and characteristic patterns by type.
- **3 Design Proposals**: Generates 3 differentiated cover design proposals based on analysis results, each with core visuals, case references, and image generation prompts.
- **One-Click Image Generation**: After selecting a proposal, directly generates a 2.35:1 (900×383) cover image; supports uploading reference images.

---

## API Key Acquisition & Security

- This skill requires the environment variable: `REDFOX_API_KEY`.
- `REDFOX_API_KEY` is provided by [RedFoxHub](https://redfox.hk/settings/api-keys?souce=github) (`https://redfox.hk`).
- Please visit [RedFoxHub](https://redfox.hk?souce=github) to register an account and obtain `REDFOX_API_KEY`.
- Configure the environment variable `REDFOX_API_KEY` on your device before using this skill.
- Before providing a key, please confirm its source, scope of use, validity period, and whether it supports reset/revocation.
- Never hard-code or expose keys in plain text within code, prompts, logs, or output files.

---

## Usage Guide

Simply describe your niche, content topic, or cover needs in natural language — no commands to memorize.

### Quick Reference

| Intent | Example Phrase | Result |
|--------|----------------|--------|
| Design by niche | "Design a beauty tutorial cover for me" | Retrieves beauty niche explosive cover data, analyzes styles, generates 3 proposals |
| Design by content topic | "Autumn whitening skincare tips, want a professional-looking cover" | Parses content intent, matches professional-style cover patterns |
| Upload reference image | "Design a cover referencing this image" + upload | Analyzes reference image style, combines with explosive data to generate proposals |
| Select proposal to generate | Reply "Choose proposal 1" | Generates 900×383 cover image per the proposal prompt |

### Output Example

After analysis, you'll receive a visual cover analysis report (HTML page) containing:

- **Style Classification Display**: Representative covers and characteristic patterns for each style type
- **3 Design Proposals**: Each with style name, core visuals, case references, and image generation prompts
- **Proposal Selection Area**: Select a proposal to generate the cover image

---

## Use Cases

| Scenario | Role | Example Question | Benefit |
|----------|------|------------------|---------|
| New article cover | WeChat creator | "Publishing skincare tips today, help me design a cover" | Generate professional cover proposals based on explosive data |
| Niche daily updates | Content operator | "Workplace fashion niche, need a set of cover proposals" | Quickly produce multiple style proposals for A/B testing |
| Custom with reference | Designer | "Design a cover referencing this image" + upload | Combine reference image with explosive patterns |
| Trend-chasing covers | Media editor | "See what covers are hot in the beauty niche lately" | Get recent explosive cover styles, stay on trend |

---

## Important Data Notes

- The database only contains data from yesterday to 30 days ago
- Default time range is the last 30 days
