#!/usr/bin/env python3
"""
B站视频下载 - API 版本
使用 redfox.hk API 解析B站视频链接，直接返回无水印视频下载链接
支持单链接和批量链接解析，自动校验B站视频链接

Usage:
    python3 downloader.py <url> [<url> ...] [--api-key <key>]
"""

import argparse
import json
import os
import sys
import warnings
from pathlib import Path
from urllib.parse import urlparse

import requests

# Suppress urllib3 OpenSSL warning on macOS
warnings.filterwarnings("ignore", category=Warning)
warnings.filterwarnings("ignore", message=".*NotOpenSSLWarning.*")

# Ensure UTF-8 output (especially on Windows where default encoding may be GBK)
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, Exception):
    pass

API_URL = "https://redfox.hk/story/api/parseWork/videoDownload/bilibili"
CONFIG_DIR = Path.home() / ".qoder" / "apis"
CONFIG_FILE = CONFIG_DIR / "redfox.json"

ENV_KEY = "REDFOX_API_KEY"

GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


def info(msg):
    print(f"{GREEN}[✓]{RESET} {msg}")


def warn(msg):
    print(f"{YELLOW}[!]{RESET} {msg}")


def error(msg):
    print(f"{RED}[✗]{RESET} {msg}")


def step(msg):
    print(f"{CYAN}[→]{RESET} {msg}")


def get_api_key(cli_key=None):
    """Get API key with priority: CLI arg > env var > config file."""
    if cli_key:
        return cli_key

    env_key = os.environ.get(ENV_KEY)
    if env_key:
        return env_key

    if CONFIG_FILE.exists():
        try:
            data = json.loads(CONFIG_FILE.read_text())
            key = data.get("api_key")
            if key:
                return key
        except (json.JSONDecodeError, OSError):
            pass

    return None


