#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
公众号10w+热门文章榜单获取脚本

功能：
1. 调用API获取10w+阅读热门文章数据（按分类和时间查询）
2. 按互动数排序
3. 输出TOP榜单列表（纯文本格式）
4. 提供四维度内容分析（内容概述、热点利用、传播作用、达成效果）

使用方法：
python fetch_hot_articles.py --type "科技数码" --start_date "2024-01-01" --end_date "2024-01-02"
python fetch_hot_articles.py --type "总排名" --start_date "yesterday" --end_date ""
python fetch_hot_articles.py --type "" --start_date "daybeforeyesterday" --end_date ""
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError


# 标准分类列表
STANDARD_CATEGORIES = [
    "人文资讯", "知识百科", "健康养生", "时尚潮流", "美食餐饮", "乐活生活",
    "旅游出行", "搞笑幽默", "情感心理", "体育娱乐", "美容美体", "文摘精选",
    "民生资讯", "财富理财", "科技数码", "创投商业", "汽车交通", "房产楼市",
    "职场发展", "教育考试", "学术研究", "企业品牌", "总排名"
]


def parse_date(date_str: str) -> str:
    """
    解析日期参数

    Args:
        date_str: 日期字符串，支持：
                 - "yesterday": 昨天
                 - "daybeforeyesterday": 前天
                 - "today": 今天
                 - "": 不限时间
                 - "YYYY-MM-DD": 具体日期

    Returns:
        格式化的日期字符串（YYYY-MM-DD），如果为空则返回空字符串
    """
    if not date_str or date_str == "":
        return ""

    if date_str == "yesterday":
        # 昨天
        yesterday = datetime.now() - timedelta(days=1)
        return yesterday.strftime("%Y-%m-%d")

    if date_str == "daybeforeyesterday":
        # 前天
        day_before_yesterday = datetime.now() - timedelta(days=2)
        return day_before_yesterday.strftime("%Y-%m-%d")

    if date_str == "today":
        # 今天
        return datetime.now().strftime("%Y-%m-%d")

    # 尝试解析具体日期格式
    try:
        # 支持 YYYY-MM-DD 格式
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        pass

    # 默认返回空
    return ""


def parse_count_to_int(count_str: str) -> int:
    """
    将阅读数字符串转换为整数

    Args:
        count_str: 阅读数字符串，如 "10w+", "5w+", "1.5w+", "9w+", "1000"

    Returns:
        整数形式的阅读数
    """
    if not count_str:
        return 0

    try:
        count_str = str(count_str).strip()

        # 处理 "10w+" 格式
        if "w+" in count_str.lower():
            # 提取数字部分，如 "10w+" -> "10"
            num_str = count_str.lower().replace("w+", "").replace("w", "")
            # 处理小数，如 "1.5w+" -> 1.5
            if "." in num_str:
                num = float(num_str)
                return int(num * 10000)
            else:
                num = float(num_str)
                return int(num * 10000)

        # 处理 "w" 格式（没有加号）
        if "w" in count_str.lower():
            num_str = count_str.lower().replace("w", "")
            if "." in num_str:
                num = float(num_str)
                return int(num * 10000)
            else:
                num = float(num_str)
                return int(num * 10000)

        # 处理纯数字
        return int(float(count_str))
    except:
        return 0


