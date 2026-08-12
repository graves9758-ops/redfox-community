#!/usr/bin/env python3
"""
快手按作品获取正文详情脚本（广域库）
调用 Redfox API，通过作品 ID（photoId）精确匹配查询单条作品详情（Lindorm 数据源）。
photoId 由列表接口返回（search_ks_keyword.py / search_ks_work.py 输出中的 work_id 字段）。
用法:
  python3 search_ks_detail.py "<photoId>"
"""

import sys
import os
import json
import time as _time
import argparse
import urllib.request
import urllib.error
from datetime import datetime

API_URL = "https://redfox.hk/story/api/ksAllData/queryWorkDetail"


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
    print("  1. 访问 https://redfox.hk?source=github 注册账号获取 API Key（格式 ak_xxxxxxxx）", file=sys.stderr)
    print("  2. 设置环境变量：export REDFOX_API_KEY=<你的apikey>", file=sys.stderr)
    print("  3. 如需永久生效，可将上述 export 语句追加到 ~/.zshrc 或 ~/.bashrc", file=sys.stderr)
    sys.exit(1)

def format_article(art: dict) -> dict:
    """格式化单条作品详情（字段与列表接口一致）。"""
    # 标题中可能存在 | 字符，需转义避免破坏 Markdown 表格列分隔
    raw_title = (art.get("caption") or "").strip() or "-"
    safe_title = raw_title.replace("|", "\\|")

    publish_time, publish_date = parse_publish_time(art.get("publishTime"))

    return {
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
        "head_url":      art.get("headUrl") or "",
        "publish_time":  publish_time,
        "publish_date":  publish_date,
        "work_type":     art.get("workType") or "",
    }


def query_work_detail(photo_id: str) -> dict:
    api_key = get_api_key()

    payload = {
        "photoId": photo_id,
    }

    req = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type":   "application/json",
            "REDFOX_API_KEY": api_key,
            "X-API-KEY":     api_key,
            "User-Agent":     "WorkBuddy/1.0",
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

    data = result.get("data")
    if not data or not isinstance(data, dict):
        print("[error] 接口未返回作品详情数据（data 为空）", file=sys.stderr)
        sys.exit(1)

    return {
        "detail":   format_article(data),
        "photo_id": photo_id,
    }


def main():
    parser = argparse.ArgumentParser(description="快手按作品获取正文详情（广域库）")
    parser.add_argument("photo_id", help="作品 ID（photoId，列表接口返回的加密 ID）")
    args = parser.parse_args()

    photo_id = args.photo_id.strip()
    if not photo_id:
        print("[error] 作品 ID 不能为空", file=sys.stderr)
        sys.exit(1)

    result = query_work_detail(photo_id)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
