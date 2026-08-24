#!/usr/bin/env python3
"""
快手账号搜索脚本（广域库）
调用 Redfox API，通过快手账号名称（profile.userName）模糊包含匹配搜索账号，支持分页。
返回的 kwaiId 可直接用于 queryWorkList 接口（search_ks_work.py --kwai-id）查询该账号作品列表。
用法:
  python3 search_ks_user.py "<账号名称>" [--page 1] [--size 20]
"""

import sys
import os
import json
import argparse
import urllib.request
import urllib.error

API_URL = "https://redfox.hk/story/api/ksAllData/searchUser"
SOURCE = "快手账号搜索-GitHub"

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


def format_users(users: list) -> list:
    items = []
    for user in users:
        items.append({
            "nickname":      (user.get("nickname") or "").strip() or "-",
            "kwai_id":       (user.get("kwaiId") or "").strip() or "",
            "signature":     (user.get("signature") or "").strip() or "",
            "head_url":      user.get("headUrl") or "",
            "cover_img_url": user.get("coverImgUrl") or "",
        })
    return items


def search_user(account_name: str, page: int = 1, page_size: int = 20) -> dict:
    api_key = get_api_key()

    payload = {
        "accountName": account_name,
        "page":        page,
        "pageSize":    page_size,
        "source":      SOURCE,
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

    data = result.get("data") or {}
    users_list = data.get("list") or []
    users_count = len(users_list)

    # 翻页逻辑：当前页不足 pageSize 条 → 已是最后一页；达到 pageSize 条 → 有下一页
    has_next = users_count >= page_size

    return {
        "users":         format_users(users_list),
        "total":         data.get("total", users_count),
        "page":          page,
        "page_size":     page_size,
        "has_next":      has_next,
    }


def main():
    parser = argparse.ArgumentParser(description="快手账号搜索（广域库）")
    parser.add_argument("account_name", help="快手账号名称（模糊搜索关键词，如：人民日报）")
    parser.add_argument("--page", dest="page", type=int, default=1, help="页码，从 1 开始（默认：1）")
    parser.add_argument("--size", dest="size", type=int, default=20, help="每页条数（默认：20，最大 50）")
    args = parser.parse_args()

    account_name = args.account_name.strip()
    if not account_name:
        print("[error] 账号名称不能为空", file=sys.stderr)
        sys.exit(1)
    if args.page < 1:
        print("[error] 页码必须为正整数", file=sys.stderr)
        sys.exit(1)
    if args.size < 1:
        print("[error] size 必须为正整数", file=sys.stderr)
        sys.exit(1)
    size = min(args.size, MAX_SIZE)

    result = search_user(account_name, args.page, size)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
