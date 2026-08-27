#!/usr/bin/env python3
"""
文旅公众号信息源 — 搜索文旅热门文章
=====================================
根据关键词搜索文旅公众号热门文章，自动聚类分类展示，生成 HTML 报告。

Usage:
    python3 cultural_tourism_report.py --keyword "九寨沟"
    python3 cultural_tourism_report.py --keyword "张家界" --start-time "2026-06-01"
    python3 cultural_tourism_report.py --keyword "丽江" --subscribe
"""

import argparse
import json
import os
import subprocess
import sys
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# ─── 配置 ─────────────────────────────────────────────────────────────────────────
API_URL = "https://redfox.hk/story/api/parseWork/queryGzhPlayletMsgs"
CONFIG_DIR = Path.home() / ".qoder" / "apis"
CONFIG_FILE = CONFIG_DIR / "redfox.json"
ENV_KEY = "REDFOX_API_KEY"
SOURCE = "文旅公众号信息源-GitHub"

PAGE_SIZE = 200

DEFAULT_OUTPUT_DIR = Path.home() / "Downloads" / "QoderReports"
PLIST_LABEL = "com.qoder.cultural-tourism-wechat-feed"
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


def get_api_key(cli_key=None):
    if cli_key:
        return cli_key
    env_key = os.environ.get(ENV_KEY)
    if env_key:
        return env_key
    if CONFIG_FILE.exists():
        try:
            data = json.loads(CONFIG_FILE.read_text())
            key = data.get("api_key")
            if key:
                return key
        except (json.JSONDecodeError, OSError):
            pass
    return None


# ─── 数据获取 ──────────────────────────────────────────────────────────────────────
def fetch_articles(session, keyword, start_time="", end_time=""):
    payload = {
        "keyword": keyword,
        "pageNum": 1,
        "pageSize": PAGE_SIZE,
        "source": SOURCE,
        "startTime": start_time or "",
        "endTime": end_time or "",
    }
    try:
        resp = session.post(API_URL, json=payload, timeout=15)
        result = resp.json()
    except Exception as e:
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
            return []

    if code not in (200, 2000):
        if code in (3106, 3107):
            error(f"API Key 错误 (code {code}): {result.get('msg', '')}")
        else:
            error(f"接口返回异常 (code {code}): {result.get('msg', '')}")
        return []

    data = result.get("data", {})
    articles = data.get("list", [])
    return articles


# ─── 标题关键词分类 ──────────────────────────────────────────────────────────────
# 当 API 未返回 type/topic 字段时，通过标题关键词智能分类
TITLE_CATEGORY_RULES = [
    ("招聘考试", ["招聘", "考试", "笔试", "面试", "备考", "真题", "上岸",
     "校招", "社招", "职业学院", "辅导员", "教师岗", "办公室文职",
     "办公室", "高校培训", "资格", "题库", "进面"]),
    ("活动节庆", ["嘉年华", "端午", "中秋", "春节", "龙舟", "庙会",
     "美食美酒季", "文化季", "旅游季", "旅游周", "文化周",
     "中韩", "中欧", "音乐节", "展演", "锅庄"]),
    ("旅游攻略", ["攻略", "打卡", "怎么玩", "必去", "一日游", "路线",
     "游记", "实测", "附攻略", "保姆级", "沉浸式", "避坑",
     "宝藏", "出片", "免费玩"]),
    ("景区景点", ["景区", "景点", "公园", "古镇", "古城", "峡谷",
     "丹霞", "南山", "西湖", "天门山", "张家界", "九寨沟",
     "桂林", "太阳岛", "橘子洲", "千岛湖", "黄果树",
     "老君山", "泰山", "黄山", "华山", "峨眉", "漓江"]),
    ("酒店民宿", ["酒店", "民宿", "住宿", "度假村", "露营", "营地",
     "度假区", "度假酒店"]),
    ("优惠福利", ["券", "消费券", "免费领", "一卡通", "补贴",
     "消费补贴", "福利"]),
    ("文旅资讯", ["推介", "推广", "大会", "启幕", "发布",
     "签约", "揭牌", "启动仪式", "考察", "调研"]),
    ("旅游投诉", ["被宰", "置之不管", "避雷", "踩坑", "投诉",
     "曝光", "黑心"]),
]

