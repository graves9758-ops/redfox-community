#!/usr/bin/env python3
from __future__ import annotations
"""
小红书账号榜单数据抓取脚本 v3
用法：
    python fetch_rank.py --period day --date 2026-04-27 --category 美食
    python fetch_rank.py --query "最新小红书日榜"
    python fetch_rank.py --query "美妆类周榜"
    python fetch_rank.py --query "2026年4月月榜"
"""
import argparse
import json
import re
import sys
import os
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

API_URL = "https://redfox.hk/story/api/xhsData/query"


def _get_api_key() -> str:
    """从环境变量获取 API Key，返回格式 ak_xxxxxxxx。"""
    return os.environ.get("REDFOX_API_KEY", "").strip()


def _http_post(url: str, payload: dict, timeout: int = 15) -> dict:
    """
    使用原生 urllib 发送 HTTPS 请求（正常验证 SSL 证书）。
    自动注入 X-API-KEY 鉴权头。
    """
    api_key = _get_api_key()
    if not api_key:
        print("[ERROR] 未设置 REDFOX_API_KEY 环境变量", file=sys.stderr)
        print("[提示] 请访问 https://redfox.hk/ 注册获取 API Key", file=sys.stderr)
        print("[提示] 设置方式：export REDFOX_API_KEY=<你的apikey>", file=sys.stderr)
        sys.exit(4)

    payload_bytes = json.dumps(payload).encode("utf-8")

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "X-API-KEY": api_key,
    }

    req = Request(url, data=payload_bytes, headers=headers, method="POST")
    try:
        resp = urlopen(req, timeout=timeout)
        data = resp.read().decode("utf-8")
        return json.loads(data)
    except json.JSONDecodeError:
        print("[ERROR] 返回数据格式异常（非 JSON）", file=sys.stderr)
        sys.exit(2)
    except HTTPError as e:
        print(f"[ERROR] HTTP {e.code}: {e.reason}", file=sys.stderr)
        sys.exit(2)
    except URLError as e:
        print(f"[ERROR] 网络请求失败: {e.reason}", file=sys.stderr)
        sys.exit(2)
    except TimeoutError:
        print("[ERROR] 请求超时，请检查网络后重试", file=sys.stderr)
        sys.exit(2)


# ─────────────────────────────────────────────────────────
# 赛道映射：关键词 → 接口 type 参数
# ─────────────────────────────────────────────────────────
CATEGORY_MAP = {
    # 精确
    "综合全部": "综合全部",
    "出行代步": "出行代步",
    "休闲爱好": "休闲爱好",
    "影视娱乐": "影视娱乐",
    "数码科技": "数码科技",
    "医疗保健": "医疗保健",
    "综合杂项": "综合杂项",
    "星座情感": "星座情感",
    "时尚穿搭": "时尚穿搭",
    "婚庆婚礼": "婚庆婚礼",
    "拍摄记录": "拍摄记录",
    "学习教育": "学习教育",
    "化妆美容": "化妆美容",
    "居家装修": "居家装修",
    "旅行度假": "旅行度假",
    "亲子育儿": "亲子育儿",
    "个人护理": "个人护理",
    "美味佳肴": "美味佳肴",
    "职业发展": "职业发展",
    "宠物天地": "宠物天地",
    "潮流鞋包": "潮流鞋包",
    "日常生活": "日常生活",
    "科学探索": "科学探索",
    "新闻资讯": "新闻资讯",
    "体育锻炼": "体育锻炼",
    # 别名 / 模糊
    "美妆": "化妆美容", "彩妆": "化妆美容", "护肤": "个人护理",
    "美容": "个人护理", "护肤美妆": "化妆美容",
    "科技": "数码科技", "互联网": "数码科技", "ai": "数码科技", "人工智能": "数码科技",
    "健康": "医疗保健", "养生": "医疗保健", "医疗": "医疗保健",
    "美食": "美味佳肴", "探店": "美味佳肴", "烹饪": "美味佳肴", "烘焙": "美味佳肴",
    "旅行": "旅行度假", "旅游": "旅行度假",
    "出行": "出行代步", "户外": "休闲爱好",
    "穿搭": "时尚穿搭", "时尚": "时尚穿搭",
    "母婴": "亲子育儿", "育儿": "亲子育儿", "亲子": "亲子育儿",
    "教育": "学习教育", "学习": "学习教育",
    "宠物": "宠物天地", "猫": "宠物天地", "狗": "宠物天地",
    "健身": "体育锻炼", "运动": "体育锻炼", "瑜伽": "体育锻炼",
    "装修": "居家装修", "家居": "居家装修", "家装": "居家装修",
    "情感": "星座情感", "星座": "星座情感",
    "娱乐": "影视娱乐", "影视": "影视娱乐", "视频": "影视娱乐",
    "vlog": "拍摄记录", "摄影": "拍摄记录", "拍照": "拍摄记录",
    "职场": "职业发展", "职场发展": "职业发展", "招聘": "职业发展",
    "婚礼": "婚庆婚礼", "结婚": "婚庆婚礼",
    "鞋包": "潮流鞋包", "包包": "潮流鞋包",
    "新闻": "新闻资讯", "资讯": "新闻资讯",
    "科普": "科学探索", "科学": "科学探索",
    "综合": "综合全部", "全品类": "综合全部", "全部": "综合全部",
    "日常": "日常生活",
}

