#!/usr/bin/env python3
"""
X(Twitter)作品评论分析脚本
调用 Redfox API 获取X(Twitter)推文评论数据，同步生成 HTML 报告
用法: python3 tweet_comment_search.py "<tweetId>" [--output-dir ~/Downloads/QoderReports]
"""

import sys
import os
import re
import json
import argparse
import urllib.request
import urllib.error
from datetime import datetime

TWEET_COMMENTS_API = "https://redfox.hk/story/api/x/tweetComments"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_PATH = os.path.join(SCRIPT_DIR, "..", "assets", "report_template.html")


def get_api_key() -> str:
    val = os.environ.get("REDFOX_API_KEY", "")
    if not val:
        print("[error] 未找到环境变量 REDFOX_API_KEY，请确认已设置 API Key", file=sys.stderr)
        print("[hint] 获取 API Key: https://redfox.hk/settings/api-keys?source=github", file=sys.stderr)
        print("[hint] 配置: export REDFOX_API_KEY=ak_xxxx...", file=sys.stderr)
        sys.exit(1)
    return val


def extract_tweet_id(input_str: str) -> str:
    """从用户输入中提取推文ID（支持直接ID或完整链接）"""
    input_str = input_str.strip()
    match = re.search(r"(?:x\.com|twitter\.com)/\w+/status/(\d+)", input_str)
    if match:
        return match.group(1)
    if input_str.isdigit():
        return input_str
    return input_str


def api_request(url: str, payload: dict, api_key: str) -> dict:
    """通用 API 请求函数（POST JSON）"""
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "X-API-Key": api_key,
            "User-Agent": "QoderWork/1.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"[error] HTTP {e.code}: {body}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"[error] 网络请求失败: {e.reason}", file=sys.stderr)
        sys.exit(1)
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        print(f"[error] 数据解析异常: {e}", file=sys.stderr)
        sys.exit(1)

    code = result.get("code")
    if code != 2000:
        print(f"[error] API 返回错误: code={code}, msg={result.get('msg', '未知')}", file=sys.stderr)
        sys.exit(1)

    return result.get("data") or {}


def _safe_int(val, default=0):
    try:
        return int(val)
    except (TypeError, ValueError):
        return default


def _safe_str(val, default=""):
    if val is None:
        return default
    return str(val)


def format_comment(raw: dict) -> dict:
    """将 API 返回的评论格式化为统一结构"""
    author = raw.get("author") or {}
    user_name = (author.get("displayName") or "").strip()
    username = (author.get("username") or "").strip()
    user_id = _safe_str(author.get("userId"))
    avatar = author.get("avatar") or ""
    verified = bool(author.get("verified") or False)
    followers = _safe_int(author.get("followers"))

    content = raw.get("content") or raw.get("text") or ""
    if isinstance(content, dict):
        content = content.get("message", "") or content.get("content", "")

    like_count = _safe_int(raw.get("likeCount") or raw.get("likes"))
    retweet_count = _safe_int(raw.get("retweetCount") or raw.get("retweets"))
    reply_count = _safe_int(raw.get("replyCount") or raw.get("replies"))
    quote_count = _safe_int(raw.get("quoteCount") or raw.get("quotes"))
    bookmark_count = _safe_int(raw.get("bookmarkCount") or raw.get("bookmarks"))
    view_count = _safe_str(raw.get("viewCount") or raw.get("views"), "0")

    tweet_id = _safe_str(raw.get("tweetId"))

    create_time = raw.get("createdAt") or raw.get("createTime") or ""
    if isinstance(create_time, (int, float)) and create_time > 1000000000:
        try:
            create_time = datetime.fromtimestamp(int(create_time)).strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            create_time = str(create_time)

    return {
        "user_name": user_name,
        "username": username,
        "user_id": user_id,
        "avatar": avatar,
        "verified": verified,
        "followers": followers,
        "content": str(content).strip(),
        "like_count": like_count,
        "retweet_count": retweet_count,
        "reply_count": reply_count,
        "quote_count": quote_count,
        "bookmark_count": bookmark_count,
        "view_count": view_count,
        "tweet_id": tweet_id,
        "create_time": str(create_time),
    }