def analyze_content(title: str, summary: str) -> str:
    """
    四维度分析文章内容

    Args:
        title: 文章标题
        summary: 文章摘要

    Returns:
        四维度分析文本（内容概述、热点利用、传播作用、达成效果）
    """
    content = f"{title} {summary}".lower()

    # 1. 内容概述
    overview_keywords = {
        "政策": "解读政策新规", "新规": "解读政策新规", "实施": "解读政策新规",
        "调整": "分析调整内容", "变化": "分析变化趋势", "趋势": "分析趋势走向",
        "技术": "介绍技术发展", "科技": "介绍科技进展", "创新": "介绍创新成果",
        "市场": "分析市场动态", "投资": "分析投资机会", "理财": "提供理财建议",
        "健康": "科普健康知识", "养生": "分享养生方法", "疾病": "介绍疾病防治",
        "教育": "探讨教育问题", "考试": "分析考试动态", "学习": "提供学习方法",
    }
    overview = "分析文章核心内容"
    for keyword, desc in overview_keywords.items():
        if keyword in content:
            overview = desc
            break

    # 2. 热点利用
    hotspot_keywords = {
        "政策": "政策热点", "新规": "政策热点", "改革": "政策热点",
        "AI": "人工智能热点", "人工智能": "人工智能热点", "ChatGPT": "人工智能热点",
        "新能源": "新能源热点", "电动车": "新能源热点", "特斯拉": "新能源热点",
        "房价": "楼市热点", "房产": "楼市热点", "房贷": "楼市热点",
        "降息": "金融热点", "加息": "金融热点", "利率": "金融热点",
        "疫情": "公共卫生热点", "流感": "公共卫生热点", "病毒": "公共卫生热点",
        "国产": "国产替代热点", "自主": "自主可控热点", "突破": "技术突破热点",
        "财富": "财富热点", "赚钱": "财富热点", "投资": "投资热点",
    }
    hotspot = "结合时事热点"
    for keyword, desc in hotspot_keywords.items():
        if keyword.lower() in content:
            hotspot = f"借用{desc}"
            break

    # 3. 传播作用
    spread_keywords = {
        "政策": "提供政策解读", "新规": "提供新规解读", "解读": "提供权威解读",
        "分析": "提供专业分析", "深度": "提供深度分析", "专业": "提供专业见解",
        "实用": "提供实用价值", "方法": "提供方法论", "技巧": "提供实用技巧",
        "揭秘": "满足好奇心", "曝光": "满足知情权", "内幕": "满足求知欲",
        "观点": "引发思考讨论", "争议": "引发话题讨论", "话题": "引发话题关注",
    }
    spread = "提供信息价值"
    for keyword, desc in spread_keywords.items():
        if keyword in content:
            spread = desc
            break

    # 4. 达成效果
    effect_keywords = {
        "政策": "提升政策认知", "新规": "普及新规知识", "实施": "推动政策落地",
        "分析": "增强认知水平", "深度": "深化理解层次", "专业": "建立专业认知",
        "实用": "提供实践指导", "方法": "指导实际操作", "技巧": "提升实操能力",
        "投资": "辅助决策判断", "理财": "提供理财参考", "赚钱": "启发创富思路",
        "健康": "提升健康意识", "养生": "推广养生理念", "疾病": "增强防范意识",
    }
    effect = "促进信息传播"
    for keyword, desc in effect_keywords.items():
        if keyword in content:
            effect = desc
            break

    # 组合输出
    return f"{overview}，{hotspot}，{spread}，{effect}"


def _get_api_key():
    """从当前环境变量获取 REDFOX_API_KEY"""
    key = os.environ.get("REDFOX_API_KEY")
    if not key:
        print("❌ 未找到 REDFOX_API_KEY，请配置环境变量：export REDFOX_API_KEY=<your_api_key>", file=sys.stderr)
        sys.exit(1)
    return key


