"""report.py — HTML 报告生成

职责：模板替换、条件区域控制、单账号/多账号 HTML 报告生成。
被 wechat_analyzer.py（入口）和 analyzer.py 调用。
"""

import json
import os
import re
import sys
from datetime import datetime

from scoring import _format_interactive_count


# ── 常量 ──
REPORT_DATA_FILE = "report_data.json"
MULTI_REPORT_DATA_FILE = "multi_report_data.json"

# 各维度满分映射
SCORE_MAX_MAP = {
    "内容健康度": 100,
    "用户活跃度": 100,
    "内容核心数据表现": 100,
    "运营规范性": 100,
}


# ════════════════════════════════════════════════════════════
#  HTML 模板辅助函数
# ════════════════════════════════════════════════════════════

def _flatten_dict(d, parent_key="", sep="."):
    """将嵌套字典扁平化为点分隔的键名"""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(_flatten_dict(v, new_key, sep).items())
        elif isinstance(v, list):
            for i, item in enumerate(v):
                if isinstance(item, dict):
                    items.extend(_flatten_dict(item, f"{new_key}[{i}]", sep).items())
                else:
                    items.append((f"{new_key}[{i}]", str(item) if item is not None else ""))
        else:
            items.append((new_key, str(v) if v is not None else ""))
    return dict(items)


def _build_replacements(report_data):
    """构建HTML模板替换字典"""
    replacements = {}

    # 近期作品表格行
    works_rows = []
    for w in report_data.get("works", []):
        if not isinstance(w, dict):
            continue
        title = w.get("title", "无标题")[:15].replace(" ", "")
        if not title.strip():
            title = "无标题"
        date_str = w.get("date", "-") or "-"
        likes = w.get("likes", "0") or "0"
        url = w.get("workUrl", "") or ""
        link = f'<a href="{url}" target="_blank">查看</a>' if url else "-"
        works_rows.append(f"<tr><td>{title}</td><td>{date_str}</td><td>{likes}</td><td>{link}</td></tr>")
    replacements["{{works_table_rows}}"] = "\n".join(works_rows)

    # 爆文列表表格
    viral_list = report_data.get("viral", {}).get("爆文列表", [])
    if not viral_list:
        viral_list = report_data.get("爆文列表", [])
    viral_rows = []
    if viral_list:
        for v in viral_list:
            if not isinstance(v, dict):
                continue
            title = v.get("标题", v.get("title", "-"))[:20] or "-"
            pub_time = v.get("发布时间", v.get("publishTime", "-")) or "-"
            interactive = v.get("互动数", v.get("interactiveCount", "-")) or "-"
            multiple = v.get("超标准倍数", v.get("multiple", "-")) or "-"
            viral_rows.append(f"<tr><td>{title}</td><td>{pub_time}</td><td>{interactive}</td><td>{multiple}</td></tr>")
    if viral_rows:
        viral_table_html = (
            '<table class="viral-table">\n'
            '    <tr><th>爆文标题</th><th>发布时间</th><th>互动数</th><th>超标准倍数</th></tr>\n'
            + "\n".join(viral_rows) + "\n"
            '</table>'
        )
    else:
        viral_table_html = '<div class="info-row"><span class="label">爆文列表：</span><span class="value">暂无爆文</span></div>'
    replacements["{{爆文列表表格}}"] = viral_table_html

    return replacements


def _is_empty_field(val):
    """判断字段是否为空"""
    return str(val).strip() in ("", "None", "none")


def _remove_section_markers(html, marker_name, should_show):
    """根据条件移除或保留标记区域"""
    start_tag = f"<!-- {marker_name}_START -->"
    end_tag = f"<!-- {marker_name}_END -->"
    if should_show:
        html = html.replace(start_tag, "").replace(end_tag, "")
    else:
        html = re.sub(rf'<!-- {marker_name}_START -->.*?<!-- {marker_name}_END -->', '', html, flags=re.DOTALL).rstrip()
    return html


def _remove_empty_info_rows(html):
    """移除HTML中值为空的info-row行"""
    html = re.sub(r'<div class="info-row">\s*<span class="label">[^<]*</span>\s*<span class="value">\s*</span>\s*</div>', '', html)
    return html


