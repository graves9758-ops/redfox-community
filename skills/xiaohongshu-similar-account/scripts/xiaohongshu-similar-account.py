#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小红书账号推荐脚本
功能：调用API查询对标账号
⚠️ 严禁任何联网搜索：本脚本不使用web_search等联网查询工具，所有数据仅来源于API接口
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.error
import ssl


# 标准赛道分类
STANDARD_CATEGORIES = [
    "综合全部", "出行代步", "休闲爱好", "影视娱乐", "数码科技",
    "医疗保健", "综合杂项", "星座情感", "时尚穿搭",
    "婚庆婚礼", "拍摄记录", "学习教育", "化妆美容",
    "居家装修", "旅行度假", "亲子育儿", "个人护理",
    "美味佳肴", "职业发展", "宠物天地", "潮流鞋包",
    "日常生活", "科学探索", "新闻资讯", "体育锻炼"
]

# 标准账号等级（7个）
STANDARD_LEVELS = ["明星", "品牌", "企业", "头部kol", "腰部kol", "尾部kol", "素人"]

# 账号等级中文到标准分类的映射
LEVEL_MAPPING = {
    # 明星相关
    "明星": "明星",
    "艺人": "明星",
    "爱豆": "明星",
    "idol": "明星",

    # 品牌相关
    "品牌": "品牌",
    "牌子": "品牌",

    # 企业相关
    "企业": "企业",
    "公司": "企业",
    "商家": "企业",
    "官方号": "企业",

    # 头部KOL相关
    "头部kol": "头部kol",
    "头部": "头部kol",
    "头部达人": "头部kol",
    "大v": "头部kol",
    "大号": "头部kol",
    "百万粉": "头部kol",

    # 腰部KOL相关
    "腰部kol": "腰部kol",
    "腰部": "腰部kol",
    "腰部达人": "腰部kol",
    "中号": "腰部kol",
    "十万粉": "腰部kol",

    # 尾部KOL相关
    "尾部kol": "尾部kol",
    "尾部": "尾部kol",
    "尾部达人": "尾部kol",
    "小号": "尾部kol",
    "万粉": "尾部kol",

    # 素人相关
    "素人": "素人",
    "普通人": "素人",
    "小白": "素人",
    "新手": "素人",
    "新人": "素人",
    "新手博主": "素人",
    "个人号": "素人"
}

# 用户常用赛道词到标准分类的映射
CATEGORY_MAPPING = {
    # 个人护理相关
    "护肤": "个人护理",
    "美容": "个人护理",
    "护肤美容": "个人护理",
    "护肤品": "个人护理",
    "保养": "个人护理",
    "面部护理": "个人护理",
    "皮肤": "个人护理",

    # 美妆相关
    "美妆": "化妆美容",
    "化妆": "化妆美容",
    "彩妆": "化妆美容",
    "平价美妆": "化妆美容",
    "美妆教程": "化妆美容",

    # 时尚穿搭相关
    "穿搭": "时尚穿搭",
    "时尚": "时尚穿搭",
    "服装": "时尚穿搭",
    "衣服": "时尚穿搭",
    "搭配": "时尚穿搭",
    "潮流穿搭": "时尚穿搭",

    # 美食相关
    "美食": "美味佳肴",
    "做饭": "美味佳肴",
    "烹饪": "美味佳肴",
    "菜谱": "美味佳肴",
    "烘焙": "美味佳肴",
    "探店": "美味佳肴",
    "餐厅": "美味佳肴",

    # 旅行相关
    "旅行": "旅行度假",
    "旅游": "旅行度假",
    "游记": "旅行度假",
    "攻略": "旅行度假",
    "酒店": "旅行度假",

    # 家居装修相关
    "家居": "居家装修",
    "装修": "居家装修",
    "改造": "居家装修",
    "租房改造": "居家装修",
    "软装": "居家装修",

    # 健身运动相关
    "健身": "体育锻炼",
    "运动": "体育锻炼",
    "减肥": "体育锻炼",
    "瑜伽": "体育锻炼",
    "瘦身": "体育锻炼",

    # 母婴育儿相关
    "母婴": "亲子育儿",
    "育儿": "亲子育儿",
    "宝妈": "亲子育儿",
    "宝宝": "亲子育儿",
    "亲子": "亲子育儿",

    # 宠物相关
    "宠物": "宠物天地",
    "猫": "宠物天地",
    "狗": "宠物天地",
    "萌宠": "宠物天地",
    "养猫": "宠物天地",
    "养狗": "宠物天地",

    # 数码科技相关
    "数码": "数码科技",
    "手机": "数码科技",
    "科技": "数码科技",
    "电脑": "数码科技",
    "测评": "数码科技",
    "互联网": "数码科技",
    "AI": "数码科技",
    "人工智能": "数码科技",
    "编程": "数码科技",
    "软件": "数码科技",
    "硬件": "数码科技",
    "智能": "数码科技",
    "机器人": "数码科技",
    "芯片": "数码科技",
    "电子": "数码科技",
    "游戏": "数码科技",
    "电竞": "数码科技",

    # 教育学习相关
    "教育": "学习教育",
    "学习": "学习教育",
    "考研": "学习教育",
    "考公": "学习教育",
    "英语": "学习教育",

    # 情感相关
    "情感": "星座情感",
    "恋爱": "星座情感",
    "星座": "星座情感",
    "心理": "星座情感",

    # 职场相关
    "职场": "职业发展",
    "工作": "职业发展",
    "求职": "职业发展",
    "面试": "职业发展",

    # 其他
    "vlog": "日常生活",
    "日常": "日常生活",
    "生活": "日常生活",
}