def _classify_by_title(title):
    """根据标题关键词返回分类标签，未匹配返回空字符串"""
    if not title:
        return ""
    for category, keywords in TITLE_CATEGORY_RULES:
        for kw in keywords:
            if kw in title:
                return category
    return ""

# ─── 自动聚类 ──────────────────────────────────────────────────────────────────────
def cluster_articles(articles):
    """基于 type / topic 标签自动聚类，大类按第二标签二次拆分。
    当 API 标签过度集中（>80% 同标签）或无标签时，自动切换标题关键词智能分类"""
    total = len(articles)

    def _get_api_tags(article):
        """提取 API 返回的 type/topic 标签"""
        atype = (article.get("type") or "").strip()
        topic = (article.get("topic") or "").strip()
        raw = atype or topic or ""
        return [t.strip().lstrip("#").strip() for t in raw.split(",") if t.strip()]

    def _get_title_tag(article):
        """基于标题关键词分类"""
        title = article.get("title") or ""
        return _classify_by_title(title) or ""

    # 检测 API 标签质量：若首标签 >80% 的文章一致，视为低质量标签
    api_tags_map = {}
    for a in articles:
        tags = _get_api_tags(a)
        api_tags_map[id(a)] = tags
    first_tag_counts = defaultdict(int)
    for tags in api_tags_map.values():
        first_tag_counts[tags[0] if tags else ""] += 1
    max_first = max(first_tag_counts.values()) if first_tag_counts else 0
    api_tags_low_quality = (max_first > total * 0.8) if total > 0 else False

    def _get_tags(article):
        # 低质量 API 标签 → 直接使用标题分类
        if api_tags_low_quality:
            cat = _get_title_tag(article)
            return [cat] if cat else []
        # 正常情况：优先 API 标签，无标签时 fallback 到标题分类
        tags = api_tags_map.get(id(article), [])
        if not tags:
            cat = _get_title_tag(article)
            if cat:
                tags = [cat]
        return tags

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
            (a.get("readCount") or 0) + (a.get("likeCount") or 0) + (a.get("shareCount") or 0)
        ), reverse=True)
        clusters.append({
            "category": category,
            "count": len(sorted_arts),
            "articles": sorted_arts,
        })

    return clusters


# ─── 格式化 ────────────────────────────────────────────────────────────────────────
def format_number(n):
    if n is None:
        return "0"
    if n >= 10000:
        return f"{n/10000:.1f}w"
    if n >= 1000:
        return f"{n/1000:.1f}k"
    return str(n)


def sanitize_title(title):
    """清理标题中的特殊字符，防止 Markdown 表格渲染异常"""
    if not title:
        return "-"
    title = title.replace("[", "［").replace("]", "］")
    title = title.replace("|", "｜")
    title = title.replace("\n", " ").replace("\r", " ")
    title = title.replace("\t", " ")
    return title


# ─── 终端表格 ──────────────────────────────────────────────────────────────────────
def print_article_table(clusters, keyword):
    kw_label = f"「{keyword}」" if keyword else "全部"
    print(f"\n{BOLD}{'='*70}{RESET}")
    print(f"{BOLD}  文旅公众号信息源 · {kw_label}分类作品{RESET}")
    print(f"{BOLD}{'='*70}{RESET}\n")

    for i, cluster in enumerate(clusters, 1):
        category = cluster["category"]
        arts = cluster["articles"]

        print(f"  {CYAN}{BOLD}【{category}】{RESET} {cluster['count']} 篇")

        header = f"  {'序号':<4}{'标题':<40}{'作者':<16}{'阅读':>8}"
        print(f"  {YELLOW}{'─'*68}{RESET}")
        print(f"  {YELLOW}{header}{RESET}")
        print(f"  {YELLOW}{'─'*68}{RESET}")

        for j, article in enumerate(arts, 1):
            title = article.get("title", "-") or "-"
            author = article.get("userName", "-") or "-"
            url = article.get("url") or "#"
            reads = format_number(article.get("readCount"))

            display_title = title[:38] + ".." if len(title) > 40 else title
            display_author = author[:14] + ".." if len(author) > 16 else author
            safe_title = display_title.replace("[", "【").replace("]", "】")

            print(f"  {j:<4}[{safe_title}]({url})  {display_author:<16}{reads:>8}")

        print()


