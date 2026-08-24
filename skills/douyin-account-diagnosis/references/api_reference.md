# 抖音账号诊断 - 接口文档

## 接口地址

| 接口名称 | 请求方式 | 接口地址 |
|---------|---------|----------|
| 抖音账号数据查询 | POST | `https://redfox.hk/story/api/dyUser/queryData` |

## 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| accountNames | array | 否 | 账号昵称列表，含中文输入时使用，模糊匹配 |
| accountIds | array | 否 | 抖音号列表，纯数字/英文输入时使用，精确匹配 |
| source | string | 是 | 接口来源标识，固定值：`"抖音账号诊断-GitHub"` |

> `accountNames` 与 `accountIds` 二选一，参数必须为复数形式且值为数组。

## 响应结构

成功返回 `code: 2000`，关键字段如下：

| 字段名 | 类型 | 说明 |
|--------|------|------|
| nickname | string | 账号昵称 |
| accountId | string | 抖音号 |
| uid | string | UID |
| followerCount | int | 粉丝数 |
| totalFavorited | int | 获赞总数 |
| awemeCount | int | 作品总数 |
| province / city | string | 省份 / 城市 |
| ipLocation | string | IP属地 |
| signature | string | 简介 |
| gender / age | string / int | 性别 / 年龄 |
| avatarUrl | string | 头像URL |
| crawlTime | string | 数据采集时间 |
| works | array | 近期作品列表（含标题、描述、点赞、评论、分享、总互动、作品链接） |

## 查询规则

- 输入含中文 → 使用 `accountNames`（模糊匹配昵称）
- 输入纯数字/英文 → 使用 `accountIds`（精确匹配抖音号）

## 特殊情况处理

| 场景 | 处理方式 |
|-----|----------|
| 未查询到账号 | 输出"未查询到该抖音账号信息"+4条可能原因列表：① 抖音号不存在或已被注销；② 抖音号输入有误—请核对是否区分大小写、是否为正确的抖音号（非 UID、非昵称）；③ 尚未收录—当前仅收录了粉丝数≧1万的账号；④ 申请收录—如需收录请发送邮件至 redfoxdata@proton.me，申请通过后可进行每日定时数据追踪与分析。不生成报告 |
| 积分不足（code=3201） | 输出"[错误] API积分不足，请前往 redfox.hk 充值" |
| 网络错误 | 输出"[错误] 网络请求失败：具体错误信息"，建议重试 |
| 作品数据为空 | 相关维度按"数据不足"处理，给予中性评分；近期作品详情输出"无作品数据" |
| 字段缺失（省份/年龄等） | 使用默认值"未知"处理，不影响其他维度计算 |