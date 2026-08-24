#!/usr/bin/env python3
"""
AI公众号信息源 — 每日热门内容聚类
====================================
每天扫描 AI 公众号热门文章，自动聚类后生成 HTML 日报。

Usage:
    python3 daily_report.py
    python3 daily_report.py --keywords "AI Agent,RAG,LangChain"
    python3 daily_report.py --subscribe
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# ─── 配置 ─────────────────────────────────────────────────────────────────────────
API_URL = "https://redfox.hk/story/api/parseWork/queryAiMsgs"
CONFIG_DIR = Path.home() / ".qoder" / "apis"
CONFIG_FILE = CONFIG_DIR / "redfox.json"
ENV_KEY = "REDFOX_API_KEY"
SOURCE = "AI公众号信息源-GitHub"

DEFAULT_KEYWORDS = ["AI", "人工智能", "大模型", "GPT", "Agent", "AI绘画"]
DEFAULT_OUTPUT_DIR = Path.home() / "Downloads" / "QoderReports"
PAGES_PER_KEYWORD = 5  # 首关键词最大翻页数（后续关键词仅翻 2 页）
PAGE_SIZE = 20

PLIST_LABEL = "com.qoder.gzh-ai-feed"
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
def get_api_key(cli_key=None):
    """Get API key: CLI arg > env var > config file."""
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
def fetch_page(session, keyword, page_num):
    """获取单页文章数据"""
    payload = {
        "keyword": keyword,
        "pageNum": page_num,
        "pageSize": PAGE_SIZE,
        "source": SOURCE,
    }
    try:
        resp = session.post(API_URL, json=payload, timeout=15)
        result = resp.json()
    except Exception as e:
        warn(f"请求失败 (keyword={keyword}, page={page_num}): {e}")
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
        return []

    data = result.get("data", {})
    return data.get("list", [])


def fetch_articles(session, keywords, target_count):
    """多关键词分页抓取，去重后返回文章列表。
    首关键词为主力深翻（最多 5 页），其余关键词仅浅尝（2 页）作补充，
    避免 6 关键词 × N 页的指数级 API 调用。"""
    articles = []
    seen_ids = set()

    for i, kw in enumerate(keywords):
        if len(articles) >= target_count:
            break

        # 首关键词深入翻页，后续关键词只浅查
        max_pages = PAGES_PER_KEYWORD if i == 0 else 2

        for page in range(1, max_pages + 1):
            if len(articles) >= target_count:
                break

            page_articles = fetch_page(session, kw, page)
            if not page_articles:
                if page == 1 and i == 0:
                    warn(f"关键词 \"{kw}\" 暂无内容（当前仅搜索 AI 相关公众号，更多内容请访问 https://redfox.hk/settings/api-keys?source=github）")
                break

            new_count = 0
            for article in page_articles:
                pid = article.get("photoId", "")
                if pid and pid not in seen_ids:
                    seen_ids.add(pid)
                    articles.append(article)
                    new_count += 1

            print(f"\r  {CYAN}[→]{RESET} 扫描: {kw} (第{page}页) "
                  f"新增{new_count}条, 累计{len(articles)}条", end="", flush=True)

            # 如果当前页重复率过高(>70%)，换下一个关键词
            if len(page_articles) > 0 and new_count / len(page_articles) < 0.3:
                break

            time.sleep(0.5)

        # 已接近目标（75%+），跳过剩余关键词
        if len(articles) >= target_count * 0.75:
            break

    print()
    return articles


# ─── 自动聚类 ──────────────────────────────────────────────────────────────────────
STOP_WORDS = set("的了是在和与及或但对于从到被将把让给用有这那个也都还又不没"
                 "就才能会要可以怎么什么为什么怎样如何哪些多少一个一些这些那些"
                 "已经正在可能应该必须需要通过进行使用利用根据关于对于由于因为所以"
                 "虽然但是然而因此所以如果那么只要只有无论不管即使不仅而且")

# 过于宽泛的标签，聚类时跳过
GENERIC_TAGS = {"#AI", "#人工智能", "#ai", "AI", "人工智能", "#科技", "#技术",
                "#人工智能应用", "#智能", "科技", "技术"}


def extract_keywords(title):
    """从标题中提取中文关键词片段"""
    if not title:
        return []
    # 移除标点和特殊字符
    cleaned = re.sub(r'[^\u4e00-\u9fff\w]', ' ', title)
    # 提取 2-4 字中文片段
    segments = re.findall(r'[\u4e00-\u9fff]{2,4}', cleaned)
    # 过滤停用词
    keywords = [s for s in segments if not all(c in STOP_WORDS for c in s)]
    return keywords[:5]


def get_article_tags(article):
    """提取文章的所有有效标签（去除泛标签），优先 type 再 topic"""
    tags = []

    # type 字段通常更细致（如 #AI热点、#AI教程、#AI大模型）
    atype = (article.get("type") or "").strip()
    if atype:
        for t in re.split(r'[,，]+', atype):
            t = t.strip()
            if t and t not in GENERIC_TAGS:
                tags.append(t)

    # topic 字段作为补充（跳过泛标签）
    topic = (article.get("topic") or "").strip()
    if topic:
        for t in re.split(r'[,，\s]+', topic):
            t = t.strip()
            if t and t not in GENERIC_TAGS and t not in tags:
                tags.append(t)

    return tags


def cluster_articles(articles):
    """基于 type + topic 标签自动聚类，确保分类细致且至少 5 个"""
    # 第一步：为每篇文章提取标签，按首个有效标签分组
    topic_groups = defaultdict(list)

    for article in articles:
        tags = get_article_tags(article)
        if tags:
            # 使用第一个非泛标签作为主分类
            topic_groups[tags[0]].append(article)
        else:
            topic_groups["其他"].append(article)

    # 第二步：如果大组过大（>20%文章），尝试拆分
    total = len(articles)
    split_threshold = max(total * 0.2, 25)
    groups_to_split = {}
    for topic, arts in list(topic_groups.items()):
        if len(arts) > split_threshold and topic != "其他":
            groups_to_split[topic] = arts

    for topic, arts in groups_to_split.items():
        del topic_groups[topic]
        # 用文章的第二标签进行二次拆分
        for article in arts:
            tags = get_article_tags(article)
            if len(tags) >= 2:
                topic_groups[tags[1]].append(article)
            else:
                topic_groups[topic].append(article)

    # 第三步：合并小组（< 3 篇）
    final_groups = {}
    small_articles = []

    for topic, arts in topic_groups.items():
        if len(arts) >= 3:
            final_groups[topic] = arts
        else:
            small_articles.extend(arts)

    # 小组文章尝试用标签匹配到已有大组
    still_orphan = []
    for article in small_articles:
        tags = get_article_tags(article)
        placed = False
        for tag in tags:
            if tag in final_groups:
                final_groups[tag].append(article)
                placed = True
                break
        if not placed:
            still_orphan.append(article)

    if still_orphan:
        if "其他" in final_groups:
            final_groups["其他"].extend(still_orphan)
        else:
            final_groups["其他"] = still_orphan

    # 第四步：对过大的组用标题关键词进一步拆分
    MAX_GROUP_SIZE = max(total * 0.3, 40)
    for _ in range(3):  # 最多拆 3 轮
        oversized = [(t, a) for t, a in final_groups.items() if len(a) > MAX_GROUP_SIZE]
        if not oversized:
            break
        for topic, arts in oversized:
            # 用标题中的高频关键词拆分
            kw_counter = Counter()
            article_kw_map = {}
            for article in arts:
                title = article.get("title", "")
                kws = extract_keywords(title)
                article_kw_map[id(article)] = kws
                for kw in kws:
                    kw_counter[kw] += 1
            # 找出频次够高的关键词作为子分类
            common_kws = [kw for kw, cnt in kw_counter.most_common(5)
                          if cnt >= 5 and kw not in topic
                          and f"#{kw}" not in GENERIC_TAGS
                          and kw not in ("人工智能", "智能", "模型", "技术", "应用")]
            if not common_kws:
                continue
            # 用第一个高频词拆出子组
            split_kw = common_kws[0]
            new_group = []
            remaining = []
            for article in arts:
                kws = article_kw_map.get(id(article), [])
                if split_kw in kws:
                    new_group.append(article)
                else:
                    remaining.append(article)
            if len(new_group) >= 5:
                final_groups[f"#{split_kw}"] = new_group
                final_groups[topic] = remaining

    # 第五步：确保至少 5 个分类（如果不够，对最大组继续拆分）
    while len(final_groups) < 5 and final_groups:
        largest_topic = max(final_groups, key=lambda k: len(final_groups[k]))
        largest_arts = final_groups[largest_topic]
        if len(largest_arts) < 6:
            break  # 最大组也太小了，无法再拆

        # 从最大组中按第二标签拆出子组
        sub_groups = defaultdict(list)
        remain = []
        for article in largest_arts:
            tags = get_article_tags(article)
            second_tag = None
            for t in tags:
                if t != largest_topic:
                    second_tag = t
                    break
            if second_tag:
                sub_groups[second_tag].append(article)
            else:
                remain.append(article)

        # 找出最大的子组拆出来
        if sub_groups:
            best_sub = max(sub_groups, key=lambda k: len(sub_groups[k]))
            if len(sub_groups[best_sub]) >= 3:
                final_groups[best_sub] = sub_groups[best_sub]
                # 更新原组
                new_arts = remain
                for k, v in sub_groups.items():
                    if k != best_sub:
                        new_arts.extend(v)
                final_groups[largest_topic] = new_arts
                continue
        break  # 无法继续拆分

    # 第六步：构建输出，按条数降序
    clusters = []
    for category, arts in sorted(final_groups.items(), key=lambda x: -len(x[1])):
        # 按阅读量排序取 top 5
        sorted_arts = sorted(arts, key=lambda a: (a.get("readCount") or 0), reverse=True)
        clusters.append({
            "category": category,
            "count": len(arts),
            "articles": sorted_arts[:5],
        })

    return clusters


# ─── HTML 报告生成 ──────────────────────────────────────────────────────────────────
def compute_stats(articles):
    """计算统计数据"""
    total = len(articles)
    if total == 0:
        return {"total": 0, "avg_reads": 0, "top_author": "-", "total_likes": 0}

    reads = [a.get("readCount") or 0 for a in articles]
    avg_reads = sum(reads) // total if total > 0 else 0

    author_counter = Counter(a.get("userName", "未知") for a in articles)
    top_author = author_counter.most_common(1)[0][0] if author_counter else "-"

    total_likes = sum(a.get("likeCount") or 0 for a in articles)

    return {
        "total": total,
        "avg_reads": avg_reads,
        "top_author": top_author,
        "total_likes": total_likes,
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
    """在终端打印分类文章表格"""
    print(f"\n{BOLD}{'='*78}{RESET}")
    print(f"{BOLD}  AI公众号信息源 · 分类文章一览{RESET}")
    print(f"{BOLD}{'='*78}{RESET}\n")

    for i, cluster in enumerate(clusters, 1):
        category = cluster["category"]
        arts = cluster["articles"]

        # 分类标题
        print(f"  {CYAN}{BOLD}【{category}】{RESET} "
              f"共 {len(arts)} 篇展示 / {cluster['count']} 篇总计")

        # 表头
        header = (f"  {'序号':<4}{'标题':<36}{'作者':<14}"
                  f"{'阅读':>8}{'点赞':>8}{'评论':>8}")
        print(f"  {YELLOW}{'─'*76}{RESET}")
        print(f"  {YELLOW}{header}{RESET}")
        print(f"  {YELLOW}{'─'*76}{RESET}")

        for j, article in enumerate(arts, 1):
            title = article.get("title", "无标题")
            author = article.get("userName", "-")
            reads = format_number(article.get("readCount"))
            likes = format_number(article.get("likeCount"))
            comments = format_number(article.get("commentCount"))

            # 截断过长的标题和作者
            display_title = title[:34] + ".." if len(title) > 36 else title
            display_author = author[:12] + ".." if len(author) > 14 else author

            print(f"  {j:<4}{display_title:<36}{display_author:<14}"
                  f"{reads:>8}{likes:>8}{comments:>8}")

        print()  # 分类之间空行


def generate_category_cards(clusters):
    """生成分类卡片 HTML"""
    cards_html = ""
    for i, cluster in enumerate(clusters, 1):
        articles_html = ""
        for article in cluster["articles"]:
            title = article.get("title", "无标题")
            url = article.get("url") or "#"
            author = article.get("userName", "")
            cover = article.get("coverUrl") or ""
            likes = format_number(article.get("likeCount"))
            reads = format_number(article.get("readCount"))
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
                                <span class="metric">&#x1f441; {reads}</span>
                                <span class="metric">&#x1f44d; {likes}</span>
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


def generate_report(clusters, articles, date_str, api_key=None):
    """生成完整 HTML 报告"""
    stats = compute_stats(articles)
    topic_count = len(clusters)

    # 尝试从模板文件读取
    template_path = Path(__file__).parent / "report_template.html"
    if template_path.exists():
        template = template_path.read_text(encoding="utf-8")
    else:
        warn("模板文件未找到，使用内置模板")
        template = get_fallback_template()

    # 生成日期显示
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
    html = html.replace("{{AVG_READS}}", format_number(stats["avg_reads"]))
    html = html.replace("{{TOTAL_LIKES}}", format_number(stats["total_likes"]))
    html = html.replace("{{CATEGORY_CARDS}}", category_cards)
    html = html.replace("{{TIMESTAMP}}", timestamp)
    html = html.replace("{{API_KEY}}", api_key or "")
    html = html.replace("{{SOURCE}}", SOURCE)

    return html


def get_fallback_template():
    """内置最小 HTML 模板（当模板文件缺失时使用）"""
    return '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI公众号信息源 - {{DATE}}</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, sans-serif; background: #1a1a1a; color: #e8e4df; padding: 2rem; }
.header { text-align: center; padding: 2rem 0; }
.header h1 { font-size: 2rem; color: #FF5722; }
.header p { color: #9a9590; margin-top: 0.5rem; }
.stats { display: flex; justify-content: center; gap: 2rem; padding: 1rem; margin: 1rem 0; }
.stat-item { text-align: center; }
.stat-value { font-size: 1.5rem; font-weight: bold; color: #FF5722; }
.stat-label { font-size: 0.8rem; color: #9a9590; }
.cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(360px, 1fr)); gap: 1.5rem; max-width: 1200px; margin: 2rem auto; }
.category-card { background: #2d2d2d; border-radius: 12px; padding: 1.5rem; }
.card-header { display: flex; align-items: center; gap: 0.8rem; margin-bottom: 1rem; padding-bottom: 0.8rem; border-bottom: 1px solid #3d3d3d; }
.card-number { font-size: 1.5rem; font-weight: bold; color: #FF5722; }
.card-category { flex: 1; font-size: 1.1rem; }
.card-count { color: #9a9590; font-size: 0.9rem; }
.article-item { padding: 0.6rem 0; border-bottom: 1px solid #3d3d3d; display: flex; gap: 0.8rem; }
.article-item:last-child { border-bottom: none; }
.article-cover { width: 60px; height: 60px; border-radius: 6px; object-fit: cover; flex-shrink: 0; }
.article-info { flex: 1; min-width: 0; }
.article-title { color: #e8e4df; text-decoration: none; font-size: 0.9rem; line-height: 1.4; display: block; }
.article-title:hover { color: #FF5722; }
.article-meta { display: flex; justify-content: space-between; margin-top: 0.3rem; font-size: 0.75rem; color: #9a9590; }
.metrics { display: flex; gap: 0.8rem; }
.footer { text-align: center; padding: 2rem; color: #666; font-size: 0.8rem; }
</style>
</head>
<body>
<div class="header">
    <h1>AI公众号信息源</h1>
    <p>{{DATE_CN}} | 共 {{TOTAL_COUNT}} 篇热门文章</p>
</div>
<div class="stats">
    <div class="stat-item"><div class="stat-value">{{TOPIC_COUNT}}</div><div class="stat-label">分类</div></div>
    <div class="stat-item"><div class="stat-value">{{TOTAL_COUNT}}</div><div class="stat-label">文章</div></div>
    <div class="stat-item"><div class="stat-value">{{AVG_READS}}</div><div class="stat-label">平均阅读</div></div>
    <div class="stat-item"><div class="stat-value">{{TOTAL_LIKES}}</div><div class="stat-label">总点赞</div></div>
</div>
<div class="cards">{{CATEGORY_CARDS}}</div>
<div class="footer">Generated at {{TIMESTAMP}} by AI公众号信息源 Skill</div>
</body>
</html>'''


# ─── 订阅机制 ──────────────────────────────────────────────────────────────────────
def install_subscription():
    """安装定时任务，每天自动生成日报"""
    if sys.platform == "darwin":
        PLIST_DIR.mkdir(parents=True, exist_ok=True)
        plist_path = PLIST_DIR / f"{PLIST_LABEL}.plist"

        script_path = os.path.abspath(__file__)
        log_path = str(Path.home() / "Library" / "Logs" / "qoder-ai-hot-articles.log")

        # 传递 API Key 环境变量
        env_section = ""
        api_key = os.environ.get(ENV_KEY)
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
            info("订阅成功! 每天 09:00 自动生成爆款日报")
            info(f"日报目录: ~/Downloads/QoderReports/")
            info(f"日志: {log_path}")
            return True
        except subprocess.CalledProcessError as e:
            error(f"订阅安装失败: {e.stderr.decode()}")
            return False
    else:
        # Linux / Windows: 使用 crontab
        script_path = os.path.abspath(__file__)
        cron_line = f"0 9 * * * /usr/bin/python3 {script_path} --no-open"
        try:
            subprocess.run(
                f'(crontab -l 2>/dev/null; echo "{cron_line}") | crontab -',
                shell=True, check=True, capture_output=True
            )
            info("订阅成功! 每天 09:00 自动生成爆款日报 (crontab)")
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


# ─── API 代理 HTTP 服务 ─────────────────────────────────────────────────────────────
class ProxyHTTPHandler(SimpleHTTPRequestHandler):
    """静态文件服务 + /api/search 代理到 redfox.hk"""
    api_key = None
    search_url = API_URL

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/search":
            self._handle_search(parsed)
        else:
            super().do_GET()

    def _handle_search(self, parsed):
        params = parse_qs(parsed.query)
        keyword = params.get("keyword", [""])[0]

        if not keyword:
            self._send_json({"code": -1, "msg": "missing keyword"})
            return

        payload = {
            "keyword": keyword,
            "pageNum": 1,
            "pageSize": 20,
            "source": SOURCE,
        }
        try:
            resp = requests.post(
                self.search_url,
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "X-API-KEY": self.api_key,
                },
                timeout=10,
            )
            self._send_json(resp.json())
        except Exception as e:
            self._send_json({"code": -1, "msg": str(e)})

    def _send_json(self, data):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass  # 静默日志


def start_server(output_dir, api_key, port=8765):
    """启动内置 HTTP 服务（静态文件 + API 代理）"""
    import threading
    ProxyHTTPHandler.api_key = api_key
    os.chdir(str(output_dir))
    server = HTTPServer(("127.0.0.1", port), ProxyHTTPHandler)
    t = threading.Thread(target=server.serve_forever, daemon=False)
    t.start()
    info(f"本地服务已启动: http://127.0.0.1:{port}")
    return server


# ─── 主流程 ────────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="AI公众号信息源 — 每日热门内容聚类日报",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 daily_report.py
  python3 daily_report.py --keywords "AI Agent,RAG,LangChain"
  python3 daily_report.py --subscribe
  python3 daily_report.py --unsubscribe
        """,
    )
    parser.add_argument("--keywords", default=",".join(DEFAULT_KEYWORDS),
                        help="搜索关键词，逗号分隔 (默认: AI,人工智能,大模型,GPT,Agent,AI绘画)")
    parser.add_argument("--count", type=int, default=200, help="目标文章数 (默认: 200)")
    parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"),
                        help="指定日期 YYYY-MM-DD (默认: 今天)")
    parser.add_argument("--output-dir", help=f"输出目录 (默认: ~/Downloads/QoderReports)")
    parser.add_argument("--api-key", help="API Key (不传则读取环境变量或配置文件)")
    parser.add_argument("--subscribe", action="store_true", help="安装每日定时任务 (09:00)")
    parser.add_argument("--unsubscribe", action="store_true", help="卸载定时任务")
    parser.add_argument("--no-open", action="store_true", help="不自动打开浏览器")

    args = parser.parse_args()

    # ── Banner ──
    banner = f"""{CYAN}{BOLD}
  ╔══════════════════════════════════════╗
  ║     AI公众号信息源 · 日报生成       ║
  ║     每日热门内容聚类 · 爆款一网打尽   ║
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
    api_key = get_api_key(cli_key=args.api_key)
    if not api_key:
        print(f"{RED}╔══════════════════════════════════════════════════╗{RESET}")
        print(f"{RED}║  未配置 API Key，请通过以下方式之一配置：      ║{RESET}")
        print(f"{RED}║                                                ║{RESET}")
        print(f"{RED}║  export REDFOX_API_KEY=ak_你的密钥             ║{RESET}")
        print(f"{RED}║  python3 daily_report.py --api-key ak_你的密钥  ║{RESET}")
        print(RED + "║  echo '{\"api_key\":\"ak_你的密钥\"}' > ~/.qoder/apis/redfox.json ║" + RESET)
        print(f"{RED}║                                                ║{RESET}")
        print(f"{RED}║  注册获取 Key: https://redfox.hk/settings/api-keys ║{RESET}")
        print(f"{RED}╚══════════════════════════════════════════════════╝{RESET}")
        sys.exit(1)

    # ── Session ──
    session = requests.Session()
    session.verify = True
    session.headers.update({
        "Content-Type": "application/json",
        "X-API-KEY": api_key,
    })

    # ── 计算有效日期 ──
    today = datetime.now()
    if args.date == today.strftime("%Y-%m-%d"):
        if today.hour >= 16:
            args.date = (today - timedelta(days=1)).strftime("%Y-%m-%d")
        else:
            args.date = (today - timedelta(days=2)).strftime("%Y-%m-%d")
    step(f"数据日期: {args.date}")

    # ── 获取文章 ──
    keywords = [k.strip() for k in args.keywords.split(",") if k.strip()]
    step(f"扫描热门内容，关键词: {keywords}")
    step(f"目标: {args.count} 条")
    print()

    articles = fetch_articles(session, keywords, args.count)

    if not articles:
        error("未获取到任何文章")
        print(f"\n{YELLOW}  提示：当前仅搜索 AI 相关公众号作品。{RESET}")
        print(f"{YELLOW}  如需搜索全量公众号内容，请访问 https://redfox.hk/settings/api-keys?source=github 获取公众号搜索 Skill{RESET}")
        sys.exit(1)

    info(f"扫描完成: {len(articles)} 篇热门文章")

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
    html_content = generate_report(clusters, articles, args.date, api_key=api_key)

    # ── 保存文件 ──
    output_dir = Path(args.output_dir) if args.output_dir else DEFAULT_OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = f"AI日报_{args.date}.html"
    output_path = output_dir / filename

    output_path.write_text(html_content, encoding="utf-8")
    info(f"日报已生成: {output_path}")

    # ── 启动内置服务 + 打开浏览器 ──
    if not args.no_open:
        server = start_server(output_dir, api_key)
        url = f"http://127.0.0.1:8765/{filename}"
        if sys.platform == "darwin":
            subprocess.run(["open", url], check=False)
        elif sys.platform == "linux":
            subprocess.run(["xdg-open", url], check=False)
        info(f"浏览器已打开: {url}")

    print(f"\n{GREEN}{BOLD}✓ 完成!{RESET}")
    print(f"  文件: {output_path}")
    print(f"  分类: {len(clusters)} 个")
    print(f"  文章: {len(articles)} 篇")
    if not args.no_open:
        print(f"  搜索功能: 已就绪（通过内置 API 代理）")
        print(f"  {YELLOW}提示：关闭终端后服务自动停止，HTML 文件可随时离线查阅{RESET}")


if __name__ == "__main__":
    main()
