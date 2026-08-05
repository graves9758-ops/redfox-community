#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抖音账号诊断 - API调用脚本
基于红狐API接口 /story/api/dyUser/query 查询抖音账号数据和作品数据
"""

import os
import json
from typing import List, Dict, Optional


class DouyinUserAPI:
    """抖音用户API调用类 - 红狐API /story/api/dyUser/query"""

    # API基础地址
    BASE_URL = "https://redfox.hk"

    # 接口路径（已验证可用）
    QUERY_ENDPOINT = "/story/api/dyUser/query"

    # 环境变量名
    ENV_VAR = "REDFOX_API_KEY"

    def __init__(self, api_key: Optional[str] = None):
        """
        初始化API客户端

        Args:
            api_key: API密钥（X-API-KEY），格式 ak_xxx，不传则从环境变量读取
        """
        self.api_key = api_key or os.environ.get(self.ENV_VAR, "")
        self.headers = {
            "Content-Type": "application/json",
            "X-API-KEY": self.api_key
        }

    def query_accounts(
        self,
        account_ids: Optional[List[str]] = None,
        account_names: Optional[List[str]] = None,
        source: str = "抖音账号诊断宗师-GitHub"
    ) -> Dict:
        """
        查询抖音账号信息

        Args:
            account_ids: 抖音号列表（unique_id、short_id、uid）
            account_names: 抖音昵称列表（模糊匹配nickname）
            source: 来源标识

        Returns:
            dict: {
                "success": bool,
                "data": list or None,
                "error": str or None,
                "fallback_needed": bool  # 是否需要降级为联网搜索
            }
        """
        import requests

        url = f"{self.BASE_URL}{self.QUERY_ENDPOINT}"

        # 构建请求体
        payload = {"source": source}
        if account_ids:
            payload["accountIds"] = account_ids
        if account_names:
            payload["accountNames"] = account_names

        if not account_ids and not account_names:
            return {
                "success": False,
                "data": None,
                "error": "accountIds 和 accountNames 至少提供一个",
                "fallback_needed": False
            }

        try:
            response = requests.post(url, json=payload, headers=self.headers, timeout=30)
            result = response.json()

            code = result.get("code")
            msg = result.get("msg", "")
            data = result.get("data")

            # 成功（红狐API成功码为200或2000，兼容新旧版本）
            if code in (200, 2000):
                accounts = data if isinstance(data, list) else ([data] if data else [])
                return {
                    "success": True,
                    "data": accounts,
                    "error": None,
                    "fallback_needed": False
                }

            # 积分不足 / 调用次数达上限
            if code == 3201 or (code == 500 and ("积分" in msg or "次数" in msg or "上限" in msg)):
                return {
                    "success": False,
                    "data": None,
                    "error": f"API业务错误: {msg}",
                    "fallback_needed": True
                }

            # 其他业务错误
            return {
                "success": False,
                "data": None,
                "error": f"API错误(code={code}): {msg}",
                "fallback_needed": True
            }

        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "data": None,
                "error": "连接失败，请检查网络",
                "fallback_needed": True
            }
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "data": None,
                "error": "请求超时",
                "fallback_needed": True
            }
        except Exception as e:
            return {
                "success": False,
                "data": None,
                "error": f"查询失败: {e}",
                "fallback_needed": True
            }


    def diagnose_account(
        self,
        account_name: Optional[str] = None,
        account_id: Optional[str] = None
    ) -> Dict:
        """
        诊断单个抖音账号（查询+数据整合）

        Args:
            account_name: 抖音昵称
            account_id: 抖音号

        Returns:
            dict: {
                "success": bool,
                "account": dict or None,  # 账号基本信息
                "works": list,            # 近7天作品列表
                "similar_accounts": list, # 相似账号列表
                "error": str or None,
                "fallback_needed": bool
            }
        """
        if not account_name and not account_id:
            return {
                "success": False,
                "account": None,
                "works": [],
                "similar_accounts": [],
                "error": "请提供抖音昵称或抖音号",
                "fallback_needed": False
            }

        # 构建查询参数
        account_ids = [account_id] if account_id else None
        account_names = [account_name] if account_name else None

        print(f"🔍 正在查询抖音账号: {account_name or account_id}")

        # 查询账号信息
        result = self.query_accounts(
            account_ids=account_ids,
            account_names=account_names
        )

        if not result["success"]:
            print(f"❌ 查询失败: {result['error']}")
            return {
                "success": False,
                "account": None,
                "works": [],
                "similar_accounts": [],
                "error": result["error"],
                "fallback_needed": result["fallback_needed"]
            }

        accounts = result["data"]
        if not accounts:
            print(f"❌ 未查询到抖音账号: {account_name or account_id}")
            return {
                "success": False,
                "account": None,
                "works": [],
                "similar_accounts": [],
                "error": "未查询到账号",
                "fallback_needed": True
            }

        # 取第一个匹配结果
        account_data = accounts[0]

        # 提取数据
        account_info = {
            "nickname": account_data.get("nickname", ""),
            "accountId": account_data.get("accountId", ""),
            "uid": account_data.get("uid", ""),
            "avatarUrl": account_data.get("avatarUrl", ""),
            "signature": account_data.get("signature", ""),
            "gender": account_data.get("gender", ""),
            "age": account_data.get("age"),
            "country": account_data.get("country", ""),
            "province": account_data.get("province", ""),
            "city": account_data.get("city", ""),
            "ipLocation": account_data.get("ipLocation", ""),
            "followerCount": account_data.get("followerCount", 0),
            "awemeCount": account_data.get("awemeCount", 0),
            "totalFavorited": account_data.get("totalFavorited", 0),
            "redfoxIndex": account_data.get("redfoxIndex"),
            "crawlTime": account_data.get("crawlTime", ""),
        }

        works = account_data.get("works", [])
        similar_accounts = account_data.get("similarAccounts", [])

        print(f"✅ 查询成功: {account_info['nickname']} (粉丝: {format_number(account_info['followerCount'])})")
        print(f"   作品数: {account_info['awemeCount']} | 近7天作品: {len(works)} | 相似账号: {len(similar_accounts)}")

        return {
            "success": True,
            "account": account_info,
            "works": works,
            "similar_accounts": similar_accounts,
            "error": None,
            "fallback_needed": False
        }

    def calculate_works_stats(self, works: List[Dict]) -> Dict:
        """
        基于近7天作品数据计算v4.0统计指标
        四维度：账号体量(35) + 内容表现(35) + 运营活跃度(20) + 平台指数(10)
        不依赖playCount，使用diggCount/commentCount/shareCount

        Args:
            works: 作品列表（DyWorkVO格式）

        Returns:
            dict: 统计数据
        """
        if not works:
            return {
                "avg_digg_count": 0,
                "avg_comment_count": 0,
                "avg_share_count": 0,
                "spread_coefficient": 0,  # 传播系数 = 分享/点赞
                "update_frequency": 0,     # 近7天发布数
                "publish_periods": [],     # 发布时段列表
            }

        total_digg = sum(w.get("diggCount", 0) or 0 for w in works)
        total_comment = sum(w.get("commentCount", 0) or 0 for w in works)
        total_share = sum(w.get("shareCount", 0) or 0 for w in works)

        n = len(works)
        avg_digg = total_digg / n
        avg_comment = total_comment / n
        avg_share = total_share / n

        # 传播系数 = 分享数/点赞数
        spread_coefficient = (total_share / total_digg * 100) if total_digg > 0 else 0

        # 发布时段
        publish_periods = []
        for w in works:
            create_time = w.get("createTime", "")
            if create_time:
                try:
                    hour = int(create_time.split(" ")[1].split(":")[0])
                    publish_periods.append(hour)
                except (IndexError, ValueError):
                    pass

        return {
            "avg_digg_count": int(avg_digg),
            "avg_comment_count": int(avg_comment),
            "avg_share_count": int(avg_share),
            "spread_coefficient": round(spread_coefficient, 2),  # 百分比
            "update_frequency": n,
            "publish_periods": publish_periods,
        }


def format_number(num) -> str:
    """格式化数字显示"""
    if num is None:
        return "-"
    try:
        num = int(num)
    except (ValueError, TypeError):
        return str(num)

    if num >= 100000000:
        return f"{num/100000000:.1f}亿"
    elif num >= 10000:
        return f"{num/10000:.1f}万"
    else:
        return f"{num:,}"


# 账号分类映射：API原词 → 输出新词
CATEGORY_MAP = {
    "全部": "全部",
    "才艺技能": "个人才艺",
    "生活": "生活vlog",
    "财经": "财富理财",
    "二次元": "二次元",
    "家居家装": "居家装修",
    "教育培训": "学习教育",
    "剧情演绎": "小剧场",
    "科技数码": "数码科技",
    "旅游": "旅行",
    "美食": "美食",
    "美妆": "化妆美容",
    "萌宠": "动物",
    "母婴亲子": "亲子",
    "汽车": "汽车",
    "情感心理": "情感",
    "三农": "三农",
    "医疗健康": "健康医学",
    "时尚": "潮流风尚",
    "舞蹈": "舞蹈才艺",
    "颜值": "颜值造型",
    "人文社科": "人文",
    "音乐": "音乐",
    "影视综艺": "影视",
    "健身": "身体锻炼",
    "体育": "体育",
    "明星八卦": "明星娱乐",
    "游戏": "游戏",
}


def map_category(raw_category: str) -> str:
    """将API原词分类映射为输出新词"""
    return CATEGORY_MAP.get(raw_category, raw_category)


def print_account_summary(result: Dict):
    """打印账号数据摘要"""
    account = result.get("account", {})
    works = result.get("works", [])
    similar = result.get("similar_accounts", [])

    print("\n" + "=" * 60)
    print(f"📋 账号数据摘要")
    print("=" * 60)
    print(f"账号昵称: {account.get('nickname', '-')}")
    print(f"抖音号: {account.get('accountId', '-')}")
    print(f"UID: {account.get('uid', '-')}")
    print(f"账号简介: {account.get('signature', '-')}")
    print(f"性别: {account.get('gender', '-')}")
    print(f"年龄: {account.get('age', '-')}")
    print(f"地域: {account.get('province', '')}{account.get('city', '')}")
    print(f"IP属地: {account.get('ipLocation', '-')}")
    print(f"粉丝数: {format_number(account.get('followerCount'))}")
    print(f"获赞总数: {format_number(account.get('totalFavorited'))}")
    print(f"作品总数: {account.get('awemeCount', '-')}")
    print(f"数据更新: {account.get('crawlTime', '-')}")

    # 作品数据
    if works:
        api = DouyinUserAPI()
        stats = api.calculate_works_stats(works)
        print(f"\n📊 近7天作品统计（共{len(works)}条）:")
        print(f"  平均点赞数: {format_number(stats['avg_digg_count'])}")
        print(f"  平均评论数: {format_number(stats['avg_comment_count'])}")
        print(f"  平均分享数: {format_number(stats['avg_share_count'])}")
        print(f"  传播系数: {stats['spread_coefficient']}%")
        print(f"  更新频率: {stats['update_frequency']}条/7天")

        print(f"\n🎬 作品列表:")
        sorted_works = sorted(works, key=lambda w: w.get("diggCount", 0) or 0, reverse=True)
        for i, work in enumerate(sorted_works[:5], 1):
            title = work.get('title', '无标题')[:30]
            digg = format_number(work.get('diggCount'))
            comment = format_number(work.get('commentCount'))
            share = format_number(work.get('shareCount'))
            print(f"  {i}. {title} | 点赞:{digg} | 评论:{comment} | 分享:{share}")

    # 相似账号
    if similar:
        print(f"\n👥 相似账号（共{len(similar)}个）:")
        for s in similar[:5]:
            classify = CATEGORY_MAP.get(s.get('accountClassifyFirst', ''), s.get('accountClassifyFirst', '-'))
            print(f"  - {s.get('nickname', '-')} | 粉丝:{format_number(s.get('followerCount'))} | 分类:{classify} | 红狐指数:{s.get('redfoxIndex', '-')}")


# 使用示例
if __name__ == "__main__":
    api = DouyinUserAPI()

    if not api.api_key:
        print(f"❌ 未设置环境变量 {DouyinUserAPI.ENV_VAR}")
        print(f"💡 请先运行: export {DouyinUserAPI.ENV_VAR}=你的API密钥值")
        exit(1)

    print(f"✅ API Key已配置: {api.api_key[:8]}...")

    # 示例1：通过名称查询
    print("\n=== 示例1：通过名称查询 ===")
    result = api.diagnose_account(account_name="疯狂小杨哥")
    if result["success"]:
        print_account_summary(result)
    elif result["fallback_needed"]:
        print(f"⚠️ API不可用，需降级为联网搜索: {result['error']}")

    print("\n" + "=" * 60 + "\n")

    # 示例2：通过抖音号查询
    print("=== 示例2：通过抖音号查询 ===")
    result = api.diagnose_account(account_id="yangge_520")
    if result["success"]:
        print_account_summary(result)
    elif result["fallback_needed"]:
        print(f"⚠️ API不可用，需降级为联网搜索: {result['error']}")
