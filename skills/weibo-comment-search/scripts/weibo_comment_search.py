#!/usr/bin/env python3
"""
微博评论分析 - 根据博文链接查询评论，同步生成 HTML 报告
用法: python3 weibo_comment_search.py "<博文链接或opusId>" [--page 1] [--cursor 0] [--no-html] [--output-dir ~/Downloads/QoderReports]
"""

import json
import os
import re
import sys
import argparse
from datetime import datetime

import urllib.request
import urllib.error

API_BASE = "https://redfox.hk"
SOURCE = "微博评论分析-GitHub"

# 脚本所在目录，用于定位模板
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_PATH = os.path.join(SCRIPT_DIR, "..", "assets", "report_template.html")


def extract_opus_id(url_or_id: str) -> str:
    """从微博博文链接中提取 opusId"""
    # https://weibo.com/1784473157/R8X4f2lnq -> R8X4f2lnq
    m = re.search(r"weibo\.com/\d+/([A-Za-z0-9]+)", url_or_id)
    if m:
        return m.group(1)
    # 直接传 opusId
    if re.match(r"^[A-Za-z0-9]+$", url_or_id):
        return url_or_id
    return ""


def sanitize_content(raw: str) -> str:
    """清理评论内容，避免 Markdown 表格格式错乱"""
    if not raw:
        return "-"
    s = raw.replace("\n", " ").replace("\r", " ")
    s = re.sub(r"\s+", " ", s).strip()
    s = s.replace("|", "\\|")
    s = s.replace("[", "【").replace("]", "】")
    return s or "-"


def format_number(n) -> str:
    """格式化数字：<10000 原样，>=10000 显示 x.xw"""
    if n is None:
        return "0"
    n = int(n)
    if n >= 10000:
        return f"{n / 10000:.1f}w"
    return str(n)


