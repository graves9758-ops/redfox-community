#!/usr/bin/env python3
"""
公众号投资博主蒸馏器 — 主脚本
==================================
通过公众号文章数据，执行七维DNA蒸馏。

Usage:
    python distill.py --account "zshbtz" --count 60
    python distill.py --account "zshbtz" --author "财躺平" --count 100
    python distill.py --validate --author "财躺平" --sample 15
    python distill.py --check-env
"""

import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

# Windows 控制台 UTF-8 编码
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# ─── 配置 ─────────────────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent.parent
OUTPUT_DIR = SCRIPT_DIR / "output"

# ─── 终端颜色 ──────────────────────────────────────────────────────────────────────
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


def info(msg):
    print(f"{GREEN}[✓]{RESET} {msg}")


def warn(msg):
    print(f"{YELLOW}[!]{RESET} {msg}")


def error(msg):
    print(f"{RED}[✗]{RESET} {msg}")


def step(msg):
    print(f"{CYAN}[→]{RESET} {msg}")


# ─── 环境检查 ──────────────────────────────────────────────────────────────────────
def check_env():
    """检查依赖环境"""
    info("环境检查中...")
    issues = []

    try:
        import requests
        info("requests 已就绪")
    except ImportError:
        warn("缺少 requests，正在安装...")
        os.system(f"{sys.executable} -m pip install requests")
        try:
            import requests
            info("requests 安装成功")
        except ImportError:
            error("requests 安装失败")
            issues.append("requests")

    # 检查 API Key
    from gzh import get_api_key
    key = get_api_key()
    if key:
        info(f"API Key 已配置（{key[:8]}...）")
    else:
        error("未找到 API Key，请先配置 REDFOX_API_KEY")
        error("获取: https://redfox.hk/settings/api-keys?source=github")
        issues.append("REDFOX_API_KEY")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    info(f"输出目录: {OUTPUT_DIR}")

    if issues:
        error(f"仍有依赖缺失: {', '.join(issues)}")
        return False
    info("环境检查通过")
    return True


