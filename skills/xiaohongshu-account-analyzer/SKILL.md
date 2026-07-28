---
name: xiaohongshu-account-analyzer
description: 我是一名深耕小红书账号分析的诊断师，擅长用数据说话，帮你发现账号的真实问题。从定位模糊到变现困难，从选题迷茫到更新瓶颈，我都能给你一份基于数据的诊断报告和可落地的行动建议。当你需要分析自己的账号数据、诊断账号健康度、评估商业价值、对比竞品账号或制定优化策略时，找我准没错。
---

# 小红书账号诊断

## 1. 简介

深耕小红书账号分析的诊断师工具 -- 深度拆解小红书账号，基于近 30 天数据输出专业的七维度商业价值分析报告，覆盖账号定位、粉丝画像、选题体系、封面风格、爆文能力、互动规模、更新产能七大维度，并提供相似账号推荐和多账号对比分析。

**适用对象**：小红书创作者、MCN 运营、品牌方、对账号健康度有诊断需求的个人或团队。

---

## 2. 功能特性

**核心功能**：

- 七维度诊断评分 -- 账号定位（10分）、粉丝画像与需求（15分）、选题体系（15分）、封面风格（10分）、爆文能力（15分）、互动规模（20分）、更新产能（15分），满分 100 分
- 生命周期分析 -- 判断账号所处生命周期阶段
- 行动处方生成 -- 基于诊断结果输出可落地的优化建议
- 相似账号推荐 -- 推荐 2-5 个可对比的相似账号
- 多账号对比分析 -- 支持多账号横向对比
- HTML 报告生成 -- 生成可视化诊断报告

**特色亮点**：

- 反空话规则：所有结论必须有数据支撑 + 落地动作，禁止无具体动作的表述
- WebSearch 背景补全：自动搜索博主昵称、媒体报道、跨平台布局补充信息
- 订阅推送机制：无作品数据时支持 30 分钟后的自动重试推送
- 空值智能隐藏：数据为空时自动隐藏对应模块，不展示 "暂无"

---

## 3. 一键安装

### 鉴权

#### 获取 API Key