def _remove_conditional_sections(html, report_data):
    """根据数据条件移除空数据模块"""
    scores = report_data.get("scores", {})

    # 爆文能力：始终展示，移除条件隐藏
    # viral_count = scores.get("爆文数", "")
    # try:
    #     viral_val = int(viral_count) if not _is_empty_field(viral_count) else 0
    # except (ValueError, TypeError):
    #     viral_val = 0
    # html = _remove_section_markers(html, "SECTION_VIRAL", viral_val > 0)
    # 直接移除标记，始终显示爆文能力模块
    html = html.replace("<!-- SECTION_VIRAL_START -->", "").replace("<!-- SECTION_VIRAL_END -->", "")

    # 近期作品：works为空时隐藏
    works = report_data.get("works", [])
    has_valid_works = any(isinstance(w, dict) and w.get("title", "").strip() for w in works)
    html = _remove_section_markers(html, "SECTION_WORKS", has_valid_works)

    # 可强化：内容健康度<16分时显示
    account_health = report_data.get("content_health", {})
    scores = report_data.get("scores", {})
    health_score = scores.get("内容健康度得分", 0)
    show_can_enhance = health_score < 16
    html = _remove_section_markers(html, "SECTION_CAN_ENHANCE", show_can_enhance)

    return html


# ════════════════════════════════════════════════════════════
#  单账号 HTML 报告生成
# ════════════════════════════════════════════════════════════

