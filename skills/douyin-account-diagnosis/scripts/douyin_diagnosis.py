#!/usr/bin/env python3
"""
抖音账号诊断工具
用于「抖音账号诊断」技能的数据获取、六维度评分与报告生成。
通过红狐(RedFox) API 获取抖音账号数据，进行六维度诊断分析并输出报告。

用法: python douyin_diagnosis.py <抖音昵称或抖音号> [--api-key <你的API Key>]
API Key 优先级: 命令行 --api-key > 环境变量 REDFOX_API_KEY
"""

import os
import sys
import json
import urllib.request
import urllib.error
from datetime import datetime
import statistics

# ============================================================
# API 配置
# ============================================================
API_URL = "https://redfox.hk/story/api/dyUser/queryData"

# 技能来源标识（所有接口调用必须携带）
SOURCE = "抖音账号诊断-GitHub"


def resolve_api_key(cli_key=None):
    """解析使用的 API Key：命令行参数 > 环境变量 REDFOX_API_KEY。未配置则返回 None。"""
    return cli_key or os.environ.get("REDFOX_API_KEY") or None


def require_api_key(cli_key=None):
    """解析 API Key；未配置时输出引导信息并退出。"""
    api_key = resolve_api_key(cli_key)
    if api_key:
        return api_key
    print("[错误] 未配置 API Key")
    print("[hint] 获取: https://redfox.hk/settings/api-keys?source=github")
    print("[hint] 配置: export REDFOX_API_KEY=ak_xxxxxxxx")
    print("[hint] 或: python douyin_diagnosis.py <账号> --api-key ak_xxxxxxxx")
    sys.exit(1)

# ============================================================
# 工具函数
# ============================================================

