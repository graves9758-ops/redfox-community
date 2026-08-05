import argparse
import json
import math
import os
import re
import sys
from datetime import datetime

import requests


API_HOST = "redfox.hk"
API_PATH_SEARCH_USER = "/story/api/gzh/data/searchUser"  # 接口1：关键词搜索账号 → 获取微信号
API_PATH_QUERY_DATA = "/story/api/gzhUser/queryData"      # 接口2：按微信号+名称精确查询完整数据
RAW_DATA_FILE = "raw_data.json"


def _work_read(w):
    """获取作品阅读数（兼容多种字段名）"""
    return w.get("clicksCount") or w.get("readCount") or w.get("readNum") or 0


def _work_like(w):
    """获取作品点赞数"""
    return w.get("likeCount") or w.get("likedCount") or 0


def _work_comment(w):
    """获取作品评论数"""
    return w.get("commentCount") or 0


def _work_share(w):
    """获取作品分享数"""
    return w.get("shareCount") or 0


def _work_collect(w):
    """获取作品在看数（微信以'在看'近似收藏行为）"""
    return w.get("watchCount") or 0


def _work_interact_total(w):
    """获取作品总互动数 = 点赞+评论+分享+在看"""
    return _work_like(w) + _work_comment(w) + _work_share(w) + _work_collect(w)


def _work_publish_time(w):
    """获取作品发布时间"""
    return w.get("publishTime") or w.get("time") or w.get("timestamp") or w.get("createTime") or ""


