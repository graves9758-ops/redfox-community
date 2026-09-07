#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小红书爆款内容榜单获取脚本

功能：
1. 调用API获取小红书爆款内容数据
2. 保持接口原始顺序，禁止重新排序
3. 输出TOP30榜单列表（纯文本格式）
4. 提供三维度内容分析（数据表现、内容结构、选题价值）

使用方法：
python fetch_explosive_articles.py --rank_date "2026-04-15" --category "时尚穿搭"
"""

import argparse
import json
import sys
import os
from datetime import datetime, timedelta
import requests

REDFOX_API_BASE = "https://redfox.hk/story/api/cozeSkill/getXhsCozeSkillDataOne"
REDFOX_API_SOURCE = "小红书单日数据爆款文章-GitHub"


def get_redfox_api_key():
    """
    获取 RedFox API Key，三级回退策略：
    1. 从环境变量 REDFOX_API_KEY 获取
    2. 从 shell 配置文件读取
    3. 提示用户配置
    """
    # 第一级：从环境变量获取
    api_key = os.environ.get("REDFOX_API_KEY")
    if api_key:
        return api_key

    # 第二级：从 shell 配置文件读取
    home = os.path.expanduser("~")
    shell_files = []
    for fname in [".zshrc", ".bashrc", ".bash_profile", ".profile"]:
        fpath = os.path.join(home, fname)
        if os.path.isfile(fpath):
            shell_files.append(fpath)

    for fpath in shell_files:
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                for line in f:
                    stripped = line.strip()
                    if stripped.startswith("export REDFOX_API_KEY="):
                        key_part = stripped.split("=", 1)[1].strip().strip('"').strip("'")
                        if key_part:
                            return key_part
        except Exception:
            continue

    # 第三级：仍未获取到，提示用户配置
    raise RuntimeError(
        "未找到 REDFOX_API_KEY 配置。\n"
        "请设置环境变量后重试：\n"
        "  macOS/Linux: export REDFOX_API_KEY=<你的apikey>\n"
        "  Windows PowerShell: [Environment]::SetEnvironmentVariable('REDFOX_API_KEY', '<值>', 'User')\n"
        "\n"
        "获取 API Key: https://redfox.hk/login"
    )


def get_query_date(user_date: str = None) -> tuple:
    """
    根据用户输入和当前时间确定查询日期

    规则：
    1. 用户指定了日期 → 直接使用
    2. 未指定日期：
       - 当前时间 >= 19:00 → 查询昨日数据（当日19:00已更新）
       - 当前时间 < 19:00 → 查询前天数据（等待当日19:00更新）

    Args:
        user_date: 用户指定的日期（格式：yyyy-MM-dd）

    Returns:
        (查询日期, 是否为自动推断)
    """
    if user_date:
        return user_date, False

    now = datetime.now()
    cutoff_time = now.replace(hour=19, minute=0, second=0, microsecond=0)

    if now >= cutoff_time:
        # 超过19:00，查询昨日（当日已更新）
        query_date = (now - timedelta(days=1)).strftime("%Y-%m-%d")
    else:
        # 未超过19:00，查询前天（等待当日更新）
        query_date = (now - timedelta(days=2)).strftime("%Y-%m-%d")

    return query_date, True


# 分类关键词映射（包含产品词映射）
CATEGORY_KEYWORDS = {
    "综合全部": ["综合", "全部", "热门", "推荐", "随便", "随便看看", "总榜", "整体"],
    "出行代步": ["出行", "代步", "交通", "汽车", "打车", "地铁", "公交", "开车", "驾车", "出行方式", "通勤", "自驾", "新能源车", "电动车"],
    "休闲爱好": ["休闲", "爱好", "兴趣", "娱乐", "休闲活动", "兴趣爱", "业余", "消遣", "手工", "DIY", "收藏"],
    "影视娱乐": ["影视", "娱乐", "电影", "电视剧", "综艺", "明星", "追剧", "看剧", "演员", "导演", "剧集", "追星", "综艺"],
    "数码科技": ["数码", "科技", "手机", "电脑", "数码产品", "科技产品", "智能", "电子", "硬件", "软件", "app", "APP", "iPhone", "安卓", "平板", "耳机", "键盘", "鼠标"],
    "医疗保健": ["医疗", "保健", "健康", "医院", "医生", "看病", "养生", "保健", "体检", "治疗", "药品", "中医", "减肥", "瘦身"],
    "综合杂项": ["杂项", "其他", "综合杂项", "杂货", "综合类"],
    "星座情感": ["星座", "情感", "爱情", "恋爱", "感情", "星座运势", "情感咨询", "脱单", "表白", "分手", "复合", "塔罗", "占卜"],
    "时尚穿搭": ["时尚", "穿搭", "衣服", "服装", "搭配", "穿衣", "时装", "潮流穿搭", "服饰", "OOTD", "ootd", "裙子", "裤子", "外套", "大衣", "西装", "毛衣", "T恤"],
    "婚庆婚礼": ["婚庆", "婚礼", "结婚", "婚纱", "婚宴", "求婚", "订婚", "婚庆策划", "新娘", "新郎", "伴娘", "钻戒"],
    "拍摄记录": ["拍摄", "记录", "摄影", "拍照", "照片", "视频", "vlog", "Vlog", "VLOG", "摄像", "短视频", "相机", "镜头"],
    "学习教育": ["学习", "教育", "培训", "课程", "考试", "学校", "教育机构", "学习方法", "考研", "考公", "留学", "英语", "编程", "技能"],
    "化妆美容": ["化妆", "美容", "美妆", "妆容", "护肤", "彩妆", "化妆品", "美容护肤", "化妆教程", "美颜", "睫毛膏", "口红", "粉底", "眉笔", "眼影", "腮红", "遮瑕", "定妆", "精华", "面霜", "水乳", "防晒", "面膜"],
    "居家装修": ["居家", "装修", "家居", "家装", "房子装修", "室内设计", "软装", "硬装", "家居好物", "家具", "收纳", "整理"],
    "旅行度假": ["旅行", "度假", "旅游", "出游", "旅行攻略", "景点", "旅游攻略", "自由行", "跟团游", "自驾游", "酒店", "民宿"],
    "亲子育儿": ["亲子", "育儿", "宝宝", "儿童", "带娃", "育儿经", "亲子活动", "母婴", "幼儿", "小孩", "奶粉", "尿布", "玩具"],
    "个人护理": ["个人护理", "护理", "护肤", "身体护理", "美容护理", "护理产品", "个人清洁", "洗发水", "沐浴露", "牙膏", "卫生巾"],
    "美味佳肴": ["美味", "佳肴", "美食", "做饭", "烹饪", "菜谱", "美食推荐", "餐厅", "探店", "食谱", "好吃", "甜品", "烘焙", "奶茶", "咖啡", "零食"],
    "职业发展": ["职业", "发展", "工作", "职场", "求职", "面试", "职业规划", "跳槽", "升职", "加薪", "简历", "副业", "创业"],
    "宠物天地": ["宠物", "猫", "狗", "养猫", "养狗", "萌宠", "宠物猫", "宠物狗", "铲屎官", "喵星人", "汪星人", "猫粮", "狗粮"],
    "潮流鞋包": ["潮流", "鞋包", "鞋子", "包包", "潮鞋", "名牌包", "运动鞋", "高跟鞋", "手提包", "球鞋", "帆布鞋", "靴子"],
    "日常生活": ["日常", "生活", "日常记录", "生活日常", "vlog日常", "生活分享", "好物推荐"],
    "科学探索": ["科学", "探索", "科普", "科学知识", "实验", "发现", "研究", "科技探索"],
    "新闻资讯": ["新闻", "资讯", "热点", "时事", "新闻报道", "新闻资讯", "最新消息"],
    "体育锻炼": ["体育", "锻炼", "运动", "健身", "减肥", "瘦身", "体育运动", "健身房", "瑜伽", "跑步", "游泳", "篮球", "足球"],
}


def match_category(user_input: str) -> str:
    """
    根据用户输入匹配分类

    Args:
        user_input: 用户输入的关键词或描述

    Returns:
        匹配的分类名称，默认返回"综合全部"
    """
    if not user_input:
        return "综合全部"

    user_input = user_input.lower().strip()

    # 遍历分类关键词进行匹配
    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in user_input:
                return category

    # 如果没有匹配到，返回综合全部
    return "综合全部"


def get_all_categories():
    """获取所有分类列表"""
    return list(CATEGORY_KEYWORDS.keys())


def fetch_explosive_articles(rank_date: str, category: str = "综合全部") -> dict:
    """
    调用API获取小红书爆款内容数据

    Args:
        rank_date: 日期（格式：yyyy-MM-dd）
        category: 分类名称（默认：综合全部）

    Returns:
        API返回的数据
    """
    api_key = get_redfox_api_key()

    headers = {
        "X-API-KEY": api_key,
    }
    params = {
        "rankDate": rank_date,
        "source": REDFOX_API_SOURCE,
        "category": category,
    }

    try:
        # 接口仅支持 GET（query 参数）；POST 会返回系统错误
        response = requests.get(REDFOX_API_BASE, params=params, headers=headers, timeout=30)
        if response.status_code >= 400:
            raise Exception(f"HTTP请求失败: {response.status_code}, {response.text}")

        data = response.json()

        # 检查API返回的错误信息（成功码为2000）
        if "code" in data and data["code"] != 2000:
            error_msg = data.get("msg", data.get("message", "未知错误"))
            raise Exception(f"API错误: {error_msg}")

        return data

    except requests.exceptions.RequestException as e:
        raise Exception(f"请求失败: {str(e)}")
    except json.JSONDecodeError as e:
        raise Exception(f"JSON解析失败: {str(e)}")


def process_ranking_data(data: dict, top_n: int = 10) -> list:
    """
    处理榜单数据，保持接口原始顺序

    Args:
        data: API返回的原始数据
        top_n: 返回前N条数据（默认10条）

    Returns:
        榜单列表（保持接口原始顺序，禁止重新排序）
    """
    # 提取笔记列表
    articles = []

    if isinstance(data, list):
        articles = data
    elif isinstance(data, dict):
        articles = data.get("data", data.get("list", data.get("articles", [])))
        if isinstance(articles, dict):
            articles = articles.get("list", articles.get("records", []))

    if not articles:
        return []

    # 保持接口原始顺序，禁止重新排序
    return articles[:top_n]


def parse_count(value) -> int:
    """解析计数值，支持 "2w+" 格式"""
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        if 'w+' in value.lower():
            num = float(value.lower().replace('w+', '').replace('w', ''))
            return int(num * 10000)
        try:
            return int(value)
        except:
            return 0
    return 0


def clean_text(text: str) -> str:
    """
    清理文本中的特殊字符，用于表格单元格显示

    清理内容：
    - 空格
    - 换行符（\r, \n）
    - URL链接
    - Image标记
    - 特殊字符（<>{}[]|\）
    """
    import re
    if not text:
        return ""

    text = str(text)
    # 移除URL
    text = re.sub(r'https?://\S+', '', text)
    # 移除Image标记
    text = re.sub(r'Image:\s*\[.*?\]', '', text)
    # 移除换行符
    text = re.sub(r'[\r\n]+', '', text)
    # 移除空格
    text = text.replace(' ', '')
    # 移除特殊字符
    text = re.sub(r'[<>{}[\]\\|]', '', text)

    return text.strip()


def generate_core_content(title: str, desc: str, user_name: str) -> str:
    """
    生成笔记核心内容摘要

    规则：主要讲述什么人做了什么事，内容丰富且信息完整

    Args:
        title: 笔记标题
        desc: 笔记描述
        user_name: 作者名称

    Returns:
        核心内容摘要（30-60字）
    """
    import re

    # 清理desc中的URL和特殊字符
    desc_clean = re.sub(r'https?://\S+', '', desc)  # 移除URL
    desc_clean = re.sub(r'Image:\s*\[.*?\]', '', desc_clean)  # 移除Image标记
    desc_clean = re.sub(r'#\S+', '', desc_clean)  # 移除话题标签
    desc_clean = re.sub(r'[\r\n]+', '', desc_clean)  # 移除换行符
    desc_clean = re.sub(r'[<>{}[\]\\]', '', desc_clean)  # 移除特殊字符

    text = f"{title} {desc_clean}".strip()

    # 识别主体（谁）
    subject = user_name if user_name else "博主"

    # 识别行为（做什么）
    action = ""
    topic = ""

    # 旅行/风景类
    if any(kw in text for kw in ["旅行", "旅游", "打卡", "景点", "出游", "攻略"]):
        action = "分享"
        location_match = re.search(r"在([^\s,，。！？]{2,8})(旅行|旅游|打卡|游玩)", text)
        if location_match:
            topic = f"{location_match.group(1)}旅行攻略与体验"
        else:
            topic = "旅行见闻与实用攻略"
    # 美食类
    elif any(kw in text for kw in ["美食", "做饭", "食谱", "餐厅", "探店", "好吃", "烹饪", "料理"]):
        action = "推荐"
        topic = "美食制作方法与餐厅探店体验"
    # 穿搭/时尚类
    elif any(kw in text for kw in ["穿搭", "穿衣", "服装", "时尚", "OOTD", "ootd", "搭配"]):
        action = "展示"
        topic = "时尚穿搭技巧与单品推荐"
    # 美妆/护肤类
    elif any(kw in text for kw in ["化妆", "妆容", "美妆", "护肤", "彩妆", "口红"]):
        action = "分享"
        topic = "美妆教程与护肤心得"
    # 宠物类
    elif any(kw in text for kw in ["宠物", "猫", "狗", "萌宠", "铲屎官"]):
        action = "记录"
        topic = "宠物日常与养护经验"
    # 游戏类
    elif any(kw in text for kw in ["游戏", "王者", "电竞", "玩家"]):
        action = "分享"
        topic = "游戏攻略与精彩操作"
    # 搞笑/娱乐类
    elif any(kw in text for kw in ["搞笑", "有趣", "沙雕", "表情包", "梗"]):
        action = "创作"
        topic = "趣味内容与搞笑段子"
    # 生活/日常类
    elif any(kw in text for kw in ["日常", "生活", "vlog", "记录", "Vlog", "VLOG"]):
        action = "记录"
        topic = "日常生活分享与个人见闻"
    # 情感类
    elif any(kw in text for kw in ["情感", "爱情", "恋爱", "故事", "感悟"]):
        action = "分享"
        topic = "情感故事与人生感悟"
    # 教程/干货类
    elif any(kw in text for kw in ["教程", "方法", "技巧", "攻略", "干货"]):
        action = "传授"
        topic = "实用技巧与干货教程"
    # 默认
    else:
        action = "分享"
        if title and len(title) > 5:
            topic = title[:25] + "..."
        else:
            topic = "精彩内容与个人体验"

    # 组合生成摘要
    summary = f"{subject}{action}{topic}"

    # 控制长度在30-60字
    if len(summary) < 30:
        if desc_clean and len(desc_clean) > 10:
            extra = desc_clean[:30].strip()
            summary = f"{summary}，{extra}..."
    elif len(summary) > 60:
        summary = summary[:57] + "..."

    # 最终清理：移除所有换行符和特殊字符
    summary = re.sub(r'[\r\n]+', '', summary)
    summary = re.sub(r'[<>{}[\]\\|]', '', summary)

    return summary


def format_ranking_list(articles: list, category: str = "综合全部") -> str:
    """
    将榜单数据格式化为表格样式

    字段：排名、笔记信息、互动数、点赞、评论、收藏、分享

    Args:
        articles: 笔记列表（保持接口原始顺序）
        category: 当前分类

    Returns:
        表格格式的字符串
    """
    if not articles:
        return f"未获取到【{clean_text(category)}】分类的爆款内容数据"

    output_lines = []

    # 表头 - 加粗并添加图标，标题后添加数据说明
    output_lines.append(f"**🔥 【{clean_text(category)}】每日爆款笔记**")
    output_lines.append("*每日爆款笔记指笔记发后第3天比第2天涨的数据由高到低Top50*")
    output_lines.append("| 排名 | 笔记信息 | 互动数 | 点赞 | 评论 | 收藏 | 分享 |")
    output_lines.append("|:---:|:---|:---:|:---:|:---:|:---:|:---:|")

    for idx, article in enumerate(articles, 1):
        # 获取并清理所有字段
        title = clean_text(article.get("title", "无标题")) or "无标题"
        user_name = clean_text(article.get("userName", "未知用户")) or "未知用户"
        photo_jump_url = article.get("photoJumpUrl", "#") or "#"
        # URL中的空格编码为%20，其他特殊字符清理
        photo_jump_url = photo_jump_url.replace(" ", "%20")
        user_jump_url = (article.get("userJumpUrl", "#") or "#").replace(" ", "%20")
        fans = clean_text(str(article.get("fans", "0"))) or "0"

        # 从anaAdd对象获取互动数据并清理
        ana_add = article.get("anaAdd", {})
        interactive_count = clean_text(str(ana_add.get("interactiveCount", "0") or article.get("interactiveCount", "0"))) or "0"
        add_interactive_count = clean_text(str(ana_add.get("addInteractiveount", "0") or article.get("addInteractiveount", "0"))) or "0"
        like_count = clean_text(str(ana_add.get("useLikeCount", "0") or article.get("useLikeCount", "0"))) or "0"
        add_like_count = clean_text(str(ana_add.get("addLikeCount", "0") or article.get("addLikeCount", "0"))) or "0"
        comment_count = clean_text(str(ana_add.get("useCommentCount", "0") or article.get("useCommentCount", "0"))) or "0"
        add_comment_count = clean_text(str(ana_add.get("addCommentCount", "0") or article.get("addCommentCount", "0"))) or "0"
        collected_count = clean_text(str(ana_add.get("collectedCount", "0") or article.get("collectedCount", "0"))) or "0"
        add_collected_count = clean_text(str(ana_add.get("addCollectedCunt", "0") or article.get("addCollectedCunt", "0"))) or "0"
        share_count = clean_text(str(ana_add.get("useShareCount", "0") or article.get("useShareCount", "0"))) or "0"
        add_share_count = clean_text(str(ana_add.get("addShareCount", "0") or article.get("addShareCount", "0"))) or "0"

        # 排名（前三名带奖牌）
        if idx == 1:
            rank_display = "🥇"
        elif idx == 2:
            rank_display = "🥈"
        elif idx == 3:
            rank_display = "🥉"
        else:
            rank_display = str(idx)

        # 笔记信息：标题链接 + 作者链接（粉丝数）
        if photo_jump_url and photo_jump_url != "#":
            if user_jump_url and user_jump_url != "#":
                note_info = f"[{title}]({photo_jump_url})<br>[{user_name}]({user_jump_url})（{fans}粉丝）"
            else:
                note_info = f"[{title}]({photo_jump_url})<br>{user_name}（{fans}粉丝）"
        else:
            if user_jump_url and user_jump_url != "#":
                note_info = f"{title}<br>[{user_name}]({user_jump_url})（{fans}粉丝）"
            else:
                note_info = f"{title}<br>{user_name}（{fans}粉丝）"

        # 格式化数字
        def format_num(val):
            try:
                num = parse_count(val)
                if num >= 10000:
                    return f"{num // 10000}w+"
                return str(val)
            except:
                return str(val)

        # 格式化显示：累计数值<br>↑新增数值
        interactive_display = f"{format_num(interactive_count)}<br>↑新增{format_num(add_interactive_count)}"
        like_display = f"{format_num(like_count)}<br>↑新增{format_num(add_like_count)}"
        comment_display = f"{format_num(comment_count)}<br>↑新增{format_num(add_comment_count)}"
        collect_display = f"{format_num(collected_count)}<br>↑新增{format_num(add_collected_count)}"
        share_display = f"{format_num(share_count)}<br>↑新增{format_num(add_share_count)}"

        output_lines.append(f"| {rank_display} | {note_info} | {interactive_display} | {like_display} | {comment_display} | {collect_display} | {share_display} |")

    return "\n".join(output_lines)


def analyze_content(article: dict) -> str:
    """
    基于笔记的具体文本内容，生成专业且通俗的内容分析

    分析规则：
    1. 内容概述：简明扼要地概括笔记核心内容
    2. 热点利用：分析笔记借用了哪些热点话题或趋势
    3. 传播作用：阐述内容起到的作用
    4. 达成效果：说明内容达到的效果

    Args:
        article: 笔记数据

    Returns:
        内容分析字符串（专业通俗风格）
    """
    # 提取文本内容
    title = article.get("title", "")
    desc = article.get("desc", "")

    # 合并所有文本用于分析
    all_text = f"{title} {desc}"

    # 动态提取关键信息
    content_analysis = []

    # 1. 内容概述 - 基于实际内容动态生成
    topic_keywords = []
    if "旅行" in all_text or "风景" in all_text or "自由" in all_text:
        topic_keywords.append("旅行生活")
    if "猫" in all_text or "狗" in all_text or "宠物" in all_text:
        topic_keywords.append("萌宠日常")
    if "游戏" in all_text or "王者" in all_text:
        topic_keywords.append("游戏娱乐")
    if "手工" in all_text or "DIY" in all_text:
        topic_keywords.append("手工创意")
    if "美食" in all_text or "做饭" in all_text:
        topic_keywords.append("美食分享")
    if "穿搭" in all_text or "时尚" in all_text:
        topic_keywords.append("时尚穿搭")
    if "上学" in all_text or "学校" in all_text:
        topic_keywords.append("校园生活")
    if "表情包" in all_text or "梗图" in all_text:
        topic_keywords.append("趣味内容")
    if "帅哥" in all_text or "美女" in all_text:
        topic_keywords.append("颜值分享")

    # 从desc中提取标签
    if "#" in desc:
        tags = [t.strip() for t in desc.split("#") if t.strip()]
        if tags:
            topic_keywords.extend(tags[:2])

    # 动态生成内容概述
    if topic_keywords:
        topic_str = "、".join(topic_keywords[:3])
        content_analysis.append(f"本笔记围绕{topic_str}等话题展开")
    else:
        if len(title) > 0:
            key_part = title[:20] if len(title) > 20 else title
            content_analysis.append(f"本笔记聚焦{key_part}等话题")

    # 2. 热点利用 - 基于实际内容动态判断
    hotspot_detected = []

    if any(word in all_text for word in ["热门", "爆火", "流行"]):
        hotspot_detected.append(("热门话题", "流量热点"))
    if any(word in all_text for word in ["治愈", "温暖", "感动"]):
        hotspot_detected.append(("治愈系", "情感热点"))
    if any(word in all_text for word in ["搞笑", "有趣", "沙雕"]):
        hotspot_detected.append(("搞笑内容", "娱乐热点"))
    if any(word in all_text for word in ["日常", "生活", "vlog"]):
        hotspot_detected.append(("生活分享", "日常热点"))

    if hotspot_detected:
        hotspots = [h[0] for h in hotspot_detected[:2]]
        content_analysis.append(f"笔记借力{'与'.join(hotspots)}等话题吸引关注")
    else:
        content_analysis.append("笔记紧扣用户感兴趣的话题")

    # 3. 传播作用
    if any(word in all_text for word in ["分享", "推荐", "安利"]):
        content_analysis.append("通过分享体验满足用户好奇心")
    elif any(word in all_text for word in ["教程", "攻略", "方法"]):
        content_analysis.append("通过提供实用价值满足用户需求")
    else:
        content_analysis.append("满足用户对相关内容的需求")

    # 4. 达成效果
    ana_add = article.get("anaAdd", {})
    like_count = parse_count(ana_add.get("useLikeCount", 0) or article.get("useLikeCount", 0))
    collected_count = parse_count(ana_add.get("collectedCount", 0) or article.get("collectedCount", 0))

    if like_count > 10000 or collected_count > 1000:
        content_analysis.append("获得高互动传播效果")
    else:
        content_analysis.append("获得良好传播效果")

    # 组合分析内容
    analysis = "，".join(content_analysis) + "。"

    return analysis


def main():
    parser = argparse.ArgumentParser(description="获取小红书爆款内容榜单")
    parser.add_argument("--rank_date", required=False, default=None, help="查询日期（格式：yyyy-MM-dd，默认今天）")
    parser.add_argument("--category", required=False, default=None, help="分类名称（如：时尚穿搭、美食佳肴等），不传则根据关键词匹配")
    parser.add_argument("--keyword", required=False, default=None, help="用户输入的关键词，用于自动匹配分类")
    parser.add_argument("--top_n", type=int, default=10, help="返回前N条数据（默认10）")
    parser.add_argument("--list_categories", action="store_true", help="列出所有可用分类")
    parser.add_argument("--output_json", required=False, default=None, help="将获取到的原始数据写入指定 JSON 缓存文件，供 gen_html 复用")

    args = parser.parse_args()

    # 列出所有分类
    if args.list_categories:
        print("可用分类列表：")
        for cat in get_all_categories():
            print(f"  - {cat}")
        return 0

    try:
        # 处理日期参数
        rank_date, is_auto = get_query_date(args.rank_date)

        # 处理分类参数
        if args.category:
            category = args.category
        elif args.keyword:
            category = match_category(args.keyword)
            print(f"根据关键词【{args.keyword}】匹配到分类：【{category}】")
        else:
            category = "综合全部"

        print(f"正在获取小红书爆款内容数据...")
        print(f"当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        if is_auto:
            cutoff_time = datetime.now().replace(hour=19, minute=0, second=0, microsecond=0)
            if datetime.now() >= cutoff_time:
                print(f"当前已过19:00，查询昨日数据（当日已更新）")
            else:
                print(f"当前未过19:00，查询前天数据（等待当日19:00更新）")
        print(f"查询日期: {rank_date}")
        print(f"分类: {category}")
        print("-" * 60)

        # 获取数据
        data = fetch_explosive_articles(rank_date, category)

        # 处理数据（保持接口原始顺序）
        articles = process_ranking_data(data, args.top_n)

        # 无数据回退逻辑：仅回退一次
        if len(articles) == 0 and is_auto:
            prev_date = (datetime.strptime(rank_date, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
            print(f"默认日期 {rank_date} 无数据，回退一天尝试 {prev_date}")
            print("-" * 60)
            data = fetch_explosive_articles(prev_date, category)
            articles = process_ranking_data(data, args.top_n)
            if articles:
                rank_date = prev_date  # 更新有效日期

        # 写入 JSON 缓存文件（有数据时）
        if args.output_json and len(articles) > 0:
            raw_articles = process_ranking_data(data, 50)  # 取全量50条写入缓存
            cache_data = {
                "rank_date": rank_date,
                "category": category,
                "articles": raw_articles
            }
            try:
                os.makedirs(os.path.dirname(os.path.abspath(args.output_json)), exist_ok=True)
                with open(args.output_json, "w", encoding="utf-8") as f:
                    json.dump(cache_data, f, ensure_ascii=False, indent=2)
                print(f"数据已缓存至: {args.output_json}", file=sys.stderr)
            except Exception as e:
                print(f"缓存写入失败: {e}", file=sys.stderr)

        # 检查数据量是否足够
        if len(articles) < 10:
            print(f"提示：当前获取到 {len(articles)} 条数据，不足10条")
            print("建议：可尝试查询其他日期或其他分类的数据")
            print("-" * 60)

        # 格式化输出
        ranking_list = format_ranking_list(articles, category)
        print(ranking_list)

        # 返回统计信息
        print("\n" + "=" * 60)
        if articles:
            print(f"共获取到 {len(articles)} 条【{category}】爆款内容数据")
        else:
            print(f"未获取到【{category}】分类的爆款内容数据")
            print("建议：尝试查询其他日期或其他分类的数据")

        return 0

    except Exception as e:
        print(f"错误: {str(e)}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
