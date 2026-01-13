"""
Day 5 示例：回测引擎
"""

import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'python'))

import apexquant as aq
from apexquant.data import DataManager
from apexquant.backtest import BacktestRunner, PerformanceAnalyzer
from apexquant.backtest.strategy import MAStrategy


def main():
    print("=" * 60)
    print("Day 5 示例：回测引擎 - 双均线策略")
    print("=" * 60)
    
    # 1. 获取数据
    print("\n[1/3] 获取历史数据...")
    manager = DataManager(data_dir="data")
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)  # 1年数据
    
    df = manager.fetch_and_store_bars(
        symbol='600519.SH',
        start_date=start_date.strftime('%Y%m%d'),
        end_date=end_date.strftime('%Y%m%d')
    )
    
    print(f"✓ 获取 {len(df)} 条数据")
    print(f"  时间范围: {df['date'].min()} 至 {df['date'].max()}")
    print(f"  价格范围: {df['close'].min():.2f} - {df['close'].max():.2f}")
    
    # 2. 创建策略
    print("\n[2/3] 创建双均线策略...")
    strategy = MAStrategy(short_window=5, long_window=20)
    print(f"  短期均线: {strategy.short_window} 日")
    print(f"  长期均线: {strategy.long_window} 日")
    
    # 3. 运行回测
    print("\n[3/3] 运行回测...")
    runner = BacktestRunner(
        initial_capital=1000000.0,
        commission_rate=0.0003,  # 万三手续费
        slippage_rate=0.001      # 千一滑点
    )
    
    result = runner.run(strategy, df)
    
    if result:
        # 基础结果
        print("\n" + "="*60)
        print("回测结果")
        print("="*60)
        print(f"总收益率: {result.total_return:.2%}")
        print(f"年化收益率: {result.annual_return:.2%}")
        print(f"夏普比率: {result.sharpe_ratio:.3f}")
        print(f"最大回撤: {result.max_drawdown:.2%}")
        print(f"\n交易统计:")
        print(f"  总交易次数: {result.total_trades}")
        print(f"  盈利交易: {result.winning_trades}")
        print(f"  亏损交易: {result.losing_trades}")
        print(f"  胜率: {result.win_rate:.2%}")
        print(f"\n成本统计:")
        print(f"  总手续费: {result.total_commission:.2f}")
        print(f"  总滑点: {result.total_slippage:.2f}")
        
        # 详细分析
        print("\n" + "="*60)
        print("性能分析")
        print("="*60)
        analyzer = PerformanceAnalyzer()
        analysis = analyzer.analyze(result, df)
        
        risk = analysis['risk_metrics']
        print(f"波动率: {risk['volatility']:.2%}")
        print(f"Calmar 比率: {risk['calmar_ratio']:.3f}")
        print(f"Sortino 比率: {risk['sortino_ratio']:.3f}")
        
        # 权益曲线
        print("\n权益曲线 (最近10天):")
        recent_equity = result.equity_curve[-10:]
        for i, equity in enumerate(recent_equity, 1):
            print(f"  Day {len(result.equity_curve)-10+i}: {equity:,.0f}")
        
        print("\n" + "="*60)
        print("✓ 回测完成！")
        print("="*60)
    else:
        print("❌ 回测失败")


if __name__ == "__main__":
    main()

