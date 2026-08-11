#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTML完整性检查脚本
用于检查和修复HTML报告中的缺失内容
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime


def generate_default_action(score):
    """根据评分生成默认行动处方占位（不生成空话内容，仅标记需AI补充）"""
    try:
        score = int(score)
    except:
        score = 0
    
    # 不生成空话式默认内容（违反反空话校验规则）
    # 仅生成占位标记，提示AI需要补充具体行动处方
    return '''
          <div class="action-title">行动处方</div>
          <div class="action-step" style="color:#999;">[待补充] 请基于诊断报告数据填写具体问题归因和行动处方</div>
        '''


def check_and_fix_html_content(html, report_data):
    """检查HTML内容完整性，识别缺失字段并修复
    
    返回: (修复后的html, 缺失字段列表)
    """
    missing_fields = []
    
    # 定义关键字段及其默认值
    critical_fields = {
        # 头部信息
        "账号名": report_data.get("header", {}).get("账号名", "未知账号"),
        "账号标识": report_data.get("header", {}).get("账号标识", "素人"),
        "数据获取时间": report_data.get("header", {}).get("数据获取时间", datetime.now().strftime("%Y-%m-%d %H:%M")),
        "综合评分": report_data.get("scores", {}).get("综合评分", "0"),
        
        # 评分字段
        "账号定位得分": report_data.get("scores", {}).get("账号定位得分", "0"),
        "粉丝画像与需求得分": report_data.get("scores", {}).get("粉丝画像与需求得分", "0"),
        "选题体系得分": report_data.get("scores", {}).get("选题体系得分", "0"),
        "封面风格得分": report_data.get("scores", {}).get("封面风格得分", "0"),
        "爆文能力得分": report_data.get("scores", {}).get("爆文能力得分", "0"),
        "互动规模得分": report_data.get("scores", {}).get("互动规模得分", "0"),
        "更新产能得分": report_data.get("scores", {}).get("更新产能得分", "0"),
        
        # 简述原因
        "账号定位简述得分和扣分原因": report_data.get("scores", {}).get("账号定位简述得分和扣分原因", "账号定位清晰"),
        "粉丝画像与需求简述得分和扣分原因": report_data.get("scores", {}).get("粉丝画像与需求简述得分和扣分原因", "粉丝画像较清晰"),
        "选题体系简述得分和扣分原因": report_data.get("scores", {}).get("选题体系简述得分和扣分原因", "选题方向明确"),
        "封面风格简述得分和扣分原因": report_data.get("scores", {}).get("封面风格简述得分和扣分原因", "封面风格统一"),
        "爆文能力简述得分和扣分原因": report_data.get("scores", {}).get("爆文能力简述得分和扣分原因", "爆文表现良好"),
        "互动规模简述得分和扣分原因": report_data.get("scores", {}).get("互动规模简述得分和扣分原因", "互动表现良好"),
        "更新产能简述得分和扣分原因": report_data.get("scores", {}).get("更新产能简述得分和扣分原因", "更新频率稳定"),
    }
    
    # 检查HTML中的关键模块是否有内容
    # 1. 检查更新时间
    update_time_match = re.search(r'数据获取时间[：:]\s*</span>\s*<span class="value">([^<]*)</span>', html)
    if update_time_match:
        value = update_time_match.group(1).strip()
        if not value or value == "":
            missing_fields.append("数据获取时间")
            fix_value = report_data.get("header", {}).get("数据获取时间", datetime.now().strftime("%Y-%m-%d %H:%M"))
            html = html.replace(
                f'<span class="value">{value}</span>',
                f'<span class="value">{fix_value}</span>',
                1
            )
    
    # 2. 检查行动处方模块
    action_section_match = re.search(r'<div class="action-box">(.*?)</div>\s*</div>', html, re.DOTALL)
    if action_section_match:
        action_content = action_section_match.group(1)
        if "问题归因" in action_content and ("暂无" in action_content or action_content.count("<div") < 3):
            missing_fields.append("行动处方")
            score = report_data.get("scores", {}).get("综合评分", 0)
            default_action = generate_default_action(score)
            html = re.sub(
                r'(<div class="action-box">).*?(</div>\s*</div>)',
                r'\1' + default_action + r'\2',
                html,
                flags=re.DOTALL
            )
    
    # 3. 检查综合诊断结论
    conclusion_match = re.search(r'综合诊断结论.*?<div class="conclusion-text">(.*?)</div>', html, re.DOTALL)
    if conclusion_match:
        conclusion_content = conclusion_match.group(1).strip()
        if not conclusion_content or len(conclusion_content) < 20:
            missing_fields.append("综合诊断结论")
            account_name = report_data.get("header", {}).get("账号名", "该账号")
            default_conclusion = f"{account_name}整体运营状况良好，建议持续优化内容质量和互动策略。"
            html = re.sub(
                r'(<div class="conclusion-text">).*?(</div>)',
                rf'\1{default_conclusion}\2',
                html,
                flags=re.DOTALL
            )
    
    # 4. 检查账号定位模块关键字段
    positioning_fields = ["TA是谁", "心智占位", "价值观锚点", "吸引力类型"]
    for pf in positioning_fields:
        pattern = rf'{pf}[：:]\s*</span>\s*<span class="value">([^<]*)</span>'
        match = re.search(pattern, html)
        if match:
            value = match.group(1).strip()
            if not value:
                missing_fields.append(pf)
    
    # 5. 检查粉丝画像模块
    fans_profile_match = re.search(r'粉丝构成[：:]\s*</span>\s*<span class="value">([^<]*)</span>', html)
    if fans_profile_match:
        value = fans_profile_match.group(1).strip()
        if not value:
            missing_fields.append("粉丝构成")
            raw = report_data.get("_raw", {})
            fans = raw.get("fans", 0)
            gender = raw.get("fansGender", {})
            female_ratio = gender.get("female_ratio", "0.5")
            try:
                fix_value = f"{fans}粉丝 | 女性{float(female_ratio)*100:.0f}%"
            except:
                fix_value = f"{fans}粉丝"
            html = html.replace(
                f'<span class="value">{value}</span>',
                f'<span class="value">{fix_value}</span>',
                1
            )
    
    # 6. 检查选题体系模块
    topic_fields = ["选题方向", "表达风格", "叙事手法"]
    for tf in topic_fields:
        pattern = rf'{tf}[：:]\s*</span>\s*<span class="value">([^<]*)</span>'
        match = re.search(pattern, html)
        if match:
            value = match.group(1).strip()
            if not value:
                missing_fields.append(tf)
    
    # 7. 检查封面风格模块
    cover_fields = ["视觉特征", "信息层级", "一致性"]
    for cf in cover_fields:
        pattern = rf'{cf}[：:]\s*</span>\s*<span class="value">([^<]*)</span>'
        match = re.search(pattern, html)
        if match:
            value = match.group(1).strip()
            if not value:
                missing_fields.append(cf)
    
    # 8. 检查更新产能模块
    update_fields = ["频率分析", "发布时间分析"]
    for uf in update_fields:
        pattern = rf'{uf}[：:]\s*</span>\s*<span class="value">([^<]*)</span>'
        match = re.search(pattern, html)
        if match:
            value = match.group(1).strip()
            if not value:
                missing_fields.append(uf)
    
    return html, missing_fields


