#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
共享基类 — API Key 管理、作品缓存、文件下载、输出格式化
========================================================================
各平台子类继承 BaseDownloader，仅需实现 fetch_works() 和 get_download_info()。
"""

import json
import os
import re
import sys
import time
import warnings
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import unquote, urlparse

import requests

warnings.filterwarnings("ignore", category=Warning)
warnings.filterwarnings("ignore", message=".*NotOpenSSLWarning.*")

# ─── 配置 ─────────────────────────────────────────────────────────────────────────
API_BASE = "https://redfox.hk"
ENV_KEY = "REDFOX_API_KEY"

DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 50
DEFAULT_RATE_LIMIT = 1.0

SUPPORT_EMAIL = "redfoxdata@proton.me"

# ─── 作品列表缓存（全量拉取优化）─────────────────────────────────────
CACHE_DIR = Path.home() / ".qoder" / "account_video_extractor_cache"
CACHE_TTL_SECONDS = 1800  # 30 分钟

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
def get_api_key() -> Optional[str]:
    """从环境变量 REDFOX_API_KEY 获取 API Key"""
    return os.environ.get(ENV_KEY)


# ─── 数字格式化 ────────────────────────────────────────────────────────────────────
def format_number(n) -> str:
    """格式化数字: >=1亿->x.x亿, >=1万->x.xw, >=1千->x.xk, 其余逗号分隔"""
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


# ─── 中文检测 ──────────────────────────────────────────────────────────────────────
def _is_chinese(text: str) -> bool:
    """判断输入是否包含中文字符"""
    return bool(re.search(r'[\u4e00-\u9fff]', text))


# ─── 作品列表缓存（全量拉取优化）─────────────────────────────────────

def _cache_key(platform: str, account_id: str) -> str:
    """生成缓存文件名（hash 防路径注入）"""
    import hashlib
    raw = f"{platform}:{account_id.strip().lower()}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16] + ".json"


def _load_works_cache(platform: str, account_id: str) -> Optional[dict]:
    """
    读取缓存。返回 (data_dict, is_fresh) 或 None。
    data_dict 包含: account, works, timestamp
    """
    if not CACHE_DIR.exists():
        return None
    cache_file = CACHE_DIR / _cache_key(platform, account_id)
    if not cache_file.exists():
        return None
    try:
        data = json.loads(cache_file.read_text(encoding="utf-8"))
        age = time.time() - data.get("timestamp", 0)
        if age > CACHE_TTL_SECONDS:
            cache_file.unlink(missing_ok=True)
            return None
        return data
    except (json.JSONDecodeError, OSError):
        cache_file.unlink(missing_ok=True)
        return None


def _save_works_cache(platform: str, account_id: str, data: dict):
    """保存作品列表缓存"""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    data["timestamp"] = time.time()
    cache_file = CACHE_DIR / _cache_key(platform, account_id)
    cache_file.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


# ─── 文件名清理 ────────────────────────────────────────────────────────────────────
def safe_filename(text: str) -> str:
    """将文本转为安全的文件名（去除非法字符、限制长度）"""
    text = re.sub(r'[\\/:*?"<>|\n\r\t]', '_', text)
    text = text.strip().strip('.')
    if len(text) > 80:
        text = text[:80]
    return text or "video"


# ─── 抽象基类 ──────────────────────────────────────────────────────────────────────

class BaseDownloader(ABC):
    """多平台视频下载器基类"""

    def __init__(self, api_key: str, platform_key: str, platform_label: str):
        """
        Args:
            api_key: API 密钥
            platform_key: 平台标识（如 "kuaishou", "bilibili"）
            platform_label: 平台中文名（如 "快手", "B站"）
        """
        self.api_key = api_key
        self.platform_key = platform_key
        self.platform_label = platform_label

    # ── 子类必须实现 ────────────────────────────────────────────────────────────

    @abstractmethod
    def fetch_works(self, account_id: str, page_size: int = DEFAULT_PAGE_SIZE, page_num: int = 1,
                    date_start: str = "", date_end: str = "") -> dict:
        """
        拉取账号作品列表

        Returns:
            dict: {
                "success": bool,
                "account": dict | None,
                "works": list[dict],
                "error": str | None,
                "rate_limited": bool
            }
            其中每个 work dict 已通过 _normalize_work() 统一字段。
        """
        ...

    @abstractmethod
    def get_download_info(self, work_url: str) -> dict:
        """
        解析视频下载链接

        Returns:
            dict: {"success": bool, "download_url": str|None, "title": str|None,
                   "cover": str|None, "duration": int|None, "resources": list, "error": str|None}
        """
        ...

    # ── 可选覆写 ────────────────────────────────────────────────────────────────

    def validate_account_id(self, account_id: str) -> tuple:
        """
        验证账号标识格式。默认拒绝纯中文输入。

        Returns:
            (is_valid: bool, message: str)
        """
        if _is_chinese(account_id):
            return False, (
                f"「{account_id}」看起来是账号昵称而非唯一标识。\n"
                "请提供平台账号的唯一 ID 以便精准查询。"
            )
        if not account_id or len(account_id) < 2:
            return False, f"「{account_id}」不是有效的账号标识，请提供正确的 ID。"
        return True, ""

    def description_hint(self) -> str:
        """返回该平台账号标识的说明文案，用于提示用户输入正确格式"""
        return f"请提供 {self.platform_label} 的账号唯一标识（如用户 ID）。"

    # ── 共享实现 ────────────────────────────────────────────────────────────────

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

    # ── 字段归一化（子类可覆写） ────────────────────────────────────────────────

    def _normalize_work(self, work: dict, account_id: str) -> dict:
        """
        将平台特有字段映射为通用 schema。子类可覆写以支持平台特定字段名。

        通用 schema:
        {
            "title": str,
            "workUrl": str,
            "publishTime": str (YYYY-MM-DD),
            "likeCount": int,
            "commentCount": int,
            "collectCount": int,
            "shareCount": int,
            "authorName": str,
            "followerCount": int
        }
        """
        return {
            "title": work.get("title") or work.get("content") or work.get("desc") or "",
            "workUrl": work.get("workUrl") or work.get("opusUrl") or work.get("url") or work.get("link") or "",
            "publishTime": work.get("publishTime") or work.get("createTime") or work.get("created_at") or work.get("pubdate") or "",
            "likeCount": work.get("likeCount") or work.get("diggCount") or work.get("like_count") or 0,
            "commentCount": work.get("commentCount") or work.get("comment_count") or 0,
            "collectCount": work.get("collectCount") or work.get("collect_count") or work.get("favoriteCount") or 0,
            "shareCount": work.get("shareCount") or work.get("share_count") or 0,
            "authorName": work.get("authorName") or work.get("nickname") or work.get("name") or account_id,
            "followerCount": work.get("authorFansCount") or work.get("authorFans") or work.get("followerCount") or work.get("follower_count") or 0,
        }


# ─── 主处理流程 ────────────────────────────────────────────────────────────────────

def process_account(
    downloader: BaseDownloader,
    account_id: str,
    page_size: int = DEFAULT_PAGE_SIZE,
    page_num: int = 1,
    date_start: str = "",
    date_end: str = "",
    rate_limit: float = DEFAULT_RATE_LIMIT,
    do_download: bool = False,
    output_dir: str = "",
) -> tuple:
    """
    处理单个账号：拉取作品 → 日期过滤 → 解析下载链接 → 下载视频

    Args:
        downloader: 平台下载器实例
        account_id: 账号标识
        page_size: 每页数量
        page_num: 页码
        date_start: 起始日期 YYYY-MM-DD
        date_end: 结束日期 YYYY-MM-DD
        rate_limit: 请求间隔秒数
        do_download: 是否下载文件
        output_dir: 下载目录

    Returns:
        (account_info: dict, results: list[dict])
    """
    # Step 1: 拉取作品
    label = downloader.platform_label
    date_info = ""
    if date_start or date_end:
        date_info = f" (日期 {date_start}~{date_end})"
    step(f"拉取{label}账号作品: {account_id}{date_info}")

    works_result = downloader.fetch_works(account_id, page_size, page_num=page_num,
                                                date_start=date_start, date_end=date_end)

    if not works_result["success"]:
        error(f"拉取失败: {works_result['error']}")
        return works_result.get("account") or {"accountId": account_id}, []

    account = works_result["account"]
    works = works_result["works"]
    has_more_api = works_result.get("has_more")  # YouTube 翻页标志
    if has_more_api is not None:
        account["_has_more"] = has_more_api
    info(f"拉取到 {len(works)} 条作品 — {account.get('accountName', account_id)}")

    if not works:
        warn("该账号暂无作品数据")
        return account, []

    # Step 1.5: 客户端日期过滤
    if date_start or date_end:
        original_count = len(works)
        filtered = []
        for w in works:
            pt = w.get("publishTime", "")
            if not pt:
                filtered.append(w)
                continue
            if date_start and pt[:10] < date_start:
                continue
            if date_end and pt[:10] > date_end:
                continue
            filtered.append(w)
        works = filtered
        skipped = original_count - len(works)
        if skipped > 0:
            info(f"日期过滤：{original_count} → {len(works)} 条（跳过 {skipped} 条）")

    if not works:
        warn("日期范围内暂无作品")
        return account, []

    # Step 1.6: 客户端分页截断（YouTube 等全量返回的平台）
    if page_size > 0 and len(works) > page_size:
        works = works[:page_size]

    # Step 2: 逐条解析下载链接
    results = []
    total = len(works)

    for i, work in enumerate(works, 1):
        work_url = work.get("workUrl") or ""
        title = work.get("title") or "无标题"

        print(f"\n  [{i}/{total}] {CYAN}解析:{RESET} {title[:50]}{'...' if len(title) > 50 else ''}")

        if not work_url:
            warn(f"  无作品链接，跳过")
            results.append({
                "title": title,
                "work_url": "",
                "likeCount": work.get("likeCount", 0),
                "shareCount": work.get("shareCount", 0),
                "commentCount": work.get("commentCount", 0),
                "collectCount": work.get("collectCount", 0),
                "publishTime": work.get("publishTime", ""),
                "download_success": False,
                "download_error": "无作品链接",
                "download_url": None,
                "cover": None,
                "duration": None,
                "resources": [],
                "local_path": None,
            })
            continue

        # 优先使用作品列表自带的无水印直链（快手），省掉下载接口调用
        direct_url = work.get("directVideoUrl")
        if direct_url:
            dl_result = {
                "success": True,
                "download_url": direct_url,
                "title": title,
                "cover": work.get("coverUrl") or "",
                "duration": None,
                "resources": [{"type": "video", "downloadUrl": direct_url}],
                "error": None,
            }
            info(f"  ✓ 免解析（作品列表含无水印直链）")
        else:
            dl_result = downloader.get_download_info(work_url)

        result_entry = {
            "title": title,
            "work_url": work_url,
            "likeCount": work.get("likeCount", 0),
            "shareCount": work.get("shareCount", 0),
            "commentCount": work.get("commentCount", 0),
            "collectCount": work.get("collectCount", 0),
            "publishTime": work.get("publishTime", ""),
            "download_success": dl_result["success"],
            "download_error": dl_result.get("error"),
            "download_url": dl_result.get("download_url"),
            "cover": dl_result.get("cover"),
            "duration": dl_result.get("duration"),
            "resources": dl_result.get("resources", []),
            "local_path": None,
        }

        if dl_result["success"] and dl_result.get("download_url"):
            resources = dl_result.get("resources", [])
            is_image_post = (
                not any(r.get("type") == "video" for r in resources if isinstance(r, dict))
                and any(r.get("type") == "image" for r in resources if isinstance(r, dict))
            )
            media_label = "图片" if is_image_post else "视频"
            info(f"  解析成功（{media_label}）" + (f" | 时长: {dl_result['duration']}s" if dl_result.get("duration") else ""))

            # Step 3: 下载
            if do_download:
                dl_url = dl_result["download_url"]
                pub_time = work.get("publishTime", "")
                time_part = pub_time[:10].replace("-", "") if pub_time else datetime.now().strftime("%Y%m%d")
                safe_title = safe_filename(title)

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
                if downloader.download_video(dl_url, out_path):
                    file_size = os.path.getsize(out_path)
                    size_mb = file_size / (1024 * 1024)
                    info(f"\r  下载完成: {filename} ({size_mb:.1f} MB)")
                    result_entry["local_path"] = out_path
                else:
                    warn(f"\r  下载失败")
                    result_entry["download_success"] = False
                    result_entry["download_error"] = "文件下载失败"
        else:
            warn(f"  解析失败: {dl_result.get('error', '未知错误')}")

        results.append(result_entry)

        # 速率限制
        if i < total:
            time.sleep(rate_limit)

    return account, results


# ─── Markdown 输出 ────────────────────────────────────────────────────────────────

def print_markdown_table(
    downloader: BaseDownloader,
    account: dict,
    results: list,
    page_num: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
):
    """
    输出 Markdown 格式的结果表格

    ⛔ 强制规则：Agent 调用方必须原样展示本函数的完整输出，禁止以下行为：
    - 禁止删除或合并任何列
    - 禁止省略翻页提示行
    - 禁止省略时间范围筛选提示和下载询问提示
    - 禁止用「...」或摘要代替完整表格内容
    - 必须逐行展示所有作品信息（含完整资源下载链接）
    """
    name = account.get("accountName", account.get("accountId", "未知"))
    fans = format_number(account.get("followerCount"))
    label = downloader.platform_label

    # 粉丝数：None 表示平台无此数据，不展示
    fans_display = f"（粉丝: {fans}）" if account.get("followerCount") is not None else ""
    print(f"\n## 📥 {label}视频下载 — @{name}{fans_display}")
    print()
    total = len(results)

    # 翻页提示：YouTube 用 continuation token；其他平台用 pageNum
    yt_has_more = account.get("_has_more")
    show_more = yt_has_more if yt_has_more is not None else (total >= page_size)

    page_info = f"当前是**第 {page_num} 页**，共 {total} 条作品"
    if show_more:
        next_page = page_num + 1
        page_info += f" | 还有更多作品，输入 `--page {next_page}` 翻看下一页"
    print(page_info)
    print()
    print("| # | 发布时间 | 作品 | 赞 | 评论 | 收藏 | 分享 | 资源下载 |")
    print("|---|----------|------|-----|------|------|------|------|")

    success_count = 0
    fail_count = 0

    for i, r in enumerate(results, 1):
        title_raw = (r.get("title") or "无标题")[:25]
        title = title_raw.replace("|", "\\|").replace("\n", " ")
        work_url = r.get("work_url", "")

        if work_url:
            title_display = f"[{title}]({work_url})"
        else:
            title_display = title

        pub_time = r.get("publishTime", "")[:10] if r.get("publishTime") else "-"
        likes = format_number(r.get("likeCount"))
        comments = format_number(r.get("commentCount"))
        collects = format_number(r.get("collectCount"))
        shares = format_number(r.get("shareCount"))

        # 资源下载列
        resources = r.get("resources", [])
        resource_parts = []
        seen_types = set()
        has_video = False
        for res in resources:
            if not isinstance(res, dict):
                continue
            rtype = res.get("type", "")
            rurl = res.get("downloadUrl") or res.get("url") or ""
            if rtype and rurl and rtype not in seen_types:
                seen_types.add(rtype)
                if rtype == "video":
                    has_video = True
                    resource_parts.append(f"[视频]({rurl})")
                elif rtype == "image":
                    resource_parts.append(f"[封面]({rurl})")
                elif rtype == "audio":
                    resource_parts.append(f"[音频]({rurl})")
                else:
                    resource_parts.append(f"[{rtype}]({rurl})")

        cover = r.get("cover")
        if cover and "image" not in seen_types:
            resource_parts.append(f"[封面]({cover})")

        # YouTube CDN 链接是 IP 锁定的签名 URL，浏览器无法直接访问
        if downloader.platform_key == "youtube" and resource_parts:
            resource_parts = ["[▶ 播放]({}) · ⚠️ 下载需 `--download`".format(work_url)] if work_url else ["⚠️ 下载需 `--download`"]

        resource_display = "<br>".join(resource_parts) if resource_parts else "-"

        if r.get("download_success") and has_video:
            success_count += 1
        elif r.get("download_success"):
            success_count += 1
        else:
            fail_count += 1

        print(f"| {i} | {pub_time} | {title_display} | {likes} | {comments} | {collects} | {shares} | {resource_display} |")

    print()
    parts = [f"{success_count} 条可下载"]
    if fail_count > 0:
        parts.append(f"{fail_count} 条下载失败")
    print(f"**合计：** {total} 条作品，{'，'.join(parts)}")
    if fail_count > 0:
        print(f"\n> ⚠️ 下载失败的视频可能是用户已删除该视频，如需数据核查可联系工作人员邮箱 **{SUPPORT_EMAIL}** 处理。")
    print(f"\n> 💡 支持输入想提取的作品时间范围，如 `--date-start 2026-07-01 --date-end 2026-07-20`")
    if success_count > 0:
        print(f"> 💾 需要将这 {success_count} 条作品批量下载到本地吗？直接告诉我即可。")


# ─── JSON 输出 ────────────────────────────────────────────────────────────────────

def print_json_output(account: dict, results: list):
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
