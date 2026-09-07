#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
import os
import re
import sys
from pathlib import Path

import requests

try:
    from docx import Document
    from bs4 import BeautifulSoup
except ImportError as e:
    print(json.dumps({"status": "error", "error": f"缺少依赖库: {str(e)}"}, ensure_ascii=False))
    sys.exit(1)

# API单次查询最大字符数
MAX_CONTENT_LENGTH = 3000

# 内容总字数上限（超过此值直接提示用户手动分批，不执行检测）
MAX_TOTAL_LENGTH = 10000

# API地址
API_URL = "https://redfox.hk/story/api/cozeSkill/sensitiveWordSearch"

# 环境变量名
ENV_KEY_NAME = "REDFOX_API_KEY"

# 常见 Shell 配置文件列表
SHELL_CONFIG_FILES = [
    ".bashrc",
    ".zshrc",
    ".bash_profile",
    ".profile",
]


def _get_api_key():
    """
    获取 API Key，优先级：
    1. 环境变量 REDFOX_API_KEY
    2. 自动从 Shell 配置文件（~/.bashrc、~/.zshrc 等）中读取
    3. 以上均未获取到则提示用户配置并退出
    """
    # 1. 优先从环境变量获取
    api_key = os.getenv(ENV_KEY_NAME, "").strip()
    if api_key:
        return api_key

    # 2. 从 Shell 配置文件中读取
    home = Path.home()
    for cfg_file in SHELL_CONFIG_FILES:
        cfg_path = home / cfg_file
        if cfg_path.is_file():
            try:
                content = cfg_path.read_text(encoding="utf-8", errors="replace")
                # 匹配 export REDFOX_API_KEY="ak_xxx" 或 export REDFOX_API_KEY=ak_xxx
                match = re.search(
                    rf'export\s+{ENV_KEY_NAME}\s*=\s*["\']?([a-zA-Z0-9_\-]+)["\']?',
                    content
                )
                if match:
                    api_key = match.group(1).strip()
                    if api_key:
                        return api_key
            except (OSError, UnicodeDecodeError):
                continue

    # 3. 未获取到，提示用户配置
    raise ValueError(
        f"未配置 {ENV_KEY_NAME}，请通过以下方式之一配置：\n"
        f"  方式一（推荐）：设置环境变量 export {ENV_KEY_NAME}=ak_xxxxxxxx\n"
        f"  方式二：将上述 export 语句写入 ~/.bashrc 或 ~/.zshrc，然后执行 source ~/.bashrc\n"
        f"  API Key 获取方式：访问 https://redfox.hk/?source=github 注册登录后在个人中心获取"
    )


def _call_api(content, platform="公众号", source="公众号违禁词查询-GitHub", max_retries=2):
    """
    调用公众号违禁词检测API（POST + JSON方式）

    Args:
        content: 待检测的文案内容
        platform: 平台名称
        source: 来源标识
        max_retries: 最大重试次数

    Returns:
        dict: API响应的data字段
    """
    api_key = _get_api_key()

    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "X-API-KEY": api_key
    }

    payload = {
        "content": content,
        "platform": platform,
        "source": source
    }

    last_error = None
    for attempt in range(max_retries + 1):
        try:
            response = requests.post(API_URL, headers=headers, json=payload, timeout=30)

            if response.status_code >= 500 and attempt < max_retries:
                import time
                time.sleep(1 * (attempt + 1))
                continue

            if response.status_code >= 400:
                raise Exception(f"HTTP请求失败: {response.status_code}, {response.text[:500]}")

            resp = response.json()

            # API返回格式: {"code": 2000, "data": {...}, "msg": "成功"}
            api_code = resp.get("code", 0)
            if api_code != 2000:
                raise Exception(f"API业务错误: code={api_code}, msg={resp.get('msg', '未知')}")

            return resp.get("data") or {}

        except requests.exceptions.Timeout as e:
            last_error = e
            if attempt < max_retries:
                import time
                time.sleep(1 * (attempt + 1))
                continue
            raise Exception(f"请求超时，已重试{max_retries}次仍失败")
        except requests.exceptions.ConnectionError as e:
            last_error = e
            if attempt < max_retries:
                import time
                time.sleep(1 * (attempt + 1))
                continue
            raise Exception(f"连接失败，已重试{max_retries}次仍失败: {str(e)}")
        except ValueError:
            # JSON解析失败，直接抛出
            raise
        except Exception as e:
            if "HTTP请求失败" in str(e) or "API业务错误" in str(e):
                raise
            last_error = e
            if attempt < max_retries:
                import time
                time.sleep(1 * (attempt + 1))
                continue
            raise Exception(f"请求失败: {str(e)}")


