"""scoring.py — 公众号账号评分引擎

职责：作品数据辅助函数、四维度评分、等级判定、格式化工具。
被 analyzer.py 和 report.py 调用。
"""

from datetime import datetime


# ════════════════════════════════════════════════════════════
#  v4.1 分类自适应评分配置
# ════════════════════════════════════════════════════════════

# 分类关键词库（description + 作品标题匹配）
CATEGORY_KEYWORDS = {
    "news_politics": [
        "时政", "新闻", "决策", "政策", "国际", "局势", "天下", "时事", "政治",
        "党", "政府", "两会", "战略", "策赢", "决胜", "环球", "观察", "人民日报",
    ],
    "finance_opinion": [
        "财经", "投资", "经济", "金融", "商业", "股市", "理财", "资本", "市场",
        "A股", "基金", "证券", "宏观经济", "吴晓波",
    ],
    "emotion_lifestyle": [
        "情感", "读书", "生活", "美文", "故事", "深夜", "陪伴", "观点", "洞见",
        "成长", "心灵", "温暖", "治愈", "励志", "十点",
    ],
    "knowledge_edu": [
        "知识", "教育", "学习", "科普", "书店", "文化", "历史", "学术", "研究",
        "阅读", "人文",
    ],
    "entertainment": [
        "搞笑", "娱乐", "段子", "视频", "明星", "八卦", "综艺", "电影", "追剧",
    ],
}

# 分类名称（中文映射，用于报告输出）
CATEGORY_NAMES = {
    "news_politics": "时政新闻",
    "finance_opinion": "财经理政",
    "emotion_lifestyle": "情感生活",
    "knowledge_edu": "知识教育",
    "entertainment": "娱乐休闲",
    "general": "综合",
}

# 各分类的四维度权重（总和必须=1.00）
CATEGORY_WEIGHTS = {
    "general":           {"content_health": 0.25, "user_activity": 0.20, "core_data": 0.40, "operation_compliance": 0.15},
    "news_politics":     {"content_health": 0.25, "user_activity": 0.08, "core_data": 0.52, "operation_compliance": 0.15},
    "finance_opinion":   {"content_health": 0.25, "user_activity": 0.15, "core_data": 0.45, "operation_compliance": 0.15},
    "emotion_lifestyle": {"content_health": 0.25, "user_activity": 0.25, "core_data": 0.35, "operation_compliance": 0.15},
    "knowledge_edu":     {"content_health": 0.30, "user_activity": 0.20, "core_data": 0.35, "operation_compliance": 0.15},
    "entertainment":     {"content_health": 0.20, "user_activity": 0.15, "core_data": 0.45, "operation_compliance": 0.20},
}

# 各分类的用户活跃度保底值（均阅阈值 → 百分制下限）
CATEGORY_ACTIVITY_FLOOR = {
    "news_politics":     {50000: 70.0, 30000: 55.0, 10000: 40.0},
    "finance_opinion":   {50000: 55.0, 30000: 45.0, 10000: 30.0},
    # 其他分类使用 general 保底
}

# general 保底（默认）
_ACTIVITY_FLOOR_GENERAL = {50000: 50.0, 30000: 40.0, 10000: 30.0}

# 各分类的用户活跃度子项阈值（互动率、评论密度、分享率）
# 格式：{score_value: threshold}，从高到低匹配
CATEGORY_ACTIVITY_THRESHOLDS = {
    "general": {
        "interaction": {1.0: 0.05, 0.7: 0.02, 0.4: 0.01},
        "comment":     {1.0: 0.0005, 0.7: 0.0002, 0.4: 0.00005},
        "share":       {1.0: 0.02, 0.7: 0.005, 0.4: 0.002},
    },
    "news_politics": {
        "interaction": {1.0: 0.03, 0.7: 0.012, 0.4: 0.006},
        "comment":     {1.0: 0.0002, 0.7: 0.00008, 0.4: 0.00002},
        "share":       {1.0: 0.015, 0.7: 0.003, 0.4: 0.001},
    },
    "finance_opinion": {
        "interaction": {1.0: 0.04, 0.7: 0.015, 0.4: 0.008},
        "comment":     {1.0: 0.0003, 0.7: 0.0001, 0.4: 0.00003},
        "share":       {1.0: 0.015, 0.7: 0.004, 0.4: 0.0015},
    },
    "emotion_lifestyle": {
        "interaction": {1.0: 0.05, 0.7: 0.02, 0.4: 0.01},
        "comment":     {1.0: 0.0005, 0.7: 0.0002, 0.4: 0.00005},
        "share":       {1.0: 0.02, 0.7: 0.005, 0.4: 0.002},
    },
    "knowledge_edu": {
        "interaction": {1.0: 0.04, 0.7: 0.02, 0.4: 0.01},
        "comment":     {1.0: 0.0004, 0.7: 0.00015, 0.4: 0.00004},
        "share":       {1.0: 0.02, 0.7: 0.005, 0.4: 0.002},
    },
    "entertainment": {
        "interaction": {1.0: 0.06, 0.7: 0.03, 0.4: 0.015},
        "comment":     {1.0: 0.0005, 0.7: 0.0002, 0.4: 0.00005},
        "share":       {1.0: 0.03, 0.7: 0.01, 0.4: 0.003},
    },
}