def search(url: str, max_cursor: str = "0", max_id_type: str = "0", page: int = 1):
    """调用 API 查询评论"""
    api_key = os.environ.get("REDFOX_API_KEY")
    if not api_key:
        print("错误: 环境变量 REDFOX_API_KEY 未设置", file=sys.stderr)
        print("[hint] 获取 API Key: https://redfox.hk/settings/api-keys?source=github", file=sys.stderr)
        print("[hint] 配置: export REDFOX_API_KEY=ak_xxxx...", file=sys.stderr)
        sys.exit(1)

    opus_id = extract_opus_id(url)
    if not opus_id:
        print(f"错误: 无法从 '{url}' 中提取 opusId", file=sys.stderr)
        sys.exit(1)

    payload = json.dumps({
        "opusId": opus_id,
        "maxCursor": str(max_cursor),
        "maxIdType": str(max_id_type),
        "source": SOURCE,
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{API_BASE}/story/api/weibo/ability/commentList",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "X-API-Key": api_key,
            "User-Agent": "QoderWork/1.0",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"错误: HTTP {e.code}: {body}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"错误: 网络请求失败: {e.reason}", file=sys.stderr)
        sys.exit(1)
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        print(f"错误: 数据解析异常: {e}", file=sys.stderr)
        sys.exit(1)

    code = data.get("code")
    if code != 2000:
        print(f"错误: 接口返回错误: code={code}, msg={data.get('msg', '未知')}", file=sys.stderr)
        sys.exit(1)

    result = data.get("data") or {}

    # 解析响应
    if isinstance(result, dict):
        comments = result.get("comments", [])
        max_id = result.get("maxId", "0")
    else:
        comments = []
        max_id = "0"

    if not isinstance(comments, list):
        comments = []

    has_next = (max_id != "0" and max_id != max_cursor)

    formatted_comments = []
    for c in comments:
        if not isinstance(c, dict):
            continue
        nickname = c.get("nickname", "")
        uid = c.get("uid", "")
        user_url = f"https://weibo.com/{uid}" if uid else ""

        formatted_comments.append({
            "nickname": nickname,
            "uid": uid or "",
            "user_url": user_url,
            "content": sanitize_content(c.get("content", "")),
            "comment_like_num": int(c.get("commentLikeNum", 0)),
            "comment_like_num_fmt": format_number(c.get("commentLikeNum", 0)),
            "create_time": c.get("createTime", ""),
        })

    return {
        "opus_id": opus_id,
        "comments": formatted_comments,
        "max_cursor": max_id,
        "has_next": has_next,
        "page": page,
    }


# ──────────────────────────────────────────────
# HTML 报告生成
# ──────────────────────────────────────────────

def escape_html(text: str) -> str:
    """HTML 实体转义"""
    return (text or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def build_comment_rows(comments: list) -> str:
    """根据评论列表生成 HTML 表格行"""
    rows = []
    for idx, c in enumerate(comments, 1):
        name = escape_html(c.get("nickname", ""))
        url = c.get("user_url", "") or "#"
        content = escape_html(c.get("content", ""))
        like = c.get("comment_like_num_fmt", "0")
        time_str = c.get("create_time", "") or ""

        # 用户名超链接，无头像
        user_cell = f'<a href="{url}" target="_blank" class="user-name">{name}</a>' if url else f'<span class="user-name">{name}</span>'

        row = (
            f'<tr>'
            f'<td class="index-cell">{idx}</td>'
            f'<td class="user-cell">{user_cell}</td>'
            f'<td class="content-cell">{content}</td>'
            f'<td class="num-cell">{like}</td>'
            f'<td class="time-cell">{time_str}</td>'
            f'</tr>'
        )
        rows.append(row)
    return "\n".join(rows)


def generate_html_report(opus_id: str, page: int, comments: list, output_dir: str = None) -> str:
    """
    读取 HTML 模板，填充评论数据，生成报告文件。
    返回生成的 HTML 文件绝对路径。
    """
    template_path = os.path.normpath(TEMPLATE_PATH)
    if not os.path.exists(template_path):
        print(f"[warn] 模板文件不存在: {template_path}，跳过 HTML 生成", file=sys.stderr)
        return ""

    with open(template_path, "r", encoding="utf-8") as f:
        html = f.read()

    total = len(comments)
    now = datetime.now()

    # 计算基本统计
    total_likes = sum(c.get("comment_like_num", 0) or 0 for c in comments)

    # 占位符替换
    # 数据占位 — 脚本直接填充
    # 分析占位 — 保留 {{PLACEHOLDER}}，后续由 backfill_html.py 回填
    replacements = {
        "{{OPUS_ID}}": escape_html(opus_id),
        "{{DATE}}": now.strftime("%Y-%m-%d"),
        "{{TOTAL_COMMENTS}}": str(total),
        "{{COMMENT_ROWS}}": build_comment_rows(comments),
        "{{TIMESTAMP}}": now.strftime("%Y-%m-%d %H:%M:%S"),
        "{{TOTAL_LIKES}}": str(total_likes),
        "{{PAGE}}": str(page),
        # {{POSITIVE_RATIO}} / {{NEGATIVE_RATIO}} / {{DEMAND_RATIO}} / {{COMPETITOR_RATIO}}
        # {{SUMMARY_POSITIVE}} / {{SUMMARY_NEGATIVE}} / {{SUMMARY_DEMAND}} / {{SUMMARY_COMPETITOR}}
        # 以上分析占位符不在脚本中替换，保留原样，由 backfill_html.py 统一回填
    }

    for key, val in replacements.items():
        html = html.replace(key, val)

    # 确定输出目录
    if output_dir:
        out_dir = os.path.expanduser(output_dir)
    else:
        out_dir = os.path.expanduser("~/Downloads/QoderReports")
    os.makedirs(out_dir, exist_ok=True)

    filename = f"微博评论分析_{opus_id}_p{page}.html"
    file_path = os.path.join(out_dir, filename)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"[html] HTML 报告已生成: {file_path}", file=sys.stderr)
    return file_path


def main():
    parser = argparse.ArgumentParser(description="微博评论分析")
    parser.add_argument("url", help="微博博文链接或 opusId")
    parser.add_argument("--cursor", default="0", help="翻页游标 (默认 0)")
    parser.add_argument("--page", type=int, default=1, help="页码 (默认 1)")
    parser.add_argument(
        "--no-html", dest="no_html", action="store_true",
        help="跳过 HTML 报告生成",
    )
    parser.add_argument(
        "--output-dir", dest="output_dir", type=str, default=None,
        help="HTML 输出目录（默认 ~/Downloads/QoderReports）",
    )
    args = parser.parse_args()

    result = search(args.url, max_cursor=args.cursor, page=args.page)

    # HTML 报告生成
    if not args.no_html:
        html_path = generate_html_report(
            opus_id=result["opus_id"],
            page=result["page"],
            comments=result["comments"],
            output_dir=args.output_dir,
        )
        result["html_path"] = html_path

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
