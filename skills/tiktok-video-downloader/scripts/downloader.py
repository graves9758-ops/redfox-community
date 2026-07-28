#!/usr/bin/env python3
"""
TikTok视频下载 - API 版本
使用 redfox.hk API 解析 TikTok 视频链接，直接返回无水印视频下载链接
支持单链接和批量链接解析，自动校验 TikTok 链接有效性

Usage:
    python3 downloader.py <url> [--api-key <key>]
    python3 downloader.py <url1> <url2> <url3> [--api-key <key>]
"""

import argparse
import json
import os
import re
import sys
import warnings
from pathlib import Path
from urllib.parse import urlparse

import requests

# Suppress urllib3 OpenSSL warning on macOS
warnings.filterwarnings("ignore", category=Warning)
warnings.filterwarnings("ignore", message=".*NotOpenSSLWarning.*")

# Ensure UTF-8 output for emoji and CJK characters on Windows console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

API_URL = "https://redfox.hk/story/api/parseWork/videoDownload/tiktok"
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


class ApiKeyError(Exception):
    """Raised when API key is missing or invalid, should stop batch processing."""
    pass


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


def is_tiktok_link(url):
    """Check if the URL is a TikTok video link (web link or short link).

    Supports:
      - https://www.tiktok.com/@user/video/xxxxx
      - https://vm.tiktok.com/xxxxx/
      - https://vt.tiktok.com/xxxxx/
    """
    try:
        parsed = urlparse(url)
        host = (parsed.hostname or "").lower()
        return host.endswith("tiktok.com")
    except Exception:
        return False


def normalize_url(url):
    """Normalize a URL: strip quotes and ensure it has a scheme."""
    url = url.strip().strip('"').strip("'")
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url


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


def get_audio_url(res):
    """Extract audio URL from a resource dict (tolerant of field naming)."""
    if not isinstance(res, dict):
        return None
    for key in ("audioUrl", "audio_url", "audioDownloadUrl", "audio_download_url",
                "musicUrl", "music_url", "soundUrl", "sound_url"):
        value = res.get(key)
        if isinstance(value, str) and value.startswith(("http://", "https://")):
            return value
    return None


