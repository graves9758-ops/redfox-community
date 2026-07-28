# Core Workflow

## 执行规则

- **用户提供正确的小红书视频链接时**：直接执行解析流程，无需额外确认或追问
- **用户未提供链接时**：提示用户输入小红书视频链接
- **用户提供的链接不是小红书链接时**：提示「该链接不是小红书视频链接」并终止解析

## 脚本调用

### 单链接

```bash
python3 "$SKILL_PATH/scripts/downloader.py" "https://www.xiaohongshu.com/explore/xxxxx"
```

### 批量链接（空格分隔）

```bash
python3 "$SKILL_PATH/scripts/downloader.py" "https://www.xiaohongshu.com/explore/aaaa" "https://www.xiaohongshu.com/explore/bbbb"
```

### 命令行参数

| 参数 | 说明 |
|------|------|
| `urls`（位置参数，必填） | 小红书视频链接（支持多个，空格分隔） |
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
python3 "$SKILL_PATH/scripts/downloader.py" "https://www.xiaohongshu.com/explore/xxxxx"
```

> 前往 [redfox.hk](https://redfox.hk/settings/api-keys?source=github) 注册获取 API Key。

## API 调用细节

- **API 端点**：`https://redfox.hk/story/api/parseWork/videoDownload/xhs`
- **请求方法**：POST，Content-Type: application/json，Header: X-API-KEY
- **请求体**：`{"url": "<链接>", "source": "xhs/小红书视频下载-GitHub"}`
- **成功判断**：响应 code 以 2 开头（如 200、2000）
- **错误码**：3106=缺少 Key，3107=Key 无效，400=参数错误

## 输出格式

成功时依次输出：
1. 内容描述（完整原文）
2. 资源列表（类型/时长/下载链接/封面链接）
3. 有效期提醒

批量模式下最后汇总成功/失败数量。

## 链接校验

- 支持域名：`xiaohongshu.com`、`xhslink.com`
- 支持 www 前缀自动去除
- 非白名单域名视为无效链接
