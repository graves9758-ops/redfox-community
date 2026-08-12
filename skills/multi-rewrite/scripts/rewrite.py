#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
copywriter-rewriter/scripts/rewrite.py

文案改写辅助脚本（Python 版）
用途：读取平台规则、输出 system prompt，并在调用时上报记录接口。
支持同时指定多个平台，逐一上报。

记录接口：https://redfox.hk/story/api/skill/record/save
网络实现：原生 urllib，默认 SSL 证书验证
说明：接口仅用于记录，需通过环境变量 REDFOX_API_KEY 鉴权（X-API-Key 请求头传入）

用法：
  python rewrite.py list                        # 列出所有支持平台
  python rewrite.py <平台>                      # 输出单平台改写规则 prompt
  python rewrite.py <平台1,平台2,...> <文案>    # 多平台批量上报改写记录
  python rewrite.py all <文案>                  # 全平台上报改写记录
"""

import sys
import os
import re
import json
import urllib.request
import urllib.error
from typing import Optional, Dict, Any, List

# ── 路径 ──────────────────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RULES_FILE = os.path.join(SCRIPT_DIR, '..', 'assets', 'platform-rules.md')

# ── 平台别名映射 ──────────────────────────────────────────────────────────────
PLATFORM_ALIAS: Dict[str, str] = {
    '公众号':     '公众号',
    '微信公众号': '公众号',
    '视频号':     '视频号',
    '微信视频号': '视频号',
    '抖音':       '抖音',
    'dy':         '抖音',
    '快手':       '快手',
    'ks':         '快手',
    '哔站':       '哔站（B站）',
    'b站':        '哔站（B站）',
    'bilibili':   '哔站（B站）',
    '哔哩哔哩':   '哔站（B站）',
    '小红书':     '小红书',
    '红书':       '小红书',
    'xhs':        '小红书',
    '知乎':       '知乎',
    'zhihu':      '知乎',
}

SUPPORTED_PLATFORMS: List[str] = [
    '公众号', '视频号', '抖音', '快手', '哔站（B站）', '小红书', '知乎'
]

# 全平台关键词
ALL_KEYWORDS = {'全部', 'all', '所有'}

# ── 记录接口配置 ───────────────────────────────────────────────────────────────
RECORD_URL = 'https://redfox.hk/story/api/skill/record/save'


# ─────────────────────────────────────────────────────────────────────────────
# 平台解析
# ─────────────────────────────────────────────────────────────────────────────

def resolve_platforms(tokens: List[str]) -> List[str]:
    """
    从 token 列表中识别所有平台，返回去重后的规范平台名列表。
    支持逗号分隔（如 "抖音,小红书"）或空格分隔（如 "抖音 小红书"）。
    若包含全平台关键词，直接返回全部七个平台。
    """
    # 展开逗号
    expanded: List[str] = []
    for t in tokens:
        expanded.extend(t.split(','))

    # 检查全平台
    for t in expanded:
        if t.strip().lower() in ALL_KEYWORDS:
            return list(SUPPORTED_PLATFORMS)

    seen: List[str] = []
    for t in expanded:
        t = t.strip()
        matched = PLATFORM_ALIAS.get(t) or PLATFORM_ALIAS.get(t.lower())
        if matched and matched not in seen:
            seen.append(matched)
    return seen


# ─────────────────────────────────────────────────────────────────────────────
# 规则提取
# ─────────────────────────────────────────────────────────────────────────────

def extract_platform_rules(platform_name: str) -> Optional[str]:
    """读取规则文件，提取指定平台的完整规则块。"""
    rules_path = os.path.normpath(RULES_FILE)
    if not os.path.exists(rules_path):
        print(f'❌ 规则文件不存在：{rules_path}', file=sys.stderr)
        sys.exit(1)

    with open(rules_path, 'r', encoding='utf-8') as f:
        content = f.read()

    sections = re.split(r'^## ', content, flags=re.MULTILINE)
    for section in sections:
        if not section.strip():
            continue
        first_line = section.split('\n')[0].strip()
        base = first_line.split('（')[0]
        if (first_line == platform_name
                or platform_name in first_line
                or base in platform_name):
            return '## ' + section.strip()
    return None


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
# 记录接口：原生 urllib，默认 SSL 证书验证（需 REDFOX_API_KEY 鉴权）
# ─────────────────────────────────────────────────────────────────────────────

def report_rewrite(platform: str, content: str) -> Dict[str, Any]:
    """
    向记录接口发送 POST 请求。

    技术要点：
      - 使用原生 urllib.request，默认 SSL 证书验证
      - 接口仅用于记录，需通过 REDFOX_API_KEY 鉴权（X-API-Key 请求头传入）
    """
    payload = json.dumps(
        {'source': '多平台文案改写-GitHub'},
        ensure_ascii=False
    ).encode('utf-8')

    req = urllib.request.Request(
        RECORD_URL,
        data=payload,
        headers={
            'Content-Type': 'application/json; charset=utf-8',
            'User-Agent': 'copywriter-rewriter/1.0',
            'X-API-Key': _get_api_key(),
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

def cmd_list() -> None:
    """列出所有支持平台及别名。"""
    print('\n支持的平台及别名：\n')
    print(f'{"平台名称":<18} | 可识别的别名')
    print('-' * 18 + '-+-' + '-' * 40)
    printed: set = set()
    for alias, platform in PLATFORM_ALIAS.items():
        if platform not in printed:
            aliases = [k for k, v in PLATFORM_ALIAS.items() if v == platform]
            print(f'{platform:<18} | {", ".join(aliases)}')
            printed.add(platform)
    print()


def cmd_platform_prompt(platform_input: str) -> None:
    """输出单个平台的改写规则 prompt。"""
    matched = PLATFORM_ALIAS.get(platform_input) or PLATFORM_ALIAS.get(platform_input.lower())
    if not matched:
        print(f'\n❌ 未识别的平台："{platform_input}"\n', file=sys.stderr)
        print(f'支持的平台：{"、".join(SUPPORTED_PLATFORMS)}\n', file=sys.stderr)
        sys.exit(1)

    rules = extract_platform_rules(matched)
    if not rules:
        print(f'\n❌ 规则文件中未找到平台"{matched}"的规则\n', file=sys.stderr)
        sys.exit(1)

    print(f'\n✅ 平台：{matched}\n')
    print('─' * 60)
    print('\n【System Prompt（供 AI 使用）】\n')
    print(rules)


def cmd_batch_report(platform_tokens: List[str], content: str) -> None:
    """
    解析多平台，逐一上报记录接口。
    platform_tokens: 可能含逗号分隔或多个独立 token
    """
    platforms = resolve_platforms(platform_tokens)

    if not platforms:
        print(f'\n❌ 未从输入中识别到任何有效平台：{platform_tokens}\n', file=sys.stderr)
        print(f'支持的平台：{"、".join(SUPPORTED_PLATFORMS)}\n', file=sys.stderr)
        sys.exit(1)

    print(f'\n📋 目标平台（共 {len(platforms)} 个）：{"、".join(platforms)}\n')
    print('═' * 60)

    for idx, platform in enumerate(platforms, 1):
        print(f'\n[{idx}/{len(platforms)}] 📌 {platform}')
        print(f'📡 上报改写记录…')
        result = report_rewrite(platform, content)
        if result.get('ok'):
            print(f'✅ 上报成功（HTTP {result.get("status_code")}）')
        else:
            print(
                f'⚠️  上报失败：{result.get("error") or result.get("status_line")}',
                file=sys.stderr
            )

    print('═' * 60)
    print(f'\n✅ 全部 {len(platforms)} 个平台处理完毕\n')


def print_help() -> None:
    platforms = '、'.join(SUPPORTED_PLATFORMS)
    print(f"""
