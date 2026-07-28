import argparse
import json
import math
import os
import re
import ssl
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta

# 状态管理文件路径（用于冷却期和失败次数控制）
STATE_FILE = os.path.join(os.path.dirname(__file__), "..", "output", "query_state.json")

# 同步冷却期（秒）
SYNC_COOLDOWN_SECONDS = 15 * 60  # 15分钟
# 失败阈值
FAILURE_THRESHOLD = 3
# 失败记录有效期（秒）
FAILURE_EXPIRE_SECONDS = 6 * 60 * 60  # 6小时


def _load_state():
    """加载状态文件"""
    try:
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {"sync_times": {}, "failures": {}}


def _save_state(state):
    """保存状态文件"""
    try:
        os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _check_sync_cooldown(red_id):
    """检查sync冷却期
    
    Returns:
        (is_in_cooldown, remaining_minutes)
    """
    state = _load_state()
    sync_times = state.get("sync_times", {})
    
    red_id_str = str(red_id)
    if red_id_str in sync_times:
        last_sync = sync_times[red_id_str]
        if isinstance(last_sync, (int, float)):
            elapsed = time.time() - last_sync
            if elapsed < SYNC_COOLDOWN_SECONDS:
                remaining_minutes = int((SYNC_COOLDOWN_SECONDS - elapsed) / 60) + 1
                return True, remaining_minutes
    return False, 0


def _record_sync(red_id):
    """记录sync时间"""
    state = _load_state()
    if "sync_times" not in state:
        state["sync_times"] = {}
    state["sync_times"][str(red_id)] = time.time()
    _save_state(state)


def _get_failure_count(user_id):
    """获取失败次数"""
    state = _load_state()
    failures = state.get("failures", {})
    
    user_id_str = str(user_id)
    if user_id_str not in failures:
        return 0
    
    # 过滤过期的失败记录
    valid_failures = []
    for fail_time in failures[user_id_str]:
        if isinstance(fail_time, (int, float)):
            if time.time() - fail_time < FAILURE_EXPIRE_SECONDS:
                valid_failures.append(fail_time)
    
    return len(valid_failures)


def _record_failure(user_id):
    """记录失败"""
    state = _load_state()
    if "failures" not in state:
        state["failures"] = {}
    
    user_id_str = str(user_id)
    if user_id_str not in state["failures"]:
        state["failures"][user_id_str] = []
    
    state["failures"][user_id_str].append(time.time())
    
    # 清理过期的失败记录
    valid_failures = [t for t in state["failures"][user_id_str] 
                      if time.time() - t < FAILURE_EXPIRE_SECONDS]
    state["failures"][user_id_str] = valid_failures
    
    _save_state(state)


def _clear_failures(user_id):
    """清除失败记录（查询成功时调用）"""
    state = _load_state()
    if "failures" in state and str(user_id) in state["failures"]:
        del state["failures"][str(user_id)]
        _save_state(state)

# 导入HTML检查模块和生成模块
try:
    from html_checker import check_and_fix_html_content, check_multi_html_content
    from html_generator import (
        generate_single_report_html,
        generate_multi_report_html,
        REPORT_DATA_FILE,
        MULTI_REPORT_DATA_FILE,
    )
except ImportError:
    # 兼容直接运行时的导入
    import importlib.util
    script_dir = os.path.dirname(__file__)
    
    spec_checker = importlib.util.spec_from_file_location("html_checker", os.path.join(script_dir, "html_checker.py"))
    html_checker = importlib.util.module_from_spec(spec_checker)
    spec_checker.loader.exec_module(html_checker)
    check_and_fix_html_content = html_checker.check_and_fix_html_content
    check_multi_html_content = html_checker.check_multi_html_content
    
    spec_generator = importlib.util.spec_from_file_location("html_generator", os.path.join(script_dir, "html_generator.py"))
    html_generator = importlib.util.module_from_spec(spec_generator)
    spec_generator.loader.exec_module(html_generator)
    generate_single_report_html = html_generator.generate_single_report_html
    generate_multi_report_html = html_generator.generate_multi_report_html
    REPORT_DATA_FILE = html_generator.REPORT_DATA_FILE
    MULTI_REPORT_DATA_FILE = html_generator.MULTI_REPORT_DATA_FILE


API_BASE_URL = "https://redfox.hk/story/api/xhsUser/query"
RAW_DATA_FILE = "raw_data.json"


def _get_api_key():
    """从当前环境变量获取 REDFOX_API_KEY"""
    api_key = os.environ.get("REDFOX_API_KEY", "")
    if not api_key:
        raise SystemExit("❌ 未找到 REDFOX_API_KEY，请配置环境变量：export REDFOX_API_KEY=<你的apikey>")
    return api_key


def _native_post(url, body, timeout=30):
    """原生urllib POST请求（不验证SSL证书）

    Args:
        url: 请求地址
        body: JSON body字典
        timeout: 超时时间（秒）

    Returns:
        dict: 解析后的JSON响应
    """
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "X-API-KEY": _get_api_key(),
    }

    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
        return json.loads(resp.read().decode("utf-8"))


def api_query(user_ids, source="小红书账号诊断-GitHub"):
    """调用API查询账号数据

    Args:
        user_ids: 小红书账号ID列表
        source: 来源标识

    Returns:
        API响应数据
    """
    body = {"userIds": user_ids, "source": source}
    return _native_post(API_BASE_URL, body)


def _map_user_attribute(raw):
    """映射账号标识"""
    mapping = {
        "明星": "明星",
        "品牌": "品牌/企业",
        "企业": "品牌/企业",
        "头部kol": "头部KOL",
        "头部KOL": "头部KOL",
        "腰部kol": "腰部KOL",
        "腰部KOL": "腰部KOL",
        "尾部kol": "尾部KOL",
        "尾部KOL": "尾部KOL",
        "素人": "素人",
    }
    return mapping.get(raw, raw or "素人")


def _get_viral_threshold(account_tag):
    """根据账号标识获取爆文标准"""
    thresholds = {
        "素人": 1000,
        "尾部KOL": 5000,
        "腰部KOL": 10000,
        "头部KOL": 20000,
        "明星": 20000,
        "品牌/企业": 1000,
    }
    return thresholds.get(account_tag, 1000)


# 粉丝区间与账号标识的映射
FANS_TYPE_MAP = {
    "0-5K": "素人",
    "5K-5w": "尾部KOL",
    "5w-50w": "腰部KOL",
    ">50w": "头部KOL",
}


def _get_fans_type(fans):
    """根据粉丝数确定粉丝区间"""
    if fans < 5000:
        return "0-5K"
    elif fans < 50000:
        return "5K-5w"
    elif fans < 500000:
        return "5w-50w"
    else:
        return ">50w"


