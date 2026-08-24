#!/usr/bin/env python3
"""
公众号文章数据采集
==================
两步 API 流程：
1. queryWorkList — 分页获取文章 UUID 列表（每页20条，offset 步进20）
2. queryWork — 按 UUID 获取单篇完整数据（正文/摘要/词云等）

UUID 缓存：首次获取后自动保存到 output/{account}_uuids.json，
后续运行直接读取缓存，避免重复消耗积分。

认证：REDFOX_API_KEY（环境变量 > 配置文件 > 公共Key）
"""

import json
import os
import sys
import time
from pathlib import Path

# Windows 控制台 UTF-8 编码
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


# ─── 配置 ─────────────────────────────────────────────────────────────────────────

WORK_LIST_URL = "https://redfox.hk/story/api/gzhData/queryWorkList"
WORK_DETAIL_URL = "https://redfox.hk/story/api/gzhData/queryWork"

CONFIG_DIR = Path.home() / ".qoder" / "apis"
CONFIG_FILE = CONFIG_DIR / "redfox.json"
ENV_KEY = "REDFOX_API_KEY"
SOURCE = "公众号投资博主蒸馏-GitHub"

PAGE_SIZE = 20  # queryWorkList offset 步进为20，非10

# UUID 缓存目录（与 distill.py 的 OUTPUT_DIR 保持一致）
SCRIPT_DIR = Path(__file__).parent.parent
CACHE_DIR = SCRIPT_DIR / "output"


# ─── 终端颜色 ──────────────────────────────────────────────────────────────────────

GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
RESET = "\033[0m"


def info(msg):
    print(f"{GREEN}[✓]{RESET} {msg}")


def warn(msg):
    print(f"{YELLOW}[!]{RESET} {msg}")


def error(msg):
    print(f"{RED}[✗]{RESET} {msg}")


def step(msg):
    print(f"{CYAN}[→]{RESET} {msg}")


# ─── API Key 管理 ──────────────────────────────────────────────────────────────────

def get_api_key(cli_key=None):
    """获取 API Key：CLI参数 > 环境变量 > 配置文件 > 公共Key"""
    if cli_key:
        return cli_key
    env_key = os.environ.get(ENV_KEY)
    if env_key:
        return env_key
    if CONFIG_FILE.exists():
        try:
            data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            key = data.get("api_key") or data.get("REDFOX_API_KEY")
            if key:
                return key
        except (json.JSONDecodeError, OSError):
            pass
    return ''


# ─── Step 1: 获取文章UUID列表 ──────────────────────────────────────────────────────

def fetch_work_list(session, account, count, force_refresh=False):
    """
    调用 queryWorkList 分页获取文章 UUID 列表。
    offset 从0开始，每页+20，循环分页直到达到目标数量。
    首次获取后自动缓存到 output/{account}_uuids.json，后续运行直接读取。

    Args:
        session: requests.Session（已设置 headers）
        account: 公众号微信号（如 zshbtz）
        count: 目标获取文章数量
        force_refresh: 是否强制刷新缓存（忽略已有缓存重新请求API）

    Returns:
        list[dict] — 每个 dict 包含 workUuid 等基础字段
    """
    # 检查 UUID 缓存
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / f"{account}_uuids.json"

    if not force_refresh and cache_file.exists():
        try:
            cached = json.loads(cache_file.read_text(encoding="utf-8"))
            cached_items = cached.get("items", [])
            if len(cached_items) >= count:
                info(f"使用 UUID 缓存（{len(cached_items)}条，跳过API请求）")
                return cached_items[:count]
            else:
                info(f"缓存仅 {len(cached_items)} 条，不足目标 {count} 条，重新请求...")
        except (json.JSONDecodeError, OSError):
            warn("缓存文件损坏，重新请求...")

    all_items = []
    offset = 0

    while len(all_items) < count:
        payload = {
            "source": SOURCE,
            "account": account,
            "sortType": "_2",
            "offset": offset,
        }

        try:
            resp = session.post(WORK_LIST_URL, json=payload, timeout=30)
            result = resp.json()
        except Exception as e:
            error(f"queryWorkList 请求失败: {e}")
            break

        code = result.get("code")
        if code not in (200, 2000):
            if code == 3108:
                warn("触发限流，等待5秒...")
                time.sleep(5)
                continue
            error(f"queryWorkList 返回错误码 {code}：{result.get('msg') or result.get('message') or '(无详细信息)'}")
            break

        data_raw = result.get("data", {})
        if isinstance(data_raw, list):
            items = data_raw
        elif isinstance(data_raw, dict):
            items = data_raw.get("list") or data_raw.get("records") or data_raw.get("data") or []
        else:
            items = []

        if not items:
            break

        # 按需截断：避免 API 返回超量数据浪费积分
        needed = count - len(all_items)
        all_items.extend(items[:needed])
        offset += PAGE_SIZE

        if len(items) < PAGE_SIZE or len(all_items) >= count:
            break  # 已无更多数据

        # 进度提示
        if len(all_items) % 20 == 0:
            step(f"  已获取 {len(all_items)} 条UUID...")

        time.sleep(0.5)  # 请求间隔

    info(f"queryWorkList 共获取 {len(all_items)} 条文章UUID")

    # 保存 UUID 缓存
    try:
        cache_data = {
            "account": account,
            "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "count": len(all_items),
            "items": all_items,
        }
        cache_file.write_text(json.dumps(cache_data, ensure_ascii=False, indent=2), encoding="utf-8")
        info(f"UUID 缓存已保存：{cache_file}")
    except OSError as e:
        warn(f"缓存写入失败: {e}")

    return all_items[:count]


