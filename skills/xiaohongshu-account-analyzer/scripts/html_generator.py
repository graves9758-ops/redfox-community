"""
HTML报告生成模块
负责单账号和多账号HTML报告的生成逻辑
"""
import os
import re
import json
from datetime import datetime

# 评分满分映射
SCORE_MAX_MAP = {
    "账号定位": 10,
    "粉丝画像与需求": 15,
    "选题体系": 10,
    "封面风格": 10,
    "爆文能力": 20,
    "互动规模": 20,
    "更新产能": 15,
     
}

# 报告数据文件名
REPORT_DATA_FILE = "report_data.json"
MULTI_REPORT_DATA_FILE = "multi_report_data.json"


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


def _format_interactive_count(count):
    """格式化互动数（万级显示，与xiaohongshu_analyzer.py保持一致使用w+格式）"""
    try:
        num = int(count)
        if num >= 10000:
            w_val = num / 10000
            if w_val == int(w_val):
                return f"{int(w_val)}w+"
            return f"{round(w_val, 1)}w+"
        return str(num)
    except (ValueError, TypeError):
        return str(count)


def _build_replacements(report_data):
    """从report_data构建替换字典，支持嵌套结构和数组索引
    
    生成的占位符格式：
    1. 完整路径：{{header.账号名}}、{{scores.账号定位得分}}
    2. 关键短路径：{{生命周期.当前阶段}}、{{核心需求反推[0].画像特征}}、{{30天目标.粉丝数.当前}}
    3. 最短路径（最后一层）：{{账号名}}、{{当前阶段}}
    三种格式都支持，确保HTML模板中任何写法都能匹配
    """
    numeric_fields = {
        "单篇互动均值", "收藏率", "爆文率", "近7天发作品数", "爆文数", "周更频率",
        "综合评分", "账号定位得分", "互动规模得分", "爆文能力得分",
        "更新产能得分", "粉丝画像与需求得分", "选题体系得分", "封面风格得分"
    }
    
    # 扁平化整个数据结构
    flat_data = _flatten_dict(report_data)
    
    replacements = {}
    for k, v in flat_data.items():
        # 空值处理：将 none/null/None/空字符串 替换为 0 或空字符串
        str_v = str(v).strip().lower() if v is not None else ""
        is_empty = str_v in ("none", "null", "")
        if is_empty:
            v = "0" if k in numeric_fields else ""
        else:
            v = str(v).strip()
        
        str_v = str(v)
        # 完整路径占位符：{{header.账号名}}
        replacements["{{" + k + "}}"] = str_v
        
        # 处理短路径 - 只有非空值才生成短路径替换
        if "." in k and not is_empty:
            parts = k.split(".")
            # 跳过_raw字典下的字段，避免覆盖其他模块的同名字段
            if parts[0] == "_raw":
                continue
            # 最短路径（最后一层）：{{账号名}}、{{当前阶段}}
            replacements["{{" + parts[-1] + "}}"] = str_v
            
            # 关键短路径：保留最后两层（如 生命周期.当前阶段）
            # 对于三层及以上结构，生成最后两层的短路径
            if len(parts) >= 2:
                # 生成最后两层的短路径，但要处理数组索引
                # 例如：conclusion.生命周期.当前阶段 -> 生命周期.当前阶段
                # 例如：fans_insight.核心需求反推[0].画像特征 -> 核心需求反推[0].画像特征
                # 例如：action.30天目标.粉丝数.当前 -> 30天目标.粉丝数.当前
                key_short = ".".join(parts[-2:])
                replacements["{{" + key_short + "}}"] = str_v
                
            # 对于四层结构，生成最后三层的短路径
            # 例如：action.30天目标.粉丝数.当前 -> 30天目标.粉丝数.当前（已由上面处理）
            if len(parts) >= 3:
                key_short_3 = ".".join(parts[-3:])
                replacements["{{" + key_short_3 + "}}"] = str_v
    
    # 评分百分比
    for dim, max_score in SCORE_MAX_MAP.items():
        score_key = dim + "得分"
        pct_key = dim + "得分_pct"
        score_val = replacements.get("{{" + score_key + "}}", "0")
        try:
            pct = round(int(score_val) / max_score * 100)
        except (ValueError, ZeroDivisionError):
            pct = 0
        replacements["{{" + pct_key + "}}"] = str(pct)

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
        url = w.get("url", "") or ""
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
    # 直接移除标记，始终显示爆文能力模块
    html = html.replace("<!-- SECTION_VIRAL_START -->", "").replace("<!-- SECTION_VIRAL_END -->", "")

    # 近期作品：works为空时隐藏
    works = report_data.get("works", [])
    has_valid_works = any(isinstance(w, dict) and w.get("title", "").strip() for w in works)
    html = _remove_section_markers(html, "SECTION_WORKS", has_valid_works)

    # 可强化：账号定位>=8分时隐藏（优先使用显示可强化字段，否则根据得分判断）
    positioning = report_data.get("positioning", {})
    show_can_enhance = positioning.get("显示可强化", None)
    if show_can_enhance is None:
        # 如果没有显示可强化字段，则根据账号定位得分判断
        scores = report_data.get("scores", {})
        positioning_score = scores.get("账号定位得分", 0)
        show_can_enhance = positioning_score < 8
    html = _remove_section_markers(html, "SECTION_CAN_ENHANCE", show_can_enhance)

    return html