def cmd_generate_html():
    """生成单账号HTML命令 - 直接使用report_data.json中的similar_accounts数据"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.normpath(os.path.join(script_dir, "..", "output", REPORT_DATA_FILE))
    template_path = os.path.normpath(os.path.join(script_dir, "..", "assets", "report_template.html"))
    raw_data_path = os.path.normpath(os.path.join(script_dir, "..", "output", "raw_data.json"))

    if not os.path.exists(data_path):
        print(json.dumps({"status": "error", "message": f"报告数据文件不存在: {data_path}，请先完成诊断报告生成并保存report_data.json"}, ensure_ascii=False))
        sys.exit(1)

    if not os.path.exists(template_path):
        print(json.dumps({"status": "error", "message": f"模板文件不存在: {template_path}"}, ensure_ascii=False))
        sys.exit(1)

    with open(data_path, "r", encoding="utf-8") as f:
        report_data = json.load(f)

    # 读取原始数据作为备用数据源
    raw_data = {}
    if os.path.exists(raw_data_path):
        try:
            with open(raw_data_path, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
        except Exception:
            pass  # 原始数据读取失败时忽略

    with open(template_path, "r", encoding="utf-8") as f:
        html = f.read()

    replacements = _build_replacements(report_data)

    # 相似账号卡片（账号名称为超链接）- 直接使用report_data.json中的similar_accounts
    # 每个账号一行，展示：账号名称（超链接）、平均阅读、总互动、推荐理由、发文特点、可学之处
    similar_cards = []
    for sa in report_data.get("similar_accounts", []):
        if not isinstance(sa, dict):
            continue
        name = sa.get("账号名称") or sa.get("accountName") or sa.get("nickname") or sa.get("name", "")
        account_url = sa.get("账号链接") or sa.get("profileUrl") or sa.get("url", "")
        avg_read = sa.get("平均阅读数") or sa.get("avgReadCount") or 0
        total_interactive = sa.get("总互动") or sa.get("totalInteractiveCount") or sa.get("interactiveCountThirty", 0)
        recommend_reason = sa.get("推荐理由") or sa.get("recommendReason") or ""
        post_feature = sa.get("发文特点") or sa.get("postFeature") or ""
        learn_point = sa.get("可学之处") or sa.get("learnPoint") or ""

        # 账号名称超链接
        name_html = f'<a href="{account_url}" target="_blank" style="color:#1890ff;text-decoration:none;font-weight:500;">{name}</a>' if account_url else name
        # 如果没有链接但有accountId，构造链接
        if not account_url:
            account_id = sa.get("accountId") or sa.get("redId") or sa.get("userId", "")
            if account_id:
                account_url = f"https://mp.weixin.qq.com/profile/{account_id}"
                name_html = f'<a href="{account_url}" target="_blank" style="color:#1890ff;text-decoration:none;font-weight:500;">{name}</a>'

        similar_cards.append(
            f'<div class="similar-card-row" style="padding:12px 0;border-bottom:1px solid #f0f0f0;">'
            f'<div style="margin-bottom:6px;"><strong>{name_html}</strong> | 平均阅读：{avg_read} | 总互动：{total_interactive}</div>'
            f'<div style="font-size:13px;color:#666;margin-bottom:4px;"><strong>推荐理由：</strong>{recommend_reason}</div>'
            f'<div style="font-size:13px;color:#666;margin-bottom:4px;"><strong>发文特点：</strong>{post_feature}</div>'
            f'<div style="font-size:13px;color:#666;"><strong>可学之处：</strong>{learn_point}</div>'
            f'</div>'
        )
    replacements["{{similar_accounts_cards}}"] = "\n".join(similar_cards)

    # 执行替换
    for key, val in replacements.items():
        html = html.replace(key, val)

    # 条件移除空数据模块
    html = _remove_conditional_sections(html, report_data)

    # 相似账号区域 - 直接展示（移除条件注释）
    html = html.replace("<!-- SIMILAR_START -->", "").replace("<!-- SIMILAR_END -->", "")

    html = _remove_empty_info_rows(html)

    # ========== 自检：检测未替换的模板字段 ==========
    unreplaced = re.findall(r'\{\{[^}]+\}\}', html)
    if unreplaced:
        # 收集所有未替换的字段
        unique_unreplaced = list(set(unreplaced))
        # 扁平化分析数据和原始数据
        flat_data = _flatten_dict(report_data)
        _rd = raw_data[0] if isinstance(raw_data, list) and len(raw_data) > 0 else raw_data
        flat_raw = _flatten_dict(_rd) if _rd and isinstance(_rd, dict) else {}

        # 字段名映射：模板字段名 -> 原始数据字段名
        field_mapping = {
            "总在看数": "collected",
            "总点赞数": "liked",
            "近30天互动量": "interactions_30d",
            "近30天发作品数": "works_30d",
            "作品总数": "works_total",
            "账号名": "nickname",
            "官方等级": "level",
        }

        for field in unique_unreplaced:
            field_name = field[2:-2]  # 移除 {{ 和 }}
            found_value = None

            # 第一步：从分析数据中查找
            for k, v in flat_data.items():
                if k == field_name or k.endswith("." + field_name):
                    if v is not None and str(v).strip() != "" and str(v) != "0":
                        found_value = v
                        break

            # 第二步：分析数据为空，从原始数据中查找
            if found_value is None and flat_raw:
                # 先尝试字段名映射
                if field_name in field_mapping:
                    raw_field = field_mapping[field_name]
                    for k, v in flat_raw.items():
                        if k == raw_field or k.endswith("." + raw_field):
                            if v is not None and str(v).strip() != "":
                                found_value = v
                                # 格式化大数字
                                if field_name in ["总在看数", "总点赞数", "近30天互动量"]:
                                    found_value = _format_interactive_count(v)
                                break
                # 再尝试直接匹配字段名
                if found_value is None:
                    for k, v in flat_raw.items():
                        if k == field_name or k.endswith("." + field_name):
                            if v is not None and str(v).strip() != "":
                                found_value = v
                                break

            # 第三步：根据值进行处理
            if found_value is not None and str(found_value).strip() != "":
                html = html.replace(field, str(found_value))
            else:
                # 数据中无值，根据字段类型填充默认值
                numeric_fields = ["得分", "分", "互动", "收藏", "点赞", "数", "率", "量", "倍", "篇", "天", "中位数参考", "优秀值参考", "等级"]
                is_numeric = any(nf in field_name for nf in numeric_fields)
                if is_numeric:
                    html = html.replace(field, "0")
                else:
                    html = html.replace(field, "")

        # 再次检查是否还有未替换字段
        remaining = re.findall(r'\{\{[^}]+\}\}', html)
        if remaining:
            print(json.dumps({
                "status": "error",
                "message": f"HTML模板字段未完全替换: {list(set(remaining))}",
                "unreplaced_fields": list(set(remaining))
            }, ensure_ascii=False))
            sys.exit(1)

    # 输出HTML文件
    output_dir = os.path.normpath(os.path.join(script_dir, "..", "output"))
    os.makedirs(output_dir, exist_ok=True)

    account_name = report_data.get("header", {}).get("账号名", "report")
    safe_name = account_name.replace("/", "_").replace("\\", "_").replace(" ", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(output_dir, f"{safe_name}_诊断报告_{timestamp}.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    result_info = {
        "status": "success",
        "message": "HTML报告已生成",
        "output_path": output_path
    }
    print(json.dumps(result_info, ensure_ascii=False))


# ════════════════════════════════════════════════════════════
#  多账号对比 HTML 报告生成
# ════════════════════════════════════════════════════════════

def _build_account_detail_html(account_data, account_index):
    """为多账号报告生成单个账号的详情HTML"""
    replacements = _build_replacements(account_data)

    # 评分条
    for dim, max_score in SCORE_MAX_MAP.items():
        score_key = dim + "得分"
        pct_key = dim + "得分_pct"
        score_val = replacements.get("{{" + score_key + "}}", "0")
        try:
            pct = round(int(score_val) / max_score * 100)
        except (ValueError, ZeroDivisionError):
            pct = 0
        replacements["{{" + pct_key + "}}"] = str(pct)

    header = account_data.get("header", {})
    raw_data = account_data.get("_raw", {})
    avatar = raw_data.get("头像", "")
    name = header.get("账号名", "")
    tag = header.get("账号标识", "")
    score = replacements.get("{{综合评分}}", "-")

    # 构建详情HTML（简化版，用于多账号对比）
    detail = f'''  <div class="account-detail">
    <div class="account-detail-header">
      <img src="{avatar}" onerror="this.style.display='none'">
      <span class="name">{name}</span>
      <span class="tag">{tag}</span>
      <span class="score">{score}分</span>
    </div>
    <div class="account-detail-body">
      <div class="score-bars">
        <div class="score-bar-item"><span class="name">内容健康度</span><div class="bar-bg"><div class="bar-fill" style="width:{replacements.get("{{内容健康度得分_pct}}", "0")}%"></div></div><span class="val">{replacements.get("{{内容健康度得分}}", "0")}分</span></div>
        <div class="score-bar-item"><span class="name">用户活跃度</span><div class="bar-bg"><div class="bar-fill" style="width:{replacements.get("{{用户活跃度得分_pct}}", "0")}%"></div></div><span class="val">{replacements.get("{{用户活跃度得分}}", "0")}分</span></div>

      </div>

      <div style="margin-top:12px; font-weight:600; font-size:13px; color:#FF2442;">综合诊断</div>
      <div class="conclusion">
        <p>{replacements.get("{{综合诊断结论内容}}", "")}</p>
      </div>'''

    # 行动处方
    detail += f'''
      <div style="margin-top:10px; font-weight:600; font-size:13px; color:#FF2442;">行动处方</div>
      <div class="action-item"><strong>问题归因</strong>：<br>• {replacements.get("{{问题归因1}}", "")}<br>• {replacements.get("{{问题归因2}}", "")}</div>
      <div class="action-item"><strong>具体动作</strong>：<br>1. {replacements.get("{{具体动作1}}", "")}<br>2. {replacements.get("{{具体动作2}}", "")}<br>3. {replacements.get("{{具体动作3}}", "")}</div>'''

    detail += '''
    </div>
  </div>'''

    detail = _remove_empty_info_rows(detail)
    return detail


def cmd_generate_multi_html(with_similar=False):
    """生成多账号对比HTML命令"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.normpath(os.path.join(script_dir, "..", "output", MULTI_REPORT_DATA_FILE))
    template_path = os.path.normpath(os.path.join(script_dir, "..", "assets", "multi_report_template.html"))

    if not os.path.exists(data_path):
        print(json.dumps({"status": "error", "message": f"多账号报告数据文件不存在: {data_path}，请先保存multi_report_data.json"}, ensure_ascii=False))
        sys.exit(1)

    if not os.path.exists(template_path):
        print(json.dumps({"status": "error", "message": f"多账号模板文件不存在: {template_path}"}, ensure_ascii=False))
        sys.exit(1)

    with open(data_path, "r", encoding="utf-8") as f:
        multi_data = json.load(f)

    with open(template_path, "r", encoding="utf-8") as f:
        html = f.read()

    accounts = multi_data.get("accounts", [])
    if not accounts:
        print(json.dumps({"status": "error", "message": "accounts数组为空，无账号数据"}, ensure_ascii=False))
        sys.exit(1)

    html = html.replace("{{账号数量}}", str(len(accounts)))

    data_time = multi_data.get("header", {}).get("数据获取时间", "")
    if not data_time and accounts:
        data_time = accounts[0].get("header", {}).get("数据获取时间", "")
    html = html.replace("{{数据获取时间}}", data_time)

    # 对比表头
    header_cells = []
    for acc in accounts:
        name = acc.get("header", {}).get("账号名", "")
        header_cells.append(f"<th>{name}</th>")
    html = html.replace("{{对比表头}}", "".join(header_cells))

    # 对比表格行
    compare_rows = []
    metrics = [
        ("综合评分", "scores", "综合评分"),
        ("平均阅读数", "data_performance", "平均阅读数"),
        ("互动率", "user_activity", "互动率"),
        ("内容健康度", "scores", "内容健康度得分"),
        "separator",
        ("用户活跃度", "scores", "用户活跃度得分"),
    ]

    best_map = {}
    for item in metrics:
        if item == "separator":
            continue
        label, section, key = item
        values = []
        for acc in accounts:
            sec = acc.get(section, {})
            raw_val = sec.get(key, "")
            try:
                v = float(raw_val) if str(raw_val).strip() not in ("",) else None
            except (ValueError, TypeError):
                v = None
            values.append(v)
        valid_vals = [v for v in values if v is not None]
        if valid_vals:
            best_map[key] = max(valid_vals)

    for item in metrics:
        if item == "separator":
            compare_rows.append('<tr style="height:4px;background:#FDE8EC;"><td colspan="99"></td></tr>')
            continue
        label, section, key = item
        cells = [f"<td>{label}</td>"]
        for acc in accounts:
            sec = acc.get(section, {})
            raw_val = sec.get(key, "")
            val_str = str(raw_val) if raw_val else ""
            if val_str.strip() == "":
                cells.append("<td>-</td>")
                continue
            try:
                num_val = float(raw_val) if str(raw_val).strip() not in ("",) else None
            except (ValueError, TypeError):
                num_val = None
            if num_val is not None and key in best_map and num_val == best_map[key]:
                cells.append(f'<td class="best">{val_str}</td>')
            else:
                cells.append(f"<td>{val_str}</td>")
        compare_rows.append("<tr>" + "".join(cells) + "</tr>")
    html = html.replace("{{对比表格行}}", "\n".join(compare_rows))

    # 对比总结
    comparison = multi_data.get("comparison", {})

    diff_items = comparison.get("核心差异", [])
    diff_html = ""
    if diff_items:
        diff_html = '<div class="summary-module summary-diff"><div class="module-title"><span class="icon">⚡</span> 核心差异</div>'
        for item in diff_items:
            if isinstance(item, dict):
                acc_name = item.get("账号名", "")
                content = item.get("内容", "")
                if content:
                    diff_html += f'<div style="margin-bottom:8px; padding:6px 10px; background:#fff; border-radius:6px;"><span style="font-weight:600; color:#D48806; font-size:12px;">{acc_name}</span><p style="font-size:13px; color:#555; line-height:1.8; margin:4px 0 0;">{content}</p></div>'
        diff_html += '</div>'
    html = html.replace("{{对比总结_核心差异}}", diff_html)

    common_items = comparison.get("共同问题", [])
    common_html = ""
    if common_items:
        common_html = '<div class="summary-module summary-common"><div class="module-title"><span class="icon">🔗</span> 共同问题</div><ul style="padding-left:18px; margin:0;">'
        for item in common_items:
            if isinstance(item, str) and item.strip():
                common_html += f'<li style="font-size:13px; color:#555; line-height:1.8;">{item}</li>'
        common_html += '</ul></div>'
    html = html.replace("{{对比总结_共同问题}}", common_html)

    advice_items = comparison.get("发展建议", [])
    advice_html = ""
    if advice_items:
        advice_html = '<div class="summary-module summary-advice"><div class="module-title"><span class="icon">🚀</span> 发展建议</div>'
        for item in advice_items:
            if isinstance(item, dict):
                acc_name = item.get("账号名", "")
                content = item.get("内容", "")
                if content:
                    advice_html += f'<div style="margin-bottom:8px; padding:6px 10px; background:#fff; border-radius:6px;"><span style="font-weight:600; color:#FF2442; font-size:12px;">{acc_name}</span><p style="font-size:13px; color:#555; line-height:1.8; margin:4px 0 0;">{content}</p></div>'
        advice_html += '</div>'
    html = html.replace("{{对比总结_发展建议}}", advice_html)

    # 各账号详情
    details = []
    for i, acc in enumerate(accounts):
        details.append(_build_account_detail_html(acc, i))
    html = html.replace("{{各账号详情}}", "\n".join(details))

    # 条件移除空数据模块
    html = _remove_conditional_sections(html, multi_data)
    html = _remove_empty_info_rows(html)

    # ========== 自检：检测未替换的模板字段 ==========
    unreplaced = re.findall(r'\{\{[^}]+\}\}', html)
    if unreplaced:
        unique_unreplaced = list(set(unreplaced))
        # 对于空值字段，根据数据类型处理
        flat_multi = _flatten_dict(multi_data)
        for field in unique_unreplaced:
            field_name = field[2:-2]  # 移除 {{ 和 }}
            # 在扁平化数据中查找对应值
            found_value = None
            for k, v in flat_multi.items():
                if k == field_name or k.endswith("." + field_name):
                    found_value = v
                    break
            # 也在各账号数据中查找
            if found_value is None or found_value == "":
                for acc in accounts:
                    flat_acc = _flatten_dict(acc)
                    for k, v in flat_acc.items():
                        if k == field_name or k.endswith("." + field_name):
                            found_value = v
                            break
                    if found_value is not None and found_value != "":
                        break
            if found_value is not None and found_value != "":
                # 数据中有值，使用该值
                html = html.replace(field, str(found_value))
            else:
                # 数据中无值，根据字段类型填充默认值
                numeric_fields = ["得分", "分", "互动", "收藏", "点赞", "数", "率", "量", "倍", "篇", "天", "中位数参考", "优秀值参考", "等级"]
                is_numeric = any(nf in field_name for nf in numeric_fields)
                if is_numeric:
                    html = html.replace(field, "0")
                else:
                    html = html.replace(field, "")
        remaining = re.findall(r'\{\{[^}]+\}\}', html)
        if remaining:
            print(json.dumps({
                "status": "error",
                "message": f"HTML模板字段未完全替换: {list(set(remaining))}",
                "unreplaced_fields": list(set(remaining))
            }, ensure_ascii=False))
            sys.exit(1)

    # 输出HTML文件
    output_dir = os.path.normpath(os.path.join(script_dir, "..", "output"))
    os.makedirs(output_dir, exist_ok=True)

    names = [acc.get("header", {}).get("账号名", "未知") for acc in accounts[:3]]
    safe_name = "vs".join(n.replace("/", "_").replace("\\", "_").replace(" ", "_") for n in names)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(output_dir, f"{safe_name}_对比报告_{timestamp}.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    result_info = {
        "status": "success",
        "message": "多账号对比HTML报告已生成",
        "output_path": output_path
    }
    print(json.dumps(result_info, ensure_ascii=False))
