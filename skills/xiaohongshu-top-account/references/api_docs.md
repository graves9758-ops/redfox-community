# 小红书榜单 API 接口文档

## 接口基础信息

| 字段 | 值 |
|------|-----|
| 接口地址 | `https://onetotenvip.com/story/xhsData/query` |
| 请求方式 | POST |
| Content-Type | `application/json` |
| 认证方式 | 无（公开接口） |

---

## 请求参数（已校验）

```json
{
  "dateType": 1,            // 榜单日期类型：1=日榜  2=周榜  3=月榜（必填）
  "rankDate": "2026-04-28", // 榜单日期 yyyy-MM-dd（必填）
                            //   日榜：填当日日期，如 2026-04-28
                            //   周榜：填该周**周一**日期，如 2026-04-20
                            //   月榜：填该月第一天，如 2026-03-01
  "type": "体育锻炼",        // 赛道分类，默认"综合全部"（必填）
  "source": "小红书指数榜"   // 固定值（必填）
}
```

> ⚠️ **重要**：`source` 必须为 `"小红书指数榜"`，使用其他值会导致接口返回空数据！
> 
> ⚠️ 注意：`page`/`pageSize` 参数无效，接口每次固定返回 50 条数据。

---

## 响应结构（实际返回）

```json
{
  "code": 2000,
  "data": [
    {
      "accountLink":    "https://www.xiaohongshu.com/user/profile/...",
      "accountName":    "恋与深空",
      "accountRanking": 1,
      "category":       "数码科技",
      "fansCount":      "254.06w",
      "fansGrowth":     "6919",
      "likedGrowth":    "24.64w",
      "commentsGrowth": "6.68w",
      "collectedGrowth":"2.53w",
      "sharedGrowth":   "13.39w",
      "newNoteCount":   null,
      "dataFetchTime":  "2026-04-29 19:00:01",
      "rankDate":       "2026-04-28",
      "rankPeriod":     "日榜"
    }
  ]
}
```

> ⚠️ 注意：新接口**不返回** `comprehensiveScore`（综合评分）字段；  
> 互动数各字段均为**字符串格式**，如 `"6.68w"`、`"1245"`。

---

## 错误码

| code | 含义 |
|------|------|
| 2000 | **成功**（注意：成功码是 2000 不是 0！） |
| 其他 | 错误，data 为空数组 |

---

## 字段映射（fetch_rank.py normalized JSON）

| 接口原始字段 | normalized 字段 | 含义 |
|------------|----------------|------|
| `accountRanking` | `rank` | 排名 |
| `accountName` | `accountName` | 账号名 |
| `category` | `category` | 赛道 |
| `fansCount` | `followers` | 总粉丝数 |
| `newNoteCount` | `newNoteCount` | 新增笔记数 |
| `fansGrowth` | `newFans` | 新增粉丝 |
| `likedGrowth` | `newLikes` | 新增点赞 |
| `commentsGrowth` | `newComments` | 新增评论 |
| `collectedGrowth` | `newCollects` | 新增收藏 |
| `sharedGrowth` | `newShares` | 新增分享 |
| `accountLink` | `profileUrl` | 主页链接 |

---

## 可用品类列表

```
综合全部
出行代步 / 休闲爱好 / 影视娱乐 / 数码科技 / 医疗保健 / 综合杂项
星座情感 / 时尚穿搭 / 婚庆婚礼 / 拍摄记录 / 学习教育 / 化妆美容
居家装修 / 旅行度假 / 亲子育儿 / 个人护理 / 美味佳肴 / 职业发展
宠物天地 / 潮流鞋包 / 日常生活 / 科学探索 / 新闻资讯 / 体育锻炼
```

**常用别名映射：**
| 用户说 | 映射到 |
|--------|--------|
| 健身、运动、瑜伽 | 体育锻炼 |
| 美妆、彩妆、护肤 | 化妆美容/个人护理 |
| 美食、探店、烹饪 | 美味佳肴 |
| 旅行、旅游 | 旅行度假 |
| 母婴、育儿 | 亲子育儿 |
| 穿搭、时尚 | 时尚穿搭 |

---

## 榜单更新规则

| 榜单类型 | 更新时间 | 统计范围 | rankDate 填写规则 | 示例 |
|---------|---------|---------|-----------------|------|
| 日榜 | 每日 19:00 | 前一天 | 填当天日期 | "2026-04-28" |
| 周榜 | 每周一 15:00 | 上周 | 填该周**周一**日期 | "2026-04-20" |
| 月榜 | 每月1日 上午9:00 | 上月 | 填该月**1日** | "2026-04-01" |

### 日期回退计算

根据当前时间判断取第几期数据：

| 榜单类型 | 当前时间 < 更新时间 | 当前时间 >= 更新时间 |
|---------|-------------------|-------------------|
| 日榜 (19:00更新) | offset=2 (前2天) | offset=1 (前1天) |
| 周榜 (周一15:00更新) | offset=2 (前2周) | offset=1 (前1周) |
| 月榜 (2号09:00更新) | offset=2 (前2月) | offset=1 (前1月) |

> ⚠️ **月榜必须用每月1日**，实测用月末最后一天（如 "2026-03-31"）返回空数据！

> ⚠️ **周榜用周一日期**，实测用周日日期（如 "2026-04-20" 周日）会返回空数据！

---

## 常见问题

### 1. 体育锻炼分类数据为空

部分分类（如体育锻炼）在某些日期可能返回空数据。需要自动回退日期尝试：
```
2026-04-29: 0条 → 回退
2026-04-28: 50条 ✓
```

### 2. 互动数据计算

最高互动需要自行计算：
```python
def parse_num(s):
    s = str(s).replace('w', '').replace('W', '')
    if '.' in s:
        return float(s) * 10000
    return float(s)

interaction = parse_num(item['newLikes']) + \
              parse_num(item['newComments']) + \
              parse_num(item['newCollects']) + \
              parse_num(item['newShares'])
```

> ⚠️ 接口返回的 `newInteraction` 字段值可能为0，不要直接使用！

---

## Python 调用示例

```python
import requests
from datetime import date, timedelta

url = "https://onetotenvip.com/story/xhsData/query"

# 日榜示例（体育锻炼）
payload_day = {
    "dateType": 1,
    "rankDate": "2026-04-28",
    "type": "体育锻炼",
    "source": "小红书指数榜"
}

# 周榜示例
payload_week = {
    "dateType": 2,
    "rankDate": "2026-04-20",  # 上周周一
    "type": "综合全部",
    "source": "小红书指数榜"
}

# 月榜示例
payload_month = {
    "dateType": 3,
    "rankDate": "2026-04-01",  # 上月1日
    "type": "综合全部",
    "source": "小红书指数榜"
}

resp = requests.post(url, json=payload_day, timeout=15)
data = resp.json()

if data["code"] == 2000:        # 注意：成功码是 2000
    print(f"获取到 {len(data['data'])} 条数据")
    for item in data["data"]:
        print(item["accountRanking"], item["accountName"],
              item["fansCount"], item["likedGrowth"])
else:
    print(f"接口返回错误: {data}")
```
