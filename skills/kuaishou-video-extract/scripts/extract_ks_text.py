#!/usr/bin/env python3
"""
快手视频提文案脚本（广域库）
两步流程：
  1. 提交任务: POST /story/api/parseWork/audioTextExtract/submit/kuaishou
     输入快手视频链接，返回 taskId
  2. 查询结果: POST /story/api/parseWork/audioTextExtract/result/kuaishou
     根据 taskId 轮询，直到 succeeded（完整文案 text + 带时间戳分句 stampSents）
用法:
  python3 extract_ks_text.py "<视频链接>"
  python3 extract_ks_text.py "<视频链接>" --interval 3 --timeout 120
  python3 extract_ks_text.py --task-id "<taskId>"   # 仅查询已有任务结果
"""

import sys
import os
import json
import time as _time
import argparse
import urllib.request
import urllib.error

SUBMIT_URL = "https://redfox.hk/story/api/parseWork/audioTextExtract/submit/kuaishou"
RESULT_URL = "https://redfox.hk/story/api/parseWork/audioTextExtract/result/kuaishou"
SOURCE = "快手视频提文案-GitHub"


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

def post_json(url: str, payload: dict, timeout: int = 30) -> dict:
    """POST JSON 请求并返回解析后的响应体。"""
    api_key = get_api_key()
    req = urllib.request.Request(
        url,
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
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"[error] HTTP {e.code}: {body}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"[error] 网络请求失败: {e.reason}", file=sys.stderr)
        sys.exit(1)
    except (json.JSONDecodeError, TypeError) as e:
        print(f"[error] 数据解析异常: {e}", file=sys.stderr)
        sys.exit(1)


def check_resp(result: dict):
    """校验统一包装 code，非 2000 直接退出。"""
    code = result.get("code")
    if code != 2000:
        print(f"[error] 接口返回错误: code={code}, msg={result.get('msg', '未知')}", file=sys.stderr)
        sys.exit(1)


def submit_task(video_url: str) -> str:
    """提交视频链接，返回任务 ID。"""
    result = post_json(SUBMIT_URL, {"url": video_url, "source": SOURCE})
    check_resp(result)
    data = result.get("data") or {}
    task_id = data.get("taskId") or ""
    if not task_id:
        print("[error] 接口未返回 taskId", file=sys.stderr)
        sys.exit(1)
    return task_id


def query_result(task_id: str) -> dict:
    """按任务 ID 查询一次提取结果。"""
    result = post_json(RESULT_URL, {"taskId": task_id, "source": SOURCE})
    check_resp(result)
    data = result.get("data")
    if not data or not isinstance(data, dict):
        print("[error] 接口未返回任务结果数据（data 为空）", file=sys.stderr)
        sys.exit(1)
    return data


def format_ms(ms) -> str:
    """毫秒转可读时间，如 2200 -> 2.20s / 73948 -> 1:13.95。"""
    try:
        ms = int(ms or 0)
    except (ValueError, TypeError):
        return "-"
    if ms < 0:
        return "-"
    sec = ms / 1000.0
    if sec < 60:
        return f"{sec:.2f}s"
    m, s = divmod(int(round(sec)), 60)
    return f"{m}:{s:02d}"


def main():
    parser = argparse.ArgumentParser(description="快手视频提文案（广域库）：提交视频链接提取完整文案与时间戳分句")
    parser.add_argument("url", nargs="?", help="快手视频分享链接（与 --task-id 二选一）")
    parser.add_argument("--task-id", dest="task_id", help="直接查询已有任务结果（不提交新任务）")
    parser.add_argument("--interval", type=float, default=3.0, help="轮询间隔秒数（默认 3）")
    parser.add_argument("--timeout", type=float, default=120.0, help="轮询总超时秒数（默认 120，超过则返回当前状态）")
    args = parser.parse_args()

    # 模式一：直接查询已有任务
    if args.task_id:
        task_id = args.task_id.strip()
        if not task_id:
            print("[error] taskId 不能为空", file=sys.stderr)
            sys.exit(1)
        data = query_result(task_id)
        out = {
            "task_id":    task_id,
            "status":     data.get("status") or "",
            "fail_reason": data.get("failReason"),
            "text":       data.get("text") or "",
            "stamp_sents": data.get("stampSents") or [],
        }
        print(json.dumps(out, ensure_ascii=False, indent=2))
        sys.exit(0 if (out["status"] == "succeeded") else 1)

    # 模式二：提交任务并轮询
    if not args.url:
        parser.print_help()
        sys.exit(1)

    video_url = args.url.strip()
    if not video_url.startswith("http"):
        print(f"[error] 视频链接格式不正确: {video_url}", file=sys.stderr)
        sys.exit(1)

    # Step 1: 提交任务
    task_id = submit_task(video_url)
    print(f"[info] 任务提交成功，taskId={task_id}，开始轮询结果...", file=sys.stderr)

    # Step 2: 轮询结果
    deadline = _time.time() + args.timeout
    last_data = None
    while _time.time() < deadline:
        data = query_result(task_id)
        last_data = data
        status = data.get("status") or ""
        if status == "succeeded":
            print("[info] 提取成功", file=sys.stderr)
            break
        if status == "failed":
            print(f"[error] 提取失败: {data.get('failReason')}", file=sys.stderr)
            sys.exit(1)
        # 其余状态（processing / asr_processing / pending 等）一律视为处理中，继续轮询
        print(f"[info] 处理中（{status}）... {_time.strftime('%H:%M:%S')}", file=sys.stderr)
        _time.sleep(args.interval)
    else:
        print(f"[warn] 轮询超时（{args.timeout}s），返回当前任务状态，可稍后用 --task-id 继续查询", file=sys.stderr)

    if not last_data:
        print("[error] 未获取到任务状态", file=sys.stderr)
        sys.exit(1)

    stamp_sents = last_data.get("stampSents") or []
    out = {
        "url":         video_url,
        "task_id":     task_id,
        "status":      last_data.get("status") or "",
        "fail_reason": last_data.get("failReason"),
        "text":        last_data.get("text") or "",
        "stamp_sents": [
            {
                "text":  s.get("textSeg") or "",
                "start": s.get("start"),
                "end":   s.get("end"),
                "start_fmt": format_ms(s.get("start")),
                "end_fmt":   format_ms(s.get("end")),
            }
            for s in stamp_sents
        ],
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
