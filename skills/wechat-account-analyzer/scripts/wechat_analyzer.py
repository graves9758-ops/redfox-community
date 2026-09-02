"""wechat_analyzer.py — 公众号账号诊断入口点

模块化拆分后，本文件仅负责 argparse 命令路由。
核心逻辑分布在以下模块中：
  - api_client.py  — 红狐 API HTTP 通信与凭证管理
  - scoring.py     — 作品辅助函数、四维度评分、等级判定
  - analyzer.py    — 单账号分析编排、查询/同步命令
  - report.py      — HTML 报告模板替换与生成

向后兼容：scoring 模块的公开函数通过 __all__ 重导出，
使 `from wechat_analyzer import _work_read` 等旧导入继续可用。
"""

import argparse
import json
import sys

from analyzer import cmd_query, cmd_sync_notes
from report import cmd_generate_html, cmd_generate_multi_html

# ── 向后兼容重导出（供 test_wechat_analyzer.py 等旧导入使用）──
from scoring import (  # noqa: F401
    _work_read,
    _work_like,
    _work_comment,
    _work_share,
    _work_collect,
    _work_interact_total,
    _work_publish_time,
    _calc_avg_read,
    _calc_viral_ratio,
    _score_content_health,
    _score_user_activity,
    _score_core_data,
    _score_operation_compliance,
)


def main():
    parser = argparse.ArgumentParser(description="公众号账号诊断宗师")
    subparsers = parser.add_subparsers(dest="command")

    # 查询子命令
    query_parser = subparsers.add_parser("query", help="查询账号数据")
    query_parser.add_argument("--account_ids", help="公众号账号ID列表，逗号分隔", required=False)
    query_parser.add_argument("--account_names", help="公众号账号名称列表，逗号分隔", required=False)
    query_parser.add_argument("--force_analyze", action="store_true", help="强制执行分析（即使无作品数据）")

    # 同步作品子命令
    sync_parser = subparsers.add_parser("sync_notes", help="同步账号作品数据")
    sync_parser.add_argument("--account_id", help="公众号账号ID（单个）", required=True)
    sync_parser.add_argument("--account_names", help="账号名称列表，逗号分隔（用于提示）", required=False)

    # 生成单账号HTML子命令
    html_parser = subparsers.add_parser("generate_html", help="基于report_data.json生成单账号HTML报告")

    # 生成多账号对比HTML子命令
    multi_parser = subparsers.add_parser("generate_multi_html", help="基于multi_report_data.json生成多账号对比HTML报告")

    args = parser.parse_args()

    if args.command == "query":
        account_ids = [x.strip() for x in args.account_ids.split(",") if x.strip()] if args.account_ids else []
        account_names = [x.strip() for x in args.account_names.split(",") if x.strip()] if args.account_names else []

        if not account_ids and not account_names:
            print(json.dumps({
                "status": "error",
                "message": "请提供至少一个账号ID（--account_ids）或名称（--account_names）"
            }, ensure_ascii=False))
            sys.exit(1)

        cmd_query(account_ids=account_ids or None, account_names=account_names or None, force_analyze=getattr(args, 'force_analyze', False))

    elif args.command == "sync_notes":
        account_id = args.account_id.strip() if args.account_id else ""
        if not account_id:
            print(json.dumps({
                "status": "error",
                "message": "请提供账号ID（--account_id）"
            }, ensure_ascii=False))
            sys.exit(1)
        cmd_sync_notes([account_id])

    elif args.command == "generate_html":
        cmd_generate_html()

    elif args.command == "generate_multi_html":
        cmd_generate_multi_html()

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
