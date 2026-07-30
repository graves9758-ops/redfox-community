#!/usr/bin/env python3
"""
X (Twitter) 平台适配器
接口已实测（2026-07）：
  search  POST {"keyword": "...", "searchType": "Top", "cursor": ""}
          → data.tweets[]（20条/页）+ nextCursor 分页
          单条自带 likeCount/replyCount/retweetCount/viewCount/createdAt
  tweetDetail / tweetComments：备用（评论内容分析场景）
注意：searchType 为必填参数（Top=热门 / Latest=最新），缺失会报 3203 上游错误。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import X_SEARCH_API, SOURCE, SUCCESS_CODES
from .base import BaseSource, PlatformUnavailable


class XSource(BaseSource):
    platform = "x"
    display_name = "X"
    #: Top=热门推文（互动量高）/ Latest=最新推文
    search_type = "Top"

    def search(self, session, keyword):
        payload = {
            "keyword": keyword,
            "searchType": self.search_type,
            "cursor": "",
            "source": SOURCE,
        }
        result = self.post_json(session, X_SEARCH_API, payload)
        if result is None:
            raise PlatformUnavailable("X 搜索请求失败（网络异常）")

        code = result.get("code")
        if code not in SUCCESS_CODES:
            msg = result.get("msg", "")
            if code == 3203:
                raise PlatformUnavailable(f"X 上游能力故障（RedFox 侧）: {msg}")
            raise PlatformUnavailable(f"X 搜索接口错误 (code {code}): {msg}")

        data = result.get("data") or {}
        tweets = data.get("tweets") if isinstance(data, dict) else None
        if not isinstance(tweets, list):
            return []

        return [self._normalize_item(t, keyword) for t in tweets]

    def _normalize_item(self, item, keyword):
        user = item.get("user") or {}
        username = item.get("username") or user.get("username") or ""
        tweet_id = str(item.get("tweetId") or "")
        url = (f"https://x.com/{username}/status/{tweet_id}"
               if username and tweet_id else "")

        return self.make_record(
            title=item.get("text") or "",
            url=url,
            author=user.get("displayName") or username,
            likes=item.get("likeCount"),
            comments=item.get("replyCount"),
            views=item.get("viewCount"),
            publish_ts=self._parse_ts(item.get("createdAt")),
            keyword=keyword,
            extra={
                "shares": self._to_int(item.get("retweetCount")),
                "work_id": tweet_id,
                "language": item.get("language") or "",
                "followers": self._to_int(user.get("followers")),
            },
        )
