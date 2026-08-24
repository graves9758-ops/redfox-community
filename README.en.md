<p align="center">
  <a href="https://redfox.hk/?source=github">
    <img src="https://lyy.redfox.hk/page/logo-redfox-name.png" alt="RedFox Logo" width="200">
  </a>
</p>

<p align="right">
  <a href="https://github.com/redfox-data/redfox-community/blob/main/README.md">中文</a>
  English
</p>

# redfoxdata · Agent Skills

This repository hosts **Agent Skills** maintained by the **redfoxdata** community for inspiration, topic research, copywriting, and data review workflows. Each skill is centered on `SKILL.md` and works with tools that support Agent Skills, such as Cursor and Claude Code.

## Repository layout

```text
.
├── README.md          # Chinese README
├── README.en.md       # This file (English)
├── skills/            # One skill per subdirectory
│   └── <skill-name>/
│       ├── SKILL.md
│       └── …          # Optional scripts, references, assets
```

## Skill directory conventions

Each skill lives in its **own subdirectory** and must include at least:

| File       | Purpose                                                                   |
| ---------- | ------------------------------------------------------------------------- |
| `SKILL.md` | Skill entry: YAML frontmatter + body (triggers, steps, constraints, etc.) |

We recommend clear frontmatter in `SKILL.md` for discovery and platform import, for example:

```yaml
---
name: Example Skill
description: One sentence on when to use the skill and what it does (be specific).
---
```

Optional folders such as `references/`, `scripts/`, and `assets/` may sit next to `SKILL.md`; keep each skill self-contained and use relative paths.

## RedFox homepage

<p align="center">
  <a href="https://redfox.hk/?source=github">
    <img src="https://lyy.redfox.hk/page/redfox-page-3.png" alt="RedFox Logo" width="100%">
  </a>
</p>

## Authentication

All API requests require a valid API KEY.

### Get your key

