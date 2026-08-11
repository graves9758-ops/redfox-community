#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""抖音涨粉账号推荐数据获取脚本

通过红狐数据API获取抖音涨粉榜数据，支持日榜/周榜/月榜，27个分类查询。
使用原生 urllib 发起请求，API Key 从环境变量 REDFOX_API_KEY 读取。

用法:
    python scripts/gzh_growth_fetcher.py --rank_type day --keyword 科技 --top_n 50
    python scripts/gzh_growth_fetcher.py --rank_type week --category 数码科技
    python scripts/gzh_growth_fetcher.py --rank_type month --category 全部 --top_n 50
    python scripts/gzh_growth_fetcher.py --list_categories
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime, timedelta
from urllib.parse import quote

# Windows 终端强制 UTF-8 输出，避免 GBK 编码错误
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


# ===== 常量 =====
API_URL = "https://redfox.hk/story/api/dyData/getDyRiseFansRank"
SOURCE = "抖音涨粉账号推荐-GitHub"
SKILL_ID = "7637816739572727835"

# Shell 配置文件候选列表（按优先级）
SHELL_RC_FILES = [
    os.path.expanduser("~/.zshrc"),
    os.path.expanduser("~/.bashrc"),
    os.path.expanduser("~/.bash_profile"),
    os.path.expanduser("~/.profile"),
]


def _get_api_key():
    """获取 REDFOX_API_KEY，优先级：环境变量 > shell 配置文件 > 提示配置"""
    # 1. 优先从当前环境变量获取
    key = os.environ.get("REDFOX_API_KEY", "").strip()
    if key:
        return key

    # 2. 尝试从 shell 配置文件中读取
    import re
    pattern = re.compile(r'^\s*export\s+REDFOX_API_KEY\s*=\s*["\']?([^"\';\s]+)["\']?', re.MULTILINE)
    for rc_file in SHELL_RC_FILES:
        if os.path.isfile(rc_file):
            try:
                with open(rc_file, "r", encoding="utf-8") as f:
                    content = f.read()
                match = pattern.search(content)
                if match:
                    key = match.group(1).strip()
                    if key:
                        os.environ["REDFOX_API_KEY"] = key
                        return key
            except Exception:
                continue

    # 3. 未找到，提示用户配置
    raise ValueError(
        "未找到 REDFOX_API_KEY。\n"
        "请按以下方式配置：\n"
        "  macOS/Linux：export REDFOX_API_KEY=ak_xxxxxxxx（追加到 ~/.zshrc 或 ~/.bashrc 后执行 source）\n"
        "  Windows：[Environment]::SetEnvironmentVariable(\"REDFOX_API_KEY\", \"ak_xxxxxxxx\", \"User\")\n"
        "API Key 可在 https://redfox.hk?source=github 注册后于个人中心获取。"
    )

CATEGORIES = [
    "全部", "个人才艺", "生活vlog", "财富理财", "二次元", "居家装修",
    "学习教育", "小剧场", "数码科技", "旅行", "美食", "化妆美容",
    "动物", "亲子", "汽车", "情感", "三农", "健康医学",
    "潮流风尚", "舞蹈才艺", "颜值造型", "人文", "音乐", "影视",
    "身体锻炼", "体育", "明星娱乐", "游戏"
]

RANK_TYPE_MAP = {
    "day": "日榜",
    "week": "周榜",
    "month": "月榜"
}

DATE_TYPE_MAP = {
    "day": 1,
    "week": 2,
    "month": 3
}

# 榜单更新时间规则
DAY_UPDATE_HOUR = 18
DAY_UPDATE_MINUTE = 0
MONTH_UPDATE_DAY = 3
MONTH_UPDATE_HOUR = 18
MONTH_UPDATE_MINUTE = 0

DATA_CACHE_FILE = os.path.join(os.path.expanduser("~"), ".workbuddy", "cache", "dy_rise_ranking_data.json")

