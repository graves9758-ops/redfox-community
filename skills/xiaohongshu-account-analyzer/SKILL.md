---
name: xiaohongshu-account-analyzer
description: 深度拆解小红书账号，输出七维度量化评分诊断报告与可导出HTML；当用户提供小红书号进行账号诊断、rednote分析、账号健康度评估、商业价值评估、多账号对比或制定优化策略时使用
---

# 小红书账号深度诊断

## 任务目标
- 本 Skill 用于：深度拆解小红书账号，输出专业的商业价值分析报告
- 能力包含：七维度评分（账号定位10分、粉丝画像与需求15分、选题体系10分、封面风格10分、爆文能力20分、互动规模20分、更新产能15分，满分100）、行动处方生成、相似账号推荐、多账号对比分析
- 触发条件：用户提供小红书号（名称下方的小红书号，格式为纯数字或字母数字组合，非中文昵称），需要生成完整的账号诊断报告

## 使用示例
| 场景 | 用户输入 | 预期产出 |
|------|---------|---------|
| 单账号诊断 | 分析小红书号 26112666886 | 输出七维度诊断报告，推荐相似账号，生成可导出图片的HTML报告 |
| 多账号对比 | 帮我对比分析 ID1 和 ID2 | 分别输出各账号诊断报告，生成横向对比总结，生成对比HTML报告 |
| 分析相似账号 | 回复序号"1"选择相似账号 | 对选中的相似账号进行完整诊断分析，输出报告并生成HTML |

## 🔑 鉴权

### 获取 API Key

