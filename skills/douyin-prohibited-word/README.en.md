# Douyin Prohibited Word Checker / douyin-prohibited-word

---

## Overview

Detect prohibited words in copy, files, or web pages for Douyin (TikTok China), highlight hits in **bold**, and deliver replacement suggestions plus a safe revised version—so you can spot compliance risks before publishing.

**Core Value**

- 🔍 **Spot risks at a glance**: Hits are **bolded** in the original text so you see exactly what to fix
- 💡 **Reads naturally after edits**: Each hit gets a context-aware replacement and a clear reason—not a blunt find-and-replace
- ✏️ **Ready to publish**: Get a full revised copy in one go, plus an auto-generated plain-text file you can download

**Intended Users**

- 🎬 **Short-video creators / editors** — Pre-check voiceover scripts and subtitles to avoid throttling or takedowns
- 🛍️ **E-commerce operators** — Compliance-check product detail and campaign copy before listing
- 🎙️ **Live-stream script planners** — Quickly screen promo lines and live-room scripts
- 🏢 **Brand / marketing teams** — Spot-check landing pages and H5 campaign copy

---

## Features

### Core Capabilities

- **Prohibited-word highlighting**: Hits are **bolded** in the original text for instant visibility
- **Smart replacement suggestions**: Each hit includes a context-aware replacement and rationale—so edits flow naturally
- **Optimized copy generation**: Delivers a publish-ready full version with replacements **bolded** for easy copy-paste
- **Automatic file delivery**: Generates a downloadable plain-text optimized copy file
- **Batch checks for long copy**: Prompts when content exceeds 3,000 characters; supports batch detection with merged results

---

## API Key Acquisition & Security

- This skill requires the environment variable: `REDFOX_API_KEY`.
- `REDFOX_API_KEY` is issued by [RedFoxHub](https://redfox.hk/settings/api-keys?source=github) (`https://redfox.hk?source=github`).
- Register at [RedFoxHub](https://redfox.hk?source=github) to obtain `REDFOX_API_KEY`.
- Configure `REDFOX_API_KEY` on your device before using this skill.
- Before providing your key, confirm its source, scope, validity period, and whether it can be reset or revoked.
- Do not hard-code or expose keys in plain text in code, prompts, logs, or output files.

---

## Usage Guide

Describe your need in natural language—no commands to memorize. You can paste copy, upload TXT/DOC/DOCX files, upload images for text extraction, or paste a web page URL.

### Quick Reference

| Intent          | Example phrase                                                                        | Result                                                                       |
| --------------- | ------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| Paste copy      | "Check this Douyin script for prohibited words: This whitening product really works…" | Detection results, edit suggestions, optimized copy, and a downloadable file |
| Upload a file   | "[Upload script.docx] Check this document for me"                                     | Text is extracted automatically, then checked                                |
| Upload an image | "[Upload subtitle-screenshot.png] Check the text in this image for prohibited words"  | Text is extracted from the image and checked (text only—no visual analysis)  |
| Paste a URL     | "Check this page for prohibited words: https://example.com/article"                   | Page text is fetched automatically, then checked                             |
| Long copy       | When copy exceeds 3,000 characters, you'll be asked how to proceed                    | Choose first segment only, batch full check, or cancel                       |

### Output Example

After detection, you receive three sections (fixed order):

**🔍 Prohibited Word Detection Results** — Platform, hit count, and word categories

**💡 Edit Suggestions** — Prohibited word → replacement → reason (in a table)

**✏️ Suggested Optimized Copy** — Full revised text with replacements **bolded**, plus an auto-generated downloadable plain-text file

If no prohibited words are found, you only see: "No prohibited words detected. Copy is compliant ✅."

---

## Use Cases

| Scenario                    | Role                | Example question                                                         | Benefit                                                             |
| --------------------------- | ------------------- | ------------------------------------------------------------------------ | ------------------------------------------------------------------- |
| Pre-publish script check    | Creator / editor    | "Check this voiceover script for Douyin prohibited words"                | Avoid throttling or takedowns caused by risky wording               |
| Bulk product copy screening | E-commerce operator | "[Upload product-copy.docx] Screen for prohibited words before listing"  | Batch screening to reduce listing penalties from non-compliant copy |
| Live-stream script review   | Live script planner | "Are there sensitive words in this promo script? How should I fix them?" | Keep live-room scripts compliant and lower live-stream risk         |
| Landing page spot check     | Brand / marketing   | "Check whether the copy on this campaign page URL is compliant"          | Fast page copy review before going live                             |

---
