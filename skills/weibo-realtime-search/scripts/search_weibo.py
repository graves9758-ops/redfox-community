#!/usr/bin/env python3
"""
微博作品搜索脚本
调用 Redfox API 搜索微博作品数据
用法: python3 search_weibo.py "<关键词>" [--search-type 1] [--page 1] [--ext-param "2"]
"""

import sys
import os
import json
import argparse
import urllib.request
import urllib.error
import re

API_URL = "https://redfox.hk/story/api/weibo/ability/searchWork"

# searchType 枚举
SEARCH_TYPE_MAP = {
    "1":  "综合排序",
    "60": "热门排序",
    "61": "实时排序",
}

# extParam 枚举
EXT_PARAM_MAP = {
    "":  "不过滤",
    "0": "普通用户",
    "2": "个人认证",
    "3": "机构认证",
}


def get_api_key() -> str:
    val = os.environ.get("REDFOX_API_KEY", "")
    if not val:
        print("[error] 未找到环境变量 REDFOX_API_KEY，请确认已设置 API Key", file=sys.stderr)
        sys.exit(1)
    return val


def sanitize_title(raw: str) -> str:
    """清理标题中的特殊字符，避免破坏 Markdown 链接格式 [title](url)"""
    s = raw.replace("\n", " ").replace("\r", " ")
    s = re.sub(r"\s+", " ", s).strip()
    s = s.replace("|", "\\|")
    s = s.replace("[", "【").replace("]", "】")
    return s or "-"


def format_articles(articles: list) -> list:
    items = []
    for art in articles:
        raw_title = (art.get("text") or art.get("caption") or art.get("workTitle") or art.get("title") or art.get("description") or "").strip() or "-"
        safe_title = sanitize_title(raw_title)

        author_name = (art.get("authorName") or art.get("nickname") or "").strip() or "-"
        # 提取博主 uid，生成主页链接
        uid = art.get("uid") or art.get("authorId") or art.get("userId") or ""
        if uid:
            author = f"[{author_name}](https://weibo.com/u/{uid})"
        else:
            author = author_name

        items.append({
            "title":          safe_title,
            "author":         author,
            "like_count":     art.get("likeCount") or art.get("likeNum") or art.get("thumbCount") or 0,
            "comment_count":  art.get("commentCount") or art.get("commentNum") or art.get("replyCount") or 0,
            "share_count":    art.get("forwardNum") or art.get("shareCount") or art.get("shareNum") or 0,
            "work_url":       art.get("workUrl") or art.get("url") or "",
            "publish_time":   art.get("publishTime") or art.get("releaseTime") or "",
            "follower_count": art.get("fansNum") or art.get("followerCount") or 0,
        })
    return items


def search(keyword: str, search_type: str, page: int = 1, ext_param: str = "") -> dict:
    api_key = get_api_key()
    payload = json.dumps({
        "searchType": search_type,
        "page":       str(page),
        "keyword":    keyword,
        "extParam":   ext_param,
        "source":     "微博作品搜索-GitHub",
    }).encode("utf-8")

    req = urllib.request.Request(
        API_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "X-API-Key":    api_key,
            "User-Agent":   "QoderWork/1.0",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
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
    if isinstance(data, list):
        articles_list = data
    elif isinstance(data, dict):
        articles_list = data.get("workList") or data.get("list") or []
    else:
        articles_list = []

    articles_count = len(articles_list)
    has_next = articles_count >= 9

    return {
        "articles":          format_articles(articles_list),
        "search_type_label": SEARCH_TYPE_MAP.get(search_type, search_type),
        "ext_param_label":   EXT_PARAM_MAP.get(ext_param, "不过滤"),
        "page":              page,
        "has_next":          has_next,
    }


def main():
    parser = argparse.ArgumentParser(description="微博作品搜索")
    parser.add_argument("keyword", help="搜索关键词")
    parser.add_argument(
        "--search-type", dest="search_type", default="1",
        choices=["1", "60", "61"],
        help="搜索类别：1-综合 60-热门 61-实时博文（默认1）",
    )
    parser.add_argument(
        "--page", dest="page", type=int, default=1,
        help="页码，从1开始（默认1）",
    )
    parser.add_argument(
        "--ext-param", dest="ext_param", default="",
        help="认证类别：0-普通用户 2-个人认证 3-机构认证（默认不传）",
    )
    args = parser.parse_args()

    keyword = args.keyword.strip()
    if not keyword:
        print("[error] 关键词不能为空", file=sys.stderr)
        sys.exit(1)
    if args.page < 1:
        print("[error] 页码必须为正整数", file=sys.stderr)
        sys.exit(1)

    result = search(keyword, args.search_type, args.page, args.ext_param)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
