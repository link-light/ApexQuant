"""
Day 7 测试：风险评估系统
"""

import sys
import os
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from apexquant.risk import RiskCalculator, RiskReporter, StressTestGenerator


def test_risk_calculator():
    """测试风险指标计算"""
    print("=" * 60)
    print("测试 RiskCalculator")
    print("=" * 60)
    
    # 创建模拟回测结果
    class MockResult:
        def __init__(self):
            self.total_return = 0.35
            self.annual_return = 0.28
            self.sharpe_ratio = 1.85
            
            # 模拟每日收益率（250天）
            np.random.seed(42)
            self.daily_returns = list(np.random.normal(0.001, 0.02, 250))
            
            # 模拟权益曲线
            self.equity_curve = [100000.0]
            for ret in self.daily_returns:
                self.equity_curve.append(self.equity_curve[-1] * (1 + ret))
    
    result = MockResult()
    
    # 创建计算器
    calculator = RiskCalculator(use_cpp=True)
    
    # 计算所有指标
    metrics = calculator.calculate_all_metrics(result)
    
    print("\n【风险指标】")
    print(f"总收益率: {metrics['total_return']:.2%}")
    print(f"年化收益率: {metrics['annual_return']:.2%}")
    print(f"夏普比率: {metrics['sharpe_ratio']:.3f}")
    print(f"最大回撤: {metrics['max_drawdown']:.2%}")
    print(f"回撤持续: {metrics['max_dd_duration']} 天")
    print(f"VaR (95%): {metrics['var_95']:.2%}")
    print(f"CVaR (95%): {metrics['cvar_95']:.2%}")
    print(f"VaR (99%): {metrics['var_99']:.2%}")
    print(f"CVaR (99%): {metrics['cvar_99']:.2%}")
    print(f"Calmar 比率: {metrics['calmar_ratio']:.3f}")
    print(f"Sortino 比率: {metrics['sortino_ratio']:.3f}")
    print(f"Omega 比率: {metrics['omega_ratio']:.3f}")
    print(f"胜率: {metrics['win_rate']:.2%}")
    print(f"盈亏比: {metrics['profit_loss_ratio']:.2f}")
    print(f"尾部比率: {metrics['tail_ratio']:.2f}")
    
    # 风险等级
    risk_level = calculator.get_risk_level(metrics)
    print(f"\n风险等级: {risk_level.upper()}")
    
    # 添加基准收益率测试
    benchmark_returns = list(np.random.normal(0.0008, 0.015, 250))
    metrics_with_benchmark = calculator.calculate_all_metrics(result, benchmark_returns)
    
    if 'alpha' in metrics_with_benchmark:
        print(f"\n【相对表现】")
        print(f"Alpha: {metrics_with_benchmark['alpha']:.2%}")
        print(f"Beta: {metrics_with_benchmark['beta']:.3f}")
        print(f"信息比率: {metrics_with_benchmark['information_ratio']:.3f}")
    
    print("\n✓ RiskCalculator 测试完成\n")
    return metrics


def test_risk_reporter(metrics):
    """测试风险报告生成"""
    print("=" * 60)
    print("测试 RiskReporter")
    print("=" * 60)
    
    # 创建报告器
    reporter = RiskReporter()
    
    # 生成风险报告
    print("\n【生成风险评估报告】")
    report = reporter.generate_risk_report(metrics, "MA 双均线策略")
    print(report)
    
    # 风险控制建议
    print("\n" + "=" * 60)
    print("【风险控制建议】")
    suggestions = reporter.suggest_risk_controls(metrics)
    print(suggestions)
    
    print("\n✓ RiskReporter 测试完成\n")


def test_stress_test():
    """测试压力测试"""
    print("=" * 60)
    print("测试 StressTestGenerator")
    print("=" * 60)
    
    # 创建生成器
    generator = StressTestGenerator()
    
    # 生成场景
    scenarios = generator.generate_scenarios()
    
    print(f"\n共生成 {len(scenarios)} 个压力测试场景:\n")
    for i, scenario in enumerate(scenarios, 1):
        print(f"{i}. {scenario['name']}")
        print(f"   描述: {scenario['description']}")
        print(f"   冲击: {scenario['shock']:.1%}")
        print(f"   波动率倍数: {scenario['volatility_multiplier']:.1f}x")
        print(f"   持续时间: {scenario['duration']} 天")
        print()
    
    # AI 生成场景
    print("=" * 60)
    print("【AI 生成压力测试场景】")
    ai_scenarios = generator.ai_generate_scenarios(
        "2024年A股市场，科技股领涨，成交量温和放大"
    )
    print(ai_scenarios)
    
    print("\n✓ StressTestGenerator 测试完成\n")


def test_cpp_risk_metrics():
    """测试 C++ 风险指标"""
    print("=" * 60)
    print("测试 C++ 风险指标")
    print("=" * 60)
    
    try:
        import apexquant_core as aq
        
        # 测试数据
        returns = [0.01, -0.02, 0.015, -0.005, 0.02, -0.03, 0.01, 0.005, -0.01, 0.008]
        equity_curve = [100, 101, 99, 100.5, 100, 102, 99, 100, 99.5, 100]
        
        print("\n【C++ 风险指标计算】")
        print(f"VaR (95%): {aq.risk.value_at_risk(returns, 0.95):.4f}")
        print(f"CVaR (95%): {aq.risk.conditional_var(returns, 0.95):.4f}")
        print(f"最大回撤: {aq.risk.max_drawdown(equity_curve):.4f}")
        print(f"Sortino: {aq.risk.sortino_ratio(returns, 0.0, 252):.4f}")
        print(f"Omega: {aq.risk.omega_ratio(returns, 0.0):.4f}")
        print(f"胜率: {aq.risk.win_rate(returns):.2%}")
        print(f"盈亏比: {aq.risk.profit_loss_ratio(returns):.2f}")
        print(f"尾部比率: {aq.risk.tail_ratio(returns, 0.95):.2f}")
        
        print("\n✓ C++ 风险指标测试完成\n")
        
    except ImportError:
        print("⚠ C++ 核心未编译，跳过测试\n")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print(" Day 7 - 风险评估系统测试")
    print("=" * 60 + "\n")
    
    # 测试 C++ 风险指标
    test_cpp_risk_metrics()
    
    # 测试风险计算器
    metrics = test_risk_calculator()
    
    # 测试风险报告生成
    test_risk_reporter(metrics)
    
    # 测试压力测试
    test_stress_test()
    
    print("=" * 60)
    print(" 所有测试完成！")
    print("=" * 60)

