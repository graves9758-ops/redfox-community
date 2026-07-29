#!/usr/bin/env python3
"""
3平台适配器 — 豆包 / Kimi / DeepSeek 统一接口

统一接口:
  submit(platform, query) -> task_id
  poll(platform, task_id) -> result_dict | None  (None = still pending)
  extract_result(platform, raw_data) -> (content, sources)
"""

import os
import json
import re
import time
from urllib.parse import urlparse

import requests

API_BASE = "https://redfox.hk"
API_KEY = os.environ.get("REDFOX_API_KEY")

PLATFORMS = {
    "doubao": {
        "submit_path": "/story/api/doubaoSearch/submit",
        "result_path": "/story/api/doubaoSearch/result",
        "label": "豆包",
    },
    "kimi": {
        "submit_path": "/story/api/kimi/submit",
        "result_path": "/story/api/kimi/result",
        "label": "Kimi",
    },
    "deepseek": {
        "submit_path": "/story/api/deepSearch/dsSubmit",
        "result_path": "/story/api/deepSearch/dsResult",
        "label": "DeepSeek",
    },
}

SOURCE_TAG = "品牌GEO分析-GitHub"


def _get_headers():
    """返回统一请求头，若 API_KEY 缺失则抛异常"""
    if not API_KEY:
        raise ValueError(
            "未配置 REDFOX_API_KEY 环境变量，"
            "请前往 https://redfox.hk/settings/api-keys?source=github 获取 API Key"
        )
    return {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json",
    }


def submit(platform, query, source=None, max_retries=3):
    """提交搜索请求，返回 task_id

    Args:
        platform: 平台 key (doubao / kimi / deepseek)
        query: 搜索关键词
        source: 来源标识，默认 SOURCE_TAG
        max_retries: 限流重试次数

    Returns:
        task_id 字符串

    Raises:
        ValueError: 平台未知或响应中无 taskId
        requests.RequestException: 网络错误
    """
    if platform not in PLATFORMS:
        raise ValueError(f"未知平台: {platform}，可选: {list(PLATFORMS.keys())}")

    config = PLATFORMS[platform]
    url = f"{API_BASE}{config['submit_path']}"

    for attempt in range(max_retries + 1):
        resp = requests.post(
            url,
            json={"inquiry_text": query, "source": source or SOURCE_TAG},
            headers=_get_headers(),
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()

        task_id = (data.get("data") or {}).get("taskId")
        if task_id:
            return task_id

        # 限流错误，等待后重试
        code = data.get("code", 0)
        if code == 3108 and attempt < max_retries:
            wait = (attempt + 1) * 2  # 2s, 4s, 6s
            time.sleep(wait)
            continue

        raise ValueError(f"提交失败，未获取到 taskId: {json.dumps(data, ensure_ascii=False)}")

    raise ValueError(f"提交失败，重试 {max_retries} 次后仍未获取到 taskId")


def poll(platform, task_id):
    """轮询单个任务状态

    Returns:
        - dict: 任务完成时返回完整响应 JSON
        - None: 任务仍在处理中
        - raises ValueError: 任务失败
    """
    if platform not in PLATFORMS:
        raise ValueError(f"未知平台: {platform}")

    config = PLATFORMS[platform]
    url = f"{API_BASE}{config['result_path']}"

    resp = requests.post(
        url,
        json={"taskId": task_id},
        headers=_get_headers(),
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()

    # 状态字段可能在 data.data.status 或 data.status
    inner = data.get("data") or {}
    status = inner.get("status", "") if isinstance(inner, dict) else ""
    if not status:
        status = data.get("status", "")

    if status in ("completed", "success", "done"):
        return data
    if status in ("failed", "error"):
        raise ValueError(f"搜索任务失败: {json.dumps(data, ensure_ascii=False)}")
    return None  # still pending


def extract_result(platform, raw_data):
    """从 API 原始响应中提取统一格式的内容和引用来源

    三平台实际响应格式:
      豆包: data.result.content + data.result.searchGuid[].text_card{title,url,sitename}
      Kimi: data.result.content + data.result.webPages[]
      DeepSeek: data.result.content + data.result (待确认)

    Args:
        platform: 平台 key
        raw_data: poll() 返回的完整 JSON dict

    Returns:
        (content: str, sources: list[dict])
        sources 每项: {"title": str, "url": str, "domain": str}
    """
    data = raw_data.get("data") or raw_data

    # result 字段可能是 dict（豆包/Kimi/DeepSeek）或 list
    result_obj = data.get("result")

    # ── 提取 content ──────────────────────────────────────
    content = ""
    if isinstance(result_obj, dict):
        # 豆包/Kimi/DeepSeek: content 在 result.content
        content = (
            result_obj.get("content")
            or result_obj.get("answer")
            or result_obj.get("text")
            or result_obj.get("response")
            or ""
        )
    elif isinstance(result_obj, str):
        content = result_obj

    # 兜底: 直接在 data 层找 content
    if not content:
        content = (
            data.get("content")
            or data.get("answer")
            or data.get("text")
            or data.get("response")
            or ""
        )

    # ── 提取 sources ──────────────────────────────────────
    sources = []

    if isinstance(result_obj, dict):
        # 豆包: searchGuid[].text_card{title, url, sitename}
        search_guid = result_obj.get("searchGuid") or []
        for item in search_guid:
            if not isinstance(item, dict):
                continue
            card = item.get("text_card") or item
            url = card.get("url") or card.get("link") or ""
            title = card.get("title") or card.get("name") or card.get("sitename") or ""
            if url or title:
                sources.append({
                    "title": title,
                    "url": url,
                    "domain": extract_domain(url),
                })

        # Kimi: webPages[]
        web_pages = result_obj.get("webPages") or []
        for item in web_pages:
            if not isinstance(item, dict):
                continue
            url = item.get("url") or item.get("link") or item.get("href") or ""
            title = item.get("title") or item.get("name") or ""
            if url or title:
                sources.append({
                    "title": title,
                    "url": url,
                    "domain": extract_domain(url),
                })

        # 通用: result.sources / result.references / result.citations
        if not sources:
            for key in ("sources", "references", "citations"):
                raw_sources = result_obj.get(key)
                if isinstance(raw_sources, list) and raw_sources:
                    for s in raw_sources:
                        if not isinstance(s, dict):
                            continue
                        url = s.get("url") or s.get("link") or s.get("href") or ""
                        title = s.get("title") or s.get("name") or s.get("text") or ""
                        sources.append({
                            "title": title,
                            "url": url,
                            "domain": extract_domain(url),
                        })
                    break

    # 兜底: data 层的 sources
    if not sources:
        for key in ("sources", "references", "citations"):
            raw_sources = data.get(key)
            if isinstance(raw_sources, list) and raw_sources:
                for s in raw_sources:
                    if not isinstance(s, dict):
                        continue
                    url = s.get("url") or s.get("link") or s.get("href") or ""
                    title = s.get("title") or s.get("name") or s.get("text") or ""
                    sources.append({
                        "title": title,
                        "url": url,
                        "domain": extract_domain(url),
                    })
                break

    return content, sources


def extract_domain(url):
    """从 URL 中提取域名（去除 www. 前缀）"""
    if not url:
        return ""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path.split("/")[0]
        return domain.replace("www.", "").lower()
    except Exception:
        return url.lower()
