#!/usr/bin/env python3
"""
海外跨平台热文搜索 — 主编排器
==============================
按用户输入的关键词（中文/英文，逗号分隔多词），搜索 X / TikTok / YouTube
热门内容，每平台取 Top N，归一化为统一列表（平台/标题/作者/播放/点赞/评论/发布时间/链接），
输出终端分组表格 + CSV + 交互式 HTML 报告。

Usage:
    python3 digest.py "AI"
    python3 digest.py "人工智能,AI agent" --days 3
    python3 digest.py "AI" --platforms tiktok --sort time
    python3 digest.py "AI" --sort views --top 5
    python3 digest.py "AI" --csv-only --no-open
"""

import argparse
import csv
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import (DEFAULT_OUTPUT_DIR, get_api_key, make_session,
                    print_no_key_guide)
from sources import SOURCES
from sources.base import PlatformUnavailable

# ─── 终端颜色 ──────────────────────────────────────────────────────────────────────
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


def info(msg):
    print(f"{GREEN}[✓]{RESET} {msg}")

def warn(msg):
    print(f"{YELLOW}[!]{RESET} {msg}")

def error(msg):
    print(f"{RED}[✗]{RESET} {msg}")

def step(msg):
    print(f"{CYAN}[→]{RESET} {msg}")


def format_number(n):
    n = int(n or 0)
    if n >= 10000:
        return f"{n/10000:.1f}w"
    if n >= 1000:
        return f"{n/1000:.1f}k"
    return str(n)


# ─── 语言识别与优先分层 ──────────────────────────────────────────────────────────
def detect_lang(text):
    """轻量语言识别（无第三方依赖）：
    zh=含汉字且无假名（简/繁中文），ja=含假名，ko=含谚文，en=含拉丁字母，other=其余。
    中英混排（如「中文标题 with English」）按 zh 计。"""
    has_han = has_kana = has_hangul = has_latin = False
    for ch in text or "":
        o = ord(ch)
        if 0x4E00 <= o <= 0x9FFF or 0x3400 <= o <= 0x4DBF:
            has_han = True
        elif 0x3040 <= o <= 0x30FF:
            has_kana = True
        elif 0xAC00 <= o <= 0xD7AF:
            has_hangul = True
        elif o < 0x80 and ch.isalpha():
            has_latin = True
    if has_han:
        return "ja" if has_kana else "zh"
    if has_kana:
        return "ja"
    if has_hangul:
        return "ko"
    if has_latin:
        return "en"
    return "other"


def keyword_pref_lang(keywords):
    """由关键词推断优先语言：含汉字→zh，纯拉丁→en，日文/韩文词同理；无法识别→None（不分层）。"""
    lang = detect_lang(" ".join(keywords))
    return lang if lang in ("zh", "en", "ja", "ko") else None


def lang_tier(lang, pref):
    """语言分层：0=关键词同语言，1=中文/英文，2=其他语言。pref 为 None 时不分层。"""
    if not pref or lang == pref:
        return 0
    if lang in ("zh", "en"):
        return 1
    return 2


# ─── 采集流程 ────────────────────────────────────────────────────────────────────
def collect(session, keywords, platforms):
    """
    平台 × 关键词 循环采集。
    返回 (records, platform_status) — platform_status: {platform: "ok"/错误信息}
    """
    records = []
    seen = set()
    platform_status = {}

    for pf in platforms:
        source_cls = SOURCES.get(pf)
        if not source_cls:
            warn(f"未知平台「{pf}」，已跳过（可选: {', '.join(SOURCES)}）")
            continue
        source = source_cls()
        pf_ok = False

        for kw in keywords:
            step(f"[{source.display_name}] 搜索「{kw}」...")
            try:
                items = source.search(session, kw)
            except PlatformUnavailable as e:
                warn(f"[{source.display_name}] 不可用，已跳过: {e}")
                platform_status[pf] = str(e)
                break
            except Exception as e:
                warn(f"[{source.display_name}] 关键词「{kw}」搜索异常: {e}")
                continue

            added = 0
            for r in items:
                dedup_key = r.get("url") or f"{pf}:{r.get('work_id')}"
                if dedup_key and dedup_key not in seen:
                    seen.add(dedup_key)
                    r["lang"] = detect_lang(r.get("title") or "")
                    records.append(r)
                    added += 1
            step(f"  +{added} 条（全局 {len(records)} 条）")
            pf_ok = True
            time.sleep(0.3)

        if pf_ok:
            platform_status[pf] = "ok"

    return records, platform_status


