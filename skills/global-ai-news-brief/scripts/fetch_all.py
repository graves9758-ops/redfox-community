#!/usr/bin/env python3
"""
全球AI新闻简报 — 数据采集脚本
并行请求 11 大平台搜索接口，统一标准化后输出 JSON。

用法:
    python3 fetch_all.py "关键词" [--output /tmp/result.json] [--platforms douyin,xhs,gzh]

依赖: 仅 Python 标准库 (urllib + concurrent.futures)，无需 pip 安装
环境变量: REDFOX_API_KEY (红狐 API 密钥)
"""

import argparse
import concurrent.futures
import json
import os
import sys
import time
import urllib.error
import urllib.request

HOST = "https://redfox.hk"
TIMEOUT = 30

# ---------------------------------------------------------------- 平台定义
# name: 平台名; path: 接口路径; body: 请求体模板; list_key: 响应中列表的定位路径
PLATFORMS = {
    "douyin": {
        "name": "抖音",
        "path": "/story/api/dy/data/searchWork",
        "body": {"keyword": "{kw}", "pageNum": 1, "pageSize": 20},
        "list_key": ["data", "list"],
    },
    "xiaohongshu": {
        "name": "小红书",
        "path": "/story/api/xhsUser/searchArticle",
        "body": {"keyword": "{kw}", "offset": 0, "sortType": "0"},
        "list_key": ["data", "list"],
    },
    "wechat_gzh": {
        "name": "公众号",
        "path": "/story/api/gzh/data/searchArticle",
        "body": {"keyword": "{kw}", "offset": 0, "sortType": "0"},
        "list_key": ["data", "list"],
    },
    "bilibili": {
        "name": "B站",
        "path": "/story/api/bili/data/workSearch",
        "body": {"keyword": "{kw}", "page": "1", "pageSize": 20, "order": "time"},
        "list_key": ["data", "workList"],
    },
    "kuaishou": {
        "name": "快手",
        "path": "/story/api/ksAllData/searchWork",
        "body": {"keyword": "{kw}", "page": 1, "size": 20, "sort": "综合"},
        "list_key": ["data", "list"],
    },
    "shipinhao": {
        "name": "视频号",
        "path": "/story/api/sphAllData/searchWork",
        "body": {"keyword": "{kw}", "page": 1, "size": 20, "sort": "综合"},
        "list_key": ["data", "list"],
    },
    "toutiao": {
        "name": "今日头条",
        "path": "/story/api/toutiao/searchWork",
        "body": {"keyword": "{kw}", "offset": "0"},
        "list_key": ["data"],  # data 直接是数组
    },
    "tiktok": {
        "name": "TikTok",
        "path": "/story/api/tiktok/ability/searchVideo",
        "body": {"keyword": "{kw}", "offset": "0", "count": "20", "sortType": "0", "publishTime": "0"},
        "list_key": ["data"],  # data 直接是数组
    },
    "instagram": {
        "name": "Instagram",
        "path": "/story/api/ins/search",
        "body": {"keyword": "{kw}"},
        "list_key": ["data", "items"],
    },
    "x_twitter": {
        "name": "X(Twitter)",
        "path": "/story/api/x/search",
        "body": {"keyword": "{kw}", "searchType": "Top"},
        "list_key": ["data", "tweets"],
    },
    "youtube": {
        "name": "YouTube",
        "path": "/story/api/youtube/searchVideo",
        "body": {"searchQuery": "{kw}"},  # 注意参数名为 searchQuery
        "list_key": ["data", "videos"],
    },
}

# ---------------------------------------------------------------- 平台专属映射函数
# 每个函数输入原始条目 dict，输出标准化 dict


def norm_douyin(i):
    vt = str(i.get("videoType", ""))
    return {
        "title": i.get("content", ""),
        "content": i.get("content", ""),
        "author": i.get("authorName", ""),
        "url": i.get("opusUrl", ""),
        "publishTime": i.get("publishTime", ""),
        "likes": i.get("likeCount", 0) or 0,
        "comments": i.get("commentCount", 0) or 0,
        "shares": i.get("shareCount", 0) or 0,
        "views": None,
        "collects": i.get("collectCount", 0) or 0,
        "followers": None,
        "coverUrl": i.get("coverUrl", ""),
        "mediaType": "image" if vt == "68" else "video",
    }


