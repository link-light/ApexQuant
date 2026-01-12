"""
Day 3 测试：可视化和 AI 分析
"""

import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import apexquant as aq
from apexquant.data import DataManager
from apexquant.visualization import ChartPlotter, AIPatternAnalyzer, SimplePredictor


def test_basic_chart():
    """测试基础 K 线图"""
    print("\n" + "="*60)
    print("测试 1: 基础 K 线图绘制")
    print("="*60)
    
    # 获取数据
    manager = DataManager(data_dir="data")
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)
    
    df = manager.fetch_and_store_bars(
        symbol='600519.SH',
        start_date=start_date.strftime('%Y%m%d'),
        end_date=end_date.strftime('%Y%m%d')
    )
    
    if df.empty:
        print("❌ 数据获取失败")
        return False
    
    # 绘制
    plotter = ChartPlotter()
    
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    fig = plotter.plot_candlestick(
        df=df,
        title="贵州茅台 K线图",
        ma_periods=[5, 10, 20],
        save_path=str(output_dir / "chart_basic.png")
    )
    
    print("✓ K 线图绘制完成")
    return True


def test_ai_pattern_analysis():
    """测试 AI 模式分析"""
    print("\n" + "="*60)
    print("测试 2: AI 模式分析")
    print("="*60)
    
    # 获取数据
    manager = DataManager(data_dir="data")
    end_date = datetime.now()
    start_date = end_date - timedelta(days=60)
    
    df = manager.fetch_and_store_bars(
        symbol='600519.SH',
        start_date=start_date.strftime('%Y%m%d'),
        end_date=end_date.strftime('%Y%m%d')
    )
    
    if df.empty:
        print("❌ 数据获取失败")
        return False
    
    # AI 分析
    api_key = os.getenv('DEEPSEEK_API_KEY', 'sk-eea85ceb681c46a3bfbd4903a44ecc2d')
    analyzer = AIPatternAnalyzer(api_key)
    
    analysis = analyzer.analyze_chart(df, recent_days=20)
    
    print("\n分析结果：")
    print(f"  趋势: {analysis['trend']}")
    print(f"  波动率: {analysis['volatility']:.2%}")
    print(f"  当前价: {analysis['support_resistance']['current']:.2f}")
    print(f"  压力位: {analysis['support_resistance']['resistance']:.2f}")
    print(f"  支撑位: {analysis['support_resistance']['support']:.2f}")
    print(f"  检测形态: {', '.join(analysis['patterns']) if analysis['patterns'] else '无'}")
    
    if 'ai_summary' in analysis:
        print(f"\nAI 分析：\n{analysis['ai_summary']}")
    else:
        print(f"\n分析摘要：\n{analysis['summary']}")
    
    print("\n✓ AI 分析完成")
    return True


def test_prediction():
    """测试预测模型"""
    print("\n" + "="*60)
    print("测试 3: 价格预测")
    print("="*60)
    
    # 获取数据
    manager = DataManager(data_dir="data")
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)
    
    df = manager.fetch_and_store_bars(
        symbol='600519.SH',
        start_date=start_date.strftime('%Y%m%d'),
        end_date=end_date.strftime('%Y%m%d')
    )
    
    if df.empty:
        print("❌ 数据获取失败")
        return False
    
    # 准备索引
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
    
    # 预测
    predictor = SimplePredictor()
    
    print("\n1. 移动平均预测:")
    pred_ma = predictor.predict_ma(df, periods=5, forecast_days=5)
    print(pred_ma)
    
    print("\n2. 线性回归预测:")
    pred_linear = predictor.predict_linear(df, forecast_days=5)
    print(pred_linear)
    
    print("\n3. 趋势跟随预测:")
    pred_trend = predictor.predict_trend_following(df, forecast_days=5)
    print(pred_trend)
    
    print("\n4. 集成预测:")
    pred_mean, pred_upper, pred_lower = predictor.predict_ensemble(df, forecast_days=5)
    print(f"均值: {pred_mean.values}")
    print(f"上界: {pred_upper.values}")
    print(f"下界: {pred_lower.values}")
    
    print("\n✓ 预测完成")
    return True


