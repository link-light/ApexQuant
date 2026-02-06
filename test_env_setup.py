#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试环境变量配置

验证API密钥是否正确从环境变量加载
"""

import os
import sys
import io

# 设置stdout为UTF-8编码
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 尝试加载.env文件
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("[OK] python-dotenv 已安装")
except ImportError:
    print("[ERROR] python-dotenv 未安装，请运行: pip install python-dotenv")
    sys.exit(1)

print("\n" + "="*60)
print("环境变量配置检查")
print("="*60)

# 检查关键环境变量
env_vars = {
    'DEEPSEEK_API_KEY': 'DeepSeek API密钥',
    'CLAUDE_API_KEY': 'Claude API密钥（可选）',
    'LOG_LEVEL': '日志级别',
    'ENABLE_MONITORING': '性能监控',
}

all_configured = True

for var_name, description in env_vars.items():
    value = os.getenv(var_name)
    
    if value:
        # 对于密钥只显示部分
        if 'KEY' in var_name or 'TOKEN' in var_name:
            display_value = f"{value[:8]}...{value[-4:]}" if len(value) > 12 else "***"
        else:
            display_value = value
        
        print(f"[OK] {var_name:25s} = {display_value}")
    else:
        status = "(可选)" if '可选' in description else "(必需)"
        print(f"[  ] {var_name:25s} = 未设置 {status}")
        
        if status == "(必需)":
            all_configured = False

print("="*60)

if all_configured:
    print("[SUCCESS] 所有必需的环境变量已正确配置")
    print("\n可以开始使用ApexQuant了！")
    sys.exit(0)
else:
    print("[WARNING] 部分必需的环境变量未配置")
    print("\n请按照以下步骤配置：")
    print("1. 复制项目根目录下的 ENV_SETUP.md 文件查看详细说明")
    print("2. 创建 .env 文件并填入你的API密钥")
    print("3. 重新运行此测试脚本")
    sys.exit(1)

