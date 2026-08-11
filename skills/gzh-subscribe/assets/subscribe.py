#!/usr/bin/env python3
"""
微信公众号文章订阅 — 每天 6 点，盯梢竞对、同类和关注账号，推送最新发文
========================================================
订阅你关注的微信公众号，自动抓取每日发文内容，表格化展示。

Usage:
    python3 subscribe.py add "公众号名称" --id "redfoxdata1" --category "竞对账号"
    python3 subscribe.py remove "公众号名称"
    python3 subscribe.py list
    python3 subscribe.py fetch
    python3 subscribe.py fetch --date 2026-05-26
    python3 subscribe.py report
    python3 subscribe.py --subscribe
    python3 subscribe.py --unsubscribe
"""

import argparse
import json
import os
import subprocess
import sys
import time
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# ─── 配置 ─────────────────────────────────────────────────────────────────────────
API_URL = "https://redfox.hk/story/api/gzh/data/queryWorkList"
CONFIG_DIR = Path.home() / ".qoder" / "apis"
CONFIG_FILE = CONFIG_DIR / "redfox.json"
ENV_KEY = "REDFOX_API_KEY"
SOURCE = "公众号账号订阅-GitHub"

SUBSCRIPTIONS_FILE = Path.home() / ".qoder" / "gzh_subscriptions.json"
MAX_SUBSCRIPTIONS = 20
DEFAULT_OUTPUT_DIR = Path.home() / "Downloads" / "QoderGzhReports"

PLIST_LABEL = "com.qoder.gzh-subscribe"
PLIST_DIR = Path.home() / "Library" / "LaunchAgents"

DEFAULT_CATEGORIES = ["竞对账号", "同类账号", "关注账号"]
CATEGORY_DOT_CLASS = {
    "竞对账号": "competitor",
    "同类账号": "similar",
    "关注账号": "following",
}

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


# ─── 订阅数据管理 ──────────────────────────────────────────────────────────────────
def load_subscriptions():
    """加载订阅列表"""
    if not SUBSCRIPTIONS_FILE.exists():
        return []
    try:
        data = json.loads(SUBSCRIPTIONS_FILE.read_text(encoding="utf-8"))
        return data.get("subscriptions", [])
    except (json.JSONDecodeError, OSError):
        return []


def save_subscriptions(subscriptions):
    """保存订阅列表"""
    SUBSCRIPTIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    data = {"subscriptions": subscriptions, "updatedAt": datetime.now().isoformat()}
    SUBSCRIPTIONS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def find_subscription(identifier):
    """查找某个订阅 — 支持按 accountName 或 accountId 查找"""
    subs = load_subscriptions()
    for sub in subs:
        if sub["accountName"] == identifier or sub["accountId"] == identifier:
            return sub
    return None


def add_subscription(account_name, account_id="", category="关注账号"):
    """添加订阅"""
    subs = load_subscriptions()

    if len(subs) >= MAX_SUBSCRIPTIONS:
        error(f"已达订阅上限（{MAX_SUBSCRIPTIONS} 个），请先取消一些订阅后再添加")
        return False

    # 按名称查重
    existing = find_subscription(account_name)
    if existing:
        id_suffix = f" (ID: {existing.get('accountId')})" if existing.get("accountId") else ""
        warn(f"已订阅过「{existing['accountName']}」{id_suffix}，无需重复添加")
        return False

    subs.append({
        "accountId": account_id,
        "accountName": account_name,
        "category": category,
        "subscribedAt": datetime.now().isoformat(),
    })
    save_subscriptions(subs)
    id_info = f" (ID: {account_id})" if account_id else ""
    info(f"已订阅「{account_name}」{id_info} — 分类: {category}")
    info(f"当前共订阅 {len(subs)}/{MAX_SUBSCRIPTIONS} 个公众号")
    return True


def remove_subscription(identifier):
    """移除订阅 — 支持按 accountName 或 accountId 移除"""
    subs = load_subscriptions()
    target = None
    for i, sub in enumerate(subs):
        if sub["accountName"] == identifier or sub["accountId"] == identifier:
            target = subs.pop(i)
            break

    if not target:
        warn(f"未找到「{identifier}」的订阅")
        return False

    save_subscriptions(subs)
    id_info = f" ({target['accountId']})" if target.get("accountId") else ""
    info(f"已取消订阅「{target['accountName']}」{id_info}")
    info(f"当前共订阅 {len(subs)}/{MAX_SUBSCRIPTIONS} 个公众号")
    return True


