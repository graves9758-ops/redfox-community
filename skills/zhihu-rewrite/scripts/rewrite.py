#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
zhihu-rewrite/scripts/rewrite.py

知乎文案改写辅助脚本
用途：上报改写记录接口

记录接口：https://redfox.hk/story/api/skill/record/save
网络实现：urllib.request（标准 SSL 校验，不跳过证书验证）

用法：
  python rewrite.py prompt                  # 输出知乎改写规则 prompt
  python rewrite.py "<文案内容>"           # 上报改写记录
"""

import sys
import os
import re
import json
import urllib.request
import urllib.error
from typing import Dict, Any

# ── 路径 ──────────────────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RULES_FILE = os.path.join(SCRIPT_DIR, '..', 'assets', 'platform-rules.md')

# ── 平台 ──────────────────────────────────────────────────────────────────────
PLATFORM = '知乎'

# ── 记录接口配置 ───────────────────────────────────────────────────────────────
RECORD_URL = 'https://redfox.hk/story/api/skill/record/save'


# ─────────────────────────────────────────────────────────────────────────────
# 规则提取
# ─────────────────────────────────────────────────────────────────────────────

def extract_platform_rules() -> str:
    """读取规则文件，提取知乎规则块。"""
    rules_path = os.path.normpath(RULES_FILE)
    if not os.path.exists(rules_path):
        print(f'❌ 规则文件不存在：{rules_path}', file=sys.stderr)
        sys.exit(1)

    with open(rules_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 提取知乎部分（从 ## 知乎 到文件末尾）
    match = re.search(r'^## 知乎\n(.*)', content, re.DOTALL | re.MULTILINE)
    if match:
        return '## 知乎\n' + match.group(1).strip()
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
# 记录接口：urllib.request，标准 SSL 校验
# ─────────────────────────────────────────────────────────────────────────────

def report_rewrite(content: str) -> Dict[str, Any]:
    """
    向记录接口发送 POST 请求。

    技术要点：
      - 使用 urllib.request 标准库发送请求
      - 默认开启 SSL 证书校验（不跳过，不设置 ssl.CERT_NONE）
      - 自动处理 TLS 握手与 SNI
    """
    payload = json.dumps(
        {'source': '知乎文案改写-GitHub'},
        ensure_ascii=False
    ).encode('utf-8')

    req = urllib.request.Request(
        RECORD_URL,
        data=payload,
        headers={
            'Content-Type': 'application/json; charset=utf-8',
            'User-Agent': 'zhihu-rewrite/1.0',
            'X-API-Key': _get_api_key(),
        },
        method='POST',
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            status_code = resp.status
            status_line = f'HTTP {resp.status} {resp.reason}'
            return {
                'ok': 200 <= status_code < 300,
                'status_code': status_code,
                'status_line': status_line,
            }
    except urllib.error.HTTPError as e:
        return {
            'ok': False,
            'status_code': e.code,
            'status_line': f'HTTP {e.code} {e.reason}',
        }
    except urllib.error.URLError as e:
        return {'ok': False, 'error': f'Request failed: {e.reason}'}
    except OSError as e:
        return {'ok': False, 'error': f'Network error: {e}'}


# ─────────────────────────────────────────────────────────────────────────────
# CLI 命令
# ─────────────────────────────────────────────────────────────────────────────

def cmd_prompt() -> None:
    """输出知乎改写规则 prompt。"""
    rules = extract_platform_rules()
    if not rules:
        print(f'\n❌ 规则文件中未找到知乎规则\n', file=sys.stderr)
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
📝 知乎文案改写辅助脚本

用法：
  python rewrite.py prompt                    # 输出知乎改写规则 prompt
  python rewrite.py "<文案内容>"              # 上报改写记录

注意：
  记录接口使用 urllib.request，标准 SSL 校验。
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
