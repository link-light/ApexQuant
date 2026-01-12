"""
Day 3 示例：可视化 + AI 图表分析
"""

import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'python'))

from apexquant.data import DataManager
from apexquant.visualization import ChartPlotter, AIPatternAnalyzer, SimplePredictor
import pandas as pd


def main():
    print("=" * 60)
    print("Day 3 示例：AI 驱动的可视化分析")
    print("=" * 60)
    
    # 设置
    os.environ['DEEPSEEK_API_KEY'] = 'sk-eea85ceb681c46a3bfbd4903a44ecc2d'
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    # 1. 获取数据
    print("\n[1] 获取数据...")
    manager = DataManager(data_dir="data")
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)
    
    df = manager.fetch_and_store_bars(
        symbol='600519.SH',
        start_date=start_date.strftime('%Y%m%d'),
        end_date=end_date.strftime('%Y%m%d')
    )
    
    print(f"✓ 获取 {len(df)} 条数据")
    
    # 2. AI 分析
    print("\n[2] AI 图表分析...")
    analyzer = AIPatternAnalyzer()
    analysis = analyzer.analyze_chart(df)
    
    print(f"  趋势: {analysis['trend']}")
    print(f"  波动率: {analysis['volatility']:.2%}")
    if analysis.get('ai_summary'):
        print(f"\nAI 分析：\n{analysis['ai_summary']}")
    
    # 3. 生成注释
    annotations = analyzer.generate_annotations(df, analysis)
    
    # 4. 预测
    print("\n[3] 价格预测...")
    
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
    
    predictor = SimplePredictor()
    predictions, upper, lower = predictor.predict_ensemble(df, forecast_days=5)
    
    print(f"  未来 5 日预测均值: {predictions.values}")
    
    # 5. 绘制完整图表
    print("\n[4] 生成可视化图表...")
    plotter = ChartPlotter()
    
    # 基础 K 线
    plotter.plot_candlestick(
        df=df,
        title="贵州茅台 K线图",
        ma_periods=[5, 10, 20],
        save_path=str(output_dir / "day3_basic.png")
    )
    print(f"  ✓ 基础图表: {output_dir}/day3_basic.png")
    
    # 带预测
    plotter.plot_with_prediction(
        df=df,
        predictions=predictions,
        title="贵州茅台 + 预测",
        ma_periods=[5, 20],
        save_path=str(output_dir / "day3_prediction.png")
    )
    print(f"  ✓ 预测图表: {output_dir}/day3_prediction.png")
    
    # 带 AI 注释
    plotter.plot_with_annotations(
        df=df,
        annotations=annotations,
        title="贵州茅台 + AI 分析",
        ma_periods=[5, 10, 20],
        save_path=str(output_dir / "day3_ai_annotated.png")
    )
    print(f"  ✓ AI 注释图表: {output_dir}/day3_ai_annotated.png")
    
    print("\n" + "=" * 60)
    print("✓ Day 3 示例完成！")
    print(f"所有图表已保存到 {output_dir}/ 目录")
    print("=" * 60)


if __name__ == "__main__":
    main()

