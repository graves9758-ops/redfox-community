#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抖音作品爬取 - API调用脚本
基于红狐API接口 /story/api/dy/data/listWorkByAccount 查询抖音账号数据和近期作品列表
"""

import os
import json
import re
import argparse
import urllib.request
import urllib.error
from datetime import datetime
from typing import Dict, Optional


class DouyinWorksFetcher:
    """抖音作品爬取 - 红狐数据API"""

    BASE_URL = "https://redfox.hk"
    QUERY_ENDPOINT = "/story/api/dy/data/listWorkByAccount"
    ENV_VAR = "REDFOX_API_KEY"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get(self.ENV_VAR, "")
        self.headers = {
            "Content-Type": "application/json",
            "X-API-KEY": self.api_key
        }

    def _is_chinese(self, text: str) -> bool:
        """判断输入是否包含中文字符"""
        return bool(re.search(r'[\u4e00-\u9fff]', text))

    def _is_pure_numeric_id(self, text: str) -> bool:
        """判断输入是否为纯数字ID（userId通常是纯数字uid）"""
        return text.isdigit()

    def _make_request(self, endpoint: str, payload: Dict) -> Dict:
        """发送API请求"""
        url = f"{self.BASE_URL}{endpoint}"
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")

        req = urllib.request.Request(url, data=data, method="POST")
        for key, value in self.headers.items():
            req.add_header(key, value)

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                return result
        except urllib.error.HTTPError as e:
            body = ""
            try:
                body = e.read().decode("utf-8")
            except Exception:
                pass
            # 红狐API限流时可能返回HTML错误页
            if "<html" in body.lower():
                return {"code": -2, "data": None, "msg": "API限流或服务异常，请稍后重试"}
            return {"code": e.code, "data": None, "msg": f"HTTP {e.code}: {body[:200]}"}
        except urllib.error.URLError as e:
            return {"code": -1, "data": None, "msg": f"连接失败: {e.reason}"}
        except Exception as e:
            return {"code": -1, "data": None, "msg": f"请求异常: {e}"}

    def query_account(self, account: str) -> Dict:
        """
        查询抖音账号信息+作品

        Args:
            account: 抖音昵称或抖音号（自动识别）

        Returns:
            dict: {
                "success": bool,
                "account": dict or None,
                "works": list,
                "error": str or None,
                "need_sync": bool (可选，未查询到账号时为True)
            }
        """
        # 自动识别输入类型，构建请求参数
        # 新接口参数：userId（纯数字uid）、uniqueName（昵称/展示ID）、shortId（短ID）
        # 纯数字 → userId；含中文或字母 → uniqueName
        if self._is_pure_numeric_id(account):
            payload = {"userId": account, "source": "抖音作品爬取-GitHub"}
            query_mode = "userId"
        else:
            payload = {"uniqueName": account, "source": "抖音作品爬取-GitHub"}
            query_mode = "uniqueName"

        print(f"🔍 正在查询抖音账号: {account} (模式: {query_mode})")

        result = self._make_request(self.QUERY_ENDPOINT, payload)
        code = result.get("code")
        msg = result.get("msg", "")
        data = result.get("data")

        # 成功码为2000（红狐平台统一成功码）
        # 新接口作品列表在 data.list，账号信息嵌入在每条作品的 author* 字段中
        work_list = data.get("list", []) if data else []
        has_valid_data = data and len(work_list) > 0
        if code == 2000 and has_valid_data:
            # 从第一条作品提取账号信息
            account_info = self._extract_account_info(work_list[0])
            # 用分页total作为作品总数
            account_info["awemeCount"] = data.get("total", len(work_list))

            # 标准化作品字段：新接口字段名映射为内部统一字段名
            works = []
            for item in work_list:
                like = int(item.get("likeCount", 0) or 0)
                comment = int(item.get("commentCount", 0) or 0)
                share = int(item.get("shareCount", 0) or 0)
                collect = int(item.get("collectCount", 0) or 0)
                works.append({
                    "title": item.get("content", ""),
                    "publishTime": item.get("publishTime", ""),
                    "likeCount": like,
                    "commentCount": comment,
                    "shareCount": share,
                    "collectCount": collect,
                    "interactiveCount": like + comment + share + collect,
                    "url": item.get("opusUrl", ""),
                    "videoId": item.get("videoId", ""),
                    "videoType": item.get("videoType", ""),
                    "coverUrl": item.get("coverUrl", ""),
                    "duration": item.get("duration", 0),
                    "tagList": item.get("tagList", []),
                })

            # 昵称查询时，提醒用户确认是否为目标账号
            if query_mode == "uniqueName" and account_info.get('nickname', '') != account:
                print(f"⚠️ 昵称查询返回的是「{account_info['nickname']}」，非您输入的「{account}」")
                print(f"   若非目标账号，请提供抖音号精准查询")

            print(f"✅ 查询成功: {account_info['nickname']} (粉丝: {format_number(account_info['followerCount'])})")
            print(f"   作品总数: {account_info['awemeCount']} | 爬取作品: {len(works)}条")

            return {
                "success": True,
                "account": account_info,
                "works": works,
                "error": None
            }

        # 未找到账号（code=2000但data为空/无作品）
        if code == 2000 and not has_valid_data:
            return {
                "success": False,
                "account": None,
                "works": [],
                "error": None,
                "need_sync": True
            }

        if code == 500 and "未找到" in msg:
            return {
                "success": False,
                "account": None,
                "works": [],
                "error": None,
                "need_sync": True
            }

        # 参数错误
        if code == 400:
            return {
                "success": False,
                "account": None,
                "works": [],
                "error": f"请求参数错误: {msg}"
            }

        # 其他错误（限流、网络异常等）
        return {
            "success": False,
            "account": None,
            "works": [],
            "error": f"API错误(code={code}): {msg}"
        }



    def _extract_account_info(self, work_item: Dict) -> Dict:
        """从作品项中提取作者账号基础信息（新接口账号信息嵌入在每条作品中）"""
        return {
            "nickname": work_item.get("authorName", ""),
            "accountId": work_item.get("authorUniqueId", ""),
            "uniqueId": work_item.get("authorUniqueId", ""),
            "uid": work_item.get("authorUid", ""),
            "secUid": work_item.get("authorSecUid", ""),
            "shortId": work_item.get("authorShortId", ""),
            "avatarUrl": work_item.get("authorAvatarUrl", ""),
            "followerCount": work_item.get("authorFansCount", 0),
            "awemeCount": 0,  # 由 query_account() 用 pagination total 覆盖
        }

    def format_markdown(self, result: Dict) -> str:
        """格式化为Markdown输出"""
        if not result["success"]:
            # 账号未查询到，输出提示信息
            if result.get("need_sync"):
                return "未查询到当前账号的相关信息，请检查输入的抖音号或昵称是否正确。建议使用抖音号进行精准查询。"
            return f"❌ 查询失败: {result['error']}"

        account = result["account"]
        works = result["works"]
        now = datetime.now().strftime("%Y-%m-%d %H:%M")

        # 昵称拼接secUid跳转链接
        nickname_display = f"[{account['nickname']}](https://www.douyin.com/user/{account['secUid']})" if account.get('secUid') else account['nickname']

        lines = []
        lines.append(f"## 🎬 {account['nickname']} - 抖音作品数据")
        lines.append("")
        lines.append("### 账号基础信息")
        lines.append("")
        lines.append("| 昵称 | 抖音号 | UID | 粉丝数 | 作品总数 |")
        lines.append("|------|--------|-----|--------|---------|")
        lines.append(
            f"| {nickname_display} | {account['accountId']} | {account['uid']} "
            f"| {format_number(account['followerCount'])} | {account['awemeCount']} |"
        )
        lines.append("")
        lines.append("---")
        lines.append("")

        # 作品列表
        lines.append(f"### 近期作品（共{len(works)}条）")
        lines.append("")

        if works:
            lines.append("| # | 发布时间 | 标题 | 点赞 | 评论 | 分享 | 收藏 | 互动 | 链接 |")
            lines.append("|---|---------|------|------|------|------|------|------|------|")

            for i, work in enumerate(works, 1):
                title = (work.get("title") or "无标题")[:40]
                publish_time = work.get("publishTime", "-")
                like = format_number(work.get("likeCount"))
                comment = format_number(work.get("commentCount"))
                share = format_number(work.get("shareCount"))
                collect = format_number(work.get("collectCount"))
                interactive = format_number(work.get("interactiveCount"))
                url = work.get("url", "")
                url_display = f"[链接]({url})" if url else "-"

                lines.append(
                    f"| {i} | {publish_time} | {title} | {like} | {comment} | {share} | {collect} | {interactive} | {url_display} |"
                )
        else:
            lines.append("> 暂无作品数据")

        lines.append("")
        lines.append(f"> 作品列表为近期作品数据，最多50条（按发布时间倒序），账号历史作品总数为 {account['awemeCount']} 条。")
        lines.append("")
        lines.append("---")
        lines.append("")

        # 数据亮点 - 互动量TOP3 + 账号特征分析
        if works:
            lines.append("### 数据亮点")
            lines.append("")

            # 互动量TOP3（列表格式，展示作品分析）
            sorted_works = sorted(works, key=lambda w: int(w.get("interactiveCount", 0) or 0), reverse=True)
            top3 = sorted_works[:3]
            medals = ["🥇", "🥈", "🥉"]

            lines.append("#### 互动量TOP3")
            lines.append("")

            for idx, work in enumerate(top3):
                title = (work.get("title") or "无标题")[:50]
                interactive = int(work.get("interactiveCount", 0) or 0)
                like = int(work.get("likeCount", 0) or 0)
                comment = int(work.get("commentCount", 0) or 0)
                share = int(work.get("shareCount", 0) or 0)

                # 生成作品分析：基于账号数据、作品内容、内容定位等总结值得学习点
                analysis_parts = []

                # 互动结构分析
                if interactive > 0:
                    like_ratio = like / interactive
                    comment_ratio = comment / interactive
                    share_ratio = share / interactive

                    if share_ratio > 0.3:
                        analysis_parts.append(f"分享率达{share_ratio*100:.0f}%，传播力极强，用户主动转发意愿高")
                    elif share_ratio > 0.15:
                        analysis_parts.append(f"分享率{share_ratio*100:.0f}%，具备较强传播属性")
                    if comment_ratio > 0.1:
                        analysis_parts.append(f"评论率{comment_ratio*100:.0f}%，用户参与讨论热烈")
                    if like_ratio > 0.85:
                        analysis_parts.append("互动以点赞为主，粉丝粘性高但传播深度有限")

                # 内容特征分析
                title_text = work.get("title") or ""
                if "#" in title_text:
                    analysis_parts.append("标题善用话题标签，借势公域流量扩大曝光")
                if "@" in title_text:
                    analysis_parts.append("内容@关联账号，形成互动联动效应")
                if any(kw in title_text for kw in ["恭喜", "获得", "荣获"]):
                    analysis_parts.append("获奖/荣誉类内容自带话题热度，易引发粉丝共鸣")
                if any(kw in title_text for kw in ["教程", "做法", "怎么做"]):
                    analysis_parts.append("教程类内容实用性强，用户收藏转发意愿高")
                if any(kw in title_text for kw in ["幕后", "花絮", "日常"]):
                    analysis_parts.append("幕后/花絮类内容拉近与粉丝距离，增强亲和力")

                # 粉丝互动比分析
                follower_count = account.get('followerCount', 0) or 0
                if follower_count > 0 and interactive > 0:
                    interaction_fan_ratio = interactive / follower_count
                    if interaction_fan_ratio > 0.1:
                        analysis_parts.append(f"互动/粉丝比达{interaction_fan_ratio*100:.1f}%，粉丝转化效率极高")
                    elif interaction_fan_ratio > 0.05:
                        analysis_parts.append(f"互动/粉丝比{interaction_fan_ratio*100:.1f}%，粉丝活跃度良好")

                analysis = "；".join(analysis_parts) if analysis_parts else "该作品互动表现突出，值得关注"

                lines.append(f"{medals[idx]} **{title}**（互动{format_number(interactive)}）")
                lines.append(f"> {analysis}")
                lines.append("")

            # 账号特征分析
            lines.append("#### 账号特征分析")
            lines.append("")

            # 更新频率分析
            publish_times = []
            for w in works:
                pt = w.get("publishTime", "")
                if pt:
                    try:
                        dt = datetime.strptime(pt, "%Y-%m-%d %H:%M:%S")
                        publish_times.append(dt)
                    except ValueError:
                        pass

            if len(publish_times) >= 2:
                publish_times.sort(reverse=True)
                gaps = [(publish_times[i] - publish_times[i + 1]).days for i in range(len(publish_times) - 1)]
                avg_gap = sum(gaps) / len(gaps)
                if avg_gap < 1.5:
                    freq_desc = f"高频更新，平均每{avg_gap:.1f}天发布1条"
                elif avg_gap < 4:
                    freq_desc = f"稳定更新，平均每{avg_gap:.1f}天发布1条"
                else:
                    freq_desc = f"低频更新，平均每{avg_gap:.1f}天发布1条"
            else:
                freq_desc = f"近期发布{len(works)}条作品"

            lines.append(f"- **更新频率：** {freq_desc}")

            # 互动表现分析
            total_interactive = sum(int(w.get("interactiveCount", 0) or 0) for w in works)
            avg_interactive = total_interactive / len(works) if works else 0
            max_interactive = max(int(w.get("interactiveCount", 0) or 0) for w in works) if works else 0
            min_interactive = min(int(w.get("interactiveCount", 0) or 0) for w in works) if works else 0

            lines.append(f"- **互动表现：** 平均互动{format_number(avg_interactive)}，最高{format_number(max_interactive)}，最低{format_number(min_interactive)}")

            # 爆款特征
            if top3:
                top3_avg = sum(int(w.get("interactiveCount", 0) or 0) for w in top3) / len(top3)
                overall_avg = avg_interactive
                if overall_avg > 0:
                    ratio = top3_avg / overall_avg
                    hot_desc = f"TOP3平均互动{format_number(top3_avg)}，是整体均值的{ratio:.1f}倍"
                else:
                    hot_desc = f"TOP3平均互动{format_number(top3_avg)}"
                lines.append(f"- **爆款特征：** {hot_desc}")

            lines.append("")
            lines.append("---")
            lines.append("")

        lines.append("### 数据说明")
        lines.append("")
        lines.append("- **数据范围：** 近期作品数据，支持分页（最多50条/页），按发布时间倒序")
        lines.append("- **互动数：** 点赞+评论+分享+收藏")
        lines.append("- **作品链接：** 接口返回opusUrl字段，提供作品直达链接")
        lines.append("- **数据来源：** 红狐数据API（广域库）")
        lines.append("")
        lines.append(f"*爬取时间：{now}*")

        return "\n".join(lines)

    def format_json(self, result: Dict) -> str:
        """格式化为JSON输出"""
        return json.dumps(result, ensure_ascii=False, indent=2)


def format_number(num) -> str:
    """格式化数字显示"""
    if num is None or num == "" or num == "—":
        return "-"
    try:
        num = int(float(str(num).replace(",", "")))
    except (ValueError, TypeError):
        return str(num)

    if num >= 100000000:
        return f"{num / 100000000:.1f}亿"
    elif num >= 10000:
        return f"{num / 10000:.1f}w"
    else:
        return f"{num:,}"


def main():
    parser = argparse.ArgumentParser(description="抖音作品爬取工具")
    parser.add_argument("--account", required=True, help="抖音昵称或抖音号")
    parser.add_argument("--output", choices=["markdown", "json"], default="markdown", help="输出格式（默认markdown）")
    args = parser.parse_args()

    fetcher = DouyinWorksFetcher()

    if not fetcher.api_key:
        print(f"❌ 未设置环境变量 {DouyinWorksFetcher.ENV_VAR}")
        print(f"💡 请先运行: export {DouyinWorksFetcher.ENV_VAR}=你的API密钥值")
        return

    print(f"✅ API Key已配置: {fetcher.api_key[:8]}...")

    # 查询模式
    result = fetcher.query_account(args.account)

    if args.output == "json":
        print(fetcher.format_json(result))
    else:
        print(fetcher.format_markdown(result))

    if not result["success"]:
        print(f"\n💡 提示：请提供目标账号的抖音号进行精准查询，避免昵称模糊匹配错误。")


if __name__ == "__main__":
    main()