def _classify_account_category(account_type, signature, works, verify_name=""):
    """v4.1: 根据账号信息自动识别内容分类

    三级信号融合：accountType → description关键词 → 作品标题关键词 + 互动结构验证
    返回：{"category": str, "confidence": float, "category_name": str, "signals": dict}
    """
    signals = {"account_type": account_type, "desc_match": "", "title_match": "", "behavior_match": ""}
    scores_by_cat = {}

    # 第一级：accountType 字段直接映射（若非空）
    _type_map = {
        "新闻媒体": "news_politics", "时政": "news_politics", "新闻": "news_politics",
        "财经": "finance_opinion", "金融": "finance_opinion",
        "情感": "emotion_lifestyle", "生活": "emotion_lifestyle",
        "教育": "knowledge_edu", "文化": "knowledge_edu",
        "娱乐": "entertainment", "影视": "entertainment",
    }
    if account_type and account_type.strip():
        for key, cat in _type_map.items():
            if key in account_type:
                return {"category": cat, "confidence": 0.95, "category_name": CATEGORY_NAMES.get(cat, "综合"),
                        "signals": {**signals, "account_type": account_type}}

    # 第二级：description 关键词匹配
    desc = (signature or "").lower()
    desc_scores = {}
    desc_match_parts = []
    for cat, keywords in CATEGORY_KEYWORDS.items():
        hits = [kw for kw in keywords if kw.lower() in desc]
        if hits:
            desc_scores[cat] = len(hits)
            desc_match_parts.append(f"{cat}:[{','.join(hits[:3])}]")
    if desc_match_parts:
        signals["desc_match"] = "; ".join(desc_match_parts)

    # 第三级：作品标题关键词统计
    title_scores = {}
    title_match_parts = []
    if works:
        titles = [w.get("title", "") for w in works[:10] if w.get("title")]
        for cat, keywords in CATEGORY_KEYWORDS.items():
            hit_count = sum(1 for t in titles if any(kw.lower() in t.lower() for kw in keywords))
            if hit_count > 0:
                title_scores[cat] = hit_count / max(len(titles), 1)
                title_match_parts.append(f"{cat}:{hit_count}/{len(titles)}")
    if title_match_parts:
        signals["title_match"] = "; ".join(title_match_parts)

    # 第四级：互动结构验证
    behavior_scores = {}
    if works:
        total_reads = sum(w.get("clicksCount", 0) or 0 for w in works)
        total_comments = sum(w.get("commentCount", 0) or 0 for w in works)
        avg_read = total_reads / len(works) if works else 0
        comment_rate = total_comments / total_reads if total_reads > 0 else 0
        # 评论率极低 + 高阅读 → 时政号特征
        if avg_read >= 10000 and comment_rate < 0.0001:
            behavior_scores["news_politics"] = 0.8
            signals["behavior_match"] = f"高均阅({int(avg_read)})+极低评论率({comment_rate:.4%})"
        elif avg_read >= 10000 and comment_rate < 0.0003:
            behavior_scores["finance_opinion"] = 0.6
            signals["behavior_match"] = f"高均阅({int(avg_read)})+低评论率({comment_rate:.4%})"
        elif comment_rate >= 0.0003:
            behavior_scores["emotion_lifestyle"] = 0.5
            signals["behavior_match"] = f"评论率较高({comment_rate:.4%})"

    # 综合加权：description(0.5) + title(0.3) + behavior(0.2)
    # 使用 CATEGORY_KEYWORDS 的插入顺序作为等分 tie-break 优先级（确定性）
    all_cats_ordered = []
    for cat in list(CATEGORY_KEYWORDS.keys()):
        if cat in desc_scores or cat in title_scores or cat in behavior_scores:
            if cat not in all_cats_ordered:
                all_cats_ordered.append(cat)
    for cat in all_cats_ordered:
        d = desc_scores.get(cat, 0)
        # description命中数归一化（最多3个即满分）
        d_norm = min(d / 3, 1.0) if d > 0 else 0
        t_norm = title_scores.get(cat, 0)
        b_norm = behavior_scores.get(cat, 0)
        scores_by_cat[cat] = d_norm * 0.5 + min(t_norm, 1.0) * 0.3 + b_norm * 0.2

    if not scores_by_cat:
        return {"category": "general", "confidence": 1.0, "category_name": "综合", "signals": signals}

    # 等分时按 CATEGORY_KEYWORDS 插入顺序优先（确定性 tie-break）
    best_cat = max(all_cats_ordered, key=lambda c: scores_by_cat.get(c, 0))
    best_score = scores_by_cat[best_cat]

    # 置信度 >= 0.3 即确认分类（description有1个关键词命中即可）
    if best_score >= 0.3:
        return {"category": best_cat, "confidence": round(best_score, 2),
                "category_name": CATEGORY_NAMES.get(best_cat, "综合"), "signals": signals}

    return {"category": "general", "confidence": 1.0, "category_name": "综合", "signals": signals}