def norm_xiaohongshu(i):
    return {
        "title": i.get("workTitle", ""),
        "content": i.get("workDesc", ""),
        "author": i.get("accountNickname", ""),
        "url": i.get("workUrl", ""),
        "publishTime": i.get("workPublishTime", ""),
        "likes": i.get("workLikedCount", 0) or 0,
        "comments": i.get("workCommentsCount", 0) or 0,
        "shares": i.get("workSharedCount", 0) or 0,
        "views": None,
        "collects": i.get("workCollectedCount", 0) or 0,
        "followers": None,
        "coverUrl": i.get("coverUrl", ""),
        "mediaType": "video" if "video" in str(i.get("workType", "")) else "image",
    }


def norm_wechat_gzh(i):
    return {
        "title": i.get("title", ""),
        "content": i.get("summary", ""),
        "author": i.get("author", ""),
        "url": i.get("workUrl", ""),
        "publishTime": i.get("publishTime", ""),
        "likes": i.get("likeCount", 0) or 0,
        "comments": i.get("commentCount", 0) or 0,
        "shares": i.get("shareCount", 0) or 0,
        "views": i.get("readCount", 0) or 0,
        "collects": i.get("collectCount", 0) or 0,
        "followers": None,
        "coverUrl": i.get("coverUrl", ""),
        "mediaType": "text",
    }


def norm_bilibili(i):
    bv = i.get("bvId", "")
    return {
        "title": i.get("title", ""),
        "content": i.get("description", ""),
        "author": i.get("author", ""),
        "url": f"https://www.bilibili.com/video/{bv}" if bv else "",
        "publishTime": i.get("created", ""),
        "likes": i.get("likeCount", 0) or 0,
        "comments": i.get("commentCount", 0) or 0,
        "shares": i.get("shareCount", 0) or 0,
        "views": i.get("playCount", 0) or 0,
        "collects": i.get("favoriteCount", 0) or 0,
        "followers": None,
        "coverUrl": i.get("picUrl", ""),
        "mediaType": "video",
    }


def norm_kuaishou(i):
    pid = i.get("photoId", "")
    return {
        "title": i.get("caption", ""),
        "content": i.get("caption", ""),
        "author": i.get("nickname", ""),
        "url": f"https://www.kuaishou.com/short-video/{pid}" if pid else "",
        "publishTime": i.get("publishTime", ""),
        "likes": i.get("likeCount", 0) or 0,
        "comments": i.get("commentCount", 0) or 0,
        "shares": i.get("shareCount", 0) or 0,
        "views": i.get("viewCount", 0) or 0,
        "collects": i.get("collectCount", 0) or 0,
        "followers": i.get("authorFans", 0) or 0,
        "coverUrl": i.get("coverUrl", ""),
        "mediaType": "video",
    }


def norm_shipinhao(i):
    return {
        "title": i.get("description", ""),
        "content": i.get("description", ""),
        "author": i.get("nickname", ""),
        "url": i.get("videoUrl", ""),
        "publishTime": i.get("publishTime", ""),
        "likes": i.get("likeCount", 0) or 0,
        "comments": i.get("commentCount", 0) or 0,
        "shares": i.get("forwardCount", 0) or 0,
        "views": None,
        "collects": i.get("favCount", 0) or 0,
        "followers": None,
        "coverUrl": i.get("coverUrl", "") or i.get("thumbUrl", ""),
        "mediaType": "video",
    }


def norm_toutiao(i):
    return {
        "title": i.get("title", ""),
        "content": "",
        "author": i.get("nickname", ""),
        "url": i.get("opusUrl", ""),
        "publishTime": _ts_to_str(i.get("publishTime")),
        "likes": None,
        "comments": i.get("commentNum", 0) or 0,
        "shares": None,
        "views": None,
        "collects": None,
        "followers": None,
        "coverUrl": "",
        "mediaType": "text",
    }


