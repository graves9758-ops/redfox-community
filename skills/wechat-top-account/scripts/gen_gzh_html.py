#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""公众号热门账号推荐HTML生成器

从API获取公众号热门账号推荐榜单数据，生成可独立打开的HTML页面。
用法：python gen_gzh_html.py [--rank_type day|week|month] [--rank_date YYYY-MM-DD] [--category 分类名] [--top N] [--output PATH]
输出：gzh_growth.html（与脚本同目录）

样式特性：
- 公众号风格（绿色主题 #07c160）
- 卡片式布局
- 公众号头像+名称+数据指标
- TOP3 奖牌徽章 + 左边框高亮
- 导出 PDF/图片功能
- 页面最大宽度 750px
"""

import json
import sys
import os
import pathlib
from datetime import datetime, timedelta
from urllib.parse import quote
import requests


# ===== 常量 =====
API_URL = "https://redfox.hk/story/api/cozeSkill/getGzhCozeSkillDataIndex"
SOURCE = "公众号综合实力账号榜-GitHub"

CATEGORIES = [
    "总排名", "乐活生活", "人文资讯", "企业品牌", "体育娱乐", "健康养生",
    "创投商业", "学术研究", "情感心理", "房产楼市", "搞笑幽默",
    "教育考试", "文摘精选", "旅游出行", "时尚潮流", "民生资讯",
    "汽车交通", "知识百科", "科技数码", "美容美体", "美食餐饮",
    "职场发展", "财富理财"
]

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
    "财富理财": ["财富", "理财", "财经", "投资", "基金", "股票", "保险", "财务", "赚钱"],
}

# 榜单更新时间规则
DAY_UPDATE_HOUR = 17
DAY_UPDATE_MINUTE = 30
MONTH_UPDATE_DAY = 3
MONTH_UPDATE_HOUR = 23
MONTH_UPDATE_MINUTE = 0

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
    try:
        cutoff = now.replace(day=MONTH_UPDATE_DAY, hour=MONTH_UPDATE_HOUR,
                             minute=MONTH_UPDATE_MINUTE, second=0, microsecond=0)
    except ValueError:
        cutoff = now.replace(day=MONTH_UPDATE_DAY, hour=MONTH_UPDATE_HOUR,
                             minute=MONTH_UPDATE_MINUTE, second=0, microsecond=0)
    return now >= cutoff


def get_latest_query_date(rank_type="day"):
    """获取最新可查询的榜单日期"""
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
        # 月榜: 每月3号23:00更新上月数据
        # rankDate传上月1号 = 上月数据
        # 3号23:00后 → 上月1号(=上月数据已更新); 3号23:00前 → 上上月1号
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
    """获取可查询的最早日期"""
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
    """验证用户指定日期是否在可查询范围"""
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

    rank_label = {"day": "日榜", "week": "周榜", "month": "月榜"}.get(rank_type, "日榜")
    reminder = (
        '非常抱歉🙏，目前公众号榜单最多支持回溯「近7天的日榜/近3周的周榜/近3个月的月榜」，'
        '我将为您查询最接近您需求时间的{}数据⭐~'
    ).format(rank_label)

    return {
        "original_date": user_date_str,
        "adjusted_date": adjusted,
        "is_adjusted": True,
        "reminder": reminder
    }


def get_query_date(rank_type="day", user_date=None):
    """根据榜单类型和当前时间确定查询日期

    Args:
        rank_type: day/week/month
        user_date: 用户指定日期

    Returns:
        (查询日期字符串, 是否自动推断, 提醒消息)
    """
    if user_date:
        validation = validate_and_adjust_date(rank_type, user_date)
        return validation["adjusted_date"], False, validation["reminder"]

    rank_date = get_latest_query_date(rank_type)

    # 检查今日日榜是否已更新
    reminder = ""
    if rank_type == "day" and not _is_after_day_update():
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        reminder = (
            '日榜数据暂未更新，将为您查询最接近您需求日期的榜单数据⭐~\n'
            f'推荐查询昨日更新的最新榜单（{yesterday}日榜）'
        )

    now = datetime.now()
    if rank_type == "day":
        if _is_after_day_update(now):
            pass  # 已过17:30，查询昨日数据
        else:
            pass  # 未过17:30，查询前天数据
    elif rank_type == "week":
        if _is_after_day_update(now):
            pass
        else:
            pass
    elif rank_type == "month":
        if _is_after_month_update(now):
            pass
        else:
            pass

    return rank_date, True, reminder


# ===== 分类匹配 =====
def match_category(user_input):
    """根据用户输入匹配分类"""
    if not user_input:
        return "人文资讯"
    if user_input in CATEGORIES:
        return user_input
    user_lower = user_input.lower().strip()
    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in user_lower:
                return category
    return "人文资讯"


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


# ===== HTTP请求 =====
def fetch_gzh_growth(rank_type="day", rank_date=None, category="人文资讯"):
    """获取公众号热门账号推荐榜单数据"""
    if not rank_date:
        rank_date = get_latest_query_date(rank_type)

    params = {
        "rankType": rank_type,
        "rankDate": rank_date,
        "category": category,
        "source": SOURCE,
    }

    credential = _get_redfox_api_key()
    if not credential:
        print(
            "未检测到 红狐Hub API Key。请按以下步骤配置：\n"
            "1. 访问 https://redfox.hk/?source=github 了解服务详情\n"
            "2. 前往 https://redfox.hk/login?source=github 注册账号（新用户获赠免费积分）\n"
            "3. 注册登录后在个人中心获取 API Key（格式 ak_xxxxxxxx）\n"
            "4. 设置环境变量：\n"
            "   macOS/Linux: export REDFOX_API_KEY=<你的apikey>\n"
            "   Windows PowerShell: $env:REDFOX_API_KEY = \"<你的apikey>\"\n"
            "   或告知我帮你自动配置到 Shell 配置文件中",
            file=sys.stderr
        )
        return {
            "fetch_time": _get_update_time_label(rank_type, rank_date),
            "rank_type": rank_type,
            "rank_date": rank_date,
            "category": category,
            "time_range": _get_data_time_range(rank_type, rank_date),
            "account_list": [],
            "error": "MISSING_API_KEY"
        }
    headers = {
        "Content-Type": "application/json",
        "X-API-KEY": credential,
    }

    try:
        response = requests.get(API_URL, params=params, headers=headers, timeout=30)
        if response.status_code != 200:
            return {
                "fetch_time": _get_update_time_label(rank_type, rank_date),
                "rank_type": rank_type,
                "rank_date": rank_date,
                "category": category,
                "time_range": _get_data_time_range(rank_type, rank_date),
                "account_list": []
            }
        api_response = response.json()
    except Exception:
        return {
            "fetch_time": _get_update_time_label(rank_type, rank_date),
            "rank_type": rank_type,
            "rank_date": rank_date,
            "category": category,
            "time_range": _get_data_time_range(rank_type, rank_date),
            "account_list": []
        }

    if isinstance(api_response, dict):
        data = api_response.get("data", [])
    elif isinstance(api_response, list):
        data = api_response
    else:
        data = []

    if not data:
        return {
            "fetch_time": _get_update_time_label(rank_type, rank_date),
            "rank_type": rank_type,
            "rank_date": rank_date,
            "category": category,
            "time_range": _get_data_time_range(rank_type, rank_date),
            "account_list": []
        }

    # 保持接口原始顺序，禁止重新排序
    # 综合评分直接采用接口返回的comprehensiveScore字段

    account_list = []
    for idx, item in enumerate(data):
        account_list.append({
            "index": idx + 1,
            "rankPosition": item.get("rankPosition", idx + 1),
            "accountName": item.get("accountName", ""),
            "accountId": item.get("accountId", ""),
            "accountAvatar": item.get("accountAvatar", ""),
            "category": item.get("category", ""),
            "compositeScore": round(float(item.get("comprehensiveScore", 0)), 1) if item.get("comprehensiveScore") else 0,
            "totalReadCount": item.get("totalReadCount", 0),
            "headlineReadCount": item.get("headlineReadCount", 0),
            "maxReadCount": item.get("maxReadCount", 0),
            "totalLikeCount": item.get("totalLikeCount", 0),
            "totalForwardCount": item.get("totalForwardCount", 0),
            "totalInSeeCount": item.get("totalInSeeCount", 0),
            "publishCount": item.get("publishCount", "-"),
        })

    return {
        "fetch_time": _get_update_time_label(rank_type, rank_date),
        "rank_type": rank_type,
        "rank_date": rank_date,
        "category": category,
        "time_range": _get_data_time_range(rank_type, rank_date),
        "account_list": account_list
    }


def _get_data_time_range(rank_type, rank_date):
    """根据榜单类型和查询日期生成数据统计时间周期描述"""
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


def _get_update_time_label(rank_type, rank_date):
    """获取榜单更新时间标签"""
    if rank_type == "day":
        d = datetime.strptime(rank_date, "%Y-%m-%d")
        update_time = d + timedelta(days=1)
        return f"{update_time.strftime('%Y-%m-%d')} 17:30"
    elif rank_type == "week":
        d = datetime.strptime(rank_date, "%Y-%m-%d")
        next_monday = d + timedelta(weeks=1)
        return f"{next_monday.strftime('%Y-%m-%d')} 17:30"
    elif rank_type == "month":
        d = datetime.strptime(rank_date, "%Y-%m-%d")
        if d.month == 12:
            update_day = datetime(d.year + 1, 1, MONTH_UPDATE_DAY)
        else:
            update_day = datetime(d.year, d.month + 1, MONTH_UPDATE_DAY)
        return f"{update_day.strftime('%Y-%m-%d')} 23:00"
    return rank_date


# ===== 数据转换 =====
def raw_data_to_account_list(raw_data):
    """将 gzh_growth_fetcher 的 raw_data 转换为 generate_html 所需的 account_list 格式

    Args:
        raw_data: gzh_growth_fetcher 输出 JSON 中的 raw_data 数组

    Returns:
        list: generate_html 所需的 account_list 格式
    """
    account_list = []
    for idx, item in enumerate(raw_data):
        account_list.append({
            "index": idx + 1,
            "rankPosition": item.get("rankPosition", idx + 1),
            "accountName": item.get("accountName", ""),
            "accountId": item.get("accountId", ""),
            "accountAvatar": item.get("accountAvatar", ""),
            "category": item.get("category", ""),
            "compositeScore": item.get("compositeScore", 0),
            "totalReadCount": item.get("totalReadCount", 0),
            "headlineReadCount": item.get("headlineReadCount", 0),
            "maxReadCount": item.get("maxReadCount", 0),
            "totalLikeCount": item.get("totalLikeCount", 0),
            "totalForwardCount": item.get("totalForwardCount", 0),
            "totalInSeeCount": item.get("totalInSeeCount", 0),
            "publishCount": item.get("publishCount", "-"),
        })
    return account_list


# ===== HTML生成 =====
def generate_html(result, top_n=50):
    """生成HTML页面 - 公众号热门账号推荐榜

    Args:
        result: 榜单数据结果
        top_n: 显示条数，默认50
    """
    account_list = result["account_list"]
    fetch_time = result["fetch_time"]
    rank_date = result.get("rank_date", "")
    category = result.get("category", "人文资讯")
    rank_type = result.get("rank_type", "day")

    rank_type_label = {"day": "日榜", "week": "周榜", "month": "月榜"}.get(rank_type, "日榜")
    time_range = result.get("time_range", _get_data_time_range(rank_type, rank_date))

    top_n = min(top_n, len(account_list), 100)
    account_list = account_list[:top_n]

    js_data = json.dumps(account_list, ensure_ascii=False, indent=2)

    page_title = f"公众号综合实力{rank_type_label} - {category}"

    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{page_title}</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'PingFang SC', sans-serif;
            background: #f5f5f5;
            color: #333;
            line-height: 1.5;
        }}

        .page-wrap {{
            max-width: 700px;
            margin: 0 auto;
            padding: 12px 12px 24px;
        }}

        .export-bar {{
            position: sticky;
            top: 0;
            z-index: 100;
            display: flex;
            justify-content: flex-end;
            gap: 10px;
            padding: 8px 0 10px;
        }}
        .btn-export-pdf, .btn-export-img {{
            background: #fff;
            color: #07c160;
            border: 1.5px solid #07c160;
            border-radius: 20px;
            padding: 6px 18px;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
        }}
        .btn-export-pdf:hover, .btn-export-img:hover {{ background: #f0faf4; }}

        .pdf-content {{ background: transparent; }}

        .header-wrap {{
            background: linear-gradient(135deg, #07c160 0%, #2dc84d 100%);
            border-radius: 12px;
            padding: 20px 16px;
            margin-bottom: 12px;
            color: #fff;
        }}
        .header-wrap h1 {{
            font-size: 22px;
            font-weight: 700;
            margin-bottom: 4px;
        }}
        .header-meta {{
            font-size: 13px;
            opacity: 0.9;
        }}
        .category-badge {{
            display: inline-block;
            background: rgba(255,255,255,0.25);
            border-radius: 10px;
            padding: 2px 10px;
            font-size: 13px;
            margin-left: 8px;
        }}

        .stats-row {{
            display: flex;
            justify-content: space-around;
            margin-top: 14px;
            padding-top: 14px;
            border-top: 1px solid rgba(255,255,255,0.2);
        }}
        .stat-item {{ text-align: center; }}
        .stat-num {{ font-size: 20px; font-weight: 700; }}
        .stat-label {{ font-size: 12px; opacity: 0.85; margin-top: 2px; }}

        .account-list {{
            display: flex;
            flex-direction: column;
            gap: 10px;
        }}

        .account-card {{
            background: #fff;
            border-radius: 12px;
            padding: 14px;
            transition: all 0.2s ease;
            border: 1px solid #f0f0f0;
        }}
        .account-card:hover {{
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        }}
        .account-card.top1 {{ border-left: 3px solid #07c160; }}
        .account-card.top2 {{ border-left: 3px solid #2dc84d; }}
        .account-card.top3 {{ border-left: 3px solid #7ed89a; }}

        .row1 {{
            display: flex;
            align-items: center;
            margin-bottom: 10px;
        }}
        .rank-num {{
            min-width: 36px;
            height: 36px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 18px;
            font-weight: 700;
            color: #999;
            margin-right: 12px;
            flex-shrink: 0;
        }}
        .account-avatar {{
            width: 40px;
            height: 40px;
            border-radius: 50%;
            object-fit: cover;
            margin-right: 10px;
            flex-shrink: 0;
        }}
        .account-info {{
            flex: 1;
            min-width: 0;
        }}
        .account-name {{
            font-size: 16px;
            font-weight: 600;
            color: #333;
            line-height: 1.4;
        }}
        .account-name a {{
            color: #333;
            text-decoration: none;
        }}
        .account-name a:hover {{
            color: #07c160;
        }}
        .account-id {{
            font-size: 12px;
            color: #999;
            margin-top: 2px;
        }}
        .publish-tag {{
            display: inline-block;
            background: #f0faf4;
            color: #07c160;
            border-radius: 4px;
            padding: 1px 6px;
            font-size: 12px;
            font-weight: 500;
            margin-left: 8px;
        }}

        .row2 {{
            display: flex;
            flex-wrap: wrap;
            gap: 14px;
            padding-left: 48px;
            margin-top: 8px;
            padding-top: 8px;
            border-top: 1px solid #f5f5f5;
        }}
        .data-item {{
            display: flex;
            align-items: center;
            gap: 4px;
            font-size: 13px;
        }}
        .data-label {{ color: #999; }}
        .data-value {{ color: #333; font-weight: 600; }}

        .footer-note {{
            text-align: center;
            font-size: 12px;
            color: #bbb;
            margin-top: 16px;
            padding: 10px 0;
        }}

        @media (max-width: 600px) {{
            .page-wrap {{ padding: 8px 8px 20px; }}
            .header-wrap {{ padding: 16px 12px; }}
            .header-wrap h1 {{ font-size: 20px; }}
            .account-card {{ padding: 12px; }}
            .account-name {{ font-size: 15px; }}
            .rank-num {{ min-width: 32px; height: 32px; font-size: 16px; }}
            .row2 {{ gap: 10px; padding-left: 44px; margin-top: 8px; }}
            .data-item {{ font-size: 12px; }}
        }}
    </style>
</head>
<body>

<div class="page-wrap">
    <div class="export-bar">
        <button class="btn-export-img" onclick="exportImage()">导出图片</button>
        <button class="btn-export-pdf" onclick="exportPdf()">导出 PDF</button>
    </div>

    <div class="pdf-content" id="pdfContent">
        <div class="header-wrap">
            <h1>公众号综合实力{rank_type_label}<span class="category-badge">{category}</span></h1>
            <div class="header-meta">更新时间：{fetch_time}</div>
            <div style="font-size:12px;color:rgba(255,255,255,0.75);margin-top:4px;">*公众号综合实力{rank_type_label}，基于阅读、点赞、转发、在看等多维数据综合排名*</div><div style="font-size:12px;color:rgba(255,255,255,0.75);">*数据统计时间周期：{time_range}*</div>
            <div class="stats-row">
                <div class="stat-item">
                    <div class="stat-num" id="totalCount">--</div>
                    <div class="stat-label">公众号数</div>
                </div>
                <div class="stat-item">
                    <div class="stat-num" id="maxRead">--</div>
                    <div class="stat-label">最高总阅读</div>
                </div>
                <div class="stat-item">
                    <div class="stat-num" id="avgRead">--</div>
                    <div class="stat-label">平均总阅读</div>
                </div>
            </div>
        </div>

        <div class="account-list" id="accountList"></div>

        <div class="footer-note">数据来源：公众号平台 · {category} · 公众号综合实力{rank_type_label}</div>
    </div>
</div>

<script>
(function() {{
    function bindCardClick() {{
        var cards = document.querySelectorAll('.account-card[data-href]');
        cards.forEach(function(card) {{
            card.addEventListener('click', function(e) {{
                if (e.target.closest('a, button')) return;
                var url = this.getAttribute('data-href');
                if (url && url !== '#') window.open(url, '_blank');
            }});
        }});
    }}
    if (document.readyState === 'loading') {{
        document.addEventListener('DOMContentLoaded', bindCardClick);
    }} else {{
        bindCardClick();
    }}
}})();

(function() {{
    var RAW = {js_data};

    var totalCount = RAW.length;
    var maxRead = 0, sumRead = 0;

    function fmtNum(val) {{
        var n = parseInt(val) || 0;
        if (n >= 100000000) return (n / 100000000).toFixed(1) + '亿';
        if (n >= 10000) return (n / 10000).toFixed(1) + '万';
        return n.toString();
    }}

    for (var i = 0; i < RAW.length; i++) {{
        var totalRead = parseInt(RAW[i].totalReadCount) || 0;
        if (totalRead > maxRead) maxRead = totalRead;
        sumRead += totalRead;
    }}
    var avgRead = totalCount > 0 ? sumRead / totalCount : 0;

    document.getElementById('totalCount').textContent = totalCount;
    document.getElementById('maxRead').textContent = fmtNum(maxRead);
    document.getElementById('avgRead').textContent = fmtNum(Math.round(avgRead));

    var html = '';
    for (var i = 0; i < RAW.length && i < {top_n}; i++) {{
        var d = RAW[i];
        var rank = i + 1;
        var cardCls = 'account-card';

        if (rank === 1) cardCls += ' top1';
        else if (rank === 2) cardCls += ' top2';
        else if (rank === 3) cardCls += ' top3';

        var searchUrl = 'https://open.weixin.qq.com/qr/code?username=' + encodeURIComponent(d.accountId || d.accountName);
        var avatar = d.accountAvatar || '';
        var accountName = d.accountName || '--';
        var accountId = d.accountId || '';

        var totalReadCount = fmtNum(d.totalReadCount);
        var headlineReadCount = fmtNum(d.headlineReadCount);
        var maxReadCount = fmtNum(d.maxReadCount);
        var totalLikeCount = fmtNum(d.totalLikeCount);
        var totalForwardCount = fmtNum(d.totalForwardCount);
        var totalInSeeCount = fmtNum(d.totalInSeeCount);
        var publishCount = d.publishCount || '-';
        var compositeScore = d.compositeScore || 0;

        var rankHtml = '';
        if (rank === 1) {{
            rankHtml = '<div class="rank-num">🥇</div>';
        }} else if (rank === 2) {{
            rankHtml = '<div class="rank-num">🥈</div>';
        }} else if (rank === 3) {{
            rankHtml = '<div class="rank-num">🥉</div>';
        }} else {{
            rankHtml = '<div class="rank-num">' + rank + '</div>';
        }}

        html += '<div class="' + cardCls + '" data-href="' + searchUrl + '">'
            + '<div class="row1">'
            + rankHtml
            + (avatar ? '<img class="account-avatar export-hide" src="' + avatar + '" referrerPolicy="no-referrer" onerror="this.style.display=\\'none\\'">' : '')
            + '<div class="account-info">'
            + '<div class="account-name"><a href="' + searchUrl + '" target="_blank" onclick="event.stopPropagation()">' + accountName + '</a>'
            + '<span class="publish-tag">发布' + publishCount + '</span>'
            + '</div>'
            + '<div class="account-id">ID: ' + accountId + ' | 综合评分: <b style="color:#07c160">' + compositeScore + '</b></div>'
            + '</div>'
            + '</div>'
            + '<div class="row2">'
            + '<div class="data-item"><span class="data-label">总阅读</span><span class="data-value">' + totalReadCount + '</span></div>'
            + '<div class="data-item"><span class="data-label">头条阅读</span><span class="data-value">' + headlineReadCount + '</span></div>'
            + '<div class="data-item"><span class="data-label">最高阅读</span><span class="data-value">' + maxReadCount + '</span></div>'
            + '<div class="data-item"><span class="data-label">点赞</span><span class="data-value">' + totalLikeCount + '</span></div>'
            + '<div class="data-item"><span class="data-label">在看</span><span class="data-value">' + totalInSeeCount + '</span></div>'
            + '<div class="data-item"><span class="data-label">转发</span><span class="data-value">' + totalForwardCount + '</span></div>'
            + '</div>'
            + '</div>';
    }}

    document.getElementById('accountList').innerHTML = html;
}})();

function _hideAvatarsForExport() {{
    var imgs = document.querySelectorAll('img.export-hide');
    imgs.forEach(function(img) {{
        img.setAttribute('data-original-src', img.src);
        img.style.display = 'none';
    }});
}}

function _restoreAvatarsAfterExport() {{
    var imgs = document.querySelectorAll('img.export-hide');
    imgs.forEach(function(img) {{
        var origSrc = img.getAttribute('data-original-src');
        if (origSrc) {{
            img.src = origSrc;
            img.removeAttribute('data-original-src');
        }}
        img.style.display = '';
    }});
}}

function exportImage() {{
    var btn = document.querySelector('.btn-export-img');
    btn.textContent = '生成中...';
    btn.style.pointerEvents = 'none';
    var target = document.getElementById('pdfContent');
    _hideAvatarsForExport();
    html2canvas(target, {{
        scale: 2,
        useCORS: true,
        allowTaint: true,
        backgroundColor: '#f5f5f5',
        logging: false,
        windowWidth: target.scrollWidth,
        windowHeight: target.scrollHeight
    }}).then(function(canvas) {{
        _restoreAvatarsAfterExport();
        var link = document.createElement('a');
        link.download = 'gzh_power_account_' + new Date().toISOString().slice(0,10) + '.png';
        link.href = canvas.toDataURL('image/png');
        link.click();
        btn.textContent = '导出图片';
        btn.style.pointerEvents = '';
    }}).catch(function(err) {{
        _restoreAvatarsAfterExport();
        alert('图片生成失败：' + err.message);
        btn.textContent = '导出图片';
        btn.style.pointerEvents = '';
    }});
}}

function exportPdf() {{
    var btn = document.querySelector('.btn-export-pdf');
    btn.textContent = '生成中...';
    btn.style.pointerEvents = 'none';
    var target = document.getElementById('pdfContent');
    _hideAvatarsForExport();
    html2canvas(target, {{
        scale: 2,
        useCORS: true,
        allowTaint: true,
            backgroundColor: '#f5f5f5',
            logging: false,
            windowWidth: target.scrollWidth,
            windowHeight: target.scrollHeight
        }}).then(function(canvas) {{
            _restoreAvatarsAfterExport();
            var imgData = canvas.toDataURL('image/png', 1.0);
            var pdf = new jspdf.jsPDF('l', 'mm', 'a4');
            var pdfW = pdf.internal.pageSize.getWidth();
            var pdfH = pdf.internal.pageSize.getHeight();
            var margin = 8;
            var contentW = pdfW - margin * 2;
            var contentH = pdfH - margin * 2;
            var imgW = contentW;
            var imgH = (canvas.height * imgW) / canvas.width;
            if (imgH > contentH) {{
                imgH = contentH;
                imgW = (canvas.width * imgH) / canvas.height;
            }}
            var imgX = (pdfW - imgW) / 2;
            var imgY = (pdfH - imgH) / 2;
            pdf.addImage(imgData, 'PNG', imgX, imgY, imgW, imgH);
            var now = new Date();
            var dateStr = now.getFullYear() +
                String(now.getMonth()+1).padStart(2,'0') +
                String(now.getDate()).padStart(2,'0') +
                '_' +
                String(now.getHours()).padStart(2,'0') +
                String(now.getMinutes()).padStart(2,'0');
            pdf.save('gzh_power_account_' + dateStr + '.pdf');
            btn.textContent = '导出 PDF';
            btn.style.pointerEvents = '';
        }}).catch(function(err) {{
            _restoreAvatarsAfterExport();
            alert('PDF 生成失败：' + err.message);
            btn.textContent = '导出 PDF';
            btn.style.pointerEvents = '';
        }});
}}
</script>

</body>
</html>'''

    # Replace js_data placeholder
    html = html.replace("{js_data}", js_data)

    return html


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='生成公众号热门账号推荐榜HTML页面')
    parser.add_argument('--rank_type', type=str, default='day', choices=['day', 'week', 'month'], help='榜单类型')
    parser.add_argument('--rank_date', type=str, help='查询日期，格式 YYYY-MM-DD')
    parser.add_argument('--category', type=str, default=None, help='分类名称')
    parser.add_argument('--keyword', type=str, help='用户输入的关键词，用于自动匹配分类')
    parser.add_argument('--output', type=str, help='输出文件路径')
    parser.add_argument('--top', type=int, default=50, help='显示条数，默认50')
    parser.add_argument('--input_json_file', type=str, default=None,
                        help='预取数据JSON文件路径（来自gzh_growth_fetcher输出），指定后不再调用API')

    args = parser.parse_args()

    if args.input_json_file:
        # 使用预取数据，不调用 API
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

        account_list = raw_data_to_account_list(raw_data)
        rank_type = fetched.get("rank_type", "day")
        rank_date = fetched.get("rank_date", "")
        category = fetched.get("category", "人文资讯")
        rank_type_label = {"day": "日榜", "week": "周榜", "month": "月榜"}.get(rank_type, "日榜")

        if args.keyword or args.category:
            print("注意: 已指定 --input_json_file，忽略 --keyword/--category 参数", file=sys.stderr)

        result = {
            "fetch_time": fetched.get("update_time", ""),
            "rank_type": rank_type,
            "rank_date": rank_date,
            "category": category,
            "time_range": _get_data_time_range(rank_type, rank_date),
            "account_list": account_list
        }

        print(f"使用预取数据生成HTML（不调用API）...", file=sys.stderr)
        print(f"榜单类型: {rank_type_label}", file=sys.stderr)
        print(f"查询日期: {rank_date}", file=sys.stderr)
        print(f"分类：{category}", file=sys.stderr)
    else:
        # 原有逻辑：调用 API 获取数据
        # 处理分类
        if args.keyword and not args.category:
            category = match_category(args.keyword)
            print(f"根据关键词【{args.keyword}】匹配到分类：【{category}】", file=sys.stderr)
        elif args.category:
            category = args.category
        else:
            category = "人文资讯"

        # 处理日期
        rank_date, is_auto, reminder = get_query_date(args.rank_type, args.rank_date)

        rank_type_label = {"day": "日榜", "week": "周榜", "month": "月榜"}.get(args.rank_type, "日榜")

        print(f"正在获取公众号综合实力{rank_type_label}数据...", file=sys.stderr)
        print(f"当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", file=sys.stderr)
        if reminder:
            print(f"提醒: {reminder}", file=sys.stderr)
        print(f"榜单类型: {rank_type_label}", file=sys.stderr)
        print(f"查询日期: {rank_date}", file=sys.stderr)
        print(f"分类：{category}", file=sys.stderr)

        result = fetch_gzh_growth(rank_type=args.rank_type, rank_date=rank_date, category=category)

    html = generate_html(result, top_n=args.top)

    if args.output:
        output_path = args.output
    else:
        rank_short = {"day": "日", "week": "周", "month": "月"}.get(result.get("rank_type", args.rank_type), "日")
        timestamp_str = datetime.now().strftime("%Y%m%d")[-8:] + f"{datetime.now().strftime('%H%M%S')}"
        filename = f"公众号综合实力{rank_short}_{result.get('category', category)}_{timestamp_str}.html"
        output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"已生成：{output_path}", file=sys.stderr)
    print(f"共 {len(result['account_list'])} 条{rank_type_label}数据，展示TOP{args.top}", file=sys.stderr)
