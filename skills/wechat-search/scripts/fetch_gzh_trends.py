#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
公众号趋势洞察数据获取脚本
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime, timedelta


def _get_api_key():
    """从当前环境变量获取 REDFOX_API_KEY"""
    api_key = os.environ.get("REDFOX_API_KEY")
    if not api_key:
        print("❌ 未找到 REDFOX_API_KEY，请配置环境变量：export REDFOX_API_KEY=<你的apikey>", file=sys.stderr)
        sys.exit(1)
    return api_key


def _http_post(url, body_dict, headers):
    """使用 urllib.request 发送 POST JSON 请求，返回解析后的 dict，失败返回 None"""
    data = json.dumps(body_dict, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw)
    except urllib.error.HTTPError as e:
        return {"__http_error__": e.code}
    except Exception as e:
        return {"__error__": str(e)}


def fetch_gzh_trends(keyword, start_date=None, debug=False, auto_expand=True):
    """调用接口获取公众号趋势数据

    auto_expand: 当数据不足时，自动拓展时间范围
    - 用户指定了时间：按用户指定时间查询，不自动拓展
    - 用户未指定时间：默认近7天；数据不足时拓展至近30天
    """
    base_url = "https://redfox.hk/story/api/gzh/search/hotArticleNew"
    api_key = _get_api_key()
    default_headers = {
        "Content-Type": "application/json",
        "X-API-Key": api_key
    }

    end_date = datetime.now().strftime("%Y-%m-%d")

    # 用户指定了时间范围，直接按指定时间查询，不自动拓展
    if start_date:
        result = _do_fetch(keyword, start_date, end_date, headers=default_headers, base_url=base_url, debug=debug)
        # 计算用户指定的时间范围天数
        days_diff = (datetime.now() - datetime.strptime(start_date, "%Y-%m-%d")).days
        result["expandedDays"] = days_diff
        return result

    # 用户未指定时间，默认近7天
    start_7 = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    result = _do_fetch(keyword, start_7, end_date, headers=default_headers, base_url=base_url, debug=debug)
    articles = result.get("articles", [])

    # 近7天数据不足10条且允许自动拓展，拓展至近30天
    if len(articles) < 10 and auto_expand:
        start_30 = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        result = _do_fetch(keyword, start_30, end_date, headers=default_headers, base_url=base_url, debug=debug)
        result["expandedDays"] = 30
        result["expandedHint"] = "近7天数据不足，已自动拓展至近30天"

    return result


def _do_fetch(keyword, start_date, end_date, headers, base_url, debug=False):
    """实际执行接口请求"""

    # 多关键词处理（支持空关键词，接口会返回全站热门）
    if keyword and keyword.strip():
        keywords = [k.strip() for k in keyword.split(",") if k.strip()]
    else:
        keywords = [""]  # 空关键词，接口返回全站热门数据

    all_articles = []
    all_latest_hot = []
    all_hot_topics = []
    all_related_searches = []

    for kw in keywords:
        json_body = {
            "keyword": kw,
            "startDate": start_date,
            "endDate": end_date,
            "source": "公众号爆款文章洞察-GitHub"
        }

        if debug:
            print(f"正在查询关键词: {kw}")

        result = _http_post(base_url, json_body, headers)

        if "__http_error__" in result:
            if debug:
                print(f"HTTP错误: {result['__http_error__']}")
        elif "__error__" in result:
            if debug:
                print(f"请求异常: {result['__error__']}")
        else:
            if debug:
                print(f"状态码: 200")

            if result.get("code") == 2000:
                data = result.get("data", {})

                # 正常文章数据
                articles = data.get("articles", [])
                all_articles.extend(articles)

                # 推荐热门文章
                latest_hot = data.get("latestHotArticles", [])
                all_latest_hot.extend(latest_hot)

                # 热门话题
                hot_topics = data.get("hotTopics", [])
                all_hot_topics.extend(hot_topics)

                # 相关搜索
                related = data.get("relatedSearches", [])
                all_related_searches.extend(related)

                if debug:
                    print(f"获取到 {len(articles)} 篇正常文章")
                    print(f"获取到 {len(latest_hot)} 篇相关推荐")
            else:
                if debug:
                    print(f"接口返回错误: {result.get('msg')}")

    # 去重
    seen_ids = set()
    unique_articles = []
    for article in all_articles:
        article_id = article.get('id')
        if article_id and article_id not in seen_ids:
            seen_ids.add(article_id)
            unique_articles.append(article)

    unique_latest = []
    for article in all_latest_hot:
        article_id = article.get('id')
        if article_id and article_id not in seen_ids:
            seen_ids.add(article_id)
            unique_latest.append(article)

    seen_topics = set()
    unique_topics = []
    for topic in all_hot_topics:
        topic_name = topic.get('name', '') or topic.get('topic', '')
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