# 接口 type 精确值（用于判断是否为模糊匹配）
EXACT_CATEGORIES = {
    "综合全部", "出行代步", "休闲爱好", "影视娱乐", "数码科技",
    "医疗保健", "综合杂项", "星座情感", "时尚穿搭", "婚庆婚礼",
    "拍摄记录", "学习教育", "化妆美容", "居家装修", "旅行度假",
    "亲子育儿", "个人护理", "美味佳肴", "职业发展", "宠物天地",
    "潮流鞋包", "日常生活", "科学探索", "新闻资讯", "体育锻炼",
}

PERIOD_MAP = {"day": 1, "week": 2, "month": 3}
PERIOD_LABEL_MAP = {"day": "日榜", "week": "周榜", "month": "月榜"}
PERIOD_LABELS = {"day": "日榜", "week": "周榜", "month": "月榜"}
# 短字符别名（精确或词边界匹配）
SHORT_ALIASES = {"day": "日", "week": "周", "month": "月"}
# 长字符别名（子串匹配即可）
LONG_ALIASES = {
    "day":   ["day", "daily", "日榜", "日排名", "日间", "今日", "昨日"],
    "week":  ["week", "weekly", "周榜", "周排名", "周间", "本周", "本周涨粉", "上周", "本周涨"],
    "month": ["month", "monthly", "月榜", "月排名", "月间", "本月", "上月"],
}


def _parse_period_keyword(text: str) -> str | None:
    # 先屏蔽完整日期模式，避免"5月10日"中的"月"被匹配为月榜
    masked = re.sub(r"\d{4}[年\-\/]\d{1,2}[月\-\/]\d{1,2}", "____", text)   # 2026年5月10号
    masked = re.sub(r"\d{1,2}月\d{1,2}(日|号)?", "____", masked)                  # 5月10日/5月10号
    masked = re.sub(r"\d{1,2}[日号](?!榜)", "____", masked)                         # 10日（排除日榜）
    
    # 优先：长字符串子串匹配（不易误匹配）
    for p, aliases in LONG_ALIASES.items():
        for a in aliases:
            if a in masked:
                return p
    # 其次：短字符精确或词边界匹配
    for p, char in SHORT_ALIASES.items():
        for i, ch in enumerate(masked):
            if ch == char:
                before = masked[i - 1] if i > 0 else " "
                after = masked[i + 1] if i < len(masked) - 1 else " "
                # 如果前后是字母/数字/空格/标点，或正好是边界，则匹配
                if not (("\u4e00" <= before <= "\u9fff") or ("\u4e00" <= after <= "\u9fff")):
                    return p
    return None
UPDATE_RULES = {
    1: {"label": "日榜", "update_time": "每日19:00", "window_days": 7},
    2: {"label": "周榜", "update_time": "每周一15:00", "window_days": 21},
    3: {"label": "月榜", "update_time": "每月1日9:00", "window_days": 90},
}


def _get_latest_date(period: str, offset: int = 1) -> date:
    """
    获取指定周期的目标日期，根据当前时间和更新时间动态调整。
    period: day / week / month
    offset: 往前回溯的期数，默认 1（上一期）
    
    时序规则（T+1）：
    - 日榜：昨天的数据，今天19:00后才能查。19:00前查"最新" → 取前天(offset=2)
    - 周榜：上周的数据，本周一15:00后才能查。周一15:00前查"最新" → 取上上周(offset=2)
    - 月榜：上月的数据，本月1日9:00后才能查。1日9:00前查"最新" → 取上上月(offset=2)
    """
    today = date.today()
    now = datetime.now()
    current_time = now.time()
    
    if period == "day":
        # 日榜：昨天数据今天19:00后才能查
        # 19:00前查"最新"(offset=1)，需要取前天(offset=2)
        if offset == 1 and current_time.hour < 19:
            offset = 2
        return today - timedelta(days=offset)
    elif period == "week":
        # 周榜：上周数据本周一15:00后才能查
        # 本周一
        days_since_monday = today.weekday()
        this_monday = today - timedelta(days=days_since_monday)
        
        # 周一15:00前查"最新"(offset=1)，需要取上上周(offset=2)
        if offset == 1 and now.weekday() == 0 and current_time.hour < 15:
            offset = 2
        
        return this_monday - timedelta(weeks=offset)
    elif period == "month":
        # 月榜：上月数据本月1日9:00后才能查
        # 1日9:00前查"最新"(offset=1)，需要取上上月(offset=2)
        if offset == 1 and now.day == 1 and current_time.hour < 9:
            offset = 2
        
        month_offset = offset - 1
        year = today.year
        month = today.month - month_offset
        while month <= 0:
            month += 12
            year -= 1
        return date(year, month, 1)
    return today - timedelta(days=offset)


