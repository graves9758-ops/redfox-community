#!/usr/bin/env python3
"""
快手按账号获取作品列表脚本（广域库）
调用 Redfox API，通过快手账号平台展示 id（kwaiId）或主页链接 id（threeXId）精准匹配查询该账号的作品列表，
按发布时间倒序（Lindorm 数据源）。
用法:
  python3 search_ks_work.py --kwai-id xxx [--page 1] [--size 20]
  python3 search_ks_work.py --threex-id xxx [--page 1] [--size 20]
"""

import sys
import os
import json
import time as _time
import argparse
import urllib.request
import urllib.error
from datetime import datetime

API_URL = "https://redfox.hk/story/api/ksAllData/queryWorkList"

MAX_SIZE = 50  # 每页条数上限


def get_api_key() -> str:
    # 获取 REDFOX_API_KEY: 环境变量 -> shell 配置文件 -> 提示用户配置
    # 1. 从环境变量获取
    val = os.environ.get("REDFOX_API_KEY", "").strip()
    if val:
        return val

    # 2. 从 shell 配置文件读取
    home = os.path.expanduser("~")
    for cf in [".zshrc", ".bashrc", ".bash_profile", ".profile"]:
        cf_path = os.path.join(home, cf)
        if os.path.isfile(cf_path):
            try:
                with open(cf_path, "r", encoding="utf-8") as f:
                    for line in f:
                        stripped = line.strip()
                        if stripped.startswith("export ") and "REDFOX_API_KEY" in stripped:
                            parts = stripped.split("=", 1)
                            if len(parts) == 2:
                                val = parts[1].strip().strip('"').strip("'")
                                if val:
                                    return val
            except (IOError, OSError):
                continue

    # 3. 未找到，提示用户配置
    print("[error] 未找到 REDFOX_API_KEY，请按以下步骤配置：", file=sys.stderr)
    print("  1. 访问 https://redfox.hk/ 注册账号获取 API Key（格式 ak_xxxxxxxx）", file=sys.stderr)
    print("  2. 设置环境变量：export REDFOX_API_KEY=<你的apikey>", file=sys.stderr)
    print("  3. 如需永久生效，可将上述 export 语句追加到 ~/.zshrc 或 ~/.bashrc", file=sys.stderr)
    sys.exit(1)

def format_articles(articles: list) -> list:
    items = []
    for art in articles:
        # 标题中可能存在 | 字符，需转义避免破坏 Markdown 表格列分隔
        raw_title = (art.get("caption") or "").strip() or "-"
        safe_title = raw_title.replace("|", "\\|")

        publish_time, publish_date = parse_publish_time(art.get("publishTime"))

        items.append({
            "title":         safe_title,
            "author":        (art.get("nickname") or "").strip() or "-",
            "author_fans":   art.get("authorFans") or 0,
            "play_count":    art.get("viewCount") or 0,
            "like_count":    art.get("likeCount") or 0,
            "comment_count": art.get("commentCount") or 0,
            "collect_count": art.get("collectCount") or 0,
            "share_count":   art.get("shareCount") or 0,
            "forward_count": art.get("forwardCount") or 0,
            "duration":      art.get("duration") or 0,   # 视频时长（毫秒）
            "work_url":      art.get("videoUrl") or "",
            "cover_url":     art.get("coverUrl") or "",
            "publish_time":  publish_time,
            "publish_date":  publish_date,
            "work_id":       art.get("photoId") or "",
            "work_type":     art.get("workType") or "",
        })
    return items


def query_work_list(kwai_id: str = "", threex_id: str = "", page: int = 1, size: int = 20) -> dict:
    api_key = get_api_key()

    payload = {
        "page": page,
        "size": size,
    }
    if kwai_id:
        payload["kwaiId"] = kwai_id
    if threex_id:
        payload["threeXId"] = threex_id

    req = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type":  "application/json",
            "REDFOX_API_KEY": api_key,
            "X-API-KEY":     api_key,
            "User-Agent":    "WorkBuddy/1.0",
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

    # 翻页逻辑：当前页不足 size 条 → 已是最后一页；达到 size 条 → 有下一页
    has_next = articles_count >= size

    return {
        "articles":        format_articles(articles_list),
        "page":            page,
        "size":            size,
        "has_next":        has_next,
        "total":           articles_count,
    }


def main():
    parser = argparse.ArgumentParser(description="快手按账号获取作品列表（广域库）")
    parser.add_argument(
        "--kwai-id", dest="kwai_id", default="",
        help="快手账号平台展示 id（如 rmrbxmtzx，与 --threex-id 二选一必填）",
    )
    parser.add_argument(
        "--threex-id", dest="threex_id", default="",
        help="快手账号主页链接 id（如 https://www.kuaishou.com/profile/3x4wxhrrzefrq4y 中的 3x4wxhrrzefrq4y，与 --kwai-id 二选一必填）",
    )
    parser.add_argument("--page", dest="page", type=int, default=1, help="页码，从 1 开始（默认：1）")
    parser.add_argument("--size", dest="size", type=int, default=20, help="每页条数（默认：20，最大 50）")
    args = parser.parse_args()

    kwai_id = args.kwai_id.strip()
    threex_id = args.threex_id.strip()
    if not kwai_id and not threex_id:
        print("[error] 必须提供 --kwai-id 或 --threex-id 之一", file=sys.stderr)
        sys.exit(1)
    if args.page < 1:
        print("[error] 页码必须为正整数", file=sys.stderr)
        sys.exit(1)
    if args.size < 1:
        print("[error] size 必须为正整数", file=sys.stderr)
        sys.exit(1)
    size = min(args.size, MAX_SIZE)

    result = query_work_list(kwai_id, threex_id, args.page, size)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