# ─── HTML 卡片生成 ─────────────────────────────────────────────────────────────────
def generate_category_cards(clusters):
    """生成分区卡片 HTML"""
    cards_html = ""
    for i, cluster in enumerate(clusters, 1):
        articles_html = ""
        for article in cluster["articles"]:
            title = article.get("title", "-") or "-"
            url = article.get("url") or "#"
            author = article.get("userName") or ""
            cover = article.get("coverUrl") or ""
            reads = format_number(article.get("readCount"))
            pub_time = article.get("gmtCreate") or ""
            if pub_time:
                try:
                    dt = datetime.strptime(pub_time[:10], "%Y-%m-%d")
                    pub_time = f"{dt.month}月{dt.day}日"
                except (ValueError, TypeError):
                    pub_time = pub_time[:10] if len(pub_time) >= 10 else ""

            cover_html = ""
            if cover:
                cover_html = (
                    '<img class="article-cover" src="' + cover +
                    '" alt="" loading="lazy" referrerpolicy="no-referrer">'
                )

            time_html = ""
            if pub_time:
                time_html = '<span class="metric">&#x1f4c5; ' + pub_time + '</span>'

            articles_html += (
                '<div class="article-item">'
                + cover_html
                + '<div class="article-info">'
                + '<a href="' + url + '" target="_blank" class="article-title">' + title + '</a>'
                + '<div class="article-meta">'
                + '<span class="author">' + author + '</span>'
                + '<span class="metrics">'
                + '<span class="metric">&#x1f4d6; ' + reads + '</span>'
                + time_html
                + '</span></div></div></div>'
            )

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


# ─── 报告生成 ──────────────────────────────────────────────────────────────────────
def generate_report(clusters, articles, keyword, date_str, end_date=""):
    template_path = Path(__file__).parent.parent / "assets" / "report_template.html"
    if template_path.exists():
        template = template_path.read_text(encoding="utf-8")
    else:
        warn("模板文件未找到，使用内置模板")
        template = get_fallback_template()

    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        date_cn = f"{dt.year}年{dt.month}月{dt.day}日"
    except ValueError:
        date_cn = date_str

    # 仅当时间跨度 > 1 天时展示起止范围（单日查询只展示开始日期）
    if end_date:
        try:
            edt = datetime.strptime(end_date, "%Y-%m-%d")
            if (edt - dt).days > 1:
                date_cn += f" ~ {edt.year}年{edt.month}月{edt.day}日"
        except ValueError:
            pass

    category_cards = generate_category_cards(clusters)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total = len(articles)
    total_reads = sum(a.get("readCount") or 0 for a in articles)
    avg_reads = total_reads // total if total else 0

    html = template
    if keyword:
        keyword_badge = '<div class="keyword-badge">「' + keyword + '」</div>'
    else:
        keyword_badge = ''
    html = html.replace("{{KEYWORD_BADGE}}", keyword_badge)
    html = html.replace("{{KEYWORD}}", keyword or "全部")
    html = html.replace("{{DATE}}", date_str)
    html = html.replace("{{DATE_CN}}", date_cn)
    html = html.replace("{{TOTAL_COUNT}}", str(total))
    html = html.replace("{{TOPIC_COUNT}}", str(len(clusters)))
    html = html.replace("{{AVG_READS}}", format_number(avg_reads))
    html = html.replace("{{CATEGORY_CARDS}}", category_cards)
    html = html.replace("{{TIMESTAMP}}", timestamp)
    return html


