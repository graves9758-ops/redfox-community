#!/usr/bin/env python3
"""
小红书热门数据查询脚本
- 接口地址：https://redfox.hk/story/api/cozeSkill/getXhsCozeSkillData
- 认证方式：X-API-KEY（通过环境变量 REDFOX_API_KEY 获取）
"""

import os
import sys
import re
import argparse
import json
import time
import platform
import subprocess
from datetime import datetime
import requests


# ========== API Key 获取逻辑 ==========

def get_api_key():
    """获取 API Key，优先从环境变量，其次从 shell 配置文件，仍未获取则提示用户配置"""

    # 1. 从当前环境变量获取
    api_key = os.getenv("REDFOX_API_KEY")
    if api_key:
        return api_key

    # 2. 从 shell 配置文件中读取
    system = platform.system()
    if system == "Windows":
        # Windows: 尝试通过 PowerShell 获取用户级永久环境变量
        try:
            result = subprocess.run(
                ['powershell', '-NoProfile', '-Command',
                 '[Environment]::GetEnvironmentVariable("REDFOX_API_KEY", "User")'],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                api_key = result.stdout.strip()
                if api_key:
                    return api_key
        except Exception:
            pass
    else:
        # macOS/Linux: 从 ~/.zshrc, ~/.bashrc, ~/.bash_profile 读取
        home = os.path.expanduser("~")
        shell_configs = [
            os.path.join(home, '.zshrc'),
            os.path.join(home, '.bashrc'),
            os.path.join(home, '.bash_profile'),
        ]
        for config_file in shell_configs:
            if os.path.exists(config_file):
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        for line in f:
                            line = line.strip()
                            # 匹配: export REDFOX_API_KEY="value" 或 export REDFOX_API_KEY=value
                            match = re.search(
                                r'export\s+REDFOX_API_KEY\s*=\s*["\']?([^"\'\s]+)["\']?',
                                line
                            )
                            if match:
                                api_key = match.group(1)
                                if api_key:
                                    return api_key
                except Exception:
                    pass

    # 3. 未获取到，提示用户配置
    system = platform.system()
    if system == "Windows":
        hint = (
            "缺少 API Key 配置，请设置环境变量 REDFOX_API_KEY。\n"
            "Windows 设置方式：\n"
            "  PowerShell 永久设置：[Environment]::SetEnvironmentVariable('REDFOX_API_KEY', '<你的apikey>', 'User')\n"
            "  CMD 永久设置：setx REDFOX_API_KEY <你的apikey>\n"
            "设置后需重启终端生效。\n"
            "获取 API Key: 访问 https://redfox.hk 注册账号，在个人中心获取"
        )
    else:
        hint = (
            "缺少 API Key 配置，请设置环境变量 REDFOX_API_KEY。\n"
            "macOS/Linux 设置方式：\n"
            "  在 ~/.zshrc（zsh）或 ~/.bashrc（bash）中添加：\n"
            "  export REDFOX_API_KEY=<你的apikey>\n"
            "  然后 source ~/.zshrc 或 source ~/.bashrc 使其生效\n"
            "获取 API Key: 访问 https://redfox.hk 注册账号，在个人中心获取"
        )
    raise ValueError(hint)


# ========== 业务逻辑 ==========

def fetch_xhs_trends(keyword: str, debug: bool = False, max_retries: int = 3, start_date: str = None):
    """
    调用接口获取小红书热门数据

    Args:
        keyword: 搜索关键词（多个关键词用逗号分隔，最多5个，总长度不超过200）
        debug: 是否打印调试信息
        max_retries: 最大重试次数
        start_date: 开始日期，格式 yyyy-MM-dd，最长为最近30天
    Returns:
        dict: 包含4类爆款数据
    """
    api_key = get_api_key()

    url = "https://redfox.hk/story/api/cozeSkill/getXhsCozeSkillData"
    params = {"keyword": keyword, "source": "小红书标题生成与评分-GitHub"}
    if start_date:
        params["startDate"] = start_date

    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json",
    }

    last_error = None
    for attempt in range(max_retries):
        try:
            if debug:
                print(f"\n=== DEBUG: 第 {attempt + 1} 次尝试 ===", file=sys.stderr)

            response = requests.get(url, params=params, headers=headers, timeout=60)

            if debug:
                print(f"状态码: {response.status_code}", file=sys.stderr)
                print(f"响应长度: {len(response.text)} 字节", file=sys.stderr)

            if response.status_code >= 400:
                raise Exception(f"HTTP请求失败: 状态码 {response.status_code}, {response.text[:200]}")

            data = response.json()
            if "data" not in data:
                raise Exception(f"API 错误: {data.get('msg', '未知错误')}")

            result_data = data.get("data", {})

            if debug:
                print("=== DEBUG: API 返回的 data 字段键 ===", file=sys.stderr)
                print(json.dumps(list(result_data.keys()), ensure_ascii=False, indent=2), file=sys.stderr)

            return {
                "keyword": keyword,
                "low_fan_explosive": result_data.get("lowPowderExplosiveArticle", []),
                "daily_like_top500": result_data.get("likeTheTop500", []),
                "daily_increment": result_data.get("singleDayIncrements", []),
                "weekly_increment": result_data.get("sevenDaysOfIncrements", [])
            }

        except requests.exceptions.RequestException as e:
            last_error = f"请求失败: {str(e)}"
        except Exception as e:
            last_error = str(e)

        if debug:
            print(f"  错误: {last_error[:100]}", file=sys.stderr)
        if attempt < max_retries - 1:
            time.sleep(2 ** attempt)

    raise Exception(f"{last_error}（已尝试 {max_retries} 次）")