BILL_NOTE_TEMPLATES = {
    "day": "💡 榜单说明：抖音日榜每日18:00更新前一日数据，本次排名数据的获取时间为{fetch_date}，与实时数据存在差异。",
    "week": "💡 榜单说明：抖音周榜每周一18:00更新前一周数据，本次排名数据的获取时间为{fetch_date}，与实时数据存在差异。",
    "month": "💡 榜单说明：抖音月榜每月3号18:00更新上一月数据，本次排名数据的获取时间为{fetch_date}，与实时数据存在差异。",
}

# 日期查询范围限制
DAY_MAX_DAYS_BACK = 7
WEEK_MAX_WEEKS_BACK = 3
MONTH_MAX_MONTHS_BACK = 3


# ===== 日期计算 =====
def _is_after_day_update(now=None):
    """判断当前时间是否已过日榜/周榜更新时间(18:00)"""
    if now is None:
        now = datetime.now()
    cutoff = now.replace(hour=DAY_UPDATE_HOUR, minute=DAY_UPDATE_MINUTE, second=0, microsecond=0)
    return now >= cutoff


def _is_after_month_update(now=None):
    """判断当前时间是否已过月榜更新时间(当月3号18:00)"""
    if now is None:
        now = datetime.now()
    cutoff = now.replace(day=MONTH_UPDATE_DAY, hour=MONTH_UPDATE_HOUR,
                         minute=MONTH_UPDATE_MINUTE, second=0, microsecond=0)
    return now >= cutoff


def get_latest_query_date(rank_type="day"):
    """获取最新可查询的榜单日期

    Args:
        rank_type: day/week/month

    Returns:
        str: 查询日期字符串 (yyyy-MM-dd)
    """
    now = datetime.now()

    if rank_type == "day":
        if _is_after_day_update(now):
            target = now - timedelta(days=1)
        else:
            target = now - timedelta(days=2)
        return target.strftime("%Y-%m-%d")

    elif rank_type == "week":
        weekday = now.weekday()
        this_monday = now - timedelta(days=weekday)
        if _is_after_day_update(now):
            return this_monday.strftime("%Y-%m-%d")
        else:
            last_monday = this_monday - timedelta(weeks=1)
            return last_monday.strftime("%Y-%m-%d")

    elif rank_type == "month":
        if _is_after_month_update(now):
            if now.month == 1:
                return datetime(now.year - 1, 12, 1).strftime("%Y-%m-%d")
            else:
                return datetime(now.year, now.month - 1, 1).strftime("%Y-%m-%d")
        else:
            if now.month == 1:
                return datetime(now.year - 1, 11, 1).strftime("%Y-%m-%d")
            elif now.month == 2:
                return datetime(now.year - 1, 12, 1).strftime("%Y-%m-%d")
            else:
                return datetime(now.year, now.month - 2, 1).strftime("%Y-%m-%d")

    return now.strftime("%Y-%m-%d")


def get_earliest_query_date(rank_type="day"):
    """获取可查询的最早日期（限制范围）

    Args:
        rank_type: day/week/month

    Returns:
        str: 最早可查询日期字符串 (yyyy-MM-dd)
    """
    now = datetime.now()

    if rank_type == "day":
        earliest = now - timedelta(days=DAY_MAX_DAYS_BACK)
        return earliest.strftime("%Y-%m-%d")

    elif rank_type == "week":
        weekday = now.weekday()
        this_monday = now - timedelta(days=weekday)
        earliest_monday = this_monday - timedelta(weeks=WEEK_MAX_WEEKS_BACK)
        return earliest_monday.strftime("%Y-%m-%d")

    elif rank_type == "month":
        m = now.month
        y = now.year
        m -= MONTH_MAX_MONTHS_BACK
        while m <= 0:
            m += 12
            y -= 1
        return datetime(y, m, 1).strftime("%Y-%m-%d")

    return now.strftime("%Y-%m-%d")


