#!/usr/bin/env python3
"""
快手作品搜索脚本（广域库）
调用 Redfox API 搜索快手作品数据
用法: python3 search_ks_work.py "<关键词>" [--sort 最多点赞] [--page 1]
"""

import sys
import os
import json
import argparse
import time as _time
import urllib.request
import urllib.error
from datetime import datetime

# Windows 终端默认 GBK 编码无法输出部分 Unicode 字符（如 \xa0），强制切换为 UTF-8
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr.encoding and sys.stderr.encoding.lower() != "utf-8":
    sys.stderr.reconfigure(encoding="utf-8")

API_URL = "https://redfox.hk/story/api/ksAllData/searchWork"

# 排序方式枚举
SORT_MAP = {
    "综合":     "综合排序",
    "最新":     "最新发布",
    "最多点赞": "最多点赞",
    "最多收藏": "最多收藏",
}


def get_api_key() -> str:
    val = os.environ.get("REDFOX_API_KEY", "")
    if not val:
        print("[error] 未找到环境变量 REDFOX_API_KEY，请确认已设置 API Key", file=sys.stderr)
        sys.exit(1)
    return val


def format_duration(ms):
    """将毫秒时长转换为 mm:ss 格式"""
    if not ms or ms <= 0:
        return ""
    total_seconds = ms // 1000
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    return f"{minutes:02d}:{seconds:02d}"


def format_articles(articles: list) -> list:
    items = []
    for art in articles:
        # publishTime 可能是日期字符串（如 "2025-07-03 17:03:25"）或 Unix 时间戳
        rt_raw = art.get("publishTime") or art.get("releaseTime") or ""
        publish_time = ""
        publish_date = ""
        if rt_raw:
            rt_str = str(rt_raw).strip()
            # 尝试按日期字符串解析
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
                try:
                    dt = datetime.strptime(rt_str, fmt)
                    publish_time = dt.strftime("%Y-%m-%d %H:%M:%S")
                    publish_date = dt.strftime("%Y-%m-%d")
                    break
                except ValueError:
                    continue
            # 若日期字符串解析失败，尝试按 Unix 时间戳解析
            if not publish_time:
                try:
                    ts = int(rt_raw)
                    if ts > 0:
                        publish_time = _time.strftime("%Y-%m-%d %H:%M:%S", _time.localtime(ts))
                        publish_date = _time.strftime("%Y-%m-%d", _time.localtime(ts))
                except (ValueError, TypeError):
                    pass

        # 标题中可能存在 | 字符，需转义避免破坏 Markdown 表格列分隔
        raw_title = (art.get("caption") or art.get("workTitle") or art.get("title") or "").strip() or "-"
        safe_title = raw_title.replace("|", "\\|")

        # 从 photoId 构建快手作品链接
        photo_id = art.get("photoId") or ""
        work_url = f"https://www.kuaishou.com/short-video/{photo_id}" if photo_id else ""

        items.append({
            "title":         safe_title,
            "author":        (art.get("nickname") or art.get("authorName") or "").strip() or "-",
            "author_url":    "",
            "author_fans":   art.get("authorFans") or 0,
            "play_count":    art.get("viewCount") or art.get("playCount") or 0,
            "like_count":    art.get("likeCount") or 0,
            "comment_count": art.get("commentCount") or 0,
            "collect_count": art.get("collectCount") or 0,
            "share_count":   art.get("shareCount") or 0,
            "forward_count": art.get("forwardCount") or 0,
            "work_url":      work_url,
            "cover_url":     art.get("coverUrl") or "",
            "video_url":     art.get("videoUrl") or "",
            "head_url":      art.get("headUrl") or "",
            "duration":      format_duration(art.get("duration", 0)),
            "duration_ms":   art.get("duration") or 0,
            "work_type":     art.get("workType") or "",
            "publish_time":  publish_time,
            "publish_date":  publish_date,
            "work_id":       photo_id or art.get("workId") or "",
        })
    return items


def search(keyword: str, sort: str, page: int = 1) -> dict:
    api_key = get_api_key()

    payload = json.dumps({
        "keyword": keyword,
        "sort":    sort,
        "page":    page,
        "size":    20,
    }).encode("utf-8")

    req = urllib.request.Request(
        API_URL,
        data=payload,
        headers={
            "Content-Type":    "application/json",
            "REDFOX_API_KEY":  api_key,
            "User-Agent":      "QoderWork/1.0",
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
        print(f"[error] 接口返回错误: code={code}, msg={result.get('msg', '未知')}", file=sys.stderr)
        sys.exit(1)

    data = result.get("data") or {}
    articles_list = data.get("list") or []
    articles_count = len(articles_list)

    # 翻页逻辑：当前页返回条数等于 size → 可能有下一页；不足 size → 已是最后一页
    page_size = data.get("size", 20)
    has_next = articles_count >= page_size

    return {
        "articles":   format_articles(articles_list),
        "sort_label": SORT_MAP.get(sort, sort),
        "page":       page,
        "has_next":   has_next,
        "total":      articles_count,
    }


def main():
    parser = argparse.ArgumentParser(description="快手作品搜索（广域库）")
    parser.add_argument("keyword", help="搜索关键词")
    parser.add_argument(
        "--sort", dest="sort", default="最多点赞",
        choices=["综合", "最新", "最多点赞", "最多收藏"],
        help="排序方式（默认：最多点赞）",
    )
    parser.add_argument(
        "--page", dest="page", type=int, default=1,
        help="页码，从 1 开始（默认：1）",
    )
    args = parser.parse_args()

    keyword = args.keyword.strip()
    if not keyword:
        print("[error] 关键词不能为空", file=sys.stderr)
        sys.exit(1)
    if args.page < 1:
        print("[error] 页码必须为正整数", file=sys.stderr)
        sys.exit(1)

    result = search(keyword, args.sort, args.page)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
