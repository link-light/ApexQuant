"""
Day 4 示例：技术指标和因子工程
"""

import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'python'))

import apexquant as aq
from apexquant.data import DataManager
from apexquant.strategy import FactorEngine, AIFactorGenerator
from apexquant.strategy.ml_model import MultiFactorModel
import pandas as pd


def main():
    print("=" * 60)
    print("Day 4 示例：高性能技术指标 + AI 因子挖掘")
    print("=" * 60)
    
    os.environ['DEEPSEEK_API_KEY'] = 'sk-eea85ceb681c46a3bfbd4903a44ecc2d'
    
    # 1. 获取数据
    print("\n[1/4] 获取股票数据...")
    manager = DataManager(data_dir="data")
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=180)
    
    df = manager.fetch_and_store_bars(
        symbol='600519.SH',
        start_date=start_date.strftime('%Y%m%d'),
        end_date=end_date.strftime('%Y%m%d')
    )
    
    print(f"✓ 获取 {len(df)} 条数据")
    
    # 2. 计算技术指标（C++ 加速）
    print("\n[2/4] 计算技术指标 (C++ 加速)...")
    engine = FactorEngine(use_cpp=aq.is_core_loaded())
    
    df = engine.calculate_all_indicators(df)
    df = engine.calculate_custom_factors(df)
    
    print(f"✓ 计算了 {len(df.columns) - 8} 个指标和因子")
    
    # 显示
    print("\n技术指标样本 (最近5天):")
    cols = ['date', 'close', 'MA5', 'MA20', 'RSI14', 'MACD', 'K', 'D']
    cols = [c for c in cols if c in df.columns]
    print(df[cols].tail().to_string(index=False))
    
    # 3. XGBoost 模型训练
    print("\n[3/4] XGBoost 多因子模型训练...")
    model = MultiFactorModel()
    
    X, y = model.prepare_training_data(df, forward_days=5)
    results = model.train(X, y)
    
    print(f"  测试准确率: {results['test_accuracy']:.2%}")
    print(f"  测试精确率: {results['test_precision']:.2%}")
    
    print("\n  Top 5 重要特征:")
    for i, (feat, imp) in enumerate(model.get_top_features(5), 1):
        print(f"    {i}. {feat}: {imp:.4f}")
    
    # 保存模型
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    model.save(str(output_dir / "factor_model.pkl"))
    
    # 4. AI 因子推荐
    print("\n[4/4] AI 因子推荐...")
    try:
        generator = AIFactorGenerator()
        factors = generator.suggest_factors(df, market_condition='normal')
        
        if factors:
            print(f"  AI 推荐的因子:")
            for i, factor in enumerate(factors[:3], 1):
                print(f"    {i}. {factor}")
    except:
        print("  (跳过 - 需要 API)")
    
    print("\n" + "=" * 60)
    print("✓ Day 4 示例完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()