def list_subscriptions():
    """列出所有订阅"""
    subs = load_subscriptions()
    if not subs:
        warn("当前没有订阅任何公众号")
        print(f"\n  使用 '{CYAN}add{RESET}' 命令添加订阅:")
        print(f"  python3 subscribe.py add \"<公众号名称>\" --id \"<账号ID>\" --category \"竞对账号\"")
        print(f"  账号 ID 支持三种格式：account / wxId / bizInfo")
        return

    # 按分类分组
    groups = defaultdict(list)
    for sub in subs:
        groups[sub.get("category", "关注账号")].append(sub)

    print(f"\n{BOLD}当前订阅 ({len(subs)}/{MAX_SUBSCRIPTIONS}):{RESET}\n")

    for cat in DEFAULT_CATEGORIES + ["其他"]:
        items = groups.pop(cat, [])
        if not items:
            if cat in DEFAULT_CATEGORIES:
                groups.pop(cat, None)
            continue

        # 分类颜色
        cat_color = {"竞对账号": RED, "同类账号": YELLOW, "关注账号": CYAN}.get(cat, CYAN)
        print(f"  {cat_color}{BOLD}▸ {cat}{RESET}")
        for item in items:
            subscribed_at = item.get("subscribedAt", "")[:10] if item.get("subscribedAt") else ""
            id_part = item.get("accountId", "")
            display_line = f"    {item['accountName']}"
            if id_part:
                display_line += f"  (ID: {id_part})"
            if subscribed_at:
                display_line += f"  订阅于 {subscribed_at}"
            print(display_line)

    # 剩余未定义分类
    for cat, items in groups.items():
        if not items:
            continue
        print(f"  {CYAN}▸ {cat}{RESET}")
        for item in items:
            id_part = item.get("accountId", "")
            display = f"    {item['accountName']}"
            if id_part:
                display += f" (ID: {id_part})"
            print(display)

    print()


# ─── 数据获取 ──────────────────────────────────────────────────────────────────────
def fetch_account_articles(session, account_id, account_name, date_str):
    """获取单个公众号文章列表（广域库 T+1，查昨天及近 7 天），需提供账号 ID，最多 5 次请求（每次 20 条，共 100 条）"""
    if not account_id:
        warn(f"「{account_name}」缺少账号 ID，无法查询。请使用 add 命令重新订阅并提供账号 ID")
        return []

    id_label = f" (ID: {account_id})"
    all_articles = []

    # T+1: 广域库查不到当天数据，取昨天往前 7 天
    target_date = datetime.strptime(date_str, "%Y-%m-%d")
    end_date = target_date - timedelta(days=1)
    start_date = end_date - timedelta(days=7)
    end_str = end_date.strftime("%Y-%m-%d")
    start_str = start_date.strftime("%Y-%m-%d")

    for page in range(5):  # 5 页，每页 20 条
        offset = page * 20
        payload = {
            "account": account_id,
            "offset": offset,
            "sortType": "0",
            "publishTimeStart": f"{start_str} 00:00:00",
            "publishTimeEnd": f"{end_str} 23:59:59",
            "source": SOURCE,
        }
        try:
            resp = session.post(API_URL, json=payload, timeout=20)
            result = resp.json()
        except requests.exceptions.Timeout:
            warn(f"请求超时: {account_name}{id_label}")
            return all_articles if all_articles else []
        except Exception as e:
            warn(f"请求失败: {account_name}{id_label}: {e}")
            return all_articles if all_articles else []

        code = result.get("code")
        if code == 3108:
            warn("触发频率限制，等待 5s...")
            time.sleep(5)
            try:
                resp = session.post(API_URL, json=payload, timeout=20)
                result = resp.json()
                code = result.get("code")
            except Exception:
                return all_articles if all_articles else []

        if code not in (200, 2000):
            if code in (3106, 3107):
                error(f"API Key 错误 (code {code}): {result.get('msg', '')}")
            elif code == 3203:
                warn(f"「{account_name}」不在广域库中，暂未收录")
                print(f"    💡 如需查询此账号，请联系红狐数据获取定制支持：redfoxdata@proton.me")
            elif code:
                warn(f"API 返回错误 (code {code}): {result.get('msg', '')} — {account_name}")
            return all_articles if all_articles else []

        data_raw = result.get("data", {})
        if not data_raw:
            break  # 无更多数据

        # 兼容多种响应结构
        if isinstance(data_raw, list):
            articles = data_raw
        elif isinstance(data_raw, dict):
            articles = data_raw.get("list") or data_raw.get("articles") or data_raw.get("records") or []
        else:
            articles = []

        if not articles:
            break  # 空页，停止翻页

        # 为每篇文章附加公众号信息
        for article in articles:
            article["_accountId"] = account_id
            article["_accountName"] = account_name
            article["_url"] = article.get("workUrl") or article.get("url") or "#"

        all_articles.extend(articles)

        # 返回不足 20 条说明已是最后一页
        if len(articles) < 20:
            break

    return all_articles


