#!/usr/bin/env python3
"""
HTML 报告分析数据回填脚本（X/Twitter 版）
将 AI 分析结果回填到脚本生成的 HTML 报告中的占位符。
用法: python3 backfill_html.py <html_path> --json-file <json_file>
      python3 backfill_html.py <html_path> --analysis-json '<json>'
      或通过 stdin 传入 JSON: echo '<json>' | python3 backfill_html.py <html_path>

推荐 --json-file：从文件直接读取，彻底规避 Windows 管道/Write 工具编码问题。
"""

import sys
import os
import json
import argparse


def backfill(html_path: str, analysis: dict) -> None:
    """读取 HTML 文件，替换分析占位符，写回文件"""
    if not os.path.exists(html_path):
        print(f"[error] HTML 文件不存在: {html_path}", file=sys.stderr)
        sys.exit(1)

    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()

    # 统计栏比例
    ratio_map = {
        "{{POSITIVE_RATIO}}": str(analysis.get("positive_ratio", "--")),
        "{{NEGATIVE_RATIO}}": str(analysis.get("negative_ratio", "--")),
        "{{DEMAND_RATIO}}": str(analysis.get("demand_ratio", "--")),
        "{{COMPETITOR_RATIO}}": str(analysis.get("competitor_ratio", "--")),
    }

    for key, val in ratio_map.items():
        html = html.replace(key, val)

    # 摘要卡片内容
    summary_map = {
        "{{SUMMARY_POSITIVE}}": analysis.get("positive_summary", ""),
        "{{SUMMARY_NEGATIVE}}": analysis.get("negative_summary", ""),
        "{{SUMMARY_DEMAND}}": analysis.get("demand_summary", ""),
        "{{SUMMARY_COMPETITOR}}": analysis.get("competitor_summary", ""),
    }

    for key, val in summary_map.items():
        html = html.replace(key, val)

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"[backfill] 分析数据已回填到: {html_path}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="HTML 报告分析数据回填")
    parser.add_argument("html_path", help="HTML 报告文件路径")
    parser.add_argument(
        "--analysis-json", dest="analysis_json", type=str, default=None,
        help='分析数据 JSON 字符串，格式: {"positive_ratio":45,"positive_summary":"<ul>...</ul>",...}',
    )
    parser.add_argument(
        "--json-file", dest="json_file", type=str, default=None,
        help="分析数据 JSON 文件路径（推荐，绕过管道编码问题）",
    )

    args = parser.parse_args()

    # 优先级：--json-file > --analysis-json > stdin
    if args.json_file:
        if not os.path.exists(args.json_file):
            print(f"[error] JSON 文件不存在: {args.json_file}", file=sys.stderr)
            sys.exit(1)
        try:
            with open(args.json_file, "r", encoding="utf-8") as f:
                analysis = json.load(f)
        except json.JSONDecodeError as e:
            print(f"[error] JSON 文件解析失败: {e}", file=sys.stderr)
            sys.exit(1)
    elif args.analysis_json:
        try:
            analysis = json.loads(args.analysis_json)
        except json.JSONDecodeError as e:
            print(f"[error] JSON 解析失败: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        # 从 stdin 读取 JSON（显式 UTF-8，避免 Windows 管道编码问题）
        try:
            raw = sys.stdin.buffer.read().decode('utf-8')
            analysis = json.loads(raw) if raw.strip() else {}
        except json.JSONDecodeError as e:
            print(f"[error] stdin JSON 解析失败: {e}", file=sys.stderr)
            sys.exit(1)

    if not analysis:
        print("[warn] 未提供分析数据，跳过回填", file=sys.stderr)
        return

    backfill(args.html_path, analysis)


if __name__ == "__main__":
    main()