def _get_monday_of_week(d: date) -> date:
    """
    获取指定日期所在周的周一
    周一=0，周二=1，...，周日=6
    """
    days_since_monday = d.weekday()
    return d - timedelta(days=days_since_monday)


def _get_2nd_of_month(d: date) -> date:
    """
    获取指定日期所在月的1号
    """
    return date(d.year, d.month, 1)


def _is_within_window(target_date: date, period: str) -> bool:
    """
    检查目标日期是否在可查询窗口内，同时确保数据已更新。
    
    T+1时序规则：
    - 日榜：昨天数据，今天19:00后才能查
    - 周榜：上周数据，本周一15:00后才能查
    - 月榜：上月数据，本月1日9:00后才能查
    """
    today = date.today()
    now = datetime.now()
    current_time = now.time()
    
    # 计算日期差
    diff = (today - target_date).days
    window = UPDATE_RULES[PERIOD_MAP[period]]["window_days"]
    
    # 基本窗口检查（diff=0表示当天，不允许查当天数据）
    if not (1 <= diff <= window):
        return False
    
    # T+1时序检查：确保数据已更新
    if period == "day":
        # 查昨天(diff=1)的数据，必须今天19:00后
        if diff == 1 and current_time.hour < 19:
            return False
    elif period == "week":
        # 查上周的数据，必须本周一15:00后
        this_monday = today - timedelta(days=today.weekday())
        last_monday = this_monday - timedelta(weeks=1)
        if target_date == last_monday:
            if now.weekday() == 0 and current_time.hour < 15:
                return False
    elif period == "month":
        # 查上月数据，必须本月1日9:00后
        last_month_1st = date(today.year, today.month - 1, 1) if today.month > 1 else date(today.year - 1, 12, 1)
        if target_date == last_month_1st:
            if now.day == 1 and current_time.hour < 9:
                return False
    
    return True


def _is_data_updated(period: str) -> bool:
    """
    判断当前时间是否已更新最新一期的数据。
    返回 True 表示已更新（可取上一期），False 表示未更新（需取上上期）。
    
    更新规则：
    - 日榜：每日 19:00 更新
    - 周榜：每周一 15:00 后更新
    - 月榜：每月 2号 9:00 更新
    """
    now = datetime.now()
    current_time = now.time()
    
    if period == "day":
        # 每日 19:00 更新
        return current_time.hour >= 19
    elif period == "week":
        # 每周一 15:00 后更新
        if now.weekday() == 0:  # 周一
            return current_time.hour >= 15
        else:
            # 不是周一，如果已过周一15:00则已更新
            return True
    elif period == "month":
        # 每月 1日 9:00 更新
        if now.day == 1:
            return current_time.hour >= 9
        else:
            # 已过1日9:00，已更新
            return True
    return True




def _parse_date_from_text(text: str, explicit_period: str | None = None) -> tuple[date | None, str | None]:
    """
    从文本中解析日期。
    若 explicit_period 已明确（如用户说了"周榜"），则不通过"最新/今日"等
    模糊关键词来推断 period，避免覆盖已识别出的明确周期。
    
    "最新"关键词会根据更新时间判断：
    - 已更新 → 取上一期
    - 未更新 → 取上上期
    """
    today = date.today()
    # YYYY-MM-DD / YYYY年MM月DD日
    m = re.search(r"(\d{4})[年\-\/](\d{1,2})[月\-\/](\d{1,2})", text)
    if m:
        try:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3))), None
        except Exception:
            pass
    
    # MM月DD日 / MM-DD 格式（不带年份）
    m2 = re.search(r"(\d{1,2})月(\d{1,2})(日|号)?", text)
    if m2:
        try:
            month = int(m2.group(1))
            day = int(m2.group(2))
            # 假设是当年
            year = date.today().year
            return date(year, month, day), None
        except Exception:
            pass
    
    # M.D / M.D日 格式（如 6.5、6.5日）
    m3 = re.search(r"(\d{1,2})\.(\d{1,2})(日|号)?", text)
    if m3:
        try:
            month = int(m3.group(1))
            day = int(m3.group(2))
            year = date.today().year
            return date(year, month, day), None
        except Exception:
            pass
    
    # 纯日期关键词（只取日期，不推断 period）
    for kw, delta, require_period in [
        ("最新", None, True),   # delta=None 表示需要根据更新时间动态判断
        ("今日", 1, False), ("今天", 1, False), ("昨日", 1, False),
        ("本周", 0, False), ("这周", 0, False), ("本月", 0, False), ("这个月", 0, False),
    ]:
        if kw in text:
            base_period = explicit_period or "day"
            
            # 动态计算 delta
            if delta is None:
                # "最新"：根据更新时间判断
                if _is_data_updated(base_period):
                    delta = 1  # 已更新，取上一期
                else:
                    delta = 2  # 未更新，取上上期
            
            d = _get_latest_date(base_period, offset=delta)
            return d, explicit_period  # 仅返回日期，period 以 explicit_period 为准
    return None, None