def norm_tiktok(i):
    author = i.get("authorData") or {}
    stats = i.get("statsData") or {}
    video = i.get("videoData") or {}
    return {
        "title": i.get("content", ""),
        "content": i.get("content", ""),
        "author": author.get("userName", ""),
        "url": i.get("shareLink", ""),
        "publishTime": _ts_to_str(i.get("publishTime")),
        "likes": stats.get("likeCount", 0) or 0,
        "comments": stats.get("commentTotal", 0) or 0,
        "shares": stats.get("shareTotal", 0) or 0,
        "views": stats.get("viewCount", 0) or 0,
        "collects": stats.get("favoriteCount", 0) or 0,
        "followers": author.get("fansCount", 0) or 0,
        "coverUrl": video.get("coverImage", ""),
        "mediaType": "video" if i.get("mediaType") == "video" else "image",
    }


def norm_instagram(i):
    code = i.get("code", "")
    user = i.get("user") or {}
    return {
        "title": i.get("captionText", ""),
        "content": i.get("captionText", ""),
        "author": user.get("username", "") or user.get("fullName", ""),
        "url": f"https://www.instagram.com/p/{code}/" if code else "",
        "publishTime": i.get("takenAtDate", "") or _ts_to_str(i.get("takenAt")),
        "likes": i.get("likeCount", 0) or 0,
        "comments": i.get("commentCount", 0) or 0,
        "shares": i.get("shareCount", 0) or 0,
        "views": i.get("playCount", 0) or 0,
        "collects": None,
        "followers": user.get("followerCount", 0) or 0,
        "coverUrl": i.get("imageUrl", "") or i.get("thumbnailUrl", ""),
        "mediaType": {"video": "video", "image": "image", "album": "image"}.get(i.get("mediaFormat", ""), "image"),
    }


def norm_x_twitter(i):
    user = i.get("user") or {}
    username = user.get("username", "") or i.get("username", "")
    tweet_id = i.get("tweetId", "")
    medias = i.get("medias") or []
    first_media = medias[0] if medias else {}
    media_type = first_media.get("type", "") if first_media else ""
    return {
        "title": i.get("text", ""),
        "content": i.get("text", ""),
        "author": user.get("displayName", "") or username,
        "url": f"https://x.com/{username}/status/{tweet_id}" if username and tweet_id else "",
        "publishTime": i.get("createdAt", ""),
        "likes": i.get("likeCount", 0) or 0,
        "comments": i.get("replyCount", 0) or 0,
        "shares": i.get("retweetCount", 0) or 0,
        "views": _to_int(i.get("viewCount")),
        "collects": i.get("bookmarkCount", 0) or 0,
        "followers": user.get("followers", 0) or 0,
        "coverUrl": first_media.get("coverUrl", ""),
        "mediaType": media_type or "text",
    }


def norm_youtube(i):
    vid = i.get("videoId", "")
    thumbs = i.get("thumbnails") or []
    return {
        "title": i.get("title", ""),
        "content": i.get("description", ""),
        "author": i.get("author", ""),
        "url": f"https://www.youtube.com/watch?v={vid}" if vid else "",
        "publishTime": i.get("publishedTime", ""),
        "likes": None,
        "comments": None,
        "shares": None,
        "views": i.get("viewCount", 0) or 0,
        "collects": None,
        "followers": None,
        "coverUrl": thumbs[0].get("url", "") if thumbs else "",
        "mediaType": "video",
    }


NORMALIZERS = {
    "douyin": norm_douyin,
    "xiaohongshu": norm_xiaohongshu,
    "wechat_gzh": norm_wechat_gzh,
    "bilibili": norm_bilibili,
    "kuaishou": norm_kuaishou,
    "shipinhao": norm_shipinhao,
    "toutiao": norm_toutiao,
    "tiktok": norm_tiktok,
    "instagram": norm_instagram,
    "x_twitter": norm_x_twitter,
    "youtube": norm_youtube,
}

# ---------------------------------------------------------------- 工具函数


def _ts_to_str(ts):
    """秒级时间戳转 'YYYY-MM-DD HH:MM:SS'，None/非法返回空串"""
    if not ts:
        return ""
    try:
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(ts)))
    except (ValueError, TypeError, OSError):
        return ""


def _to_int(v):
    try:
        return int(v) if v is not None else None
    except (ValueError, TypeError):
        return None


def _deep_get(obj, keys):
    """按路径取嵌套字段，任一环节缺失返回 None"""
    cur = obj
    for k in keys:
        if isinstance(cur, dict) and k in cur:
            cur = cur[k]
        else:
            return None
    return cur


# ---------------------------------------------------------------- 请求与解析


