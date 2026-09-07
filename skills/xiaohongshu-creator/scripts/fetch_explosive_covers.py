#!/usr/bin/env python3
"""
小红书爆款数据查询脚本
使用原生 requests 调用红狐数据接口
"""

import os
import sys
import argparse
import json

import requests


def get_api_key():
    """从环境变量获取 API Key，未找到则从 shell 配置文件读取"""
    # 1. 尝试从环境变量获取
    api_key = os.getenv("REDFOX_API_KEY")
    if api_key:
        return api_key.strip()

    # 2. 尝试从 shell 配置文件读取
    home = os.path.expanduser("~")

    if sys.platform == "win32":
        # Windows: 尝试从用户级永久环境变量读取
        try:
            import subprocess
            result = subprocess.run(
                ["powershell", "-NoProfile", "-command",
                 "[Environment]::GetEnvironmentVariable('REDFOX_API_KEY', 'User')"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        except Exception:
            pass
    else:
        # macOS/Linux: 尝试从 shell 配置文件读取
        for config_file in [".zshrc", ".bashrc", ".bash_profile", ".profile"]:
            config_path = os.path.join(home, config_file)
            if os.path.exists(config_path):
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        for line in f:
                            line = line.strip()
                            if line.startswith("export REDFOX_API_KEY="):
                                key = line.split("=", 1)[1].strip().strip('"').strip("'")
                                if key:
                                    return key
                except Exception:
                    continue

    return None


def fetch_xhs_trends(keyword: str, debug: bool = False, max_retries: int = 3, start_date: str = None):
    """
    调用红狐数据接口获取小红书爆款数据

    Args:
        keyword: 搜索关键词（多个关键词用逗号分隔，最多5个，总长度不超过200）
        debug: 是否打印调试信息
        max_retries: 最大重试次数
        start_date: 开始日期，格式 yyyy-MM-dd，最长为最近30天

    Returns:
        dict: 包含4类爆款数据

    Raises:
        Exception: 当API调用失败时抛出异常
    """
    api_key = get_api_key()
    if not api_key:
        print("❌ 未找到 REDFOX_API_KEY 环境变量", file=sys.stderr)
        print("请配置 API Key：", file=sys.stderr)
        print("  macOS/Linux: export REDFOX_API_KEY=<你的apikey>", file=sys.stderr)
        print("  Windows: [Environment]::SetEnvironmentVariable('REDFOX_API_KEY', '<你的apikey>', 'User')", file=sys.stderr)
        print("详细说明请参考技能文档中的「鉴权」部分", file=sys.stderr)
        sys.exit(1)

    url = "https://redfox.hk/story/api/cozeSkill/getXhsCozeSkillData"
    params = {
        "keyword": keyword,
        "source": "小红书爆款封面生成-GitHub"
    }

    if start_date:
        params["startDate"] = start_date

    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    last_error = None
    for attempt in range(max_retries):
        try:
            if debug:
                print(f"\n=== DEBUG: 第 {attempt + 1} 次尝试 ===", file=sys.stderr)
                print(f"URL: {url}", file=sys.stderr)
                print(f"Params: {params}", file=sys.stderr)

            response = requests.get(url, params=params, headers=headers, timeout=60)

            if debug:
                print(f"状态码: {response.status_code}", file=sys.stderr)
                print(f"响应长度: {len(response.text)} 字节", file=sys.stderr)

            if response.status_code >= 400:
                raise Exception(f"HTTP请求失败: 状态码 {response.status_code}, {response.text[:200]}")

            data = response.json()

            if "data" not in data:
                error_msg = data.get("msg", "未知错误")
                raise Exception(f"API 错误: {error_msg}")

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
            if debug:
                print(f"  请求异常: {type(e).__name__}: {str(e)[:100]}", file=sys.stderr)
            import time
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            continue
        except Exception as e:
            last_error = str(e)
            if debug:
                print(f"  错误: {type(e).__name__}: {str(e)[:100]}", file=sys.stderr)
            import time
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            continue

    raise Exception(f"{last_error}（已尝试 {max_retries} 次）")


def get_cover_urls(data, max_per_category=5):
    """提取所有封面图URL"""
    urls = []
    categories = [
        ('low_fan_explosive', '低粉高赞'),
        ('daily_like_top500', '点赞最多'),
        ('daily_increment', '单日互动爆发'),
        ('weekly_increment', '7日持续增长')
    ]
    for key, name in categories:
        items = data.get(key, [])[:max_per_category]
        for item in items:
            cover_url = item.get('coverUrl', '')
            photo_id = item.get('photoId', '')
            title = item.get('title', '')[:20]
            if cover_url and photo_id:
                urls.append({
                    'category': name,
                    'title': title,
                    'photo_id': photo_id,
                    'cover_url': cover_url,
                    'link': f"https://www.xiaohongshu.com/explore/{photo_id}"
                })
    return urls


def format_output(data: dict, max_items: int = None, start_date: str = None):
    """
    格式化输出热门数据（表格形式）

    Args:
        data: 原始数据
        max_items: 每类爆款数据最多展示数量，None 表示展示所有数据
        start_date: 开始日期，格式 yyyy-MM-dd，用于计算统计时间范围
    """
    from datetime import datetime, timedelta

    def get_time_range(start_date):
        if start_date:
            try:
                start = datetime.strptime(start_date, '%Y-%m-%d')
                end = datetime.now()
                days = (end - start).days
                if days <= 1:
                    return "近1天"
                elif days <= 7:
                    return f"近{days}天"
                else:
                    return f"近{days}天"
            except:
                return "近30天"
        return "近30天"

    time_range = get_time_range(start_date)

    def process_title(item):
        """处理标题：转义特殊字符，空标题使用desc替代"""
        title = item.get('title', '')
        if not title or title.strip() == '':
            desc = item.get('desc', '')
            if desc:
                title = desc.replace('\n', ' ').replace('\r', ' ').strip()[:30]
                if len(desc) > 30:
                    title = title + '...'

        if not title or title.strip() == '':
            title = '无标题'

        title = title.replace('|', '\\|')
        title = title.replace('\n', ' ').replace('\r', ' ')
        title = ' '.join(title.split())

        if len(title) > 30:
            title = title[:30] + "..."

        return title

    def format_time(item):
        """格式化发布时间为 X月X日"""
        pub_time = item.get('publicTime', '')
        if pub_time:
            try:
                month = int(pub_time[5:7])
                day = int(pub_time[8:10])
                return f"{month}月{day}日"
            except:
                pass
        return '--'

    def format_note_link(item):
        """生成作品链接"""
        photo_id = item.get('photoId', '')
        if photo_id:
            return f"[查看详情](https://www.xiaohongshu.com/explore/{photo_id})"
        return '--'

    def get_latest_date(data):
        """获取数据中最新的发布日期"""
        all_items = []
        for key in ['low_fan_explosive', 'daily_like_top500', 'daily_increment', 'weekly_increment']:
            all_items.extend(data.get(key, []))

        latest_date = None
        for item in all_items:
            pub_time = item.get('publicTime', '')
            if pub_time:
                try:
                    date_str = pub_time[:10]
                    if latest_date is None or date_str > latest_date:
                        latest_date = date_str
                except:
                    pass
        return latest_date

    output = []

    latest_date = get_latest_date(data)

    def dedup_items(items):
        seen = set()
        result = []
        for item in items:
            photo_id = item.get('photoId', '')
            if photo_id and photo_id not in seen:
                seen.add(photo_id)
                result.append(item)
        return result

    low_fan_items = dedup_items(data.get("low_fan_explosive", []))
    daily_like_items = dedup_items(data.get("daily_like_top500", []))
    daily_increment_items = dedup_items(data.get("daily_increment", []))
    weekly_increment_items = dedup_items(data.get("weekly_increment", []))

    total_count = len(low_fan_items) + len(daily_like_items) + len(daily_increment_items) + len(weekly_increment_items)

    if total_count == 0:
        keyword = data.get("keyword", "")
        output.append(f"# 小红书爆款数据分析报告\n\n**关键词**：{keyword}\n\n")
        output.append("---\n\n")
        output.append("## 暂无相关爆款数据\n\n")
        output.append(f"很抱歉，当前关键词 **「{keyword}」** 尚未有足够的爆款笔记数据。\n\n")
        output.append("### 可能原因\n\n")
        output.append("- 该关键词相对小众或新兴，爆款内容积累较少\n")
        output.append("- 近期该赛道热度较低，暂无突出爆款笔记\n")
        output.append("- 关键词表述方式可以更加具体或热门\n\n")
        output.append("### 建议操作\n\n")
        output.append("- 更换为更热门的关键词，如：**\"早八穿搭\"**、**\"减脂餐\"**、**\"职场干货\"** 等\n")
        output.append("- 尝试更细分的长尾关键词，如：**\"小个子穿搭\"**、**\"学生党便当\"** 等\n")
        output.append("- 输入其他感兴趣的领域或赛道进行追踪\n\n")
        output.append("---\n\n")
        output.append("*数据来源：小红书爆款雷达，每日更新最新热门内容*\n")
        return "\n".join(output)

    # 1. 低粉高赞
    items = low_fan_items
    if max_items is not None:
        items = items[:max_items]

    output.append(f"\n### - **低粉高赞**（粉丝<5000的博主中点赞最多的内容）")
    output.append("\n")

    if not items:
        output.append("(无数据)\n")
    else:
        output.append("| 封面 | 序号 | 发布时间 | 标题 | 作者 | 收藏 | 分享 | 评论 | 点赞 | **互动总数** |")
        output.append("|------|------|----------|------|------|------|------|------|------|-------------|")

        for idx, item in enumerate(items, 1):
            user_id = item.get('userId', '')
            user_name = item.get('userName', '未知')
            fans = item.get('fans', 0)

            cover_url = item.get('coverUrl', '')
            if cover_url:
                cover_str = f"![]({cover_url})"
            else:
                cover_str = "--"

            if user_id:
                author_str = f"[{user_name}](https://www.xiaohongshu.com/user/profile/{user_id})（粉丝：{fans}）"
            else:
                author_str = f"{user_name}（粉丝：{fans}）"

            title = process_title(item)
            pub_time = format_time(item)

            photo_id = item.get('photoId', '')
            if photo_id:
                note_link = f"https://www.xiaohongshu.com/explore/{photo_id}"
                title_with_link = f"[{title}]({note_link})"
            else:
                title_with_link = title

            output.append(f"| {cover_str} | {idx} | {pub_time} | {title_with_link} | {author_str} | {item.get('collectedCount', 0)} | {item.get('useShareCount', 0)} | {item.get('useCommentCount', 0)} | {item.get('useLikeCount', 0)} | **{item.get('interactiveCount', 0)}** |")

    # 2. 点赞最多
    items = data.get("daily_like_top500", [])
    if max_items is not None:
        items = items[:max_items]

    output.append(f"\n### - **点赞最多**（统计时间内点赞数最多的内容）")
    output.append("\n")

    if not items:
        output.append("(无数据)\n")
    else:
        output.append("| 封面 | 序号 | 发布时间 | 标题 | 作者 | **点赞** | 收藏 | 分享 | 评论 | 互动总数 |")
        output.append("|------|------|----------|------|------|--------|------|------|------|------------|")

        for idx, item in enumerate(items, 1):
            user_id = item.get('userId', '')
            user_name = item.get('userName', '未知')
            fans = item.get('fans', 0)

            cover_url = item.get('coverUrl', '')
            if cover_url:
                cover_str = f"![]({cover_url})"
            else:
                cover_str = "--"

            if user_id:
                author_str = f"[{user_name}](https://www.xiaohongshu.com/user/profile/{user_id})（粉丝：{fans}）"
            else:
                author_str = f"{user_name}（粉丝：{fans}）"

            title = process_title(item)
            pub_time = format_time(item)

            photo_id = item.get('photoId', '')
            if photo_id:
                note_link = f"https://www.xiaohongshu.com/explore/{photo_id}"
                title_with_link = f"[{title}]({note_link})"
            else:
                title_with_link = title

            output.append(f"| {cover_str} | {idx} | {pub_time} | {title_with_link} | {author_str} | **{item.get('useLikeCount', 0)}** | {item.get('collectedCount', 0)} | {item.get('useShareCount', 0)} | {item.get('useCommentCount', 0)} | {item.get('interactiveCount', 0)} |")

    # 3. 单日互动爆发
    items = data.get("daily_increment", [])
    if max_items is not None:
        items = items[:max_items]

    output.append(f"\n### - **单日互动爆发**（当天互动量增长最多的内容）")
    output.append("\n")

    if not items:
        output.append("(无数据)\n")
    else:
        output.append("| 封面 | 序号 | 发布时间 | 标题 | 作者 | 收藏 | 分享 | 评论 | 点赞 | 互动总数 |")
        output.append("|------|------|----------|------|------|------|------|------|------|------------|")

        for idx, item in enumerate(items, 1):
            user_id = item.get('userId', '')
            user_name = item.get('userName', '未知')
            fans = item.get('fans', 0)

            cover_url = item.get('coverUrl', '')
            if cover_url:
                cover_str = f"![]({cover_url})"
            else:
                cover_str = "--"

            if user_id:
                author_str = f"[{user_name}](https://www.xiaohongshu.com/user/profile/{user_id})（粉丝：{fans}）"
            else:
                author_str = f"{user_name}（粉丝：{fans}）"

            title = process_title(item)
            pub_time = format_time(item)

            photo_id = item.get('photoId', '')
            if photo_id:
                note_link = f"https://www.xiaohongshu.com/explore/{photo_id}"
                title_with_link = f"[{title}]({note_link})"
            else:
                title_with_link = title

            ana_add = item.get('anaAdd', {})
            if ana_add:
                total = ana_add.get('addInteractiveount', 0)
                collected = ana_add.get('addCollectedCunt', 0)
                share = ana_add.get('addShareCount', 0)
                comment = ana_add.get('addCommentCount', 0)
                like = ana_add.get('addLikeCount', 0)
            else:
                total = 0
                collected = 0
                share = 0
                comment = 0
                like = 0

            output.append(f"| {cover_str} | {idx} | {pub_time} | {title_with_link} | {author_str} | {collected} | {share} | {comment} | {like} | **{total}** |")

    # 4. 7日持续增长
    items = data.get("weekly_increment", [])
    if max_items is not None:
        items = items[:max_items]

    output.append(f"\n### - **7日持续增长**（近7天互动量持续增长最多的内容）")
    output.append("\n")

    if not items:
        output.append("(无数据)\n")
    else:
        output.append("| 封面 | 序号 | 发布时间 | 标题 | 作者 | 收藏 | 分享 | 评论 | 点赞 | 互动总数 |")
        output.append("|------|------|----------|------|------|------|------|------|------|------------|")

        for idx, item in enumerate(items, 1):
            user_id = item.get('userId', '')
            user_name = item.get('userName', '未知')
            fans = item.get('fans', 0)

            cover_url = item.get('coverUrl', '')
            if cover_url:
                cover_str = f"![]({cover_url})"
            else:
                cover_str = "--"

            if user_id:
                author_str = f"[{user_name}](https://www.xiaohongshu.com/user/profile/{user_id})（粉丝：{fans}）"
            else:
                author_str = f"{user_name}（粉丝：{fans}）"

            title = process_title(item)
            pub_time = format_time(item)

            photo_id = item.get('photoId', '')
            if photo_id:
                note_link = f"https://www.xiaohongshu.com/explore/{photo_id}"
                title_with_link = f"[{title}]({note_link})"
            else:
                title_with_link = title

            ana_add = item.get('anaAdd', {})
            if ana_add:
                total = ana_add.get('addInteractiveount', 0)
                collected = ana_add.get('addCollectedCunt', 0)
                share = ana_add.get('addShareCount', 0)
                comment = ana_add.get('addCommentCount', 0)
                like = ana_add.get('addLikeCount', 0)
            else:
                total = 0
                collected = 0
                share = 0
                comment = 0
                like = 0

            output.append(f"| {cover_str} | {idx} | {pub_time} | {title_with_link} | {author_str} | {collected} | {share} | {comment} | {like} | **{total}** |")

    return "\n".join(output)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='小红书爆款数据查询工具')
    parser.add_argument('--keyword', required=True, help='搜索关键词')
    parser.add_argument('--max-items', type=int, default=10,
                       help='每类爆款内容最多展示数量（默认10条）')
    parser.add_argument('--output-format', choices=['text', 'json', 'markdown'],
                       default='json', help='输出格式：text（文本表格）、json（JSON格式，默认）或 markdown（Markdown格式）')
    parser.add_argument('--output-file', type=str, default=None,
                       help='输出文件路径（默认：关键词_爆款数据.md）')
    parser.add_argument('--start-date', type=str, default=None,
                       help='开始日期，格式 yyyy-MM-dd（默认最近30天）')
    parser.add_argument('--debug', action='store_true', help='启用调试模式')
    parser.add_argument('--max-retries', type=int, default=3,
                       help='最大重试次数（默认3次）')

    args = parser.parse_args()

    try:
        data = fetch_xhs_trends(args.keyword, debug=args.debug, max_retries=args.max_retries, start_date=args.start_date)

        if args.output_format == 'json':
            output_content = json.dumps(data, ensure_ascii=False, indent=2)
        elif args.output_format == 'markdown':
            markdown_header = f"# 小红书爆款数据分析报告\n\n**关键词**：{args.keyword}\n\n"
            output_content = markdown_header + format_output(data, max_items=args.max_items, start_date=args.start_date)
        else:
            output_content = format_output(data, max_items=args.max_items, start_date=args.start_date)

        output_file = args.output_file

        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(output_content)
            print(f"✓ 结果已保存到: {output_file}", file=sys.stderr)
            print(f"✓ 关键词: {args.keyword}", file=sys.stderr)
            total_items = (
                len(data.get('low_fan_explosive', [])) +
                len(data.get('daily_like_top500', [])) +
                len(data.get('daily_increment', [])) +
                len(data.get('weekly_increment', []))
            )
            print(f"✓ 总计: {total_items} 条数据", file=sys.stderr)
            print(f"  - 低粉高赞: {len(data.get('low_fan_explosive', []))} 条", file=sys.stderr)
            print(f"  - 点赞最多: {len(data.get('daily_like_top500', []))} 条", file=sys.stderr)
            print(f"  - 单日互动爆发: {len(data.get('daily_increment', []))} 条", file=sys.stderr)
            print(f"  - 7日持续增长: {len(data.get('weekly_increment', []))} 条", file=sys.stderr)
            cover_urls = get_cover_urls(data, max_per_category=3)
            if cover_urls:
                print(f"\n=== 封面图URL（用于风格分析）===", file=sys.stderr)
                for i, item in enumerate(cover_urls, 1):
                    print(f"{i}. [{item['category']}] {item['title']}: {item['cover_url']}", file=sys.stderr)
        else:
            print(output_content)
            print(f"\n✓ 关键词: {args.keyword}", file=sys.stderr)

    except Exception as e:
        print(f"❌ 错误: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
