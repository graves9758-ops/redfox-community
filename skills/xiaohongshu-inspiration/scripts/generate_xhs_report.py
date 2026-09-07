#!/usr/bin/env python3
"""
小红书作品爬取 - 报告生成脚本
从 JSON 数据生成 CSV（Excel 兼容）和 HTML 可视化报告
用法: python3 generate_xhs_report.py "<关键词>" --input data.json [--output-dir ~/Downloads/XhsCrawl]
"""

import sys
import os
import json
import csv
import argparse
from datetime import datetime
from pathlib import Path

DEFAULT_OUTPUT_DIR = Path.home() / "Downloads" / "XhsCrawl"
TEMPLATE_PATH = Path(__file__).parent.parent / "assets" / "report_template.html"


# ─── CSV 导出 ────────────────────────────────────────────────────────────────────
def export_csv(works: list, keyword: str, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_kw = "".join(c for c in keyword if c.isalnum() or c in " _-")[:20] or "小红书"
    filename = f"小红书作品_{safe_kw}_{date_str}.csv"
    filepath = output_dir / filename

    fieldnames = ["序号", "笔记标题", "作者", "收藏数", "分享数", "评论数", "点赞数",
                  "互动总数", "作者粉丝数", "发布时间", "描述/话题", "封面图链接", "作品链接"]

    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for i, w in enumerate(works, 1):
            writer.writerow({
                "序号": i,
                "笔记标题": w.get("title", ""),
                "作者": w.get("author", ""),
                "收藏数": w.get("collect_count", 0),
                "分享数": w.get("share_count", 0),
                "评论数": w.get("comment_count", 0),
                "点赞数": w.get("like_count", 0),
                "互动总数": w.get("interactive_count", 0),
                "作者粉丝数": w.get("author_fans", 0),
                "发布时间": w.get("publish_time", ""),
                "描述/话题": w.get("desc", ""),
                "封面图链接": w.get("cover", ""),
                "作品链接": w.get("work_url", ""),
            })

    return filepath


# ─── HTML 报告生成 ───────────────────────────────────────────────────────────────
def generate_html(works: list, keyword: str, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_kw = "".join(c for c in keyword if c.isalnum() or c in " _-")[:20] or "小红书"
    html_filename = f"小红书作品_{safe_kw}_{date_str}.html"
    html_path = output_dir / html_filename

    if TEMPLATE_PATH.exists():
        template = TEMPLATE_PATH.read_text(encoding="utf-8")
    else:
        print("[error] HTML 模板文件不存在，请确认 assets/report_template.html 已就位", file=sys.stderr)
        sys.exit(1)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    works_json = json.dumps(works, ensure_ascii=False)

    html = template
    html = html.replace("{{KEYWORD}}", keyword)
    html = html.replace("{{DATE}}", datetime.now().strftime("%Y-%m-%d"))
    html = html.replace("{{TIMESTAMP}}", timestamp)
    html = html.replace("{{TOTAL_COUNT}}", str(len(works)))
    html = html.replace("{{WORKS_DATA}}", works_json)

    html_path.write_text(html, encoding="utf-8")
    return html_path


# ─── 主流程 ───────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="小红书作品报告生成（CSV + HTML）")
    parser.add_argument("keyword", help="搜索关键词（用于文件命名）")
    parser.add_argument("--input", "-i", required=True,
                        help="JSON 数据文件路径（crawl_xhs.py 的输出）")
    parser.add_argument("--output-dir", "-o", default=str(DEFAULT_OUTPUT_DIR),
                        help=f"输出目录（默认：{DEFAULT_OUTPUT_DIR}）")
    parser.add_argument("--format", "-f", choices=["csv", "html", "both"], default="both",
                        help="输出格式（默认：both）")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"[error] 输入文件不存在: {input_path}", file=sys.stderr)
        sys.exit(1)

    try:
        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"[error] 无法解析 JSON 文件: {e}", file=sys.stderr)
        sys.exit(1)

    works = data.get("articles") or data.get("works") or []
    if not works:
        print("[error] 数据为空，无法生成报告", file=sys.stderr)
        sys.exit(1)

    output_dir = Path(os.path.expanduser(args.output_dir))
    keyword = args.keyword.strip()
    generated = {}

    if args.format in ("csv", "both"):
        csv_path = export_csv(works, keyword, output_dir)
        generated["csv"] = str(csv_path)
        print(f"[csv] {csv_path}")

    if args.format in ("html", "both"):
        html_path = generate_html(works, keyword, output_dir)
        generated["html"] = str(html_path)
        print(f"[html] {html_path}")

    print(json.dumps({"status": "ok", **generated, "total": len(works)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
