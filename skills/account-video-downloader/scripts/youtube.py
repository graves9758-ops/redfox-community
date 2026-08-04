#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YouTube 平台视频下载器
"""

import json

import requests

from .base import (
    API_BASE,
    DEFAULT_PAGE_SIZE,
    BaseDownloader,
)


class YouTubeDownloader(BaseDownloader):
    """YouTube 频道视频下载器

    翻页机制：使用 YouTube 原生 continuation token，非传统 pageNum/pageSize。
    每页约 100 条视频。
    """

    WORKS_ENDPOINT = "/story/api/youtube/channel/videos"
    DOWNLOAD_ENDPOINT = "/story/api/parseWork/videoDownload/youtube"

    def __init__(self, api_key: str):
        super().__init__(api_key, "youtube", "YouTube")
        self._continuation_token = None   # 翻页 token
        self._has_more = False            # 是否还有更多页

    def validate_account_id(self, account_id: str) -> tuple:
        """YouTube 频道标识为频道 URL（channel）"""
        if not account_id or len(account_id) < 5:
            return False, f"「{account_id}」不是有效的 YouTube 频道标识，请提供频道 URL。"
        return True, ""

    def description_hint(self) -> str:
        return "请提供 YouTube 频道 URL（如 https://www.youtube.com/@channelname 或 https://www.youtube.com/channel/UC...）。"

    def fetch_works(self, account_id: str, page_size: int = DEFAULT_PAGE_SIZE, page_num: int = 1,
                    date_start: str = "", date_end: str = "") -> dict:
        """
        拉取 YouTube 频道视频列表。

        翻页机制：首页传 channel，后续页传 continuation token。
        page_size 参数在此平台上不生效（每页固定约 100 条）。
        """
        # 翻页逻辑：page_num==1 首页传 channel；后续页传 continuation token
        if page_num <= 1:
            self._continuation_token = None
            payload = {"channel": account_id, "source": "多平台主页作品提取-GitHub"}
        elif self._continuation_token:
            payload = {"continuation": self._continuation_token, "source": "多平台主页作品提取-GitHub"}
        else:
            return {"success": False, "account": None, "works": [],
                    "error": "无更多页面可翻（请从首页开始或等待 continuation token）"}

        url = f"{API_BASE}{self.WORKS_ENDPOINT}"
        headers = {
            "Content-Type": "application/json",
            "REDFOX_API_KEY": self.api_key,
        }

        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=30)
            result = resp.json()
        except requests.exceptions.Timeout:
            return {"success": False, "account": None, "works": [], "error": "请求超时，请稍后重试"}
        except requests.exceptions.RequestException as e:
            return {"success": False, "account": None, "works": [], "error": f"网络请求失败: {e}"}
        except json.JSONDecodeError:
            return {"success": False, "account": None, "works": [], "error": "API 返回无效数据"}

        # YouTube API 响应可能被 redfox 的 {code, data, msg} 包裹，也可能直接返回
        code = result.get("code")
        msg = result.get("msg", "")

        if code is not None:
            # 标准 redfox 包裹格式
            if code not in (200, 2000):
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
            data_raw = result.get("data", result)
        else:
            # 直接返回数据（无 code 包裹）
            data_raw = result

        return self._parse_channel_response(data_raw, account_id)

    def get_download_info(self, work_url: str) -> dict:
        payload = {"url": work_url, "source": "多平台主页作品提取-GitHub"}
        url = f"{API_BASE}{self.DOWNLOAD_ENDPOINT}"
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

        return self._parse_download_data(data.get("data"))

    def _parse_channel_response(self, data_raw: dict, account_id: str) -> dict:
        """解析 YouTube 频道视频 API 响应

        响应结构：
        {
          "results": [...],
          "playlist_info": {"title": "...", "numVideos": "5200", ...},
          "continuation_token": "...",
          "has_more": true
        }
        """
        if not data_raw or not isinstance(data_raw, dict):
            return {"success": False, "account": None, "works": [],
                    "error": "未查询到该频道的作品数据，可能频道尚未收录"}

        # 提取视频列表
        raw_works = data_raw.get("results", [])
        if not raw_works:
            return {"success": True,
                    "account": {"accountId": account_id, "accountName": account_id},
                    "works": [], "error": None}

        works = [self._normalize_work(w, account_id) for w in raw_works]

        # 提取频道信息
        playlist_info = data_raw.get("playlist_info", {}) or {}
        account_info = {
            "accountId": account_id,
            "accountName": playlist_info.get("title") or account_id,
            "followerCount": None,
        }

        # 存储翻页 token
        self._continuation_token = data_raw.get("continuation_token")
        self._has_more = data_raw.get("has_more", False)

        return {
            "success": True,
            "account": account_info,
            "works": works,
            "error": None,
            "has_more": self._has_more,
            "continuation_token": self._continuation_token,
        }

    def _normalize_work(self, work: dict, account_id: str) -> dict:
        """YouTube 视频字段归一化

        API 返回字段：videoId, title, lengthText, viewCountText,
        thumbnails, channelHandle, channelId, channelTitle, index
        """
        video_id = work.get("videoId", "")
        # 封面取最高分辨率缩略图
        thumbnails = work.get("thumbnails", []) or []
        cover = thumbnails[-1].get("url") if thumbnails else ""
        return {
            "title": work.get("title") or "",
            "workUrl": f"https://www.youtube.com/watch?v={video_id}" if video_id else "",
            "publishTime": "",
            "likeCount": 0,
            "commentCount": 0,
            "collectCount": 0,
            "shareCount": 0,
            "authorName": work.get("channelTitle") or account_id,
            "followerCount": None,
            "coverUrl": cover,
        }

    def _parse_download_data(self, payload_data) -> dict:
        """解析下载接口返回数据"""
        result = {
            "success": True,
            "download_url": None,
            "title": None,
            "cover": None,
            "duration": None,
            "resources": [],
            "error": None,
        }

        if not payload_data:
            return {**result, "success": False, "error": "API 返回空数据"}

        if isinstance(payload_data, dict):
            result["title"] = payload_data.get("desc") or payload_data.get("title")
            result["cover"] = payload_data.get("cover") or payload_data.get("coverUrl") or payload_data.get("thumbnail")

            dur = payload_data.get("duration") or payload_data.get("durationSeconds")
            if isinstance(dur, (int, float)):
                result["duration"] = int(dur)

            resources = payload_data.get("resources", [])
            if isinstance(resources, list):
                result["resources"] = resources
                for res in resources:
                    if isinstance(res, dict):
                        rtype = res.get("type", "")
                        dl = res.get("downloadUrl") or res.get("url")
                        if dl and rtype == "video" and not result["download_url"]:
                            result["download_url"] = dl
                        if dl and rtype == "image":
                            if not result["cover"]:
                                result["cover"] = dl
                            if not result["download_url"]:
                                result["download_url"] = dl
                        res_dur = res.get("durationSeconds")
                        if isinstance(res_dur, (int, float)) and not result["duration"]:
                            result["duration"] = int(res_dur)

            if not result["download_url"]:
                result["download_url"] = (
                    payload_data.get("videoUrl")
                    or payload_data.get("video_url")
                    or payload_data.get("downloadUrl")
                    or payload_data.get("download_url")
                    or payload_data.get("playUrl")
                )

        return result