def match_category(keyword: str) -> tuple[str, bool]:
    kw = keyword.strip()
    if not kw:
        return "综合全部", False
    if kw in CATEGORY_MAP:
        return CATEGORY_MAP[kw], kw in EXACT_CATEGORIES
    lower_kw = kw.lower()
    for k, v in CATEGORY_MAP.items():
        if k.lower() == lower_kw:
            return v, k in EXACT_CATEGORIES
    for k, v in CATEGORY_MAP.items():
        if k in kw or kw in k:
            return v, True
    return "综合全部", True


# ─────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────
# 综合评分计算
# ─────────────────────────────────────────────────────────
def _parse_num(val) -> float:
    """将字符串或数字转为 float，失败返回 0"""
    if val is None or val == "-" or val == "":
        return 0
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip()
    if not s:
        return 0
    try:
        if "w" in s.lower() or "万" in s:
            return float(s.lower().replace("w", "").replace("万", "")) * 10000
        return float(s)
    except Exception:
        return 0

def _normalize_by_max(values: list, base: float = 100) -> list:
    """归一化：除以最大值，乘以基础分"""
    max_val = max(values) if values else 0
    if max_val == 0:
        return [0.0] * len(values)
    return [v / max_val * base for v in values]


def calculate_scores_batch(items: list) -> list:
    """
    批量计算评分并返回归一化后的分数
    
    评分规则（满分100）：使用对数归一化 ln(x)/ln(max)
    - 总粉丝数：20%
    - 新增粉丝：20%
    - 新增点赞：15%
    - 新增收藏：15%
    - 新增分享：15%
    - 新增评论：15%
    """
    import math
    
    # 提取所有数据
    followers_list = [_parse_num(i.get("followers") or i.get("fansCount") or i.get("fans")) for i in items]
    fans_list = [_parse_num(i.get("newFans") or i.get("fansGrowth")) for i in items]
    likes_list = [_parse_num(i.get("newLikes") or i.get("likedGrowth")) for i in items]
    collects_list = [_parse_num(i.get("newCollects") or i.get("collectedGrowth")) for i in items]
    shares_list = [_parse_num(i.get("newShares") or i.get("sharedGrowth")) for i in items]
    comments_list = [_parse_num(i.get("newComments") or i.get("commentsGrowth")) for i in items]
    
    # 获取最大值
    max_followers = max(followers_list) if followers_list else 1
    max_fans = max(fans_list) if fans_list else 1
    max_likes = max(likes_list) if likes_list else 1
    max_collects = max(collects_list) if collects_list else 1
    max_shares = max(shares_list) if shares_list else 1
    max_comments = max(comments_list) if comments_list else 1
    
    results = []
    for item in items:
        followers = _parse_num(item.get("followers") or item.get("fansCount") or item.get("fans"))
        fans_growth = _parse_num(item.get("newFans") or item.get("fansGrowth"))
        likes_growth = _parse_num(item.get("newLikes") or item.get("likedGrowth"))
        collects_growth = _parse_num(item.get("newCollects") or item.get("collectedGrowth"))
        shares_growth = _parse_num(item.get("newShares") or item.get("sharedGrowth"))
        comments_growth = _parse_num(item.get("newComments") or item.get("commentsGrowth"))
        
        # 对数归一化：ln(x+1)/ln(max+1)
        def log_norm(val, max_val):
            if val <= 0 or max_val <= 1:
                return 0
            return math.log(val + 1) / math.log(max_val + 1) * 100
        
        norm_followers = log_norm(followers, max_followers)
        norm_fans = log_norm(fans_growth, max_fans)
        norm_likes = log_norm(likes_growth, max_likes)
        norm_collects = log_norm(collects_growth, max_collects)
        norm_shares = log_norm(shares_growth, max_shares)
        norm_comments = log_norm(comments_growth, max_comments)
        
        # 加权求和
        score = (
            norm_followers * 0.20 +
            norm_fans * 0.20 +
            norm_likes * 0.15 +
            norm_collects * 0.15 +
            norm_shares * 0.15 +
            norm_comments * 0.15
        )
        
        item["comprehensiveScore"] = int(score)  # 保留整数
    
    return items
