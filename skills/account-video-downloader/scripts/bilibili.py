#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
哔哩哔哩平台视频下载器
"""

import json
import re

import requests

from .base import (
    API_BASE,
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    BaseDownloader,
)


class BilibiliDownloader(BaseDownloader):
    """B站账号视频下载器"""

    WORKS_ENDPOINT = "/story/api/bili/data/accountWorkList"
    DOWNLOAD_ENDPOINT = "/story/api/parseWork/videoDownload/bilibili"

    def __init__(self, api_key: str):
        super().__init__(api_key, "bilibili", "B站")

    @staticmethod
    def _extract_mid(account_id: str) -> str:
        """从B站主页链接中提取 mid"""
        m = re.search(r'space\.bilibili\.com/(\d+)', account_id)
        return m.group(1) if m else ""

    def validate_account_id(self, account_id: str) -> tuple:
        """B站账号标识为账号主页链接（accountUrl）"""
        if not account_id or len(account_id) < 5:
            return False, f"「{account_id}」不是有效的B站主页链接，请提供完整的个人空间 URL。"
        if "bilibili.com" not in account_id and "b23.tv" not in account_id:
            return False, f"「{account_id}」不是B站域名链接，请提供如 https://space.bilibili.com/123456 格式的主页 URL。"
        return True, ""

    def description_hint(self) -> str:
        return "请提供B站账号的主页链接（如 https://space.bilibili.com/123456）。"

    def fetch_works(self, account_id: str, page_size: int = DEFAULT_PAGE_SIZE, page_num: int = 1,
                    date_start: str = "", date_end: str = "") -> dict:
        mid = self._extract_mid(account_id)
        payload = {
            "accountUrl": account_id,
            "page": page_num,
            "pageSize": min(page_size, MAX_PAGE_SIZE),
            "order": "time",
            "source": "多平台主页作品提取-GitHub",
        }
        if mid:
            payload["mid"] = mid

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

        code = result.get("code")
        msg = result.get("msg", "")

        if code in (200, 2000):
            data_raw = result.get("data", {})
            if not data_raw:
                return {"success": False, "account": None, "works": [],
                        "error": "未查询到该账号的作品数据，可能账号尚未收录"}

            # B站 API 返回 data.workList
            raw_works = data_raw.get("workList", []) if isinstance(data_raw, dict) else []

            works = [self._normalize_work(w, account_id) for w in raw_works]

            # 提取账号信息：用第一条作品的 author 作为账号名
            account_info = {"accountId": account_id}
            if works:
                account_info["accountName"] = works[0].get("authorName", account_id)
            else:
                account_info["accountName"] = account_id
            # B站 API 无粉丝数返回
            account_info["followerCount"] = None

            # B站 API 返回 total（作品总数），用于精确判断 has_more
            total_count = data_raw.get("total", 0)
            has_more = (page_num * min(page_size, MAX_PAGE_SIZE)) < total_count

            return {
                "success": True,
                "account": account_info,
                "works": works,
                "error": None,
                "has_more": has_more,
            }

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

    def _normalize_work(self, work: dict, account_id: str) -> dict:
        """B站视频字段归一化"""
        bv_id = work.get("bvId", "")
        return {
            "title": work.get("title") or "",
            "workUrl": f"https://www.bilibili.com/video/{bv_id}" if bv_id else (work.get("url") or ""),
            "publishTime": work.get("created") or work.get("publishTime") or "",
            "likeCount": work.get("likeCount", 0),
            "commentCount": work.get("commentCount", 0),
            "collectCount": work.get("favoriteCount", 0),
            "shareCount": work.get("shareCount", 0),
            "authorName": work.get("author") or work.get("authorName") or account_id,
            "followerCount": 0,
        }

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
            result["cover"] = payload_data.get("cover") or payload_data.get("coverUrl")

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
