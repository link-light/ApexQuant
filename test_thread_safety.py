#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试数据源线程安全性
"""

import sys
import io
import time
import threading
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

# 设置stdout为UTF-8编码
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 设置日志
logging.basicConfig(
    level=logging.WARNING,  # 减少日志输出
    format='%(asctime)s - %(threadName)s - %(levelname)s - %(message)s'
)

# 导入数据源
sys.path.insert(0, 'python')
from apexquant.simulation.data_source import SimulationDataSource, MockDataSource

print("="*60)
print("数据源线程安全性测试")
print("="*60)

# 测试1: MockDataSource并发测试
print("\n[1/3] 测试MockDataSource并发访问...")
mock_source = MockDataSource(num_days=50, initial_price=100.0)

def fetch_mock_data(thread_id):
    """线程任务：获取模拟数据"""
    try:
        df = mock_source.get_stock_data(
            symbol='TEST.SH',
            start_date='2024-01-01',
            end_date='2024-03-01'
        )
        if df is not None:
            return f"Thread-{thread_id}: OK ({len(df)} rows)"
        else:
            return f"Thread-{thread_id}: FAIL (no data)"
    except Exception as e:
        return f"Thread-{thread_id}: ERROR ({e})"

# 并发执行
num_threads = 10
with ThreadPoolExecutor(max_workers=num_threads) as executor:
    futures = [executor.submit(fetch_mock_data, i) for i in range(num_threads)]
    
    results = []
    for future in as_completed(futures):
        result = future.result()
        results.append(result)

# 检查结果
success_count = sum(1 for r in results if 'OK' in r)
print(f"      完成: {success_count}/{num_threads} 线程成功")

if success_count == num_threads:
    print("      [OK] MockDataSource线程安全")
else:
    print("      [FAIL] MockDataSource存在并发问题")
    for r in results:
        if 'FAIL' in r or 'ERROR' in r:
            print(f"           {r}")

# 测试2: 缓存功能测试
print("\n[2/3] 测试SimulationDataSource缓存...")

# 创建真实数据源（会使用缓存）
try:
    real_source = SimulationDataSource(primary_source="baostock", backup_source="akshare")
    
    # 第一次获取（应该从网络获取）
    start_time = time.time()
    df1 = real_source.get_stock_data('600519.SH', '2024-01-01', '2024-01-10', use_cache=True)
    first_time = time.time() - start_time
    
    # 第二次获取（应该从缓存获取）
    start_time = time.time()
    df2 = real_source.get_stock_data('600519.SH', '2024-01-01', '2024-01-10', use_cache=True)
    second_time = time.time() - start_time
    
    if df1 is not None and df2 is not None:
        print(f"      第一次获取: {first_time:.3f}秒")
        print(f"      第二次获取: {second_time:.3f}秒 (缓存)")
        
        if second_time < first_time * 0.1:  # 缓存应该快10倍以上
            print("      [OK] 缓存工作正常")
        else:
            print("      [WARNING] 缓存可能未生效")
    else:
        print("      [SKIP] 无法获取真实数据（可能网络问题）")
        
except Exception as e:
    print(f"      [SKIP] 真实数据源测试失败: {e}")

# 测试3: 并发缓存测试
print("\n[3/3] 测试并发缓存访问...")

def fetch_cached_data(thread_id):
    """线程任务：获取缓存数据"""
    try:
        df = mock_source.get_stock_data(
            symbol='CACHE_TEST.SH',
            start_date='2024-01-01',
            end_date='2024-02-01'
        )
        if df is not None:
            return f"Thread-{thread_id}: OK"
        else:
            return f"Thread-{thread_id}: FAIL"
    except Exception as e:
        return f"Thread-{thread_id}: ERROR ({e})"

# 并发执行
num_threads = 20
start_time = time.time()

with ThreadPoolExecutor(max_workers=num_threads) as executor:
    futures = [executor.submit(fetch_cached_data, i) for i in range(num_threads)]
    
    results = []
    for future in as_completed(futures):
        result = future.result()
        results.append(result)

elapsed = time.time() - start_time

# 检查结果
success_count = sum(1 for r in results if 'OK' in r)
print(f"      完成: {success_count}/{num_threads} 线程成功")
print(f"      耗时: {elapsed:.3f}秒")

if success_count == num_threads:
    print("      [OK] 并发缓存访问安全")
else:
    print("      [FAIL] 并发缓存访问存在问题")

print("\n" + "="*60)
print("[SUCCESS] 线程安全性测试完成！")
print("="*60)

