#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
wechat-article-style/scripts/rewrite.py

公众号文案改写辅助脚本
用途：上报改写记录接口

记录接口：https://redfox.hk/story/api/skill/record/save
网络实现：使用 requests 库，开启 SSL 证书验证

用法：
  python rewrite.py prompt                  # 输出公众号改写规则 prompt
  python rewrite.py "<文案内容>"           # 上报改写记录
"""

import sys
import os
import re
import json
from typing import Dict, Any

try:
    import requests
except ImportError:
    print('❌ 缺少 requests 依赖，请执行: pip install requests', file=sys.stderr)
    sys.exit(1)

# ── 路径 ──────────────────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RULES_FILE = os.path.join(SCRIPT_DIR, '..', 'assets', 'platform-rules.md')

# ── 平台 ──────────────────────────────────────────────────────────────────────
PLATFORM = '公众号'

# ── 记录接口配置 ───────────────────────────────────────────────────────────────
RECORD_URL = 'https://redfox.hk/story/api/skill/record/save'
REQUEST_TIMEOUT = 10


# ─────────────────────────────────────────────────────────────────────────────
# 规则提取
# ─────────────────────────────────────────────────────────────────────────────

def extract_platform_rules() -> str:
    """读取规则文件，提取公众号规则块。"""
    rules_path = os.path.normpath(RULES_FILE)
    if not os.path.exists(rules_path):
        print(f'❌ 规则文件不存在：{rules_path}', file=sys.stderr)
        sys.exit(1)

    with open(rules_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 提取公众号部分（从 ## 公众号 到文件末尾）
    match = re.search(r'^## 公众号\n(.*)', content, re.DOTALL | re.MULTILINE)
    if match:
        return '## 公众号\n' + match.group(1).strip()
    return ''


# ─────────────────────────────────────────────────────────────────────────────
# API Key 获取
# ─────────────────────────────────────────────────────────────────────────────

def _get_api_key():
    """从当前环境变量获取 REDFOX_API_KEY"""
    api_key = os.environ.get("REDFOX_API_KEY", "")
    if not api_key:
        raise SystemExit(
            "❌ 未配置 REDFOX_API_KEY。\n"
            "本 skill 调用红狐接口仅用于记录改写次数，使用完全免费，不会扣除任何积分。\n"
            "请先获取免费 API Key：https://redfox.hk/settings/api-keys?source=github\n"
            "然后配置环境变量：export REDFOX_API_KEY=<你的apikey>"
        )
    return api_key


# ─────────────────────────────────────────────────────────────────────────────
# 记录接口：使用 requests 库，开启 SSL 证书验证
# ─────────────────────────────────────────────────────────────────────────────

def report_rewrite(content: str) -> Dict[str, Any]:
    """
    向记录接口发送 POST 请求。

    技术要点：
      - 使用 requests 库发送 POST 请求
      - verify=True（默认），开启 SSL 证书验证
      - 超时 10 秒
    """
    payload = {'source': '公众号文案改写-GitHub'}
    headers = {
        'Content-Type': 'application/json; charset=utf-8',
        'User-Agent': 'wechat-article-style/1.0',
        'X-API-Key': _get_api_key(),
    }

    try:
        resp = requests.post(
            RECORD_URL,
            json=payload,
            headers=headers,
            timeout=REQUEST_TIMEOUT,
            verify=True,
        )
        return {
            'ok': resp.ok,
            'status_code': resp.status_code,
            'status_line': f'HTTP {resp.status_code} {resp.reason}',
        }
    except requests.exceptions.SSLError as e:
        return {'ok': False, 'error': f'SSL certificate verification failed: {e}'}
    except requests.exceptions.ConnectionError as e:
        return {'ok': False, 'error': f'Connection failed: {e}'}
    except requests.exceptions.Timeout as e:
        return {'ok': False, 'error': f'Request timeout: {e}'}
    except requests.exceptions.RequestException as e:
        return {'ok': False, 'error': f'Request failed: {e}'}


# ─────────────────────────────────────────────────────────────────────────────
# CLI 命令
# ─────────────────────────────────────────────────────────────────────────────

def cmd_prompt() -> None:
    """输出公众号改写规则 prompt。"""
    rules = extract_platform_rules()
    if not rules:
        print(f'\n❌ 规则文件中未找到公众号规则\n', file=sys.stderr)
        sys.exit(1)

    print(f'\n✅ 平台：{PLATFORM}\n')
    print('─' * 60)
    print('\n【System Prompt（供 AI 使用）】\n')
    print(rules)


def cmd_report(content: str) -> None:
    """上报改写记录。"""
    print(f'\n📡 上报改写记录…')
    result = report_rewrite(content)
    if result.get('ok'):
        print(f'✅ 上报成功（HTTP {result.get("status_code")}）')
    else:
        print(
            f'⚠️  上报失败：{result.get("error") or result.get("status_line")}',
            file=sys.stderr
        )


def print_help() -> None:
    print(f"""
📝 公众号文案改写辅助脚本

用法：
  python rewrite.py prompt                    # 输出公众号改写规则 prompt
  python rewrite.py "<文案内容>"              # 上报改写记录

注意：
  记录接口使用 requests 库，开启 SSL 证书验证。
""")


# ─────────────────────────────────────────────────────────────────────────────
# 入口
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    args = sys.argv[1:]

    if not args or args[0] in ('-h', '--help'):
        print_help()
        sys.exit(0)

    first = args[0].lower()

    # ── prompt ──────────────────────────────────────────────────────────────
    if first == 'prompt':
        cmd_prompt()
        return

    # ── 上报记录 ────────────────────────────────────────────────────────────
    content = ' '.join(args)
    cmd_report(content)


if __name__ == '__main__':
    main()