def _build_similar_accounts_cards(report_data):
    """构建相似账号卡片HTML"""
    similar_cards = []
    for sa in report_data.get("similar_accounts", []):
        if not isinstance(sa, dict):
            continue
        name = sa.get("账号名称") or sa.get("accountName") or sa.get("nickname") or sa.get("name", "")
        account_url = sa.get("账号链接") or sa.get("profileUrl") or sa.get("url", "")
        fans_count = sa.get("粉丝数") or sa.get("followerCount") or sa.get("fans") or sa.get("fansCount", 0)
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
                account_url = f"https://www.xiaohongshu.com/user/profile/{account_id}"
                name_html = f'<a href="{account_url}" target="_blank" style="color:#1890ff;text-decoration:none;font-weight:500;">{name}</a>'
        
        similar_cards.append(
            f'<div class="similar-card-row" style="padding:12px 0;border-bottom:1px solid #f0f0f0;">'
            f'<div style="margin-bottom:6px;"><strong>{name_html}</strong> | 粉丝：{fans_count} | 总互动：{total_interactive}</div>'
            f'<div style="font-size:13px;color:#666;margin-bottom:4px;"><strong>推荐理由：</strong>{recommend_reason}</div>'
            f'<div style="font-size:13px;color:#666;margin-bottom:4px;"><strong>发文特点：</strong>{post_feature}</div>'
            f'<div style="font-size:13px;color:#666;"><strong>可学之处：</strong>{learn_point}</div>'
            f'</div>'
        )
    return "\n".join(similar_cards)