def save_api_key(api_key):
    """Persist API key to config file."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps({"api_key": api_key}, indent=2))
    os.chmod(CONFIG_FILE, 0o600)  # secure file permissions
    info(f"API Key saved to {CONFIG_FILE}")


def is_bilibili_video_url(url):
    """Check if the URL is a valid Bilibili video link.

    Accepts:
      - www.bilibili.com  (PC web links / mobile share links)
      - b23.tv           (mobile short links)
    """
    try:
        parsed = urlparse(url)
    except Exception:
        return False
    domain = parsed.netloc.lower()
    if domain.startswith("www."):
        domain = domain[4:]
    return domain in ("bilibili.com", "b23.tv")


def extract_download_url(data):
    """Extract video download URL from API response data (tolerant of field naming)."""
    if isinstance(data, str):
        return data
    if not isinstance(data, dict):
        return None

    # Common field names that may carry the downloadable video link
    candidate_keys = [
        "videoUrl", "video_url", "downloadUrl", "download_url",
        "videoDownloadUrl", "video_download_url", "playUrl", "play_url",
        "url", "link",
    ]
    for key in candidate_keys:
        value = data.get(key)
        if isinstance(value, str) and value.startswith(("http://", "https://")):
            return value

    # Nested structures: data.video.url / data.media[0].url etc.
    for nested_key in ("video", "media", "result", "detail"):
        nested = data.get(nested_key)
        found = extract_download_url(nested) if isinstance(nested, (dict, list)) else None
        if found:
            return found

    if isinstance(data.get("videos"), list):
        for item in data["videos"]:
            found = extract_download_url(item)
            if found:
                return found

    return None


def format_duration(seconds):
    """Format duration in seconds to readable string: 'X 秒（约 X 分 X 秒）'."""
    if not isinstance(seconds, (int, float)) or not seconds:
        return "未知"
    seconds = int(seconds)
    if seconds < 60:
        return f"{seconds} 秒"
    minutes = seconds // 60
    secs = seconds % 60
    if secs == 0:
        return f"{seconds} 秒（约 {minutes} 分）"
    return f"{seconds} 秒（约 {minutes} 分 {secs} 秒）"


def process_single_url(url, session, output_json, index=None):
    """Process a single Bilibili video URL.

    Args:
        index: optional entry number for markdown output header.

    Returns:
        "success" — parsed successfully
        "error"   — non-fatal error, can continue with next URL
        "fatal"   — invalid URL or API Key issue, stop all processing
    """
    # ── Validate URL first ──
    if not is_bilibili_video_url(url):
        error(f"该链接不是B站视频链接：{url}")
        print(f"  请输入正确的B站视频链接")
        print(f"  支持格式：www.bilibili.com 网页链接 或 b23.tv 短链")
        return "fatal"

    step(f"URL: {url}")
    step("Calling redfox.hk API...")

    try:
        resp = session.post(API_URL, json={"url": url, "source": "bilibili/B站视频下载-GitHub"}, timeout=30)
        result = resp.json()
    except requests.exceptions.RequestException as e:
        error(f"API request failed: {e}")
        return "error"
    except json.JSONDecodeError:
        error(f"API returned invalid JSON: {resp.text[:200]}")
        return "error"

    code = result.get("code")
    msg = result.get("msg", "")

    # 成功 code 以 2 开头（如 200、2000），其余为错误
    if not str(code).startswith("2"):
        if code == 3106:
            error("缺少 API Key")
            return "fatal"
        elif code == 3107:
            error("API Key 无效或已失效，请检查是否正确")
            print("  配置方式：export REDFOX_API_KEY=ark_你的密钥")
            return "fatal"
        elif code == 400:
            error(f"请求参数错误: {msg}")
        else:
            error(f"API error (code {code}): {msg}")
        return "error"

    data = result.get("data")
    if not data:
        error("API returned empty data")
        return "error"

    # ── Parse result ──
    if output_json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return "success"

    desc = data.get("desc") if isinstance(data, dict) else None
    cover = data.get("cover") if isinstance(data, dict) else None
    resources = data.get("resources") if isinstance(data, dict) else None

    # ── Markdown output ──
    print()
    if index is not None:
        print(f"第 {index} 个\n")

    if desc:
        desc_text = str(desc).replace('\n', ' ').strip()
        print(f"内容描述: {desc_text}\n")

    # Collect video, audio, cover info from resources
    video_link = None
    audio_link = None
    cover_link = cover or None
    duration_val = None

    if isinstance(resources, list) and resources:
        for res in resources:
            if not isinstance(res, dict):
                continue
            rtype = (res.get("type") or "").lower()
            dl = res.get("downloadUrl")
            cu = res.get("coverUrl")
            dur = res.get("durationSeconds")

            if dur and not duration_val:
                duration_val = dur
            if cu and not cover_link:
                cover_link = cu
            if dl:
                if "audio" in rtype:
                    audio_link = dl
                else:
                    video_link = dl
    else:
        # Fallback: extract from top-level
        video_link = extract_download_url(data)
        if not video_link:
            error("未能从 API 返回结果中提取下载链接，原始返回如下：")
            print(json.dumps(data, ensure_ascii=False, indent=2))
            return "error"

    # Build markdown table
    print("| 项目 | 详情 |")
    print("| --- | --- |")

    if video_link:
        print(f"| 视频 | [下载链接]({video_link}) |")
    else:
        print("| 视频 | - |")

    if cover_link:
        print(f"| 封面图 | [查看封面]({cover_link}) |")
    else:
        print("| 封面图 | - |")

    print(f"\n> ⚠️ 视频下载链接有效期约 5 分钟，请立即复制到浏览器打开或下载！")
    return "success"


def main():
    parser = argparse.ArgumentParser(
        description="B站视频下载 - 使用 redfox.hk API 解析视频并返回下载链接（支持批量）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 downloader.py https://www.bilibili.com/video/BVxxxxxx
  python3 downloader.py https://www.bilibili.com/video/BVxxxxxx --api-key ark_xxxxx
  python3 downloader.py https://www.bilibili.com/video/BVaaaaa https://www.bilibili.com/video/BVbbbbb

也可通过环境变量 REDFOX_API_KEY 配置密钥：
  export REDFOX_API_KEY=ark_xxxxx
  python3 downloader.py <url> [<url> ...]
        """,
    )
    parser.add_argument(
        "urls",
        nargs="+",
        help="B站视频链接（支持多个，空格分隔），如 https://www.bilibili.com/video/BVxxxxxx",
    )
    parser.add_argument("--api-key", help="API Key（格式 ark_xxx，不传则读取环境变量或配置文件）")
    parser.add_argument(
        "--save-key",
        action="store_true",
        help="将本次传入的 API Key 保存到配置文件",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="以 JSON 格式输出完整返回结果",
    )

    args = parser.parse_args()

    # ── Banner ──
    banner = f"""{CYAN}{BOLD}
  ╔══════════════════════════════════════╗
  ║   Bilibili Video Downloader       ║
  ║   B站视频下载                     ║
  ╚══════════════════════════════════════╝{RESET}
"""
    print(banner)

    # ── API Key ──
    api_key = get_api_key(cli_key=args.api_key)
    if not api_key:
        error("未找到 API Key，请设置环境变量 REDFOX_API_KEY 或使用 --api-key 参数")
        print(f"  获取 Key: https://redfox.hk/settings/api-keys?source=github")
        sys.exit(1)

    # Save key if requested
    if args.save_key:
        save_api_key(api_key)

    # ── Normalize URLs ──
    urls = []
    for raw_url in args.urls:
        url = raw_url.strip().strip('"').strip("'")
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        urls.append(url)

    total = len(urls)

    # ── Session ──
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "X-API-KEY": api_key,
    })

    # ── Process URLs ──
    success_count = 0

    for i, url in enumerate(urls, 1):
        if total > 1:
            print(f"\n---\n")

        status = process_single_url(url, session, args.json, index=i if total > 1 else None)

        if status == "fatal":
            # Invalid URL or API Key issue — stop all processing
            sys.exit(1)
        elif status == "success":
            success_count += 1

    # ── Summary (batch mode) ──
    if total > 1:
        print(f"\n---\n")
        fail_count = total - success_count
        if fail_count == 0:
            print(f"✓ 批量解析完成：共 {total} 个链接，全部成功")
        else:
            print(f"✓ 批量解析完成：共 {total} 个链接，成功 {success_count} 个，失败 {fail_count} 个")

    # ── Enterprise procurement guidance ──
    print(f"\n💼 另外红狐配套全量数据库可提供完整详实数据，如需了解采购方案，可前往红狐hub 企业服务(https://redfox.hk/dashboard/enterprise) 对接咨询")

    sys.exit(0 if success_count > 0 else 1)


if __name__ == "__main__":
    main()