def filter_by_days(records, days):
    """按时间窗口过滤（publish_ts 缺失或超窗的记录排除，按平台统计提示）"""
    if days <= 0:
        return records
    cutoff = (datetime.now() - timedelta(days=days)).timestamp()
    kept, dropped = [], []
    for r in records:
        ts = int(r.get("publish_ts") or 0)
        if ts and ts >= cutoff:
            kept.append(r)
        else:
            dropped.append(r)
    if dropped:
        drop_cnt, keep_cnt = {}, {}
        for r in dropped:
            pf = r.get("platform") or "?"
            drop_cnt[pf] = drop_cnt.get(pf, 0) + 1
        for r in kept:
            pf = r.get("platform") or "?"
            keep_cnt[pf] = keep_cnt.get(pf, 0) + 1

        def _name(pf):
            return SOURCES[pf].display_name if pf in SOURCES else pf

        detail = "，".join(f"{_name(pf)} {n} 条" for pf, n in drop_cnt.items())
        warn(f"{len(dropped)} 条发布时间缺失或超出最近 {days} 天窗口，已排除（{detail}）")
        for pf, n in drop_cnt.items():
            if not keep_cnt.get(pf):
                warn(f"{_name(pf)} {n} 条均为窗口外的历史热门内容，如需查看请加 --days 0")
    return kept


SORT_LABELS = {"likes": "点赞数", "views": "播放数",
               "comments": "评论数", "time": "发布时间"}


def _sort_key(r, sort_by):
    """排序键：主指标降序，播放数/发布时间作次序兜底。
    某平台主指标全为 0 时（如 YouTube 无点赞数）自动回退到播放数排序。"""
    views = int(r.get("views") or 0)
    likes = int(r.get("likes") or 0)
    comments = int(r.get("comments") or 0)
    ts = int(r.get("publish_ts") or 0)
    if sort_by == "time":
        return (ts, views, likes)
    if sort_by == "views":
        return (views, likes, ts)
    if sort_by == "comments":
        return (comments, views, likes, ts)
    return (likes, views, ts)  # likes


def sort_records(records, sort_by, pref_lang=None):
    """先按指标降序，再按语言分层稳定排序：关键词同语言 > 中/英文 > 其他语言。"""
    records.sort(key=lambda r: _sort_key(r, sort_by), reverse=True)
    if pref_lang:
        records.sort(key=lambda r: lang_tier(r.get("lang"), pref_lang))
    return records


def limit_per_platform(records, top, sort_by, pref_lang=None):
    """按平台分组 → 组内排序（语言分层 + 指标降序）→ 每组截取前 N（0=不限）→ 按平台顺序合并"""
    groups, order = {}, []
    for r in records:
        pf = r.get("platform") or "?"
        if pf not in groups:
            groups[pf] = []
            order.append(pf)
        groups[pf].append(r)
    merged = []
    for pf in order:
        g = sort_records(groups[pf], sort_by, pref_lang)
        merged.extend(g if top <= 0 else g[:top])
    return merged