def _fill_unreplaced_fields(html, report_data, raw_data=None):
    """检测并填充未替换的模板字段"""
    unreplaced = re.findall(r'\{\{[^}]+\}\}', html)
    if not unreplaced:
        return html, []
    
    unique_unreplaced = list(set(unreplaced))
    # 扁平化分析数据和原始数据
    flat_data = _flatten_dict(report_data)
    flat_raw = _flatten_dict(raw_data) if raw_data else {}

    # 字段名映射：模板字段名 -> 原始数据字段名
    field_mapping = {
        "总收藏数": "collected",
        "总点赞数": "liked",
        "粉丝数": "fans",
        "近30天互动量": "interactions_30d",
        "近30天发作品数": "works_30d",
        "作品总数": "works_total",
        "账号名": "nickname",
        "官方等级": "level",
        "账号标识": "userAttribute",
        "数据获取时间": "queryTime",
    }
    
    filled_fields = []
    for field in unique_unreplaced:
        field_name = field[2:-2]  # 移除 {{ 和 }}
        found_value = None

        # 第一步：从分析数据中查找（包括空值）
        for k, v in flat_data.items():
            if k == field_name or k.endswith("." + field_name):
                # 接受任何非None的值，包括空字符串
                if v is not None:
                    found_value = v
                    break

        # 第二步：分析数据为空或不存在，从原始数据中查找
        if (found_value is None or str(found_value).strip() == "") and flat_raw:
            # 先尝试字段名映射
            if field_name in field_mapping:
                raw_field = field_mapping[field_name]
                for k, v in flat_raw.items():
                    if k == raw_field or k.endswith("." + raw_field):
                        if v is not None and str(v).strip() != "":
                            found_value = v
                            # 格式化大数字
                            if field_name in ["总收藏数", "总点赞数", "粉丝数", "近30天互动量"]:
                                found_value = _format_interactive_count(v)
                            break
            # 再尝试直接匹配字段名
            if found_value is None or str(found_value).strip() == "":
                for k, v in flat_raw.items():
                    if k == field_name or k.endswith("." + field_name):
                        if v is not None and str(v).strip() != "":
                            found_value = v
                            break

        # 第三步：根据值进行处理
        if found_value is not None and str(found_value).strip() != "":
            html = html.replace(field, str(found_value))
            filled_fields.append(field_name)
        else:
            # 数据中无值，根据字段类型填充默认值
            # 精确匹配数字字段，避免误判
            numeric_exact = ["得分", "分", "粉丝数", "互动量", "收藏数", "点赞数", "爆文数", "篇", "率", "倍数", "中位数参考", "优秀值参考", "等级", "占比"]
            is_numeric = any(field_name.endswith(nf) or field_name == nf for nf in numeric_exact)
            # 特殊处理：时间、日期等字段不是数字
            time_fields = ["时间", "日期", "日期"]
            is_time = any(tf in field_name for tf in time_fields)
            
            if is_numeric and not is_time:
                html = html.replace(field, "0")
            else:
                html = html.replace(field, "-")

    return html, filled_fields


def generate_single_report_html(report_data, template_path, raw_data=None):
    """生成单账号HTML报告
    
    Args:
        report_data: 分析数据字典
        template_path: HTML模板路径
        raw_data: 原始数据字典（可选，用于填充缺失字段）
    
    Returns:
        tuple: (html_content, error_message)
    """
    if not os.path.exists(template_path):
        return None, f"模板文件不存在: {template_path}"
    
    # 评分保护：如果report_data中评分为空，从raw_data回填
    if raw_data and isinstance(raw_data.get("scores"), dict):
        if not isinstance(report_data.get("scores"), dict):
            report_data["scores"] = {}
        for k, v in raw_data["scores"].items():
            cur = report_data["scores"].get(k)
            if cur in (None, "", 0, "0", "0.0") and v not in (None, "", 0, "0", "0.0"):
                report_data["scores"][k] = v
    
    with open(template_path, "r", encoding="utf-8") as f:
        html = f.read()
    
    replacements = _build_replacements(report_data)
    
    # 相似账号卡片
    replacements["{{similar_accounts_cards}}"] = _build_similar_accounts_cards(report_data)

    # 执行替换
    for key, val in replacements.items():
        html = html.replace(key, val)

    # 条件移除空数据模块
    html = _remove_conditional_sections(html, report_data)

    # 相似账号区域 - 直接展示（移除条件注释）
    html = html.replace("<!-- SIMILAR_START -->", "").replace("<!-- SIMILAR_END -->", "")

    html = _remove_empty_info_rows(html)

    # 填充未替换的字段
    html, filled_fields = _fill_unreplaced_fields(html, report_data, raw_data)
    
    # 最终检查
    remaining = re.findall(r'\{\{[^}]+\}\}', html)
    if remaining:
        return None, f"HTML模板字段未完全替换: {list(set(remaining))}"
    
    return html, None


