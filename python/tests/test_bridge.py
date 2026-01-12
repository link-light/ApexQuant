"""
Day 1 测试：C++ 与 Python 桥接测试
测试核心数据结构和工具函数
"""

import sys
import os

# 确保能找到 apexquant 模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    import apexquant as aq
except ImportError as e:
    print(f"错误: 无法导入 apexquant 模块")
    print(f"详情: {e}")
    print("\n请先编译 C++ 模块:")
    print("  mkdir build && cd build")
    print("  cmake ..")
    print("  cmake --build . --config Release")
    sys.exit(1)


def test_system_info():
    """测试系统信息"""
    print("\n" + "="*60)
    print("测试 1: 系统信息")
    print("="*60)
    
    aq.print_info()
    
    if not aq.is_core_loaded():
        print("❌ C++ 核心模块未加载")
        return False
    
    print("✓ C++ 核心模块加载成功")
    return True


def test_tick_structure():
    """测试 Tick 数据结构"""
    print("\n" + "="*60)
    print("测试 2: Tick 数据结构")
    print("="*60)
    
    # 创建 Tick
    tick = aq.Tick(
        symbol="600519.SH",
        timestamp=1704067200000,  # 2024-01-01 00:00:00
        last_price=1800.50,
        bid_price=1800.30,
        ask_price=1800.70,
        volume=1000000
    )
    
    print(f"Tick 对象: {tick}")
    print(f"  证券代码: {tick.symbol}")
    print(f"  最新价: {tick.last_price}")
    print(f"  中间价: {tick.mid_price()}")
    print(f"  买卖价差: {tick.spread()}")
    
    assert tick.symbol == "600519.SH"
    assert tick.last_price == 1800.50
    assert abs(tick.mid_price() - 1800.50) < 1e-6
    assert abs(tick.spread() - 0.40) < 1e-6
    
    print("✓ Tick 数据结构测试通过")
    return True


def test_bar_structure():
    """测试 Bar 数据结构"""
    print("\n" + "="*60)
    print("测试 3: Bar 数据结构")
    print("="*60)
    
    # 创建 Bar (阳线)
    bar = aq.Bar(
        symbol="600519.SH",
        timestamp=1704067200000,
        open=1800.0,
        high=1850.0,
        low=1790.0,
        close=1820.0,
        volume=5000000
    )
    
    print(f"Bar 对象: {bar}")
    print(f"  OHLC: O={bar.open}, H={bar.high}, L={bar.low}, C={bar.close}")
    print(f"  涨跌幅: {bar.change_rate():.2%}")
    print(f"  是否阳线: {bar.is_bullish()}")
    print(f"  实体大小: {bar.body_size()}")
    print(f"  上影线: {bar.upper_shadow()}")
    print(f"  下影线: {bar.lower_shadow()}")
    
    assert bar.symbol == "600519.SH"
    assert bar.is_bullish()
    assert abs(bar.change_rate() - 0.011111) < 1e-5
    assert bar.body_size() == 20.0
    assert bar.upper_shadow() == 30.0
    assert bar.lower_shadow() == 10.0
    
    print("✓ Bar 数据结构测试通过")
    return True


def test_position_structure():
    """测试 Position 数据结构"""
    print("\n" + "="*60)
    print("测试 4: Position 数据结构")
    print("="*60)
    
    # 创建持仓
    pos = aq.Position(
        symbol="600519.SH",
        quantity=1000,
        avg_price=1800.0
    )
    
    # 更新市值
    current_price = 1850.0
    pos.update_market_value(current_price)
    
    print(f"Position 对象: {pos}")
    print(f"  证券代码: {pos.symbol}")
    print(f"  持仓数量: {pos.quantity}")
    print(f"  平均成本: {pos.avg_price}")
    print(f"  当前市值: {pos.market_value}")
    print(f"  未实现盈亏: {pos.unrealized_pnl}")
    print(f"  是否多头: {pos.is_long()}")
    print(f"  是否空仓: {pos.is_flat()}")
    
    assert pos.is_long()
    assert not pos.is_flat()
    assert pos.market_value == 1850000.0
    assert pos.unrealized_pnl == 50000.0
    
    print("✓ Position 数据结构测试通过")
    return True


def test_order_structure():
    """测试 Order 数据结构"""
    print("\n" + "="*60)
    print("测试 5: Order 数据结构")
    print("="*60)
    
    # 创建限价买单
    order = aq.Order(
        symbol="600519.SH",
        side=aq.OrderSide.BUY,
        quantity=1000,
        price=1800.0
    )
    
    order.order_id = "ORDER_001"
    order.status = aq.OrderStatus.PARTIAL_FILLED
    order.filled_quantity = 600
    order.filled_avg_price = 1799.5
    
    print(f"Order 对象: {order}")
    print(f"  订单ID: {order.order_id}")
    print(f"  证券代码: {order.symbol}")
    print(f"  方向: {'买入' if order.side == aq.OrderSide.BUY else '卖出'}")
    print(f"  类型: {order.type}")
    print(f"  状态: {order.status}")
    print(f"  委托数量: {order.quantity}")
    print(f"  已成交: {order.filled_quantity}")
    print(f"  剩余数量: {order.remaining_quantity()}")
    print(f"  成交率: {order.fill_ratio():.1%}")
    print(f"  是否活跃: {order.is_active()}")
    
    assert order.symbol == "600519.SH"
    assert order.side == aq.OrderSide.BUY
    assert order.type == aq.OrderType.LIMIT
    assert order.remaining_quantity() == 400
    assert abs(order.fill_ratio() - 0.6) < 1e-6
    assert order.is_active()
    
    print("✓ Order 数据结构测试通过")
    return True


