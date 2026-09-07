#!/usr/bin/env python3
"""
小红书作品爬取脚本
调用 Redfox API 爬取小红书热门作品数据
用法: python3 crawl_xhs.py "<关键词>" [--start-date YYYY-MM-DD] [--end-date YYYY-MM-DD] [--sort-type _0|_2|_4]
"""

import sys
import os
import re
import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta

try:
    import requests
except ImportError:
    print("[error] 缺少 requests 库，请执行: pip3 install requests", file=sys.stderr)
    sys.exit(1)

API_URL = "https://redfox.hk/story/api/xhs/crawl/work"


SHELL_CONFIG_FILES = [".zshrc", ".bashrc", ".bash_profile", ".profile", ".zprofile"]


def get_api_key() -> str:
    """获取 API Key：环境变量优先，其次扫描 Shell 配置文件"""
    val = os.environ.get("REDFOX_API_KEY", "").strip()
    if val:
        return val
    for cfg in SHELL_CONFIG_FILES:
        cfg_path = Path.home() / cfg
        if cfg_path.is_file():
            try:
                content = cfg_path.read_text(encoding="utf-8", errors="replace")
                m = re.search(r'export\s+REDFOX_API_KEY\s*=\s*["\']?([a-zA-Z0-9_\-]+)["\']?', content)
                if m and m.group(1).strip():
                    return m.group(1).strip()
            except OSError:
                continue
    print("[error] 未找到 REDFOX_API_KEY，请设置环境变量或将 export REDFOX_API_KEY=ak_xxxxxxxx 写入 ~/.zshrc / ~/.bashrc 后 source", file=sys.stderr)
    print("  API Key 获取：https://redfox.hk/?source=github 注册登录后在个人中心获取", file=sys.stderr)
    sys.exit(1)


def format_works(works: list) -> list:
    """将原始数据转换为统一格式"""
    items = []
    for w in works:
        title = (w.get("title") or "").strip() or "-"
        items.append({
            "title": title,
            "author": (w.get("authorNickname") or "").strip(),
            "collect_count": w.get("collectedCount", 0) or 0,
            "share_count": w.get("sharedCount", 0) or 0,
            "comment_count": w.get("commentsCount", 0) or 0,
            "like_count": w.get("likedCount", 0) or 0,
            "publish_time": w.get("createTime", ""),
            "work_url": w.get("shareInfoLink", ""),
            "cover": w.get("cover", ""),
            "desc": w.get("desc", ""),
            "author_fans": w.get("authorFans", 0) or 0,
            "interactive_count": w.get("interactiveCount", 0) or 0,
            "work_id": w.get("id", ""),
        })
    items.sort(key=lambda x: x["like_count"], reverse=True)
    return items


def get_default_date_range() -> tuple:
    """返回默认日期范围：最近30天"""
    today = datetime.now()
    start = today - timedelta(days=30)
    return start.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d")


def crawl(keyword: str, start_date: str = "", end_date: str = "", sort_type: str = "_0") -> dict:
    """调用爬取接口，返回作品数据"""
    if not start_date and not end_date:
        start_date, end_date = get_default_date_range()
    api_key = get_api_key()
    payload = {
        "keyword": keyword,
        "startDate": start_date,
        "endDate": end_date,
        "source": "小红书作品爬取-GitHub",
        "sortType": sort_type,
    }

    headers = {
        "Content-Type": "application/json",
        "X-API-Key": api_key,
        "User-Agent": "QoderWork/1.0",
    }

    try:
        resp = requests.post(API_URL, json=payload, headers=headers, timeout=15, verify=True)
        resp.raise_for_status()
        result = resp.json()
    except requests.exceptions.HTTPError as e:
        print(f"[error] HTTP {resp.status_code}: {resp.text}", file=sys.stderr)
        sys.exit(1)
    except requests.exceptions.ConnectionError as e:
        print(f"[error] 网络请求失败: {e}", file=sys.stderr)
        sys.exit(1)
    except requests.exceptions.Timeout:
        print("[error] 请求超时，请稍后重试", file=sys.stderr)
        sys.exit(1)
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        print(f"[error] 数据解析异常: {e}", file=sys.stderr)
        sys.exit(1)

    code = result.get("code")
    if code != 2000:
        print(f"[error] 接口返回错误: code={code}, msg={result.get('msg', '未知')}", file=sys.stderr)
        sys.exit(1)

    data = result.get("data") or {}
    raw_list = (
        data.get("works")
        or data.get("list")
        or data.get("articles")
        or []
    )
    raw_hot = data.get("latestHotArticles") or []

    return {
        "articles": format_works(raw_list),
        "total": len(raw_list),
        "relatedSearches": data.get("relatedSearches") or [],
        "latestHotArticles": format_works(raw_hot),
        "hotTopics": data.get("hotTopics") or [],
    }


def main():
    parser = argparse.ArgumentParser(description="小红书作品爬取脚本")
    parser.add_argument("keyword", help="搜索关键词")
    parser.add_argument("--start-date", "-s", default="", help="起始日期，格式 YYYY-MM-DD（默认：30天前）")
    parser.add_argument("--end-date", "-e", default="", help="结束日期，格式 YYYY-MM-DD（默认：今天）")
    parser.add_argument("--sort-type", "-t", default="_0", choices=["_0", "_2", "_4"],
                        help="排序方式: _0=相关性(默认), _2=最新, _4=最热")
    args = parser.parse_args()

    keyword = args.keyword.strip()

    result = crawl(keyword, start_date=args.start_date, end_date=args.end_date, sort_type=args.sort_type)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
