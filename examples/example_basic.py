"""
ApexQuant 基础示例
演示如何使用核心数据结构和工具函数
"""

import sys
import os

# 添加 Python 包路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'python'))

import apexquant as aq
from datetime import datetime


def example_1_statistical_functions():
    """示例 1: 统计函数"""
    print("=" * 60)
    print("示例 1: 统计函数")
    print("=" * 60)
    
    # 模拟股票价格数据
    prices = [100.0, 102.5, 101.8, 105.2, 103.9, 
              106.5, 108.2, 107.5, 110.0, 109.2]
    
    print(f"价格序列: {prices}")
    print(f"均值: {aq.calculate_mean(prices):.2f}")
    print(f"标准差: {aq.calculate_std(prices):.2f}")
    print(f"最高价: {aq.calculate_max(prices):.2f}")
    print(f"最低价: {aq.calculate_min(prices):.2f}")
    print(f"中位数: {aq.calculate_median(prices):.2f}")
    
    # 计算收益率
    returns = aq.pct_change(prices)
    print(f"\n收益率: {[f'{r:.2%}' for r in returns[:5]]}...")
    print(f"平均收益率: {aq.calculate_mean(returns):.2%}")
    print()


def example_2_tick_data():
    """示例 2: Tick 数据"""
    print("=" * 60)
    print("示例 2: Tick 数据处理")
    print("=" * 60)
    
    # 创建 Tick 快照
    tick = aq.Tick(
        symbol="600519.SH",
        timestamp=int(datetime.now().timestamp() * 1000),
        last_price=1820.50,
        bid_price=1820.30,
        ask_price=1820.70,
        volume=5000000
    )
    
    print(f"证券代码: {tick.symbol}")
    print(f"最新价: {tick.last_price}")
    print(f"买一价: {tick.bid_price}")
    print(f"卖一价: {tick.ask_price}")
    print(f"中间价: {tick.mid_price()}")
    print(f"买卖价差: {tick.spread()}")
    print(f"成交量: {tick.volume:,}")
    print()


def example_3_bar_analysis():
    """示例 3: K 线分析"""
    print("=" * 60)
    print("示例 3: K 线分析")
    print("=" * 60)
    
    # 创建一根阳线
    bar1 = aq.Bar(
        symbol="600519.SH",
        timestamp=int(datetime.now().timestamp() * 1000),
        open=1800.0,
        high=1850.0,
        low=1790.0,
        close=1830.0,
        volume=8000000
    )
    
    print("K 线 1 (阳线):")
    print(f"  OHLC: {bar1.open}, {bar1.high}, {bar1.low}, {bar1.close}")
    print(f"  涨跌幅: {bar1.change_rate():.2%}")
    print(f"  是否阳线: {bar1.is_bullish()}")
    print(f"  实体大小: {bar1.body_size():.2f}")
    print(f"  上影线: {bar1.upper_shadow():.2f}")
    print(f"  下影线: {bar1.lower_shadow():.2f}")
    
    # 创建一根阴线
    bar2 = aq.Bar(
        symbol="600519.SH",
        timestamp=int(datetime.now().timestamp() * 1000),
        open=1830.0,
        high=1835.0,
        low=1800.0,
        close=1810.0,
        volume=6000000
    )
    
    print("\nK 线 2 (阴线):")
    print(f"  OHLC: {bar2.open}, {bar2.high}, {bar2.low}, {bar2.close}")
    print(f"  涨跌幅: {bar2.change_rate():.2%}")
    print(f"  是否阳线: {bar2.is_bullish()}")
    print()


def example_4_position_management():
    """示例 4: 持仓管理"""
    print("=" * 60)
    print("示例 4: 持仓管理")
    print("=" * 60)
    
    # 创建多头持仓
    pos = aq.Position(
        symbol="600519.SH",
        quantity=1000,
        avg_price=1800.0
    )
    
    print(f"初始持仓: {pos.quantity} 股，成本 {pos.avg_price}")
    
    # 模拟价格变化
    prices = [1800.0, 1820.0, 1850.0, 1830.0, 1880.0]
    
    print("\n价格变化及盈亏:")
    for price in prices:
        pos.update_market_value(price)
        pnl_pct = (pos.unrealized_pnl / (pos.avg_price * pos.quantity)) * 100
        print(f"  价格 {price}: 市值 {pos.market_value:,.0f}, "
              f"未实现盈亏 {pos.unrealized_pnl:+,.0f} ({pnl_pct:+.2f}%)")
    print()


