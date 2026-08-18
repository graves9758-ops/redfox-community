#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
短剧-抖音信息源日报生成脚本 (增强版 v2.3)
=========================================
每日扫描抖音短剧爆款内容,智能聚类题材后生成HTML日报

v2.3 调整说明（相关词命中直查 + 无数据确认制）：
- 【相关词命中直查】关键词校验匹配 topic_keywords 中规定的**题材名+全部相关词**
  （如「打脸」命中逆袭题材相关词、「总裁」命中霸总题材相关词、「宠妻/替身」命中
  霸总相关词等），命中后**直接使用该关键词查询数据**（不替换题材、不降级全量）。
- 【无数据确认制】查询无匹配数据或全量数据不足时，**禁止自动发起任何额外查询**
  （禁止自动降级全量、禁止自动扩展题材）。脚本停止并输出推荐题材关键词，
  由 Agent 询问用户是否按推荐词重新查询，得到用户确认后才可发起查询。
- 全量查询数据不足(小于 AUTO_EXPAND_THRESHOLD)时仅提示推荐题材并等待确认，不自动扩展。

v2.2 调整说明（同步自"短剧-B站信息源" v2.2 增强 + 用户新规则）：
- 【前置校验】查询前先判断用户的输入条件：
  1) 分类/关键词是否符合短剧题材词库（穿越/霸总/重生/甜宠/悬疑等）
  2) 日期是否在有效查询范围（格式正确、不晚于今天）
- 【不满足不请求接口】关键词/分类不满足短剧题材词库时，明确提醒"关键词不满足
  查询条件"并推荐相关分类和关键词，**不发起任何接口请求**（避免浪费API额度），
  直接停止并引导用户改用推荐词重新查询。
- 【日期兜底】用户查询的日期未更新或超过查询时间范围时，自动向前回退获取最近
  时间范围数据，并明确告知"当前查询时间未更新或超过查询时间范围，已为您自动
  获取最近时间范围数据"。

v2.0 增强说明（同步自B站版，针对"数据查询结果为空"问题的降失败率机制）：
1. 【P0-日期探活】查询前先用 pageSize=1、不带 keyword 的轻量请求探测目标日期
   是否有数据；无数据立即拦截，避免盲目消耗多题材查询额度。
2. 【P0-自动回退】--latest 从最近日期向前最多回退 FALLBACK_DAYS(默认7) 天，
   找到第一个有数据的日期再生成日报；输出中明确标注实际数据日期。
3. 【P1-确认制题材补充】全量查询数据不足(小于 AUTO_EXPAND_THRESHOLD)时，
   仅提示推荐题材并等待用户确认，确认前不自动扩展题材（v2.3 确认制）。
4. 【P1-空结果重试】单题材查询为空/异常时，间隔 RETRY_INTERVAL 秒重试 1 次。
5. 【P1-题材词校验】--topics 传入明显非题材词时给出提示（不阻断，仅提醒）。
6. 【P2-结构化空因】每次空结果输出原因分类：无数据 / 关键词无匹配 / API异常。
7. 【P2-防御式解析】兼容 {"code":2000,"data":{"list":[...]}} 与直出 list 两种
   格式，防止服务端调整响应结构时脚本静默失效。

用法与原版完全兼容：
    python3 playlet_douyin_daily.py --latest
    python3 playlet_douyin_daily.py --date 2026-08-05
    python3 playlet_douyin_daily.py --topics "穿越,霸总" --latest
