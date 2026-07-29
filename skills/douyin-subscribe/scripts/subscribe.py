#!/usr/bin/env python3
"""
抖音账号订阅追踪 — 订阅抖音账号，每日自动推送最新作品
========================================================
订阅关注的抖音账号，自动抓取最新作品数据，表格化展示。

Usage:
    python3 subscribe.py add "5437662" --name "李佳琦" --category "竞对账号"
    python3 subscribe.py add "5437662,13232311,3234242"
    python3 subscribe.py remove "5437662"
    python3 subscribe.py list
    python3 subscribe.py fetch
    python3 subscribe.py fetch --date 2026-06-01
"""

import argparse
import json
import os
import re
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# ─── 配置 ─────────────────────────────────────────────────────────────────────────
API_URL = "https://redfox.hk/story/api/dy/data/listWorkByAccount"
ENV_KEY = "REDFOX_API_KEY"

SUBSCRIPTIONS_FILE = Path.home() / ".qoder" / "douyin_subscriptions.json"
MAX_SUBSCRIPTIONS = 20

# 失败计数文件（规则3：同一参数 6h 内 3 次失败后拒绝调用）
FAILURES_FILE = Path.home() / ".qoder" / "douyin_subscribe_failures.json"
SUPPORT_EMAIL = "redfoxdata@proton.me"
RATE_LIMIT_MAX_FAILURES = 3
RATE_LIMIT_WINDOW_HOURS = 6

DEFAULT_CATEGORIES = ["竞对账号", "同类账号", "关注账号"]

# ─── 终端颜色 ──────────────────────────────────────────────────────────────────────
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


def info(msg):
    print(f"{GREEN}[✓]{RESET} {msg}")


def warn(msg):
    print(f"{YELLOW}[!]{RESET} {msg}")


def error(msg):
    print(f"{RED}[✗]{RESET} {msg}")


def step(msg):
    print(f"{CYAN}[→]{RESET} {msg}")


# ─── API Key 管理 ──────────────────────────────────────────────────────────────────
def get_api_key(cli_key=None):
    """Get API key: CLI arg > env var. 必须配置，否则报错退出。"""
    if cli_key:
        return cli_key
    env_key = os.environ.get(ENV_KEY)
    if env_key:
        return env_key
    error("未找到 REDFOX_API_KEY，请先配置 API Key：")
    print(f"  {CYAN}方案1（推荐）：{RESET}export REDFOX_API_KEY=ak_你的密钥")
    print(f"  {CYAN}方案2：{RESET}命令行参数 --api-key ak_你的密钥")
    print(f"  {CYAN}获取地址：{RESET}https://redfox.hk/settings/api-keys?source=github")
    sys.exit(1)


# ─── 订阅数据管理 ──────────────────────────────────────────────────────────────────
def load_subscriptions():
    """加载订阅列表"""
    if not SUBSCRIPTIONS_FILE.exists():
        return []
    try:
        data = json.loads(SUBSCRIPTIONS_FILE.read_text(encoding="utf-8"))
        return data.get("subscriptions", [])
    except (json.JSONDecodeError, OSError):
        return []


def save_subscriptions(subscriptions):
    """保存订阅列表"""
    SUBSCRIPTIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    data = {"subscriptions": subscriptions, "updatedAt": datetime.now().isoformat()}
    SUBSCRIPTIONS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def find_subscription(identifier):
    """查找某个订阅 — 按 accountId 查找"""
    subs = load_subscriptions()
    for sub in subs:
        if sub["accountId"] == identifier:
            return sub
    return None


def add_subscriptions(account_ids, account_name="", category="关注账号"):
    """添加订阅 — 支持逗号分隔的多个抖音号，拆分后逐个添加"""
    ids = [aid.strip() for aid in account_ids.split(",") if aid.strip()]
    if not ids:
        error("请提供至少一个有效的抖音号")
        return False

    subs = load_subscriptions()
    added_count = 0

    for aid in ids:
        if len(subs) >= MAX_SUBSCRIPTIONS:
            error(f"已达订阅上限（{MAX_SUBSCRIPTIONS} 个），请先取消一些订阅后再添加")
            break

        existing = find_subscription(aid)
        if existing:
            warn(f"已订阅过抖音号「{aid}」（{existing.get('accountName', '')}），跳过")
            continue

        subs.append({
            "accountId": aid,
            "accountName": account_name or aid,
            "category": category,
            "subscribedAt": datetime.now().isoformat(),
        })
        added_count += 1
        info(f"已订阅抖音号「{aid}」{f'— {account_name}' if account_name else ''} — 分类: {category}")

    if added_count > 0:
        save_subscriptions(subs)
        info(f"本次新增 {added_count} 个订阅，当前共 {len(subs)}/{MAX_SUBSCRIPTIONS} 个")
    else:
        warn("本次未新增任何订阅")

    return added_count > 0


def remove_subscription(identifier):
    """移除订阅 — 按 accountId 移除"""
    subs = load_subscriptions()
    target = None
    for i, sub in enumerate(subs):
        if sub["accountId"] == identifier:
            target = subs.pop(i)
            break

    if not target:
        warn(f"未找到抖音号「{identifier}」的订阅")
        return False

    save_subscriptions(subs)
    name = target.get("accountName", "")
    name_info = f"（{name}）" if name and name != identifier else ""
    info(f"已取消订阅「{identifier}」{name_info}")
    info(f"当前共订阅 {len(subs)}/{MAX_SUBSCRIPTIONS} 个抖音账号")
    return True


def list_subscriptions():
    """列出所有订阅"""
    subs = load_subscriptions()
    if not subs:
        warn("当前没有订阅任何抖音账号")
        print(f"\n  使用 '{CYAN}add{RESET}' 命令添加订阅:")
        print(f"  python3 subscribe.py add \"<抖音号>\" --name \"<账号名>\"")
        print(f"  python3 subscribe.py add \"<抖音号1>,<抖音号2>\"  # 支持多个")
        return

    groups = defaultdict(list)
    for sub in subs:
        groups[sub.get("category", "关注账号")].append(sub)

    print(f"\n{BOLD}当前订阅 ({len(subs)}/{MAX_SUBSCRIPTIONS}):{RESET}\n")

    for cat in DEFAULT_CATEGORIES + ["其他"]:
        items = groups.pop(cat, [])
        if not items:
            if cat in DEFAULT_CATEGORIES:
                groups.pop(cat, None)
            continue

        cat_color = {"竞对账号": RED, "同类账号": YELLOW, "关注账号": CYAN}.get(cat, CYAN)
        print(f"  {cat_color}{BOLD}▸ {cat}{RESET}")
        for item in items:
            subscribed_at = item.get("subscribedAt", "")[:10] if item.get("subscribedAt") else ""
            display_line = f"    {item['accountName']}  (抖音号: {item['accountId']})"
            if subscribed_at:
                display_line += f"  订阅于 {subscribed_at}"
            print(display_line)

    for cat, items in groups.items():
        if not items:
            continue
        print(f"  {CYAN}▸ {cat}{RESET}")
        for item in items:
            print(f"    {item['accountName']}  (抖音号: {item['accountId']})")

    print()


