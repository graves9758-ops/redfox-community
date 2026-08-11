# Bilibili Search & Download / bilibili-search-download

---

## Overview

Bilibili Search & Download is a smart video collection tool. Enter a keyword to search across Bilibili, automatically fetching all HD download links after search — combining search, filter, and download into one seamless workflow.

**Core Value**

- Search across all Bilibili with a single keyword, eliminating manual page-by-page browsing
- Automatically batch-fetch all video download links after search, no manual selection needed
- Auto-resolve the highest available quality, returning video, audio, and cover resources simultaneously

**Target Users**

- Content Creators — Quickly gather video materials and inspiration
- Brand Operators — Monitor competitors' content on Bilibili
- Marketing Planners — Research trending topics and content direction
- MCN Agencies — Batch collect creator videos for analysis
- Video Editors — Obtain HD source files for secondary creation

---

## Features

### Core Capabilities

- **Keyword Search**: Search across all Bilibili with any keyword, with pagination and multi-dimensional sorting (publish time / views / likes / comments / favorites)
- **Auto Batch Download**: Automatically fetch all video download links and cover images after search, no manual selection
- **HD Resolution**: Auto-resolve the highest available quality, returning video streams, audio streams, and covers
- **Credit Protection**: Proactive credit consumption estimation before search and pagination, execution after confirmation

---

## Usage Guide

Describe your needs in natural language — no commands to memorize.

### Quick Reference

| Intent | Example | Result |
|--------|---------|--------|
| Search videos | "Search Bilibili for down jacket reviews" | Keyword search with auto batch download links |
| Sort search | "Search Bilibili for phone reviews sorted by newest" | Search with specified sorting, auto download links |
| Next page | "Next page" | Next page of results with auto download links |
| Direct download | "Download https://www.bilibili.com/video/BVxxx/" | Direct download via link |

### Output Example

**Search results** are displayed as a table with keyword, total results, sort method (default: by views descending), and page number at the top. The table includes serial number, video title, uploader, views, likes, comments, and favorites. **Download results** show each video's title, cover image, download link, and resource type.

---

## Installation

This skill is a standard Skill file package, compatible with all AI Agent platforms that support the Skill mechanism. Place the skill folder into the Skills directory of your target platform.

Prerequisites: Python 3.6+, no additional dependencies required.

Configure the data service access credential (REDFOX_API_KEY) — see the Usage Guide > Authentication Configuration section.

---

## Use Cases

| Scenario | Role | Example Query | Benefit |
|----------|------|---------------|---------|
| Quick Material Collection | Video Creator | "Search Bilibili for AI art tutorials" | Material collection reduced from hours to minutes |
| Competitor Monitoring | Brand Operator | "Search Bilibili for XX brand newest videos sorted by time" | Timely competitive content strategy insights |
| Trending Research | Marketing Planner | "Search Bilibili for XX topic sorted by views" | Quickly grasp platform content trends |
| Secondary Creation | Video Editor | "Download this Bilibili video link" | Direct access to HD source files |

---

## Get Help

- RedFoxHub Official: [https://redfox.hk?source=github](https://redfox.hk?source=github)
- Enterprise Services: [https://redfox.hk/dashboard/enterprise?source=github](https://redfox.hk/dashboard/enterprise?source=github)
