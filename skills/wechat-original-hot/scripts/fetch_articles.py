#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
公众号原创爆款文章获取脚本

功能：
1. 调用API获取公众号原创爆款文章数据
2. 按阅读量排序
3. 输出TOP榜单列表（Markdown格式，含链接）
4. 支持分类查询和时间区间查询

使用方法：
python fetch_articles.py --type "科技数码" --source "公众号文章原创之王-GitHub" --start_date "2026-05-03" --end_date "2026-05-04"
python fetch_articles.py --type "总排名" --source "公众号文章原创之王-GitHub"  # 自动判断时间
python fetch_articles.py  # 默认：总排名，自动判断时间
"""

import argparse
import json
import os
import sys
import ssl
import urllib.request
import urllib.error
from datetime import datetime, timedelta


# ==================== 分类映射 ====================

CATEGORY_MAPPING = {
    "人文资讯": ["人文", "文化", "历史", "哲学", "文学", "艺术", "人文社科"],
    "知识百科": ["知识", "百科", "科普", "冷知识", "常识", "百科全书"],
    "健康养生": ["健康", "养生", "保健", "医疗", "中医", "健身", "营养", "健康生活"],
    "时尚潮流": ["时尚", "潮流", "穿搭", "美妆", "时尚穿搭", "流行趋势"],
    "美食餐饮": ["美食", "餐饮", "美食推荐", "菜谱", "烹饪", "吃货", "饮食"],
    "乐活生活": ["乐活", "生活", "生活方式", "生活品质", "品质生活", "生活技巧"],
    "旅游出行": ["旅游", "出行", "旅行", "攻略", "景点", "自驾游", "旅游攻略"],
    "搞笑幽默": ["搞笑", "幽默", "段子", "笑话", "娱乐", "开心", "趣事"],
    "情感心理": ["情感", "心理", "情感故事", "恋爱", "婚姻", "亲情", "友情", "心理辅导"],
    "体育娱乐": ["体育", "娱乐", "运动", "明星", "电影", "音乐", "综艺", "体育赛事"],
    "美容美体": ["美容", "美体", "护肤", "减肥", "瘦身", "美容护肤", "塑形"],
    "文摘精选": ["文摘", "精选", "好文", "美文", "精选文章", "优秀文章"],
    "财富理财": ["财富", "理财", "投资", "金融", "基金", "股票", "保险", "财商"],
    "科技数码": ["科技", "数码", "互联网", "手机", "电脑", "科技新闻", "数码产品"],
    "创投商业": ["创投", "商业", "创业", "投资", "商业模式", "创业故事", "商业财经"],
    "汽车交通": ["汽车", "交通", "购车", "用车", "汽车评测", "交通出行"],
    "房产楼市": ["房产", "楼市", "买房", "卖房", "房产投资", "房地产", "房价"],
    "职场发展": ["职场", "职业", "工作", "求职", "职场技巧", "职业发展", "职场故事"],
    "教育考试": ["教育", "考试", "学习", "培训", "高考", "考研", "教育培训", "学习方法"],
    "学术研究": ["学术", "研究", "论文", "科研", "学术前沿", "研究成果"],
    "企业品牌": ["企业", "品牌", "公司", "管理", "企业文化", "品牌故事", "企业案例"],
    "总排名": ["总排名", "全部", "所有分类", "综合排名", "总榜"]
}


def match_category(user_input: str) -> str:
    """
    根据用户输入匹配分类

    Args:
        user_input: 用户输入的文本

    Returns:
        匹配的标准分类名称，默认返回"总排名"
    """
    if not user_input:
        return "总排名"

    user_input_lower = user_input.lower().strip()

    # 1. 精确匹配
    for category in CATEGORY_MAPPING.keys():
        if user_input_lower == category.lower():
            return category

    # 2. 包含匹配
    for category in CATEGORY_MAPPING.keys():
        if category.lower() in user_input_lower or user_input_lower in category.lower():
            return category

    # 3. 关键词匹配
    for category, keywords in CATEGORY_MAPPING.items():
        for keyword in keywords:
            if keyword.lower() in user_input_lower:
                return category

    # 默认返回总排名
    return "总排名"


# ==================== API Key 获取 ====================

def get_api_key():
    """从当前环境变量获取 REDFOX_API_KEY"""
    api_key = os.getenv("REDFOX_API_KEY")
    if not api_key:
        print("❌ 未找到 REDFOX_API_KEY，请配置环境变量：export REDFOX_API_KEY=<你的apikey>", file=sys.stderr)
        sys.exit(1)
    return api_key


# ==================== 接口调用 ====================

def fetch_articles_api(url: str, params: dict, api_key: str, timeout: int = 30) -> dict:
    """
    使用原生 urllib.request 发 HTTPS POST 请求（verify=False）

    Args:
        url: API 地址
        params: 请求参数（JSON body）
        api_key: X-API-KEY 认证密钥
        timeout: 超时时间（秒）

    Returns:
        API 响应数据（dict）
    """
    headers = {
        "Content-Type": "application/json",
        "X-API-KEY": api_key
    }

    body = json.dumps(params, ensure_ascii=False)
    data = body.encode("utf-8")

    req = urllib.request.Request(url, data=data, headers=headers, method="POST")

    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE

    try:
        with urllib.request.urlopen(req, context=ssl_ctx, timeout=timeout) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise Exception(f"HTTP请求失败: {e.code}, {e.read().decode('utf-8', errors='replace')}")
    except urllib.error.URLError as e:
        raise Exception(f"请求失败: {e.reason}")

    return result


def fetch_articles_by_category(type: str, source: str, start_date: str = "", end_date: str = "") -> dict:
    """
    调用新接口获取文章数据

    Args:
        type: 分类名称
        source: 数据源
        start_date: 开始日期（YYYY-MM-DD）
        end_date: 结束日期（YYYY-MM-DD）

    Returns:
        API 响应数据
    """
    url = "https://redfox.hk/story/api/cozeSkill/getWxDataByCategoryAndTime"

    # 获取 API Key（环境变量 > shell配置文件 > 提示用户配置）
    api_key = get_api_key()

    params = {
        "type": type,
        "source": source
    }

    if start_date:
        params["startDate"] = start_date
    if end_date:
        params["endDate"] = end_date

    print(f"正在获取原创爆款文章推荐...")
    print(f"分类: {type}")
    print(f"数据源: {source}")
    if start_date:
        print(f"开始日期: {start_date}")
    if end_date:
        print(f"结束日期: {end_date}")
    print("-" * 60)

    data = fetch_articles_api(url, params, api_key)

    if data.get("code") != 2000:
        raise Exception(f"API错误: {data.get('msg', '未知错误')}")

    return data


# ==================== 数据处理 ====================

def parse_count_to_int(count_str: str) -> int:
    """解析阅读数字符串为整数"""
    if not count_str:
        return 0

    count_str = str(count_str).strip().replace(",", "")

    if "10w+" in count_str.lower() or "10万+" in count_str:
        return 100000
    elif "w+" in count_str.lower() or "万+" in count_str:
        # 处理 "1w+", "5w+" 等格式
        try:
            num_str = count_str.lower().replace("w+", "").replace("万+", "")
            num = float(num_str)
            return int(num * 10000)
        except:
            return 0
    elif "w" in count_str.lower() or "万" in count_str:
        try:
            num = float(count_str.lower().replace("w", "").replace("万", ""))
            return int(num * 10000)
        except:
            return 0
    else:
        try:
            return int(float(count_str))
        except:
            return 0


def get_reading_score(article: dict) -> int:
    """获取阅读量作为排序依据"""
    clicks_count = parse_count_to_int(article.get("clicksCount", "0"))
    return int(clicks_count or 0)


def process_articles(data: dict) -> list:
    """
    处理文章数据，按阅读量排序

    Args:
        data: API 响应数据

    Returns:
        排序后的文章列表
    """
    articles = data.get("data", {}).get("originalRank", [])

    if not articles:
        return []

    # 按阅读量排序
    articles.sort(key=get_reading_score, reverse=True)

    return articles


# ==================== 时间计算 ====================

def get_query_date_range() -> tuple:
    """
    根据当前时间判断查询日期范围

    数据每日 19:30 更新，更新前一天（T-1）的数据。
    - 当前时间 < 19:30：查询 T-2 数据
    - 当前时间 >= 19:30：查询 T-1 数据

    Returns:
        (start_date, end_date, query_date_display, update_date_display)
    """
    now = datetime.now()
    current_hour = now.hour
    current_minute = now.minute

    if current_hour < 19 or (current_hour == 19 and current_minute < 30):
        # 当前时间 < 19:30，查询 T-2 数据
        query_date = now - timedelta(days=2)  # 前天
        update_date = now - timedelta(days=1)  # 昨天
    else:
        # 当前时间 >= 19:30，查询 T-1 数据
        query_date = now - timedelta(days=1)  # 昨天
        update_date = now  # 今天

    start_date = query_date.strftime("%Y-%m-%d")
    end_date = (query_date + timedelta(days=1)).strftime("%Y-%m-%d")
    query_date_display = query_date.strftime("%Y年%m月%d日")
    update_date_display = update_date.strftime("%Y年%m月%d日")

    return start_date, end_date, query_date_display, update_date_display


def get_recent_days_range(days: int = 7) -> tuple:
    """
    获取最近N天的日期范围

    Args:
        days: 天数（默认7天）

    Returns:
        (start_date, end_date, date_range_display)
    """
    now = datetime.now()
    end_date = now
    start_date = now - timedelta(days=days-1)  # 包含今天，所以是days-1

    start_date_str = start_date.strftime("%Y-%m-%d")
    end_date_str = end_date.strftime("%Y-%m-%d")
    date_range_display = f"{start_date.strftime('%Y年%m月%d日')}至{end_date.strftime('%Y年%m月%d日')}"

    return start_date_str, end_date_str, date_range_display


# ==================== 输出格式化 ====================

def format_count(count_str: str) -> str:
    """格式化阅读数显示"""
    if not count_str:
        return "0"

    count_str = str(count_str).strip()

    # 保留原始的 w+ 或 万+ 格式
    if "10w+" in count_str.lower() or "10万+" in count_str or "10W+" in count_str:
        return "10w+"
    elif "w+" in count_str.lower() or "万+" in count_str:
        # 保留原始格式，如 "1w+", "5w+"
        return count_str.lower().replace("万+", "w+")

    count = parse_count_to_int(count_str)
    if count >= 10000:
        return f"{count/10000:.1f}w"
    else:
        return str(count)


def output_table(articles: list, limit: int = 20, mode: str = "preview", category: str = "总排名"):
    """
    输出文章表格

    Args:
        articles: 文章列表
        limit: 显示条数
        mode: 输出模式（preview/full）
        category: 分类名称
    """
    total = len(articles)
    display_count = min(limit, total) if mode == "preview" else total
    display_articles = articles[:display_count]

    # 输出表格
    print("\n| 序号 | 作者 | 标题 | 阅读数 |")
    print("|------|------|------|--------|")

    for i, article in enumerate(display_articles, 1):
        author = article.get("userName", "-")
        title = article.get("title", "-")
        clicks = format_count(article.get("clicksCount", "0"))

        account_id = article.get("accountId", "")
        ori_url = article.get("oriUrl", "")

        # 构建链接
        author_link = f"https://open.weixin.qq.com/qr/code?username={account_id}" if account_id else ""
        title_link = ori_url if ori_url else ""

        # 输出行
        if author_link:
            author_display = f"[{author}]({author_link})"
        else:
            author_display = author

        if title_link:
            title_display = f"[{title}]({title_link})"
        else:
            title_display = title

        print(f"| {i} | {author_display} | {title_display} | {clicks} |")

    print("\n导出功能：输出生成HTML榜单页面，表格内容支持导出 PDF 格式，自动生成并打开")

    # 文章少于10篇时的提示
    if total < 10:
        category_display = category if category != "总排名" else "综合"
        print(f"\n💡 {category_display}赛道10w+文章较少，您可以拓展过去30天或者看看综合10w+文章~")

    if mode == "preview" and total > limit:
        print(f"\n共获取到{total}条爆款原创热门文章,当前展示前{limit}条。")
        print(f"\n📬 订阅服务")
        print("是否需要订阅具体赛道的账号表现？我们支持：")
        print("人文资讯、知识百科、健康养生、时尚潮流、美食餐饮、乐活生活、旅游出行、搞笑幽默、情感心理、体育娱乐、美容美体、文摘精选、财富理财、科技数码、创投商业、汽车交通、房产楼市、职场发展、教育考试、学术研究、企业品牌、总排名")
        print("订阅推送 — 每天19点30分推送最新公众号原创文章")
        print("暂不需要 — 仅本次查询")
    else:
        print(f"\n共获取到{total}条爆款原创热门文章。")

    print(f"\n另外红狐配套全量数据库可提供完整详实数据，如需了解采购方案，可发送邮件至 redfoxdata@proton.me 对接咨洵")


# ==================== 主函数 ====================

def main():
    parser = argparse.ArgumentParser(description="获取公众号原创爆款文章")
    parser.add_argument("--type", default="", help="分类名称（如'科技数码'，默认'总排名'）")
    parser.add_argument("--source", default="公众号文章原创之王-GitHub", help="数据源")
    parser.add_argument("--start_date", default="", help="开始日期（YYYY-MM-DD）")
    parser.add_argument("--end_date", default="", help="结束日期（YYYY-MM-DD）")
    parser.add_argument("--recent", type=int, default=0, help="最近N天（如7表示最近7天）")
    parser.add_argument("--limit", type=int, default=20, help="显示条数（默认20）")
    parser.add_argument("--mode", default="preview", choices=["preview", "full"], help="输出模式")
    parser.add_argument("--temp_file", default="temp_articles.json", help="临时JSON文件路径")
    parser.add_argument("--query_intent", default="", help="查询意图（today/yesterday，用于判断是否需要提示）")

    args = parser.parse_args()

    # 匹配分类
    category = match_category(args.type) if args.type else "总排名"

    # 确定日期范围
    if args.recent > 0:
        # 用户查询最近N天
        start_date, end_date, date_range_display = get_recent_days_range(args.recent)
        query_date_display = date_range_display
        is_specific_date = False
        is_recent_query = True
    elif args.start_date:
        # 用户指定了日期
        start_date = args.start_date
        end_date = args.end_date if args.end_date else (datetime.strptime(start_date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
        query_date_display = datetime.strptime(start_date, "%Y-%m-%d").strftime("%Y年%m月%d日")
        is_specific_date = True
        is_recent_query = False
    else:
        # 自动判断日期
        start_date, end_date, query_date_display, update_date_display = get_query_date_range()
        is_specific_date = False
        is_recent_query = False

    # 判断用户查询意图是否为"今日"或"昨日"
    query_intent = args.query_intent.lower() if args.query_intent else ""
    need_prompt = False
    if query_intent in ["today", "今日", "今天"]:
        # 用户想查询今日数据
        need_prompt = True
        intent_date_str = "今天"
    elif query_intent in ["yesterday", "昨日", "昨天"]:
        # 用户想查询昨日数据
        need_prompt = True
        intent_date_str = "昨天"

    # 调用接口
    try:
        data = fetch_articles_by_category(category, args.source, start_date, end_date)
    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        sys.exit(1)

    # 处理数据
    articles = process_articles(data)

    if not articles:
        print("❌ 未获取到文章数据")
        sys.exit(0)

    # 保存临时文件
    with open(args.temp_file, 'w', encoding='utf-8') as f:
        json.dump({"articles": articles}, f, ensure_ascii=False, indent=2)
    print(f"✅ 数据已保存到临时文件: {args.temp_file}")

    # 输出数据说明
    print(f"\n💡 数据说明")
    print(f"公众号原创文章推荐将在每日19点30分准时更新昨日文章数据，以下数据为获取时间时的快照，和实时数据有所差别。")

    # 判断数据更新状态（所有情况统一处理）
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    current_hour = datetime.now().hour
    current_minute = datetime.now().minute
    if current_hour < 19 or (current_hour == 19 and current_minute < 30):
        # 19:30前，最新数据是T-2（前天）
        latest_date = today - timedelta(days=2)
        latest_date_str = "前天"
    else:
        # 19:30后，最新数据是T-1（昨天）
        latest_date = today - timedelta(days=1)
        latest_date_str = "昨天"

    # 回溯日期（30天前）
    earliest_date = today - timedelta(days=30)

    # 判断是否需要提示（数据查询日期和用户询问日期不一致）
    need_date_prompt = False
    prompt_message = ""

    if is_recent_query:
        # 最近N天查询，检查查询的结束日期是否晚于最新日期
        # 解析 query_date_display 获取结束日期
        if "至" in query_date_display:
            end_date_str = query_date_display.split("至")[1].replace("年", "-").replace("月", "-").replace("日", "")
            try:
                query_end_date = datetime.strptime(end_date_str.strip(), "%Y-%m-%d")
                if query_end_date > latest_date:
                    need_date_prompt = True
                    prompt_message = f"\n非常抱歉🙏，最新的是{latest_date_str}的数据，我将为您查询最接近您需求的时间范围。"
            except:
                pass

        print(f"\n📊 原创爆文推荐")
        print(f"{query_date_display}的原创爆款文章")
    elif is_specific_date:
        # 指定日期查询
        query_date = datetime.strptime(start_date, "%Y-%m-%d")

        if query_date > latest_date:
            # 用户查询未更新日期的榜单（查询日期晚于最新日期）
            need_date_prompt = True
            prompt_message = f"\n非常抱歉🙏，最新的是{latest_date_str}的数据，我将为您查询最接近您需求的{query_date_display}原创文章。"
        elif query_date < earliest_date:
            # 用户查询时间早于回溯日期
            need_date_prompt = True
            prompt_message = f"\n非常抱歉🙏，目前最多支持回溯「过去30天」，我将为您查询最接近您需求的时间范围~"

        print(f"\n📊 原创爆文推荐")
        print(f"{query_date_display}当天的原创爆款文章")
    else:
        # 默认查询，检查是否需要提示
        if need_prompt:
            # 用户想查询"今日"或"昨日"，但数据还没更新
            need_date_prompt = True
            prompt_message = f"\n非常抱歉🙏，最新的是{latest_date_str}的数据，我将为您查询最接近您需求的{query_date_display}原创文章。"

        print(f"\n📊 原创爆文推荐")
        print(f"{query_date_display}当天的原创爆款文章")

    # 统一输出提示信息
    if need_date_prompt:
        print(prompt_message)

    # 输出表格
    output_table(articles, args.limit, args.mode, category)


if __name__ == "__main__":
    main()
