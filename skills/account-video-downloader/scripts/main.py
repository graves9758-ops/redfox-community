#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多平台账号主页视频提取器 — 统一入口
=====================================
支持平台：抖音、快手、哔哩哔哩、YouTube

Usage:
    python3 main.py --platform douyin --account "抖音号"
    python3 main.py --platform kuaishou --account "kwaiId"
    python3 main.py --platform bilibili --account "主页URL" --download
    python3 main.py --platform youtube --account "频道URL" --download --output-dir ./videos
"""

import argparse
import os
import sys
from datetime import datetime

# Windows 终端 UTF-8 编码修复
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from .base import (
    DEFAULT_PAGE_SIZE,
    DEFAULT_RATE_LIMIT,
    MAX_PAGE_SIZE,
    get_api_key,
    info,
    warn,
    error,
    BOLD,
    CYAN,
    RED,
    YELLOW,
    RESET,
    process_account,
    print_markdown_table,
    print_json_output,
)
from .kuaishou import KuaishouDownloader
from .douyin import DouyinDownloader
from .bilibili import BilibiliDownloader
from .youtube import YouTubeDownloader

# ─── 平台注册表 ────────────────────────────────────────────────────────────────────

PLATFORM_REGISTRY = {
    "douyin": {
        "label": "抖音",
        "downloader_cls": DouyinDownloader,
        "help": "抖音账号视频下载（抖音号 uniqueName）",
    },
    "kuaishou": {
        "label": "快手",
        "downloader_cls": KuaishouDownloader,
        "help": "快手账号视频下载（用户 ID）",
    },
    "bilibili": {
        "label": "B站",
        "downloader_cls": BilibiliDownloader,
        "help": "B站账号视频下载（主页链接 accountUrl）",
    },
    "youtube": {
        "label": "YouTube",
        "downloader_cls": YouTubeDownloader,
        "help": "YouTube 频道视频下载（频道 ID / @handle）",
    },
}


def get_platform(name: str) -> dict:
    """根据平台名获取平台配置，支持模糊匹配"""
    name_lower = name.lower().strip()
    if name_lower in PLATFORM_REGISTRY:
        return PLATFORM_REGISTRY[name_lower]
    # 模糊匹配
    fuzzy_map = {
        "dy": "douyin",
        "douyin": "douyin",
        "ks": "kuaishou",
        "kuaishou": "kuaishou",
        "bili": "bilibili",
        "b站": "bilibili",
        "yt": "youtube",
        "youtube": "youtube",
    }
    mapped = fuzzy_map.get(name_lower)
    if mapped:
        return PLATFORM_REGISTRY[mapped]
    return None


def main():
    platforms_help = "\n".join(
        f"  {k:12s} — {v['label']}：{v['help']}"
        for k, v in PLATFORM_REGISTRY.items()
    )

    parser = argparse.ArgumentParser(
        description="多平台账号主页视频提取器 — 支持抖音/快手/B站/YouTube",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
支持的平台:
{platforms_help}

示例:
  python3 main.py --platform kuaishou --account "kwaiId"
  python3 main.py --platform bilibili --account "主页URL" --download
  python3 main.py --platform youtube --account "频道URL" --download --output-dir ./videos
        """,
    )
    parser.add_argument("--platform", "-p", required=True,
                        help="目标平台：douyin / kuaishou / bilibili / youtube")
    parser.add_argument("--account", "-a", required=False,
                        help="单个账号标识")
    parser.add_argument("--accounts", required=False,
                        help="多个账号标识，逗号分隔")
    parser.add_argument("--count", "-c", type=int, default=DEFAULT_PAGE_SIZE,
                        help=f"拉取作品数量（默认{DEFAULT_PAGE_SIZE}，最多{MAX_PAGE_SIZE}）")
    parser.add_argument("--page", type=int, default=1, help="页码（默认1）")
    parser.add_argument("--date-start", help="起始日期 YYYY-MM-DD")
    parser.add_argument("--date-end", help="结束日期 YYYY-MM-DD")
    parser.add_argument("--download", "-d", action="store_true", help="下载视频文件到本地")
    parser.add_argument("--output-dir", "-o", default="", help="下载目录（默认 output/）")
    parser.add_argument("--json", "-j", action="store_true", help="JSON 格式输出")
    parser.add_argument("--rate-limit", "-r", type=float, default=DEFAULT_RATE_LIMIT,
                        help=f"请求间隔秒数（默认{DEFAULT_RATE_LIMIT}）")

    args = parser.parse_args()

    # ── 平台识别 ──
    platform_cfg = get_platform(args.platform)
    if not platform_cfg:
        error(f"不支持的平台: {args.platform}")
        print(f"  支持: {', '.join(PLATFORM_REGISTRY.keys())}")
        sys.exit(1)

    platform_label = platform_cfg["label"]
    downloader_cls = platform_cfg["downloader_cls"]

    # ── 收集账号列表 ──
    account_ids = []
    if args.account:
        account_ids.append(args.account.strip())
    if args.accounts:
        account_ids.extend([a.strip() for a in args.accounts.split(",") if a.strip()])

    if not account_ids:
        error("请提供至少一个账号标识（--account 或 --accounts）")
        sys.exit(1)

    # ── API Key ──
    api_key = get_api_key()
    if not api_key:
        error("未找到 API Key，请设置 REDFOX_API_KEY 环境变量")
        print(f"  获取 Key: https://redfox.hk/settings/api-keys?source=github")
        print(f"  设置方式: export REDFOX_API_KEY=ak_你的密钥")
        sys.exit(1)

    # ── 创建下载器 ──
    downloader = downloader_cls(api_key)

    # ── 账号标识验证 ──
    invalid_ids = []
    for aid in account_ids:
        valid, msg = downloader.validate_account_id(aid)
        if not valid:
            invalid_ids.append((aid, msg))

    if invalid_ids:
        print(f"\n{RED}{BOLD}⚠️ 以下输入不是有效的{platform_label}账号标识：{RESET}\n")
        for aid, msg in invalid_ids:
            print(f"  {YELLOW}• {msg}{RESET}\n")
        print(f"{CYAN}💡 {downloader.description_hint()}{RESET}\n")
        sys.exit(2)

    # ── 下载目录 ──
    output_dir = args.output_dir or os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "output")
    if args.download:
        os.makedirs(output_dir, exist_ok=True)

    # ── Banner ──
    print(f"""{CYAN}{BOLD}
  ╔══════════════════════════════════════════╗
  ║     多平台账号主页视频提取器               ║
  ║     Multi-Platform Account Video         ║
  ║     Extractor                            ║
  ╚══════════════════════════════════════════╝{RESET}
""")
    info(f"平台: {platform_label} | API Key 已加载 | 账号数: {len(account_ids)} | 作品数/账号: {min(args.count, MAX_PAGE_SIZE)}")

    all_accounts = []
    all_results = []

    for idx, account_id in enumerate(account_ids):
        if idx > 0:
            print(f"\n{CYAN}{'─' * 50}{RESET}\n")

        account, results = process_account(
            downloader,
            account_id,
            page_size=args.count,
            page_num=args.page,
            date_start=args.date_start or "",
            date_end=args.date_end or "",
            rate_limit=args.rate_limit,
            do_download=args.download,
            output_dir=output_dir,
        )
        all_accounts.append(account)
        all_results.append((account, results))

    # ── 输出结果 ──
    print(f"\n{CYAN}{BOLD}{'=' * 50}{RESET}\n")

    if args.json:
        output = {
            "platform": platform_cfg["label"],
            "platform_key": args.platform,
            "accounts": [],
            "total_works": 0,
            "total_success": 0,
            "total_failed": 0,
            "generated_at": datetime.now().isoformat(),
        }
        for account, results in all_results:
            output["accounts"].append({
                "account": account,
                "total": len(results),
                "success": sum(1 for r in results if r.get("download_success")),
                "failed": sum(1 for r in results if not r.get("download_success")),
                "results": results,
            })
            output["total_works"] += len(results)
            output["total_success"] += sum(1 for r in results if r.get("download_success"))
            output["total_failed"] += sum(1 for r in results if not r.get("download_success"))
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        for account, results in all_results:
            if results:
                print_markdown_table(downloader, account, results, page_num=args.page, page_size=args.count)
            else:
                name = account.get("accountName", account.get("accountId", "未知"))
                warn(f"@{name}：暂无作品或拉取失败")

        total_works = sum(len(r) for _, r in all_results)
        total_success = sum(sum(1 for x in r if x.get("download_success")) for _, r in all_results)
        total_failed = total_works - total_success
        print(f"\n{BOLD}总计：{RESET}{len(account_ids)} 个账号，{total_works} 条作品，成功 {total_success} 条，失败 {total_failed} 条")

    if args.download:
        info(f"视频文件保存至: {os.path.abspath(output_dir)}")

    total_success_final = sum(sum(1 for x in r if x.get("download_success")) for _, r in all_results)
    total_works_final = sum(len(r) for _, r in all_results)
    sys.exit(0 if total_success_final == total_works_final else 1)


if __name__ == "__main__":
    main()
