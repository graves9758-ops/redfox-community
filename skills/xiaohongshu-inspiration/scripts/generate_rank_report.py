#!/usr/bin/env python3
"""
小红书榜单 HTML 报告生成脚本
用法：
    python generate_rank_report.py --data result.json --output report.html
    python generate_rank_report.py --data result.json  # 自动命名输出文件
"""
import argparse
import json
import sys
import html as html_utils
from datetime import datetime
from pathlib import Path


# ─────────────────────────────────────────────────────────
# 赛道识别：基于账号名 + 主页链接，识别更精准的细分赛道
# ─────────────────────────────────────────────────────────

# 细分赛道识别规则（按优先级排序）
CATEGORY_INFER_RULES = [
    # 游戏类（最高优先级）
    {"keywords": ["王者荣耀", "第五人格", "崩坏", "蛋仔", "原神", "鸣潮", "阴阳师", "明日方舟", "光遇", "恋与深空"], "category": "游戏"},
    {"keywords": ["吃鸡", "和平精英", "PUBG", "英雄联盟", "LOL", "无畏契约", "Valorant", "CSGO", "DOTA"], "category": "游戏"},
    {"keywords": ["迷你世界", "我的世界", "MC", "Minecraft"], "category": "游戏"},
    {"keywords": ["超自然行动组"], "category": "游戏"},

    # 品牌/官方类
    {"keywords": ["official", "工作室"], "category": "官方账号"},
    {"keywords": ["爱奇艺", "优酷", "腾讯视频", "芒果TV", "Bilibili", "B站"], "category": "视频平台"},
    {"keywords": ["微博", "新浪", "凤凰网", "澎湃", "界面新闻"], "category": "新闻媒体"},
    {"keywords": ["茶百道", "喜茶", "奈雪", "一点点", "蜜雪冰城", "霸王茶姬"], "category": "奶茶饮品"},
    {"keywords": ["德施曼", "凯迪仕", "飞利浦智能锁"], "category": "智能家居"},
    {"keywords": ["天猫", "京东", "淘宝", "拼多多"], "category": "电商平台"},

    # 明星/娱乐类
    {"keywords": ["赵露思", "白鹿", "虞书欣", "张凌赫", "田曦薇", "万妮达", "李维嘉"], "category": "明星"},
    {"keywords": ["煎饼果仔"], "category": "短剧"},
    {"keywords": ["小胡同学", "神仙藤井树"], "category": "美妆博主"},
    {"keywords": ["papi酱"], "category": "搞笑博主"},

    # 美食类细分
    {"keywords": ["刘雨鑫", "茄猫", "小镇上的猪精", "阿晨吃饱了"], "category": "美食博主"},
    {"keywords": ["美食", "吃货"], "category": "美食博主"},
    {"keywords": ["烘焙", "蛋糕", "面包", "甜品"], "category": "烘焙甜点"},
    {"keywords": ["探店", "奶茶", "咖啡"], "category": "探店美食"},

    # 旅行/户外类
    {"keywords": ["程前朋友圈"], "category": "商业观察"},
    {"keywords": ["柯子又胖了", "旅行", "旅游", "自驾", "露营"], "category": "旅行博主"},
    {"keywords": ["Linksphotograph", "行缘", "旅行摄影"], "category": "旅行摄影"},

    # 宠物类
    {"keywords": ["扣肉有脾气", "宠物", "猫", "狗", "萌宠", "铲屎"], "category": "宠物博主"},

    # 时尚/穿搭类
    {"keywords": ["穿搭", "OOTD", "衣橱"], "category": "穿搭博主"},
    {"keywords": ["康康和爷爷"], "category": "时尚博主"},
    {"keywords": ["白昼小熊"], "category": "潮流博主"},

    # 健身/运动类
    {"keywords": ["帕梅拉", "欧阳春晓"], "category": "健身博主"},
    {"keywords": ["健身", "瑜伽", "减脂", "增肌", "运动"], "category": "健身运动"},

    # 学习/知识类
    {"keywords": ["周小闹", "Prof.Alan"], "category": "知识博主"},
    {"keywords": ["教育", "学习", "干货", "职场"], "category": "知识教育"},

    # 科技/测评类
    {"keywords": ["小狮日记", "数码", "手机", "电脑", "测评", "评测", "搞机", "极客", "科技"], "category": "科技数码"},
    {"keywords": ["AI", "人工智能", "ChatGPT", "GPT"], "category": "AI科技"},

    # 亲子/母婴类
    {"keywords": ["一只静猪"], "category": "亲子博主"},
    {"keywords": ["母婴", "育儿", "宝宝", "辣妈", "萌娃"], "category": "母婴育儿"},

    # 家居/装修类
    {"keywords": ["家居", "装修", "软装", "设计", "收纳"], "category": "家居博主"},

    # 情感/心理类
    {"keywords": ["星座", "情感", "恋爱", "心理", "塔罗", "MBTI"], "category": "情感博主"},

    # 日常生活/Vlog
    {"keywords": ["日记", "vlog", "plog", "日常", "记录", "生活"], "category": "日常Vlog"},

    # 科学/探索类
    {"keywords": ["亿点点不一样", "科普", "科学", "探索", "实验"], "category": "科学探索"},
]

