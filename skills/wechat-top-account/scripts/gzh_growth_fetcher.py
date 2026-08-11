#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""公众号热门账号推荐榜数据获取脚本

通过HTTP请求获取公众号热门账号推荐榜单数据，支持日榜/周榜/月榜，22个分类查询。

用法:
    python scripts/gzh_growth_fetcher.py --rank_type day --keyword 科技 --top_n 50
    python scripts/gzh_growth_fetcher.py --rank_type week --category 科技数码
    python scripts/gzh_growth_fetcher.py --rank_type month --category 总排名 --top_n 50
    python scripts/gzh_growth_fetcher.py --list_categories
"""

import argparse
import json
import os
import sys
import pathlib
from datetime import datetime, timedelta
from urllib.parse import quote
import requests


# ===== 常量 =====
API_URL = "https://redfox.hk/story/api/cozeSkill/getGzhCozeSkillDataIndex"
SOURCE = "公众号综合实力账号榜-GitHub"

CATEGORIES = [
    "乐活生活", "人文资讯", "企业品牌", "体育娱乐", "健康养生",
    "创投商业", "学术研究", "情感心理", "房产楼市", "搞笑幽默",
    "教育考试", "文摘精选", "旅游出行", "时尚潮流", "民生资讯",
    "汽车交通", "知识百科", "科技数码", "美容美体", "美食餐饮",
    "职场发展", "财富理财", "总排名"
]

RANK_TYPE_MAP = {
    "day": "日榜",
    "week": "周榜",
    "month": "月榜"
}

# 榜单更新时间规则
# 日榜：每日17:30更新昨日数据
# 周榜：每周一17:30更新上周数据
# 月榜：每月3号23:00更新上月数据

DAY_UPDATE_HOUR = 17
DAY_UPDATE_MINUTE = 30
MONTH_UPDATE_DAY = 3
MONTH_UPDATE_HOUR = 23
MONTH_UPDATE_MINUTE = 0

DATA_DESCRIPTION_TEMPLATE = "公众号综合实力{rank_label}，基于阅读、点赞、转发、在看等多维数据综合排名\n数据统计时间周期：{time_range}"

def get_data_time_range(rank_type, rank_date):
    """根据榜单类型和查询日期生成数据统计时间周期描述"""
    from datetime import datetime, timedelta
    import calendar
    date_obj = datetime.strptime(rank_date, "%Y-%m-%d")
    if rank_type == "day":
        return f"{rank_date}"
    elif rank_type == "week":
        end_date = date_obj + timedelta(days=6)
        return f"{date_obj.strftime('%Y-%m-%d')}至{end_date.strftime('%Y-%m-%d')}"
    elif rank_type == "month":
        last_day = calendar.monthrange(date_obj.year, date_obj.month)[1]
        return f"{date_obj.strftime('%Y-%m')}-01至{date_obj.strftime('%Y-%m')}-{last_day:02d}"
    return rank_date

# 日期查询范围限制
DAY_MAX_DAYS_BACK = 7
WEEK_MAX_WEEKS_BACK = 3
MONTH_MAX_MONTHS_BACK = 3


# ===== 日期计算 =====
def _is_after_day_update(now=None):
    """判断当前时间是否已过日榜/周榜更新时间(17:30)"""
    if now is None:
        now = datetime.now()
    cutoff = now.replace(hour=DAY_UPDATE_HOUR, minute=DAY_UPDATE_MINUTE, second=0, microsecond=0)
    return now >= cutoff


def _is_after_month_update(now=None):
    """判断当前时间是否已过月榜更新时间(当月3号23:00)"""
    if now is None:
        now = datetime.now()
    # 本月3号23:00
    try:
        cutoff = now.replace(day=MONTH_UPDATE_DAY, hour=MONTH_UPDATE_HOUR,
                             minute=MONTH_UPDATE_MINUTE, second=0, microsecond=0)
    except ValueError:
        # 2月没有30号等情况不会出现(3号一定存在)
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
        # 日榜: 每日17:30更新昨日数据
        # 17:30后 → 查昨天; 17:30前 → 查前天
        if _is_after_day_update(now):
            target = now - timedelta(days=1)
        else:
            target = now - timedelta(days=2)
        return target.strftime("%Y-%m-%d")

    elif rank_type == "week":
        # 周榜: 每周一17:30更新上周数据
        # 周一17:30后 → 查本周一; 周一17:30前 → 查上周一
        weekday = now.weekday()  # 0=Monday
        this_monday = now - timedelta(days=weekday)
        if _is_after_day_update(now):
            # 17:30后 → 本周一
            return this_monday.strftime("%Y-%m-%d")
        else:
            # 17:30前 → 上周一
            last_monday = this_monday - timedelta(weeks=1)
            return last_monday.strftime("%Y-%m-%d")

    elif rank_type == "month":
        # 月榜: 每月3号23:00更新上月数据
        # rankDate传上月1号 = 上月数据
        # 3号23:00后 → 上月1号(=上月数据已更新); 3号23:00前 → 上上月1号(=上上月数据)
        if _is_after_month_update(now):
            # 已过3号23:00 → 上月1号
            if now.month == 1:
                return datetime(now.year - 1, 12, 1).strftime("%Y-%m-%d")
            else:
                return datetime(now.year, now.month - 1, 1).strftime("%Y-%m-%d")
        else:
            # 未过3号23:00 → 上上月1号
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
        # 最近7天
        earliest = now - timedelta(days=DAY_MAX_DAYS_BACK)
        return earliest.strftime("%Y-%m-%d")

    elif rank_type == "week":
        # 最近3周
        weekday = now.weekday()
        this_monday = now - timedelta(days=weekday)
        earliest_monday = this_monday - timedelta(weeks=WEEK_MAX_WEEKS_BACK)
        return earliest_monday.strftime("%Y-%m-%d")

    elif rank_type == "month":
        # 最近3个月
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
        dict: {
            "original_date": 原始日期,
            "adjusted_date": 调整后的日期(可能不变),
            "is_adjusted": 是否被调整,
            "reminder": 提醒消息(无调整时为空)
        }
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

    # 超出范围，自动调整到最近可查询日期
    if user_date > latest:
        adjusted = latest.strftime("%Y-%m-%d")
    else:
        adjusted = earliest.strftime("%Y-%m-%d")

    reminder = (
        '非常抱歉🙏，目前公众号榜单最多支持回溯「近7天的日榜/近3周的周榜/近3个月的月榜」，'
        '我将为您查询最接近您需求时间的{}数据⭐~'
    ).format(RANK_TYPE_MAP.get(rank_type, "日榜"))

    return {
        "original_date": user_date_str,
        "adjusted_date": adjusted,
        "is_adjusted": True,
        "reminder": reminder
    }


def get_today_query_reminder(rank_type="day"):
    """当用户查询今日日榜但数据未更新时，生成提醒

    Args:
        rank_type: day/week/month

    Returns:
        str: 提醒消息，不需要提醒时返回空字符串
    """
    if rank_type == "day" and not _is_after_day_update():
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        return (
            '日榜数据暂未更新，将为您查询最接近您需求日期的榜单数据⭐~\n'
            f'推荐查询昨日更新的最新榜单（{yesterday}日榜）'
        )
    return ""


# ===== 认证 =====
def _get_redfox_api_key():
    """三级认证回退获取 红狐Hub API Key

    优先级：
    1. 环境变量 REDFOX_API_KEY
    2. Shell 配置文件（.zshrc / .bashrc / PowerShell Profile）
    3. 返回 None，由上层提示用户配置

    Returns:
        str or None: API Key
    """
    # 第一级：环境变量
    api_key = os.getenv("REDFOX_API_KEY")
    if api_key and api_key.startswith("ak_"):
        return api_key

    # 第二级：Shell 配置文件
    home = pathlib.Path.home()
    config_files = []

    if sys.platform == "win32":
        # PowerShell Profile
        ps_dir = home / "Documents" / "WindowsPowerShell"
        if ps_dir.exists():
            for f in ps_dir.glob("Microsoft.PowerShell_profile.ps1"):
                config_files.append(f)
        ps7_dir = home / "Documents" / "PowerShell"
        if ps7_dir.exists():
            for f in ps7_dir.glob("Microsoft.PowerShell_profile.ps1"):
                config_files.append(f)
        # Git Bash / MSYS2
        for name in [".bashrc", ".bash_profile", ".profile"]:
            p = home / name
            if p.exists():
                config_files.append(p)
    else:
        for name in [".zshrc", ".bashrc", ".bash_profile", ".profile"]:
            p = home / name
            if p.exists():
                config_files.append(p)

    for config in config_files:
        try:
            content = config.read_text(encoding="utf-8", errors="ignore")
            for line in content.splitlines():
                line = line.strip()
                # 匹配 export REDFOX_API_KEY=xxx 或 set REDFOX_API_KEY=xxx
                if line.startswith("export REDFOX_API_KEY=") or line.startswith("set REDFOX_API_KEY="):
                    parts = line.split("=", 1)
                    if len(parts) == 2:
                        key = parts[1].strip().strip('"').strip("'")
                        if key and key.startswith("ak_"):
                            return key
                # 匹配 PowerShell: $env:REDFOX_API_KEY = "xxx"
                if "$env:REDFOX_API_KEY" in line:
                    parts = line.split("=", 1)
                    if len(parts) == 2:
                        key = parts[1].strip().strip('"').strip("'")
                        if key and key.startswith("ak_"):
                            return key
        except Exception:
            continue

    return None


def _get_api_headers():
    """获取API请求头，含X-API-KEY凭证

    三级回退：环境变量 → Shell配置 → 报错提示
    """
    api_key = _get_redfox_api_key()
    if not api_key:
        raise ValueError(
            "未检测到 红狐Hub API Key。请按以下步骤配置：\n"
            "1. 访问 https://redfox.hk/?source=github 了解服务详情\n"
            "2. 前往 https://redfox.hk/login?source=github 注册账号（新用户获赠免费积分）\n"
            "3. 注册登录后在个人中心获取 API Key（格式 ak_xxxxxxxx）\n"
            "4. 设置环境变量：\n"
            "   macOS/Linux: export REDFOX_API_KEY=<你的apikey>\n"
            "   Windows PowerShell: $env:REDFOX_API_KEY = \"<你的apikey>\"\n"
            "   或告知我帮你自动配置到 Shell 配置文件中"
        )
    return {
        "Content-Type": "application/json",
        "X-API-KEY": api_key,
    }


# ===== API调用 =====
def fetch_ranking_data(rank_type="day", rank_date=None, category="人文资讯"):
    """获取公众号热门账号推荐榜数据

    Args:
        rank_type: day/week/month
        rank_date: 查询日期 (yyyy-MM-dd)，None则自动计算
        category: 分类名称

    Returns:
        dict: API返回的完整数据
    """
    if rank_date is None:
        rank_date = get_latest_query_date(rank_type)

    params = {
        "rankType": rank_type,
        "rankDate": rank_date,
        "category": category,
        "source": SOURCE,
    }

    headers = _get_api_headers()

    try:
        response = requests.get(API_URL, params=params, headers=headers, timeout=30)
        if response.status_code >= 400:
            raise ValueError(f"HTTP请求失败: {response.status_code}, {response.text}")
        result = response.json()
    except requests.exceptions.RequestException as e:
        raise ValueError(f"请求失败: {str(e)}")

    if result.get("code") != 2000:
        raise ValueError(f"API返回错误: code={result.get('code')}, msg={result.get('msg', '未知错误')}")

    return result


# ===== 分类匹配 =====
CATEGORY_KEYWORDS = {
    "总排名": ["总排名", "综合", "全部", "热门", "推荐", "随便", "总榜", "整体"],
    "乐活生活": ["乐活", "生活", "日常", "生活方式", "生活日常", "好物推荐"],
    "人文资讯": ["人文", "资讯", "文化", "历史", "哲学", "人文社科"],
    "企业品牌": ["企业", "品牌", "公司", "商业品牌", "品牌营销"],
    "体育娱乐": ["体育", "娱乐", "运动", "健身", "篮球", "足球", "综艺", "明星"],
    "健康养生": ["健康", "养生", "保健", "中医", "调理", "减肥", "瘦身"],
    "创投商业": ["创投", "商业", "投资", "创业", "融资", "商业模式"],
    "学术研究": ["学术", "研究", "论文", "科研", "学报"],
    "情感心理": ["情感", "心理", "恋爱", "婚姻", "情绪", "心理咨询"],
    "房产楼市": ["房产", "楼市", "买房", "房价", "地产", "租房", "装修"],
    "搞笑幽默": ["搞笑", "幽默", "段子", "吐槽", "沙雕", "表情包"],
    "教育考试": ["教育", "考试", "培训", "考研", "考公", "留学", "英语", "学习"],
    "文摘精选": ["文摘", "精选", "美文", "散文", "故事", "文章精选"],
    "旅游出行": ["旅游", "出行", "旅行", "攻略", "景点", "酒店", "度假"],
    "时尚潮流": ["时尚", "潮流", "穿搭", "服饰", "OOTD", "ootd", "搭配"],
    "民生资讯": ["民生", "社会", "热点", "时事", "政策", "民生新闻"],
    "汽车交通": ["汽车", "交通", "车", "新能源", "电动车", "买车"],
    "知识百科": ["知识", "百科", "科普", "常识", "冷知识"],
    "科技数码": ["科技", "数码", "手机", "电脑", "智能", "AI", "互联网", "软件", "硬件"],
    "美容美体": ["美容", "美体", "护肤", "化妆", "美妆", "彩妆"],
    "美食餐饮": ["美食", "餐饮", "做饭", "烹饪", "餐厅", "探店", "食谱"],
    "职场发展": ["职场", "工作", "求职", "面试", "跳槽", "升职", "加薪", "简历"],
    "财富理财": ["财富", "理财", "财经", "基金", "股票", "保险", "财务", "赚钱"],
}


def match_category(keyword):
    """根据关键词匹配分类

    Args:
        keyword: 搜索关键词

    Returns:
        str or None: 匹配到的分类名，多个匹配时返回列表
    """
    # 精确匹配分类名
    if keyword in CATEGORIES:
        return keyword
    # 子串匹配分类名
    matches = [c for c in CATEGORIES if keyword in c]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        return matches
    # 关键词映射匹配
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


def get_comprehensive_score(item):
    """获取综合评分（满分100），直接采用接口返回的comprehensiveScore字段

    Args:
        item: 单条数据

    Returns:
        float: 综合评分(0-100)
    """
    try:
        return round(float(item.get("comprehensiveScore", 0)), 1)
    except (ValueError, TypeError):
        return 0.0


def format_ranking_table(data_list, top_n=50, start=1):
    """格式化榜单为Markdown表格（严格遵循core_workflow.md标准模板）

    表格字段: 排名 | 账号名称 | 综合评分(满分100) | 发布数/文章数 | 总阅读数 | 头条阅读数 | 最高阅读数 | 总点赞 | 总在看 | 总转发

    Args:
        data_list: API返回的data数组
        top_n: 显示前N条
        start: 起始排名(1-based)，用于"查看更多"时从TOP21开始

    Returns:
        str: Markdown表格字符串
    """
    # start为1时从第1条开始，start为21时从第21条开始
    items = data_list[start-1:start-1+top_n]

    header = "| 排名 | 账号名称 | 综合评分(满分100) | 发布数/文章数 | 总阅读数 | 头条阅读数 | 最高阅读数 | 总点赞 | 总在看 | 总转发 |"
    separator = "|:---:|:---|---:|:---:|---:|---:|---:|---:|:---:|---:|"

    rows = []
    for idx, item in enumerate(items):
        # 使用实际索引位置判断奖牌，避免API返回的rankPosition重复
        display_rank = start + idx
        name = item.get("accountName", "-")
        account_id = item.get("accountId", "")
        name_link = f"[{name}](https://open.weixin.qq.com/qr/code?username={quote(account_id)})"
        score = get_comprehensive_score(item)
        publish = item.get("publishCount", "-")
        total_read = format_number(item.get("totalReadCount", 0))
        headline_read = format_number(item.get("headlineReadCount", 0))
        max_read = format_number(item.get("maxReadCount", 0))
        like_count = format_number(item.get("totalLikeCount", 0))
        in_see_count = format_number(item.get("totalInSeeCount", 0))
        forward_count = format_number(item.get("totalForwardCount", 0))

        rank_medals = {1: "🥇", 2: "🥈", 3: "🥉"}
        if display_rank in rank_medals:
            # TOP3: 账号名称加粗，综合评分/总阅读/头条阅读/最高阅读/总点赞/总转发加粗
            row = f"| {rank_medals[display_rank]} | **{name_link}** | **{score}** | {publish} | **{total_read}** | **{headline_read}** | **{max_read}** | **{like_count}** | **{in_see_count}** | **{forward_count}** |"
        else:
            # 非TOP3: 账号名称不加粗，但综合评分/总阅读/头条阅读/最高阅读/总点赞/总转发仍需加粗
            row = f"| {display_rank} | {name_link} | **{score}** | {publish} | **{total_read}** | **{headline_read}** | **{max_read}** | **{like_count}** | **{in_see_count}** | **{forward_count}** |"
        rows.append(row)

    return "\n".join([header, separator] + rows)


# 功能询问文案模板（一字不改，遵循core_workflow.md）
FEATURE_PROMPT = """技能还支持以下功能：

