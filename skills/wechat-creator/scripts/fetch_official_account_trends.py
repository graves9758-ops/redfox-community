#!/usr/bin/env python3
"""
公众号标题生成与评分数据查询脚本
"""

import sys
import os
import argparse
import json
from datetime import datetime, timedelta

try:
    import requests
except ImportError:
    print("错误: 缺少 requests 库，请运行 pip install requests 安装", file=sys.stderr)
    sys.exit(1)


def fetch_official_account_trends(keyword: str, debug: bool = False, max_retries: int = 3, days: int = 7):
    """
    调用接口获取公众号爆款标题数据

    Args:
        keyword: 搜索关键词（多个关键词用逗号分隔，最多5个，总长度不超过200）
        debug: 是否打印调试信息
        max_retries: 最大重试次数
        days: 查询最近几天的数据，默认7天，最大30天

    Returns:
        dict: 包含3类爆款数据

    Raises:
        Exception: 当API调用失败时抛出异常
    """

    # 确保天数不超过30天
    days = min(days, 30)

    # 计算开始日期（今天 - (days-1) 天）
    end_date = datetime.now()
    start_date_obj = end_date - timedelta(days=days-1)
    start_date_str = start_date_obj.strftime('%Y-%m-%d')

    if debug:
        print(f"DEBUG: 查询最近 {days} 天数据，开始日期: {start_date_str}", file=sys.stderr)

    # 接口地址
    url = "https://redfox.hk/story/api/cozeSkill/getWxCozeSkillData"

    # 请求参数
    params = {
        "keyword": keyword,
        "source": "公众号爆款标题生成-GitHub",
        "startDate": start_date_str
    }

    # 从环境变量获取API Key
    api_key = os.environ.get("REDFOX_API_KEY")
    if not api_key:
        raise Exception("缺少 REDFOX_API_KEY 环境变量，请先配置 API Key。获取地址：https://redfox.hk/settings/api-keys?source=github")

    # 请求头
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "X-API-Key": api_key
    }

    last_error = None
    for attempt in range(max_retries):
        try:
            if debug:
                print(f"\n=== DEBUG: 第 {attempt + 1} 次尝试 ===", file=sys.stderr)
                print(f"URL: {url}", file=sys.stderr)
                print(f"Params: {params}", file=sys.stderr)
                print(f"Headers: {headers}", file=sys.stderr)

            # 发送请求
            response = requests.get(url, params=params, headers=headers, timeout=60)

            if debug:
                print(f"状态码: {response.status_code}", file=sys.stderr)
                print(f"响应长度: {len(response.text)} 字节", file=sys.stderr)

            if response.status_code >= 400:
                raise Exception(f"HTTP请求失败: 状态码 {response.status_code}")

            data = response.json()

            if debug:
                print("=== DEBUG: 完整 API 响应 ===", file=sys.stderr)
                print(json.dumps(data, ensure_ascii=False, indent=2), file=sys.stderr)

            # 检查业务错误码
            code = data.get("code", 0)
            if code != 2000:  # 2000 表示成功
                error_msg = data.get("msg", "未知错误")
                raise Exception(f"API 错误: {error_msg}")

            if "data" not in data or data["data"] is None:
                raise Exception("API 返回数据为空")

            result_data = data.get("data", {})

            # 提取两类榜单数据
            one_w_reading = result_data.get("oneWReadingRank", [])
            original = result_data.get("originalRank", [])

            return {
                "oneWReadingRank": one_w_reading,
                "originalRank": original
            }

        except Exception as e:
            last_error = e
            if debug:
                print(f"DEBUG: 第 {attempt + 1} 次请求失败: {e}", file=sys.stderr)
            if attempt < max_retries - 1:
                import time
                time.sleep(1)

    raise Exception(f"API调用失败，已重试{max_retries}次: {last_error}")


