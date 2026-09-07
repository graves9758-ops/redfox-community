# 小红书热门数据格式说明

## 概览

本文档定义了小红书热门数据查询脚本 `fetch_xhs_trends.py` 的输入输出格式规范。

## 输入格式

### 脚本参数

```bash
python scripts/fetch_xhs_trends.py --keyword <关键词> [选项]
```

| 参数 | 必填 | 说明 | 默认值 |
|------|------|------|--------|
| `--keyword` | 是 | 搜索关键词（支持多个关键词，逗号分隔，最多5个，总长度不超过200字符） | - |
| `--start-date` | 否 | 开始日期，格式 yyyy-MM-dd | 最近30天 |
| `--max-items` | 否 | 每类内容最多展示数量 | 10 |
| `--output-format` | 否 | 输出格式：text、json 或 markdown | markdown |
| `--output-file` | 否 | 输出文件路径 | 关键词_爆款数据.md |
| `--debug` | 否 | 调试模式，打印原始API响应 | False |

## 输出格式

### 四类爆款内容

脚本返回**近30天**的小红书热门数据，包含以下四类爆款内容：

| 内容类型 |适用场景 |
|---------|---------|
| **新手友好爆款** |  适合模仿学习，发现低成本爆款 |
| **当日点赞爆款** |  了解当前最热门内容 |
| **爆发增长内容** | 发现快速增长的内容 |
| **持续增长内容** | 发现持续增长的内容 |

### 作品数据字段（完整）

每个作品包含以下字段：

#### 作品基本信息

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `photoId` | string | 作品ID（唯一标识） |
| `title` | string | 作品标题 |
| `desc` | string | 作品描述/正文 |
| `publicTime` | string | 发布时间（格式：YYYY-MM-DD HH:MM:SS） |

#### 作者信息

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `userId` | string | 作者ID |
| `userName` | string | 作者名称 |
| `userHeadUrl` | string | 作者头像URL |
| `fans` | int | 粉丝数 |


**作者主页链接拼接规则**：
```
https://www.xiaohongshu.com/user/profile/{userId}
```

#### 互动数据（非增量类）

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `useLikeCount` | int | 点赞数 |
| `collectedCount` | int | 收藏数 |
| `useCommentCount` | int | 评论数 |
| `useShareCount` | int | 分享数 |
| `interactiveCount` | int | 互动总数 |

#### 互动数据（增量类）

增量类（单日增量、七日增量）的数据在 `anaAdd` 对象中：

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `anaAdd.addLikeCount` | int | 新增点赞数 |
| `anaAdd.addCollectedCunt` | int | 新增收藏数（注意：API字段名有拼写错误） |
| `anaAdd.addCommentCount` | int | 新增评论数 |
| `anaAdd.addShareCount` | int | 新增分享数 |
| `anaAdd.addInteractiveount` | int | 新增互动总数（注意：API字段名有拼写错误） |
| `anaAdd.useLikeCount` | int | 总点赞数 |
| `anaAdd.collectedCount` | int | 总收藏数 |
| `anaAdd.useCommentCount` | int | 总评论数 |
| `anaAdd.useShareCount` | int | 总分享数 |
| `anaAdd.interactiveCount` | int | 总互动数 |
| `anaAdd.pred_readnum` | int | 预测阅读数 |

#### 图片链接

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `coverUrl` | string | 封面图URL |
| `thumbnail` | string | 缩略图URL |

### JSON 输出示例

```json
{
  "keyword": "高考",
  "low_fan_explosive": [
    {
      "photoId": "69aa603c0000000015021b18",
      "title": "对于26高考女宝们的选大学建议",
      "desc": "一定要选人文关怀好以及男女平等的大学...",
      "publicTime": "2026-03-06 13:03:56",
      "userId": "68ebaae60000000037006191",
      "userName": "Alley",
      "userHeadUrl": "https://sns-avatar-qc.xhscdn.com/...",
      "fans": 2,
      "useLikeCount": 23439,
      "collectedCount": 15610,
      "useCommentCount": 846,
      "useShareCount": 697,
      "interactiveCount": 39895,
      "coverUrl": "http://sns-img-hw.xhscdn.com/...",
      "thumbnail": "http://sns-img-hw.xhscdn.com/..."
    }
  ],
  "daily_like_top": [...],
  "daily_increment": [
    {
      "photoId": "...",
      "title": "...",
      "anaAdd": {
        "addLikeCount": 12345,
        "addCollectedCunt": 2345,
        "addCommentCount": 567,
        "addShareCount": 89,
        "addInteractiveount": 15346,
        "useLikeCount": 50000,
        "collectedCount": 10000,
        "useCommentCount": 2000,
        "useShareCount": 500,
        "interactiveCount": 62500,
        "pred_readnum": 800000
      }
    }
  ],
  "weekly_increment": [...]
}
```