# ========== 格式化输出 ==========

# 四类数据的配置
CATEGORY_CONFIG = [
    ('low_fan_explosive', '低粉高赞', '粉丝<5000的博主中点赞最多的内容', 'standard'),
    ('daily_like_top500', '点赞最多', '统计时间内点赞数最多的内容', 'like_highlight'),
    ('daily_increment', '单日互动爆发', '当天互动量增长最多的内容', 'ana_add'),
    ('weekly_increment', '7日持续增长', '近7天互动量持续增长最多的内容', 'ana_add'),
]


def process_title(item):
    """处理标题：空标题用desc替代，转义特殊字符，截断过长标题"""
    title = item.get('title', '')
    if not title or not title.strip():
        desc = item.get('desc', '')
        if desc:
            title = desc.replace('\n', ' ').replace('\r', ' ').strip()[:30]
            if len(desc) > 30:
                title += '...'
    if not title or not title.strip():
        title = '无标题'
    title = title.replace('|', '\\|').replace('\n', ' ').replace('\r', ' ')
    title = ' '.join(title.split())
    if len(title) > 30:
        title = title[:30] + "..."
    return title


def format_time(item):
    """格式化发布时间为 X月X日"""
    pub_time = item.get('publicTime', '')
    if pub_time:
        try:
            return f"{int(pub_time[5:7])}月{int(pub_time[8:10])}日"
        except (ValueError, IndexError):
            pass
    return '--'


def format_author(item):
    """生成作者信息（含主页链接）"""
    user_id = item.get('userId', '')
    user_name = item.get('userName', '未知')
    fans = item.get('fans', 0)
    if user_id:
        return f"[{user_name}](https://www.xiaohongshu.com/user/profile/{user_id})（粉丝：{fans}）"
    return f"{user_name}（粉丝：{fans}）"


def format_title_with_link(item):
    """生成带作品链接的标题"""
    title = process_title(item)
    photo_id = item.get('photoId', '')
    if photo_id:
        return f"[{title}](https://www.xiaohongshu.com/explore/{photo_id})"
    return title


def get_ana_add_stats(item):
    """从 anaAdd 对象获取新增互动数据"""
    ana_add = item.get('anaAdd', {})
    if ana_add:
        return (
            ana_add.get('addCollectedCunt', 0),
            ana_add.get('addShareCount', 0),
            ana_add.get('addCommentCount', 0),
            ana_add.get('addLikeCount', 0),
            ana_add.get('addInteractiveount', 0),
        )
    return (0, 0, 0, 0, 0)


def dedup_items(items):
    """按 photoId 去重"""
    seen = set()
    result = []
    for item in items:
        photo_id = item.get('photoId', '')
        if photo_id and photo_id not in seen:
            seen.add(photo_id)
            result.append(item)
    return result


def sort_by_time_desc(items):
    """按发布时间倒序排列"""
    return sorted(items, key=lambda x: x.get('publicTime', '') or '0', reverse=True)


def render_category_table(items, layout_type):
    """渲染单个类别的 Markdown 表格行"""
    rows = []
    for idx, item in enumerate(items, 1):
        pub_time = format_time(item)
        title_with_link = format_title_with_link(item)
        author_str = format_author(item)

        if layout_type == 'standard':
            rows.append(
                f"| {idx} | {pub_time} | {title_with_link} | {author_str} "
                f"| {item.get('collectedCount', 0)} | {item.get('useShareCount', 0)} "
                f"| {item.get('useCommentCount', 0)} | {item.get('useLikeCount', 0)} "
                f"| **{item.get('interactiveCount', 0)}** |"
            )
        elif layout_type == 'like_highlight':
            rows.append(
                f"| {idx} | {pub_time} | {title_with_link} | {author_str} "
                f"| **{item.get('useLikeCount', 0)}** | {item.get('collectedCount', 0)} "
                f"| {item.get('useShareCount', 0)} | {item.get('useCommentCount', 0)} "
                f"| {item.get('interactiveCount', 0)} |"
            )
        elif layout_type == 'ana_add':
            collected, share, comment, like, total = get_ana_add_stats(item)
            rows.append(
                f"| {idx} | {pub_time} | {title_with_link} | {author_str} "
                f"| {collected} | {share} | {comment} | {like} | **{total}** |"
            )
    return rows