# ─── Step 2: 逐篇获取完整数据 ──────────────────────────────────────────────────────

def fetch_work_detail(session, uuid):
    """
    调用 queryWork 获取单篇文章完整数据。

    Args:
        session: requests.Session（已设置 headers）
        uuid: 文章UUID

    Returns:
        dict — 包含 title/content/summary/wordCloud 等完整字段，失败返回 None
    """
    payload = {
        "source": SOURCE,
        "workUuid": uuid,
    }

    try:
        resp = session.post(WORK_DETAIL_URL, json=payload, timeout=30)
        result = resp.json()
    except Exception as e:
        warn(f"queryWork({uuid[:8]}...) 请求失败: {e}")
        return None

    code = result.get("code")
    if code not in (200, 2000):
        if code == 3108:
            time.sleep(5)
            return fetch_work_detail(session, uuid)  # 重试一次
        warn(f"queryWork({uuid[:8]}...) 返回错误码 {code}：{result.get('msg') or result.get('message') or '(无详细信息)'}")
        return None

    data = result.get("data", {})
    if isinstance(data, list) and data:
        data = data[0]
    return data if isinstance(data, dict) else None


def fetch_work_details(session, uuid_items, batch_delay=0.3):
    """
    批量获取文章详情。

    Args:
        session: requests.Session
        uuid_items: UUID列表（从 fetch_work_list 返回）
        batch_delay: 每篇请求间隔（秒）

    Returns:
        list[dict] — 完整文章数据列表
    """
    articles = []
    total = len(uuid_items)

    for i, item in enumerate(uuid_items):
        uuid = item.get("workUuid") or item.get("uuid") or item.get("id") or (item if isinstance(item, str) else "")
        if not uuid:
            continue

        detail = fetch_work_detail(session, uuid)
        if detail:
            articles.append(detail)

        # 进度提示
        done = i + 1
        if done % 10 == 0 or done == total:
            step(f"  已获取 {done}/{total} 篇正文...")

        time.sleep(batch_delay)

    info(f"queryWork 共获取 {len(articles)} 篇完整文章")
    return articles


# ─── 主采集函数 ──────────────────────────────────────────────────────────────────────

def fetch_articles(account, author_name="", count=None, api_key=None, force_refresh=False):
    """
    两步流程采集公众号文章：
    1. queryWorkList 获取UUID列表（优先读缓存）
    2. queryWork 逐篇获取完整数据

    Args:
        account: 公众号微信号（如 zshbtz）
        author_name: 博主显示名称（用于日志）
        count: 目标文章数量（20/60/100）
        api_key: API Key（可选）
        force_refresh: 是否强制刷新UUID缓存

    Returns:
        list[dict] — 标准化文章数据列表，每个 dict 包含：
            - title: 标题
            - content: 正文
            - summary: 摘要
            - publish_time: 发布时间
            - url: 链接
            - content_keywords: 内容关键词（list[dict]，含 keyword/weight）
            - read_count/like_count/comment_count/share_count/collect_count/reward_count: 互动数据
            - author: 作者名
            - uuid: 文章UUID
    """
    if not HAS_REQUESTS:
        error("缺少 requests 库，请执行: pip install requests")
        return []

    key = get_api_key(api_key)

    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "X-API-Key": key,
    })

    display = author_name or account
    step(f"开始采集公众号 [{display}]（微信号: {account}）的文章...")

    # Step 1: 获取UUID列表
    step("Step 1: 获取文章UUID列表...")
    uuid_items = fetch_work_list(session, account, count=count, force_refresh=force_refresh)

    if not uuid_items:
        error(f"未获取到 [{display}] 的文章列表，请检查微信号是否正确")
        return []

    # Step 2: 逐篇获取完整数据
    step("Step 2: 逐篇获取文章正文...")
    raw_articles = fetch_work_details(session, uuid_items)

    if not raw_articles:
        error(f"获取到UUID但无法获取正文数据")
        return []

    # 标准化输出
    articles = []
    for raw in raw_articles:
        # 内容关键词（API 字段名: contentKeywords，非 wordCloud）
        ck_raw = raw.get("contentKeywords") or raw.get("wordCloud") or raw.get("contentWordCloud") or []
        if isinstance(ck_raw, str):
            try:
                ck_raw = json.loads(ck_raw)
            except (json.JSONDecodeError, ValueError):
                ck_raw = []
        content_keywords = ck_raw if isinstance(ck_raw, list) else []

        articles.append({
            "title": raw.get("title") or raw.get("workName") or "",
            "content": raw.get("content") or raw.get("workContent") or raw.get("workText") or "",
            "summary": raw.get("summary") or raw.get("workSummary") or "",
            "publish_time": raw.get("publishTime") or raw.get("publicTime") or "",
            "url": raw.get("workUrl") or raw.get("url") or "",
            "content_keywords": content_keywords,
            # 互动数据（直接来自 API）
            "read_count": raw.get("readCount", 0),
            "like_count": raw.get("likeCount", 0),
            "comment_count": raw.get("commentCount", 0),
            "share_count": raw.get("shareCount", 0),
            "collect_count": raw.get("collectCount", 0) if raw.get("collectCount") is not None else 0,
            "reward_count": raw.get("rewardCount", 0) if raw.get("rewardCount") is not None else 0,
            "author": raw.get("accountName") or raw.get("accountNickName") or author_name or account,
            "uuid": raw.get("workUuid") or raw.get("uuid") or raw.get("id") or "",
            "platform": "gzh",
        })

    info(f"[{display}] 共采集到 {len(articles)} 篇完整文章")
    return articles