def test_mean_calculation():
    """测试均值计算"""
    print("\n" + "="*60)
    print("测试 6: C++ 均值计算")
    print("="*60)
    
    # 测试数据
    data = [1.0, 2.0, 3.0, 4.0, 5.0]
    
    # 调用 C++ 函数
    mean = aq.calculate_mean(data)
    
    print(f"输入数据: {data}")
    print(f"均值 (C++ 计算): {mean}")
    
    # 验证结果
    expected = sum(data) / len(data)
    print(f"均值 (Python 验证): {expected}")
    
    assert abs(mean - expected) < 1e-10
    assert mean == 3.0
    
    print("✓ 均值计算测试通过")
    return True


def test_statistical_functions():
    """测试其他统计函数"""
    print("\n" + "="*60)
    print("测试 7: 其他统计函数")
    print("="*60)
    
    data = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
    
    # 标准差
    std = aq.calculate_std(data)
    print(f"标准差: {std:.4f}")
    assert abs(std - 3.0277) < 0.01
    
    # 最大值/最小值
    max_val = aq.calculate_max(data)
    min_val = aq.calculate_min(data)
    print(f"最大值: {max_val}, 最小值: {min_val}")
    assert max_val == 10.0
    assert min_val == 1.0
    
    # 中位数
    median = aq.calculate_median(data)
    print(f"中位数: {median}")
    assert median == 5.5
    
    # 累积和
    cumsum = aq.cumulative_sum(data)
    print(f"累积和: {cumsum}")
    assert cumsum[-1] == 55.0
    
    # 滚动均值
    rolling = aq.rolling_mean(data, 3)
    print(f"滚动均值(窗口=3): {rolling}")
    assert abs(rolling[0] - 2.0) < 1e-10
    
    # 百分比变化
    pct = aq.pct_change(data)
    print(f"百分比变化: {pct[:3]}")  # 只打印前3个
    assert abs(pct[0] - 1.0) < 1e-10  # (2-1)/1 = 1.0
    
    print("✓ 统计函数测试通过")
    return True


def test_correlation():
    """测试相关性计算"""
    print("\n" + "="*60)
    print("测试 8: 相关性计算")
    print("="*60)
    
    x = [1.0, 2.0, 3.0, 4.0, 5.0]
    y = [2.0, 4.0, 6.0, 8.0, 10.0]  # 完全正相关
    
    # 协方差
    cov = aq.calculate_covariance(x, y)
    print(f"协方差: {cov:.4f}")
    
    # 相关系数
    corr = aq.calculate_correlation(x, y)
    print(f"相关系数: {corr:.4f}")
    
    # 完全正相关，相关系数应该为 1.0
    assert abs(corr - 1.0) < 1e-10
    
    print("✓ 相关性计算测试通过")
    return True


def test_performance():
    """性能测试：对比 C++ 和 Python"""
    print("\n" + "="*60)
    print("测试 9: 性能对比")
    print("="*60)
    
    import time
    import random
    
    # 生成大量数据
    n = 1000000
    data = [random.random() * 100 for _ in range(n)]
    
    print(f"数据量: {n:,} 个浮点数")
    
    # C++ 计算
    start = time.time()
    cpp_mean = aq.calculate_mean(data)
    cpp_time = time.time() - start
    print(f"C++ 计算均值: {cpp_mean:.6f}, 耗时: {cpp_time*1000:.2f} ms")
    
    # Python 计算
    start = time.time()
    py_mean = sum(data) / len(data)
    py_time = time.time() - start
    print(f"Python 计算均值: {py_mean:.6f}, 耗时: {py_time*1000:.2f} ms")
    
    # 加速比
    speedup = py_time / cpp_time
    print(f"加速比: {speedup:.1f}x")
    
    # 验证结果一致
    assert abs(cpp_mean - py_mean) < 1e-6
    
    print("✓ 性能测试完成")
    return True


def run_all_tests():
    """运行所有测试"""
    print("\n")
    print("╔" + "═"*58 + "╗")
    print("║" + " "*10 + "ApexQuant Day 1 桥接测试" + " "*23 + "║")
    print("╚" + "═"*58 + "╝")
    
    tests = [
        test_system_info,
        test_tick_structure,
        test_bar_structure,
        test_position_structure,
        test_order_structure,
        test_mean_calculation,
        test_statistical_functions,
        test_correlation,
        test_performance,
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
                print(f"❌ {test_func.__name__} 失败")
        except Exception as e:
            failed += 1
            print(f"❌ {test_func.__name__} 异常: {e}")
            import traceback
            traceback.print_exc()
    
    # 总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    print(f"通过: {passed}/{len(tests)}")
    print(f"失败: {failed}/{len(tests)}")
    
    if failed == 0:
        print("\n🎉 所有测试通过！Day 1 任务完成！")
        print("="*60)
        return True
    else:
        print(f"\n⚠️  有 {failed} 个测试失败")
        print("="*60)
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