def fetch_all_articles(session, subscriptions, date_str):
    """拉取所有订阅公众号在指定日期的文章"""
    all_articles = []
    total = len(subscriptions)

    for i, sub in enumerate(subscriptions, 1):
        aid = sub.get("accountId", "")
        name = sub["accountName"]
        print(f"\r  {CYAN}[→]{RESET} 拉取: {name} ({i}/{total})", end="", flush=True)

        articles = fetch_account_articles(session, aid, name, date_str)
        if articles:
            for article in articles:
                article["_category"] = sub.get("category", "关注账号")
            all_articles.extend(articles)

        # 避免请求过快
        if i < total:
            time.sleep(0.3)

    print()
    return all_articles


# ─── 数字格式化 ────────────────────────────────────────────────────────────────────
def format_number(n):
    """格式化数字: 1234 -> 1.2k, 12345 -> 1.2w"""
    if n is None:
        return "0"
    n = int(n)
    if n >= 10000:
        return f"{n/10000:.1f}w"
    if n >= 1000:
        return f"{n/1000:.1f}k"
    return str(n)


# ─── 终端表格展示 ──────────────────────────────────────────────────────────────────
def print_terminal_table(articles):
    """在终端打印文章表格"""
    if not articles:
        warn("没有获取到任何文章")
        return

    # 按分类分组
    groups = defaultdict(list)
    for article in articles:
        cat = article.get("_category", "关注账号")
        if cat not in DEFAULT_CATEGORIES:
            cat = "关注账号"
        groups[cat].append(article)

    # 分类颜色
    cat_colors = {"竞对账号": RED, "同类账号": YELLOW, "关注账号": CYAN}
    cat_icons = {"竞对账号": "⚔", "同类账号": "◎", "关注账号": "★"}

    total_shown = 0

    for cat in DEFAULT_CATEGORIES:
        arts = groups.get(cat, [])
        if not arts:
            continue

        # 按时间降序排序（最新的在前）
        arts.sort(key=lambda a: a.get("publicTime") or a.get("publishDate") or a.get("publishTime") or "", reverse=True)

        cat_color = cat_colors.get(cat, CYAN)
        cat_icon = cat_icons.get(cat, "●")

        print(f"\n  {cat_color}{BOLD}{cat_icon} {cat}{RESET} — {len(arts)} 篇文章")
        print(f"  {YELLOW}{'─'*100}{RESET}")

        # 表头
        header = (f"  {'发文日期':<12}{'作者':<16}{'标题':<30}"
                  f"{'简介':<22}{'阅读':>8}{'点赞':>8}")
        print(f"  {YELLOW}{header}{RESET}")
        print(f"  {YELLOW}{'─'*100}{RESET}")

        for article in arts[:10]:  # 每类最多展示 10 篇
            pub_date = (article.get("publicTime") or
                        article.get("publishDate") or
                        article.get("publishTime") or
                        article.get("date") or "-")[:10]
            author = (article.get("_accountName") or
                      article.get("author") or
                      article.get("userName") or "-")
            title = article.get("title") or article.get("name") or "无标题"
            summary = (article.get("summary") or
                       article.get("description") or
                       article.get("digest") or
                       article.get("abstract") or "")
            reads = format_number(article.get("readCount") or
                                  article.get("clicksCount") or
                                  article.get("reads"))
            likes = format_number(article.get("likeCount") or article.get("likes"))
            url = article.get("_url") or "#"

            # 截断
            author_d = author[:14] + ".." if len(author) > 16 else author
            title_d = title[:27] + ".." if len(title) > 30 else title
            summary_d = summary[:19] + ".." if len(summary) > 22 else summary

            # 每行
            print(f"  {pub_date:<12}{author_d:<16}{title_d:<30}"
                  f"{summary_d:<22}{reads:>8}{likes:>8}")
            # 链接行
            if url != "#":
                print(f"  {'':>12}{'':>16}{CYAN}  ↳ {url}{RESET}")

            total_shown += 1

    # 如果有超过 10 篇的，提示截断
    remaining = len(articles) - total_shown
    if remaining > 0:
        print(f"\n  {YELLOW}... 还有 {remaining} 篇文章，请在 HTML 日报中查看完整列表{RESET}")

    print()


