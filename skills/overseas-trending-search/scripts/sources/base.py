#!/usr/bin/env python3
"""
平台适配器抽象基类 — 所有平台实现统一接口，主流程对平台无感知
新增平台（如 YouTube）只需继承 BaseSource 并实现 search()，无需改动主流程
"""

import re
import time
from datetime import datetime, timedelta


class PlatformUnavailable(Exception):
    """平台上游能力不可用（如 RedFox 3203 能力故障），主流程应优雅降级跳过"""
    pass


class BaseSource:
    """平台适配器基类"""

    #: 平台标识（x / tiktok / youtube）
    platform = ""
    #: 平台展示名
    display_name = ""

    def search(self, session, keyword):
        """
        按关键词搜索，返回归一化记录列表（make_record 产物）。
        平台上游故障时应抛出 PlatformUnavailable，由主流程降级处理。
        """
        raise NotImplementedError

    # ─── 归一化 ─────────────────────────────────────────────────────────────────
    def make_record(self, title, url, author, likes, comments, views,
                    publish_ts, keyword, extra=None):
        """生成统一记录 schema，主流程只认这个结构"""
        record = {
            "platform": self.platform,
            "platform_name": self.display_name,
            "title": (title or "").strip() or "无标题",
            "url": url or "",
            "author": author or "未知作者",
            "likes": self._to_int(likes),
            "comments": self._to_int(comments),
            "views": self._to_int(views),
            "publish_ts": publish_ts or 0,
            "publish_time": self._fmt_ts(publish_ts),
            "keyword": keyword or "",
        }
        if extra:
            record.update(extra)
        return record

    # ─── 工具 ───────────────────────────────────────────────────────────────────
    @staticmethod
    def _to_int(v):
        try:
            return int(v or 0)
        except (ValueError, TypeError):
            return 0

    @staticmethod
    def _fmt_ts(ts):
        try:
            ts = int(ts)
            if ts > 10**12:  # 毫秒级时间戳兼容
                ts = ts // 1000
            return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
        except (ValueError, TypeError, OSError):
            return ""

    @staticmethod
    def _parse_ts(value):
        """兼容秒/毫秒时间戳、ISO 时间字符串与相对时间（如 "1 day ago"），返回秒级 int"""
        if value is None:
            return 0
        if isinstance(value, (int, float)):
            ts = int(value)
            return ts // 1000 if ts > 10**12 else ts
        s = str(value).strip()
        if s.isdigit():
            ts = int(s)
            return ts // 1000 if ts > 10**12 else ts
        for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d %H:%M:%S", "%a %b %d %H:%M:%S %z %Y"):
            try:
                return int(datetime.strptime(s.replace("Z", "+0000"), fmt).timestamp())
            except (ValueError, TypeError):
                continue
        return BaseSource._parse_relative_ts(s)

    #: 相对时间单位 → 秒数（月/年为近似值，概要场景足够）
    _REL_UNITS = {
        "second": 1, "minute": 60, "hour": 3600, "day": 86400,
        "week": 604800, "month": 2592000, "year": 31536000,
    }
    _REL_UNITS_ZH = {
        "秒": 1, "分钟": 60, "小时": 3600, "天": 86400,
        "周": 604800, "个月": 2592000, "月": 2592000, "年": 31536000,
    }

    @staticmethod
    def _parse_relative_ts(s):
        """解析相对时间："3 hours ago" / "Streamed 1 day ago" / "2 天前" 等"""
        m = re.search(r"(\d+)\s*(second|minute|hour|day|week|month|year)s?\s*ago", s, re.I)
        if m:
            secs = int(m.group(1)) * BaseSource._REL_UNITS[m.group(2).lower()]
            return int((datetime.now() - timedelta(seconds=secs)).timestamp())
        m = re.search(r"(\d+)\s*(个月|分钟|小时|秒|天|周|月|年)前", s)
        if m:
            secs = int(m.group(1)) * BaseSource._REL_UNITS_ZH[m.group(2)]
            return int((datetime.now() - timedelta(seconds=secs)).timestamp())
        return 0

    # ─── 稳健请求（递增延迟重试）────────────────────────────────────────────────
    def post_json(self, session, url, payload, max_retries=3, timeout=30):
        """
        POST JSON，失败（网络异常/非 JSON）递增延迟重试。
        返回解析后的 dict；彻底失败返回 None。
        """
        for attempt in range(max_retries):
            try:
                resp = session.post(url, json=payload, timeout=timeout)
                return resp.json()
            except Exception:
                if attempt < max_retries - 1:
                    time.sleep(0.5 * (attempt + 1))
        return None
