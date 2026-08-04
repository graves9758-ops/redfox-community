#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快手平台视频下载器
"""

import json
import re
import sys

import requests

from .base import (
    API_BASE,
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    BaseDownloader,
    error,
    info,
    warn,
)


class KuaishouDownloader(BaseDownloader):
    """快手账号视频下载器"""

    # 平台端点
    WORKS_ENDPOINT = "/story/api/ksAllData/queryWorkList"
    DOWNLOAD_ENDPOINT = "/story/api/parseWork/videoDownload/kuaishou"

    def __init__(self, api_key: str):
        super().__init__(api_key, "kuaishou", "快手")

    def validate_account_id(self, account_id: str) -> tuple:
        """快手只接受 kwaiId，拒绝 URL / 昵称"""
        if not account_id or len(account_id) < 2:
            return False, "请输入快手账号 ID（kwaiId）。"

        # 拒绝主页链接
        if "kuaishou.com" in account_id or "kuaishou.cn" in account_id:
            return False, (
                "快手不支持主页链接，请提供**账号 ID（kwaiId）**。\n"
                "获取方式：快手 APP → 目标账号主页 → 昵称下方显示的 ID（例如 junningjunning666）。"
            )

        # 拒绝中文昵称
        if re.search(r'[\u4e00-\u9fff]', account_id):
            return False, (
                f"「{account_id}」是账号昵称而非 ID。快手昵称可能重名，请提供唯一的**账号 ID（kwaiId）**。\n"
                "获取方式：快手 APP → 目标账号主页 → 昵称下方显示的 ID。"
            )

        return True, ""

    def description_hint(self) -> str:
        return "请提供快手账号 ID / kwaiId（快手 APP → 目标主页 → 昵称下方显示，如 junningjunning666）。"

    def fetch_works(self, account_id: str, page_size: int = DEFAULT_PAGE_SIZE, page_num: int = 1,
                    date_start: str = "", date_end: str = "") -> dict:
        payload = {
            "kwaiId": account_id,
            "page": page_num,
            "size": min(page_size, MAX_PAGE_SIZE),
            "source": "多平台主页作品提取-GitHub",
        }

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

            # 提取账号信息：快手响应中每项有 nickname / authorFans
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
        """快手视频字段归一化"""
        photo_id = work.get("photoId", "")
        return {
            "title": work.get("caption") or work.get("title") or "",
            "workUrl": f"https://www.kuaishou.com/short-video/{photo_id}" if photo_id else (work.get("workUrl") or ""),
            "publishTime": work.get("publishTime") or "",
            "likeCount": work.get("likeCount", 0),
            "commentCount": work.get("commentCount", 0),
            "collectCount": work.get("collectCount") or 0,
            "shareCount": work.get("shareCount", 0),
            "authorName": work.get("nickname") or work.get("authorName") or account_id,
            "followerCount": work.get("authorFans") or work.get("authorFansCount") or 0,
            # 作品列表接口直接返回无水印 mp4 地址，无需再调下载接口
            "directVideoUrl": work.get("videoUrl") or "",
            "coverUrl": work.get("coverUrl") or "",
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

        payload_data = data.get("data")
        if not payload_data:
            return {"success": False, "download_url": None, "title": None, "cover": None,
                    "duration": None, "resources": [], "error": "API 返回空数据"}

        return self._parse_download_data(payload_data)

    def _parse_download_data(self, payload_data) -> dict:
        """解析下载接口返回数据，提取资源链接"""
        result = {
            "success": True,
            "download_url": None,
            "title": None,
            "cover": None,
            "duration": None,
            "resources": [],
            "error": None,
        }

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
