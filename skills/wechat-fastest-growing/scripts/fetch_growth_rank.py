#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""公众号阅读增长率排行榜获取脚本"""

import argparse
import os
import re
import sys
from datetime import datetime, timedelta

import requests


SKILL_ID = "7633629455969337344"
API_URL = "https://redfox.hk/story/api/cozeSkill/getGzhCozeSkillDataRaise"


def parse_date(date_str: str) -> str:
    """解析日期参数，支持yesterday/today/YYYY-MM-DD"""
    date_str = date_str.strip().lower()

    if date_str == "yesterday":
        return (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    if date_str == "today":
        return datetime.now().strftime("%Y-%m-%d")

    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        today = datetime.now()
        if dt < today - timedelta(days=30):
            raise Exception(f"日期不能早于30天前")
        if dt > today:
            raise Exception("日期不能晚于今天")
        return date_str
    except ValueError:
        raise Exception("日期格式错误，请使用 YYYY-MM-DD 格式")


def _extract_api_key_from_config(filepath: str) -> str | None:
    """从shell配置文件中提取 REDFOX_API_KEY 的值"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line_stripped = line.strip()
                if "REDFOX_API_KEY" not in line_stripped:
                    continue
                # 匹配 export REDFOX_API_KEY=xxx、export REDFOX_API_KEY="xxx"、set REDFOX_API_KEY=xxx 等
                m = re.search(r'REDFOX_API_KEY\s*[=:]\s*["\']?([^\s"\'#]+)["\']?', line_stripped)
                if m:
                    return m.group(1)
    except (OSError, UnicodeDecodeError):
        pass
    return None


def get_api_key() -> str:
    """获取 API Key，三级回退：环境变量 → shell配置文件 → 提示用户配置"""
    # 第一级：从当前设备环境变量获取
    api_key = os.getenv("REDFOX_API_KEY")
    if api_key:
        return api_key

    # 兼容旧变量名
    api_key = os.getenv(f"COZE_REDFOX_API_{SKILL_ID}")
    if api_key:
        return api_key

    # 第二级：从shell配置文件中自动读取
    home = os.path.expanduser("~")
    config_files = [
        os.path.join(home, ".bashrc"),
        os.path.join(home, ".bash_profile"),
        os.path.join(home, ".zshrc"),
        os.path.join(home, ".profile"),
    ]
    for config_file in config_files:
        if not os.path.isfile(config_file):
            continue
        api_key = _extract_api_key_from_config(config_file)
        if api_key:
            return api_key

    # 第三级：提示用户配置
    raise ValueError(
        "缺少 API Key，请按以下步骤配置：\n"
        "1. 访问 https://redfox.hk/login?source=github 注册账号\n"
        "2. 登录后在个人中心获取 API Key（格式：ak_xxxxxxxx）\n"
        "3. 设置环境变量：export REDFOX_API_KEY=<你的apikey>\n"
        "   或永久配置：echo 'export REDFOX_API_KEY=<你的apikey>' >> ~/.bashrc && source ~/.bashrc"
    )


def fetch_data(rank_date: str, source: str) -> dict:
    """调用API获取榜单数据"""
    api_key = get_api_key()
    headers = {
        "Content-Type": "application/json",
        "X-API-KEY": api_key
    }
    try:
        resp = requests.get(API_URL, params={"rankDate": rank_date, "source": source},
                            headers=headers, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        raise Exception(f"API调用失败: {e}")


def safe_str(val) -> str:
    return "-" if val is None or val == "" else str(val)


def parse_int(val) -> int:
    if val is None or val == "":
        return 0
    try:
        return int(val)
    except (ValueError, TypeError):
        return 0


def format_count(val) -> str:
    """格式化计数：10000~999999显示为Xw+"""
    num = parse_int(val)
    if num == 0 and (val is None or val == ""):
        return "-"
    if num >= 1000000:
        return str(num)
    if num >= 10000:
        return f"{num // 10000}w+"
    return str(num)


def make_link(title: str, url: str) -> str:
    """生成Markdown链接"""
    t, u = safe_str(title), safe_str(url)
    return f'[{t}]({u})' if t != "-" and u != "-" else t


def calc_score_v2(items: list) -> list:
    """计算综合评分指数（8-10分）- 横向对比版本

    维度1：总互动量（转发+在看+点赞）→ 权重40%
    维度2：加权互动值（转发*5 + 在看*3 + 点赞*2）→ 权重60%
    使用min-max归一化映射到8-10分
    """
    if not items:
        return []

    # 提取所有文章的互动数据
    data_points = []
    for item in items:
        max_w = item.get("maxWork") or {}
        share = parse_int(max_w.get("shareCount"))
        watch = parse_int(max_w.get("watchCount"))
        like = parse_int(max_w.get("likeCount"))

        total_interactions = share + watch + like  # 维度1
        weighted_value = share * 5 + watch * 3 + like * 2  # 维度2

        data_points.append({
            "item": item,
            "total_interactions": total_interactions,
            "weighted_value": weighted_value
        })

    # 计算min-max
    total_min = min(d["total_interactions"] for d in data_points)
    total_max = max(d["total_interactions"] for d in data_points)
    weighted_min = min(d["weighted_value"] for d in data_points)
    weighted_max = max(d["weighted_value"] for d in data_points)

    results = []
    for dp in data_points:
        # 维度1归一化（避免除零）
        if total_max == total_min:
            norm_total = 0.5
        else:
            norm_total = (dp["total_interactions"] - total_min) / (total_max - total_min)

        # 维度2归一化
        if weighted_max == weighted_min:
            norm_weighted = 0.5
        else:
            norm_weighted = (dp["weighted_value"] - weighted_min) / (weighted_max - weighted_min)

        # 综合得分 = 维度1*0.4 + 维度2*0.6
        combined = norm_total * 0.4 + norm_weighted * 0.6

        # 映射到8-10分
        score = 8 + combined * 2

        results.append((dp["item"], score))

    return results


def render_table(data_list: list) -> str:
    """渲染Markdown表格"""
    lines = [
        "数据说明：公众号阅读增长率排行；每位作者一行，展示该作者最高阅读代表作（标题可跳转原文）。"
        "综合评分指数 8–10 分，综合阅读、在看、点赞、转发等互动指标加权评定。\n",
        "| 序号 | 作者 | 最高阅读数文章 | 在看数 | 点赞数 | 转发数 | 阅读数 | 发布时间 | 综合评分指数 |",
        "| :---: | :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: |"
    ]

    # 使用min-max归一化计算综合评分指数
    scored_data = calc_score_v2(data_list)

    # 按综合评分指数降序排序
    scored_data.sort(key=lambda x: x[1], reverse=True)

    for rank_num, (acc, score) in enumerate(scored_data, 1):
        max_w = acc.get("maxWork") or {}
        user = safe_str(acc.get("userName"))

        lines.append(
            f"| {rank_num} | {user} | {make_link(max_w.get('title'), max_w.get('oriUrl'))} | "
            f"{format_count(max_w.get('watchCount'))} | {format_count(max_w.get('likeCount'))} | "
            f"{format_count(max_w.get('shareCount'))} | {safe_str(max_w.get('clicksCount'))} | "
            f"{safe_str(max_w.get('publicTime'))} | {score:.2f} |"
        )

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="获取公众号阅读增长率排行榜")
    parser.add_argument("--rankDate", required=True, help="榜单日期")
    parser.add_argument("--source", default="公众号阅读增长榜-GitHub", help="数据源（内部参数，使用默认值即可）")
    args = parser.parse_args()

    try:
        rank_date = parse_date(args.rankDate)
        data = []
        api_calls = 0
        max_retry_days = 30

        # 数据为空时向前追溯，直到找到数据或超过30天上限
        current_date = rank_date
        today = datetime.now().strftime("%Y-%m-%d")
        earliest = (datetime.now() - timedelta(days=max_retry_days)).strftime("%Y-%m-%d")

        for offset in range(max_retry_days + 1):
            try_date = (datetime.strptime(rank_date, "%Y-%m-%d") - timedelta(days=offset)).strftime("%Y-%m-%d")
            if try_date < earliest or try_date > today:
                break

            result = fetch_data(try_date, args.source)
            api_calls += 1

            if result.get("code") != 2000:
                continue

            batch = result.get("data", [])
            if batch:
                data = batch
                rank_date = try_date
                # 找到数据立即停止，不再继续调用接口
                break

        if not data:
            print(f"\n榜单日期: {rank_date} | 近{max_retry_days}天暂无数据\n")
            return

        print(f"\n榜单日期: {rank_date} | 榜单数量: {len(data)} 个账号 | API调用次数: {api_calls}\n")
        print(render_table(data))
        print("\n数据获取完成")

    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
