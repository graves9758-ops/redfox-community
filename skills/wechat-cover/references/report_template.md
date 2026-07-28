# 爆款封面分析报告 HTML 模板

## 文件说明

本模板采用 **JS 渲染型** 架构：HTML 结构和渲染逻辑固定在 `references/report_template.html` 中，Agent 只需注入一段 JSON 数据，页面自动渲染，无需在输出时临时生成大量 HTML。

**模板文件**：`references/report_template.html`

**⚠️ 重要：按风格类型分类展示封面，不要逐张输出分析结果！**

---

## 使用方式

1. 读取 `references/report_template.html` 模板文件
2. 将分析结果组装为 JSON 对象
3. 用 SearchReplace 将模板中 `__REPORT_DATA__` 的值替换为实际 JSON
4. 写入 `./爆款封面分析报告_{关键词}.html`
5. 执行 `open ./爆款封面分析报告_{关键词}.html` 打开浏览器

**替换目标**（模板中唯一的占位区域）：
```javascript
var __REPORT_DATA__ = {
    "keyword": "",
    "analysisCount": 0,
    "styles": [],
    "plans": []
};
```

---

## JSON 数据结构

```json
{
    "keyword": "美食,食谱,做饭",
    "analysisCount": 20,
    "styles": [
        {
            "name": "🍽️ 家常俯拍·满桌多菜",
            "count": 12,
            "coreVisual": "俯视/高角度拍摄，3-6道菜品铺满白色桌面，自然暖光",
            "features": "满桌丰盛感营造家的味道；白色桌面干净清爽；菜品色彩丰富",
            "covers": [
                "https://mmbiz.qpic.cn/xxx1/0?wx_fmt=jpeg",
                "https://mmbiz.qpic.cn/xxx2/0?wx_fmt=jpeg"
            ]
        }
    ],
    "plans": [
        {
            "name": "家常俯拍·满桌温馨",
            "coreVisual": "俯视角度拍摄4-6道家常菜铺满白色桌面，暖色自然光",
            "case": {
                "imageUrl": "https://mmbiz.qpic.cn/xxx/0?wx_fmt=jpeg",
                "url": "https://mp.weixin.qq.com/s/xxx",
                "title": "在家待客，简单四道家常菜",
                "author": "小李食代",
                "reads": "10.0w"
            },
            "prompt": "2.35:1横版比例（900x383像素）。参考封面：https://... 。俯视角度拍摄白色大理石桌面上摆放4-5道精致家常菜..."
        }
    ]
}
```

---

## 字段说明

### 顶层字段

| 字段 | 类型 | 说明 | 数据来源 |
|------|------|------|----------|
| `keyword` | string | 用户输入的主题关键词 | 用户输入 |
| `analysisCount` | number | 实际分析的封面图数量 | 过滤后统计 |
| `styles` | array | 风格类型分类列表 | 分析归类 |
| `plans` | array | 3个设计方案 | 分析总结 |

### styles 数组元素

| 字段 | 类型 | 说明 |
|------|------|------|
| `name` | string | 风格类型名称（可含emoji） |
| `count` | number | 该风格出现次数 |
| `coreVisual` | string | 核心视觉描述 |
| `features` | string | 关键特征描述 |
| `covers` | string[] | 代表性封面图URL（最多5张） |

### plans 数组元素

| 字段 | 类型 | 说明 |
|------|------|------|
| `name` | string | 方案风格名称 |
| `coreVisual` | string | 核心视觉描述 |
| `case.imageUrl` | string | 案例封面图URL（imageUrl 字段原始值） |
| `case.url` | string | 案例文章链接（url 字段） |
| `case.title` | string | 案例文章标题 |
| `case.author` | string | 案例作者名（author 字段） |
| `case.reads` | string | 案例阅读数（格式化后，如"10.0w"） |
| `prompt` | string | 生图提示词（含2.35:1比例说明和参考封面URL） |

---

## 图片过滤规则

- 空白图片（纯色块、无内容）：排除，不放入 covers 数组
- 小尺寸图片（宽或高 <10px）：排除
- 每个风格类型最多5张代表性封面图

---

## 样式规范

| 元素 | 样式规则 |
|------|----------|
| 封面图容器比例 | 2.35:1 (180x77px 风格展示 / 300x128px 案例参考) |
| 封面图适配 | object-fit: cover, object-position: center |
| 防盗链 | 模板已内置 `<meta name="referrer" content="no-referrer">` |

---

## 输出文件命名

生成HTML报告时，文件名格式：
```
爆款封面分析报告_{关键词}.html
```

保存路径：当前工作目录（使用相对路径 ./）