def fetch_platform(key, keyword, api_key):
    """请求单个平台，返回 (平台key, 结果dict)。失败时 result 含 error 字段。"""
    cfg = PLATFORMS[key]
    headers = {
        "Content-Type": "application/json",
        "REDFOX-API-KEY": api_key,
        "X-API-Key": api_key,
    }
    body_dict = {k: v.replace("{kw}", keyword) if isinstance(v, str) else v
                 for k, v in cfg["body"].items()}
    body_dict["source"] = "全球AI新闻简报-GitHub"
    body = json.dumps(body_dict).encode("utf-8")
    req = urllib.request.Request(f"{HOST}{cfg['path']}", data=body, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            raw = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")[:500]
        return key, {"platform": cfg["name"], "error": f"HTTP {e.code}: {detail}"}
    except urllib.error.URLError as e:
        return key, {"platform": cfg["name"], "error": f"网络错误: {e.reason}"}
    except Exception as e:  # noqa: BLE001 — 兜底保证单平台失败不影响整体
        return key, {"platform": cfg["name"], "error": f"解析错误: {e}"}

    if raw.get("code") != 2000:
        return key, {"platform": cfg["name"], "error": f"接口返回 code={raw.get('code')}, msg={raw.get('msg')}"}

    items = _deep_get(raw, cfg["list_key"])
    if items is None:
        items = []

    norm = NORMALIZERS[key]
    normalized = [norm(i) for i in items]
    total = _to_int(_deep_get(raw, ["data", "total"])) if key != "toutiao" and key != "tiktok" else None

    return key, {
        "platform": cfg["name"],
        "count": len(normalized),
        "total": total,
        "items": normalized,
    }


def main():
    parser = argparse.ArgumentParser(description="全球AI新闻简报 — 11 平台并行搜索")
    parser.add_argument("keyword", help="搜索关键词")
    parser.add_argument("-o", "--output", default="/tmp/news_intel_result.json", help="输出 JSON 路径")
    parser.add_argument("--platforms", default=None,
                        help="逗号分隔的平台子集，如 douyin,xhs。默认全部 11 平台")
    parser.add_argument("--pretty", action="store_true", help="格式化输出 JSON")
    args = parser.parse_args()

    api_key = os.environ.get("REDFOX_API_KEY", "").strip()
    if not api_key:
        print("错误: 环境变量 REDFOX_API_KEY 未设置", file=sys.stderr)
        print("请先执行: export REDFOX_API_KEY='你的密钥'", file=sys.stderr)
        sys.exit(1)

    if args.platforms:
        selected = [p.strip() for p in args.platforms.split(",") if p.strip()]
        unknown = [p for p in selected if p not in PLATFORMS]
        if unknown:
            print(f"错误: 未知平台 {unknown}，可选: {list(PLATFORMS)}", file=sys.stderr)
            sys.exit(1)
    else:
        selected = list(PLATFORMS)

    print(f"开始并行搜索 {len(selected)} 个平台，关键词: {args.keyword}", file=sys.stderr)
    results = {}
    errors = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(selected)) as pool:
        futures = {pool.submit(fetch_platform, k, args.keyword, api_key): k for k in selected}
        for fut in concurrent.futures.as_completed(futures):
            key, result = fut.result()
            if "error" in result:
                errors.append(result)
                print(f"  ✗ {result['platform']}: {result['error']}", file=sys.stderr)
            else:
                results[key] = result
                print(f"  ✓ {result['platform']}: {result['count']} 条", file=sys.stderr)

    total_items = sum(r["count"] for r in results.values())
    total_engagement = sum(
        (i.get("likes") or 0) + (i.get("comments") or 0) + (i.get("shares") or 0)
        for r in results.values() for i in r["items"]
    )

    output = {
        "keyword": args.keyword,
        "generatedAt": time.strftime("%Y-%m-%d %H:%M:%S"),
        "platformCount": len(results),
        "failedPlatforms": errors,
        "totalItems": total_items,
        "totalEngagement": total_engagement,
        "results": results,
    }

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2 if args.pretty else None)

    print(f"\n完成: 成功 {len(results)}/{len(selected)} 平台, 共 {total_items} 条, 总互动 {total_engagement}", file=sys.stderr)
    print(args.output)


if __name__ == "__main__":
    main()
