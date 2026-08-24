#!/usr/bin/env python3
"""
Qoder Image Generator - 基于 gpt-image-2 的图片生成工具
使用 redfox.hk API 提交图片生成任务并下载结果
支持文生图（generate）和图生图（edit）

Usage:
    python3 imagegen.py "提示词" [options]
    python3 imagegen.py "修改提示词" --image ~/path/to/ref.png
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

import requests

SUBMIT_URL = "https://redfox.hk/story/api/parseWork/imageGen/submitSkill"
RESULT_URL = "https://redfox.hk/story/api/parseWork/imageGen/result"
UPLOAD_URL = "https://redfox.hk/story/api/parseWork/imageGen/uploadImage"
CONFIG_DIR = Path.home() / ".qoder" / "apis"
CONFIG_FILE = CONFIG_DIR / "redfox.json"
ENV_KEY = "REDFOX_API_KEY"
SOURCE = "GPT image2-GitHub"
POLL_INTERVAL = 3  # seconds
MAX_POLL_ATTEMPTS = 60  # max ~3 minutes

# 经过测试验证的分辨率白名单：非白名单分辨率可能导致生成过慢或失败
# 快速档（常规速度）
FAST_SIZES = {"1024x1024", "1024x1536", "1536x1024", "1792x1024", "1024x1792"}
# 高清档（画质更高，生成更慢）
HD_SIZES = {"2048x2048", "2048x1152", "1152x2048"}
ALLOWED_SIZES = FAST_SIZES | HD_SIZES

MAX_PROMPT_LENGTH = 500  # 提示词最大字数限制

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
    """Get API key: CLI arg > env var > config file."""
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


def upload_image(api_key, image_path):
    """Upload a local image file to OSS, return the image URL."""
    image_path = os.path.expanduser(image_path)
    if not os.path.isfile(image_path):
        error(f"Image file not found: {image_path}")
        return None

    # Determine format from extension
    ext = os.path.splitext(image_path)[1].lower()
    fmt_map = {".png": "png", ".jpg": "jpeg", ".jpeg": "jpeg", ".webp": "webp"}
    fmt = fmt_map.get(ext, "png")

    step(f"Uploading image: {image_path}")

    try:
        with open(image_path, "rb") as f:
            files = {"file": (os.path.basename(image_path), f)}
            data = {"format": fmt}
            headers = {"X-API-KEY": api_key}
            resp = requests.post(UPLOAD_URL, files=files, data=data, headers=headers, timeout=60, verify=True)
            result = resp.json()
    except requests.exceptions.RequestException as e:
        error(f"Upload request failed: {e}")
        return None
    except json.JSONDecodeError:
        error(f"Upload returned invalid JSON: {resp.text[:200]}")
        return None

    code = result.get("code")
    if not str(code).startswith("2"):
        error(f"Upload failed (code {code}): {result.get('msg', '')}")
        return None

    data = result.get("data", {})
    image_url = data.get("imageUrl")
    if not image_url:
        error("Upload succeeded but no imageUrl returned")
        return None

    info(f"Upload complete: {image_url}")
    return image_url


def confirm_retry():
    """询问用户是否需要重试。"""
    while True:
        answer = input(f"{YELLOW}[?]{RESET} 是否重试？(y/n): ").strip().lower()
        if answer in ('y', 'yes'):
            return True
        if answer in ('n', 'no'):
            return False


def submit_task(session, prompt, parameters=None, operation="generate", images=None):
    """Submit image generation task, return taskId."""
    payload = {"prompt": prompt, "source": SOURCE, "operation": operation}
    if parameters:
        payload["parameters"] = parameters
    if images:
        payload["images"] = images

    try:
        resp = session.post(SUBMIT_URL, json=payload, timeout=30)
        result = resp.json()
    except requests.exceptions.RequestException as e:
        error(f"API request failed: {e}")
        return None
    except json.JSONDecodeError:
        error(f"API returned invalid JSON: {resp.text[:200]}")
        return None

    code = result.get("code")
    msg = result.get("msg", "")

    if not str(code).startswith("2"):
        error(f"Submit failed (code {code}): {msg}")
        return None

    data = result.get("data")
    if not data or not data.get("taskId"):
        error("API did not return taskId")
        return None

    return data["taskId"]


def poll_result(session, task_id):
    """Poll for task result until success/failed/timeout."""
    for attempt in range(1, MAX_POLL_ATTEMPTS + 1):
        try:
            resp = session.post(RESULT_URL, json={"taskId": task_id}, timeout=15)
            result = resp.json()
        except requests.exceptions.RequestException as e:
            warn(f"Poll request failed (attempt {attempt}): {e}")
            time.sleep(POLL_INTERVAL)
            continue
        except json.JSONDecodeError:
            warn(f"Invalid JSON response (attempt {attempt})")
            time.sleep(POLL_INTERVAL)
            continue

        code = result.get("code")
        if not str(code).startswith("2"):
            error(f"Query failed (code {code}): {result.get('msg', '')}")
            return None

        data = result.get("data", {})
        status = data.get("status")

        if status == "success":
            return data.get("imagePaths", [])
        elif status == "failed":
            reason = data.get("failReason", "unknown")
            error(f"Generation failed: {reason}")
            return None
        else:
            # still pending
            elapsed = attempt * POLL_INTERVAL
            print(f"\r  {CYAN}⏳ Generating... ({elapsed}s){RESET}", end="", flush=True)
            time.sleep(POLL_INTERVAL)

    print()
    error("Timeout: task did not complete within expected time")
    return None


def download_images(session, image_urls, output_dir, prefix="image"):
    """Download generated images to output directory."""
    downloaded = []
    total = len(image_urls)

    for i, url in enumerate(image_urls, 1):
        # Determine extension from URL
        ext = ".png"
        url_path = url.split("?")[0]
        for fmt in [".png", ".jpg", ".jpeg", ".webp"]:
            if url_path.lower().endswith(fmt):
                ext = fmt
                break

        filename = f"{prefix}_{i}{ext}" if total > 1 else f"{prefix}{ext}"
        filepath = os.path.join(output_dir, filename)

        step(f"Downloading {i}/{total}: {filename}")
        try:
            resp = session.get(url, stream=True, timeout=120)
            resp.raise_for_status()
            total_size = int(resp.headers.get("content-length", 0))
            dl = 0
            with open(filepath, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        dl += len(chunk)
                        if total_size > 0:
                            pct = int(dl * 100 / total_size)
                            bar = "█" * (pct // 5) + "░" * (20 - pct // 5)
                            print(f"\r  {bar} {pct}%", end="", flush=True)
            print()
            downloaded.append(filepath)
        except requests.exceptions.RequestException as e:
            error(f"Download failed: {e}")

    return downloaded


def main():
    parser = argparse.ArgumentParser(
        description="AI 图片生成器 - 基于 gpt-image-2 模型，支持文生图与图生图",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # 文生图
  python3 imagegen.py "一只橘色的猫咪坐在窗台上看着窗外的夕阳"
  python3 imagegen.py "futuristic city" --size 1792x1024 --quality medium
  python3 imagegen.py "logo design" -n 4 --format webp --bg transparent

  # 图生图（上传参考图 + 修改提示词）
  python3 imagegen.py "把猫咪改成白色，背景换成星空" --image ~/Pictures/cat.png
  python3 imagegen.py "改成赛博朋克风格" --image ref.jpg --fidelity high
        """,
    )
    parser.add_argument("prompt", help="图片生成/编辑提示词 (最多 500 字)")
    parser.add_argument("--api-key", help="API Key (不传则读取环境变量或配置文件)")
    parser.add_argument("-o", "--output-dir", help="输出目录 (默认 ~/Downloads/QoderImages)")
    parser.add_argument("-n", "--count", type=int, default=1, help="生成图片数量 (1-10, 默认 1)")
    parser.add_argument("--size", default="1024x1792",
                        help="图片尺寸 (默认 1024x1792, 可选: 1024x1024/1024x1536/1536x1024/1792x1024/1024x1792/2048x2048/2048x1152/1152x2048)")
    parser.add_argument("--quality", default="medium", choices=["low", "medium", "high", "auto"],
                        help="图片质量 (默认 medium)")
    parser.add_argument("--format", default="png", choices=["png", "jpeg", "webp"],
                        help="输出格式 (默认 png)")
    parser.add_argument("--bg", "--background", default="auto", choices=["transparent", "opaque", "auto"],
                        help="背景类型 (默认 auto)")
    parser.add_argument("--compression", type=int, default=0,
                        help="压缩比例 0-100 (默认 0, 无压缩)")
    parser.add_argument("--image", help="参考图片路径 (启用图生图 edit 模式)")
    parser.add_argument("--fidelity", choices=["high", "low"],
                        help="输入图保真度 (仅图生图模式, high=高保真/low=低保真)")
    parser.add_argument("--no-download", action="store_true",
                        help="仅提交任务并返回 taskId, 不等待结果")
    parser.add_argument("--task-id", help="直接查询已有任务的结果 (跳过提交)")
    parser.add_argument("--prefix", default="image", help="下载文件名前缀 (默认 image)")

    args = parser.parse_args()

    # ── Validate size ──
    if args.size not in ALLOWED_SIZES:
        error(f"当前比例暂不支持: {args.size}")
        print(f"  该分辨率会影响生图速度，可能导致生成失败。请使用以下尺寸：")
        print(f"  快速档: {', '.join(sorted(FAST_SIZES))}")
        print(f"  高清档（画质更高，生成更慢）: {', '.join(sorted(HD_SIZES))}")
        sys.exit(1)

    # ── Validate prompt length ──
    if len(args.prompt) > MAX_PROMPT_LENGTH:
        error(f"提示词过长 ({len(args.prompt)} 字)，请控制在 {MAX_PROMPT_LENGTH} 字以内")
        sys.exit(1)

    # ── Banner ──
    banner = f"""{CYAN}{BOLD}
  ╔══════════════════════════════════════╗
  ║     Qoder Image Generator (API)      ║
  ║     AI 图片生成工具 · gpt-image-2    ║
  ╚══════════════════════════════════════╝{RESET}
"""
    print(banner)

    # ── API Key ──
    api_key = get_api_key(cli_key=args.api_key)
    if not api_key:
        error("未找到 API Key，请设置环境变量 REDFOX_API_KEY 或使用 --api-key 参数")
        print(f"  获取 Key: https://redfox.hk/settings/api-keys?source=github")
        sys.exit(1)

    # ── Session (all requests use HTTPS with SSL verification) ──
    session = requests.Session()
    session.verify = True
    session.headers.update({
        "Content-Type": "application/json",
        "X-API-KEY": api_key,
    })

    # ── Mode: Query existing task ──
    if args.task_id:
        step(f"Querying task: {args.task_id}")
        image_urls = poll_result(session, args.task_id)
        if not image_urls:
            sys.exit(1)
        print()
        info(f"Generated {len(image_urls)} image(s)")
        output_dir = args.output_dir or str(Path.home() / "Downloads" / "QoderImages")
        os.makedirs(output_dir, exist_ok=True)
        downloaded = download_images(session, image_urls, output_dir, args.prefix)
        if downloaded:
            print(f"\n{GREEN}{BOLD}✓ Done!{RESET}")
            for f in downloaded:
                size_kb = os.path.getsize(f) / 1024
                print(f"  {f} ({size_kb:.1f} KB)")
        sys.exit(0)

    # ── Mode: Submit new task ──
    prompt = args.prompt.strip()
    if not prompt:
        error("提示词不能为空")
        sys.exit(1)

    # Determine operation mode
    operation = "generate"
    images = None

    if args.image:
        # Image-to-image: upload reference image first
        operation = "edit"
        image_url = upload_image(api_key, args.image)
        if not image_url:
            sys.exit(1)
        images = [{"url": image_url}]
        step(f"Mode: 图生图 (edit)")
    else:
        step(f"Mode: 文生图 (generate)")

    step(f"Prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")

    # Build parameters
    parameters = {
        "modelName": "gpt-image-2",
        "n": max(1, min(10, args.count)),
        "size": args.size,
        "quality": args.quality,
        "outputFormat": args.format,
        "background": args.bg,
        "outputCompression": max(0, min(100, args.compression)),
    }

    # Add fidelity for edit mode
    if operation == "edit" and args.fidelity:
        parameters["inputFidelity"] = args.fidelity

    step(f"Parameters: {args.size}, quality={args.quality}, n={parameters['n']}, format={args.format}")

    # Submit
    while True:
        step("Submitting task...")
        task_id = submit_task(session, prompt, parameters, operation, images)
        if task_id:
            break
        if not confirm_retry():
            sys.exit(1)

    info(f"Task submitted: {task_id}")

    if args.no_download:
        print(f"\n{GREEN}{BOLD}✓ Task submitted successfully{RESET}")
        print(f"  taskId: {task_id}")
        print(f"  查询命令: python3 imagegen.py \"\" --task-id {task_id}")
        sys.exit(0)

    # Poll for result
    step("Waiting for generation...")
    image_urls = poll_result(session, task_id)
    if not image_urls:
        sys.exit(1)

    print()
    info(f"Generated {len(image_urls)} image(s)")

    # Download
    output_dir = args.output_dir or str(Path.home() / "Downloads" / "QoderImages")
    os.makedirs(output_dir, exist_ok=True)

    downloaded = download_images(session, image_urls, output_dir, args.prefix)

    if downloaded:
        print(f"\n{GREEN}{BOLD}✓ Done!{RESET}")
        for f in downloaded:
            size_kb = os.path.getsize(f) / 1024
            print(f"  {f} ({size_kb:.1f} KB)")
        sys.exit(0)
    else:
        print(f"\n{RED}{BOLD}✗ Download failed{RESET}")
        sys.exit(1)


if __name__ == "__main__":
    main()
