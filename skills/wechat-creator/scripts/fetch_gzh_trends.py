#!/usr/bin/env python3
"""
公众号热门数据查询脚本
接口：红狐数据 - 公众号爆款文章搜索
"""

import os
import sys
import argparse
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional


def _do_fetch(keyword: str, start_date: str, end_date: str, headers: dict, base_url: str, debug: bool = False) -> dict:
    """
    执行单次API请求

    Args:
        keyword: 搜索关键词（多个关键词用英文逗号分隔）
        start_date: 开始日期，格式 yyyy-MM-dd
        end_date: 结束日期，格式 yyyy-MM-dd
        headers: 请求头
        base_url: API基础URL
        debug: 是否打印调试信息

    Returns:
        dict: 包含articles列表和其他元数据
    """
    params = {
        "keyword": keyword,
        "startDate": start_date,
        "endDate": end_date,
        "source": "公众号文案创作-GitHub"
    }

    if debug:
        print(f"\n=== DEBUG: API请求参数 ===", file=sys.stderr)
        print(f"URL: {base_url}", file=sys.stderr)
        print(f"Params: {json.dumps(params, ensure_ascii=False)}", file=sys.stderr)

    try:
        response = requests.post(base_url, headers=headers, json=params, timeout=60)

        if debug:
            print(f"状态码: {response.status_code}", file=sys.stderr)
            print(f"响应长度: {len(response.text)} 字节", file=sys.stderr)

        if response.status_code >= 400:
            raise Exception(f"HTTP请求失败: 状态码 {response.status_code}")

        data = response.json()

        # 检查返回码（2000表示成功）
        code = data.get("code", 0)
        if code != 2000:
            error_msg = data.get("msg", "未知错误")
            raise Exception(f"API错误(code={code}): {error_msg}")

        articles = data.get("data", {}).get("articles", [])

        if debug:
            print(f"返回文章数: {len(articles)}", file=sys.stderr)
            if articles:
                print(f"首篇文章字段: {list(articles[0].keys())}", file=sys.stderr)

        return {
            "articles": articles,
            "keyword": keyword,
            "startDate": start_date,
            "endDate": end_date
        }

    except requests.exceptions.Timeout:
        raise Exception("请求超时，请稍后重试")
    except requests.exceptions.ConnectionError:
        raise Exception("网络连接失败，请检查网络")
    except json.JSONDecodeError:
        raise Exception("响应数据解析失败")
    except Exception as e:
        raise Exception(str(e))


def fetch_gzh_trends(keyword: str, start_date: str = None, debug: bool = False, auto_expand: bool = True) -> dict:
    """
    调用接口获取公众号趋势数据

    Args:
        keyword: 搜索关键词（多个关键词用英文逗号分隔）
        start_date: 开始日期，格式 yyyy-MM-dd，最长为最近30天
        debug: 是否打印调试信息
        auto_expand: 当数据不足时，自动拓展时间范围
            - 用户指定了时间：按用户指定时间查询，不自动拓展
            - 用户未指定时间：默认近7天；数据不足时拓展至近30天

    Returns:
        dict: 包含articles列表、expandedDays、expandedHint等字段

    关键词规则：
        - 多关键词以英文逗号分隔
        - 最多5个关键词
        - 总长度不超过200字符
    """
    base_url = "https://redfox.hk/story/api/gzh/search/hotArticleNew"
    api_key = os.environ.get("REDFOX_API_KEY", "")
    if not api_key:
        raise Exception("缺少API Key：请设置环境变量 REDFOX_API_KEY。获取方式：https://redfox.hk/settings/api-keys?source=github")
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": api_key
    }

    end_date = datetime.now().strftime("%Y-%m-%d")

    # 用户指定了时间范围，直接按指定时间查询，不自动拓展
    if start_date:
        result = _do_fetch(keyword, start_date, end_date, headers=headers, base_url=base_url, debug=debug)
        # 计算用户指定的时间范围天数
        days_diff = (datetime.now() - datetime.strptime(start_date, "%Y-%m-%d")).days
        result["expandedDays"] = days_diff
        return result

    # 用户未指定时间，默认近7天
    start_7 = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    result = _do_fetch(keyword, start_7, end_date, headers=headers, base_url=base_url, debug=debug)
    articles = result.get("articles", [])

    # 近7天数据不足10条且允许自动拓展，拓展至近30天
    if len(articles) < 10 and auto_expand:
        start_30 = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        result = _do_fetch(keyword, start_30, end_date, headers=headers, base_url=base_url, debug=debug)
        result["expandedDays"] = 30
        result["expandedHint"] = "近7天数据不足，已自动拓展至近30天"
    else:
        result["expandedDays"] = 7

    return result


