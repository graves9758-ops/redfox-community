#!/usr/bin/env python3
"""
Qoder Video Downloader - API 版本
使用 redfox.hk API 解析并下载无水印视频/图文
支持：抖音、小红书、快手、视频号、B站、YouTube、Instagram、X、TikTok、Threads、Facebook、Vimeo 等

Usage:
    python3 downloader.py <url> [--api-key <key>] [--output-dir <path>]
"""

import argparse
import json
import os
import re
import sys
import warnings
from pathlib import Path

import requests

# Suppress urllib3 OpenSSL warning on macOS
warnings.filterwarnings("ignore", category=Warning)
warnings.filterwarnings("ignore", message=".*NotOpenSSLWarning.*")

API_URL = "https://redfox.hk/story/api/parseWork/parse"
CONFIG_DIR = Path.home() / ".qoder" / "apis"
CONFIG_FILE = CONFIG_DIR / "redfox.json"

ENV_KEY = "REDFOX_API_KEY"

PLATFORM_MAP = {
    "dy": "抖音",
    "xhs": "小红书",
    "xhsw": "小红书",
    "ks": "快手",
    "bili": "B站",
}

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


def require_api_key(cli_key=None):
    """Resolve API key or exit with configuration guidance."""
    api_key = get_api_key(cli_key=cli_key)
    if api_key:
        return api_key

    print(f"{RED}╔══════════════════════════════════════════════════╗{RESET}")
    print(f"{RED}║  未配置 API Key，请通过以下方式之一配置：      ║{RESET}")
    print(f"{RED}║                                                ║{RESET}")
    print(f"{RED}║  export REDFOX_API_KEY=ak_你的密钥             ║{RESET}")
    print(f"{RED}║  python3 downloader.py <url> --api-key ak_xxx  ║{RESET}")
    print(RED + "║  echo '{\"api_key\":\"ak_你的密钥\"}' > ~/.qoder/apis/redfox.json ║" + RESET)
    print(f"{RED}║                                                ║{RESET}")
    print(f"{RED}║  注册获取 Key: https://redfox.hk/settings/api-keys ║{RESET}")
    print(f"{RED}╚══════════════════════════════════════════════════╝{RESET}")
    sys.exit(1)


