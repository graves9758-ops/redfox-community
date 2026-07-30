#!/usr/bin/env python3
"""
YouTube视频评论分析脚本
调用 Redfox API 获取YouTube视频评论数据，默认不生成 HTML 报告，结果仅输出到 stdout，不落盘缓存
用法: python3 youtube_comment_search.py "<videoId>" [--sort-by top|newest] [--language-code zh-CN] [--country-code US] [--continuation-token TOKEN] [--html] [--output-dir ~/Downloads/QoderReports]
"""

import sys
import os
import re
import json
import argparse
import urllib.request
import urllib.error
from datetime import datetime

# 修复 Windows 控制台 UTF-8 输出
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

VIDEO_COMMENTS_API = "https://redfox.hk/story/api/youtube/videoComments"

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


def extract_video_id(input_str: str) -> str:
    """从用户输入中提取视频ID（支持直接ID或完整链接）"""
    input_str = input_str.strip()
    # youtube.com/watch?v=VIDEO_ID
    match = re.search(r"(?:youtube\.com)/watch\?v=([a-zA-Z0-9_-]+)", input_str)
    if match:
        return match.group(1)
    # youtu.be/VIDEO_ID
    match = re.search(r"youtu\.be/([a-zA-Z0-9_-]+)", input_str)
    if match:
        return match.group(1)
    # youtube.com/shorts/VIDEO_ID
    match = re.search(r"youtube\.com/shorts/([a-zA-Z0-9_-]+)", input_str)
    if match:
        return match.group(1)
    # 纯视频ID（字母数字下划线连字符组合，11位左右）
    if re.match(r"^[a-zA-Z0-9_-]{8,15}$", input_str):
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
            "REDFOX_API_KEY": api_key,
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
    display_name = (author.get("displayName") or "").strip()
    channel_id = _safe_str(author.get("channelId"))
    channel_url = author.get("channelUrl") or ""
    avatar_url = author.get("avatarUrl") or ""
    is_creator = bool(author.get("isCreator") or False)
    is_verified = bool(author.get("isVerified") or False)

    content = raw.get("content") or ""
    if isinstance(content, dict):
        content = content.get("message", "") or content.get("content", "")

    like_count = _safe_int(raw.get("likeCount") or raw.get("likes"))
    reply_count = _safe_int(raw.get("replyCount") or raw.get("replies"))
    comment_id = _safe_str(raw.get("commentId"))
    published_time = _safe_str(raw.get("publishedTime") or raw.get("published_time"))

    return {
        "display_name": display_name,
        "channel_id": channel_id,
        "channel_url": channel_url,
        "avatar_url": avatar_url,
        "is_creator": is_creator,
        "is_verified": is_verified,
        "comment_id": comment_id,
        "content": str(content).strip(),
        "like_count": like_count,
        "reply_count": reply_count,
        "published_time": str(published_time),
    }


def fetch_video_comments(video_id: str, api_key: str, sort_by: str = "top",
                         language_code: str = "zh-CN", country_code: str = "US",
                         continuation_token: str = None) -> tuple:
    """调用YouTube评论API，返回 (comments_list, next_token)"""
    payload = {
        "videoId": video_id,
        "sortBy": sort_by,
        "languageCode": language_code,
        "countryCode": country_code,
        "source": "YouTube视频评论分析-GitHub",
    }
    if continuation_token:
        payload["continuationToken"] = continuation_token

    data = api_request(VIDEO_COMMENTS_API, payload, api_key)

    raw_comments = data.get("comments") or []
    if not isinstance(raw_comments, list):
        raw_comments = []

    all_comments = [format_comment(c) for c in raw_comments]
    next_token = data.get("continuationToken") or ""

    return all_comments, next_token


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
        name = escape_html(c.get("display_name", ""))
        channel_url = escape_html(c.get("channel_url", ""))
        content = escape_html(c.get("content", ""))
        likes = c.get("like_count", 0) or 0
        replies = c.get("reply_count", 0) or 0
        published_time = escape_html(c.get("published_time", ""))
        is_creator = c.get("is_creator", False)
        is_verified = c.get("is_verified", False)

        verified_badge = '<span class="verified-badge" title="已认证">&#x2713;</span>' if is_verified else ""
        creator_badge = '<span class="creator-badge" title="创作者">&#x1F3AC;</span>' if is_creator else ""

        row = (
            f'<tr>'
            f'<td>'
            f'<div class="user-cell">'
            f'<a href="{channel_url}" target="_blank" class="user-name">{name}{verified_badge}{creator_badge}</a>'
            f'</div>'
            f'</td>'
            f'<td class="content-cell">{content}</td>'
            f'<td class="num-cell">{fmt_num(likes)}</td>'
            f'<td class="num-cell">{fmt_num(replies)}</td>'
            f'<td class="time-cell">{published_time}</td>'
            f'</tr>'
        )
        rows.append(row)
    return "\n".join(rows)