def generate_multi_report_html(multi_data, template_path):
    """生成多账号对比HTML报告
    
    Args:
        multi_data: 多账号数据字典
        template_path: HTML模板路径
    
    Returns:
        tuple: (html_content, error_message)
    """
    if not os.path.exists(template_path):
        return None, f"多账号模板文件不存在: {template_path}"
    
    with open(template_path, "r", encoding="utf-8") as f:
        html = f.read()

    accounts = multi_data.get("accounts", [])
    if not accounts:
        return None, "accounts数组为空，无账号数据"

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
        ("近30天互动量", "interactive_scale", "近30天互动量"),
        ("周更频率", "update_rhythm", "周更频率"),
        ("爆文率", "viral", "爆文率"),
        ("账号定位", "scores", "账号定位得分"),
        "separator",
        ("互动规模", "scores", "互动规模得分"),
        ("爆文能力", "scores", "爆文能力得分"),
        ("更新产能", "scores", "更新产能得分"),
        ("粉丝画像", "scores", "粉丝画像与需求得分"),
        ("选题体系", "scores", "选题体系得分"),
        ("封面风格", "scores", "封面风格得分"),
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

    # 填充未替换的字段（多账号版本）
    html, _ = _fill_multi_unreplaced_fields(html, multi_data, accounts)
    
    # 最终检查
    remaining = re.findall(r'\{\{[^}]+\}\}', html)
    if remaining:
        return None, f"HTML模板字段未完全替换: {list(set(remaining))}"
    
    return html, None


def _fill_multi_unreplaced_fields(html, multi_data, accounts):
    """填充多账号报告中未替换的字段"""
    unreplaced = re.findall(r'\{\{[^}]+\}\}', html)
    if not unreplaced:
        return html, []
    
    unique_unreplaced = list(set(unreplaced))
    flat_multi = _flatten_dict(multi_data)
    filled_fields = []
    
    for field in unique_unreplaced:
        field_name = field[2:-2]  # 移除 {{ 和 }}
        found_value = None
        
        # 在扁平化数据中查找对应值
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
            html = html.replace(field, str(found_value))
            filled_fields.append(field_name)
        else:
            numeric_fields = ["得分", "分", "粉丝", "互动", "收藏", "点赞", "数", "率", "量", "倍", "篇", "天", "中位数参考", "优秀值参考", "等级"]
            is_numeric = any(nf in field_name for nf in numeric_fields)
            if is_numeric:
                html = html.replace(field, "0")
            else:
                html = html.replace(field, "")
    
    return html, filled_fields


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
        <div class="score-bar-item"><span class="name">账号定位</span><div class="bar-bg"><div class="bar-fill" style="width:{replacements.get("{{账号定位得分_pct}}", "0")}%"></div></div><span class="val">{replacements.get("{{账号定位得分}}", "0")}分</span></div>
        <div class="score-bar-item"><span class="name">粉丝画像</span><div class="bar-bg"><div class="bar-fill" style="width:{replacements.get("{{粉丝画像与需求得分_pct}}", "0")}%"></div></div><span class="val">{replacements.get("{{粉丝画像与需求得分}}", "0")}分</span></div>
        <div class="score-bar-item"><span class="name">选题体系</span><div class="bar-bg"><div class="bar-fill" style="width:{replacements.get("{{选题体系得分_pct}}", "0")}%"></div></div><span class="val">{replacements.get("{{选题体系得分}}", "0")}分</span></div>
        <div class="score-bar-item"><span class="name">封面风格</span><div class="bar-bg"><div class="bar-fill" style="width:{replacements.get("{{封面风格得分_pct}}", "0")}%"></div></div><span class="val">{replacements.get("{{封面风格得分}}", "0")}分</span></div>
        <div class="score-bar-item"><span class="name">爆文能力</span><div class="bar-bg"><div class="bar-fill" style="width:{replacements.get("{{爆文能力得分_pct}}", "0")}%"></div></div><span class="val">{replacements.get("{{爆文能力得分}}", "0")}分</span></div>
        <div class="score-bar-item"><span class="name">互动规模</span><div class="bar-bg"><div class="bar-fill" style="width:{replacements.get("{{互动规模得分_pct}}", "0")}%"></div></div><span class="val">{replacements.get("{{互动规模得分}}", "0")}分</span></div>
        <div class="score-bar-item"><span class="name">更新产能</span><div class="bar-bg"><div class="bar-fill" style="width:{replacements.get("{{更新产能得分_pct}}", "0")}%"></div></div><span class="val">{replacements.get("{{更新产能得分}}", "0")}分</span></div>
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
