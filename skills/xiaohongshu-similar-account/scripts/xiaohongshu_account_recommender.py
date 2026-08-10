#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小红书相似账号推荐脚本
调用红狐相似账号 API（POST https://redfox.hk/story/api/xhsUser/querySimilarAccounts），
支持按账号 ID 或「赛道 + 粉丝数 + 账号等级」查询，输出同阶对标/高阶标杆分组并生成 HTML 报告。

用法：
    python xiaohongshu_account_recommender.py --red_id "27493135897"
    python xiaohongshu_account_recommender.py --track "美味佳肴" --min_fans 0 --max_fans 3000 --level "素人"

依赖：仅 Python 标准库（urllib）。API Key 通过环境变量 REDFOX_API_KEY 注入。
"""
import argparse
import html
import json
import os
import ssl
import sys
import urllib.request

API_URL = "https://redfox.hk/story/api/xhsUser/querySimilarAccounts"

# 赛道映射（用户口语 -> 红狐赛道值），未命中时原样透传
TRACK_MAP = {
    "做饭": "美味佳肴", "美食": "美味佳肴", "厨艺": "美味佳肴",
    "穿搭": "潮流穿搭", "时尚": "潮流穿搭",
    "美妆": "美妆护肤", "护肤": "美妆护肤",
    "健身": "健身运动", "运动": "健身运动",
    "育儿": "亲子育儿", "母婴": "亲子育儿",
    "家居": "家居生活", "装修": "家居生活",
    "旅行": "旅行摄影", "旅游": "旅行摄影",
    "职场": "职场干货", "工作": "职场干货",
    "学习": "学习成长", "知识": "学习成长",
}

# 账号等级映射，未命中时原样透传
LEVEL_MAP = {
    "小白": "素人", "新手": "素人", "素人": "素人",
    "腰部": "腰部达人", "达人": "腰部达人",
    "头部": "头部达人", "大V": "头部达人",
}


def parse_fans(raw):
    """解析粉丝数：单值 -> (0, 值)；区间 'a-b' -> (a, b)；None -> ('', '')"""
    if raw is None:
        return "", ""
    s = str(raw).strip()
    if not s:
        return "", ""
    if "-" in s:
        a, b = s.split("-", 1)
        return a.strip(), b.strip()
    return "0", s


def call_api(payload):
    key = os.environ.get("REDFOX_API_KEY", "")
    if not key:
        sys.exit("错误：未设置 REDFOX_API_KEY 环境变量，请先 export REDFOX_API_KEY=\"ak_xxx\"")
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(API_URL, data=data, method="POST", headers={
        "Content-Type": "application/json",
        "X-API-KEY": key,
    })
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=60, context=ctx) as resp:
        return json.loads(resp.read().decode("utf-8"))


def render_html(groups):
    """生成 HTML 报告并返回文件路径"""
    cards = []
    for title, rows in groups:
        if not rows:
            continue
        items = "".join(
            f'<tr><td><a href="{html.escape(r.get("userUrl") or r.get("link") or "#")}">{html.escape(str(r.get("userName") or r.get("nickname") or "未知账号"))}</a></td>'
            f'<td>{html.escape(str(r.get("fans") or r.get("fansCount") or "?"))}</td>'
            f'<td>{html.escape(str(r.get("interact") or r.get("interactCount") or r.get("totalInteract") or "?"))}</td>'
            f'<td>{html.escape(str(r.get("reason") or r.get("recommendReason") or ""))}</td></tr>'
            for r in rows
        )
        cards.append(
            f"<h2>{html.escape(title)}（{len(rows)}个）</h2>"
            f'<table border="1" cellspacing="0" cellpadding="6" style="border-collapse:collapse;width:100%">'
            f"<tr><th>账号名</th><th>粉丝数</th><th>近30天互动数</th><th>推荐理由</th></tr>{items}</table>"
        )
    report = f"""<!DOCTYPE html>
<html lang="zh"><head><meta charset="utf-8"><title>小红书对标账号推荐</title></head>
<body style="font-family:system-ui,sans-serif;max-width:900px;margin:24px auto">
<h1>小红书对标账号推荐</h1>
<p style="color:#888">数据获取时间为入库快照，和实时数据存在差别。</p>
{''.join(cards)}
</body></html>"""
    path = os.path.abspath("similar_accounts_report.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(report)
    return path


def main():
    ap = argparse.ArgumentParser(description="小红书相似账号推荐（红狐 API）")
    ap.add_argument("--red_id", help="小红书账号 ID（输入方式 A）")
    ap.add_argument("--track", help="赛道（输入方式 B），自动做口语映射")
    ap.add_argument("--min_fans", help="最小粉丝数（输入方式 B）")
    ap.add_argument("--max_fans", help="最大粉丝数（输入方式 B）")
    ap.add_argument("--level", help="账号等级（输入方式 B，如 小白/素人/腰部/头部）")
    args = ap.parse_args()

    if not args.red_id and not args.track:
        sys.exit("错误：必须提供 --red_id 或 --track 之一")

    if args.red_id:
        payload = {"redId": args.red_id}
    else:
        track = TRACK_MAP.get(args.track, args.track)
        level = LEVEL_MAP.get(args.level, args.level) if args.level else args.level
        min_fans, max_fans = parse_fans(args.min_fans), parse_fans(args.max_fans)
        payload = {
            "track": track,
            "minFans": min_fans[0] if min_fans[0] else ("0" if args.min_fans else ""),
            "maxFans": max_fans[1] if max_fans[1] else ("3000" if args.max_fans else ""),
            "level": level or "",
        }

    result = call_api(payload)

    # API 层错误（如 code != 0）：直接展示 msg 退出，不生成报告
    if isinstance(result, dict) and result.get("code") not in (0, None):
        print(f"API 返回错误 code={result.get('code')}: {result.get('msg', '未知错误')}")
        sys.exit(1)
    print(json.dumps(result, ensure_ascii=False, indent=1)[:2000])

    # 兼容多种返回结构：data.similarAccounts / data.accounts / data.peer / data.target ...
    data = result.get("data") or result
    groups = []
    for key, title in (("peerAccounts", "可直接抄的同阶对标"), ("targetAccounts", "可追赶的高阶标杆"),
                       ("similarAccounts", "对标账号"), ("peer", "同阶对标"), ("target", "高阶标杆")):
        rows = data.get(key) if isinstance(data, dict) else None
        if isinstance(rows, list) and rows:
            groups.append((title, rows))
    if not groups and isinstance(data, list) and data:
        groups.append(("对标账号", data))

    html_path = render_html(groups)
    print(f"\nHTML 报告已生成: {html_path}")


if __name__ == "__main__":
    main()
