#!/usr/bin/env python3
"""
TikTok 平台适配器
接口已实测（2026-07）：
  searchVideo  POST {"keyword": "..."}  → 20 条/次，自带点赞/评论/播放/发布时间
  awemeDetail  POST {"awemeId": "..."}  → 单条详情（日常概要无需调用）
  userAwemeList POST {"secUserId": "..."} → 作者作品列表（备用）
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import TIKTOK_SEARCH_API, SOURCE, SUCCESS_CODES
from .base import BaseSource, PlatformUnavailable


class TikTokSource(BaseSource):
    platform = "tiktok"
    display_name = "TikTok"

    def search(self, session, keyword):
        result = self.post_json(session, TIKTOK_SEARCH_API,
                                {"keyword": keyword, "source": SOURCE})
        if result is None:
            raise PlatformUnavailable("TikTok 搜索请求失败（网络异常）")

        code = result.get("code")
        if code not in SUCCESS_CODES:
            msg = result.get("msg", "")
            if code == 3203:
                raise PlatformUnavailable(f"TikTok 上游能力故障: {msg}")
            raise PlatformUnavailable(f"TikTok 搜索接口错误 (code {code}): {msg}")

        data = result.get("data") or []
        if not isinstance(data, list):
            return []

        records = []
        for item in data:
            stats = item.get("statsData") or {}
            author = item.get("authorData") or {}
            record = self.make_record(
                title=item.get("content") or "",
                url=item.get("shareLink") or "",
                author=author.get("userName") or author.get("userHandle") or "",
                likes=stats.get("likeCount"),
                comments=stats.get("commentTotal"),
                views=stats.get("viewCount"),
                publish_ts=self._parse_ts(item.get("publishTime")),
                keyword=keyword,
                extra={
                    "shares": self._to_int(stats.get("shareTotal")),
                    "work_id": str(item.get("workId") or ""),
                    "area": item.get("area") or "",
                    "cover": (item.get("videoData") or {}).get("coverImage") or "",
                },
            )
            records.append(record)
        return records
