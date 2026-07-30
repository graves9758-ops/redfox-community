#!/usr/bin/env python3
"""
overseas-trending-search — 统一配置与密钥加载
密钥加载优先级：--api-key 参数 > REDFOX_API_KEY 环境变量 > ~/.qoder/apis/redfox.json
"""

import json
import os
from pathlib import Path

# ─── RedFox 网关 ──────────────────────────────────────────────────────────────────
BASE_URL = "https://redfox.hk/story/api"

X_SEARCH_API = f"{BASE_URL}/x/search"
X_DETAIL_API = f"{BASE_URL}/x/tweetDetail"
X_COMMENTS_API = f"{BASE_URL}/x/tweetComments"

TIKTOK_SEARCH_API = f"{BASE_URL}/tiktok/ability/searchVideo"
TIKTOK_DETAIL_API = f"{BASE_URL}/tiktok/ability/awemeDetail"
TIKTOK_USER_AWEME_API = f"{BASE_URL}/tiktok/ability/userAwemeList"

# YouTube 接口（2026-07 实测）：searchVideo 列表 + videoDetail 补点赞/评论
YOUTUBE_SEARCH_API = f"{BASE_URL}/youtube/searchVideo"
YOUTUBE_DETAIL_API = f"{BASE_URL}/youtube/videoDetail"
YOUTUBE_COMMENTS_API = f"{BASE_URL}/youtube/videoComments"

# ─── 密钥与渠道 ────────────────────────────────────────────────────────────────────
CONFIG_FILE = Path.home() / ".qoder" / "apis" / "redfox.json"
ENV_KEY = "REDFOX_API_KEY"
SOURCE = "ChinaTrendingDigest-RedSkill"

DEFAULT_OUTPUT_DIR = Path.home() / "Downloads" / "QoderOverseasTrending"
SUCCESS_CODES = (200, 2000)


def get_api_key(cli_key=None):
    """按优先级加载 RedFox API Key，找不到返回 None"""
    if cli_key:
        return cli_key
    env_key = os.environ.get(ENV_KEY)
    if env_key:
        return env_key
    if CONFIG_FILE.exists():
        try:
            data = json.loads(CONFIG_FILE.read_text())
            key = data.get("api_key")
            if key:
                return key
        except (json.JSONDecodeError, OSError):
            pass
    return None


def make_session(api_key):
    """构造带认证头的 requests.Session（RedFox 网关统一 X-API-KEY 认证）"""
    import requests
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "X-API-KEY": api_key,
    })
    return session


def print_no_key_guide():
    print("╔══════════════════════════════════════════════════════╗")
    print("║  未配置 API Key，请通过以下方式之一配置：            ║")
    print("║                                                      ║")
    print("║  export REDFOX_API_KEY=ak_你的密钥                   ║")
    print("║  python3 digest.py --api-key ak_你的密钥              ║")
    print("║  echo '{\"api_key\":\"ak_你的密钥\"}' > ~/.qoder/apis/redfox.json ║")
    print("║                                                      ║")
    print("║  注册获取 Key: https://redfox.hk/settings/api-keys   ║")
    print("╚══════════════════════════════════════════════════════╝")
