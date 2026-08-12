# Core Workflow

## 🔄 工作流程

### Step 1：调用提文案脚本（自动完成「提交任务 → 轮询 → 取结果」两步）

```bash
python3 ~/.workbuddy/skills/kuaishou-text-extract/scripts/extract_ks_text.py "<视频链接>" [--interval 3] [--timeout 120]
# 或查询已有任务结果（脚本中途超时后可续查）
python3 ~/.workbuddy/skills/kuaishou-text-extract/scripts/extract_ks_text.py --task-id "<taskId>"
```

**参数说明：**

| 参数 | 必填 | 含义 |
|------|------|------|
| `url` | 二选一 | 快手视频分享链接（如 `https://www.kuaishou.com/short-video/3x88nbkyjtga6zk`） |
| `--task-id` | 二选一 | 任务 ID，直接查询已有任务结果（不提交新任务） |
| `--interval` | 否 | 轮询间隔秒数（默认 3） |
| `--timeout` | 否 | 轮询总超时秒数（默认 120，超时返回当前状态，可用 --task-id 续查） |

**脚本输出结构：**

| 字段 | 说明 |
|------|------|
| `task_id` | 任务 ID（可续查） |
| `status` | 任务状态：succeeded / failed / processing / asr_processing 等 |
| `fail_reason` | 失败原因（成功时为 null） |
| `text` | 完整提取文案（所有片段拼接） |
| `stamp_sents` | 带时间戳的分句数组（text / start / end / start_fmt / end_fmt） |

### Step 2：展示提取结果

> 📝 视频文案提取成功（taskId: `{task_id}`），完整文案如下：

```markdown
{完整文案 text}
```

### Step 3：若用户需要带时间戳的分句（用于字幕/剪辑定位），输出：

> ⏱️ 带时间戳分句（共 N 句）：

```markdown
| # | 时间区间 | 文案片段 |
|---|---------|---------|
| 1 | 0.20s - 6.72s | 视频中这个小孩今年才3岁，他叫苗苗... |
| 2 | 7.00s - 9.88s | 锅里的青菜在油的包裹下发出滋滋的声响。 |
```

### Step 4：处理中/失败情况

- 若返回 `processing` / `asr_processing` / `running` / `uploading` 等状态且无文本：提示用户「任务仍在处理中，可稍后回复查询」，并用 `--task-id` 续查。
- 若 `status=failed`：展示失败原因（如「视频链接解析失败」），提示核对链接是否为快手视频分享链接（支持 `www.kuaishou.com/short-video/xxx` 或 `v.kuaishou.com/xxx`，不支持 photoId 直接构造的链接）。
- 若轮询超时：提示用户任务 ID，稍后可用 `--task-id` 继续查询。

### Step 5：后续引导（可选）

> 💡 需要我根据这段文案分析选题结构、生成仿写脚本，或继续分析该作品评论区口碑吗？