def test_chart_with_prediction():
    """测试带预测的图表"""
    print("\n" + "="*60)
    print("测试 4: K 线图 + 预测")
    print("="*60)
    
    import pandas as pd
    
    # 获取数据
    manager = DataManager(data_dir="data")
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)
    
    df = manager.fetch_and_store_bars(
        symbol='600519.SH',
        start_date=start_date.strftime('%Y%m%d'),
        end_date=end_date.strftime('%Y%m%d')
    )
    
    if df.empty:
        print("❌ 数据获取失败")
        return False
    
    # 准备索引
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
    
    # 预测
    predictor = SimplePredictor()
    predictions, _, _ = predictor.predict_ensemble(df, forecast_days=5)
    
    # 绘图
    plotter = ChartPlotter()
    
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    fig = plotter.plot_with_prediction(
        df=df,
        predictions=predictions,
        title="贵州茅台 K线图 + 预测",
        ma_periods=[5, 20],
        save_path=str(output_dir / "chart_with_prediction.png")
    )
    
    print("✓ 预测图表绘制完成")
    return True


def test_chart_with_ai_annotations():
    """测试带 AI 注释的图表"""
    print("\n" + "="*60)
    print("测试 5: K 线图 + AI 注释")
    print("="*60)
    
    import pandas as pd
    
    # 获取数据
    manager = DataManager(data_dir="data")
    end_date = datetime.now()
    start_date = end_date - timedelta(days=60)
    
    df = manager.fetch_and_store_bars(
        symbol='600519.SH',
        start_date=start_date.strftime('%Y%m%d'),
        end_date=end_date.strftime('%Y%m%d')
    )
    
    if df.empty:
        print("❌ 数据获取失败")
        return False
    
    # AI 分析
    api_key = os.getenv('DEEPSEEK_API_KEY', 'sk-eea85ceb681c46a3bfbd4903a44ecc2d')
    analyzer = AIPatternAnalyzer(api_key)
    
    analysis = analyzer.analyze_chart(df, recent_days=30)
    annotations = analyzer.generate_annotations(df, analysis)
    
    print(f"\n生成了 {len(annotations)} 个注释")
    
    # 准备索引
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
    
    # 绘图
    plotter = ChartPlotter()
    
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    fig = plotter.plot_with_annotations(
        df=df,
        annotations=annotations,
        title="贵州茅台 K线图 + AI 分析",
        ma_periods=[5, 10, 20],
        save_path=str(output_dir / "chart_with_annotations.png")
    )
    
    print("✓ AI 注释图表绘制完成")
    return True


def test_comparison_chart():
    """测试多股票对比图"""
    print("\n" + "="*60)
    print("测试 6: 多股票对比")
    print("="*60)
    
    # 获取数据
    manager = DataManager(data_dir="data")
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)
    
    symbols = ['600519.SH', '000858.SZ']  # 茅台、五粮液
    data_dict = manager.get_multiple_stocks(
        symbols=symbols,
        start_date=start_date.strftime('%Y%m%d'),
        end_date=end_date.strftime('%Y%m%d')
    )
    
    if not data_dict:
        print("❌ 数据获取失败")
        return False
    
    # 绘图
    plotter = ChartPlotter()
    
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    fig = plotter.plot_comparison(
        data_dict=data_dict,
        title="白酒板块对比（贵州茅台 vs 五粮液）",
        normalize=True,
        save_path=str(output_dir / "chart_comparison.png")
    )
    
    print("✓ 对比图绘制完成")
    return True


def run_all_tests():
    """运行所有测试"""
    print("\n")
    print("╔" + "═"*58 + "╗")
    print("║" + " "*10 + "ApexQuant Day 3 测试" + " "*26 + "║")
    print("╚" + "═"*58 + "╝")
    
    import pandas as pd
    
    tests = [
        test_basic_chart,
        test_ai_pattern_analysis,
        test_prediction,
        test_chart_with_prediction,
        test_chart_with_ai_annotations,
        test_comparison_chart,
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
    
    print(f"\n图表保存在 output/ 目录")
    
    if failed == 0:
        print("\n🎉 所有测试通过！Day 3 任务完成！")
        return True
    else:
        print(f"\n⚠️  有 {failed} 个测试失败")
        return False


if __name__ == "__main__":
    # 设置环境变量
    if not os.getenv('DEEPSEEK_API_KEY'):
        os.environ['DEEPSEEK_API_KEY'] = 'sk-eea85ceb681c46a3bfbd4903a44ecc2d'
    
    success = run_all_tests()
    sys.exit(0 if success else 1)