# ─── HTML 报告生成 ──────────────────────────────────────────────────────────────────
def compute_stats(articles):
    """计算统计数据"""
    total = len(articles)
    if total == 0:
        return {"article_count": 0, "account_count": 0,
                "avg_reads": "0", "total_likes": "0"}

    reads = [a.get("readCount") or a.get("clicksCount") or a.get("reads") or 0 for a in articles]
    avg_reads = sum(int(r) for r in reads) // total if total > 0 else 0
    total_likes = sum(int(a.get("likeCount") or a.get("likes") or 0) for a in articles)

    accounts = set(a.get("_accountId") or a.get("uid") or a.get("_accountName") for a in articles)

    return {
        "article_count": total,
        "account_count": len(accounts),
        "avg_reads": format_number(avg_reads),
        "total_likes": format_number(total_likes),
    }


def generate_category_sections(articles):
    """生成分类区块 HTML"""
    groups = defaultdict(list)
    for article in articles:
        cat = article.get("_category", "关注账号")
        if cat not in DEFAULT_CATEGORIES:
            cat = "关注账号"
        groups[cat].append(article)

    sections_html = ""
    cat_order = ["竞对账号", "同类账号", "关注账号"]

    for cat in cat_order:
        arts = groups.get(cat, [])
        if not arts:
            continue

        # 按时间降序
        arts.sort(key=lambda a: a.get("publicTime") or a.get("publishDate") or a.get("publishTime") or "", reverse=True)

        dot_class = CATEGORY_DOT_CLASS.get(cat, "other")

        rows_html = ""
        for article in arts:
            pub_date = (article.get("publicTime") or
                        article.get("publishDate") or
                        article.get("publishTime") or
                        article.get("date") or "-")[:10]
            author = (article.get("_accountName") or
                      article.get("author") or
                      article.get("userName") or "-")
            title = article.get("title") or article.get("name") or "无标题"
            summary = (article.get("summary") or
                       article.get("description") or
                       article.get("digest") or
                       article.get("abstract") or "")
            reads = format_number(article.get("readCount") or
                                  article.get("clicksCount") or
                                  article.get("reads"))
            likes = format_number(article.get("likeCount") or article.get("likes"))
            url = article.get("_url") or "#"

            rows_html += f"""
                <tr>
                    <td class="date">{pub_date}</td>
                    <td class="author">{author}</td>
                    <td class="title"><a href="{url}" target="_blank" rel="noopener">{title}</a></td>
                    <td class="summary" title="{summary}">{summary}</td>
                    <td class="reads">{reads}</td>
                    <td class="likes">{likes}</td>
                </tr>"""

        sections_html += f"""
        <div class="category-section">
            <div class="category-header">
                <span class="category-dot {dot_class}"></span>
                <span class="category-name">{cat}</span>
                <span class="category-count">{len(arts)} 篇文章</span>
            </div>
            <div class="table-wrapper">
                <table>
                    <thead>
                        <tr>
                            <th>发文日期</th>
                            <th>公众号</th>
                            <th>标题</th>
                            <th>简介</th>
                            <th>阅读</th>
                            <th>点赞</th>
                        </tr>
                    </thead>
                    <tbody>{rows_html}
                    </tbody>
                </table>
            </div>
        </div>"""

    return sections_html