请前往 [红狐hub](https://redfox.hk/settings/api-keys?source=github) 获取 API KEY。

### 配置 API Key

将 `REDFOX_API_KEY` 配置为环境变量：

```bash
export REDFOX_API_KEY="ak_xxxx..."
```

脚本通过 `os.getenv('REDFOX_API_KEY')` 读取密钥，缺失时报错退出并提供配置指引。请求头自动携带 `X-API-KEY`。

---

## 前置准备
- 数据接口：POST https://redfox.hk/story/api/xhsUser/query（详见 references/api_guide.md）
- WebSearch：获取博主昵称后执行背景信息补全
- 评分规则与数据填写规范：详见 references/workflow_guide.md

## 操作步骤

### 标准流程（单账号诊断）

**步骤1：开场白引导**
- 输出 `references/workflow_guide.md` 中的标准开场白
- 引导用户输入小红书号（纯数字或字母数字组合，非中文昵称）

**步骤2：数据查询**
- 识别用户输入：纯数字或字母数字组合识别为小红书号
- 调用脚本：`python scripts/xiaohongshu_analyzer.py query --user_ids "小红书号"`
- 脚本将原始数据保存至 `output/raw_data.json`
- 若用户输入中文昵称，提示用户提供小红书号

**步骤3：WebSearch背景补全**
- 搜索「小红书 + 昵称」补全背景信息
- 搜索「昵称 + 采访/报道」寻找媒体报道
- 搜索抖音/B站/公众号等跨平台布局

**步骤4：查询结果处理**
- **失败阈值**（返回 `query_type: "threshold_exceeded"`）：
  ```
  当前小红书号已超过失败阈值，请联系客服邮箱redfoxdata@proton.me 或访问 https://redfox.hk/?source=github处理
  ```
- **未查询到账号**（账号数据为空）：
  ```
  未查询到相关账号：当前 Skill 仅收录热门账号。如需定制数据，可邮件联系[红狐数据](https://redfox.hk/?source=github)咨询：redfoxdata@proton.me
  ```
- **查询成功** → 继续步骤5-7
- **多账号数据** → 转多账号对比流程

**步骤5：诊断报告生成**
- 读取 `references/report_template.md` 获取报告格式
- 读取 `references/workflow_guide.md` 获取评分规则和数据填写规范
- 将脚本数据填入模板，在对话中直接输出诊断报告（不生成md文件）
- **账号作品模块提示（必须输出）**：在展示任何小红书作品链接之前，必须先输出：
  ```
  ！！！受小红书风控规则限制，部分作品链接可能无法正常跳转，您可复制对应作品标题前往小红书搜索查看，感谢理解🙇‍♀️🙇‍♀️
  ```
- **数据字段说明**：gmtCreate 是红狐数据系统首次收录该账号的时间，不是小红书账号注册时间，严禁用于判断账号运营时长
- **综合评分结论规则**：
  - >=60分：列>=2个已验证可复用的具体动作
  - <60分：先点明薄弱项对应的数据问题，再给建议
- **空值处理**：数据字段为空时直接隐藏对应模块，不展示"暂无"

**步骤6：展示相似账号**
- 从脚本返回数据的 `similar_accounts` 字段提取2-5个相似账号
- 按格式直接展示（无需询问），展示完成后进入步骤7

**步骤7：生成HTML报告**
- **步骤7.1**：生成数据模板
  - `python scripts/xiaohongshu_analyzer.py build_report_data --account_name "账号名"`
- **步骤7.2**：填充AI分析内容到 `output/report_data.json`（与对话输出完全一致）
  - **评分字段（各维度得分、综合评分）保留脚本计算的值，禁止覆盖**
  - 数值字段填纯数字（不带%或单位）
  - 空值字段留空字符串""
- **步骤7.3**：生成HTML
  - `python scripts/xiaohongshu_analyzer.py generate_html`
- **步骤7.4**：在对话中展示HTML文件内容

### 多账号对比流程
- **步骤5M**：为每个账号生成诊断报告（同步骤5），输出对比总结（核心差异、共同问题、发展建议）
- **步骤6M**：展示相似账号（同步骤6）
- **步骤7M**：生成多账号HTML报告
  - `python scripts/xiaohongshu_analyzer.py build_multi_report_data --account_names "账号1,账号2"`
  - 填充 `output/multi_report_data.json`
  - `python scripts/xiaohongshu_analyzer.py generate_multi_html`
  - 在对话中展示HTML文件内容

### 可选分支
- **用户提供后台数据**：直接使用数据生成报告，跳过步骤2-3
- **用户回复序号继续分析相似账号**：获取该账号小红书号，执行完整流程（步骤2-7）

## 资源索引
- 脚本: [scripts/xiaohongshu_analyzer.py](scripts/xiaohongshu_analyzer.py) — query查询数据保存raw_data.json，build_report_data生成report_data.json模板，generate_html生成HTML报告
- 脚本: [scripts/html_generator.py](scripts/html_generator.py) — HTML报告生成逻辑（模板替换、字段填充、条件移除）
- 脚本: [scripts/html_checker.py](scripts/html_checker.py) — HTML数据完整性检查与修复
- 参考: [references/report_template.md](references/report_template.md) — 生成报告前必须先读取，输出时严格按照此格式
- 参考: [references/api_guide.md](references/api_guide.md) — 理解接口字段时读取
- 参考: [references/workflow_guide.md](references/workflow_guide.md) — 处理开场白、查询结果、相似账号展示、评分规则和数据填写规范时读取
- 参考: [references/benchmark_data.md](references/benchmark_data.md) — 理解各账号层级基准数据和优秀值参考时读取
- 资产: [assets/report_template.html](assets/report_template.html) — 单账号HTML格式报告模板
- 资产: [assets/report_data_template.json](assets/report_data_template.json) — 单账号报告数据模板
- 资产: [assets/multi_report_template.html](assets/multi_report_template.html) — 多账号对比HTML格式报告模板
- 资产: [assets/multi_report_data_template.json](assets/multi_report_data_template.json) — 多账号报告数据模板

## 注意事项
- 诊断报告必须在对话中直接输出，不得生成md文件
- 所有动态生成内容必须基于接口返回数据+WebSearch结果，禁止虚构
- 输出顺序：对话输出诊断报告 → 展示相似账号 → 生成HTML并展示
- HTML报告内容必须与对话输出完全一致
- HTML报告生成必须在步骤7执行，不得省略
- 互动规模和更新产能基于获取到的作品日期差计算，非固定30天
- 爆文判断基于互动数（点赞+收藏），非仅点赞数
- gmtCreate 是红狐数据系统首次收录时间，不是账号注册时间