def _extract_benchmark_from_api(raw):
    """从接口数据中提取水平衡量基准数据
    
    Args:
        raw: 接口返回的原始数据，包含 accountAvgList 和 accountExcellentList
        
    Returns:
        tuple: (benchmark字典, fans_type, account_tag)
    """
    fans = raw.get("fans", 0)
    fans_type = _get_fans_type(fans)
    account_tag = raw.get("accountTag", "") or FANS_TYPE_MAP.get(fans_type, "素人")
    
    avg_list = raw.get("accountAvgList", []) or []
    excellent_list = raw.get("accountExcellentList", []) or []
    
    # 构建中位数参考字典
    avg_dict = {}
    for item in avg_list:
        if item.get("fansType") == fans_type:
            name = item.get("name", "")
            value = item.get("value", 0)
            avg_dict[name] = float(value) if value else 0
    
    # 构建优秀值参考字典
    excellent_dict = {}
    for item in excellent_list:
        if item.get("fansType") == fans_type:
            name = item.get("name", "")
            value = item.get("value", 0)
            excellent_dict[name] = float(value) if value else 0
    
    # 获取兜底基准数据
    fallback_benchmark = BENCHMARK_DATA.get(account_tag, BENCHMARK_DATA.get("素人", {}))
    
    # 映射到水平衡量指标
    benchmark = {
        "近30天作品互动量": {
            "中位数参考": avg_dict.get("近30天作品互动量均值", 0),
            "优秀值参考": excellent_dict.get("近30天作品互动量均值", 0),
        },
        "近30天发作品数": {
            "中位数参考": avg_dict.get("近30天发作品数均值", 0),
            "优秀值参考": excellent_dict.get("近30天发作品数均值", 0),
        },
        "总点赞数": {
            "中位数参考": avg_dict.get("总点赞数均值", 0),
            "优秀值参考": excellent_dict.get("总点赞数均值", 0),
        },
        "总收藏数": {
            "中位数参考": avg_dict.get("总收藏数均值", 0),
            "优秀值参考": excellent_dict.get("总收藏数均值", 0),
        },
        "作品总数": {
            "中位数参考": avg_dict.get("作品总数均值", 0),
            "优秀值参考": excellent_dict.get("作品总数均值", 0),
        },
        "周更频率": {
            "中位数参考": avg_dict.get("近30天发作品数均值", 0) / 4.0 if avg_dict.get("近30天发作品数均值", 0) else 2.0,
            "优秀值参考": excellent_dict.get("近30天发作品数均值", 0) / 4.0 if excellent_dict.get("近30天发作品数均值", 0) else 5.0,
        },
    }
    
    # 计算互动率和收藏率（基于接口返回的点赞数、收藏数、粉丝数）
    # 互动率 = (点赞数 + 收藏数) / 粉丝数 * 100%
    # 收藏率 = 收藏数 / 点赞数 * 100%
    
    # 获取中位数参考的点赞数、收藏数、粉丝数
    avg_like = avg_dict.get("总点赞数均值", 0)
    avg_collect = avg_dict.get("总收藏数均值", 0)
    avg_fans = avg_dict.get("粉丝数均值", fans)  # 如果没有粉丝数均值，使用当前账号粉丝数
    
    # 获取优秀值参考的点赞数、收藏数、粉丝数
    excellent_like = excellent_dict.get("总点赞数均值", 0)
    excellent_collect = excellent_dict.get("总收藏数均值", 0)
    excellent_fans = excellent_dict.get("粉丝数均值", fans)  # 如果没有粉丝数均值，使用当前账号粉丝数
    
    # 计算互动率中位数参考和优秀值参考
    interaction_rate_avg = round((avg_like + avg_collect) / avg_fans * 100, 2) if avg_fans > 0 else 0.5
    interaction_rate_excellent = round((excellent_like + excellent_collect) / excellent_fans * 100, 2) if excellent_fans > 0 else 1.5
    
    # 计算收藏率中位数参考和优秀值参考
    collect_rate_avg = round(avg_collect / avg_like * 100, 2) if avg_like > 0 else 8.0
    collect_rate_excellent = round(excellent_collect / excellent_like * 100, 2) if excellent_like > 0 else 15.0
    
    benchmark["互动率"] = {
        "中位数参考": interaction_rate_avg,
        "优秀值参考": interaction_rate_excellent,
    }
    benchmark["收藏率"] = {
        "中位数参考": collect_rate_avg,
        "优秀值参考": collect_rate_excellent,
    }
    
    return benchmark, fans_type, account_tag


# 水衡量基准数据（按账号标识分类，作为兜底默认值）
# 基于Excel数据"中位值和优秀值.xlsx"更新的基准数据
# 数据结构：每个粉丝区间包含中位数和优秀值两行数据
BENCHMARK_DATA = {
    "素人": {  # 0-5k粉丝
        "近30天作品互动量": {"中位数参考": 71.65, "优秀值参考": 38878.00},
        "近30天发作品数": {"中位数参考": 3.00, "优秀值参考": 12.00},
        "总点赞数": {"中位数参考": 362.61, "优秀值参考": 31087.00},
        "总收藏数": {"中位数参考": 117.75, "优秀值参考": 7368.00},
        "作品总数": {"中位数参考": 16.73, "优秀值参考": 23.00},
        "互动率": {"中位数参考": 0.5, "优秀值参考": 2.0},  # 估算值
        "收藏率": {"中位数参考": 8.0, "优秀值参考": 25.0},  # 估算值
        "周更频率": {"中位数参考": 0.75, "优秀值参考": 3.0},  # 近30天/4
    },
    "尾部KOL": {  # 5k-5w粉丝
        "近30天作品互动量": {"中位数参考": 483.50, "优秀值参考": 124263.00},
        "近30天发作品数": {"中位数参考": 6.00, "优秀值参考": 24.00},
        "总点赞数": {"中位数参考": 41604.23, "优秀值参考": 329082.00},
        "总收藏数": {"中位数参考": 16201.18, "优秀值参考": 82391.50},
        "作品总数": {"中位数参考": 120.30, "优秀值参考": 136.50},
        "互动率": {"中位数参考": 1.0, "优秀值参考": 3.5},  # 估算值
        "收藏率": {"中位数参考": 12.0, "优秀值参考": 28.0},  # 估算值
        "周更频率": {"中位数参考": 1.5, "优秀值参考": 6.0},  # 近30天/4
    },
    "腰部KOL": {  # 5w-50w粉丝
        "近30天作品互动量": {"中位数参考": 3797.60, "优秀值参考": 254721.50},
        "近30天发作品数": {"中位数参考": 7.00, "优秀值参考": 19.00},
        "总点赞数": {"中位数参考": 398278.10, "优秀值参考": 2381874.00},
        "总收藏数": {"中位数参考": 148994.22, "优秀值参考": 481938.50},
        "作品总数": {"中位数参考": 245.56, "优秀值参考": 284.50},
        "互动率": {"中位数参考": 1.2, "优秀值参考": 4.0},  # 估算值
        "收藏率": {"中位数参考": 15.0, "优秀值参考": 30.0},  # 估算值
        "周更频率": {"中位数参考": 1.75, "优秀值参考": 4.75},  # 近30天/4
    },
    "头部KOL": {  # 大于50w粉丝
        "近30天作品互动量": {"中位数参考": 33700.54, "优秀值参考": 251250.50},
        "近30天发作品数": {"中位数参考": 7.00, "优秀值参考": 12.00},
        "总点赞数": {"中位数参考": 4371187.20, "优秀值参考": 7763569.00},
        "总收藏数": {"中位数参考": 1295796.82, "优秀值参考": 1654083.00},
        "作品总数": {"中位数参考": 428.73, "优秀值参考": 485.50},
        "互动率": {"中位数参考": 1.5, "优秀值参考": 5.0},  # 估算值
        "收藏率": {"中位数参考": 18.0, "优秀值参考": 35.0},  # 估算值
        "周更频率": {"中位数参考": 1.75, "优秀值参考": 3.0},  # 近30天/4
    },
    "明星": {  # 与头部KOL相近
        "近30天作品互动量": {"中位数参考": 33700.54, "优秀值参考": 251250.50},
        "近30天发作品数": {"中位数参考": 7.00, "优秀值参考": 12.00},
        "总点赞数": {"中位数参考": 4371187.20, "优秀值参考": 7763569.00},
        "总收藏数": {"中位数参考": 1295796.82, "优秀值参考": 1654083.00},
        "作品总数": {"中位数参考": 428.73, "优秀值参考": 485.50},
        "互动率": {"中位数参考": 2.0, "优秀值参考": 8.0},
        "收藏率": {"中位数参考": 20.0, "优秀值参考": 40.0},
        "周更频率": {"中位数参考": 1.75, "优秀值参考": 3.0},
    },
    "品牌/企业": {  # 与尾部KOL相近
        "近30天作品互动量": {"中位数参考": 483.50, "优秀值参考": 124263.00},
        "近30天发作品数": {"中位数参考": 6.00, "优秀值参考": 24.00},
        "总点赞数": {"中位数参考": 41604.23, "优秀值参考": 329082.00},
        "总收藏数": {"中位数参考": 16201.18, "优秀值参考": 82391.50},
        "作品总数": {"中位数参考": 120.30, "优秀值参考": 136.50},
        "互动率": {"中位数参考": 0.5, "优秀值参考": 1.5},
        "收藏率": {"中位数参考": 8.0, "优秀值参考": 15.0},
        "周更频率": {"中位数参考": 1.5, "优秀值参考": 6.0},
    },
}


def _calc_coefficient_of_variation(works):
    """计算离散系数（衡量稳定性），基于近7天作品的互动量（点赞+收藏）"""
    if not works or len(works) < 2:
        return None
    
    interactions = []
    for w in works:
        like_count = w.get("likedCount") or 0
        collect_count = w.get("collectedCount") or 0
        total_interaction = like_count + collect_count
        interactions.append(total_interaction)
    
    if not interactions:
        return None
    
    mean_val = sum(interactions) / len(interactions)
    if mean_val == 0:
        return None
    
    variance = sum((x - mean_val) ** 2 for x in interactions) / len(interactions)
    std_dev = math.sqrt(variance)
    cv = std_dev / mean_val
    
    return round(cv, 2)