def generate_report(articles, date_str):
    """生成完整 HTML 报告"""
    stats = compute_stats(articles)

    # 尝试从模板文件读取
    template_path = Path(__file__).parent / "report_template.html"
    if template_path.exists():
        template = template_path.read_text(encoding="utf-8")
    else:
        warn("模板文件未找到，使用内置模板")
        template = get_fallback_template()

    # 日期中文显示
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        weekdays = ["一", "二", "三", "四", "五", "六", "日"]
        date_cn = f"{dt.year}年{dt.month}月{dt.day}日 星期{weekdays[dt.weekday()]}"
    except ValueError:
        date_cn = date_str

    category_sections = generate_category_sections(articles)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    html = template
    html = html.replace("{{DATE}}", date_str)
    html = html.replace("{{DATE_CN}}", date_cn)
    html = html.replace("{{ACCOUNT_COUNT}}", str(stats["account_count"]))
    html = html.replace("{{ARTICLE_COUNT}}", str(stats["article_count"]))
    html = html.replace("{{AVG_READS}}", stats["avg_reads"])
    html = html.replace("{{TOTAL_LIKES}}", stats["total_likes"])
    html = html.replace("{{CATEGORY_SECTIONS}}", category_sections)
    html = html.replace("{{TIMESTAMP}}", timestamp)

    return html


def get_fallback_template():
    """内置最小 HTML 模板（当模板文件缺失时使用）"""
    return '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>公众号订阅日报 - {{DATE}}</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, sans-serif; background: #0f0f0f; color: #f0ece6; padding: 2rem; }
