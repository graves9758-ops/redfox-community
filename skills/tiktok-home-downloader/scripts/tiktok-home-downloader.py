#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TikTok 主页视频批量提取 — 根据 TikTok 账号（主页链接 / @handle / secUserId）
拉取主页作品列表，解析无水印下载链接，批量下载到本地
================================================================================
基于 redfox.hk API：
  1. POST /story/api/tiktok/ability/userAwemeList       — 拉取用户主页作品数据
  2. POST /story/api/parseWork/videoDownload/tiktok     — 解析视频下载链接

Usage:
    # 拉取作品并展示下载链接（不下载文件）
    python3 tiktok-home-downloader.py --account "https://www.tiktok.com/@tiktok"

    # 下载视频到本地
    python3 tiktok-home-downloader.py --account "@tiktok" --download

    # 多账号 + 指定数量
    python3 tiktok-home-downloader.py --accounts "@tiktok,MS4wLjABxxxx" --count 20 --download

    # JSON 输出
    python3 tiktok-home-downloader.py --account "@tiktok" --json
"""

import argparse
import json
import os
import re
import sys
import time
import warnings
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import unquote, urlparse, parse_qs

# Windows 终端 UTF-8 编码修复
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import requests

warnings.filterwarnings("ignore", category=Warning)
warnings.filterwarnings("ignore", message=".*NotOpenSSLWarning.*")

# ─── 配置 ─────────────────────────────────────────────────────────────────────────
API_BASE = "https://redfox.hk"
WORKS_ENDPOINT = "/story/api/tiktok/ability/userAwemeList"
DOWNLOAD_ENDPOINT = "/story/api/parseWork/videoDownload/tiktok"

ENV_KEY = "REDFOX_API_KEY"
CONFIG_FILE = Path.home() / ".qoder" / "apis" / "redfox.json"

# 接口调用来源标识（随每次 API 请求上送）
REQUEST_SOURCE = "TikTok主页视频批量提取-GitHub"

DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 50
DEFAULT_RATE_LIMIT = 1.0

# 浏览器 UA（用于从主页链接解析 secUserId）
BROWSER_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)

# ─── 失败阈值保护配置 ────────────────────────────────────────────────────────────
FAILURES_FILE = Path.home() / ".qoder" / "tiktok-home-downloader_failures.json"
RATE_LIMIT_MAX_FAILURES = 5      # 6 小时内累计失败次数上限
RATE_LIMIT_WINDOW_HOURS = 6      # 失败计数窗口
SUPPORT_EMAIL = "redfoxdata@proton.me"

# ─── 终端颜色 ──────────────────────────────────────────────────────────────────────
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


def info(msg: str):
    print(f"{GREEN}[OK]{RESET} {msg}")


def warn(msg: str):
    print(f"{YELLOW}[!!]{RESET} {msg}")


def error(msg: str):
    print(f"{RED}[XX]{RESET} {msg}")


def step(msg: str):
    print(f"{CYAN}[>>]{RESET} {msg}")


# ─── API Key 管理 ──────────────────────────────────────────────────────────────────
def get_api_key(cli_key: Optional[str] = None) -> Optional[str]:
    """获取 API Key：CLI > 环境变量 > 配置文件"""
    if cli_key:
        return cli_key
    env_key = os.environ.get(ENV_KEY)
    if env_key:
        return env_key
    if CONFIG_FILE.exists():
        try:
            data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            key = data.get("api_key")
            if key:
                return key
        except (json.JSONDecodeError, OSError):
            pass
    return None


# ─── 数字格式化 ────────────────────────────────────────────────────────────────────
def format_number(n) -> str:
    """格式化数字: ≥1亿→x.x亿, ≥1万→x.xw, ≥1千→x.xk, 其余逗号分隔"""
    if n is None:
        return "-"
    try:
        n = int(n)
    except (ValueError, TypeError):
        return str(n)
    if n >= 100000000:
        return f"{n / 100000000:.1f}亿"
    if n >= 10000:
        return f"{n / 10000:.1f}w"
    if n >= 1000:
        return f"{n / 1000:.1f}k"
    return f"{n:,}"


def ts_to_date(ts) -> str:
    """秒级时间戳 → YYYY-MM-DD，失败返回空串"""
    if not ts:
        return ""
    try:
        return datetime.fromtimestamp(int(ts)).strftime("%Y-%m-%d")
    except (ValueError, TypeError, OSError):
        return ""


# ─── TikTok 账号输入识别 ──────────────────────────────────────────────────────────
def _is_chinese(text: str) -> bool:
    """判断输入是否包含中文字符（说明可能是昵称而非账号标识）"""
    return bool(re.search(r'[\u4e00-\u9fff]', text))


SEC_USER_ID_PATTERN = re.compile(r'^MS4w[A-Za-z0-9_\-]{20,}$')
HANDLE_PATTERN = re.compile(r'^@?[A-Za-z0-9][A-Za-z0-9._]{0,60}$')

# secUserId 不正确时返回的获取方式指引
SEC_USER_ID_GUIDE = (
    "secUserId 获取方式（secUserId 为 MS4w 开头的完整长串）：\n"
    "    方法一（推荐）：打开手机 TikTok App → 进入账号主页 → 「分享」→「复制链接」，\n"
    "      分享链接中自带 sec_uid=MS4w... 参数（注意：分享链接需要带上 sec_uid=MS4w... 参数），\n"
    "      直接把完整分享链接提供给技能即可\n"
    "    方法二：在能打开 TikTok 的网络环境下访问账号主页 → Ctrl+U 查看页面源码 →\n"
    "      Ctrl+F 搜索 secUid，\"secUid\":\"MS4w...\" 引号中的完整长串即为 secUserId\n"
    "    方法三：主页按 F12 打开开发者工具 → Console 执行：\n"
    "      JSON.parse(document.getElementById('__UNIVERSAL_DATA_FOR_REHYDRATION__').textContent)"
    ".__DEFAULT_SCOPE__['webapp.user-detail'].userInfo.user.secUid"
)


def resolve_sec_user_id(raw: str) -> tuple[str, str]:
    """
    将用户输入解析为 secUserId。

    支持输入：
      - secUserId（MS4w 开头的长串）
      - TikTok 主页链接（https://www.tiktok.com/@handle）
      - @handle 或 handle

    Returns:
        (sec_user_id, error_message)  # 成功时 error_message 为空
    """
    text = raw.strip().strip('"').strip("'")

    # 1) 已是 secUserId
    if SEC_USER_ID_PATTERN.match(text):
        return text, ""

    # 1.1) 疑似 secUserId 但格式不正确 → 返回获取方式指引
    if text.startswith("MS4w"):
        return "", (
            f"「{text}」不是有效的 secUserId（应为 MS4w 开头的完整长串，请检查是否复制完整）。\n\n"
            f"{SEC_USER_ID_GUIDE}"
        )

    # 2) URL 输入
    if text.lower().startswith(("http://", "https://")):
        # 2.0) 分享链接优先：URL 参数中已带 sec_uid 时无需访问页面，直接提取
        try:
            qs_input = parse_qs(urlparse(text).query)
            sec_uid_input = (qs_input.get("sec_uid") or qs_input.get("secUid") or [None])[0]
            if sec_uid_input:
                if SEC_USER_ID_PATTERN.match(sec_uid_input):
                    return sec_uid_input, ""
                return "", (
                    f"链接中的 sec_uid 参数「{sec_uid_input}」不是有效的 secUserId。\n\n"
                    f"{SEC_USER_ID_GUIDE}"
                )
        except ValueError:
            pass

        try:
            resp = requests.get(text, headers={"User-Agent": BROWSER_UA},
                                timeout=30, allow_redirects=True)
            final_url = resp.url
            html = resp.text
        except requests.exceptions.RequestException as e:
            return "", (
                f"访问主页链接失败: {e}，请检查链接是否正确或稍后重试。\n"
                "提示：分享链接需要带上 sec_uid=MS4w... 参数——请在手机 TikTok App 中进入账号主页 →"
                "「分享」→「复制链接」，带 sec_uid 参数的分享链接可以直接查询，无需访问页面。"
            )

        parsed = urlparse(final_url)
        host = (parsed.netloc or "").lower()
        if "tiktok.com" not in host:
            return "", "该链接不是 TikTok 主页链接，请提供 TikTok 账号主页链接（如 https://www.tiktok.com/@tiktok）"

        # 视频链接 → 提示提供主页链接
        if "/video/" in parsed.path:
            return "", (
                "检测到您输入的是单条视频链接。本技能用于提取账号主页全部作品，"
                "请提供 TikTok 账号**主页链接**（如 https://www.tiktok.com/@tiktok）"
            )

        # URL 参数中的 sec_uid
        qs = parse_qs(parsed.query)
        sec_uid = (qs.get("sec_uid") or qs.get("secUid") or [None])[0]
        if sec_uid:
            if SEC_USER_ID_PATTERN.match(sec_uid):
                return sec_uid, ""
            return "", (
                f"链接中的 sec_uid 参数「{sec_uid}」不是有效的 secUserId。\n\n"
                f"{SEC_USER_ID_GUIDE}"
            )

        # 从页面 HTML 中提取 secUid
        m = re.search(r'"secUid"\s*:\s*"(MS4w[^"]+)"', html) or \
            re.search(r'"sec_uid"\s*:\s*"(MS4w[^"]+)"', html)
        if m:
            return m.group(1), ""

        return "", (
            "无法从该主页链接解析出账号标识（可能是地区限制或页面反爬）。\n"
            "提示：分享链接需要带上 sec_uid=MS4w... 参数——请在手机 TikTok App 中进入账号主页 →"
            "「分享」→「复制链接」，把带 sec_uid 参数的分享链接直接提供给技能即可；"
            "也可直接提供该账号的 secUserId"
        )

    # 3) @handle / handle
    if HANDLE_PATTERN.match(text):
        handle = text.lstrip("@")
        profile_url = f"https://www.tiktok.com/@{handle}"
        sec_uid, err = resolve_sec_user_id(profile_url)
        if err:
            return "", err
        return sec_uid, ""

    # 4) 中文昵称
    if _is_chinese(text):
        return "", (
            f"「{text}」看起来是账号昵称。TikTok 账号昵称存在多个重名情况，"
            "请提供准确的 TikTok 账号**主页链接**（如 https://www.tiktok.com/@tiktok）"
            "或主页 URL 中的账号 handle（如 @tiktok）"
        )

    return "", f"「{text}」无法识别，请提供 TikTok 主页链接、@handle 或 secUserId"


# ─── 失败计数 / 频率限制 ────────────────────────────────────────────────────────
def _load_failures() -> dict:
    """加载失败记录"""
    if FAILURES_FILE.exists():
        try:
            return json.loads(FAILURES_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def _save_failures(failures: dict):
    """保存失败记录"""
    FAILURES_FILE.parent.mkdir(parents=True, exist_ok=True)
    FAILURES_FILE.write_text(json.dumps(failures, ensure_ascii=False, indent=2), encoding="utf-8")


def _check_rate_limit(account_id: str) -> tuple[bool, str]:
    """
    检查是否超过失败阈值（6h 内 5 次失败）。

    Returns:
        (blocked: bool, message: str)
    """
    failures = _load_failures()
    key = account_id.strip().lower()
    record = failures.get(key)
    if not record:
        return False, ""

    last_fail_time = record.get("lastFailTime", 0)
    fail_count = record.get("count", 0)

    # 距上次失败超过窗口时间，计数归零
    if time.time() - last_fail_time > RATE_LIMIT_WINDOW_HOURS * 3600:
        del failures[key]
        _save_failures(failures)
        return False, ""

    # 窗口内失败达上限，拒绝调用
    if fail_count >= RATE_LIMIT_MAX_FAILURES:
        return True, (
            f"当前账号下载已超过失败阈值，"
            f"请联系客服邮箱 {SUPPORT_EMAIL} 处理"
        )

    return False, ""


def _record_failure(account_id: str):
    """记录一次失败"""
    failures = _load_failures()
    key = account_id.strip().lower()
    record = failures.get(key, {"count": 0, "lastFailTime": 0})

    # 距上次失败超过窗口，重置计数
    if time.time() - record.get("lastFailTime", 0) > RATE_LIMIT_WINDOW_HOURS * 3600:
        record = {"count": 0, "lastFailTime": 0}

    record["count"] += 1
    record["lastFailTime"] = time.time()
    failures[key] = record
    _save_failures(failures)


def _record_success(account_id: str):
    """成功后计数归零"""
    failures = _load_failures()
    key = account_id.strip().lower()
    if key in failures:
        del failures[key]
        _save_failures(failures)


# ─── 文件名清理 ────────────────────────────────────────────────────────────────────
def safe_filename(text: str) -> str:
    """将文本转为安全的文件名（去除非法字符、限制长度）"""
    text = re.sub(r'[\\/:*?"<>|\n\r\t]', '_', text)
    text = text.strip().strip('.')
    if len(text) > 80:
        text = text[:80]
    return text or "video"


# ─── 核心提取器类 ──────────────────────────────────────────────────────────────────
class TikTokHomeVideoExtractor:
    """TikTok 主页视频批量提取器"""

    def __init__(self, api_key: str):
        self.api_key = api_key

    # ── 作品拉取 ────────────────────────────────────────────────────────────────

    def fetch_works(self, sec_user_id: str) -> dict:
        """
        拉取 TikTok 用户主页作品列表

        Args:
            sec_user_id: 用户 secUserId

        Returns:
            dict: {
                "success": bool,
                "account": dict | None,
                "works": list,
                "error": str | None,
                "rate_limited": bool  # 是否因失败阈值被拒绝
            }
        """
        # 规则：失败阈值检查
        blocked, block_msg = _check_rate_limit(sec_user_id)
        if blocked:
            return {"success": False, "account": None, "works": [],
                    "error": block_msg, "rate_limited": True}

        payload = {"secUserId": sec_user_id, "source": REQUEST_SOURCE}

        url = f"{API_BASE}{WORKS_ENDPOINT}"
        headers = {
            "Content-Type": "application/json",
            "REDFOX_API_KEY": self.api_key,
        }

        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=60)
            result = resp.json()
        except requests.exceptions.Timeout:
            _record_failure(sec_user_id)
            return {"success": False, "account": None, "works": [], "error": "请求超时，请稍后重试"}
        except requests.exceptions.RequestException as e:
            _record_failure(sec_user_id)
            return {"success": False, "account": None, "works": [], "error": f"网络请求失败: {e}"}
        except json.JSONDecodeError:
            _record_failure(sec_user_id)
            return {"success": False, "account": None, "works": [], "error": "API 返回无效数据"}

        code = result.get("code")
        msg = result.get("msg", "")

        # 成功码：200 或 2000
        if code in (200, 2000):
            data_raw = result.get("data", [])
            if not data_raw:
                return {"success": False, "account": None, "works": [],
                        "error": ("未查询到该账号的作品数据，请确认 secUserId 是否正确、是否复制完整。\n"
                                  f"{SEC_USER_ID_GUIDE}")}

            # data 可能是 list 或 dict
            if isinstance(data_raw, list):
                works = data_raw
            elif isinstance(data_raw, dict):
                works = data_raw.get("list") or data_raw.get("records") or []
            else:
                works = []

            # 提取账号信息（从第一条作品的 authorData 中）
            account_info = {"accountId": sec_user_id}
            if works:
                author = works[0].get("authorData") or {}
                account_info["accountName"] = author.get("userName") or author.get("userHandle") or sec_user_id
                account_info["userHandle"] = author.get("userHandle", "")
                account_info["followerCount"] = author.get("fansCount", 0)
                account_info["workCount"] = author.get("workCount", 0)
                account_info["userSignature"] = author.get("userSignature", "")
                account_info["userArea"] = author.get("userArea", "")

            # 映射字段（统一键名）
            for w in works:
                stats = w.get("statsData") or {}
                video = w.get("videoData") or {}
                w["title"] = w.get("content") or ""
                w["workUrl"] = w.get("shareLink") or ""
                w["publishDate"] = ts_to_date(w.get("publishTime"))
                w["likeCount"] = stats.get("likeCount", 0)
                w["commentCount"] = stats.get("commentTotal", 0)
                w["collectCount"] = stats.get("favoriteCount", 0)
                w["shareCount"] = stats.get("shareTotal", 0)
                w["viewCount"] = stats.get("viewCount", 0)
                # 列表接口自带的无水印直链（解析失败时的兜底）
                w["noMarkUrl"] = video.get("downloadNoMarkAddress") or video.get("playAddress") or ""
                w["listCover"] = video.get("coverImage") or ""
                w["isPhoto"] = (w.get("mediaType") == "photo")

            # 按发布时间倒序
            works.sort(key=lambda w: w.get("publishTime") or 0, reverse=True)

            # 成功：失败计数归零
            _record_success(sec_user_id)

            return {
                "success": True,
                "account": account_info,
                "works": works,
                "error": None,
            }

        # 错误码处理
        _record_failure(sec_user_id)
        if code == 3108:
            return {"success": False, "account": None, "works": [],
                    "error": "调用频率超限，请稍后重试或增加 --rate-limit 参数"}
        if code in (3106, 3107):
            return {"success": False, "account": None, "works": [],
                    "error": f"API Key 无效 (code {code})，请检查配置"}
        if code == 400:
            return {"success": False, "account": None, "works": [],
                    "error": f"请求参数错误: {msg}"}

        return {"success": False, "account": None, "works": [],
                "error": f"API 错误 (code {code}): {msg}"}

    # ── 视频解析 ────────────────────────────────────────────────────────────────

    def get_download_info(self, work_url: str) -> dict:
        """
        解析视频下载链接

        Args:
            work_url: 作品链接（shareLink）

        Returns:
            dict: {"success": bool, "download_url": str|None, "title": str|None,
                   "cover": str|None, "duration": int|None, "resources": list, "error": str|None}
        """
        payload = {"url": work_url, "source": REQUEST_SOURCE}
        url = f"{API_BASE}{DOWNLOAD_ENDPOINT}"
        headers = {
            "Content-Type": "application/json",
            "REDFOX_API_KEY": self.api_key,
        }

        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=30)
            data = resp.json()
        except requests.exceptions.Timeout:
            return {"success": False, "download_url": None, "title": None, "cover": None,
                    "duration": None, "resources": [], "error": "解析超时"}
        except requests.exceptions.RequestException as e:
            return {"success": False, "download_url": None, "title": None, "cover": None,
                    "duration": None, "resources": [], "error": f"网络请求失败: {e}"}
        except json.JSONDecodeError:
            return {"success": False, "download_url": None, "title": None, "cover": None,
                    "duration": None, "resources": [], "error": "API 返回无效数据"}

        code = data.get("code")
        msg = data.get("msg", "")

        if not str(code).startswith("2"):
            if code == 3108:
                err = "调用频率超限"
            elif code in (3106, 3107):
                err = "API Key 无效"
            elif code == 400:
                err = f"参数错误: {msg}"
            else:
                err = f"API 错误 (code {code}): {msg}"
            return {"success": False, "download_url": None, "title": None, "cover": None,
                    "duration": None, "resources": [], "error": err}

        payload_data = data.get("data")
        if not payload_data:
            return {"success": False, "download_url": None, "title": None, "cover": None,
                    "duration": None, "resources": [], "error": "API 返回空数据"}

        result = {
            "success": True,
            "download_url": None,
            "title": None,
            "cover": None,
            "duration": None,
            "resources": [],
            "error": None,
        }

        if isinstance(payload_data, dict):
            result["title"] = payload_data.get("title") or payload_data.get("desc")
            result["cover"] = payload_data.get("cover")

            # 提取 resources 列表
            resources = payload_data.get("resources", [])
            if isinstance(resources, list):
                result["resources"] = resources
                for res in resources:
                    if isinstance(res, dict):
                        rtype = res.get("type", "")
                        dl = res.get("downloadUrl") or res.get("url")
                        # 视频类型：提取下载链接
                        if dl and rtype == "video" and not result["download_url"]:
                            result["download_url"] = dl
                        # 图片类型：提取封面 + 下载链接（图文作品可下载首图）
                        if dl and rtype == "image":
                            if not result["cover"]:
                                result["cover"] = dl
                            if not result["download_url"]:
                                result["download_url"] = dl
                        res_dur = res.get("durationSeconds")
                        if isinstance(res_dur, (int, float)) and not result["duration"]:
                            result["duration"] = int(res_dur)

            # 如果 resources 中没有，使用顶层字段
            if not result["download_url"]:
                result["download_url"] = (
                    payload_data.get("videoUrl")
                    or payload_data.get("video_url")
                    or payload_data.get("downloadUrl")
                    or payload_data.get("download_url")
                )

        return result

    # ── 视频下载 ────────────────────────────────────────────────────────────────

    def download_video(self, download_url: str, output_path: str) -> bool:
        """
        下载视频文件到本地

        Args:
            download_url: 视频下载直链
            output_path: 保存路径

        Returns:
            bool: 是否下载成功
        """
        try:
            resp = requests.get(download_url, timeout=120, stream=True)
            resp.raise_for_status()

            total = int(resp.headers.get("content-length", 0))
            downloaded = 0

            with open(output_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)

            # 验证文件大小
            if total > 0 and downloaded < total * 0.9:
                warn(f"  文件可能不完整: {downloaded}/{total} bytes")
                return False

            return True
        except requests.exceptions.RequestException as e:
            error(f"  下载失败: {e}")
            return False
        except OSError as e:
            error(f"  文件写入失败: {e}")
            return False


# ─── Markdown 输出 ────────────────────────────────────────────────────────────────

def print_markdown_table(account: dict, results: list[dict], page_num: int = 1,
                         page_size: int = DEFAULT_PAGE_SIZE, total_works: int = 0):
    """
    输出 Markdown 格式的结果表格

    ⛔ 强制规则：Agent 调用方必须原样展示本函数的完整输出，禁止以下行为：
    - 禁止删除或合并任何列（#、发布时间、作品、播放、赞、评论、收藏、分享、资源下载 缺一不可）
    - 禁止省略翻页提示行
    - 禁止省略时间范围筛选提示和下载询问提示
    - 禁止用「...」或摘要代替完整表格内容
    - 必须逐行展示所有作品信息（含完整资源下载链接）
    """
    name = account.get("accountName", account.get("accountId", "未知"))
    fans = format_number(account.get("followerCount"))

    print(f"\n## 📥 TikTok 视频下载 — @{name}（粉丝: {fans}）")
    print()
    # 翻页信息
    total = len(results)
    page_info = f"当前是**第 {page_num} 页**，共 {total} 条作品"
    shown_end = page_num * page_size
    if total_works > shown_end:
        next_page = page_num + 1
        page_info += f" | 还有更多作品（共 {total_works} 条），输入 `--page {next_page}` 翻看下一页"
    print(page_info)
    print()
    print("| # | 发布时间 | 作品 | 播放 | 赞 | 评论 | 收藏 | 分享 | 资源下载 |")
    print("|---|----------|------|------|-----|------|------|------|------|")

    success_count = 0
    fail_count = 0

    for i, r in enumerate(results, 1):
        title_raw = (r.get("title") or "无标题")[:25]
        title = title_raw.replace("|", "\\|").replace("\n", " ")
        work_url = r.get("work_url", "")

        # 作品标题作为可点击链接
        if work_url:
            title_display = f"[{title}]({work_url})"
        else:
            title_display = title

        pub_time = r.get("publishDate", "")
        pub_display = pub_time[5:] if len(pub_time) >= 10 else (pub_time or "-")
        views = format_number(r.get("viewCount"))
        likes = format_number(r.get("likeCount"))
        comments = format_number(r.get("commentCount"))
        collects = format_number(r.get("collectCount"))
        shares = format_number(r.get("shareCount"))

        # 资源下载列：仅展示视频/封面可点击下载链接
        resources = r.get("resources", [])
        resource_parts = []
        has_video = False
        has_cover = False
        for res in resources:
            if not isinstance(res, dict):
                continue
            rtype = res.get("type", "")
            rurl = res.get("downloadUrl") or res.get("url") or ""
            if rtype == "video" and rurl and not has_video:
                has_video = True
                resource_parts.append(f"[视频]({rurl})")
            elif rtype == "image" and rurl and not has_cover:
                has_cover = True
                resource_parts.append(f"[封面]({rurl})")

        # 封面兜底：resources 无图片时使用顶层 cover
        cover = r.get("cover")
        if cover and not has_cover:
            resource_parts.append(f"[封面]({cover})")

        resource_display = " · ".join(resource_parts) if resource_parts else "-"

        if r.get("download_success"):
            success_count += 1
        else:
            fail_count += 1

        print(f"| {i} | {pub_display} | {title_display} | {views} | {likes} | {comments} | {collects} | {shares} | {resource_display} |")

    print()
    # 汇总
    parts = [f"{success_count} 条可下载"]
    if fail_count > 0:
        parts.append(f"{fail_count} 条下载失败")
    print(f"**合计：** {total} 条作品，{'，'.join(parts)}")
    if fail_count > 0:
        print(f"\n> ⚠️ 下载失败的视频可能是用户已删除该视频，如需数据核查可联系工作人员邮箱 **redfoxdata@proton.me** 处理。")
    print(f"\n> 💡 支持输入想提取的作品时间范围，如 `--date-start 2026-07-01 --date-end 2026-07-20`")
    if success_count > 0:
        print(f"> 💾 需要将这 {success_count} 条作品批量下载到本地吗？直接告诉我即可。")


# ─── JSON 输出 ────────────────────────────────────────────────────────────────────

def print_json_output(account: dict, results: list[dict]):
    """输出 JSON 格式结果"""
    output = {
        "account": account,
        "total": len(results),
        "success": sum(1 for r in results if r.get("download_success")),
        "failed": sum(1 for r in results if not r.get("download_success")),
        "results": results,
        "generated_at": datetime.now().isoformat(),
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))


# ─── 主处理流程 ────────────────────────────────────────────────────────────────────

def process_account(
    extractor: TikTokHomeVideoExtractor,
    sec_user_id: str,
    page_size: int,
    page_num: int = 1,
    date_start: str = "",
    date_end: str = "",
    rate_limit: float = DEFAULT_RATE_LIMIT,
    do_download: bool = False,
    output_dir: str = "",
) -> tuple[dict, list[dict], int]:
    """
    处理单个账号：拉取作品 → 日期过滤 → 分页切片 → 解析下载链接 → 下载视频

    Returns:
        (account_info, results_list, total_works_after_filter)
    """
    # Step 1: 拉取作品
    step(f"拉取账号主页作品: {sec_user_id[:24]}..."
         + (f" (日期 {date_start}~{date_end})" if date_start or date_end else ""))
    works_result = extractor.fetch_works(sec_user_id)

    if not works_result["success"]:
        error(f"拉取失败: {works_result['error']}")
        return works_result.get("account") or {"accountId": sec_user_id}, [], 0

    account = works_result["account"]
    works = works_result["works"]
    info(f"拉取到 {len(works)} 条作品 — {account.get('accountName', sec_user_id)}")

    if not works:
        warn("该账号暂无作品数据")
        return account, [], 0

    # Step 1.5: 客户端日期过滤（在解析下载链接之前，避免浪费 API 配额）
    if date_start or date_end:
        original_count = len(works)
        filtered = []
        for w in works:
            pt = w.get("publishDate", "")
            if not pt:
                filtered.append(w)  # 无发布时间的不筛选
                continue
            if date_start and pt < date_start:
                continue
            if date_end and pt > date_end:
                continue
            filtered.append(w)
        works = filtered
        skipped = original_count - len(works)
        if skipped > 0:
            info(f"日期过滤：{original_count} → {len(works)} 条（跳过 {skipped} 条）")

    if not works:
        warn("日期范围内暂无作品")
        return account, [], 0

    total_after_filter = len(works)

    # Step 1.6: 客户端分页切片
    start = (page_num - 1) * page_size
    end = start + page_size
    works = works[start:end]
    if not works:
        warn("当前页暂无作品（页码超出范围）")
        return account, [], total_after_filter

    # Step 2: 逐条解析下载链接
    results = []
    total = len(works)

    for i, work in enumerate(works, 1):
        work_url = work.get("workUrl") or ""
        title = work.get("title") or "无标题"

        print(f"\n  [{i}/{total}] {CYAN}解析:{RESET} {title[:50]}{'...' if len(title) > 50 else ''}")

        if not work_url:
            warn("  无作品链接，跳过")
            results.append({
                "title": title,
                "work_url": "",
                "workId": work.get("workId", ""),
                "viewCount": work.get("viewCount", 0),
                "likeCount": work.get("likeCount", 0),
                "shareCount": work.get("shareCount", 0),
                "commentCount": work.get("commentCount", 0),
                "collectCount": work.get("collectCount", 0),
                "publishDate": work.get("publishDate", ""),
                "download_success": False,
                "download_error": "无作品链接",
                "download_url": None,
                "cover": None,
                "resources": [],
                "local_path": None,
            })
            continue

        dl_result = extractor.get_download_info(work_url)

        # 兜底：解析接口失败时，使用列表接口自带的无水印直链
        if not dl_result["success"] and work.get("noMarkUrl"):
            dl_result = {
                "success": True,
                "download_url": work["noMarkUrl"],
                "title": title,
                "cover": work.get("listCover") or None,
                "duration": None,
                "resources": [{"type": "video", "downloadUrl": work["noMarkUrl"]}],
                "error": None,
            }

        result_entry = {
            "title": title,
            "work_url": work_url,
            "workId": work.get("workId", ""),
            "viewCount": work.get("viewCount", 0),
            "likeCount": work.get("likeCount", 0),
            "shareCount": work.get("shareCount", 0),
            "commentCount": work.get("commentCount", 0),
            "collectCount": work.get("collectCount", 0),
            "publishDate": work.get("publishDate", ""),
            "download_success": dl_result["success"],
            "download_error": dl_result.get("error"),
            "download_url": dl_result.get("download_url"),
            "cover": dl_result.get("cover") or work.get("listCover") or None,
            "resources": dl_result.get("resources", []),
            "local_path": None,
        }

        if dl_result["success"] and dl_result.get("download_url"):
            # 判断媒体类型：视频 or 图片
            resources = dl_result.get("resources", [])
            is_image_post = work.get("isPhoto", False) or (
                not any(r.get("type") == "video" for r in resources if isinstance(r, dict))
                and any(r.get("type") == "image" for r in resources if isinstance(r, dict))
            )
            media_label = "图片" if is_image_post else "视频"
            info(f"  解析成功（{media_label}）")

            # Step 3: 下载
            if do_download:
                dl_url = dl_result["download_url"]
                # 生成文件名
                pub_date = work.get("publishDate", "")
                time_part = pub_date.replace("-", "") if pub_date else datetime.now().strftime("%Y%m%d")
                safe_title = safe_filename(title)

                # 确定扩展名：视频优先 mp4，图片优先 jpg
                VIDEO_EXTS = ("mp4", "mov", "webm", "avi")
                IMAGE_EXTS = ("jpg", "jpeg", "png", "webp", "gif", "bmp")
                ext = ".jpg" if is_image_post else ".mp4"
                parsed = urlparse(dl_url)
                path_part = unquote(parsed.path)
                if "." in path_part.rsplit("/", 1)[-1]:
                    url_ext = path_part.rsplit(".", 1)[-1].split("?")[0].lower()
                    if is_image_post and url_ext in IMAGE_EXTS:
                        ext = f".{url_ext}"
                    elif not is_image_post and url_ext in VIDEO_EXTS:
                        ext = f".{url_ext}"

                filename = f"{time_part}_{safe_title}{ext}"
                out_path = os.path.join(output_dir, filename)

                print(f"  {CYAN}下载中...{RESET}", end="", flush=True)
                if extractor.download_video(dl_url, out_path):
                    file_size = os.path.getsize(out_path)
                    size_mb = file_size / (1024 * 1024)
                    info(f"\r  下载完成: {filename} ({size_mb:.1f} MB)")
                    result_entry["local_path"] = out_path
                else:
                    warn("\r  下载失败")
                    result_entry["download_success"] = False
                    result_entry["download_error"] = "文件下载失败"
        else:
            warn(f"  解析失败: {dl_result.get('error', '未知错误')}")

        results.append(result_entry)

        # 速率限制
        if i < total:
            time.sleep(rate_limit)

    return account, results, total_after_filter


# ─── 主入口 ────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="TikTok 主页视频批量提取 — 拉取作品 + 解析下载链接 + 批量下载",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python3 tiktok-home-downloader.py --account "https://www.tiktok.com/@tiktok"
  python3 tiktok-home-downloader.py --account "@tiktok" --download
  python3 tiktok-home-downloader.py --accounts "@tiktok,MS4wLjABxxxx" --count 20 --download
  python3 tiktok-home-downloader.py --account "@tiktok" --json
        """,
    )
    parser.add_argument("--account", "-a", help="单个 TikTok 账号（主页链接 / @handle / secUserId）")
    parser.add_argument("--accounts", help="多个 TikTok 账号，逗号分隔")
    parser.add_argument("--count", "-c", type=int, default=DEFAULT_PAGE_SIZE,
                        help=f"每页作品数量（默认{DEFAULT_PAGE_SIZE}，最多{MAX_PAGE_SIZE}）")
    parser.add_argument("--page", "-p", type=int, default=1, help="页码（默认1）")
    parser.add_argument("--date-start", help="起始日期 YYYY-MM-DD，筛选此日期之后的作品")
    parser.add_argument("--date-end", help="结束日期 YYYY-MM-DD，筛选此日期之前的作品")
    parser.add_argument("--download", "-d", action="store_true", help="下载视频文件到本地")
    parser.add_argument("--output-dir", "-o", default="", help="下载目录（默认 output/）")
    parser.add_argument("--json", "-j", action="store_true", help="JSON 格式输出")
    parser.add_argument("--rate-limit", "-r", type=float, default=DEFAULT_RATE_LIMIT,
                        help=f"请求间隔秒数（默认{DEFAULT_RATE_LIMIT}）")
    parser.add_argument("--api-key", "-k", help="API Key")

    args = parser.parse_args()

    # ── 收集账号列表 ──
    account_inputs = []
    if args.account:
        account_inputs.append(args.account.strip())
    if args.accounts:
        account_inputs.extend([a.strip() for a in args.accounts.split(",") if a.strip()])

    if not account_inputs:
        error("请提供至少一个 TikTok 账号（--account 或 --accounts），支持主页链接 / @handle / secUserId")
        sys.exit(1)

    # ── 解析 secUserId ──
    sec_user_ids = []
    for raw in account_inputs:
        sec_uid, err = resolve_sec_user_id(raw)
        if err:
            print(f"\n{RED}{BOLD}⚠️ 无法识别账号「{raw}」{RESET}\n")
            for line in err.splitlines():
                print(f"  {YELLOW}{line}{RESET}")
            print()
            print(f"{CYAN}💡 请提供 TikTok 账号主页链接（如 https://www.tiktok.com/@tiktok）、"
                  f"@handle 或 secUserId。{RESET}\n")
            sys.exit(2)
        sec_user_ids.append(sec_uid)

    # 去重（保持顺序）
    sec_user_ids = list(dict.fromkeys(sec_user_ids))

    # ── API Key ──
    api_key = get_api_key(cli_key=args.api_key)
    if not api_key:
        error("未找到 API Key，请设置 REDFOX_API_KEY 环境变量或使用 --api-key 参数")
        print("  获取 Key: https://redfox.hk/settings/api-keys?source=github")
        sys.exit(1)

    # ── 下载目录 ──
    output_dir = args.output_dir or os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "output")
    if args.download:
        os.makedirs(output_dir, exist_ok=True)

    # ── Banner ──
    print(f"""{CYAN}{BOLD}
  ╔══════════════════════════════════════════╗
  ║     TikTok 主页视频批量提取                ║
  ║     TikTok Home Downloader               ║
  ╚══════════════════════════════════════════╝{RESET}
""")
    info(f"API Key 已加载 | 账号数: {len(sec_user_ids)} | 每页作品数: {min(args.count, MAX_PAGE_SIZE)}")

    extractor = TikTokHomeVideoExtractor(api_key)

    all_results = []

    for idx, sec_uid in enumerate(sec_user_ids):
        if idx > 0:
            print(f"\n{CYAN}{'─' * 50}{RESET}\n")

        account, results, total_works = process_account(
            extractor, sec_uid,
            page_size=min(args.count, MAX_PAGE_SIZE),
            page_num=args.page,
            date_start=args.date_start or "",
            date_end=args.date_end or "",
            rate_limit=args.rate_limit,
            do_download=args.download,
            output_dir=output_dir,
        )
        all_results.append((account, results, total_works))

    # ── 输出结果 ──
    print(f"\n{CYAN}{BOLD}{'=' * 50}{RESET}\n")

    if args.json:
        # JSON 聚合输出
        output = {
            "accounts": [],
            "total_works": 0,
            "total_success": 0,
            "total_failed": 0,
            "generated_at": datetime.now().isoformat(),
        }
        for account, results, _ in all_results:
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
        # Markdown 表格输出
        for account, results, total_works in all_results:
            if results:
                print_markdown_table(account, results, page_num=args.page,
                                     page_size=min(args.count, MAX_PAGE_SIZE),
                                     total_works=total_works)
            else:
                name = account.get("accountName", account.get("accountId", "未知"))
                warn(f"@{name}：暂无作品或拉取失败")

        # 汇总
        total_works = sum(len(r) for _, r, _ in all_results)
        total_success = sum(sum(1 for x in r if x.get("download_success")) for _, r, _ in all_results)
        total_failed = total_works - total_success
        print(f"\n{BOLD}总计：{RESET}{len(sec_user_ids)} 个账号，{total_works} 条作品，成功 {total_success} 条，失败 {total_failed} 条")

    if args.download:
        info(f"视频文件保存至: {os.path.abspath(output_dir)}")

    # 退出码
    total_success_final = sum(sum(1 for x in r if x.get("download_success")) for _, r, _ in all_results)
    total_works_final = sum(len(r) for _, r, _ in all_results)
    sys.exit(0 if total_success_final == total_works_final else 1)


if __name__ == "__main__":
    main()