### 文本输出格式（表格形式）

文本输出采用 Markdown 表格格式，结构清晰，便于阅读：

```markdown
## 1、新手友好爆款
统计时间：近30天

| 序号 | 标题 | 作者 | 作品分类 | 收藏 | 分享 | 评论 | 点赞 | 互动总数 |
|------|------|------|----------|------|------|------|------|----------|
| 1 | 对于26高考女宝们的选大学建议 | [Alley](https://www.xiaohongshu.com/user/profile/68ebaae60000000037006191)（粉丝：2） | 教育 / 大学教育 | 15610 | 697 | 846 | 23439 | 39895 |
| 2 | 查出来个高考状元 | [泽陈泽陈](https://www.xiaohongshu.com/user/profile/684c0a9d000000001d00b1a1)（粉丝：4279） | 教育 / 中学教育 | 2860 | 221 | 44 | 23617 | 26521 |
...
| 10 | ... | ... | ... | ... | ... | ... | ... | ... |

## 2、当日点赞爆款
统计时间：近30天

| 序号 | 标题 | 作者 | 作品分类 | 收藏 | 分享 | 评论 | 点赞 |
|------|------|------|----------|------|------|------|------|
| 1 | 被1w人看过的地理书x厦门日光岩 | [深海里遇见你](https://www.xiaohongshu.com/user/profile/634a71b8000000001802d092)（粉丝：7404） | 教育 / 中学教育 | 57637 | 14733 | 2818 | 460237 |
...
| 10 | ... | ... | ... | ... | ... | ... | ... |

## 3、爆发增长内容
统计时间：近30天

| 序号 | 标题 | 作者 | 作品分类 | 新增收藏 | 新增分享 | 新增评论 | 新增点赞 | 互动增量 |
|------|------|------|----------|----------|----------|----------|----------|----------|
| 1 | 今年春晚预测的中高考考点❗ | [北大旺仔](https://www.xiaohongshu.com/user/profile/5de3e57c00000000010055f8)（粉丝：179984） | 教育 / 中学教育 | 14639 | 1485 | 102 | 19257 | 33998 |
...
| 10 | ... | ... | ... | ... | ... | ... | ... | ... |

## 4、持续增长内容
统计时间：近30天

| 序号 | 标题 | 作者 | 作品分类 | 新增收藏 | 新增分享 | 新增评论 | 新增点赞 | 互动增量 |
|------|------|------|----------|----------|----------|----------|----------|----------|
| 1 | 高考文言文词类活用-活用作状语 友好版！ | [我是摆子](https://www.xiaohongshu.com/user/profile/5d99de820000000001000015)（粉丝：52197） | 教育 / 中学教育 | 29937 | 1162 | 150 | 75196 | 105283 |
...
| 10 | ... | ... | ... | ... | ... | ... | ... | ... |
```

### 表格字段说明

#### 新手友好爆款
| 列名 | 说明 |
|------|------|
| 序号 | 排名|
| 标题 | 作品标题|
| 作者 | 作者名称（可点击跳转）+ 粉丝数 |
| 收藏 | 收藏数 |
| 分享 | 分享数 |
| 评论 | 评论数 |
| 点赞 | 点赞数 |
| 互动总数 | 互动总数 |

#### 当日点赞爆款
| 列名 | 说明 |
|------|------|
| 序号 | 排名|
| 标题 | 作品标题|
| 作者 | 作者名称（可点击跳转）+ 粉丝数 |
| 收藏 | 收藏数 |
| 分享 | 分享数 |
| 评论 | 评论数 |
| 点赞 | 点赞数 |

#### 增长内容
| 列名 | 说明 |
|------|------|
| 序号 | 排名 |
| 标题 | 作品标题 |
| 作者 | 作者名称（可点击跳转）+ 粉丝数 |
| 新增收藏 | 新增收藏数 |
| 新增分享 | 新增分享数 |
| 新增评论 | 新增评论数 |
| 新增点赞 | 新增点赞数 |
| 互动增量 | 互动增量总数 |

## 使用注意事项

### 数据获取原则

1. **必须调用脚本查询**：不能使用其他方式查询或直接搜索网络资讯
2. **必须等待脚本执行完成**：获取返回结果后才能进行后续步骤
3. **必须展示完整数据列表**：不能跳过或询问用户

### 数据展示原则

1. **展示所有字段**：每个作品展示完整信息，包括封面图、作者链接、分类、互动数据等
2. **四类爆款内容全部展示**：

### 字段说明

1. **增量内容的 anaAdd 字段**：仅爆发增长和持续增长内容包含此字段
2. **API字段拼写错误**：`addCollectedCunt` 和 `addInteractiveount` 是 API 的原始拼写，保持不变
3. **封面图和缩略图**：通常相同，但有时缩略图分辨率更低
