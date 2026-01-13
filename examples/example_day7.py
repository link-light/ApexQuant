"""
Day 7 示例：完整风险评估流程
"""

import sys
import os
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'python'))

from apexquant.risk import RiskCalculator, RiskReporter, StressTestGenerator
from apexquant.backtest import MAStrategy, BacktestRunner
from apexquant.data import AKShareWrapper


def main():
    """完整风险评估示例"""
    
    print("=" * 80)
    print("ApexQuant - Day 7: 完整风险评估流程")
    print("=" * 80)
    
    # ==================== 1. 准备数据 ====================
    print("\n【步骤 1：准备数据】")
    
    wrapper = AKShareWrapper()
    symbol = "600519"  # 贵州茅台
    
    print(f"获取股票 {symbol} 数据...")
    df = wrapper.get_historical_data(symbol, start_date="2022-01-01", end_date="2024-01-01")
    
    if df is None or df.empty:
        print("⚠ 数据获取失败，使用模拟数据")
        # 生成模拟数据
        dates = pd.date_range(start='2022-01-01', end='2024-01-01', freq='D')
        np.random.seed(42)
        prices = 100 * np.exp(np.cumsum(np.random.normal(0.0005, 0.02, len(dates))))
        
        df = pd.DataFrame({
            'date': dates,
            'open': prices * 0.99,
            'high': prices * 1.02,
            'low': prices * 0.98,
            'close': prices,
            'volume': np.random.randint(1000000, 10000000, len(dates))
        })
    
    print(f"✓ 数据加载完成，共 {len(df)} 条记录")
    
    # ==================== 2. 运行回测 ====================
    print("\n【步骤 2：运行回测】")
    
    runner = BacktestRunner(
        initial_capital=100000,
        commission_rate=0.0003
    )
    
    strategy = MAStrategy(short_window=10, long_window=30)
    result = runner.run(strategy, df, symbol=symbol)
    
    print(f"\n基础回测结果:")
    print(f"  总收益率: {result.total_return:.2%}")
    print(f"  年化收益率: {result.annual_return:.2%}")
    print(f"  夏普比率: {result.sharpe_ratio:.3f}")
    print(f"  最大回撤: {result.max_drawdown:.2%}")
    
    # ==================== 3. 风险指标计算 ====================
    print("\n【步骤 3：计算完整风险指标】")
    
    calculator = RiskCalculator(use_cpp=True)
    
    # 生成基准收益率（模拟沪深300）
    np.random.seed(123)
    benchmark_returns = list(np.random.normal(0.0003, 0.015, len(result.daily_returns)))
    
    metrics = calculator.calculate_all_metrics(result, benchmark_returns)
    
    print("\n【收益指标】")
    print(f"  总收益率: {metrics['total_return']:.2%}")
    print(f"  年化收益率: {metrics['annual_return']:.2%}")
    print(f"  夏普比率: {metrics['sharpe_ratio']:.3f}")
    print(f"  Sortino 比率: {metrics['sortino_ratio']:.3f}")
    print(f"  Calmar 比率: {metrics['calmar_ratio']:.3f}")
    print(f"  Omega 比率: {metrics['omega_ratio']:.3f}")
    
    print("\n【风险指标】")
    print(f"  最大回撤: {metrics['max_drawdown']:.2%}")
    print(f"  回撤持续: {metrics['max_dd_duration']} 天")
    print(f"  VaR (95%): {metrics['var_95']:.2%}")
    print(f"  CVaR (95%): {metrics['cvar_95']:.2%}")
    print(f"  VaR (99%): {metrics['var_99']:.2%}")
    print(f"  CVaR (99%): {metrics['cvar_99']:.2%}")
    
    print("\n【相对表现】")
    print(f"  Alpha: {metrics.get('alpha', 0):.2%}")
    print(f"  Beta: {metrics.get('beta', 0):.3f}")
    print(f"  信息比率: {metrics.get('information_ratio', 0):.3f}")
    
    print("\n【交易统计】")
    print(f"  胜率: {metrics['win_rate']:.2%}")
    print(f"  盈亏比: {metrics['profit_loss_ratio']:.2f}")
    print(f"  尾部比率: {metrics['tail_ratio']:.2f}")
    
    risk_level = calculator.get_risk_level(metrics)
    print(f"\n【风险等级】: {risk_level.upper()}")
    
    # ==================== 4. AI 风险报告 ====================
    print("\n" + "=" * 80)
    print("【步骤 4：生成 AI 风险评估报告】")
    print("=" * 80)
    
    reporter = RiskReporter()
    report = reporter.generate_risk_report(metrics, "MA 双均线策略")
    print(report)
    
    # ==================== 5. 风险控制建议 ====================
    print("\n" + "=" * 80)
    print("【步骤 5：风险控制建议】")
    print("=" * 80)
    
    suggestions = reporter.suggest_risk_controls(metrics)
    print(suggestions)
    
    # ==================== 6. 压力测试 ====================
    print("\n" + "=" * 80)
    print("【步骤 6：压力测试】")
    print("=" * 80)
    
    stress_tester = StressTestGenerator()
    
    # 生成压力测试场景
    scenarios = stress_tester.generate_scenarios()
    print(f"\n生成 {len(scenarios)} 个压力测试场景\n")
    
    # 运行压力测试
    stress_results = []
    
    for i, scenario in enumerate(scenarios[:3], 1):  # 仅测试前3个场景
        print(f"{i}. 场景: {scenario['name']}")
        print(f"   描述: {scenario['description']}")
        
        # 应用场景
        stressed_data = stress_tester.apply_scenario(df, scenario)
        
        # 运行回测
        try:
            strategy = MAStrategy(short_window=10, long_window=30)
            stressed_result = runner.run(strategy, stressed_data, symbol=symbol)
            
            stress_results.append({
                'scenario': scenario['name'],
                'return': stressed_result.total_return,
                'max_dd': stressed_result.max_drawdown,
                'sharpe': stressed_result.sharpe_ratio
            })
            
            print(f"   收益率: {stressed_result.total_return:.2%}")
            print(f"   最大回撤: {stressed_result.max_drawdown:.2%}")
            print(f"   夏普比率: {stressed_result.sharpe_ratio:.3f}")
            
        except Exception as e:
            print(f"   ⚠ 压力测试失败: {e}")
        
        print()
    
    # ==================== 7. AI 场景生成 ====================
    print("=" * 80)
    print("【步骤 7：AI 生成压力测试场景】")
    print("=" * 80)
    
    ai_scenarios = stress_tester.ai_generate_scenarios(
        "当前A股市场处于震荡行情，成交量萎缩，市场情绪谨慎"
    )
    print(ai_scenarios)
    
    # ==================== 8. 综合评估 ====================
    print("\n" + "=" * 80)
    print("【综合风险评估总结】")
    print("=" * 80)
    
    print(f"""
策略风险概况：
- 风险等级: {risk_level.upper()}
- 收益/风险比: {metrics['annual_return'] / max(metrics['max_drawdown'], 0.001):.2f}
- 极端风险 (99% CVaR): {metrics['cvar_99']:.2%}

压力测试表现:
""")
    
    for res in stress_results:
        print(f"- {res['scenario']}: 收益 {res['return']:.2%}, 回撤 {res['max_dd']:.2%}")
    
    print("\n" + "=" * 80)
    print("风险评估完成！")
    print("=" * 80)


if __name__ == "__main__":
    main()