def generate_html_report(video_id: str, comments: list, output_dir: str = None) -> str:
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

    video_url = f"https://www.youtube.com/watch?v={video_id}"
    replacements = {
        "{{VIDEO_ID}}": escape_html(video_id),
        "{{VIDEO_URL}}": video_url,
        "{{DATE}}": now.strftime("%Y-%m-%d"),
        "{{TOTAL_COMMENTS}}": str(total),
        "{{COMMENT_ROWS}}": build_comment_rows(comments),
        "{{TIMESTAMP}}": now.strftime("%Y-%m-%d %H:%M:%S"),
        "{{TOTAL_LIKES}}": str(total_likes),
    }

    for key, val in replacements.items():
        html = html.replace(key, val)

    if output_dir:
        out_dir = os.path.expanduser(output_dir)
    else:
        out_dir = os.path.expanduser("~/Downloads/QoderReports")
    os.makedirs(out_dir, exist_ok=True)

    filename = f"YouTube视频评论分析_{video_id}.html"
    file_path = os.path.join(out_dir, filename)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"[html] HTML 报告已生成: {file_path}", file=sys.stderr)
    return file_path


def main():
    parser = argparse.ArgumentParser(description="YouTube视频评论查询")
    parser.add_argument("video_id", help="视频ID 或视频链接")
    parser.add_argument("--sort-by", dest="sort_by", type=str, default="top",
                        help="排序方式：top（热门）或 newest（最新），默认 top")
    parser.add_argument("--language-code", dest="language_code", type=str, default="zh-CN",
                        help="语言偏好，默认 zh-CN")
    parser.add_argument("--country-code", dest="country_code", type=str, default="US",
                        help="地区代码，默认 US")
    parser.add_argument("--continuation-token", dest="continuation_token", type=str, default=None,
                        help="翻页令牌，从上一次返回结果中的 continuation_token 字段获取")
    parser.add_argument("--html", dest="html", action="store_true",
                        help="同步生成 HTML 报告（默认不生成）")
    parser.add_argument("--output-dir", dest="output_dir", type=str, default=None,
                        help="HTML 输出目录（默认 ~/Downloads/QoderReports）")

    args = parser.parse_args()

    video_id = extract_video_id(args.video_id)
    if not video_id:
        print("[error] 视频ID不能为空", file=sys.stderr)
        sys.exit(1)

    api_key = get_api_key()
    comments, next_token = fetch_video_comments(
        video_id, api_key,
        sort_by=args.sort_by,
        language_code=args.language_code,
        country_code=args.country_code,
        continuation_token=args.continuation_token,
    )

    total = len(comments)

    output = {
        "video_id": video_id,
        "sort_by": args.sort_by,
        "language_code": args.language_code,
        "country_code": args.country_code,
        "total_fetched": total,
        "has_next": bool(next_token),
        "continuation_token": next_token,
        "comments": comments,
    }

    if args.html:
        html_path = generate_html_report(
            video_id=video_id,
            comments=comments,
            output_dir=args.output_dir,
        )
        output["html_path"] = html_path

    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