def _calc_decay_ratio(works, viral_threshold):
    """计算爆文后衰减比（承接比），互动=点赞+收藏"""
    if not works or len(works) < 2:
        return None
    
    # 找到第一个爆文（互动数 = 点赞 + 收藏）
    viral_index = None
    for i, w in enumerate(works):
        like_count = w.get("likedCount") or 0
        collect_count = w.get("collectedCount") or 0
        total_inter = like_count + collect_count
        if total_inter > viral_threshold:
            viral_index = i
            break
    
    if viral_index is None or viral_index >= len(works) - 1:
        return None
    
    # 计算爆文互动量
    viral_work = works[viral_index]
    viral_like = viral_work.get("likedCount") or 0
    viral_collect = viral_work.get("collectedCount") or 0
    viral_interaction = viral_like + viral_collect
    
    if viral_interaction == 0:
        return None
    
    # 计算爆文后3篇均值互动量
    next_works = works[viral_index + 1: viral_index + 4]
    if not next_works:
        return None
    
    next_total = 0
    for nw in next_works:
        next_total += (nw.get("likedCount") or 0) + (nw.get("collectedCount") or 0)
    next_avg = next_total / len(next_works)
    
    # 承接比 = 爆文后3篇均值 / 爆文互动量 * 100%
    carry_ratio = next_avg / viral_interaction * 100
    return round(carry_ratio, 2)


def _calc_interaction_structure(works):
    """计算互动结构（点赞/收藏占比，接口无分享字段）"""
    if not works:
        return None, None
    
    total_like = 0
    total_collect = 0
    
    for w in works:
        total_like += w.get("likedCount") or 0
        total_collect += w.get("collectedCount") or 0
    
    total = total_like + total_collect
    if total == 0:
        return None, None
    
    like_pct = round(total_like / total * 100, 1)
    collect_pct = round(total_collect / total * 100, 1)
    
    return like_pct, collect_pct


def _calc_interaction_rate(works, fans):
    """计算互动率（近7天总互动(点赞+收藏) / 粉丝数 * 100%）"""
    if not works or fans == 0:
        return None
    
    total_interaction = 0
    for w in works:
        like_count = w.get("likedCount") or 0
        collect_count = w.get("collectedCount") or 0
        total_interaction += like_count + collect_count
    
    interaction_rate = total_interaction / fans * 100
    return round(interaction_rate, 2)


def _calc_viral_magnification(works, viral_threshold):
    """计算爆文放大倍数，互动=点赞+收藏"""
    if not works:
        return None
    
    viral_interactions = []
    non_viral_interactions = []
    
    for w in works:
        like_count = w.get("likedCount") or 0
        collect_count = w.get("collectedCount") or 0
        total = like_count + collect_count
        
        # 爆文判断：互动数 = 点赞 + 收藏
        if total > viral_threshold:
            viral_interactions.append(total)
        else:
            non_viral_interactions.append(total)
    
    if not viral_interactions or not non_viral_interactions:
        return None
    
    viral_avg = sum(viral_interactions) / len(viral_interactions)
    non_viral_avg = sum(non_viral_interactions) / len(non_viral_interactions)
    
    if non_viral_avg == 0:
        return None
    
    return round(viral_avg / non_viral_avg, 0)


def _get_level_judgment(value, benchmark, is_lower_better=False):
    """根据基准值判断等级
    
    基准数据结构：
    - 中位数参考：同层级账号中位数
    - 优秀值参考：同层级账号优秀值
    """
    if value is None:
        return "数据不足"
    
    median_val = benchmark.get("中位数参考", 0)
    excellent_val = benchmark.get("优秀值参考", 0)
    
    if is_lower_better:
        # 数值越低越好（如间隔标准差）
        if value <= excellent_val:
            return "优秀"
        elif value <= median_val:
            return "良好"
        else:
            return "待提升"
    else:
        # 数值越高越好（如互动率、收藏率）
        if value >= excellent_val:
            return "优秀"
        elif value >= median_val:
            return "良好"
        else:
            return "待提升"


def _format_fans_count(fans):
    """粉丝数格式化，>=10000转w+，<10000直接展示原值"""
    if fans >= 10000:
        w_val = fans / 10000
        if w_val == int(w_val):
            return f"{int(w_val)}w+"
        return f"{round(w_val, 1)}w+"
    else:
        return str(fans)


def _format_interactive_count(count):
    """互动量格式化，>=10000转w+，<10000直接展示原值"""
    try:
        count = int(count)
    except (ValueError, TypeError):
        return str(count)
    if count >= 10000:
        w_val = count / 10000
        if w_val == int(w_val):
            return f"{int(w_val)}w+"
        return f"{round(w_val, 1)}w+"
    else:
        return str(count)


def _score_interactive_scale(interactive_count, collect_count, benchmark=None):
    """互动规模评分（满分20），基于互动量和收藏量
    
    互动量维度：10分（>优秀值10分，>中位数6分，其他1分）
    收藏量维度：10分（>优秀值10分，>中位数6分，其他1分）
    """
    score = 0
    
    # 从benchmark获取中位数和优秀值
    median_interactive = 1000  # 默认中位数
    excellent_interactive = 10000  # 默认优秀值
    median_collect = 100  # 默认中位数
    excellent_collect = 1000  # 默认优秀值
    
    if benchmark:
        if "近30天作品互动量" in benchmark:
            median_interactive = benchmark["近30天作品互动量"].get("中位数参考", 1000)
            excellent_interactive = benchmark["近30天作品互动量"].get("优秀值参考", 10000)
        if "总收藏数" in benchmark:
            median_collect = benchmark["总收藏数"].get("中位数参考", 100)
            excellent_collect = benchmark["总收藏数"].get("优秀值参考", 1000)
    
    # 互动量维度（10分）
    if interactive_count > excellent_interactive:
        score += 10
    elif interactive_count > median_interactive:
        score += 6
    else:
        score += 1
    
    # 收藏量维度（10分）
    if collect_count > excellent_collect:
        score += 10
    elif collect_count > median_collect:
        score += 6
    else:
        score += 1
    
    return score


def _score_update_rhythm(weekly_count, fans=0):
    """更新产能评分（满分15分）- 基于周更频率和粉丝数
    
    参考Excel数据中的近30天发作品数中位数和优秀值：
    - 0-5k: 中位数3篇，优秀值12篇 → 周更0.75篇/3篇
    - 5k-5w: 中位数6篇，优秀值24篇 → 周更1.5篇/6篇
    - 5w-50w: 中位数7篇，优秀值19篇 → 周更1.75篇/4.75篇
    - >50w: 中位数7篇，优秀值12篇 → 周更1.75篇/3篇
    """
    # 粉丝数>5000的账号基础分更高
    if fans > 50000:
        base_score = 10  # 头部账号
    elif fans > 10000:
        base_score = 9  # 中腰部账号
    elif fans > 5000:
        base_score = 8  # 尾部账号
    else:
        base_score = 5  # 素人账号
    
    if weekly_count >= 5:
        return min(base_score + 5, 15)
    elif weekly_count >= 4:
        return min(base_score + 4, 15)
    elif weekly_count >= 3:
        return min(base_score + 3, 15)
    elif weekly_count >= 2:
        return min(base_score + 2, 15)
    elif weekly_count >= 1:
        return min(base_score + 1, 15)
    else:
        return min(base_score, 15)


