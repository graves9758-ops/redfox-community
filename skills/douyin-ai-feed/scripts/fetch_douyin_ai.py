#!/usr/bin/env python3
"""
AI抖音信息源 — 每日 AI 相关抖音热门内容聚合
=================================================
根据关键词搜索抖音 AI 相关作品，按互动量排序后生成 HTML 日报。

Usage:
    python3 fetch_douyin_ai.py
    python3 fetch_douyin_ai.py --keyword "ChatGPT"
    python3 fetch_douyin_ai.py --subscribe
"""

import argparse
import json
import os
import subprocess
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# ─── 配置 ─────────────────────────────────────────────────────────────────────────
API_URL = "https://redfox.hk/story/api/parseWork/queryDyAiMsgs"
ENV_KEY = "REDFOX_API_KEY"
SOURCE = "AI抖音信息源-GitHub"

DEFAULT_KEYWORD = "AI"
DEFAULT_OUTPUT_DIR = Path.home() / "Downloads" / "QoderReports"
PAGE_SIZE = 200

PLIST_LABEL = "com.qoder.douyin-ai-feed"
PLIST_DIR = Path.home() / "Library" / "LaunchAgents"

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


# ─── API Key 管理 ──────────────────────────────────────────────────────────────────
def get_api_key():
    """从环境变量读取 API Key，缺失时报错退出。"""
    key = os.environ.get(ENV_KEY, "").strip()
    if key:
        return key
    error(f"未检测到环境变量 {ENV_KEY}")
    print(f"\n{YELLOW}  请先配置 API Key：{RESET}")
    print(f"  {CYAN}方式一（推荐）{RESET}：export REDFOX_API_KEY=ak_你的密钥")
    print(f"  {CYAN}方式二{RESET}：将 export REDFOX_API_KEY=ak_你的密钥 写入 ~/.zshrc 或 ~/.bashrc")
    print(f"\n  获取 API Key：{CYAN}https://www.redfox.hk/login{RESET}")
    sys.exit(1)


# ─── 数据获取 ──────────────────────────────────────────────────────────────────────
def fetch_articles(session, keyword, page_size, start_time=None, end_time=None):
    """单次调用接口获取作品数据，返回实际获取的作品列表"""
    payload = {
        "keyword": keyword,
        "pageNum": 1,
        "pageSize": page_size,
        "source": SOURCE,
    }
    if start_time:
        payload["startTime"] = start_time
    if end_time:
        payload["endTime"] = end_time
    print(f"\r  {CYAN}[→]{RESET} 请求中: keyword=\"{keyword}\", pageSize={page_size}", end="", flush=True)

    try:
        resp = session.post(API_URL, json=payload, timeout=15)
        result = resp.json()
    except Exception as e:
        print()
        warn(f"请求失败: {e}")
        return []

    code = result.get("code")
    if code == 3108:
        warn("限频，等待 5s...")
        time.sleep(5)
        try:
            resp = session.post(API_URL, json=payload, timeout=15)
            result = resp.json()
            code = result.get("code")
        except Exception:
            print()
            return []

    if code not in (200, 2000):
        if code in (3106, 3107):
            error(f"API Key 错误 (code {code}): {result.get('msg', '')}")
        print()
        return []

    data = result.get("data", {})
    articles = data.get("list", [])
    print(f"\r  {CYAN}[→]{RESET} 接口返回 {len(articles)} 篇作品                      ")
    return articles