def match_level(user_input):
    """
    匹配用户输入到标准账号等级（中文）

    Args:
        user_input: 用户输入的账号等级描述

    Returns:
        匹配的标准账号等级（如："素人"、"头部kol"）或None
    """
    if not user_input:
        return None

    # 直接匹配映射表
    for keyword, level in LEVEL_MAPPING.items():
        if keyword in user_input:
            return level

    # 模糊匹配标准分类
    for level in STANDARD_LEVELS:
        if level in user_input:
            return level

    # 没有匹配到，返回None
    return None


def match_category(user_input):
    """
    匹配用户输入到标准赛道分类

    Args:
        user_input: 用户输入的赛道描述

    Returns:
        匹配的标准分类
    """
    if not user_input:
        return "综合全部"

    # 直接匹配映射表
    for keyword, category in CATEGORY_MAPPING.items():
        if keyword in user_input:
            return category

    # 模糊匹配标准分类
    for category in STANDARD_CATEGORIES:
        if category in user_input:
            return category

    # 默认返回"综合全部"
    return "综合全部"


def get_api_key():
    """从当前环境变量获取 REDFOX_API_KEY"""
    api_key = os.getenv("REDFOX_API_KEY")
    if not api_key:
        print("❌ 未找到 REDFOX_API_KEY，请配置环境变量：export REDFOX_API_KEY=<你的apikey>", file=sys.stderr)
        sys.exit(1)
    return api_key