# 兜底关键词
FALLBACK_KEYWORDS = {
    "新闻媒体": ["吃瓜", "资讯", "热点", "日报"],
    "影视娱乐": ["影视", "娱乐", "综艺", "剧集", "电影", "演员"],
    "休闲爱好": ["爱好", "手工", "DIY", "绘画", "乐器"],
    "科学探索": ["天文", "地理", "宇宙", "太空"],
}


def infer_category(account_name: str, profile_url: str = "") -> str:
    """
    根据账号名和主页链接推断赛道分类。
    优先级：精确账号匹配 > 分类规则 > 兜底
    """
    combined = (account_name + " " + profile_url).lower()

    # 1. 精确账号名匹配（最高优先级）
    exact_account_map = {
        "王者荣耀": "游戏",
        "第五人格": "游戏",
        "崩坏：星穹铁道": "游戏",
        "网易蛋仔派对": "游戏",
        "超自然行动组": "游戏",
        "恋与深空": "游戏",
        "茶百道ChaPanda": "奶茶饮品",
        "德施曼": "智能家居",
        "爱奇艺": "视频平台",
        "亿点点不一样": "科学探索",
        "朱铁雄": "短剧",
        "一只静猪": "亲子博主",
        "扣肉有脾气": "宠物博主",
        "王冰汝": "新闻媒体",
        "神仙藤井树": "美妆博主",
        "小胡同学呀": "美妆博主",
        "康康和爷爷": "时尚博主",
        "帕梅拉Pamela Reif": "健身博主",
        "煎饼果仔（张问初）": "短剧",
        "Prof.Alan Macfarlane": "知识博主",
        "周小闹": "知识博主",
        "刘雨鑫JASON": "美食博主",
        "茄猫的罐头": "美食博主",
        "程前朋友圈": "商业观察",
        "Linksphotograph": "旅行摄影",
        "李蠕蠕": "搞笑博主",
        "吃瓜吗喽": "新闻媒体",
    }
    for exact_name, cat in exact_account_map.items():
        if exact_name.lower() in combined:
            return cat

    # 2. 规则遍历匹配
    for rule in CATEGORY_INFER_RULES:
        for kw in rule["keywords"]:
            if kw.lower() in combined:
                return rule["category"]

    # 3. 兜底关键词
    for category, keywords in FALLBACK_KEYWORDS.items():
        for kw in keywords:
            if kw.lower() in combined:
                return category

    return "日常Vlog"


def parse_num(val) -> int:
    """解析数字字符串，如 '24.64w' -> 246400, '6919' -> 6919"""
    if val is None or val == "-":
        return 0
    s = str(val).replace("w", "").replace("W", "").replace("+", "")
    try:
        if "." in s:
            return int(float(s) * 10000)
        return int(float(s))
    except (ValueError, TypeError):
        return 0


def format_interaction(num: int) -> str:
    if num >= 100_000:
        return f"{num // 10_000}w+"
    elif num >= 10_000:
        return f"{num / 10_000:.1f}w+"
    return str(num)


def format_followers(num: int) -> str:
    if num >= 100_000_000:
        return f"{num / 100_000_000:.1f}亿"
    elif num >= 10_000:
        return f"{num / 10_000:.1f}万"
    return str(num)