def save_api_key(api_key):
    """Persist API key to config file."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps({"api_key": api_key}, indent=2))
    os.chmod(CONFIG_FILE, 0o600)  # secure file permissions
    info(f"API Key saved to {CONFIG_FILE}")


def sanitize_filename(name):
    """Remove or replace characters unsafe for filenames."""
    if not name:
        return None
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    name = name.strip().replace(" ", "_")
    name = name[:120]  # limit length
    return name or None


def download_file(session, url, filepath, desc="Downloading"):
    """Download a file with progress display."""
    try:
        resp = session.get(url, stream=True, timeout=120)
        resp.raise_for_status()

        total = int(resp.headers.get("content-length", 0))
        downloaded = 0

        with open(filepath, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total > 0:
                        pct = int(downloaded * 100 / total)
                        bar = "█" * (pct // 5) + "░" * (20 - pct // 5)
                        print(f"\r  {bar} {pct}%", end="", flush=True)
        print()
        return True

    except requests.exceptions.RequestException as e:
        error(f"Download failed: {e}")
        return False


def is_valid_share_url(url):
    """Check if the URL is a valid sharing link from supported platforms.
    Returns (is_valid: bool, platform_name: str or None).
    """
    # Domain -> Platform mapping for known sharing link patterns
    platform_patterns = [
        # 抖音 Douyin
        (r'(https?://)?(www\.)?v\.douyin\.com/', '抖音'),
        (r'(https?://)?(www\.)?douyin\.com/(video|jingxuan|note)/', '抖音'),
        (r'(https?://)?(www\.)?douyin\.com\/user\/', '抖音'),
        # 小红书 Xiaohongshu
        (r'(https?://)?(www\.)?xhslink\.(com|cn)/', '小红书'),
        (r'(https?://)?(www\.)?xiaohongshu\.com/', '小红书'),
        (r'(https?://)?(www\.)?xhslink\.com/', '小红书'),
        # 快手 Kuaishou
        (r'(https?://)?(www\.)?v\.kuaishou\.com/', '快手'),
        (r'(https?://)?(www\.)?kuaishou\.com/', '快手'),
        # 视频号 WeChat Channels
        (r'(https?://)?weixin\.qq\.com/sph/', '视频号'),
        # B站 Bilibili
        (r'(https?://)?(www\.)?b23\.tv/', 'B站'),
        (r'(https?://)?(www\.)?bilibili\.com/video/', 'B站'),
        # YouTube
        (r'(https?://)?(www\.)?youtu\.be/', 'YouTube'),
        (r'(https?://)?(www\.)?youtube\.com/watch\?', 'YouTube'),
        (r'(https?://)?(www\.)?youtube\.com/shorts/', 'YouTube'),
        # Instagram
        (r'(https?://)?(www\.)?instagram\.com/p/', 'Instagram'),
        (r'(https?://)?(www\.)?instagram\.com/reel/', 'Instagram'),
        # X / Twitter
        (r'(https?://)?(www\.)?x\.com/\w+/status/', 'X (Twitter)'),
        (r'(https?://)?(www\.)?twitter\.com/\w+/status/', 'X (Twitter)'),
        # TikTok
        (r'(https?://)?(www\.)?tiktok\.com/@', 'TikTok'),
        # Threads
        (r'(https?://)?(www\.)?threads\.net/@', 'Threads'),
        # Facebook
        (r'(https?://)?(www\.)?facebook\.com/.*/videos/', 'Facebook'),
        (r'(https?://)?(www\.)?fb\.com/.*/videos/', 'Facebook'),
        # Vimeo
        (r'(https?://)?(www\.)?vimeo\.com/\d+', 'Vimeo'),
    ]
    for pattern, name in platform_patterns:
        if re.search(pattern, url, re.IGNORECASE):
            return True, name
    return False, None


def show_url_guide():
    """Show supported platform URL formats."""
    print(f"\n{YELLOW}╔══════════════════════════════════════════════════════════╗{RESET}")
    print(f"{YELLOW}║  链接格式不支持或无法识别，请检查是否传入了正确的分享链接  ║{RESET}")
    print(f"{YELLOW}╠══════════════════════════════════════════════════════════╣{RESET}")
    print(f"{YELLOW}║  支持的链接格式：                                       ║{RESET}")
    print(f"{YELLOW}║  🎵 抖音     v.douyin.com/xxx                           ║{RESET}")
    print(f"{YELLOW}║  📕 小红书   xhslink.com/xxx 或 xhslink.cn/xxx           ║{RESET}")
    print(f"{YELLOW}║  📱 快手     v.kuaishou.com/xxx                         ║{RESET}")
    print(f"{YELLOW}║  📺 视频号   weixin.qq.com/sph/xxx                      ║{RESET}")
    print(f"{YELLOW}║  📺 B站      b23.tv/xxx 或 bilibili.com/video/xxx        ║{RESET}")
    print(f"{YELLOW}║  ▶️ YouTube  youtu.be/xxx 或 youtube.com/watch?v=xxx     ║{RESET}")
    print(f"{YELLOW}║  📷 Instagram instagram.com/p/xxx                       ║{RESET}")
    print(f"{YELLOW}║  🐦 X/Twitter  x.com/xxx/status/xxx                     ║{RESET}")
    print(f"{YELLOW}║  🎵 TikTok   tiktok.com/@xxx/video/xxx                  ║{RESET}")
    print(f"{YELLOW}║  🧵 Threads  threads.net/@xxx/post/xxx                  ║{RESET}")
    print(f"{YELLOW}║  📘 Facebook  facebook.com/xxx/videos/xxx               ║{RESET}")
    print(f"{YELLOW}║  🎬 Vimeo    vimeo.com/xxxxxx                           ║{RESET}")
    print(f"{YELLOW}╚══════════════════════════════════════════════════════════╝{RESET}")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="短视频下载器 - 使用 redfox.hk API 下载无水印视频",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 downloader.py https://v.douyin.com/xxxxxx/
  python3 downloader.py https://b23.tv/xxxxxx --api-key ak_xxxxx
  python3 downloader.py https://xhslink.com/o/xxxxxx -o ~/Videos

也可通过环境变量 REDFOX_API_KEY 配置密钥：
  export REDFOX_API_KEY=ak_xxxxx
  python3 downloader.py <url>
        """,
    )
    parser.add_argument("url", help="视频/图文链接")
    parser.add_argument("--api-key", help="API Key（格式 ak_xxx，不传则读取环境变量或配置文件）")
    parser.add_argument("-o", "--output-dir", help="输出目录（默认 ~/Downloads/QoderVideos）")
    parser.add_argument(
        "--save-key",
        action="store_true",
        help="将本次传入的 API Key 保存到配置文件",
    )

    args = parser.parse_args()

    # ── Banner ──
    banner = f"""{CYAN}{BOLD}
  ╔══════════════════════════════════════╗
  ║     Qoder Video Downloader (API)     ║
  ║     视频下载去水印工具          ║
  ╚══════════════════════════════════════╝{RESET}
"""
    print(banner)

    # ── API Key ──
    api_key = require_api_key(cli_key=args.api_key)

    # Save key if requested
    if args.save_key:
        if not args.api_key:
            warn("--save-key 需要同时传入 --api-key")
            sys.exit(1)
        save_api_key(api_key)

    # ── URL ──
    url = args.url.strip().strip('"').strip("'")
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    step(f"URL: {url}")

    # ── URL validation ──
    is_valid, platform = is_valid_share_url(url)
    if not is_valid:
        error("链接格式不支持，无法进行去水印下载")
        show_url_guide()
        sys.exit(1)

    info(f"检测到平台: {platform}")

    # ── Call API ──
    step("Calling redfox.hk API...")

    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "X-API-KEY": api_key,
    })

    try:
        resp = session.post(API_URL, json={"url": url, "source": "短视频下载器-SkillHub"}, timeout=30)
        result = resp.json()
    except requests.exceptions.RequestException as e:
        error(f"API request failed: {e}")
        sys.exit(1)
    except json.JSONDecodeError:
        error(f"API returned invalid JSON: {resp.text[:200]}")
        sys.exit(1)

    code = result.get("code")
    msg = result.get("msg", "")

    # 成功 code 以 2 开头（如 200、2000），其余为错误
    if not str(code).startswith("2"):
        if code == 3106:
            error("缺少 API Key")
        elif code == 3107:
            error("API Key 无效或已失效，请检查是否正确")
            print("  配置方式：export REDFOX_API_KEY=ak_你的密钥")
            print("  获取 Key：https://redfox.hk/settings/api-keys?source=github")
        elif code == 400:
            error(f"请求参数错误: {msg}")
        else:
            error(f"API error (code {code}): {msg}")
        sys.exit(1)

    data = result.get("data")
    if not data:
        error("API returned empty data")
        sys.exit(1)

    aweme_type = data.get("awemeType")
    platform = data.get("platform", "unknown")
    title = data.get("title", "untitled")

    print()
    info(f"Platform: {PLATFORM_MAP.get(platform, platform)}")
    info(f"Title: {title[:80]}")

    # ── Output directory ──
    output_dir = args.output_dir or str(Path.home() / "Downloads" / "QoderVideos")
    os.makedirs(output_dir, exist_ok=True)

    # ── Download ──
    downloaded_files = []

    if aweme_type == "video":
        video_url = data.get("videoUrl")
        if not video_url:
            error("API did not return video URL")
            sys.exit(1)

        safe_title = sanitize_filename(title) or f"video_{platform}"
        filename = f"{safe_title}.mp4"
        filepath = os.path.join(output_dir, filename)

        info(f"Type: Video")
        step("Downloading video...")

        if download_file(session, video_url, filepath):
            downloaded_files.append(filepath)

    elif aweme_type == "photo":
        image_urls = data.get("imageUrls") or []
        if not image_urls:
            error("API did not return image URLs")
            sys.exit(1)

        safe_title = sanitize_filename(title) or f"photo_{platform}"
        total = len(image_urls)
        info(f"Type: Photo (共 {total} 张)")

        for i, img_url in enumerate(image_urls, 1):
            ext = os.path.splitext(img_url.split("?")[0])[1] or ".jpg"
            filename = f"{safe_title}_{i}{ext}"
            filepath = os.path.join(output_dir, filename)

            step(f"Downloading image {i}/{total}...")
            if download_file(session, img_url, filepath):
                downloaded_files.append(filepath)

    else:
        error(f"Unknown awemeType: {aweme_type}")
        sys.exit(1)

    # ── Result ──
    if downloaded_files:
        print(f"\n{GREEN}{BOLD}✓ Download complete!{RESET}")
        for f in downloaded_files:
            size_mb = os.path.getsize(f) / (1024 * 1024)
            print(f"  {f} ({size_mb:.1f} MB)")
        sys.exit(0)
    else:
        print(f"\n{RED}{BOLD}✗ Download failed{RESET}")
        sys.exit(1)


if __name__ == "__main__":
    main()