def validate_and_adjust_date(rank_type, user_date_str):
    """验证用户指定的日期是否在可查询范围内，超出范围则自动调整

    Args:
        rank_type: day/week/month
        user_date_str: 用户指定的日期 (yyyy-MM-dd)

    Returns:
        dict: {original_date, adjusted_date, is_adjusted, reminder}
    """
    user_date = datetime.strptime(user_date_str, "%Y-%m-%d")
    latest = datetime.strptime(get_latest_query_date(rank_type), "%Y-%m-%d")
    earliest = datetime.strptime(get_earliest_query_date(rank_type), "%Y-%m-%d")

    if earliest <= user_date <= latest:
        return {
            "original_date": user_date_str,
            "adjusted_date": user_date_str,
            "is_adjusted": False,
            "reminder": ""
        }

    if user_date > latest:
        adjusted = latest.strftime("%Y-%m-%d")
    else:
        adjusted = earliest.strftime("%Y-%m-%d")

    reminder = (
        '非常抱歉🙏，目前抖音榜单最多支持回溯「近7天的日榜/近3周的周榜/近3个月的月榜」，'
        '我已为您查询最接近您需求的时间范围~'
    )

    return {
        "original_date": user_date_str,
        "adjusted_date": adjusted,
        "is_adjusted": True,
        "reminder": reminder
    }


def get_data_time_range(rank_type, rank_date):
    """根据榜单类型和查询日期生成数据统计时间周期描述"""
    import calendar
    date_obj = datetime.strptime(rank_date, "%Y-%m-%d")
    if rank_type == "day":
        return rank_date
    elif rank_type == "week":
        end_date = date_obj + timedelta(days=6)
        return f"{date_obj.strftime('%Y-%m-%d')}至{end_date.strftime('%Y-%m-%d')}"
    elif rank_type == "month":
        last_day = calendar.monthrange(date_obj.year, date_obj.month)[1]
        return f"{date_obj.strftime('%Y-%m')}-01至{date_obj.strftime('%Y-%m')}-{last_day:02d}"
    return rank_date


def get_today_query_reminder(rank_type="day"):
    """当用户查询今日日榜但数据未更新时，生成提醒"""
    if rank_type == "day" and not _is_after_day_update():
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        return (
            '日榜数据暂未更新，将为您查询最接近您需求日期的榜单数据~\n'
            f'推荐查询昨日更新的最新榜单（{yesterday}日榜）'
        )
    return ""


# ===== API调用 =====
def fetch_ranking_data(rank_type="day", rank_date=None, category="全部"):
    """获取抖音涨粉账号推荐数据

    Args:
        rank_type: day/week/month
        rank_date: 查询日期 (yyyy-MM-dd)，None则自动计算
        category: 分类名称

    Returns:
        list: API返回的data数组
    """
    if rank_date is None:
        rank_date = get_latest_query_date(rank_type)

    # 获取凭证
    credential = _get_api_key()

    date_type = DATE_TYPE_MAP.get(rank_type, 1)

    payload = {
        "dateType": date_type,
        "rankDate": rank_date,
        "category": category,
        "source": "dy_rise_fans_rank"
    }

    headers = {
        "Content-Type": "application/json",
        "X-API-KEY": credential
    }

    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(API_URL, data=data, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=30) as resp:
            if resp.status >= 400:
                raise ValueError(f"HTTP请求失败: {resp.status}")
            body = resp.read().decode("utf-8")
            result = json.loads(body)

        if str(result.get("code")) not in ("200", "2000"):
            raise ValueError(f"API返回错误: code={result.get('code')}, msg={result.get('msg', '未知错误')}")

        return result.get("data", [])

    except urllib.error.URLError as e:
        raise ValueError(f"请求失败: {str(e)}")


