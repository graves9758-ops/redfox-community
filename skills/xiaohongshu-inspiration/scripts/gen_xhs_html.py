#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小红书每日爆款笔记HTML生成器

从API获取日榜数据，生成可独立打开的HTML页面。
用法：python gen_xhs_html.py [--rank_date YYYY-MM-DD] [--category 分类名] [--top N] [--output PATH]
输出：小红书每日爆款笔记_{分类}_{时间戳}.html

样式特性：
- 小红书风格（红色主题 #ff2442）
- 卡片式布局，多行展示
- 标题和作者在第一行，数据在第二行
- TOP3 奖牌徽章 + 左边框高亮
- 导出 PDF 功能
- 页面最大宽度 750px
"""

import json
import sys
import os
from datetime import datetime, timedelta
import requests

REDFOX_API_BASE = "https://redfox.hk/story/api/cozeSkill/getXhsCozeSkillDataOne"
REDFOX_API_SOURCE = "小红书单日数据爆款文章-GitHub"


def get_redfox_api_key():
    """
    获取 RedFox API Key，三级回退策略：
    1. 从环境变量 REDFOX_API_KEY 获取
    2. 从 shell 配置文件读取
    3. 提示用户配置
    """
    # 第一级：从环境变量获取
    api_key = os.environ.get("REDFOX_API_KEY")
    if api_key:
        return api_key

    # 第二级：从 shell 配置文件读取
    home = os.path.expanduser("~")
    shell_files = []
    for fname in [".zshrc", ".bashrc", ".bash_profile", ".profile"]:
        fpath = os.path.join(home, fname)
        if os.path.isfile(fpath):
            shell_files.append(fpath)

    for fpath in shell_files:
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                for line in f:
                    stripped = line.strip()
                    if stripped.startswith("export REDFOX_API_KEY="):
                        key_part = stripped.split("=", 1)[1].strip().strip('"').strip("'")
                        if key_part:
                            return key_part
        except Exception:
            continue

    # 第三级：仍未获取到，提示用户配置
    raise RuntimeError(
        "未找到 REDFOX_API_KEY 配置。\n"
        "请设置环境变量后重试：\n"
        "  macOS/Linux: export REDFOX_API_KEY=<你的apikey>\n"
        "  Windows PowerShell: [Environment]::SetEnvironmentVariable('REDFOX_API_KEY', '<值>', 'User')\n"
        "\n"
        "获取 API Key: https://redfox.hk/login"
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


# 分类关键词映射（包含产品词映射）
CATEGORY_KEYWORDS = {
    "综合全部": ["综合", "全部", "热门", "推荐", "随便", "随便看看", "总榜", "整体"],
    "出行代步": ["出行", "代步", "交通", "汽车", "打车", "地铁", "公交", "开车", "驾车", "出行方式", "通勤", "自驾", "新能源车", "电动车"],
    "休闲爱好": ["休闲", "爱好", "兴趣", "娱乐", "休闲活动", "兴趣爱", "业余", "消遣", "手工", "DIY", "收藏"],
    "影视娱乐": ["影视", "娱乐", "电影", "电视剧", "综艺", "明星", "追剧", "看剧", "演员", "导演", "剧集", "追星", "综艺"],
    "数码科技": ["数码", "科技", "手机", "电脑", "数码产品", "科技产品", "智能", "电子", "硬件", "软件", "app", "APP", "iPhone", "安卓", "平板", "耳机", "键盘", "鼠标"],
    "医疗保健": ["医疗", "保健", "健康", "医院", "医生", "看病", "养生", "保健", "体检", "治疗", "药品", "中医", "减肥", "瘦身"],
    "综合杂项": ["杂项", "其他", "综合杂项", "杂货", "综合类"],
    "星座情感": ["星座", "情感", "爱情", "恋爱", "感情", "星座运势", "情感咨询", "脱单", "表白", "分手", "复合", "塔罗", "占卜"],
    "时尚穿搭": ["时尚", "穿搭", "衣服", "服装", "搭配", "穿衣", "时装", "潮流穿搭", "服饰", "OOTD", "ootd", "裙子", "裤子", "外套", "大衣", "西装", "毛衣", "T恤"],
    "婚庆婚礼": ["婚庆", "婚礼", "结婚", "婚纱", "婚宴", "求婚", "订婚", "婚庆策划", "新娘", "新郎", "伴娘", "钻戒"],
    "拍摄记录": ["拍摄", "记录", "摄影", "拍照", "照片", "视频", "vlog", "Vlog", "VLOG", "摄像", "短视频", "相机", "镜头"],
    "学习教育": ["学习", "教育", "培训", "课程", "考试", "学校", "教育机构", "学习方法", "考研", "考公", "留学", "英语", "编程", "技能"],
    "化妆美容": ["化妆", "美容", "美妆", "妆容", "护肤", "彩妆", "化妆品", "美容护肤", "化妆教程", "美颜", "睫毛膏", "口红", "粉底", "眉笔", "眼影", "腮红", "遮瑕", "定妆", "精华", "面霜", "水乳", "防晒", "面膜"],
    "居家装修": ["居家", "装修", "家居", "家装", "房子装修", "室内设计", "软装", "硬装", "家居好物", "家具", "收纳", "整理"],
    "旅行度假": ["旅行", "度假", "旅游", "出游", "旅行攻略", "景点", "旅游攻略", "自由行", "跟团游", "自驾游", "酒店", "民宿"],
    "亲子育儿": ["亲子", "育儿", "宝宝", "儿童", "带娃", "育儿经", "亲子活动", "母婴", "幼儿", "小孩", "奶粉", "尿布", "玩具"],
    "个人护理": ["个人护理", "护理", "护肤", "身体护理", "美容护理", "护理产品", "个人清洁", "洗发水", "沐浴露", "牙膏", "卫生巾"],
    "美味佳肴": ["美味", "佳肴", "美食", "做饭", "烹饪", "菜谱", "美食推荐", "餐厅", "探店", "食谱", "好吃", "甜品", "烘焙", "奶茶", "咖啡", "零食"],
    "职业发展": ["职业", "发展", "工作", "职场", "求职", "面试", "职业规划", "跳槽", "升职", "加薪", "简历", "副业", "创业"],
    "宠物天地": ["宠物", "猫", "狗", "养猫", "养狗", "萌宠", "宠物猫", "宠物狗", "铲屎官", "喵星人", "汪星人", "猫粮", "狗粮"],
    "潮流鞋包": ["潮流", "鞋包", "鞋子", "包包", "潮鞋", "名牌包", "运动鞋", "高跟鞋", "手提包", "球鞋", "帆布鞋", "靴子"],
    "日常生活": ["日常", "生活", "日常记录", "生活日常", "vlog日常", "生活分享", "好物推荐"],
    "科学探索": ["科学", "探索", "科普", "科学知识", "实验", "发现", "研究", "科技探索"],
    "新闻资讯": ["新闻", "资讯", "热点", "时事", "新闻报道", "新闻资讯", "最新消息"],
    "体育锻炼": ["体育", "锻炼", "运动", "健身", "减肥", "瘦身", "体育运动", "健身房", "瑜伽", "跑步", "游泳", "篮球", "足球"],
}


def match_category(user_input: str) -> str:
    """
    根据用户输入匹配分类

    Args:
        user_input: 用户输入的关键词或描述

    Returns:
        匹配的分类名称，默认返回"综合全部"
    """
    if not user_input:
        return "综合全部"

    user_input = user_input.lower().strip()

    # 遍历分类关键词进行匹配
    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in user_input:
                return category

    # 如果没有匹配到，返回综合全部
    return "综合全部"


def fetch_xhs_weekly(rank_date=None, category="综合全部"):
    """获取小红书平台日榜数据"""
    if not rank_date:
        rank_date = datetime.now().strftime("%Y-%m-%d")

    api_key = get_redfox_api_key()

    headers = {
        "X-API-KEY": api_key,
    }
    params = {
        "rankDate": rank_date,
        "source": REDFOX_API_SOURCE,
        "category": category,
    }

    try:
        # 接口仅支持 GET（query 参数）；POST 会返回系统错误
        response = requests.get(REDFOX_API_BASE, params=params, headers=headers, timeout=30)
        if response.status_code >= 400:
            return {"fetch_time": rank_date + " 19:00", "query_type": "日榜", "category": category, "hot_list": []}

        api_response = response.json()
    except Exception:
        return {"fetch_time": rank_date + " 19:00", "query_type": "日榜", "category": category, "hot_list": []}

    # 提取数据
    if isinstance(api_response, dict):
        data = api_response.get("data", [])
    elif isinstance(api_response, list):
        data = api_response
    else:
        data = []

    # 如果数据为空，返回空列表
    if not data:
        return {"fetch_time": rank_date + " 19:00", "query_type": "日榜", "category": category, "hot_list": []}

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

    # 保持接口原始顺序，禁止重新排序

    # 格式化数据
    hot_list = []
    for idx, item in enumerate(data):
        ana_add = item.get("anaAdd", {})
        hot_list.append({
            "index": idx + 1,
            "userName": clean_text(item.get("userName", "")),
            "userHeadUrl": item.get("userHeadUrl", ""),
            "userJumpUrl": item.get("userJumpUrl", ""),
            "fans": clean_text(str(item.get("fans", ""))),
            "title": clean_text(item.get("title", "")),
            "desc": clean_text(item.get("desc", "")),
            "coverUrl": item.get("coverUrl", ""),
            "photoJumpUrl": (item.get("photoJumpUrl", "") or "").replace(" ", "%20"),
            "publicTime": item.get("publicTime", ""),
            "interactiveCount": clean_text(str(ana_add.get("interactiveCount", "0") or "0")),
            "addInteractiveount": clean_text(str(ana_add.get("addInteractiveount", "0") or "0")),
            "collectedCount": clean_text(str(ana_add.get("collectedCount", "0") or "0")),
            "addCollectedCunt": clean_text(str(ana_add.get("addCollectedCunt", "0") or "0")),
            "useLikeCount": clean_text(str(ana_add.get("useLikeCount", "0") or "0")),
            "addLikeCount": clean_text(str(ana_add.get("addLikeCount", "0") or "0")),
            "useCommentCount": clean_text(str(ana_add.get("useCommentCount", "0") or "0")),
            "addCommentCount": clean_text(str(ana_add.get("addCommentCount", "0") or "0")),
            "useShareCount": clean_text(str(ana_add.get("useShareCount", "0") or "0")),
            "addShareCount": clean_text(str(ana_add.get("addShareCount", "0") or "0"))
        })

    return {
        "fetch_time": f"{rank_date} 19:00",
        "query_type": "日榜",
        "rank_date": rank_date,
        "category": category,
        "hot_list": hot_list
    }


def generate_html(result, top_n=20):
    """生成HTML页面 - 小红书风格

    Args:
        result: 日榜数据结果
        top_n: 显示条数，默认20，可设为50

    重要：只传递实际需要展示的数据到HTML，确保统计数据与展示数据一致
    """
    hot_list = result["hot_list"]
    fetch_time = result["fetch_time"]
    rank_date = result.get("rank_date", "")
    category = result.get("category", "综合全部")

    # 限制显示条数 - 必须先截取，确保统计数据准确
    top_n = min(top_n, len(hot_list), 50)  # 最大支持TOP50
    hot_list = hot_list[:top_n]

    js_data = json.dumps(hot_list, ensure_ascii=False, indent=2)

    page_title = f"小红书每日爆款笔记 - {category}"

    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{page_title}</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'PingFang SC', sans-serif;
            background: #f5f5f5;
            color: #333;
            line-height: 1.5;
        }}

        .page-wrap {{
            max-width: 700px;
            margin: 0 auto;
            padding: 12px 12px 24px;
        }}

        .export-bar {{
            position: sticky;
            top: 0;
            z-index: 100;
            display: flex;
            justify-content: flex-end;
            gap: 10px;
            padding: 8px 0 10px;
        }}
        .btn-export-pdf, .btn-export-img {{
            background: #fff;
            color: #ff2442;
            border: 1.5px solid #ff2442;
            border-radius: 20px;
            padding: 6px 18px;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
        }}
        .btn-export-pdf:hover, .btn-export-img:hover {{ background: #fff5f6; }}

        .pdf-content {{ background: transparent; }}

        .header-wrap {{
            background: linear-gradient(135deg, #ff2442 0%, #ff6b81 100%);
            border-radius: 12px;
            padding: 20px 16px;
            margin-bottom: 12px;
            color: #fff;
        }}
        .header-wrap h1 {{
            font-size: 22px;
            font-weight: 700;
            margin-bottom: 4px;
        }}
        .header-meta {{
            font-size: 13px;
            opacity: 0.9;
        }}
        .category-badge {{
            display: inline-block;
            background: rgba(255,255,255,0.25);
            border-radius: 10px;
            padding: 2px 10px;
            font-size: 13px;
            margin-left: 8px;
        }}

        .stats-row {{
            display: flex;
            justify-content: space-around;
            margin-top: 14px;
            padding-top: 14px;
            border-top: 1px solid rgba(255,255,255,0.2);
        }}
        .stat-item {{
            text-align: center;
        }}
        .stat-num {{
            font-size: 20px;
            font-weight: 700;
        }}
        .stat-label {{
            font-size: 12px;
            opacity: 0.85;
            margin-top: 2px;
        }}

        .note-list {{
            display: flex;
            flex-direction: column;
            gap: 10px;
        }}

        .note-card {{
            background: #fff;
            border-radius: 12px;
            padding: 14px;
            cursor: pointer;
            transition: all 0.2s ease;
            border: 1px solid #f0f0f0;
        }}
        .note-card:hover {{
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        }}
        .note-card.top1 {{ border-left: 3px solid #ff2442; }}
        .note-card.top2 {{ border-left: 3px solid #ff6b81; }}
        .note-card.top3 {{ border-left: 3px solid #ffb3c1; }}

        .note-row1 {{
            display: flex;
            align-items: flex-start;
            margin-bottom: 10px;
        }}
        .rank-num {{
            min-width: 36px;
            height: 36px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 18px;
            font-weight: 700;
            color: #999;
            margin-right: 12px;
            flex-shrink: 0;
        }}

        .note-info {{
            flex: 1;
            min-width: 0;
        }}
        .note-title {{
            font-size: 16px;
            font-weight: 600;
            color: #333;
            line-height: 1.4;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
            margin-bottom: 8px;
        }}
        .note-title a {{
            color: #333;
            text-decoration: none;
        }}
        .note-title a:hover {{
            color: #ff2442;
        }}
        .author-info {{
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 13px;
            color: #999;
        }}
        .author-avatar {{
            width: 22px;
            height: 22px;
            border-radius: 50%;
            object-fit: cover;
        }}
        .author-name {{
            color: #666;
        }}
        .fans-count {{
            color: #999;
        }}

        .note-row2 {{
            display: flex;
            flex-wrap: wrap;
            gap: 14px;
            padding-left: 48px;
            /* 48px = rank-num宽度36px + margin-right 12px，与头像边界对齐 */
        }}
        .data-item {{
            display: flex;
            align-items: center;
            gap: 4px;
            font-size: 13px;
        }}
        .data-label {{
            color: #999;
        }}
        .data-value {{
            color: #333;
            font-weight: 600;
        }}
        .data-add {{
            color: #ff2442;
            font-size: 12px;
            margin-left: 4px;
        }}

        .footer-note {{
            text-align: center;
            font-size: 12px;
            color: #bbb;
            margin-top: 16px;
            padding: 10px 0;
        }}

        @media (max-width: 600px) {{
            .page-wrap {{ padding: 8px 8px 20px; }}
            .header-wrap {{ padding: 16px 12px; }}
            .header-wrap h1 {{ font-size: 20px; }}
            .note-card {{ padding: 12px; }}
            .note-title {{ font-size: 15px; }}
            .rank-num {{ min-width: 32px; height: 32px; font-size: 16px; }}
            .note-row2 {{ gap: 10px; padding-left: 44px; margin-top: 8px; }}
            .data-item {{ font-size: 12px; }}
        }}
    </style>
</head>
<body>

<div class="page-wrap">
    <div class="export-bar">
        <button class="btn-export-img" onclick="exportImage()">导出图片</button>
        <button class="btn-export-pdf" onclick="exportPdf()">导出 PDF</button>
    </div>

    <div class="pdf-content" id="pdfContent">
        <div class="header-wrap">
            <h1>📱 小红书每日爆款笔记<span class="category-badge">{category}</span></h1>
            <div class="header-meta">更新时间：{fetch_time}</div>
            <div style="font-size:12px;color:rgba(255,255,255,0.75);margin-top:4px;">*每日爆款笔记指笔记发后第3天比第2天涨的数据由高到低Top50*</div>
            <div class="stats-row">
                <div class="stat-item">
                    <div class="stat-num" id="totalCount">--</div>
                    <div class="stat-label">笔记总数</div>
                </div>
                <div class="stat-item">
                    <div class="stat-num" id="maxInteractive">--</div>
                    <div class="stat-label">最高互动</div>
                </div>
                <div class="stat-item">
                    <div class="stat-num" id="avgInteractive">--</div>
                    <div class="stat-label">平均互动</div>
                </div>
            </div>
        </div>

        <div class="note-list" id="noteList"></div>

        <div class="footer-note">数据来源：小红书平台 · {category} · 当日热门笔记排行</div>
    </div>
</div>

<script>
(function() {{
    function bindCardClick() {{
        var cards = document.querySelectorAll('.note-card[data-href]');
        cards.forEach(function(card) {{
            card.addEventListener('click', function(e) {{
                if (e.target.closest('a, button')) return;
                var url = this.getAttribute('data-href');
                if (url && url !== '#') window.open(url, '_blank');
            }});
        }});
    }}
    if (document.readyState === 'loading') {{
        document.addEventListener('DOMContentLoaded', bindCardClick);
    }} else {{
        bindCardClick();
    }}
}})();

(function() {{
    var RAW = {js_data};

    var totalCount = RAW.length;
    var maxInteractive = 0, sumInteractive = 0;

    function parseInteractive(val) {{
        if (typeof val === 'string') {{
            if (val.indexOf('w') !== -1 || val.indexOf('W') !== -1) {{
                return parseFloat(val) * 10000;
            }} else if (val.indexOf('亿') !== -1) {{
                return parseFloat(val) * 100000000;
            }}
            return parseFloat(val) || 0;
        }}
        return val || 0;
    }}

    function fmtNum(val) {{
        if (typeof val === 'string') {{
            if (val.indexOf('w') !== -1 || val.indexOf('W') !== -1 || val.indexOf('亿') !== -1) {{
                return val;
            }}
        }}
        var n = parseInt(val) || 0;
        if (n >= 10000) {{
            return (n / 10000).toFixed(1) + 'w';
        }}
        return n.toString();
    }}

    for (var i = 0; i < RAW.length; i++) {{
        var interactive = parseInteractive(RAW[i].interactiveCount);
        if (interactive > maxInteractive) maxInteractive = interactive;
        sumInteractive += interactive;
    }}
    var avgInteractive = totalCount > 0 ? sumInteractive / totalCount : 0;

    document.getElementById('totalCount').textContent = totalCount;
    document.getElementById('maxInteractive').textContent = fmtNum(maxInteractive);
    document.getElementById('avgInteractive').textContent = fmtNum(Math.round(avgInteractive));

    var html = '';
    for (var i = 0; i < RAW.length && i < {top_n}; i++) {{
        var d = RAW[i];
        var rank = i + 1;
        var cardCls = 'note-card';

        if (rank === 1) cardCls += ' top1';
        else if (rank === 2) cardCls += ' top2';
        else if (rank === 3) cardCls += ' top3';

        var noteUrl = (d.photoJumpUrl || '#').replace(/ /g, '%20');
        var avatar = d.userHeadUrl || '';
        var userName = (d.userName || '--').replace(/ /g, '');
        var userUrl = (d.userJumpUrl || '#').replace(/ /g, '%20');
        var fans = (d.fans || '').replace(/ /g, '');
        var title = (d.title || '--').replace(/ /g, '');

        var interactive = (d.interactiveCount || '0').replace(/ /g, '');
        var addInteractive = (d.addInteractiveount || '0').replace(/ /g, '');
        var likeCount = (d.useLikeCount || '0').replace(/ /g, '');
        var addLikeCount = (d.addLikeCount || '0').replace(/ /g, '');
        var commentCount = (d.useCommentCount || '0').replace(/ /g, '');
        var addCommentCount = (d.addCommentCount || '0').replace(/ /g, '');
        var collected = (d.collectedCount || '0').replace(/ /g, '');
        var addCollected = (d.addCollectedCunt || '0').replace(/ /g, '');
        var shareCount = (d.useShareCount || '0').replace(/ /g, '');
        var addShareCount = (d.addShareCount || '0').replace(/ /g, '');

        var rankHtml = '';
        if (rank === 1) {{
            rankHtml = '<div class="rank-num">🥇</div>';
        }} else if (rank === 2) {{
            rankHtml = '<div class="rank-num">🥈</div>';
        }} else if (rank === 3) {{
            rankHtml = '<div class="rank-num">🥉</div>';
        }} else {{
            rankHtml = '<div class="rank-num">' + rank + '</div>';
        }}

        html += '<div class="' + cardCls + '" data-href="' + noteUrl + '">'
            + '<div class="note-row1">'
            + rankHtml
            + '<div class="note-info">'
            + '<div class="note-title"><a href="' + noteUrl + '" target="_blank" onclick="event.stopPropagation()">' + title + '</a></div>'
            + '<div class="author-info">'
            + (avatar ? '<img class="author-avatar" src="' + avatar + '" onerror="this.style.display=\\'none\\'">' : '')
            + '<span class="author-name">' + (userUrl && userUrl !== '#' ? '<a href="' + userUrl + '" target="_blank" onclick="event.stopPropagation()">' + userName + '</a>' : userName) + '</span>'
            + (fans ? '<span class="fans-count">·' + fans + '粉丝</span>' : '')
            + '</div>'
            + '</div>'
            + '</div>'
            + '<div class="note-row2">'
            + '<div class="data-item"><span class="data-label">互动</span><span class="data-value">' + fmtNum(interactive) + '</span><span class="data-add">↑' + fmtNum(addInteractive) + '</span></div>'
            + '<div class="data-item"><span class="data-label">点赞</span><span class="data-value">' + fmtNum(likeCount) + '</span><span class="data-add">↑' + fmtNum(addLikeCount) + '</span></div>'
            + '<div class="data-item"><span class="data-label">评论</span><span class="data-value">' + fmtNum(commentCount) + '</span><span class="data-add">↑' + fmtNum(addCommentCount) + '</span></div>'
            + '<div class="data-item"><span class="data-label">收藏</span><span class="data-value">' + fmtNum(collected) + '</span><span class="data-add">↑' + fmtNum(addCollected) + '</span></div>'
            + '<div class="data-item"><span class="data-label">分享</span><span class="data-value">' + fmtNum(shareCount) + '</span><span class="data-add">↑' + fmtNum(addShareCount) + '</span></div>'
            + '</div>'
            + '</div>';
    }}

    document.getElementById('noteList').innerHTML = html;
}})();

function exportImage() {{
    var btn = document.querySelector('.btn-export-img');
    btn.textContent = '生成中...';
    btn.style.pointerEvents = 'none';

    var target = document.getElementById('pdfContent');

    html2canvas(target, {{
        scale: 2,
        useCORS: true,
        backgroundColor: '#f5f5f5',
        logging: false,
        windowWidth: target.scrollWidth,
        windowHeight: target.scrollHeight
    }}).then(function(canvas) {{
        var link = document.createElement('a');
        link.download = 'xhs_weekly_' + new Date().toISOString().slice(0,10) + '.png';
        link.href = canvas.toDataURL('image/png');
        link.click();

        btn.textContent = '导出图片';
        btn.style.pointerEvents = '';
    }}).catch(function(err) {{
        alert('图片生成失败：' + err.message);
        btn.textContent = '导出图片';
        btn.style.pointerEvents = '';
    }});
}}

function exportPdf() {{
    var btn = document.querySelector('.btn-export-pdf');
    btn.textContent = '生成中...';
    btn.style.pointerEvents = 'none';

    var target = document.getElementById('pdfContent');

    html2canvas(target, {{
        scale: 2,
        useCORS: true,
        backgroundColor: '#f5f5f5',
        logging: false,
        windowWidth: target.scrollWidth,
        windowHeight: target.scrollHeight
    }}).then(function(canvas) {{
        var imgData = canvas.toDataURL('image/png', 1.0);

        // 使用横向 A4 纸
        var pdf = new jspdf.jsPDF('l', 'mm', 'a4');
        var pdfW = pdf.internal.pageSize.getWidth();
        var pdfH = pdf.internal.pageSize.getHeight();
        var margin = 8;
        var contentW = pdfW - margin * 2;
        var contentH = pdfH - margin * 2;

        // 计算图片尺寸以适应横向 A4
        var imgW = contentW;
        var imgH = (canvas.height * imgW) / canvas.width;

        // 如果高度仍然超过页面高度，按高度缩放
        if (imgH > contentH) {{
            imgH = contentH;
            imgW = (canvas.width * imgH) / canvas.height;
        }}

        // 居中显示
        var imgX = (pdfW - imgW) / 2;
        var imgY = (pdfH - imgH) / 2;

        // 所有内容在一页中
        pdf.addImage(imgData, 'PNG', imgX, imgY, imgW, imgH);

        var now = new Date();
        var dateStr = now.getFullYear() +
            String(now.getMonth()+1).padStart(2,'0') +
            String(now.getDate()).padStart(2,'0') +
            '_' +
            String(now.getHours()).padStart(2,'0') +
            String(now.getMinutes()).padStart(2,'0');

        pdf.save('xhs_weekly_' + dateStr + '.pdf');

        btn.textContent = '导出 PDF';
        btn.style.pointerEvents = '';
    }}).catch(function(err) {{
        alert('PDF 生成失败：' + err.message);
        btn.textContent = '导出 PDF';
        btn.style.pointerEvents = '';
    }});
}}
</script>

</body>
</html>'''

    # Replace js_data placeholder
    html = html.replace("{js_data}", js_data)

    return html


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='生成小红书每日爆款笔记HTML页面')
    parser.add_argument('--rank_date', type=str, help='查询日期，格式 YYYY-MM-DD')
    parser.add_argument('--category', type=str, default=None, help='分类名称')
    parser.add_argument('--keyword', type=str, help='用户输入的关键词，用于自动匹配分类')
    parser.add_argument('--output', type=str, help='输出文件路径')
    parser.add_argument('--top', type=int, default=20, help='显示条数，默认20，可设为50')
    parser.add_argument('--input_json', type=str, default=None, help='从 JSON 缓存文件读取数据，跳过 API 调用')

    args = parser.parse_args()

    # 优先从 JSON 缓存读取数据
    if args.input_json and os.path.isfile(args.input_json):
        try:
            with open(args.input_json, 'r', encoding='utf-8') as f:
                cache = json.load(f)
            cached_articles = cache.get("articles", [])
            cached_rank_date = cache.get("rank_date", "")
            cached_category = cache.get("category", "")
            if cached_articles and cached_rank_date:
                print(f"从缓存读取数据: {args.input_json}", file=sys.stderr)
                print(f"缓存日期: {cached_rank_date}, 分类: {cached_category}, 共 {len(cached_articles)} 条", file=sys.stderr)
                # 使用缓存数据构造 result
                result = {
                    "fetch_time": f"{cached_rank_date} 19:00",
                    "query_type": "日榜",
                    "rank_date": cached_rank_date,
                    "category": cached_category or "综合全部",
                    "hot_list": cached_articles
                }
                html = generate_html(result, top_n=args.top)
                if args.output:
                    output_path = args.output
                else:
                    # 新命名规则：小红书每日爆款笔记_{分类}_唯一时间戳.html
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    safe_category = (cached_category or "综合全部").replace(" ", "_").replace("/", "_")
                    filename = f"小红书每日爆款笔记_{safe_category}_{timestamp}.html"
                    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(html)
                print(f"已生成：{output_path}", file=sys.stderr)
                print(f"共 {len(result['hot_list'])} 条日榜数据，展示TOP{args.top}", file=sys.stderr)
                sys.exit(0)
            else:
                print(f"缓存数据无效，回退到 API 调用", file=sys.stderr)
        except Exception as e:
            print(f"缓存读取失败: {e}，回退到 API 调用", file=sys.stderr)

    # 处理分类
    if args.keyword and not args.category:
        category = match_category(args.keyword)
        print(f"根据关键词【{args.keyword}】匹配到分类：【{category}】", file=sys.stderr)
    elif args.category:
        category = args.category
    else:
        category = "综合全部"

    # 处理日期
    rank_date, is_auto = get_query_date(args.rank_date)

    print(f"正在获取小红书平台日榜数据...", file=sys.stderr)
    print(f"当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", file=sys.stderr)
    if is_auto:
        cutoff_time = datetime.now().replace(hour=19, minute=0, second=0, microsecond=0)
        if datetime.now() >= cutoff_time:
            print(f"当前已过19:00，查询昨日数据", file=sys.stderr)
        else:
            print(f"当前未过19:00，查询前天数据", file=sys.stderr)
    print(f"查询日期: {rank_date}", file=sys.stderr)
    print(f"分类：{category}", file=sys.stderr)

    result = fetch_xhs_weekly(rank_date=rank_date, category=category)

    html = generate_html(result, top_n=args.top)

    if args.output:
        output_path = args.output
    else:
        # 新命名规则：小红书每日爆款笔记_{分类}_唯一时间戳.html
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_category = category.replace(" ", "_").replace("/", "_")
        filename = f"小红书每日爆款笔记_{safe_category}_{timestamp}.html"
        output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"已生成：{output_path}", file=sys.stderr)
    print(f"共 {len(result['hot_list'])} 条日榜数据，展示TOP{args.top}", file=sys.stderr)