def query_similar_accounts(redId=None, track=None, maxFans=None, minFans=None, level=None):
    """
    调用API查询对标账号（统一接口，支持5个参数）

    Args:
        redId: 小红书账号ID
        track: 赛道类型
        maxFans: 最大粉丝量
        minFans: 最小粉丝量
        level: 账号等级（中文：明星、品牌、企业、头部kol、腰部kol、尾部kol、素人）

    Returns:
        同阶对标和高阶标杆账号列表
    """
    url = "https://redfox.hk/story/api/xhsUser/querySimilarAccounts"

    # 获取凭证（环境变量 > shell配置文件 > 提示用户配置）
    api_key = get_api_key()

    # 构建请求参数
    payload = {
        "redId": redId if redId else "",
        "track": track if track else "",
        "maxFans": maxFans if maxFans else "",
        "minFans": minFans if minFans is not None else "",
        "level": level if level else "",
        "source": "小红书对标账号-GitHub"
    }

    headers = {
        "Content-Type": "application/json",
        "X-API-KEY": api_key
    }

    # 原生 urllib POST 请求（verify=False）
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")

    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE

    try:
        with urllib.request.urlopen(req, context=ssl_ctx, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise Exception(f"HTTP请求失败: {e.code}, {e.read().decode('utf-8', errors='replace')}")
    except urllib.error.URLError as e:
        raise Exception(f"请求失败: {e.reason}")

    # 检查返回数据
    if "data" not in result:
        raise Exception(f"API返回格式错误: {result}")

    data = result.get("data")

    # 处理data为None的情况
    if data is None:
        msg = result.get("msg", "未知错误")
        raise Exception(f"API返回错误: {msg}")

    same_level_accounts = data.get("sameLevelAccounts", [])
    high_level_accounts = data.get("highLevelAccounts", [])

    return same_level_accounts, high_level_accounts


def format_number(num):
    """
    格式化数字（万粉显示为w+）
    """
    if num is None:
        return "0"
    if num >= 10000:
        return f"{round(num / 10000, 1)}w"
    return str(num)


def format_level(level):
    """
    格式化账号等级（空值显示为"无"）
    """
    if level is None or level == "":
        return "无"
    return level


def generate_recommendation_reason(account):
    """
    生成推荐理由（基于账号所有数据综合分析，不少于20字）
    分析维度：粉丝规模、更新频率、互动表现、内容方向、爆文案例、账号等级、作品特点
    """
    works = account.get("works") or []
    fans = account.get("fans") or 0
    note_count = account.get("noteCountSeven") or 0
    collected = account.get("collected") or 0
    liked = account.get("liked") or 0
    total_interactive = collected + liked
    total_work = account.get("totalWork") or 0
    level = account.get("level") or ""
    interactive_seven = account.get("interactiveCountSeven") or 0

    # 收集分析点
    analysis_points = []

    # 1. 粉丝规模分析
    if fans >= 500000:
        analysis_points.append(f"粉丝规模达{format_number(fans)}，头部影响力")
    elif fans >= 100000:
        analysis_points.append(f"粉丝{format_number(fans)}，中腰部成熟账号")
    elif fans >= 10000:
        analysis_points.append(f"粉丝{format_number(fans)}，已具备变现能力")
    elif fans >= 1000:
        analysis_points.append(f"粉丝{format_number(fans)}，成长期账号")
    elif fans > 0:
        analysis_points.append(f"粉丝{format_number(fans)}，起号阶段潜力股")

    # 2. 更新频率分析
    if note_count >= 7:
        analysis_points.append("日更勤快，运营活跃度高")
    elif note_count >= 4:
        analysis_points.append("周更稳定，持续运营中")
    elif note_count >= 1:
        analysis_points.append("有持续更新")

    # 3. 互动表现分析
    if interactive_seven >= 10000:
        analysis_points.append(f"近7天互动{format_number(interactive_seven)}，热度很高")
    elif interactive_seven >= 1000:
        analysis_points.append(f"近7天互动{format_number(interactive_seven)}，活跃度不错")

    if total_interactive >= 100000:
        analysis_points.append(f"累计互动{format_number(total_interactive)}，爆款潜力账号")
    elif total_interactive >= 10000:
        analysis_points.append(f"累计互动{format_number(total_interactive)}，内容质量稳定")
    elif total_interactive >= 1000:
        analysis_points.append("有一定互动基础")

    # 4. 作品内容方向分析
    if works:
        titles = [w.get("title", "") for w in works if w.get("title")]
        descs = [w.get("desc", "") for w in works if w.get("desc")]
        all_text = " ".join(titles + descs)

        # 内容方向识别
        content_directions = []
        if "测评" in all_text or "评测" in all_text:
            content_directions.append("测评类")
        if "教程" in all_text or "干货" in all_text or "攻略" in all_text:
            content_directions.append("干货教程")
        if "平价" in all_text or "学生党" in all_text or "便宜" in all_text:
            content_directions.append("平价推荐")
        if "避雷" in all_text or "踩坑" in all_text:
            content_directions.append("避雷测评")
        if "开箱" in all_text:
            content_directions.append("开箱分享")
        if "日常" in all_text or "vlog" in all_text.lower():
            content_directions.append("日常vlog")
        if "好物" in all_text or "推荐" in all_text:
            content_directions.append("好物推荐")

        if content_directions:
            analysis_points.append("内容方向：" + "/".join(content_directions[:2]))

        # 5. 爆文案例
        best_work = None
        best_interactive = 0
        for w in works:
            interactive = (w.get("likedCount") or 0) + (w.get("collectedCount") or 0)
            if interactive > best_interactive:
                best_interactive = interactive
                best_work = w

        if best_work and best_interactive >= 100:
            title = best_work.get("title", "")
            if title and len(title) >= 3:
                short_title = title[:10] + "..." if len(title) > 10 else title
                analysis_points.append(f"爆文「{short_title}」获{format_number(best_interactive)}互动")

        # 6. 标题特征分析
        if titles:
            title_features = []
            # 带数字的标题
            has_number = sum(1 for t in titles if any(c.isdigit() for c in t))
            if has_number >= len(titles) * 0.5:
                title_features.append("善用数字标题")
            # 带问号的标题
            has_question = sum(1 for t in titles if "？" in t or "?" in t)
            if has_question >= len(titles) * 0.3:
                title_features.append("标题带问句吸引点击")

            if title_features:
                analysis_points.append("、".join(title_features))

    # 7. 账号等级分析
    level_tips = {
        "头部kol": "头部KOL，商业价值高",
        "腰部kol": "腰部达人，性价比优选",
        "尾部kol": "尾部达人，成长潜力大",
        "素人": "素人博主，真实种草力强"
    }
    if level in level_tips:
        analysis_points.append(level_tips[level])

    # 8. 作品数量分析
    if total_work >= 500:
        analysis_points.append(f"作品{total_work}篇，内容积累丰富")
    elif total_work >= 100:
        analysis_points.append(f"作品{total_work}篇，运营经验足")

    # 组合推荐理由，确保不少于20字
    if len(analysis_points) >= 3:
        # 取前3-4个要点组合
        result = "，".join(analysis_points[:4])
    elif len(analysis_points) >= 1:
        result = "，".join(analysis_points)
        # 如果字数不够，补充基础信息
        if len(result) < 20:
            if fans > 0:
                result += f"，粉丝{format_number(fans)}"
            if total_interactive > 0:
                result += f"，互动{format_number(total_interactive)}"
    else:
        # 兜底：使用基础数据
        result = f"粉丝{format_number(fans)}，互动{format_number(total_interactive)}"
        if note_count > 0:
            result += f"，近7天更新{note_count}篇"

    # 确保不少于20字
    if len(result) < 20:
        result += "，可参考学习其运营方式"

    return result


def generate_content_analysis(account):
    """
    生成发文特点分析
    分析标题特征、内容特征、情绪方向、定位策略
    """
    analysis_parts = []

    works = account.get("works", [])

    if not works:
        return "暂无近期作品数据"

    # 分析标题特征
    titles = [w.get("title", "") for w in works if w.get("title")]
    if titles:
        # 提取标题中的关键词模式
        title_features = []

        # 检查是否带数字
        has_number = any(any(c.isdigit() for c in t) for t in titles)
        if has_number:
            title_features.append("标题带数字")

        # 检查是否带问号/感叹号
        has_question = any("？" in t or "?" in t for t in titles)
        if has_question:
            title_features.append("标题带问句")

        # 检查标题长度
        avg_len = sum(len(t) for t in titles) / len(titles)
        if avg_len < 10:
            title_features.append("标题简短")
        elif avg_len > 20:
            title_features.append("标题详细")

        if title_features:
            analysis_parts.append("标题特征：" + "、".join(title_features))

    # 分析内容特征
    descs = [w.get("desc", "") for w in works if w.get("desc")]
    if descs:
        content_features = []

        # 检查内容长度
        avg_desc_len = sum(len(d) for d in descs) / len(descs)
        if avg_desc_len > 200:
            content_features.append("内容详实")
        elif avg_desc_len < 50:
            content_features.append("内容简洁")

        # 检查是否带话题标签
        has_hashtag = any("#" in d for d in descs)
        if has_hashtag:
            content_features.append("善用话题标签")

        if content_features:
            analysis_parts.append("内容特征：" + "、".join(content_features))

    # 分析情绪方向
    if titles or descs:
        emotion_hints = []

        # 正面情绪词
        positive_words = ["推荐", "好用", "必买", "必看", "干货", "分享", "攻略"]
        # 负面/警示情绪词
        negative_words = ["避雷", "踩坑", "千万别", "不要", "教训"]
        # 疑问/互动情绪词
        interactive_words = ["怎么", "如何", "为什么", "你觉得", "大家"]

        all_text = " ".join(titles + descs)

        if any(word in all_text for word in positive_words):
            emotion_hints.append("正向分享风格")
        if any(word in all_text for word in negative_words):
            emotion_hints.append("避雷警示风格")
        if any(word in all_text for word in interactive_words):
            emotion_hints.append("互动问答风格")

        if emotion_hints:
            analysis_parts.append("情绪方向：" + "、".join(emotion_hints))

    # 分析定位策略
    if works:
        # 计算互动率
        total_interactive = sum(
            (w.get("likedCount") or 0) + (w.get("collectedCount") or 0) + (w.get("sharedCount") or 0)
            for w in works
        )

        strategy_hints = []

        if total_interactive > 0:
            # 找出互动最高的作品
            best_work = max(works, key=lambda w: (
                (w.get("likedCount") or 0) + (w.get("collectedCount") or 0) + (w.get("sharedCount") or 0)
            ))
            best_title = best_work.get("title", "")
            if best_title:
                strategy_hints.append(f"爆款方向：「{best_title[:15]}...」" if len(best_title) > 15 else f"爆款方向：「{best_title}」")

        # 统计封面特征
        covers = [w.get("cover", "") for w in works if w.get("cover")]
        if covers:
            strategy_hints.append("首图统一风格")

        if strategy_hints:
            analysis_parts.append("定位策略：" + "、".join(strategy_hints))

    return "；".join(analysis_parts) if analysis_parts else "可参考该账号的内容方向和运营策略"


def format_table(accounts, title_line):
    """
    格式化账号表格（严格按照模版）
    """
    lines = []
    lines.append(title_line)
    lines.append("")
    lines.append("| 账号名 | 粉丝数 | 近30天互动数 | 推荐理由 |")
    lines.append("| --- | --- | --- | --- |")

    for account in accounts:
        nickname = account.get("nickname") or "未知"
        url = account.get("url") or "#"
        fans = format_number(account.get("fans"))
        interactive_thirty = format_number(account.get("interactiveCountThirty") or 0)

        # 生成推荐理由
        recommendation = generate_recommendation_reason(account)

        # 账号名做成超链接
        account_link = f"[{nickname}]({url})"
        lines.append(f"| {account_link} | {fans} | {interactive_thirty} | {recommendation} |")

    return "\n".join(lines)


def format_account_detail(account, index):
    """
    格式化账号详情（严格按照模版）
    """
    lines = []

    nickname = account.get("nickname") or "未知"
    url = account.get("url") or "#"
    fans = format_number(account.get("fans"))
    collected = account.get("collected") or 0
    liked = account.get("liked") or 0
    total_interactive = format_number(collected + liked)

    # 按模版格式
    lines.append(f"{index}. 账号名：[{nickname}]({url})")
    lines.append(f"   | 粉丝：{fans} | 总互动：{total_interactive} |")

    # 推荐理由
    recommendation = generate_recommendation_reason(account)
    lines.append(f"   ✅ 推荐理由：{recommendation}")

    # 发文特点
    content_analysis = generate_content_analysis(account)
    lines.append(f"   📝 发文特点：{content_analysis}")

    return "\n".join(lines)


def get_earliest_gmt_create(same_level_accounts, high_level_accounts):
    """
    获取所有账号中最早的gmtCreate时间
    """
    all_accounts = (same_level_accounts or []) + (high_level_accounts or [])
    gmt_creates = []

    for account in all_accounts:
        gmt = account.get("gmtCreate")
        if gmt:
            gmt_creates.append(gmt)

    if not gmt_creates:
        return "入库时刻"

    # 返回最早的时间（字符串排序即可，格式为 "YYYY-MM-DD HH:MM:SS"）
    return min(gmt_creates)


def generate_analysis_summary(same_level_accounts, high_level_accounts):
    """
    生成分析总结（严格按照模版）
    """
    lines = []
    lines.append("📊 **分析总结**：")

    if same_level_accounts:
        avg_fans = sum(a.get("fans") or 0 for a in same_level_accounts) / len(same_level_accounts)
        interactive_total = sum(a.get("interactiveCountThirty") or 0 for a in same_level_accounts)
        avg_interactive = interactive_total / len(same_level_accounts)
        lines.append(f"- 同阶对标账号平均粉丝数：{format_number(avg_fans)}，平均互动量：{format_number(avg_interactive)}")

    if high_level_accounts:
        avg_fans = sum(a.get("fans") or 0 for a in high_level_accounts) / len(high_level_accounts)
        interactive_total = sum(a.get("interactiveCountThirty") or 0 for a in high_level_accounts)
        avg_interactive = interactive_total / len(high_level_accounts)
        lines.append(f"- 高阶标杆账号平均粉丝数：{format_number(avg_fans)}，平均互动量：{format_number(avg_interactive)}")

    if same_level_accounts or high_level_accounts:
        lines.append("- 建议优先参考：同阶对标中的高频更新账号，学习其内容节奏和选题方向")

    return "\n".join(lines)


def format_output(same_level_accounts, high_level_accounts, gmt_create=None):
    """
    格式化输出结果（严格按照模版顺序）
    """
    output_lines = []

    # 获取最早的gmtCreate时间
    earliest_gmt = get_earliest_gmt_create(same_level_accounts, high_level_accounts)

    # 1. 提示语（只显示有数据的组）
    same_count = len(same_level_accounts) if same_level_accounts else 0
    high_count = len(high_level_accounts) if high_level_accounts else 0

    tips_parts = []
    if same_count > 0:
        tips_parts.append(f"【可直接抄的同阶对标（{same_count}个）】")
    if high_count > 0:
        tips_parts.append(f"【可追赶的高阶标杆（{high_count}个）】")

    if tips_parts:
        output_lines.append(f"✨ 为你匹配到{'和'.join(tips_parts)}的{len(tips_parts)}组对标，可按需参考：")
    else:
        output_lines.append("✨ 暂未匹配到符合条件的对标账号，请尝试调整筛选条件。")

    output_lines.append(f"| 数据说明：数据获取时间为{earliest_gmt}，和实时数据存在差别。")

    # 2. 同阶对标表格（有数据才展示）
    if same_level_accounts:
        table_title = f"👉 【可直接抄的同阶对标（{len(same_level_accounts)}个）】（可直接复制玩法）"
        output_lines.append(format_table(same_level_accounts, table_title))

    # 3. 高阶标杆表格（有数据才展示）
    if high_level_accounts:
        table_title = f"👉 【可追赶的高阶标杆（{len(high_level_accounts)}个）】（模式成熟可参考）"
        output_lines.append(format_table(high_level_accounts, table_title))

    # 4. 分析总结（有数据才展示）
    if same_level_accounts or high_level_accounts:
        output_lines.append("")
        output_lines.append(generate_analysis_summary(same_level_accounts, high_level_accounts))

    # 5. 订阅服务
    output_lines.append("")
    output_lines.append("📬 **订阅服务**")
    output_lines.append('       1️⃣ 是否订阅"现查询条件"的对标账号推送，每日下午7点更新最新数据。你可选择推送频率和时间~')
    output_lines.append("       2️⃣ 暂不需要")

    return "\n".join(output_lines)


def generate_html(same_level_accounts, high_level_accounts, gmt_create):
    """
    使用模版生成HTML报告文件，内容与输出格式完全一致
    """
    import os

    earliest_gmt = get_earliest_gmt_create(same_level_accounts, high_level_accounts)
    same_count = len(same_level_accounts) if same_level_accounts else 0
    high_count = len(high_level_accounts) if high_level_accounts else 0

    # 开场白
    intro_parts = []
    if same_count > 0:
        intro_parts.append(f"【可直接抄的同阶对标（{same_count}个）】")
    if high_count > 0:
        intro_parts.append(f"【可追赶的高阶标杆（{high_count}个）】")

    if intro_parts:
        intro_text = f"✨ 为你匹配到{'和'.join(intro_parts)}的{len(intro_parts)}组对标，可按需参考："
    else:
        intro_text = "✨ 暂未匹配到符合条件的对标账号，请尝试调整筛选条件。"

    data_note = f"数据说明：数据获取时间为{earliest_gmt}，和实时数据存在差别。"

    # 同阶对标HTML
    same_level_html = ""
    if same_level_accounts:
        same_level_title = f"👉 【可直接抄的同阶对标（{same_count}个）】"
        same_level_subtitle = "可直接复制玩法"
        rows = ""
        for acc in same_level_accounts:
            nickname = acc.get("nickname") or "未知"
            url = acc.get("url") or "#"
            fans = format_number(acc.get("fans"))
            interactive_thirty = format_number(acc.get("interactiveCountThirty") or 0)
            reason = generate_recommendation_reason(acc)
            rows += f'''                    <tr>
                        <td><a href="{url}" target="_blank">{nickname}</a></td>
                        <td>{fans}</td>
                        <td>{interactive_thirty}</td>
                        <td class="reason">{reason}</td>
                    </tr>
'''
        same_level_html = f'''        <div class="section">
            <div class="section-title">{same_level_title}</div>
            <div class="section-subtitle">{same_level_subtitle}</div>
            <table>
                <thead>
                    <tr>
                        <th class="col-name">账号名</th>
                        <th class="col-fans">粉丝数</th>
                        <th class="col-interact">近30天互动数</th>
                        <th class="col-reason">推荐理由</th>
                    </tr>
                </thead>
                <tbody>
{rows}                </tbody>
            </table>
        </div>
'''

    # 高阶标杆HTML
    high_level_html = ""
    if high_level_accounts:
        high_level_title = f"👉 【可追赶的高阶标杆（{high_count}个）】"
        high_level_subtitle = "模式成熟可参考"
        rows = ""
        for acc in high_level_accounts:
            nickname = acc.get("nickname") or "未知"
            url = acc.get("url") or "#"
            fans = format_number(acc.get("fans"))
            interactive_thirty = format_number(acc.get("interactiveCountThirty") or 0)
            reason = generate_recommendation_reason(acc)
            rows += f'''                    <tr>
                        <td><a href="{url}" target="_blank">{nickname}</a></td>
                        <td>{fans}</td>
                        <td>{interactive_thirty}</td>
                        <td class="reason">{reason}</td>
                    </tr>
'''
        high_level_html = f'''        <div class="section">
            <div class="section-title">{high_level_title}</div>
            <div class="section-subtitle">{high_level_subtitle}</div>
            <table>
                <thead>
                    <tr>
                        <th class="col-name">账号名</th>
                        <th class="col-fans">粉丝数</th>
                        <th class="col-interact">近30天互动数</th>
                        <th class="col-reason">推荐理由</th>
                    </tr>
                </thead>
                <tbody>
{rows}                </tbody>
            </table>
        </div>
'''

    # 分析总结HTML
    summary_html = ""
    if same_level_accounts or high_level_accounts:
        summary_items = ""
        if same_level_accounts:
            avg_fans = sum(a.get("fans") or 0 for a in same_level_accounts) / len(same_level_accounts)
            interactive_total = sum(a.get("interactiveCountThirty") or 0 for a in same_level_accounts)
            avg_interactive = interactive_total / len(same_level_accounts)
            summary_items += f'            <div class="summary-item">• 同阶对标账号平均粉丝数：{format_number(avg_fans)}，平均互动量：{format_number(avg_interactive)}</div>\n'

        if high_level_accounts:
            avg_fans = sum(a.get("fans") or 0 for a in high_level_accounts) / len(high_level_accounts)
            interactive_total = sum(a.get("interactiveCountThirty") or 0 for a in high_level_accounts)
            avg_interactive = interactive_total / len(high_level_accounts)
            summary_items += f'            <div class="summary-item">• 高阶标杆账号平均粉丝数：{format_number(avg_fans)}，平均互动量：{format_number(avg_interactive)}</div>\n'

        summary_items += '            <div class="summary-item">• 建议优先参考：同阶对标中的高频更新账号，学习其内容节奏和选题方向</div>\n'

        summary_html = f'''        <div class="summary-section">
            <div class="summary-title">📊 **分析总结**：</div>
{summary_items}        </div>
'''

    # 完整HTML
    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>小红书对标账号推荐</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background: #f5f5f5; padding: 20px; line-height: 1.6; }}
        .container {{ max-width: 1000px; margin: 0 auto; background: #fff; border-radius: 12px; box-shadow: 0 2px 12px rgba(0,0,0,0.1); padding: 32px; }}
        .intro {{ margin-bottom: 24px; }}
        .intro-text {{ font-size: 16px; color: #333; margin-bottom: 8px; }}
        .data-note {{ font-size: 14px; color: #999; background: #f9f9f9; padding: 8px 12px; border-radius: 4px; display: inline-block; }}
        .section {{ margin-bottom: 32px; }}
        .section-title {{ font-size: 18px; font-weight: bold; color: #333; margin-bottom: 12px; }}
        .section-subtitle {{ font-size: 14px; color: #666; margin-bottom: 16px; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 14px 12px; text-align: left; border-bottom: 1px solid #f0f0f0; }}
        th {{ background: #fafafa; font-weight: 600; color: #333; font-size: 14px; }}
        td {{ color: #666; font-size: 14px; vertical-align: top; }}
        tr:hover {{ background: #fafafa; }}
        a {{ color: #ff2442; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
        .reason {{ font-size: 13px; color: #888; line-height: 1.6; }}
        .col-name {{ width: 18%; }}
        .col-fans {{ width: 10%; }}
        .col-interact {{ width: 10%; }}
        .col-reason {{ width: 62%; }}
        .summary-section {{ margin-bottom: 32px; }}
        .summary-title {{ font-size: 16px; font-weight: bold; color: #333; margin-bottom: 16px; }}
        .summary-item {{ font-size: 14px; color: #666; margin-bottom: 8px; padding-left: 16px; position: relative; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="intro">
            <div class="intro-text">{intro_text}</div>
            <div class="data-note">| {data_note}</div>
        </div>
{same_level_html}{high_level_html}{summary_html}    </div>
</body>
</html>'''

    return html


def save_to_json(same_level_accounts, high_level_accounts, gmt_create, json_path):
    """
    将所有数据保存到临时JSON文件
    """
    data = {
        "gmt_create": gmt_create,
        "same_level_accounts": same_level_accounts or [],
        "high_level_accounts": high_level_accounts or []
    }
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return json_path


def generate_html_from_json(json_path, html_path):
    """
    从JSON文件读取数据并生成HTML文件
    """
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    same_level_accounts = data.get("same_level_accounts", [])
    high_level_accounts = data.get("high_level_accounts", [])
    gmt_create = data.get("gmt_create")

    html_content = generate_html(same_level_accounts, high_level_accounts, gmt_create)

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    return html_path


def main():
    parser = argparse.ArgumentParser(description="小红书账号推荐脚本")
    parser.add_argument("--red_id", help="小红书账号ID")
    parser.add_argument("--track", help="赛道类型（如：化妆美容、美味佳肴等）")
    parser.add_argument("--max_fans", type=int, help="最大粉丝量")
    parser.add_argument("--min_fans", type=int, help="最小粉丝量")
    parser.add_argument("--level", default="素人", help="账号等级（明星、品牌、企业、头部kol、腰部kol、尾部kol、素人），默认素人")

    args = parser.parse_args()

    # 判断是否为高等级账号（头部kol、企业、明星、品牌），只展示同阶对标
    high_level_types = ["头部kol", "企业", "明星", "品牌"]
    is_high_level_account = args.level and args.level in high_level_types

    try:
        same_level_accounts, high_level_accounts = query_similar_accounts(
            redId=args.red_id,
            track=args.track,
            maxFans=args.max_fans,
            minFans=args.min_fans,
            level=args.level
        )

        # 如果是高等级账号，不展示高阶标杆
        if is_high_level_account:
            high_level_accounts = []

        # 获取数据获取时间（取第一个账号的gmtCreate）
        gmt_create = None
        first_account = None
        if same_level_accounts and len(same_level_accounts) > 0:
            gmt_create = same_level_accounts[0].get("gmtCreate")
            first_account = same_level_accounts[0]
        elif high_level_accounts and len(high_level_accounts) > 0:
            gmt_create = high_level_accounts[0].get("gmtCreate")
            first_account = high_level_accounts[0]

        # 生成文件名：账号名+时间戳（用户输入了具体账号）或 对标账号+时间戳（按条件查询）
        import time
        timestamp = int(time.time())
        if args.red_id:
            # 用户输入了具体账号ID，使用账号名+时间戳
            if first_account and first_account.get("nickname"):
                nickname = first_account.get("nickname", "")
                safe_nickname = "".join(c for c in nickname if c.isalnum() or c in "-_")[:20]
                html_filename = f"./{safe_nickname}_{timestamp}.html"
                json_filename = f"./{safe_nickname}_{timestamp}.json"
            else:
                html_filename = f"./对标账号_{timestamp}.html"
                json_filename = f"./对标账号_{timestamp}.json"
        else:
            # 按条件查询，使用"对标账号"+时间戳
            html_filename = f"./对标账号_{timestamp}.html"
            json_filename = f"./对标账号_{timestamp}.json"

        # 1. 格式化输出（严格按照模版）
        result = format_output(same_level_accounts, high_level_accounts, gmt_create)
        print(result)

        # 2. 将所有数据存入临时JSON文件（必须执行）
        save_to_json(same_level_accounts, high_level_accounts, gmt_create, json_filename)

        # 3. 读取JSON文件数据生成HTML文件（必须执行）
        generate_html_from_json(json_filename, html_filename)

        # 4. 输出结果（包含HTML路径供AI展示）
        output = {
            "status": "success",
            "html_path": html_filename
        }
        print("")
        print(json.dumps(output, ensure_ascii=False))

    except Exception as e:
        # 账号未收录或其他错误
        print(f"查询失败: {str(e)}。未查询到相关账号：当前 Skill 仅收录热门账号。如需定制数据，可邮件联系红狐数据咨询：redfoxdata@proton.me")


if __name__ == "__main__":
    main()