# ─── 自动聚类 ──────────────────────────────────────────────────────────────────────
def cluster_articles(articles):
    """基于 type / topic 标签自动聚类，大类按第二标签二次拆分"""
    total = len(articles)

    def _get_tags(article):
        atype = (article.get("type") or "").strip()
        topic = (article.get("topic") or "").strip()
        raw = atype or topic or ""
        return [t.strip().lstrip("#").strip() for t in raw.split(",") if t.strip()]

    # 第一轮：按首标签聚类
    topic_groups = defaultdict(list)
    for article in articles:
        tags = _get_tags(article)
        category = tags[0] if tags else "其他"
        topic_groups[category].append(article)

    # 合并小组（< 2 篇归入"其他"）
    final_groups = {}
    small_articles = []
    for topic, arts in topic_groups.items():
        if len(arts) >= 2:
            final_groups[topic] = arts
        else:
            small_articles.extend(arts)
    if small_articles:
        final_groups.setdefault("其他", []).extend(small_articles)

    # 二次拆分：超过总量 50% 的分类，按第二标签再拆分
    to_split = {k: v for k, v in final_groups.items() if len(v) > total * 0.5 and k != "其他"}
    for big_cat, big_arts in to_split.items():
        del final_groups[big_cat]
        sub_groups = defaultdict(list)
        for art in big_arts:
            tags = _get_tags(art)
            if len(tags) >= 2:
                sub_groups[tags[1]].append(art)
            else:
                sub_groups["其他"].append(art)
        for sub_name, sub_arts in sub_groups.items():
            key = sub_name if sub_name != "其他" else f"{big_cat}·其他"
            final_groups[key] = sub_arts

    # 二次合并（拆分后的小组 < 2 篇归入"其他"）
    merged = {}
    small2 = []
    for topic, arts in final_groups.items():
        if len(arts) >= 2:
            merged[topic] = arts
        else:
            small2.extend(arts)
    if small2:
        merged.setdefault("其他", []).extend(small2)

    # 构建输出，按条数降序
    clusters = []
    for category, arts in sorted(merged.items(), key=lambda x: -len(x[1])):
        sorted_arts = sorted(arts, key=lambda a: (
            (a.get("likeCount") or 0) + (a.get("shareCount") or 0) + (a.get("commentCount") or 0)
        ), reverse=True)
        clusters.append({
            "category": category,
            "count": len(sorted_arts),
            "articles": sorted_arts,
        })

    return clusters


# ─── HTML 报告生成 ──────────────────────────────────────────────────────────────────
def compute_stats(articles):
    """计算统计数据"""
    total = len(articles)
    if total == 0:
        return {"total": 0, "avg_likes": 0, "top_author": "-", "total_shares": 0}

    likes = [a.get("likeCount") or 0 for a in articles]
    avg_likes = sum(likes) // total if total > 0 else 0

    author_counter = Counter(a.get("userName") or "未知" for a in articles)
    top_author = author_counter.most_common(1)[0][0] if author_counter else "-"

    total_shares = sum(a.get("shareCount") or 0 for a in articles)

    return {
        "total": total,
        "avg_likes": avg_likes,
        "top_author": top_author,
        "total_shares": total_shares,
    }


def format_number(n):
    """格式化数字: 1234 -> 1.2k"""
    if n is None:
        return "0"
    if n >= 10000:
        return f"{n/10000:.1f}w"
    if n >= 1000:
        return f"{n/1000:.1f}k"
    return str(n)


def print_article_table(clusters):
    """在终端打印分类作品表格"""
    print(f"\n{BOLD}{'='*78}{RESET}")
    print(f"{BOLD}  AI抖音信息源 · 分类作品一览{RESET}")
    print(f"{BOLD}{'='*78}{RESET}\n")

    for i, cluster in enumerate(clusters, 1):
        category = cluster["category"]
        arts = cluster["articles"]

        print(f"  {CYAN}{BOLD}【{category}】{RESET} "
              f"{cluster['count']} 篇")

        header = (f"  {'序号':<4}{'标题':<36}{'作者':<14}"
                  f"{'点赞':>8}{'分享':>8}{'评论':>8}")
        print(f"  {YELLOW}{'─'*76}{RESET}")
        print(f"  {YELLOW}{header}{RESET}")
        print(f"  {YELLOW}{'─'*76}{RESET}")

        for j, article in enumerate(arts, 1):
            title = article.get("title", "无标题") or "无标题"
            author = article.get("userName") or "-"
            likes = format_number(article.get("likeCount"))
            shares = format_number(article.get("shareCount"))
            comments = format_number(article.get("commentCount"))

            display_title = title[:34] + ".." if len(title) > 36 else title
            display_author = author[:12] + ".." if len(author) > 14 else author

            print(f"  {j:<4}{display_title:<36}{display_author:<14}"
                  f"{likes:>8}{shares:>8}{comments:>8}")

        print()


