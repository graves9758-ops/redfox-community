#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
xiaohongshu-rewriting/scripts/rewrite.py

小红书文案改写辅助脚本
用途：上报改写记录接口

记录接口：https://redfox.hk/story/api/skill/record/save
网络实现：原生 urllib，默认 SSL 证书验证
说明：接口仅用于记录，无需鉴权

用法：
  python rewrite.py prompt                  # 输出小红书改写规则 prompt
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
PLATFORM = '小红书'

# ── 记录接口配置 ───────────────────────────────────────────────────────────────
RECORD_URL = 'https://redfox.hk/story/api/skill/record/save'


# ─────────────────────────────────────────────────────────────────────────────
# 规则提取
# ─────────────────────────────────────────────────────────────────────────────

def extract_platform_rules() -> str:
    """读取规则文件，提取小红书规则块。"""
    rules_path = os.path.normpath(RULES_FILE)
    if not os.path.exists(rules_path):
        print(f'❌ 规则文件不存在：{rules_path}', file=sys.stderr)
        sys.exit(1)

    with open(rules_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 提取小红书部分（从 ## 小红书 到文件末尾）
    match = re.search(r'^## 小红书\n(.*)', content, re.DOTALL | re.MULTILINE)
    if match:
        return '## 小红书\n' + match.group(1).strip()
    return ''


# ─────────────────────────────────────────────────────────────────────────────
# 记录接口：原生 urllib，默认 SSL 证书验证（无需鉴权）
# ─────────────────────────────────────────────────────────────────────────────

def report_rewrite(content: str) -> Dict[str, Any]:
    """
    向记录接口发送 POST 请求。

    技术要点：
      - 使用原生 urllib.request，默认 SSL 证书验证
      - 接口仅用于记录，无需鉴权
    """
    payload = json.dumps(
        {'source': '小红书文案改写-GitHub'},
        ensure_ascii=False
    ).encode('utf-8')

    req = urllib.request.Request(
        RECORD_URL,
        data=payload,
        headers={
            'Content-Type': 'application/json; charset=utf-8',
            'User-Agent': 'xiaohongshu-rewriting/1.0',
        },
        method='POST',
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return {
                'ok': True,
                'status_code': resp.status,
                'status_line': f'HTTP {resp.status}',
            }
    except urllib.error.HTTPError as e:
        return {
            'ok': False,
            'status_code': e.code,
            'status_line': f'HTTP {e.code}',
            'error': str(e),
        }
    except Exception as e:
        return {
            'ok': False,
            'error': str(e),
        }


# ─────────────────────────────────────────────────────────────────────────────
# CLI 命令
# ─────────────────────────────────────────────────────────────────────────────

def cmd_prompt() -> None:
    """输出小红书改写规则 prompt。"""
    rules = extract_platform_rules()
    if not rules:
        print(f'\n❌ 规则文件中未找到小红书规则\n', file=sys.stderr)
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
📝 小红书文案改写辅助脚本

用法：
  python rewrite.py prompt                    # 输出小红书改写规则 prompt
  python rewrite.py "<文案内容>"              # 上报改写记录

注意：
  记录接口使用原生 urllib，默认 SSL 证书验证，无需鉴权。
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