Visit [RedFoxHub](https://redfox.hk/settings/api-keys?source=github) to obtain an API KEY.

## A rich library of skills

<p align="center">
  <a href="https://redfox.hk/skills?source=github">
    <img src="https://lyy.redfox.hk/page/redfox-page-2.png" alt="RedFox Logo" width="100%">
  </a>
</p>

### How to use skills

#### Local / Cursor

Copy the skill folder you need into your client’s skills directory (e.g. Cursor user skills or project `.cursor/skills/`—follow your client’s docs), or point the client’s “Add skill” flow at that subdirectory.

#### For Agent

Tell your agent (openclaw / workbuddy / qoder):

```bash
Please help me check and install the following Agent Skill in the current workspace.

Skill: Xiaohongshu Latest Hot Notes / xiaohongshu-realtime-search
Source: https://github.com/redfox-data/redfox-community/tree/main/skills/xiaohongshu-realtime-search

Please follow these steps in order:
1. Check whether this Skill is already installed in the project
2. Visit the GitHub URL above, read SKILL.md / README, and confirm installation steps and dependencies
3. If not installed: install the Skill to the appropriate directory for this project (prefer reusing existing skills paths)
4. If already installed: compare with the remote version, update as needed, and explain any changes
5. When done, report: installation path, how to trigger this Skill, and a brief usage example

If network access is limited, try git clone or curl; ask me first if anything is ambiguous or conflicts arise.
```

#### skills cli

Run the following in an interactive terminal (you can copy as-is):

```bash
npx skills init // install skills cli

npx skills add redfox-data/redfox-community // browse the redfox repo and select a skill to install

npx skills add https://github.com/redfox-data/redfox-community/tree/main/skills/seedance-video-gen // install a specific skill
```

Follow the prompts to install skills into a specific agent folder or globally.

#### SkillHub

Open SkillHub and install by searching for the **Chinese display name** of the skill under `skills/`:

https://skillhub.cn/skills

**Search examples:** `公众号爆款文章查询` or `抖音每日最具影响力账号`

#### ClawHub (`clawhub`)

Browse and install from the official redfox-data profile on ClawHub:

https://clawhub.ai/user/redfox-data

## Multi-platform API docs

<p align="center">
  <a href="https://redfox.hk/apis?source=github">
    <img src="https://lyy.redfox.hk/page/redfox-page-1.png" alt="RedFox Logo" width="100%">
  </a>
</p>

### What's in the API docs

- Request header reference
- Request parameter reference
- Response values and data structure reference
- Request examples
- Response examples
- Common status code reference

### API catalog

#### Douyin

- [Get Douyin content details (Premium)](https://redfox.hk/apis/douyin/0OT1E306)
- [Get Douyin content details (Wide)](https://redfox.hk/apis/douyin/FK67XDVQ)
- [Get Douyin account info (Premium)](https://redfox.hk/apis/douyin/XUT4CECZ)
- [Search Douyin accounts by keyword (Premium)](https://redfox.hk/apis/douyin/P5CHB3BZ)
- [Search Douyin accounts by keyword (Wide)](https://redfox.hk/apis/douyin/L6OUNUN1)
- [Search Douyin content by keyword (Premium)](https://redfox.hk/apis/douyin/774OBKK0)
- [Search Douyin content by keyword (Wide)](https://redfox.hk/apis/douyin/OWIBYU1V)
- [Get Douyin account content list (Premium)](https://redfox.hk/apis/douyin/QEQLCKD6)
- [Get Douyin account content list (Wide)](https://redfox.hk/apis/douyin/QSL2ZSXM)
- [Search Douyin AI content by keyword (Premium)](https://redfox.hk/apis/douyin/I8P3HTVH)
- [Extract video transcript — submit task](https://redfox.hk/apis/douyin/8DCJW2ZF)
- [Douyin hot account recommendations](https://redfox.hk/apis/douyin/20060017)
- [Douyin daily hot content ranking](https://redfox.hk/apis/douyin/HUCIASU)

#### Xiaohongshu (RED)

- [Xiaohongshu hot account recommendations](https://redfox.hk/apis/xiaohongshu/20060016)
- [Get Xiaohongshu account info (Premium)](https://redfox.hk/apis/xiaohongshu/4IVIDHEN)
- [Get Xiaohongshu content details (Premium)](https://redfox.hk/apis/xiaohongshu/KR1LPTBF)
- [Search Xiaohongshu accounts by keyword (Premium)](https://redfox.hk/apis/xiaohongshu/439NFLBD)
- [Search Xiaohongshu content by keyword (Premium)](https://redfox.hk/apis/xiaohongshu/384C6W6B)
- [Search Xiaohongshu AI content by keyword (Premium)](https://redfox.hk/apis/xiaohongshu/047JJ3UA)
- [Get Xiaohongshu account content list (Premium)](https://redfox.hk/apis/xiaohongshu/XN3ULENA)
- [Get Xiaohongshu top-level comments (Wide)](https://redfox.hk/apis/xiaohongshu/5AM3X4HZ)
- [Xiaohongshu viral note insights](https://redfox.hk/apis/xiaohongshu/3X8FGEEM)
- [Xiaohongshu 7-day viral notes](https://redfox.hk/apis/xiaohongshu/LBYLC5AK)
- [Extract video transcript — submit task](https://redfox.hk/apis/xiaohongshu/DCZW5V7A)

#### WeChat Official Accounts

- [Get WeChat account info (Premium)](https://redfox.hk/apis/gongzhonghao/6C4A77XR)
- [Get WeChat account info (Wide)](https://redfox.hk/apis/gongzhonghao/KUQYSQNX)
- [Get WeChat article by content UUID (Premium)](https://redfox.hk/apis/gongzhonghao/XEO0QQNF)
- [Get WeChat article by content UUID (Wide)](https://redfox.hk/apis/gongzhonghao/1LDQ7E1C)
- [Search WeChat accounts by keyword (Premium)](https://redfox.hk/apis/gongzhonghao/DNVPQZEZ)
- [Search WeChat accounts by keyword (Wide)](https://redfox.hk/apis/gongzhonghao/5Y84NI1D)
- [Search WeChat articles by keyword (Premium)](https://redfox.hk/apis/gongzhonghao/PW97QFBS)
- [Search WeChat articles by keyword (Wide)](https://redfox.hk/apis/gongzhonghao/FVQ8D4W5)
- [Get WeChat account article list (Premium)](https://redfox.hk/apis/gongzhonghao/XNV30XZ3)
- [Get WeChat account article list (Wide)](https://redfox.hk/apis/gongzhonghao/8IQD0BJC)
- [Get WeChat article by URL (Realtime)](https://redfox.hk/apis/gongzhonghao/I3CIBRI2)
- [Search WeChat AI-generated articles by keyword (Premium)](https://redfox.hk/apis/gongzhonghao/IE0887SO)

#### WeChat Channels

- [Search WeChat Channels content by keyword (Wide)](https://redfox.hk/apis/shipinhao/E7G00COY)
- [Search WeChat Channels accounts by keyword (Wide)](https://redfox.hk/apis/shipinhao/NL4I3533)
- [Get WeChat Channels content details (Wide)](https://redfox.hk/apis/shipinhao/OE4KUEUO)
- [Get WeChat Channels account content list (Wide)](https://redfox.hk/apis/shipinhao/OVUTOTCV)
- [Update WeChat Channels content details by link (Realtime)](https://redfox.hk/apis/shipinhao/OVUTOTCV)
- [Extract transcript from link — submit task (WeChat Channels)](https://redfox.hk/apis/shipinhao/MH5YA9DL)

#### Kuaishou

- [Search Kuaishou accounts (Wide)](https://redfox.hk/apis/kuaishou/GU17EVLV)
- [Get Kuaishou account content list (Wide)](https://redfox.hk/apis/kuaishou/27DQ6SF9)
- [Get Kuaishou content details (Wide)](https://redfox.hk/apis/kuaishou/UOM99OQI)
- [Search Kuaishou content by keyword (Wide)](https://redfox.hk/apis/kuaishou/ZWR31P2A)
- [Extract video transcript — submit task](https://redfox.hk/apis/kuaishou/8TUUDDCJ)

#### Bilibili

- [Get Bilibili content details (Premium)](https://redfox.hk/apis/bilibili/TIN1NMTZ)
- [Get Bilibili account info (Premium)](https://redfox.hk/apis/bilibili/EH53TOT7)
- [Search Bilibili accounts by keyword (Premium)](https://redfox.hk/apis/bilibili/ZXJLJQ21)
- [Search Bilibili content by keyword (Premium)](https://redfox.hk/apis/bilibili/LEN9QXR3)
- [Get Bilibili account content list (Premium)](https://redfox.hk/apis/bilibili/VPA67I98)
- [Get Bilibili audio URL](https://redfox.hk/apis/bilibili/9Q2PQBKU)
- [Extract transcript from link — submit task](https://redfox.hk/apis/bilibili/SQ4FHFZX)

#### Toutiao

- [Get Toutiao account content list (Realtime)](https://redfox.hk/apis/jinritoutiao/28CFGF5I)
- [Get Toutiao content details (Realtime)](https://redfox.hk/apis/jinritoutiao/PAB6Z75Y)
- [Get Toutiao content comments (Realtime)](https://redfox.hk/apis/jinritoutiao/ZMFVK589)
- [Search Toutiao accounts by keyword (Realtime)](https://redfox.hk/apis/jinritoutiao/4QS1F8DE)
- [Get Toutiao account content list (Realtime)](https://redfox.hk/apis/jinritoutiao/R1IGR09H)

#### TikTok

- [Get single TikTok post data](https://redfox.hk/apis/tool-tiktok/6SE9WIHJ)
- [Get TikTok user homepage posts](https://redfox.hk/apis/tool-tiktok/R473NUE9)
- [TikTok keyword video search](https://redfox.hk/apis/tool-tiktok/PXZXY8KQ)
- [Search TikTok accounts by keyword](https://redfox.hk/apis/tool-tiktok/20070019)

#### X (Twitter)

- [X (Twitter) get comments](<https://redfox.hk/apis/X(Twitter)/ABJQXHUE>)
- [X (Twitter) get user info](<https://redfox.hk/apis/X(Twitter)/AKFHJMXQ>)
- [X (Twitter) search tweets](<https://redfox.hk/apis/X(Twitter)/5K5EG87P>)
- [X (Twitter) get single tweet details](<https://redfox.hk/apis/X(Twitter)/QCP75W33>)

#### YouTube

- [YouTube extract video transcript](https://redfox.hk/apis/Youtube/WYRKHK6C)
- [YouTube search videos](https://redfox.hk/apis/Youtube/GC5SC5HS)
- [YouTube get video details](https://redfox.hk/apis/Youtube/609DF2IR)
- [YouTube get video comments](https://redfox.hk/apis/Youtube/WULKP6JP)

#### Instagram

- [Instagram unified search](https://redfox.hk/apis/Instagram/GM0TISWI)
- [Instagram get user info](https://redfox.hk/apis/Instagram/3YJT69FL)
- [Instagram get post details](https://redfox.hk/apis/Instagram/Z9M88QI8)
- [Instagram get post comments](https://redfox.hk/apis/Instagram/U1SGKF2G)

#### Autohome

- [Autohome search content by keyword](https://redfox.hk/apis/qichezhijia/CI7VW144)

#### Dongchedi

- [Dongchedi search content by keyword](https://redfox.hk/apis/dongchedi/W86F8SSK)
- [Dongchedi content details](https://redfox.hk/apis/dongchedi/QQ5E3EZ9)

#### Yiche

- [Yiche video details](https://redfox.hk/apis/yiche/3BXWEB6Y)

#### AI search

- [Kimi text search](https://redfox.hk/apis/tool-ai-search/USDIOVU23)
- [Doubao text search](https://redfox.hk/apis/tool-ai-search/I9R9LIDL)
- [DeepSeek text search](https://redfox.hk/apis/tool-ai-search/KGX4SDXQ)

#### AI tools

- [GPT image generation](https://redfox.hk/apis/tool/HUV4KRFQ)
- [Doubao image generation](https://redfox.hk/apis/tool/7OM96HCF)
- [Doubao video generation](https://redfox.hk/apis/tool/ER2ATHKI)
- [Upload image](https://redfox.hk/apis/tool/FXDGJO1V)
- [Upload video / image / audio](https://redfox.hk/apis/tool/6L178PZD)
- [Short video downloader](https://redfox.hk/apis/tool/AWUTFI4V)
- [YouTube video download](https://redfox.hk/apis/tool/D52IUEIM)
- [X (Twitter) video download](https://redfox.hk/apis/tool/7UW1PT1F)
- [TikTok video download](https://redfox.hk/apis/tool/MQMDU19Q)
- [Xiaohongshu video download](https://redfox.hk/apis/tool/QPNFJRG1)
- [WeChat Channels video download](https://redfox.hk/apis/tool/U2NJ13MW)
- [Douyin video download](https://redfox.hk/apis/tool/0W27H3O6)
- [Kuaishou video download](https://redfox.hk/apis/tool/0ZIWOO8P)
- [Bilibili video download](https://redfox.hk/apis/tool/CWX77QIH)
- [Instagram video download](https://redfox.hk/apis/tool/UUSP1G1P)

#### More platform APIs

- [Coming soon](https://redfox.hk/apis)

## Contributing

Issues and pull requests are welcome for new skills or fixes.

1. Fork this repository
2. Add or edit a subdirectory under `skills/`
3. Ensure `SKILL.md` stands alone, steps are actionable, and dependencies/risks are documented
4. Open a pull request with a short note on motivation and use cases

---

**redfoxdata** — Turn repeatable new-media workflows into shareable, evolvable Agent skills.