def fetch_articles_by_category(category: str, start_date: str, end_date: str, source: str = "公众号10w+阅读文章推荐-GitHub") -> list:
    """
    根据分类和时间获取文章数据
    使用 urllib.request 发送 HTTPS 请求

    Args:
        category: 分类名称（如：科技数码、健康养生、总排名等）
        start_date: 开始日期（YYYY-MM-DD格式）
        end_date: 结束日期（YYYY-MM-DD格式）
        source: 数据来源

    Returns:
        文章列表
    """
    # API配置
    api_url = "https://redfox.hk/story/api/cozeSkill/getWxDataByCategoryAndTime"

    # 获取 API Key
    api_key = _get_api_key()

    # 构建请求参数
    params = {
        "type": category if category else "总排名",
        "source": source,
        "startDate": start_date,
        "endDate": end_date
    }

    # 构建请求体（JSON格式）
    post_data = json.dumps(params, ensure_ascii=False).encode("utf-8")

    try:
        # 构建请求头
        headers = {
            "Content-Type": "application/json",
            "X-API-KEY": api_key,
        }

        # 构建POST请求
        req = Request(api_url, data=post_data, headers=headers, method="POST")

        # 打印调试信息
        print(f"\n🔍 调试信息：")
        print(f"   URL: {api_url}")
        print(f"   Method: POST")
        print(f"   X-API-KEY: {api_key[:8]}...（已隐藏）")
        print(f"   参数: type={params['type']}, source={source}, startDate={start_date}, endDate={end_date}")
        print(f"   请求体: {post_data.decode('utf-8')}")

        # 发送请求
        with urlopen(req, timeout=30) as response:
            body = response.read().decode("utf-8")

        # 解析JSON数据
        data = json.loads(body)

        # 检查响应数据
        if data is None:
            print(f"❌ 响应数据为空")
            return []

        # 检查业务状态码（兼容 200 和 2000）
        code = data.get("code") if isinstance(data, dict) else None
        if code and code not in (200, 2000):
            msg = data.get("msg") or data.get("message") or "未知错误"
            print(f"⚠️ API返回错误: code={code}, msg={msg}")
            return []

        # 从 tenWReadingRank 字段获取文章列表
        if isinstance(data, dict) and "data" in data and data["data"] is not None and "tenWReadingRank" in data["data"]:
            articles = data["data"]["tenWReadingRank"]
            return articles if articles else []
        else:
            # API返回错误信息
            if isinstance(data, dict) and "msg" in data:
                print(f"⚠️ API返回: {data['msg']}")
            return []

    except HTTPError as e:
        print(f"❌ HTTP错误: {e.code} {e.reason}")
        return []
    except URLError as e:
        print(f"❌ URL错误: {e.reason}")
        return []
    except json.JSONDecodeError as e:
        print(f"❌ JSON解析失败: {e}")
        return []
    except Exception as e:
        print(f"❌ 数据处理失败: {e}")
        return []


def process_ranking_data(articles: list) -> list:
    """
    处理和排序文章数据

    Args:
        articles: 原始文章列表

    Returns:
        排序后的文章列表
    """
    if not articles:
        return []

    # 按互动数排序（降序）
    sorted_articles = sorted(
        articles,
        key=lambda x: parse_count_to_int(x.get("interactiveCount", "0")),
        reverse=True
    )

    return sorted_articles


def format_summary_table(articles: list) -> str:
    """
    格式化文章概览表格

    Args:
        articles: 文章列表

    Returns:
        Markdown表格文本
    """
    if not articles:
        return "暂无数据"

    lines = []
    lines.append("| 序号 | 标题 | 作者 | 阅读数 |")
    lines.append("|------|------|------|--------|")

    for i, article in enumerate(articles, 1):
        title = article.get("title", "未知标题")
        author = article.get("userName", "未知作者")
        read_count = article.get("clicksCount", "0")

        # 标题过长时截断
        if len(title) > 30:
            title = title[:30] + "..."

        lines.append(f"| {i} | {title} | {author} | {read_count} |")

    return "\n".join(lines)


