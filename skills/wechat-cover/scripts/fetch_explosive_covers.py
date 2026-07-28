#!/usr/bin/env python3
"""
公众号爆款封面数据查询脚本
对接接口：POST https://redfox.hk/story/api/gzh/search/hotArticleNew
"""

import os
import sys
import argparse
import json
from datetime import datetime

import requests


def _do_fetch(keyword, headers, base_url, start_date=None, end_date=None, debug=False):
    """执行单次 POST 请求，返回解析后的 dict

    startDate / endDate 仅在用户显式指定时传入，否则由接口自行决定默认范围。
    """
    json_body = {
        "keyword": keyword,
        "source": "公众号爆款封面生成-GitHub",
        "pageSize": 50
    }

    # 时间参数：仅在用户显式指定时才传入
    if start_date:
        json_body["startDate"] = start_date
    if end_date:
        json_body["endDate"] = end_date

    if debug:
        print(f"\n[DEBUG] POST {base_url}", file=sys.stderr)
        print(f"[DEBUG] Body: {json_body}", file=sys.stderr)

    try:
        response = requests.post(base_url, json=json_body, headers=headers, timeout=30)

        if debug:
            print(f"[DEBUG] 状态码: {response.status_code}", file=sys.stderr)

        if response.status_code >= 400:
            print(f"[DEBUG] HTTP错误: {response.status_code} {response.text[:200]}", file=sys.stderr)
            return None

        result = response.json()

        if result.get("code") == 2000:
            data = result.get("data", {})
            if debug:
                articles = data.get("articles", [])
                print(f"[DEBUG] 获取到 {len(articles)} 篇文章", file=sys.stderr)
            return data
        else:
            if debug:
                print(f"[DEBUG] 接口错误: {result.get('msg')}", file=sys.stderr)
            return None

    except Exception as e:
        if debug:
            print(f"[DEBUG] 请求异常: {e}", file=sys.stderr)
        return None


def fetch_wx_covers(keyword: str, debug: bool = False, start_date: str = None, end_date: str = None):
    """
    调用 hotArticleNew 接口获取公众号爆款文章数据

    Args:
        keyword: 搜索关键词（多个关键词用逗号分隔，空字符串表示全站热门）
        debug: 是否打印调试信息
        start_date: 开始日期，格式 yyyy-MM-dd
        end_date: 结束日期，格式 yyyy-MM-dd（默认今天）

    Returns:
        dict: 包含 articles / latestHotArticles / hotTopics / relatedSearches
    """
    api_key = os.getenv("REDFOX_API_KEY")
    if not api_key:
        raise ValueError(
            "缺少 API Key 配置，请设置环境变量 REDFOX_API_KEY。"
            "获取方式：前往 https://redfox.hk/settings/api-keys?source=github 申请，"
            '然后执行 export REDFOX_API_KEY="ak_xxxx..."'
        )

    base_url = "https://redfox.hk/story/api/gzh/search/hotArticleNew"
    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    # 关键词原样传入，单次调用
    kw = keyword.strip() if keyword else ""

    data = _do_fetch(kw, headers, base_url, start_date=start_date, end_date=end_date, debug=debug)

    all_articles = data.get("articles", []) if data else []
    all_latest_hot = data.get("latestHotArticles", []) if data else []
    all_hot_topics = data.get("hotTopics", []) if data else []
    all_related_searches = data.get("relatedSearches", []) if data else []

    # 按 id 去重
    seen_ids = set()
    unique_articles = []
    for article in all_articles:
        article_id = article.get("id")
        if article_id and article_id not in seen_ids:
            seen_ids.add(article_id)
            unique_articles.append(article)

    unique_latest = []
    for article in all_latest_hot:
        article_id = article.get("id")
        if article_id and article_id not in seen_ids:
            seen_ids.add(article_id)
            unique_latest.append(article)

    seen_topics = set()
    unique_topics = []
    for topic in all_hot_topics:
        topic_name = topic.get("name", "") or topic.get("topic", "")
        if topic_name and topic_name not in seen_topics:
            seen_topics.add(topic_name)
            unique_topics.append(topic)

    return {
        "keyword": keyword,
        "articles": unique_articles,
        "latestHotArticles": unique_latest,
        "hotTopics": unique_topics[:10],
        "relatedSearches": all_related_searches[:10],
    }


