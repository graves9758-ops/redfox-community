#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抖音平台视频下载器
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


class DouyinDownloader(BaseDownloader):
    """抖音账号视频下载器"""

    WORKS_ENDPOINT = "/story/api/dy/data/listWorkByAccount"
    DOWNLOAD_ENDPOINT = "/story/api/parseWork/videoDownload/douyin"

    def __init__(self, api_key: str):
        super().__init__(api_key, "douyin", "抖音")

    def validate_account_id(self, account_id: str) -> tuple:
        """抖音只接受抖音号（uniqueName），拒绝 URL / 昵称 / sec_uid"""
        if not account_id or len(account_id) < 2:
            return False, "请输入抖音号。"

        # 拒绝主页链接
        if "douyin.com" in account_id:
            return False, (
                "抖音不支持主页链接，请提供**抖音号**。\n"
                "抖音号获取方式：抖音 APP → 目标账号主页 → 头像下方「抖音号：xxx」字段（例如 JCLjiangchenglan）。"
            )

        # 拒绝中文昵称
        if re.search(r'[\u4e00-\u9fff]', account_id):
            return False, (
                f"「{account_id}」是账号昵称而非抖音号。抖音昵称可能重名，请提供唯一的**抖音号**。\n"
                "获取方式：抖音 APP → 目标账号主页 → 头像下方「抖音号：xxx」字段。"
            )

        # 拒绝 sec_uid（长哈希值，非抖音号）
        if len(account_id) > 20:
            return False, (
                "这看起来是加密的用户 ID（sec_uid），不是抖音号。请提供**抖音号**。\n"
                "获取方式：抖音 APP → 目标账号主页 → 头像下方「抖音号：xxx」字段（例如 JCLjiangchenglan）。"
            )

        return True, ""

    def description_hint(self) -> str:
        return "请提供抖音号（抖音 APP → 目标主页 → 头像下方「抖音号」字段，如 JCLjiangchenglan）。"

    def fetch_works(self, account_id: str, page_size: int = DEFAULT_PAGE_SIZE, page_num: int = 1,
                    date_start: str = "", date_end: str = "") -> dict:
        payload = {
            "uniqueName": account_id,
            "shortId": "",
            "pageNum": page_num,
            "pageSize": min(page_size, MAX_PAGE_SIZE),
            "source": "多平台主页作品提取-GitHub",
        }
        if date_start:
            payload["startDate"] = date_start
        if date_end:
            payload["endDate"] = date_end

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

            if isinstance(data_raw, list):
                raw_works = data_raw
            elif isinstance(data_raw, dict):
                raw_works = data_raw.get("list") or []
            else:
                raw_works = []

            works = [self._normalize_work(w, account_id) for w in raw_works]

            account_info = {"accountId": account_id}
            if works:
                account_info["accountName"] = works[0].get("authorName", account_id)
                account_info["followerCount"] = works[0].get("followerCount", 0)
            else:
                account_info["accountName"] = account_id

            return {
                "success": True,
                "account": account_info,
                "works": works,
                "error": None,
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
        """抖音视频字段归一化"""
        return {
            "title": work.get("content") or work.get("title") or "",
            "workUrl": work.get("opusUrl") or work.get("workUrl") or "",
            "publishTime": work.get("publishTime") or "",
            "likeCount": work.get("likeCount", 0),
            "commentCount": work.get("commentCount", 0),
            "collectCount": work.get("collectCount", 0),
            "shareCount": work.get("shareCount", 0),
            "authorName": work.get("authorName") or work.get("nickname") or account_id,
            "followerCount": work.get("authorFansCount") or work.get("followerCount") or 0,
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
