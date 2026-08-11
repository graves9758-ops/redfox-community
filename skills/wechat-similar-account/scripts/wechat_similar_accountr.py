#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
公众号账号推荐脚本
功能：调用API查询对标账号和头部账号，输出查询账号基本信息+近5篇文章
"""

import argparse
import json
import os
import platform
import re
import urllib.error
import urllib.parse
import urllib.request


def get_api_key():
    """获取 RedFox API Key，依次从环境变量、shell配置文件中读取，均未找到则提示用户配置"""
    # 1. 从环境变量获取
    api_key = os.getenv("REDFOX_API_KEY")
    if api_key:
        return api_key.strip()

    # 2. 从shell配置文件中读取
    system = platform.system()
    if system == "Windows":
        api_key = _read_api_key_from_windows()
    else:
        api_key = _read_api_key_from_unix_shell_config()

    if api_key:
        return api_key.strip()

    # 3. 未找到，提示用户配置
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
    """从 Unix shell 配置文件中读取 REDFOX_API_KEY"""
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
                    # 匹配 export REDFOX_API_KEY=xxx 或 REDFOX_API_KEY=xxx
                    m = re.match(r'^(?:export\s+)?REDFOX_API_KEY=["\']?(.+?)["\']?\s*$', line)
                    if m:
                        return m.group(1)
        except (IOError, OSError):
            continue
    return None


def _read_api_key_from_windows():
    """从 Windows 环境中读取 REDFOX_API_KEY（注册表 + PowerShell Profile）"""
    # 2a. 尝试从注册表读取用户级环境变量
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

    # 2b. 尝试从 PowerShell Profile 读取
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
                    # 匹配 $env:REDFOX_API_KEY = "xxx" 或 setx REDFOX_API_KEY xxx
                    m = re.match(r'\$env:REDFOX_API_KEY\s*=\s*["\']?(.+?)["\']?\s*$', line)
                    if m:
                        return m.group(1)
        except (IOError, OSError):
            continue

    return None


def query_similar_accounts(accountId=None, accountName=None, accountType=None):
    """调用API查询对标账号和头部账号"""
    credential = get_api_key()

    url = "https://redfox.hk/story/api/gzhUser/querySimilarAccounts"
    headers = {
        "Content-Type": "application/json",
        "X-API-KEY": credential
    }

    payload = {
        "accountId": accountId if accountId else "",
        "accountName": accountName if accountName else "",
        "accountType": accountType if accountType else "",
        "source": "公众号相似账号推荐-GitHub"
    }

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

    if "data" not in result:
        raise Exception(f"API返回格式错误: {result}")

    data = result.get("data")
    if data is None:
        # API返回未找到账号，返回空数据让主流程走"未查询到账号"提示
        return None, [], []

    # API 返回 currentAccount（查询账号信息）、benchmarkAccounts（同阶对标）、topAccounts（高阶标杆）
    current_account = data.get("currentAccount")
    benchmark_accounts = data.get("benchmarkAccounts", [])
    top_accounts = data.get("topAccounts", [])

    return current_account, benchmark_accounts, top_accounts


def format_number(num):
    """格式化数字：< 10000直接展示，>= 10000格式化为X.Xw"""
    if num is None:
        return "0"
    if num >= 10000:
        return f"{round(num / 10000, 1)}w"
    return str(num)


def get_account_url(account_id):
    """生成账号跳转链接"""
    return f"https://open.weixin.qq.com/qr/code?username={account_id}"


def calc_seven_day_reads(account):
    """计算近7天文章阅读数：从works累加clicksCount；works为空则返回0（interactiveCountSeven是互动量不是阅读量，不可混用）"""
    works = account.get("works") or []
    if works:
        return sum(w.get("clicksCount") or 0 for w in works)
    # API不返回近7天阅读数字段，works为空时无法计算，返回0
    return 0


def _extract_content_themes(works):
    """从文章标题和摘要中提取内容主题聚焦方向"""
    if not works:
        return []

    theme_keywords = {
        "历史人物深度解析": ["人物", "历史", "皇帝", "将军", "朝代", "古人", "王朝"],
        "历史事件复盘": ["事件", "战争", "变革", "运动", "革命", "转折", "战役"],
        "情感故事": ["情感", "婚姻", "爱情", "亲情", "家庭", "夫妻", "恋爱"],
        "职场成长": ["职场", "升职", "领导", "工作", "同事", "老板", "跳槽"],
        "干货技能": ["教程", "技巧", "方法", "攻略", "步骤", "Excel", "PPT", "干货"],
        "资源盘点": ["资源", "工具", "盘点", "合集", "推荐", "神器", "大全"],
        "社会热点解读": ["热点", "政策", "官宣", "发布", "突发", "重磅", "最新"],
        "理财投资": ["理财", "投资", "基金", "股票", "房产", "资产", "财务"],
        "健康养生": ["健康", "养生", "饮食", "睡眠", "运动", "中医", "长寿"],
        "心理成长洞察": ["心理", "成长", "自律", "认知", "思维", "情绪", "格局"],
        "生活好物推荐": ["好物", "推荐", "同款", "购买", "测评", "体验", "种草"],
        "深度观点评论": ["深度", "观点", "评论", "思考", "反思", "洞察", "剖析"],
        "资讯整合速览": ["汇总", "一览", "速览", "榜单", "排行", "周报"],
        "人物故事": ["故事", "人生", "传记", "经历", "逆袭", "传奇"],
        "教育考试升学": ["考试", "高考", "中考", "招生", "录取", "成绩", "志愿", "培训", "升学"],
        "校园生活日常": ["校园", "学生", "老师", "班级", "开学", "毕业", "期末"],
        "本地生活资讯": ["本地", "城市", "社区", "区域", "区县", "乡镇", "街道", "身边"],
        "政务公告通知": ["通知", "公告", "政策", "官方", "发布", "通告", "政务"],
        "亲子育儿教育": ["亲子", "育儿", "宝宝", "孩子", "母婴", "早教", "家长"],
        "小说阅读推荐": ["小说", "阅读", "连载", "书评", "读书", "推荐书", "书单"],
        "职场招聘信息": ["招聘", "求职", "岗位", "简历", "面试", "内推", "校招"],
        "美食探店分享": ["美食", "菜谱", "做法", "食谱", "烹饪", "好吃", "探店"],
        "旅行出游攻略": ["旅行", "旅游", "攻略", "景点", "出行", "打卡", "自驾"],
        "娱乐影视综艺": ["明星", "综艺", "电影", "电视剧", "娱乐", "八卦", "追剧"],
        "科技数码产品": ["科技", "数码", "手机", "电脑", "AI", "互联网", "软件"],
        "房产家居装修": ["房产", "房价", "楼盘", "装修", "家居", "买房", "租房"],
        "汽车出行交通": ["汽车", "新能源", "买车", "驾照", "车型", "交通"],
        "金融理财保险": ["银行", "保险", "贷款", "信用卡", "利率", "存款"],
    }

    all_text = " ".join(
        [w.get("title", "") for w in works if w.get("title")] +
        [w.get("summary", "") for w in works if w.get("summary")]
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
    if has_cover > len(works) * 0.7:
        style_parts.append("图文深度")
    elif has_cover == 0:
        style_parts.append("纯文字")

    summaries = [w.get("summary", "") for w in works if w.get("summary")]
    if summaries:
        avg_len = sum(len(s) for s in summaries) / len(summaries)
        if avg_len > 200:
            style_parts.append("长文深度解析")
        elif avg_len < 50:
            style_parts.append("短平快资讯")
        else:
            style_parts.append("中等深度内容")

    return "/".join(style_parts) if style_parts else ""


def _analyze_publish_schedule(works):
    """从文章发布时间推断发文时段规律"""
    if not works:
        return ""

    hours = []
    for w in works:
        pt = w.get("publishTime") or ""
        # 匹配 HH:MM 或 HH
        m = re.search(r'(\d{1,2}):(\d{2})', pt)
        if m:
            hours.append(int(m.group(1)))

    if not hours:
        return ""

    # 统计最频繁的发文时段
    from collections import Counter
    hour_counter = Counter(hours)
    most_common_hour, count = hour_counter.most_common(1)[0]
    total = len(hours)

    # 时段标签
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
        return f"{period}{most_common_hour}点固定发文"
    elif count >= 2:
        return f"{period}时段为主"
    return ""


def _extract_top_article(works, avg_read):
    """提取最高阅读文章的标题（爆文引用），返回 (标题, 阅读数) 或 None"""
    if not works or avg_read <= 0:
        return None

    # 找阅读数最高的文章
    top_work = max(works, key=lambda w: w.get("clicksCount") or 0)
    top_clicks = top_work.get("clicksCount") or 0

    # 只有达到均阅2倍才算爆文，才有引用价值
    if top_clicks >= avg_read * 2 and top_clicks > 0:
        title = top_work.get("title") or ""
        # 截断过长的标题
        if len(title) > 20:
            title = title[:18] + "…"
        return (title, top_clicks)
    return None


def _calc_interaction_rate(works, avg_read=None):
    """计算互动率：优先基于 works 中的阅读和互动数据，兼容 avgReadCount 为 null 的场景"""
    if not works:
        return None

    total_clicks = sum(w.get("clicksCount") or 0 for w in works)
    total_interactive = sum(w.get("interactiveCount") or 0 for w in works)

    # 互动数不应超过阅读数，如果互动数异常大则说明数据不准确
    if total_clicks <= 0 or total_interactive <= 0:
        return None

    rate = total_interactive / total_clicks
    # 互动率超过100%通常是数据异常（如互动数含阅读数），不输出
    if rate > 1.0:
        return None
    # 互动率过低也没有参考价值
    if rate < 0.001:
        return None
    return rate


def _calc_share_rate(works):
    """计算分享率：分享数/阅读数，反映内容传播力"""
    if not works:
        return None

    total_clicks = sum(w.get("clicksCount") or 0 for w in works)
    total_shares = sum(w.get("shareCount") or 0 for w in works)

    if total_clicks <= 0 or total_shares <= 0:
        return None

    rate = total_shares / total_clicks
    if rate > 1.0 or rate < 0.001:
        return None
    return rate


def _add_sparse_data_reasons(parts, account, account_type, redfox_index, article_count_seven, works, content_themes):
    """当近7天阅读数或平均阅读数为0时，补充其他维度的推荐理由"""
    # 红狐指数维度：作为账号综合质量的参考
    if redfox_index > 0:
        if redfox_index >= 800:
            parts.append(f"红狐指数{redfox_index:.0f}，账号综合质量在「{account_type}」赛道中表现突出")
        elif redfox_index >= 500:
            parts.append(f"红狐指数{redfox_index:.0f}，账号处于成长阶段，发展潜力可关注")
        else:
            parts.append(f"红狐指数{redfox_index:.0f}，同赛道起步阶段定位匹配")

    # 近7天互动数维度：仅在主函数未输出过时才补充
    interactive_count_seven = account.get("interactiveCountSeven") or 0
    if interactive_count_seven > 0 and not any("互动" in p for p in parts):
        parts.append(f"近7天互动{format_number(interactive_count_seven)}，用户活跃度可参考")

    # 内容方向补充：从文章标题推断（即使没有阅读数据，有文章也可以提取方向）
    if works and not content_themes:
        topic = _infer_topic_from_titles(works)
        if topic:
            parts.append(f"内容方向：{topic}")

    # 分享传播力：从 works 中提取分享数据（仅在主函数未输出过时才补充）
    if works and not any("分享" in p for p in parts):
        share_rate = _calc_share_rate(works)
        if share_rate and share_rate >= 0.01:
            parts.append(f"分享率{share_rate*100:.1f}%，内容传播力强")

    # 发文时段规律：从 publishTime 推断（仅在主函数未输出过时才补充）
    if works and not any("发文" in p or "固定" in p or "时段" in p for p in parts):
        schedule = _analyze_publish_schedule(works)
        if schedule:
            parts.append(schedule)

    # 更新节奏补充：如果前面没有提到更新节奏
    if article_count_seven > 0 and not any("更新" in p or "日更" in p or "周更" in p for p in parts):
        parts.append(f"近7天发文{article_count_seven}篇，保持更新节奏")

    # 通用推荐方向：当以上维度都不够时
    if len(parts) < 2 and account_type:
        parts.append(f"同赛道定位匹配，可参考其内容策略和运营节奏")


def _infer_topic_from_titles(works):
    """从文章标题中推断内容方向（用于数据稀疏时的补充推荐理由）"""
    if not works:
        return ""

    titles = [w.get("title", "") for w in works if w.get("title")]
    if not titles:
        return ""

    extended_themes = {
        "教育考试升学": ["考试", "高考", "中考", "招生", "录取", "成绩", "志愿", "培训", "升学"],
        "校园生活日常": ["校园", "学生", "老师", "班级", "开学", "毕业", "期末"],
        "本地生活资讯": ["本地", "城市", "社区", "区域", "区县", "乡镇", "街道", "身边"],
        "政务公告通知": ["通知", "公告", "政策", "官方", "发布", "通告", "政务"],
        "亲子育儿教育": ["亲子", "育儿", "宝宝", "孩子", "母婴", "早教", "家长"],
        "小说阅读推荐": ["小说", "阅读", "连载", "书评", "读书", "推荐书", "书单"],
        "职场招聘信息": ["招聘", "求职", "岗位", "简历", "面试", "内推", "校招"],
        "美食探店分享": ["美食", "菜谱", "做法", "食谱", "烹饪", "好吃", "探店"],
        "旅行出游攻略": ["旅行", "旅游", "攻略", "景点", "出行", "打卡", "自驾"],
        "娱乐影视综艺": ["明星", "综艺", "电影", "电视剧", "娱乐", "八卦", "追剧"],
        "科技数码产品": ["科技", "数码", "手机", "电脑", "AI", "互联网", "软件"],
        "房产家居装修": ["房产", "房价", "楼盘", "装修", "家居", "买房", "租房"],
        "汽车出行交通": ["汽车", "新能源", "买车", "驾照", "车型", "交通"],
        "金融理财保险": ["银行", "保险", "贷款", "信用卡", "利率", "存款"],
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


def generate_recommendation_reason(account):
    """生成推荐理由：基于账号数据、内容数据、更新节奏、整体内容策略定位总结值得学习点"""
    parts = []

    works = account.get("works") or []
    account_type = account.get("accountType") or ""
    avg_read = account.get("avgReadCount") or 0
    seven_day_reads = calc_seven_day_reads(account)
    article_count_seven = account.get("articleCountSeven") or 0
    redfox_index = account.get("redfoxIndex") or 0
    interactive_count_seven = account.get("interactiveCountSeven") or 0

    # 从 works 计算实际阅读数据（当 avgReadCount 为 null 时仍可从 works 获取）
    works_total_reads = sum(w.get("clicksCount") or 0 for w in works) if works else 0
    works_avg_read = works_total_reads / len(works) if works and len(works) > 0 else 0
    # 使用 max(avgReadCount, works均值) 作为爆文判断基准
    effective_avg = max(avg_read, works_avg_read) if works_avg_read > 0 else avg_read

    # 1. 爆文洞察 + 内容主题聚焦
    burst_works = []
    if works and effective_avg > 0:
        for w in works:
            clicks = w.get("clicksCount") or 0
            if clicks >= effective_avg * 2:
                burst_works.append(w)

    content_themes = _extract_content_themes(works) if works else []

    if burst_works and content_themes:
        burst_count = len(burst_works)
        theme_str = "/".join(content_themes[:2])
        parts.append(f"同赛道近7天{burst_count}篇爆文，全聚焦于{theme_str}")
    elif burst_works:
        burst_count = len(burst_works)
        parts.append(f"同赛道近7天{burst_count}篇爆文")
    elif content_themes:
        theme_str = "/".join(content_themes[:2])
        parts.append(f"同赛道，内容聚焦于{theme_str}")
    elif account_type:
        parts.append(f"同属「{account_type}」赛道")

    # 2. 爆文标题引用：提取最高阅读文章标题，增强可借鉴性
    if works and effective_avg > 0:
        top_article = _extract_top_article(works, effective_avg)
        if top_article:
            title, clicks = top_article
            parts.append(f"爆文「{title}」达均阅{clicks/effective_avg:.1f}倍")

    # 3. 更新节奏 + 内容策略 + 发文时段
    strategy_parts = []
    if article_count_seven >= 7:
        strategy_parts.append("日更高产")
    elif article_count_seven >= 4:
        strategy_parts.append("稳定周更3-4篇")
    elif article_count_seven >= 1:
        strategy_parts.append("持续更新")

    content_style = _analyze_content_strategy(works)
    if content_style:
        strategy_parts.append(content_style)

    # 发文时段规律
    if works:
        schedule = _analyze_publish_schedule(works)
        if schedule:
            strategy_parts.append(schedule)

    if strategy_parts:
        parts.append("，".join(strategy_parts))

    # 4. 数据亮点：互动率 + 分享率（修复互动率异常问题）
    if works:
        interaction_rate = _calc_interaction_rate(works, effective_avg)
        if interaction_rate and interaction_rate >= 0.005:
            parts.append(f"互动率{interaction_rate*100:.1f}%")

        share_rate = _calc_share_rate(works)
        if share_rate and share_rate >= 0.01:
            parts.append(f"分享率{share_rate*100:.1f}%，内容传播力强")

    # 5. 近7天互动数据（当 avgRead 为 null 但互动数有值时）
    if interactive_count_seven > 0 and avg_read == 0:
        parts.append(f"近7天互动{format_number(interactive_count_seven)}，用户活跃度可参考")

    # 6. 当近7天阅读数或平均阅读数为0时，补充其他维度的推荐理由
    if seven_day_reads == 0 or avg_read == 0:
        _add_sparse_data_reasons(parts, account, account_type, redfox_index, article_count_seven, works, content_themes)

    # 7. 结论
    if parts:
        result = "<br>".join(parts)
    else:
        # fallback
        fallback_parts = []
        if account_type:
            fallback_parts.append(f"同属「{account_type}」赛道")
        if avg_read > 0:
            fallback_parts.append(f"均阅{format_number(avg_read)}")
        elif works_avg_read > 0:
            fallback_parts.append(f"均阅{format_number(works_avg_read)}")
        if seven_day_reads > 0:
            fallback_parts.append(f"7天阅读{format_number(seven_day_reads)}")
        elif interactive_count_seven > 0:
            fallback_parts.append(f"7天互动{format_number(interactive_count_seven)}")
        result = "，".join(fallback_parts) + "，可参考运营策略"

    result = bold_bracket_content(result)

    if len(result) < 20:
        result += "，可参考运营策略"

    return result



def format_query_account_info(query_account):
    """格式化查询账号基本信息"""
    if not query_account:
        return "未获取到查询账号信息"

    lines = []
    lines.append("**查询账号基本信息**")
    lines.append("")

    account_name = query_account.get("accountName") or "未知"
    account_id = query_account.get("accountId") or "未知"
    account_type = query_account.get("accountType") or "未知"
    account_url = get_account_url(account_id)
    redfox_index = query_account.get("redfoxIndex") or 0
    avg_read = query_account.get("avgReadCount") or 0
    seven_day_reads = calc_seven_day_reads(query_account)
    article_count_seven = query_account.get("articleCountSeven")
    if article_count_seven is None:
        # currentAccount可能不含articleCountSeven，从works数量推断
        works_count = len(query_account.get("works") or [])
        article_count_seven = works_count if works_count > 0 else "暂无"

    lines.append(f"- 账号名称：[{account_name}]({account_url})")
    lines.append(f"- 账号ID：{account_id}")
    lines.append(f"- 账号分类：{account_type}")
    lines.append(f"- 红狐指数：{redfox_index:.0f}" if redfox_index else "- 红狐指数：无")
    lines.append(f"- 平均阅读数：{format_number(avg_read)}")
    lines.append(f"- 近7天阅读数：{format_number(seven_day_reads)}")
    lines.append(f"- 近7天发文章数：{article_count_seven}")

    # 近5篇文章
    works = query_account.get("works") or []
    if works:
        lines.append("")
        lines.append("**近5篇文章**")
        lines.append("")
        lines.append("| 文章标题 | 阅读数 | 点赞数 | 评论数 | 在看数 | 总互动数 | 发布时间 |")
        lines.append("| --- | --- | --- | --- | --- | --- | --- |")
        for w in works[:5]:
            title = w.get("title") or "无标题"
            work_url = w.get("workUrl") or ""
            if work_url:
                title = f"[{title}]({work_url})"
            clicks = format_number(w.get("clicksCount"))
            likes = format_number(w.get("likeCount"))
            comments = format_number(w.get("commentCount"))
            watches = format_number(w.get("watchCount"))
            interactive = format_number(w.get("interactiveCount"))
            publish_time = w.get("publishTime") or "未知"
            lines.append(f"| {title} | {clicks} | {likes} | {comments} | {watches} | {interactive} | {publish_time} |")

    return "\n".join(lines)


def format_table(accounts, title_line, query_account=None):
    """格式化对标账号Markdown表格"""
    lines = []
    lines.append(title_line)
    lines.append("")
    lines.append("| 账号名称 | 红狐指数 | 平均阅读数 | 近7天阅读数 | 近7日文章发布数 | 推荐理由 |")
    lines.append("| --- | --- | --- | --- | --- | --- |")

    qa_id = (query_account or {}).get("accountId")

    for account in accounts:
        account_name = account.get("accountName") or "未知"
        redfox_index = account.get("redfoxIndex") or 0
        avg_read = format_number(account.get("avgReadCount"))
        seven_day_reads = format_number(calc_seven_day_reads(account))
        redfox_display = f"{redfox_index:.0f}" if redfox_index else "无"
        account_url = get_account_url(account.get("accountId") or "")
        account_link = f"[{account_name}]({account_url})"

        article_count_seven = account.get("articleCountSeven")
        if article_count_seven is None or article_count_seven == 0:
            # currentAccount可能不含articleCountSeven，从works数量推断
            works_count = len(account.get("works") or [])
            article_count_seven = works_count if works_count > 0 else 0
        article_count_display = str(article_count_seven) if article_count_seven else "0"

        # 查询账号标注
        if qa_id and account.get("accountId") == qa_id:
            lines.append(f"| **{account_link}（查询账号）** | **{redfox_display}** | **{avg_read}** | **{seven_day_reads}** | **{article_count_display}** | —（当前账号） |")
        else:
            recommendation = generate_recommendation_reason(account)
            lines.append(f"| {account_link} | {redfox_display} | {avg_read} | {seven_day_reads} | {article_count_display} | {recommendation} |")

    return "\n".join(lines)


def get_earliest_gmt_create(benchmark_accounts, top_accounts):
    """获取最早的数据更新时间"""
    all_accounts = (benchmark_accounts or []) + (top_accounts or [])
    gmt_creates = [acc.get("gmtCreate") for acc in all_accounts if acc.get("gmtCreate")]
    return min(gmt_creates) if gmt_creates else "入库时刻"


def generate_analysis_summary(benchmark_accounts, top_accounts):
    """生成分析总结"""
    lines = []
    lines.append("**分析总结**：")

    if benchmark_accounts:
        avg_read = sum(a.get("avgReadCount") or 0 for a in benchmark_accounts) / len(benchmark_accounts)
        avg_seven_reads = sum(calc_seven_day_reads(a) for a in benchmark_accounts) / len(benchmark_accounts)
        avg_redfox = sum(a.get("redfoxIndex") or 0 for a in benchmark_accounts) / len(benchmark_accounts)
        lines.append(f"- 同阶对标平均阅读数：{format_number(avg_read)}，平均近7天阅读数：{format_number(avg_seven_reads)}，平均红狐指数：{avg_redfox:.0f}")

    if top_accounts:
        avg_read = sum(a.get("avgReadCount") or 0 for a in top_accounts) / len(top_accounts)
        avg_seven_reads = sum(calc_seven_day_reads(a) for a in top_accounts) / len(top_accounts)
        avg_redfox = sum(a.get("redfoxIndex") or 0 for a in top_accounts) / len(top_accounts)
        lines.append(f"- 高阶标杆平均阅读数：{format_number(avg_read)}，平均近7天阅读数：{format_number(avg_seven_reads)}，平均红狐指数：{avg_redfox:.0f}")

    if benchmark_accounts or top_accounts:
        lines.append("- 对标匹配基于3层加权体系：核心基础匹配(40%)+运营变现匹配(35%)+数据特征匹配(25%)")
        lines.append("- 建议优先参考：对标账号中的高频更新账号，学习其内容节奏和选题方向")

    return "\n".join(lines)


def format_output(query_account, benchmark_accounts, top_accounts):
    """格式化完整文本输出"""
    output_lines = []
    earliest_gmt = get_earliest_gmt_create(benchmark_accounts, top_accounts)

    # 查询账号基本信息
    if query_account:
        output_lines.append(format_query_account_info(query_account))
        output_lines.append("")

    # 对标账号列表：查询账号排第一 + 对标账号
    benchmark_with_query = []
    if query_account:
        benchmark_with_query.append(query_account)
    if benchmark_accounts:
        benchmark_with_query.extend(benchmark_accounts)

    # 匹配结果
    bench_count = len(benchmark_with_query)
    top_count = len(top_accounts) if top_accounts else 0

    tips_parts = []
    if bench_count > 0:
        tips_parts.append(f"【可直接抄的同阶对标（{bench_count}个）】")
    if top_count > 0:
        tips_parts.append(f"【可追赶的高阶标杆（{top_count}个）】")

    if tips_parts:
        output_lines.append(f"为你匹配到{'和'.join(tips_parts)}的{len(tips_parts)}组推荐，可按需参考：")
        output_lines.append(f"| 数据说明：数据获取时间为{earliest_gmt}，和实时数据存在差别。")

        if benchmark_with_query:
            table_title = f"👉【可直接抄的同阶对标（{bench_count}个）】（和查询账号阅读数最接近，可直接复制玩法）"
            output_lines.append(format_table(benchmark_with_query, table_title, query_account))

        if top_accounts:
            table_title = f"👉【可追赶的高阶标杆（{len(top_accounts)}个）】（阅读数是查询账号的3-5倍，模式成熟可参考）"
            output_lines.append(format_table(top_accounts, table_title))

        if benchmark_accounts or top_accounts:
            output_lines.append("")
            output_lines.append(generate_analysis_summary(benchmark_accounts, top_accounts))

        output_lines.append("")
        output_lines.append("**订阅服务**")
        qa_name = (query_account or {}).get("accountName") or "现查询条件"
        output_lines.append(f'       1. 是否订阅"{qa_name}"的相似账号推送，每日下午19点更新最新数据。你可自行选择推送频率和时间~')
        output_lines.append("       2. 暂不需要")
    else:
        # 未查询到账号数据
        output_lines.append("当前未查询到该账号相关数据，请确认账号名称或ID输入是否正确后重试。")

    # 企业采购引导（所有输出结果末尾统一追加）
    output_lines.append("")
    output_lines.append("> 💼 另外红狐配套全量数据库可提供完整详实数据，如需了解采购方案，可前往红狐hub[企业服务](https://redfox.hk/dashboard/enterprise?source=github)对接咨询")

    return "\n".join(output_lines)


def main():
    parser = argparse.ArgumentParser(description="公众号账号推荐脚本")
    parser.add_argument("--account_id", help="公众号ID")
    parser.add_argument("--account_name", help="公众号名称")
    parser.add_argument("--account_type", help="账号分类")

    args = parser.parse_args()

    if not args.account_id and not args.account_name and not args.account_type:
        print("错误：请提供公众号ID(--account_id)或公众号名称(--account_name)或账号分类(--account_type)")
        return

    try:
        query_account, benchmark_accounts, top_accounts = query_similar_accounts(
            accountId=args.account_id,
            accountName=args.account_name,
            accountType=args.account_type
        )

        # currentAccount 直接从 API 获取，无需再从账号列表中匹配
        # 当 currentAccount 为空时（如按分类查询且未命中具体账号），尝试从返回列表中匹配
        if not query_account and (args.account_name or args.account_id):
            search_name = args.account_name or ""
            search_id = args.account_id or ""
            all_accounts = (benchmark_accounts or []) + (top_accounts or [])
            for acc in all_accounts:
                acc_name = acc.get("accountName") or ""
                acc_id = acc.get("accountId") or ""
                if (search_name and search_name in acc_name) or (search_id and search_id == acc_id):
                    query_account = acc
                    break

        # 格式化输出
        result = format_output(query_account, benchmark_accounts, top_accounts)
        print(result)

    except Exception as e:
        print(f"查询失败: {str(e)}")


if __name__ == "__main__":
    main()