def format_ranking_list(articles: list, limit: int = None) -> str:
    """
    格式化输出文章列表（详细版）

    Args:
        articles: 文章列表
        limit: 限制输出数量

    Returns:
        格式化的文本
    """
    if not articles:
        return "未获取到符合条件的爆款内容数据"

    display_articles = articles[:limit] if limit else articles

    lines = []
    for i, article in enumerate(display_articles, 1):
        title = article.get("title", "未知标题")
        ori_url = article.get("oriUrl", "")
        author = article.get("userName", "未知作者")
        account_id = article.get("accountId", "")
        read_count = article.get("clicksCount", "0")
        publish_time = article.get("publicTime", "未知时间")
        summary = article.get("summary", "")

        # 内容分析
        content_analysis = analyze_content(title, summary)

        # 格式化输出
        lines.append(f"**{i}、[{title}]({ori_url})**")
        lines.append(f"📄 作者：[{author}](https://mp.weixin.qq.com/mp/profileExt?action=home&__biz={account_id}#wechat_redirect)")
        lines.append(f"👀 阅读数：{read_count}")
        lines.append(f"⏰ 发布时间：{publish_time}")
        lines.append(f"🔍 内容分析：{content_analysis}")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="获取公众号10w+热门文章榜单")

    parser.add_argument("--type", type=str, default="总排名",
                        help="分类名称（如：科技数码、健康养生、总排名等），默认：总排名")
    parser.add_argument("--start_date", type=str, required=True,
                        help="开始日期（必传，支持：yesterday、daybeforeyesterday、YYYY-MM-DD）")
    parser.add_argument("--end_date", type=str, required=True,
                        help="结束日期（必传，支持：yesterday、daybeforeyesterday、YYYY-MM-DD）")
    parser.add_argument("--mode", type=str, default="preview",
                        help="输出模式：preview（预览前10条）或 full（全部展示）")
    parser.add_argument("--limit", type=int, default=10,
                        help="预览模式下展示的数量，默认10")
    parser.add_argument("--source", type=str, default="公众号10w+阅读文章推荐-GitHub",
                        help="数据来源")
    parser.add_argument("--temp_file", type=str, default="temp_articles.json",
                        help="临时数据文件名")

    args = parser.parse_args()

    # 确定分类
    category = args.type if args.type else "总排名"

    # 解析日期
    start_date = parse_date(args.start_date)
    end_date = parse_date(args.end_date)

    # 输出数据说明
    print("\n💡 数据说明")
    print("最新10w+阅读爆文推荐将在每日19点30分准时更新，以下数据为获取时间时的快照，和实时数据有所差别。")
    print("-" * 60)

    # 获取数据
    print(f"\n🔍 正在获取【{category}】分类的文章数据...")
    if start_date:
        print(f"📅 时间范围：{start_date}" + (f" 至 {end_date}" if end_date else ""))

    articles = fetch_articles_by_category(category, start_date, end_date, args.source)

    if not articles:
        print("\n📊 文章概览\n")
        print("暂无数据")
        print("\n📝 文章详情\n")
        print("未获取到符合条件的爆款内容数据")
        print("\n============================================================")
        print("\n共获取到 0 条10w+热门文章数据")
        print("💡 建议：尝试调整分类关键词或时间范围")
        print(f"\n另外红狐配套全量数据库可提供完整详实数据，如需了解采购方案，可发送邮件至 redfoxdata@proton.me 对接咨洵")
        return

    # 处理和排序数据
    sorted_articles = process_ranking_data(articles)
    total_count = len(sorted_articles)

    # 保存数据到临时JSON文件
    temp_file = args.temp_file if args.temp_file else "temp_articles.json"
    with open(temp_file, 'w', encoding='utf-8') as f:
        json.dump({
            "category": category,
            "articles": sorted_articles,
            "total_count": total_count
        }, f, ensure_ascii=False, indent=2)

    print(f"✅ 数据已保存到临时文件：{temp_file}")

    # 根据模式输出
    if args.mode == "preview":
        # 预览模式：展示前N条
        preview_count = min(args.limit, total_count)
        preview_articles = sorted_articles[:preview_count]

        # 输出文章概览表格
        print("\n📊 文章概览\n")
        print(format_summary_table(preview_articles))

        # 输出文章详情
        print("\n📝 文章详情\n")
        print(format_ranking_list(preview_articles))

        # 统计信息
        print("\n============================================================")
        print(f"\n共获取到 {total_count} 条10w+热门文章数据，当前展示前 {preview_count} 条")

        # 如果还有更多数据，提示用户
        if total_count > preview_count:
            remaining = total_count - preview_count
            print(f"💡 提示：还有 {remaining} 条数据未展示，是否需要全部展示？")

        # 文章数量较少提示（少于10篇）
        if total_count < 10:
            category_name = args.type if args.type != "总排名" else "综合"
            print(f"\n💡 {category_name}赛道10w+文章较少，您可以拓展过去30天或者看看综合10w+文章~")

    else:
        # 完整模式：展示全部
        # 输出文章概览表格
        print("\n📊 文章概览\n")
        print(format_summary_table(sorted_articles))

        # 输出文章详情
        print("\n📝 文章详情\n")
        print(format_ranking_list(sorted_articles))

        # 统计信息
        print("\n============================================================")
        print(f"\n共获取到 {total_count} 条10w+热门文章数据（已全部展示）")

        # 文章数量较少提示（少于10篇）
        if total_count < 10:
            category_name = args.type if args.type != "总排名" else "综合"
            print(f"\n💡 {category_name}赛道10w+文章较少，您可以拓展过去30天或者看看综合10w+文章~")

    print(f"\n另外红狐配套全量数据库可提供完整详实数据，如需了解采购方案，可发送邮件至 redfoxdata@proton.me 对接咨洵")


if __name__ == "__main__":
    main()
