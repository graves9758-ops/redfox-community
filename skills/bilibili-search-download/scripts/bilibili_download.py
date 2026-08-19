#!/usr/bin/env python3
"""
B站视频下载脚本
调用红狐 API 获取哔哩哔哩视频下载链接，支持批量下载，结果仅输出到 stdout
用法（单个）: python3 bilibili_download.py --url "https://www.bilibili.com/video/BV1AmSSBMEqo/"
用法（批量）: python3 bilibili_download.py --url "https://www.bilibili.com/video/BVxxx1/" --url "https://www.bilibili.com/video/BVxxx2/"
"""

import sys
import os
import json
import argparse
import urllib.request
import urllib.error

# 修复 Windows 控制台 UTF-8 输出
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

VIDEO_DOWNLOAD_API = "https://redfox.hk/story/api/parseWork/videoDownload/bilibili"


def get_api_key() -> str:
    val = os.environ.get("REDFOX_API_KEY", "")
    if not val:
        print("[error] 未找到环境变量 REDFOX_API_KEY，请确认已设置 API Key", file=sys.stderr)
        print("[hint] 获取 API Key: https://redfox.hk/settings/api-keys?source=github", file=sys.stderr)
        print("[hint] 配置: export REDFOX_API_KEY=ak_xxxx...", file=sys.stderr)
        sys.exit(1)
    return val


def api_request(url: str, payload: dict, api_key: str) -> dict:
    """通用 API 请求函数（POST JSON）"""
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "REDFOX_API_KEY": api_key,
            "User-Agent": "QoderWork/1.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
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
        print(f"[error] API 返回错误: code={code}, msg={result.get('msg', '未知')}", file=sys.stderr)
        sys.exit(1)

    return result.get("data") or {}


def _safe_str(val, default=""):
    if val is None:
        return default
    return str(val)


def _safe_int(val, default=0):
    try:
        return int(val)
    except (TypeError, ValueError):
        return default


def format_resource(raw: dict) -> dict:
    """格式化单个资源条目"""
    return {
        "type": _safe_str(raw.get("type")),
        "cover_url": _safe_str(raw.get("coverUrl")),
        "download_url": _safe_str(raw.get("downloadUrl")),
        "duration_seconds": _safe_int(raw.get("durationSeconds")),
    }


def download_video(video_url: str, api_key: str) -> dict:
    """调用 B站视频下载 API，返回下载信息"""
    payload = {"url": video_url, "source": "B站搜索批量下载-GitHub"}
    data = api_request(VIDEO_DOWNLOAD_API, payload, api_key)

    raw_resources = data.get("resources") or []
    if not isinstance(raw_resources, list):
        raw_resources = []

    resources = [format_resource(r) for r in raw_resources]

    return {
        "request_url": video_url,
        "title": _safe_str(data.get("title")),
        "cover": _safe_str(data.get("cover")),
        "desc": _safe_str(data.get("desc")),
        "video_url": _safe_str(data.get("videoUrl")),
        "resources": resources,
    }


def main():
    parser = argparse.ArgumentParser(description="B站视频下载")
    parser.add_argument("--url", dest="urls", type=str, action="append", required=True,
                        help="B站视频链接，可多次指定用于批量下载（如 --url URL1 --url URL2）")

    args = parser.parse_args()

    api_key = get_api_key()

    results = []
    for url in args.urls:
        video_url = url.strip()
        if not video_url:
            print(f"[warn] 跳过空链接", file=sys.stderr)
            continue
        try:
            result = download_video(video_url, api_key)
            results.append(result)
        except SystemExit:
            results.append({
                "request_url": video_url,
                "error": "下载失败",
            })

    output = {
        "total_requested": len(args.urls),
        "total_success": len([r for r in results if "error" not in r]),
        "results": results,
    }

    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