def check_multi_html_content(html, accounts):
    """检查多账号HTML内容完整性
    
    返回: (修复后的html, 缺失字段列表)
    """
    missing_fields = []
    
    # 检查每个账号的关键信息
    for i, acc in enumerate(accounts):
        header = acc.get("header", {})
        scores = acc.get("scores", {})
        
        name = header.get("账号名", "")
        if not name:
            missing_fields.append(f"账号{i+1}-账号名")
        
        total_score = scores.get("综合评分", "")
        if not total_score:
            missing_fields.append(f"账号{i+1}-综合评分")
    
    # 检查对比总结是否存在
    if "核心差异" not in html or len(re.findall(r"核心差异", html)) == 0:
        missing_fields.append("核心差异")
        default_summary = '''
<div class="comparison-summary">
  <div class="section-title">核心差异</div>
  <p>各账号在定位、内容策略上存在差异，建议针对性优化。</p>
</div>
'''
        html = html.replace('</body>', default_summary + '</body>')
    
    return html, missing_fields


def cmd_check():
    """命令行入口：检查HTML文件"""
    parser = argparse.ArgumentParser(description="HTML完整性检查")
    parser.add_argument("--html", required=True, help="HTML文件路径")
    parser.add_argument("--data", required=True, help="report_data.json路径")
    parser.add_argument("--type", choices=["single", "multi"], default="single", help="报告类型")
    args = parser.parse_args()
    
    # 读取HTML
    if not os.path.exists(args.html):
        print(json.dumps({"status": "error", "message": f"HTML文件不存在: {args.html}"}, ensure_ascii=False))
        sys.exit(1)
    
    with open(args.html, "r", encoding="utf-8") as f:
        html = f.read()
    
    # 读取数据
    if not os.path.exists(args.data):
        print(json.dumps({"status": "error", "message": f"数据文件不存在: {args.data}"}, ensure_ascii=False))
        sys.exit(1)
    
    with open(args.data, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # 执行检查
    if args.type == "single":
        html, missing_fields = check_and_fix_html_content(html, data)
    else:
        accounts = data.get("accounts", [data])
        html, missing_fields = check_multi_html_content(html, accounts)
    
    # 写回HTML
    with open(args.html, "w", encoding="utf-8") as f:
        f.write(html)
    
    result = {
        "status": "success",
        "message": "HTML完整性检查完成",
        "missing_fields": missing_fields,
        "fixed": len(missing_fields) > 0
    }
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    cmd_check()