# ===== 分类匹配 =====
CATEGORY_KEYWORDS = {
    "全部": ["全部", "综合", "全部", "热门", "推荐", "随便", "总榜", "整体"],
    "个人才艺": ["才艺", "个人", "技能", "展示"],
    "生活vlog": ["生活", "vlog", "日常", "VLOG", "Vlog"],
    "财富理财": ["财富", "理财", "投资", "基金", "股票", "保险", "财务", "赚钱"],
    "二次元": ["二次元", "动漫", "ACG", "cosplay", "Cosplay"],
    "居家装修": ["居家", "装修", "家居", "装饰", "房子装修"],
    "学习教育": ["教育", "学习", "考试", "培训", "考研", "留学", "英语"],
    "小剧场": ["小剧场", "短剧", "剧情", "剧场"],
    "数码科技": ["数码", "科技", "手机", "电脑", "智能", "AI", "互联网", "软件"],
    "旅行": ["旅行", "旅游", "出行", "攻略", "景点", "酒店", "度假"],
    "美食": ["美食", "餐饮", "做饭", "烹饪", "餐厅", "探店", "食谱", "吃"],
    "化妆美容": ["化妆", "美容", "护肤", "美妆", "彩妆", "美体"],
    "动物": ["动物", "宠物", "猫", "狗", "萌宠"],
    "亲子": ["亲子", "育儿", "宝宝", "儿童", "母婴"],
    "汽车": ["汽车", "车", "新能源", "电动车", "买车"],
    "情感": ["情感", "恋爱", "婚姻", "情绪", "心理"],
    "三农": ["三农", "农村", "农业", "农民", "种植"],
    "健康医学": ["健康", "医学", "养生", "保健", "中医", "医疗"],
    "潮流风尚": ["潮流", "时尚", "穿搭", "服饰", "OOTD", "ootd", "搭配"],
    "舞蹈才艺": ["舞蹈", "跳舞", "舞"],
    "颜值造型": ["颜值", "造型", "美", "颜值博主"],
    "人文": ["人文", "文化", "历史", "哲学", "人文社科"],
    "音乐": ["音乐", "唱歌", "乐器", "歌曲"],
    "影视": ["影视", "电影", "电视", "剧集", "综艺"],
    "身体锻炼": ["锻炼", "健身", "运动", "减肥", "瘦身", "体能"],
    "体育": ["体育", "篮球", "足球", "运动赛事"],
    "明星娱乐": ["明星", "娱乐", "娱乐圈", "偶像"],
    "游戏": ["游戏", "电竞", "手游", "端游", "主机"]
}


def match_category(keyword):
    """根据关键词匹配分类

    Args:
        keyword: 搜索关键词

    Returns:
        str or None or list: 匹配到的分类名
    """
    if keyword in CATEGORIES:
        return keyword
    matches = [c for c in CATEGORIES if keyword in c]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        return matches
    # 关键词模糊匹配
    keyword_lower = keyword.lower().strip()
    for category, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw.lower() in keyword_lower or keyword_lower in kw.lower():
                return category
    return None


# ===== 数据格式化 =====
def format_number(num):
    """格式化数字：超过1万显示x.x万，超过1亿显示x.x亿"""
    try:
        num = int(num)
    except (ValueError, TypeError):
        return str(num)
    if num >= 100000000:
        return f"{num / 100000000:.1f}亿"
    if num >= 10000:
        return f"{num / 10000:.1f}万"
    return str(num)


def format_rate(rate):
    """格式化涨粉率：0.15 -> 15.0%"""
    try:
        return f"{float(rate) * 100:.1f}%"
    except (ValueError, TypeError):
        return str(rate)


def format_ranking_table(data_list, top_n=50, start=1):
    """格式化榜单为Markdown表格

    表格字段: 排名 | 账号名称 | 总粉丝数 | 涨粉率 | 粉丝增量

    Args:
        data_list: API返回的data数组
        top_n: 显示前N条
        start: 起始排名(1-based)

    Returns:
        str: Markdown表格字符串
    """
    items = data_list[start-1:start-1+top_n]

    header = "| 排名 | 账号名称 | 总粉丝数 | 涨粉率 | 粉丝增量 |"
    separator = "| ---: | :--- | ---: | ---: | ---: |"

    rows = []
    for item in items:
        rank = item.get("ranking", "-")
        name = item.get("nickname", "-")
        account_link = item.get("accountLink", "")
        if account_link:
            name_link = f"[{name}]({account_link})"
        else:
            name_link = name
        follower_count = format_number(item.get("followerCount", 0))
        fans_incr_rate = format_rate(item.get("fansIncrRate", 0))
        add_follower = format_number(item.get("addFollowerCount", 0))

        rank_medals = {1: "🥇", 2: "🥈", 3: "🥉"}
        if isinstance(rank, int) and rank in rank_medals:
            row = f"| {rank_medals[rank]} | **{name_link}** | **{follower_count}** | **{fans_incr_rate}** | **{add_follower}** |"
        else:
            row = f"| {rank} | {name_link} | {follower_count} | {fans_incr_rate} | {add_follower} |"
        rows.append(row)

    return "\n".join([header, separator] + rows)