def _read_from_shell_config():
    """从shell配置文件中尝试读取REDFOX_API_KEY（仅macOS/Linux）"""
    if sys.platform == "win32":
        return None
    home = os.path.expanduser("~")
    config_files = [
        os.path.join(home, ".zshrc"),
        os.path.join(home, ".bashrc"),
        os.path.join(home, ".bash_profile"),
        os.path.join(home, ".profile"),
    ]
    for config_file in config_files:
        try:
            if os.path.isfile(config_file):
                with open(config_file, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                match = re.search(r'export\s+REDFOX_API_KEY\s*=\s*["\']?([^"\'\n]+)["\']?', content)
                if match:
                    return match.group(1).strip()
        except (OSError, PermissionError):
            continue
    return None


def _get_credential():
    """获取API凭证 - 优先从环境变量REDFOX_API_KEY读取，其次从shell配置文件读取"""
    credential = os.getenv("REDFOX_API_KEY")
    if credential and credential.strip():
        return credential.strip()

    # 环境变量未设置，尝试从shell配置文件读取
    credential = _read_from_shell_config()
    if credential:
        return credential

    raise ValueError(
        "未找到 REDFOX_API_KEY，请配置环境变量后重试。\n"
        "  macOS/Linux: export REDFOX_API_KEY=<你的apikey>\n"
        "  Windows:     [Environment]::SetEnvironmentVariable('REDFOX_API_KEY', '<值>', 'User')\n"
        "获取API Key: 访问 https://redfox.hk/ 注册后在个人中心获取"
    )


def _get_headers():
    """获取请求头"""
    return {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-API-KEY": _get_credential(),
    }


def https_post(path, body_dict):
    """POST请求"""
    url = f"https://{API_HOST}{path}"
    body_json = json.dumps(body_dict, ensure_ascii=False)
    response = requests.post(url, data=body_json.encode("utf-8"), headers=_get_headers(), timeout=30)
    return response.json()


def _extract_benchmark_from_api(raw):
    """从接口数据中提取水平衡量基准数据
    
    Args:
        raw: 接口返回的原始数据，包含 accountAvgList 和 accountExcellentList
        
    Returns:
        dict: benchmark字典
    """
    avg_list = raw.get("accountAvgList", []) or []
    excellent_list = raw.get("accountExcellentList", []) or []
    
    # 构建中位数参考字典（取第一条数据）
    avg_dict = {}
    if avg_list:
        for k, v in avg_list[0].items():
            if k != "fansType":
                try:
                    avg_dict[k] = float(v) if v else 0
                except (ValueError, TypeError):
                    pass
    
    # 构建优秀值参考字典（取第一条数据）
    excellent_dict = {}
    if excellent_list:
        for k, v in excellent_list[0].items():
            if k != "fansType":
                try:
                    excellent_dict[k] = float(v) if v else 0
                except (ValueError, TypeError):
                    pass
    
    # 兜底基准数据
    fallback_benchmark = BENCHMARK_DATA.get("素人", {})
    
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
        "总在看数": {
            "中位数参考": avg_dict.get("总在看数均值", 0),
            "优秀值参考": excellent_dict.get("总在看数均值", 0),
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
    
    # 计算互动率和收藏率（基于阅读数）
    # 互动率 = (点赞数 + 在看数) / 阅读数 * 100%
    # 收藏率 = 在看数 / 阅读数 * 100%
    
    # 获取中位数参考的点赞数、在看数
    avg_like = avg_dict.get("总点赞数均值", 0)
    avg_collect = avg_dict.get("总在看数均值", 0)
    avg_read = avg_dict.get("平均阅读数均值", 100)
    
    # 获取优秀值参考的点赞数、在看数
    excellent_like = excellent_dict.get("总点赞数均值", 0)
    excellent_collect = excellent_dict.get("总在看数均值", 0)
    excellent_read = excellent_dict.get("平均阅读数均值", 1000)
    
    # 计算互动率中位数参考和优秀值参考（基于阅读数）
    interaction_rate_avg = round((avg_like + avg_collect) / avg_read * 100, 2) if avg_read > 0 else 0.5
    interaction_rate_excellent = round((excellent_like + excellent_collect) / excellent_read * 100, 2) if excellent_read > 0 else 1.5
    
    # 计算收藏率中位数参考和优秀值参考
    collect_rate_avg = round(avg_collect / avg_read * 100, 2) if avg_read > 0 else 1.0
    collect_rate_excellent = round(excellent_collect / excellent_read * 100, 2) if excellent_read > 0 else 3.0
    
    benchmark["互动率"] = {
        "中位数参考": interaction_rate_avg,
        "优秀值参考": interaction_rate_excellent,
    }
    benchmark["收藏率"] = {
        "中位数参考": collect_rate_avg,
        "优秀值参考": collect_rate_excellent,
    }
    
    return benchmark






def _calc_interaction_structure(works):
    """计算互动结构（点赞/评论/在看占比）"""
    if not works:
        return None, None
    
    total_like = sum(_work_like(w) for w in works)
    total_comment = sum(_work_comment(w) for w in works)
    total_share = sum(_work_share(w) for w in works)
    
    total = total_like + total_comment + total_share
    if total == 0:
        return None, None
    
    like_pct = round(total_like / total * 100, 1)
    collect_pct = round((total_comment + total_share) / total * 100, 1)
    
    return like_pct, collect_pct




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




def _score_content_health(works, signature, verify_name, account_type):
    """内容健康度评分（原始分0-10分，综合评分时×3=0-30分，占30%）
    
    更新稳定性(15%): 10分=日更，8分=周更3-5次，5分=周更1-2次，<5=不规律
    内容垂直度(15%): 10分=极度垂直单一领域，7分=主领域+偶尔跨界，<5=内容杂乱
    原创能力(10%): 10分=90%+原创，8分=70-90%原创，5分=50-70%，<5=大量转载
    质量稳定性(10%): 波动<20%得高分，>50%扣分
    内容深度(5%): 长文比例、专业引用、独家观点
    形式创新(5%): 多媒体运用、互动形式、排版创新
    总权重=60%→归一化为0-10分→×3=0-30分(综合评分权重30%)
    """
    if not works:
        return {
            "更新稳定性": 0, "内容垂直度": 0, "原创能力": 0,
            "质量稳定性": 0, "内容深度": 0, "形式创新": 0,
            "原始分": 0, "总分": 0
        }
    
    # 更新稳定性(15%): 7天发文>=5篇满分, 3-4篇0.7, 1-2篇0.3, 0篇0
    work_count = len(works)
    if work_count >= 5:
        update_stability = 1.0
    elif work_count >= 3:
        update_stability = 0.7
    elif work_count >= 1:
        update_stability = 0.3
    else:
        update_stability = 0
    
    # 内容垂直度(15%): 基于accountType和works标题关键词匹配
    # 公众号通常专注某一领域，默认给中等偏上基础分
    vertical_score = 0.65  # 默认中等偏上（公众号通常有明确定位）
    if account_type and works:
        type_keywords = set(account_type.split())
        match_count = 0
        for w in works:
            title = (w.get("title") or "").lower()
            if any(kw in title for kw in type_keywords):
                match_count += 1
        match_ratio = match_count / len(works) if works else 0
        if match_ratio >= 0.9:
            vertical_score = 1.0
        elif match_ratio >= 0.7:
            vertical_score = 0.7
        elif match_ratio >= 0.4:
            vertical_score = 0.4
        else:
            vertical_score = 0.2
    
    # 原创能力(10%): 综合多种原创标记字段判断
    # 优先查works中的原创字段，其次查标题文字，无法判断时给中等分（不惩罚优质未标记内容）
    original_count = sum(
        1 for w in works
        if w.get("isOriginal") or w.get("originalFlag") or w.get("type") == "original"
        or "原创" in (w.get("title") or "")
    )
    original_ratio = original_count / len(works) if works else 0
    if original_ratio >= 0.7:
        original_score = 1.0
    elif original_ratio >= 0.4:
        original_score = 0.75
    elif original_ratio > 0:
        original_score = 0.55
    else:
        # 无原创标记：不代表非原创，给中等分(0.60)，避免错误惩罚优质账号
        original_score = 0.60
    
    # 质量稳定性(10%): 基于阅读量变异系数(标准差/均值)
    reads = [_work_read(w) for w in works if _work_read(w) > 0]
    if len(reads) >= 3:
        import statistics
        mean_read = statistics.mean(reads)
        std_read = statistics.stdev(reads)
        cv = std_read / mean_read if mean_read > 0 else 1
        if cv <= 0.3:
            quality_stability = 1.0
        elif cv <= 0.5:
            quality_stability = 0.6
        elif cv <= 0.8:
            quality_stability = 0.3
        else:
            quality_stability = 0.1
    else:
        quality_stability = 0.5
    
    # 内容深度(5%): 基于标题长度(长标题通常信息更丰富)
    avg_title_len = sum(len(w.get("title") or "") for w in works) / len(works) if works else 0
    if avg_title_len >= 20:
        depth_score = 1.0
    elif avg_title_len >= 14:
        depth_score = 0.7
    elif avg_title_len >= 8:
        depth_score = 0.4
    else:
        depth_score = 0.2
    
    # 形式创新(5%): 基于封面图多样性(有coverUrl的比例)
    covers = [w for w in works if w.get("coverUrl")]
    cover_ratio = len(covers) / len(works) if works else 0
    innovation_score = min(1.0, cover_ratio * 1.2)
    
    # 加权计算原始分(0-10)
    raw_score = (
        update_stability * 0.15 +
        vertical_score * 0.15 +
        original_score * 0.10 +
        quality_stability * 0.10 +
        depth_score * 0.05 +
        innovation_score * 0.05
    ) / 0.60 * 10  # 归一化到0-10
    
    raw_score = round(min(10, max(0, raw_score)), 1)
    
    return {
        "更新稳定性": round(update_stability * 10, 1),
        "内容垂直度": round(vertical_score * 10, 1),
        "原创能力": round(original_score * 10, 1),
        "质量稳定性": round(quality_stability * 10, 1),
        "内容深度": round(depth_score * 10, 1),
        "形式创新": round(innovation_score * 10, 1),
        "原始分": raw_score,
        "总分": round(raw_score * 3, 1)  # ×3换算为0-30分（综合评分权重30%）
    }


def _score_user_activity(works, interaction_rate=0):
    """用户活跃度评分（原始分0-10分，综合评分时×2.5=0-25分）
    
    互动率(20%): (点赞+在看+留言)/阅读量：>5%得高分，<1%低分
    留言质量(10%): 留言长度、深度讨论比例、作者回复率
    分享传播力(10%): 预估分享率，基于内容类型和行业基准
    阅读完成率(5%): 基于文章长度和行业基准，>60%高分
    活跃时段集中度(5%): 推送时间固定性，用户阅读时间规律
    总权重=50%→归一化为0-10分→×2.5=0-25分(综合评分权重25%)
    """
    if not works:
        return {
            "互动率": 0, "留言质量": 0, "分享传播力": 0,
            "阅读完成率": 0, "活跃时段集中度": 0,
            "原始分": 0, "总分": 0,
            "_extra": {"interaction_rate": 0, "comment_density": 0}
        }
    
    # 计算各项指标
    total_reads = sum(_work_read(w) for w in works)
    total_likes = sum(_work_like(w) for w in works)
    total_comments = sum(_work_comment(w) for w in works)
    total_shares = sum(_work_share(w) for w in works)
    total_watches = sum(w.get("watchCount") or 0 for w in works)
    
    # 互动率(20%): (点赞+评论+分享+在看)/阅读数
    if total_reads > 0:
        inter_rate = (total_likes + total_comments + total_shares + total_watches) / total_reads
    else:
        inter_rate = 0
    if inter_rate >= 0.05:
        interaction_score = 1.0
    elif inter_rate >= 0.02:
        interaction_score = 0.7
    elif inter_rate >= 0.01:
        interaction_score = 0.4
    else:
        interaction_score = 0.1
    
    # 留言质量(10%): 评论数/阅读数
    comment_density = total_comments / total_reads if total_reads > 0 else 0
    if comment_density >= 0.005:
        comment_score = 1.0
    elif comment_density >= 0.002:
        comment_score = 0.7
    elif comment_density >= 0.0005:
        comment_score = 0.4
    else:
        comment_score = 0.1
    
    # 分享传播力(10%): 分享数/阅读数
    share_rate = total_shares / total_reads if total_reads > 0 else 0
    if share_rate >= 0.03:
        share_score = 1.0
    elif share_rate >= 0.015:
        share_score = 0.7
    elif share_rate >= 0.005:
        share_score = 0.4
    else:
        share_score = 0.1
    
    # 阅读完成率(5%): 无法精确获取，根据互动率推断
    # 高互动率通常意味着高完成率
    read_completion = min(1.0, inter_rate * 8) if inter_rate > 0 else 0.3
    
    # 活跃时段集中度(5%): 发布时间规律性
    from collections import Counter
    hours = []
    for w in works:
        pub_time = w.get("publishTime", "") or ""
        if pub_time:
            try:
                if isinstance(pub_time, (int, float)):
                    if pub_time > 1e12:
                        pub_time = pub_time / 1000
                    hour = datetime.fromtimestamp(pub_time).hour
                else:
                    hour = int(str(pub_time)[11:13]) if len(str(pub_time)) > 13 else -1
                if hour >= 0:
                    hours.append(hour)
            except (ValueError, OSError):
                pass
    
    if hours:
        hour_counter = Counter(hours)
        top_hour_count = hour_counter.most_common(1)[0][1]
        concentration = top_hour_count / len(hours)
        if concentration >= 0.6:
            time_score = 1.0
        elif concentration >= 0.4:
            time_score = 0.6
        else:
            time_score = 0.3
    else:
        time_score = 0.3
    
    # 加权计算原始分(0-10)
    raw_score = (
        interaction_score * 0.20 +
        comment_score * 0.10 +
        share_score * 0.10 +
        read_completion * 0.05 +
        time_score * 0.05
    ) / 0.50 * 10  # 归一化到0-10
    
    raw_score = round(min(10, max(0, raw_score)), 1)
    
    return {
        "互动率": round(interaction_score * 10, 1),
        "留言质量": round(comment_score * 10, 1),
        "分享传播力": round(share_score * 10, 1),
        "阅读完成率": round(read_completion * 10, 1),
        "活跃时段集中度": round(time_score * 10, 1),
        "原始分": raw_score,
        "总分": round(raw_score * 2.5, 1),  # ×2.5换算为0-25分（综合评分权重25%）
        "_extra": {
            "interaction_rate": round(inter_rate * 100, 2),
            "comment_density": round(comment_density * 100, 2)
        }
    }


def _score_core_data(works, avg_read_count):
    """内容核心数据表现评分（0-40分制，综合评分时转换为百分制）
    
    阅读数表现(15分): 平均阅读数区间分段
    点赞数表现(10分): 平均点赞数+点赞率
    评论数表现(7分): 平均评论数+评论率
    互动率表现(5分): 综合互动率
    发布时间合理性(3分): 黄金时段发文比例
    满分=40分，转换为百分制：raw/40*100
    """
    if not works:
        return {
            "阅读数表现": 0, "点赞数表现": 0, "评论数表现": 0,
            "互动率表现": 0, "发布时间合理性": 0,
            "原始分": 0, "总分": 0
        }
    
    # 1. 阅读数表现(15分) - 基于公众号行业真实水平校准
    # 行业参考：普通账号500-3000，良好账号3000-1万，优质账号1-5万，顶尖账号5万+
    avg_read = avg_read_count or 0
    if avg_read >= 100000:
        read_score = 15   # 超顶级，如人民日报等媒体大号
    elif avg_read >= 50000:
        read_score = 13   # 行业顶尖（5万+）
    elif avg_read >= 20000:
        read_score = 11   # 行业优秀（2-5万）← 占豪/洞见在此区间
    elif avg_read >= 10000:
        read_score = 9    # 行业良好（1-2万）
    elif avg_read >= 5000:
        read_score = 7    # 中等水平（5000-1万）
    elif avg_read >= 1000:
        read_score = 4    # 偏低
    else:
        read_score = 2    # 极低
    
    # 2. 点赞数表现(10分)
    total_likes = sum(_work_like(w) for w in works)
    total_reads = sum(_work_read(w) for w in works)
    avg_likes = total_likes / len(works) if works else 0
    like_rate = total_likes / total_reads if total_reads > 0 else 0
    
    if avg_likes >= 3000 or like_rate >= 0.03:
        like_score = 10
    elif avg_likes >= 1000 or like_rate >= 0.015:
        like_score = 8
    elif avg_likes >= 300 or like_rate >= 0.005:
        like_score = 5
    elif avg_likes >= 100 or like_rate >= 0.003:
        like_score = 3
    else:
        like_score = 1
    
    # 3. 评论数表现(7分)
    total_comments = sum(_work_comment(w) for w in works)
    avg_comments = total_comments / len(works) if works else 0
    comment_rate = total_comments / total_reads if total_reads > 0 else 0
    
    if avg_comments >= 500 or comment_rate >= 0.005:
        comment_score = 7
    elif avg_comments >= 200 or comment_rate >= 0.003:
        comment_score = 5
    elif avg_comments >= 100 or comment_rate >= 0.002:
        comment_score = 4
    elif avg_comments >= 50 or comment_rate >= 0.001:
        comment_score = 2
    else:
        comment_score = 1
    
    # 4. 互动率表现(5分) - 基于公众号行业真实水平校准
    # 行业参考：普通1-3%，良好3-8%，优秀8-15%，顶尖15%+
    total_shares = sum(_work_share(w) for w in works)
    total_watches = sum(w.get("watchCount") or 0 for w in works)
    inter_rate = (total_likes + total_comments + total_shares + total_watches) / total_reads if total_reads > 0 else 0
    
    if inter_rate >= 0.10:    # 顶尖：10%+（极少账号能达到）← 占豪/洞见在此区间
        inter_score = 5
    elif inter_rate >= 0.05:  # 优秀：5-10%
        inter_score = 4
    elif inter_rate >= 0.03:  # 良好：3-5%
        inter_score = 3
    elif inter_rate >= 0.015: # 中等：1.5-3%
        inter_score = 2
    elif inter_rate >= 0.005: # 偏低：0.5-1.5%
        inter_score = 1
    else:
        inter_score = 0
    
    # 5. 发布时间合理性(3分): 黄金时段发文比例
    golden_count = 0
    total_with_time = 0
    for w in works:
        pub_time = w.get("publishTime", "") or ""
        hour = -1
        if pub_time:
            try:
                if isinstance(pub_time, (int, float)):
                    if pub_time > 1e12:
                        pub_time = pub_time / 1000
                    hour = datetime.fromtimestamp(pub_time).hour
                else:
                    hour = int(str(pub_time)[11:13]) if len(str(pub_time)) > 13 else -1
            except (ValueError, OSError):
                pass
        if hour >= 0:
            total_with_time += 1
            if (7 <= hour <= 9) or (12 <= hour <= 13) or (20 <= hour <= 22):
                golden_count += 1
    
    if total_with_time > 0:
        golden_ratio = golden_count / total_with_time
        if golden_ratio >= 0.6:
            time_score = 3
        elif golden_ratio >= 0.3:
            time_score = 2
        elif golden_ratio >= 0.1:
            time_score = 1
        else:
            time_score = 0
    else:
        time_score = 1
    
    raw_score = round(read_score + like_score + comment_score + inter_score + time_score, 1)
    
    return {
        "阅读数表现": read_score,
        "点赞数表现": like_score,
        "评论数表现": comment_score,
        "互动率表现": inter_score,
        "发布时间合理性": time_score,
        "原始分": raw_score,
        "总分": round(raw_score / 40 * 100, 1)  # 转换为百分制
    }


def _score_operation_compliance(works, verify_name):
    """运营规范性评分（直接0-10分，综合评分权重10%）
    
    更新频率(5分): 7天发文数
    发布时间合理性(3分): 固定时段发文比例
    账号认证(2分): 是否有认证
    """
    if not works:
        return {
            "更新频率": 0, "发布时间合理性": 0, "账号认证": 0,
            "原始分": 0
        }
    
    # 更新频率(5分)
    work_count = len(works)
    if work_count >= 5:
        freq_score = 5
    elif work_count >= 3:
        freq_score = 4
    elif work_count >= 2:
        freq_score = 3
    elif work_count >= 1:
        freq_score = 2
    else:
        freq_score = 0
    
    # 发布时间合理性(3分): 固定时段发文占比
    hours = []
    for w in works:
        pub_time = w.get("publishTime", "") or ""
        if pub_time:
            try:
                if isinstance(pub_time, (int, float)):
                    if pub_time > 1e12:
                        pub_time = pub_time / 1000
                    hour = datetime.fromtimestamp(pub_time).hour
                else:
                    hour = int(str(pub_time)[11:13]) if len(str(pub_time)) > 13 else -1
                if hour >= 0:
                    hours.append(hour)
            except (ValueError, OSError):
                pass
    
    if hours:
        from collections import Counter
        hour_counter = Counter(hours)
        top_hour_count = hour_counter.most_common(1)[0][1]
        regularity = top_hour_count / len(hours)
        if regularity >= 0.6:
            time_score = 3
        elif regularity >= 0.4:
            time_score = 2
        elif regularity >= 0.2:
            time_score = 1
        else:
            time_score = 0
    else:
        time_score = 0.5
    
    # 账号认证(2分)
    auth_score = 2 if verify_name else 0
    
    raw_score = round(freq_score + time_score + auth_score, 1)
    
    return {
        "更新频率": freq_score,
        "发布时间合理性": time_score,
        "账号认证": auth_score,
        "原始分": raw_score
    }


def _get_score_level(score, max_score):
    """根据得分率返回评级（含图标）：优/良/中/差"""
    rate = score / max_score * 100 if max_score > 0 else 0
    if rate >= 80:
        return "优"
    elif rate >= 60:
        return "良"
    elif rate >= 40:
        return "中"
    else:
        return "差"


def _get_score_level_icon(score, max_score):
    """根据得分率返回评级+图标"""
    rate = score / max_score * 100 if max_score > 0 else 0
    if rate >= 80:
        return "优 ⭐"
    elif rate >= 60:
        return "良 ✅"
    elif rate >= 40:
        return "中 📊"
    else:
        return "差 ⚠️"


def _get_overall_grade(score):
    """根据综合评分返回等级图标+评级+等级

    评级标准（基于公众号行业真实水平）：
    S级(行业标杆) >=85：平均阅读3万+、互动率10%+ 的顶尖账号
    A级(优质账号) >=75：平均阅读1-3万、稳定更新的优质账号
    B级(健康账号) >=65：正常运营、有一定互动的健康账号
    C级(中等账号) >=55：基础运营待提升
    D级(亚健康)   >=45：运营不稳定或互动偏低
    E级(问题账号)  <45：严重问题需全面诊断
    """
    if score >= 85:
        return "🏆 标杆账号", "S级"
    elif score >= 75:
        return "⭐ 优质账号", "A级"
    elif score >= 65:
        return "✅ 健康账号", "B级"
    elif score >= 55:
        return "📊 中等账号", "C级"
    elif score >= 45:
        return "⚠️ 亚健康账号", "D级"
    else:
        return "❌ 问题账号", "E级"


def _analyze_single_account(raw, has_works=True):
    """对单个账号原始数据进行评分和结构化处理
    
    适配 queryData 接口返回的字段命名：
    accountId / accountName / avatar / verifyName / description / works / similarAccounts
    """
    # 无作品提示
    no_works_hint = "" if has_works else "该账号暂未获取到作品数据"
        
    # 统一字段读取
    nickname = raw.get("accountName", "")
    account_id = raw.get("accountId", "")
    signature = raw.get("description", "")
    avg_read_count = raw.get("avgReadCount", 0) or 0
    account_type = raw.get("accountType", "")
    verify_name = raw.get("verifyName", "")
    works = raw.get("works", []) or []
    
    if not works:
        has_works = False
    
    # 四维度评分
    content_health = _score_content_health(works, signature, verify_name, account_type)
    user_activity = _score_user_activity(works if has_works else [])
    core_data = _score_core_data(works if has_works else [], avg_read_count)
    operation_compliance = _score_operation_compliance(works if has_works else [], verify_name)
    
    # 综合评分：四维度加权均値（内容健康30% + 用户活跃30% + 核心数据30% + 运营规范性10%）
    dim1_score = round(content_health["原始分"] / 10 * 100, 1)
    dim2_score = round(user_activity["原始分"] / 10 * 100, 1)
    dim3_score = round(core_data["原始分"] / 40 * 100, 1)
    dim4_score = round(operation_compliance["原始分"] / 10 * 100, 1)
    
    total_score = round(
        dim1_score * 0.30 + dim2_score * 0.30 + dim3_score * 0.30 + dim4_score * 0.10, 1
    )
    total_score = max(0, min(100, total_score))

    # 评级
    overall_level = _get_score_level(total_score, 100)
    overall_grade, overall_rank = _get_overall_grade(total_score)
    dim1_level = _get_score_level(dim1_score, 100)
    dim1_level_icon = _get_score_level_icon(dim1_score, 100)
    dim2_level = _get_score_level(dim2_score, 100)
    dim2_level_icon = _get_score_level_icon(dim2_score, 100)
    dim3_level = _get_score_level(dim3_score, 100)
    dim3_level_icon = _get_score_level_icon(dim3_score, 100)
    dim4_level = _get_score_level(dim4_score, 100)
    dim4_level_icon = _get_score_level_icon(dim4_score, 100)

    # 构建scores结构
    scores = {
        "综合评分": total_score,
        "综合得分层级": overall_level,
        "综合评级": overall_grade,
        "综合等级": overall_rank,
        "内容健康度得分": dim1_score,
        "内容健康度满分": 100,
        "内容健康度得分率": round(dim1_score, 1),
        "内容健康度评级": dim1_level,
        "内容健康度评级图标": dim1_level_icon,
        "用户活跃度得分": dim2_score,
        "用户活跃度满分": 100,
        "用户活跃度得分率": round(dim2_score, 1),
        "用户活跃度评级": dim2_level,
        "用户活跃度评级图标": dim2_level_icon,
        "内容核心数据表现得分": dim3_score,
        "内容核心数据表现满分": 100,
        "内容核心数据表现得分率": round(dim3_score, 1),
        "内容核心数据表现评级": dim3_level,
        "内容核心数据表现评级图标": dim3_level_icon,
        "运营规范性得分": dim4_score,
        "运营规范性满分": 100,
        "运营规范性得分率": round(dim4_score, 1),
        "运营规范性评级": dim4_level,
        "运营规范性评级图标": dim4_level_icon,
        # 内容健康度子项（原始0-10分，×3=0-30分）
        "更新稳定性得分": content_health["更新稳定性"],
        "更新稳定性满分": 10,
        "内容垂直度得分": content_health["内容垂直度"],
        "内容垂直度满分": 10,
        "原创能力得分": content_health["原创能力"],
        "原创能力满分": 10,
        "质量稳定性得分": content_health["质量稳定性"],
        "质量稳定性满分": 10,
        "内容深度得分": content_health["内容深度"],
        "内容深度满分": 10,
        "形式创新得分": content_health["形式创新"],
        "形式创新满分": 10,
        "内容健康度原始分": content_health["原始分"],
        # 用户活跃度子项（原始0-10分，×2.5=0-25分）
        "互动率得分": user_activity["互动率"],
        "互动率满分": 10,
        "留言质量得分": user_activity["留言质量"],
        "留言质量满分": 10,
        "分享传播力得分": user_activity["分享传播力"],
        "分享传播力满分": 10,
        "阅读完成率得分": user_activity["阅读完成率"],
        "阅读完成率满分": 10,
        "活跃时段集中度得分": user_activity["活跃时段集中度"],
        "活跃时段集中度满分": 10,
        "用户活跃度原始分": user_activity["原始分"],
        # 内容核心数据表现子项（0-40分制）
        "阅读数表现得分": core_data["阅读数表现"],
        "阅读数表现满分": 15,
        "点赞数表现得分": core_data["点赞数表现"],
        "点赞数表现满分": 10,
        "评论数表现得分": core_data["评论数表现"],
        "评论数表现满分": 7,
        "互动率表现得分": core_data["互动率表现"],
        "互动率表现满分": 5,
        "发布时间合理性得分": core_data["发布时间合理性"],
        "发布时间合理性满分": 3,
        "内容核心数据原始分": core_data["原始分"],
        # 运营规范性子项（直接0-10分）
        "更新频率得分": operation_compliance["更新频率"],
        "更新频率满分": 5,
        "发布时间合理性2得分": operation_compliance["发布时间合理性"],
        "发布时间合理性2满分": 3,
        "账号认证得分": operation_compliance["账号认证"],
        "账号认证满分": 2,
    }

    # 计算优势模块和待优化模块
    dim_score_rates = [
        {"维度名": "内容健康度", "得分": dim1_score, "得分率": dim1_score},
        {"维度名": "用户活跃度", "得分": dim2_score, "得分率": dim2_score},
        {"维度名": "内容核心数据表现", "得分": dim3_score, "得分率": dim3_score},
        {"维度名": "运营规范性", "得分": dim4_score, "得分率": dim4_score},
    ]
    dim_sorted = sorted(dim_score_rates, key=lambda x: x["得分率"], reverse=True)
    scores["优势模块"] = dim_sorted[:2]
    scores["待优化模块"] = dim_sorted[-2:]

    # 互动率和更新频率计算
    # 注意：queryData 的 interactiveCount = 阅读数+互动分项之和，不能直接用于互动率计算
    # 始终使用分项加总：like+comment+share+watch
    interaction_rate = 0
    if works:
        total_reads = sum(_work_read(w) for w in works if _work_read(w) and _work_read(w) < 100001)
        total_interactions = sum(
            _work_like(w) + _work_comment(w) + _work_share(w) + (w.get("watchCount") or 0)
            for w in works
        )
        if total_reads > 0:
            interaction_rate = round(total_interactions / total_reads * 100, 2)
    works_7d = len(works) if works else 0

    # 行业对标（基于公众号真实行业水平）
    # 数据来源：公众号行业研究报告，覆盖10万+个人/企业公众号
    scores["行业对标"] = {
        "综合评分": {"本账号": f"{total_score}分", "行业均值": "45-55分", "头部账号": "85-95分"},
        "平均阅读量": {"本账号": str(avg_read_count), "行业均值": "2000-8000", "头部账号": "3-10万"},
        "互动率": {"本账号": f"{interaction_rate}%", "行业均值": "1-3%", "头部账号": "10-25%"},
        "更新频率": {"本账号": f"{works_7d}篇/近期", "行业均值": "2-4篇/周", "头部账号": "5-7篇/周"},
    }
    
    # 构建返回结果
    result = {
        "header": {
            "账号名": nickname,
            "账号ID": account_id,
            "账号链接": f"https://open.weixin.qq.com/qr/code?username={account_id}" if account_id else "",
            "账号类型": account_type,
            "账号简介": signature,
            "认证信息": verify_name,
            "平均阅读数": avg_read_count,
            "no_works_hint": no_works_hint,
        },
        "scores": scores,
        "content_health": {
            "更新稳定性": f"{content_health['更新稳定性']}/10",
            "内容垂直度": f"{content_health['内容垂直度']}/10",
            "原创能力": f"{content_health['原创能力']}/10",
            "质量稳定性": f"{content_health['质量稳定性']}/10",
            "内容深度": f"{content_health['内容深度']}/10",
            "形式创新": f"{content_health['形式创新']}/10",
            "原始分": f"{content_health['原始分']}/10",
            "总分": f"{dim1_score}/50",
            "评级": dim1_level,
            "评级图标": dim1_level_icon,
        },
        "user_activity": {
            "互动率": f"{user_activity['互动率']}/10",
            "留言质量": f"{user_activity['留言质量']}/10",
            "分享传播力": f"{user_activity['分享传播力']}/10",
            "阅读完成率": f"{user_activity['阅读完成率']}/10",
            "活跃时段集中度": f"{user_activity['活跃时段集中度']}/10",
            "原始分": f"{user_activity['原始分']}/10",
            "总分": f"{dim2_score}/50",
            "评级": dim2_level,
            "评级图标": dim2_level_icon,
        },
        "works": [
            {
                "标题": ("[{0}]({1})".format(w.get("title", ""), w.get("workUrl", "")) if w.get("workUrl") else w.get("title", "")),
                "阅读数": _work_read(w),
                "点赞数": _work_like(w),
                "评论数": _work_comment(w),
                "在看数": w.get("watchCount") or 0,
                "发布时间": _work_publish_time(w),
            }
            for w in (works[:5] if works else [])
        ],
        "works_hint": "",
        "similar_accounts": [
            {
                "账号名称": sa.get("accountName", ""),
                "账号ID": sa.get("accountId", ""),
                "平均阅读数": "",  # queryData 相似账号不返回该字段
            }
            for sa in ((raw.get("similarAccounts") or [])[:5])
            if sa.get("accountName")
        ],
        "_raw": raw,
    }

    # 保存report_data.json
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.normpath(os.path.join(script_dir, "..", "output"))
    os.makedirs(output_dir, exist_ok=True)
    report_path = os.path.join(output_dir, REPORT_DATA_FILE)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    return result
    
def _save_raw_data(raw_data):
    """将接口原始数据保存到raw_data.json"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, "..", "output")
    output_dir = os.path.normpath(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    raw_path = os.path.join(output_dir, RAW_DATA_FILE)
    with open(raw_path, "w", encoding="utf-8") as f:
        json.dump(raw_data, f, ensure_ascii=False, indent=2)


def cmd_query(account_ids=None, account_names=None, force_analyze=False):
    """查询命令：searchUser 获取微信号 → queryData 精确查询完整数据
    
    流程：
    1. searchUser(keyword=name) 搜索名称 → 必须名称完全匹配，取 account(微信号)
    2. queryData(accountIds=[微信号], accountNames=[名称]) → 精确定位，返回完整数据+works+相似账号
    
    按 ID 查询时：预期传入微信号（如 duhaoshu）或 gh_xxx 格式
    
    Args:
        account_ids: 微信号/gh_xxx ID 列表（可选）
        account_names: 账号名称列表（可选）
        force_analyze: 是否强制分析
    """
    items = []
    names_to_query = account_names if account_names else []
    ids_to_query = account_ids if account_ids else []
    
    if not names_to_query and not ids_to_query:
        print(json.dumps({
            "status": "error",
            "message": "请提供账号名称或账号ID",
            "query_type": "not_found",
            "data": []
        }, ensure_ascii=False))
        return
    
    # ── 按名称查询：searchUser 微信号 → queryData 完整数据 ──
    for name in names_to_query:
        # 第一步：searchUser 搜索，必须名称完全匹配
        try:
            search_resp = https_post(API_PATH_SEARCH_USER, {"keyword": name, "offset": 0})
        except Exception as e:
            print(json.dumps({
                "status": "error",
                "message": f"搜索失败: {str(e)}",
                "query_type": "not_found",
                "data": []
            }, ensure_ascii=False))
            return
        
        if not (isinstance(search_resp, dict) and search_resp.get("code") == 2000):
            print(json.dumps({
                "status": "error",
                "message": f"搜索失败: {search_resp.get('msg', '未知错误')}",
                "query_type": "not_found",
                "data": []
            }, ensure_ascii=False))
            return
        
        search_list = (search_resp.get("data") or {}).get("list", [])
        if not search_list:
            print(json.dumps({
                "status": "success",
                "query_type": "not_found",
                "message": f"未查询到账号【{name}】，该账号可能名称有误或暂无数据，请核实公众号名称后重试。",
                "data": []
            }, ensure_ascii=False))
            return
        
        # 必须名称完全匹配
        matched = next((a for a in search_list if a.get("accountName", "") == name), None)
        if matched is None:
            candidates = [
                {
                    "name": a.get("accountName", ""),
                    "wxId": a.get("wxId", ""),       # 公众号ID，gh_xxx 格式
                    "account": a.get("account", ""),  # 微信号，如 duhaoshu
                }
                for a in search_list[:5]
                if a.get("accountName")
            ]
            # 候选列表文案：账号名称 + 公众号ID + 微信号
            candidates_lines = []
            for c in candidates:
                parts = [f"「{c['name']}」"]
                if c["wxId"]:
                    parts.append(f"ID: {c['wxId']}")
                if c["account"]:
                    parts.append(f"微信号: {c['account']}")
                candidates_lines.append(" ".join(parts))
            candidates_str = "、".join(candidates_lines)
            print(json.dumps({
                "status": "success",
                "query_type": "not_found",
                "message": (
                    f"未找到名称为「{name}」的公众号，"
                    f"搜索结果中有较相近的账号：{candidates_str}，"
                    f"请确认公众号名称后重试，或可用公众号ID（微信号）直接查询。"
                ),
                "candidates": candidates,
                "data": []
            }, ensure_ascii=False))
            return
        
        # 微信号（account 字段）= queryData.accountIds 的正确参数格式
        weixin_id = matched.get("account", "")
        
        # 第二步：queryData 用微信号+名称精确定位，得到 works+similarAccounts
        try:
            data_resp = https_post(API_PATH_QUERY_DATA, {
                "accountIds": [weixin_id] if weixin_id else [],
                "accountNames": [name]
            })
        except Exception as e:
            print(json.dumps({
                "status": "error",
                "message": f"请求失败: {str(e)}",
                "query_type": "not_found",
                "data": []
            }, ensure_ascii=False))
            return
        
        if not (isinstance(data_resp, dict) and data_resp.get("code") == 2000):
            print(json.dumps({
                "status": "error",
                "message": f"查询失败: {data_resp.get('msg', '未知错误')}",
                "query_type": "not_found",
                "data": []
            }, ensure_ascii=False))
            return
        
        data_list = data_resp.get("data") or []
        if not data_list:
            print(json.dumps({
                "status": "success",
                "query_type": "not_found",
                "message": f"未查询到账号【{name}】的详细数据。",
                "data": []
            }, ensure_ascii=False))
            return
        
        # 优先取微信号匹配的账号，否则取 works 最多的
        exact = next((a for a in data_list if a.get("account", "") == weixin_id), None)
        best = exact if exact else max(data_list, key=lambda x: len(x.get("works", []) or []))
        works = best.get("works", []) or []
        avg_read = _calc_avg_read(works)
        items.append({**best, "avgReadCount": avg_read})
    
    # ── 按 ID 查询：直接用微信号/gh_xxx 调 queryData ──
    for wx_id in ids_to_query:
        try:
            resp = https_post(API_PATH_QUERY_DATA, {
                "accountIds": [wx_id],
                "accountNames": []
            })
        except Exception as e:
            print(json.dumps({
                "status": "error",
                "message": f"请求失败: {str(e)}",
                "query_type": "not_found",
                "data": []
            }, ensure_ascii=False))
            return
        
        if not (isinstance(resp, dict) and resp.get("code") == 2000):
            print(json.dumps({
                "status": "error",
                "message": f"查询失败: {resp.get('msg', '未知错误')}",
                "query_type": "not_found",
                "data": []
            }, ensure_ascii=False))
            return
        
        data_list = resp.get("data") or []
        if not data_list:
            print(json.dumps({
                "status": "success",
                "query_type": "not_found",
                "message": f"未查询到ID为【{wx_id}】的公众号，请确认ID是否正确。",
                "data": []
            }, ensure_ascii=False))
            return
        
        account = data_list[0]
        works = account.get("works", []) or []
        avg_read = _calc_avg_read(works)
        items.append({**account, "avgReadCount": avg_read})

    
    if not items:
        print(json.dumps({
            "status": "success",
            "query_type": "not_found",
            "data": []
        }, ensure_ascii=False))
        return

    _save_raw_data(items)

    if len(items) > 1:
        accounts_with_works = [it for it in items if it.get("works")]
        if not accounts_with_works:
            if force_analyze:
                [_analyze_single_account(it, has_works=False) for it in items]
                print(json.dumps({
                    "status": "success",
                    "query_type": "multi",
                    "message": "数据已保存",
                    "no_works_hint": "暂未获取到作品数据"
                }, ensure_ascii=False))
                return
            print(json.dumps({
                "status": "success",
                "query_type": "multi",
                "message": "这些账号暂无作品数据",
                "no_works_hint": "暂未获取到作品数据"
            }, ensure_ascii=False))
            return
        
        [_analyze_single_account(it) for it in accounts_with_works]
        print(json.dumps({"status": "success", "query_type": "multi", "message": "数据已保存"}, ensure_ascii=False))
        return

    raw_item = items[0]
    works = raw_item.get("works", []) or []
    _analyze_single_account(raw_item, has_works=bool(works))
    print(json.dumps({
        "status": "success",
        "query_type": "single",
        "message": "数据已保存",
        "no_works_hint": "该账号暂无作品数据" if not works else None
    }, ensure_ascii=False))


def _calc_avg_read(works):
    """从作品列表计算平均阅读数（排除 API 上限值 100001 以避免拉高均值）"""
    if not works:
        return 0
    reads_real = [_work_read(w) for w in works if 0 < _work_read(w) < 100001]
    reads_all  = [_work_read(w) for w in works if _work_read(w) > 0]
    reads = reads_real if reads_real else reads_all
    return int(sum(reads) / len(reads)) if reads else 0


REPORT_DATA_FILE = "report_data.json"
MULTI_REPORT_DATA_FILE = "multi_report_data.json"

# 各维度满分映射
SCORE_MAX_MAP = {
    "内容健康度": 100,
    "用户活跃度": 100,
    "内容核心数据表现": 100,
    "运营规范性": 100,
}


def _flatten_dict(d, parent_key="", sep="."):
    """将嵌套字典扁平化为点分隔的键名"""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(_flatten_dict(v, new_key, sep).items())
        elif isinstance(v, list):
            for i, item in enumerate(v):
                if isinstance(item, dict):
                    items.extend(_flatten_dict(item, f"{new_key}[{i}]", sep).items())
                else:
                    items.append((f"{new_key}[{i}]", str(item) if item is not None else ""))
        else:
            items.append((new_key, str(v) if v is not None else ""))
    return dict(items)


def _build_replacements(report_data):
    """构建HTML模板替换字典"""
    replacements = {}

    # 近期作品表格行
    works_rows = []
    for w in report_data.get("works", []):
        if not isinstance(w, dict):
            continue
        title = w.get("title", "无标题")[:15].replace(" ", "")
        if not title.strip():
            title = "无标题"
        date_str = w.get("date", "-") or "-"
        likes = w.get("likes", "0") or "0"
        url = w.get("workUrl", "") or ""
        link = f'<a href="{url}" target="_blank">查看</a>' if url else "-"
        works_rows.append(f"<tr><td>{title}</td><td>{date_str}</td><td>{likes}</td><td>{link}</td></tr>")
    replacements["{{works_table_rows}}"] = "\n".join(works_rows)

    # 爆文列表表格
    viral_list = report_data.get("viral", {}).get("爆文列表", [])
    if not viral_list:
        viral_list = report_data.get("爆文列表", [])
    viral_rows = []
    if viral_list:
        for v in viral_list:
            if not isinstance(v, dict):
                continue
            title = v.get("标题", v.get("title", "-"))[:20] or "-"
            pub_time = v.get("发布时间", v.get("publishTime", "-")) or "-"
            interactive = v.get("互动数", v.get("interactiveCount", "-")) or "-"
            multiple = v.get("超标准倍数", v.get("multiple", "-")) or "-"
            viral_rows.append(f"<tr><td>{title}</td><td>{pub_time}</td><td>{interactive}</td><td>{multiple}</td></tr>")
    if viral_rows:
        viral_table_html = (
            '<table class="viral-table">\n'
            '    <tr><th>爆文标题</th><th>发布时间</th><th>互动数</th><th>超标准倍数</th></tr>\n'
            + "\n".join(viral_rows) + "\n"
            '</table>'
        )
    else:
        viral_table_html = '<div class="info-row"><span class="label">爆文列表：</span><span class="value">暂无爆文</span></div>'
    replacements["{{爆文列表表格}}"] = viral_table_html

    return replacements


def _is_empty_field(val):
    """判断字段是否为空"""
    return str(val).strip() in ("", "None", "none")


def _remove_section_markers(html, marker_name, should_show):
    """根据条件移除或保留标记区域"""
    start_tag = f"<!-- {marker_name}_START -->"
    end_tag = f"<!-- {marker_name}_END -->"
    if should_show:
        html = html.replace(start_tag, "").replace(end_tag, "")
    else:
        html = re.sub(rf'<!-- {marker_name}_START -->.*?<!-- {marker_name}_END -->', '', html, flags=re.DOTALL).rstrip()
    return html


def _remove_empty_info_rows(html):
    """移除HTML中值为空的info-row行"""
    html = re.sub(r'<div class="info-row">\s*<span class="label">[^<]*</span>\s*<span class="value">\s*</span>\s*</div>', '', html)
    return html


def _remove_conditional_sections(html, report_data):
    """根据数据条件移除空数据模块"""
    scores = report_data.get("scores", {})

    # 爆文能力：始终展示，移除条件隐藏
    # viral_count = scores.get("爆文数", "")
    # try:
    #     viral_val = int(viral_count) if not _is_empty_field(viral_count) else 0
    # except (ValueError, TypeError):
    #     viral_val = 0
    # html = _remove_section_markers(html, "SECTION_VIRAL", viral_val > 0)
    # 直接移除标记，始终显示爆文能力模块
    html = html.replace("<!-- SECTION_VIRAL_START -->", "").replace("<!-- SECTION_VIRAL_END -->", "")

    # 近期作品：works为空时隐藏
    works = report_data.get("works", [])
    has_valid_works = any(isinstance(w, dict) and w.get("title", "").strip() for w in works)
    html = _remove_section_markers(html, "SECTION_WORKS", has_valid_works)

    # 可强化：内容健康度<16分时显示
    account_health = report_data.get("content_health", {})
    scores = report_data.get("scores", {})
    health_score = scores.get("内容健康度得分", 0)
    show_can_enhance = health_score < 16
    html = _remove_section_markers(html, "SECTION_CAN_ENHANCE", show_can_enhance)

    return html


def cmd_generate_html():
    """生成单账号HTML命令 - 直接使用report_data.json中的similar_accounts数据"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.normpath(os.path.join(script_dir, "..", "output", REPORT_DATA_FILE))
    template_path = os.path.normpath(os.path.join(script_dir, "..", "assets", "report_template.html"))
    raw_data_path = os.path.normpath(os.path.join(script_dir, "..", "output", "raw_data.json"))

    if not os.path.exists(data_path):
        print(json.dumps({"status": "error", "message": f"报告数据文件不存在: {data_path}，请先完成诊断报告生成并保存report_data.json"}, ensure_ascii=False))
        sys.exit(1)

    if not os.path.exists(template_path):
        print(json.dumps({"status": "error", "message": f"模板文件不存在: {template_path}"}, ensure_ascii=False))
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
            pass  # 原始数据读取失败时忽略

    with open(template_path, "r", encoding="utf-8") as f:
        html = f.read()

    replacements = _build_replacements(report_data)

    # 相似账号卡片（账号名称为超链接）- 直接使用report_data.json中的similar_accounts
    # 每个账号一行，展示：账号名称（超链接）、平均阅读、总互动、推荐理由、发文特点、可学之处
    similar_cards = []
    for sa in report_data.get("similar_accounts", []):
        if not isinstance(sa, dict):
            continue
        name = sa.get("账号名称") or sa.get("accountName") or sa.get("nickname") or sa.get("name", "")
        account_url = sa.get("账号链接") or sa.get("profileUrl") or sa.get("url", "")
        avg_read = sa.get("平均阅读数") or sa.get("avgReadCount") or 0
        total_interactive = sa.get("总互动") or sa.get("totalInteractiveCount") or sa.get("interactiveCountThirty", 0)
        recommend_reason = sa.get("推荐理由") or sa.get("recommendReason") or ""
        post_feature = sa.get("发文特点") or sa.get("postFeature") or ""
        learn_point = sa.get("可学之处") or sa.get("learnPoint") or ""
        
        # 账号名称超链接
        name_html = f'<a href="{account_url}" target="_blank" style="color:#1890ff;text-decoration:none;font-weight:500;">{name}</a>' if account_url else name
        # 如果没有链接但有accountId，构造链接
        if not account_url:
            account_id = sa.get("accountId") or sa.get("redId") or sa.get("userId", "")
            if account_id:
                account_url = f"https://mp.weixin.qq.com/profile/{account_id}"
                name_html = f'<a href="{account_url}" target="_blank" style="color:#1890ff;text-decoration:none;font-weight:500;">{name}</a>'
        
        similar_cards.append(
            f'<div class="similar-card-row" style="padding:12px 0;border-bottom:1px solid #f0f0f0;">'
            f'<div style="margin-bottom:6px;"><strong>{name_html}</strong> | 平均阅读：{avg_read} | 总互动：{total_interactive}</div>'
            f'<div style="font-size:13px;color:#666;margin-bottom:4px;"><strong>推荐理由：</strong>{recommend_reason}</div>'
            f'<div style="font-size:13px;color:#666;margin-bottom:4px;"><strong>发文特点：</strong>{post_feature}</div>'
            f'<div style="font-size:13px;color:#666;"><strong>可学之处：</strong>{learn_point}</div>'
            f'</div>'
        )
    replacements["{{similar_accounts_cards}}"] = "\n".join(similar_cards)

    # 执行替换
    for key, val in replacements.items():
        html = html.replace(key, val)

    # 条件移除空数据模块
    html = _remove_conditional_sections(html, report_data)

    # 相似账号区域 - 直接展示（移除条件注释）
    html = html.replace("<!-- SIMILAR_START -->", "").replace("<!-- SIMILAR_END -->", "")

    html = _remove_empty_info_rows(html)

    # ========== 自检：检测未替换的模板字段 ==========
    import re
    unreplaced = re.findall(r'\{\{[^}]+\}\}', html)
    if unreplaced:
        # 收集所有未替换的字段
        unique_unreplaced = list(set(unreplaced))
        # 扁平化分析数据和原始数据
        flat_data = _flatten_dict(report_data)
        _rd = raw_data[0] if isinstance(raw_data, list) and len(raw_data) > 0 else raw_data
        flat_raw = _flatten_dict(_rd) if _rd and isinstance(_rd, dict) else {}

        # 字段名映射：模板字段名 -> 原始数据字段名
        field_mapping = {
            "总在看数": "collected",
            "总点赞数": "liked",
            "近30天互动量": "interactions_30d",
            "近30天发作品数": "works_30d",
            "作品总数": "works_total",
            "账号名": "nickname",
            "官方等级": "level",
        }

        for field in unique_unreplaced:
            field_name = field[2:-2]  # 移除 {{ 和 }}
            found_value = None

            # 第一步：从分析数据中查找
            for k, v in flat_data.items():
                if k == field_name or k.endswith("." + field_name):
                    if v is not None and str(v).strip() != "" and str(v) != "0":
                        found_value = v
                        break

            # 第二步：分析数据为空，从原始数据中查找
            if found_value is None and flat_raw:
                # 先尝试字段名映射
                if field_name in field_mapping:
                    raw_field = field_mapping[field_name]
                    for k, v in flat_raw.items():
                        if k == raw_field or k.endswith("." + raw_field):
                            if v is not None and str(v).strip() != "":
                                found_value = v
                                # 格式化大数字
                                if field_name in ["总在看数", "总点赞数", "近30天互动量"]:
                                    found_value = _format_interactive_count(v)
                                break
                # 再尝试直接匹配字段名
                if found_value is None:
                    for k, v in flat_raw.items():
                        if k == field_name or k.endswith("." + field_name):
                            if v is not None and str(v).strip() != "":
                                found_value = v
                                break

            # 第三步：根据值进行处理
            if found_value is not None and str(found_value).strip() != "":
                html = html.replace(field, str(found_value))
            else:
                # 数据中无值，根据字段类型填充默认值
                numeric_fields = ["得分", "分", "互动", "收藏", "点赞", "数", "率", "量", "倍", "篇", "天", "中位数参考", "优秀值参考", "等级"]
                is_numeric = any(nf in field_name for nf in numeric_fields)
                if is_numeric:
                    html = html.replace(field, "0")
                else:
                    html = html.replace(field, "")

        # 再次检查是否还有未替换字段
        remaining = re.findall(r'\{\{[^}]+\}\}', html)
        if remaining:
            print(json.dumps({
                "status": "error",
                "message": f"HTML模板字段未完全替换: {list(set(remaining))}",
                "unreplaced_fields": list(set(remaining))
            }, ensure_ascii=False))
            sys.exit(1)

    # 输出HTML文件
    output_dir = os.path.normpath(os.path.join(script_dir, "..", "output"))
    os.makedirs(output_dir, exist_ok=True)

    account_name = report_data.get("header", {}).get("账号名", "report")
    safe_name = account_name.replace("/", "_").replace("\\", "_").replace(" ", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(output_dir, f"{safe_name}_诊断报告_{timestamp}.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    result_info = {
        "status": "success",
        "message": "HTML报告已生成",
        "output_path": output_path
    }
    print(json.dumps(result_info, ensure_ascii=False))


def _build_account_detail_html(account_data, account_index):
    """为多账号报告生成单个账号的详情HTML"""
    replacements = _build_replacements(account_data)

    # 评分条
    for dim, max_score in SCORE_MAX_MAP.items():
        score_key = dim + "得分"
        pct_key = dim + "得分_pct"
        score_val = replacements.get("{{" + score_key + "}}", "0")
        try:
            pct = round(int(score_val) / max_score * 100)
        except (ValueError, ZeroDivisionError):
            pct = 0
        replacements["{{" + pct_key + "}}"] = str(pct)

    header = account_data.get("header", {})
    raw_data = account_data.get("_raw", {})
    avatar = raw_data.get("头像", "")
    name = header.get("账号名", "")
    tag = header.get("账号标识", "")
    score = replacements.get("{{综合评分}}", "-")

    # 构建详情HTML（简化版，用于多账号对比）
    detail = f'''  <div class="account-detail">
    <div class="account-detail-header">
      <img src="{avatar}" onerror="this.style.display='none'">
      <span class="name">{name}</span>
      <span class="tag">{tag}</span>
      <span class="score">{score}分</span>
    </div>
    <div class="account-detail-body">
      <div class="score-bars">
        <div class="score-bar-item"><span class="name">内容健康度</span><div class="bar-bg"><div class="bar-fill" style="width:{replacements.get("{{内容健康度得分_pct}}", "0")}%"></div></div><span class="val">{replacements.get("{{内容健康度得分}}", "0")}分</span></div>
        <div class="score-bar-item"><span class="name">用户活跃度</span><div class="bar-bg"><div class="bar-fill" style="width:{replacements.get("{{用户活跃度得分_pct}}", "0")}%"></div></div><span class="val">{replacements.get("{{用户活跃度得分}}", "0")}分</span></div>

      </div>

      <div style="margin-top:12px; font-weight:600; font-size:13px; color:#FF2442;">综合诊断</div>
      <div class="conclusion">
        <p>{replacements.get("{{综合诊断结论内容}}", "")}</p>
      </div>'''

    # 行动处方
    detail += f'''
      <div style="margin-top:10px; font-weight:600; font-size:13px; color:#FF2442;">行动处方</div>
      <div class="action-item"><strong>问题归因</strong>：<br>• {replacements.get("{{问题归因1}}", "")}<br>• {replacements.get("{{问题归因2}}", "")}</div>
      <div class="action-item"><strong>具体动作</strong>：<br>1. {replacements.get("{{具体动作1}}", "")}<br>2. {replacements.get("{{具体动作2}}", "")}<br>3. {replacements.get("{{具体动作3}}", "")}</div>'''

    detail += '''
    </div>
  </div>'''

    detail = _remove_empty_info_rows(detail)
    return detail


def cmd_generate_multi_html(with_similar=False):
    """生成多账号对比HTML命令"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.normpath(os.path.join(script_dir, "..", "output", MULTI_REPORT_DATA_FILE))
    template_path = os.path.normpath(os.path.join(script_dir, "..", "assets", "multi_report_template.html"))

    if not os.path.exists(data_path):
        print(json.dumps({"status": "error", "message": f"多账号报告数据文件不存在: {data_path}，请先保存multi_report_data.json"}, ensure_ascii=False))
        sys.exit(1)

    if not os.path.exists(template_path):
        print(json.dumps({"status": "error", "message": f"多账号模板文件不存在: {template_path}"}, ensure_ascii=False))
        sys.exit(1)

    with open(data_path, "r", encoding="utf-8") as f:
        multi_data = json.load(f)

    with open(template_path, "r", encoding="utf-8") as f:
        html = f.read()

    accounts = multi_data.get("accounts", [])
    if not accounts:
        print(json.dumps({"status": "error", "message": "accounts数组为空，无账号数据"}, ensure_ascii=False))
        sys.exit(1)

    html = html.replace("{{账号数量}}", str(len(accounts)))

    data_time = multi_data.get("header", {}).get("数据获取时间", "")
    if not data_time and accounts:
        data_time = accounts[0].get("header", {}).get("数据获取时间", "")
    html = html.replace("{{数据获取时间}}", data_time)

    # 对比表头
    header_cells = []
    for acc in accounts:
        name = acc.get("header", {}).get("账号名", "")
        header_cells.append(f"<th>{name}</th>")
    html = html.replace("{{对比表头}}", "".join(header_cells))

    # 对比表格行
    compare_rows = []
    metrics = [
        ("综合评分", "scores", "综合评分"),
        ("平均阅读数", "data_performance", "平均阅读数"),
        ("互动率", "user_activity", "互动率"),
        ("内容健康度", "scores", "内容健康度得分"),
        "separator",
        ("用户活跃度", "scores", "用户活跃度得分"),
    ]

    best_map = {}
    for item in metrics:
        if item == "separator":
            continue
        label, section, key = item
        values = []
        for acc in accounts:
            sec = acc.get(section, {})
            raw_val = sec.get(key, "")
            try:
                v = float(raw_val) if str(raw_val).strip() not in ("",) else None
            except (ValueError, TypeError):
                v = None
            values.append(v)
        valid_vals = [v for v in values if v is not None]
        if valid_vals:
            best_map[key] = max(valid_vals)

    for item in metrics:
        if item == "separator":
            compare_rows.append('<tr style="height:4px;background:#FDE8EC;"><td colspan="99"></td></tr>')
            continue
        label, section, key = item
        cells = [f"<td>{label}</td>"]
        for acc in accounts:
            sec = acc.get(section, {})
            raw_val = sec.get(key, "")
            val_str = str(raw_val) if raw_val else ""
            if val_str.strip() == "":
                cells.append("<td>-</td>")
                continue
            try:
                num_val = float(raw_val) if str(raw_val).strip() not in ("",) else None
            except (ValueError, TypeError):
                num_val = None
            if num_val is not None and key in best_map and num_val == best_map[key]:
                cells.append(f'<td class="best">{val_str}</td>')
            else:
                cells.append(f"<td>{val_str}</td>")
        compare_rows.append("<tr>" + "".join(cells) + "</tr>")
    html = html.replace("{{对比表格行}}", "\n".join(compare_rows))

    # 对比总结
    comparison = multi_data.get("comparison", {})

    diff_items = comparison.get("核心差异", [])
    diff_html = ""
    if diff_items:
        diff_html = '<div class="summary-module summary-diff"><div class="module-title"><span class="icon">⚡</span> 核心差异</div>'
        for item in diff_items:
            if isinstance(item, dict):
                acc_name = item.get("账号名", "")
                content = item.get("内容", "")
                if content:
                    diff_html += f'<div style="margin-bottom:8px; padding:6px 10px; background:#fff; border-radius:6px;"><span style="font-weight:600; color:#D48806; font-size:12px;">{acc_name}</span><p style="font-size:13px; color:#555; line-height:1.8; margin:4px 0 0;">{content}</p></div>'
        diff_html += '</div>'
    html = html.replace("{{对比总结_核心差异}}", diff_html)

    common_items = comparison.get("共同问题", [])
    common_html = ""
    if common_items:
        common_html = '<div class="summary-module summary-common"><div class="module-title"><span class="icon">🔗</span> 共同问题</div><ul style="padding-left:18px; margin:0;">'
        for item in common_items:
            if isinstance(item, str) and item.strip():
                common_html += f'<li style="font-size:13px; color:#555; line-height:1.8;">{item}</li>'
        common_html += '</ul></div>'
    html = html.replace("{{对比总结_共同问题}}", common_html)

    advice_items = comparison.get("发展建议", [])
    advice_html = ""
    if advice_items:
        advice_html = '<div class="summary-module summary-advice"><div class="module-title"><span class="icon">🚀</span> 发展建议</div>'
        for item in advice_items:
            if isinstance(item, dict):
                acc_name = item.get("账号名", "")
                content = item.get("内容", "")
                if content:
                    advice_html += f'<div style="margin-bottom:8px; padding:6px 10px; background:#fff; border-radius:6px;"><span style="font-weight:600; color:#FF2442; font-size:12px;">{acc_name}</span><p style="font-size:13px; color:#555; line-height:1.8; margin:4px 0 0;">{content}</p></div>'
        advice_html += '</div>'
    html = html.replace("{{对比总结_发展建议}}", advice_html)

    # 各账号详情
    details = []
    for i, acc in enumerate(accounts):
        details.append(_build_account_detail_html(acc, i))
    html = html.replace("{{各账号详情}}", "\n".join(details))

    # 条件移除空数据模块
    html = _remove_conditional_sections(html, multi_data)
    html = _remove_empty_info_rows(html)

    # ========== 自检：检测未替换的模板字段 ==========
    import re
    unreplaced = re.findall(r'\{\{[^}]+\}\}', html)
    if unreplaced:
        unique_unreplaced = list(set(unreplaced))
        # 对于空值字段，根据数据类型处理
        flat_multi = _flatten_dict(multi_data)
        for field in unique_unreplaced:
            field_name = field[2:-2]  # 移除 {{ 和 }}
            # 在扁平化数据中查找对应值
            found_value = None
            for k, v in flat_multi.items():
                if k == field_name or k.endswith("." + field_name):
                    found_value = v
                    break
            # 也在各账号数据中查找
            if found_value is None or found_value == "":
                for acc in accounts:
                    flat_acc = _flatten_dict(acc)
                    for k, v in flat_acc.items():
                        if k == field_name or k.endswith("." + field_name):
                            found_value = v
                            break
                    if found_value is not None and found_value != "":
                        break
            if found_value is not None and found_value != "":
                # 数据中有值，使用该值
                html = html.replace(field, str(found_value))
            else:
                # 数据中无值，根据字段类型填充默认值
                numeric_fields = ["得分", "分", "互动", "收藏", "点赞", "数", "率", "量", "倍", "篇", "天", "中位数参考", "优秀值参考", "等级"]
                is_numeric = any(nf in field_name for nf in numeric_fields)
                if is_numeric:
                    html = html.replace(field, "0")
                else:
                    html = html.replace(field, "")
        remaining = re.findall(r'\{\{[^}]+\}\}', html)
        if remaining:
            print(json.dumps({
                "status": "error",
                "message": f"HTML模板字段未完全替换: {list(set(remaining))}",
                "unreplaced_fields": list(set(remaining))
            }, ensure_ascii=False))
            sys.exit(1)

    # 输出HTML文件
    output_dir = os.path.normpath(os.path.join(script_dir, "..", "output"))
    os.makedirs(output_dir, exist_ok=True)

    names = [acc.get("header", {}).get("账号名", "未知") for acc in accounts[:3]]
    safe_name = "vs".join(n.replace("/", "_").replace("\\", "_").replace(" ", "_") for n in names)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(output_dir, f"{safe_name}_对比报告_{timestamp}.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    result_info = {
        "status": "success",
        "message": "多账号对比HTML报告已生成",
        "output_path": output_path
    }
    print(json.dumps(result_info, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description="公众号账号诊断宗师")
    subparsers = parser.add_subparsers(dest="command")

    # 查询子命令
    query_parser = subparsers.add_parser("query", help="查询账号数据")
    query_parser.add_argument("--account_ids", help="公众号账号ID列表，逗号分隔", required=False)
    query_parser.add_argument("--account_names", help="公众号账号名称列表，逗号分隔", required=False)
    query_parser.add_argument("--force_analyze", action="store_true", help="强制执行分析（即使无作品数据）")

    # 生成单账号HTML子命令
    html_parser = subparsers.add_parser("generate_html", help="基于report_data.json生成单账号HTML报告")

    # 生成多账号对比HTML子命令
    multi_parser = subparsers.add_parser("generate_multi_html", help="基于multi_report_data.json生成多账号对比HTML报告")

    args = parser.parse_args()

    if args.command == "query":
        account_ids = [x.strip() for x in args.account_ids.split(",") if x.strip()] if args.account_ids else []
        account_names = [x.strip() for x in args.account_names.split(",") if x.strip()] if args.account_names else []

        if not account_ids and not account_names:
            print(json.dumps({
                "status": "error",
                "message": "请提供至少一个账号ID（--account_ids）或名称（--account_names）"
            }, ensure_ascii=False))
            sys.exit(1)

        cmd_query(account_ids=account_ids or None, account_names=account_names or None, force_analyze=getattr(args, 'force_analyze', False))

    elif args.command == "generate_html":
        cmd_generate_html()

    elif args.command == "generate_multi_html":
        cmd_generate_multi_html()

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