def query_account(keyword, api_key):
    """调用红狐API查询抖音账号数据。keyword 可为昵称或抖音号。"""
    headers = {
        "Content-Type": "application/json",
        "X-API-KEY": api_key,
    }
    # 优先用 accountIds（精确匹配），若含中文则用 accountNames（模糊匹配）
    if _is_chinese(keyword):
        payload_key = "accountNames"
    else:
        payload_key = "accountIds"
    # 请求体必须携带 source 字段（技能来源标识）
    payload = json.dumps({payload_key: [keyword], "source": SOURCE}).encode("utf-8")
    req = urllib.request.Request(API_URL, data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            if result.get("code") == 2000 and result.get("data"):
                return result["data"][0]
            elif result.get("code") == 3201:
                print("[错误] API积分不足，请前往 redfox.hk 充值。")
                return None
            else:
                print(f"[错误] API返回异常: code={result.get('code')}, msg={result.get('msg', '')}")
                return None
    except urllib.error.URLError as e:
        print(f"[错误] 网络请求失败: {e}")
        return None
    except Exception as e:
        print(f"[错误] {e}")
        return None


def _is_chinese(s):
    return any("\u4e00" <= ch <= "\u9fff" for ch in s)


def _parse_dt(s):
    if not s:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def _safe_div(a, b):
    if not b or b == 0:
        return 0.0
    return a / b


def _fmt_num(n):
    """数字格式化，大数加万/亿后缀。"""
    if n is None:
        return "N/A"
    if n >= 100_000_000:
        return f"{n / 100_000_000:.2f}亿"
    if n >= 10_000:
        return f"{n / 10_000:.2f}万"
    return str(n)


def _cv(values):
    """变异系数 = 标准差 / 均值"""
    if len(values) < 2:
        return 0.0
    m = statistics.mean(values)
    if m == 0:
        return 0.0
    return statistics.stdev(values) / m


# ============================================================
# 维度1: 账号基础画像 (10分)
# ============================================================

def diagnose_profile(acc):
    score = 0
    details = []

    # 头像 (2分)
    avatar = acc.get("avatarUrl", "")
    if avatar:
        score += 2
        details.append(("头像", "已设置", 2, 2))
    else:
        details.append(("头像", "未设置", 0, 2))

    # 简介 (3分)
    sig = acc.get("signature", "") or ""
    if len(sig) >= 15:
        score += 3
        details.append(("简介", f"{len(sig)}字，内容完整", 3, 3))
    elif len(sig) > 0:
        score += 1
        details.append(("简介", f"仅{len(sig)}字，偏短", 1, 3))
    else:
        details.append(("简介", "空简介", 0, 3))

    # 地域一致性 (2分)
    province = acc.get("province", "") or ""
    ip_loc = acc.get("ipLocation", "") or ""
    if province and ip_loc and province == ip_loc:
        score += 2
        details.append(("地域一致性", f"{province} = IP({ip_loc})，一致", 2, 2))
    elif province or ip_loc:
        score += 1
        details.append(("地域一致性", f"省份={province}, IP={ip_loc}", 1, 2))
    else:
        details.append(("地域一致性", "地域信息缺失", 0, 2))

    # 性别/年龄完整度 (2分)
    gender = acc.get("gender", "")
    age = acc.get("age")
    if gender and gender != "未知":
        score += 1
    if age is not None:
        score += 1
    detail_str = f"性别={gender or '未知'}, 年龄={age if age else '未知'}"
    gained = (1 if gender and gender != "未知" else 0) + (1 if age else 0)
    details.append(("人群标签", detail_str, gained, 2))

    # 账号ID完整度 (1分)
    account_id = acc.get("accountId", "")
    if account_id:
        score += 1
        details.append(("抖音号", account_id, 1, 1))
    else:
        details.append(("抖音号", "未设置", 0, 1))

    return score, details


# ============================================================
# 维度2: 内容生产力 (15分)
# ============================================================

def diagnose_productivity(acc):
    score = 0
    details = []
    aweme_count = acc.get("awemeCount", 0) or 0
    total_favorited = acc.get("totalFavorited", 0) or 0
    works = acc.get("works", []) or []

    # 作品总量 (5分)
    if aweme_count < 100:
        s = 2
        label = f"{aweme_count}，偏少"
    elif aweme_count < 1000:
        s = 4
        label = f"{aweme_count}，正常"
    elif aweme_count < 3000:
        s = 5
        label = f"{aweme_count}，高产"
    else:
        s = 4
        label = f"{aweme_count}，极高产(需警惕刷量)"
    score += s
    details.append(("作品总量", label, s, 5))

    # 人均获赞 (5分)
    avg_likes = _safe_div(total_favorited, aweme_count)
    if avg_likes < 100:
        s = 1
        label = f"{avg_likes:.0f}，低效"
    elif avg_likes < 500:
        s = 3
        label = f"{avg_likes:.0f}，正常"
    elif avg_likes < 1000:
        s = 4
        label = f"{avg_likes:.0f}，良好"
    else:
        s = 5
        label = f"{avg_likes:.0f}，高效"
    score += s
    details.append(("人均获赞", label, s, 5))

    # 发布频率 (5分) - 从works推算
    if len(works) >= 2:
        times = sorted([_parse_dt(w.get("createTime", "")) for w in works if _parse_dt(w.get("createTime", ""))])
        if len(times) >= 2:
            span_days = (times[-1] - times[0]).total_seconds() / 86400
            if span_days == 0:
                span_days = 1
            freq = len(works) / span_days
            if freq < 0.5:
                s = 2
                label = f"日均{freq:.2f}条，低频"
            elif freq <= 2:
                s = 5
                label = f"日均{freq:.2f}条，正常"
            elif freq <= 3:
                s = 4
                label = f"日均{freq:.2f}条，高频"
            else:
                s = 3
                label = f"日均{freq:.2f}条，极高频"
            score += s
            details.append(("发布频率", label, s, 5))
        else:
            details.append(("发布频率", "数据不足", 3, 5))
            score += 3
    else:
        details.append(("发布频率", "作品数据不足", 3, 5))
        score += 3

    return score, details


# ============================================================
# 维度3: 互动健康度 (30分)
# ============================================================

def diagnose_engagement(acc):
    score = 0
    details = []
    followers = acc.get("followerCount", 0) or 0
    total_favorited = acc.get("totalFavorited", 0) or 0
    works = acc.get("works", []) or []

    # 粉丝获赞比 (10分)
    fan_like_ratio = _safe_div(total_favorited, followers)
    if fan_like_ratio < 5:
        s = 3
        label = f"{fan_like_ratio:.2f}，偏低"
    elif fan_like_ratio < 20:
        s = 7
        label = f"{fan_like_ratio:.2f}，正常"
    else:
        s = 10
        label = f"{fan_like_ratio:.2f}，优质(长尾效应强)"
    score += s
    details.append(("粉丝获赞比", label, s, 10))

    # 粉丝互动率 (10分)
    if works and followers > 0:
        avg_inter = statistics.mean([w.get("interactiveCount", 0) or 0 for w in works])
        engagement_rate = _safe_div(avg_inter, followers) * 100
        if engagement_rate > 5:
            s = 10
            label = f"{engagement_rate:.2f}%，优秀"
        elif engagement_rate > 2:
            s = 7
            label = f"{engagement_rate:.2f}%，正常"
        elif engagement_rate > 1:
            s = 4
            label = f"{engagement_rate:.2f}%，偏低"
        else:
            s = 1
            label = f"{engagement_rate:.2f}%，极低(疑似僵尸粉)"
        score += s
        details.append(("粉丝互动率", label, s, 10))
    else:
        details.append(("粉丝互动率", "数据不足", 3, 10))
        score += 3

    # 互动结构比 (5分)
    if works:
        total_digg = sum(w.get("diggCount", 0) or 0 for w in works)
        total_comment = sum(w.get("commentCount", 0) or 0 for w in works)
        total_share = sum(w.get("shareCount", 0) or 0 for w in works)
        if total_digg > 0:
            comment_ratio = total_comment / total_digg * 100
            share_ratio = total_share / total_digg * 100
            if comment_ratio > 5 and share_ratio > 5:
                s = 5
                label = f"赞:评:转 = 100:{comment_ratio:.1f}:{share_ratio:.1f}，健康"
            elif comment_ratio > 3 or share_ratio > 3:
                s = 3
                label = f"赞:评:转 = 100:{comment_ratio:.1f}:{share_ratio:.1f}，一般"
            else:
                s = 2
                label = f"赞:评:转 = 100:{comment_ratio:.1f}:{share_ratio:.1f}，互动单一"
            score += s
            details.append(("互动结构比", label, s, 5))
        else:
            details.append(("互动结构比", "无点赞数据", 0, 5))
    else:
        details.append(("互动结构比", "无作品数据", 0, 5))

    # 作品均互动 (5分)
    if works:
        avg_inter = statistics.mean([w.get("interactiveCount", 0) or 0 for w in works])
        if followers > 0:
            benchmark = followers * 0.03  # 3% 为基准
            if avg_inter > benchmark:
                s = 5
                label = f"均{_fmt_num(int(avg_inter))}互动，超基准"
            elif avg_inter > benchmark * 0.5:
                s = 3
                label = f"均{_fmt_num(int(avg_inter))}互动，接近基准"
            else:
                s = 1
                label = f"均{_fmt_num(int(avg_inter))}互动，低于基准"
            score += s
            details.append(("作品均互动", label, s, 5))
        else:
            details.append(("作品均互动", "粉丝数为0", 2, 5))
            score += 2
    else:
        details.append(("作品均互动", "无作品数据", 0, 5))

    return score, details


# ============================================================
# 维度4: 内容质量 (20分)
# ============================================================

def diagnose_quality(acc):
    score = 0
    details = []
    followers = acc.get("followerCount", 0) or 0
    works = acc.get("works", []) or []

    if not works:
        details.append(("爆款率", "无作品数据", 0, 6))
        details.append(("中位互动", "无作品数据", 0, 4))
        details.append(("互动稳定性", "无作品数据", 0, 5))
        details.append(("零互动占比", "无作品数据", 0, 5))
        return 0, details

    digg_counts = [w.get("diggCount", 0) or 0 for w in works]
    inter_counts = [w.get("interactiveCount", 0) or 0 for w in works]

    # 爆款率 (6分) - 点赞超过粉丝数10%
    threshold = followers * 0.1
    hits = sum(1 for d in digg_counts if d > threshold)
    hit_rate = hits / len(works) * 100
    if hit_rate > 10:
        s = 6
        label = f"{hit_rate:.1f}%，优秀"
    elif hit_rate > 5:
        s = 4
        label = f"{hit_rate:.1f}%，良好"
    elif hit_rate > 0:
        s = 3
        label = f"{hit_rate:.1f}%，偏低"
    else:
        s = 1
        label = f"{hit_rate:.1f}%，无爆款"
    score += s
    details.append(("爆款率", label, s, 6))

    # 中位互动 vs 均值偏离 (4分)
    if len(digg_counts) >= 2:
        med = statistics.median(digg_counts)
        avg = statistics.mean(digg_counts)
        if avg > 0:
            deviation = abs(med - avg) / avg
            if deviation < 0.2:
                s = 4
                label = f"中位{_fmt_num(int(med))} vs 均值{_fmt_num(int(avg))}，分布均匀"
            elif deviation < 0.5:
                s = 3
                label = f"中位{_fmt_num(int(med))} vs 均值{_fmt_num(int(avg))}，轻度偏离"
            else:
                s = 1
                label = f"中位{_fmt_num(int(med))} vs 均值{_fmt_num(int(avg))}，严重偏离(靠爆款拉动)"
            score += s
            details.append(("中位/均值偏离", label, s, 4))
        else:
            details.append(("中位/均值偏离", "互动数据为零", 0, 4))
    else:
        details.append(("中位/均值偏离", "数据不足", 2, 4))
        score += 2

    # 互动稳定性 (5分) - 变异系数
    cv = _cv(inter_counts)
    if cv < 0.5:
        s = 5
        label = f"CV={cv:.2f}，稳定输出"
    elif cv < 1.0:
        s = 3
        label = f"CV={cv:.2f}，波动一般"
    else:
        s = 1
        label = f"CV={cv:.2f}，严重依赖爆款"
    score += s
    details.append(("互动稳定性", label, s, 5))

    # 零互动占比 (5分)
    zero_count = sum(1 for d in digg_counts if d < 10)
    zero_rate = zero_count / len(works) * 100
    if zero_rate < 5:
        s = 5
        label = f"{zero_rate:.1f}%，质量稳定"
    elif zero_rate < 20:
        s = 3
        label = f"{zero_rate:.1f}%，部分低质"
    else:
        s = 1
        label = f"{zero_rate:.1f}%，大量低质/限流"
    score += s
    details.append(("零互动占比", label, s, 5))

    return score, details


# ============================================================
# 维度5: 内容趋势 (15分)
# ============================================================

def diagnose_trend(acc):
    score = 0
    details = []
    works = acc.get("works", []) or []
    crawl_time = _parse_dt(acc.get("crawlTime", ""))

    if not works:
        details.append(("近期趋势", "无作品数据", 0, 5))
        details.append(("爆款集中度", "无作品数据", 0, 5))
        details.append(("最新活跃度", "无作品数据", 0, 5))
        return 0, details

    # 按时间排序
    sorted_works = sorted(works, key=lambda w: _parse_dt(w.get("createTime", "")) or datetime.min)

    # 近期趋势 (5分) - 最近30% vs 最早30%
    n = len(sorted_works)
    if n >= 4:
        early = sorted_works[:max(1, n // 3)]
        recent = sorted_works[-(max(1, n // 3)):]
        early_avg = statistics.mean([w.get("interactiveCount", 0) or 0 for w in early])
        recent_avg = statistics.mean([w.get("interactiveCount", 0) or 0 for w in recent])
        if early_avg > 0:
            change = (recent_avg - early_avg) / early_avg * 100
            if change > 20:
                s = 5
                label = f"近期上升{change:.0f}%，增长期"
            elif change > -20:
                s = 4
                label = f"近期变化{change:+.0f}%，平稳期"
            elif change > -50:
                s = 2
                label = f"近期下降{abs(change):.0f}%，衰退期"
            else:
                s = 1
                label = f"近期暴跌{abs(change):.0f}%，严重衰退"
        else:
            s = 3
            label = "早期无互动数据"
        score += s
        details.append(("近期趋势", label, s, 5))
    else:
        details.append(("近期趋势", "作品数不足", 3, 5))
        score += 3

    # 爆款集中度 (5分)
    inter_counts = [w.get("interactiveCount", 0) or 0 for w in works]
    if inter_counts:
        max_inter = max(inter_counts)
        avg_inter = statistics.mean(inter_counts)
        if avg_inter > 0:
            concentration = max_inter / avg_inter
            if concentration < 3:
                s = 5
                label = f"最大/均值={concentration:.1f}倍，均匀分布"
            elif concentration < 5:
                s = 4
                label = f"最大/均值={concentration:.1f}倍，较为均匀"
            elif concentration < 10:
                s = 2
                label = f"最大/均值={concentration:.1f}倍，依赖爆款"
            else:
                s = 1
                label = f"最大/均值={concentration:.1f}倍，严重依赖单条"
            score += s
            details.append(("爆款集中度", label, s, 5))
        else:
            details.append(("爆款集中度", "无互动数据", 0, 5))
    else:
        details.append(("爆款集中度", "无数据", 0, 5))

    # 最新活跃度 (5分)
    latest_time = _parse_dt(sorted_works[-1].get("createTime", ""))
    if latest_time and crawl_time:
        days_since = (crawl_time - latest_time).days
        if days_since <= 3:
            s = 5
            label = f"最近{days_since}天前发布，活跃"
        elif days_since <= 7:
            s = 4
            label = f"最近{days_since}天前发布，正常"
        elif days_since <= 14:
            s = 2
            label = f"最近{days_since}天前发布，偏沉默"
        else:
            s = 1
            label = f"最近{days_since}天前发布，已断更"
        score += s
        details.append(("最新活跃度", label, s, 5))
    else:
        details.append(("最新活跃度", "时间数据缺失", 3, 5))
        score += 3

    return score, details


# ============================================================
# 维度6: 粉丝质量 (10分)
# ============================================================

def diagnose_fans(acc):
    score = 0
    details = []
    followers = acc.get("followerCount", 0) or 0
    total_favorited = acc.get("totalFavorited", 0) or 0
    works = acc.get("works", []) or []

    # 粉丝规模 (4分)
    if followers < 10000:
        s = 1
        label = f"{_fmt_num(followers)}，尾部"
    elif followers < 100000:
        s = 2
        label = f"{_fmt_num(followers)}，腰部"
    elif followers < 1000000:
        s = 3
        label = f"{_fmt_num(followers)}，头部"
    else:
        s = 4
        label = f"{_fmt_num(followers)}，超头部"
    score += s
    details.append(("粉丝规模", label, s, 4))

    # 粉丝互动比 (3分)
    if works and followers > 0:
        avg_inter = statistics.mean([w.get("interactiveCount", 0) or 0 for w in works])
        fan_eng = _safe_div(avg_inter, followers) * 100
        if fan_eng > 3:
            s = 3
            label = f"{fan_eng:.2f}%，粉丝活跃"
        elif fan_eng > 1:
            s = 2
            label = f"{fan_eng:.2f}%，粉丝一般"
        else:
            s = 1
            label = f"{fan_eng:.2f}%，粉丝不活跃"
        score += s
        details.append(("粉丝互动比", label, s, 3))
    else:
        details.append(("粉丝互动比", "数据不足", 1, 3))
        score += 1

    # 获赞/粉丝背离 (3分)
    ratio = _safe_div(total_favorited, followers)
    if ratio > 100:
        s = 1
        label = f"获赞/粉丝={ratio:.1f}，异常高(疑似刷赞/搬运)"
    elif ratio > 50:
        s = 2
        label = f"获赞/粉丝={ratio:.1f}，偏高"
    elif ratio > 0:
        s = 3
        label = f"获赞/粉丝={ratio:.1f}，正常"
    else:
        s = 1
        label = "数据异常"
    score += s
    details.append(("获赞/粉丝背离", label, s, 3))

    return score, details


# ============================================================
# 预警检测
# ============================================================

def check_warnings(acc):
    warnings = []
    followers = acc.get("followerCount", 0) or 0
    total_favorited = acc.get("totalFavorited", 0) or 0
    works = acc.get("works", []) or []

    if works and followers > 50000:
        avg_inter = statistics.mean([w.get("interactiveCount", 0) or 0 for w in works])
        rate = _safe_div(avg_inter, followers) * 100
        if rate < 0.5:
            warnings.append("僵尸粉预警: 粉丝互动率 < 0.5% 且粉丝数 > 5万")

    ratio = _safe_div(total_favorited, followers)
    if ratio > 100:
        # 检查近期是否骤降
        if len(works) >= 2:
            sorted_works = sorted(works, key=lambda w: _parse_dt(w.get("createTime", "")) or datetime.min)
            early_avg = statistics.mean([w.get("interactiveCount", 0) or 0 for w in sorted_works[:len(sorted_works)//2]])
            recent_avg = statistics.mean([w.get("interactiveCount", 0) or 0 for w in sorted_works[len(sorted_works)//2:]])
            if recent_avg < early_avg * 0.5:
                warnings.append("刷量预警: 获赞/粉丝比 > 100 且近期互动骤降")

    if len(works) >= 4:
        sorted_works = sorted(works, key=lambda w: _parse_dt(w.get("createTime", "")) or datetime.min)
        n = len(sorted_works)
        early = sorted_works[:max(1, n // 3)]
        recent = sorted_works[-(max(1, n // 3)):]
        early_avg = statistics.mean([w.get("interactiveCount", 0) or 0 for w in early])
        recent_avg = statistics.mean([w.get("interactiveCount", 0) or 0 for w in recent])
        if early_avg > 0 and recent_avg < early_avg * 0.5:
            warnings.append("衰退预警: 近期作品均互动 < 早期的 50%")

    zero_count = sum(1 for w in works if (w.get("diggCount", 0) or 0) < 10)
    if works and zero_count / len(works) > 0.3:
        warnings.append("限流预警: 零互动占比 > 30%")

    crawl_time = _parse_dt(acc.get("crawlTime", ""))
    if works and crawl_time:
        latest = max(_parse_dt(w.get("createTime", "")) or datetime.min for w in works)
        if (crawl_time - latest).days > 14:
            warnings.append("断更预警: 最新作品距数据采集时间 > 14 天")

    inter_counts = [w.get("interactiveCount", 0) or 0 for w in works]
    if inter_counts:
        max_inter = max(inter_counts)
        avg_inter = statistics.mean(inter_counts)
        if avg_inter > 0 and max_inter / avg_inter > 10:
            warnings.append("单条依赖预警: 最大爆款互动 > 均值的 10 倍")

    return warnings


# ============================================================
# 报告生成
# ============================================================

WEIGHTS = {
    "profile": 0.10,
    "productivity": 0.15,
    "engagement": 0.30,
    "quality": 0.20,
    "trend": 0.15,
    "fans": 0.10,
}

DIM_NAMES = {
    "profile": "账号基础画像",
    "productivity": "内容生产力",
    "engagement": "互动健康度",
    "quality": "内容质量",
    "trend": "内容趋势",
    "fans": "粉丝质量",
}

DIM_MAX = {
    "profile": 10,
    "productivity": 15,
    "engagement": 30,
    "quality": 20,
    "trend": 15,
    "fans": 10,
}


def generate_report(acc):
    lines = []
    lines.append("=" * 60)
    lines.append("               抖音账号诊断报告")
    lines.append("=" * 60)

    # 基本信息
    lines.append("")
    lines.append("【基本信息】")
    lines.append(f"  昵称:     {acc.get('nickname', 'N/A')}")
    lines.append(f"  抖音号:   {acc.get('accountId', 'N/A')}")
    lines.append(f"  UID:      {acc.get('uid', 'N/A')}")
    lines.append(f"  粉丝数:   {_fmt_num(acc.get('followerCount', 0))}")
    lines.append(f"  作品数:   {_fmt_num(acc.get('awemeCount', 0))}")
    lines.append(f"  获赞总数: {_fmt_num(acc.get('totalFavorited', 0))}")
    lines.append(f"  地区:     {(acc.get('province') or '')}{(acc.get('city') or '') or 'N/A'}")
    lines.append(f"  IP属地:   {acc.get('ipLocation', 'N/A')}")
    lines.append(f"  数据时间: {acc.get('crawlTime', 'N/A')}")

    # 执行诊断
    diagnoses = {
        "profile": diagnose_profile(acc),
        "productivity": diagnose_productivity(acc),
        "engagement": diagnose_engagement(acc),
        "quality": diagnose_quality(acc),
        "trend": diagnose_trend(acc),
        "fans": diagnose_fans(acc),
    }

    # 各维度明细
    lines.append("")
    lines.append("【维度评分明细】")
    total_score = 0
    for key in ["profile", "productivity", "engagement", "quality", "trend", "fans"]:
        score, details = diagnoses[key]
        max_score = DIM_MAX[key]
        normalized = _safe_div(score, max_score) * 100
        weighted = normalized * WEIGHTS[key]
        total_score += weighted
        lines.append("")
        lines.append(f"  {DIM_NAMES[key]} ({score}/{max_score})")
        for item_name, desc, gained, full in details:
            bar = "+" * gained + "-" * (full - gained)
            lines.append(f"    [{bar}] {item_name}: {desc} ({gained}/{full})")

    # 综合评分
    lines.append("")
    lines.append("=" * 60)
    total_score = round(total_score)
    if total_score >= 85:
        grade = "优质账号"
        emoji = "🟢"
    elif total_score >= 70:
        grade = "正常账号"
        emoji = "🟡"
    elif total_score >= 50:
        grade = "待优化"
        emoji = "🟠"
    else:
        grade = "风险账号"
        emoji = "🔴"
    lines.append(f"  综合诊断评分: {total_score}/100  {emoji} {grade}")
    lines.append("=" * 60)

    # 预警
    warnings = check_warnings(acc)
    if warnings:
        lines.append("")
        lines.append("【风险预警】")
        for w in warnings:
            lines.append(f"  ⚠ {w}")
    else:
        lines.append("")
        lines.append("【风险预警】无")

    # 近期作品（必须输出项）
    works = acc.get("works", []) or []
    lines.append("")
    lines.append("【近期作品详情】")
    if works:
        sorted_works = sorted(works, key=lambda w: _parse_dt(w.get("createTime", "")) or datetime.min, reverse=True)
        lines.append(f"  共 {len(sorted_works)} 条近期作品")
        lines.append("")
        for i, w in enumerate(sorted_works, 1):
            t = w.get("createTime", "N/A")
            d = w.get("diggCount", 0)
            c = w.get("commentCount", 0)
            s = w.get("shareCount", 0)
            inter = w.get("interactiveCount", 0)
            desc = (w.get("desc", "") or w.get("title", ""))[:60]
            url = w.get("workUrl", "")
            lines.append(f"  {i}. [{t}] 赞{d} 评{c} 转{s} 总{inter}")
            lines.append(f"     {desc}")
            lines.append(f"     {url}")
    else:
        lines.append("  无作品数据")

    lines.append("")
    lines.append("-" * 60)
    lines.append("  数据来源: 红狐RedFox API (redfox.hk)")
    lines.append("-" * 60)

    return "\n".join(lines)


# ============================================================
# 主入口
# ============================================================

def main():
    args = sys.argv[1:]
    cli_key = None
    if "--api-key" in args:
        idx = args.index("--api-key")
        if idx + 1 < len(args):
            cli_key = args[idx + 1]
            args = args[:idx] + args[idx + 2:]
        else:
            print("[错误] --api-key 参数后需要提供密钥值")
            sys.exit(1)

    if not args:
        print("用法: python douyin_diagnosis.py <抖音昵称或抖音号> [--api-key <你的API Key>]")
        print("示例: python douyin_diagnosis.py 桔桔的茶园小动物")
        print("示例: python douyin_diagnosis.py xiaojuju8")
        sys.exit(1)

    keyword = args[0]
    print(f"正在查询抖音账号: {keyword} ...")

    acc = query_account(keyword, require_api_key(cli_key))
    if not acc:
        print("未查询到该账号，请检查昵称或抖音号是否正确。")
        sys.exit(1)

    report = generate_report(acc)
    print(report)


if __name__ == "__main__":
    main()