def _score_viral(viral_rate, interaction_30d, fans):
    """爆文能力评分（满分15），基于爆文率和近30天互动量评估
    
    爆文率：10分
    近30天互动量评估：5分
    """
    score = 0
    # 爆文率（10分）：爆文数/近7天发作品数*100%
    if viral_rate >= 30:  # 爆文率>=30%
        score += 10
    elif viral_rate >= 20:  # 爆文率>=20%
        score += 8
    elif viral_rate >= 10:  # 爆文率>=10%
        score += 6
    elif viral_rate >= 5:  # 爆文率>=5%
        score += 4
    elif viral_rate > 0:  # 有爆文但爆文率<5%
        score += 2
    else:  # 无爆文
        score += 1
    
    # 近30天互动量评估（5分）：基于互动量/粉丝数的比值
    if interaction_30d and fans and fans > 0:
        interaction_ratio = interaction_30d / fans
        if interaction_ratio >= 1.0:  # 互动量>=粉丝数，极强
            score += 5
        elif interaction_ratio >= 0.5:  # 互动量>=粉丝数50%，强
            score += 4
        elif interaction_ratio >= 0.2:  # 互动量>=粉丝数20%，良好
            score += 3
        elif interaction_ratio >= 0.1:  # 互动量>=粉丝数10%，一般
            score += 2
        else:  # 互动量<粉丝数10%，较弱
            score += 1
    return min(score, 15)


def _score_positioning(works, account_tag, signature, fans=0):
    """账号定位评分（满分10）
    
    对粉丝数>5000的账号以夸赞为主，评分更宽松
    """
    # 粉丝数>5000的账号基础分更高，以夸赞为主
    if fans > 50000:
        score = 8  # 头部账号，基础分高
    elif fans > 10000:
        score = 7  # 中腰部账号，基础分较高
    elif fans > 5000:
        score = 6  # 尾部账号，基础分适中
    else:
        score = 5  # 素人账号，基础分正常
    
    # 简介完整度
    if signature and len(signature.strip()) > 5:
        score += 1
    # 内容垂直度
    if works:
        tags = []
        for w in works:
            desc = w.get("desc") or ""
            if desc:
                tags.extend([t.strip() for t in desc.split("#") if t.strip()])
        unique_tags = set(tags)
        if len(unique_tags) <= 5:
            score += 1  # 对粉丝数>5000的账号，垂直度要求放宽
    return min(score, 10)


def _get_viral_magnification_judgment(viral_avg, non_viral_avg):
    """判断爆文放大倍数是否健康"""
    if non_viral_avg == 0 or viral_avg == 0:
        return "数据不足"
    magnification = viral_avg / non_viral_avg
    if magnification > 100:
        return "极不健康（无中间态，只有爆文和完全沉默）"
    elif magnification > 50:
        return "不健康（内容质量波动大）"
    elif magnification > 20:
        return "一般（有提升空间）"
    else:
        return "健康（内容质量稳定）"


def _score_fans_insight(collect_rate, fans_gender, works, fans):
    """粉丝画像与需求评分（满分15），含粉丝数评估"""
    score = 5  # 基础分
    # 收藏率评估（3分）
    if collect_rate and collect_rate > 30:
        score += 3
    elif collect_rate and collect_rate > 20:
        score += 2
    elif collect_rate and collect_rate > 10:
        score += 1
    # 粉丝画像集中度（3分）
    if fans_gender and isinstance(fans_gender, dict):
        female_ratio = fans_gender.get("female_ratio", 0)
        if female_ratio > 0.7 or female_ratio < 0.3:
            score += 3
        elif female_ratio > 0.6 or female_ratio < 0.4:
            score += 2
        else:
            score += 1
    # 粉丝数规模评估（4分）
    if fans >= 100000:
        score += 4
    elif fans >= 50000:
        score += 3
    elif fans >= 10000:
        score += 2
    elif fans >= 5000:
        score += 1
    return min(score, 15)


def _score_topic_system(works, fans=0):
    """选题体系评分（满分15）
    
    核心逻辑：选题方向单一/聚焦是加分项，专注某一赛道深耕是好的
    - 有固定选题方向：加分
    - 有固定栏目/标签：加分
    - 选题一致性高：加分
    
    对粉丝数>5000的账号评分更宽松
    """
    if not works:
        return 5 if fans > 5000 else 3
    
    # 粉丝数>5000的账号基础分更高
    if fans > 50000:
        score = 10  # 头部账号，基础分高
    elif fans > 10000:
        score = 9  # 中腰部账号，基础分较高
    elif fans > 5000:
        score = 8  # 尾部账号，基础分适中
    else:
        score = 6  # 素人账号，基础分正常
    
    titles = [w.get("title", "") for w in works if w.get("title")]
    
    # 选题方向聚焦/单一：加分项（专注赛道深耕是好事）
    unique_titles = set(titles[:5])
    if len(unique_titles) <= 2:  # 选题高度聚焦
        score += 4
    elif len(unique_titles) <= 3:  # 选题较为聚焦
        score += 3
    elif len(unique_titles) <= 4:  # 选题有一定聚焦
        score += 2
    
    # 有固定栏目/标签：加分项
    tags = []
    for w in works:
        desc = w.get("desc") or ""
        if desc:
            tags.extend([t.strip() for t in desc.split("#") if t.strip()])
    unique_tags = set(tags)
    if unique_tags:
        if len(unique_tags) <= 3:  # 标签高度统一
            score += 3
        elif len(unique_tags) <= 5:  # 标签较为统一
            score += 2
        else:
            score += 1
    
    return min(score, 15)


def _score_cover_style(works, fans=0):
    """封面风格评分（满分10）
    
    封面统一或多样只是风格的一种，不作为评分标准
    主要基于：有封面、有作品、粉丝数规模
    对粉丝数>5000的账号以夸赞为主，评分更宽松
    """
    if not works:
        # 粉丝数>5000的账号即使没有作品也给更高基础分
        return 5 if fans > 5000 else 2
    
    # 粉丝数>5000的账号基础分更高，以夸赞为主
    if fans > 50000:
        score = 9  # 头部账号，基础分高
    elif fans > 10000:
        score = 8  # 中腰部账号，基础分较高
    elif fans > 5000:
        score = 7  # 尾部账号，基础分适中
    else:
        score = 5  # 素人账号，基础分正常
    
    # 有封面图加分
    covers = [w.get("coverUrl") or w.get("thumbUrl") for w in works]
    valid_covers = [c for c in covers if c]
    if valid_covers:
        score += 1
    
    return min(score, 10)


def _format_gender(fans_gender):
    """格式化粉丝性别比例"""
    if not fans_gender or not isinstance(fans_gender, dict):
        return ""
    male = float(fans_gender.get("male_ratio", 0))
    female = float(fans_gender.get("female_ratio", 0))
    female_pct = round(female * 100)
    male_pct = round(male * 100)
    return f"女性{female_pct}% / 男性{male_pct}%"