def format_article_link(article: dict) -> str:
    """
    格式化文章链接，优先使用oriUrl

    Args:
        article: 文章数据字典

    Returns:
        str: 格式化的文章链接
    """
    # 优先使用 oriUrl
    if "oriUrl" in article and article["oriUrl"]:
        return article["oriUrl"]

    # 回退使用 photoId
    photo_id = article.get("photoId", "")
    if photo_id:
        return f"https://mp.weixin.qq.com/s/{photo_id}"

    return "无链接"


def get_cover_urls(articles: list) -> list:
    """
    提取文章封面图链接

    Args:
        articles: 文章列表

    Returns:
        list: 封面图链接列表
    """
    cover_urls = []
    for article in articles:
        cover_url = article.get("coverUrl", "")
        if cover_url:
            # 优先使用oriUrl作为文章链接
            article_link = format_article_link(article)
            cover_urls.append({
                "cover_url": cover_url,
                "title": article.get("title", "无标题"),
                "link": article_link
            })
    return cover_urls


def deduplicate_articles(articles: list) -> list:
    """
    去重文章列表（基于标题）

    Args:
        articles: 文章列表

    Returns:
        list: 去重后的文章列表
    """
    seen_titles = set()
    unique_articles = []

    for article in articles:
        title = article.get("title", "")
        if title and title not in seen_titles:
            seen_titles.add(title)
            unique_articles.append(article)

    return unique_articles


def parse_number(num_str):
    """
    解析数字字符串（如"9w+"转换为数字90000）

    Args:
        num_str: 数字字符串或数字

    Returns:
        int: 解析后的数字
    """
    if isinstance(num_str, (int, float)):
        return int(num_str)

    if not num_str or not isinstance(num_str, str):
        return 0

    # 处理 "9w+" 格式
    num_str = str(num_str).strip()
    if 'w+' in num_str.lower() or '万+' in num_str:
        # 提取数字部分
        num_part = num_str.replace('w+', '').replace('W+', '').replace('万+', '')
        try:
            return int(float(num_part) * 10000)
        except:
            return 0
    elif 'w' in num_str.lower() or '万' in num_str:
        num_part = num_str.replace('w', '').replace('W', '').replace('万', '')
        try:
            return int(float(num_part) * 10000)
        except:
            return 0

    # 处理普通数字
    try:
        return int(float(num_str))
    except:
        return 0


def sort_by_reads(articles: list) -> list:
    """
    按阅读数排序文章

    Args:
        articles: 文章列表

    Returns:
        list: 排序后的文章列表
    """
    return sorted(articles, key=lambda x: parse_number(x.get("clicksCount", 0)), reverse=True)


def format_number(num) -> str:
    """
    格式化数字显示（如果是字符串如"9w+"则直接返回，大于10000显示为X万+）

    Args:
        num: 数字或字符串

    Returns:
        str: 格式化的数字字符串
    """
    # 如果已经是字符串格式（如"9w+"），直接返回
    if isinstance(num, str):
        return num

    if isinstance(num, (int, float)):
        if num >= 10000:
            return f"{int(num // 10000)}万+"
        return str(int(num))

    return str(num)