# ════════════════════════════════════════════════════════════
#  作品数据辅助函数
# ════════════════════════════════════════════════════════════

def _work_read(w):
    """获取作品阅读数（兼容多种字段名）"""
    for key in ("clicksCount", "readCount", "readNum"):
        val = w.get(key)
        if val is not None:
            return val
    return 0


def _work_like(w):
    """获取作品点赞数"""
    for key in ("likeCount", "likedCount"):
        val = w.get(key)
        if val is not None:
            return val
    return 0


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


# ════════════════════════════════════════════════════════════
#  基准数据与交互结构
# ════════════════════════════════════════════════════════════

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


def _calc_avg_read(works):
    """从作品列表计算平均阅读数

    10万+文章按100001计入均值：该值为微信阅读量显示上限的截断值，
    真实阅读量≥10万，属于保守下界。排除爆款文章会系统性低估头部账号
    （如爆款率25%的账号）的平均阅读水平。
    """
    if not works:
        return 0
    reads = [_work_read(w) for w in works if _work_read(w) > 0]
    return int(sum(reads) / len(reads)) if reads else 0


def _calc_viral_ratio(works):
    """计算爆款率：10万+阅读文章占有效作品的比例

    阅读量>=100001 即微信生态的"10万+"爆款（100001为截断下界，真实值更高）。
    """
    if not works:
        return 0
    valid = [_work_read(w) for w in works if _work_read(w) > 0]
    if not valid:
        return 0
    viral_count = sum(1 for r in valid if r >= 100001)
    return viral_count / len(valid)


# ════════════════════════════════════════════════════════════
#  四维度评分函数
# ════════════════════════════════════════════════════════════

