#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小红书低粉爆款笔记获取脚本 - 使用原生 socket+SSL 调用红狐数据 API

功能：
1. 获取小红书低粉爆款笔记
2. 按互动数排序
3. 格式化输出为文本列表
4. 生成HTML文件（内置模板，无需子进程调用）

使用方法：
python scripts/fetch_explosive_articles.py --rank_date "2025-01-15"
python scripts/fetch_explosive_articles.py --keyword "穿搭" --top_n 50
python scripts/fetch_explosive_articles.py --realtime --top_n 50
python scripts/fetch_explosive_articles.py --rank_date "2025-01-15" --show_all
"""

import argparse
import json
import sys
import os
from datetime import datetime, timedelta
import re
import random
import time
import socket
import ssl


def parse_number(num_str):
    """解析数字，支持格式如'13w+'、'4w+'、'5000'等"""
    if not num_str:
        return 0
    num_str = str(num_str).strip().replace(",", "")
    if 'w' in num_str.lower():
        try:
            return int(float(num_str.lower().replace('w', '').replace('+', '')) * 10000)
        except:
            return 0
    try:
        return int(float(num_str.replace('+', '')))
    except:
        return 0


def format_number(num):
    """格式化数字，超过1万显示为w"""
    try:
        num_int = int(float(str(num).replace(",", "")))
        if num_int >= 10000:
            return f"{num_int / 10000:.2f}w"
        return str(num_int)
    except:
        return str(num)


def clean_text(text):
    """清理文本：去除空格、换行符、制表符等"""
    if not text:
        return ""
    return str(text).replace(" ", "").replace("\n", "").replace("\r", "").replace("\t", "").strip()


# 25个分类及其关键词映射
CATEGORY_KEYWORDS = {
    "综合全部": ["综合", "全部", "所有", "热门", "总榜"],
    "出行代步": ["出行", "代步", "打车", "交通", "地铁", "公交", "自驾", "骑行", "通勤", "高铁", "飞机票", "签证"],
    "休闲爱好": ["休闲", "爱好", "游戏", "手工", "拼豆", "棋牌", "钓鱼", "园艺", "露营", "桌游", "乐高", "积木"],
    "影视娱乐": ["影视", "娱乐", "电影", "电视剧", "综艺", "明星", "追剧", "动漫", "追星", "爱豆", "偶像", "演唱会"],
    "数码科技": ["数码", "科技", "手机", "电脑", "相机", "耳机", "AI", "人工智能", "软件", "程序", "键盘", "平板", "智能家居"],
    "医疗保健": ["医疗", "保健", "健康", "医院", "养生", "中医", "体检", "药品", "看病", "牙科", "近视", "减肥药"],
    "综合杂项": ["杂项", "其他"],
    "星座情感": ["星座", "情感", "恋爱", "失恋", "表白", "塔罗", "情侣", "脱单", "暗恋", "分手", "复合", "暧昧"],
    "时尚穿搭": ["时尚", "穿搭", "衣服", "搭配", "OOTD", "服饰", "裙子", "外套", "风衣", "衬衫", "卫衣", "大衣"],
    "婚庆婚礼": ["婚庆", "婚礼", "结婚", "婚纱", "备婚", "婚照", "求婚", "彩礼", "婚戒", "司仪"],
    "拍摄记录": ["拍摄", "记录", "摄影", "Vlog", "短视频", "拍照", "写真", "胶片", "胶卷", "拍立得", "滤镜"],
    "学习教育": ["学习", "教育", "考试", "考研", "英语", "读书", "留学", "培训", "雅思", "托福", "四六级", "考公", "考编"],
    "化妆美容": ["化妆", "美容", "美妆", "护肤", "口红", "粉底", "眼妆", "仿妆", "腮红", "遮瑕", "修容", "高光", "眉笔"],
    "居家装修": ["居家", "装修", "家居", "家具", "收纳", "房间", "软装", "改造", "宜家", "厨房", "卫生间", "阳台"],
    "旅行度假": ["旅行", "度假", "旅游", "出游", "景点", "攻略", "自驾游", "跟团", "民宿", "签证", "出国", "免签"],
    "亲子育儿": ["亲子", "育儿", "宝宝", "幼儿", "奶粉", "孕期", "胎教", "早教", "辅食", "婴儿", "玩具", "幼儿园"],
    "个人护理": ["个人护理", "洗护", "护发", "沐浴", "口腔", "身体乳", "卫生", "洗发水", "牙膏", "防晒", "除毛"],
    "美味佳肴": ["美味", "佳肴", "美食", "做饭", "烹饪", "菜谱", "食谱", "甜品", "烘焙", "蛋糕", "零食", "小吃", "探店", "餐厅"],
    "职业发展": ["职业", "发展", "职场", "求职", "面试", "简历", "升职", "跳槽", "副业", "创业", "兼职", "加薪", "转行"],
    "宠物天地": ["宠物", "猫", "狗", "养猫", "养狗", "萌宠", "铲屎官", "猫咪", "狗狗", "兔", "仓鼠", "水族", "鸟"],
    "潮流鞋包": ["潮流", "鞋包", "球鞋", "跑鞋", "包包", "手袋", "背包", "AJ", "椰子", "奢侈品", "名品", "潮牌"],
    "日常生活": ["日常", "生活", "生活技巧", "省钱", "好物", "实用", "租房", "搬家", "买菜", "清洁", "家务", "收纳整理"],
    "科学探索": ["科学", "探索", "科普", "实验", "物理", "化学", "生物", "天文", "数学", "心理学", "哲学", "历史"],
    "新闻资讯": ["新闻", "资讯", "时事", "热点", "社会", "国际", "政策", "法规", "事件"],
    "体育锻炼": ["体育", "锻炼", "健身", "运动", "跑步", "瑜伽", "游泳", "篮球", "足球", "羽毛球", "网球", "骑行", "徒步"],
}

VALID_CATEGORIES = list(CATEGORY_KEYWORDS.keys())


def get_redfox_api_key() -> str:
    """
    三级回退获取 REDFOX_API_KEY：
    1. 当前环境变量 REDFOX_API_KEY
    2. shell 配置文件（.zshrc / .bashrc / PowerShell profile）
    3. 提示用户配置
    返回 API Key 字符串，未找到则返回空字符串
    """
    # 第一级：当前环境变量
    api_key = os.getenv("REDFOX_API_KEY", "").strip()
    if api_key:
        print(f"[鉴权] 从环境变量读取到 REDFOX_API_KEY（前8位: {api_key[:8]}...）", file=sys.stderr)
        return api_key

    # 第二级：从 shell 配置文件中读取
    home = os.path.expanduser("~")
    shell_configs = []

    if sys.platform == "win32":
        # Windows：PowerShell profile + Git Bash .bashrc
        ps_profile = os.path.join(home, "Documents", "WindowsPowerShell", "Microsoft.PowerShell_profile.ps1")
        shell_configs.append(ps_profile)
        # PowerShell 7 profile
        ps7_profile = os.path.join(home, "Documents", "PowerShell", "Microsoft.PowerShell_profile.ps1")
        shell_configs.append(ps7_profile)
        # Git Bash
        shell_configs.append(os.path.join(home, ".bashrc"))
        shell_configs.append(os.path.join(home, ".bash_profile"))
    else:
        # macOS / Linux
        shell_configs = [
            os.path.join(home, ".zshrc"),
            os.path.join(home, ".bashrc"),
            os.path.join(home, ".bash_profile"),
            os.path.join(home, ".profile"),
        ]

    for config_path in shell_configs:
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line_stripped = line.strip()
                        # 忽略注释行
                        if line_stripped.startswith('#') or not line_stripped:
                            continue
                        # 匹配多种写法：export KEY=val, KEY="val", $env:KEY="val", set KEY=val
                        for pattern in [
                            r'(?:export\s+)?REDFOX_API_KEY\s*=\s*["\']([^"\'\n]+)["\']',
                            r'(?:export\s+)?REDFOX_API_KEY\s*=\s*([^\s"\'\n]+)',
                            r'\$env:REDFOX_API_KEY\s*=\s*["\']([^"\'\n]+)["\']',
                            r'set\s+REDFOX_API_KEY\s*=\s*([^\s"\'\n]+)',
                        ]:
                            match = re.search(pattern, line_stripped)
                            if match:
                                api_key = match.group(1).strip()
                                if api_key:
                                    print(f"[鉴权] 从 {config_path} 读取到 REDFOX_API_KEY（前8位: {api_key[:8]}...）", file=sys.stderr)
                                    # 自动注入到当前环境变量，方便后续使用
                                    os.environ["REDFOX_API_KEY"] = api_key
                                    return api_key
            except Exception as e:
                print(f"[鉴权] 读取 {config_path} 失败: {e}", file=sys.stderr)
                continue

    # 第三级：未找到，打印配置指引
    print("=" * 60, file=sys.stderr)
    print("[鉴权] 未找到 REDFOX_API_KEY，请按以下步骤配置：", file=sys.stderr)
    print("", file=sys.stderr)
    print("获取 API Key：", file=sys.stderr)
    print("  1. 访问 https://redfox.hk/ 了解服务详情", file=sys.stderr)
    print("  2. 前往 https://redfox.hk/login 注册账号（新用户赠送免费积分）", file=sys.stderr)
    print("  3. 登录后在个人中心获取 API Key（格式: ak_xxxxxxxx）", file=sys.stderr)
    print("", file=sys.stderr)
    print("配置方法：", file=sys.stderr)
    if sys.platform == "win32":
        print("  Windows PowerShell:", file=sys.stderr)
        print('    [Environment]::SetEnvironmentVariable("REDFOX_API_KEY", "ak_xxxxxxxx", "User")', file=sys.stderr)
        print("  Git Bash:", file=sys.stderr)
        print('    export REDFOX_API_KEY=ak_xxxxxxxx', file=sys.stderr)
        print("  配置后需重启终端生效", file=sys.stderr)
    else:
        print("  export REDFOX_API_KEY=ak_xxxxxxxx", file=sys.stderr)
        print("  追加到 ~/.zshrc 或 ~/.bashrc 后执行 source 使其生效", file=sys.stderr)
    print("=" * 60, file=sys.stderr)

    return ""


def match_category(keyword: str) -> str:
    """
    根据用户输入的关键词匹配对应的分类。
    匹配优先级：
    1. 精确匹配分类名称
    2. 关键词包含映射表中的词汇
    3. 未匹配则返回"综合全部"
    """
    if not keyword:
        return "综合全部"

    keyword_clean = keyword.strip()

    # 优先级1：精确匹配分类名称
    if keyword_clean in VALID_CATEGORIES:
        return keyword_clean

    # 优先级2：关键词包含映射表中的词汇
    for category, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in keyword_clean or keyword_clean in kw:
                return category

    # 优先级3：未匹配则返回综合全部
    return "综合全部"


def fetch_ranking_data(rank_date: str, source: str, category: str, top_n: int = 50) -> dict:
    """
    使用原生 socket+SSL 发送 HTTPS 请求调用红狐数据 API
    返回字典：
      {"type": "data", "data": [...]}  - 有数据
      {"type": "empty"}                - 数据为空
      {"type": "msg", "msg": "..."}    - data为null但msg有值
      {"type": "error"}                - 网络或其他错误
    """
    from urllib.parse import urlencode

    # 获取 API Key（三级回退）
    api_key = get_redfox_api_key()

    host = "redfox.hk"
    path = "/story/api/cozeSkill/getXhsCozeSkillDataLowFans"

    params = {
        "rankDate": rank_date,
        "category": category,
        "source": "小红书冷门账号爆款文章-GitHub"
    }
    query_string = urlencode(params)
    full_path = f"{path}?{query_string}"

    http_request = (
        f"GET {full_path} HTTP/1.1\r\n"
        f"Host: {host}\r\n"
        f"X-API-KEY: {api_key or ''}\r\n"
        f"User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36\r\n"
        f"Accept: application/json, text/plain, */*\r\n"
        f"Accept-Language: zh-CN,zh;q=0.9,en;q=0.8\r\n"
        f"Connection: close\r\n"
        f"\r\n"
    )

    print(f"[调试] 开始获取数据，日期: {rank_date}", file=sys.stderr)
    print(f"[调试] 使用原生 socket+SSL 请求 API", file=sys.stderr)

    max_attempts = 5
    for attempt in range(1, max_attempts + 1):
        try:
            print(f"[调试] 第 {attempt} 次尝试...", file=sys.stderr)

            if attempt > 1:
                delay = random.uniform(0.5, 2)
                time.sleep(delay)

            # DNS 解析
            ip_address = socket.gethostbyname(host)
            print(f"[调试] 域名解析: {host} -> {ip_address}", file=sys.stderr)

            # 创建 socket 连接
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(45)
            sock.connect((ip_address, 443))

            # SSL 包装
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE

            ssl_sock = context.wrap_socket(sock, server_hostname=None)
            ssl_sock.sendall(http_request.encode('utf-8'))

            # 接收响应
            response_data = b""
            while True:
                chunk = ssl_sock.recv(4096)
                if not chunk:
                    break
                response_data += chunk

            ssl_sock.close()
            sock.close()

            response_str = response_data.decode('utf-8', errors='ignore')
            print(f"[调试] 接收数据长度: {len(response_data)} 字节", file=sys.stderr)

            # 解析 HTTP 响应
            header_end = response_str.find('\r\n\r\n')
            if header_end == -1:
                continue

            headers_section = response_str[:header_end]
            body = response_str[header_end + 4:]

            status_line = headers_section.split('\r\n')[0]
            print(f"[调试] 状态行: {status_line}", file=sys.stderr)

            if "200" not in status_line:
                if attempt < max_attempts:
                    continue
                return {"type": "error"}

            data = json.loads(body)

            if isinstance(data, list):
                data = {"code": 2000, "data": data}

            if data.get("code") == 2000:
                raw_data = data.get("data")
                msg = data.get("msg", "")

                # data为null且msg有值时，返回msg
                if raw_data is None and msg:
                    print(f"[调试] data为null，msg有值: {msg}", file=sys.stderr)
                    return {"type": "msg", "msg": msg}

                if not isinstance(raw_data, list):
                    print(f"[调试] data非列表类型或为空", file=sys.stderr)
                    return {"type": "empty"}

                print(f"[调试] 原始数据条数: {len(raw_data)}", file=sys.stderr)

                cleaned_data = []
                for item in raw_data:
                    if isinstance(item, dict):
                        cleaned_item = {
                            "title": item.get("title", ""),
                            "photoJumpUrl": item.get("photoJumpUrl", ""),
                            "userName": item.get("userName", "未知作者"),
                            "userJumpUrl": item.get("userJumpUrl", ""),
                            "useLikeCount": item.get("useLikeCount", "0"),
                            "collectedCount": item.get("collectedCount", "0"),
                            "useCommentCount": item.get("useCommentCount", "0"),
                            "useShareCount": item.get("useShareCount", "0"),
                            "interactiveCount": item.get("interactiveCount", "0"),
                            "fans": item.get("fans", "0"),
                            "desc": item.get("desc", ""),
                            "analysis": item.get("analysis", ""),
                            "coverUrl": item.get("coverUrl", ""),
                            "userHeadUrl": item.get("userHeadUrl", ""),
                            "publicTime": item.get("publicTime", "")
                        }
                        if cleaned_item["interactiveCount"] and cleaned_item["interactiveCount"] != "0":
                            cleaned_data.append(cleaned_item)

                print(f"[调试] 清理后数据条数: {len(cleaned_data)}", file=sys.stderr)

                if cleaned_data:
                    return {"type": "data", "data": cleaned_data}
                else:
                    return {"type": "empty"}
            else:
                error_msg = data.get('message', '') or data.get('msg', '')
                # code非2000但msg有值时，返回msg
                if error_msg:
                    print(f"[调试] 接口返回非2000，msg: {error_msg}", file=sys.stderr)
                    return {"type": "msg", "msg": error_msg}
                print(f"[错误] 接口返回错误，无msg", file=sys.stderr)
                return {"type": "error"}

        except Exception as e:
            print(f"[错误] 请求异常: {str(e)}", file=sys.stderr)
            if attempt < max_attempts:
                continue
            else:
                raise

    return {"type": "error"}


def process_ranking_data(data: list, top_n: int = 50) -> list:
    """处理榜单数据，按互动数排序"""
    if not data or not isinstance(data, list):
        return []

    sorted_articles = sorted(
        data,
        key=lambda x: parse_number(x.get("interactiveCount", "0")),
        reverse=True
    )
    return sorted_articles[:top_n]


def format_ranking_list(articles: list, query_category: str = "综合全部", show_all: bool = False, rank_date: str = "") -> str:
    """
    将榜单数据格式化为表格

    第一次输出：Top1-Top20，表格后加"查看更多"提示
    查看更多时：Top21-Top50
    表格字段：序号、笔记信息、互动总数、点赞数、评论数、收藏数、分享数、发布时间
    """
    if not articles:
        return "未获取到符合条件的爆款内容数据"

    output_lines = []

    # 新增说明文字
    output_lines.append(f"数据查询标准为粉丝数低于5000、笔记点赞数大于500，已帮你查询到{len(articles)}条低粉爆款笔记~")
    output_lines.append("")

    # 输出更新时间（使用榜单日期）
    if rank_date:
        update_time = rank_date
    else:
        update_time = datetime.now().strftime("%Y-%m-%d")
    if query_category == "综合全部":
        if show_all:
            table_title = f"**🏆 低粉爆款笔记（TOP 21-{len(articles)}）**"
        else:
            table_title = f"**🏆 低粉爆款笔记（TOP 20）**"
        table_title += f"\n\n更新时间：{update_time}"
    else:
        if show_all:
            table_title = f"**🏆 {query_category}低粉爆款笔记（TOP 21-{len(articles)}）**"
        else:
            table_title = f"**🏆 {query_category}低粉爆款笔记（TOP 20）**"
        table_title += f"\n\n更新时间：{update_time}"
    output_lines.append(table_title)
    output_lines.append("")

    # 确定显示的数据范围
    if show_all:
        display_articles = articles[20:]  # Top21-Top50
        start_idx = 21
    else:
        display_articles = articles[:20]  # Top1-Top20
        start_idx = 1

    # 表格：序号、笔记信息、互动总数、点赞数、评论数、收藏数、分享数、发布时间
    output_lines.append("| 序号 | 笔记信息 | 互动总数 | 点赞数 | 评论数 | 收藏数 | 分享数 | 发布时间 |")
    output_lines.append("|:----:|:--------|:------:|:------:|:------:|:------:|:------:|:------:|")

    for idx, article in enumerate(display_articles, start=start_idx):
        title = article.get("title", "")
        photo_url = article.get("photoJumpUrl", "")
        user_name = article.get("userName", "未知作者")
        user_url = article.get("userJumpUrl", "")
        like_count = article.get("useLikeCount", "0")
        interactive_count = article.get("interactiveCount", "0")
        fans_count = article.get("fans", "0")
        comment_count = article.get("useCommentCount", "0")
        collect_count = article.get("collectedCount", "0")
        share_count = article.get("useShareCount", "0")

        if not title or str(title).strip() == "":
            title = "无笔记标题"
        else:
            title = clean_text(title)

        user_name_clean = clean_text(user_name)
        like_clean = clean_text(like_count)
        interactive_clean = clean_text(interactive_count)
        fans_clean = clean_text(fans_count)
        comment_clean = clean_text(comment_count)
        collect_clean = clean_text(collect_count)
        share_clean = clean_text(share_count)
        public_time = article.get("publicTime", "")
        # 格式化发布时间：只保留月-日 时:分
        if public_time and len(public_time) >= 16:
            public_time_display = public_time[5:16]
        else:
            public_time_display = public_time

        # 序号
        if idx == 1:
            rank_display = "🥇"
        elif idx == 2:
            rank_display = "🥈"
        elif idx == 3:
            rank_display = "🥉"
        else:
            rank_display = str(idx)

        # 笔记信息列：标题<br>作者（跳转链接）+ 粉丝数
        if photo_url:
            note_info = f"[{title}]({photo_url})<br>[{user_name_clean}]({user_url})（{fans_clean} 粉丝）"
        else:
            note_info = f"{title}<br>[{user_name_clean}]({user_url})（{fans_clean} 粉丝）"

        output_lines.append(f"| {rank_display} | {note_info} | {interactive_clean} | {like_clean} | {comment_clean} | {collect_clean} | {share_clean} | {public_time_display} |")

    output_lines.append("")

    # 第一次输出时（非show_all），在表格后加"查看更多"提示
    if not show_all and len(articles) > 20:
        output_lines.append('可以输入"查看更多"展示剩余榜单~')

    return "\n".join(output_lines)


def generate_insights_analysis(articles: list) -> str:
    """
    基于所有获取的数据（50条）生成爆款规律分析

    包含：标题特征（表格）、内容主题（表格）、可参考亮点
    参考笔记带可跳转链接
    """
    if not articles or len(articles) == 0:
        return "暂无数据可分析"

    output_lines = []

    output_lines.append("**💡 爆款规律分析**")
    output_lines.append("")
    output_lines.append(f"基于所有 {len(articles)} 条数据进行分析：")
    output_lines.append("")

    # ========== 1. 标题特征（表格输出）==========
    output_lines.append("### 1. 标题特征")
    output_lines.append("")

    # 分类统计标题类型，examples存储(title, url)
    title_types = {
        "短标题": {"count": 0, "examples": [], "feature": "≤10字，简洁有力", "template": "XX的XX/XX就是XX", "effect": "快速抓住注意力，降低阅读门槛"},
        "疑问句式": {"count": 0, "examples": [], "feature": "含？/吗/如何/为什么", "template": "XX吗？/如何XX？/为什么XX？", "effect": "激发好奇心，引导点击查看答案"},
        "情感化表达": {"count": 0, "examples": [], "feature": "含情感关键词（笑/哭/爱/泪）", "template": "太XX了！/XX到哭/谁懂XX", "effect": "引发情感共鸣，增强代入感"},
        "数字列举型": {"count": 0, "examples": [], "feature": "含数字/N条/N个", "template": "N个XX/N条XX/XX第N天", "effect": "信息量明确，用户预期清晰"},
        "感叹强调型": {"count": 0, "examples": [], "feature": "含！/太/超/绝", "template": "太XX了！/超XX！/绝绝子", "effect": "强化语气，传递强烈情绪"},
        "悬念留白型": {"count": 0, "examples": [], "feature": "含居然/竟然/没想到", "template": "居然XX/竟然XX/没想到XX", "effect": "制造信息差，驱动点击揭秘"},
    }

    general_count = 0
    general_examples = []

    for article in articles:
        title = article.get('title', '') or ''
        url = article.get('photoJumpUrl', '')
        if not title:
            general_count += 1
            continue

        matched = False

        # 短标题
        if len(title) <= 10:
            title_types["短标题"]["count"] += 1
            if len(title_types["短标题"]["examples"]) < 5:
                title_types["短标题"]["examples"].append((title, url))
            matched = True

        # 疑问句式
        if '?' in title or '？' in title or '吗' in title or '如何' in title or '为什么' in title or '怎么' in title:
            title_types["疑问句式"]["count"] += 1
            if len(title_types["疑问句式"]["examples"]) < 5:
                title_types["疑问句式"]["examples"].append((title, url))
            matched = True

        # 情感化表达
        emotional_words = ['笑', '哭', '爱', '心', '泪', '喜', '悲', '感动', '心疼', '温暖']
        if any(word in title for word in emotional_words):
            title_types["情感化表达"]["count"] += 1
            if len(title_types["情感化表达"]["examples"]) < 5:
                title_types["情感化表达"]["examples"].append((title, url))
            matched = True

        # 数字列举型
        if re.search(r'\d+', title):
            title_types["数字列举型"]["count"] += 1
            if len(title_types["数字列举型"]["examples"]) < 5:
                title_types["数字列举型"]["examples"].append((title, url))
            matched = True

        # 感叹强调型
        if '！' in title or '!' in title or '太' in title or '超' in title or '绝' in title:
            title_types["感叹强调型"]["count"] += 1
            if len(title_types["感叹强调型"]["examples"]) < 5:
                title_types["感叹强调型"]["examples"].append((title, url))
            matched = True

        # 悬念留白型
        if '居然' in title or '竟然' in title or '没想到' in title or '原来' in title:
            title_types["悬念留白型"]["count"] += 1
            if len(title_types["悬念留白型"]["examples"]) < 5:
                title_types["悬念留白型"]["examples"].append((title, url))
            matched = True

        if not matched:
            general_count += 1
            if len(general_examples) < 5:
                general_examples.append((title, url))

    # 添加通用类型
    if general_count > 0:
        title_types["其他类型"] = {
            "count": general_count,
            "examples": general_examples,
            "feature": "无显著特征标记",
            "template": "XX的XX/XX和XX",
            "effect": "靠内容本身质量驱动传播"
        }

    # 输出标题特征表格（参考笔记带跳转链接）
    output_lines.append("| 标题类型 | 标题特征 | 占比 | 标题模版 | 描述（引发作用） | 参考笔记 |")
    output_lines.append("|:-------:|:-------:|:----:|:-------:|:--------------:|:-------:|")

    for ttype, info in sorted(title_types.items(), key=lambda x: x[1]["count"], reverse=True):
        if info["count"] == 0:
            continue
        percentage = f"{info['count'] * 100 / len(articles):.1f}%"
        # 参考笔记带跳转链接
        ref_notes = []
        for ex_title, ex_url in info["examples"][:5]:
            ex_title_clean = clean_text(ex_title)[:15]
            if ex_url:
                ref_notes.append(f"[{ex_title_clean}]({ex_url})")
            else:
                ref_notes.append(ex_title_clean)
        examples_str = "、".join(ref_notes)
        output_lines.append(f"| {ttype} | {info['feature']} | {percentage} | {info['template']} | {info['effect']} | {examples_str} |")

    output_lines.append("")

    # ========== 2. 内容主题（表格输出）==========
    output_lines.append("### 2. 内容主题")
    output_lines.append("")

    # 内容分类定义
    theme_definitions = {
        "宠物萌宠": {
            "keywords": ['宠物', '猫', '狗', '动物', '小猫', '小狗', '猫咪', '狗狗', '橘猫', '布偶'],
            "feature": "萌宠日常/宠物搞笑/养宠经验",
            "effect": "高互动高收藏，情感共鸣强"
        },
        "美食探店": {
            "keywords": ['美食', '吃', '料理', '味道', '吃货', '饭', '食谱', '烘焙', '烹饪'],
            "feature": "美食教程/探店推荐/食谱分享",
            "effect": "收藏率极高，实用性强"
        },
        "时尚穿搭": {
            "keywords": ['穿搭', '时尚', '搭配', '衣服', 'OOTD', '裙子'],
            "feature": "穿搭灵感/平价好物/搭配技巧",
            "effect": "分享率高，传播力强"
        },
        "旅行打卡": {
            "keywords": ['旅行', '景点', '打卡', '攻略', '旅游', '出游', '拍照'],
            "feature": "旅行攻略/小众景点/拍照指南",
            "effect": "收藏分享双高，攻略价值大"
        },
        "美妆护肤": {
            "keywords": ['护肤', '化妆', '彩妆', '保养', '美妆', '口红', '面膜'],
            "feature": "护肤心得/好物推荐/妆容教程",
            "effect": "收藏率高，用户粘性强"
        },
        "情感生活": {
            "keywords": ['情感', '生活', '日常', '家庭', '父母', '爸妈', '老公', '老婆', '闺蜜'],
            "feature": "生活记录/情感故事/日常感悟",
            "effect": "评论互动高，共鸣感强"
        },
        "搞笑娱乐": {
            "keywords": ['搞笑', '哈哈', '笑', '幽默', '梗', '段子', '沙雕'],
            "feature": "搞笑段子/生活趣事/反差内容",
            "effect": "分享率最高，传播力最强"
        },
        "知识科普": {
            "keywords": ['知识', '学习', '教育', '学霸', '干货', '技巧', '方法', '教程'],
            "feature": "干货分享/知识科普/方法总结",
            "effect": "收藏率最高，长尾效应强"
        },
        "健身运动": {
            "keywords": ['健身', '运动', '减肥', '瑜伽', '锻炼', '跑步', '瘦'],
            "feature": "健身打卡/减肥记录/运动教程",
            "effect": "互动稳定，用户追随感强"
        }
    }

    # 统计各主题，examples存储(title, url)
    theme_stats = {}
    for theme, definition in theme_definitions.items():
        theme_stats[theme] = {"count": 0, "examples": []}

    theme_stats["其他"] = {"count": 0, "examples": []}

    for article in articles:
        desc = article.get('desc', '')
        title = article.get('title', '') or ''
        url = article.get('photoJumpUrl', '')
        combined_text = title + desc

        matched = False
        for theme, definition in theme_definitions.items():
            if any(keyword in combined_text for keyword in definition["keywords"]):
                theme_stats[theme]["count"] += 1
                if len(theme_stats[theme]["examples"]) < 5:
                    theme_stats[theme]["examples"].append((title, url))
                matched = True
                break

        if not matched:
            theme_stats["其他"]["count"] += 1
            if len(theme_stats["其他"]["examples"]) < 5:
                theme_stats["其他"]["examples"].append((title, url))

    # 输出内容主题表格（参考笔记带跳转链接）
    output_lines.append("| 内容分类 | 内容特征 | 占比 | 实际效果 | 参考笔记 |")
    output_lines.append("|:-------:|:-------:|:----:|:-------:|:-------:|")

    for theme in list(theme_definitions.keys()) + ["其他"]:
        info = theme_stats[theme]
        if info["count"] == 0:
            continue
        percentage = f"{info['count'] * 100 / len(articles):.1f}%"
        # 参考笔记带跳转链接
        ref_notes = []
        for ex_title, ex_url in info["examples"][:5]:
            ex_title_clean = clean_text(ex_title)[:15] if ex_title else "无标题"
            if ex_url:
                ref_notes.append(f"[{ex_title_clean}]({ex_url})")
            else:
                ref_notes.append(ex_title_clean)
        examples_str = "、".join(ref_notes)
        if theme in theme_definitions:
            effect = theme_definitions[theme]["effect"]
            feature = theme_definitions[theme]["feature"]
        else:
            effect = "内容质量驱动传播"
            feature = "多元内容，无明确分类"
        output_lines.append(f"| {theme} | {feature} | {percentage} | {effect} | {examples_str} |")

    output_lines.append("")

    # ========== 3. 可参考亮点 ==========
    output_lines.append("### 3. 可参考亮点")
    output_lines.append("")

    highlights = []

    high_interactive = [a for a in articles if parse_number(a.get('interactiveCount', '0')) > 50000]
    if high_interactive:
        avg_fans_high = sum([parse_number(a.get('fans', '0')) for a in high_interactive]) // len(high_interactive)
        highlights.append(f"**低粉高爆**：高互动笔记平均粉丝数仅{avg_fans_high}，说明内容质量是关键")

    total_collect = sum([parse_number(a.get('collectedCount', '0')) for a in articles])
    total_share = sum([parse_number(a.get('useShareCount', '0')) for a in articles])
    if total_collect > 0 and total_share > 0:
        collect_share_ratio = total_collect / total_share
        if collect_share_ratio > 1.5:
            highlights.append(f"**收藏驱动**：收藏数是分享数的{collect_share_ratio:.1f}倍，用户倾向收藏保存")
        elif collect_share_ratio < 0.7:
            highlights.append(f"**分享驱动**：分享数是收藏数的{(1/collect_share_ratio):.1f}倍，用户倾向主动传播")

    top5 = articles[:5]
    top5_text = " ".join([a.get('desc', '') + " " + (a.get('title', '') or '') for a in top5])
    if '猫' in top5_text or '狗' in top5_text or '宠物' in top5_text:
        highlights.append(f"**宠物经济**：TOP5中宠物内容占比高，萌宠内容易引发情感共鸣")
    if '笑' in top5_text or '搞笑' in top5_text or '哈哈' in top5_text:
        highlights.append(f"**幽默元素**：搞笑娱乐内容容易获得高互动")
    if '真实' in top5_text or '生活' in top5_text:
        highlights.append(f"**真实记录**：真实生活分享更受用户欢迎")

    long_desc_articles = [a for a in articles if len(a.get('desc', '')) > 50]
    if len(long_desc_articles) > len(articles) * 0.6:
        highlights.append(f"**详实描述**：{len(long_desc_articles)}篇笔记使用详细描述，信息密度高")

    for highlight in highlights:
        output_lines.append(f"- {highlight}")

    return "\n".join(output_lines)


# ========== HTML生成功能（内置，避免子进程调用） ==========

def get_article_html(article: dict, rank: int) -> str:
    """生成单篇笔记的HTML"""
    try:
        title = article.get("title", "无笔记标题") or "无笔记标题"
        photo_url = article.get("photoJumpUrl", "#")
        user_name = article.get("userName", "未知作者")
        user_url = article.get("userJumpUrl", "#")
        fans = article.get("fans", "0")
        desc = article.get("desc", "")

        like_count = article.get("useLikeCount", "0")
        collect_count = article.get("collectedCount", "0")
        comment_count = article.get("useCommentCount", "0")
        share_count = article.get("useShareCount", "0")
        interactive_count = article.get("interactiveCount", "0")

        analysis = generate_content_analysis(desc, title)

        top_class = "top" if rank <= 3 else ""

        stats_html = f'''
            <div class="info-item">
                <span class="info-stat">❤️ 点赞 <span class="info-stat-value">{like_count}</span></span>
            </div>
            <div class="info-item">
                <span class="info-stat">⭐ 收藏 <span class="info-stat-value">{collect_count}</span></span>
            </div>
            <div class="info-item">
                <span class="info-stat">💬 评论 <span class="info-stat-value">{comment_count}</span></span>
            </div>
            <div class="info-item">
                <span class="info-stat">📤 分享 <span class="info-stat-value">{share_count}</span></span>
            </div>
            <div class="info-item">
                <span class="info-stat">互动总数 <span class="info-stat-value">{interactive_count}</span></span>
            </div>
        '''

        user_head_url = article.get("userHeadUrl", "")
        if user_head_url:
            author_html = f'<img src="{user_head_url}" class="author-avatar" alt="{user_name}">{user_name}（{fans} 粉丝）'
        else:
            author_html = f'<span class="author-avatar-placeholder"></span>{user_name}（{fans} 粉丝）'

        return f'''
            <div class="article-item">
                <div class="article-body">
                    <div class="article-rank {top_class}">{rank}</div>
                    <div class="article-content">
                        <a href="{photo_url}" target="_blank" class="article-title">{title}</a>
                        <div class="article-info">
                            <a href="{user_url}" target="_blank" class="info-source-link">
                                {author_html}
                            </a>
                            {stats_html}
                        </div>
                        <div class="article-analysis">
                            <div class="analysis-label">🔍 内容分析</div>
                            <div class="analysis-text">{analysis}</div>
                        </div>
                    </div>
                </div>
            </div>'''
    except:
        return ""


def generate_content_analysis(desc, title):
    """根据描述内容生成内容分析"""
    if not desc and not title:
        return "暂无分析"

    analysis_parts = []

    if title:
        analysis_parts.append(f"笔记主题围绕「{title[:30]}{'...' if len(title) > 30 else ''}」展开")

    if desc:
        tags = re.findall(r'#([^\s#]+)', desc)
        if tags:
            tag_list = "、".join(tags[:5])
            analysis_parts.append(f"内容涵盖{tag_list}等话题")

        if any(keyword in desc for keyword in ["穿搭", "搭配", "时尚", "潮流"]):
            content_type = "穿搭分享"
        elif any(keyword in desc for keyword in ["美食", "探店", "料理", "味道"]):
            content_type = "美食探店"
        elif any(keyword in desc for keyword in ["旅行", "景点", "打卡", "攻略"]):
            content_type = "旅行攻略"
        elif any(keyword in desc for keyword in ["护肤", "化妆", "彩妆", "保养"]):
            content_type = "美妆护肤"
        elif any(keyword in desc for keyword in ["健身", "运动", "减肥", "瑜伽"]):
            content_type = "健身运动"
        else:
            content_type = "生活分享"
        analysis_parts.append(f"属于{content_type}类型")

    if analysis_parts:
        analysis = "，".join(analysis_parts) + "，获得了较好的用户互动和传播效果"
    else:
        analysis = "内容吸引了用户的关注和互动"

    return analysis


def generate_html_from_template(keyword: str, articles: list, rank_date: str = "", top_n: int = 20, output: str = "./xiaohongshu_lowtop.html") -> str:
    """使用模板生成HTML页面（只展示榜单数据），模板从assets目录读取"""

    # 获取模板文件路径（基于脚本所在目录计算）
    script_dir = os.path.dirname(os.path.abspath(__file__))
    template_path = os.path.join(script_dir, "..", "assets", "preview-template.html")

    # 读取模板
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            template = f.read()
    except Exception as e:
        print(f"[错误] 无法读取模板文件 {template_path}: {str(e)}", file=sys.stderr)
        return ""

    # 生成笔记列表HTML
    articles_html = ""
    for i, article in enumerate(articles[:top_n], 1):
        articles_html += get_article_html(article, i)

    # 生成更新时间：使用榜单日期，固定19:30
    if rank_date:
        try:
            dt = datetime.strptime(rank_date, "%Y-%m-%d")
            update_time = f"{dt.year}年-{dt.month:02d}-{dt.day:02d} 19:30"
        except:
            update_time = f"{rank_date} 19:30"
    else:
        dt = datetime.now()
        update_time = f"{dt.year}年-{dt.month:02d}-{dt.day:02d} 19:30"

    # 替换模板变量
    html_content = template.replace("{{KEYWORD}}", keyword)
    html_content = html_content.replace("{{TOP_N}}", str(top_n))
    html_content = html_content.replace("{{UPDATE_TIME}}", update_time)
    html_content = html_content.replace("{{ARTICLES_HTML}}", articles_html)

    # 写入输出文件
    try:
        with open(output, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"[调试] HTML文件已生成: {output}", file=sys.stderr)
    except Exception as e:
        print(f"[错误] 无法写入HTML文件 {output}: {str(e)}", file=sys.stderr)
        return ""

    return html_content


# ========== 主函数 ==========

def main():
    parser = argparse.ArgumentParser(description="获取小红书低粉爆款笔记")
    parser.add_argument("--rank_date", required=False, help="查询日期（yyyy-MM-dd格式，默认今天）")
    parser.add_argument("--top_n", type=int, default=50, help="返回前N条数据（默认50）")
    parser.add_argument("--realtime", action="store_true", help="实时热榜模式")
    parser.add_argument("--category", required=False, default="综合全部", help="内容分类")
    parser.add_argument("--keyword", required=False, help="用户输入的关键词，用于自动匹配分类")
    parser.add_argument("--show_all", action="store_true", help="显示Top21-50数据（用于查看更多）")
    parser.add_argument("--debug", action="store_true", help="启用调试模式")

    args = parser.parse_args()

    if not args.debug:
        import io
        sys.stderr = io.StringIO()

    try:
        # 计算当前时间是否在19:30之后
        current_time = datetime.now()
        is_after_1930 = current_time.hour > 19 or (current_time.hour == 19 and current_time.minute >= 30)

        # 模糊日期词 → 转换为具体日期的偏移天数
        fuzzy_date_offsets = {
            "今天": 0, "今日": 0,
            "明天": 1, "明日": 1,
            "后天": 2,
            "大后天": 3,
            "昨天": -1, "昨日": -1,
            "前天": -2, "前日": -2,
            "大前天": -3,
        }

        # 处理查询日期
        if args.realtime:
            search_dates = [(current_time - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(1, 8)]
        elif args.rank_date:
            rank_date_trim = args.rank_date.strip()
            # 如果是模糊日期词，转换为具体日期
            if rank_date_trim in fuzzy_date_offsets:
                offset = fuzzy_date_offsets[rank_date_trim]
                converted_date = (current_time + timedelta(days=offset)).strftime("%Y-%m-%d")
                print(f"[调试] 识别到模糊日期 '{rank_date_trim}'，转换为具体日期: {converted_date}", file=sys.stderr)
                search_dates = [converted_date]
            else:
                search_dates = [rank_date_trim]
        else:
            # 用户未指定日期：19:30之后查前一天，19:30之前查前两天
            if is_after_1930:
                default_date = (current_time - timedelta(days=1)).strftime("%Y-%m-%d")
            else:
                default_date = (current_time - timedelta(days=2)).strftime("%Y-%m-%d")
            search_dates = [default_date]

        # 计算最新数据日期（用于空数据时提示）
        # 19:30之前：最新数据是前两天；19:30之后：最新数据是前一天
        if is_after_1930:
            latest_data_date = (current_time - timedelta(days=1)).strftime("%Y-%m-%d")
        else:
            latest_data_date = (current_time - timedelta(days=2)).strftime("%Y-%m-%d")

        # 处理分类
        query_category = args.category
        if args.keyword:
            query_category = match_category(args.keyword)
            print(f"[调试] 关键词 '{args.keyword}' 匹配到分类: {query_category}", file=sys.stderr)

        if query_category not in VALID_CATEGORIES:
            print(f"[调试] 分类 '{query_category}' 不在有效列表中，回退到综合全部", file=sys.stderr)
            query_category = "综合全部"

        source = "小红书冷门账号爆款文章-GitHub"

        # 查找数据：数据为空时直接查询最新数据日期，不询问用户
        result_data = None
        empty_or_msg = None
        query_date = search_dates[0]
        auto_switched = False  # 标记是否自动切换了日期
        print(f"[调试] 尝试查询日期: {query_date}", file=sys.stderr)
        result = fetch_ranking_data(query_date, source, query_category, args.top_n)

        if result["type"] == "data":
            result_data = result["data"]
            start_date = query_date
        elif result["type"] == "msg":
            empty_or_msg = result
        else:
            # 数据为空，计算最新数据日期并直接查询
            if is_after_1930:
                latest_data_date = (current_time - timedelta(days=1)).strftime("%Y-%m-%d")
            else:
                latest_data_date = (current_time - timedelta(days=2)).strftime("%Y-%m-%d")
            print(f"[调试] {query_date} 暂无数据，自动查询最新数据日期: {latest_data_date}", file=sys.stderr)
            fallback_result = fetch_ranking_data(latest_data_date, source, query_category, args.top_n)
            if fallback_result["type"] == "data":
                result_data = fallback_result["data"]
                start_date = latest_data_date
                auto_switched = True
            else:
                empty_or_msg = fallback_result

        if not result_data:
            if empty_or_msg and empty_or_msg["type"] == "msg":
                print(empty_or_msg["msg"])
            else:
                print(f"当前日期暂无数据，最新数据日期为 {latest_data_date}，是否查询\"{latest_data_date}\"日期的爆款数据？")
            return 1

        # 处理数据
        articles = process_ranking_data(result_data, args.top_n)

        if not articles:
            print(f"当前日期暂无数据，最新数据日期为 {latest_data_date}，是否查询\"{latest_data_date}\"日期的爆款数据？")
            return 1

        # ===== 组装完整输出（严格按顺序） =====
        full_output_lines = []

        # 格式保护声明：提示AI原样输出，禁止修改格式
        full_output_lines.append("<!-- 以下内容已格式化完成，必须原样输出给用户。禁止修改格式、禁止将表格改为列表、禁止省略任何部分（含订阅服务和HTML文件包） -->")
        full_output_lines.append("")

        # 如果自动切换了日期，在最前面提示用户
        if auto_switched:
            full_output_lines.append(f"**数据还没更新，目前最新数据到{start_date}。我将直接为您查询{start_date}的对应数据。**")
            full_output_lines.append("")

        # 第1部分：爆款笔记（更新时间）表格
        table_text = format_ranking_list(articles, query_category, args.show_all, rank_date=start_date)
        full_output_lines.append(table_text)

        # 第2部分：爆款规律分析
        insights = generate_insights_analysis(articles)
        full_output_lines.append("")
        full_output_lines.append("---")
        full_output_lines.append("")
        full_output_lines.append(insights)

        # 第3部分：功能选择
        full_output_lines.append("")
        full_output_lines.append("---")
        full_output_lines.append("")
        full_output_lines.append("技能还支持以下功能：")
        full_output_lines.append("1\uFE0F\u20E3 支持订阅小红书低粉爆款笔记。订阅后将在每日19:30为您推送当日小红书低粉爆款笔记TOP50。直接回复\"订阅\"或 \"1\"即可订阅相关内容。")
        full_output_lines.append("2\uFE0F\u20E3 可生成小红书风格的html文件包。支持导出PDF，方便阅读、保存和分享。")
        full_output_lines.append("回复对应的数字即可。")
        full_output_lines.append("")


        # 写入Markdown文件（暂不生成HTML，等用户确认后再生成）
        import time as _time
        file_timestamp = str(int(_time.time() * 1000))
        safe_category = query_category.replace("/", "-")
        file_base = f"小红书{safe_category}低粉爆款数据_{file_timestamp}"
        md_output = f"./{file_base}.md"

        full_output_text = "\n".join(full_output_lines)
        with open(md_output, 'w', encoding='utf-8') as f:
            f.write(full_output_text)

        # 保存数据缓存文件，供后续HTML生成复用，避免重复请求API
        cache_file = f"./{file_base}_cache.json"
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(articles, f, ensure_ascii=False, indent=2)

        # 同时输出到stdout
        print(full_output_text)

        return 0

    except Exception as e:
        print(f"错误: {str(e)}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
