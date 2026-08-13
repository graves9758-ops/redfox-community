#!/usr/bin/env python3
"""
微博用户博文查询脚本
调用 Redfox API 查询指定用户的最新博文
用法: python3 user_work_list.py "<uid或主页链接>" [--page 1]
"""

import sys
import os
import json
import argparse
import urllib.request
import urllib.error
import re

API_URL = "https://redfox.hk/story/api/weibo/ability/userWorkList"


def get_api_key() -> str:
    val = os.environ.get("REDFOX_API_KEY", "")
    if not val:
        print("[error] 未找到环境变量 REDFOX_API_KEY，请确认已设置 API Key", file=sys.stderr)
        sys.exit(1)
    return val


def extract_uid(raw: str) -> str:
    """从微博主页链接中提取 uid，或直接返回纯数字 uid"""
    raw = raw.strip()
    # 支持 https://weibo.com/1784473157 格式
    m = re.search(r"weibo\.com/(\d+)", raw)
    if m:
        return m.group(1)
    # 支持纯数字 uid
    if re.fullmatch(r"\d+", raw):
        return raw
    print(f"[error] 无法从输入中提取有效的 uid: {raw}", file=sys.stderr)
    sys.exit(1)


def sanitize_content(raw: str) -> str:
    """清理博文内容中的特殊字符，避免破坏 Markdown 格式"""
    s = raw.replace("\n", " ").replace("\r", " ")
    s = re.sub(r"\s+", " ", s).strip()
    s = s.replace("|", "\\|")
    s = s.replace("[", "【").replace("]", "】")
    return s or "-"


def format_articles(uid: str, articles: list) -> list:
    items = []
    for art in articles:
        content = (art.get("content") or art.get("text") or art.get("title") or "").strip()
        safe_content = sanitize_content(content)

        mblog_id = art.get("mblogId") or art.get("mblogid") or art.get("id") or ""
        if mblog_id:
            work_url = f"https://weibo.com/{uid}/{mblog_id}"
        else:
            work_url = ""

        items.append({
            "content":       safe_content,
            "forward_num":   art.get("forwardNum") or 0,
            "comment_num":   art.get("commentNum") or 0,
            "like_num":      art.get("likeNum") or 0,
            "publish_time":  art.get("publishTime") or "",
            "work_url":      work_url,
        })
    return items


def search(uid: str, page: int = 1) -> dict:
    api_key = get_api_key()
    payload = json.dumps({
        "uid":    uid,
        "page":   str(page),
        "source": "微博用户博文搜索-GitHub",
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
        articles_list = data.get("workList") or data.get("list") or data.get("articles") or []
    else:
        articles_list = []

    articles_count = len(articles_list)
    has_next = articles_count >= 9

    # 从第一条博文中提取用户昵称
    user_name = uid  # 默认回退为 uid
    if articles_list and isinstance(articles_list, list):
        first = articles_list[0]
        if isinstance(first, dict):
            user_name = first.get("nickname") or uid

    return {
        "uid":       uid,
        "user_name": user_name,
        "articles":  format_articles(uid, articles_list),
        "page":      page,
        "has_next":  has_next,
    }


def main():
    parser = argparse.ArgumentParser(description="微博用户博文查询")
    parser.add_argument("input", help="用户 uid 或微博主页链接（如 https://weibo.com/1784473157）")
    parser.add_argument(
        "--page", dest="page", type=int, default=1,
        help="页码，从1开始（默认1）",
    )
    args = parser.parse_args()

    if not args.input.strip():
        print("[error] 请输入用户 uid 或主页链接", file=sys.stderr)
        sys.exit(1)
    if args.page < 1:
        print("[error] 页码必须为正整数", file=sys.stderr)
        sys.exit(1)

    uid = extract_uid(args.input)
    result = search(uid, args.page)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