def _score_content_health(works, signature, verify_name, account_type):
    """内容健康度评分（原始分0-10分，综合评分时由analyzer按 原始分/10×100 转为百分制，权重按分类自适应，默认25%）

    更新稳定性(15%): 10分=日更，8分=周更3-5次，5分=周更1-2次，<5=不规律
    内容垂直度(15%): 10分=极度垂直单一领域，7分=主领域+偶尔跨界，<5=内容杂乱
    原创能力(10%): 10分=90%+原创，8分=70-90%原创，5分=50-70%，<5=大量转载
    质量稳定性(10%): 阅读量波动系数（排除10万+截断值后计算），波动≤35%得高分；全部10万+直接满分
    内容深度(5%): 长文比例、专业引用、独家观点
    形式创新(5%): 多媒体运用、互动形式、排版创新
    总权重=60%→归一化为0-10分→analyzer转换为百分制(综合评分权重25%)
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
    # accountType是平台分类标签（如"人文资讯"），存在即代表平台已确认账号领域定位，
    # 给基础分0.75；标题命中分类关键词时作为增强，避免整串匹配失效导致误判
    vertical_score = 0.75  # 有分类标签的基础分（公众号通常有明确定位）
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
            vertical_score = 0.85
        elif match_ratio >= 0.4:
            vertical_score = 0.75
        # match_ratio < 0.4 时维持基础分：分类标签存在即有明确定位

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
        original_score = 0.70
    else:
        # 无原创标记：不代表非原创，给较高中等分(0.75)，避免错误惩罚优质账号
        original_score = 0.75

    # 质量稳定性(10%): 基于阅读量变异系数(标准差/均值)
    # 排除10万+截断值(100001)：该值非真实阅读量，计入会虚增波动、反向惩罚爆款账号；
    # 全部为10万+的账号直接给满分（常态爆款即顶级稳定）
    valid_reads_all = [_work_read(w) for w in works if _work_read(w) > 0]
    viral_all = bool(valid_reads_all) and all(r >= 100001 for r in valid_reads_all)
    if viral_all:
        quality_stability = 1.0
        cv = 0
    else:
        reads = [_work_read(w) for w in works if 0 < _work_read(w) < 100001]
        if len(reads) >= 3:
            import statistics
            mean_read = statistics.mean(reads)
            std_read = statistics.stdev(reads)
            cv = std_read / mean_read if mean_read > 0 else 1
            if cv <= 0.35:
                quality_stability = 1.0
            elif cv <= 0.6:
                quality_stability = 0.6
            elif cv <= 0.9:
                quality_stability = 0.3
            else:
                quality_stability = 0.1
        else:
            quality_stability = 0.5
            cv = 0

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
        "总分": round(raw_score * 3, 1)  # 兼容字段，analyzer实际使用原始分/10×100转百分制
    }


def _score_user_activity(works, interaction_rate=0, category="general"):
    """用户活跃度评分（原始分0-10分，综合评分时由analyzer按 原始分/10×100 转为百分制，权重按分类自适应）

    v4.1: 根据账号分类自动调整互动率/评论密度/分享率的评分阈值
    互动率(20%): (点赞+在看+留言)/阅读量
    留言质量(10%): 评论密度（公众号评论需审核）
    分享传播力(10%): 分享率
    阅读完成率(5%): 基于互动率+绝对互动量推断
    活跃时段集中度(5%): 推送时间固定性
    总权重=50%→归一化为0-10分→analyzer转换为百分制
    """
    if not works:
        return {
            "互动率": 0, "留言质量": 0, "分享传播力": 0,
            "阅读完成率": 0, "活跃时段集中度": 0,
            "原始分": 0, "总分": 0,
            "_extra": {"interaction_rate": 0, "comment_density": 0, "category": category}
        }

    # 计算各项指标
    total_reads = sum(_work_read(w) for w in works)
    total_likes = sum(_work_like(w) for w in works)
    total_comments = sum(_work_comment(w) for w in works)
    total_shares = sum(_work_share(w) for w in works)
    total_watches = sum(w.get("watchCount") or 0 for w in works)

    # v4.1: 获取分类对应的阈值配置
    thresholds = CATEGORY_ACTIVITY_THRESHOLDS.get(category, CATEGORY_ACTIVITY_THRESHOLDS["general"])
    inter_thresh = thresholds["interaction"]
    comment_thresh = thresholds["comment"]
    share_thresh = thresholds["share"]

    # 互动率(20%): (点赞+评论+分享+在看)/阅读数 — 分类自适应阈值
    if total_reads > 0:
        inter_rate = (total_likes + total_comments + total_shares + total_watches) / total_reads
    else:
        inter_rate = 0
    if inter_rate >= inter_thresh[1.0]:
        interaction_score = 1.0
    elif inter_rate >= inter_thresh[0.7]:
        interaction_score = 0.7
    elif inter_rate >= inter_thresh[0.4]:
        interaction_score = 0.4
    else:
        interaction_score = 0.1

    # 留言质量(10%): 评论数/阅读数 — 分类自适应阈值
    # 公众号评论需作者审核，评论密度远低于开放平台
    comment_density = total_comments / total_reads if total_reads > 0 else 0
    if comment_density >= comment_thresh[1.0]:
        comment_score = 1.0
    elif comment_density >= comment_thresh[0.7]:
        comment_score = 0.7
    elif comment_density >= comment_thresh[0.4]:
        comment_score = 0.4
    else:
        comment_score = 0.1

    # 分享传播力(10%): 分享数/阅读数 — 分类自适应阈值
    share_rate = total_shares / total_reads if total_reads > 0 else 0
    if share_rate >= share_thresh[1.0]:
        share_score = 1.0
    elif share_rate >= share_thresh[0.7]:
        share_score = 0.7
    elif share_rate >= share_thresh[0.4]:
        share_score = 0.4
    else:
        share_score = 0.1

    # 阅读完成率(5%): 无法精确获取，根据互动率+绝对互动量推断
    # 大号绝对互动量极高（100万+总互动），阅读完成率不会低于0.6
    read_completion = min(1.0, inter_rate * 8) if inter_rate > 0 else 0.3
    if total_reads > 0:
        total_interactions = total_likes + total_comments + total_shares + total_watches
        if total_interactions >= 100000:
            read_completion = max(read_completion, 0.6)
        if total_interactions >= 500000:
            read_completion = max(read_completion, 0.7)

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
        "总分": round(raw_score * 2.5, 1),  # 兼容字段，analyzer实际使用原始分/10×100转百分制
        "_extra": {
            "interaction_rate": round(inter_rate * 100, 2),
            "comment_density": round(comment_density * 100, 4),
            "category": category,
        }
    }


def _score_core_data(works, avg_read_count, category="general"):
    """内容核心数据表现评分（0-31分制，综合评分时转换为百分制）

    v4.1: 根据账号分类调整互动类子项的评分灵敏度
    阅读数表现(8分): 平均阅读数区间分段
    点赞数表现(6分): 平均点赞数+点赞率
    评论数表现(4分): 平均评论数+评论率
    互动率表现(3分): 综合互动率
    发布时间合理性(2分): 黄金时段发文比例
    爆款产出力(8分): 10万+阅读文章占比（爆款率）
    满分=31分，转换为百分制：raw/31*100
    """
    if not works:
        return {
            "阅读数表现": 0, "点赞数表现": 0, "评论数表现": 0,
            "互动率表现": 0, "发布时间合理性": 0,
            "爆款产出力": 0,
            "原始分": 0, "总分": 0
        }

    # 1. 阅读数表现(8分) - 基于公众号行业真实水平校准
    # 行业参考：普通账号500-3000，良好账号3000-1万，优质账号1-5万，顶尖账号5万+
    avg_read = avg_read_count or 0
    if avg_read >= 100000:
        read_score = 8    # 超顶级，如人民日报等媒体大号
    elif avg_read >= 80000:
        read_score = 7.5  # 行业顶尖（8万+）
    elif avg_read >= 50000:
        read_score = 6.5  # 行业顶尖（5万+）
    elif avg_read >= 30000:
        read_score = 5    # 行业优秀（3-5万）
    elif avg_read >= 20000:
        read_score = 4    # 行业优秀（2-3万）
    elif avg_read >= 10000:
        read_score = 3    # 行业良好（1-2万）
    elif avg_read >= 5000:
        read_score = 2    # 中等水平（5000-1万）
    elif avg_read >= 1000:
        read_score = 1    # 偏低
    else:
        read_score = 0.5  # 极低

    # 2. 点赞数表现(6分)
    total_likes = sum(_work_like(w) for w in works)
    total_reads = sum(_work_read(w) for w in works)
    avg_likes = total_likes / len(works) if works else 0
    like_rate = total_likes / total_reads if total_reads > 0 else 0

    if avg_likes >= 3000 or like_rate >= 0.03:
        like_score = 6
    elif avg_likes >= 1000 or like_rate >= 0.015:
        like_score = 5
    elif avg_likes >= 300 or like_rate >= 0.005:
        like_score = 3
    elif avg_likes >= 100 or like_rate >= 0.003:
        like_score = 1.5
    else:
        like_score = 1

    # 3. 评论数表现(4分)
    # 微信公众号评论生态校准：评论需经作者审核展示，大号篇均5-30条已属优秀，
    # 旧阈值(500+/200+/100+)对标开放平台(抖音/小红书)，严重低估公众号头部账号
    total_comments = sum(_work_comment(w) for w in works)
    avg_comments = total_comments / len(works) if works else 0
    comment_rate = total_comments / total_reads if total_reads > 0 else 0

    if avg_comments >= 20 or comment_rate >= 0.0005:
        comment_score = 4
    elif avg_comments >= 10 or comment_rate >= 0.0003:
        comment_score = 3
    elif avg_comments >= 5 or comment_rate >= 0.0001:
        comment_score = 2
    elif avg_comments >= 2:
        comment_score = 1
    else:
        comment_score = 0.5

    # 4. 互动率表现(3分) - 基于公众号行业真实水平校准
    # 行业参考：普通1-3%，良好3-8%，优秀8-15%，顶尖15%+
    total_shares = sum(_work_share(w) for w in works)
    total_watches = sum(w.get("watchCount") or 0 for w in works)
    inter_rate = (total_likes + total_comments + total_shares + total_watches) / total_reads if total_reads > 0 else 0

    if inter_rate >= 0.10:    # 顶尖：10%+（极少账号能达到）
        inter_score = 3
    elif inter_rate >= 0.05:   # 优秀：5-10%
        inter_score = 2.5
    elif inter_rate >= 0.03:  # 良好：3-5%
        inter_score = 2
    elif inter_rate >= 0.015: # 中等：1.5-3%
        inter_score = 1.5
    elif inter_rate >= 0.005:  # 偏低：0.5-1.5%
        inter_score = 1
    else:
        inter_score = 0

    # 5. 发布时间合理性(2分): 黄金时段发文比例
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
            time_score = 2
        elif golden_ratio >= 0.3:
            time_score = 1.5
        elif golden_ratio >= 0.1:
            time_score = 1
        else:
            time_score = 0
    else:
        time_score = 0.5

    # 6. 爆款产出力(8分): 10万+阅读文章占比（微信生态顶级传播力信号）
    # 10万+是微信阅读量显示上限，爆款率>20%即为头部账号，40%+为超级头部
    viral_ratio = _calc_viral_ratio(works)
    if viral_ratio >= 0.40:
        viral_score = 8
    elif viral_ratio >= 0.30:
        viral_score = 7
    elif viral_ratio >= 0.25:
        viral_score = 6.5
    elif viral_ratio >= 0.20:
        viral_score = 6
    elif viral_ratio >= 0.10:
        viral_score = 4.5
    elif viral_ratio >= 0.05:
        viral_score = 3
    elif viral_ratio >= 0.02:
        viral_score = 2
    elif viral_ratio > 0:
        viral_score = 1
    else:
        viral_score = 0

    # v4.1: 分类感知的互动增益
    # 时政/新闻号互动天然低（读者被动消费），对互动类子项给予分类增益
    # 增益后不超过各子项满分上限
    _engagement_boost = {
        "news_politics": 2.0,     # 时政号互动分数×2（上限封顶）
        "finance_opinion": 1.5,   # 财经号互动分数×1.5
    }
    boost = _engagement_boost.get(category, 1.0)
    if boost > 1.0:
        like_score = min(6, like_score * boost)
        comment_score = min(4, comment_score * boost)
        inter_score = min(3, inter_score * boost)

    raw_score = round(
        read_score + like_score + comment_score + inter_score + time_score
        + viral_score, 1
    )

    return {
        "阅读数表现": read_score,
        "点赞数表现": like_score,
        "评论数表现": comment_score,
        "互动率表现": inter_score,
        "发布时间合理性": time_score,
        "爆款产出力": viral_score,
        "爆款率": round(viral_ratio * 100, 1),
        "原始分": raw_score,
        "总分": round(raw_score / 31 * 100, 1)  # 转换为百分制
    }


def _score_operation_compliance(works, verify_name):
    """运营规范性评分（直接0-10分，综合评分权重按分类自适应，默认15%）

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


# ════════════════════════════════════════════════════════════
#  等级判定
# ════════════════════════════════════════════════════════════

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

    评级标准（基于公众号行业真实水平校准）：
    公众号生态中均阅3万+即属top 0.1%头部，80分+即为S级标杆
    S级(行业标杆) >=80：均阅3万+、稳定日更、高互动的顶尖账号
    A级(优质账号) >=70：均阅1-3万、持续优质内容的优质账号
    B级(健康账号) >=60：正常运营、有稳定输出的健康账号
    C级(中等账号) >=50：基础运营待提升
    D级(亚健康)   >=40：运营不稳定或互动偏低
    E级(问题账号)  <40：严重问题需全面诊断
    """
    if score >= 80:
        return "🏆 标杆账号", "S级"
    elif score >= 70:
        return "⭐ 优质账号", "A级"
    elif score >= 60:
        return "✅ 健康账号", "B级"
    elif score >= 50:
        return "📊 中等账号", "C级"
    elif score >= 40:
        return "⚠️ 亚健康账号", "D级"
    else:
        return "❌ 问题账号", "E级"
