#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小红书七日爆款笔记获取脚本

功能：
1. 调用API获取小红书七日爆款笔记数据
2. 按互动数排序
3. 输出TOP30榜单列表（纯文本格式）
4. 提供三维度内容分析（数据表现、内容结构、选题价值）

使用方法：
python fetch_explosive_articles.py --rank_date "2026-04-15" --category "时尚穿搭"
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from urllib.parse import quote
import requests


def get_api_key() -> str:
    """
    获取 REDFOX_API_KEY

    三级认证回退机制：
    1. 从当前设备环境变量 REDFOX_API_KEY 中获取
    2. 若未获取到，自动从 shell 配置文件中读取
    3. 仍然没有则提示用户配置

    Returns:
        API Key 字符串

    Raises:
        ValueError: 未找到 API Key 时抛出，附带配置指引
    """
    import platform
    import re as re_mod

    # 第一级：环境变量
    api_key = os.environ.get("REDFOX_API_KEY", "").strip()
    if api_key:
        return api_key

    # 第二级：Shell 配置文件
    home = os.path.expanduser("~")
    config_files = []

    if platform.system() == "Windows":
        config_files = [
            os.path.join(home, "Documents", "WindowsPowerShell", "Microsoft.PowerShell_profile.ps1"),
            os.path.join(home, "Documents", "PowerShell", "Microsoft.PowerShell_profile.ps1"),
        ]
    else:
        config_files = [
            os.path.join(home, ".zshrc"),
            os.path.join(home, ".bashrc"),
            os.path.join(home, ".bash_profile"),
            os.path.join(home, ".profile"),
        ]

    for cf in config_files:
        if os.path.isfile(cf):
            try:
                with open(cf, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                match = re_mod.search(
                    r'REDFOX_API_KEY\s*[=:]\s*["\']?([a-zA-Z0-9_\-]+)["\']?',
                    content
                )
                if match:
                    return match.group(1).strip()
            except Exception:
                continue

    # 第三级：提示用户配置
    raise ValueError(
        "未找到 REDFOX_API_KEY。请按以下步骤配置：\n"
        "1. 访问 https://redfox.hk/login?source=github 注册并获取 API Key\n"
        "2. 设置环境变量：\n"
        "   macOS/Linux: export REDFOX_API_KEY=<你的apikey>\n"
        "   Windows PowerShell: [Environment]::SetEnvironmentVariable('REDFOX_API_KEY', '<值>', 'User')\n"
        "3. 配置后重启终端使其生效"
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
# 注："综合杂项"已归类到"综合全部"，其关键词并入"综合全部"下
CATEGORY_KEYWORDS = {
    "综合全部": ["综合", "全部", "热门", "推荐", "随便", "随便看看", "总榜", "整体", "杂项", "其他", "综合杂项", "杂货", "综合类"],
    "出行代步": ["出行", "代步", "交通", "汽车", "打车", "地铁", "公交", "开车", "驾车", "出行方式", "通勤", "自驾", "新能源车", "电动车", "去处", "旅游", "购物地", "休闲娱乐", "出行攻略", "酒店民宿"],
    "休闲爱好": ["休闲", "爱好", "兴趣", "娱乐", "休闲活动", "兴趣爱", "业余", "消遣", "手工", "DIY", "收藏"],
    "影视娱乐": ["影视", "娱乐", "电影", "电视剧", "综艺", "明星", "追剧", "看剧", "演员", "导演", "剧集", "追星", "综艺", "动漫", "短剧", "八卦"],
    "数码科技": ["数码", "科技", "手机", "电脑", "数码产品", "科技产品", "智能", "电子", "硬件", "软件", "app", "APP", "iPhone", "安卓", "平板", "耳机", "键盘", "鼠标", "互联网", "游戏", "软件服务"],
    "医疗保健": ["医疗", "保健", "健康", "医院", "医生", "看病", "养生", "体检", "治疗", "药品", "中医", "减肥", "瘦身", "保健品", "医疗器械", "医疗方法", "医疗健康"],
    "星座情感": ["星座", "情感", "爱情", "恋爱", "感情", "星座运势", "情感咨询", "脱单", "表白", "分手", "复合", "塔罗", "占卜", "星座命理", "两性关系", "励志鸡汤", "心理学"],
    "时尚穿搭": ["时尚", "穿搭", "衣服", "服装", "搭配", "穿衣", "时装", "潮流穿搭", "服饰", "OOTD", "ootd", "裙子", "裤子", "外套", "大衣", "西装", "毛衣", "T恤", "鞋", "包", "潮玩", "鞋靴", "潮流资讯", "品牌设计"],
    "婚庆婚礼": ["婚庆", "婚礼", "结婚", "婚纱", "婚宴", "求婚", "订婚", "婚庆策划", "新娘", "新郎", "伴娘", "钻戒", "婚礼经验", "婚礼造型", "婚礼用品", "结婚场地"],
    "拍摄记录": ["拍摄", "记录", "摄影", "拍照", "照片", "视频", "vlog", "Vlog", "VLOG", "摄像", "短视频", "相机", "镜头"],
    "学习教育": ["学习", "教育", "培训", "课程", "考试", "学校", "教育机构", "学习方法", "考研", "考公", "留学", "英语", "编程", "技能", "学前教育", "小学", "中学", "大学", "教育日常", "知识科普", "外语教育"],
    "化妆美容": ["化妆", "美容", "美妆", "妆容", "护肤", "彩妆", "化妆品", "美容护肤", "化妆教程", "美颜", "睫毛膏", "口红", "粉底", "眉笔", "眼影", "腮红", "遮瑕", "定妆", "精华", "面霜", "水乳", "防晒", "面膜"],
    "居家装修": ["居家", "装修", "家居", "家装", "房子装修", "室内设计", "软装", "硬装", "家居好物", "家具", "收纳", "整理"],
    "旅行度假": ["旅行", "度假", "旅游", "出游", "旅行攻略", "景点", "旅游攻略", "自由行", "跟团游", "自驾游", "酒店", "民宿"],
    "亲子育儿": ["亲子", "育儿", "宝宝", "儿童", "带娃", "育儿经", "亲子活动", "母婴", "幼儿", "小孩", "奶粉", "尿布", "玩具"],
    "个人护理": ["个人护理", "护理", "护肤", "身体护理", "美容护理", "护理产品", "个人清洁", "洗发水", "沐浴露", "牙膏", "卫生巾", "洗护用品", "洗护", "美甲", "香水", "整形", "医美"],
    "美味佳肴": ["美味", "佳肴", "美食", "做饭", "烹饪", "菜谱", "美食推荐", "餐厅", "探店", "食谱", "好吃", "甜品", "烘焙", "奶茶", "咖啡", "零食"],
    "职业发展": ["职业", "发展", "工作", "职场", "求职", "面试", "职业规划", "跳槽", "升职", "加薪", "简历", "副业", "创业", "职业培训", "职场行业", "职场干货"],
    "宠物天地": ["宠物", "猫", "狗", "养猫", "养狗", "萌宠", "宠物猫", "宠物狗", "铲屎官", "喵星人", "汪星人", "猫粮", "狗粮", "其他宠物", "宠物经验", "宠物食品", "宠物交流"],
    "潮流鞋包": ["潮流", "鞋包", "鞋子", "包包", "潮鞋", "名牌包", "运动鞋", "高跟鞋", "手提包", "球鞋", "帆布鞋", "靴子"],
    "日常生活": ["日常", "生活", "日常记录", "生活日常", "vlog日常", "生活分享", "好物推荐"],
    "科学探索": ["科学", "探索", "科普", "科学知识", "实验", "发现", "研究", "科技探索", "社科", "生活科普", "文化", "人文"],
    "新闻资讯": ["新闻", "资讯", "热点", "时事", "新闻报道", "新闻资讯", "最新消息", "民生新闻", "金融理财", "财经", "楼市资讯"],
    "体育锻炼": ["体育", "锻炼", "运动", "健身", "减肥", "瘦身", "体育运动", "健身房", "瑜伽", "跑步", "游泳", "篮球", "足球"],
}


def match_category(user_input: str):
    """
    根据用户输入匹配分类（最长关键词优先，避免短词抢占长词）

    规则：
    - 用户输入包含某分类的关键词 → 返回该分类（取命中关键词最长的分类，最精确）
    - 未命中任何关键词 → 返回 None（由调用方走"推荐相近分类"流程）

    Args:
        user_input: 用户输入的关键词或描述

    Returns:
        匹配的分类名称；未命中返回 None
    """
    if not user_input:
        return None

    user_input = user_input.lower().strip()
    best_category = None
    best_len = 0

    # 遍历分类关键词，取命中关键词最长的分类（最精确匹配）
    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            kw = keyword.lower()
            if kw in user_input and len(kw) > best_len:
                best_category = category
                best_len = len(kw)

    return best_category


def suggest_categories(user_input: str, top_n: int = 3) -> list:
    """
    根据用户输入推荐最相近的分类（用于关键词未精确命中时）

    评分逻辑：
    - 命中词加分：输入包含某分类的关键词 → 每个命中词 +5 并累加词长
    - 字符重合加分：输入字符与分类名/关键词字符集的重合数
    - 综合得分排序；**只返回得分>0（强相关）的分类，数量 1~top_n 个**；
      若所有分类得分均为 0（完全无关联），兜底返回 top_n 个

    Args:
        user_input: 用户输入的关键词或描述
        top_n: 推荐分类数量上限（默认3）

    Returns:
        推荐分类名称列表（按相关度降序，1~top_n 个）
    """
    if not user_input:
        return []

    user_input_lower = user_input.lower().strip()
    input_chars = set(user_input_lower)
    scores = {}

    for category, keywords in CATEGORY_KEYWORDS.items():
        related_words = [category.lower()] + [k.lower() for k in keywords]
        hit_score = 0
        char_overlap = 0

        for word in related_words:
            if word and word in user_input_lower:
                hit_score += 5 + len(word)
            if word:
                char_overlap += len(input_chars & set(word))

        scores[category] = hit_score + char_overlap

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    # 仅保留得分>0（强相关）的分类，数量不足 top_n 不强凑
    strong = [c for c, s in ranked if s > 0][:top_n]
    # 完全无关联时兜底返回 top_n 个
    if not strong:
        strong = [c for c, _ in ranked[:top_n]]
    return strong


def get_all_categories():
    """获取所有分类列表"""
    return list(CATEGORY_KEYWORDS.keys())


def fetch_explosive_articles(rank_date: str, category: str = "综合全部") -> dict:
    """
    调用API获取小红书七日爆款笔记数据（使用原生 requests）

    Args:
        rank_date: 日期（格式：yyyy-MM-dd）
        category: 分类名称（默认：综合全部）

    Returns:
        API返回的数据
    """
    credential = get_api_key()

    source = quote("小红书七日数据爆款文章-GitHub")
    category_encoded = quote(category)
    url = f"https://redfox.hk/story/api/cozeSkill/getXhsCozeSkillDataSeven?rankDate={rank_date}&source={source}&category={category_encoded}"

    headers = {
        "Content-Type": "application/json",
        "X-API-KEY": credential
    }

    try:
        response = requests.get(url, headers=headers, timeout=30)
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
    处理榜单数据，按互动数排序

    Args:
        data: API返回的原始数据
        top_n: 返回前N条数据（默认10条）

    Returns:
        排序后的榜单列表
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

    # 按互动数排序
    def get_interaction_score(article):
        # 优先从anaAdd对象获取互动数
        ana_add = article.get("anaAdd", {})
        interactive_count = ana_add.get("interactiveCount", 0) or article.get("interactiveCount", 0)
        # 处理 "2w+" 这样的格式
        if isinstance(interactive_count, str):
            if 'w+' in interactive_count.lower():
                num = float(interactive_count.lower().replace('w+', '').replace('w', ''))
                return int(num * 10000)
            try:
                return int(interactive_count)
            except:
                pass
        if interactive_count and int(interactive_count) > 0:
            return int(interactive_count)
        # 备用计算：点赞 + 收藏*2 + 评论*3 + 分享*5
        like_count = parse_count(ana_add.get("useLikeCount", 0) or article.get("useLikeCount", 0))
        collected_count = parse_count(ana_add.get("collectedCount", 0) or article.get("collectedCount", 0))
        comment_count = parse_count(ana_add.get("useCommentCount", 0) or article.get("useCommentCount", 0))
        share_count = parse_count(ana_add.get("useShareCount", 0) or article.get("useShareCount", 0))
        return like_count + collected_count * 2 + comment_count * 3 + share_count * 5

    sorted_articles = sorted(articles, key=get_interaction_score, reverse=True)

    return sorted_articles[:top_n]


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
        articles: 排序后的笔记列表
        category: 当前分类

    Returns:
        表格格式的字符串
    """
    if not articles:
        return f"未获取到【{clean_text(category)}】分类的爆款内容数据"

    output_lines = []

    # 表头 - 加粗并添加图标
    output_lines.append(f"**🔥 【{clean_text(category)}】七日爆款笔记**")
    output_lines.append("| 排名 | 笔记信息 | 互动数 | 点赞 | 评论 | 收藏 | 分享 |")
    output_lines.append("|:---:|:---|:---:|:---:|:---:|:---:|:---:|")

    for idx, article in enumerate(articles, 1):
        # 获取并清理所有字段
        title = clean_text(article.get("title", "无标题")) or "无标题"
        user_name = clean_text(article.get("userName", "未知用户")) or "未知用户"
        photo_jump_url = article.get("photoJumpUrl", "#") or "#"
        # URL中的空格编码为%20，其他特殊字符清理
        photo_jump_url = photo_jump_url.replace(" ", "%20")
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

        # 笔记信息：标题链接 + 作者（粉丝数）
        if photo_jump_url and photo_jump_url != "#":
            note_info = f"[{title}]({photo_jump_url})<br>{user_name}（{fans}粉丝）"
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
    parser = argparse.ArgumentParser(description="获取小红书七日爆款笔记")
    parser.add_argument("--rank_date", required=False, default=None, help="查询日期（格式：yyyy-MM-dd，默认今天）")
    parser.add_argument("--category", required=False, default=None, help="分类名称（如：时尚穿搭、美食佳肴等），不传则根据关键词匹配")
    parser.add_argument("--keyword", required=False, default=None, help="用户输入的关键词，用于自动匹配分类")
    parser.add_argument("--top_n", type=int, default=10, help="返回前N条数据（默认10）")
    parser.add_argument("--save_json", type=str, default=None, help="将原始API数据保存到指定JSON文件路径")
    parser.add_argument("--list_categories", action="store_true", help="列出所有可用分类")

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
            if category is None:
                # 关键词未精确命中任何分类：推荐3个相近分类 + API文档选项，等待用户确认
                # （Agent 需将推荐展示给用户，由用户确认分类后携带 --category 重新执行，或选择"若无..."停止流程）
                suggested = suggest_categories(args.keyword)
                print(f"根据关键词【{args.keyword}】未能精确匹配到具体分类")
                print("为您推荐以下相近分类：")
                for i, cat in enumerate(suggested, 1):
                    print(f"  {i}. {cat}")
                print("⚠️若无想要查询的分类，可前往 https://redfox.hk/apis/xiaohongshu/384C6W6B?source=github API文档查询更精确的作品~")
                print("请回复分类名称或序号确认查询分类（确认后将以指定分类重新查询），或回复\"若无\"停止本次查询。")
                return 0
            print(f"根据关键词【{args.keyword}】匹配到分类：【{category}】")
        else:
            category = "综合全部"

        print(f"正在获取小红书七日爆款笔记数据...")
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

        # 自动保存原始API数据到临时文件（供后续HTML生成复用，避免重复请求）
        # 如果指定了 --save_json，使用指定路径；否则自动保存到临时目录
        if args.save_json:
            save_path = args.save_json
        else:
            temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".cache")
            os.makedirs(temp_dir, exist_ok=True)
            safe_category = "".join(c for c in category if c.isalnum() or c in ('_', '-'))
            save_path = os.path.join(temp_dir, f"xhs_weekly_{safe_category}_{rank_date}.json")
        os.makedirs(os.path.dirname(save_path) or ".", exist_ok=True)
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"原始数据已保存到: {save_path}")

        # 处理并排序
        articles = process_ranking_data(data, args.top_n)

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