def _safe_float(val, default=0.0):
    """安全转换为float"""
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def _median(values):
    """计算中位数"""
    if not values:
        return 0.0
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    mid = n // 2
    if n % 2 == 0:
        return (sorted_vals[mid - 1] + sorted_vals[mid]) / 2
    return sorted_vals[mid]


def format_analysis(data_list, rank_type="day", top_n=50):
    """格式化涨粉推荐分析（3维度结构化输出）

    维度一：涨粉态势概览（全量数据统计）
    维度二：增长模式分析（分层对比洞察）
    维度三：运营洞察建议（可执行决策参考）

    Args:
        data_list: API返回的data数组
        rank_type: day/week/month
        top_n: 分析前N个账号

    Returns:
        str: Markdown分析文本
    """
    rank_label = RANK_TYPE_MAP.get(rank_type, "日榜")
    items = data_list[:top_n]

    if not items:
        return "暂无数据可供分析。"

    lines = [f"### 抖音涨粉账号推荐{rank_label}分析\n"]
    lines.append("以下内容分析基于获取的全部数据（TOP50）进行~\n")

    # ===== 维度一：涨粉态势概览 =====
    rates = [_safe_float(item.get("fansIncrRate", 0)) for item in items]
    increments = [_safe_float(item.get("addFollowerCount", 0)) for item in items]

    avg_rate = sum(rates) / len(rates) if rates else 0
    median_rate = _median(rates)
    total_increment = sum(increments)
    top10_increment = sum(sorted(increments, reverse=True)[:min(10, len(increments))])
    concentration = (top10_increment / total_increment * 100) if total_increment > 0 else 0

    # 增量分层
    tier_10w = sum(1 for v in increments if v >= 100000)
    tier_5w = sum(1 for v in increments if 50000 <= v < 100000)
    tier_1w = sum(1 for v in increments if 10000 <= v < 50000)
    tier_below = sum(1 for v in increments if v < 10000)

    lines.append("#### 一、涨粉态势概览（全量数据统计）")
    lines.append(f"- **平均涨粉率**：{avg_rate * 100:.1f}%")
    lines.append(f"- **中位数涨粉率**：{median_rate * 100:.1f}%")
    if avg_rate > median_rate * 1.5:
        lines.append(f"  > 平均值远高于中位数，说明涨粉分化严重，少数高增长账号拉高了整体水平")
    lines.append(f"- **增量集中度**：TOP10占比{concentration:.0f}%" + ("（头部集中度高）" if concentration > 50 else "（分布相对均衡）"))
    lines.append(f"- **增量分层分布**：10万+ {tier_10w}个 | 5-10万 {tier_5w}个 | 1-5万 {tier_1w}个 | 1万以下 {tier_below}个")
    lines.append("")

    # ===== 维度二：增长模式分析 =====
    # 按粉丝基数分3层
    tier_head = [item for item in items if _safe_float(item.get("followerCount", 0)) >= 5000000]
    tier_mid = [item for item in items if 1000000 <= _safe_float(item.get("followerCount", 0)) < 5000000]
    tier_tail = [item for item in items if _safe_float(item.get("followerCount", 0)) < 1000000]

    def _tier_stats(tier_items, tier_name):
        if not tier_items:
            return f"- **{tier_name}**：0个账号"
        tier_rates = [_safe_float(it.get("fansIncrRate", 0)) for it in tier_items]
        tier_increments = [_safe_float(it.get("addFollowerCount", 0)) for it in tier_items]
        avg_r = sum(tier_rates) / len(tier_rates) * 100
        avg_inc = sum(tier_increments) / len(tier_increments)
        # 找该层涨粉率最高的账号
        best = max(tier_items, key=lambda x: _safe_float(x.get("fansIncrRate", 0)))
        best_name = best.get("nickname", "未知")
        best_rate = format_rate(best.get("fansIncrRate", 0))
        return (f"- **{tier_name}**：{len(tier_items)}个账号，平均涨粉率{avg_r:.1f}%，"
                f"平均粉丝增量{format_number(int(avg_inc))}，涨粉率最高：{best_name}（{best_rate}）")

    lines.append("#### 二、增长模式分析（分层对比洞察）")
    lines.append("")
    lines.append(_tier_stats(tier_head, "头部大号（≥500万）"))
    lines.append(_tier_stats(tier_mid, "中腰部号（100-500万）"))
    lines.append(_tier_stats(tier_tail, "尾部小号（<100万）"))
    lines.append("")

    # 判断增长模式
    head_avg_rate = sum(_safe_float(it.get("fansIncrRate", 0)) for it in tier_head) / len(tier_head) if tier_head else 0
    tail_avg_rate = sum(_safe_float(it.get("fansIncrRate", 0)) for it in tier_tail) / len(tier_tail) if tier_tail else 0

    if tail_avg_rate > head_avg_rate * 3 and tail_avg_rate > 0.1:
        mode = "小号爆发型"
        mode_desc = "尾部小号涨粉率远超头部，增长主要由新锐账号驱动"
    elif head_avg_rate >= tail_avg_rate * 0.7 and head_avg_rate > 0:
        mode = "大号稳增型"
        mode_desc = "头部大号保持稳定增长，粉丝基数仍是增量主力"
    else:
        mode = "混合增长型"
        mode_desc = "各层级账号均有增长动力，无单一主导模式"
    lines.append(f"- **主导增长模式**：{mode} — {mode_desc}")
    lines.append("")

    # ===== 维度三：运营洞察建议 =====
    lines.append("#### 三、运营洞察建议（可执行决策参考）")
    lines.append("")

    # 涨粉标杆：涨粉率TOP3 且 粉丝增量TOP10
    by_rate = sorted(items, key=lambda x: _safe_float(x.get("fansIncrRate", 0)), reverse=True)
    top3_by_rate = by_rate[:3]
    top10_by_increment = sorted(items, key=lambda x: _safe_float(x.get("addFollowerCount", 0)), reverse=True)[:10]
    top10_names = {it.get("nickname") for it in top10_by_increment}
    benchmarks = [it for it in top3_by_rate if it.get("nickname") in top10_names]
    if not benchmarks:
        benchmarks = top3_by_rate[:2]  # fallback

    lines.append("**🎯 涨粉标杆（值得研究的账号）**")
    for it in benchmarks:
        name = it.get("nickname", "未知")
        r = format_rate(it.get("fansIncrRate", 0))
        inc = format_number(it.get("addFollowerCount", 0))
        rate_val = _safe_float(it.get("fansIncrRate", 0))
        fc = _safe_float(it.get("followerCount", 0))
        if rate_val >= 0.3:
            driver = "爆款内容/热点事件驱动"
        elif rate_val >= 0.1:
            driver = "内容策略优化/话题借势"
        elif fc >= 5000000:
            driver = "粉丝基数驱动/品牌营销"
        else:
            driver = "稳步增长"
        lines.append(f"- {name}：涨粉率{r}，粉丝增量{inc}，增长驱动力：{driver}")
    lines.append("")

    # 潜力账号：粉丝基数<100万 且 涨粉率>10% 且 粉丝增量>3万
    potentials = [
        it for it in items
        if _safe_float(it.get("followerCount", 0)) < 1000000
        and _safe_float(it.get("fansIncrRate", 0)) > 0.1
        and _safe_float(it.get("addFollowerCount", 0)) > 30000
    ]
    # 按涨粉率降序
    potentials.sort(key=lambda x: _safe_float(x.get("fansIncrRate", 0)), reverse=True)

    lines.append("**🚀 潜力账号（适合合作/投放）**")
    if potentials:
        for it in potentials[:5]:  # 最多展示5个
            name = it.get("nickname", "未知")
            fc = format_number(it.get("followerCount", 0))
            r = format_rate(it.get("fansIncrRate", 0))
            inc = format_number(it.get("addFollowerCount", 0))
            lines.append(f"- {name}：总粉丝{fc}，涨粉率{r}，粉丝增量{inc}，推荐理由：高增长势头+中等粉丝基数性价比高")
    else:
        lines.append("- 本期无符合筛选条件的潜力账号")
    lines.append("")

    # 风险信号：涨粉率<1% 且 排名TOP30以后
    risks = [
        it for it in items
        if _safe_float(it.get("fansIncrRate", 0)) < 0.01
        and _safe_float(it.get("ranking", 0)) > 30
    ]

    lines.append("**⚠️ 风险信号（需关注异常）**")
    if risks:
        for it in risks[:3]:  # 最多展示3个
            name = it.get("nickname", "未知")
            r = format_rate(it.get("fansIncrRate", 0))
            fc = _safe_float(it.get("followerCount", 0))
            if fc >= 5000000:
                reason = "粉丝基数过大导致增长放缓"
            else:
                reason = "可能存在内容断更/舆情等问题"
            lines.append(f"- {name}：涨粉率{r}，{reason}")
    else:
        lines.append("- 本期无显著风险信号")
    lines.append("")

    return "\n".join(lines)


