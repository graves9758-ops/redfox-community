#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抖音相似账号推荐脚本
功能：调用红狐API查询抖音对标账号和头部账号，输出对标账号信息+近期作品+深度分析
接口文档：POST /dyUser/querySimilarAccounts
"""

import argparse
import json
import os
import platform
import re
import urllib.error
import urllib.parse
import urllib.request


# ============================================================
# API Key 管理
# ============================================================

def get_api_key():
    """获取 RedFox API Key，依次从环境变量、shell配置文件中读取，均未找到则提示用户配置"""
    api_key = os.getenv("REDFOX_API_KEY")
    if api_key:
        return api_key.strip()

    system = platform.system()
    if system == "Windows":
        api_key = _read_api_key_from_windows()
    else:
        api_key = _read_api_key_from_unix_shell_config()

    if api_key:
        return api_key.strip()

    if system == "Windows":
        config_hint = (
            "未找到 REDFOX_API_KEY 配置，请按以下步骤配置：\n"
            "  1. 访问 https://redfox.hk?source=github 注册账号并获取 API Key\n"
            "  2. 在 PowerShell 中执行：\n"
            '     [Environment]::SetEnvironmentVariable("REDFOX_API_KEY", "<你的API Key>", "User")\n'
            "  3. 重启终端后生效"
        )
    else:
        shell = os.getenv("SHELL", "")
        if "zsh" in shell:
            rc_file = "~/.zshrc"
        elif "bash" in shell:
            rc_file = "~/.bashrc"
        else:
            rc_file = "~/.bashrc"
        config_hint = (
            "未找到 REDFOX_API_KEY 配置，请按以下步骤配置：\n"
            "  1. 访问 https://redfox.hk?source=github 注册账号并获取 API Key\n"
            f"  2. 执行：echo 'export REDFOX_API_KEY=<你的API Key>' >> {rc_file}\n"
            f"  3. 执行：source {rc_file}"
        )
    raise ValueError(config_hint)


def _read_api_key_from_unix_shell_config():
    config_files = [
        os.path.expanduser("~/.zshrc"),
        os.path.expanduser("~/.bashrc"),
        os.path.expanduser("~/.bash_profile"),
        os.path.expanduser("~/.profile"),
    ]
    for config_file in config_files:
        if not os.path.isfile(config_file):
            continue
        try:
            with open(config_file, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line = line.strip()
                    m = re.match(r'^(?:export\s+)?REDFOX_API_KEY=["\']?(.+?)["\']?\s*$', line)
                    if m:
                        return m.group(1)
        except (IOError, OSError):
            continue
    return None


def _read_api_key_from_windows():
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment")
        try:
            value, _ = winreg.QueryValueEx(key, "REDFOX_API_KEY")
            if value:
                return str(value)
        finally:
            winreg.CloseKey(key)
    except (ImportError, OSError):
        pass

    ps_profile_paths = [
        os.path.join(os.path.expanduser("~"), "Documents", "WindowsPowerShell", "Microsoft.PowerShell_profile.ps1"),
        os.path.join(os.path.expanduser("~"), "Documents", "PowerShell", "Microsoft.PowerShell_profile.ps1"),
    ]
    for profile_path in ps_profile_paths:
        if not os.path.isfile(profile_path):
            continue
        try:
            with open(profile_path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line = line.strip()
                    m = re.match(r'\$env:REDFOX_API_KEY\s*=\s*["\']?(.+?)["\']?\s*$', line)
                    if m:
                        return m.group(1)
        except (IOError, OSError):
            continue
    return None


# ============================================================
# API 调用
# ============================================================

def query_similar_accounts(accountId=None, accountName=None):
    """调用API查询对标账号和头部账号

    接口文档：POST /dyUser/querySimilarAccounts
    两种查询模式：
      1. 传入accountId：通过账号ID查询该账号信息并匹配对标账号
      2. 传入accountName：通过账号名称查询该账号信息并匹配对标账号

    响应字段：
      data.currentAccount: DyUserInfoVO 当前账号信息（含redfoxIndex、similarAccounts）
      data.benchmarkAccounts: List<DySimilarAccountDetailVO> 对标账号列表（红狐指数向上最近的5个）
      data.topAccounts: List<DySimilarAccountDetailVO> 头部账号列表（同分类红狐指数倒序前5）
      账号详情 DySimilarAccountDetailVO: nickname, url, followerCount, uid,
        awemeCount, totalFavorited, awemeCountSeven, interactiveCountSeven,
        interactiveCountThirty, lastAwemeCreateTime, redfoxIndex, works[]
      作品 DyWorkVO: awemeId, title, coverUrl, desc, createTime, diggCount,
        commentCount, shareCount, playCount, interactiveCount, workUrl
    """
    credential = get_api_key()

    url = "https://redfox.hk/story/api/dyUser/querySimilarAccounts"
    headers = {
        "Content-Type": "application/json",
        "X-API-KEY": credential
    }

    payload = {}
    if accountId:
        payload["accountId"] = accountId
    if accountName:
        payload["accountName"] = accountName
    payload["source"] = "抖音相似账号推荐-GitHub"

    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise Exception(f"HTTP请求失败: {e.code}, {body}")
    except urllib.error.URLError as e:
        raise Exception(f"请求失败: {str(e)}")

    # 实际成功码为2000（非文档中的200）
    if result.get("code") not in (200, 2000):
        msg = result.get("msg", "未知错误")
        raise Exception(f"API返回错误: {msg}")

    data = result.get("data")
    if data is None:
        return None, [], []

    current_account = data.get("currentAccount")
    benchmark_accounts = data.get("benchmarkAccounts") or []
    top_accounts = data.get("topAccounts") or []

    return current_account, benchmark_accounts, top_accounts


# ============================================================
# 数据格式化
# ============================================================

def format_number(num):
    """格式化数字：< 10000直接展示，>= 10000格式化为X.Xw，>= 100000000格式化为X.X亿"""
    if num is None:
        return "0"
    if num >= 100000000:
        return f"{round(num / 100000000, 1)}亿"
    if num >= 10000:
        return f"{round(num / 10000, 1)}w"
    return str(num)


def calc_avg_play(account):
    """从works计算平均播放量"""
    works = account.get("works") or []
    if not works:
        return 0
    total = sum(w.get("playCount") or 0 for w in works)
    return total / len(works) if len(works) > 0 else 0


def calc_seven_day_plays(account):
    """计算近7天播放量：从works累加playCount"""
    works = account.get("works") or []
    if works:
        return sum(w.get("playCount") or 0 for w in works)
    return account.get("interactiveCountSeven") or 0


# ============================================================
# 内容分析辅助函数
# ============================================================

def _extract_content_themes(works):
    """从作品标题中提取内容主题聚焦方向"""
    if not works:
        return []

    theme_keywords = {
        "美食": ["美食", "菜谱", "做法", "食谱", "烹饪", "好吃", "探店", "下厨", "家常", "下饭", "快手菜"],
        "旅行": ["旅行", "旅游", "攻略", "景点", "出行", "打卡", "自驾"],
        "数码科技": ["科技", "数码", "手机", "电脑", "AI", "互联网", "软件", "测评"],
        "学习教育": ["科普", "知识", "考试", "高考", "考研", "培训", "学习", "升学", "原理", "揭秘"],
        "情感": ["情感", "婚姻", "爱情", "亲情", "家庭", "夫妻", "恋爱"],
        "小剧场": ["搞笑", "剧情", "段子", "整蛊", "反转", "沙雕", "短剧", "连载", "大结局"],
        "身体锻炼": ["健身", "运动", "减肥", "瑜伽", "跑步", "增肌"],
        "化妆美容": ["美妆", "护肤", "化妆", "口红", "粉底", "种草"],
        "潮流风尚": ["穿搭", "时尚", "搭配", "OOTD", "潮流", "衣服"],
        "亲子": ["亲子", "育儿", "宝宝", "孩子", "母婴", "早教"],
        "汽车": ["汽车", "新能源", "买车", "驾照", "车型", "评测"],
        "游戏": ["游戏", "电竞", "攻略", "排位", "上分", "直播"],
        "音乐": ["音乐", "翻唱", "歌曲", "吉他", "钢琴", "原创"],
        "动物": ["宠物", "猫", "狗", "萌宠", "撸猫", "遛狗"],
        "居家装修": ["装修", "家居", "设计", "改造", "收纳", "好物"],
        "财富理财": ["理财", "投资", "基金", "股票", "房产", "存款", "财经", "金融"],
        "三农": ["农村", "农活", "种地", "养殖", "家乡", "田园"],
        "健康医学": ["健康", "养生", "饮食", "睡眠", "中医", "医疗", "医生"],
        "舞蹈才艺": ["舞蹈", "编舞", "街舞", "古典舞", "教学"],
        "二次元": ["动漫", "漫画", "cos", "二次元", "手办"],
        "颜值造型": ["颜值", "造型", "变装", "化妆", "美颜"],
        "人文": ["人文", "社科", "历史", "哲学", "文化", "读书"],
        "影视": ["影视", "综艺", "电影", "电视剧", "解说", "影评"],
        "体育": ["体育", "足球", "篮球", "赛事", "奥运", "比赛"],
        "明星娱乐": ["明星", "八卦", "娱乐圈", "偶像", "追星"],
        "个人才艺": ["才艺", "技能", "手艺", "表演", "绝活"],
        "生活vlog": ["日常", "vlog", "记录", "生活", "沉浸式"],
    }

    all_text = " ".join(
        [w.get("title", "") for w in works if w.get("title")] +
        [w.get("desc", "") for w in works if w.get("desc")]
    )

    matched_themes = []
    for theme, keywords in theme_keywords.items():
        match_count = sum(1 for kw in keywords if kw in all_text)
        if match_count >= 1:
            matched_themes.append((theme, match_count))

    matched_themes.sort(key=lambda x: x[1], reverse=True)
    return [t[0] for t in matched_themes[:3]]


def _analyze_content_strategy(works):
    """分析内容策略和风格定位"""
    if not works:
        return ""

    style_parts = []
    has_cover = sum(1 for w in works if w.get("coverUrl"))
    if has_cover > len(works) * 0.5:
        style_parts.append("短视频")
    else:
        style_parts.append("图文/混剪")

    titles = [w.get("title", "") for w in works if w.get("title")]
    if titles:
        avg_len = sum(len(t) for t in titles) / len(titles)
        if avg_len > 30:
            style_parts.append("深度解析")
        elif avg_len < 10:
            style_parts.append("短平快")
        else:
            style_parts.append("中等深度")

    return "/".join(style_parts) if style_parts else ""


def _analyze_publish_schedule(works):
    """从作品发布时间推断发布时段规律"""
    if not works:
        return ""

    hours = []
    for w in works:
        pt = w.get("createTime") or ""
        m = re.search(r'(\d{1,2}):(\d{2})', pt)
        if m:
            hours.append(int(m.group(1)))

    if not hours:
        return ""

    from collections import Counter
    hour_counter = Counter(hours)
    most_common_hour, count = hour_counter.most_common(1)[0]
    total = len(hours)

    if 5 <= most_common_hour < 9:
        period = "早间"
    elif 9 <= most_common_hour < 12:
        period = "上午"
    elif 12 <= most_common_hour < 14:
        period = "午间"
    elif 14 <= most_common_hour < 18:
        period = "下午"
    elif 18 <= most_common_hour < 22:
        period = "晚间"
    else:
        period = "深夜"

    if count >= total * 0.6 and count >= 2:
        return f"{period}{most_common_hour}点固定发布"
    elif count >= 2:
        return f"{period}时段为主"
    return ""


def _extract_top_work(works, avg_play):
    """提取最高播放作品的标题（爆品引用），返回 (标题, 播放量) 或 None"""
    if not works or avg_play <= 0:
        return None

    top_work = max(works, key=lambda w: w.get("playCount") or 0)
    top_plays = top_work.get("playCount") or 0

    if top_plays >= avg_play * 2 and top_plays > 0:
        title = top_work.get("title") or ""
        if len(title) > 20:
            title = title[:18] + "…"
        return (title, top_plays)
    return None


def _calc_interaction_rate(works):
    """计算互动率：总互动数/播放量"""
    if not works:
        return None

    total_plays = sum(w.get("playCount") or 0 for w in works)
    total_interactive = sum(w.get("interactiveCount") or 0 for w in works)

    if total_plays <= 0 or total_interactive <= 0:
        return None

    rate = total_interactive / total_plays
    if rate > 1.0:
        return None
    if rate < 0.001:
        return None
    return rate


def _calc_like_rate(works):
    """计算点赞率：点赞数/播放量（diggCount/playCount）"""
    if not works:
        return None

    total_plays = sum(w.get("playCount") or 0 for w in works)
    total_likes = sum(w.get("diggCount") or 0 for w in works)

    if total_plays <= 0 or total_likes <= 0:
        return None

    rate = total_likes / total_plays
    if rate > 1.0 or rate < 0.001:
        return None
    return rate


def _add_sparse_data_reasons(parts, account, aweme_count_seven, works, content_themes):
    """当数据稀疏时，补充其他维度的推荐理由"""
    interactive_count_seven = account.get("interactiveCountSeven") or 0
    if interactive_count_seven > 0 and not any("互动" in p for p in parts):
        parts.append(f"近7天互动{format_number(interactive_count_seven)}，用户活跃度可参考")

    if works and not content_themes:
        topic = _infer_topic_from_titles(works)
        if topic:
            parts.append(f"内容方向：{topic}")

    if works and not any("点赞率" in p for p in parts):
        like_rate = _calc_like_rate(works)
        if like_rate and like_rate >= 0.01:
            parts.append(f"点赞率{like_rate*100:.1f}%，用户粘性强")

    if works and not any("发布" in p or "固定" in p or "时段" in p for p in parts):
        schedule = _analyze_publish_schedule(works)
        if schedule:
            parts.append(schedule)

    if aweme_count_seven > 0 and not any("更新" in p or "日更" in p or "周更" in p for p in parts):
        parts.append(f"近7天发布{aweme_count_seven}条，保持更新节奏")

    follower_count = account.get("followerCount") or 0
    total_favorited = account.get("totalFavorited") or 0
    if follower_count > 0 and not any("粉丝" in p for p in parts):
        parts.append(f"粉丝{format_number(follower_count)}，总获赞{format_number(total_favorited)}，账号体量可参考")

    if len(parts) < 2:
        parts.append("同赛道定位匹配，可参考其内容策略和运营节奏")


def _infer_topic_from_titles(works):
    """从作品标题中推断内容方向"""
    if not works:
        return ""

    titles = [w.get("title", "") for w in works if w.get("title")]
    if not titles:
        return ""

    extended_themes = {
        "美食": ["美食", "菜谱", "做法", "食谱", "烹饪", "好吃", "探店"],
        "旅行": ["旅行", "旅游", "攻略", "景点", "出行", "打卡"],
        "数码科技": ["科技", "数码", "手机", "电脑", "AI", "互联网", "软件"],
        "学习教育": ["科普", "知识", "原理", "揭秘", "考试", "学习"],
        "小剧场": ["搞笑", "剧情", "段子", "反转"],
        "化妆美容": ["美妆", "护肤", "化妆", "口红", "种草"],
        "汽车": ["汽车", "新能源", "买车", "车型"],
        "游戏": ["游戏", "电竞", "攻略", "上分"],
        "亲子": ["亲子", "育儿", "宝宝", "孩子", "母婴"],
        "情感": ["情感", "婚姻", "爱情", "恋爱"],
        "财富理财": ["理财", "投资", "基金", "股票"],
        "健康医学": ["健康", "养生", "医疗", "中医"],
    }

    all_titles_text = " ".join(titles)
    matched = []
    for theme, keywords in extended_themes.items():
        match_count = sum(1 for kw in keywords if kw in all_titles_text)
        if match_count >= 1:
            matched.append(theme)

    return "/".join(matched[:2]) if matched else ""


def bold_bracket_content(text):
    """将「」中的内容加粗展示"""
    return re.sub(r'「([^」]+)」', r'「**\1**」', text)


def _describe_like_level(like_rate):
    """根据点赞率分级描述用户粘性"""
    pct = like_rate * 100
    if pct >= 5:
        return f"点赞率{pct:.1f}%，用户粘性极强"
    elif pct >= 3:
        return f"点赞率{pct:.1f}%，用户粘性强"
    else:
        return f"点赞率{pct:.1f}%，粘性尚可"


# ============================================================
# 推荐理由生成
# ============================================================

def generate_recommendation_reason(account, query_avg_play=None, query_redfox_index=None):
    """生成推荐理由：基于账号数据、内容数据、更新节奏等多维度总结值得学习点

    当查询账号红狐指数为0时，走「学习点总结」模式：
    基于账号数据、内容数据、更新节奏、整体内容策略定位等总结该账号的值得学习点
    eg: 同赛道近7天2篇爆文，全聚焦于历史人物、历史事件的深度分析，路径可复制

    当查询账号红狐指数>0时，走标准8级维度模式。
    """
    # 判断是否走「学习点总结」模式（查询账号红狐指数为0）
    is_zero_redfox = query_redfox_index is None or query_redfox_index <= 0

    if is_zero_redfox:
        return _generate_learning_point_reason(account, query_avg_play)

    # ===== 以下为标准8级维度模式（红狐指数>0） =====
    parts = []

    works = account.get("works") or []
    aweme_count_seven = account.get("awemeCountSeven") or 0
    follower_count = account.get("followerCount") or 0
    total_favorited = account.get("totalFavorited") or 0
    interactive_count_seven = account.get("interactiveCountSeven") or 0

    # 从 works 计算播放数据
    works_total_plays = sum(w.get("playCount") or 0 for w in works) if works else 0
    works_avg_play = works_total_plays / len(works) if works and len(works) > 0 else 0
    effective_avg = works_avg_play if works_avg_play > 0 else 0

    # 1. 内容主题聚焦
    burst_works = []
    if works and effective_avg > 0:
        for w in works:
            plays = w.get("playCount") or 0
            if plays >= effective_avg * 2:
                burst_works.append(w)

    content_themes = _extract_content_themes(works) if works else []

    if burst_works and content_themes:
        burst_count = len(burst_works)
        theme_str = "/".join(content_themes[:2])
        parts.append(f"近7天{burst_count}条爆品，聚焦于{theme_str}")
    elif burst_works:
        burst_count = len(burst_works)
        parts.append(f"近7天{burst_count}条爆品")
    elif content_themes:
        theme_str = "/".join(content_themes[:2])
        parts.append(f"内容聚焦于{theme_str}")

    # 2. 爆品标题引用
    if works and effective_avg > 0:
        top_work = _extract_top_work(works, effective_avg)
        if top_work:
            title, plays = top_work
            parts.append(f"爆品「{title}」达均播{plays/effective_avg:.1f}倍")

    # 3. 与查询账号的播放倍数对比
    if query_avg_play and query_avg_play > 0 and effective_avg > 0:
        ratio = effective_avg / query_avg_play
        if ratio >= 3:
            parts.append(f"均播约为你的{ratio:.1f}倍，模式成熟可追赶")
        elif ratio >= 1.5:
            parts.append(f"均播约为你的{ratio:.1f}倍，运营策略可参考")
        elif 0.7 <= ratio <= 1.3:
            parts.append(f"均播与你接近，玩法可直接复制")
        elif ratio < 0.7:
            parts.append(f"均播约为你的{ratio:.1f}倍，起号阶段可互鉴")

    # 4. 更新节奏 + 近7天发布量 + 内容策略
    strategy_parts = []
    if aweme_count_seven >= 7:
        strategy_parts.append(f"日更高产（近7天{aweme_count_seven}条）")
    elif aweme_count_seven >= 4:
        strategy_parts.append(f"稳定周更（近7天{aweme_count_seven}条）")
    elif aweme_count_seven >= 1:
        strategy_parts.append(f"持续更新（近7天{aweme_count_seven}条）")

    content_style = _analyze_content_strategy(works)
    if content_style:
        strategy_parts.append(content_style)

    if works:
        schedule = _analyze_publish_schedule(works)
        if schedule:
            strategy_parts.append(schedule)

    if strategy_parts:
        parts.append("，".join(strategy_parts))

    # 5. 数据亮点：互动率 + 点赞率
    if works:
        interaction_rate = _calc_interaction_rate(works)
        if interaction_rate and interaction_rate >= 0.005:
            parts.append(f"互动率{interaction_rate*100:.1f}%")

        like_rate = _calc_like_rate(works)
        if like_rate and like_rate >= 0.01:
            parts.append(_describe_like_level(like_rate))

    # 6. 粉丝量级 + 总获赞 + 红狐指数对比
    if follower_count > 0:
        parts.append(f"粉丝{format_number(follower_count)}，总获赞{format_number(total_favorited)}")

    redfox_index = account.get("redfoxIndex")
    if redfox_index is not None and query_redfox_index is not None and query_redfox_index > 0:
        diff = redfox_index - query_redfox_index
        if diff > 0:
            parts.append(f"红狐指数{redfox_index:.1f}，高出你{diff:.1f}点")
        elif abs(diff) < 5:
            parts.append(f"红狐指数{redfox_index:.1f}，与你接近")

    # 7. 近7天互动数据
    if interactive_count_seven > 0 and effective_avg == 0:
        parts.append(f"近7天互动{format_number(interactive_count_seven)}，用户活跃度可参考")

    # 8. 数据稀疏补充
    if effective_avg == 0:
        _add_sparse_data_reasons(parts, account, aweme_count_seven, works, content_themes)

    # 9. 结论兜底
    if parts:
        result = "<br>".join(parts)
    else:
        fallback_parts = []
        if follower_count > 0:
            fallback_parts.append(f"粉丝{format_number(follower_count)}")
        if total_favorited > 0:
            fallback_parts.append(f"总获赞{format_number(total_favorited)}")
        if aweme_count_seven > 0:
            fallback_parts.append(f"7天发布{aweme_count_seven}条")
        if interactive_count_seven > 0:
            fallback_parts.append(f"7天互动{format_number(interactive_count_seven)}")
        result = "，".join(fallback_parts) + "，可参考运营策略" if fallback_parts else "同赛道对标账号，可参考运营策略"

    result = bold_bracket_content(result)

    if len(result) < 20:
        result += "，可参考运营策略"

    return result


def _generate_learning_point_reason(account, query_avg_play=None):
    """红狐指数为0时的推荐理由：基于账号数据、内容数据、更新节奏、整体内容策略定位等总结值得学习点

    eg: 同赛道近7天2篇爆文，全聚焦于历史人物、历史事件的深度分析，路径可复制
    """
    parts = []

    works = account.get("works") or []
    aweme_count_seven = account.get("awemeCountSeven") or 0
    follower_count = account.get("followerCount") or 0
    total_favorited = account.get("totalFavorited") or 0
    interactive_count_seven = account.get("interactiveCountSeven") or 0

    # 从 works 计算播放数据
    works_total_plays = sum(w.get("playCount") or 0 for w in works) if works else 0
    works_avg_play = works_total_plays / len(works) if works and len(works) > 0 else 0
    effective_avg = works_avg_play if works_avg_play > 0 else 0

    content_themes = _extract_content_themes(works) if works else []

    # 1. 同赛道 + 爆品/内容聚焦 + 路径可复制
    if works and content_themes:
        # 统计高互动作品（互动量 >= 平均互动2倍视为爆品）
        interactive_list = [w.get("interactiveCount") or 0 for w in works]
        avg_interactive = sum(interactive_list) / len(interactive_list) if interactive_list else 0
        burst_count = sum(1 for ic in interactive_list if ic >= avg_interactive * 2 and ic > 0) if avg_interactive > 0 else 0
        theme_str = "/".join(content_themes[:2])

        if burst_count > 0:
            parts.append(f"同赛道近7天{burst_count}篇爆文，全聚焦于{theme_str}，路径可复制")
        else:
            parts.append(f"同赛道内容聚焦于{theme_str}，内容策略可参考")
    elif content_themes:
        theme_str = "/".join(content_themes[:2])
        parts.append(f"同赛道内容聚焦于{theme_str}，内容策略可参考")

    # 2. 更新节奏 + 内容策略定位
    strategy_parts = []
    if aweme_count_seven >= 7:
        strategy_parts.append(f"日更高产（近7天{aweme_count_seven}条）")
    elif aweme_count_seven >= 4:
        strategy_parts.append(f"稳定周更（近7天{aweme_count_seven}条）")
    elif aweme_count_seven >= 1:
        strategy_parts.append(f"持续更新（近7天{aweme_count_seven}条）")

    content_style = _analyze_content_strategy(works)
    if content_style:
        strategy_parts.append(content_style)

    if works:
        schedule = _analyze_publish_schedule(works)
        if schedule:
            strategy_parts.append(schedule)

    if strategy_parts:
        parts.append("，".join(strategy_parts))

    # 3. 互动/点赞数据亮点
    if works:
        interaction_rate = _calc_interaction_rate(works)
        if interaction_rate and interaction_rate >= 0.005:
            parts.append(f"互动率{interaction_rate*100:.1f}%")

        like_rate = _calc_like_rate(works)
        if like_rate and like_rate >= 0.01:
            parts.append(_describe_like_level(like_rate))

    # 4. 粉丝量级 + 总获赞
    if follower_count > 0:
        parts.append(f"粉丝{format_number(follower_count)}，总获赞{format_number(total_favorited)}")

    # 5. 近7天互动
    if interactive_count_seven > 0 and effective_avg == 0:
        parts.append(f"近7天互动{format_number(interactive_count_seven)}")

    # 6. 数据稀疏补充
    if effective_avg == 0:
        _add_sparse_data_reasons(parts, account, aweme_count_seven, works, content_themes)

    # 结论兜底
    if not parts:
        fallback_parts = []
        if follower_count > 0:
            fallback_parts.append(f"粉丝{format_number(follower_count)}")
        if total_favorited > 0:
            fallback_parts.append(f"总获赞{format_number(total_favorited)}")
        if aweme_count_seven > 0:
            fallback_parts.append(f"7天发布{aweme_count_seven}条")
        if interactive_count_seven > 0:
            fallback_parts.append(f"7天互动{format_number(interactive_count_seven)}")
        parts = ["，".join(fallback_parts) + "，运营策略可参考"] if fallback_parts else ["同赛道对标账号，运营策略可参考"]

    result = "<br>".join(parts)
    result = bold_bracket_content(result)

    if len(result) < 20:
        result += "，运营策略可参考"

    return result


# ============================================================
# 输出格式化
# ============================================================

def format_account_info(account, label="查询账号"):
    """格式化账号基本信息（适配新版接口currentAccount/DyUserInfoVO）"""
    if not account:
        return f"未获取到{label}信息"

    lines = []
    lines.append(f"**{label}基本信息**")
    lines.append("")

    nickname = account.get("nickname") or "未知"
    # 统一使用secUid拼接抖音主页链接，secUid为空时回退uid
    sec_uid = account.get("secUid") or ""
    uid = account.get("uid") or ""
    if sec_uid:
        url = f"https://www.douyin.com/user/{sec_uid}"
    elif uid and uid != "未知":
        url = f"https://www.douyin.com/user/{uid}"
    else:
        url = "#"
    account_id = account.get("accountId") or ""
    follower_count = account.get("followerCount") or 0
    aweme_count = account.get("awemeCount") or 0
    total_favorited = account.get("totalFavorited") or 0
    aweme_count_seven = account.get("awemeCountSeven") or 0
    # currentAccount 无 awemeCountSeven 字段，用 works 列表长度代替
    if aweme_count_seven == 0:
        works_list = account.get("works") or []
        if works_list:
            aweme_count_seven = len(works_list)
    interactive_count_seven = account.get("interactiveCountSeven") or 0
    interactive_count_thirty = account.get("interactiveCountThirty") or 0
    last_aweme_create_time = account.get("lastAwemeCreateTime") or "未知"
    signature = account.get("signature") or ""
    gender = account.get("gender") or ""
    province = account.get("province") or ""
    city = account.get("city") or ""
    ip_location = account.get("ipLocation") or ""
    redfox_index = account.get("redfoxIndex")
    crawl_time = account.get("crawlTime") or ""

    lines.append(f"- 账号名称：[{nickname}]({url})")
    if account_id:
        lines.append(f"- 抖音号：{account_id}")
    lines.append(f"- 账号ID（uid）：{uid}")
    if signature:
        sig = signature.replace("\n", " | ")
        lines.append(f"- 简介：{sig}")
    if gender:
        lines.append(f"- 性别：{gender}")
    location_parts = [p for p in [province, city] if p]
    if location_parts:
        lines.append(f"- 地区：{''.join(location_parts)}")
    if ip_location:
        lines.append(f"- IP属地：{ip_location}")
    lines.append(f"- 粉丝数：{format_number(follower_count)}")
    lines.append(f"- 总获赞数：{format_number(total_favorited)}")
    lines.append(f"- 作品总数：{format_number(aweme_count)}")
    if redfox_index is not None:
        lines.append(f"- 红狐指数：{redfox_index}")
    lines.append(f"- 近7天发布数：{aweme_count_seven}")
    lines.append(f"- 近7天互动量：{format_number(interactive_count_seven)}")
    if interactive_count_thirty:
        lines.append(f"- 近30天互动数：{format_number(interactive_count_thirty)}")
    lines.append(f"- 最近作品发布：{last_aweme_create_time}")

    # 近期作品
    works = account.get("works") or []
    if works:
        lines.append("")
        lines.append("**近期作品**")
        lines.append("")
        lines.append("| 作品标题 | 点赞数 | 评论数 | 分享数 | 总互动数 | 发布时间 |")
        lines.append("| --- | --- | --- | --- | --- | --- |")
        for w in works[:5]:
            title = w.get("title") or "无标题"
            work_url = w.get("workUrl") or ""
            if work_url:
                title = f"[{title}]({work_url})"
            diggs = format_number(w.get("diggCount"))
            comments = format_number(w.get("commentCount"))
            shares = format_number(w.get("shareCount"))
            interactive = format_number(w.get("interactiveCount"))
            create_time = w.get("createTime") or "未知"
            lines.append(f"| {title} | {diggs} | {comments} | {shares} | {interactive} | {create_time} |")

    return "\n".join(lines)


def format_table(accounts, title_line, query_avg_play=None, query_redfox_index=None, current_account=None):
    """格式化对标账号Markdown表格（含红狐指数），本账号置首行"""
    lines = []
    lines.append(title_line)
    lines.append("")
    lines.append("| 账号名称 | 粉丝数 | 总获赞 | 近7天互动 | 红狐指数 | 指数差距 | 推荐理由 |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- |")

    # 本账号置首行
    if current_account:
        ca_nickname = current_account.get("nickname") or "未知"
        # 统一使用secUid拼接抖音主页链接，secUid为空时回退uid
        ca_sec_uid = current_account.get("secUid") or ""
        ca_uid = current_account.get("uid") or ""
        if ca_sec_uid:
            ca_url = f"https://www.douyin.com/user/{ca_sec_uid}"
        elif ca_uid:
            ca_url = f"https://www.douyin.com/user/{ca_uid}"
        else:
            ca_url = "#"
        ca_followers = current_account.get("followerCount") or 0
        ca_favorited = current_account.get("totalFavorited") or 0
        ca_interactive_seven = current_account.get("interactiveCountSeven") or 0
        ca_redfox = current_account.get("redfoxIndex")

        ca_link = f"**[{ca_nickname}]({ca_url})**"
        ca_followers_display = format_number(ca_followers)
        ca_favorited_display = format_number(ca_favorited)
        ca_interactive_display = format_number(ca_interactive_seven)
        ca_redfox_display = f"{ca_redfox:.1f}" if ca_redfox is not None else "-"
        ca_diff_display = "本账号"
        ca_reason = "「**本账号**」"

        lines.append(f"| {ca_link} | {ca_followers_display} | {ca_favorited_display} | {ca_interactive_display} | {ca_redfox_display} | {ca_diff_display} | {ca_reason} |")

    for account in accounts:
        nickname = account.get("nickname") or "未知"
        # 统一使用secUid拼接抖音主页链接，secUid为空时回退uid
        sec_uid = account.get("secUid") or ""
        uid = account.get("uid") or ""
        if sec_uid:
            url = f"https://www.douyin.com/user/{sec_uid}"
        elif uid:
            url = f"https://www.douyin.com/user/{uid}"
        else:
            url = "#"
        follower_count = account.get("followerCount") or 0
        total_favorited = account.get("totalFavorited") or 0
        interactive_count_seven = account.get("interactiveCountSeven") or 0
        redfox_index = account.get("redfoxIndex")

        account_link = f"[{nickname}]({url})"
        followers_display = format_number(follower_count)
        favorited_display = format_number(total_favorited)
        interactive_display = format_number(interactive_count_seven)
        redfox_display = f"{redfox_index:.1f}" if redfox_index is not None else "-"

        # 计算指数差距
        if redfox_index is not None and query_redfox_index is not None and query_redfox_index > 0:
            diff = redfox_index - query_redfox_index
            if diff > 0:
                diff_display = f"+{diff:.1f}"
            elif diff < 0:
                diff_display = f"{diff:.1f}"
            else:
                diff_display = "0"
        else:
            diff_display = "-"

        recommendation = generate_recommendation_reason(account, query_avg_play, query_redfox_index)
        lines.append(f"| {account_link} | {followers_display} | {favorited_display} | {interactive_display} | {redfox_display} | {diff_display} | {recommendation} |")

    return "\n".join(lines)


def generate_analysis_summary(benchmark_accounts, top_accounts, query_avg_play=None, query_redfox_index=None):
    """生成深度分析：共通点 + 差异 + 建议"""
    lines = []
    lines.append("")
    lines.append("**深度分析**")
    lines.append("")

    all_accounts = (benchmark_accounts or []) + (top_accounts or [])
    if not all_accounts:
        return ""

    # --- 共通点分析 ---
    lines.append("📌 **共通点**")
    common_points = []

    # 更新节奏共通
    update_counts = [acc.get("awemeCountSeven") or 0 for acc in all_accounts if acc.get("awemeCountSeven")]
    if update_counts:
        avg_update = sum(update_counts) / len(update_counts)
        if avg_update >= 7:
            common_points.append(f"- 更新节奏：同赛道账号普遍日更（平均近7天{avg_update:.0f}条）")
        elif avg_update >= 3:
            common_points.append(f"- 更新节奏：同赛道账号平均近7天{avg_update:.0f}条，保持稳定更新")
        else:
            common_points.append(f"- 更新节奏：同赛道账号平均近7天{avg_update:.0f}条，低频高质型")

    # 互动表现共通
    interaction_rates = []
    for acc in all_accounts:
        works = acc.get("works") or []
        rate = _calc_interaction_rate(works)
        if rate:
            interaction_rates.append(rate)
    if interaction_rates:
        avg_rate = sum(interaction_rates) / len(interaction_rates)
        common_points.append(f"- 互动表现：相似账号平均互动率{avg_rate*100:.1f}%，反映该赛道用户互动偏好")

    # 粉丝量级分布
    follower_counts = [acc.get("followerCount") or 0 for acc in all_accounts if acc.get("followerCount")]
    if follower_counts:
        avg_followers = sum(follower_counts) / len(follower_counts)
        common_points.append(f"- 粉丝量级：相似账号平均粉丝{format_number(avg_followers)}，处于同一发展阶段")

    # 红狐指数分布
    redfox_indices = [acc.get("redfoxIndex") for acc in all_accounts if acc.get("redfoxIndex") is not None]
    if redfox_indices:
        avg_redfox = sum(redfox_indices) / len(redfox_indices)
        common_points.append(f"- 红狐指数：相似账号平均{avg_redfox:.1f}")

    if common_points:
        lines.extend(common_points)
    else:
        lines.append("- 同赛道账号，内容方向和目标受众有较高重合度")

    # --- 差异分析 ---
    lines.append("")
    lines.append("📊 **差异分析**")
    diff_points = []

    # 红狐指数差异
    if query_redfox_index is not None:
        benchmark_redfox = [acc.get("redfoxIndex") for acc in (benchmark_accounts or []) if acc.get("redfoxIndex") is not None]
        top_redfox = [acc.get("redfoxIndex") for acc in (top_accounts or []) if acc.get("redfoxIndex") is not None]
        if benchmark_redfox:
            avg_bench = sum(benchmark_redfox) / len(benchmark_redfox)
            diff = avg_bench - query_redfox_index
            direction = "高" if diff > 0 else "低"
            diff_points.append(f"- 红狐指数差距：对标账号平均{avg_bench:.1f}，比你{direction}{abs(diff):.1f}点")
        if top_redfox:
            max_top = max(top_redfox)
            diff = max_top - query_redfox_index
            if diff > 0:
                diff_points.append(f"- 头部差距：头部标杆最高红狐指数{max_top:.1f}，比你高{diff:.1f}点")
            elif diff < 0:
                diff_points.append(f"- 红狐指数领先：你的红狐指数{query_redfox_index:.1f}已超过头部标杆最高{max_top:.1f}，表现优异")
            else:
                diff_points.append(f"- 红狐指数持平：你的红狐指数与头部标杆最高{max_top:.1f}一致")

    if query_avg_play and query_avg_play > 0:
        # 对标账号播放量差异
        bench_plays = []
        for acc in (benchmark_accounts or []):
            works = acc.get("works") or []
            if works:
                avg = sum(w.get("playCount") or 0 for w in works) / len(works)
                bench_plays.append(avg)
        if bench_plays:
            bench_avg = sum(bench_plays) / len(bench_plays)
            ratio = bench_avg / query_avg_play
            if ratio > 1.3:
                diff_points.append(f"- 播放量差距：对标账号均播是你的{ratio:.1f}倍，内容吸引力有提升空间")
            elif 0.7 <= ratio <= 1.3:
                diff_points.append(f"- 播放量差距：对标账号均播与你接近，竞争激烈需差异化突围")

        # 头部播放量差异
        top_plays = []
        for acc in (top_accounts or []):
            works = acc.get("works") or []
            if works:
                avg = sum(w.get("playCount") or 0 for w in works) / len(works)
                top_plays.append(avg)
        if top_plays:
            top_avg = sum(top_plays) / len(top_plays)
            ratio = top_avg / query_avg_play
            diff_points.append(f"- 头部差距：头部标杆均播是你的{ratio:.1f}倍，模式成熟可追赶")

    # 更新节奏差异
    bench_updates = [acc.get("awemeCountSeven") or 0 for acc in (benchmark_accounts or []) if acc.get("awemeCountSeven")]
    if bench_updates:
        max_update = max(bench_updates)
        if max_update >= 7:
            diff_points.append(f"- 更新节奏差异：部分对标账号日更（近7天{max_update}条），高频更新是流量基础")

    if diff_points:
        lines.extend(diff_points)
    else:
        lines.append("- 建议对比各账号的内容形式、更新节奏和互动策略，找到差异化突破点")

    # --- 优化建议 ---
    lines.append("")
    lines.append("💡 **优化建议**")
    suggestions = []

    # 基于数据差异给出建议
    if benchmark_accounts:
        top_bench = max(benchmark_accounts, key=lambda a: a.get("interactiveCountSeven") or 0)
        top_update = top_bench.get("awemeCountSeven") or 0
        if top_update >= 5:
            suggestions.append(f"1. **提升更新频率**：互动量最高的对标账号近7天发布{top_update}条，建议保持稳定更新节奏")

    if top_accounts:
        top_head = max(top_accounts, key=lambda a: a.get("followerCount") or 0)
        high_followers = top_head.get("followerCount") or 0
        high_works = top_head.get("works") or []
        if high_works:
            high_like_rate = _calc_like_rate(high_works)
            if high_like_rate and high_like_rate >= 0.03:
                suggestions.append(f"2. **优化内容吸引力**：头部标杆点赞率{high_like_rate*100:.1f}%，建议强化开头3秒吸引力和选题热度")

    if not suggestions:
        suggestions.append("1. **学习对标账号的内容方向和选题策略**，找到适合自己的内容定位")
        suggestions.append("2. **参考头部标杆的运营模式**，逐步提升内容质量和更新节奏")
        suggestions.append("3. **关注互动率高的账号**，学习其内容形式和互动引导方式")

    lines.extend(suggestions)

    return "\n".join(lines)


def format_output(current_account, benchmark_accounts, top_accounts, query_avg_play=None, query_redfox_index=None):
    """格式化完整文本输出（适配新版接口）"""
    output_lines = []

    # 当前账号基本信息（优先使用querySimilarAccounts返回的currentAccount）
    if current_account:
        output_lines.append(format_account_info(current_account, "查询账号"))
        output_lines.append("")

    # 匹配结果
    bench_count = len(benchmark_accounts) if benchmark_accounts else 0
    top_count = len(top_accounts) if top_accounts else 0

    tips_parts = []
    if bench_count > 0:
        tips_parts.append(f"【对标账号（{bench_count}个）】")
    if top_count > 0:
        tips_parts.append(f"【头部账号（{top_count}个）】")

    if tips_parts:
        output_lines.append(f"为你匹配到{'和'.join(tips_parts)}的{len(tips_parts)}组推荐，可按需参考：")

        if benchmark_accounts:
            total_bench = bench_count + (1 if current_account else 0)
            table_title = f"👉【对标账号（{total_bench}个）】（红狐指数向上最近的账号，可直接复制玩法）"
            output_lines.append(format_table(benchmark_accounts, table_title, query_avg_play, query_redfox_index, current_account))

        if top_accounts:
            table_title = f"👉【头部账号（{top_count}个）】（同分类红狐指数倒序前5，模式成熟可追赶）"
            output_lines.append(format_table(top_accounts, table_title, query_avg_play, query_redfox_index))

        # 深度分析
        analysis = generate_analysis_summary(benchmark_accounts, top_accounts, query_avg_play, query_redfox_index)
        if analysis:
            output_lines.append(analysis)
    else:
        output_lines.append("当前未查询到相关对标账号数据。可能原因：1) 抖音号或名称输入有误；2) 暂无相关对标数据。")
        output_lines.append("建议：确认抖音号/名称是否正确后重新查询。")

    # 数据说明统一放在末尾
    crawl_time = current_account.get("crawlTime") if current_account else None
    output_lines.append("")
    if crawl_time:
        output_lines.append(f"*数据更新时间：{crawl_time}*")
    output_lines.append("*红狐指数：每周更新，若统计周期内账号未发布作品，红狐指数可能为0。*")

    # 订阅服务提示
    account_name = current_account.get("nickname") or account_id if current_account else account_id
    output_lines.append("")
    output_lines.append(format_subscription_prompt(account_name))

    return "\n".join(output_lines)


# ============================================================
def format_subscription_prompt(account_name):
    """查询结果末尾输出订阅服务提示文案"""
    lines = []
    lines.append(f"是否订阅「{account_name}」的相似账号最新信息推送？")
    lines.append("")
    lines.append("1. 每日下午19点推送最新数据。可自行选择推送频率和时间~")
    lines.append("2. 暂不需要")
    return "\n".join(lines)



def main():
    parser = argparse.ArgumentParser(description="抖音相似账号推荐脚本")
    parser.add_argument("--account_id", help="抖音账号ID或昵称（支持unique_id、short_id、uid、昵称）")

    args = parser.parse_args()

    if not args.account_id:
        print("错误：请提供 --account_id 抖音号或昵称")
        return

    try:
        # 判断输入是昵称还是抖音号/uid
        is_likely_nickname = bool(re.search(r'[\u4e00-\u9fff]', args.account_id))

        # 直接调用 querySimilarAccounts，支持 accountName 和 accountId 两种方式
        if is_likely_nickname:
            current_account, benchmark_accounts, top_accounts = query_similar_accounts(accountName=args.account_id)
        else:
            current_account, benchmark_accounts, top_accounts = query_similar_accounts(accountId=args.account_id)

        # 计算当前账号的平均播放量
        query_avg_play = None
        query_redfox_index = None
        if current_account:
            works = current_account.get("works") or []
            if works:
                query_avg_play = sum(w.get("playCount") or 0 for w in works) / len(works)
            query_redfox_index = current_account.get("redfoxIndex")

        # 格式化输出
        result = format_output(current_account, benchmark_accounts, top_accounts, query_avg_play, query_redfox_index)
        print(result)

    except Exception as e:
        error_msg = str(e)
        # 账号未找到时，输出提示信息
        if "未找到账号" in error_msg:
            print("未查询到当前账号的相关信息，请检查输入的抖音号或昵称是否正确。")
        else:
            print(f"查询失败: {error_msg}")


if __name__ == "__main__":
    main()