# ─────────────────────────────────────────────────────────
def fetch(period: str, rank_date: str, category: str, is_latest: bool = False) -> tuple[list[dict], str, str]:
    """
    获取榜单数据
    is_latest: 是否查询"最新"，如果是则当天无数据时告知更新时间并回退前一天
    返回: (数据列表, 实际查询的日期, 提示信息)
    """
    from datetime import datetime, timedelta
    
    # 更新时间提示
    update_time_hint = {
        "day": "每日19:00",
        "week": "每周一15:00",
        "month": "每月1日9:00",
    }
    
    current_date = rank_date
    original_date = rank_date
    fallback_hint = ""
    
    payload = {
        "dateType": PERIOD_MAP[period],
        "rankDate": current_date,
        "type": category if category else "综合全部",
        "source": "小红书最夯账号",
    }
    result = _http_post(API_URL, payload, timeout=15)

    if result.get("code") == 2000:
        data = result.get("data", [])
        if data:
            return data, current_date, ""
    
    # 回退策略：根据周期类型回退到正确的日期
    def get_fallback_date(current: str, period_type: str) -> str:
        """根据周期类型计算回退日期"""
        d = datetime.strptime(current, "%Y-%m-%d").date()
        if period_type == "day":
            # 日榜：回退前一天
            d -= timedelta(days=1)
        elif period_type == "week":
            # 周榜：回退到上一个周一
            d = _get_monday_of_week(d) - timedelta(weeks=1)
        elif period_type == "month":
            # 月榜：回退到上一个月1日
            if d.month == 1:
                d = date(d.year - 1, 12, 1)
            else:
                d = date(d.year, d.month - 1, 1)
        return d.strftime("%Y-%m-%d")
    
    # 当天无数据
    if is_latest:
        # 查询最新数据但当天无数据，告知更新时间并回退
        ut = update_time_hint.get(period, "")
        fallback_hint = f"{current_date} 暂无数据（{PERIOD_LABEL_MAP.get(period, '日榜')}{ut}更新），已为您查询上一期的数据"
        current_date = get_fallback_date(current_date, period)
        
        payload["rankDate"] = current_date
        try:
            result = _http_post(API_URL, payload, timeout=15)
        except Exception:
            print("[ERROR] 回退查询失败", file=sys.stderr)
            sys.exit(2)
        
        if result.get("code") == 2000:
            data = result.get("data", [])
            if data:
                return data, current_date, fallback_hint
        
        # 上一期也无数据，继续回退最多3期
        max_fallback = {"day": 7, "week": 3, "month": 3}.get(period, 3)
        for i in range(2, max_fallback + 1):
            current_date = get_fallback_date(current_date, period)
            payload["rankDate"] = current_date
            try:
                result = _http_post(API_URL, payload, timeout=15)
            except Exception:
                continue
            
            if result.get("code") == 2000:
                data = result.get("data", [])
                if data:
                    fallback_hint = f"{original_date} 暂无数据，已为您查询 {current_date} 的数据"
                    return data, current_date, fallback_hint
        
        print(f"[ERROR] 近{max_fallback}期均无数据", file=sys.stderr)
        sys.exit(3)
    else:
        # 用户指定具体日期但无数据，告知更新时间并自动回退
        ut = update_time_hint.get(period, "")
        fallback_hint = f"{current_date} 暂无数据（{PERIOD_LABEL_MAP.get(period, '日榜')}{ut}更新），已为您查询上一期的数据"
        current_date = get_fallback_date(current_date, period)
        
        payload["rankDate"] = current_date
        try:
            result = _http_post(API_URL, payload, timeout=15)
        except Exception:
            print("[ERROR] 回退查询失败", file=sys.stderr)
            sys.exit(2)
        
        if result.get("code") == 2000:
            data = result.get("data", [])
            if data:
                return data, current_date, fallback_hint
        
        print(f"[ERROR] {original_date} 及上一期均暂无数据", file=sys.stderr)
        sys.exit(3)
    
    return [], current_date, ""


def _fmt_num(val) -> str:
    """将数字格式化为易读形式，None / 0 / '-' 统一显示 '-'"""
    if val is None or val == "-":
        return "-"
    try:
        n = int(val)
    except (ValueError, TypeError):
        return str(val)
    if n == 0:
        return "-"
    if n >= 100_000_000:
        return f"{n/100_000_000:.1f}亿"
    if n >= 10_000:
        return f"{n/10_000:.1f}w"
    return str(n)


