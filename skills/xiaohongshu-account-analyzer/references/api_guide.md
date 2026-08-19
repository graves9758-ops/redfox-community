# API接口与评分逻辑

## 接口请求

**请求方式**：POST
**请求地址**：https://redfox.hk/story/api/xhsUser/query

| 参数名  | 类型          | 必填 | 说明                                  |
| ------- | ------------- | ---- | ------------------------------------- |
| userIds | Array<String> | 是   | 小红书号列表                          |
| source  | String        | 否   | 来源标识，默认"小红书账号诊断-Github" |

**请求头**：
| Header | 说明 |
|--------|------|
| Content-Type | application/json |
| X-API-KEY | API密钥，从环境变量 `REDFOX_API_KEY` 读取 |

**请求体示例**：

```json
{
  "userIds": ["26112666886"],
  "source": "小红书账号诊断-Github"
}
```

## 接口响应字段

### 账号数据

| 字段                   | 说明                                       | 示例                                                 |
| ---------------------- | ------------------------------------------ | ---------------------------------------------------- |
| nickname               | 账号名                                     | "小小希"                                             |
| desc                   | 简介                                       | "准八 丨26届生地会考 丨27届中考定期搞福利🥺谢谢支持" |
| 小红书号               | 小红书号                                   | "26112666886"                                        |
| fans                   | 粉丝数                                     | 4431                                                 |
| level                  | 官方等级（可为null）                       | 7 或 null                                            |
| userAttribute          | 账号标识                                   | "素人"/"尾部kol"/"腰部kol"/"头部kol"/"企业"/"品牌"   |
| avatar                 | 头像URL                                    | "https://..."                                        |
| totalWork              | 作品总数                                   | 127                                                  |
| liked                  | 总点赞数                                   | 217035                                               |
| collected              | 总收藏数                                   | 24745                                                |
| noteCountThirty        | 近30天发作品数                             | 70                                                   |
| interactiveCountThirty | 近30天作品互动量                           | 133547                                               |
| recentIndex            | 周指数                                     | 827.32                                               |
| topProvinces           | 粉丝省份偏向                               | "广东"                                               |
| topAges                | 粉丝年龄偏向                               | "<18"                                                |
| fansGender             | 粉丝性别偏向                               | {"male_ratio": "0.13", "female_ratio": "0.87"}       |
| gmtCreate              | 红狐数据系统首次收录时间（非账号注册时间） | "2025-04-22 10:30:00"                                |

### 作品数据（works数组，最多5篇）

| 字段           | 说明                   | 示例                              |
| -------------- | ---------------------- | --------------------------------- |
| id             | 作品ID                 | "69e478b70000000021007e7b"        |
| title          | 作品标题               | "姚译添疯了"                      |
| createTime     | 发布时间（毫秒时间戳） | "1776580791000"                   |
| likedCount     | 点赞数                 | 22                                |
| collectedCount | 收藏数                 | 0                                 |
| workUrl        | 作品链接               | "https://www.xiaohongshu.com/..." |

### 相似账号数据（similarAccounts数组）

| 字段                   | 兼容字段                 | 说明     |
| ---------------------- | ------------------------ | -------- |
| 小红书号               | accountId, 小红书号      | 小红书号 |
| nickname               | accountName, name        | 账号名称 |
| fans                   | followerCount, fansCount | 粉丝数   |
| liked                  | totalLikeCount           | 总点赞数 |
| interactiveCountThirty | interactiveCountThirty   | 总互动数 |

## 评分规则

评分规则详见 [workflow_guide.md](workflow_guide.md) 中的"评分体系"章节，此处不再重复。

## 注意事项

- 脚本根据账号标识动态计算爆文标准
- 爆文判断基于互动数（点赞+收藏），而非仅点赞数
- 互动规模和更新产能基于获取到的作品日期差计算
- level、avatar、部分works字段值可为null，脚本已做兼容处理
- gmtCreate 是红狐数据系统首次收录该账号的时间，不是小红书账号注册时间