def example_5_order_flow():
    """示例 5: 订单流"""
    print("=" * 60)
    print("示例 5: 订单流模拟")
    print("=" * 60)
    
    # 创建买单
    order = aq.Order(
        symbol="600519.SH",
        side=aq.OrderSide.BUY,
        quantity=1000,
        price=1820.0  # 限价单
    )
    
    order.order_id = "ORDER_20260112_001"
    
    print(f"订单 ID: {order.order_id}")
    print(f"证券: {order.symbol}")
    print(f"方向: {'买入' if order.side == aq.OrderSide.BUY else '卖出'}")
    print(f"类型: {order.type.name}")
    print(f"委托数量: {order.quantity}")
    print(f"委托价格: {order.price}")
    
    # 模拟部分成交
    print("\n模拟订单成交过程:")
    
    fills = [
        (300, 1819.8),
        (400, 1820.0),
        (300, 1820.2),
    ]
    
    for fill_qty, fill_price in fills:
        order.filled_quantity += fill_qty
        # 更新成交均价
        total_value = order.filled_avg_price * (order.filled_quantity - fill_qty)
        total_value += fill_price * fill_qty
        order.filled_avg_price = total_value / order.filled_quantity
        
        order.status = (aq.OrderStatus.FILLED if order.filled_quantity >= order.quantity 
                       else aq.OrderStatus.PARTIAL_FILLED)
        
        print(f"  成交 {fill_qty} 股 @ {fill_price}, "
              f"累计 {order.filled_quantity}/{order.quantity}, "
              f"成交率 {order.fill_ratio():.1%}")
    
    print(f"\n订单最终状态: {order.status.name}")
    print(f"成交均价: {order.filled_avg_price:.2f}")
    print()


def example_6_rolling_statistics():
    """示例 6: 滚动统计"""
    print("=" * 60)
    print("示例 6: 滚动统计")
    print("=" * 60)
    
    # 模拟价格序列
    prices = [100.0, 102.0, 101.5, 103.0, 105.0, 
              104.0, 106.0, 108.0, 107.0, 110.0,
              109.0, 111.0, 113.0, 112.0, 115.0]
    
    # 计算 5 日滚动均值
    ma5 = aq.rolling_mean(prices, 5)
    
    print("价格与 5 日均线:")
    print("日期  价格    MA5")
    print("-" * 30)
    
    for i in range(len(ma5)):
        price = prices[i + 4]  # 从第 5 个价格开始
        print(f"Day {i+5:2d}  {price:6.2f}  {ma5[i]:6.2f}")
    
    print()


def example_7_correlation_analysis():
    """示例 7: 相关性分析"""
    print("=" * 60)
    print("示例 7: 相关性分析")
    print("=" * 60)
    
    # 模拟两只股票的价格
    stock_a = [100.0, 102.0, 101.0, 105.0, 107.0, 
               106.0, 110.0, 112.0, 111.0, 115.0]
    
    stock_b = [50.0, 51.0, 50.5, 52.5, 53.5, 
               53.0, 55.0, 56.0, 55.5, 57.5]
    
    # 计算相关系数
    corr = aq.calculate_correlation(stock_a, stock_b)
    cov = aq.calculate_covariance(stock_a, stock_b)
    
    print(f"股票 A 均值: {aq.calculate_mean(stock_a):.2f}")
    print(f"股票 B 均值: {aq.calculate_mean(stock_b):.2f}")
    print(f"协方差: {cov:.4f}")
    print(f"相关系数: {corr:.4f}")
    
    if corr > 0.8:
        print("→ 强正相关，两只股票走势高度一致")
    elif corr > 0.5:
        print("→ 中等正相关")
    elif corr > 0.2:
        print("→ 弱正相关")
    elif corr > -0.2:
        print("→ 几乎无相关")
    else:
        print("→ 负相关")
    
    print()


def main():
    """运行所有示例"""
    print("\n")
    print("╔" + "═"*58 + "╗")
    print("║" + " "*15 + "ApexQuant 基础示例" + " "*24 + "║")
    print("╚" + "═"*58 + "╝")
    print()
    
    # 检查核心模块
    if not aq.is_core_loaded():
        print("❌ 错误: C++ 核心模块未加载")
        print("请先编译 C++ 模块:")
        print("  Windows: build.bat")
        print("  Linux/macOS: ./build.sh")
        return
    
    print("✓ C++ 核心模块已加载\n")
    
    # 运行所有示例
    examples = [
        example_1_statistical_functions,
        example_2_tick_data,
        example_3_bar_analysis,
        example_4_position_management,
        example_5_order_flow,
        example_6_rolling_statistics,
        example_7_correlation_analysis,
    ]
    
    for example in examples:
        try:
            example()
        except Exception as e:
            print(f"❌ 示例执行失败: {e}")
            import traceback
            traceback.print_exc()
    
    print("=" * 60)
    print("所有示例执行完成！")
    print("=" * 60)
    print()


if __name__ == "__main__":
    main()

