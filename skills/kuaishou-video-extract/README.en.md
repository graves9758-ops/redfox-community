# Kuaishou Video Extract / kuaishou-video-extract

---

## Overview

Extract speech text from Kuaishou videos with a single link. Automatically submits and retrieves results, delivering the full transcript along with timestamped sentences. Supports task ID-based resume queries—an efficient tool for replicating viral scripts and generating subtitles.

**Core Value**

- **One-click extraction**: Paste a video link and the full process runs automatically—speech to text in one step.
- **Full transcript + timestamps**: Receive both the concatenated full text and per-sentence timestamps, covering script replication and subtitle production needs.
- **Resume queries without loss**: If processing times out or is interrupted, resume by task ID—no lost tasks.

**Intended Users**

- 🔍 **Content creators** — Replicate viral video scripts and deconstruct topic structures.
- 📊 **Operations / data analysts** — Quickly transcribe video content and evaluate copy quality.
- 🎬 **Video editors / subtitlers** — Use timestamped sentences to rapidly generate subtitle drafts.

---

## Features

### Core Capabilities

- **One-click text extraction**: Submit a video link and the extraction process runs automatically.
- **Full transcript output**: Returns the complete concatenated text from all segments for direct script replication.
- **Timestamped sentences**: Each sentence includes precise start and end times for seamless subtitle production and editing.
- **Task resume**: Continue querying by task ID if processing times out or is interrupted.
- **Status compatibility**: Compatible with multiple processing states for stable and reliable extraction.

---

## API Key Acquisition & Security

- This skill requires the environment variable: `REDFOX_API_KEY`.
- `REDFOX_API_KEY` is issued by [RedFoxHub](https://redfox.hk/settings/api-keys?source=github) (`https://redfox.hk`).
- Register at [RedFoxHub](https://redfox.hk?source=github) to obtain `REDFOX_API_KEY`.
- Configure `REDFOX_API_KEY` on your device before using this skill.
- Before providing your key, confirm its source, scope, validity period, and whether it can be reset or revoked.
- Do not hard-code or expose keys in plain text in code, prompts, logs, or output files.

---

## Usage Guide

Simply describe your needs in natural language—no commands to memorize.

### Quick Reference

| Intent | Example phrase | Result |
| -------- | ---------------------------- | -------- |
| Extract video text | "Extract the speech text from this Kuaishou video" | Paste the link to auto-extract and return the full transcript |
| Get subtitle timestamps | "Give me the transcript with timestamps for this video" | Returns timestamped sentence list for subtitle creation |
| Resume a task | "Check the extraction result for that video from earlier" | Continue querying by task ID without losing the task |
| Replicate viral scripts | "Extract the script from this viral video so I can analyze its structure" | Get the full speech draft to aid script deconstruction and adaptation |

### Output Example

After successful extraction, you receive:

📝 Full transcript:

> In this video, a 3-year-old child named Miaomiao… The vegetables sizzle in the oil in the pan…

Optionally view per-sentence timestamps:

| # | Time range | Transcript segment |
|---|---------|---------|
| 1 | 0.20s - 6.72s | In this video, a 3-year-old child named Miaomiao… |
| 2 | 7.00s - 9.88s | The vegetables sizzle in the oil in the pan. |

---

## Use Cases

| Scenario | Role | Example question | Benefit |
| -------- | -------- | -------- | -------- |
| Viral script replication | Content creator | "Extract the transcript from this viral video" | Get the full speech draft to deconstruct topic structure and script patterns |
| Video content analysis | Operations / data analyst | "Transcribe what this video says" | Quickly understand video content and evaluate copy quality and information density |
| Subtitle production | Video editor / subtitler | "Extract the transcript and timestamps from this video" | Use per-sentence timestamps to rapidly generate subtitle drafts with precise frame alignment |

---
