"""
Day 6 示例：回测优化和 AI 分析
"""

import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'python'))

import apexquant as aq
from apexquant.data import DataManager
from apexquant.backtest import BacktestRunner
from apexquant.backtest.strategy import MAStrategy
from apexquant.backtest.optimizer import ParameterOptimizer
from apexquant.backtest.monte_carlo import MonteCarloSimulator
from apexquant.backtest.ai_analyzer import AIBacktestAnalyzer
import numpy as np


def main():
    print("=" * 60)
    print("Day 6 示例：参数优化 + 蒙特卡洛 + AI 分析")
    print("=" * 60)
    
    os.environ['DEEPSEEK_API_KEY'] = 'sk-eea85ceb681c46a3bfbd4903a44ecc2d'
    
    # 1. 获取数据
    print("\n[1/4] 获取数据...")
    manager = DataManager(data_dir="data")
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=180)
    
    df = manager.fetch_and_store_bars(
        symbol='600519.SH',
        start_date=start_date.strftime('%Y%m%d'),
        end_date=end_date.strftime('%Y%m%d')
    )
    
    print(f"✓ 获取 {len(df)} 条数据")
    
    # 2. 参数优化（网格搜索）
    print("\n[2/4] 参数优化（网格搜索）...")
    
    best_params = None
    best_score = -np.inf
    
    for sw in [3, 5, 7, 10]:
        for lw in [15, 20, 25, 30]:
            if sw >= lw:
                continue
            
            try:
                strategy = MAStrategy(short_window=sw, long_window=lw)
                runner = BacktestRunner(initial_capital=1000000.0)
                result = runner.run(strategy, df)
                
                score = result.sharpe_ratio
                
                if score > best_score:
                    best_score = score
                    best_params = {'short_window': sw, 'long_window': lw}
                    print(f"  新最佳: SW={sw}, LW={lw}, 夏普={score:.3f}")
            except:
                pass
    
    print(f"\n最佳参数: {best_params}")
    print(f"最佳夏普: {best_score:.3f}")
    
    # 3. 使用最佳参数回测
    print("\n[3/4] 使用最佳参数回测...")
    
    strategy = MAStrategy(**best_params)
    runner = BacktestRunner(initial_capital=1000000.0)
    result = runner.run(strategy, df)
    
    print(f"\n优化后表现:")
    print(f"  总收益率: {result.total_return:.2%}")
    print(f"  年化收益率: {result.annual_return:.2%}")
    print(f"  夏普比率: {result.sharpe_ratio:.3f}")
    print(f"  最大回撤: {result.max_drawdown:.2%}")
    print(f"  胜率: {result.win_rate:.2%}")
    
    # 4. 蒙特卡洛风险分析
    print("\n[4/4] 蒙特卡洛风险分析...")
    
    simulator = MonteCarloSimulator(n_simulations=200, n_days=len(df))
    
    if result.daily_returns:
        simulated_paths = simulator.simulate_from_returns(
            result.daily_returns,
            initial_value=1000000.0
        )
        
        analysis = simulator.analyze_results(simulated_paths)
        
        print(f"\n风险统计 (200次模拟):")
        print(f"  预期终值: {analysis['mean_final_value']:,.0f}")
        print(f"  5% 最差情况: {analysis['percentile_5']:,.0f}")
        print(f"  95% 最好情况: {analysis['percentile_95']:,.0f}")
        print(f"  亏损概率: {analysis['probability_loss']:.2%}")
        
        # 绘制模拟路径
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        
        simulator.plot_paths(
            n_paths=100,
            save_path=str(output_dir / "day6_monte_carlo.png")
        )
        
        print(f"\n  ✓ 模拟路径图: {output_dir}/day6_monte_carlo.png")
    
    # 5. AI 深度分析
    print("\n" + "="*60)
    print("AI 深度分析")
    print("="*60)
    
    try:
        analyzer = AIBacktestAnalyzer()
        
        analysis_report = analyzer.analyze_result(result, "优化后双均线策略")
        print(f"\n{analysis_report}")
        
    except Exception as e:
        print(f"\n⚠️  AI 分析跳过: {e}")
    
    print("\n" + "="*60)
    print("✓ Day 6 示例完成！")
    print("="*60)


if __name__ == "__main__":
    main()