# ─── 终端表格 ──────────────────────────────────────────────────────────────────────
def print_terminal_table(records, keywords, platform_status, sort_by, top, pref_lang=None):
    kw_label = " + ".join(keywords)
    sort_label = SORT_LABELS.get(sort_by, sort_by)
    top_label = f"每平台 Top {top}" if top > 0 else "不限条数"
    lang_label = {"zh": "中文优先", "en": "English 优先"}.get(pref_lang)
    lang_suffix = f" · {lang_label}" if lang_label else ""

    print(f"\n{BOLD}{'=' * 128}{RESET}")
    print(f"{BOLD}  海外跨平台热文搜索 · 「{kw_label}」· 共 {len(records)} 条 · {top_label} · 按{sort_label}降序{lang_suffix}{RESET}")
    print(f"{BOLD}{'=' * 128}{RESET}")

    status_parts = []
    for pf, st in platform_status.items():
        name = SOURCES[pf].display_name if pf in SOURCES else pf
        status_parts.append(f"{name}: {'✓' if st == 'ok' else '✗ ' + st}")
    if status_parts:
        print(f"  {CYAN}平台状态：{' | '.join(status_parts)}{RESET}")

    if not records:
        print(f"  {YELLOW}无结果。可尝试放宽时间窗口（--days 0 不限）或更换关键词{RESET}\n")
        return

    # 按平台分组展示（records 已按平台分组排好序）
    groups, order = {}, []
    for r in records:
        pf = r.get("platform") or "?"
        if pf not in groups:
            groups[pf] = []
            order.append(pf)
        groups[pf].append(r)

    header = (f"  {'序号':<4}{'平台':<8}{'标题':<24}{'作者':<14}"
              f"{'播放':>7}{'点赞':>7}{'评论':>7}{'发布时间':<18}{'链接':<30}")
    idx = 0
    for pf in order:
        g = groups[pf]
        name = g[0].get("platform_name") or pf
        print(f"\n  {CYAN}{BOLD}▎{name}（{len(g)} 条 · 按{sort_label}）{RESET}")
        print(f"  {YELLOW}{'─' * 110}{RESET}")
        print(f"  {YELLOW}{header}{RESET}")
        print(f"  {YELLOW}{'─' * 110}{RESET}")
        for r in g:
            idx += 1
            pf_name = (r.get("platform_name") or r.get("platform") or "")[:6]
            title = r.get("title", "")
            title = (title[:20] + "…") if len(title) > 20 else title
            author = r.get("author", "")
            author = (author[:11] + "..") if len(author) > 13 else author
            views = format_number(r.get("views"))
            likes = format_number(r.get("likes")) if int(r.get("likes") or 0) else "-"
            comments = format_number(r.get("comments")) if int(r.get("comments") or 0) else "-"
            pub = (r.get("publish_time") or "")[:16]
            url = r.get("url", "")
            url = (url[:27] + "..") if len(url) > 29 else url
            print(f"  {idx:<4}{pf_name:<8}{title:<24}{author:<14}"
                  f"{views:>7}{likes:>7}{comments:>7}{pub:<18}{url:<30}")
        print(f"  {YELLOW}{'─' * 110}{RESET}")
    print()


