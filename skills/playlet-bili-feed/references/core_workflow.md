# 核心执行流程

## 第一步：日期有效性预检（必须执行，先于任何接口调用）

> ⛔ **核心规则：未经用户确认，禁止调用任何数据接口，禁止自动执行 `--latest`**
>
> 注：`--latest` 允许在用户确认后自动回退；脚本层会先做**真实探活**（轻量请求），以接口返回为准判断日期是否有数据。

### 数据更新规则
- 每日 **15:00** 更新前一天的数据（**实际更新时间可能延迟**，以真实探活结果为准）
- **15:00前**：估算最新可用日期 = T-2（前天）
- **15:00后**：估算最新可用日期 = T-1（昨天）

### 执行流程（每次查询前强制执行）

1. 获取当前系统日期 T 和当前时间，按15:00规则**估算**最新可用日期（仅作初始起点）
2. 用 `pageSize=1` 不带 keyword 的轻量请求**真实探测**目标日期是否有数据
3. **若探活命中**（该日期有数据）：直接执行查询，无需额外确认
4. **若探活未命中**（该日期无数据），向用户输出以下提示：

```
**⚠️{查询日期}数据尚未更新**
数据更新规则：每日15:00更新前一天的数据
当前可查询的最新日期：{最新可查询到数据的日期}

是否需要查询{最新可查询到数据的日期}的数据？
```

5. **等待用户明确确认后**，才能执行查询（带 `--latest` 参数，脚本会自动回退定位最近有数据的日期）
6. 若用户拒绝，则不执行任何接口调用

### 示例对话

```
用户：查询今天的短剧B站日报
Agent：⚠️2026-06-16数据尚未更新（探活确认该日期无数据）
      数据更新规则：每日15:00更新前一天的数据
      当前可查询的最新日期：2026-06-14

      是否需要查询2026-06-14的数据？
用户：好的
Agent：（执行 python3 "$SKILL_PATH/scripts/playlet_bili_daily.py" --latest）
```

## 第二步：生成爆款日报

```bash
# 生成最新一期日报（用户确认后，自动探测回退到最近有数据的日期，不扣积分）
python3 "$SKILL_PATH/scripts/playlet_bili_daily.py" --latest

# 生成指定日期日报（历史日期已有数据，无需确认）
python3 "$SKILL_PATH/scripts/playlet_bili_daily.py" --date 2026-06-10

# 自定义题材查询（用户指定方向，仅用用户题材列表批量查询）
python3 "$SKILL_PATH/scripts/playlet_bili_daily.py" --topics "穿越,霸总,重生,悬疑" --latest

# 订阅 / 取消订阅
python3 "$SKILL_PATH/scripts/playlet_bili_daily.py" --subscribe
python3 "$SKILL_PATH/scripts/playlet_bili_daily.py" --unsubscribe
```

> **查询策略**：默认查询全部短剧内容（pageSize=200），所有题材通过批量接口一次性查询。用户自定义题材时仅使用用户提供的列表，同样批量查询。**关键词校验规则（v2.3.1）**：关键词需命中短剧题材词库（`topic_keywords` 中规定的**题材名+全部相关词**，如「打脸」命中逆袭题材相关词、「总裁」命中霸总题材相关词），**命中后直接使用该关键词查询数据**；不满足时提醒"关键词不满足查询条件"并推荐相关词，**不发起接口请求**。**无数据确认制**：查询无匹配数据或全量数据不足时，**禁止自动扩展题材/降级全量**，提示推荐题材关键词并等待用户确认后再查询。

> **降失败率机制（v2.0增强）**：
> - **真实探活**：查询前先用 `pageSize=1` 无 keyword 轻量请求探测目标日期，以接口返回为准（数据源实际更新可能晚于15:00），无数据立即拦截，避免空跑耗额度
> - **自动回退**：`--latest` 从最近日期向前最多回退7天，定位第一个有数据的日期再出日报
> - **空结果重试**：单题材查询为空/异常时自动重试1次（间隔4秒）
> - **题材词校验**：`--topics` 传入非题材词时提示，建议改用题材词库（v2.3.1：校验匹配题材名+全部相关词，命中后直接查询该关键词）
> - **结构化空因**：空结果明确输出"无数据/关键词无匹配/接口异常"及下一步建议

## 第三步：执行创作趋势分析

日报生成后，**必须**基于聚类结果自动执行创作趋势分析：

1. 读取题材聚类结果，选取 TOP 5 热门题材
2. 分析每个题材的爆款数量、平均互动数据、头部作品特征
3. 识别新兴起量题材（数量少但互动高）
4. 输出结构化创作趋势报告

生成的HTML日报保存在 `~/Downloads/QoderReports/`，自动浏览器打开。终端同步输出题材分类表格 + 创作趋势分析报告。