CATEGORY_HEADERS = {
    'standard': (
        "| 序号 | 发布时间 | 标题 | 作者 | 收藏 | 分享 | 评论 | 点赞 | **互动总数** |",
        "|------|----------|------|------|------|------|------|------|-------------|"
    ),
    'like_highlight': (
        "| 序号 | 发布时间 | 标题 | 作者 | **点赞** | 收藏 | 分享 | 评论 | 互动总数 |",
        "|------|----------|------|------|--------|------|------|------|------------|"
    ),
    'ana_add': (
        "| 序号 | 发布时间 | 标题 | 作者 | 收藏 | 分享 | 评论 | 点赞 | 互动总数 |",
        "|------|----------|------|------|------|------|------|------|------------|"
    ),
}


def format_output(data: dict, max_items: int = None, start_date: str = None):
    """格式化输出热门数据（Markdown 表格）"""

    # 计算统计时间范围
    time_range = "近30天"
    if start_date:
        try:
            days = (datetime.now() - datetime.strptime(start_date, '%Y-%m-%d')).days
            time_range = f"近{days}天" if days > 1 else "近1天"
        except ValueError:
            pass

    # 去重 + 检查数据总量
    deduped = {}
    total_count = 0
    for key, _, _, _ in CATEGORY_CONFIG:
        items = dedup_items(data.get(key, []))
        deduped[key] = items
        total_count += len(items)

    output = []

    # 无数据时输出友好提示
    if total_count == 0:
        keyword = data.get("keyword", "")
        output.append(f"# 小红书爆款数据分析报告\n\n**关键词**：{keyword}\n\n---\n\n")
        output.append(f"## 暂无相关爆款数据\n\n很抱歉，当前关键词 **「{keyword}」** 尚未有足够的爆款笔记数据。\n\n")
        output.append("### 可能原因\n\n- 该关键词相对小众或新兴，爆款内容积累较少\n")
        output.append("- 近期该赛道热度较低，暂无突出爆款笔记\n- 关键词表述方式可以更加具体或热门\n\n")
        output.append("### 建议操作\n\n- 更换为更热门的关键词，如：**\"早八穿搭\"**、**\"减脂餐\"**、**\"职场干货\"** 等\n")
        output.append("- 尝试更细分的长尾关键词，如：**\"小个子穿搭\"**、**\"学生党便当\"** 等\n\n")
        output.append("---\n\n*数据来源：小红书爆款雷达，每日更新最新热门内容*\n")
        return "\n".join(output)

    # 按类别渲染表格
    for key, name, desc, layout_type in CATEGORY_CONFIG:
        items = sort_by_time_desc(deduped[key])
        if max_items is not None:
            items = items[:max_items]

        output.append(f"\n### - **{name}**（{desc}）\n")

        if not items:
            output.append("(无数据)\n")
        else:
            header, separator = CATEGORY_HEADERS[layout_type]
            output.append(header)
            output.append(separator)
            output.extend(render_category_table(items, layout_type))

    return "\n".join(output)


# ========== 入口 ==========

def main():
    parser = argparse.ArgumentParser(description='小红书热门数据查询工具')
    parser.add_argument('--keyword', required=True, help='搜索关键词')
    parser.add_argument('--max-items', type=int, default=10, help='每类爆款内容最多展示数量（默认10条）')
    parser.add_argument('--output-format', choices=['text', 'json', 'markdown'], default='markdown',
                        help='输出格式：text/json/markdown（默认markdown）')
    parser.add_argument('--output-file', type=str, default=None, help='输出文件路径（默认：关键词_爆款数据.md）')
    parser.add_argument('--start-date', type=str, default=None, help='开始日期，格式 yyyy-MM-dd')
    parser.add_argument('--debug', action='store_true', help='启用调试模式')
    parser.add_argument('--max-retries', type=int, default=3, help='最大重试次数（默认3次）')

    args = parser.parse_args()

    try:
        data = fetch_xhs_trends(args.keyword, debug=args.debug, max_retries=args.max_retries,
                                start_date=args.start_date)

        if args.output_format == 'json':
            output_content = json.dumps(data, ensure_ascii=False, indent=2)
        elif args.output_format == 'markdown':
            markdown_header = f"# 小红书爆款数据分析报告\n\n**关键词**：{args.keyword}\n\n"
            output_content = markdown_header + format_output(data, max_items=args.max_items,
                                                             start_date=args.start_date)
        else:
            output_content = format_output(data, max_items=args.max_items, start_date=args.start_date)

        output_file = args.output_file
        if output_file is None and args.output_format == 'markdown':
            output_file = f"{args.keyword}_爆款数据.md"

        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(output_content)
            total_items = sum(len(data.get(k, [])) for k, _, _, _ in CATEGORY_CONFIG)
            print(f"✓ 结果已保存到: {output_file}", file=sys.stderr)
            print(f"✓ 关键词: {args.keyword} | 总计: {total_items} 条数据", file=sys.stderr)
            for key, name, _, _ in CATEGORY_CONFIG:
                print(f"  - {name}: {len(data.get(key, []))} 条", file=sys.stderr)
        else:
            print(output_content)

    except Exception as e:
        print(f"❌ 错误: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