def format_output(data: dict, max_items: int = 10) -> str:
    """
    格式化输出热门数据（表格形式）

    Args:
        data: 原始数据，包含articles列表
        max_items: 最多展示文章数量

    Returns:
        str: Markdown格式的输出内容
    """

    def process_title(item: dict) -> str:
        """处理标题：转义特殊字符，空标题使用summary替代，并添加作品链接"""
        title = item.get('title', '')

        # 如果标题为空，尝试使用 summary 字段
        if not title or title.strip() == '':
            summary = item.get('summary', '')
            if summary:
                # 移除 summary 中的换行符并截取前30个字符
                title = summary.replace('\n', ' ').replace('\r', ' ').strip()[:30]
                if len(summary) > 30:
                    title = title + '...'

        if not title or title.strip() == '':
            title = '无标题'

        # 转义 Markdown 表格特殊字符（|）
        title = title.replace('|', '\\|')
        # 移除换行符
        title = title.replace('\n', ' ').replace('\r', ' ')
        # 移除多余空格
        title = ' '.join(title.split())

        # 截断过长标题
        if len(title) > 30:
            title = title[:30] + "..."

        # 添加作品链接（公众号使用 url 字段）
        article_url = item.get('url', '')
        if article_url:
            title = f"[{title}]({article_url})"

        return title

    def process_author(item: dict) -> str:
        """处理作者信息"""
        # API返回的字段：author（公众号名称）
        author_name = item.get('author', '未知')

        # 简化输出，只显示作者名
        return author_name

    output = []

    # 获取文章列表并去重
    articles = data.get("articles", [])

    # 按 id 去重（API 返回数据可能有重复）
    def dedup_items(items: List[dict]) -> List[dict]:
        seen = set()
        result = []
        for item in items:
            article_id = item.get('id', '')
            if article_id and article_id not in seen:
                seen.add(article_id)
                result.append(item)
        return result

    articles = dedup_items(articles)

    # 截取指定数量
    display_articles = articles[:max_items] if max_items is not None else articles
    display_total = len(display_articles)

    # 输出标题
    keyword = data.get("keyword", "")
    expanded_days = data.get("expandedDays", 7)
    expanded_hint = data.get("expandedHint", "")

    output.append(f"# 公众号爆款数据分析报告\n")
    output.append(f"\n**关键词**：{keyword}")
    output.append(f"\n**爆款总数**：{display_total} 条")
    output.append(f"\n**统计时间**：近 {expanded_days} 天")

    if expanded_hint:
        output.append(f"\n*{expanded_hint}*")

    output.append("\n\n---\n")

    # 如果没有数据，输出友好提示
    if display_total == 0:
        output.append("## 暂无相关爆款数据\n\n")
        output.append(f"很抱歉，当前关键词 **「{keyword}」** 尚未有足够的爆款文章数据。\n\n")
        output.append("### 可能原因\n\n")
        output.append("- 该关键词相对小众或新兴，爆款内容积累较少\n")
        output.append("- 近期该赛道热度较低，暂无突出爆款文章\n")
        output.append("- 关键词表述方式可以更加具体或热门\n\n")
        output.append("### 建议操作\n\n")
        output.append("- 更换为更热门的关键词，如：**\"职场干货\"**、**\"个人成长\"**、**\"理财知识\"** 等\n")
        output.append("- 尝试更细分的长尾关键词，如：**\"副业赚钱\"**、**\"时间管理技巧\"** 等\n")
        output.append("- 输入其他感兴趣的领域或赛道进行追踪\n\n")
        output.append("---\n\n")
        output.append("*数据来源：红狐数据公众号爆款雷达，每日更新最新热门内容*\n")
        return "\n".join(output)

    # 输出爆款文章表格
    output.append(f"\n## 爆款文章列表（共 {display_total} 条）\n\n")

    output.append("| 序号 | 标题 | 作者 | **阅读数** | 在看 | 点赞 | 评论 |")
    output.append("|------|------|------|---------|------|------|------|")

    for idx, item in enumerate(display_articles, 1):
        title = process_title(item)
        author_str = process_author(item)

        # 互动数据（API实际返回字段）
        clicks_count = item.get('clicksCount', '0')
        watch_count = item.get('watchCount', '0')
        like_count = item.get('likeCount', '0')
        comments_count = item.get('commentsCount', '0')
        # API没有返回shareCount字段，暂时不显示

        output.append(f"| {idx} | {title} | {author_str} | **{clicks_count}** | {watch_count} | {like_count} | {comments_count} |")

    output.append("\n\n---\n\n")
    output.append("*数据来源：红狐数据公众号爆款雷达，每日更新最新热门内容*\n")

    return "\n".join(output)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='公众号热门数据查询工具（红狐数据）')
    parser.add_argument('--keyword', required=True,
                       help='搜索关键词（多个关键词用英文逗号分隔，最多5个，总长度不超过200字符）')
    parser.add_argument('--max-items', type=int, default=10,
                       help='最多展示文章数量（默认10条）')
    parser.add_argument('--start-date', type=str, default=None,
                       help='开始日期，格式 yyyy-MM-dd（最长为最近30天）')
    parser.add_argument('--output-format', choices=['text', 'json', 'markdown'],
                       default='markdown', help='输出格式（默认markdown）')
    parser.add_argument('--debug', action='store_true', help='启用调试模式')
    parser.add_argument('--no-auto-expand', action='store_true',
                       help='禁用自动拓展时间范围（默认开启）')

    args = parser.parse_args()

    try:
        auto_expand = not args.no_auto_expand

        data = fetch_gzh_trends(
            keyword=args.keyword,
            start_date=args.start_date,
            debug=args.debug,
            auto_expand=auto_expand
        )

        # 生成输出内容
        if args.output_format == 'json':
            output_content = json.dumps(data, ensure_ascii=False, indent=2)
        else:
            output_content = format_output(data, max_items=args.max_items)

        # 直接输出到控制台
        print(output_content)
        print(f"\n另外红狐配套全量数据库可提供完整详实数据，如需了解采购方案，可发送邮件至 redfoxdata@proton.me 对接咨洵")

    except Exception as e:
        print(f"❌ 错误: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