def build_markdown_table(items: list, period_label: str, date_str: str,
                          cat_display: str, fetch_time: str, total: int,
                          fuzzy_flag: bool = False) -> str:
    update_time_map = {1: "每日19:00", 2: "每周一15:00", 3: "每月1日9:00"}
    period_key = {"日榜": "day", "周榜": "week", "月榜": "month"}.get(period_label, "day")
    ut = update_time_map.get(PERIOD_MAP.get(period_key, 1), "")

    lines = [
        f"💡 榜单说明：{period_label}{ut}更新。",
        "📐 排名算法：综合评分根据达人在小红书的 **总粉丝数**、周期内的 **粉丝增量**、"
        "**点赞增量**、**收藏增量**、**分享增量** 以及 **评论增量** 加权计算所得（满分100）。",
    ]
    cat_suffix = f"（{cat_display}）" if cat_display != "全品类" else ""
    lines.append(f"📊 {date_str} 小红书{cat_display}{cat_suffix}最夯账号（{period_label}）")
    lines.append("")

    # 表头（新增综合评分列）
    lines.append("排名\t账号名\t综合评分\t总粉丝数\t新增笔记数\t新增粉丝\t新增点赞\t新增评论\t新增收藏\t新增分享")
    lines.append("----\t------\t----\t----------\t--------\t--------\t--------\t--------\t--------\t--------")

    is_all_category = (cat_display == "全品类" or cat_display == "综合全部")
    
    for item in items:
        account_name = item.get('accountName', '')
        account_link = item.get('accountLink', item.get('profileUrl', ''))
        track = (item.get('category') or cat_display)
        
        # 全品类时账号名后加"·赛道"
        if is_all_category and track:
            account_display = f"[{account_name}·{track}]({account_link})" if account_link else f"{account_name}·{track}"
        else:
            account_display = f"[{account_name}]({account_link})" if account_link else account_name

        followers   = _fmt_num(item.get('fansCount') or item.get('followers') or item.get('totalFollowers'))
        new_fans    = _fmt_num(item.get('fansGrowth') or item.get('newFans') or item.get('newFollowers'))
        new_likes   = _fmt_num(item.get('likedGrowth') or item.get('newLikes') or item.get('newLikeCount'))
        new_comments= _fmt_num(item.get('commentsGrowth') or item.get('newComments') or item.get('newCommentCount'))
        new_collects= _fmt_num(item.get('collectedGrowth') or item.get('newCollects') or item.get('newCollectCount'))
        new_shares  = _fmt_num(item.get('sharedGrowth') or item.get('newShares') or item.get('newShareCount'))
        new_notes   = item.get('newNoteCount') or '-'
        rank = item.get('accountRanking') or item.get('rank', '-')
        score = item.get('comprehensiveScore', 0)
        if isinstance(score, (int, float)) and score > 0:
            score = int(score)
        else:
            score = '-'

        lines.append(
            f"{rank}\t{account_display}\t{score}\t{followers}\t"
            f"{new_notes}\t{new_fans}\t{new_likes}\t{new_comments}\t{new_collects}\t{new_shares}"
        )

    shown = len(items)
    lines.extend([
        "",
        "⚡ 更多操作",
        "• 点击下方下载HTML报告文件，可在浏览器中打开查看，支持一键导出PDF/高清图片",
        f"• 本次榜单完整共{total}条数据，是否需要查看剩余{max(0,total-shown)}条？",
        "",
        "📬 订阅服务",
        "1️⃣ 是否需要订阅每日/周/月的小红书账号最新排名，订阅后定时推送给您？",
        "2️⃣ 是否需要订阅具体赛道的账号表现？我们支持：综合全部、出行代步、休闲爱好、影视娱乐、数码科技、医疗保健、综合杂项、星座情感、时尚穿搭、婚庆婚礼、拍摄记录、学习教育、化妆美容、居家装修、旅行度假、亲子育儿、个人护理、美味佳肴、职业发展、宠物天地、潮流鞋包、日常生活、科学探索、新闻资讯、体育锻炼",
    ])
    return "\n".join(lines)


def to_normalized_json(items: list, period: str, date_str: str,
                       category: str) -> dict:
    fetch_time = items[0].get("dataFetchTime", "") if items else ""

    def parse_inter(s: str) -> int:
        s = s.strip()
        if not s:
            return 0
        if "w" in s.lower():
            try:
                return int(float(s.lower().replace("w", "")) * 10000)
            except Exception:
                return 0
        try:
            return int(s)
        except Exception:
            return 0

    # 批量计算评分并按评分降序排序
    scored_items = calculate_scores_batch(items)
    
    normalized_list = []
    for item in scored_items:
        score = item.get("comprehensiveScore", 0)
        normalized_list.append({
            "rank":          item.get("accountRanking") or item.get("rank"),
            "accountName":   item.get("accountName", ""),
            # 新接口直接返回 category 字段
            "category":      item.get("category") or category or "综合全部",
            "comprehensiveScore": score,
            # 粉丝总量
            "followers":     item.get("fansCount") or item.get("followers") or None,
            # 新增各项指标（新接口字段：字符串格式如 "6.68w"）
            "newNoteCount":  item.get("newNoteCount") or 0,
            "newFans":       item.get("fansGrowth") or item.get("newFans") or None,
            "newLikes":      item.get("likedGrowth") or item.get("newLikes") or None,
            "newComments":   item.get("commentsGrowth") or item.get("newComments") or None,
            "newCollects":   item.get("collectedGrowth") or item.get("newCollects") or None,
            "newShares":     item.get("sharedGrowth") or item.get("newShares") or None,
            # 互动合计（旧接口兼容保留）
            "newInteraction": parse_inter(item.get("newInteractionCount", "0")),
            "profileUrl":    item.get("accountLink") or item.get("profileUrl", ""),
        })
    
    # 按综合评分降序排序
    normalized_list.sort(key=lambda x: x.get("comprehensiveScore", 0), reverse=True)
    
    # 更新排序后的排名
    for i, item in enumerate(normalized_list):
        item["rank"] = i + 1

    return {
        "period": period,
        "date": date_str,
        "category": category,
        "fetchTime": fetch_time,
        "total": len(normalized_list),
        "list": normalized_list,
    }