def process_single_video(url, api_key, json_mode=False):
    """Process a single TikTok video URL: validate, call API, print results.

    Returns True on success, False on failure.
    Raises ApiKeyError if the API key is missing/invalid (fatal for batch mode).
    Terminates the process (sys.exit) if the URL is not a TikTok link.
    """
    # ── Validate TikTok link ──
    if not is_tiktok_link(url):
        error(f"该链接不是 TikTok 视频链接，请输入正确的 TikTok 视频链接：{url}")
        print(f"  正确的链接格式示例：")
        print(f"  https://www.tiktok.com/@user/video/xxxxx")
        print(f"  https://vm.tiktok.com/xxxxx/")
        sys.exit(1)

    step(f"URL: {url}")

    # ── Call API ──
    step("Calling redfox.hk API...")

    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "X-API-KEY": api_key,
    })

    try:
        resp = session.post(API_URL, json={"url": url, "source": "TikTok视频下载-GitHub"}, timeout=30)
        result = resp.json()
    except requests.exceptions.RequestException as e:
        error(f"API request failed: {e}")
        return False
    except json.JSONDecodeError:
        error(f"API returned invalid JSON: {resp.text[:200]}")
        return False

    code = result.get("code")
    msg = result.get("msg", "")

    # 成功 code 以 2 开头（如 200、2000），其余为错误
    if not str(code).startswith("2"):
        if code == 3106:
            error("缺少 API Key")
            raise ApiKeyError()
        elif code == 3107:
            error("API Key 无效或已失效，请检查是否正确")
            print("  配置方式：export REDFOX_API_KEY=ark_你的密钥")
            raise ApiKeyError()
        elif code == 400:
            error(f"请求参数错误: {msg}")
        else:
            error(f"API error (code {code}): {msg}")
        return False

    data = result.get("data")
    if not data:
        error("API returned empty data")
        return False

    # ── Parse result ──
    if json_mode:
        print(json.dumps(data, ensure_ascii=False, indent=2))

    desc = data.get("desc") if isinstance(data, dict) else None
    cover = data.get("cover") if isinstance(data, dict) else None
    resources = data.get("resources") if isinstance(data, dict) else None

    print(f"\n{GREEN}{BOLD}✓ 解析成功！{RESET}")

    # 内容描述（完整原文，不截断）
    if desc:
        print(f"\n{CYAN}{BOLD}📝 内容描述：{RESET}")
        for line in str(desc).splitlines():
            print(f"  {line}")

    # 资源列表：类型 / 时长 / 下载链接 / 封面图 / 音频链接
    if isinstance(resources, list) and resources:
        print(f"\n{CYAN}{BOLD}🎬 资源列表（共 {len(resources)} 个）：{RESET}")
        for i, res in enumerate(resources, 1):
            if not isinstance(res, dict):
                continue
            rtype = res.get("type") or "未知"
            dl = res.get("downloadUrl") or "-"
            cu = res.get("coverUrl") or cover or "-"
            dur = res.get("durationSeconds")
            dur_str = f"{dur} 秒" if isinstance(dur, (int, float)) and dur else "未知"
            audio = get_audio_url(res)
            print(f"\n  {BOLD}【资源 {i}】{RESET}")
            print(f"    资源类型：{rtype}")
            print(f"    时长：{dur_str}")
            print(f"    下载链接：{dl}")
            print(f"    封面图：{cu}")
            if audio:
                print(f"    音频链接：{audio}")
    else:
        # 回退：无 resources 字段时从顶层提取
        download_url = extract_download_url(data)
        if not download_url:
            error("未能从 API 返回结果中提取下载链接，原始返回如下：")
            print(json.dumps(data, ensure_ascii=False, indent=2))
            return False
        print(f"\n{CYAN}{BOLD}🎬 资源：{RESET}")
        print(f"    下载链接：{download_url}")
        if cover:
            print(f"    封面图：{cover}")
        audio = get_audio_url(data) if isinstance(data, dict) else None
        if audio:
            print(f"    音频链接：{audio}")

    print(f"\n{CYAN}复制链接到浏览器或下载工具即可下载。{RESET}")
    print(f"\n{YELLOW}⚠️ 视频下载链接有效期约 5 分钟，请立即复制到浏览器打开或下载！{RESET}")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="TikTok视频下载 - 使用 redfox.hk API 解析视频并返回下载链接，支持批量解析",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # 单个链接
  python3 downloader.py https://www.tiktok.com/@user/video/xxxxx
  python3 downloader.py https://www.tiktok.com/@user/video/xxxxx --api-key ark_xxxxx

  # 批量链接（空格分隔）
  python3 downloader.py https://www.tiktok.com/@user/video/111 https://www.tiktok.com/@user/video/222

也可通过环境变量 REDFOX_API_KEY 配置密钥：
  export REDFOX_API_KEY=ark_xxxxx
  python3 downloader.py <url> [<url> ...]
        """,
    )
    parser.add_argument("urls", nargs="+", help="TikTok 视频链接（支持多个，空格分隔），如 https://www.tiktok.com/@user/video/xxxxx")
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
  ║   TikTok Video Downloader            ║
  ║   TikTok视频下载                     ║
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

    # ── Process URLs ──
    total = len(args.urls)
    if total > 1:
        print(f"{CYAN}{BOLD}📋 批量解析模式：共 {total} 个链接{RESET}\n")

    success_count = 0
    fail_count = 0

    for idx, raw_url in enumerate(args.urls, 1):
        if total > 1:
            print(f"\n{CYAN}{BOLD}{'='*50}{RESET}")
            print(f"{CYAN}{BOLD}📋 第 {idx}/{total} 个链接{RESET}")
            print(f"{CYAN}{BOLD}{'='*50}{RESET}")

        url = normalize_url(raw_url)

        try:
            ok = process_single_video(url, api_key, json_mode=args.json)
        except ApiKeyError:
            # API Key 无效，后续链接必然也会失败，直接退出
            if fail_count > 0 or success_count > 0:
                print(f"\n{RED}API Key 无效，已终止批量解析。{RESET}")
            sys.exit(1)

        if ok:
            success_count += 1
        else:
            fail_count += 1

    # ── Summary ──
    if total > 1:
        print(f"\n{CYAN}{BOLD}{'='*50}{RESET}")
        print(f"{CYAN}{BOLD}📋 批量解析完成{RESET}")
        print(f"  {GREEN}✓ 成功：{success_count} 个{RESET}")
        print(f"  {RED}✗ 失败：{fail_count} 个{RESET}")

    print(f"\n{CYAN}复制链接到浏览器或下载工具即可下载。{RESET}")
    sys.exit(0 if success_count > 0 else 1)


if __name__ == "__main__":
    main()