"""

import argparse
import json
import os
import sys
import time
import webbrowser
from datetime import datetime, timedelta
from urllib import request, error


# ============ 配置 ============
API_BASE_URL = "https://redfox.hk/story/api/parseWork/queryPlayletMsgs"
CACHE_DIR = os.path.expanduser("~/.workbuddy/cache")
CACHE_FILE = os.path.join(CACHE_DIR, "playlet_douyin_data.json")
OUTPUT_DIR = os.path.expanduser("~/Downloads/QoderReports")
DATA_UPDATE_HOUR = 15       # 数据源声称的更新时刻（仅作提示参考，不再作为唯一依据）
FALLBACK_DAYS = 7           # --latest 自动回退的最大天数
RETRY_TIMES = 1             # 空结果/异常重试次数
RETRY_INTERVAL = 4          # 重试间隔（秒）
REQUEST_TIMEOUT = 30        # 单次请求超时（秒）
AUTO_EXPAND_THRESHOLD = 100 # 全量结果少于该值时提示用户确认是否扩展题材（不自动扩展）
AUTO_EXPAND_TOPICS = ["穿越", "霸总", "重生", "悬疑", "甜宠", "逆袭"]  # 推荐扩展顺序（仅供提示，需用户确认后才查询）
HOT_TOPICS = ["穿越", "霸总", "重生", "悬疑", "甜宠", "逆袭", "年代", "战神", "古装"]  # 推荐题材顺序

# 短剧题材词库：用于 --topics 输入校验提示
# 规则：关键词需命中 topic_keywords 中规定的题材名+全部相关词（如「打脸」命中逆袭题材相关词），命中后直接用该关键词查询数据
TOPIC_KEYWORDS_THESAURUS = {
    "穿越": ["穿越", "时空", "古代", "现代", "回到", "大宋", "北宋", "南宋", "唐朝", "明朝", "清朝"],
    "霸总": ["霸总", "总裁", "豪门", "冷酷", "宠妻", "娇妻", "替身"],
    "重生": ["重生", "逆袭", "回到", "翻盘", "重来", "再生"],
    "悬疑": ["悬疑", "推理", "反转", "惊悚", "谜案", "秘密", "真相"],
    "甜宠": ["甜宠", "恋爱", "撒糖", "甜蜜", "宠溺", "甜甜"],
    "逆袭": ["逆袭", "翻身", "打脸", "崛起", "反击", "报复"],
    "年代": ["年代", "八零", "九零", "七零", "六零"],
    "战神": ["战神", "龙王", "兵王", "高手"],
    "古装": ["古装", "宫廷", "皇后", "贵妃", "王爷", "世子"],
}
# 全部有效词集合（题材名 + 各题材相关词 + 扩展词），用于关键词前置校验
TOPIC_THESAURUS = {
    "穿越", "霸总", "重生", "悬疑", "甜宠", "逆袭", "年代", "战神",
    "古装", "总裁", "豪门", "复仇", "惊悚", "推理", "反转", "爽文",
    "科幻", "玄幻", "修仙", "都市", "职场", "萌宝", "萌娃", "亲子",
    "离婚", "闪婚", "替身", "虐恋", "先婚后爱", "双重生",
}
for _t, _kws in TOPIC_KEYWORDS_THESAURUS.items():
    TOPIC_THESAURUS.add(_t)
    TOPIC_THESAURUS.update(_kws)


# ============ 工具函数 ============
def get_api_key():
    """从环境变量获取 API Key"""
    api_key = os.environ.get("REDFOX_API_KEY")
    if not api_key:
        print("❌ 错误:未找到 REDFOX_API_KEY 环境变量")
        print("请先配置:export REDFOX_API_KEY=<你的apikey>")
        sys.exit(1)
    return api_key


def calculate_latest_date():
    """按15:00规则估算最新可用日期（仅作初始起点，实际以探活为准）"""
    now = datetime.now()
    if now.hour < DATA_UPDATE_HOUR:
        return (now - timedelta(days=2)).strftime("%Y-%m-%d")
    else:
        return (now - timedelta(days=1)).strftime("%Y-%m-%d")


def validate_date(date_str):
    """旧接口保留：基于本地时钟的日期校验（新逻辑改走 probe_date）"""
    latest_date = calculate_latest_date()
    target_date = datetime.strptime(date_str, "%Y-%m-%d")
    latest = datetime.strptime(latest_date, "%Y-%m-%d")
    return target_date <= latest, latest_date


def check_topics(topics):
    """
    v2.2 前置校验：判断用户输入的分类/关键词是否符合短剧题材词库。
    返回 (有效词列表, 无效词列表, 推荐词列表)
    推荐逻辑：优先从无效词中提取包含的题材词，再补充热门题材词。
    """
    hot_topics = ["穿越", "霸总", "重生", "甜宠", "悬疑", "逆袭",
                  "年代", "战神", "古装", "都市", "科幻"]
    valid, invalid = [], []
    for t in topics:
        if t in TOPIC_THESAURUS or t == "短剧":
            valid.append(t)
        else:
            invalid.append(t)
    recommends = []
    for t in invalid:
        # 无效词若包含题材词（如"穿越重生"含"穿越""重生"），优先推荐
        contained = [w for w in TOPIC_THESAURUS if w in t or t in w]
        for c in contained:
            if c not in recommends:
                recommends.append(c)
    for h in hot_topics:
        if h not in recommends:
            recommends.append(h)
    return valid, invalid, recommends


def check_date(date_str):
    """
    v2.2 前置校验：判断日期是否在有效查询范围（格式正确、不晚于今天）。
    返回 (是否有效, 提示信息, 推荐日期或None)
    """
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return False, f"日期格式无效：{date_str}（应为 YYYY-MM-DD）", None
    today = datetime.now().date()
    if d.date() > today:
        latest = calculate_latest_date()
        return False, f"日期 {date_str} 超出有效查询范围（晚于今天，数据每日15:00更新前一天）", latest
    return True, "", None


def parse_response(result):
    """
    防御式响应解析（加固，非修复）：兼容两种格式
    格式A(API实际完整响应): {"code":2000,"data":{"list":[...],"total":M},"msg":"..."}
    格式B(兜底/直出):      {"list":[...], "pageNum":1, "pages":N, "total":M}
    返回: (items列表, error_msg或None)
    """
    if not isinstance(result, dict):
        return [], "响应非JSON对象"
    # 格式A：code/data 包装（当前 API 实际格式）
    if result.get("code") == 2000:
        data = result.get("data") or {}
        return data.get("list") or [], None
    # 显式业务错误
    code = result.get("code")
    if code is not None:
        msg = result.get("msg")
        return [], f"API业务错误 code={code} msg={msg}"
    # 格式B：直出 list（兜底）
    if "list" in result:
        return result.get("list") or [], None
    return [], None


def http_post(payload, api_key):
    """执行一次 POST 请求，返回原始响应 dict（网络/HTTP 层异常向上抛）"""
    data = json.dumps(payload).encode('utf-8')
    req = request.Request(
        API_BASE_URL,
        data=data,
        headers={
            "Content-Type": "application/json",
            "X-API-KEY": api_key
        },
        method="POST"
    )
    with request.urlopen(req, timeout=REQUEST_TIMEOUT) as response:
        return json.loads(response.read().decode('utf-8'))


def build_payload(start_time, end_time, keyword=None, page_size=200):
    """构建请求体；keyword 为 None 时表示全量查询（不带 keyword 字段）"""
    payload = {
        "msgType": "短剧",
        "platform": 1,  # 1=抖音
        "source": "短剧抖音信息源-GitHub",
        "pageNum": 1,
        "pageSize": page_size,
        "startTime": start_time,
        "endTime": end_time,
    }
    if keyword:
        payload["keyword"] = keyword
    return payload


def probe_date_available(api_key, start_time, end_time):
    """
    探活：pageSize=1 + 不带 keyword 的轻量请求，确认该日期是否有数据。
    返回 (bool, info_str)；False 说明该日期数据源无任何数据（未更新/缺失）。
    成本：每次探测约 1 次接口额度，远低于无脑全量查询。
    """
    payload = build_payload(start_time, end_time, keyword=None, page_size=1)
    try:
        result = http_post(payload, api_key)
        items, err = parse_response(result)
        if err:
            print(f"  ⚠️ 探活请求异常: {err}")
            return False, "probe_error"
        if items:
            return True, "ok"
        return False, "no_data"
    except Exception as e:
        print(f"  ⚠️ 探活请求失败: {e}")
        return False, "probe_fail"


def _fetch_topic_once(api_key, payload, topic):
    """单题材单次查询（含重试），返回 (items, api_error: bool)"""
    for attempt in range(RETRY_TIMES + 1):
        try:
            result = http_post(payload, api_key)
            items, err = parse_response(result)
            if err:
                if attempt < RETRY_TIMES:
                    time.sleep(RETRY_INTERVAL)
                continue
            return items, False  # 解析成功（可能为空 list，但非异常）
        except Exception as e:
            if attempt < RETRY_TIMES:
                print(f"  ⚠️ 题材 {topic} 第{attempt+1}次请求失败({e})，{RETRY_INTERVAL}s后重试...")
                time.sleep(RETRY_INTERVAL)
            else:
                print(f"❌ 查询题材 {topic} 失败:{str(e)}")
    return [], True


# ============ 数据获取 ============
def fetch_playlet_data(
    topics=None,
    start_time=None,
    end_time=None,
    count=200,
    use_cache=False,
):
    """
    调用 API 查询抖音短剧数据（增强版）

    Args:
        topics: 题材列表(逗号分隔)，None/空 → 全量查询，数据不足时自动扩展题材
        start_time / end_time: 查询时间窗
        count: 扫描作品数量
        use_cache: 是否使用缓存

    Returns:
        (items, meta) 其中 meta 含 reason 字段用于结构化空因:
            reason in {"ok", "no_data", "probe_fail", "probe_error",
                       "keyword_no_match", "api_error"}
    """
    if use_cache:
        cached_data = load_cache()
        if cached_data:
            print("📦 使用缓存数据")
            return cached_data, {"reason": "ok", "note": "cache"}

    if not start_time or not end_time:
        latest_date = calculate_latest_date()
        start_time = f"{latest_date} 00:00:00"
        end_time = f"{latest_date} 23:59:59"

    api_key = get_api_key()
    meta = {"reason": "ok", "probed": False, "date": start_time[:10]}

    # ---- P0-2 探活：先确认该日期数据源是否有数据 ----
    available, info = probe_date_available(api_key, start_time, end_time)
    meta["probed"] = True
    if not available:
        meta["reason"] = "no_data" if info == "no_data" else info
        print(f"📭 日期 {start_time[:10]} 数据源无数据（{info}），跳过查询以避免浪费额度")
        return [], meta

    # ---- 确定查询题材序列 ----
    # 用户指定题材 → 仅用用户列表（文档规则：自定义时不用扩展列表）
    # 未指定 → 全量查询；数据不足时自动按 AUTO_EXPAND_TOPICS 扩展
    if topics:
        query_topics = list(topics)
        auto_expand = False
    else:
        query_topics = [None]
        auto_expand = True

    all_items = []
    api_errors = 0
    expanded = False

    for topic in query_topics:
        keyword = None if topic is None or topic == "短剧" else topic
        payload = build_payload(start_time, end_time, keyword=keyword,
                                page_size=min(count, 200))
        items, had_error = _fetch_topic_once(api_key, payload, topic or "全量")
        if had_error:
            api_errors += 1
        if items:
            all_items.extend(items)

        # ---- 确认制（v2.3）：全量数据不足时不再自动扩展题材 ----
        # 仅提示推荐题材并等待用户确认，确认前不发起任何额外请求
        if auto_expand:
            unique_ids = {it.get("photoId") for it in all_items if it.get("photoId")}
            if len(unique_ids) < min(count, AUTO_EXPAND_THRESHOLD):
                expanded = True
                print(f"  ⚠️ 全量数据不足({len(unique_ids)}条 < {AUTO_EXPAND_THRESHOLD})，不自动扩展题材")
                print(f"  💡 推荐题材: {'、'.join(AUTO_EXPAND_TOPICS)}")
                print(f"  ❓ 请确认是否按推荐题材扩展查询（使用 --topics 重新查询），确认前不会发起任何额外请求")
                meta["reason"] = "need_confirm_expand"

    # 去重(基于photoId)
    seen = set()
    unique_items = []
    for item in all_items:
        item_id = item.get("photoId")
        if item_id and item_id not in seen:
            seen.add(item_id)
            unique_items.append(item)

    # 按点赞量排序
    unique_items.sort(key=lambda x: x.get("likeCount", 0), reverse=True)

    if not unique_items:
        # 探活通过但实际查询为空 → 大概率是关键词无匹配
        if topics and topics != [None]:
            meta["reason"] = "keyword_no_match"
        else:
            meta["reason"] = "no_data"
        return [], meta

    # 保存缓存
    save_cache(unique_items)
    meta["reason"] = "ok"
    return unique_items[:count], meta


# ============ 题材聚类 ============
def cluster_by_topic(items):
    """按题材聚类作品（词库与 TOPIC_KEYWORDS_THESAURUS 保持一致）"""
    topic_keywords = dict(TOPIC_KEYWORDS_THESAURUS)
    clusters = {}
    for item in items:
        title = item.get("title", "")
        matched_topics = []
        for topic, keywords in topic_keywords.items():
            if any(kw in title for kw in keywords):
                matched_topics.append(topic)
        matched_topic = matched_topics[0] if matched_topics else "其他"
        clusters.setdefault(matched_topic, []).append(item)
    return clusters


# ============ HTML 日报 ============
def format_number(num):
    """格式化数字(万→w)"""
    if num is None:
        return "0"
    if num >= 10000:
        return f"{num/10000:.1f}w"
    return str(num)


def generate_html_report(items, clusters, date_str):
    """生成HTML日报（抖音粉 #FB7299）"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    html_file = os.path.join(OUTPUT_DIR, f"短剧抖音日报_{date_str}.html")

    try:
        dt_obj = datetime.strptime(date_str, "%Y-%m-%d")
        weekdays = ["一", "二", "三", "四", "五", "六", "日"]
        date_cn = f"{dt_obj.year}年{dt_obj.month}月{dt_obj.day}日 星期{weekdays[dt_obj.weekday()]}"
    except ValueError:
        date_cn = date_str

    total_count = len(items)
    topic_count = len(clusters)
    total_likes = sum(item.get("likeCount", 0) for item in items)
    avg_likes = total_likes / total_count if total_count > 0 else 0

    category_cards = ""
    for i, (topic, topic_items) in enumerate(
            sorted(clusters.items(), key=lambda x: len(x[1]), reverse=True), 1):
        articles_html = ""
        for item in topic_items[:5]:
            title = item.get("title", "无标题")
            author = item.get("userName", "")
            cover = item.get("coverUrl") or ""
            url = item.get("url") or ""
            photo_id = item.get("photoId") or ""

            raw_shares = item.get("shareCount", 0) or 0
            raw_likes = item.get("likeCount", 0) or 0
            raw_comments = item.get("commentCount", 0) or 0

            metrics_parts = []
            if raw_shares > 0:
                metrics_parts.append(f'<span class="metric">🔗 {format_number(raw_shares)}</span>')
            if raw_likes > 0:
                metrics_parts.append(f'<span class="metric">👍 {format_number(raw_likes)}</span>')
            if raw_comments > 0:
                metrics_parts.append(f'<span class="metric">💬 {format_number(raw_comments)}</span>')
            metrics_html = ''.join(metrics_parts)

            cover_html = ""
            if cover:
                cover_html = f'<img class="article-cover" src="{cover}" alt="" loading="lazy">'

            if url:
                title_html = f'<a href="{url}" target="_blank" class="article-title">{title}</a>'
            elif photo_id:
                title_html = f'<a href="https://www.douyin.com/video/{photo_id}" target="_blank" class="article-title">{title}</a>'
            else:
                title_html = f'<span class="article-title">{title}</span>'

            articles_html += f'''
                <div class="article-item">
                    {cover_html}
                    <div class="article-info">
                        {title_html}
                        <div class="article-meta">
                            <span class="author">{author}</span>
                            <span class="metrics">
                                {metrics_html}
                            </span>
                        </div>
                    </div>
                </div>'''

        category_cards += f'''
        <div class="category-card reveal">
            <div class="card-header">
                <span class="card-number">{i:02d}</span>
                <h3 class="card-category">#{topic}</h3>
                <span class="card-count">{len(topic_items)} 部</span>
            </div>
            <div class="card-body">{articles_html}
            </div>
        </div>'''

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    html_content = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>短剧-抖音信息源 - {date_str}</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, sans-serif; background: #1a1a1a; color: #e8e4df; padding: 2rem; }}
.header {{ text-align: center; padding: 2rem 0; }}
.header h1 {{ font-size: 2rem; color: #FB7299; }}
.header p {{ color: #9a9590; margin-top: 0.5rem; }}
.stats {{ display: flex; justify-content: center; gap: 2rem; padding: 1rem; margin: 1rem 0; }}
.stat-item {{ text-align: center; }}
.stat-value {{ font-size: 1.5rem; font-weight: bold; color: #FB7299; }}
.stat-label {{ font-size: 0.8rem; color: #9a9590; }}
.cards {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(360px, 1fr)); gap: 1.5rem; max-width: 1200px; margin: 2rem auto; }}
.category-card {{ background: #2d2d2d; border-radius: 12px; padding: 1.5rem; }}
.card-header {{ display: flex; align-items: center; gap: 0.8rem; margin-bottom: 1rem; padding-bottom: 0.8rem; border-bottom: 1px solid #3d3d3d; }}
.card-number {{ font-size: 1.5rem; font-weight: bold; color: #FB7299; }}
.card-category {{ flex: 1; font-size: 1.1rem; }}
.card-count {{ color: #9a9590; font-size: 0.9rem; }}
.article-item {{ padding: 0.6rem 0; border-bottom: 1px solid #3d3d3d; display: flex; gap: 0.8rem; }}
.article-item:last-child {{ border-bottom: none; }}
.article-cover {{ width: 60px; height: 60px; border-radius: 6px; object-fit: cover; flex-shrink: 0; }}
.article-info {{ flex: 1; min-width: 0; }}
.article-title {{ color: #e8e4df; font-size: 0.9rem; line-height: 1.4; display: block; }}
.article-title:hover {{ color: #FB7299; text-decoration: underline; cursor: pointer; }}
a.article-title {{ text-decoration: none; }}
a.article-title:hover {{ color: #FB7299; text-decoration: underline; }}
.article-meta {{ display: flex; justify-content: space-between; margin-top: 0.3rem; font-size: 0.75rem; color: #9a9590; }}
.metrics {{ display: flex; gap: 0.8rem; }}
.footer {{ text-align: center; padding: 2rem; color: #666; font-size: 0.8rem; }}
.reveal {{ animation: fadeIn 0.5s ease-in; }}
@keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(20px); }} to {{ opacity: 1; transform: translateY(0); }} }}
</style>
</head>
<body>
<div class="header">
    <h1>🎬 短剧-抖音信息源</h1>
    <p>{date_cn} | 共 {total_count} 部热门短剧</p>
</div>
<div class="stats">
    <div class="stat-item"><div class="stat-value">{topic_count}</div><div class="stat-label">题材</div></div>
    <div class="stat-item"><div class="stat-value">{total_count}</div><div class="stat-label">短剧</div></div>
    <div class="stat-item"><div class="stat-value">{format_number(int(avg_likes))}</div><div class="stat-label">平均点赞</div></div>
    <div class="stat-item"><div class="stat-value">{format_number(total_likes)}</div><div class="stat-label">总点赞</div></div>
</div>
<div class="cards">{category_cards}</div>
<div class="footer">Generated at {timestamp} by 短剧-抖音信息源 Skill<br>数据说明:每日15:00更新前一天的数据 | 数据来源:红狐Hub</div>
</body>
</html>'''

    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    return html_file


# ============ 缓存 ============
def load_cache():
    if not os.path.exists(CACHE_FILE):
        return None
    try:
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
            if time.time() - cache_data.get("timestamp", 0) < 3600:
                return cache_data.get("items")
    except Exception:
        pass
    return None


def save_cache(items):
    os.makedirs(CACHE_DIR, exist_ok=True)
    cache_data = {"timestamp": time.time(), "items": items}
    try:
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


# ============ 主流程 ============
def find_latest_available_date(api_key, max_fallback=FALLBACK_DAYS):
    """
    P0-2 自动回退：从最近日期开始向前探测，返回第一个有数据的日期。
    返回 (date_str, found: bool)
    """
    latest = calculate_latest_date()
    cursor = datetime.strptime(latest, "%Y-%m-%d")
    for i in range(max_fallback + 1):
        d = (cursor - timedelta(days=i)).strftime("%Y-%m-%d")
        print(f"  🔎 探测 {d} ...", end="")
        ok, info = probe_date_available(
            api_key, f"{d} 00:00:00", f"{d} 23:59:59"
        )
        print(" 有数据" if ok else f" 无数据({info})")
        if ok:
            return d, True
    return latest, False


def main():
    global OUTPUT_DIR
    parser = argparse.ArgumentParser(description="短剧-抖音信息源日报生成工具 (v2.2增强版)")
    parser.add_argument("--topics", type=str, help="题材关键词,逗号分隔;不满足短剧题材词时提醒并推荐,不请求接口")
    parser.add_argument("--count", type=int, default=200, help="扫描作品数量")
    parser.add_argument("--date", type=str, help="指定日期 YYYY-MM-DD;超出有效范围时提醒并自动回退最近有数据的日期")
    parser.add_argument("--start-time", type=str, help="开始时间 YYYY-MM-DD HH:MM:SS")
    parser.add_argument("--end-time", type=str, help="结束时间 YYYY-MM-DD HH:MM:SS")
    parser.add_argument("--latest", action="store_true", help="使用最新有数据的日期(自动回退)")
    parser.add_argument("--output-dir", type=str, default=OUTPUT_DIR, help="输出目录")
    parser.add_argument("--api-key", type=str, help="指定 API Key")
    parser.add_argument("--subscribe", action="store_true", help="开启每日订阅")
    parser.add_argument("--unsubscribe", action="store_true", help="关闭每日订阅")
    parser.add_argument("--from-cache", action="store_true", help="使用缓存数据")
    args = parser.parse_args()

    if args.subscribe:
        print("✅ 已开启每日订阅,日报将自动保存至:", OUTPUT_DIR)
        return
    if args.unsubscribe:
        print("✅ 已关闭每日订阅")
        return

    if args.output_dir:
        OUTPUT_DIR = args.output_dir

    api_key = args.api_key or get_api_key()

    # ---- 前置校验：关键词/分类是否符合短剧题材词库（不满足则不请求接口）----
    topics = None
    if args.topics:
        raw_topics = [t.strip() for t in args.topics.split(",") if t.strip()]
        valid_topics, invalid_topics, recommends = check_topics(raw_topics)
        if invalid_topics:
            print(f"⚠️ 关键词 {invalid_topics} 不满足短剧查询条件（短剧按题材/剧情词匹配标题，非短剧题材词大概率无结果）")
            print(f"💡 推荐相关分类和关键词：{'、'.join(recommends[:10])}")
            if valid_topics:
                print(f"✅ 已保留有效关键词 {valid_topics} 继续查询，无效关键词已自动忽略")
                topics = valid_topics
            else:
                print("🛑 关键词均不满足短剧查询条件，未发起任何接口请求。请使用推荐题材词重新查询。")
                return
        else:
            topics = valid_topics

    # ---- 确定查询日期 ----
    if args.start_time:
        start_time = args.start_time
        date_str = args.start_time[:10]
        end_time = args.end_time or f"{date_str} 23:59:59"
    elif args.latest:
        # P0-2 自动回退：探测最近有数据的日期
        print(f"🔎 --latest: 自动寻找最近有数据的日期(最多回退{FALLBACK_DAYS}天)...")
        date_str, found = find_latest_available_date(api_key)
        if not found:
            print(f"📭 最近 {FALLBACK_DAYS} 天内均无数据，请稍后再试或联系数据源确认更新状态")
            return
        start_time = f"{date_str} 00:00:00"
        end_time = f"{date_str} 23:59:59"
        print(f"✅ 已定位最新可用日期: {date_str}")
    elif args.date:
        date_str = args.date
        # v2.2: 前置校验——日期格式与有效查询范围
        date_ok, date_msg, date_suggest = check_date(date_str)
        if not date_ok:
            print(f"⚠️ {date_msg}")
            if date_suggest:
                print(f"💡 推荐查询时间范围：{date_suggest}（已为您自动获取该时间范围数据）")
        # 探活式预检（替代纯本地时钟判断）
        ok, info = probe_date_available(api_key, f"{date_str} 00:00:00", f"{date_str} 23:59:59")
        if not ok:
            # v2.1: 日期兜底——未更新/超范围时自动回退最近有数据的日期，不再等待确认
            print(f"⚠️ 当前查询时间 {date_str} 未更新或超过查询时间范围，已为您自动获取最近时间范围数据...")
            new_date, found = find_latest_available_date(api_key)
            if not found:
                print(f"📭 最近 {FALLBACK_DAYS} 天内均无数据，请稍后再试或联系数据源确认更新状态")
                return
            print(f"✅ 已为您自动获取最近时间范围数据: {new_date}（原查询 {date_str} 未更新或超过查询时间范围）")
            date_str = new_date
        start_time = f"{date_str} 00:00:00"
        end_time = f"{date_str} 23:59:59"
    else:
        date_str = calculate_latest_date()
        start_time = f"{date_str} 00:00:00"
        end_time = f"{date_str} 23:59:59"

    print(f"🔍 正在查询 {date_str} 的抖音短剧数据...")

    items, meta = fetch_playlet_data(
        topics=topics,
        start_time=start_time,
        end_time=end_time,
        count=args.count,
        use_cache=args.from_cache,
    )

    if not items:
        reason = meta.get("reason", "unknown")
        hint = {
            "no_data": "数据源当日无数据（未更新或缺失）",
            "probe_fail": "探测请求失败（网络/接口异常）",
            "probe_error": "探测请求异常（接口返回异常）",
            "keyword_no_match": "查询条件(题材词)在该日期无匹配作品",
            "api_error": "接口调用异常",
        }.get(reason, "未知原因")
        print(f"📭 未查询到相关数据 [原因: {hint}]")
        if reason == "no_data":
            print("💡 建议: 使用 --latest 自动回退到最近有数据的日期")
        # v2.3 无数据确认制：提示推荐题材并等待用户确认，不自动降级全量/不自动扩展
        print(f"💡 推荐题材关键词：{'、'.join(HOT_TOPICS)}")
        print("❓ 是否按推荐题材重新查询？请确认后使用 --topics 重新查询（确认前不发起任何额外请求）。")
        return

    print(f"✅ 共获取 {len(items)} 部短剧作品")

    clusters = cluster_by_topic(items)
    print(f"📊 聚类为 {len(clusters)} 个题材方向")

    html_file = generate_html_report(items, clusters, date_str)
    print(f"📄 日报已生成:{html_file}")

    webbrowser.open(f"file://{html_file}")

    print(f"\n## 短剧-抖音信息源 · {date_str} 日报\n")
    print(f"**扫描 {len(items)} 部热门短剧,聚类 {len(clusters)} 个题材方向**\n")
    print("### 题材概览\n")
    print("| 题材 | 数量 | 占比 | 爆款亮点 |")
    print("|------|------|------|---------|")
    for topic, topic_items in sorted(clusters.items(), key=lambda x: len(x[1]), reverse=True):
        top_item = topic_items[0] if topic_items else {}
        print(f"| #{topic} | {len(topic_items)}部 | {len(topic_items)/len(items)*100:.1f}% | 《{top_item.get('title', '')[:20]}》{format_number(top_item.get('likeCount', 0))}赞 |")


if __name__ == "__main__":
    main()