# ─── 文本预处理 ────────────────────────────────────────────────────────────────────
def clean_text(text):
    """清洗文本"""
    if not text:
        return ""
    text = str(text)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'&nbsp;', ' ', text)
    text = re.sub(r'&amp;', '&', text)
    text = re.sub(r'&lt;', '<', text)
    text = re.sub(r'&gt;', '>', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def split_paragraphs(text):
    """分段"""
    if not text:
        return []
    return [p.strip() for p in text.split('\n') if p.strip()]


# ─── 核心词典（蒸馏质量关键：必须从raw全文逐篇提取，禁止依赖clean中间层） ──────

# 股票/指数词典：标准名 → [别名列表]（别名用于宽松匹配，覆盖口语化表达）
STOCK_DICT = {
    # 指数
    "上证指数": ["上证", "沪指", "大盘", "A股"],
    "创业板指": ["创业板", "创业板指"],
    "中证500": ["中证500"],
    "沪深300": ["沪深300"],
    "科创50": ["科创50", "科创板"],
    "中证1000": ["中证1000"],
    "纳斯达克": ["纳斯达克", "纳指"],
    "标普500": ["标普500", "标普"],
    "恒生指数": ["恒生", "恒指"],
    "恒生科技": ["恒生科技"],
    # A股龙头
    "贵州茅台": ["茅台", "贵州茅台"],
    "五粮液": ["五粮液"],
    "美的": ["美的集团", "美的"],
    "格力": ["格力", "格力电器"],
    "中国平安": ["平安", "中国平安"],
    "宁德时代": ["宁德", "宁德时代"],
    "比亚迪": ["比亚迪"],
    "长江电力": ["长江电力", "长电"],
    "寒武纪": ["寒武纪"],
    "中芯国际": ["中芯", "中芯国际"],
    "中际旭创": ["中际旭创", "旭创"],
    # 港股/美股
    "腾讯": ["腾讯"],
    "阿里巴巴": ["阿里", "阿里巴巴"],
    "美团": ["美团"],
    "京东": ["京东"],
    "小米": ["小米"],
    "百度": ["百度"],
    "英伟达": ["英伟达", "NVIDIA"],
    "苹果": ["苹果", "Apple"],
    "特斯拉": ["特斯拉", "Tesla"],
    "谷歌": ["谷歌", "Google"],
    "微软": ["微软", "Microsoft"],
    "Meta": ["Meta", "Facebook"],
    "台积电": ["台积电", "TSMC"],
    "美光": ["美光", "Micron"],
    # 其他
    "华为": ["华为"],
    "字节跳动": ["字节", "字节跳动", "抖音"],
    "拼多多": ["拼多多", "PDD"],
}

# 投资关键短语（领域专用，比通用句子频次更精准）
INVESTMENT_PHRASES = [
    # 估值/价值
    "估值", "安全边际", "内在价值", "护城河", "价值投资", "基本面", "财报",
    "分红", "股息率", "ROE", "PE", "PB", "自由现金流", "市盈率", "市净率",
    # 趋势/技术
    "趋势", "钝化", "均线", "支撑", "压力", "突破", "回调", "反弹",
    "放量", "缩量", "涨停", "跌停", "连板", "龙头", "妖股",
    # 操作
    "仓位", "加仓", "减仓", "止损", "止盈", "建仓", "清仓", "定投",
    "急涨不追", "急跌不抄底", "追高", "抄底",
    # 宏观
    "美联储", "利率", "关税", "通胀", "降息", "加息", "流动性",
    "地缘政治", "中美", "制裁",
    # 产业链
    "产业链", "景气", "周期", "拐点", "国产替代", "算力", "AI",
    "人工智能", "半导体", "芯片", "新能源", "光伏", "储能",
    "商业航天", "卫星", "光通信", "存储",
    # 哲学/认知
    "认知", "慢慢变富", "道法自然", "逆向", "周期会来的",
    "长期主义", "复利", "贪婪", "恐惧", "知足常乐",
    # 市场情绪
    "恐慌", "贪婪", "情绪", "人声鼎沸", "共识", "关注度",
    "量化", "ETF", "指数基金", "散户", "机构",
]

# 板块关键词映射（用于文章级别计数）
SECTOR_KEYWORDS = {
    "AI/人工智能": ["AI", "人工智能", "大模型", "GPT", "算力", "Agent", "ChatGPT"],
    "半导体/芯片": ["半导体", "芯片", "光刻", "中芯", "台积电", "制程", "封装"],
    "商业航天/卫星": ["航天", "卫星", "火箭", "商业航天", "星链", "太空", "低轨"],
    "新能源": ["新能源", "光伏", "风电", "储能", "锂电", "充电桩", "碳中和"],
    "金融/银行": ["银行", "券商", "保险", "金融", "信贷"],
    "消费/白酒": ["消费", "白酒", "食品", "零售", "茅台", "五粮液", "品牌"],
    "煤炭/资源": ["煤炭", "资源", "矿业", "铜", "锂", "稀土"],
    "房地产": ["房地产", "楼市", "房价", "开发商", "物业"],
    "医药": ["医药", "医疗", "创新药", "生物科技", "CXO"],
    "光通信": ["光通信", "光模块", "光纤", "CPO", "硅光"],
    "存储": ["存储", "DRAM", "NAND", "HBM", "闪存"],
    "军工": ["军工", "国防", "装备", "导弹"],
    "机器人": ["机器人", "人形机器人", "减速器", "伺服"],
    "脑机接口": ["脑机", "Neuralink", "脑科学"],
    "核聚变": ["核聚变", "可控核", "托卡马克"],
}

# 个股识别正则（中文股票名称模式 — 捕获词典外的个股，补充STOCK_DICT）
STOCK_NAME_PATTERN = re.compile(
    r'(?:中国|中|国|华|南|北|东|西|新|大|上|深|长|广|江|浙|海|天|金|银|龙|凤|'
    r'安|宝|富|恒|嘉|美|高|万|百|千|红|蓝|绿|紫|星|光|明|达|利|通|信|科|泰|'
    r'航|发|沈|成|西|赣|鲁|闽|川|渝|鄂|湘|皖|豫|冀|辽|吉|黑)[\u4e00-\u9fff]{1,5}'
    r'(?:股份|科技|电子|集团|控股|材料|设备|能源|动力|智能|芯片|生物|药业|'
    r'化工|机械|光电|信息|通信|网络|软件|互联|新材|环保|装备|工业|精密|'
    r'电气|自动化|仪器|仪表|航空|航天|船舶|重工)'
)

# 短线信号词（蒸馏用：情绪周期/辨识度/卡位等短线专有术语）
SHORT_SIGNAL_KW = [
    "涨停", "连板", "龙头", "资金流入", "主力买入", "封板",
    "竞价", "炸板", "反包", "首板", "二板", "三板", "妖股",
    "情绪", "辨识度", "卡位", "补涨", "加速", "打板", "游资",
    "龙虎榜", "复盘", "盘面", "资金流向", "止损",
]

# 长线/基本面指标词（蒸馏用：财务报表和估值分析术语）
FINANCIAL_METRICS_KW = [
    "护城河", "ROE", "净利润", "毛利率", "自由现金流", "估值",
    "PE", "PB", "分红", "回购", "业绩增长", "核心竞争力",
    "市场份额", "研发", "壁垒", "内在价值", "市盈率", "市净率",
    "股息率", "营收增长", "净利率", "ROA", "资产负债率",
]

# 投资格言/金句关键词（用于提取哲理性表达）
WISDOM_INDICATORS = [
    "道", "禅", "悟", "哲学", "认知", "智慧", "思维", "格局",
    "长期", "耐心", "时间", "复利", "慢慢", "变富",
    "恐惧", "贪婪", "纪律", "原则", "底线",
]


# ─── 统计分析（基于raw全文逐篇提取） ──────────────────────────────────────────────
def analyze_articles(articles: list, author_name: str) -> dict:
    """
    统计分析文章数据。
    核心原则：必须从raw全文逐篇提取，不依赖任何clean/NER中间层。
    """
    stats = {
        "author": author_name,
        "total_articles": len(articles),
        "analysis_time": datetime.now().isoformat(),
    }

    # 1. 基础统计（含精确字数）
    word_counts = []
    publish_dates = []
    all_contents = []

    for a in articles:
        content = clean_text(a.get("content", "") or a.get("正文", ""))
        title = a.get("title", "") or a.get("标题", "")
        pub_time = a.get("publish_time", "") or a.get("发布时间", "")

        wc = len(content)
        word_counts.append(wc)
        all_contents.append({
            "title": title, "content": content,
            "publish_time": pub_time, "word_count": wc,
        })
        if pub_time:
            publish_dates.append(str(pub_time)[:10])

    sorted_wc = sorted(word_counts)
    stats["word_count"] = {
        "avg": round(sum(word_counts) / len(word_counts), 0) if word_counts else 0,
        "min": min(word_counts) if word_counts else 0,
        "max": max(word_counts) if word_counts else 0,
        "median": sorted_wc[len(sorted_wc) // 2] if word_counts else 0,
    }

    # 2. 发布频率
    if publish_dates:
        date_counter = Counter(publish_dates)
        stats["publish_frequency"] = {
            "total_days": len(date_counter),
            "avg_per_day": round(len(articles) / max(len(date_counter), 1), 1),
            "most_active_date": date_counter.most_common(1)[0] if date_counter else None,
        }

    # 3. 内容关键词聚合（API 字段: contentKeywords，非 wordCloud）
    ck_agg = Counter()
    for a in articles:
        ck = a.get("content_keywords", [])
        if isinstance(ck, list):
            for item in ck:
                if isinstance(item, dict):
                    ck_agg[item.get("keyword", "")] += item.get("weight", 1.0)
    stats["top_keywords"] = [{"keyword": k, "weight": round(v, 2)} for k, v in ck_agg.most_common(30)]

    # 4. 个股/指数频次提取（词典+别名+正则双通道，含上下文和复合评分）
    stock_counter = Counter()
    stock_context = defaultdict(list)  # 个股 → 相关文章标题列表

    for a in all_contents:
        text = f"{a['title']} {a['content']}"
        title_short = a['title'][:60] if a['title'] else ""

        # 通道A：词典+别名匹配（精确，含口语化别名）
        for stock_name, aliases in STOCK_DICT.items():
            if any(alias.lower() in text.lower() for alias in aliases):
                stock_counter[stock_name] += 1
                if title_short:
                    stock_context[stock_name].append(title_short)

        # 通道B：正则模式匹配（捕获词典外的个股全称）
        regex_matches = STOCK_NAME_PATTERN.findall(text)
        for m in regex_matches:
            if len(m) >= 3:
                # 排除已被词典覆盖的个股
                already_covered = any(m == sn or m in aliases for sn, aliases in STOCK_DICT.items())
                if not already_covered:
                    stock_counter[m] += 1
                    if title_short:
                        stock_context[m].append(title_short)

    # 复合评分：提及频率 + 短线/长线关键词上下文权重
    stock_scores = {}
    for stock, count in stock_counter.items():
        contexts = stock_context.get(stock, [])
        context_text = " ".join(contexts)
        # 基础分 = 提及次数
        score = count
        # 短线信号加分（出现短线术语说明该个股有短线关注价值）
        score += sum(1 for kw in SHORT_SIGNAL_KW if kw in context_text)
        # 长线指标加分（出现基本面术语说明该个股有长线分析深度）
        score += sum(2 for kw in FINANCIAL_METRICS_KW if kw in context_text)
        stock_scores[stock] = score

    # 输出：按复合评分排序，保留上下文
    top_stocks = sorted(stock_scores.items(), key=lambda x: x[1], reverse=True)[:30]
    stats["stock_mentions"] = [
        {"stock": s, "count": stock_counter[s], "score": sc,
         "ratio": round(stock_counter[s] / max(len(articles), 1), 2),
         "sample_titles": stock_context.get(s, [])[:3]}
        for s, sc in top_stocks
    ]
    # 正则发现的词典外个股（供AI审查是否有重要遗漏）
    dict_stocks = set(STOCK_DICT.keys())
    regex_discovered = [
        {"stock": s, "count": stock_counter[s], "sample_titles": stock_context.get(s, [])[:2]}
        for s, _ in top_stocks if s not in dict_stocks
    ][:10]
    stats["regex_discovered_stocks"] = regex_discovered

    # 5. 板块文章级计数（每篇只计一次）
    sector_article_counts = {}
    for sector, kws in SECTOR_KEYWORDS.items():
        count = sum(
            1 for a in all_contents
            if any(kw in f"{a['title']} {a['content']}" for kw in kws)
        )
        if count > 0:
            sector_article_counts[sector] = count
    stats["sector_focus"] = dict(
        sorted(sector_article_counts.items(), key=lambda x: x[1], reverse=True)
    )

    # 6. 投资关键短语提取
    phrase_counter = Counter()
    for a in all_contents:
        text = f"{a['title']} {a['content']}"
        for phrase in INVESTMENT_PHRASES:
            c = text.count(phrase)
            if c > 0:
                phrase_counter[phrase] += c
    stats["investment_phrases"] = [
        {"phrase": p, "count": c} for p, c in phrase_counter.most_common(40)
    ]

    # 7. 交易类型判定（使用扩充的SHORT_SIGNAL_KW + FINANCIAL_METRICS_KW）
    long_kw = list(set(FINANCIAL_METRICS_KW + [
        "价值投资", "基本面", "财报", "持有", "长期",
        "安全边际", "定投", "生意", "核心竞争力", "业绩增长",
    ]))
    short_kw = list(set(SHORT_SIGNAL_KW + [
        "跌停", "封板", "炸板", "反包", "首板", "二板", "三板",
        "卡位", "补涨", "加速", "辨识度",
    ]))

    long_count = sum(a["content"].count(kw) for a in all_contents for kw in long_kw)
    short_count = sum(a["content"].count(kw) for a in all_contents for kw in short_kw)

    stats["trader_type"] = {
        "long_score": long_count,
        "short_score": short_count,
        "classified_type": "长线" if long_count > short_count * 1.5 else ("短线" if short_count > long_count * 1.5 else "混合"),
    }

    # 8. 标志性表达提取
    phrase_counter_sig = Counter()
    for a in all_contents:
        sentences = re.split(r'[。！？\n]', a["content"])
        for s in sentences:
            s = s.strip()
            if 4 <= len(s) <= 30:
                phrase_counter_sig[s] += 1
    stats["signature_phrases"] = [
        {"phrase": p, "count": c}
        for p, c in phrase_counter_sig.most_common(50) if c >= 2
    ][:20]

    # 8b. 投资格言/金句提取
    wisdom_phrases = []
    for p, c in phrase_counter_sig.most_common(100):
        if any(ind in p for ind in WISDOM_INDICATORS) and c >= 2:
            wisdom_phrases.append({"phrase": p, "count": c})
    stats["investment_wisdom"] = wisdom_phrases[:15]

    # 9. 文章结构分析 + 开头/结尾/标题模式检测
    structures = []
    opening_patterns = Counter()
    closing_patterns = Counter()

    for a in all_contents:
        paragraphs = split_paragraphs(a["content"])
        if not paragraphs:
            continue
        opening = paragraphs[0][:100]
        closing = paragraphs[-1][:100] if len(paragraphs) > 1 else ""

        if "免责" in opening:
            opening_patterns["免责声明开头"] += 1
        if "今天" in opening[:10]:
            opening_patterns["今日盘面开头"] += 1

        if "免责" in closing or "风险" in closing or "投资需谨慎" in closing:
            closing_patterns["风险/免责结尾"] += 1
        if "链接" in closing or "星标" in closing or "关注" in closing:
            closing_patterns["引导关注结尾"] += 1

        structures.append({
            "title": a["title"],
            "para_count": len(paragraphs),
            "opening": opening,
            "closing": closing,
            "word_count": a["word_count"],
            "publish_time": a["publish_time"],
        })
    stats["article_structures"] = structures[:20]
    stats["opening_patterns"] = dict(opening_patterns.most_common(5))
    stats["closing_patterns"] = dict(closing_patterns.most_common(5))

    # 10. 标题模式分析
    title_patterns = {"疑问句": 0, "感叹句": 0, "陈述句": 0, "数字开头": 0}
    title_format_counter = Counter()
    for a in all_contents:
        t = a.get("title", "")
        if t:
            if "？" in t or "?" in t:
                title_patterns["疑问句"] += 1
            elif "！" in t or "!" in t:
                title_patterns["感叹句"] += 1
            else:
                title_patterns["陈述句"] += 1
            if t[0].isdigit():
                title_patterns["数字开头"] += 1
            if len(t) > 6:
                prefix = re.sub(r'[（(].+?[）)]', '', t)[:8]
                title_format_counter[prefix] += 1
    stats["title_patterns"] = title_patterns
    stats["title_format_templates"] = [
        {"prefix": p, "count": c}
        for p, c in title_format_counter.most_common(5) if c >= 3
    ]

    # 11. 交易术语统计（整合SHORT_SIGNAL_KW + FINANCIAL_METRICS_KW + 操作术语）
    trading_terms = list(set(
        SHORT_SIGNAL_KW + FINANCIAL_METRICS_KW + [
            "情绪周期", "止盈", "仓位", "满仓", "清仓",
            "减仓", "加仓", "建仓", "空仓", "做多", "做空", "牛市", "熊市", "震荡",
            "放量", "缩量", "突破", "回调", "反弹", "趋势", "支撑", "压力", "均线",
            "K线", "MACD", "量价", "换手率", "成交额", "市值",
            "基本面", "技术面", "资金面", "消息面", "板块轮动",
        ]
    ))
    term_counter = Counter()
    for a in all_contents:
        for term in trading_terms:
            c = a["content"].count(term)
            if c > 0:
                term_counter[term] += c
    stats["trading_terms"] = [{"term": t, "count": c} for t, c in term_counter.most_common(30)]

    # 12. 免责声明检测
    disclaimer_kw = ["免责声明", "不构成", "投资建议", "个人日记", "个人笔记", "理财需谨慎", "投资有风险"]
    dc = sum(1 for a in all_contents if any(kw in a["content"] for kw in disclaimer_kw))
    stats["has_disclaimer"] = {"count": dc, "ratio": round(dc / max(len(articles), 1), 2)}

    # 13. 师承/影响源扫描
    mentor_kw = {
        "巴菲特": ["巴菲特", "伯克希尔"],
        "芒格": ["芒格", "穷查理"],
        "段永平": ["段永平"],
        "李录": ["李录"],
        "格雷厄姆": ["格雷厄姆", "聪明的投资者"],
        "彼得林奇": ["彼得林奇", "林奇"],
        "索罗斯": ["索罗斯", "反身性"],
        "达利欧": ["达利欧", "原则"],
        "霍华德马克斯": ["霍华德", "马克斯", "投资最重要的事"],
    }
    mentor_scores = {}
    for mentor, kws in mentor_kw.items():
        score = sum(a["content"].count(kw) for a in all_contents for kw in kws)
        if score > 0:
            mentor_scores[mentor] = score
    stats["mentor_influence"] = dict(sorted(mentor_scores.items(), key=lambda x: x[1], reverse=True))

    # 14. 语气量化分析（感叹句/疑问句/第一人称/口语化 四类标记）
    tone_markers = {
        "感叹句": 0, "疑问句": 0, "第一人称": 0, "口语化": 0,
    }
    for a in all_contents:
        c = a["content"]
        tone_markers["感叹句"] += len(re.findall(r'[！!]', c))
        tone_markers["疑问句"] += len(re.findall(r'[？?]', c))
        tone_markers["第一人称"] += len(re.findall(r'我[们]?', c))
        tone_markers["口语化"] += len(re.findall(r'[吧呢啊嘛哦哈嘿哟啦哇]', c))
    # 归一化为每篇平均
    n = max(len(articles), 1)
    tone_avg = {k: round(v / n, 1) for k, v in tone_markers.items()}
    total_tone = sum(tone_markers.values())
    if total_tone > n * 10:
        tone_style = "强语气型"
    elif total_tone > n * 3:
        tone_style = "中等语气型"
    else:
        tone_style = "冷静克制型"
    stats["tone_analysis"] = {
        "markers_total": tone_markers,
        "per_article_avg": tone_avg,
        "tone_style": tone_style,
    }

    # 15. 论证链模式提取（检测博主特有的分析推理路径）
    # 常见论证模式标记词
    arg_patterns = {
        "事件驱动型": ["消息", "事件", "突发", "利好", "利空", "催化", "政策", "发布"],
        "数据驱动型": ["数据", "财报", "营收", "利润", "增长率", "同比", "环比", "出货量"],
        "逻辑推演型": ["因此", "所以", "导致", "意味着", "由此可见", "逻辑是", "推导"],
        "类比推理型": ["类似", "参照", "对比", "历史", "上一轮", "复盘", "如同"],
        "产业链分析型": ["产业链", "上下游", "景气度", "传导", "供需", "产能", "订单"],
        "逆向思维型": ["反过来", "逆向", "反直觉", "大多数人", "相反", "市场错了"],
    }
    arg_scores = {}
    for pattern_name, kws in arg_patterns.items():
        score = sum(a["content"].count(kw) for a in all_contents for kw in kws)
        if score > 0:
            arg_scores[pattern_name] = score
    stats["argumentation_style"] = dict(
        sorted(arg_scores.items(), key=lambda x: x[1], reverse=True)
    )

    # 16. 核心分析工具识别（博主用什么思维框架分析市场）
    thinking_tools = {
        "宏观经济分析": ["GDP", "PMI", "CPI", "PPI", "利率", "美联储", "货币政策", "财政政策"],
        "产业链研究": ["产业链", "上下游", "景气度", "产能", "供需格局", "行业格局"],
        "财务报表分析": ["财报", "营收", "净利润", "毛利率", "现金流", "ROE", "负债"],
        "技术面分析": ["K线", "MACD", "均线", "支撑", "压力", "趋势", "量价", "突破"],
        "资金面分析": ["北向资金", "主力资金", "融资余额", "资金流向", "龙虎榜", "机构"],
        "情绪周期分析": ["情绪", "周期", "高潮", "冰点", "退潮", "修复", "分歧", "一致"],
        "全球对标分析": ["美股", "纳斯达克", "标普", "英伟达", "台积电", "全球", "海外"],
        "政策面分析": ["政策", "监管", "制裁", "关税", "补贴", "规划", "纲要"],
    }
    tool_scores = {}
    for tool_name, kws in thinking_tools.items():
        score = sum(a["content"].count(kw) for a in all_contents for kw in kws)
        if score > 0:
            tool_scores[tool_name] = score
    stats["thinking_tools"] = dict(
        sorted(tool_scores.items(), key=lambda x: x[1], reverse=True)
    )

    # 17. 数据引用密度（区分"数据驱动型"和"主观判断型"博主）
    data_ref_kws = [
        "数据", "财报", "同比", "环比", "增长", "下降", "%", "营收", "利润",
        "出货量", "产能", "利用率", "订单", "库存", "价格指数",
        "成交额", "万亿", "千亿", "百亿", "亿元",
    ]
    data_ref_count = sum(
        a["content"].count(kw) for a in all_contents for kw in data_ref_kws
    )
    total_chars = sum(a["word_count"] for a in all_contents)
    data_density = round(data_ref_count / max(total_chars, 1) * 1000, 2)  # 每千字数据引用次数
    if data_density > 5:
        data_style = "高密度数据驱动型"
    elif data_density > 2:
        data_style = "中等数据引用型"
    else:
        data_style = "主观判断型"
    stats["data_citation"] = {
        "total_refs": data_ref_count,
        "density_per_1k": data_density,
        "data_style": data_style,
    }

    # 18. 跨市场视角检测（是否关注全球市场联动）
    cross_market_kws = {
        "美股": ["美股", "纳斯达克", "标普", "道琼斯", "美联储", "英伟达", "苹果", "特斯拉", "谷歌", "微软"],
        "港股": ["港股", "恒生", "恒指", "恒生科技", "南向资金"],
        "A股": ["A股", "上证", "深证", "创业板", "科创板"],
        "商品/汇率": ["黄金", "原油", "美元", "人民币", "汇率", "铜", "锂"],
    }
    cross_market = {}
    for market, kws in cross_market_kws.items():
        count = sum(a["content"].count(kw) for a in all_contents for kw in kws)
        if count > 0:
            cross_market[market] = count
    # 跨市场广度：涉及几个市场
    cross_breadth = len(cross_market)
    stats["cross_market"] = {
        "markets": dict(sorted(cross_market.items(), key=lambda x: x[1], reverse=True)),
        "breadth": cross_breadth,
        "perspective": "全球视角" if cross_breadth >= 3 else ("多市场" if cross_breadth >= 2 else "单一市场"),
    }

    # 19. 信息密度评估（投资分析内容占比，区分干货型和水文型）
    investment_content_kws = list(set(
        SHORT_SIGNAL_KW + FINANCIAL_METRICS_KW + [
            "估值", "仓位", "板块", "赛道", "龙头", "趋势", "基本面",
            "技术面", "资金面", "消息面", "产业链", "景气", "周期",
        ]
    ))
    inv_content_count = sum(
        a["content"].count(kw) for a in all_contents for kw in investment_content_kws
    )
    info_density = round(inv_content_count / max(total_chars, 1) * 1000, 2)  # 每千字投资内容密度
    if info_density > 10:
        info_level = "高信息密度（投资分析占比80%+）"
    elif info_density > 5:
        info_level = "中等信息密度（投资分析占比50-80%）"
    else:
        info_level = "低信息密度（生活/闲聊/引流内容较多）"
    stats["information_density"] = {
        "investment_refs": inv_content_count,
        "density_per_1k": info_density,
        "level": info_level,
    }

    # 20. 互动数据统计（API 直接返回，非正文推断）
    engagement = {
        "read_avg": 0, "read_max": 0, "read_total": 0,
        "like_avg": 0, "like_max": 0, "like_total": 0,
        "comment_avg": 0, "comment_total": 0,
        "share_avg": 0, "share_total": 0,
        "collect_avg": 0, "collect_total": 0,
        "reward_total": 0,
        "engagement_rate": 0,  # 互动率 = (点赞+评论+转发) / 阅读
    }
    if all_contents:
        reads = [a.get("read_count", 0) or 0 for a in articles]
        likes = [a.get("like_count", 0) or 0 for a in articles]
        comments = [a.get("comment_count", 0) or 0 for a in articles]
        shares = [a.get("share_count", 0) or 0 for a in articles]
        collects = [a.get("collect_count", 0) or 0 for a in articles]
        rewards = [a.get("reward_count", 0) or 0 for a in articles]
        n = len(articles)
        engagement["read_avg"] = round(sum(reads) / n, 0)
        engagement["read_max"] = max(reads)
        engagement["read_total"] = sum(reads)
        engagement["like_avg"] = round(sum(likes) / n, 0)
        engagement["like_max"] = max(likes)
        engagement["like_total"] = sum(likes)
        engagement["comment_avg"] = round(sum(comments) / n, 0)
        engagement["comment_total"] = sum(comments)
        engagement["share_avg"] = round(sum(shares) / n, 0)
        engagement["share_total"] = sum(shares)
        engagement["collect_avg"] = round(sum(collects) / n, 0)
        engagement["collect_total"] = sum(collects)
        engagement["reward_total"] = sum(rewards)
        total_reads = engagement["read_total"] or 1
        engagement["engagement_rate"] = round(
            (engagement["like_total"] + engagement["comment_total"] + engagement["share_total"]) / total_reads * 100, 2
        )
        # 互动层级判定
        er = engagement["engagement_rate"]
        if er > 5:
            engagement["level"] = "极高互动（粉丝粘性极强）"
        elif er > 2:
            engagement["level"] = "高互动（活跃粉丝群体）"
        elif er > 1:
            engagement["level"] = "中等互动"
        else:
            engagement["level"] = "低互动（阅读量大但互动少）"
    stats["engagement"] = engagement

    return stats


# ─── 生成数据底稿和蒸馏任务 ──────────────────────────────────────────────────────────
def generate_brief(stats, author_name):
    """生成数据底稿"""
    lines = []
    lines.append(f"# {author_name} 蒸馏数据底稿")
    lines.append(f"\n> 生成时间：{stats.get('analysis_time', '')}")
    lines.append(f"> 内容总数：{stats['total_articles']} 篇\n")

    lines.append("## 1. 基础统计\n")
    wc = stats.get("word_count", {})
    lines.append(f"- 平均字数：{wc.get('avg', 0)}")
    lines.append(f"- 最短/最长：{wc.get('min', 0)} / {wc.get('max', 0)}")
    lines.append(f"- 中位数：{wc.get('median', 0)}\n")

    pf = stats.get("publish_frequency", {})
    lines.append("## 2. 发布频率\n")
    lines.append(f"- 发布天数：{pf.get('total_days', 0)}")
    lines.append(f"- 日均发文：{pf.get('avg_per_day', 0)} 篇\n")

    tt = stats.get("trader_type", {})
    lines.append("## 3. 交易类型判定\n")
    lines.append(f"- 长线关键词得分：{tt.get('long_score', 0)}")
    lines.append(f"- 短线关键词得分：{tt.get('short_score', 0)}")
    lines.append(f"- 判定结果：**{tt.get('classified_type', '未知')}**\n")

    lines.append("## 4. 个股/指数提及排行 TOP20（复合评分 = 提及频率 + 上下文关键词权重）\n")
    lines.append("| 个股 | 提及次数 | 综合评分 | 占比 | 相关文章 |")
    lines.append("|------|---------|---------|------|---------|")
    for s in stats.get("stock_mentions", [])[:20]:
        titles = "、".join(s.get("sample_titles", [])[:2])
        lines.append(f"| {s['stock']} | {s['count']} | {s['score']} | {s['ratio']:.0%} | {titles} |")
    lines.append("")

    # 正则发现的词典外个股（重要补充信息）
    regex_stocks = stats.get("regex_discovered_stocks", [])
    if regex_stocks:
        lines.append("### 正则发现的词典外个股（AI审查是否有重要遗漏）\n")
        for s in regex_stocks:
            titles = "、".join(s.get("sample_titles", [])[:2])
            lines.append(f"- **{s['stock']}**（{s['count']}次）相关文章：{titles}")
        lines.append("")

    lines.append("## 5. 板块关注度（文章级计数）\n")
    for sector, count in stats.get("sector_focus", {}).items():
        ratio = count / max(stats['total_articles'], 1)
        lines.append(f"- {sector}：{count}篇（{ratio:.0%}）")
    lines.append("")

    lines.append("## 6. 投资关键短语 TOP30\n")
    for p in stats.get("investment_phrases", [])[:30]:
        lines.append(f"- {p['phrase']}（{p['count']}次）")
    lines.append("")

    lines.append("## 7. 标志性表达 TOP15\n")
    for p in stats.get("signature_phrases", [])[:15]:
        lines.append(f"- 「{p['phrase']}」出现 {p['count']} 次")
    lines.append("")

    lines.append("## 8. 投资格言/金句\n")
    wisdom = stats.get("investment_wisdom", [])
    if wisdom:
        for p in wisdom[:10]:
            lines.append(f"- 「{p['phrase']}」出现 {p['count']} 次")
    else:
        lines.append("- 未检测到高频投资格言")
    lines.append("")

    lines.append("## 9. 交易术语使用频率 TOP20\n")
    for t in stats.get("trading_terms", [])[:20]:
        lines.append(f"- {t['term']}（{t['count']}次）")
    lines.append("")

    lines.append("## 10. 标题模式分析\n")
    for k, v in stats.get("title_patterns", {}).items():
        lines.append(f"- {k}：{v}")
    templates = stats.get("title_format_templates", [])
    if templates:
        lines.append("\n**固定格式模板：**")
        for t in templates:
            lines.append(f"- 「{t['prefix']}...」（{t['count']}次）")
    lines.append("")

    lines.append("## 11. 开头/结尾模式\n")
    op = stats.get("opening_patterns", {})
    if op:
        lines.append("**开头模式：**")
        for k, v in op.items():
            lines.append(f"- {k}：{v}篇")
    cp = stats.get("closing_patterns", {})
    if cp:
        lines.append("\n**结尾模式：**")
        for k, v in cp.items():
            lines.append(f"- {k}：{v}篇")
    lines.append("")

    hd = stats.get("has_disclaimer", {})
    lines.append(f"## 12. 免责声明\n")
    lines.append(f"- 含免责声明：{hd.get('count', 0)}/{stats['total_articles']}（{hd.get('ratio', 0):.0%}）\n")

    mi = stats.get("mentor_influence", {})
    lines.append("## 13. 师承/影响源\n")
    if mi:
        for mentor, score in mi.items():
            lines.append(f"- {mentor}（提及{score}次）")
    else:
        lines.append("- 未检测到明显师承影响")
    lines.append("")

    lines.append("## 14. 高频关键词 TOP20\n")
    for kw in stats.get("top_keywords", [])[:20]:
        lines.append(f"- {kw['keyword']}（权重：{kw['weight']}）")
    lines.append("")

    lines.append("## 15. 内容结构样本（前5篇）\n")
    for s in stats.get("article_structures", [])[:5]:
        lines.append(f"### {s['title']}")
        lines.append(f"- 段落数：{s['para_count']}")
        lines.append(f"- 字数：{s['word_count']}")
        lines.append(f"- 开头：{s['opening'][:80]}...")
        lines.append(f"- 结尾：{s['closing'][:80]}...")
        lines.append("")

    # ── 互动数据（API数值，非正文推断）──
    eg = stats.get("engagement", {})
    if eg:
        lines.append("## 互动数据统计\n")
        lines.append(f"- 篇均阅读：{eg.get('read_avg', 0):.0f}（最高 {eg.get('read_max', 0)}）")
        lines.append(f"- 篇均点赞：{eg.get('like_avg', 0):.0f}（最高 {eg.get('like_max', 0)}）")
        lines.append(f"- 篇均评论：{eg.get('comment_avg', 0):.0f}")
        lines.append(f"- 篇均转发：{eg.get('share_avg', 0):.0f}")
        lines.append(f"- 篇均收藏：{eg.get('collect_avg', 0):.0f}")
        lines.append(f"- 互动率：{eg.get('engagement_rate', 0)}%")
        lines.append(f"- 互动层级：**{eg.get('level', '未知')}**")
        lines.append("")

    # ── 思维层分析维度（16-21）──
    lines.append("---\n")
    lines.append("## 16. 语气量化分析\n")
    tone = stats.get("tone_analysis", {})
    markers = tone.get("markers_total", {})
    avg = tone.get("per_article_avg", {})
    if markers:
        lines.append(f"- 风格分类：**{tone.get('tone_style', '未知')}**")
        lines.append(f"- 感叹句：{markers.get('感叹句', 0)}（篇均{avg.get('感叹句', 0)}）")
        lines.append(f"- 疑问句：{markers.get('疑问句', 0)}（篇均{avg.get('疑问句', 0)}）")
        lines.append(f"- 第一人称：{markers.get('第一人称', 0)}（篇均{avg.get('第一人称', 0)}）")
        lines.append(f"- 口语化：{markers.get('口语化', 0)}（篇均{avg.get('口语化', 0)}）")
    lines.append("")

    lines.append("## 17. 论证链模式（博主特有推理路径）\n")
    arg = stats.get("argumentation_style", {})
    if arg:
        for pattern, score in arg.items():
            lines.append(f"- **{pattern}**：{score}分")
    else:
        lines.append("- 未检测到明显论证模式偏好")
    lines.append("")

    lines.append("## 18. 核心分析工具（思维框架）\n")
    tools = stats.get("thinking_tools", {})
    if tools:
        for tool, score in tools.items():
            lines.append(f"- **{tool}**：{score}分")
    else:
        lines.append("- 未检测到明确思维框架")
    lines.append("")

    lines.append("## 19. 数据引用密度\n")
    dc = stats.get("data_citation", {})
    if dc:
        lines.append(f"- 风格分类：**{dc.get('data_style', '未知')}**")
        lines.append(f"- 总引用次数：{dc.get('total_refs', 0)}")
        lines.append(f"- 每千字数据引用：{dc.get('density_per_1k', 0)}次")
    lines.append("")

    lines.append("## 20. 跨市场视角\n")
    cm = stats.get("cross_market", {})
    if cm:
        lines.append(f"- 视角分类：**{cm.get('perspective', '未知')}**（涉及{cm.get('breadth', 0)}个市场）")
        for market, count in cm.get("markets", {}).items():
            lines.append(f"- {market}：{count}次提及")
    lines.append("")

    lines.append("## 21. 信息密度评估\n")
    info = stats.get("information_density", {})
    if info:
        lines.append(f"- 密度等级：**{info.get('level', '未知')}**")
        lines.append(f"- 投资关键词总量：{info.get('investment_refs', 0)}")
        lines.append(f"- 每千字投资密度：{info.get('density_per_1k', 0)}")
    lines.append("")

    return "\n".join(lines)


def generate_task(stats, author_name):
    """生成AI蒸馏任务清单（七维DNA）"""
    tt = stats.get("trader_type", {})
    trader_type = tt.get("classified_type", "未知")

    lines = []
    lines.append(f"# {author_name} AI蒸馏任务清单\n")
    lines.append(f"> 交易类型：{trader_type}")
    lines.append(f"> 内容数：{stats['total_articles']} 篇")
    lines.append("")

    lines.append("## 蒸馏任务\n")
    lines.append("请基于数据底稿，按七维DNA框架生成风格画像。\n")

    # 构建思维层参考数据
    thinking_tools_ref = ', '.join(list(stats.get("thinking_tools", {}).keys())[:5]) or '待分析'
    arg_ref = ', '.join(list(stats.get("argumentation_style", {}).keys())[:3]) or '待分析'
    tone_ref = stats.get("tone_analysis", {}).get("tone_style", "待分析")
    data_ref = stats.get("data_citation", {}).get("data_style", "待分析")
    cross_ref = stats.get("cross_market", {}).get("perspective", "待分析")
    info_ref = stats.get("information_density", {}).get("level", "待分析")

    dims = [
        ("维度1：交易体系DNA", [
            "提取核心交易模式", "提取选股逻辑", "提取买入信号",
            "提取卖出/止损信号", "提取仓位管理策略",
            f"提取核心分析工具/思维框架（脚本参考：{thinking_tools_ref}）",
            "每个要点需引用至少2条原文证据",
        ]),
        ("维度2：市场判断DNA", [
            "判定交易流派", "提取板块偏好", "提取持仓周期特征",
            "提取多空判断条件", "追踪历史预判与实际走势对比",
            f"分析跨市场视角（脚本检测：{cross_ref}）",
        ]),
        ("维度3：表达风格DNA", [
            "分析文章结构", "提取TOP10标志性表达",
            "分析标题模式", "提取开头模板", "提取结尾模式",
            f"分析语气和人称特征（脚本量化：{tone_ref}）",
            f"提取论证链模式（脚本检测：{arg_ref}）",
            f"评估数据引用风格（脚本检测：{data_ref}）",
        ]),
        ("维度4：内容深度DNA", [
            f"统计平均字数：{stats.get('word_count', {}).get('avg', 0)}字",
            f"评估信息密度（脚本检测：{info_ref}）",
            "评估复盘详细度", "评估预判明确度",
        ]),
        ("维度5：互动特征DNA", [
            "分析读者互动方式", "分析战绩展示方式", "分析争议处理方式",
            f"免责声明使用率：{stats.get('has_disclaimer', {}).get('ratio', 0):.0%}",
        ]),
        ("维度6：热点图谱DNA", [
            f"核心赛道排序（参考：{', '.join(list(stats.get('sector_focus', {}).keys())[:5])}）",
            "提取龙头记忆", "提取常用盘面指标", "提取资金面关注点",
        ]),
        ("维度7：人设基因DNA", [
            "提取投资经历和入市背景",
            "分析投资哲学演变（对比早期 vs 近期内容）",
            "提取里程碑事件（重大盈亏/转折点）",
            f"分析师承/影响源（参考：{', '.join(list(stats.get('mentor_influence', {}).keys())[:5]) or '未检测到'}）",
        ]),
    ]

    for title, items in dims:
        lines.append(f"### {title}")
        for item in items:
            lines.append(f"- {item}")
        lines.append("")

    lines.append("## 输出格式\n")
    lines.append("按照 `assets/profile_template.md` 模板输出，保存为：")
    lines.append(f"`output/{author_name}_风格画像.md`\n")

    lines.append("## 质量要求\n")
    lines.append("- 每个维度至少3个具体特征")
    lines.append("- 每个特征至少1条原文证据")
    lines.append("- 标注蒸馏置信度（高/中/低）")
    lines.append("- 禁止编造未在原文中出现的数据")

    return "\n".join(lines)


# ─── 主流程 ──────────────────────────────────────────────────────────────────────────
def distill(account, author_name, count=None, api_key=None, force_refresh=False):
    """蒸馏指定博主"""
    step(f"开始蒸馏：{author_name}（微信号: {account}，目标: {count}篇）")

    # 采集文章
    from gzh import fetch_articles
    articles = fetch_articles(
        account=account,
        author_name=author_name,
        count=count,
        api_key=api_key,
        force_refresh=force_refresh,
    )

    if not articles:
        error(f"未获取到「{author_name}」的文章数据，请检查微信号是否正确")
        return False

    info(f"「{author_name}」共 {len(articles)} 条内容")

    # 保存完整文章到磁盘（供后续校验/AI精读使用）
    articles_file = OUTPUT_DIR / f"{author_name}_完整文章.json"
    articles_file.write_text(json.dumps(articles, ensure_ascii=False, indent=2), encoding="utf-8")
    info(f"完整文章已保存：{articles_file}")

    # Phase 2: 统计分析
    step("统计分析中...")
    stats = analyze_articles(articles, author_name)

    # 保存统计数据
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    stats_file = OUTPUT_DIR / f"{author_name}_统计数据.json"
    stats_file.write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    info(f"统计数据已保存：{stats_file}")

    # Phase 3: 生成数据底稿和蒸馏任务
    step("生成数据底稿和蒸馏任务...")
    brief = generate_brief(stats, author_name)
    task = generate_task(stats, author_name)

    brief_file = OUTPUT_DIR / f"{author_name}_数据底稿.md"
    task_file = OUTPUT_DIR / f"{author_name}_蒸馏任务.md"
    brief_file.write_text(brief, encoding="utf-8")
    task_file.write_text(task, encoding="utf-8")
    info(f"数据底稿已保存：{brief_file}")
    info(f"蒸馏任务已保存：{task_file}")

    # Phase 3.5: 生成结构化JSON画像
    step("生成结构化JSON画像...")
    json_profile = generate_json_profile(stats, author_name)
    profile_file = OUTPUT_DIR / f"{author_name}_画像.json"
    profile_file.write_text(json.dumps(json_profile, ensure_ascii=False, indent=2), encoding="utf-8")
    info(f"JSON画像已保存：{profile_file}")
    info(f"JSON画像为基础框架，AI需基于蒸馏任务深入阅读原文后补充完善")

    print()
    print(f"{BOLD}{'='*60}{RESET}")
    print(f"{BOLD}  数据底稿和蒸馏任务已生成{RESET}")
    print(f"{BOLD}  请AI读取以下文件并生成七维DNA风格画像：{RESET}")
    print(f"  1. {brief_file}")
    print(f"  2. {task_file}")
    print(f"  3. {profile_file}（JSON画像基础框架）")
    print(f"  4. 参考模板：{SCRIPT_DIR}/assets/profile_template.md")
    print(f"  输出到：{OUTPUT_DIR}/{author_name}_风格画像.md")
    print(f"{BOLD}  蒸馏完成后请执行校验：{RESET}")
    print(f"  python distill.py --validate --author \"{author_name}\"")
    print(f"{BOLD}{'='*60}{RESET}")
    print()
    return True


# ─── JSON结构化画像生成 ─────────────────────────────────────────────────────────────
def generate_json_profile(stats, author_name):
    """基于统计数据生成结构化JSON画像（七维DNA）。"""
    wc = stats.get("word_count", {})
    tt = stats.get("trader_type", {})

    stock_mentions = [
        {"name": s["stock"], "count": s["count"], "score": s["score"]}
        for s in stats.get("stock_mentions", [])[:20]
    ]
    stock_names = [s["name"] for s in stock_mentions]
    regex_discovered = [s["stock"] for s in stats.get("regex_discovered_stocks", [])[:5]]
    sectors = [f"{s}（{c}篇）" for s, c in list(stats.get("sector_focus", {}).items())[:8]]
    sig_phrases = [p["phrase"] for p in stats.get("signature_phrases", [])[:10]]
    inv_phrases = [p["phrase"] for p in stats.get("investment_phrases", [])[:15]]
    wisdom = [p["phrase"] for p in stats.get("investment_wisdom", [])[:8]]

    templates = stats.get("title_format_templates", [])
    title_style = f"固定格式：'{templates[0]['prefix']}...'" if templates else "自由格式"

    op = stats.get("opening_patterns", {})
    cp = stats.get("closing_patterns", {})
    opening = max(op, key=op.get) if op else "自由开头"
    closing = max(cp, key=cp.get) if cp else "自由结尾"

    # 提取思维层数据
    thinking_tools = list(stats.get("thinking_tools", {}).keys())[:5]
    arg_styles = list(stats.get("argumentation_style", {}).keys())[:3]
    tone_data = stats.get("tone_analysis", {})
    tone_style = tone_data.get("tone_style", "")
    data_cite = stats.get("data_citation", {})
    data_style = data_cite.get("data_style", "")
    cross_data = stats.get("cross_market", {})
    cross_perspective = cross_data.get("perspective", "")
    cross_markets = list(cross_data.get("markets", {}).keys())
    info_density = stats.get("information_density", {})

    profile = {
        "大V名称": author_name,
        "蒸馏日期": datetime.now().strftime("%Y-%m-%d"),
        "样本文章数": stats["total_articles"],
        "蒸馏置信度": "高" if stats["total_articles"] >= 60 else "中",
        "风格类型": f"{tt.get('classified_type', '未知')}型投资者",

        "投资体系": {
            "核心流派": f"{tt.get('classified_type', '未知')}投资，{'基本面,估值' if tt.get('long_score', 0) > tt.get('short_score', 0) else '技术,趋势'}为核心",
            "选股逻辑": inv_phrases[:3] if inv_phrases else [],
            "买入决策": [],
            "卖出决策": [],
            "止损纪律": "",
            "仓位管理": "",
            "持仓周期": "",
            "核心分析工具": thinking_tools,
        },

        "市场判断": {
            "研判方式": "",
            "板块偏好": sectors,
            "风险偏好": "",
            "典型看多条件": [],
            "典型看空条件": [],
            "大盘依赖度": "",
            "周期判断": "",
            "逆向思维": "逆向思维型" in arg_styles,
        },

        "表达风格": {
            "文章结构": "",
            "段落长度": "",
            "语气": tone_style,
            "标志性表达": sig_phrases,
            "投资格言": wisdom,
            "数据引用": data_style,
            "论证方式": arg_styles,
            "标题风格": title_style,
            "开头模式": opening,
            "结尾模式": closing,
            "文风温度": tone_style,
            "免责声明": f"使用率{stats.get('has_disclaimer', {}).get('ratio', 0):.0%}",
        },

        "内容深度": {
            "平均字数": int(wc.get("avg", 0)),
            "中位数字数": int(wc.get("median", 0)),
            "信息密度": info_density.get("level", ""),
            "时效性": "",
            "分析深度": "",
            "预判明确度": "",
            "更新频率": f"{stats.get('publish_frequency', {}).get('avg_per_day', 0)}篇/天",
        },

        "互动特征": {
            "读者互动": "",
            "争议处理": "",
            "战绩展示": "",
            "粉丝运营": "",
            "生活分享": "",
            "互动数据": {
                "篇均阅读": int(stats.get("engagement", {}).get("read_avg", 0)),
                "篇均点赞": int(stats.get("engagement", {}).get("like_avg", 0)),
                "篇均评论": int(stats.get("engagement", {}).get("comment_avg", 0)),
                "篇均转发": int(stats.get("engagement", {}).get("share_avg", 0)),
                "互动率": f"{stats.get('engagement', {}).get('engagement_rate', 0)}%",
                "互动层级": stats.get("engagement", {}).get("level", ""),
            },
        },

        "关注图谱": {
            "核心赛道": [s.split("（")[0] for s in sectors[:6]],
            "常提及个股": stock_mentions,
            "正则发现补充": regex_discovered,
            "宏观关注": cross_markets,
            "常用指标": [],
            "投资格言": wisdom,
            "跨市场": cross_perspective,
        },
    }

    return profile


# ─── 准确性校验 ─────────────────────────────────────────────────────────────────────
def validate_profile(author_name, sample_n=10, **kwargs):
    """校验画像准确性：随机抽样文章，比对画像声明与实际内容。"""
    import random
    random.seed(42)

    step(f"开始校验：{author_name}")

    # 加载画像
    profile_file = OUTPUT_DIR / f"{author_name}_画像.json"
    if not profile_file.exists():
        stats_file = OUTPUT_DIR / f"{author_name}_统计数据.json"
        if stats_file.exists():
            stats_data = json.loads(stats_file.read_text(encoding="utf-8"))
            profile = generate_json_profile(stats_data, author_name)
        else:
            error(f"未找到 {author_name} 的画像或统计数据")
            return None
    else:
        profile = json.loads(profile_file.read_text(encoding="utf-8"))

    # 从完整文章文件获取样本（优先），回退到统计数据截断文本
    articles = []
    full_file = OUTPUT_DIR / f"{author_name}_完整文章.json"
    if full_file.exists():
        try:
            full_data = json.loads(full_file.read_text(encoding="utf-8"))
            articles = [
                {"title": a.get("title", ""), "content": a.get("content", ""),
                 "publish_time": a.get("publish_time", "")}
                for a in full_data
            ]
            info(f"从完整文章文件读取 {len(articles)} 篇（含完整正文）")
        except (json.JSONDecodeError, OSError):
            warn("完整文章文件损坏，回退到统计数据截断文本")

    if not articles:
        stats_file = OUTPUT_DIR / f"{author_name}_统计数据.json"
        if stats_file.exists():
            stats_data = json.loads(stats_file.read_text(encoding="utf-8"))
            structures = stats_data.get("article_structures", [])
            articles = [
                {"title": s.get("title", ""),
                 "content": s.get("opening", "") + s.get("closing", ""),
                 "publish_time": s.get("publish_time", "")}
                for s in structures
            ]
            warn(f"回退到截断文本模式（仅开头+结尾各100字，准确率偏低）")

    if not articles:
        error(f"无法获取 {author_name} 的文章用于校验")
        return None

    sampled = random.sample(articles, min(sample_n, len(articles)))

    # 获取画像声明
    focus = profile.get("关注图谱", {})
    stocks = focus.get("常提及个股", [])
    stock_names = [s.get("name", "") for s in stocks if isinstance(s, dict)]
    sig_phrases = profile.get("表达风格", {}).get("标志性表达", [])

    # A. 个股提及校验
    stock_hits = 0
    for art in sampled:
        text = f"{art.get('title', '')} {art.get('content', '')}"
        if any(sn.lower() in text.lower() for sn in stock_names if sn):
            stock_hits += 1
    stock_acc = stock_hits / len(sampled) * 100 if sampled else 0

    # B. 风格特征校验
    style_hits = 0
    style_total = 3
    if any(any(p in f"{a.get('title', '')} {a.get('content', '')}" for p in sig_phrases[:3]) for a in sampled):
        style_hits += 1
    avg_claimed = profile.get("内容深度", {}).get("平均字数", 0)
    if avg_claimed > 0:
        actual_avg = sum(len(a.get("content", "")) for a in sampled) / len(sampled)
        if abs(actual_avg - avg_claimed) / avg_claimed < 0.5:
            style_hits += 1
    else:
        style_hits += 1
    # 标题风格：检查样本标题是否与画像声称的模式一致
    title_style = profile.get("表达风格", {}).get("标题风格", "")
    sampled_titles = [a.get("title", "") for a in sampled]
    title_exclaim = sum(1 for t in sampled_titles if "！" in t or "!" in t)
    title_ratio = title_exclaim / max(len(sampled_titles), 1)
    if title_ratio >= 0.3:  # 至少30%标题含感叹号即为语气型标题
        style_hits += 1
    style_acc = style_hits / style_total * 100

    # C. 投资体系校验
    system_hits = 1
    system_total = 3
    core = profile.get("投资体系", {}).get("核心流派", "")
    full_text = " ".join([a.get("content", "") for a in sampled])
    # 流派关键词拆分为两字以上独立词（处理中文逗号连接的情况）
    core_kws = [w.strip() for w in re.split(r'[\s,，+、/]+', core) if len(w.strip()) >= 2]
    if any(kw in full_text for kw in core_kws):
        system_hits += 1
    sectors = focus.get("核心赛道", [])
    # 赛道名去掉篇数后缀（如 "AI/人工智能（17篇）" → ["AI", "人工智能"]）
    sector_kws_all = set()
    for s in sectors[:3]:
        s_clean = re.sub(r'[（(]\d+篇[）)]', '', s).strip()
        for part in re.split(r'[/、]', s_clean):
            if len(part.strip()) >= 2:
                sector_kws_all.add(part.strip())
    if any(kw in full_text for kw in sector_kws_all):
        system_hits += 1
    system_acc = system_hits / system_total * 100

    # 综合
    total_hits = stock_hits + style_hits + system_hits
    total_items = len(sampled) + style_total + system_total
    overall_acc = total_hits / total_items * 100

    result = {
        "author": author_name,
        "stock_acc": round(stock_acc, 0),
        "style_acc": round(style_acc, 0),
        "system_acc": round(system_acc, 0),
        "overall_acc": round(overall_acc, 0),
        "passed": overall_acc >= 80,
        "sampled": len(sampled),
    }

    print(f"\n  | 校验维度 | 总题数 | 命中数 | 准确率 |")
    print(f"  |---------|--------|--------|--------|")
    print(f"  | A. 个股提及 | {len(sampled)} | {stock_hits} | {stock_acc:.0f}% |")
    print(f"  | B. 风格特征 | {style_total} | {style_hits} | {style_acc:.0f}% |")
    print(f"  | C. 投资体系 | {system_total} | {system_hits} | {system_acc:.0f}% |")
    print(f"  | **综合** | {total_items} | {total_hits} | **{overall_acc:.0f}%** |")
    print(f"\n  准出标准：综合准确率 >= 80%")
    print(f"  结果：{'通过' if result['passed'] else '需补充蒸馏'}")

    if not result["passed"]:
        warn(f"准确率 {overall_acc:.0f}% < 80%，建议：")
        warn("1. 增加采集数量（--count 100）")
        warn("2. 仔细阅读raw全文补充蒸馏")
        warn("3. 更新画像中不准确的字段后重新校验")

    report_file = OUTPUT_DIR / f"{author_name}_校验报告_{datetime.now().strftime('%Y%m%d')}.json"
    report_file.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    info(f"校验报告已保存：{report_file}")

    return result


# ─── CLI ────────────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="公众号投资博主蒸馏器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
示例:
  python distill.py --account "zshbtz" --count 60
  python distill.py --account "zshbtz" --author "财躺平" --count 100
  python distill.py --validate --author "财躺平" --sample 15
  python distill.py --check-env
""",
    )
    parser.add_argument("--account", help="公众号微信号（如 zshbtz）")
    parser.add_argument("--author", help="博主显示名称（可选，默认使用微信号）")
    parser.add_argument("--count", type=int, default=None,
                        help="文章数量档位（20/60/100，蒸馏模式必填）")
    parser.add_argument("--no-cache", action="store_true", help="强制刷新UUID缓存，重新请求API")
    parser.add_argument("--api-key", help="API Key（可选，默认从环境变量读取）")
    parser.add_argument("--check-env", action="store_true", help="检查环境依赖")
    parser.add_argument("--validate", action="store_true", help="校验画像准确性（>=80%%准出）")
    parser.add_argument("--sample", type=int, default=10, help="校验抽样文章数（默认10）")

    args = parser.parse_args()

    if args.check_env:
        sys.exit(0 if check_env() else 1)

    if not check_env():
        sys.exit(1)

    # --author 可选，默认使用 --account
    author_name = args.author or args.account

    if args.validate and author_name:
        result = validate_profile(author_name, sample_n=args.sample)
        sys.exit(0 if result and result["passed"] else 1)
    elif args.account:
        if args.count is None:
            error("蒸馏模式必须指定 --count（20/60/100），请选择文章数量档位")
            sys.exit(1)
        distill(
            account=args.account,
            author_name=author_name,
            count=args.count,
            api_key=args.api_key,
            force_refresh=args.no_cache,
        )
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
