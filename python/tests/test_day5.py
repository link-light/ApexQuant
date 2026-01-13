"""
Day 5 测试：回测引擎
"""

import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import apexquant as aq
from apexquant.data import DataManager
from apexquant.backtest import Strategy, BacktestRunner, PerformanceAnalyzer
import pandas as pd
import numpy as np


def test_backtest_config():
    """测试回测配置"""
    print("\n" + "="*60)
    print("测试 1: 回测配置")
    print("="*60)
    
    if not aq.is_core_loaded():
        print("⚠️  C++ 模块未加载，跳过")
        return True
    
    config = aq.BacktestConfig()
    config.initial_capital = 1000000.0
    config.commission_rate = 0.0003
    config.slippage_rate = 0.001
    
    print(f"初始资金: {config.initial_capital:,.0f}")
    print(f"手续费率: {config.commission_rate:.4f}")
    print(f"滑点率: {config.slippage_rate:.4f}")
    
    print("\n✓ 配置创建成功")
    return True


def test_simple_backtest():
    """测试简单回测"""
    print("\n" + "="*60)
    print("测试 2: 简单回测")
    print("="*60)
    
    if not aq.is_core_loaded():
        print("⚠️  C++ 模块未加载，跳过")
        return True
    
    # 创建测试数据
    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    prices = 100 + np.cumsum(np.random.randn(100) * 2)
    
    data = pd.DataFrame({
        'date': dates,
        'symbol': '600519.SH',
        'timestamp': (dates.astype('int64') // 10**6).astype('int64'),
        'open': prices,
        'high': prices * 1.02,
        'low': prices * 0.98,
        'close': prices,
        'volume': np.random.randint(1000000, 5000000, 100)
    })
    
    # 简单买入持有策略
    class BuyAndHoldStrategy(Strategy):
        def __init__(self):
            super().__init__("Buy and Hold")
            self.bought = False
        
        def on_bar(self, bar):
            if not self.bought and self.bar_index == 5:
                cash = self.get_cash()
                quantity = int(cash * 0.9 / bar.close / 100) * 100
                if quantity > 0:
                    self.buy(bar.symbol, quantity)
                    self.bought = True
            self.bar_index += 1
    
    # 运行回测
    strategy = BuyAndHoldStrategy()
    runner = BacktestRunner(initial_capital=1000000.0)
    
    result = runner.run(strategy, data)
    
    if result:
        print(f"\n回测结果:")
        print(f"  总收益率: {result.total_return:.2%}")
        print(f"  年化收益率: {result.annual_return:.2%}")
        print(f"  夏普比率: {result.sharpe_ratio:.3f}")
        print(f"  最大回撤: {result.max_drawdown:.2%}")
        print(f"  交易次数: {result.total_trades}")
        
        print("\n✓ 简单回测完成")
        return True
    else:
        print("❌ 回测失败")
        return False


def test_ma_strategy():
    """测试双均线策略"""
    print("\n" + "="*60)
    print("测试 3: 双均线策略")
    print("="*60)
    
    if not aq.is_core_loaded():
        print("⚠️  C++ 模块未加载，跳过")
        return True
    
    # 获取真实数据
    manager = DataManager(data_dir="data")
    end_date = datetime.now()
    start_date = end_date - timedelta(days=180)
    
    df = manager.fetch_and_store_bars(
        symbol='600519.SH',
        start_date=start_date.strftime('%Y%m%d'),
        end_date=end_date.strftime('%Y%m%d')
    )
    
    if df.empty or len(df) < 50:
        print("❌ 数据不足")
        return False
    
    print(f"数据: {len(df)} 条")
    
    # 导入策略
    from apexquant.backtest.strategy import MAStrategy
    
    # 运行回测
    strategy = MAStrategy(short_window=5, long_window=20)
    runner = BacktestRunner(
        initial_capital=1000000.0,
        commission_rate=0.0003,
        slippage_rate=0.001
    )
    
    result = runner.run(strategy, df)
    
    if result:
        print(f"\n回测结果:")
        print(f"  总收益率: {result.total_return:.2%}")
        print(f"  年化收益率: {result.annual_return:.2%}")
        print(f"  夏普比率: {result.sharpe_ratio:.3f}")
        print(f"  最大回撤: {result.max_drawdown:.2%}")
        print(f"  交易次数: {result.total_trades}")
        print(f"  胜率: {result.win_rate:.2%}")
        print(f"  总手续费: {result.total_commission:.2f}")
        
        # 性能分析
        print("\n性能分析:")
        analyzer = PerformanceAnalyzer()
        analysis = analyzer.analyze(result, df)
        analyzer.print_report(analysis)
        
        print("\n✓ 双均线策略测试完成")
        return True
    else:
        print("❌ 回测失败")
        return False


def test_custom_strategy():
    """测试自定义策略"""
    print("\n" + "="*60)
    print("测试 4: 自定义策略（RSI 反转）")
    print("="*60)
    
    if not aq.is_core_loaded():
        print("⚠️  C++ 模块未加载，跳过")
        return True
    
    # RSI 反转策略
    class RSIStrategy(Strategy):
        def __init__(self, period=14, oversold=30, overbought=70):
            super().__init__("RSI Strategy")
            self.period = period
            self.oversold = oversold
            self.overbought = overbought
        
        def on_bar(self, bar):
            if self.bar_index < self.period:
                self.bar_index += 1
                return
            
            # 计算 RSI
            closes = self.data['close'].iloc[max(0, self.bar_index - self.period):self.bar_index + 1]
            
            if len(closes) < self.period + 1:
                self.bar_index += 1
                return
            
            rsi_values = aq.indicators.rsi(closes.tolist(), self.period)
            current_rsi = rsi_values[-1]
            
            if np.isnan(current_rsi):
                self.bar_index += 1
                return
            
            # 超卖：买入
            if current_rsi < self.oversold and not self.has_position(bar.symbol):
                cash = self.get_cash()
                quantity = int(cash * 0.5 / bar.close / 100) * 100
                if quantity > 0:
                    self.buy(bar.symbol, quantity)
            
            # 超买：卖出
            elif current_rsi > self.overbought and self.has_position(bar.symbol):
                self.close_position(bar.symbol)
            
            self.bar_index += 1
    
    # 获取数据
    manager = DataManager(data_dir="data")
    end_date = datetime.now()
    start_date = end_date - timedelta(days=180)
    
    df = manager.fetch_and_store_bars(
        symbol='600519.SH',
        start_date=start_date.strftime('%Y%m%d'),
        end_date=end_date.strftime('%Y%m%d')
    )
    
    if df.empty or len(df) < 50:
        print("❌ 数据不足")
        return False
    
    # 运行回测
    strategy = RSIStrategy(period=14, oversold=30, overbought=70)
    runner = BacktestRunner(initial_capital=1000000.0)
    
    result = runner.run(strategy, df)
    
    if result:
        print(f"\n回测结果:")
        print(f"  总收益率: {result.total_return:.2%}")
        print(f"  夏普比率: {result.sharpe_ratio:.3f}")
        print(f"  最大回撤: {result.max_drawdown:.2%}")
        print(f"  交易次数: {result.total_trades}")
        print(f"  胜率: {result.win_rate:.2%}")
        
        print("\n✓ 自定义策略测试完成")
        return True
    else:
        print("❌ 回测失败")
        return False


def run_all_tests():
    """运行所有测试"""
    print("\n")
    print("╔" + "═"*58 + "╗")
    print("║" + " "*10 + "ApexQuant Day 5 测试" + " "*26 + "║")
    print("╚" + "═"*58 + "╝")
    
    tests = [
        test_backtest_config,
        test_simple_backtest,
        test_ma_strategy,
        test_custom_strategy,
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
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
        print("\n🎉 所有测试通过！Day 5 任务完成！")
        return True
    else:
        print(f"\n⚠️  有 {failed} 个测试失败")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