# ─── 数据获取 ──────────────────────────────────────────────────────────────────────
# ─── 失败计数 / 频率限制（规则 3）───────────────────────────────────────────────
def _load_failures():
    """加载失败记录"""
    if FAILURES_FILE.exists():
        try:
            return json.loads(FAILURES_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def _save_failures(failures):
    """保存失败记录"""
    FAILURES_FILE.parent.mkdir(parents=True, exist_ok=True)
    FAILURES_FILE.write_text(json.dumps(failures, ensure_ascii=False, indent=2), encoding="utf-8")


def _check_rate_limit(account_id):
    """检查是否超过失败阈值（6h 内 3 次失败），返回 (blocked: bool, message: str)"""
    failures = _load_failures()
    key = account_id.strip().lower()
    record = failures.get(key)
    if not record:
        return False, ""

    last_fail_time = record.get("lastFailTime", 0)
    fail_count = record.get("count", 0)

    # 距上次失败超过 6 小时，计数归零
    if time.time() - last_fail_time > RATE_LIMIT_WINDOW_HOURS * 3600:
        del failures[key]
        _save_failures(failures)
        return False, ""

    # 6h 内失败 >= 3 次，拒绝调用
    if fail_count >= RATE_LIMIT_MAX_FAILURES:
        return True, f"当前账号「{account_id}」订阅已超过失败阈值，请联系客服邮箱 {SUPPORT_EMAIL} 处理"

    return False, ""


def _record_failure(account_id):
    """记录一次失败"""
    failures = _load_failures()
    key = account_id.strip().lower()
    record = failures.get(key, {"count": 0, "lastFailTime": 0})

    # 距上次失败超过 6 小时，重置计数
    if time.time() - record.get("lastFailTime", 0) > RATE_LIMIT_WINDOW_HOURS * 3600:
        record = {"count": 0, "lastFailTime": 0}

    record["count"] += 1
    record["lastFailTime"] = time.time()
    failures[key] = record
    _save_failures(failures)


def _record_success(account_id):
    """成功后计数归零"""
    failures = _load_failures()
    key = account_id.strip().lower()
    if key in failures:
        del failures[key]
        _save_failures(failures)


def _filter_works_by_date(works, date_str=None, date_start=None, date_end=None):
    """客户端按发布时间过滤作品（新 API 不支持服务端日期过滤）"""
    if not date_str and not (date_start and date_end):
        return works

    filtered = []
    for w in works:
        pub = w.get("publishTime") or ""
        if not pub:
            continue
        pub_date = pub[:10]  # YYYY-MM-DD
        if date_start and date_end:
            if date_start <= pub_date <= date_end:
                filtered.append(w)
        elif date_str:
            if pub_date == date_str:
                filtered.append(w)
    return filtered


def _map_work_fields(work):
    """将新 API 字段映射为脚本内部统一字段名，保持下游逻辑不变"""
    work["title"] = work.get("content") or work.get("title") or ""
    work["workUrl"] = work.get("opusUrl") or work.get("workUrl") or ""
    work["accountName"] = work.get("authorName") or work.get("accountName") or ""
    work["secUid"] = work.get("authorSecUid") or work.get("secUid") or ""
    work["followerCount"] = work.get("authorFansCount") or work.get("followerCount")
    return work


def fetch_account_works(session, account_id, date_str=None, date_start=None, date_end=None):
    """获取单个抖音账号的作品列表 — 通过广域库 API（listWorkByAccount）"""
    if not account_id:
        warn("无效的抖音号: 空")
        return []

    # 规则3：检查频率限制
    blocked, block_msg = _check_rate_limit(account_id)
    if blocked:
        warn(block_msg)
        return "__rate_limited__"

    payload = {
        "uniqueName": account_id,
        "userId": "",
        "shortId": "",
        "pageNum": 1,
        "pageSize": 10,
    }

    try:
        resp = session.post(API_URL, json=payload, timeout=20)
        result = resp.json()
    except requests.exceptions.Timeout:
        warn(f"请求超时: 抖音号 {account_id}")
        _record_failure(account_id)
        return []
    except Exception as e:
        warn(f"请求失败: 抖音号 {account_id}: {e}")
        _record_failure(account_id)
        return []

    code = result.get("code")
    if code == 3108:
        warn("触发频率限制，等待 5s...")
        time.sleep(5)
        try:
            resp = session.post(API_URL, json=payload, timeout=20)
            result = resp.json()
            code = result.get("code")
        except Exception:
            _record_failure(account_id)
            return []

    if code not in (200, 2000):
        if code in (3106, 3107):
            error(f"API Key 错误 (code {code}): {result.get('msg', '')}")
        elif code:
            warn(f"API 返回错误 (code {code}): {result.get('msg', '')} — 抖音号 {account_id}")
        _record_failure(account_id)
        return []

    # 规则3：查询成功，计数归零
    _record_success(account_id)

    data_raw = result.get("data", {})
    if not data_raw:
        return []

    if isinstance(data_raw, list):
        works = data_raw
    elif isinstance(data_raw, dict):
        works = data_raw.get("list") or data_raw.get("articles") or data_raw.get("records") or []
    else:
        works = []

    # 映射新 API 字段为统一字段名
    for work in works:
        _map_work_fields(work)

    # 客户端日期过滤（新 API 不支持服务端日期过滤）
    if date_str or (date_start and date_end):
        works = _filter_works_by_date(works, date_str, date_start, date_end)

    for work in works[:10]:
        work["_accountId"] = account_id

    return works[:10]


def fetch_all_works(session, subscriptions, date_str=None, date_start=None, date_end=None):
    """拉取所有订阅账号的作品 — 返回 (works, empty_accounts, rate_limited_accounts)"""
    all_works = []
    empty_accounts = []
    rate_limited_accounts = []
    total = len(subscriptions)

    for i, sub in enumerate(subscriptions, 1):
        aid = sub.get("accountId", "")
        name = sub.get("accountName", aid)
        if not aid:
            warn(f"跳过无抖音号的订阅: {name}")
            continue

        print(f"\r  {CYAN}[→]{RESET} 拉取: {name} ({aid}) ({i}/{total})", end="", flush=True)

        works = fetch_account_works(session, aid, date_str, date_start, date_end)
        if works == "__rate_limited__":
            # 规则3：被频率限制拒绝
            rate_limited_accounts.append(name)
        elif works:
            # 优先使用 API 返回的真实 accountName（而非传入的 ID）
            real_name = works[0].get("accountName") or name
            for work in works:
                work["_accountName"] = real_name
                work["_category"] = sub.get("category", "关注账号")
            all_works.extend(works)
        else:
            empty_accounts.append(name)

        if i < total:
            time.sleep(0.3)

    print()
    return all_works, empty_accounts, rate_limited_accounts


# ─── 数字格式化 ────────────────────────────────────────────────────────────────────
def format_number(n):
    """格式化数字: 1234 -> 1.2k, 12345 -> 1.2w"""
    if n is None:
        return "0"
    try:
        n = int(n)
    except (ValueError, TypeError):
        return str(n)
    if n >= 10000:
        return f"{n / 10000:.1f}w"
    if n >= 1000:
        return f"{n / 1000:.1f}k"
    return str(n)


def format_fans(n):
    """格式化粉丝数"""
    if n is None:
        return "-"
    try:
        n = int(n)
    except (ValueError, TypeError):
        return str(n)
    if n >= 10000:
        return f"{n / 10000:.0f}w+"
    return str(n)


# ─── CJK 宽度工具 ─────────────────────────────────────────────────────────────────
def _display_width(text):
    """计算字符串在终端中的显示宽度（CJK 字符占 2 格）"""
    width = 0
    for ch in str(text):
        cp = ord(ch)
        if (0x4E00 <= cp <= 0x9FFF or 0x3400 <= cp <= 0x4DBF or
            0x20000 <= cp <= 0x2A6DF or 0x2A700 <= cp <= 0x2B73F or
            0x2B740 <= cp <= 0x2B81F or 0x2B820 <= cp <= 0x2CEAF or
            0xF900 <= cp <= 0xFAFF or 0x2F800 <= cp <= 0x2FA1F or
            0x3000 <= cp <= 0x303F or 0xFF01 <= cp <= 0xFF60 or
            0xFFE0 <= cp <= 0xFFE6):
            width += 2
        else:
            width += 1
    return width


def _pad(text, width):
    """按显示宽度右填充空格"""
    text = str(text)
    return text + ' ' * max(0, width - _display_width(text))


def _rpad(text, width):
    """按显示宽度左填充空格（右对齐）"""
    text = str(text)
    return ' ' * max(0, width - _display_width(text)) + text


def _truncate(text, max_width):
    """按显示宽度截断，超出加 .."""
    text = str(text)
    if _display_width(text) <= max_width:
        return text
    result = ''
    w = 0
    for ch in text:
        cw = 2 if ord(ch) > 127 else 1
        if w + cw + 2 > max_width:
            break
        result += ch
        w += cw
    return result + '..'


# ─── 终端表格展示 ──────────────────────────────────────────────────────────────────
def print_terminal_table(works):
    """在终端打印作品表格 — 按账号依次展示"""
    if not works:
        warn("没有获取到任何作品")
        return

    # 按分类 → 账号分组
    cat_groups = defaultdict(list)
    for work in works:
        cat = work.get("_category", "关注账号")
        if cat not in DEFAULT_CATEGORIES:
            cat = "关注账号"
        cat_groups[cat].append(work)

    cat_colors = {"竞对账号": RED, "同类账号": YELLOW, "关注账号": CYAN}
    cat_icons = {"竞对账号": "⚔", "同类账号": "◎", "关注账号": "★"}

    # 列宽定义（终端显示宽度）
    W_TITLE = 36
    W_NUM = 8
    W_TIME = 16
    SEP_WIDTH = W_TITLE + W_NUM * 4 + W_TIME
    SEP = '─' * SEP_WIDTH

    total_shown = 0

    for cat in DEFAULT_CATEGORIES:
        arts = cat_groups.get(cat, [])
        if not arts:
            continue

        # 按账号分组
        account_groups = defaultdict(list)
        for art in arts:
            account_key = art.get("_accountName") or art.get("authorName") or art.get("_accountId", "未知")
            account_groups[account_key].append(art)

        cat_color = cat_colors.get(cat, CYAN)
        cat_icon = cat_icons.get(cat, "●")
        print(f"\n  {cat_color}{BOLD}{cat_icon} {cat}{RESET} — {len(arts)} 条作品")

        for account_name, account_works in sorted(account_groups.items(), key=lambda x: x[0]):
            # 按分享数降序
            account_works.sort(key=lambda a: -(int(a.get("shareCount", 0) or 0)))

            fans = format_fans(account_works[0].get("followerCount"))
            print(f"\n  {BOLD}▸ {account_name}（粉丝: {fans}）{RESET}")
            print(f"  {YELLOW}{SEP}{RESET}")

            header = (f"  {_pad('作品标题', W_TITLE)}"
                      f"{_rpad('收藏数', W_NUM)}{_rpad('评论数', W_NUM)}"
                      f"{_rpad('分享数', W_NUM)}{_rpad('点赞数', W_NUM)}"
                      f"  {_pad('发布时间', W_TIME)}")
            print(f"  {YELLOW}{header}{RESET}")
            print(f"  {YELLOW}{SEP}{RESET}")

            for work in account_works:
                title = work.get("title") or "无标题"
                title_d = _truncate(title, W_TITLE)

                collects = format_number(work.get("collectCount"))
                comments = format_number(work.get("commentCount"))
                shares = format_number(work.get("shareCount"))
                likes = format_number(work.get("likeCount"))

                pub_time = work.get("publishTime") or "-"
                if len(pub_time) > 16:
                    pub_time = pub_time[:16]
                pub_short = pub_time[5:16] if len(pub_time) >= 16 else pub_time

                row = (f"  {_pad(title_d, W_TITLE)}"
                       f"{_rpad(collects, W_NUM)}{_rpad(comments, W_NUM)}"
                       f"{_rpad(shares, W_NUM)}{_rpad(likes, W_NUM)}"
                       f"  {_pad(pub_short, W_TIME)}")
                print(row)
                total_shown += 1

    remaining = len(works) - total_shown
    if remaining > 0:
        print(f"\n  {YELLOW}... 还有 {remaining} 条作品未展示{RESET}")

    print()


# ─── Markdown 表格输出 ─────────────────────────────────────────────────────────────
# ─── 数据总结生成 ────────────────────────────────────────────────────────────────
# 常见中文停用词（用于话题提取时过滤）
_STOP_WORDS_CN = set([
    "这是", "不是", "一个", "没有", "可以", "这个", "那个", "什么", "怎么",
    "为什么", "一样", "大家", "你们", "他们", "我们", "自己", "今天", "明天",
    "昨天", "已经", "还是", "就是", "如果", "因为", "所以", "但是", "虽然",
    "不过", "一下", "一点", "很多", "非常", "比较", "真的", "现在", "不要",
    "也是", "只是", "这种", "那种", "这些", "那些", "一定", "这么", "那么",
    "吗", "呢", "吧", "啊", "哦", "嗯", "呀", "哈",
    "@", "#", " ", "，", "。", "！", "？", "、", "：", "；", "\n", "\r",
    "...", "..", "～", "~", "｜", "|", "/", "\\", "(", ")", "（", "）",
    "🔥", "😭", "✨", "🤜", "🤛", "👍", "❤", "💪",
])
# 常见无意义后缀（话题中的垃圾词）
_TOPIC_NOISE = set([
    "四大名著", "青年创作者成长计划", "抖音商城", "抖音美食", "抖音",
    "西游记", "水浒传",
])

def _extract_phrases(title, min_len=2, max_len=6):
    """从标题中提取候选中文短语（连续中文字符序列）"""
    phrases = []
    buf = ""
    for ch in title:
        if '\u4e00' <= ch <= '\u9fff':
            buf += ch
        else:
            if len(buf) >= min_len:
                for l in range(min_len, min(max_len + 1, len(buf) + 1)):
                    for i in range(len(buf) - l + 1):
                        sub = buf[i:i + l]
                        if sub not in _STOP_WORDS_CN and sub not in _TOPIC_NOISE:
                            phrases.append(sub)
            buf = ""
    if len(buf) >= min_len:
        for l in range(min_len, min(max_len + 1, len(buf) + 1)):
            for i in range(len(buf) - l + 1):
                sub = buf[i:i + l]
                if sub not in _STOP_WORDS_CN and sub not in _TOPIC_NOISE:
                    phrases.append(sub)
    return phrases


def _group_topics(phrase_counter):
    """合并语义相近的话题：长短语优先，去重子串"""
    # 按频率降序，同频时长短语优先
    items = sorted(phrase_counter.items(), key=lambda x: (-x[1], -len(x[0])))
    result = []
    for phrase, count in items:
        if count < 2:
            continue
        # 检查是否为已采纳短语的子串（长短语优先）
        is_sub = False
        for accepted, _ in result:
            if phrase in accepted:
                is_sub = True
                break
        if is_sub:
            continue
        # 检查是否为已采纳短语的父串（替换短短语）
        expanded = False
        for i, (accepted, ac_count) in enumerate(result):
            if accepted in phrase:
                result[i] = (phrase, count + ac_count)
                expanded = True
                break
        if expanded:
            continue
        result.append((phrase, count))
        if len(result) >= 5:
            break
    return result


def generate_summary(works):
    """根据作品数据生成 HTML + 纯文本双版本总结"""
    if not works:
        return "", ""

    # 1. 按账号聚合统计
    account_stats = defaultdict(lambda: {"total_likes": 0, "total_shares": 0, "total_collects": 0, "count": 0, "best_title": "", "best_likes": 0})
    for w in works:
        name = w.get("_accountName") or "未知"
        likes = int(w.get("likeCount", 0) or 0)
        shares = int(w.get("shareCount", 0) or 0)
        collects = int(w.get("collectCount", 0) or 0)
        s = account_stats[name]
        s["total_likes"] += likes
        s["total_shares"] += shares
        s["total_collects"] += collects
        s["count"] += 1
        if likes > s["best_likes"]:
            s["best_likes"] = likes
            s["best_title"] = (w.get("title") or "无标题")[:40]

    # 2. 突出的账号表现（按总点赞数降序 TOP3）
    top_accounts = sorted(account_stats.items(), key=lambda x: -x[1]["total_likes"])[:3]

    # 3. 爆款作品 TOP5（按综合互动量降序）
    for w in works:
        w["_engagement"] = (int(w.get("likeCount", 0) or 0) +
                            int(w.get("shareCount", 0) or 0) * 3 +
                            int(w.get("collectCount", 0) or 0) * 2 +
                            int(w.get("commentCount", 0) or 0) * 4)
    top_works = sorted(works, key=lambda x: -x["_engagement"])[:5]

    # 4. 高频话题提取
    phrase_counter = Counter()
    for w in works:
        title = w.get("title", "")
        for phrase in _extract_phrases(title):
            phrase_counter[phrase] += 1
    top_topics = _group_topics(phrase_counter)[:5]

    # ── 生成 HTML 版本 ──
    html = '<div class="summary-block">\n'
    html += '  <h3>📈 对上述作品的总结</h3>\n'

    # 突出的账号表现
    html += '  <div class="highlight"><strong>突出的账号表现：</strong></div>\n'
    html += '  <ul class="top-list">\n'
    for i, (name, s) in enumerate(top_accounts, 1):
        html += f'    <li><span><span class="rank">#{i}</span>{name} · 代表作「{s["best_title"]}」</span><span class="metric">点赞 {format_number(s["best_likes"])} · 总分享 {format_number(s["total_shares"])} · {s["count"]}条作品</span></li>\n'
    html += '  </ul>\n'

    # 爆款作品 TOP5
    html += '  <div class="highlight"><strong>爆款作品 TOP5（综合互动量）：</strong></div>\n'
    html += '  <ul class="top-list">\n'
    for i, w in enumerate(top_works, 1):
        title = (w.get("title") or "无标题")[:35]
        account = w.get("_accountName") or "未知"
        likes = format_number(w.get("likeCount"))
        shares = format_number(w.get("shareCount"))
        html += f'    <li><span><span class="rank">#{i}</span>{title} <small style="color:#999">— {account}</small></span><span class="metric">点赞 {likes} · 分享 {shares}</span></li>\n'
    html += '  </ul>\n'

    # 高频话题 TOP5
    if top_topics:
        html += '  <div class="highlight"><strong>高频话题 TOP5：</strong></div>\n'
        html += '  <ul class="top-list">\n'
        for i, (topic, count) in enumerate(top_topics, 1):
            html += f'    <li><span><span class="rank">#{i}</span>{topic}</span><span class="metric">出现 {count} 次</span></li>\n'
        html += '  </ul>\n'

    html += '</div>\n'

    # ── 生成纯文本版本（Markdown 格式，供对话展示）──
    text = ""
    text += "\n> 1. **突出的账号表现**：\n"
    for i, (name, s) in enumerate(top_accounts, 1):
        text += f">    - #{i} **{name}** · 代表作「{s['best_title']}」- 点赞 {format_number(s['best_likes'])} · 总分享 {format_number(s['total_shares'])} · {s['count']}条作品\n"

    text += ">\n> 2. **爆款作品 TOP5（综合互动量）**：\n"
    for i, w in enumerate(top_works, 1):
        title = (w.get("title") or "无标题")[:35]
        account = w.get("_accountName") or "未知"
        likes = format_number(w.get("likeCount"))
        shares = format_number(w.get("shareCount"))
        text += f">    - #{i} 「{title}」— {account} · 点赞 {likes} · 分享 {shares}\n"

    if top_topics:
        text += ">\n> 3. **高频话题 TOP5**：\n"
        for i, (topic, count) in enumerate(top_topics, 1):
            text += f">    - #{i} **{topic}**（出现 {count} 次）\n"

    return html, text


# ─── HTML 报告生成 ─────────────────────────────────────────────────────────────────
def generate_html_report(works, subscriptions, date_label, empty_accounts, output_path=None, rate_limited_accounts=None):
    """生成 HTML 报告文件，返回 html_file_path"""
    rate_limited_accounts = rate_limited_accounts or []
    if not works and not empty_accounts and not rate_limited_accounts:
        return None

    today = datetime.now().strftime('%Y-%m-%d')

    # 确定输出路径
    if output_path:
        out_dir = Path(output_path).parent
        html_file = Path(output_path)
    else:
        # 优先使用 SKILL_PATH/report/，其次用脚本所在目录/report/
        skill_dir = os.environ.get("SKILL_PATH", "")
        if skill_dir:
            out_dir = Path(skill_dir) / 'report'
        else:
            out_dir = Path(__file__).resolve().parent.parent / 'report'
        # 从作品数据提取账号名称，用于文件名
        account_names = list(dict.fromkeys(
            w.get("accountName") or w.get("_account_id", "unknown") for w in works
        ))
        if len(account_names) == 1:
            name_part = account_names[0]
        elif len(account_names) > 1:
            name_part = "_".join(account_names[:3])
            if len(account_names) > 3:
                name_part += f"_等{len(account_names)}账号"
        else:
            name_part = "抖音订阅"
        # 文件名安全处理：替换非法字符
        safe_name = re.sub(r'[\\/:*?"<>|]', '_', name_part)
        html_file = out_dir / f'{safe_name}_{today}_report.html'
    out_dir.mkdir(parents=True, exist_ok=True)

    # 分组数据
    cat_groups = defaultdict(list)
    for work in works:
        cat = work.get("_category", "关注账号")
        if cat not in DEFAULT_CATEGORIES:
            cat = "关注账号"
        cat_groups[cat].append(work)

    cat_colors = {
        "竞对账号": ("#e74c3c", "#fadbd8"),
        "同类账号": ("#f39c12", "#fdebd0"),
        "关注账号": ("#3498db", "#d6eaf8"),
    }

    # 构建 HTML
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>抖音账号作品报告 — {datetime.now().strftime('%Y-%m-%d')}</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC',
      'Microsoft YaHei', sans-serif;
    background: #f5f6fa; color: #2c3e50; line-height: 1.6;
  }}
  .container {{ max-width: 1100px; margin: 0 auto; padding: 20px; }}
  .header {{
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    color: white; padding: 32px 28px; border-radius: 12px; margin-bottom: 24px;
    text-align: center;
  }}
  .header h1 {{ font-size: 24px; margin-bottom: 6px; }}
  .header .subtitle {{ font-size: 14px; opacity: 0.75; }}
  .stats-bar {{
    display: flex; gap: 16px; flex-wrap: wrap; margin-bottom: 24px;
  }}
  .stat-card {{
    flex: 1; min-width: 140px; background: white; border-radius: 10px;
    padding: 16px 20px; box-shadow: 0 1px 4px rgba(0,0,0,.06);
    text-align: center;
  }}
  .stat-card .number {{ font-size: 28px; font-weight: 700; }}
  .stat-card .label {{ font-size: 13px; color: #7f8c8d; margin-top: 4px; }}
  .stat-card.works .number {{ color: #3498db; }}
  .stat-card.accounts .number {{ color: #2ecc71; }}
  .stat-card.empty .number {{ color: #e74c3c; }}
  .category-section {{ margin-bottom: 28px; }}
  .category-title {{
    font-size: 18px; font-weight: 700; padding: 8px 16px;
    border-radius: 8px 8px 0 0; display: inline-block;
  }}
  .account-block {{
    background: white; border-radius: 10px; margin-bottom: 16px;
    box-shadow: 0 1px 4px rgba(0,0,0,.06); overflow: hidden;
  }}
  .account-header {{
    padding: 14px 20px; border-bottom: 1px solid #eee;
    display: flex; align-items: center; justify-content: space-between;
    flex-wrap: wrap; gap: 8px;
  }}
  .account-name {{ font-size: 16px; font-weight: 700; }}
  .account-fans {{ font-size: 13px; color: #7f8c8d; }}
  .account-fans strong {{ color: #e74c3c; }}
  .table-wrap {{ overflow-x: auto; padding: 0 20px 16px; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
  th {{
    background: #f8f9fa; padding: 10px 12px; text-align: left;
    font-weight: 600; color: #555; border-bottom: 2px solid #dee2e6;
    white-space: nowrap;
  }}
  th.right {{ text-align: right; }}
  td {{
    padding: 10px 12px; border-bottom: 1px solid #f1f3f5;
    vertical-align: top;
  }}
  td.right {{ text-align: right; font-variant-numeric: tabular-nums; }}
  tr:hover {{ background: #f8f9ff; }}
  td.title {{ max-width: 360px; }}
  td.title a {{
    color: #2c3e50; text-decoration: none; font-weight: 500;
  }}
  td.title a:hover {{ color: #3498db; text-decoration: underline; }}
  .empty-notice {{
    background: #fff3cd; border-left: 4px solid #f39c12;
    padding: 12px 20px; border-radius: 6px; margin-bottom: 16px;
    font-size: 14px; color: #856404;
  }}
  .summary-block {{
    background: white; border-radius: 10px; margin-bottom: 16px;
    box-shadow: 0 1px 4px rgba(0,0,0,.06); padding: 20px 24px;
  }}
  .summary-block h3 {{
    margin: 0 0 12px; font-size: 16px; color: #2c3e50;
    border-bottom: 2px solid #3498db; padding-bottom: 8px; display: inline-block;
  }}
  .summary-block .highlight {{
    background: #eaf6ff; border-left: 4px solid #3498db;
    padding: 10px 16px; border-radius: 6px; margin: 10px 0;
    font-size: 14px; color: #2c3e50; line-height: 1.6;
  }}
  .summary-block .top-list {{
    list-style: none; padding: 0; margin: 8px 0;
  }}
  .summary-block .top-list li {{
    padding: 8px 12px; border-bottom: 1px solid #f1f3f5;
    font-size: 14px; display: flex; justify-content: space-between;
  }}
  .summary-block .top-list li:last-child {{ border-bottom: none; }}
  .summary-block .rank {{ color: #e74c3c; font-weight: 700; margin-right: 8px; }}
  .summary-block .metric {{ color: #7f8c8d; font-size: 13px; }}
  .footer {{
    text-align: center; padding: 20px; color: #999; font-size: 13px;
    border-top: 1px solid #e8e8e8; margin-top: 20px;
  }}
  .badge {{
    display: inline-block; padding: 2px 8px; border-radius: 4px;
    font-size: 12px; font-weight: 600;
  }}
  @media (max-width: 768px) {{
    .container {{ padding: 12px; }}
    .header {{ padding: 20px 16px; }}
    .stats-bar {{ gap: 8px; }}
    .stat-card {{ min-width: 100px; padding: 12px; }}
    .stat-card .number {{ font-size: 22px; }}
    table {{ font-size: 12px; }}
    th, td {{ padding: 8px 6px; }}
    td.title {{ max-width: 180px; }}
  }}
</style>
</head>
<body>
<div class="container">

<div class="header">
  <h1>📊 抖音账号作品报告</h1>
  <div class="subtitle">生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}  |  {date_label}</div>
</div>

<div class="stats-bar">
  <div class="stat-card accounts">
    <div class="number">{len(subscriptions)}</div>
    <div class="label">订阅账号</div>
  </div>
  <div class="stat-card works">
    <div class="number">{len(works)}</div>
    <div class="label">作品总数</div>
  </div>
  <div class="stat-card empty">
    <div class="number">{len(empty_accounts)}</div>
    <div class="label">无更新账号</div>
  </div>
</div>
"""

    # 分类展示
    for cat in DEFAULT_CATEGORIES:
        arts = cat_groups.get(cat, [])
        if not arts:
            continue

        cat_color, cat_bg = cat_colors.get(cat, ("#3498db", "#d6eaf8"))
        cat_icons = {"竞对账号": "⚔️", "同类账号": "◎", "关注账号": "⭐"}

        # 按账号分组
        account_groups = defaultdict(list)
        for art in arts:
            account_key = art.get("_accountName") or art.get("authorName") or art.get("_accountId", "未知")
            account_groups[account_key].append(art)

        html += f"""
<div class="category-section">
  <div class="category-title" style="background:{cat_bg};color:{cat_color};">
    {cat_icons.get(cat, '●')} {cat} — {len(arts)} 条作品
  </div>
"""

        for account_name, account_works in sorted(account_groups.items(), key=lambda x: x[0]):
            account_works.sort(key=lambda a: -(int(a.get("shareCount", 0) or 0)))
            fans = format_fans(account_works[0].get("followerCount"))
            sec_uid = account_works[0].get("secUid") or ""
            account_link = f"https://www.douyin.com/user/{sec_uid}" if sec_uid else ""

            name_html = f'<a href="{account_link}" target="_blank" style="color:inherit;text-decoration:none;">{account_name}</a>' if account_link else account_name

            html += f"""
  <div class="account-block">
    <div class="account-header">
      <span class="account-name">📌 {name_html}</span>
      <span class="account-fans">粉丝: <strong>{fans}</strong> | 作品: {len(account_works)} 条</span>
    </div>
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>作品标题</th>
            <th class="right">收藏数</th>
            <th class="right">评论数</th>
            <th class="right">分享数</th>
            <th class="right">点赞数</th>
            <th>发布时间</th>
          </tr>
        </thead>
        <tbody>
"""
            for work in account_works:
                title = work.get("title") or "无标题"
                video_url = work.get("workUrl") or work.get("videoUrl", "#")
                collects = format_number(work.get("collectCount"))
                comments = format_number(work.get("commentCount"))
                shares = format_number(work.get("shareCount"))
                likes = format_number(work.get("likeCount"))
                pub_time = work.get("publishTime") or "-"
                if len(pub_time) > 16:
                    pub_time = pub_time[:16]

                title_display = title.replace("\n", " ")

                html += f"""          <tr>
            <td class="title"><a href="{video_url}" target="_blank">{title_display}</a></td>
            <td class="right">{collects}</td>
            <td class="right">{comments}</td>
            <td class="right">{shares}</td>
            <td class="right">{likes}</td>
            <td>{pub_time}</td>
          </tr>
"""
            html += """        </tbody>
      </table>
    </div>
  </div>
"""

    # 无更新账号
    if empty_accounts:
        html += '<div class="category-section">\n'
        for name in empty_accounts:
            html += f'<div class="empty-notice">⚠️ <strong>{name}</strong>：该时间段内无更新作品</div>\n'
        html += '</div>\n'

    # 被频率限制的账号
    if rate_limited_accounts:
        html += '<div class="category-section">\n'
        for name in rate_limited_accounts:
            html += (f'<div class="empty-notice" style="border-left-color:#e67e22;">'
                     f'⚠️ <strong>{name}</strong>：该账号订阅已超过失败阈值，请联系客服邮箱处理。</div>\n')
        html += '</div>\n'

    # ── 数据总结区块（占位，脚本结束时替换为实际内容）──
    if works:
        html += '\n<!-- SUMMARY_PLACEHOLDER -->\n'

    html += f"""
<div class="footer">
  订阅账号: {len(subscriptions)} 个 | 作品总数: {len(works)} 条 | 无更新: {len(empty_accounts)} 个 | 限流: {len(rate_limited_accounts)} 个<br>
  由抖音账号订阅追踪自动生成 | redfox.hk
</div>

</div>
</body>
</html>"""

    html_file.write_text(html, encoding="utf-8")
    return str(html_file)


def print_markdown_table(works):
    """输出纯 Markdown 表格，供 Agent 直接展示给用户"""
    if not works:
        print("没有获取到任何作品")
        return

    cat_groups = defaultdict(list)
    for work in works:
        cat = work.get("_category", "关注账号")
        if cat not in DEFAULT_CATEGORIES:
            cat = "关注账号"
        cat_groups[cat].append(work)

    for cat in DEFAULT_CATEGORIES:
        arts = cat_groups.get(cat, [])
        if not arts:
            continue

        account_groups = defaultdict(list)
        for art in arts:
            account_key = art.get("_accountName") or art.get("authorName") or art.get("_accountId", "未知")
            account_groups[account_key].append(art)

        print(f"\n### {cat}（{len(arts)} 条作品）")

        for account_name, account_works in sorted(account_groups.items(), key=lambda x: x[0]):
            account_works.sort(key=lambda a: -(int(a.get("shareCount", 0) or 0)))
            fans = format_fans(account_works[0].get("followerCount"))
            sec_uid = account_works[0].get("secUid") or ""
            account_link = f"https://www.douyin.com/user/{sec_uid}" if sec_uid else ""

            if account_link:
                print(f"\n**[{account_name}]({account_link})**（粉丝: {fans}）")
            else:
                print(f"\n**{account_name}**（粉丝: {fans}）")
            print()
            print("| 作品标题 | 收藏数 | 评论数 | 分享数 | 点赞数 | 发布时间 |")
            print("|----------|--------|--------|--------|--------|----------|")

            for work in account_works:
                title = work.get("title") or "无标题"
                work_url = work.get("workUrl") or work.get("videoUrl") or ""
                title_safe = title.replace("|", "\\|").replace("\n", " ")
                if work_url:
                    title_d = f"[{title_safe}]({work_url})"
                else:
                    title_d = title_safe

                collects = format_number(work.get("collectCount"))
                comments = format_number(work.get("commentCount"))
                shares = format_number(work.get("shareCount"))
                likes = format_number(work.get("likeCount"))

                pub_time = work.get("publishTime") or "-"
                if len(pub_time) > 16:
                    pub_time = pub_time[:16]
                pub_short = pub_time[5:16] if len(pub_time) >= 16 else pub_time

                print(f"| {title_d} | {collects} | {comments} | {shares} | {likes} | {pub_short} |")

    print()



# ─── 主流程 ────────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="抖音账号订阅追踪 — 订阅抖音账号，追踪最新作品",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 subscribe.py add "5437662" --name "李佳琦" --category "竞对账号"
  python3 subscribe.py add "5437662,13232311,3234242"
  python3 subscribe.py remove "5437662"
  python3 subscribe.py list
  python3 subscribe.py fetch
  python3 subscribe.py fetch --date 2026-06-01
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # ── add 子命令 ──
    add_parser = subparsers.add_parser("add", help="添加订阅（需提供抖音号）")
    add_parser.add_argument("account_ids",
                            help="抖音号，支持逗号分隔多个（如 5437662,13232311）")
    add_parser.add_argument("--name", dest="account_name", default="",
                            help="账号名（可选，仅用于显示）")
    add_parser.add_argument("--category", default="关注账号",
                            choices=DEFAULT_CATEGORIES + ["其他"],
                            help="分类标签（默认: 关注账号）")

    # ── remove 子命令 ──
    remove_parser = subparsers.add_parser("remove", help="取消订阅")
    remove_parser.add_argument("account_id", help="抖音号")

    # ── list 子命令 ──
    subparsers.add_parser("list", help="列出所有订阅")

    # ── fetch 子命令 ──
    fetch_parser = subparsers.add_parser("fetch", help="拉取最新作品")
    fetch_parser.add_argument("--accounts", default="",
                              help="抖音号列表，逗号分隔（如 YuZhouXiaoLi1220,Fish688688）")
    fetch_parser.add_argument("--date", default="",
                              help="指定单日日期 YYYY-MM-DD（默认: 最新数据）")
    fetch_parser.add_argument("--date-start", default="",
                              help="日期范围开始 YYYY-MM-DD")
    fetch_parser.add_argument("--date-end", default="",
                              help="日期范围结束 YYYY-MM-DD")
    fetch_parser.add_argument("--markdown", action="store_true",
                              help="输出 Markdown 格式表格（供 Agent 展示）")
    fetch_parser.add_argument("--html", action="store_true",
                              help="生成 HTML 报告文件")
    fetch_parser.add_argument("--html-path", default="",
                              help="HTML 报告输出路径")

    # ── 全局参数 ──
    parser.add_argument("--api-key", help="API Key")
    args = parser.parse_args()

    # ── Banner ──
    banner = f"""{CYAN}{BOLD}
  ╔══════════════════════════════════════╗
  ║     抖音账号订阅 · 作品追踪           ║
  ║     竞对 · 同类 · 关注 · 一网打尽     ║
  ╚══════════════════════════════════════╝{RESET}
"""
    print(banner)

    # ── 检查依赖 ──
    if not HAS_REQUESTS:
        error("缺少 requests 库，请安装: pip3 install requests")
        sys.exit(1)

    # ── 分发命令 ──
    if args.command == "add":
        add_subscriptions(args.account_ids, args.account_name, args.category)
        return

    if args.command == "remove":
        remove_subscription(args.account_id)
        return

    if args.command == "list":
        list_subscriptions()
        return

    if args.command == "fetch":
        # ── 获取账号列表：优先 --accounts 参数，其次 JSON 文件 ──
        accounts_arg = getattr(args, 'accounts', '') or ''
        is_adhoc_query = bool(accounts_arg)  # 区分规则1/2的关键标志

        if accounts_arg:
            # 直接从命令行参数构建订阅列表（无需文件存储）
            raw_ids = [aid.strip() for aid in accounts_arg.split(",") if aid.strip()]
            subscriptions = [
                {"accountId": aid, "accountName": aid, "category": "关注账号"}
                for aid in raw_ids
            ]
        else:
            subscriptions = load_subscriptions()

        if not subscriptions:
            error("未指定任何抖音账号，请使用 --accounts 参数传入抖音号")
            print(f"\n  示例: {CYAN}python3 subscribe.py fetch --accounts \"YuZhouXiaoLi1220,Fish688688\" --html{RESET}")
            sys.exit(1)

        api_key = get_api_key(cli_key=args.api_key)

        session = requests.Session()
        session.verify = True
        session.headers.update({
            "Content-Type": "application/json",
            "REDFOX_API_KEY": api_key,
        })

        date_str = args.date or ""
        date_start = getattr(args, 'date_start', '') or ''
        date_end = getattr(args, 'date_end', '') or ''
        user_specified_date = bool(date_str or date_start or date_end)

        # ── 规则 1 & 2：根据是否已订阅，决定默认查询策略 ──
        if not user_specified_date:
            if is_adhoc_query:
                # 规则1：未订阅账号，默认查近 30 天
                fallback_start = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
                fallback_end = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
                date_label = f"（近 30 天: {fallback_start} 至 {fallback_end}）"
            else:
                # 规则2：已订阅账号，默认查 T-1
                yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
                date_str = yesterday
                date_label = f"（日期: {date_str}）"
        else:
            if date_start and date_end:
                date_label = f"（日期范围: {date_start} 至 {date_end}）"
            elif date_str:
                date_label = f"（日期: {date_str}）"
            else:
                date_label = "（最新数据）"

        step(f"从 {len(subscriptions)} 个抖音账号拉取作品{date_label}...")
        print()

        if is_adhoc_query and not user_specified_date:
            # 规则1：查近 30 天
            works, empty_accounts, rate_limited_accounts = fetch_all_works(
                session, subscriptions, None, fallback_start, fallback_end
            )
        else:
            works, empty_accounts, rate_limited_accounts = fetch_all_works(
                session, subscriptions,
                date_str or None,
                date_start or None,
                date_end or None
            )

        # ── 规则 1：近 30 天无数据，自动回溯近半年 ──
        if is_adhoc_query and not works and not user_specified_date and not rate_limited_accounts:
            info("近 30 天无更新作品，自动回溯近半年...")
            print()
            half_year_start = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')
            half_year_end = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            date_label = f"（回溯半年: {half_year_start} 至 {half_year_end}）"
            step(f"从 {len(subscriptions)} 个抖音账号拉取作品{date_label}...")
            print()
            works, empty_accounts, rate_limited_accounts = fetch_all_works(
                session, subscriptions, None, half_year_start, half_year_end
            )
            date_str = ""
            date_start = half_year_start
            date_end = half_year_end

        # ── 规则 2：已订阅账号 T-1 无数据时的提示 ──
        if not is_adhoc_query and not works and not user_specified_date:
            for name in empty_accounts:
                print(f"\n  {YELLOW}[!]{RESET} 「{name}」昨日暂未发布作品")
            print(f"\n  {CYAN}💡 如需数据核查可联系工作人员邮箱 {SUPPORT_EMAIL} 处理{RESET}")

        # ── 规则 3：被频率限制拒绝的账号提示 ──
        for name in rate_limited_accounts:
            print(f"\n  {RED}[✗]{RESET} 「{name}」当前账号订阅已超过失败阈值，请联系客服邮箱 {SUPPORT_EMAIL} 处理")

        if not works and not empty_accounts and not rate_limited_accounts:
            warn("未获取到任何作品，可能是账号暂无数据或 API 暂时不可用")
            sys.exit(1)

        # ── 规则 1：未订阅账号近半年无数据的最终提示 ──
        if is_adhoc_query and not works and not rate_limited_accounts:
            for name in empty_accounts:
                print(f"\n  {YELLOW}[!]{RESET} 抱歉您订阅的「{name}」账号近半年都未发布过作品")
            print(f"\n  {CYAN}💡 如果需要数据核查可联系工作人员邮箱 {SUPPORT_EMAIL} 处理{RESET}")

        if works:
            info(f"拉取完成: 共 {len(works)} 条作品")

        # ── 未收录账号提示 ──
        NOT_FOUND_MSG = (
            "当前暂未找到该账号信息，可能是数据覆盖范围有限所致。\n"
            "不过别担心，我们将尽快为您更新数据，通常10分钟内可查，"
            "特殊情况下需1天，您可订阅明日推送。"
        )

        # ── 输出（终端 / Markdown / HTML） ──
        want_html = getattr(args, 'html', False)
        html_path_arg = getattr(args, 'html_path', '') or ''

        # 仅当有作品数据时才生成 HTML 报告
        if want_html and works:
            html_file = generate_html_report(
                works, subscriptions, date_label, empty_accounts,
                output_path=html_path_arg or None,
                rate_limited_accounts=rate_limited_accounts
            )
            if html_file:
                # ── 生成总结并嵌入 HTML（替换占位符）──
                summary_html, summary_text = generate_summary(works)
                raw = Path(html_file).read_text(encoding="utf-8")
                raw = raw.replace("<!-- SUMMARY_PLACEHOLDER -->", summary_html)
                Path(html_file).write_text(raw, encoding="utf-8")
                # ── 自动打开 HTML 报告 ──
                try:
                    import subprocess
                    subprocess.Popen(["open", str(html_file)])
                except Exception:
                    pass
                info(f"HTML 报告已生成: {html_file}")
                # ── 输出 Markdown 表格（带链接，供 Agent 对话展示）──
                print_markdown_table(works)
                for name in empty_accounts:
                    warn(f"「{name}」该时间段内无更新作品")
                for name in rate_limited_accounts:
                    print(f"\n**{name}**：当前账号订阅已超过失败阈值，请联系客服邮箱 {SUPPORT_EMAIL} 处理")
                # ── 输出纯文本总结（供 Agent 对话展示，与 HTML 内容一致）──
                if summary_text:
                    print(f"\n{GREEN}=== 作品总结（与 HTML 报告一致）==={RESET}")
                    print(summary_text)
        elif want_html and not works:
            info("无作品数据，跳过 HTML 报告生成")
            # 仍然输出提示信息
            for name in empty_accounts:
                warn(f"「{name}」该时间段内无更新作品")
            for name in rate_limited_accounts:
                print(f"\n**{name}**：当前账号订阅已超过失败阈值，请联系客服邮箱 {SUPPORT_EMAIL} 处理")
        elif getattr(args, 'markdown', False):
            if works:
                print_markdown_table(works)
                # ── 输出纯文本总结 ──
                _, summary_text = generate_summary(works)
                if summary_text:
                    print(f"\n### 对上述作品的总结")
                    print(summary_text)
            for name in empty_accounts:
                print(f"\n**{name}**：该时间段内无更新作品")
            for name in rate_limited_accounts:
                print(f"\n**{name}**：当前账号订阅已超过失败阈值，请联系客服邮箱 {SUPPORT_EMAIL} 处理")
            print(f"\n订阅账号: {len(subscriptions)} 个 | 作品总数: {len(works)} 条")
        else:
            if works:
                print_terminal_table(works)
            for name in empty_accounts:
                warn(f"「{name}」该时间段内无更新作品")
            for name in rate_limited_accounts:
                warn(f"「{name}」当前账号订阅已超过失败阈值，请联系客服邮箱 {SUPPORT_EMAIL} 处理")
            print(f"\n{GREEN}{BOLD}✓ 完成!{RESET}")
            print(f"  订阅账号: {len(subscriptions)} 个")
            print(f"  作品总数: {len(works)} 条")
        return

    # ── 无命令 ──
    parser.print_help()
    print(f"\n{CYAN}快速开始:{RESET}")
    print(f"  add <抖音号>      — 添加订阅（支持逗号分隔多个）")
    print(f"  remove <抖音号>   — 取消订阅")
    print(f"  list              — 查看订阅")
    print(f"  fetch             — 拉取作品")


if __name__ == "__main__":
    main()