def _analyze_single_account(raw, has_works=True):
    """对单个账号原始数据进行评分和结构化处理
    
    Args:
        raw: 原始账号数据
        has_works: 是否有作品数据，False时跳过作品相关分析
    """
    # 无作品确认提示（有账号但无作品时）
    no_works_hint = "" if has_works else "检测到该账号近30天无作品数据。请确认：该账号近30天是否真的无作品？\n1.该账号近30天确实无作品，直接分析\n2.该账号近30天有作品，需要实时获取最新作品（大概需要30分钟，自动推送诊断报告）"
    
    fans = raw.get("fans", 0)
    nickname = raw.get("nickname", "")
    level = raw.get("level") or ""
    account_tag_raw = raw.get("userAttribute", "素人")
    account_tag = _map_user_attribute(account_tag_raw)
    total_work = raw.get("totalWork", 0)
    liked = raw.get("liked", 0)
    collected = raw.get("collected", 0)
    note_count_thirty = raw.get("noteCountThirty", 0)
    interactive_thirty = raw.get("interactiveCountThirty", 0)
    top_provinces = raw.get("topProvinces", "")
    top_ages = raw.get("topAges", "")
    fans_gender = raw.get("fansGender", {})
    works = raw.get("works", []) or []
    similar_accounts = raw.get("similarAccounts", []) or []
    red_id = raw.get("redId", "")
    avatar = raw.get("avatarUrl") or raw.get("avatar", "")
    gmt_create = raw.get("gmtCreate", "")
    signature = raw.get("signature", "")

    # 空值保护
    fans = fans if fans is not None else 0
    liked = liked if liked is not None else 0
    collected = collected if collected is not None else 0
    note_count_thirty = note_count_thirty if note_count_thirty is not None else 0
    interactive_thirty = interactive_thirty if interactive_thirty is not None else 0

    # 计算各项指标
    viral_threshold = _get_viral_threshold(account_tag)
    if has_works and works:
        # 爆文判断：互动数 = 点赞 + 收藏
        viral_count = sum(1 for w in works if ((w.get("likedCount") or 0) + (w.get("collectedCount") or 0)) > viral_threshold)
        viral_rate = round(viral_count / len(works) * 100, 1) if works else 0
        coefficient_of_variation = _calc_coefficient_of_variation(works)
        decay_ratio = _calc_decay_ratio(works, viral_threshold)
        like_pct, collect_pct = _calc_interaction_structure(works)
    else:
        viral_count = 0
        viral_rate = 0
        coefficient_of_variation = 0
        decay_ratio = 0
        like_pct, collect_pct = 0, 0
    
    avg_interaction = round(interactive_thirty / note_count_thirty, 1) if note_count_thirty > 0 else 0
    collect_rate = round(collected / liked * 100, 1) if liked > 0 else 0
    weekly_count = round(note_count_thirty / 4.3, 1)
    
    # 互动率计算：使用接口直接返回的近30天互动量
    interaction_rate = round(interactive_thirty / fans * 100, 2) if fans > 0 else 0
    
    # 获取水平衡量基准（优先使用接口数据，兜底使用默认值）
    api_benchmark, api_fans_type, api_account_tag = _extract_benchmark_from_api(raw)
    default_benchmark = BENCHMARK_DATA.get(account_tag, BENCHMARK_DATA["素人"])
    # 合并：接口数据优先，缺失时使用默认值
    benchmark = {}
    for key in default_benchmark:
        if key in api_benchmark and api_benchmark[key].get("中位数参考"):
            benchmark[key] = api_benchmark[key]
        else:
            benchmark[key] = default_benchmark[key]
    
    # 计算近7天作品平均互动数（用于爆文能力评分）
    # 近7天作品：按发布时间筛选
    from datetime import datetime, timedelta
    now = datetime.now()
    seven_days_ago = now - timedelta(days=7)
    works_7d = []
    for w in works:
        publish_time = w.get("publishTime", "")
        if publish_time:
            try:
                # 假设时间格式为 "2024-01-01" 或类似
                pub_dt = datetime.strptime(publish_time[:10], "%Y-%m-%d")
                if pub_dt >= seven_days_ago:
                    works_7d.append(w)
            except:
                pass
    if not works_7d:
        works_7d = works  # 如果无法筛选，使用全部作品
    
    avg_interaction_7d = 0
    if works_7d:
        total_7d = sum((w.get("likedCount") or 0) + (w.get("collectedCount") or 0) for w in works_7d)
        avg_interaction_7d = round(total_7d / len(works_7d), 1) if works_7d else 0
    
    # 七维度评分（总分100）
    # 满分分配：账号定位10 + 粉丝画像与需求15 + 选题体系15 + 封面风格10 + 爆文能力15 + 互动规模20 + 更新产能15 = 100
    score_positioning = _score_positioning(works, account_tag, signature, fans)
    score_fans_insight = _score_fans_insight(collect_rate, fans_gender, works, fans)
    score_topic_system = _score_topic_system(works, fans)
    score_cover_style = _score_cover_style(works, fans)
    score_viral = _score_viral(viral_rate, interactive_thirty, fans)
    score_interactive = _score_interactive_scale(interactive_thirty, collected, benchmark)
    score_update = _score_update_rhythm(weekly_count, fans)
    total_score = (score_positioning + score_fans_insight + score_topic_system + 
                   score_cover_style + score_viral + score_interactive + score_update)

    # 规则：粉丝数>5000的账号，评分必须>60分
    # 通过提升各维度最低分来确保总评分达标
    if fans > 5000 and total_score < 61:
        # 计算需要提升的分数
        needed = 61 - total_score
        # 按比例提升各维度分数（确保每维度至少得满分的一半）
        if score_positioning < 5:
            score_positioning = 5
        if score_fans_insight < 8:
            score_fans_insight = 8
        if score_topic_system < 8:
            score_topic_system = 8
        if score_cover_style < 5:
            score_cover_style = 5
        if score_viral < 8:
            score_viral = 8
        if score_interactive < 10:
            score_interactive = 10
        if score_update < 8:
            score_update = 8
        # 重新计算总分
        total_score = (score_positioning + score_fans_insight + score_topic_system + 
                       score_cover_style + score_viral + score_interactive + score_update)

    # 评分一致性检查：确保七维度评分之和等于总分
    score_sum = score_positioning + score_fans_insight + score_topic_system + score_cover_style + score_viral + score_interactive + score_update
    if score_sum != total_score:
        total_score = score_sum  # 以七维度评分之和为准

    # 水平衡量：使用互动数均值和收藏数均值，不用率
    interaction_avg_level = _get_level_judgment(interactive_thirty, benchmark["近30天作品互动量"]) if interactive_thirty else "数据不足"
    collect_avg_level = _get_level_judgment(collected, benchmark["总收藏数"]) if collected else "数据不足"
    
    # 爆文列表（含超标准倍数）
    viral_list = []
    viral_interactions = []
    non_viral_interactions = []
    for w in works:
        like_count = w.get("likedCount") or 0
        collect_count = w.get("collectedCount") or 0
        total_inter = like_count + collect_count
        title = (w.get("title") or "无标题")[:30]
        date_str = ""
        ts = w.get("time") or w.get("timestamp") or w.get("createTime")
        if ts:
            try:
                if isinstance(ts, (int, float)):
                    if ts > 1e12:
                        ts = ts / 1000
                    date_str = datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
                else:
                    date_str = str(ts)[:10]
            except (ValueError, OSError):
                date_str = ""
        
        # 爆文判断：互动数 = 点赞 + 收藏
        if total_inter > viral_threshold:
            magnification = round(total_inter / viral_threshold, 1) if viral_threshold else 0
            viral_list.append({
                "标题": title,
                "发布时间": date_str,
                "互动数": _format_interactive_count(total_inter),
                "超标准倍数": f"{magnification}x"
            })
            viral_interactions.append(total_inter)
        else:
            non_viral_interactions.append(total_inter)
    
    # 计算爆文和非爆文的平均互动（用于放大倍数计算）
    viral_avg_raw = round(sum(viral_interactions) / len(viral_interactions)) if viral_interactions else 0
    non_viral_avg_raw = round(sum(non_viral_interactions) / len(non_viral_interactions)) if non_viral_interactions else 0
    non_viral_avg = _format_interactive_count(non_viral_avg_raw)

    # 格式化相似账号
    similar_list = []
    for sa in similar_accounts[:5]:
        account_id = sa.get("accountId") or sa.get("redId") or sa.get("userId", "")
        # 优先使用数据中的url字段，如果没有则使用redId拼接
        profile_url = sa.get("url") or sa.get("profileUrl") or sa.get("homepageUrl") or ""
        if not profile_url and account_id:
            profile_url = f"https://www.xiaohongshu.com/user/profile/{account_id}"
        similar_list.append({
            "accountId": account_id,
            "accountName": sa.get("accountName") or sa.get("nickname") or sa.get("name", ""),
            "profileUrl": profile_url,
            "avatarUrl": sa.get("avatarUrl") or sa.get("avatar") or sa.get("headUrl", ""),
            "followerCount": sa.get("followerCount") or sa.get("fans") or sa.get("fansCount", 0),
            "accountType": sa.get("accountType") or sa.get("trackType", ""),
            "accountSecType": sa.get("accountSecType") or sa.get("subType", ""),
            "signature": sa.get("signature") or sa.get("desc") or sa.get("bio", ""),
            "totalAwemeCount": sa.get("totalAwemeCount") or sa.get("workCount") or sa.get("noteCount") or sa.get("totalWork", 0),
            "totalLikeCount": sa.get("totalLikeCount") or sa.get("likedCount") or sa.get("likeCount") or sa.get("liked", 0),
            "totalCollectedCount": sa.get("totalCollectedCount") or sa.get("collectCount") or sa.get("favCount") or sa.get("collected", 0),
            "totalInteractiveCount": sa.get("interactiveCountThirty") or sa.get("totalInteractiveCount") or sa.get("interactCount", 0),
        })

    result = {
        "header": {
            "账号名": nickname,
            "账号标识": account_tag,
            "数据获取时间": gmt_create,
            "无作品提示": no_works_hint,
        },
        "scores": {
            "综合评分": total_score,
            "账号定位得分": score_positioning,
            "账号定位满分": 10,
            "账号定位简述原因": "",
            "粉丝画像与需求得分": score_fans_insight,
            "粉丝画像与需求满分": 15,
            "粉丝画像与需求简述原因": "",
            "选题体系得分": score_topic_system,
            "选题体系满分": 15,
            "选题体系简述原因": "",
            "封面风格得分": score_cover_style,
            "封面风格满分": 10,
            "封面风格简述原因": "",
            "爆文能力得分": score_viral,
            "爆文能力满分": 15,
            "爆文能力简述原因": "",
            "互动规模得分": score_interactive,
            "互动规模满分": 20,
            "互动规模简述原因": "",
            "更新产能得分": score_update,
            "更新产能满分": 15,
            "更新产能简述原因": "",
            "爆文率": viral_rate,
            "爆文数": viral_count,
            "近7天发作品数": len(works),
            "爆文标准": viral_threshold,
        },
        "conclusion": {
            "综合诊断结论内容": "",
            "可借鉴的优点": "",
            "可成长的地方": "",
        },
        "positioning": {
            "TA是谁": "",
            "心智占位": "",
            "核心身份": "",
            "价值观锚点": "",
            "吸引力类型": "",
            "赛道痛点": "",
            "你的优势": "",
            "可强化": "",
            "显示可强化": score_positioning < 8,  # 账号定位<8分时才显示可强化
        },
        "fans_insight": {
            "粉丝构成": "",
            "核心需求反推": [
                {"画像特征": "", "推断需求": "", "内容匹配度": "", "付费意愿": ""},
                {"画像特征": "", "推断需求": "", "内容匹配度": "", "付费意愿": ""},
                {"画像特征": "", "推断需求": "", "内容匹配度": "", "付费意愿": ""}
            ],
            "收藏率判断": "",
            "内容类型": "",
            "变现路径推断": "",
            "粉丝内容匹配度": "",
            "变现机会": "",
        },
        "topic_system": {
            "选题方向": "",
            "表达风格": "",
            "叙事手法": "",
            "人格一致性": "",
            "选题案例1_标题": works[0].get("title", "")[:20] if works else "",
            "选题案例1_互动数": works[0].get("likes", 0) if works else 0,
            "选题案例1_分析": "",
            "选题案例2_标题": works[1].get("title", "")[:20] if len(works) > 1 else "",
            "选题案例2_互动数": works[1].get("likes", 0) if len(works) > 1 else 0,
            "选题案例2_分析": "",
        },
        "cover_style": {
            "视觉特征": "",
            "信息层级": "",
            "一致性": "",
            "封面案例1_标题": works[0].get("title", "")[:20] if works else "",
            "封面案例1_互动数": works[0].get("likes", 0) if works else 0,
            "封面案例1_分析": "",
            "封面案例2_标题": works[1].get("title", "")[:20] if len(works) > 1 else "",
            "封面案例2_互动数": works[1].get("likes", 0) if len(works) > 1 else 0,
            "封面案例2_分析": "",
        },
        "viral": {
            "爆文率": viral_rate,
            "爆文数": viral_count,
            "爆文标准": viral_threshold,
            "标题规律": "",
            "爆文内容规律": "",
            "情绪特点": "",
            "爆文列表": viral_list,
            "非爆文平均互动": non_viral_avg,
            "爆文放大倍数": round(viral_avg_raw / non_viral_avg_raw, 1) if non_viral_avg_raw > 0 and viral_avg_raw > 0 else 0,
            "爆文放大倍数判断": _get_viral_magnification_judgment(viral_avg_raw, non_viral_avg_raw),
        },
        "interactive_scale": {
            "近30天互动量": _format_interactive_count(interactive_thirty),
            "总收藏数": _format_interactive_count(collected),
            "官方等级": level,
            "互动率": interaction_rate,
            "收藏率": collect_rate,
            "互动结构_点赞占比": like_pct,
            "互动结构_收藏占比": collect_pct,
            "类型判断": "",
            "水平衡量_互动数等级": interaction_avg_level,
            "水平衡量_互动数中位数参考": _format_interactive_count(benchmark["近30天作品互动量"]["中位数参考"]),
            "水平衡量_互动数优秀值参考": _format_interactive_count(benchmark["近30天作品互动量"]["优秀值参考"]),
            "水平衡量_收藏数等级": collect_avg_level,
            "水平衡量_收藏数中位数参考": _format_interactive_count(benchmark["总收藏数"]["中位数参考"]),
            "水平衡量_收藏数优秀值参考": _format_interactive_count(benchmark["总收藏数"]["优秀值参考"]),
        },
        "update_rhythm": {
            "近30天发作品数": note_count_thirty,
            "周更频率": weekly_count,
            "频率分析": "",
            "水平衡量_周更频率等级": _get_level_judgment(weekly_count, benchmark["周更频率"]) if weekly_count else "数据不足",
            "水平衡量_周更频率中位数参考": benchmark["周更频率"]["中位数参考"],
            "水平衡量_周更频率优秀值参考": benchmark["周更频率"]["优秀值参考"],
        },
        "action": {
            "问题归因1": "",
            "问题归因2": "",
            "具体动作1": "",
            "具体动作2": "",
            "具体动作3": "",
            "成功指标周期": "7",
            "成功指标A_指标": "",
            "成功指标A_当前": "",
            "成功指标A_目标": "",
            "成功指标B_指标": "",
            "成功指标B_当前": "",
            "成功指标B_目标": "",
            "未达标兜底": "",
            "可以学": [
                {"策略": "", "来源账号": "", "可复制度": "", "怎么学": ""},
                {"策略": "", "来源账号": "", "可复制度": "", "怎么学": ""},
                {"策略": "", "来源账号": "", "可复制度": "", "怎么学": ""}
            ],
            "反常识发现1": "",
            "反常识发现2": "",
            "30天目标": {
                "粉丝数": {"当前": _format_fans_count(fans), "目标": ""},
                "爆文率": {"当前": f"{viral_rate}%", "目标": ""},
                "互动率": {"当前": f"{interaction_rate}%", "目标": ""},
                "收藏率": {"当前": f"{collect_rate}%", "目标": ""},
                "爆文后承接比": {"当前": f"{decay_ratio}%", "目标": ""},
                "简介完整度": {"当前": "", "目标": "3/3"},
            },
        },
        "works": works[:5],
        "similar_accounts": similar_list,
        "无作品提示": no_works_hint,
        # 原始数据保留，供参考
        "_raw": {
            "redId": red_id,
            "粉丝数原始": fans,
            "近30天互动量原始": interactive_thirty,
            "头像": avatar,
            "简介": signature,
            "粉丝省份": top_provinces,
            "粉丝年龄": top_ages,
            "粉丝性别": fans_gender,
            "作品总数": total_work,
            "总点赞数": liked,
            "总收藏数": collected,
        },
    }


