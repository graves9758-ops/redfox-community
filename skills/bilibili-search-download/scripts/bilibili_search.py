#!/usr/bin/env python3
"""
B站作品关键词搜索脚本
调用红狐 API 搜索哔哩哔哩作品，结果仅输出到 stdout，不落盘缓存
用法: python3 bilibili_search.py --keyword "羽绒服" [--page 1] [--page-size 10] [--order like] [--date-range 7d]
"""

import sys
import os
import json
import argparse
import urllib.request
import urllib.error

# 修复 Windows 控制台 UTF-8 输出
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

WORK_SEARCH_API = "https://redfox.hk/story/api/bili/data/workSearch"


def get_api_key() -> str:
    val = os.environ.get("REDFOX_API_KEY", "")
    if not val:
        print("[error] 未找到环境变量 REDFOX_API_KEY，请确认已设置 API Key", file=sys.stderr)
        print("[hint] 获取 API Key: https://redfox.hk/settings/api-keys?source=github", file=sys.stderr)
        print("[hint] 配置: export REDFOX_API_KEY=ak_xxxx...", file=sys.stderr)
        sys.exit(1)
    return val


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


def format_work(raw: dict) -> dict:
    """将 API 返回的作品格式化为统一结构"""
    return {
        "bv_id": _safe_str(raw.get("bvId")),
        "title": _safe_str(raw.get("title")),
        "description": _safe_str(raw.get("description")),
        "author": _safe_str(raw.get("author")),
        "author_id": _safe_str(raw.get("authorId")),
        "duration": _safe_int(raw.get("duration")),
        "pic_url": _safe_str(raw.get("picUrl")),
        "created": _safe_str(raw.get("created")),
        "first_type": _safe_str(raw.get("firstType")),
        "second_type": _safe_str(raw.get("secondType")),
        "play_count": _safe_int(raw.get("playCount")),
        "like_count": _safe_int(raw.get("likeCount")),
        "favorite_count": _safe_int(raw.get("favoriteCount")),
        "comment_count": _safe_int(raw.get("commentCount")),
        "share_count": _safe_int(raw.get("shareCount")),
        "coin_count": _safe_int(raw.get("coinCount")),
        "video_review": _safe_int(raw.get("videoReview")),
        "interaction_quantity": _safe_int(raw.get("interactionQuantity")),
        "tag_names": raw.get("tagNames") if isinstance(raw.get("tagNames"), list) else [],
        "video_url": f"https://www.bilibili.com/video/{_safe_str(raw.get('bvId'))}",
    }


def search_works(keyword: str, api_key: str, page: int = 1,
                 page_size: int = 10, order: str = "like", date_range: str = "7d") -> dict:
    """调用 B站作品搜索 API，返回搜索结果"""
    payload = {
        "keyword": keyword,
        "page": str(page),
        "pageSize": page_size,
        "order": order,
        "dateRange": date_range,
        "source": "B站搜索批量下载-GitHub",
    }

    data = api_request(WORK_SEARCH_API, payload, api_key)

    raw_works = data.get("workList") or []
    if not isinstance(raw_works, list):
        raw_works = []

    works = [format_work(w) for w in raw_works]

    return {
        "keyword": keyword,
        "page": _safe_int(data.get("page"), page),
        "page_size": _safe_int(data.get("pageSize"), page_size),
        "total": _safe_int(data.get("total"), 0),
        "works": works,
    }


def main():
    parser = argparse.ArgumentParser(description="B站作品关键词搜索")
    parser.add_argument("--keyword", dest="keyword", type=str, required=True,
                        help="搜索关键词（必填）")
    parser.add_argument("--page", dest="page", type=int, default=1,
                        help="页码，默认 1")
    parser.add_argument("--page-size", dest="page_size", type=int, default=10,
                        help="每页条数，默认 10，最大 50")
    parser.add_argument("--order", dest="order", type=str, default="play",
                        choices=["time", "play", "like", "comment", "favorite"],
                        help="排序方式：time=最新发布/play=综合排序/like=最多点赞/comment=评论数/favorite=收藏数，默认 play（综合排序）")
    parser.add_argument("--date-range", dest="date_range", type=str, default="7d",
                        choices=["7d", "30d", "90d", "all"],
                        help="发布时间范围：7d=最近7天/30d=最近30天/90d=最近90天/all=不限，默认 7d")

    args = parser.parse_args()

    if not args.keyword.strip():
        print("[error] 搜索关键词不能为空", file=sys.stderr)
        sys.exit(1)

    api_key = get_api_key()

    result = search_works(
        keyword=args.keyword.strip(),
        api_key=api_key,
        page=args.page,
        page_size=min(args.page_size, 50),
        order=args.order,
        date_range=args.date_range,
    )

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