def parse_work_detail(data: dict) -> dict:
    """解析推文详情（顶层 data，不含 threadReplies）"""
    author = data.get("author") or {}

    create_time = data.get("createdAt") or ""
    if isinstance(create_time, (int, float)) and create_time > 1000000000:
        try:
            create_time = datetime.fromtimestamp(int(create_time)).strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            create_time = str(create_time)

    return {
        "tweet_id": _safe_str(data.get("tweetId")),
        "content": (data.get("content") or "").strip(),
        "text": (data.get("text") or "").strip(),
        "created_at": str(create_time),
        "like_count": _safe_int(data.get("likeCount") or data.get("likes")),
        "retweet_count": _safe_int(data.get("retweetCount") or data.get("retweets")),
        "reply_count": _safe_int(data.get("replyCount") or data.get("replies")),
        "quote_count": _safe_int(data.get("quoteCount") or data.get("quotes")),
        "bookmark_count": _safe_int(data.get("bookmarkCount") or data.get("bookmarks")),
        "view_count": _safe_str(data.get("viewCount") or data.get("views"), "0"),
        "language": data.get("language") or "",
        "author_name": (author.get("displayName") or "").strip(),
        "author_username": (author.get("username") or "").strip(),
        "author_uid": _safe_str(author.get("userId")),
        "author_avatar": author.get("avatar") or "",
        "author_verified": bool(author.get("verified") or False),
        "author_followers": _safe_int(author.get("followers")),
        "medias": data.get("medias") or [],
        "cursor": data.get("cursor") or "",
    }


def fetch_tweet_data(tweet_id: str, api_key: str) -> tuple:
    """调用推文评论API，返回 (work_detail, comments_list, total_reply_count)"""
    data = api_request(TWEET_COMMENTS_API, {"tweetId": tweet_id, "source": "X(Twitter)作品评论分析-GitHub"}, api_key)

    work_detail = parse_work_detail(data)

    raw_replies = data.get("threadReplies") or []
    if not isinstance(raw_replies, list):
        raw_replies = []

    all_comments = [format_comment(c) for c in raw_replies]

    total_reply_count = work_detail.get("reply_count", 0)

    return work_detail, all_comments, total_reply_count