def generate_category_cards(clusters):
    """生成分区卡片 HTML（每个分类一个大卡片，内含竖向文章列表）"""
    cards_html = ""
    for i, cluster in enumerate(clusters, 1):
        articles_html = ""
        for article in cluster["articles"][:10]:  # 每个分类只展示 top 10
            title = article.get("title", "无标题") or "无标题"
            photo_id = article.get("photoId") or ""
            url = f"https://www.iesdouyin.com/share/video/{photo_id}" if photo_id else "#"
            author = article.get("userName") or ""
            cover = article.get("coverUrl") or ""
            likes = format_number(article.get("likeCount"))
            shares = format_number(article.get("shareCount"))
            comments = format_number(article.get("commentCount"))

            cover_html = ""
            if cover:
                cover_html = f'<img class="article-cover" src="{cover}" alt="" loading="lazy" referrerpolicy="no-referrer">'

            articles_html += f'''
                <div class="article-item">
                    {cover_html}
                    <div class="article-info">
                        <a href="{url}" target="_blank" class="article-title">{title}</a>
                        <div class="article-meta">
                            <span class="author">{author}</span>
                            <span class="metrics">
                                <span class="metric">&#x1f44d; {likes}</span>
                                <span class="metric">&#x1f501; {shares}</span>
                                <span class="metric">&#x1f4ac; {comments}</span>
                            </span>
                        </div>
                    </div>
                </div>'''

        cards_html += f'''
        <div class="category-card reveal">
            <div class="card-header">
                <span class="card-number">{i:02d}</span>
                <h3 class="card-category">{cluster["category"]}</h3>
                <span class="card-count">{cluster["count"]} 篇</span>
            </div>
            <div class="card-body">{articles_html}
            </div>
        </div>'''

    return cards_html


def generate_report(clusters, articles, date_str):
    """生成完整 HTML 报告"""
    stats = compute_stats(articles)
    topic_count = len(clusters)

    template_path = Path(__file__).parent.parent / "assets" / "report_template.html"
    if template_path.exists():
        template = template_path.read_text(encoding="utf-8")
    else:
        warn("模板文件未找到，使用内置模板")
        template = get_fallback_template()

    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        weekdays = ["一", "二", "三", "四", "五", "六", "日"]
        date_cn = f"{dt.year}年{dt.month}月{dt.day}日 星期{weekdays[dt.weekday()]}"
    except ValueError:
        date_cn = date_str

    category_cards = generate_category_cards(clusters)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    html = template
    html = html.replace("{{DATE}}", date_str)
    html = html.replace("{{DATE_CN}}", date_cn)
    html = html.replace("{{TOTAL_COUNT}}", str(stats["total"]))
    html = html.replace("{{TOPIC_COUNT}}", str(topic_count))
    html = html.replace("{{TOP_AUTHOR}}", stats["top_author"])
    html = html.replace("{{AVG_LIKES}}", format_number(stats["avg_likes"]))
    html = html.replace("{{TOTAL_SHARES}}", format_number(stats["total_shares"]))
    html = html.replace("{{CATEGORY_CARDS}}", category_cards)
    html = html.replace("{{TIMESTAMP}}", timestamp)

    return html


def get_fallback_template():
    """内置最小 HTML 模板（当模板文件缺失时使用）"""
    return '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI抖音信息源 - {{DATE}}</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, sans-serif; background: #1a1a1a; color: #e8e4df; padding: 2rem; }