def extract_from_file(file_path):
    """从文件中提取文本（支持DOC、DOCX、TXT等文本类型文件）"""
    if not os.path.exists(file_path):
        raise Exception(f"文件不存在: {file_path}")

    file_ext = os.path.splitext(file_path)[1].lower()

    if file_ext in ['.doc', '.docx']:
        doc = Document(file_path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text.strip()
    elif file_ext == '.txt':
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            return f.read().strip()
    elif file_ext in ['.csv', '.md', '.log', '.json', '.xml', '.html', '.htm']:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            return f.read().strip()
    else:
        raise Exception(f"不支持的文件类型: {file_ext}，仅支持图片、TXT、DOC、DOCX等文本类型文件")


def extract_from_web(url):
    """
    从网页中提取文本。优先使用Playwright无头浏览器渲染JS后提取（支持SPA页面），
    若Playwright不可用则回退到requests方式。
    """
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    # 优先尝试Playwright（支持SPA/JS动态渲染页面）
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=30000)
            page.wait_for_timeout(3000)  # 等待JS渲染

            # 优先提取文章正文区域（常见选择器）
            article_selectors = [
                'article', '.article-content', '.article-body', '.article-detail',
                '.post-content', '.post-body', '.content-body', '.entry-content',
                '.rich_media_content', '#js_content', '.detail-content',
                '.article-content', '.news-content', '.text-content',
            ]
            text = None
            for selector in article_selectors:
                try:
                    el = page.query_selector(selector)
                    if el:
                        extracted = el.inner_text().strip()
                        if len(extracted) > 100:  # 正文区域通常较长
                            text = extracted
                            break
                except Exception:
                    continue

            # 无匹配正文区域时回退到body
            if not text:
                text = page.inner_text('body')

            browser.close()
            return text.strip()
    except Exception:
        pass  # Playwright不可用，回退到requests方式

    # 回退：使用requests获取静态HTML并提取文本
    try:
        response = requests.get(url, timeout=30, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        if response.status_code >= 400:
            raise Exception(f"网页请求失败: HTTP {response.status_code}")

        soup = BeautifulSoup(response.text, 'html.parser')
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        text = soup.get_text(separator='\n', strip=True)
        return text.strip()
    except Exception as e:
        raise Exception(f"网页内容提取失败: {str(e)}")


def check_sensitive_words(content):
    """
    调用公众号违禁词检测API（POST方式，参数通过请求体传递）

    Args:
        content: 待检测的文案内容

    Returns:
        dict: 包含检测结果和格式化HTML的字典
    """

    # 内容长度校验
    if len(content) > MAX_CONTENT_LENGTH:
        return {
            "status": "error",
            "platform": "公众号",
            "original_content": content[:200] + "...",
            "error": f"文案内容过长（{len(content)}字符），单次上限为{MAX_CONTENT_LENGTH}字符，请缩减后重试"
        }

    try:
        # 调用API
        api_data = _call_api(content)

        # 从API返回的content中提取违禁词列表
        api_content = api_data.get("content") or ""
        original_content = api_data.get("originalContent") or content
        prohibited_words_type = api_data.get("prohibitedWordsType") or []

        # 提取违禁词文本（兼容banned-word/sensitive-word/industry-banned-word三种类名，去重）
        sensitive_words = list(dict.fromkeys(
            re.findall(r'<span class="(?:banned-word|sensitive-word|industry-banned-word)">(.*?)</span>', api_content)
        ))

        # 将所有违禁词标签样式统一替换为color:red样式
        html_content = re.sub(
            r'<span class="(?:banned-word|sensitive-word|industry-banned-word)">',
            '<span style="color:red">',
            api_content
        )

        # 过滤英文误匹配：API会将英文单词内部子串误标为违禁词（如"Glasswing"中的"ass"）
        english_words = re.findall(r'[A-Za-z]+', original_content)
        false_positive_words = set()
        for ew in english_words:
            for sw in sensitive_words:
                if sw.isascii() and sw.isalpha() and sw.lower() in ew.lower() and sw.lower() != ew.lower():
                    false_positive_words.add(sw)

        # 从sensitive_words中移除误匹配项
        sensitive_words = [w for w in sensitive_words if w not in false_positive_words]

        # 从html_content中移除误匹配的span标签，还原为纯文本
        for fpw in false_positive_words:
            escaped = re.escape(fpw)
            html_content = re.sub(
                rf'<span style="color:red">{escaped}</span>',
                fpw,
                html_content
            )

        result = {
            "status": "success",
            "platform": "公众号",
            "original_content": original_content,
            "sensitive_words": sensitive_words,
            "prohibited_words_type": prohibited_words_type,
            "word_count": len(sensitive_words),
            "html_content": html_content
        }

        return result

    except ValueError as e:
        return {
            "status": "error",
            "platform": "公众号",
            "original_content": content,
            "error": str(e)
        }
    except Exception as e:
        return {
            "status": "error",
            "platform": "公众号",
            "original_content": content,
            "error": f"处理失败: {str(e)}"
        }


def main():
    parser = argparse.ArgumentParser(description="公众号违禁词检测工具")

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--content", help="直接传入文案文本")
    group.add_argument("--file", help="文件路径（支持TXT、DOC、DOCX等文本类型文件）")
    group.add_argument("--url", help="网页地址")

    parser.add_argument("--extract-only", action="store_true", help="仅提取文本不检测，返回提取的文本内容和长度")

    args = parser.parse_args()

    # 获取文本内容
    try:
        if args.content:
            text = args.content
        elif args.file:
            text = extract_from_file(args.file)
        elif args.url:
            text = extract_from_web(args.url)
        else:
            print(json.dumps({"status": "error", "error": "请指定输入方式：--content、--file 或 --url"}, ensure_ascii=False))
            return
    except Exception as e:
        print(json.dumps({"status": "error", "error": f"文本提取失败: {str(e)}"}, ensure_ascii=False))
        return

    if not text:
        print(json.dumps({"status": "error", "error": "未提取到文本内容"}, ensure_ascii=False))
        return

    # 仅提取模式：返回文本内容和长度，不调用检测API
    if args.extract_only:
        print(json.dumps({"status": "extracted", "content": text, "length": len(text)}, ensure_ascii=False))
        return

    # 调用违禁词检测
    result = check_sensitive_words(text)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