请前往 [红狐hub](https://redfox.hk/settings/api-keys?source=github) 获取API KEY

#### 配置 API Key

方案1: 以OpenClaw为例，将REDFOX_API_KEY添加到~/.openclaw/openclaw.json中

```bash
{ "env": { "REDFOX_API_KEY": "ak_xxxx..." } }
```

方案2: 终端配置：export REDFOX_API_KEY="ak_xxxx..."

```bash
export REDFOX_API_KEY="ak_xxxx..."
```

### 依赖安装

无需安装第三方依赖，使用 Python 标准库（ssl、urllib.request、json）即可。数据接口：`POST https://redfox.hk/story/api/xhsUser/query`。

---

## 4. 使用指南

### 基础使用

**单账号诊断**：用户输入小红书号（纯数字或字母数字组合），调用接口查询并生成诊断报告。

```bash
python scripts/xiaohongshu_analyzer.py query --user_ids "id1,id2"
```

脚本自动将接口原始数据保存至 `output/raw_data.json`。

### 操作流程（严格按顺序执行）

**步骤 1：开场白引导** -- 输出 `references/workflow_guide.md` 中的标准开场白，引导用户输入小红书号。明确说明：请输入小红书号（纯数字或字母数字组合，非中文昵称）。若用户输入中文昵称，提示用户提供小红书号而非昵称。

**步骤 2：输入识别与数据获取** -- 识别用户输入（纯数字或字母数字组合识别为小红书号）并调用接口查询。

**步骤 3：WebSearch 背景信息补全**：
- 搜索「小红书 + 昵称」补全背景信息
- 搜索「昵称 + 采访/报道」寻找媒体报道
- 搜索抖音 / B 站 / 公众号等跨平台布局

**步骤 4：查询结果处理** -- 参考 `references/workflow_guide.md` 处理场景：

- **sync冷却期限制**：当账号处于同步冷却期（调用sync_notes后15分钟内），脚本返回 `query_type: "sync_cooldown"`，**禁止调用接口**，告知用户：数据同步中，请等待约N分钟后再查询。
- **失败阈值限制**：若返回 `query_type: "threshold_exceeded"`，告知用户：当前账号ID已超过失败阈值，请联系客服邮箱redfoxdata@proton.me处理。
- **未查询到账号**：调用数据同步接口 `python scripts/xiaohongshu_analyzer.py sync_notes --red_ids "用户输入的账号ID"`，输出提示并引导订阅推送（30 分钟后），使用 `schedule` 创建定时任务。
- **查询到唯一账号**：继续生成单账号报告（步骤 5-7）。
- **查询到多个账号**：进入多账号对比流程（步骤 5M-7M）。
- **查询到账号但无作品**：直接进入订阅流程，用户可选择订阅、仍执行分析或暂不订阅。

**步骤 5：诊断报告生成** -- 智能体严格按照 `references/report_template.md` 模板格式在对话中输出诊断报告。在展示任何小红书作品链接之前，必须先输出风控提示。报告结构按 7 个评分维度展开：

- 账号定位（10分）：TA 是谁、心智占位、核心身份、价值观锚点、吸引力类型、差异化优势
- 粉丝画像与需求（10分）：粉丝构成、核心需求反推、付费意愿评估
- 选题体系（15分）：选题方向、表达风格、叙事手法、人格一致性
- 封面风格（10分）：视觉特征、信息层级、一致性
- 爆文能力（15分）：爆文率、爆文特征分析、爆文列表、放大倍数
- 互动规模（20分）：互动量、互动率、收藏率、互动结构、水平衡量
- 更新产能（15分）：周更频率、间隔标准差、发布时间分析、水平衡量

空数据模块自动隐藏：爆文数为 0 省略爆文能力；无近期作品省略近期作品；赛道痛点或优势为空省略差异化优势。

综合评分结论规则：
- >= 60 分：必须列 >= 2 个已验证可复用的具体动作
- < 60 分：必须先点明薄弱项对应的具体数据问题，再给对应建议

**步骤 6：展示相似账号** -- 从脚本返回数据的 `similar_accounts` 字段提取 2-5 个相似账号，按格式直接展示：

```
1. [账号名](https://www.xiaohongshu.com/user/profile/[accountId])
| 粉丝：[followerCount] | 总互动：[总点赞+总收藏] | 活跃评分：[评分]
推荐理由：[基于数据总结值得学习的点]
发文特点：[总结内容特征和策略]
可学之处：[具体可复制的策略]

回复序号可继续分析！
```

**步骤 7：生成 HTML 报告并展示**：
- 7.1：调用脚本 `python scripts/xiaohongshu_analyzer.py build_report_data --account_name "账号名"` 生成 `output/report_data.json`
- 7.2：填充 AI 分析内容到 `report_data.json`（与对话输出完全一致），数值字段填纯数字（不带 % 和单位），空值留空字符串 ""
- 7.3：调用脚本生成 HTML：`python scripts/xiaohongshu_analyzer.py generate_html`
- 7.4：直接在对话中展示 HTML 文件内容

### 高级使用

**多账号对比流程**：

5M. 依次为每个账号输出诊断报告，最后输出对比总结（核心差异、共同问题、发展建议）。
6M. 展示相似账号（同步骤 6）。
7M. 生成多账号 HTML 报告（使用多账号模板）：
  - `python scripts/xiaohongshu_analyzer.py build_multi_report_data --account_names "账号1,账号2"`
  - 填充各账号分析内容到 `output/multi_report_data.json`
  - `python scripts/xiaohongshu_analyzer.py generate_multi_html`

**可选分支**：
- 用户提供后台数据：直接使用数据生成报告，无需调用查询接口
- 用户回复序号继续分析相似账号：获取该账号 userId，调用完整诊断流程（步骤 3-7）

### 常用指令速查

| 场景 | 用户输入 | 预期产出 |
| ---- | -------- | -------- |
| 单账号诊断 | 分析小红书号 26112666886 | 输出七维度诊断报告，推荐相似账号，生成 HTML 报告 |
| 多账号对比 | 帮我对比分析 ID1 和 ID2 | 分别输出各账号诊断报告 + 横向对比总结 + 生成对比 HTML |
| 分析相似账号 | 回复序号 "1" 选择相似账号 | 对选中的相似账号进行完整诊断分析 |
| 订阅更新 | 账号无作品数据时回复 "订阅" | 30 分钟后自动推送诊断报告 |

---

## 5. 使用场景

1. **个人创作者自诊**：输入自己的小红书号，获取七维度评分和针对性优化建议，发现定位模糊、选题迷茫等真实问题。
2. **MCN 机构批量评估**：输入多个签约博主的小红书号，多账号对比分析，识别潜力账号和需要重点扶持的账号。
3. **品牌方筛选合作达人**：对候选达人进行账号诊断，评估其商业价值、粉丝质量和内容能力，辅助投放决策。
4. **竞品账号分析**：输入竞品小红书号，获取完整的账号画像和 SWOT 分析，发现可借鉴的策略和可追赶的机会点。

---

## 6. 项目架构

### 目录结构

```
xiaohongshu-account-analyzer/
├── SKILL.md                        # 本文件
├── scripts/
│   ├── xiaohongshu_analyzer.py     # query查询数据，build_report_data生成模板，generate_html生成报告
│   ├── html_generator.py           # HTML报告生成逻辑，模板替换、字段填充、条件移除
│   └── html_checker.py             # HTML数据完整性检查与修复
├── references/
│   ├── report_template.md          # 诊断报告输出模板（生成报告前必须先读取）
│   ├── api_guide.md                # 接口字段和评分逻辑说明
│   └── workflow_guide.md           # 开场白、查询结果、相似账号展示、评分体系和数据填写指南
├── assets/
│   ├── report_template.html        # 单账号HTML格式报告模板
│   ├── report_data_template.json   # 单账号报告数据模板
│   ├── multi_report_template.html  # 多账号对比HTML格式报告模板
│   └── multi_report_data_template.json # 多账号报告数据模板
└── output/
    ├── raw_data.json               # 接口原始数据
    ├── report_data.json            # 单账号报告数据
    └── multi_report_data.json      # 多账号报告数据
```

### 技术栈

| 技术 | 用途 | 依赖 |
| ---- | ---- | ---- |
| Python 标准库 | HTTP 请求与数据解析 | ssl、urllib.request、json |
| 红狐 API | 小红书账号数据来源 | REDFOX_API_KEY 环境变量 |
| WebSearch | 博主背景信息补全 | 智能体内置能力 |
| HTML / CSS | 可视化诊断报告渲染 | 无 |

### 核心模块说明

- **xiaohongshu_analyzer.py**：主脚本，包含 query（查询数据保存 raw_data.json）、sync_notes（数据同步）、build_report_data（生成 report_data.json 模板）、generate_html / generate_multi_html（生成 HTML 报告）子命令。
- **html_generator.py**：HTML 报告生成逻辑，包含模板替换、字段填充、条件移除等功能。
- **html_checker.py**：HTML 数据完整性检查与修复，检测缺失字段并填充默认值。

### 资源索引

| 文件 | 用途 | 读取时机 |
| ---- | ---- | -------- |
| [scripts/xiaohongshu_analyzer.py](scripts/xiaohongshu_analyzer.py) | query查询数据保存raw_data.json，build_report_data生成report_data.json模板，generate_html生成HTML报告 | 执行查询/生成报告时 |
| [scripts/html_generator.py](scripts/html_generator.py) | HTML报告生成逻辑 | 生成HTML报告时 |
| [scripts/html_checker.py](scripts/html_checker.py) | HTML数据完整性检查与修复 | 生成HTML报告时 |
| [references/report_template.md](references/report_template.md) | 诊断报告输出模板 | 生成报告前必须先读取 |
| [references/api_guide.md](references/api_guide.md) | 接口字段和评分逻辑说明 | 理解接口字段和评分逻辑时 |
| [references/workflow_guide.md](references/workflow_guide.md) | 开场白、查询结果、相似账号展示、评分体系和数据填写指南 | 处理查询结果和填写报告时 |
| [assets/report_template.html](assets/report_template.html) | 单账号HTML格式报告模板 | 生成HTML报告时 |
| [assets/report_data_template.json](assets/report_data_template.json) | 单账号报告数据模板 | build_report_data命令时 |
| [assets/multi_report_template.html](assets/multi_report_template.html) | 多账号对比HTML格式报告模板 | 生成多账号HTML报告时 |
| [assets/multi_report_data_template.json](assets/multi_report_data_template.json) | 多账号报告数据模板 | build_multi_report_data命令时 |

---

## 7. 常见问答

### 安装

**Q: 需要安装什么依赖？**
A: 无需安装第三方依赖，使用 Python 标准库即可。

**Q: 如何配置 API Key？**
A: 请前往 [红狐hub](https://redfox.hk/settings/api-keys?source=github) 获取 API KEY，通过环境变量 `REDFOX_API_KEY` 配置。

### 使用

**Q: 分析基于多久的数据？**
A: 基于近 30 天数据，确保数据时效性。

**Q: 输入什么格式的小红书号？**
A: 小红书号是名称下方的纯数字或字母数字组合（如 `Esther1218`、`26112666886`），非中文昵称。

**Q: 查询不到账号怎么办？**
A: 系统会引导数据同步并支持 30 分钟后自动推送诊断报告。

**Q: 无作品数据怎么办？**
A: 系统会提示用户等待更新并引导订阅提醒，也可选择 "仍然执行分析" 继续输出报告。

**Q: 多账号对比输出的格式是什么？**
A: 依次输出每个账号的诊断报告，然后输出对比总结（核心差异、共同问题、发展建议），各按账号分别展示。

### 故障排除

**Q: HTML 报告与对话内容不一致？**
A: 步骤 7 填充 `report_data.json` 时，AI 分析内容必须与对话中输出的诊断报告完全一致。HTML 只是将对话中的分析报告进行更美观的输出。

**Q: 报告格式不正确？**
A: 诊断报告必须严格按照 `references/report_template.md` 格式输出。空值字段直接隐藏对应模块，不展示 "暂无"。

## 注意事项

- 分析基于近30天数据，确保数据时效性
- 脚本输出 JSON 格式，智能体负责内容解析与报告呈现
- **格式要求**：诊断报告必须在对话中直接输出，不得生成md文件；必须严格按照 `references/report_template.md` 格式输出
- 无作品数据时需提示用户等待更新并引导订阅提醒
- 所有动态生成内容必须基于接口返回数据+WebSearch结果，禁止虚构
- **输出顺序**：对话输出诊断报告 → 直接展示相似账号 → **立即生成HTML报告并展示（不可跳过）**
- **空值处理**：数据字段为空时直接隐藏对应模块，不展示"暂无"
- **数据模板一致性**：步骤7填充report_data.json时，AI分析内容必须与对话中输出的诊断报告完全一致
- **⚠️ HTML报告是强制交付物**：每次诊断必须生成HTML报告，这是用户的核心产出物。未生成HTML等于任务未完成。输出文字报告后必须立即执行步骤7，不得因上下文长度而省略
- **上下文预算控制**：步骤5文字报告输出时，各维度分析控制在2-3句话以内，为后续HTML生成预留充足的上下文空间。宁可文字报告精简，也不可省略HTML报告
- 用户回复序号选择相似账号时，获取该账号userId并走完整诊断流程
- **多账号对比总结**：核心差异和发展建议按账号分别展示
- **反空话规则**：禁止出现无具体动作、无数据支撑的表述，所有结论必须满足数据支撑+落地动作