def parse_natural_query(query: str) -> dict:
    text = query.strip()
    result = {
        "period": "day",
        "date": str(_get_latest_date("day")),
        "category": "综合全部",
        "category_fuzzy": False,
        "warning": "",
        "date_fallback": False,
        "is_latest": False,  # 是否询问最新数据
    }

    # 判断是否询问最新（没有明确指定具体日期数字）
    # "最新"、"今天"不算明确日期，应该走 is_latest + 自动回退
    has_explicit_date = bool(
        re.search(r"\d{4}[年\-\/]\d{1,2}[月\-\/]\d{1,2}", text) or  # 2026-05-10
        re.search(r"\d{1,2}月\d{1,2}(日|号)?", text) or  # 5月10号
        re.search(r"\d{1,2}[日号](?!榜)", text)  # 10日/10号（排除"日榜"）
    )
    result["is_latest"] = not has_explicit_date

    # 1. 解析周期（_parse_period_keyword 已内置日期屏蔽）
    period = _parse_period_keyword(text)

    # 2. 解析日期
    found_date, _ = _parse_date_from_text(text, explicit_period=period)

    # 3. 确定周期和日期
    if found_date:
        # 有明确日期时，如果也匹配到了周期关键词则用周期，否则默认日榜
        if period and period != "day":
            result["period"] = period
        else:
            result["period"] = "day"
        result["date"] = str(found_date)
    else:
        # 无明确日期，使用周期关键词（默认日榜）
        result["period"] = period if period else "day"
        # is_latest=True 时，日期由 fetch 函数自动回退

    # 4. 根据周期类型自动纠正日期
    # 周榜：必须传入周一日期
    # 月榜：必须传入每月1日
    if result["date"] and result["period"] in ("week", "month"):
        parsed_date = date.fromisoformat(result["date"])
        if result["period"] == "week":
            corrected_date = _get_monday_of_week(parsed_date)
            if corrected_date != parsed_date:
                result["date"] = str(corrected_date)
                result["date_corrected"] = True
                result["date_correction_msg"] = f"周榜已自动纠正为该周周一：{corrected_date}"
        elif result["period"] == "month":
            corrected_date = _get_2nd_of_month(parsed_date)
            if corrected_date != parsed_date:
                result["date"] = str(corrected_date)
                result["date_corrected"] = True
                result["date_correction_msg"] = f"月榜已自动纠正为当月1日：{corrected_date}"

    # 5. 回溯范围校验
    target_date = date.fromisoformat(result["date"])
    if not _is_within_window(target_date, result["period"]):
        window = UPDATE_RULES[PERIOD_MAP[result["period"]]]["window_days"]
        unit = {"day": "天", "week": "周", "month": "月"}[result["period"]]
        best_date = _get_latest_date(result["period"])
        result["warning"] = (
            f"⚠️ 抱歉🙏，目前小红书榜单最多支持回溯「近{window}{unit}」，"
            f"已自动切换至最近可用数据。"
        )
        result["date"] = str(best_date)
        result["date_fallback"] = True

    # 6. 赛道匹配（去除周期/日期关键词后）
    exclude = r"[\d年月日周榜周排名本月本月度今日最近最新"
    exclude += r"小红书榜单排名账号排行榜最夯给我查询看看想要要看]"
    kw = re.sub(exclude, "", text)
    matched_type, fuzzy = match_category(kw)
    result["category"] = matched_type
    result["category_fuzzy"] = fuzzy

    return result


