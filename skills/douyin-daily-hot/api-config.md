# API 配置与调用

## 🔑 鉴权方式

所有红狐 API 请求都需要在请求头中携带 API Key：

| 项 | 值 |
|----|----|
| 请求头 | `X-API-KEY` |
| 值来源 | 环境变量 `REDFOX_API_KEY`（或 Agent 配置文件的 `env.REDFOX_API_KEY`） |
| 获取地址 | https://redfox.hk/settings/api-keys |

## 📡 接口信息

- **接口地址**：`POST https://redfox.hk/story/api/dy/search/likesRank`
- **Content-Type**：`application/json`
- **认证方式**：请求头 `X-API-KEY`，值从环境变量 `REDFOX_API_KEY` 获取
- **固定参数**：`source`（数据来源标识，值由 Agent 按脚本约定传入）
- **可选参数**：
  - `type`：赛道分类（见 interaction-guide.md 赛道表）
  - `startTime` / `endTime`：日期范围（格式 `YYYY-MM-DD`）

## 📦 请求示例

```bash
curl -X POST "https://redfox.hk/story/api/dy/search/likesRank" \
  -H "X-API-KEY: $REDFOX_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"source": "dy", "type": "美食", "startTime": "2026-08-01", "endTime": "2026-08-07"}'
```

## ⚠️ 注意事项

- 数据每日定时收录更新，查询「今天」时请先向用户说明最新数据为昨日
- 日期回溯最多 30 天，超出范围需提示用户取最接近时间范围
- API Key 不要写入任何脚本或仓库文件，始终通过环境变量注入
- 接口被限流时（429），等待后重试，不要高频轮询