def sort_articles(articles):
    """按总分降序排序文章"""
    return sorted(articles, key=lambda x: x.get('totalScore') or 0, reverse=True)


def format_num(n):
    """格式化数字"""
    if n >= 10000:
        return f"{n/10000:.1f}w"
    return str(n)


def generate_recommend_reason(item):
    """生成推荐理由"""
    title = item.get('title', '')
    relevance = item.get('relevanceScore') or 0
    clicks = item.get('clicksCount', 0) or 0

    reasons = []

    if relevance >= 7:
        reasons.append("与关键词高度相关")
    elif relevance >= 5:
        reasons.append("与关键词较为相关")

    if clicks >= 100000:
        reasons.append("阅读量10w+")
    elif clicks >= 50000:
        reasons.append("阅读量较高")

    if '技巧' in title or '方法' in title:
        reasons.append("实用性强")
    elif '误区' in title or '陷阱' in title:
        reasons.append("避坑指南")

    return "；".join(reasons) if reasons else "综合推荐"


def get_card_html(item):
    """生成单张卡片HTML"""
    title = item.get('title', '') or item.get('summary', '')[:50]
    author = item.get('author', '') or '-'
    pub_time = item.get('publicTime', '')[:10]
    note_link = item.get('url', '')

    clicks_count = item.get('clicksCount', 0) or 0
    watch_count = item.get('watchCount', 0) or 0
    relevance = item.get('relevanceScore', 0) or 0
    popularity = item.get('popularityScore', 0) or 0
    recency = item.get('recencyScore', 0) or 0
    total = item.get('totalScore', 0) or 0

    reason = generate_recommend_reason(item)

    # 截取摘要前100字
    summary = item.get('summary', '')[:100] if item.get('summary') else ''

    card = f'''
    <div class="card">
        <div class="card-content">
            <div class="card-header">
                <h3 class="card-title">
                    <a href="{note_link}" target="_blank">{title}</a>
                </h3>
                <div class="card-scores">
                    <span class="score-tag relevance">相关性 {relevance:.1f}</span>
                    <span class="score-tag popularity">热度 {popularity:.1f}</span>
                    <span class="score-tag recency">时效 {recency:.1f}</span>
                    <span class="score-tag total">总分 {total:.1f}</span>
                </div>
            </div>
            <div class="card-meta">
                <span class="author">👤 {author}</span>
                <span class="date">📅 {pub_time}</span>
                <span class="clicks">👁 阅读 {format_num(clicks_count)}</span>
                <span class="watch">👀 在看 {format_num(watch_count)}</span>
            </div>
            <div class="card-summary">{summary}...</div>
            <div class="card-footer">
                <span class="reason">💡 {reason}</span>
                <a href="{note_link}" target="_blank" class="read-more">查看文章 →</a>
            </div>
        </div>
    </div>
    '''
    return card


def get_empty_html(keyword, hot_topics):
    """生成空结果HTML"""
    # 分类建议
    categories = ["AI 前沿", "副业赚钱", "自媒体运营", "工具推荐", "行业案例", "流量增长"]
    category_btns = " ".join([f'<span class="category-btn">{cat}</span>' for cat in categories])

    # 热门话题列表
    topics_html = ""
    if hot_topics:
        topics_html = '<div class="topics-box">\n<h4>📈 热门话题</h4>\n<ul class="topics-list">\n'
        for topic in hot_topics[:6]:
            topic_name = topic.get('name', '') or topic.get('topic', '')
            count = topic.get('count', 0) or topic.get('articleCount', 0)
            topics_html += f'<li>· {topic_name}（{count} 篇）</li>\n'
        topics_html += '</ul>\n</div>'

    html = f'''
    <div class="empty-result">
        <div class="empty-icon">🔍</div>
        <h3 class="empty-title">抱歉，未找到与"{keyword}"直接相关的内容</h3>
        <div class="empty-tips">
            <h4>💡 你可以试试：</h4>
            {topics_html}
            <div class="categories-box">
                <h4>📂 按分类浏览：</h4>
                <div class="categories-list">{category_btns}</div>
            </div>
            <p class="retry-tip">✏️ 或使用更短/宽泛的关键词重试</p>
        </div>
    </div>
    '''
    return html


def get_recommend_section_html(articles):
    """生成相关推荐区域HTML"""
    if not articles:
        return ""

    cards = []
    for item in articles[:6]:  # 最多展示6条
        cards.append(get_card_html(item))

    section = f'''
    <div class="recommend-section">
        <h3 class="section-title">📌 相关推荐</h3>
        <div class="recommend-cards">
            {"".join(cards)}
        </div>
    </div>
    '''
    return section