## 查询策略

### 默认查询
- 查询全部短剧内容（pageSize=200）
- 全量数据不足（<100条）时**不自动扩展题材**，提示推荐题材（穿越→霸总→重生→悬疑→甜宠→逆袭）并等待用户确认（v2.3.1 无数据确认制）
- 查询前自动探活目标日期；空结果自动重试1次

### 自定义查询
- 用户指定题材通过批量接口一次性查询（不使用自动扩展列表）
- **关键词校验**：命中短剧题材词库（题材名+全部相关词，如「打脸」命中逆袭题材相关词）后**直接使用该关键词查询数据**
- 查询结果自动去重（基于photoId）
- 题材聚类基于标题关键词匹配
- 非题材词（热点词/商品词等）给出提示，建议改用题材词库，避免空结果

## 字段映射（B站短剧特殊处理）

### API字段说明

| 字段 | B站短剧API行为 | 处理方式 |
|------|--------------|---------|
| `readCount` | 有真实数据（播放量） | ✅ 正常获取，但不展示 |
| `likeCount` | 真实点赞数 | ✅ 作为主排序指标 |
| `commentCount` | 真实评论数 | ✅ 正常展示 |
| `shareCount` | 真实分享数 | ✅ 正常展示 |
| `url` | 恒为None | 用`photoId`（BV号）智能拼接 |
| `photoId` | BV号格式（如BV1onEQ6sEiL） | 直接用于链接生成 |
| `coverUrl` | 含`hdslb.com`（B站CDN） | 正常加载，无需防盗链 |

### 链接生成规则

```python
# B站短剧API不返回url字段，使用BV号拼接视频链接
photo_id = item.get("photoId") or ""  # BV号格式
if photo_id:
    url = f"https://www.bilibili.com/video/{photo_id}"
    title_html = f'<a href="{url}" target="_blank" class="article-title">{title}</a>'
else:
    title_html = f'<span class="article-title">{title}</span>'
```

**说明**：API的url字段恒为None，作品链接通过BV号拼接B站视频地址。

### 图片加载规则

```html
<!-- B站CDN（hdslb.com）无防盗链限制，无需设置referrerpolicy -->
<img src="{coverUrl}" loading="lazy">
```

### 排序规则

```python
# B站短剧统一按likeCount降序排序
items.sort(key=lambda x: x.get("likeCount", 0), reverse=True)
```

## 指标展示规则

### 展示指标
每个作品最多展示3项指标：
- 🔗 分享（shareCount）
- 👍 点赞（likeCount）
- 💬 评论（commentCount）

### 零值隐藏规则
**当某项指标值为0时，不展示该字段**。动态构建指标HTML：

```python
# 获取原始数值
raw_shares = item.get("shareCount", 0) or 0
raw_likes = item.get("likeCount", 0) or 0
raw_comments = item.get("commentCount", 0) or 0

# 值为0时不展示该字段
metrics_parts = []
if raw_shares > 0:
    metrics_parts.append(f'<span class="metric">🔗 {format_number(raw_shares)}</span>')
if raw_likes > 0:
    metrics_parts.append(f'<span class="metric">👍 {format_number(raw_likes)}</span>')
if raw_comments > 0:
    metrics_parts.append(f'<span class="metric">💬 {format_number(raw_comments)}</span>')
metrics_html = ''.join(metrics_parts)
```

## HTML输出格式

### 样式规范
- **深色主题**：`#1a1a1a` 背景
- **B站主题色**：`#00A1D6`（替代抖音的 `#FB7299`）
- **卡片式网格布局**：`grid-template-columns: repeat(auto-fill, minmax(360px, 1fr))`
- **题材编号**：01/02/03...
- **中文日期显示**：2026年6月16日 星期二
- **图片懒加载**：`loading="lazy"`

### 与抖音版本的差异

| 项目 | 抖音版本 | B站版本 |
|------|---------|--------|
| API接口 | queryPlayletMsgs | queryPlayletMsgs |
| platform | 1 | 6 |
| 排序字段 | likeCount | likeCount |
| 播放量 | 可用（readCount） | 可用但不展示（readCount） |
| 展示指标 | 播放/点赞/评论 | 分享/点赞/评论（零值隐藏） |
| url字段 | 有效 | None（用BV号拼接） |
| 内容来源 | 抖音原生 | B站原生 |
| 链接格式 | douyin.com/video/{id} | bilibili.com/video/{BV号} |
| 主题色 | #FB7299（粉） | #00A1D6（蓝） |
| 文件名 | 短剧抖音日报 | 短剧B站日报 |
| 图片防盗链 | 需referrerpolicy | 无需（B站CDN） |