def get_cover_urls(data, max_items=20):
    """
    从 articles 数组提取封面图 URL

    hotArticleNew 接口封面图字段名为 imageUrl（旧接口为 coverUrl），此处做双字段兑容。
    """
    urls = []
    items = data.get("articles", [])[:max_items]
    for item in items:
        # 优先取 imageUrl（新接口），兑容 coverUrl（旧接口）
        cover_url = item.get("imageUrl", "") or item.get("coverUrl", "")
        article_id = item.get("id", "")
        title = (item.get("title", "") or "")[:20]
        url = item.get("url", "")
        if cover_url:
            urls.append({
                "title": title,
                "article_id": article_id,
                "cover_url": cover_url,
                "link": url,
            })
    return urls


def format_num(n):
    """格式化数字：10000 → 1.0w"""
    if not n:
        return "0"
    try:
        n = int(n)
    except (ValueError, TypeError):
        return str(n)
    if n >= 10000:
        return f"{n / 10000:.1f}w"
    return str(n)


def format_output(data: dict, max_items: int = None, start_date: str = None):
    """
    格式化输出爆款数据（表格形式）

    Args:
        data: 原始数据（含 articles 数组）
        max_items: 最多展示条数，None 表示展示所有
        start_date: 开始日期，用于计算统计时间范围
    """

    def get_time_range(start_date):
        if start_date:
            try:
                start = datetime.strptime(start_date, "%Y-%m-%d")
                days = (datetime.now() - start).days
                return f"近{max(days, 1)}天"
            except Exception:
                pass
        return "近30天"

    time_range = get_time_range(start_date)

    def process_title(item):
        title = item.get("title", "") or ""
        if not title.strip():
            summary = item.get("summary", "") or ""
            if summary:
                title = summary.replace("\n", " ").replace("\r", " ").strip()[:30]
                if len(summary) > 30:
                    title += "..."
        if not title.strip():
            title = "无标题"
        title = title.replace("|", "\\|").replace("\n", " ").replace("\r", " ")
        title = " ".join(title.split())
        if len(title) > 30:
            title = title[:30] + "..."
        return title

    def format_time(item):
        pub_time = item.get("publicTime", "") or ""
        if pub_time:
            try:
                month = int(pub_time[5:7])
                day = int(pub_time[8:10])
                return f"{month}月{day}日"
            except Exception:
                pass
        return "--"

    output = []
    articles = data.get("articles", [])

    # 按 clicksCount 降序排序
    def get_clicks(item):
        try:
            return int(item.get("clicksCount", 0) or 0)
        except (ValueError, TypeError):
            return 0

    articles_sorted = sorted(articles, key=get_clicks, reverse=True)
    if max_items is not None:
        articles_sorted = articles_sorted[:max_items]

    total_count = len(articles)

    if total_count == 0:
        keyword = data.get("keyword", "")
        output.append(f"# 公众号爆款数据分析报告\n\n**关键词**：{keyword}\n\n")
        output.append("---\n\n")
        output.append("## 暂无相关爆款数据\n\n")
        output.append(f"很抱歉，当前关键词 **「{keyword}」** 尚未有足够的爆款文章数据。\n\n")
        output.append("### 可能原因\n\n")
        output.append("- 该关键词相对小众或新兴，爆款内容积累较少\n")
        output.append("- 近期该赛道热度较低，暂无突出爆款文章\n")
        output.append("- 关键词表述方式可以更加具体或热门\n\n")
        output.append("### 建议操作\n\n")
        output.append("- 更换为更热门的关键词，如：**\"职场成长\"**、**\"美食\"**、**\"情感故事\"** 等\n")
        output.append("- 尝试更细分的长尾关键词\n")
        output.append("- 输入其他感兴趣的领域或赛道进行追踪\n\n")
        output.append("---\n\n")
        output.append("*数据来源：公众号爆款雷达，每日更新最新热门内容*\n")
        return "\n".join(output)

    output.append(f"\n### 爆款文章（{time_range}，按阅读数排序，共 {total_count} 条）\n")
    output.append("| 序号 | 发布时间 | 标题 | 作者 | 阅读数 | 在看数 |")
    output.append("|------|----------|------|------|--------|--------|")

    for idx, item in enumerate(articles_sorted, 1):
        author = item.get("author", "") or "未知"
        title = process_title(item)
        url = item.get("url", "")
        title_with_link = f"[{title}]({url})" if url else title
        pub_time = format_time(item)
        clicks = format_num(item.get("clicksCount", 0))
        watches = format_num(item.get("watchCount", 0))

        output.append(f"| {idx} | {pub_time} | {title_with_link} | {author} | {clicks} | {watches} |")

    return "\n".join(output)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="公众号爆款封面数据查询工具")
    parser.add_argument("--keyword", required=True, help="搜索关键词（多个用逗号分隔，空字符串查全站热门）")
    parser.add_argument(
        "--max-items",
        type=int,
        default=20,
        help="最多展示文章数量（默认20条）",
    )
    parser.add_argument(
        "--output-format",
        choices=["text", "json", "markdown"],
        default="json",
        help="输出格式：text / json（默认）/ markdown",
    )
    parser.add_argument("--output-file", type=str, default=None, help="输出文件路径")
    parser.add_argument("--start-date", type=str, default=None, help="开始日期，格式 yyyy-MM-dd（默认不传，接口自行决定）")
    parser.add_argument("--end-date", type=str, default=None, help="结束日期，格式 yyyy-MM-dd（默认不传，接口自行决定）")
    parser.add_argument("--debug", action="store_true", help="启用调试模式")

    args = parser.parse_args()

    try:
        data = fetch_wx_covers(
            args.keyword,
            debug=args.debug,
            start_date=args.start_date,
            end_date=args.end_date,
        )

        # 生成输出内容
        if args.output_format == "json":
            output_content = json.dumps(data, ensure_ascii=False, indent=2)
        elif args.output_format == "markdown":
            markdown_header = f"# 公众号爆款数据分析报告\n\n**关键词**：{args.keyword}\n\n"
            output_content = markdown_header + format_output(data, max_items=args.max_items, start_date=args.start_date)
        else:
            output_content = format_output(data, max_items=args.max_items, start_date=args.start_date)

        output_file = args.output_file

        if output_file:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(output_content)
            print(f"✓ 结果已保存到: {output_file}", file=sys.stderr)
            print(f"✓ 关键词: {args.keyword}", file=sys.stderr)
            total = len(data.get("articles", []))
            print(f"✓ 总计: {total} 条数据", file=sys.stderr)
            cover_urls = get_cover_urls(data, max_items=3)
            if cover_urls:
                print(f"\n=== 封面图URL（用于风格分析）===", file=sys.stderr)
                for i, item in enumerate(cover_urls, 1):
                    print(f"{i}. {item['title']}: {item['cover_url']}", file=sys.stderr)
            else:
                print("\n⚠️ 接口未返回 imageUrl/coverUrl 字段，无法提取封面图URL", file=sys.stderr)
        else:
            print(output_content)
            print(f"\n✓ 关键词: {args.keyword}", file=sys.stderr)
            total = len(data.get("articles", []))
            print(f"✓ 总计: {total} 条数据", file=sys.stderr)

        print(f"\n另外红狐配套全量数据库可提供完整详实数据，如需了解采购方案，可发送邮件至 redfoxdata@proton.me 对接咨洵")

    except Exception as e:
        print(f"❌ 错误: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