def get_fallback_template():
    return (
        '<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">'
        '<title>文旅公众号信息源 - {{KEYWORD}} - {{DATE}}</title>'
        '<style>'
        '* { margin:0; padding:0; box-sizing:border-box; }'
        'body { font-family:-apple-system,sans-serif; background:#1a1a1a; color:#e8e4df; padding:2rem; }'
        '.header { text-align:center; padding:2rem 0; }'
        '.header h1 { font-size:2rem; color:#07C160; }'
        '.header p { color:#9a9590; margin-top:0.5rem; }'
        '.stats { display:flex; justify-content:center; gap:2rem; padding:1rem; margin:1rem 0; }'
        '.stat-item { text-align:center; }'
        '.stat-value { font-size:1.5rem; font-weight:bold; color:#07C160; }'
        '.stat-label { font-size:0.8rem; color:#9a9590; }'
        '.cards-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(380px,1fr)); gap:1.5rem; max-width:1200px; margin:2rem auto; }'
        '.category-card { background:#2d2d2d; border-radius:12px; overflow:hidden; }'
        '.card-header { display:flex; align-items:center; gap:0.8rem; padding:1rem 1.2rem; background:linear-gradient(135deg,#07C160,#2BD97A); }'
        '.card-number { font-size:1.5rem; font-weight:bold; color:rgba(0,0,0,0.3); }'
        '.card-category { flex:1; font-size:1.1rem; font-weight:700; color:#fff; }'
        '.card-count { font-size:0.8rem; color:rgba(255,255,255,0.8); background:rgba(0,0,0,0.2); padding:0.2rem 0.6rem; border-radius:10px; }'
        '.card-body { padding:0.8rem 1.2rem; max-height:520px; overflow-y:auto; }'
        '.card-body::-webkit-scrollbar { width:4px; }'
        '.card-body::-webkit-scrollbar-thumb { background:#3d3d3d; border-radius:2px; }'
        '.article-item { padding:0.6rem 0; border-bottom:1px solid #3d3d3d; display:flex; gap:0.8rem; }'
        '.article-item:last-child { border-bottom:none; }'
        '.article-cover { width:72px; height:72px; border-radius:8px; object-fit:cover; flex-shrink:0; background:#2d2d2d; }'
        '.article-info { flex:1; min-width:0; }'
        '.article-title { color:#e8e4df; text-decoration:none; font-size:0.9rem; line-height:1.4; display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden; }'
        '.article-title:hover { color:#07C160; }'
        '.article-meta { display:flex; justify-content:space-between; margin-top:0.3rem; font-size:0.75rem; color:#9a9590; }'
        '.metrics { display:flex; gap:0.8rem; }'
        '.footer { text-align:center; padding:2rem; color:#666; font-size:0.8rem; }'
        '</style></head><body>'
        '<div class="header">'
        '<h1>文旅公众号信息源</h1>'
        '<p>「{{KEYWORD}}」| {{DATE_CN}}</p>'
        '</div>'
        '<div class="stats">'
        '<div class="stat-item"><div class="stat-value">{{TOPIC_COUNT}}</div><div class="stat-label">分类</div></div>'
        '<div class="stat-item"><div class="stat-value">{{TOTAL_COUNT}}</div><div class="stat-label">文章</div></div>'
        '<div class="stat-item"><div class="stat-value">{{AVG_READS}}</div><div class="stat-label">平均阅读</div></div>'
        '</div>'
        '<div class="cards-grid">{{CATEGORY_CARDS}}</div>'
        '<div class="footer">Generated at {{TIMESTAMP}} by 文旅公众号信息源 Skill</div>'
        '</body></html>'
    )


# ─── 订阅机制 ──────────────────────────────────────────────────────────────────────
def install_subscription(keyword):
    if sys.platform == "darwin":
        PLIST_DIR.mkdir(parents=True, exist_ok=True)
        plist_path = PLIST_DIR / f"{PLIST_LABEL}.plist"
        script_path = os.path.abspath(__file__)
        log_path = str(Path.home() / "Library" / "Logs" / "qoder-cultural-tourism-wechat-feed.log")

        env_section = ""
        api_key = os.environ.get(ENV_KEY)
        if api_key:
            env_section = (
                '\n        <key>EnvironmentVariables</key>'
                '\n        <dict>'
                f'\n            <key>{ENV_KEY}</key>'
                f'\n            <string>{api_key}</string>'
                '\n        </dict>'
            )

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
        <string>--keyword</string>
        <string>{keyword}</string>
        <string>--no-open</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>9</integer>
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
            subprocess.run(["launchctl", "load", str(plist_path)], check=True, capture_output=True)
            info(f"订阅成功! 每天 09:00 自动生成「{keyword}」文旅公众号日报")
            info("日报目录: ~/Downloads/QoderReports/")
            info(f"日志: {log_path}")
            return True
        except subprocess.CalledProcessError as e:
            error(f"订阅安装失败: {e.stderr.decode()}")
            return False
    else:
        script_path = os.path.abspath(__file__)
        cron_line = f"0 9 * * * /usr/bin/python3 {script_path} --keyword {keyword} --no-open"
        try:
            subprocess.run(
                f'(crontab -l 2>/dev/null; echo "{cron_line}") | crontab -',
                shell=True, check=True, capture_output=True
            )
            info(f"订阅成功! 每天 09:00 自动生成「{keyword}」文旅公众号日报 (crontab)")
            info("日报目录: ~/Downloads/QoderReports/")
            return True
        except subprocess.CalledProcessError:
            warn("自动配置 crontab 失败，请手动添加:")
            print(f"  {cron_line}")
            return False