.header { text-align: center; padding: 2rem 0; }
.header h1 { font-size: 2rem; color: #4FC3F7; }
.header p { color: #9a9590; margin-top: 0.5rem; }
.stats { display: flex; justify-content: center; gap: 2rem; padding: 1rem; margin: 1rem 0; }
.stat-item { text-align: center; }
.stat-value { font-size: 1.5rem; font-weight: bold; color: #4FC3F7; }
.stat-label { font-size: 0.8rem; color: #666; }
.category-section { margin: 2rem 0; }
.category-header { display: flex; align-items: center; gap: 0.6rem; margin-bottom: 0.8rem; }
.category-dot { width: 10px; height: 10px; border-radius: 50%; }
.category-dot.competitor { background: #F06292; }
.category-dot.similar { background: #FFB74D; }
.category-dot.following { background: #4FC3F7; }
.category-name { font-size: 1.2rem; font-weight: bold; }
.category-count { font-size: 0.85rem; color: #9a9590; }
.table-wrapper { overflow-x: auto; border: 1px solid rgba(255,255,255,0.06); border-radius: 10px; background: #1e1e1e; }
table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
thead th { background: #1a1a1a; color: #9a9590; text-align: left; padding: 0.6rem 0.8rem; border-bottom: 1px solid rgba(255,255,255,0.06); text-transform: uppercase; font-size: 0.72rem; }
tbody td { padding: 0.6rem 0.8rem; border-bottom: 1px solid rgba(255,255,255,0.06); }
tbody tr:hover { background: #252525; }
td.date { white-space: nowrap; color: #9a9590; }
td.title a { color: #f0ece6; text-decoration: none; }
td.title a:hover { color: #4FC3F7; }
td.summary { color: #9a9590; max-width: 250px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
td.reads { color: #4FC3F7; text-align: right; }
td.likes { color: #F06292; text-align: right; }
.footer { text-align: center; padding: 2rem; color: #666; font-size: 0.8rem; margin-top: 2rem; border-top: 1px solid rgba(255,255,255,0.06); }
</style>
</head>
<body>
<div class="header">
    <h1>公众号订阅日报</h1>
    <p>{{DATE_CN}} &middot; {{ACCOUNT_COUNT}} 个公众号 &middot; {{ARTICLE_COUNT}} 篇文章</p>
</div>
<div class="stats">
    <div class="stat-item"><div class="stat-value">{{ACCOUNT_COUNT}}</div><div class="stat-label">订阅公众号</div></div>
    <div class="stat-item"><div class="stat-value">{{ARTICLE_COUNT}}</div><div class="stat-label">今日发文</div></div>
    <div class="stat-item"><div class="stat-value">{{AVG_READS}}</div><div class="stat-label">平均阅读</div></div>
    <div class="stat-item"><div class="stat-value">{{TOTAL_LIKES}}</div><div class="stat-label">总点赞</div></div>
</div>
<div class="container">{{CATEGORY_SECTIONS}}</div>
<div class="footer">由微信公众号文章订阅 Skill 生成 &middot; {{TIMESTAMP}}</div>
</body>
</html>'''


# ─── 订阅定时任务 ──────────────────────────────────────────────────────────────────
def install_subscription():
    """安装定时任务，每天自动拉取并生成日报"""
    if sys.platform == "darwin":
        PLIST_DIR.mkdir(parents=True, exist_ok=True)
        plist_path = PLIST_DIR / f"{PLIST_LABEL}.plist"

        script_path = os.path.abspath(__file__)
        log_path = str(Path.home() / "Library" / "Logs" / "qoder-gzh-subscribe.log")

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
        <string>fetch</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>6</integer>
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
            info("订阅成功! 每天 06:00 自动拉取所有订阅公众号的发文并生成日报")
            info(f"日报目录: ~/Downloads/QoderGzhReports/")
            info(f"日志: {log_path}")
            return True
        except subprocess.CalledProcessError as e:
            error(f"订阅安装失败: {e.stderr.decode()}")
            return False
    else:
        # Linux / Windows: 使用 crontab
        script_path = os.path.abspath(__file__)
        cron_line = f"0 6 * * * /usr/bin/python3 {script_path} fetch"
        try:
            subprocess.run(
                f'(crontab -l 2>/dev/null; echo "{cron_line}") | crontab -',
                shell=True, check=True, capture_output=True
            )
            info("订阅成功! 每天 06:00 自动拉取并生成日报 (crontab)")
            info(f"日报目录: ~/Downloads/QoderGzhReports/")
            return True
        except subprocess.CalledProcessError:
            warn("自动配置 crontab 失败，请手动添加:")
            print(f"  {cron_line}")
            return False


def remove_subscription_task():
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


# ─── 主流程 ────────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="微信公众号文章订阅 — 订阅公众号，追踪每日发文",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 subscribe.py add "公众号名称" --id "redfoxdata1" --category "竞对账号"
  python3 subscribe.py add "公众号名称" --id "gh_53301f7745f3"
  python3 subscribe.py add "公众号名称" --id "MzY4ODI4ODc2MA=="
  python3 subscribe.py remove "公众号名称"
  python3 subscribe.py remove "WebNotes"
  python3 subscribe.py list
  python3 subscribe.py fetch
  python3 subscribe.py report --date 2026-05-26
  python3 subscribe.py --subscribe
  python3 subscribe.py --unsubscribe

账号 ID 支持三种格式（三选一即可）：
  account    — 公众号标识，最容易获取（如 redfoxdata1）
  wxId       — 微信号，仅限自己的公众号后台查看（如 gh_53301f7745f3）
  bizInfo    — 文章链接中的 biz 编码，通过手机端浏览器提取（如 MzY4ODI4ODc2MA==）
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # ── add 子命令 ──
    add_parser = subparsers.add_parser("add", help="添加订阅")
    add_parser.add_argument("account_name", help="公众号名称（必填）")
    add_parser.add_argument("--id", dest="account_id", required=True,
                            help="账号 ID — 支持三种格式（必填）：account（公众号标识）/ wxId（微信号）/ bizInfo（文章链接编码）")
    add_parser.add_argument("--category", default="关注账号",
                            choices=DEFAULT_CATEGORIES + ["其他"],
                            help="分类标签（默认: 关注账号）")

    # ── remove 子命令 ──
    remove_parser = subparsers.add_parser("remove", help="取消订阅")
    remove_parser.add_argument("identifier", help="公众号名称 或 公众号 ID")

    # ── list 子命令 ──
    subparsers.add_parser("list", help="列出所有订阅")

    # ── fetch 子命令 ──
    fetch_parser = subparsers.add_parser("fetch", help="拉取今日发文")
    fetch_parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"),
                              help="指定日期 YYYY-MM-DD（默认: 今天）")
    fetch_parser.add_argument("--no-report", action="store_true",
                              help="仅终端展示，不生成日报")

    # ── report 子命令 ──
    report_parser = subparsers.add_parser("report", help="生成 HTML 日报")
    report_parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"),
                               help="指定日期 YYYY-MM-DD（默认: 今天）")
    report_parser.add_argument("--output-dir", help="输出目录")

    # ── 全局参数 ──
    parser.add_argument("--api-key", help="API Key")
    parser.add_argument("--subscribe", action="store_true", help="安装每日定时任务（06:00 自动拉取）")
    parser.add_argument("--unsubscribe", action="store_true", help="卸载定时任务")

    args = parser.parse_args()

    # ── Banner ──
    banner = f"""{CYAN}{BOLD}
  ╔══════════════════════════════════════╗
  ║     公众号订阅追踪 · 发文监控         ║
  ║     竞对 · 同类 · 关注 · 一网打尽     ║
  ╚══════════════════════════════════════╝{RESET}
"""
    print(banner)

    # ── 订阅/取消 ──
    if args.subscribe:
        install_subscription()
        return
    if args.unsubscribe:
        remove_subscription_task()
        return

    # ── 检查依赖 ──
    if not HAS_REQUESTS:
        error("缺少 requests 库，请安装: pip3 install requests")
        sys.exit(1)

    # ── 分发命令 ──
    if args.command == "add":
        add_subscription(args.account_name, args.account_id, args.category)
        return

    if args.command == "remove":
        remove_subscription(args.identifier)
        return

    if args.command == "list":
        list_subscriptions()
        return

    if args.command in ("fetch", "report"):
        # 检查是否有订阅
        subscriptions = load_subscriptions()
        if not subscriptions:
            error("尚未订阅任何公众号，请先用 'add' 命令添加订阅")
            print(f"\n  示例: {CYAN}python3 subscribe.py add \"公众号名称\" --id \"WebNotes\"{RESET}")
            sys.exit(1)

        # API Key
        api_key = get_api_key(cli_key=args.api_key)
        if not api_key:
            print(f"{RED}╔══════════════════════════════════════════════════╗{RESET}")
            print(f"{RED}║  未配置 API Key，请通过以下方式之一配置：      ║{RESET}")
            print(f"{RED}║                                                ║{RESET}")
            print(f"{RED}║  export REDFOX_API_KEY=ak_你的密钥             ║{RESET}")
            print(f"{RED}║  python3 subscribe.py --api-key ak_你的密钥     ║{RESET}")
            print(RED + "║  echo '{\"api_key\":\"ak_你的密钥\"}' > ~/.qoder/apis/redfox.json ║" + RESET)
            print(f"{RED}║                                                ║{RESET}")
            print(f"{RED}║  注册获取 Key: https://redfox.hk/settings/api-keys ║{RESET}")
            print(f"{RED}╚══════════════════════════════════════════════════╝{RESET}")
            sys.exit(1)

        # Session
        session = requests.Session()
        session.verify = True
        session.headers.update({
            "Content-Type": "application/json",
            "X-API-KEY": api_key,
        })

        # 拉取文章
        step(f"从 {len(subscriptions)} 个公众号拉取发文（日期: {args.date}）...")
        print()

        articles = fetch_all_articles(session, subscriptions, args.date)

        if not articles:
            warn("未获取到任何文章")
            print(f"    💡 当前 Skill 基于红狐广域库。如确认账号 ID 正确但仍查不到，")
            print(f"    请联系红狐数据获取定制支持：redfoxdata@proton.me")
            sys.exit(1)

        info(f"拉取完成: 共 {len(articles)} 篇文章")

        # 终端表格始终展示
        print_terminal_table(articles)

        # 生成 HTML 日报（fetch --no-report 时跳过）
        if args.command == "report" or (args.command == "fetch" and not args.no_report):
            step("生成 HTML 日报...")
            html_content = generate_report(articles, args.date)

            output_dir = Path(args.output_dir) if hasattr(args, 'output_dir') and args.output_dir else DEFAULT_OUTPUT_DIR
            output_dir.mkdir(parents=True, exist_ok=True)
            filename = f"公众号日报_{args.date}.html"
            output_path = output_dir / filename

            output_path.write_text(html_content, encoding="utf-8")
            info(f"日报已生成: {output_path}")

            # 打开浏览器
            if sys.platform == "darwin":
                subprocess.run(["open", str(output_path)], check=False)
            elif sys.platform == "linux":
                subprocess.run(["xdg-open", str(output_path)], check=False)

        print(f"\n{GREEN}{BOLD}✓ 完成!{RESET}")
        print(f"  订阅公众号: {len(subscriptions)} 个")
        print(f"  文章总数: {len(articles)} 篇")
        return

    # ── 无命令 ──
    parser.print_help()
    print(f"\n{CYAN}快速开始:{RESET}")
    print(f"  add <名称>        — 添加订阅")
    print(f"  remove <名称/ID>  — 取消订阅")
    print(f"  list              — 查看订阅")
    print(f"  fetch             — 拉取发文")
    print(f"  report            — 生成日报")


if __name__ == "__main__":
    main()