# ─── CSV 导出 ──────────────────────────────────────────────────────────────────────
def export_csv(records, keyword, output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now().strftime("%Y-%m-%d")
    filepath = output_dir / f"海外热文_{keyword}_{date_str}.csv"

    fieldnames = ["平台", "标题", "作者", "播放/阅读数", "点赞数", "评论数",
                  "分享数", "发布时间", "链接", "命中关键词"]
    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in records:
            writer.writerow({
                "平台": r.get("platform_name", ""),
                "标题": r.get("title", ""),
                "作者": r.get("author", ""),
                "播放/阅读数": r.get("views", 0),
                "点赞数": r.get("likes", 0),
                "评论数": r.get("comments", 0),
                "分享数": r.get("shares", 0),
                "发布时间": r.get("publish_time", ""),
                "链接": r.get("url", ""),
                "命中关键词": r.get("keyword", ""),
            })
    return filepath


# ─── HTML 报告 ────────────────────────────────────────────────────────────────────
def generate_html(records, keyword, platform_status):
    template_path = Path(__file__).parent.parent / "assets" / "report_template.html"
    template = template_path.read_text(encoding="utf-8")

    status_label = " | ".join(
        f"{SOURCES[pf].display_name if pf in SOURCES else pf}: "
        f"{'正常' if st == 'ok' else st}"
        for pf, st in platform_status.items()
    )
    html = template
    html = html.replace("{{KEYWORD}}", keyword)
    html = html.replace("{{DATE}}", datetime.now().strftime("%Y-%m-%d"))
    html = html.replace("{{TIMESTAMP}}", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    html = html.replace("{{TOTAL_COUNT}}", str(len(records)))
    html = html.replace("{{PLATFORM_STATUS}}", status_label)
    html = html.replace("{{INITIAL_DATA}}", json.dumps(records, ensure_ascii=False))
    return html


# ─── 主流程 ────────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="海外跨平台热文搜索 — X / TikTok / YouTube",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 digest.py "AI"
  python3 digest.py "人工智能,AI agent" --days 3
  python3 digest.py "AI" --platforms tiktok --sort time
  python3 digest.py "AI" --sort views --top 5
  python3 digest.py "AI" --csv-only --no-open
        """,
    )
    parser.add_argument("keywords", nargs="?", default="",
                        help="搜索关键词，中文/英文均可，多词用英文逗号分隔")
    parser.add_argument("--days", type=int, default=1,
                        help="时间窗口：最近 N 天（默认 1，0=不限）")
    parser.add_argument("--platforms", default="x,tiktok,youtube",
                        help="平台列表，逗号分隔（默认 x,tiktok,youtube）")
    parser.add_argument("--sort", default="views",
                        choices=["likes", "views", "comments", "time"],
                        help="排序: views(默认) / likes / comments / time")
    parser.add_argument("--top", type=int, default=5,
                        help="每平台最多返回条数（默认 5，0=不限）")
    parser.add_argument("--output-dir", help="输出目录（默认 ~/Downloads/QoderChinaDigest）")
    parser.add_argument("--api-key", help="RedFox API Key")
    parser.add_argument("--csv-only", action="store_true", help="仅生成 CSV")
    parser.add_argument("--no-open", action="store_true", help="不自动打开浏览器")

    args = parser.parse_args()

    banner = f"""{CYAN}{BOLD}
  ╔══════════════════════════════════════════════╗
  ║        海外跨平台热文搜索                      ║
  ║        Overseas Trending Search               ║
  ║        X / TikTok / YouTube · 每日热文一览     ║
  ╚══════════════════════════════════════════════╝{RESET}
"""
    print(banner)

    try:
        import requests  # noqa: F401
    except ImportError:
        error("缺少 requests 库，请安装: pip3 install requests")
        sys.exit(1)

    api_key = get_api_key(cli_key=args.api_key)
    if not api_key:
        print_no_key_guide()
        sys.exit(1)

    if not args.keywords:
        try:
            args.keywords = input(f"{CYAN}请输入关键词（多词用逗号分隔）: {RESET}").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            sys.exit(0)
    keywords = [k.strip() for k in args.keywords.split(",") if k.strip()]
    if not keywords:
        error("关键词不能为空")
        sys.exit(1)

    platforms = [p.strip().lower() for p in args.platforms.split(",") if p.strip()]
    output_dir = os.path.expanduser(args.output_dir or str(DEFAULT_OUTPUT_DIR))

    session = make_session(api_key)

    # ── 采集 ──
    records, platform_status = collect(session, keywords, platforms)

    # ── 语言优先分层（中文词→中文优先，英文词→英文优先，其余语言兜底）──
    pref_lang = keyword_pref_lang(keywords)

    # ── 时间过滤 + 每平台 Top N ──
    records = filter_by_days(records, args.days)
    records = limit_per_platform(records, args.top, args.sort, pref_lang)

    # ── 终端表格 ──
    print_terminal_table(records, keywords, platform_status, args.sort, args.top, pref_lang)

    if not records:
        sys.exit(0)

    # ── 统计 ──
    total_likes = sum(int(r.get("likes") or 0) for r in records)
    pf_counter = {}
    for r in records:
        pf_counter[r.get("platform_name", "?")] = pf_counter.get(r.get("platform_name", "?"), 0) + 1
    pf_dist = " | ".join(f"{k} {v}" for k, v in pf_counter.items())
    print(f"  {BOLD}统计:{RESET} 共 {len(records)} 条 | {pf_dist} | 总点赞 {format_number(total_likes)}")

    # ── CSV ──
    main_kw = keywords[0]
    csv_path = export_csv(records, main_kw, output_dir)
    info(f"CSV 已保存: {csv_path}")

    # ── HTML ──
    if not args.csv_only:
        step("生成 HTML 报告 ...")
        html_content = generate_html(records, " + ".join(keywords), platform_status)
        html_path = Path(output_dir) / f"海外热文_{main_kw}_{datetime.now().strftime('%Y-%m-%d')}.html"
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        html_path.write_text(html_content, encoding="utf-8")
        info(f"HTML 报告已保存: {html_path}")

        if not args.no_open:
            step("打开浏览器...")
            try:
                subprocess.run(["open", str(html_path)], check=True)
            except Exception:
                print(f"  请手动打开: {html_path}")

    print(f"\n{GREEN}╔══════════════════════════════════════════════════╗{RESET}")
    print(f"{GREEN}║  ✓ 热文搜索完成!                                  ║{RESET}")
    print(f"{GREEN}╚══════════════════════════════════════════════════╝{RESET}\n")


if __name__ == "__main__":
    main()