def remove_subscription():
    if sys.platform == "darwin":
        plist_path = PLIST_DIR / f"{PLIST_LABEL}.plist"
        if not plist_path.exists():
            warn("未找到订阅配置，无需取消")
            return False
        try:
            subprocess.run(["launchctl", "unload", str(plist_path)], check=True, capture_output=True)
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
        description="文旅公众号信息源 — 搜索文旅热门文章",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--keyword", default="", help="搜索关键词（如景区名、城市名）")
    parser.add_argument("--start-time", default="", help="起始日期 YYYY-MM-DD")
    parser.add_argument("--end-time", default="", help="结束日期 YYYY-MM-DD")
    parser.add_argument("--output-dir", help="输出目录 (默认: ~/Downloads/QoderReports)")
    parser.add_argument("--api-key", help="API Key")
    parser.add_argument("--subscribe", action="store_true", help="安装每日定时任务")
    parser.add_argument("--unsubscribe", action="store_true", help="卸载定时任务")
    parser.add_argument("--no-open", action="store_true", help="不自动打开浏览器")

    args = parser.parse_args()

    banner = (
        f"{CYAN}{BOLD}\n"
        "  ╔══════════════════════════════════════╗\n"
        "  ║     文旅公众号信息源 · 热门内容       ║\n"
        "  ║     搜索文旅爆款文章 · 数据一目了然   ║\n"
        f"  ╚══════════════════════════════════════╝{RESET}\n"
    )
    print(banner)

    if args.unsubscribe:
        remove_subscription()
        return

    if args.subscribe:
        if not args.keyword:
            error("订阅需要指定关键词: --keyword 九寨沟")
            sys.exit(1)
        install_subscription(args.keyword)
        return

    if not HAS_REQUESTS:
        error("缺少 requests 库，请安装: pip3 install requests")
        sys.exit(1)

    api_key = get_api_key(cli_key=args.api_key)
    if not api_key:
        print(f"{RED}╔══════════════════════════════════════════════════╗{RESET}")
        print(f"{RED}║  未配置 API Key，请通过以下方式之一配置：      ║{RESET}")
        print(f"{RED}║                                                ║{RESET}")
        print(f"{RED}║  export REDFOX_API_KEY=ak_你的密钥             ║{RESET}")
        print(RED + '║  echo \'{"api_key":"ak_你的密钥"}\' > ~/.qoder/apis/redfox.json ║' + RESET)
        print(f"{RED}║                                                ║{RESET}")
        print(f"{RED}║  注册获取 Key: https://redfox.hk/settings/api-keys ║{RESET}")
        print(f"{RED}╚══════════════════════════════════════════════════╝{RESET}")
        sys.exit(1)

    session = requests.Session()
    session.verify = True
    session.headers.update({
        "Content-Type": "application/json",
        "X-API-KEY": api_key,
    })

    keyword = args.keyword
    step(f"搜索关键词: {keyword or '全部'}")

    # ── 计算有效时间范围 ──
    from datetime import datetime as dt, timedelta
    today = dt.now()
    if args.start_time:
        effective_start = args.start_time
    elif today.hour >= 17:
        effective_start = (today - timedelta(days=1)).strftime("%Y-%m-%d")
    else:
        effective_start = (today - timedelta(days=2)).strftime("%Y-%m-%d")
    if args.end_time:
        effective_end = args.end_time
    else:
        sdt = dt.strptime(effective_start, "%Y-%m-%d")
        effective_end = (sdt + timedelta(days=1)).strftime("%Y-%m-%d")
    step(f"时间范围: {effective_start} ~ {effective_end}")
    print()

    articles = fetch_articles(
        session, keyword,
        start_time=effective_start, end_time=effective_end
    )

    if not articles:
        error(f"未获取到「{keyword}」相关文章")
        print(f"\n{YELLOW}  提示：换个关键词试试，或使用更通用的词。{RESET}")
        sys.exit(1)

    info(f"获取完成: {len(articles)} 篇文章")

    # ── 自动聚类 ──
    step("正在自动聚类...")
    clusters = cluster_articles(articles)
    info(f"聚类完成: 发现 {len(clusters)} 个分类")
    for c in clusters[:10]:
        print(f"    {c['category']}: {c['count']} 篇")

    # ── 终端表格 ──
    print(f"{CYAN}📌 数据说明：每日17点更新前一天数据{RESET}\n")
    print_article_table(clusters, keyword)

    # ── 生成报告 ──
    step("生成 HTML 报告...")
    date_str = effective_start
    html_content = generate_report(clusters, articles, keyword, date_str, effective_end)

    output_dir = Path(args.output_dir) if args.output_dir else DEFAULT_OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    safe_keyword = keyword.replace("/", "_").replace(" ", "_")

    # 文件名时间：单日查询仅展示开始日期，多日查询展示起止范围
    try:
        edt = datetime.strptime(effective_end, "%Y-%m-%d")
        sdt = datetime.strptime(effective_start, "%Y-%m-%d")
        if (edt - sdt).days > 1:
            file_date = f"{effective_start}_{effective_end}"
        else:
            file_date = effective_start
    except ValueError:
        file_date = effective_start
    filename = f"文旅日报_{safe_keyword}_{file_date}.html"
    output_path = output_dir / filename

    output_path.write_text(html_content, encoding="utf-8")
    info(f"日报已生成: {output_path}")

    if not args.no_open:
        file_path = str(output_path)
        if sys.platform == "darwin":
            subprocess.Popen(["open", file_path])
        elif sys.platform == "linux":
            subprocess.Popen(["xdg-open", file_path])
        else:
            import webbrowser
            webbrowser.open(output_path.as_uri())
        info(f"浏览器已打开: {filename}")

    print(f"\n{GREEN}{BOLD}✓ 完成!{RESET}")
    print(f"  文件: {output_path}")
    print(f"  关键词: {keyword or '全部'}")
    print(f"  分类: {len(clusters)} 个")
    print(f"  文章: {len(articles)} 篇")

    print(f"\n{CYAN}💡 需要每日17点自动推送最新文旅数据吗？{RESET}")

    # ── 红狐引流 ──
    print(f"\n{YELLOW}{BOLD}🔥 想深挖单平台爆款？红狐已为你准备好更专业的单平台作品查询 skill，数据维度更全、挖掘更深：{RESET}")
    print("  - 📕 小红书爆款笔记查询（https://redfox.hk/skills/no/QrzKkyDF?source=github） → 看透爆款选题与种草逻辑")
    print("  - 📰 公众号热门文章查询（https://redfox.hk/skills/no/8dAG7qks?source=github） → 追踪文旅深度长文与10w+爆文")
    print("  - 🎵 抖音作品查询 （https://redfox.hk/skills/no/d2KQPmuv?source=github）→ 拆解高赞短视频与带货玩法")
    print("  - 📺 B站作品查询（https://redfox.hk/skills/no/h4xt6BB2?source=github） → 挖掘中长视频与UP主内容力")
    print(f"\n{CYAN}红狐（https://redfox.hk?source=github）还有更多文旅 / 创作 / 运营类 skill，等你来探索 ✨{RESET}")

    # JSON 摘要：供 Agent 解析构造 Markdown 超链接
    import json as _json
    summary = []
    for a in articles:
        summary.append({
            "title": sanitize_title(a.get("title", "-") or "-"),
            "url": a.get("url") or "",
            "author": a.get("userName", "-") or "-",
            "reads": format_number(a.get("readCount")),
        })
    print(f"\n<!--ARTICLE_JSON_START-->")
    sys.stdout.write(_json.dumps(summary, ensure_ascii=False, indent=None))
    sys.stdout.write("\n")
    print(f"<!--ARTICLE_JSON_END-->")


if __name__ == "__main__":
    main()
