#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
公众号10w+热门文章HTML生成脚本

功能：
1. 读取API数据
2. 生成公众号风格的HTML页面
3. 支持PDF导出

使用方法：
python generate_hot_html.py --data_file data.json --output ranking.html
python generate_hot_html.py --articles '[{"title": "...", ...}]' --output ranking.html
"""

import argparse
import json
import os
from datetime import datetime


def get_rank_display(rank: int) -> str:
    """获取排名显示（奖牌或数字）"""
    if rank == 1:
        return "🥇"
    elif rank == 2:
        return "🥈"
    elif rank == 3:
        return "🥉"
    else:
        return str(rank)


def get_article_html(article: dict, rank: int, is_top: bool = False) -> str:
    """生成单篇文章的HTML"""
    try:
        title = article.get("title", "未知标题")
        url = article.get("oriUrl", "#")
        account = article.get("userName", article.get("accountId", "未知账号"))
        account_id = article.get("accountId", "")
        reads = article.get("clicksCount", "0")
        
        # 处理日期
        public_time = article.get("publicTime", "")
        if public_time:
            try:
                date = str(public_time)[:10]
            except:
                date = ""
        else:
            date = ""

        # 生成公众号名片链接
        if account_id:
            account_url = f"https://open.weixin.qq.com/qr/code?username={account_id}"
        else:
            account_url = "#"

        top_class = " top-item" if is_top else ""
        rank_display = get_rank_display(rank)
        top_rank_class = " top" if is_top else ""

        return f'''
                    <li class="article-item{top_class}">
                        <div class="article-body">
                            <div class="article-rank{top_rank_class}">{rank_display}</div>
                            <div class="article-content">
                                <a href="{url}" target="_blank" class="article-title">{title}</a>
                                <div class="article-info">
                                    <span class="info-item"><a href="{account_url}" target="_blank" class="info-source-link"><span class="info-source-icon">👤</span>{account}</a></span>
                                    <span class="info-item"><span class="info-stat">📖 阅读 <span class="info-stat-value">{reads}</span></span></span>
                                    <span class="info-item"><span class="info-stat">📅 {date}</span></span>
                                </div>
                            </div>
                        </div>
                    </li>'''
    except:
        # 如果生成失败，返回空字符串
        return ""


def generate_html(keyword: str, articles: list, insights: dict = None, top_n: int = 10) -> str:
    """生成完整的HTML页面"""
    # 数据验证
    if not articles:
        articles = []
    
    # 计算统计数据
    try:
        account_count = len(set(a.get("accountId", "") for a in articles if a.get("accountId")))
    except:
        account_count = 0

    # 计算日期范围
    dates = []
    for a in articles:
        try:
            public_time = a.get("publicTime", "")
            if public_time:
                date_str = str(public_time)[:10]  # 只取日期部分
                if date_str and len(date_str) >= 10:  # 确保日期格式正确
                    dates.append(date_str)
        except:
            continue
    
    if dates:
        try:
            min_date = min(datetime.strptime(d, "%Y-%m-%d") for d in dates if d)
            max_date = max(datetime.strptime(d, "%Y-%m-%d") for d in dates if d)
            days = (max_date - min_date).days + 1
        except:
            days = 30
    else:
        days = 30

    # 生成文章列表HTML
    articles_html = ""
    for i, article in enumerate(articles[:top_n], 1):
        try:
            articles_html += get_article_html(article, i, i <= 3)
        except:
            # 如果单篇文章生成失败，跳过
            continue

    # 完整的HTML模板
    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{keyword} · 公众号10w+阅读文章</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
            background: #f5f5f5;
            color: #333;
            line-height: 1.8;
            padding: 12px;
        }}

        .container {{
            max-width: 680px;
            margin: 0 auto;
            background: #fff;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
            overflow: hidden;
        }}

        .brand-header {{
            background: linear-gradient(135deg, #fff 0%, #f8fff8 100%);
            padding: 32px 24px 28px;
            text-align: center;
            border-bottom: 1px solid #eee;
        }}

        .brand-title {{
            font-size: 26px;
            font-weight: 700;
            color: #1a1a1a;
            margin-bottom: 8px;
            letter-spacing: 1px;
        }}

        .brand-subtitle {{
            font-size: 14px;
            color: #888;
        }}

        .export-btn {{
            display: inline-flex;
            align-items: center;
            gap: 4px;
            background: linear-gradient(135deg, #0088ff, #0066cc);
            color: #fff;
            border: none;
            padding: 5px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 2px 8px rgba(0, 136, 255, 0.3);
        }}

        .export-btn:hover {{
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(0, 136, 255, 0.4);
        }}

        .brand-stats {{
            display: flex;
            justify-content: center;
            gap: 32px;
            margin-top: 24px;
            padding-top: 20px;
            border-top: 1px dashed #e5e5e5;
        }}

        .brand-stat {{
            text-align: center;
        }}

        .brand-stat-num {{
            font-size: 24px;
            font-weight: 700;
            color: rgb(0, 179, 84);
        }}

        .brand-stat-label {{
            font-size: 12px;
            color: #999;
            margin-top: 4px;
        }}

        .content {{
            padding: 24px 20px;
        }}

        .section-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 20px;
            gap: 12px;
        }}

        .section-header .export-btn {{
            font-size: 12px;
            padding: 5px 12px;
        }}

        .section-right {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}

        .section-title {{
            font-size: 18px;
            font-weight: 600;
            color: #1a1a1a;
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        .section-title::before {{
            content: "";
            width: 4px;
            height: 20px;
            background: rgb(0, 179, 84);
            border-radius: 2px;
        }}

        .section-badge {{
            background: rgba(0, 179, 84, 0.1);
            color: rgb(0, 179, 84);
            font-size: 12px;
            padding: 4px 12px;
            border-radius: 12px;
            font-weight: 500;
        }}

        .article-list {{
            list-style: none;
        }}

        .article-item {{
            background: #fff;
            border: 1px solid #eee;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 16px;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }}

        .article-item:hover {{
            border-color: rgb(0, 179, 84);
            box-shadow: 0 4px 16px rgba(0, 179, 84, 0.12);
            transform: translateY(-2px);
        }}

        .article-item:last-child {{
            margin-bottom: 0;
        }}

        .article-item.top-item {{
            background: linear-gradient(135deg, #fff 0%, #f8fff8 100%);
            border-color: rgba(0, 179, 84, 0.3);
        }}

        .article-item.top-item::before {{
            content: "";
            position: absolute;
            top: 0;
            left: 0;
            width: 4px;
            height: 100%;
            background: linear-gradient(180deg, rgb(0, 179, 84), #06a54a);
        }}

        .article-body {{
            display: flex;
            align-items: flex-start;
            gap: 14px;
        }}

        .article-rank {{
            width: 36px;
            height: 36px;
            background: rgb(0, 179, 84);
            color: #fff;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 14px;
            flex-shrink: 0;
        }}

        .article-rank.top {{
            background: linear-gradient(135deg, #ffd700, #ff8c00);
            color: #fff;
            font-size: 22px;
            font-weight: normal;
        }}

        .article-content {{
            flex: 1;
        }}

        .article-title {{
            font-size: 17px;
            font-weight: 600;
            color: #1a1a1a;
            line-height: 1.5;
            text-decoration: none;
            display: block;
            margin-bottom: 12px;
            cursor: pointer;
            transition: color 0.2s;
        }}

        .article-title:hover {{
            color: rgb(0, 179, 84);
        }}

        .article-info {{
            display: flex;
            align-items: center;
            flex-wrap: wrap;
            gap: 0;
            font-size: 14px;
            color: #888;
        }}

        .info-item {{
            padding: 0 12px;
            position: relative;
        }}

        .info-item::before {{
            content: "|";
            position: absolute;
            left: 0;
            top: 50%;
            transform: translateY(-50%);
            color: #e0e0e0;
            font-size: 10px;
        }}

        .info-item:first-child {{
            padding-left: 0;
        }}

        .info-item:first-child::before {{
            display: none;
        }}

        .info-source-link {{
            display: inline-flex;
            align-items: center;
            gap: 4px;
            color: #0088ff;
            text-decoration: none;
            transition: color 0.2s;
        }}

        .info-source-link:hover {{
            text-decoration: underline;
        }}

        .info-source-icon {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-size: 14px;
            vertical-align: middle;
        }}

        .info-category {{
            font-size: 11px;
            color: rgb(0, 179, 84);
            background: rgba(0, 179, 84, 0.1);
            padding: 2px 8px;
            border-radius: 4px;
            font-weight: 500;
        }}

        .info-stat {{
            display: flex;
            align-items: center;
            gap: 4px;
        }}

        .info-stat-value {{
            color: #0088ff;
            font-weight: 600;
        }}

        .footer {{
            background: #fafafa;
            padding: 24px;
            text-align: center;
            border-top: 1px solid #eee;
        }}

        .footer-text {{
            font-size: 13px;
            color: #888;
        }}

        .footer-copy {{
            font-size: 11px;
            color: #bbb;
            margin-top: 8px;
        }}

        @media (max-width: 480px) {{
            body {{
                padding: 0;
            }}

            .container {{
                border-radius: 0;
            }}

            .brand-stats {{
                gap: 20px;
            }}

            .article-info {{
                gap: 8px;
            }}
        }}

        @media print {{
            .export-btn {{
                display: none !important;
            }}
            .container {{
                padding: 15mm !important;
            }}
            .brand-header {{
                padding: 8mm 10mm !important;
                margin-bottom: 8mm !important;
            }}
            .brand-stats {{
                padding: 6mm !important;
                gap: 10px !important;
            }}
            .brand-stat {{
                padding: 4mm 6mm !important;
            }}
            .section-header {{
                padding: 6mm 0 !important;
            }}
            .article-item {{
                padding: 6mm 8mm !important;
                margin-bottom: 4mm !important;
            }}
            .footer {{
                padding: 8mm !important;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="brand-header">
            <h1 class="brand-title">{keyword} · 10w+阅读文章</h1>
            <p class="brand-subtitle">每日推送公众号10w+爆款内容，解析流量密码</p>
            <div class="brand-stats">
                <div class="brand-stat">
                    <div class="brand-stat-num">{top_n}</div>
                    <div class="brand-stat-label">篇爆款文章</div>
                </div>
                <div class="brand-stat">
                    <div class="brand-stat-num">{account_count}</div>
                    <div class="brand-stat-label">个账号</div>
                </div>
                <div class="brand-stat">
                    <div class="brand-stat-num">{days}</div>
                    <div class="brand-stat-label">天内热文</div>
                </div>
            </div>
        </div>

        <div class="content">
            <div class="section-header">
                <h2 class="section-title">TOP{top_n} 爆款文章</h2>
                <div class="section-right">
                    <span class="section-badge">阅读量排序</span>
                    <button class="export-btn" onclick="exportToPDF()">📥 导出PDF</button>
                </div>
            </div>

            <ul class="article-list">
                {articles_html}
            </ul>
        </div>

        <div class="footer">
            <p class="footer-text">公众号10w+阅读文章，每日更新最新爆文内容</p>
            <p class="footer-copy">备注：互动数据为入库快照，实时数据可能持续增长</p>
        </div>
    </div>

    <script>
        function exportToPDF() {{
            const element = document.querySelector('.container');
            const button = document.querySelector('.export-btn');
            button.style.display = 'none';

            // 计算内容高度，决定PDF尺寸
            const contentHeight = element.scrollHeight;
            const contentWidth = element.scrollWidth;
            // 根据内容比例决定纸张尺寸，mm为单位，1mm ≈ 3.78px
            const pdfWidth = Math.max(210, Math.ceil(contentWidth / 3.78) + 20);
            const pdfHeight = Math.max(297, Math.ceil(contentHeight / 3.78) + 20);

            const opt = {{
                margin: 0,
                filename: '{keyword}_爆款内容分析.pdf',
                image: {{ type: 'jpeg', quality: 0.95 }},
                html2canvas: {{
                    scale: 2,
                    useCORS: true,
                    logging: false,
                    scrollX: 0,
                    scrollY: 0
                }},
                jsPDF: {{
                    unit: 'mm',
                    format: [pdfWidth, pdfHeight],
                    orientation: pdfWidth > pdfHeight ? 'landscape' : 'portrait'
                }},
                pagebreak: {{ mode: 'none' }}
            }};

            html2pdf().set(opt).from(element).save().then(() => {{
                button.style.display = 'inline-flex';
            }});
        }}
    </script>
</body>
</html>'''

    return html


def main():
    parser = argparse.ArgumentParser(description="生成公众号10w+热门文章HTML")
    parser.add_argument("--temp_file", default="temp_articles.json", help="临时JSON文件路径")
    parser.add_argument("--output", default="ranking.html", help="输出文件路径")
    parser.add_argument("--display_count", type=int, default=None, help="要展示的文章数量（如果不指定，则展示所有文章）")

    args = parser.parse_args()

    try:
        # 从临时JSON文件读取数据
        try:
            with open(args.temp_file, "r", encoding="utf-8") as f:
                temp_data = json.load(f)
            keyword = temp_data.get("keyword", "热门文章")
            articles = temp_data.get("articles", [])
            if not isinstance(articles, list):
                articles = []
        except FileNotFoundError:
            print(f"错误: 临时文件不存在 - {args.temp_file}", file=sys.stderr)
            return 1
        except json.JSONDecodeError:
            print(f"错误: 临时文件格式错误 - {args.temp_file}", file=sys.stderr)
            return 1
        except Exception as e:
            print(f"错误: 读取临时文件失败 - {str(e)}", file=sys.stderr)
            return 1

        if not articles:
            print(f"错误: 临时文件中没有文章数据", file=sys.stderr)
            return 1

        # 根据display_count参数确定要展示的文章数量
        display_count = args.display_count if args.display_count is not None else len(articles)
        display_articles = articles[:display_count]

        print(f"✅ 从临时文件读取到 {len(articles)} 条文章数据，本次展示 {len(display_articles)} 条")

        # 生成HTML（使用display_articles而不是articles）
        try:
            html_content = generate_html(keyword, display_articles, None, len(display_articles))
        except Exception as e:
            print(f"错误: 生成HTML失败 - {str(e)}", file=sys.stderr)
            return 1

        # 写入文件
        try:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(html_content)
        except Exception as e:
            print(f"错误: 写入文件失败 - {str(e)}", file=sys.stderr)
            return 1

        print(f"✅ HTML文件已生成: {args.output}")
        return 0

    except Exception as e:
        print(f"错误: {str(e)}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