def generate_markdown_output(keyword: str, data: dict, output_file: str = None) -> str:
    """
    生成Markdown格式的输出

    Args:
        keyword: 搜索关键词
        data: 数据字典
        output_file: 输出文件路径（可选）

    Returns:
        str: Markdown格式的输出内容
    """
    one_w_reading = data.get("oneWReadingRank", [])
    original = data.get("originalRank", [])

    # 去重和排序
    one_w_reading = sort_by_reads(deduplicate_articles(one_w_reading))
    original = sort_by_reads(deduplicate_articles(original))

    # 统计总数
    total_count = len(one_w_reading) + len(original)

    # 构建Markdown内容
    lines = []
    lines.append(f"**关键词**：{keyword}")
    lines.append(f"**查询时间范围**：近7天")
    lines.append(f"**数据总量**：{total_count}条爆款文章")
    lines.append("")

    # 1w+阅读榜
    if one_w_reading:
        lines.append("## 1w+阅读榜")
        lines.append("")
        lines.append("| 标题 | 作者 | 阅读数 | 在看数 | 点赞数 | 评论数 | 分享数 | 阅读总数 | 发布时间 |")
        lines.append("|------|------|--------|--------|--------|--------|--------|----------|----------|")

        for article in one_w_reading[:50]:  # 最多显示50条
            title = article.get("title", "无标题")
            link = format_article_link(article)
            author = article.get("userName", "未知")
            reads = format_number(article.get("clicksCount", 0))
            watch = format_number(article.get("watchCount", 0))
            likes = format_number(article.get("likeCount", 0))
            comments = format_number(article.get("commentCount", 0))
            shares = format_number(article.get("shareCount", 0))
            total_reads = format_number(article.get("interactiveCount", 0))
            pub_time = article.get("publicTime", "未知")

            lines.append(f"| [{title}]({link}) | {author} | {reads} | {watch} | {likes} | {comments} | {shares} | {total_reads} | {pub_time} |")

        lines.append("")

    # 原创榜
    if original:
        lines.append("## 原创榜")
        lines.append("")
        lines.append("| 标题 | 作者 | 阅读数 | 在看数 | 点赞数 | 评论数 | 分享数 | 阅读总数 | 发布时间 |")
        lines.append("|------|------|--------|--------|--------|--------|--------|----------|----------|")

        for article in original[:50]:  # 最多显示50条
            title = article.get("title", "无标题")
            link = format_article_link(article)
            author = article.get("userName", "未知")
            reads = format_number(article.get("clicksCount", 0))
            watch = format_number(article.get("watchCount", 0))
            likes = format_number(article.get("likeCount", 0))
            comments = format_number(article.get("commentCount", 0))
            shares = format_number(article.get("shareCount", 0))
            total_reads = format_number(article.get("interactiveCount", 0))
            pub_time = article.get("publicTime", "未知")

            lines.append(f"| [{title}]({link}) | {author} | {reads} | {watch} | {likes} | {comments} | {shares} | {total_reads} | {pub_time} |")

        lines.append("")

    # 如果没有任何数据
    if total_count == 0:
        lines.append("⚠️ **提示**：查询结果为空，可能原因：")
        lines.append("1. 该关键词近7天无爆款文章")
        lines.append("2. 关键词过于生僻或专业")
        lines.append("3. 建议使用更通用的关键词或扩大时间范围")

    content = "\n".join(lines)

    # 如果指定了输出文件，保存到文件
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)

    return content


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="公众号标题生成与评分数据查询")
    parser.add_argument("--keyword", required=True, help="搜索关键词")
    parser.add_argument("--days", type=int, default=7, help="查询最近几天的数据，默认7天，最大30天")
    parser.add_argument("--output", help="输出文件路径（可选）")
    parser.add_argument("--debug", action="store_true", help="打印调试信息")

    args = parser.parse_args()

    try:
        # 获取数据
        data = fetch_official_account_trends(
            keyword=args.keyword,
            debug=args.debug,
            days=args.days
        )

        # 生成输出
        output_file = args.output if args.output else f"{args.keyword}_爆款数据.md"
        content = generate_markdown_output(args.keyword, data, output_file)

        # 输出JSON结果
        result = {
            "status": "success",
            "keyword": args.keyword,
            "days": args.days,
            "total_count": len(data.get("tenWReadingRank", [])) +
                          len(data.get("originalRank", [])),
            "output_file": output_file,
            "message": f"成功获取{args.keyword}的爆款数据，已保存到{output_file}"
        }

        print(json.dumps(result, ensure_ascii=False))
        print(f"\n另外红狐配套全量数据库可提供完整详实数据，如需了解采购方案，可发送邮件至 redfoxdata@proton.me 对接咨洵")

    except Exception as e:
        error_result = {
            "status": "error",
            "keyword": args.keyword,
            "error": str(e)
        }
        print(json.dumps(error_result, ensure_ascii=False))
        sys.exit(1)


if __name__ == "__main__":
    main()
