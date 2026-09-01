<p align="center">
  <a href="https://redfox.hk/?source=github">
    <img src="https://lyy.redfox.hk/page/logo-redfox-name.png" alt="RedFox Logo" width="200">
  </a>
</p>

<p align="right">
  中文
  <a href="https://github.com/redfox-data/redfox-community/blob/main/README.en.md">English</a>
</p>

# redfoxdata · Agent Skills

本仓库收录 **redfoxdata** 社区维护的多枚 Agent 技能（Skill），面向灵感、选题、文案创作、数据复盘等场景。技能以 `SKILL.md` 为核心，可与 Cursor、Claude Code 等支持 Agent Skills 的工具配合使用。

## 仓库结构

```text
.
├── README.md          # 本说明（中文）
├── README.en.md       # English README
├── skills/            # 技能（每个子目录一枚技能）
│   └── <skill-name>/
│       ├── SKILL.md
│       └── …          # 脚本、参考文档等（可选）
```

## 技能目录约定

每个技能是一个**独立子文件夹**，且至少包含：

| 文件       | 说明                                                              |
| ---------- | ----------------------------------------------------------------- |
| `SKILL.md` | 技能入口：YAML frontmatter + 正文（触发条件、步骤、约束、示例等） |

建议在 `SKILL.md` 的 frontmatter 中提供清晰元信息，便于检索与导入平台识别，例如：

```yaml
---
name: Example Skill
description: 一句话说明技能适用场景与能力边界（建议具体，避免空泛）。
---
```

可选：`references/`、`scripts/`、`assets/` 等，与 `SKILL.md` 同目录存放，保持单技能自包含、路径相对引用即可。

## RedFox首页

<p align="center">
  <a href="https://redfox.hk/?source=github">
    <img src="https://lyy.redfox.hk/page/redfox-page-3.png" alt="RedFox Logo" width="100%">
  </a>
</p>

## 身份认证

所有 API 请求都需要有效的 API KEY。

### 获取链接：