1️⃣ 支持对以上数据进行分析。其中包含**内容生态变化分析**、**热点影响力量化**、**蓝海赛道挖掘**三种分析角度，方便您了解公众号阅读数据或获取运营参考时使用。

2️⃣ 可生成公众号风格的html文件包。支持**导出图片**、**导出PDF**，方便阅读、保存和分享。

3️⃣ 支持订阅每日/周/月的公众号账号最新排名，订阅后将定时推送给您（日榜将在每日17点30更新/周榜将在每周一17:30准时更新/月榜将在每月3号23:00准时推送）。直接回复"订阅日/周/月榜"即可订阅相关榜单，或者"全部订阅"将会为您推送全部类型的榜单。

回复数字即可~"""


def format_full_output(rank_label, category, update_time, data_description,
                       time_range, reminder, data_list, top_n=50, start=1):
    """格式化完整的榜单输出（严格遵循core_workflow.md标准模板）

    输出顺序：标题 → 数据说明 → reminder → 表格 → 功能询问文案

    Args:
        rank_label: 榜单标签（日榜/周榜/月榜）
        category: 分类名
        update_time: 更新时间
        data_description: 数据说明文本
        time_range: 数据统计时间周期
        reminder: 日期提醒（可为空）
        data_list: API返回的data数组
        top_n: 显示前N条
        start: 起始排名

    Returns:
        str: 完整的Markdown输出
    """
    parts = []

    # 标题（二级标题）
    parts.append(f"## 公众号热门账号推荐榜{rank_label} - {category} （更新时间：{update_time}）")
    parts.append("")

    # 数据说明（斜体，在标题后、表格前）
    parts.append(f"*公众号综合实力{rank_label}，基于阅读、点赞、转发、在看等多维数据综合排名*")
    parts.append(f"*数据统计时间周期：{time_range}*")
    parts.append("")

    # reminder（如有）
    if reminder:
        parts.append(reminder)
        parts.append("")

    # 榜单表格
    parts.append(format_ranking_table(data_list, top_n, start))
    parts.append("")

    # 功能询问文案（一字不改）
    parts.append(FEATURE_PROMPT)
    parts.append("")
    parts.append("另外红狐配套全量数据库可提供完整详实数据，如需了解采购方案，可发送邮件至 redfoxdata@proton.me 对接咨洵")

    return "\n".join(parts)


def format_analysis(data_list, rank_type="day", top_n=3):
    """格式化综合实力分析

    Args:
        data_list: API返回的data数组
        rank_type: day/week/month
        top_n: 分析前N个公众号

    Returns:
        str: Markdown分析文本
    """
    rank_label = RANK_TYPE_MAP.get(rank_type, "日榜")
    items = data_list[:top_n]

    if not items:
        return "暂无数据可供分析。"

    lines = [f"**{rank_label}综合实力分析**\n"]

    for i, item in enumerate(items):
        name = item.get("accountName", "未知")
        score = get_comprehensive_score(item)
        total_read = item.get("totalReadCount", 0)
        headline_read = item.get("headlineReadCount", 0)
        max_read = item.get("maxReadCount", 0)
        like_count = item.get("totalLikeCount", 0)
        forward_count = item.get("totalForwardCount", 0)
        in_see_count = item.get("totalInSeeCount", 0)
        publish = item.get("publishCount", "-")

        lines.append(f"**第{i+1}名：{name}（综合评分：{score}）**")
        lines.append(f"- 风格：总阅读{format_number(total_read)}，头条阅读{format_number(headline_read)}，最高阅读{format_number(max_read)}")
        lines.append(f"- 特征：发布{publish}，获赞{format_number(like_count)}次，在看{format_number(in_see_count)}次，转发{format_number(forward_count)}次")

        # 分析建议
        try:
            total_int = int(total_read) if total_read else 0
        except (ValueError, TypeError):
            total_int = 0
        try:
            like_int = int(like_count) if like_count else 0
        except (ValueError, TypeError):
            like_int = 0

        interaction_rate = f"{like_int / total_int * 100:.2f}%" if total_int and total_int > 0 else "N/A"
        lines.append(f"- 建议：互动率{interaction_rate}，{'内容传播力强，可作为竞品研究标杆' if score >= 80 else '内容稳定产出，关注互动提升空间'}")
        lines.append("")

    return "\n".join(lines)


def get_update_time_label(rank_type, rank_date):
    """获取榜单更新时间标签

    Args:
        rank_type: day/week/month
        rank_date: 查询日期

    Returns:
        str: 更新时间标签
    """
    if rank_type == "day":
        # 日榜：查询日期的次日17:30
        d = datetime.strptime(rank_date, "%Y-%m-%d")
        update_time = d + timedelta(days=1)
        return f"{update_time.strftime('%Y-%m-%d')} 17:30"
    elif rank_type == "week":
        # 周榜：查询周一的下一个周一17:30
        d = datetime.strptime(rank_date, "%Y-%m-%d")
        next_monday = d + timedelta(weeks=1)
        return f"{next_monday.strftime('%Y-%m-%d')} 17:30"
    elif rank_type == "month":
        # 月榜：查询月份的次月3号23:00
        d = datetime.strptime(rank_date, "%Y-%m-%d")
        if d.month == 12:
            update_day = datetime(d.year + 1, 1, MONTH_UPDATE_DAY)
        else:
            update_day = datetime(d.year, d.month + 1, MONTH_UPDATE_DAY)
        return f"{update_day.strftime('%Y-%m-%d')} 23:00"
    return rank_date


# ===== 主函数 =====
def main():
    parser = argparse.ArgumentParser(description="公众号热门账号推荐榜数据获取工具")
    parser.add_argument("--rank_type", choices=["day", "week", "month"], default="day",
                        help="榜单类型: day=日榜, week=周榜, month=月榜 (默认: day)")
    parser.add_argument("--rank_date", type=str, default=None,
                        help="查询日期(yyyy-MM-dd)，不指定则自动计算")
    parser.add_argument("--category", type=str, default=None,
                        help="分类名称，如'科技数码'")
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
    parser.add_argument("--input_json_file", type=str, default=None,
                        help="预取数据JSON文件路径（来自本脚本之前的输出），指定后不再调用API")

    args = parser.parse_args()

    # 使用预取数据模式
    if args.input_json_file:
        if not os.path.isfile(args.input_json_file):
            print(f"错误: 文件不存在: {args.input_json_file}", file=sys.stderr)
            sys.exit(1)
        try:
            with open(args.input_json_file, 'r', encoding='utf-8') as f:
                fetched = json.load(f)
        except Exception as e:
            print(f"错误: 读取文件失败: {e}", file=sys.stderr)
            sys.exit(1)

        raw_data = fetched.get("raw_data", [])
        if not raw_data:
            print("错误: 输入文件中无 raw_data 数据", file=sys.stderr)
            sys.exit(1)

        rank_type = fetched.get("rank_type", "day")
        rank_date = fetched.get("rank_date", "")
        category = fetched.get("category", "人文资讯")
        rank_label = fetched.get("rank_label", RANK_TYPE_MAP.get(rank_type, "日榜"))
        update_time = fetched.get("update_time", "")
        reminder = fetched.get("reminder", "")

        print(f"使用预取数据重新处理（不调用API）...", file=sys.stderr)
        print(f"榜单类型: {rank_label}", file=sys.stderr)
        print(f"查询日期: {rank_date}", file=sys.stderr)
        print(f"分类: {category}", file=sys.stderr)

        # 从预取数据重新格式化
        data_list = raw_data
        top_n = min(args.top_n, len(data_list))

        time_range = get_data_time_range(rank_type, rank_date)

        output = {
            "status": "success",
            "rank_type": rank_type,
            "rank_label": rank_label,
            "rank_date": rank_date,
            "category": category,
            "data_description": fetched.get("data_description", ""),
            "total_count": fetched.get("total_count", len(data_list)),
            "top_n": top_n,
            "update_time": update_time,
            "reminder": reminder,
            "ranking_table": format_ranking_table(data_list, args.top_n, args.start),
            "analysis": format_analysis(data_list, rank_type),
            "raw_data": data_list,
            "formatted_markdown": format_full_output(
                rank_label, category, update_time,
                fetched.get("data_description", ""), time_range,
                reminder, data_list, args.top_n, args.start
            ),
        }

        # 输出JSON到stdout，确保Windows下GBK终端也能正确输出
        json_str = json.dumps(output, ensure_ascii=False)
        try:
            sys.stdout.write(json_str + "\n")
            sys.stdout.flush()
        except UnicodeEncodeError:
            # Windows GBK终端无法编码emoji等字符时，回退到UTF-8编码
            sys.stdout.buffer.write(json_str.encode('utf-8', errors='replace') + b"\n")
            sys.stdout.buffer.flush()
        return

    # 列出分类
    if args.list_categories:
        print("可用分类列表：", file=sys.stderr)
        for i, cat in enumerate(CATEGORIES, 1):
            print(f"  {i}. {cat}", file=sys.stderr)
        return

    # 确定分类
    category = "人文资讯"
    if args.category:
        category = args.category
    elif args.keyword:
        matched = match_category(args.keyword)
        if matched is None:
            print(f"未找到匹配'{args.keyword}'的分类，可用分类：{', '.join(CATEGORIES)}", file=sys.stderr)
            return
        elif isinstance(matched, list):
            print(f"关键词'{args.keyword}'匹配到多个分类：{', '.join(matched)}，请指定更精确的分类名", file=sys.stderr)
            return
        else:
            category = matched
            print(f"根据关键词【{args.keyword}】匹配到分类：【{category}】", file=sys.stderr)

    # 确定查询日期
    rank_label = RANK_TYPE_MAP.get(args.rank_type, "日榜")
    print(f"正在获取公众号综合实力{rank_label}数据...", file=sys.stderr)
    print(f"当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", file=sys.stderr)

    reminder = ""

    if args.rank_date:
        # 用户指定了日期，验证范围
        validation = validate_and_adjust_date(args.rank_type, args.rank_date)
        rank_date = validation["adjusted_date"]
        if validation["is_adjusted"]:
            reminder = validation["reminder"]
            print(f"用户指定日期: {args.rank_date} → 调整为: {rank_date}", file=sys.stderr)
            print(f"提醒: {reminder}", file=sys.stderr)
    else:
        # 自动计算最新可查询日期
        rank_date = get_latest_query_date(args.rank_type)
        # 检查今日日榜是否已更新
        today_reminder = get_today_query_reminder(args.rank_type)
        if today_reminder:
            reminder = today_reminder
            print(f"提醒: {reminder}", file=sys.stderr)

    print(f"榜单类型: {rank_label}", file=sys.stderr)
    print(f"查询日期: {rank_date}", file=sys.stderr)
    print(f"分类: {category}", file=sys.stderr)
    print("-" * 60, file=sys.stderr)

    try:
        result = fetch_ranking_data(
            rank_type=args.rank_type,
            rank_date=rank_date,
            category=category,
        )
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        return

    data_list = result.get("data", [])
    if not data_list:
        print("未获取到数据", file=sys.stderr)
        return

    # 原始输出
    if args.raw:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    # 格式化输出
    # 综合评分直接采用接口返回的comprehensiveScore字段
    scored_data = []
    for item in data_list[:args.top_n]:
        item_copy = dict(item)
        item_copy["compositeScore"] = get_comprehensive_score(item)
        scored_data.append(item_copy)

    update_time = get_update_time_label(args.rank_type, rank_date)
    time_range = get_data_time_range(args.rank_type, rank_date)

    output = {
        "status": "success",
        "rank_type": args.rank_type,
        "rank_label": rank_label,
        "rank_date": rank_date,
        "category": category,
        "data_description": DATA_DESCRIPTION_TEMPLATE.format(rank_label=rank_label, time_range=time_range),
        "total_count": len(data_list),
        "top_n": min(args.top_n, len(data_list)),
        "update_time": update_time,
        "reminder": reminder,
        "ranking_table": format_ranking_table(data_list, args.top_n, args.start),
        "analysis": format_analysis(data_list, args.rank_type),
        "raw_data": scored_data,
        "formatted_markdown": format_full_output(
            rank_label, category, update_time,
            DATA_DESCRIPTION_TEMPLATE.format(rank_label=rank_label, time_range=time_range),
            time_range, reminder, data_list, args.top_n, args.start
        ),
    }

    # 输出JSON到stdout，确保Windows下GBK终端也能正确输出
    json_str = json.dumps(output, ensure_ascii=False)
    try:
        sys.stdout.write(json_str + "\n")
        sys.stdout.flush()
    except UnicodeEncodeError:
        # Windows GBK终端无法编码emoji等字符时，回退到ASCII编码
        sys.stdout.buffer.write(json_str.encode('utf-8', errors='replace') + b"\n")
        sys.stdout.buffer.flush()


if __name__ == "__main__":
    main()
