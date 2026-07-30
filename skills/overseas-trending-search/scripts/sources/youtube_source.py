#!/usr/bin/env python3
"""
YouTube 平台适配器
接口已实测（2026-07）：
  searchVideo   POST {"searchQuery": "..."}
      → data.videos[]（20条/次）：title / videoId / author / channelId /
        viewCount（原始整数）/ duration / publishedTime（相对时间，如 "1 day ago"）/ thumbnails[]
  videoDetail   POST {"videoId": "..."}
      → likeCount / commentCount（本地化展示串，如 "1928万"、"244万"）、
        date（中文日期，如 "2026年7月24日"）、videoUrl / channelHandle / description
  videoComments POST {"videoId": "..."}
      → data.comments[] + continuationToken（评论内容分析场景备用）
注意：searchVideo 不含点赞/评论数，需对候选视频调 videoDetail 补全；
      为控制积分消耗，默认只对 viewCount 前 detail_top 条补详情，其余回退为 0。
"""

import re
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import YOUTUBE_SEARCH_API, YOUTUBE_DETAIL_API, SOURCE, SUCCESS_CODES
from .base import BaseSource, PlatformUnavailable


class YouTubeSource(BaseSource):
    platform = "youtube"
    display_name = "YouTube"
    #: 对 viewCount 前 N 条调详情补点赞/评论。searchVideo 每次返回 20 条，
    #: 取 20 即全量补全——热文按点赞排序，漏拉详情会导致高赞视频排不上来
    detail_top = 20

    def search(self, session, keyword):
        result = self.post_json(session, YOUTUBE_SEARCH_API,
                                {"searchQuery": keyword, "source": SOURCE})
        if result is None:
            raise PlatformUnavailable("YouTube 搜索请求失败（网络异常）")

        code = result.get("code")
        if code not in SUCCESS_CODES:
            msg = result.get("msg", "")
            if code == 3203:
                raise PlatformUnavailable(f"YouTube 上游能力故障: {msg}")
            raise PlatformUnavailable(f"YouTube 搜索接口错误 (code {code}): {msg}")

        data = result.get("data") or {}
        videos = data.get("videos") if isinstance(data, dict) else None
        if not isinstance(videos, list):
            return []

        # 按播放量排序，只对前 N 条调详情（点赞/评论数仅详情接口提供）
        videos = [v for v in videos if isinstance(v, dict)]
        videos.sort(key=lambda v: self._to_int(v.get("viewCount")), reverse=True)
        details = {}
        for v in videos[:self.detail_top]:
            vid = str(v.get("videoId") or "")
            if not vid:
                continue
            detail = self._fetch_detail(session, vid)
            if detail:
                details[vid] = detail
            time.sleep(0.2)

        return [self._normalize_item(v, keyword, details.get(str(v.get("videoId") or "")))
                for v in videos]

    def _fetch_detail(self, session, video_id):
        result = self.post_json(session, YOUTUBE_DETAIL_API, {"videoId": video_id})
        if result and result.get("code") in SUCCESS_CODES:
            data = result.get("data")
            if isinstance(data, dict) and data:
                return data
        return None

    def _normalize_item(self, item, keyword, detail=None):
        detail = detail or {}
        vid = str(item.get("videoId") or "")
        cover = ""
        thumbs = item.get("thumbnails")
        if isinstance(thumbs, list) and thumbs:
            best = max(thumbs,
                       key=lambda t: int(t.get("width") or 0) * int(t.get("height") or 0))
            cover = best.get("url") or ""

        # 发布时间：优先详情精确日期（"2026年7月24日"），回退列表相对时间（"1 day ago"）
        publish_ts = (self._parse_cn_date(detail.get("date"))
                      or self._parse_ts(item.get("publishedTime")))

        return self.make_record(
            title=item.get("title") or detail.get("title") or "",
            url=detail.get("videoUrl") or (f"https://www.youtube.com/watch?v={vid}" if vid else ""),
            author=item.get("author") or detail.get("author") or "",
            likes=self._parse_display_count(detail.get("likeCount")),
            comments=self._parse_display_count(detail.get("commentCount")),
            views=self._to_int(item.get("viewCount")) or self._parse_display_count(detail.get("viewCount")),
            publish_ts=publish_ts,
            keyword=keyword,
            extra={
                "shares": 0,
                "work_id": vid,
                "cover": cover,
                "duration": item.get("duration") or "",
                "channel_id": item.get("channelId") or "",
                "channel_handle": detail.get("channelHandle") or "",
            },
        )

    # ─── 本地化展示串解析 ────────────────────────────────────────────────────────
    @staticmethod
    def _parse_display_count(value):
        """
        解析 YouTube 本地化计数字符串 → int
        兼容："1928万" / "1,797,749,387次观看" / "244万" / "1.9M" / "24K" / 原始整数
        """
        if value is None:
            return 0
        if isinstance(value, (int, float)):
            return int(value)
        text = str(value).strip().replace(",", "").replace(" ", "")
        m = re.match(r"^([\d.]+)(.*)$", text)
        if not m:
            return 0
        try:
            num = float(m.group(1))
        except ValueError:
            return 0
        suffix = m.group(2).upper()
        if "亿" in suffix:
            mult = 100_000_000
        elif "万" in suffix:
            mult = 10_000
        elif "千" in suffix:
            mult = 1_000
        elif suffix.startswith("B"):
            mult = 1_000_000_000
        elif suffix.startswith("M"):
            mult = 1_000_000
        elif suffix.startswith("K"):
            mult = 1_000
        else:
            mult = 1
        return int(num * mult)

    @staticmethod
    def _parse_cn_date(value):
        """中文日期 "2026年7月24日" → 秒级时间戳"""
        if not value:
            return 0
        m = re.match(r"^(\d{4})年(\d{1,2})月(\d{1,2})日$", str(value).strip())
        if not m:
            return 0
        try:
            return int(datetime(int(m.group(1)), int(m.group(2)), int(m.group(3))).timestamp())
        except ValueError:
            return 0
