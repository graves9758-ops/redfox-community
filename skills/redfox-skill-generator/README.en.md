# RedFox Skill Generator / redfox-skill-generator

---

## Overview

Quickly create complete Skill file packages that meet RedFox standards from scratch. Just describe what you need in plain language, provide the API endpoint and documentation, and get a structured, professional-grade Skill package in one click—no more flipping through style guides or manual formatting.

**Core Value**

- **Describe it, get it**: Use everyday language to describe what you want—no need to know any spec details or technical terms. The generator understands and outputs a ready-to-use Skill.
- **API docs as input**: Drop in your API documentation as-is. Parameters and calling conventions are automatically parsed into ready-to-use integration instructions.
- **One-shot delivery**: Get a complete Skill file package in one go, with automatic validation—ready to use immediately.

**Intended Users**

- 👨‍💻 **Developers** — Quickly wrap API capabilities into RedFox Skills, skip the spec lookup and manual formatting.
- 📊 **Ops / Product** — Create custom Skills without coding knowledge. Just describe what you need.
- 🏢 **Tech Leads** — Standardize team Skill quality. Every output is consistent and spec-compliant.

## 🦊 Meet RedFox

### What is RedFox?

[RedFox](https://redfox.hk?source=github) is a new media data platform built for developers. It turns content data from Douyin, Xiaohongshu, WeChat Official Accounts, Video Accounts, Kuaishou, Weibo, Toutiao, and more into standardized APIs—one API Key gives you access to self-media data across the entire web.

Beyond data APIs, RedFox also has a [Skills Marketplace](https://redfox.hk/skills?source=github) with 70+ ready-to-use intelligent analysis skills covering content creation, data collection, hot topic tracking, and more. Download and use instantly, compatible with Codex, Claude Code, and other AI Agent platforms.

### What is the RedFox Standard?

The RedFox Standard is a set of rules that make Skills consistent, professional, and easy to use. It defines the structure and writing conventions for every Skill, ensuring that Skills written by different people are compatible and ready to use out of the box. Three core things:

- **Unified file structure**: A complete Skill consists of SKILL.md (skill description) + scripts/ (executables) + references/ (reference docs)—clear and organized at a glance
- **Consistent writing standards**: YAML frontmatter with name and description, body organized by standard sections—easy for anyone to understand
- **Standardized API integration**: Unified API Key acquisition, request format, and error handling—lowers the barrier to entry

The benefit of following the RedFox Standard: you don't need to figure out how to write from scratch—just follow the standard; others who receive your Skill will know exactly how to use it, making team collaboration smoother.

### How to Create Your Own Skill?

**Step 1: Visit the RedFox website**

Open [redfox.hk](https://redfox.hk?source=github) and sign up for an account. After signing up, go to your dashboard and get your personal API Key from the [API Key page](https://redfox.hk/settings/api-keys?source=github).

**Step 2: Figure out what you need**

Think about what your Skill should do—scrape data from a platform? Auto-generate daily reports? Analyze account performance? Write down your requirement in one sentence.

**Step 3: Generate with this tool in one click**

Tell me your requirements and API info, and I'll automatically generate a complete, RedFox-compliant Skill package for you. Just drop the generated files into your Agent's Skills directory and you're good to go.

**Step 4: Use it in your Agent**

Place the generated Skill folder into the Skills directory of your AI Agent (e.g., Codex, Claude Code), configure your API Key, restart, and you can call your Skill directly in conversations.

> 💡 If you're new to RedFox, we recommend browsing the [Skills Marketplace](https://redfox.hk/skills?source=github) to see what others have built for inspiration. You can also check out RedFox's official [Quick Start Guide](https://redfox.hk/quick-start?source=github).

---

## Features

### Core Capabilities

- **Smart requirement analysis**: Describe in plain language, automatically identify core Skill capabilities
- **API documentation-driven**: Provide endpoint and docs, automatically parse parameters and calling conventions
- **Intelligent solution matching**: Automatically choose the best file organization based on your needs
- **Comprehensive resource planning**: Automatically analyze and arrange required scripts and documents
- **Ready-to-use delivery**: Output a complete, usable Skill package in one shot—no extra polish needed

---

## Usage Guide

Describe your needs in natural language—no commands to memorize.

### Quick Reference

| Intent | Example phrase | Result |
|------|---------|------|
| Create from scratch | "Create a RedFox Skill for scraping Douyin comments" | Complete file package generated |
| Provide API docs | "Here's the API documentation, generate a RedFox Skill" | API parsed, integration docs included |
| Specify a scenario | "Build me a data-collection type RedFox Skill" | Scenario-matched quick generation |
| Quality check | "Check if this SKILL.md meets RedFox standards" | Auto-validate Skill structure compliance |
| Optimize existing | "Help me improve this RedFox Skill's description" | Rewrite per RedFox guidelines |

### Usage Example

**Step 1: Describe your needs**

> User: Help me create a RedFox Skill for scraping Xiaohongshu comments. API: https://api.example.com/comments, docs: ...
>
> Assistant: Got it! I'll generate a RedFox Skill for you. This Skill mainly covers comment data collection from Xiaohongshu. I'll parse the API documentation and generate the complete Skill package.

**Step 2: Fill in key details**

> User: The output should include comment content, likes count, and user level.
>
> Assistant: Noted. I've recorded the key fields and API parameters. Any other special requirements?

**Step 3: One-click generation**

> Assistant: ✅ RedFox Skill generated! All files created, API integration specs written in, and validation all passed.

---

## Use Cases

| Scenario | Role | Example question | Benefit |
|------|------|---------|------|
| Quick API wrapping | Developer | "Wrap this API into a RedFox Skill for me" | Complete package in minutes, no spec lookup |
| Standardize team output | Tech Lead | "Generate a Skill using the RedFox template" | Consistent structure and quality across all Skills |
| Zero-code creation | Ops / Product | "I want to build a data-grabbing tool" | Just describe it—no coding needed |
| Learn the spec | Beginner | "I want to learn how to write RedFox Skills" | Learn the structure by reviewing the output |