def escape_html(text: str) -> str:
    """HTML 实体转义"""
    return (
        (text or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def fmt_num(n) -> str:
    """格式化数字：>= 10000 使用 x.xw 格式"""
    n = int(n) if n else 0
    if n >= 10000:
        return f"{n / 10000:.1f}w"
    return str(n)


def build_comment_rows(comments: list) -> str:
    """根据评论列表生成 HTML 表格行"""
    rows = []
    for c in comments:
        name = escape_html(c.get("user_name", ""))
        username = escape_html(c.get("username", ""))
        content = escape_html(c.get("content", ""))
        likes = c.get("like_count", 0) or 0
        retweets = c.get("retweet_count", 0) or 0
        replies = c.get("reply_count", 0) or 0
        create_time = c.get("create_time", "") or ""
        try:
            dt = datetime.strptime(str(create_time)[:19], "%Y-%m-%d %H:%M:%S")
            time_str = dt.strftime("%m-%d %H:%M")
        except (ValueError, TypeError):
            time_str = str(create_time)[5:16] if len(str(create_time)) >= 16 else str(create_time)
        tweet_id = escape_html(c.get("tweet_id", ""))
        verified = c.get("verified", False)

        user_url = f"https://x.com/{username}" if username else "#"
        tweet_url = f"https://x.com/{username}/status/{tweet_id}" if username and tweet_id else "#"
        verified_badge = '<span class="verified-badge" title="已认证">&#x2713;</span>' if verified else ""

        row = (
            f'<tr>'
            f'<td>'
            f'<div class="user-cell">'
            f'<a href="{user_url}" target="_blank" class="user-name">{name}{verified_badge}</a>'
            f'<span class="user-handle">@{username}</span>'
            f'</div>'
            f'</td>'
            f'<td class="content-cell">'
            f'<a href="{tweet_url}" target="_blank" class="comment-link">{content}</a>'
            f'</td>'
            f'<td class="num-cell">{fmt_num(likes)}</td>'
            f'<td class="num-cell">{fmt_num(retweets)}</td>'
            f'<td class="num-cell">{fmt_num(replies)}</td>'
            f'<td class="time-cell">{time_str}</td>'
            f'</tr>'
        )
        rows.append(row)
    return "\n".join(rows)


def generate_html_report(tweet_id: str, comments: list, work_detail: dict = None, output_dir: str = None) -> str:
    """读取 HTML 模板，填充评论数据，生成报告文件"""
    template_path = os.path.normpath(TEMPLATE_PATH)
    if not os.path.exists(template_path):
        print(f"[warn] 模板文件不存在: {template_path}，跳过 HTML 生成", file=sys.stderr)
        return ""

    with open(template_path, "r", encoding="utf-8") as f:
        html = f.read()

    total = len(comments)
    now = datetime.now()
    total_likes = sum(c.get("like_count", 0) or 0 for c in comments)

    wd = work_detail or {}
    author_username = wd.get("author_username") or ""
    tweet_url = f"https://x.com/{author_username}/status/{tweet_id}" if author_username else ""
    replacements = {
        "{{TWEET_ID}}": escape_html(tweet_id),
        "{{TWEET_URL}}": tweet_url,
        "{{DATE}}": now.strftime("%Y-%m-%d"),
        "{{TOTAL_COMMENTS}}": str(total),
        "{{COMMENT_ROWS}}": build_comment_rows(comments),
        "{{TIMESTAMP}}": now.strftime("%Y-%m-%d %H:%M:%S"),
        "{{TOTAL_LIKES}}": str(total_likes),
        "{{CONTENT}}": escape_html(wd.get("content") or ""),
        "{{AUTHOR_NAME}}": escape_html(wd.get("author_name") or ""),
        "{{AUTHOR_USERNAME}}": escape_html(wd.get("author_username") or ""),
        "{{AUTHOR_UID}}": escape_html(wd.get("author_uid") or ""),
        "{{AUTHOR_AVATAR}}": wd.get("author_avatar") or "",
        "{{AUTHOR_VERIFIED}}": "true" if wd.get("author_verified") else "false",
        "{{AUTHOR_FOLLOWERS}}": fmt_num(wd.get("author_followers") or 0),
        "{{CREATED_AT}}": escape_html(wd.get("created_at") or ""),
        "{{LIKE_COUNT}}": fmt_num(wd.get("like_count") or 0),
        "{{RETWEET_COUNT}}": fmt_num(wd.get("retweet_count") or 0),
        "{{REPLY_COUNT}}": fmt_num(wd.get("reply_count") or 0),
        "{{QUOTE_COUNT}}": fmt_num(wd.get("quote_count") or 0),
        "{{BOOKMARK_COUNT}}": fmt_num(wd.get("bookmark_count") or 0),
        "{{VIEW_COUNT}}": fmt_num(wd.get("view_count") or 0),
    }

    for key, val in replacements.items():
        html = html.replace(key, val)

    if output_dir:
        out_dir = os.path.expanduser(output_dir)
    else:
        out_dir = os.path.expanduser("~/Downloads/QoderReports")
    os.makedirs(out_dir, exist_ok=True)

    filename = f"X作品评论分析_{tweet_id}.html"
    file_path = os.path.join(out_dir, filename)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"[html] HTML 报告已生成: {file_path}", file=sys.stderr)
    return file_path


def main():
    parser = argparse.ArgumentParser(description="X(Twitter)作品评论查询")
    parser.add_argument("tweet_id", help="推文ID 或推文链接")
    parser.add_argument("--no-html", dest="no_html", action="store_true", help="跳过 HTML 报告生成")
    parser.add_argument("--output-dir", dest="output_dir", type=str, default=None, help="HTML 输出目录（默认 ~/Downloads/QoderReports）")

    args = parser.parse_args()

    tweet_id = extract_tweet_id(args.tweet_id)
    if not tweet_id:
        print("[error] 推文ID不能为空", file=sys.stderr)
        sys.exit(1)

    api_key = get_api_key()
    work_detail, comments, total_reply_count = fetch_tweet_data(tweet_id, api_key)

    total = len(comments)

    output = {
        "work_detail": work_detail,
        "total_count": total_reply_count,
        "total_fetched": total,
        "has_next": False,
        "comments": comments,
    }

    if not args.no_html:
        html_path = generate_html_report(
            tweet_id=tweet_id,
            comments=comments,
            work_detail=work_detail,
            output_dir=args.output_dir,
        )
        output["html_path"] = html_path

    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()