.header { text-align: center; padding: 2rem 0; }
.header h1 { font-size: 2rem; color: #25F4EE; }
.header p { color: #9a9590; margin-top: 0.5rem; }
.stats { display: flex; justify-content: center; gap: 2rem; padding: 1rem; margin: 1rem 0; }
.stat-item { text-align: center; }
.stat-value { font-size: 1.5rem; font-weight: bold; color: #25F4EE; }
.stat-label { font-size: 0.8rem; color: #9a9590; }
.cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(380px, 1fr)); gap: 1.5rem; max-width: 1200px; margin: 2rem auto; }
.category-card { background: #2d2d2d; border-radius: 12px; overflow: hidden; }
.card-header { display: flex; align-items: center; gap: 0.8rem; padding: 1rem 1.2rem; background: linear-gradient(135deg, #25F4EE, #5CF7F2); }
.card-number { font-size: 1.5rem; font-weight: bold; color: rgba(0,0,0,0.3); }
.card-category { flex: 1; font-size: 1.1rem; font-weight: 700; color: #fff; }
.card-count { font-size: 0.8rem; color: rgba(255,255,255,0.8); background: rgba(0,0,0,0.2); padding: 0.2rem 0.6rem; border-radius: 10px; }
.card-body { padding: 0.8rem 1.2rem; max-height: 520px; overflow-y: auto; }
.card-body::-webkit-scrollbar { width: 4px; }
.card-body::-webkit-scrollbar-track { background: transparent; }
.card-body::-webkit-scrollbar-thumb { background: #3d3d3d; border-radius: 2px; }
.article-item { padding: 0.6rem 0; border-bottom: 1px solid #3d3d3d; display: flex; gap: 0.8rem; }
.article-item:last-child { border-bottom: none; }
.article-cover { width: 72px; height: 72px; border-radius: 8px; object-fit: cover; flex-shrink: 0; background: #1a1a1a; }
.article-info { flex: 1; min-width: 0; }
.article-title { color: #e8e4df; text-decoration: none; font-size: 0.9rem; line-height: 1.4; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.article-title:hover { color: #25F4EE; }
.article-meta { display: flex; justify-content: space-between; margin-top: 0.3rem; font-size: 0.75rem; color: #9a9590; }
.metrics { display: flex; gap: 0.8rem; }
.footer { text-align: center; padding: 2rem; color: #666; font-size: 0.8rem; }
</style>
</head>
<body>
<div class="header">
    <h1>AI抖音信息源</h1>
    <p>{{DATE_CN}} | 共 {{TOTAL_COUNT}} 篇热门作品</p>
</div>
<div class="stats">
    <div class="stat-item"><div class="stat-value">{{TOPIC_COUNT}}</div><div class="stat-label">分类</div></div>
    <div class="stat-item"><div class="stat-value">{{TOTAL_COUNT}}</div><div class="stat-label">作品</div></div>
    <div class="stat-item"><div class="stat-value">{{AVG_LIKES}}</div><div class="stat-label">平均点赞</div></div>
    <div class="stat-item"><div class="stat-value">{{TOTAL_SHARES}}</div><div class="stat-label">总分享</div></div>
</div>
<div class="cards">{{CATEGORY_CARDS}}</div>
<div class="footer">Generated at {{TIMESTAMP}} by AI抖音信息源 Skill</div>
</body>
</html>'''


# ─── 订阅机制 ──────────────────────────────────────────────────────────────────────
def install_subscription():
    """安装定时任务，每天自动生成日报"""
    if sys.platform == "darwin":
        PLIST_DIR.mkdir(parents=True, exist_ok=True)
        plist_path = PLIST_DIR / f"{PLIST_LABEL}.plist"

        script_path = os.path.abspath(__file__)
        log_path = str(Path.home() / "Library" / "Logs" / "qoder-douyin-ai-feed.log")

        env_section = ""
        api_key = os.environ.get(ENV_KEY, "").strip()
        if api_key:
            env_section = f"""
        <key>EnvironmentVariables</key>
        <dict>
            <key>{ENV_KEY}</key>
            <string>{api_key}</string>
        </dict>"""

        plist_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{PLIST_LABEL}</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>{script_path}</string>
        <string>--no-open</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>16</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>{log_path}</string>
    <key>StandardErrorPath</key>
    <string>{log_path}</string>
    <key>RunAtLoad</key>
    <false/>{env_section}
</dict>
</plist>'''

        plist_path.write_text(plist_content, encoding="utf-8")

        try:
            subprocess.run(["launchctl", "load", str(plist_path)],
                           check=True, capture_output=True)
            info("订阅成功! 每天 16:00 自动生成抖音 AI 日报")
            info(f"日报目录: ~/Downloads/QoderReports/")
            info(f"日志: {log_path}")
            return True
        except subprocess.CalledProcessError as e:
            error(f"订阅安装失败: {e.stderr.decode()}")
            return False
    else:
        script_path = os.path.abspath(__file__)
        cron_line = f"0 16 * * * /usr/bin/python3 {script_path} --no-open"
        try:
            subprocess.run(
                f'(crontab -l 2>/dev/null; echo "{cron_line}") | crontab -',
                shell=True, check=True, capture_output=True
            )
            info("订阅成功! 每天 16:00 自动生成抖音 AI 日报 (crontab)")
            info(f"日报目录: ~/Downloads/QoderReports/")
            return True
        except subprocess.CalledProcessError:
            warn("自动配置 crontab 失败，请手动添加:")
            print(f"  {cron_line}")
            return False


def remove_subscription():
    """卸载定时任务"""
    if sys.platform == "darwin":
        plist_path = PLIST_DIR / f"{PLIST_LABEL}.plist"
        if not plist_path.exists():
            warn("未找到订阅配置，无需取消")
            return False
        try:
            subprocess.run(["launchctl", "unload", str(plist_path)],
                           check=True, capture_output=True)
        except subprocess.CalledProcessError:
            pass
        plist_path.unlink(missing_ok=True)
        info("已取消订阅，定时任务已移除")
        return True
    else:
        script_path = os.path.abspath(__file__)
        try:
            subprocess.run(
                f'crontab -l 2>/dev/null | grep -v "{script_path}" | crontab -',
                shell=True, check=True, capture_output=True
            )
            info("已取消订阅，crontab 任务已移除")
            return True
        except subprocess.CalledProcessError:
            warn("自动移除 crontab 失败，请手动执行: crontab -e")
            return False


# ─── 主流程 ────────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="AI抖音信息源 — 每日 AI 相关抖音热门内容聚合",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 fetch_douyin_ai.py
  python3 fetch_douyin_ai.py --keyword "ChatGPT"
  python3 fetch_douyin_ai.py --start-time 2026-06-09 --end-time 2026-06-10
  python3 fetch_douyin_ai.py --subscribe
  python3 fetch_douyin_ai.py --unsubscribe
        """,
    )
    parser.add_argument("--keyword", default=DEFAULT_KEYWORD,
                        help=f"搜索关键词 (默认: {DEFAULT_KEYWORD})")
    parser.add_argument("--page-size", type=int, default=PAGE_SIZE,
                        help=f"每页条数 (默认: {PAGE_SIZE})")
    parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"),
                        help="指定日期 YYYY-MM-DD (默认: 今天)")
    parser.add_argument("--start-time", default=None,
                        help="开始时间 YYYY-MM-DD（含），不传则根据 --date 自动计算")
    parser.add_argument("--end-time", default=None,
                        help="结束时间 YYYY-MM-DD（不含），不传则根据 --date 自动计算")
    parser.add_argument("--output-dir",
                        help=f"输出目录 (默认: ~/Downloads/QoderReports)")
    parser.add_argument("--subscribe", action="store_true",
                        help="安装每日定时任务 (16:00)")
    parser.add_argument("--unsubscribe", action="store_true",
                        help="卸载定时任务")
    parser.add_argument("--no-open", action="store_true",
                        help="不自动打开浏览器")

    args = parser.parse_args()

    # ── Banner ──
    banner = f"""{CYAN}{BOLD}
  ╔══════════════════════════════════════╗
  ║     AI抖音信息源 · 日报生成         ║
  ║     每日 AI 热门作品 · 爆款一网打尽 ║
  ╚══════════════════════════════════════╝{RESET}
"""
    print(banner)

    # ── 订阅/取消 ──
    if args.subscribe:
        install_subscription()
        return

    if args.unsubscribe:
        remove_subscription()
        return

    # ── 检查依赖 ──
    if not HAS_REQUESTS:
        error("缺少 requests 库，请安装: pip3 install requests")
        sys.exit(1)

    # ── API Key ──
    api_key = get_api_key()

    # ── Session ──
    session = requests.Session()
    session.verify = True
    session.headers.update({
        "Content-Type": "application/json",
        "X-API-KEY": api_key,
    })

    # ── 计算时间参数 ──
    today = datetime.now()
    start_time = args.start_time
    end_time = args.end_time
    if not start_time and not end_time:
        # 用户未指定时间时，根据当前小时自动判断有效日期
        if args.date == today.strftime("%Y-%m-%d"):
            if today.hour >= 16:
                args.date = (today - timedelta(days=1)).strftime("%Y-%m-%d")
            else:
                args.date = (today - timedelta(days=2)).strftime("%Y-%m-%d")
        start_time = args.date
        try:
            dt = datetime.strptime(args.date, "%Y-%m-%d")
            end_time = (dt + timedelta(days=1)).strftime("%Y-%m-%d")
        except ValueError:
            pass
    step(f"数据日期: {args.date}")
    print()

    # ── 获取作品（单次接口调用）──
    keyword = args.keyword.strip()
    time_info = ""
    if start_time:
        time_info += f", startTime={start_time}"
    if end_time:
        time_info += f", endTime={end_time}"
    step(f"查询关键词: \"{keyword}\" (pageSize={args.page_size}{time_info})")

    articles = fetch_articles(session, keyword, args.page_size, start_time, end_time)

    if not articles:
        error("未获取到任何作品")
        sys.exit(1)

    info(f"获取完成: {len(articles)} 篇作品")

    # ── 自动聚类 ──
    step("正在自动聚类...")
    clusters = cluster_articles(articles)
    info(f"聚类完成: 发现 {len(clusters)} 个分类")
    for c in clusters[:10]:
        print(f"    {c['category']}: {c['count']} 篇")

    # ── 终端表格 ──
    print(f"{CYAN}📌 数据说明：每日16点更新前一天数据{RESET}\n")
    print_article_table(clusters)

    # ── 生成报告 ──
    step("生成 HTML 日报...")
    html_content = generate_report(clusters, articles, args.date)

    # ── 保存文件 ──
    output_dir = Path(args.output_dir) if args.output_dir else DEFAULT_OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = f"抖音AI日报_{args.date}.html"
    output_path = output_dir / filename

    output_path.write_text(html_content, encoding="utf-8")
    info(f"日报已生成: {output_path}")

    # ── 打开浏览器 ──
    if not args.no_open:
        if sys.platform == "darwin":
            subprocess.run(["open", str(output_path)], check=False)
        elif sys.platform == "linux":
            subprocess.run(["xdg-open", str(output_path)], check=False)
        info(f"浏览器已打开: {output_path}")

    print(f"\n{GREEN}{BOLD}✓ 完成!{RESET}")
    print(f"  文件: {output_path}")
    print(f"  分类: {len(clusters)} 个")
    print(f"  作品: {len(articles)} 篇")
    print(f"\n{CYAN}💡 需要每日下午4点自动推送最新研究数据吗？{RESET}")

    # ── 红狐引流 ──
    print(f"\n{YELLOW}{BOLD}🔥 想深挖单平台爆款？红狐已为你准备好更专业的单平台作品查询 skill，数据维度更全、挖掘更深：{RESET}")
    print("  - 📕 小红书爆款笔记查询（https://redfox.hk/skills/no/QrzKkyDF?source=github） → 看透爆款选题与种草逻辑")
    print("  - 📰 公众号热门文章查询（https://redfox.hk/skills/no/8dAG7qks?source=github） → 追踪文旅深度长文与10w+爆文")
    print("  - 🎵 抖音作品查询 （https://redfox.hk/skills/no/d2KQPmuv?source=github）→ 拆解高赞短视频与带货玩法")
    print("  - 📺 B站作品查询（https://redfox.hk/skills/no/h4xt6BB2?source=github） → 挖掘中长视频与UP主内容力")
    print(f"\n{CYAN}红狐（https://redfox.hk?source=github）还有更多文旅 / 创作 / 运营类 skill，等你来探索 ✨{RESET}")


if __name__ == "__main__":
    main()