def _save_raw_data(raw_data):
    """将接口原始数据保存到raw_data.json"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, "..", "output")
    output_dir = os.path.normpath(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    raw_path = os.path.join(output_dir, RAW_DATA_FILE)
    with open(raw_path, "w", encoding="utf-8") as f:
        json.dump(raw_data, f, ensure_ascii=False, indent=2)


def cmd_query(user_ids, force_analyze=False):
    """查询命令：调用API获取数据，保存raw_data.json，输出结构化结果
    
    Args:
        user_ids: 小红书账号ID列表
        force_analyze: 是否强制分析（订阅推送时为True，即使无作品也执行分析）
    """
    # 检查失败阈值
    for user_id in user_ids:
        failure_count = _get_failure_count(user_id)
        if failure_count >= FAILURE_THRESHOLD:
            print(json.dumps({
                "status": "error",
                "message": "当前账号ID已超过失败阈值，请联系客服邮箱redfoxdata@proton.me处理",
                "query_type": "threshold_exceeded",
                "data": {"accounts": []}
            }, ensure_ascii=False))
            return
    
    # 检查sync冷却期
    for user_id in user_ids:
        in_cooldown, remaining = _check_sync_cooldown(user_id)
        if in_cooldown:
            print(json.dumps({
                "status": "error",
                "message": f"数据同步中，请等待约{remaining}分钟后再查询，如果急需可联系工作人员邮箱redfoxdata@proton.me",
                "query_type": "sync_cooldown",
                "data": {"accounts": [], "remaining_minutes": remaining}
            }, ensure_ascii=False))
            return
    
    try:
        raw = api_query(user_ids)
    except Exception as e:
        # 记录失败
        for user_id in user_ids:
            _record_failure(user_id)
        print(json.dumps({
            "status": "error",
            "message": f"请求失败: {str(e)}",
            "query_type": "not_found",
            "data": {"accounts": []}
        }, ensure_ascii=False))
        return

    if isinstance(raw, dict) and raw.get("code") == 5000:
        # 记录失败（账号可能不存在）
        for user_id in user_ids:
            _record_failure(user_id)
        print(json.dumps({
            "status": "error",
            "message": f"接口返回: {raw.get('msg', '系统忙')}",
            "query_type": "not_found",
            "data": {"accounts": []}
        }, ensure_ascii=False))
        return

    raw_data = raw
    if isinstance(raw, dict) and raw.get("data") is not None:
        raw_data = raw["data"]

    if isinstance(raw_data, dict):
        items = [raw_data]
    elif isinstance(raw_data, list):
        items = raw_data
    else:
        items = []

    if not items:
        # 记录失败（账号未被数据库收录）
        for user_id in user_ids:
            _record_failure(user_id)
        print(json.dumps({
            "status": "success",
            "query_type": "not_found",
            "data": {"accounts": []}
        }, ensure_ascii=False))
        return

    _save_raw_data(raw)
    
    # 查询成功，清除失败记录
    for user_id in user_ids:
        _clear_failures(user_id)

    full_data_items = [it for it in items if isinstance(it, dict) and ("fans" in it or "noteCountThirty" in it)]

    if len(full_data_items) > 1:
        # 多账号对比：检查是否有账号没有作品数据
        accounts_need_sync = []
        accounts_with_works = []
        for it in full_data_items:
            works = it.get("works", []) or []
            if not works:
                accounts_need_sync.append({
                    "nickname": it.get("nickname", ""),
                    "redId": it.get("redId", "")
                })
            else:
                accounts_with_works.append(it)
        
        # 如果所有账号都没有作品数据
        if not accounts_with_works:
            # 如果是订阅推送（force_analyze参数），仍然执行分析
            if force_analyze:
                accounts = [_analyze_single_account(it, has_works=False) for it in full_data_items]
                output = {
                    "status": "success",
                    "query_type": "multi",
                    "message": "数据已保存到 output/raw_data.json 中，请读取该文件获取数据进行分析",
                    "no_works_hint": "检测到该账号近30天无作品数据。请确认：该账号近30天是否真的无作品？\n1.该账号近30天确实无作品，直接分析\n2.该账号近30天有作品，需要实时获取最新作品（大概需要30分钟，自动推送诊断报告）"
                }
                print(json.dumps(output, ensure_ascii=False))
                return
            # 否则返回订阅提示
            output = {
                "status": "success",
                "query_type": "need_sync",
                "message": "这些账号暂无作品数据，需要订阅同步",
                "need_sync": accounts_need_sync
            }
            print(json.dumps(output, ensure_ascii=False))
            return
        
        # 部分账号有作品数据，生成有数据的账号报告
        accounts = [_analyze_single_account(it) for it in accounts_with_works]
        output = {
            "status": "success",
            "query_type": "multi",
            "message": "数据已保存到 output/raw_data.json 中，请读取该文件获取数据进行分析"
        }
        # 如果有账号需要同步作品数据，返回提示
        if accounts_need_sync:
            output["need_sync"] = accounts_need_sync
        print(json.dumps(output, ensure_ascii=False))
        return

    if len(full_data_items) == 1:
        raw_item = full_data_items[0]
        works = raw_item.get("works", []) or []
        
        # 检查是否需要同步作品数据
        if not works:
            red_id = raw_item.get("redId", "")
            nickname = raw_item.get("nickname", "")
            # 如果是订阅推送（force_analyze参数），仍然执行分析
            if force_analyze:
                result = _analyze_single_account(raw_item, has_works=False)
                output = {
                    "status": "success",
                    "query_type": "single",
                    "message": "数据已保存到 output/raw_data.json 中，请读取该文件获取数据进行分析",
                    "no_works_hint": "检测到该账号近30天无作品数据。请确认：该账号近30天是否真的无作品？\n1.该账号近30天确实无作品，直接分析\n2.该账号近30天有作品，需要实时获取最新作品（大概需要30分钟，自动推送诊断报告）"
                }
                print(json.dumps(output, ensure_ascii=False))
                return
            # 否则返回订阅提示
            output = {
                "status": "success",
                "query_type": "need_sync",
                "message": "该账号暂无作品数据，需要订阅同步",
                "need_sync": [{"nickname": nickname, "redId": red_id}]
            }
            print(json.dumps(output, ensure_ascii=False))
            return
        
        result = _analyze_single_account(raw_item)
        output = {
            "status": "success",
            "query_type": "unique",
            "message": "数据已保存到 output/raw_data.json 中，请读取该文件获取数据进行分析"
        }
        print(json.dumps(output, ensure_ascii=False))
        return

    print(json.dumps({
        "status": "success",
        "query_type": "not_found",
        "message": "当前未查询到该账号相关数据，是当前数据覆盖范围不足导致的。不过别担心，我们将提供账号数据去实时获取；1.接收实时获取，大概需要30分钟，自动推送诊断报告 2.下次再说"
    }, ensure_ascii=False))


def cmd_sync_notes(red_ids, account_names=None):
    """订阅命令：调用接口同步账号作品数据
    
    参数:
        red_ids: 小红书账号ID列表（redId）
        account_names: 账号名称列表（可选）
    """
    SYNC_API_URL = "https://redfox.hk/story/api/xhsUser/syncUserNotes"
    results = []
    
    for i, red_id in enumerate(red_ids):
        account_name = account_names[i] if account_names and i < len(account_names) else f"账号{red_id}"
        
        # 检查sync冷却期，冷却期内不再调用接口
        in_cooldown, remaining = _check_sync_cooldown(red_id)
        if in_cooldown:
            results.append({
                "redId": red_id,
                "redId_str": str(red_id),
                "account_name": account_name,
                "status": "cooldown",
                "message": f"数据同步中，请等待约{remaining}分钟后再查询，如果急需可联系工作人员邮箱redfoxdata@proton.me",
                "remaining_minutes": remaining
            })
            continue
        
        # 记录sync时间（用于冷却期控制）
        _record_sync(red_id)
        
        try:
            body = {"redId": red_id, "source": "小红书账号诊断-GitHub"}
            result_data = _native_post(SYNC_API_URL, body)
            
            # 无论接口返回什么，都认为同步请求已发出
            results.append({
                "redId": red_id,
                "redId_str": str(red_id),
                "account_name": account_name,
                "status": "success",
                "schedule_required": True,
                "schedule_time_minutes": 30
            })
        except Exception as e:
            results.append({
                "redId": red_id,
                "status": "error",
                "message": f"订阅失败: {str(e)}"
            })
    
    print(json.dumps({
        "status": "success",
        "query_type": "sync",
        "data": {"sync_results": results}
    }, ensure_ascii=False))


def cmd_build_report_data(account_name):
    """基于模板生成report_data.json文件
    
    Args:
        account_name: 账号名称，用于标识
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    template_path = os.path.normpath(os.path.join(script_dir, "..", "assets", "report_data_template.json"))
    output_dir = os.path.normpath(os.path.join(script_dir, "..", "output"))
    output_path = os.path.join(output_dir, REPORT_DATA_FILE)
    
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 读取模板
    if not os.path.exists(template_path):
        print(json.dumps({"status": "error", "message": f"模板文件不存在: {template_path}"}, ensure_ascii=False))
        sys.exit(1)
    
    with open(template_path, "r", encoding="utf-8") as f:
        template_data = json.load(f)
    
    # 如果有raw_data.json，从中提取基础信息填充模板
    raw_data_path = os.path.join(output_dir, RAW_DATA_FILE)
    if os.path.exists(raw_data_path):
        try:
            with open(raw_data_path, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
            
            # 从raw_data提取基础信息填充模板的header部分
            if "header" in template_data:
                # 账号名优先使用传入参数，其次使用raw_data中的数据
                template_data["header"]["账号名"] = account_name or raw_data.get("nickname", "")
                template_data["header"]["账号标识"] = raw_data.get("userAttribute", "素人")
                template_data["header"]["数据获取时间"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # 填充scores部分的基础分值（如果有）
            if "scores" in template_data and "scores" in raw_data:
                for key in raw_data["scores"]:
                    if key in template_data["scores"]:
                        template_data["scores"][key] = raw_data["scores"][key]
        except Exception as e:
            pass  # 模板保持原样，由agent后续填充
    
    # 写入report_data.json（每次都覆盖）
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(template_data, f, ensure_ascii=False, indent=2)
    
    print(json.dumps({
        "status": "success",
        "message": f"report_data.json模板已生成，请基于此文件填充分析数据",
        "output_path": output_path,
        "template_structure": list(template_data.keys())
    }, ensure_ascii=False))


def cmd_build_multi_report_data(account_names):
    """基于模板生成multi_report_data.json文件
    
    Args:
        account_names: 账号名称列表
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    template_path = os.path.normpath(os.path.join(script_dir, "..", "assets", "multi_report_data_template.json"))
    output_dir = os.path.normpath(os.path.join(script_dir, "..", "output"))
    output_path = os.path.join(output_dir, MULTI_REPORT_DATA_FILE)
    
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 读取模板
    if not os.path.exists(template_path):
        print(json.dumps({"status": "error", "message": f"模板文件不存在: {template_path}"}, ensure_ascii=False))
        sys.exit(1)
    
    with open(template_path, "r", encoding="utf-8") as f:
        template_data = json.load(f)
    
    # 根据账号数量生成accounts数组
    accounts_template = template_data.get("accounts", [{}])
    if accounts_template:
        account_template = accounts_template[0]
        template_data["accounts"] = [json.loads(json.dumps(account_template)) for _ in account_names]
    
    # 写入multi_report_data.json（每次都覆盖）
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(template_data, f, ensure_ascii=False, indent=2)
    
    print(json.dumps({
        "status": "success",
        "message": f"multi_report_data.json模板已生成，请基于此文件填充分析数据",
        "output_path": output_path,
        "account_count": len(account_names)
    }, ensure_ascii=False))


def cmd_generate_html():
    """生成单账号HTML命令 - 使用html_generator模块"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.normpath(os.path.join(script_dir, "..", "output", REPORT_DATA_FILE))
    template_path = os.path.normpath(os.path.join(script_dir, "..", "assets", "report_template.html"))
    raw_data_path = os.path.normpath(os.path.join(script_dir, "..", "output", RAW_DATA_FILE))

    if not os.path.exists(data_path):
        print(json.dumps({"status": "error", "message": f"报告数据文件不存在: {data_path}，请先完成诊断报告生成并保存report_data.json"}, ensure_ascii=False))
        sys.exit(1)

    with open(data_path, "r", encoding="utf-8") as f:
        report_data = json.load(f)

    # 读取原始数据作为备用数据源
    raw_data = {}
    if os.path.exists(raw_data_path):
        try:
            with open(raw_data_path, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
        except Exception:
            pass

    # 生成HTML
    html, error = generate_single_report_html(report_data, template_path, raw_data)
    if error:
        print(json.dumps({"status": "error", "message": error}, ensure_ascii=False))
        sys.exit(1)

    # 输出HTML文件
    output_dir = os.path.normpath(os.path.join(script_dir, "..", "output"))
    os.makedirs(output_dir, exist_ok=True)

    account_name = report_data.get("header", {}).get("账号名", "report")
    safe_name = account_name.replace("/", "_").replace("\\", "_").replace(" ", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(output_dir, f"{safe_name}_诊断报告_{timestamp}.html")
    
    # 数据完整性检查与修复
    html, missing_fields = check_and_fix_html_content(html, report_data)
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    result_info = {
        "status": "success",
        "message": "HTML报告已生成",
        "output_path": output_path
    }
    if missing_fields:
        result_info["warning"] = f"以下字段缺失已用默认值填充: {missing_fields}"
    print(json.dumps(result_info, ensure_ascii=False))


def cmd_generate_multi_html(with_similar=False):
    """生成多账号对比HTML命令 - 使用html_generator模块"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.normpath(os.path.join(script_dir, "..", "output", MULTI_REPORT_DATA_FILE))
    template_path = os.path.normpath(os.path.join(script_dir, "..", "assets", "multi_report_template.html"))

    if not os.path.exists(data_path):
        print(json.dumps({"status": "error", "message": f"多账号报告数据文件不存在: {data_path}，请先保存multi_report_data.json"}, ensure_ascii=False))
        sys.exit(1)

    with open(data_path, "r", encoding="utf-8") as f:
        multi_data = json.load(f)

    # 生成HTML
    html, error = generate_multi_report_html(multi_data, template_path)
    if error:
        print(json.dumps({"status": "error", "message": error}, ensure_ascii=False))
        sys.exit(1)

    accounts = multi_data.get("accounts", [])

    # 输出HTML文件
    output_dir = os.path.normpath(os.path.join(script_dir, "..", "output"))
    os.makedirs(output_dir, exist_ok=True)

    names = [acc.get("header", {}).get("账号名", "未知") for acc in accounts[:3]]
    safe_name = "vs".join(n.replace("/", "_").replace("\\", "_").replace(" ", "_") for n in names)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(output_dir, f"{safe_name}_对比报告_{timestamp}.html")
    
    # 多账号HTML数据完整性检查（简化版）
    html, missing_fields = check_multi_html_content(html, accounts)
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    result_info = {
        "status": "success",
        "message": "多账号对比HTML报告已生成",
        "output_path": output_path
    }
    if missing_fields:
        result_info["warning"] = f"以下字段缺失已用默认值填充: {missing_fields}"
    print(json.dumps(result_info, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description="小红书账号诊断师")
    subparsers = parser.add_subparsers(dest="command")

    # 查询子命令
    query_parser = subparsers.add_parser("query", help="查询账号数据")
    query_parser.add_argument("--user_ids", help="小红书账号ID列表，逗号分隔", required=True)
    query_parser.add_argument("--force_analyze", action="store_true", help="强制执行分析（即使无作品数据）")

    # 同步作品子命令
    sync_parser = subparsers.add_parser("sync_notes", help="同步账号作品数据")
    sync_parser.add_argument("--red_ids", help="小红书redId列表，逗号分隔", required=True)
    sync_parser.add_argument("--account_names", help="账号名称列表，逗号分隔（用于提示）", required=False)

    # 生成单账号HTML子命令
    html_parser = subparsers.add_parser("generate_html", help="基于report_data.json生成单账号HTML报告")

    # 生成多账号对比HTML子命令
    multi_parser = subparsers.add_parser("generate_multi_html", help="基于multi_report_data.json生成多账号对比HTML报告")

    # 构建report_data.json子命令
    build_parser = subparsers.add_parser("build_report_data", help="基于模板生成report_data.json")
    build_parser.add_argument("--account_name", help="账号名称", required=True)

    # 构建multi_report_data.json子命令
    build_multi_parser = subparsers.add_parser("build_multi_report_data", help="基于模板生成multi_report_data.json")
    build_multi_parser.add_argument("--account_names", help="账号名称列表，逗号分隔", required=True)

    args = parser.parse_args()

    if args.command == "query":
        user_ids = [x.strip() for x in args.user_ids.split(",") if x.strip()]

        if not user_ids:
            print(json.dumps({
                "status": "error",
                "message": "请提供至少一个账号ID（--user_ids）"
            }, ensure_ascii=False))
            sys.exit(1)

        cmd_query(user_ids, force_analyze=getattr(args, 'force_analyze', False))

    elif args.command == "sync_notes":
        red_ids = [x.strip() for x in args.red_ids.split(",") if x.strip()]
        if not red_ids:
            print(json.dumps({
                "status": "error",
                "message": "请提供至少一个redId（--red_ids）"
            }, ensure_ascii=False))
            sys.exit(1)
        account_names = [x.strip() for x in args.account_names.split(",") if x.strip()] if args.account_names else []
        cmd_sync_notes(red_ids, account_names)

    elif args.command == "generate_html":
        cmd_generate_html()

    elif args.command == "generate_multi_html":
        cmd_generate_multi_html()

    elif args.command == "build_report_data":
        cmd_build_report_data(args.account_name)

    elif args.command == "build_multi_report_data":
        account_names = [x.strip() for x in args.account_names.split(",") if x.strip()]
        if not account_names:
            print(json.dumps({
                "status": "error",
                "message": "请提供至少一个账号名称（--account_names）"
            }, ensure_ascii=False))
            sys.exit(1)
        cmd_build_multi_report_data(account_names)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
