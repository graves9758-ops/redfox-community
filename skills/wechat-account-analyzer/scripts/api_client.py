"""api_client.py — 红狐 API HTTP 通信层

职责：API 凭证管理、HTTP POST 请求封装。
被 analyzer.py 和 report.py 调用。
"""

import json
import os
import re
import sys

import requests


# ── API 常量 ──
API_HOST = "redfox.hk"
API_PATH_SEARCH_USER = "/story/api/gzh/data/searchUser"  # 接口1：关键词搜索账号 → 获取微信号
API_PATH_QUERY_DATA = "/story/api/gzhUser/queryData"      # 接口2：按微信号+名称精确查询完整数据
RAW_DATA_FILE = "raw_data.json"


def _read_from_shell_config():
    """从shell配置文件中尝试读取REDFOX_API_KEY（仅macOS/Linux）"""
    if sys.platform == "win32":
        return None
    home = os.path.expanduser("~")
    config_files = [
        os.path.join(home, ".zshrc"),
        os.path.join(home, ".bashrc"),
        os.path.join(home, ".bash_profile"),
        os.path.join(home, ".profile"),
    ]
    for config_file in config_files:
        try:
            if os.path.isfile(config_file):
                with open(config_file, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                match = re.search(r'export\s+REDFOX_API_KEY\s*=\s*["\']?([^"\'\n]+)["\']?', content)
                if match:
                    return match.group(1).strip()
        except (OSError, PermissionError):
            continue
    return None


def _get_credential():
    """获取API凭证 - 优先从环境变量REDFOX_API_KEY读取，其次从shell配置文件读取"""
    credential = os.getenv("REDFOX_API_KEY")
    if credential and credential.strip():
        return credential.strip()

    # 环境变量未设置，尝试从shell配置文件读取
    credential = _read_from_shell_config()
    if credential:
        return credential

    raise ValueError(
        "未找到 REDFOX_API_KEY，请配置环境变量后重试。\n"
        "  macOS/Linux: export REDFOX_API_KEY=<你的apikey>\n"
        "  Windows:     [Environment]::SetEnvironmentVariable('REDFOX_API_KEY', '<值>', 'User')\n"
        "获取API Key: 访问 https://redfox.hk/ 注册后在个人中心获取"
    )


def _get_headers():
    """获取请求头"""
    return {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-API-KEY": _get_credential(),
    }


def https_post(path, body_dict):
    """POST请求"""
    url = f"https://{API_HOST}{path}"
    body_json = json.dumps(body_dict, ensure_ascii=False)
    response = requests.post(url, data=body_json.encode("utf-8"), headers=_get_headers(), timeout=30)
    return response.json()
