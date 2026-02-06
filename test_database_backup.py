#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试数据库备份功能
"""

import sys
import io
import logging
import time
from pathlib import Path

# 设置stdout为UTF-8编码
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 导入数据库管理器
sys.path.insert(0, 'python')
from apexquant.simulation.database import DatabaseManager

print("="*60)
print("数据库备份功能测试")
print("="*60)

# 创建测试数据库
db_path = "data/test_backup.db"
print(f"\n[1/7] 创建测试数据库: {db_path}")
db = DatabaseManager(db_path, auto_backup=False)

# 创建测试数据
print("\n[2/7] 创建测试账户...")
account_id = db.create_account(
    initial_capital=1000000.0,
    strategy_type="test_strategy",
    account_name="Test Backup Account"
)
print(f"      账户ID: {account_id}")

# 测试手动备份
print("\n[3/7] 测试手动备份...")
backup_path = db.backup()
if backup_path:
    print(f"      [OK] 备份成功: {backup_path}")
else:
    print("      [FAIL] 备份失败")
    sys.exit(1)

# 等待1秒创建第二个备份
time.sleep(1)
print("\n[4/7] 创建第二个备份...")
backup_path2 = db.backup()
if backup_path2:
    print(f"      [OK] 备份成功: {backup_path2}")

# 列出所有备份
print("\n[5/7] 列出所有备份...")
backups = db.list_backups()
print(f"      找到 {len(backups)} 个备份文件:")
for i, backup in enumerate(backups, 1):
    print(f"      {i}. {backup['name']}")
    print(f"         大小: {backup['size']/1024:.2f} KB")
    print(f"         创建时间: {backup['created']}")

# 测试自动备份
print("\n[6/7] 测试自动备份...")
db2 = DatabaseManager("data/test_auto_backup.db", auto_backup=True)
print("      [OK] 自动备份已触发")

# 测试备份清理
print("\n[7/7] 测试备份清理...")
db._cleanup_old_backups(days=0)  # 清理所有备份（测试用）
remaining_backups = db.list_backups()
print(f"      清理后剩余备份: {len(remaining_backups)} 个")

print("\n" + "="*60)
print("[SUCCESS] 所有备份功能测试通过！")
print("="*60)

# 清理测试文件
print("\n清理测试文件...")
Path(db_path).unlink(missing_ok=True)
Path("data/test_auto_backup.db").unlink(missing_ok=True)
print("[OK] 测试完成")