# ─────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="小红书账号榜单抓取 v3（支持自然语言）")
    parser.add_argument("--query", "-q", type=str, default="",
                        help="自然语言查询，如：最新美食周榜 / 2026年4月美妆日榜")
    parser.add_argument("--period", choices=["day", "week", "month"], default=None)
    parser.add_argument("--date", default="", help="目标日期 YYYY-MM-DD")
    parser.add_argument("--category", default="", help="赛道类型")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--output", default="", help="JSON 输出文件路径")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    parser.add_argument("--html", action="store_true", help="生成 HTML 报告文件")
    args = parser.parse_args()

    # 自然语言模式
    if args.query:
        parsed = parse_natural_query(args.query)
        period = parsed["period"]
        rank_date = parsed["date"]
        category = parsed["category"]
        category_fuzzy = parsed["category_fuzzy"]
        if parsed["warning"]:
            print(f"\n{parsed['warning']}\n", file=sys.stderr)
        if parsed["date_fallback"]:
            print(f"[WARN] 已回退至最近可用日期：{rank_date}", file=sys.stderr)
        print(f"[INFO] 解析结果 → 周期={period} 日期={rank_date} 赛道={category} 最新={parsed['is_latest']}", file=sys.stderr)
    else:
        period = args.period or "day"
        rank_date = args.date if args.date else str(_get_latest_date(period))
        category = args.category if args.category else "综合全部"
        category_fuzzy = False
        parsed = {"is_latest": args.date == ""}  # 没有指定日期则为最新查询

    # 回溯校验
    target_date = date.fromisoformat(rank_date)
    if not _is_within_window(target_date, period):
        window = UPDATE_RULES[PERIOD_MAP[period]]["window_days"]
        unit = {"day": "天", "week": "周", "month": "月"}[period]
        best = _get_latest_date(period)
        print(f"\n⚠️ 抱歉🙏，榜单最多回溯「近{window}{unit}」，已切换至 {best}\n", file=sys.stderr)
        rank_date = str(best)

    limit = min(args.limit, 50)
    # 判断是否查询最新数据（用户未指定具体日期）
    is_latest = parsed.get("is_latest", False)
    items, actual_date, fallback_info = fetch(period, rank_date, category, is_latest=is_latest)
    # 如果实际查询的日期与请求的日期不同，更新 rank_date
    if actual_date != rank_date:
        rank_date = actual_date
    # 如果有回退提示信息，输出给用户
    if fallback_info:
        print(fallback_info)
    total = len(items)
    fetch_time = items[0].get("dataFetchTime", rank_date) if items else rank_date
    period_label = PERIOD_LABELS.get(period, "日榜")

    CAT_DISPLAY = {
        "综合全部": "全品类", "化妆美容": "美妆类", "个人护理": "个护类",
        "美味佳肴": "美食类", "旅行度假": "旅行类", "数码科技": "科技类",
        "医疗保健": "健康类", "亲子育儿": "亲子类", "体育锻炼": "运动类",
        "学习教育": "教育类", "宠物天地": "宠物类", "时尚穿搭": "穿搭类",
        "居家装修": "家居类", "职业发展": "职场类", "影视娱乐": "娱乐类",
        "星座情感": "情感类", "潮流鞋包": "鞋包类", "休闲爱好": "爱好类",
        "科学探索": "科普类", "新闻资讯": "资讯类", "出行代步": "出行类",
        "拍摄记录": "拍摄类", "婚庆婚礼": "婚礼类", "综合杂项": "综合类",
        "日常生活": "日常类",
    }
    cat_display = CAT_DISPLAY.get(category, category + "类")

    # 先在全部数据上计算评分并排序，确保评分一致性
    normalized_all = to_normalized_json(items, period, rank_date, category)
    # 保存 JSON 时使用 limit 截取已排序的数据
    if args.output:
        saved_items = items[:args.limit]
        normalized = to_normalized_json(saved_items, period, rank_date, category)
        normalized["total"] = len(saved_items)
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(normalized, f, ensure_ascii=False, indent=2)
        print(f"[INFO] 已保存：{args.output}", file=sys.stderr)

    if args.format == "json":
        print(json.dumps(items, ensure_ascii=False, indent=2))
    else:
        # Markdown 输出时使用截取后的已评分数据
        display = normalized_all["list"][:limit]
        print(build_markdown_table(display, period_label, rank_date,
                                    cat_display, fetch_time, total, category_fuzzy))
    
    # 生成 HTML 报告文件
    if args.html:
        from generate_report import generate_html
        # 准备数据
        html_data = {
            "list": normalized_all["list"][:limit],
            "total": min(total, limit),
            "period": period,
            "date": rank_date,
            "category": category,
            "fetchTime": fetch_time,
        }
        # 生成文件名：赛道+周期+日期_时间戳
        date_str = rank_date.replace("-", "")
        timestamp = datetime.now().strftime("%H%M%S")
        html_filename = f"小红书{cat_display}{period_label}_{date_str}_{timestamp}.html"
        html_path = Path.cwd() / html_filename
        generate_html(html_data, str(html_path))
        print(f"\n📄 HTML报告已生成：{html_path}")


if __name__ == "__main__":
    main()
