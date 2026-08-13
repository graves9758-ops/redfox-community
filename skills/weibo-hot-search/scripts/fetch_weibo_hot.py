#!/usr/bin/env python3
"""
微博热搜榜单获取脚本
调用 Redfox API 获取微博热搜数据
用法: python3 fetch_weibo_hot.py
"""

import sys
import os
import json
import urllib.request
import urllib.error
import urllib.parse

API_URL = "https://redfox.hk/story/api/weibo/ability/hotSearch"

# tag 图标 URL → 文字+颜色映射
TAG_MAP = {
    "https://simg.s.weibo.com/20210226_fei.png":        "沸",
    "https://simg.s.weibo.com/moter/flags/16_0.png":     "沸",
    "https://simg.s.weibo.com/20210226_hot.png":         "热",
    "https://simg.s.weibo.com/moter/flags/2_0.png":      "热",
    "https://simg.s.weibo.com/20210226_new.png":         "新",
    "https://simg.s.weibo.com/moter/flags/1_0.png":      "新",
    "https://simg.s.weibo.com/20210226_warm.png":        "暖",
    "https://simg.s.weibo.com/moter/flags/32768_0.png":  "暖",
}


def get_api_key() -> str:
    val = os.environ.get("REDFOX_API_KEY", "")
    if not val:
        print("[error] 未找到环境变量 REDFOX_API_KEY，请确认已设置 API Key", file=sys.stderr)
        sys.exit(1)
    return val


def fetch() -> dict:
    api_key = get_api_key()
    payload = json.dumps({
        "source": "微博热搜-GitHub",
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
    # 兼容 data 为列表或字典
    if isinstance(data, list):
        items_list = data
    elif isinstance(data, dict):
        items_list = data.get("list") or data.get("hotList") or data.get("items") or []
    else:
        items_list = []

    hot_items = []
    for idx, item in enumerate(items_list, start=1):
        title = (item.get("topSearchName") or item.get("title") or item.get("word") or item.get("name") or "").strip()
        if not title:
            continue

        hot_score_raw = item.get("topSearchNum") or item.get("hotScore") or item.get("hot") or item.get("score") or ""
        # 只保留数字部分（去除可能混入的汉字如"万"等）
        import re as _re
        hot_score_raw = _re.sub(r"[^\d]", "", str(hot_score_raw))
        try:
            hot_score = int(hot_score_raw)
        except (ValueError, TypeError):
            hot_score = 0

        tag = (item.get("tag") or item.get("label") or "").strip()
        # 将 tag 图片 URL 映射为文字标签（如 新/热/沸/暖）
        tag_text = TAG_MAP.get(tag, "-") if tag else "-"
        hot_score_display = str(hot_score)

        hot_items.append({
            "rank":              idx,
            "title":             title,
            "url":               f"https://s.weibo.com/weibo?q={urllib.parse.quote(title)}",
            "hot_score":         hot_score,
            "hot_score_display": hot_score_display,
            "tag_text":          tag_text,
        })

    return {"items": hot_items}


if __name__ == "__main__":
    result = fetch()
    print(json.dumps(result, ensure_ascii=False, indent=2))
