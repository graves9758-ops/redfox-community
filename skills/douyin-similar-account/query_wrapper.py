#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import io
import subprocess
import json

# 重配置输出编码
if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 直接调用脚本
sys.argv = ['script', '--account_id', '疯狂小杨哥']
exec(open('scripts/douyin_similar_account.py', encoding='utf-8').read())
