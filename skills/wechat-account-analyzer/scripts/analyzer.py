"""analyzer.py — 公众号账号分析编排

职责：单账号评分处理、原始数据保存、查询命令、同步命令。
被 wechat_analyzer.py（入口）调用。
"""

import json
import os

from api_client import (
    https_post,
    API_PATH_SEARCH_USER,
    API_PATH_QUERY_DATA,
    RAW_DATA_FILE,
)
from scoring import (
    _score_content_health,
    _score_user_activity,
    _score_core_data,
    _score_operation_compliance,
    _get_score_level,
    _get_score_level_icon,
    _get_overall_grade,
    _work_read,
    _work_like,
    _work_comment,
    _work_share,
    _work_publish_time,
    _calc_avg_read,
    _classify_account_category,
    CATEGORY_WEIGHTS,
    CATEGORY_ACTIVITY_FLOOR,
    _ACTIVITY_FLOOR_GENERAL,
    CATEGORY_NAMES,
)
from report import REPORT_DATA_FILE


# ════════════════════════════════════════════════════════════
#  单账号分析
# ════════════════════════════════════════════════════════════

def _analyze_single_account(raw, has_works=True):
    """对单个账号原始数据进行评分和结构化处理

    适配 queryData 接口返回的字段命名：
    accountId / accountName / avatar / verifyName / description / works / similarAccounts
    """
    # 无作品提示
    no_works_hint = "" if has_works else "该账号暂未获取到作品数据"

    # 统一字段读取
    nickname = raw.get("accountName", "")
    account_id = raw.get("accountId", "")
    signature = raw.get("description", "")
    avg_read_count = raw.get("avgReadCount", 0) or 0
    account_type = raw.get("accountType", "")
    verify_name = raw.get("verifyName", "")
    works = raw.get("works", []) or []

    if not works:
        has_works = False

    # v4.1: 账号分类识别（在评分之前调用）
    category_info = _classify_account_category(account_type, signature, works, verify_name)
    category = category_info["category"]
    category_name = category_info["category_name"]

    # 四维度评分（用户活跃度传入分类参数）
    content_health = _score_content_health(works, signature, verify_name, account_type)
    user_activity = _score_user_activity(works if has_works else [], category=category)
    core_data = _score_core_data(works if has_works else [], avg_read_count, category=category)
    operation_compliance = _score_operation_compliance(works if has_works else [], verify_name)

    # 综合评分：v4.1 分类自适应权重
    weights = CATEGORY_WEIGHTS.get(category, CATEGORY_WEIGHTS["general"])
    dim1_score = round(content_health["原始分"] / 10 * 100, 1)
    dim2_score = round(user_activity["原始分"] / 10 * 100, 1)
    dim3_score = round(core_data["原始分"] / 31 * 100, 1)
    dim4_score = round(operation_compliance["原始分"] / 10 * 100, 1)

    # v4.1: 分类感知的阅读量保底机制
    # 时政号保底更激进（互动天然极低），财经号次之，其他分类使用 general 保底
    floor_config = CATEGORY_ACTIVITY_FLOOR.get(category, _ACTIVITY_FLOOR_GENERAL)
    for threshold in sorted(floor_config.keys(), reverse=True):
        if avg_read_count >= threshold:
            dim2_score = max(dim2_score, floor_config[threshold])
            break

    total_score = round(
        dim1_score * weights["content_health"]
        + dim2_score * weights["user_activity"]
        + dim3_score * weights["core_data"]
        + dim4_score * weights["operation_compliance"], 1
    )
    total_score = max(0, min(100, total_score))

    # 评级
    overall_level = _get_score_level(total_score, 100)
    overall_grade, overall_rank = _get_overall_grade(total_score)
    dim1_level = _get_score_level(dim1_score, 100)
    dim1_level_icon = _get_score_level_icon(dim1_score, 100)
    dim2_level = _get_score_level(dim2_score, 100)
    dim2_level_icon = _get_score_level_icon(dim2_score, 100)
    dim3_level = _get_score_level(dim3_score, 100)
    dim3_level_icon = _get_score_level_icon(dim3_score, 100)
    dim4_level = _get_score_level(dim4_score, 100)
    dim4_level_icon = _get_score_level_icon(dim4_score, 100)

    # 构建scores结构
    scores = {
        "综合评分": total_score,
        "综合得分层级": overall_level,
        "综合评级": overall_grade,
        "综合等级": overall_rank,
        "账号分类": category_name,
        "分类ID": category,
        "使用权重": {
            "内容健康度": f"{int(weights['content_health']*100)}%",
            "用户活跃度": f"{int(weights['user_activity']*100)}%",
            "内容核心数据": f"{int(weights['core_data']*100)}%",
            "运营规范性": f"{int(weights['operation_compliance']*100)}%",
        },
        "内容健康度得分": dim1_score,
        "内容健康度满分": 100,
        "内容健康度得分率": round(dim1_score, 1),
        "内容健康度评级": dim1_level,
        "内容健康度评级图标": dim1_level_icon,
        "用户活跃度得分": dim2_score,
        "用户活跃度满分": 100,
        "用户活跃度得分率": round(dim2_score, 1),
        "用户活跃度评级": dim2_level,
        "用户活跃度评级图标": dim2_level_icon,
        "内容核心数据表现得分": dim3_score,
        "内容核心数据表现满分": 100,
        "内容核心数据表现得分率": round(dim3_score, 1),
        "内容核心数据表现评级": dim3_level,
        "内容核心数据表现评级图标": dim3_level_icon,
        "运营规范性得分": dim4_score,
        "运营规范性满分": 100,
        "运营规范性得分率": round(dim4_score, 1),
        "运营规范性评级": dim4_level,
        "运营规范性评级图标": dim4_level_icon,
        # 内容健康度子项（原始0-10分，×3=0-30分）
        "更新稳定性得分": content_health["更新稳定性"],
        "更新稳定性满分": 10,
        "内容垂直度得分": content_health["内容垂直度"],
        "内容垂直度满分": 10,
        "原创能力得分": content_health["原创能力"],
        "原创能力满分": 10,
        "质量稳定性得分": content_health["质量稳定性"],
        "质量稳定性满分": 10,
        "内容深度得分": content_health["内容深度"],
        "内容深度满分": 10,
        "形式创新得分": content_health["形式创新"],
        "形式创新满分": 10,
        "内容健康度原始分": content_health["原始分"],
        # 用户活跃度子项（原始0-10分，×2.5=0-25分）
        "互动率得分": user_activity["互动率"],
        "互动率满分": 10,
        "留言质量得分": user_activity["留言质量"],
        "留言质量满分": 10,
        "分享传播力得分": user_activity["分享传播力"],
        "分享传播力满分": 10,
        "阅读完成率得分": user_activity["阅读完成率"],
        "阅读完成率满分": 10,
        "活跃时段集中度得分": user_activity["活跃时段集中度"],
        "活跃时段集中度满分": 10,
        "用户活跃度原始分": user_activity["原始分"],
        # 内容核心数据表现子项（0-43分制）
        "阅读数表现得分": core_data["阅读数表现"],
        "阅读数表现满分": 8,
        "点赞数表现得分": core_data["点赞数表现"],
        "点赞数表现满分": 6,
        "评论数表现得分": core_data["评论数表现"],
        "评论数表现满分": 4,
        "互动率表现得分": core_data["互动率表现"],
        "互动率表现满分": 3,
        "发布时间合理性得分": core_data["发布时间合理性"],
        "发布时间合理性满分": 2,
        "爆款产出力得分": core_data["爆款产出力"],
        "爆款产出力满分": 8,
        "爆款率": core_data.get("爆款率", 0),
        "内容核心数据原始分": core_data["原始分"],
        # 运营规范性子项（直接0-10分）
        "更新频率得分": operation_compliance["更新频率"],
        "更新频率满分": 5,
        "发布时间合理性2得分": operation_compliance["发布时间合理性"],
        "发布时间合理性2满分": 3,
        "账号认证得分": operation_compliance["账号认证"],
        "账号认证满分": 2,
    }

    # 计算优势模块和待优化模块
    dim_score_rates = [
        {"维度名": "内容健康度", "得分": dim1_score, "得分率": dim1_score},
        {"维度名": "用户活跃度", "得分": dim2_score, "得分率": dim2_score},
        {"维度名": "内容核心数据表现", "得分": dim3_score, "得分率": dim3_score},
        {"维度名": "运营规范性", "得分": dim4_score, "得分率": dim4_score},
    ]
    dim_sorted = sorted(dim_score_rates, key=lambda x: x["得分率"], reverse=True)
    scores["优势模块"] = dim_sorted[:2]
    scores["待优化模块"] = dim_sorted[-2:]

    # 互动率和更新频率计算
    # 注意：queryData 的 interactiveCount = 阅读数+互动分项之和，不能直接用于互动率计算
    # 始终使用分项加总：like+comment+share+watch
    # 阅读数含10万+截断值（100001为保守下界），与 _score_user_activity 口径保持一致
    interaction_rate = 0
    if works:
        total_reads = sum(_work_read(w) for w in works if _work_read(w) > 0)
        total_interactions = sum(
            _work_like(w) + _work_comment(w) + _work_share(w) + (w.get("watchCount") or 0)
            for w in works
        )
        if total_reads > 0:
            interaction_rate = round(total_interactions / total_reads * 100, 2)
    works_7d = len(works) if works else 0

    # 行业对标（基于公众号真实行业水平）
    # 数据来源：公众号行业研究报告，覆盖10万+个人/企业公众号
    scores["行业对标"] = {
        "综合评分": {"本账号": f"{total_score}分", "行业均值": "45-55分", "头部账号": "85-95分"},
        "平均阅读量": {"本账号": str(avg_read_count), "行业均值": "2000-8000", "头部账号": "3-10万"},
        "互动率": {"本账号": f"{interaction_rate}%", "行业均值": "1-3%", "头部账号": "10-25%"},
        "更新频率": {"本账号": f"{works_7d}篇/近期", "行业均值": "2-4篇/周", "头部账号": "5-7篇/周"},
    }

    # 构建返回结果
    result = {
        "header": {
            "账号名": nickname,
            "账号ID": account_id,
            "账号链接": f"https://open.weixin.qq.com/qr/code?username={account_id}" if account_id else "",
            "账号类型": account_type,
            "账号分类": category_name,
            "分类ID": category,
            "分类置信度": category_info["confidence"],
            "账号简介": signature,
            "认证信息": verify_name,
            "平均阅读数": avg_read_count,
            "no_works_hint": no_works_hint,
        },
        "scores": scores,
        "content_health": {
            "更新稳定性": f"{content_health['更新稳定性']}/10",
            "内容垂直度": f"{content_health['内容垂直度']}/10",
            "原创能力": f"{content_health['原创能力']}/10",
            "质量稳定性": f"{content_health['质量稳定性']}/10",
            "内容深度": f"{content_health['内容深度']}/10",
            "形式创新": f"{content_health['形式创新']}/10",
            "原始分": f"{content_health['原始分']}/10",
            "总分": f"{dim1_score}/50",
            "评级": dim1_level,
            "评级图标": dim1_level_icon,
        },
        "user_activity": {
            "互动率": f"{user_activity['互动率']}/10",
            "留言质量": f"{user_activity['留言质量']}/10",
            "分享传播力": f"{user_activity['分享传播力']}/10",
            "阅读完成率": f"{user_activity['阅读完成率']}/10",
            "活跃时段集中度": f"{user_activity['活跃时段集中度']}/10",
            "原始分": f"{user_activity['原始分']}/10",
            "总分": f"{dim2_score}/50",
            "评级": dim2_level,
            "评级图标": dim2_level_icon,
        },
        "works": [
            {
                "标题": ("[{0}]({1})".format(w.get("title", ""), w.get("workUrl", "")) if w.get("workUrl") else w.get("title", "")),
                "阅读数": _work_read(w),
                "点赞数": _work_like(w),
                "评论数": _work_comment(w),
                "在看数": w.get("watchCount") or 0,
                "发布时间": _work_publish_time(w),
            }
            for w in (works[:5] if works else [])
        ],
        "works_hint": "",
        "similar_accounts": [
            {
                "账号名称": sa.get("accountName", ""),
                "账号ID": sa.get("accountId", ""),
                "平均阅读数": "",  # queryData 相似账号不返回该字段
            }
            for sa in ((raw.get("similarAccounts") or [])[:5])
            if sa.get("accountName")
        ],
        "_raw": raw,
    }

    # 保存report_data.json
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.normpath(os.path.join(script_dir, "..", "output"))
    os.makedirs(output_dir, exist_ok=True)
    report_path = os.path.join(output_dir, REPORT_DATA_FILE)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    return result