def get_topics_section_html(hot_topics):
    """生成热门话题区域HTML"""
    if not hot_topics:
        return ""

    topics_html = '<div class="topics-section"><h3>📈 热门话题推荐</h3><div class="topics-grid">'
    for topic in hot_topics[:6]:
        topic_name = topic.get('name', '') or topic.get('topic', '')
        count = topic.get('count', 0) or topic.get('articleCount', 0)
        topics_html += f'<div class="topic-item"><div class="topic-name">{topic_name}</div><div class="topic-count">{count} 篇文章</div></div>'
    topics_html += '</div></div>'

    return topics_html


def generate_html(keyword, articles, latest_hot, hot_topics, result_status):
    """生成HTML页面"""
    html_template = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>公众号趋势洞察 - {keyword}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
        }}
        .header {{
            text-align: center;
            padding: 30px 0;
            color: white;
        }}
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        .header .subtitle {{
            font-size: 1.1em;
            opacity: 0.9;
        }}
        .partial-tip {{
            background: #fff3cd;
            border: 1px solid #ffc107;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 20px;
            color: #856404;
        }}
        .partial-tip strong {{
            color: #d63031;
        }}
        .card {{
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            margin-bottom: 20px;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}
        .card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 8px 15px rgba(0, 0, 0, 0.2);
        }}
        .card-content {{
            padding: 20px;
        }}
        .card-header {{
            margin-bottom: 15px;
        }}
        .card-title {{
            font-size: 1.2em;
            margin-bottom: 10px;
        }}
        .card-title a {{
            color: #2d3436;
            text-decoration: none;
        }}
        .card-title a:hover {{
            color: #6c5ce7;
        }}
        .card-scores {{
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
        }}
        .score-tag {{
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: 500;
        }}
        .score-tag.relevance {{
            background: #e3f2fd;
            color: #1976d2;
        }}
        .score-tag.popularity {{
            background: #fff3e0;
            color: #f57c00;
        }}
        .score-tag.recency {{
            background: #e8f5e9;
            color: #388e3c;
        }}
        .score-tag.total {{
            background: #fce4ec;
            color: #c2185b;
        }}
        .card-meta {{
            display: flex;
            gap: 15px;
            color: #636e72;
            font-size: 0.9em;
            margin-bottom: 10px;
        }}
        .card-summary {{
            color: #2d3436;
            line-height: 1.6;
            margin-bottom: 15px;
        }}
        .card-footer {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-top: 1px solid #dfe6e9;
            padding-top: 10px;
        }}
        .reason {{
            color: #636e72;
            font-size: 0.9em;
        }}
        .read-more {{
            color: #6c5ce7;
            text-decoration: none;
            font-weight: 500;
        }}
        .read-more:hover {{
            text-decoration: underline;
        }}
        .empty-result {{
            background: white;
            border-radius: 12px;
            padding: 40px;
            text-align: center;
        }}
        .empty-icon {{
            font-size: 4em;
            margin-bottom: 20px;
        }}
        .empty-title {{
            color: #2d3436;
            margin-bottom: 30px;
        }}
        .empty-tips {{
            text-align: left;
        }}
        .empty-tips h4 {{
            color: #6c5ce7;
            margin-bottom: 15px;
        }}
        .topics-box {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
        }}
        .topics-list {{
            list-style: none;
        }}
        .topics-list li {{
            padding: 8px 0;
            color: #2d3436;
        }}
        .categories-box {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
        }}
        .categories-list {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }}
        .category-btn {{
            background: #6c5ce7;
            color: white;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 0.9em;
            cursor: pointer;
            transition: background 0.3s;
        }}
        .category-btn:hover {{
            background: #5f27cd;
        }}
        .retry-tip {{
            color: #636e72;
            font-style: italic;
            margin-top: 15px;
        }}
        .topics-section {{
            background: white;
            border-radius: 12px;
            padding: 20px;
            margin-top: 20px;
        }}
        .topics-section h3 {{
            color: #6c5ce7;
            margin-bottom: 15px;
        }}
        .topics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 15px;
        }}
        .topic-item {{
            background: #f8f9fa;
            padding: 12px;
            border-radius: 8px;
            transition: background 0.3s;
        }}
        .topic-item:hover {{
            background: #e9ecef;
        }}
        .topic-name {{
            font-weight: 500;
            color: #2d3436;
        }}
        .topic-count {{
            color: #636e72;
            font-size: 0.9em;
        }}
        .recommend-section {{
            margin-top: 30px;
        }}
        .section-title {{
            color: white;
            font-size: 1.5em;
            text-align: center;
            margin-bottom: 20px;
            padding: 15px;
            background: rgba(255, 255, 255, 0.2);
            border-radius: 12px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 公众号趋势洞察</h1>
            <p class="subtitle">关键词: {keyword} | 查询结果: {total} 篇文章</p>
        </div>
        {content}
    </div>
</body>
</html>
'''

    total = len(articles)

    if result_status == "empty":
        # articles为0，展示推荐热门文章
        content_parts = [get_empty_html(keyword, hot_topics)]
        if latest_hot:
            content_parts.append(get_recommend_section_html(latest_hot))
        content = "\n".join(content_parts)
    elif result_status == "partial":
        # articles < 10，展示提示 + 文章 + 热门话题 + 推荐热门文章
        content_parts = [f'<div class="partial-tip"><strong>💡 仅找到 {total} 条结果</strong>，以下内容可能也对你有帮助：</div>']
        for item in articles:
            content_parts.append(get_card_html(item))
        if hot_topics:
            content_parts.append(get_topics_section_html(hot_topics))
        if latest_hot:
            content_parts.append(get_recommend_section_html(latest_hot))
        content = "\n".join(content_parts)
    else:
        # articles >= 10，正常展示 + 推荐热门文章
        content_parts = []
        for item in articles:
            content_parts.append(get_card_html(item))
        if latest_hot:
            content_parts.append(get_recommend_section_html(latest_hot))
        content = "\n".join(content_parts)

    return html_template.format(keyword=keyword, total=total, content=content)


def output_json(keyword, articles, latest_hot, hot_topics, related_searches, result_status, expanded_days=None, expanded_hint=None):
    """输出JSON结果"""
    output = {
        "keyword": keyword,
        "total": len(articles),
        "resultStatus": result_status,
        "articles": articles,
    }

    # 根据不同状态附加不同数据
    if result_status == "normal":
        # articles >= 10，附加推荐热门文章
        if latest_hot:
            output["latestHotArticles"] = latest_hot
    elif result_status == "partial":
        # articles < 10，附加热门话题和推荐热门文章
        if hot_topics:
            output["hotTopics"] = hot_topics
        if latest_hot:
            output["latestHotArticles"] = latest_hot
    elif result_status == "empty":
        # articles为0，附加推荐热门文章、热门话题、相关搜索
        if latest_hot:
            output["latestHotArticles"] = latest_hot
        if hot_topics:
            output["hotTopics"] = hot_topics
        if related_searches:
            output["relatedSearches"] = related_searches
        output["suggestion"] = "建议使用更短或更宽泛的关键词重试"
    # 拓展时间信息
    if expanded_days and expanded_hint:
        output["expandedDays"] = expanded_days
        output["expandedHint"] = expanded_hint

    print(json.dumps(output, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description="获取公众号趋势数据")
    parser.add_argument("--keyword", required=True, help="搜索关键词，多个用逗号分隔")
    parser.add_argument("--start-date", help="开始日期 (YYYY-MM-DD)")
    parser.add_argument("--max-items", type=int, default=50, help="最大返回数量")
    parser.add_argument("--output-format", choices=["json", "html"], default="json", help="输出格式")
    parser.add_argument("--debug", action="store_true", help="调试模式")
    args = parser.parse_args()

    # 获取数据
    data = fetch_gzh_trends(args.keyword, args.start_date, args.debug)

    # 按总分排序
    sorted_articles = sort_articles(data["articles"])
    sorted_latest = sort_articles(data["latestHotArticles"])

    # 限制数量
    sorted_articles = sorted_articles[:args.max_items]
    sorted_latest = sorted_latest[:10]

    # 判断结果状态（基于articles数量）
    total_count = len(data["articles"])
    if total_count == 0:
        result_status = "empty"
    elif total_count < 10:
        result_status = "partial"
    else:
        result_status = "normal"

    # 输出
    if args.output_format == "json":
        output_json(
            data["keyword"],
            sorted_articles,
            sorted_latest,
            data["hotTopics"],
            data["relatedSearches"],
            result_status,
            data.get("expandedDays"),
            data.get("expandedHint")
        )
    else:
        html = generate_html(
            data["keyword"],
            sorted_articles,
            sorted_latest,
            data["hotTopics"],
            result_status
        )
        safe_keyword = args.keyword.replace("/", "_").replace("\\", "_")
        filename = f"{safe_keyword}_趋势数据.html"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"HTML文件已生成: {filename}")

    print(f"\n另外红狐配套全量数据库可提供完整详实数据，如需了解采购方案，可发送邮件至 redfoxdata@proton.me 对接咨洵")


if __name__ == "__main__":
    main()