PERIOD_UPDATE_RULES = {
    "day": "每日 19:00 更新",
    "week": "每周一 15:00 更新",
    "month": "每月 2号 9:00 更新",
}
PERIOD_LABELS = {"day": "日榜", "week": "周榜", "month": "月榜"}

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>小红书{period_label}榜单 · {date}</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Helvetica Neue", Arial, sans-serif;
    background: linear-gradient(135deg, #fff1f2 0%, #fff7f0 100%);
    min-height: 100vh;
    padding: 24px;
    color: #1a1a1a;
  }}
  .header {{
    text-align: center;
    margin-bottom: 32px;
  }}
  .header .logo {{
    font-size: 48px;
    margin-bottom: 8px;
  }}
  .header h1 {{
    font-size: 28px;
    font-weight: 700;
    color: #ff2442;
    margin-bottom: 6px;
  }}
  .header .meta {{
    font-size: 13px;
    color: #888;
  }}
  .notice {{
    background: #fff8e1;
    border-left: 4px solid #ffb300;
    border-radius: 8px;
    padding: 12px 16px;
    margin-bottom: 24px;
    font-size: 13px;
    color: #5d4037;
  }}
  .stats-bar {{
    display: flex;
    gap: 16px;
    margin-bottom: 24px;
    flex-wrap: wrap;
  }}
  .stat-card {{
    flex: 1;
    min-width: 120px;
    background: #fff;
    border-radius: 12px;
    padding: 16px;
    text-align: center;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  }}
  .stat-card .num {{
    font-size: 28px;
    font-weight: 700;
    color: #ff2442;
  }}
  .stat-card .label {{
    font-size: 12px;
    color: #888;
    margin-top: 4px;
  }}
  .table-wrap {{
    background: #fff;
    border-radius: 16px;
    overflow: hidden;
    box-shadow: 0 4px 20px rgba(0,0,0,0.08);
    margin-bottom: 24px;
  }}
  table {{
    width: 100%;
    border-collapse: collapse;
  }}
  thead th {{
    background: linear-gradient(135deg, #ff2442, #ff6b7a);
    color: #fff;
    padding: 14px 16px;
    text-align: left;
    font-size: 13px;
    font-weight: 600;
    white-space: nowrap;
  }}
  tbody tr {{
    border-bottom: 1px solid #f5f5f5;
    transition: background 0.15s;
  }}
  tbody tr:hover {{ background: #fff5f5; }}
  tbody tr:last-child {{ border-bottom: none; }}
  td {{
    padding: 12px 16px;
    font-size: 14px;
    vertical-align: middle;
  }}
  .rank-badge {{
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 32px;
    height: 32px;
    border-radius: 50%;
    font-weight: 700;
    font-size: 14px;
  }}
  .rank-1 {{ background: #FFD700; color: #5d4000; }}
  .rank-2 {{ background: #C0C0C0; color: #3d3d3d; }}
  .rank-3 {{ background: #CD7F32; color: #fff; }}
  .rank-other {{ background: #f0f0f0; color: #555; }}
  .account-name {{
    font-weight: 600;
    color: #333;
    text-decoration: none;
    cursor: pointer;
    transition: color 0.15s;
  }}
  .account-name:hover {{
    color: #ff2442;
    text-decoration: underline;
  }}
  .score-bar-wrap {{
    display: flex;
    align-items: center;
    gap: 8px;
  }}
  .score-bar {{
    flex: 1;
    height: 8px;
    background: #f0f0f0;
    border-radius: 4px;
    overflow: hidden;
    max-width: 100px;
  }}
  .score-fill {{
    height: 100%;
    background: linear-gradient(90deg, #ff2442, #ff8fa3);
    border-radius: 4px;
  }}
  .score-num {{
    font-weight: 600;
    color: #ff2442;
    min-width: 36px;
  }}
  .interaction {{
    font-weight: 600;
    color: #ff6b35;
  }}
  .tag {{
    display: inline-block;
    background: #fff0f3;
    color: #ff2442;
    border-radius: 12px;
    padding: 2px 8px;
    font-size: 11px;
    font-weight: 500;
  }}
  .export-bar {{
    text-align: center;
    margin-bottom: 16px;
    display: flex;
    gap: 12px;
    justify-content: center;
    flex-wrap: wrap;
  }}
  .btn {{
    padding: 10px 24px;
    border-radius: 24px;
    border: none;
    cursor: pointer;
    font-size: 14px;
    font-weight: 600;
    transition: transform 0.1s, box-shadow 0.1s;
  }}
  .btn:hover {{ transform: translateY(-1px); box-shadow: 0 4px 12px rgba(0,0,0,0.15); }}
  .btn-primary {{ background: linear-gradient(135deg, #ff2442, #ff6b7a); color: #fff; }}
  .btn-secondary {{ background: #fff; color: #ff2442; border: 2px solid #ff2442; }}
  .footer {{
    text-align: center;
    font-size: 12px;
    color: #bbb;
    padding: 16px;
  }}
  @media print {{
    .export-bar {{ display: none; }}
    body {{ background: #fff; padding: 0; }}
    .table-wrap {{ box-shadow: none; }}
  }}
</style>
</head>
<body>

<div class="header">
  <div class="logo">📊</div>
  <h1>小红书{period_label} · {category_label}</h1>
  <div class="meta">数据日期：{date} &nbsp;|&nbsp; 共 {total} 个账号上榜</div>
</div>

<div class="notice">
  💡 <strong>榜单说明</strong>：{update_rule}。<br>
  📐 <strong>排名算法</strong>：综合评分根据达人在小红书的 <strong>总粉丝数</strong>、周期内的 <strong>粉丝增量</strong>、<strong>点赞增量</strong>、<strong>收藏增量</strong>、<strong>分享增量</strong> 以及 <strong>评论增量</strong> 加权计算所得（满分100）。

</div>

<div class="stats-bar">
  <div class="stat-card"><div class="num">{total}</div><div class="label">上榜账号</div></div>
  <div class="stat-card"><div class="num">{top_interaction}</div><div class="label">最高互动</div></div>
  <div class="stat-card"><div class="num">{total_notes}</div><div class="label">总新增笔记</div></div>
</div>

<div class="export-bar">
  <button class="btn btn-primary" onclick="window.print()">🖨️ 打印 / 导出 PDF</button>
  <button class="btn btn-secondary" id="downloadImgBtn" onclick="downloadAsImage()">📷 保存为图片</button>
</div>

<script src="https://cdn.jsdelivr.net/npm/html2canvas@1.4.1/dist/html2canvas.min.js"></script>
<script>
async function downloadAsImage() {{
  const btn = document.getElementById('downloadImgBtn');
  btn.textContent = '⏳ 生成中...';
  btn.disabled = true;
  try {{
    const element = document.querySelector('.table-wrap');
    const canvas = await html2canvas(element, {{
      scale: 2,
      backgroundColor: '#ffffff',
      useCORS: true
    }});
    const link = document.createElement('a');
    link.download = '小红书榜单_{date}.png';
    link.href = canvas.toDataURL('image/png');
    link.click();
    btn.textContent = '✅ 下载成功';
    setTimeout(() => {{
      btn.textContent = '📷 保存为图片';
      btn.disabled = false;
    }}, 2000);
  }} catch (e) {{
    alert('生成图片失败，请尝试使用浏览器截图');
    btn.textContent = '📷 保存为图片';
    btn.disabled = false;
  }}
}}
</script>

<div class="table-wrap">
<table>
  <thead>
    <tr>
      <th>排名</th>
      <th>账号名</th>
      <th>综合评分</th>
      <th>总粉丝数</th>
      <th>新增笔记数</th>
      <th>新增粉丝</th>
      <th>新增点赞</th>
      <th>新增评论</th>
      <th>新增收藏</th>
      <th>新增分享</th>
    </tr>
  </thead>
  <tbody>
{rows}
  </tbody>
</table>
</div>



</body>
</html>"""

ROW_TEMPLATE = """    <tr>
      <td><span class="rank-badge {rank_class}">{rank}</span></td>
      <td><a href="{profile_url}" target="_blank" class="account-name" title="点击查看小红书主页">{account_name}</a></td>
      <td><span class="score">{score}</span></td>
      <td>{followers}</td>
      <td>{new_notes}</td>
      <td class="interaction">{new_fans}</td>
      <td class="interaction">{new_likes}</td>
      <td class="interaction">{new_comments}</td>
      <td class="interaction">{new_collects}</td>
      <td class="interaction">{new_shares}</td>
    </tr>"""


def _fmt(val, fmt_fn=None) -> str:
    """通用格式化：None / 空字符串 显示 '-'。
    若值为字符串（新接口直接返回如 '254.06w'），直接返回；
    若值为整数，调用 fmt_fn 格式化。
    """
    if val is None or val == "" or val == "-":
        return "-"
    # 字符串直接返回（新接口已格式化好）
    if isinstance(val, str):
        return val if val.strip() else "-"
    # 数字
    try:
        n = int(val)
        if n == 0:
            return "-"
        return fmt_fn(n) if fmt_fn else str(n)
    except (TypeError, ValueError):
        return str(val) if val else "-"


def generate_html(data: dict, output_path: str):
    items = data.get("list", [])
    total = data.get("total", len(items))
    fetch_time = data.get("fetchTime", data.get("date", "未知"))
    period = data.get("period", "day")
    date_str = data.get("date", "")
    category = data.get("category", "")

    period_label = PERIOD_LABELS.get(period, "日榜")
    category_label = category + "类" if category else "全品类"
    update_rule = PERIOD_UPDATE_RULES.get(period, PERIOD_UPDATE_RULES["day"])

    # 手动计算最高互动：点赞 + 评论 + 收藏 + 分享
    top_interaction_raw = 0
    for i in items:
        interaction = (
            parse_num(i.get("newLikes")) +
            parse_num(i.get("newComments")) +
            parse_num(i.get("newCollects")) +
            parse_num(i.get("newShares"))
        )
        if interaction > top_interaction_raw:
            top_interaction_raw = interaction
    top_interaction = format_interaction(top_interaction_raw)
    total_notes = sum(i.get("newNoteCount", 0) or 0 for i in items)

    rows = []
    for item in items:
        rank = item.get("rank", 0)
        if rank == 1:
            rank_class = "rank-1"
        elif rank == 2:
            rank_class = "rank-2"
        elif rank == 3:
            rank_class = "rank-3"
        else:
            rank_class = "rank-other"

        rows.append(ROW_TEMPLATE.format(
            rank=rank,
            rank_class=rank_class,
            account_name=html_utils.escape(item.get("accountName", "")),
            profile_url=html_utils.escape(item.get("accountLink") or item.get("profileUrl", "#")),
            category=html_utils.escape(infer_category(item.get("accountName", ""), item.get("accountLink") or item.get("profileUrl", ""))),
            followers=_fmt(item.get("followers"), format_followers),
            new_notes=item.get("newNoteCount", "-") or "-",
            new_fans=_fmt(item.get("newFans"), format_interaction),
            new_likes=_fmt(item.get("newLikes"), format_interaction),
            new_comments=_fmt(item.get("newComments"), format_interaction),
            new_collects=_fmt(item.get("newCollects"), format_interaction),
            new_shares=_fmt(item.get("newShares"), format_interaction),
            score=int(item.get("comprehensiveScore")) if item.get("comprehensiveScore") else "-",
        ))

    html = HTML_TEMPLATE.format(
        period_label=period_label,
        category_label=category_label,
        update_rule=update_rule,
        date=date_str,
        fetch_time=fetch_time,
        total=total,
        top_interaction=top_interaction,
        total_notes=total_notes,
        rows="\n".join(rows),
        gen_time=datetime.now().strftime("%Y-%m-%d %H:%M"),
    )

    Path(output_path).write_text(html, encoding="utf-8")
    print(f"[INFO] HTML 报告已生成：{output_path}")


def main():
    parser = argparse.ArgumentParser(description="生成小红书榜单 HTML 报告")
    parser.add_argument("--data", required=True, help="fetch_rank.py 输出的 JSON 文件路径")
    parser.add_argument("--output", default="", help="HTML 输出路径，不填则自动命名")
    args = parser.parse_args()

    data_path = Path(args.data)
    if not data_path.exists():
        print(f"[ERROR] 找不到数据文件：{args.data}", file=sys.stderr)
        sys.exit(1)

    with open(data_path, encoding="utf-8") as f:
        data = json.load(f)

    if not args.output:
        period = data.get("period", "day")
        period_label = {"day": "日榜", "week": "周榜", "month": "月榜"}.get(period, "榜单")
        category = data.get("category", "") or "全品类"
        # 格式：关键词_日期_时间戳，如：小红书美妆日榜_20260505_143022
        date_str = data.get("date", "").replace("-", "")
        timestamp = datetime.now().strftime("%H%M%S")
        keyword = f"小红书{category}{period_label}"
        output_path = str(data_path.parent / f"{keyword}_{date_str}_{timestamp}.html")
    else:
        output_path = args.output

    generate_html(data, output_path)


if __name__ == "__main__":
    main()
