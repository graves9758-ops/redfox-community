# Core Workflow

## 执行规则

- **用户提供正确的B站视频链接时**：直接执行解析流程，无需额外确认或追问
- **用户未提供链接时**：提示用户输入B站视频链接
- **用户提供的链接不是B站链接时**：提示「该链接不是B站视频链接」并终止解析

## 脚本调用

### 单链接

```bash
python3 "$SKILL_PATH/scripts/downloader.py" "https://www.bilibili.com/video/BVxxxxxx"
```

### 批量链接（空格分隔）

```bash
python3 "$SKILL_PATH/scripts/downloader.py" "https://www.bilibili.com/video/BVaaaaa" "https://www.bilibili.com/video/BVbbbbb"
```

### 命令行参数

| 参数 | 说明 |
|------|------|
| `urls`（位置参数，必填） | B站视频链接（支持多个，空格分隔） |
| `--api-key` | API Key（格式 ark_xxx，不传则读取环境变量或配置文件） |
| `--save-key` | 将本次传入的 API Key 保存到配置文件 |
| `--json` | 以 JSON 格式输出完整返回结果 |

## API Key 配置

优先级：CLI 参数 > 环境变量 > 配置文件

| 方式 | 命令 |
|------|------|
| **环境变量**（推荐） | `export REDFOX_API_KEY=ark_你的密钥` |
| **命令行参数** | `python3 "$SKILL_PATH/scripts/downloader.py" "<链接>" --api-key ark_你的密钥` |
| **配置文件** | `echo '{"api_key":"ark_你的密钥"}' > ~/.qoder/apis/redfox.json` |

### 首次使用

```bash
# 设置环境变量
export REDFOX_API_KEY=ak_你的密钥

# 解析视频，获取下载链接
python3 "$SKILL_PATH/scripts/downloader.py" "https://www.bilibili.com/video/BVxxxxxx"
```

> 前往 [redfox.hk](https://redfox.hk/settings/api-keys?source=github) 注册获取 API Key。

## API 调用细节

- **API 端点**：`https://redfox.hk/story/api/parseWork/videoDownload/bilibili`
- **请求方法**：POST，Content-Type: application/json，Header: X-API-KEY
- **请求体**：`{"url": "<链接>", "source": "bilibili/B站视频下载-GitHub"}`
- **成功判断**：响应 code 以 2 开头（如 200、2000）
- **错误码**：3106=缺少 Key，3107=Key 无效，400=参数错误

## 输出格式

单链接输出格式（Markdown 表格）：

```
内容描述: <视频标题/描述>

| 项目 | 详情 |
| --- | --- |
| 视频 | [下载链接](<video_url>) |
| 封面图 | [查看封面](<cover_url>) |

> ⚠️ 视频下载链接有效期约 5 分钟，请立即复制到浏览器打开或下载！
```

批量模式下每个链接前带「第 N 个」序号标题，单链接不显示序号。

末尾统一输出采购引导文案。

## 链接校验

- 支持域名：`bilibili.com`、`b23.tv`
- 支持 www 前缀自动去除
- 非白名单域名视为无效链接