请前往 [红狐hub](https://redfox.hk/settings/api-keys?source=github) 获取API KEY

## 丰富多样的Skill

<p align="center">
  <a href="https://redfox.hk/skills?source=github">
    <img src="https://lyy.redfox.hk/page/redfox-page-2.png" alt="RedFox Logo" width="100%">
  </a>
</p>

### Skill如何使用

#### 本地 / Cursor

将需要的技能目录复制到你所用工具的 skills 目录（例如 Cursor 的 user skills 或项目内 `.cursor/skills/` 等，以你当前客户端文档为准），或通过客户端提供的「添加技能」入口指向该子文件夹。

#### For Agent

直接告诉智能体Agent（openclaw/workbuddy/qoder）：

```bash
请帮我在当前工作区检查并安装以下 Agent Skill。

Skill：小红书最新热门笔记 / xiaohongshu-realtime-search
源码地址：https://github.com/redfox-data/redfox-community/tree/main/skills/xiaohongshu-realtime-search

请按顺序执行：
1. 检查本项目是否已安装该 Skill
2. 访问上述 GitHub 地址，阅读 SKILL.md / README，确认安装步骤与依赖
3. 若未安装：将 Skill 安装到本项目适用的目录（优先沿用已有 skills 路径）
4. 若已安装：对比远程内容，按需更新并说明变更
5. 完成后告知：安装路径、如何触发该 Skill、简短使用示例

网络受限时可尝试 git clone 或 curl；有歧义或冲突时先询问我。
```

#### skills cli

在交互终端执行以下命令，可直接复制

```bash
npx skills init //安装skills cli

npx skills add redfox-data/redfox-community //检索redfox仓库选择安装skill

npx skills add https://github.com/redfox-data/redfox-community/tree/main/skills/seedance-video-gen //安装具体skill
```

根据提示将skill安装在指定的agent文件夹中或者安装在全局

#### SkillHub

访问SkillHub搜索skills目录中对应技能的中文名安装：https://skillhub.cn/skills

搜索示例：公众号爆款文章查询 或 抖音每日最具影响力账号

#### ClawHub（`clawhub`）

访问clawhub红狐数据官方主页搜索安装skill：https://clawhub.ai/user/redfox-data

## 多平台API文档

<p align="center">
  <a href="https://redfox.hk/apis?source=github">
    <img src="https://lyy.redfox.hk/page/redfox-page-1.png" alt="RedFox Logo" width="100%">
  </a>
</p>

### API文档中包含：

- 请求头说明
- 请求参数说明
- 返回值和数据结构说明
- 请求示例
- 响应示例
- 常见状态码说明

### API明细：

#### 抖音：

- [获取抖音作品内容详情 (优质库)](https://redfox.hk/apis/douyin/0OT1E306)
- [获取抖音作品内容详情 (广域库)](https://redfox.hk/apis/douyin/FK67XDVQ)
- [获取抖音账号信息 (优质库)](https://redfox.hk/apis/douyin/XUT4CECZ)
- [搜索关键词获取抖音账号 (优质库)](https://redfox.hk/apis/douyin/P5CHB3BZ)
- [搜索关键词获取抖音账号 (广域库)](https://redfox.hk/apis/douyin/L6OUNUN1)
- [搜索关键词获取抖音作品 (优质库)](https://redfox.hk/apis/douyin/774OBKK0)
- [搜索关键词获取抖音作品 (广域库)](https://redfox.hk/apis/douyin/OWIBYU1V)
- [获取抖音账号作品列表 (优质库)](https://redfox.hk/apis/douyin/QEQLCKD6)
- [获取抖音账号作品列表 (广域库)](https://redfox.hk/apis/douyin/QSL2ZSXM)
- [搜索关键词获取抖音 AI 作品(优质库)](https://redfox.hk/apis/douyin/I8P3HTVH)
- [视频提文案-提交任务](https://redfox.hk/apis/douyin/8DCJW2ZF)
- [抖音热门账号推荐](https://redfox.hk/apis/douyin/20060017)
- [抖音每日热门作品榜](https://redfox.hk/apis/douyin/HUCIASU)

#### 小红书：

- [小红书热门账号推荐](https://redfox.hk/apis/xiaohongshu/20060016)
- [获取小红书账号信息 (优质库)](https://redfox.hk/apis/xiaohongshu/4IVIDHEN)
- [获取小红书作品内容详情 (优质库)](https://redfox.hk/apis/xiaohongshu/KR1LPTBF)
- [搜索关键词获取小红书账号 (优质库)](https://redfox.hk/apis/xiaohongshu/439NFLBD)
- [搜索关键词获取小红书作品 (优质库)](https://redfox.hk/apis/xiaohongshu/384C6W6B)
- [搜索关键词获取小红书 AI 作品(优质库)](https://redfox.hk/apis/xiaohongshu/047JJ3UA)
- [查询小红书账号作品列表（优质库](https://redfox.hk/apis/xiaohongshu/XN3ULENA)
- [获取小红书一级评论（广域库）](https://redfox.hk/apis/xiaohongshu/5AM3X4HZ)
- [小红书爆款笔记洞察](https://redfox.hk/apis/xiaohongshu/3X8FGEEM)
- [小红书七日爆款笔记](https://redfox.hk/apis/xiaohongshu/LBYLC5AK)
- [视频提文案-提交任务](https://redfox.hk/apis/xiaohongshu/DCZW5V7A)

#### 公众号：

- [获取公众号账号信息 (优质库)](https://redfox.hk/apis/gongzhonghao/6C4A77XR)
- [获取公众号账号信息 (广域库)](https://redfox.hk/apis/gongzhonghao/KUQYSQNX)
- [根据作品uuid获取公众号作品 (优质库)](https://redfox.hk/apis/gongzhonghao/XEO0QQNF)
- [根据作品uuid获取公众号作品 (广域库)](https://redfox.hk/apis/gongzhonghao/1LDQ7E1C)
- [搜索关键词获取公众号账号 (优质库)](https://redfox.hk/apis/gongzhonghao/DNVPQZEZ)
- [搜索关键词获取公众号账号 (广域库)](https://redfox.hk/apis/gongzhonghao/5Y84NI1D)
- [搜索关键词获取公众号作品 (优质库)](https://redfox.hk/apis/gongzhonghao/PW97QFBS)
- [搜索关键词获取公众号作品 (广域库)](https://redfox.hk/apis/gongzhonghao/FVQ8D4W5)
- [获取公众号账号作品列表 (优质库)](https://redfox.hk/apis/gongzhonghao/XNV30XZ3)
- [获取公众号账号作品列表 (广域库)](https://redfox.hk/apis/gongzhonghao/8IQD0BJC)
- [根据作品地址获取公众号作品（实时）](https://redfox.hk/apis/gongzhonghao/I3CIBRI2)
- [搜索关键词获取公众号 AI 创作作品 (优质库)](https://redfox.hk/apis/gongzhonghao/IE0887SO)

#### 视频号：

- [搜索关键词获取视频号作品 (广域库)](https://redfox.hk/apis/shipinhao/E7G00COY)
- [搜索关键词获取视频号账号 (广域库)](https://redfox.hk/apis/shipinhao/NL4I3533)
- [获取视频号作品内容详情 (广域库)](https://redfox.hk/apis/shipinhao/OE4KUEUO)
- [获取视频号账号作品列表 (广域库)](https://redfox.hk/apis/shipinhao/OVUTOTCV)
- [视频号作品链接更新详情（实时）](https://redfox.hk/apis/shipinhao/OVUTOTCV)
- [链接提文案-提交任务（视频号）](https://redfox.hk/apis/shipinhao/MH5YA9DL)

#### 快手

- [快手账号搜索（广域库）](https://redfox.hk/apis/kuaishou/GU17EVLV)
- [快手按账号获取作品列表（广域库）](https://redfox.hk/apis/kuaishou/27DQ6SF9)
- [快手按作品获取正文详情（广域库）](https://redfox.hk/apis/kuaishou/UOM99OQI)
- [快手按关键词搜索作品（广域库）](https://redfox.hk/apis/kuaishou/ZWR31P2A)
- [视频提文案-提交任务](https://redfox.hk/apis/kuaishou/8TUUDDCJ)

#### 哔哩哔哩：

- [获取哔哩哔哩作品内容详情 (优质库)](https://redfox.hk/apis/bilibili/TIN1NMTZ)
- [获取哔哩哔哩账号信息 (优质库)](https://redfox.hk/apis/bilibili/EH53TOT7)
- [搜索关键词获取哔哩哔哩账号 (优质库)](https://redfox.hk/apis/bilibili/ZXJLJQ21)
- [搜索关键词获取哔哩哔哩作品 (优质库)](https://redfox.hk/apis/bilibili/LEN9QXR3)
- [获取哔哩哔哩账号作品列表 (优质库)](https://redfox.hk/apis/bilibili/VPA67I98)
- [获取哔哩哔哩音频地址](https://redfox.hk/apis/bilibili/9Q2PQBKU)
- [链接提文案-提交任务](https://redfox.hk/apis/bilibili/SQ4FHFZX)

#### 今日头条

- [获取今日头条账号作品列表 (实时)](https://redfox.hk/apis/jinritoutiao/28CFGF5I)
- [获取今日头条作品内容详情 (实时)](https://redfox.hk/apis/jinritoutiao/PAB6Z75Y)
- [获取今日头条作品评论 (实时)](https://redfox.hk/apis/jinritoutiao/ZMFVK589)
- [获取今日头条关键词搜索账号 (实时)](https://redfox.hk/apis/jinritoutiao/4QS1F8DE)
- [获取今日头条账号作品列表 (实时)](https://redfox.hk/apis/jinritoutiao/R1IGR09H)

#### Tiktok：

- [TikTok获取单个作品数据](https://redfox.hk/apis/tool-tiktok/6SE9WIHJ)
- [TikTok获取用户主页作品数据](https://redfox.hk/apis/tool-tiktok/R473NUE9)
- [TikTok关键词视频搜索](https://redfox.hk/apis/tool-tiktok/PXZXY8KQ)
- [Tiktok关键词搜索账号](https://redfox.hk/apis/tool-tiktok/20070019)

#### X(Twitter):

- [X(Twitter)获取评论](<https://redfox.hk/apis/X(Twitter)/ABJQXHUE>)
- [X(Twitter)获取用户信息](<https://redfox.hk/apis/X(Twitter)/AKFHJMXQ>)
- [X(Twitter)搜索推文](<https://redfox.hk/apis/X(Twitter)/5K5EG87P>)
- [X(Twitter)获取单个推文详情](<https://redfox.hk/apis/X(Twitter)/QCP75W33>)

#### Youtube:

- [Youtube视频提文案](https://redfox.hk/apis/Youtube/WYRKHK6C)
- [Youtube搜索视频](https://redfox.hk/apis/Youtube/GC5SC5HS)
- [Youtube获取视频详情](https://redfox.hk/apis/Youtube/609DF2IR)
- [Youtube获取视频评论](https://redfox.hk/apis/Youtube/WULKP6JP)

#### Instagram:

- [Instagram综合搜索](https://redfox.hk/apis/Instagram/GM0TISWI)
- [Instagram获取用户信息](https://redfox.hk/apis/Instagram/3YJT69FL)
- [Instagram获取帖子详情](https://redfox.hk/apis/Instagram/Z9M88QI8)
- [Instagram获取帖子评论](https://redfox.hk/apis/Instagram/U1SGKF2G)

#### 汽车之家:

- [汽车之家关键词搜索作品](https://redfox.hk/apis/qichezhijia/CI7VW144)

#### 懂车帝:

- [懂车帝关键词搜索作品](https://redfox.hk/apis/dongchedi/W86F8SSK)
- [懂车帝作品详情](https://redfox.hk/apis/dongchedi/QQ5E3EZ9)

#### 易车:

- [易车视频详情](https://redfox.hk/apis/yiche/3BXWEB6Y)

#### AI搜索：

- [kimi纯文字搜索](https://redfox.hk/apis/tool-ai-search/USDIOVU23)
- [豆包纯文字搜索](https://redfox.hk/apis/tool-ai-search/I9R9LIDL)
- [Deepseek纯文字搜索](https://redfox.hk/apis/tool-ai-search/KGX4SDXQ)

#### AI工具：

- [GPT图片生成](https://redfox.hk/apis/tool/HUV4KRFQ)
- [豆包图片生成](https://redfox.hk/apis/tool/7OM96HCF)
- [豆包视频生成](https://redfox.hk/apis/tool/ER2ATHKI)
- [上传图片](https://redfox.hk/apis/tool/FXDGJO1V)
- [上传视频/图片/音频](https://redfox.hk/apis/tool/6L178PZD)
- [短视频下载器](https://redfox.hk/apis/tool/AWUTFI4V)
- [YouTube视频下载](https://redfox.hk/apis/tool/D52IUEIM)
- [X(Twitter)视频下载](https://redfox.hk/apis/tool/7UW1PT1F)
- [TikTok视频下载](https://redfox.hk/apis/tool/MQMDU19Q)
- [小红书视频下载](https://redfox.hk/apis/tool/QPNFJRG1)
- [视频号视频下载](https://redfox.hk/apis/tool/U2NJ13MW)
- [抖音视频下载](https://redfox.hk/apis/tool/0W27H3O6)
- [快手视频下载](https://redfox.hk/apis/tool/0ZIWOO8P)
- [哔哩哔哩视频下载](https://redfox.hk/apis/tool/CWX77QIH)
- [Instagram视频下载](https://redfox.hk/apis/tool/UUSP1G1P)

#### 更多平台API：

- [敬请期待！！](https://redfox.hk/apis)

## 参与贡献

欢迎通过 Issue / Pull Request 贡献新技能或修正现有技能。

1. Fork 本仓库
2. 在 `skills/` 下新增或修改对应子目录
3. 确保 `SKILL.md` 可独立理解、步骤可执行、依赖与风险有说明
4. 发起 Pull Request，并在描述中简要说明变更动机与适用场景

---

**redfoxdata** — 将可重复的新媒体工作流沉淀为可分享、可演进的 Agent 技能。