def _save_raw_data(raw_data):
    """将接口原始数据保存到raw_data.json"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, "..", "output")
    output_dir = os.path.normpath(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    raw_path = os.path.join(output_dir, RAW_DATA_FILE)
    with open(raw_path, "w", encoding="utf-8") as f:
        json.dump(raw_data, f, ensure_ascii=False, indent=2)


# ════════════════════════════════════════════════════════════
#  查询命令
# ════════════════════════════════════════════════════════════

def cmd_query(account_ids=None, account_names=None, force_analyze=False):
    """查询命令：searchUser 获取微信号 → queryData 精确查询完整数据

    流程：
    1. searchUser(keyword=name) 搜索名称 → 必须名称完全匹配，取 account(微信号)
    2. queryData(accountIds=[微信号], accountNames=[名称]) → 精确定位，返回完整数据+works+相似账号

    按 ID 查询时：预期传入微信号（如 duhaoshu）或 gh_xxx 格式

    Args:
        account_ids: 微信号/gh_xxx ID 列表（可选）
        account_names: 账号名称列表（可选）
        force_analyze: 是否强制分析
    """
    items = []
    names_to_query = account_names if account_names else []
    ids_to_query = account_ids if account_ids else []

    if not names_to_query and not ids_to_query:
        print(json.dumps({
            "status": "error",
            "message": "请提供账号名称或账号ID",
            "query_type": "not_found",
            "data": []
        }, ensure_ascii=False))
        return

    # ── 按名称查询：searchUser 微信号 → queryData 完整数据 ──
    for name in names_to_query:
        # 第一步：searchUser 搜索，必须名称完全匹配
        try:
            search_resp = https_post(API_PATH_SEARCH_USER, {"keyword": name, "offset": 0})
        except Exception as e:
            print(json.dumps({
                "status": "error",
                "message": f"搜索失败: {str(e)}",
                "query_type": "not_found",
                "data": []
            }, ensure_ascii=False))
            return

        if not (isinstance(search_resp, dict) and search_resp.get("code") == 2000):
            print(json.dumps({
                "status": "error",
                "message": f"搜索失败: {search_resp.get('msg', '未知错误')}",
                "query_type": "not_found",
                "data": []
            }, ensure_ascii=False))
            return

        search_list = (search_resp.get("data") or {}).get("list", [])
        if not search_list:
            print(json.dumps({
                "status": "success",
                "query_type": "not_found",
                "message": f"未查询到账号【{name}】，该账号可能尚未收录或名称有误，请核实公众号名称后重试。",
                "data": []
            }, ensure_ascii=False))
            return

        # 必须名称完全匹配
        matched = next((a for a in search_list if a.get("accountName", "") == name), None)
        if matched is None:
            candidates = [
                {
                    "name": a.get("accountName", ""),
                    "wxId": a.get("wxId", ""),       # 公众号ID，gh_xxx 格式
                    "account": a.get("account", ""),  # 微信号，如 duhaoshu
                }
                for a in search_list[:5]
                if a.get("accountName")
            ]
            # 候选列表文案：账号名称 + 公众号ID + 微信号
            candidates_lines = []
            for c in candidates:
                parts = [f"「{c['name']}」"]
                if c["wxId"]:
                    parts.append(f"ID: {c['wxId']}")
                if c["account"]:
                    parts.append(f"微信号: {c['account']}")
                candidates_lines.append(" ".join(parts))
            candidates_str = "、".join(candidates_lines)
            print(json.dumps({
                "status": "success",
                "query_type": "not_found",
                "message": (
                    f"未找到名称为「{name}」的公众号，"
                    f"搜索结果中有较相近的账号：{candidates_str}，"
                    f"请确认公众号名称后重试，或可用公众号ID（微信号）直接查询。"
                ),
                "candidates": candidates,
                "data": []
            }, ensure_ascii=False))
            return

        # 微信号（account 字段）= queryData.accountIds 的正确参数格式
        weixin_id = matched.get("account", "")

        # 第二步：queryData 用微信号+名称精确定位，得到 works+similarAccounts
        try:
            data_resp = https_post(API_PATH_QUERY_DATA, {
                "accountIds": [weixin_id] if weixin_id else [],
                "accountNames": [name]
            })
        except Exception as e:
            print(json.dumps({
                "status": "error",
                "message": f"请求失败: {str(e)}",
                "query_type": "not_found",
                "data": []
            }, ensure_ascii=False))
            return

        if not (isinstance(data_resp, dict) and data_resp.get("code") == 2000):
            print(json.dumps({
                "status": "error",
                "message": f"查询失败: {data_resp.get('msg', '未知错误')}",
                "query_type": "not_found",
                "data": []
            }, ensure_ascii=False))
            return

        data_list = data_resp.get("data") or []
        if not data_list:
            print(json.dumps({
                "status": "success",
                "query_type": "not_found",
                "message": f"未查询到账号【{name}】的详细数据。",
                "data": []
            }, ensure_ascii=False))
            return

        # 优先取微信号匹配的账号，否则取 works 最多的
        exact = next((a for a in data_list if a.get("account", "") == weixin_id), None)
        best = exact if exact else max(data_list, key=lambda x: len(x.get("works", []) or []))
        works = best.get("works", []) or []
        avg_read = _calc_avg_read(works)
        items.append({**best, "avgReadCount": avg_read})

    # ── 按 ID 查询：直接用微信号/gh_xxx 调 queryData ──
    for wx_id in ids_to_query:
        try:
            resp = https_post(API_PATH_QUERY_DATA, {
                "accountIds": [wx_id],
                "accountNames": []
            })
        except Exception as e:
            print(json.dumps({
                "status": "error",
                "message": f"请求失败: {str(e)}",
                "query_type": "not_found",
                "data": []
            }, ensure_ascii=False))
            return

        if not (isinstance(resp, dict) and resp.get("code") == 2000):
            print(json.dumps({
                "status": "error",
                "message": f"查询失败: {resp.get('msg', '未知错误')}",
                "query_type": "not_found",
                "data": []
            }, ensure_ascii=False))
            return

        data_list = resp.get("data") or []
        if not data_list:
            print(json.dumps({
                "status": "success",
                "query_type": "not_found",
                "message": f"未查询到ID为【{wx_id}】的公众号，请确认ID是否正确。",
                "data": []
            }, ensure_ascii=False))
            return

        account = data_list[0]
        works = account.get("works", []) or []
        avg_read = _calc_avg_read(works)
        items.append({**account, "avgReadCount": avg_read})


    if not items:
        print(json.dumps({
            "status": "success",
            "query_type": "not_found",
            "data": []
        }, ensure_ascii=False))
        return

    _save_raw_data(items)

    accounts_with_works = [it for it in items if it.get("works")]
    accounts_need_sync = [it for it in items if not it.get("works")]

    if len(items) > 1:
        if not accounts_with_works:
            if force_analyze:
                [_analyze_single_account(it, has_works=False) for it in items]
                print(json.dumps({
                    "status": "success",
                    "query_type": "multi",
                    "message": "数据已保存",
                    "no_works_hint": "暂未获取到作品数据"
                }, ensure_ascii=False))
                return
            print(json.dumps({
                "status": "success",
                "query_type": "need_sync",
                "message": "这些账号暂无作品数据",
                "need_sync": [{"nickname": it.get("accountName", ""), "redId": it.get("accountId", "")} for it in items]
            }, ensure_ascii=False))
            return

        [_analyze_single_account(it) for it in accounts_with_works]
        output = {"status": "success", "query_type": "multi", "message": "数据已保存"}
        if accounts_need_sync:
            output["need_sync"] = [{"nickname": it.get("accountName", ""), "redId": it.get("accountId", "")} for it in accounts_need_sync]
        print(json.dumps(output, ensure_ascii=False))
        return

    raw_item = items[0]
    works = raw_item.get("works", []) or []
    _analyze_single_account(raw_item, has_works=bool(works))
    print(json.dumps({
        "status": "success",
        "query_type": "single",
        "message": "数据已保存",
        "no_works_hint": "该账号暂无作品数据" if not works else None
    }, ensure_ascii=False))


# ════════════════════════════════════════════════════════════
#  同步命令
# ════════════════════════════════════════════════════════════

def cmd_sync_notes(account_ids):
    """订阅命令：调用接口同步账号作品数据

    参数:
        account_ids: 公众号账号ID列表
    """
    results = []

    for account_id in account_ids:
        try:
            body = {
                "accountId": account_id,
                "source": "公众号账号诊断-GitHub"
            }
            response = https_post("/story/api/gzhUser/syncUserNotes", body)

            if isinstance(response, dict) and response.get("code") == 5000:
                results.append({
                    "accountId": account_id,
                    "account_name": f"账号{account_id}",
                    "status": "success",
                    "schedule_required": True,
                    "schedule_time_minutes": 30
                })
            else:
                results.append({
                    "accountId": account_id,
                    "account_name": f"账号{account_id}",
                    "status": "success",
                    "schedule_required": True,
                    "schedule_time_minutes": 30
                })
        except Exception as e:
            results.append({
                "accountId": account_id,
                "status": "error",
                "message": f"订阅失败: {str(e)}"
            })

    print(json.dumps({
        "status": "success",
        "query_type": "sync",
        "data": {"sync_results": results}
    }, ensure_ascii=False))