📝 文案改写辅助脚本（Python 版）

用法：
  python rewrite.py list                          # 列出所有支持平台
  python rewrite.py <平台>                        # 输出单平台改写规则 prompt
  python rewrite.py <平台1,平台2> <文案内容>      # 多平台批量上报（逗号分隔）
  python rewrite.py 抖音 小红书 知乎 <文案内容>   # 多平台批量上报（空格分隔）
  python rewrite.py all <文案内容>                # 全平台上报

支持平台：{platforms}
全平台关键词：全部、all、所有

注意：
  记录接口使用原生 urllib，默认 SSL 证书验证，需配置 REDFOX_API_KEY 鉴权（X-API-Key 请求头传入）。
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

    # ── list ──────────────────────────────────────────────────────────────
    if first == 'list':
        cmd_list()
        return

    # ── 判断是否为单平台 prompt 查询（无文案内容）─────────────────────────
    # 策略：若只有一个 token 且能精确匹配到平台，视为 prompt 查询
    if len(args) == 1:
        matched = (PLATFORM_ALIAS.get(args[0])
                   or PLATFORM_ALIAS.get(args[0].lower()))
        if matched:
            cmd_platform_prompt(args[0])
            return
        # 单 token 但不认识
        print(f'\n❌ 未识别的平台或命令："{args[0]}"\n', file=sys.stderr)
        print_help()
        sys.exit(1)

    # ── 多 token：尝试从前缀识别平台，其余部分作为文案 ───────────────────
    # 从左到右扫描，连续能识别为平台的 token 归入平台列表，之后视为文案
    platform_tokens: List[str] = []
    content_start = len(args)  # 默认无文案

    for i, token in enumerate(args):
        # 展开逗号分隔
        sub_tokens = token.split(',')
        all_platform = all(
            (PLATFORM_ALIAS.get(t.strip()) or PLATFORM_ALIAS.get(t.strip().lower())
             or t.strip().lower() in ALL_KEYWORDS)
            for t in sub_tokens if t.strip()
        )
        if all_platform:
            platform_tokens.append(token)
        else:
            content_start = i
            break

    content = ' '.join(args[content_start:]) if content_start < len(args) else ''

    if not platform_tokens:
        # 没有识别到任何平台 token
        print(f'\n❌ 输入中未找到可识别的平台关键词\n', file=sys.stderr)
        print(f'支持的平台：{"、".join(SUPPORTED_PLATFORMS)}\n', file=sys.stderr)
        print_help()
        sys.exit(1)

    cmd_batch_report(platform_tokens, content)


if __name__ == '__main__':
    main()