def get_update_time_label(rank_type, rank_date):
    """获取榜单更新时间标签"""
    if rank_type == "day":
        d = datetime.strptime(rank_date, "%Y-%m-%d")
        update_time = d + timedelta(days=1)
        return f"{update_time.strftime('%Y-%m-%d')} 18:00"
    elif rank_type == "week":
        d = datetime.strptime(rank_date, "%Y-%m-%d")
        next_monday = d + timedelta(weeks=1)
        return f"{next_monday.strftime('%Y-%m-%d')} 18:00"
    elif rank_type == "month":
        d = datetime.strptime(rank_date, "%Y-%m-%d")
        if d.month == 12:
            update_day = datetime(d.year + 1, 1, MONTH_UPDATE_DAY)
        else:
            update_day = datetime(d.year, d.month + 1, MONTH_UPDATE_DAY)
        return f"{update_day.strftime('%Y-%m-%d')} 18:00"
    return rank_date


# ===== 主函数 =====
def main():
    parser = argparse.ArgumentParser(description="抖音涨粉账号推荐数据获取工具")
    parser.add_argument("--rank_type", choices=["day", "week", "month"], default="day",
                        help="榜单类型: day=日榜, week=周榜, month=月榜 (默认: day)")
    parser.add_argument("--rank_date", type=str, default=None,
                        help="查询日期(yyyy-MM-dd)，不指定则自动计算")
    parser.add_argument("--category", type=str, default=None,
                        help="分类名称，如'数码科技'")
    parser.add_argument("--keyword", type=str, default=None,
                        help="分类关键词，模糊匹配分类名")
    parser.add_argument("--top_n", type=int, default=50,
                        help="显示前N条 (默认: 50)")
    parser.add_argument("--start", type=int, default=1,
                        help="起始排名 (默认: 1，用于查看更多时从TOP21开始)")
    parser.add_argument("--list_categories", action="store_true",
                        help="列出所有可用分类")
    parser.add_argument("--raw", action="store_true",
                        help="输出原始JSON数据")
    parser.add_argument("--from_cache", action="store_true",
                        help="从本地缓存文件读取数据（查看更多时使用，避免重复调用API）")

    args = parser.parse_args()

    # 列出分类
    if args.list_categories:
        print("可用分类列表：")
        for i, cat in enumerate(CATEGORIES, 1):
            print(f"  {i}. {cat}")
        return

    # 从缓存读取数据（查看更多时使用）
    if args.from_cache:
        if not os.path.isfile(DATA_CACHE_FILE):
            print(f"错误：缓存文件不存在，请先查询一次榜单数据")
            return
        try:
            with open(DATA_CACHE_FILE, "r", encoding="utf-8") as f:
                cached = json.load(f)
        except Exception as e:
            print(f"错误：读取缓存文件失败: {e}")
            return

        data_list = cached.get("account_list", [])
        if not data_list:
            print("错误：缓存数据为空")
            return

        rank_type = cached.get("rank_type", args.rank_type)
        rank_date = cached.get("rank_date", "")
        category = cached.get("category", "全部")
        rank_label = RANK_TYPE_MAP.get(rank_type, "日榜")
        reminder = cached.get("reminder", "")

        print(f"从缓存读取数据（{rank_label} - {category} - {rank_date}）")
        print("-" * 60)

        update_time = cached.get("update_time", "")
        time_range = cached.get("time_range", "")
        data_description = cached.get("data_description", "")

        output = {
            "status": "success",
            "rank_type": rank_type,
            "rank_label": rank_label,
            "rank_date": rank_date,
            "category": category,
            "data_description": data_description,
            "total_count": len(data_list),
            "top_n": min(args.top_n, len(data_list)),
            "update_time": update_time,
            "time_range": time_range,
            "reminder": reminder,
            "ranking_table": format_ranking_table(data_list, args.top_n, args.start),
            "analysis": format_analysis(data_list, rank_type),
            "account_list": data_list,
        }

        if args.raw:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print(json.dumps(output, ensure_ascii=False))
        return

    # 确定分类
    category = "全部"
    if args.category:
        category = args.category
    elif args.keyword:
        matched = match_category(args.keyword)
        if matched is None:
            print(f"未找到匹配'{args.keyword}'的分类，可用分类：{', '.join(CATEGORIES)}")
            return
        elif isinstance(matched, list):
            print(f"关键词'{args.keyword}'匹配到多个分类：{', '.join(matched)}，请指定更精确的分类名")
            return
        else:
            category = matched
            print(f"根据关键词【{args.keyword}】匹配到分类：【{category}】")

    # 确定查询日期
    rank_label = RANK_TYPE_MAP.get(args.rank_type, "日榜")
    print(f"正在获取抖音涨粉账号推荐{rank_label}数据...")
    print(f"当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    reminder = ""

    if args.rank_date:
        validation = validate_and_adjust_date(args.rank_type, args.rank_date)
        rank_date = validation["adjusted_date"]
        if validation["is_adjusted"]:
            reminder = validation["reminder"]
            print(f"用户指定日期: {args.rank_date} -> 调整为: {rank_date}")
            print(f"提醒: {reminder}")
    else:
        rank_date = get_latest_query_date(args.rank_type)
        today_reminder = get_today_query_reminder(args.rank_type)
        if today_reminder:
            reminder = today_reminder
            print(f"提醒: {reminder}")

    print(f"榜单类型: {rank_label}")
    print(f"查询日期: {rank_date}")
    print(f"分类: {category}")
    print("-" * 60)

    try:
        data_list = fetch_ranking_data(
            rank_type=args.rank_type,
            rank_date=rank_date,
            category=category,
        )
    except Exception as e:
        print(f"错误: {e}")
        return

    if not data_list:
        print("未获取到数据")
        return

    # 格式化输出
    update_time = get_update_time_label(args.rank_type, rank_date)
    time_range = get_data_time_range(args.rank_type, rank_date)
    fetch_date = rank_date
    data_description = BILL_NOTE_TEMPLATES.get(args.rank_type, BILL_NOTE_TEMPLATES["day"]).format(fetch_date=fetch_date)

    output = {
        "status": "success",
        "rank_type": args.rank_type,
        "rank_label": rank_label,
        "rank_date": rank_date,
        "category": category,
        "data_description": data_description,
        "total_count": len(data_list),
        "top_n": min(args.top_n, len(data_list)),
        "update_time": update_time,
        "time_range": time_range,
        "reminder": reminder,
        "ranking_table": format_ranking_table(data_list, args.top_n, args.start),
        "analysis": format_analysis(data_list, args.rank_type),
        "account_list": data_list,
    }

    # 自动写入本地缓存文件，供gen_gzh_html.py直接读取
    try:
        os.makedirs(os.path.dirname(DATA_CACHE_FILE), exist_ok=True)
        with open(DATA_CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

    # 原始输出
    if args.raw:
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return

    print(json.dumps(output, ensure_ascii=False))


if __name__ == "__main__":
    main()
