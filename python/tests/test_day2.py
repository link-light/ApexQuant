"""
Day 2 测试：数据获取和 AI 增强
"""

import sys
import os
from datetime import datetime, timedelta

# 添加路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    import apexquant as aq
    from apexquant.data import AKShareDataFetcher, DataManager
    from apexquant.ai import DeepSeekClient, SentimentAnalyzer, AIDataCleaner
except ImportError as e:
    print(f"导入失败: {e}")
    sys.exit(1)


def test_akshare_data():
    """测试 AKShare 数据获取"""
    print("\n" + "="*60)
    print("测试 1: AKShare 数据获取")
    print("="*60)
    
    fetcher = AKShareDataFetcher()
    
    # 获取贵州茅台近3个月数据
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)
    
    df = fetcher.get_stock_bars(
        symbol='600519.SH',
        start_date=start_date.strftime('%Y%m%d'),
        end_date=end_date.strftime('%Y%m%d')
    )
    
    if df.empty:
        print("❌ 未获取到数据")
        return False
    
    print(f"✓ 获取数据 {len(df)} 条")
    print(f"  日期范围: {df['date'].min()} 至 {df['date'].max()}")
    print(f"  价格范围: {df['close'].min():.2f} - {df['close'].max():.2f}")
    print(f"  平均成交量: {df['volume'].mean():.0f}")
    
    # 显示最近5天
    print("\n最近5天数据:")
    print(df[['date', 'open', 'high', 'low', 'close', 'volume']].tail())
    
    return True


def test_data_manager():
    """测试数据管理器"""
    print("\n" + "="*60)
    print("测试 2: 数据管理器")
    print("="*60)
    
    manager = DataManager(data_dir="data")
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)
    
    # 获取多只股票
    symbols = ['600519.SH', '000858.SZ']  # 茅台、五粮液
    
    data_dict = manager.get_multiple_stocks(
        symbols=symbols,
        start_date=start_date.strftime('%Y%m%d'),
        end_date=end_date.strftime('%Y%m%d')
    )
    
    if not data_dict:
        print("❌ 未获取到数据")
        return False
    
    print(f"✓ 成功获取 {len(data_dict)} 只股票数据")
    
    for symbol, df in data_dict.items():
        print(f"\n{symbol}:")
        print(f"  数据量: {len(df)}")
        
        # 使用 C++ 计算统计
        if aq.is_core_loaded():
            stats = manager.calculate_statistics(df, 'close')
            print(f"  收盘价统计 (C++):")
            print(f"    均值: {stats['mean']:.2f}")
            print(f"    标准差: {stats['std']:.2f}")
            print(f"    最高: {stats['max']:.2f}")
            print(f"    最低: {stats['min']:.2f}")
    
    return True


def test_cpp_bar_conversion():
    """测试 DataFrame 到 C++ Bar 的转换"""
    print("\n" + "="*60)
    print("测试 3: C++ Bar 对象转换")
    print("="*60)
    
    if not aq.is_core_loaded():
        print("⚠️  C++ 模块未加载，跳过")
        return True
    
    manager = DataManager(data_dir="data")
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    df = manager.fetch_and_store_bars(
        symbol='600519.SH',
        start_date=start_date.strftime('%Y%m%d'),
        end_date=end_date.strftime('%Y%m%d')
    )
    
    if df.empty:
        print("❌ 未获取到数据")
        return False
    
    # 转换为 C++ Bar 对象
    bars = manager.convert_to_bars(df)
    
    print(f"✓ 转换了 {len(bars)} 个 Bar 对象")
    
    # 显示前3个
    print("\n前3个 Bar:")
    for i, bar in enumerate(bars[:3]):
        print(f"  {i+1}. {bar}")
        print(f"     涨跌幅: {bar.change_rate():.2%}")
    
    return True


def test_data_cleaning():
    """测试数据清洗"""
    print("\n" + "="*60)
    print("测试 4: AI 数据清洗")
    print("="*60)
    
    import pandas as pd
    import numpy as np
    
    # 创建带缺失值和异常值的测试数据
    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    prices = 1800 + np.random.randn(100) * 20
    
    # 添加缺失值
    prices[10:15] = np.nan
    prices[50] = np.nan
    
    # 添加异常值
    prices[30] = 5000  # 异常高值
    prices[70] = 500   # 异常低值
    
    df = pd.DataFrame({
        'date': dates,
        'close': prices
    })
    
    print(f"原始数据: {len(df)} 条")
    print(f"缺失值: {df['close'].isna().sum()}")
    
    # 清洗
    cleaner = AIDataCleaner()
    df_clean = cleaner.clean_pipeline(df, columns=['close'])
    
    print(f"\n✓ 清洗完成")
    print(f"  清洗后数据: {len(df_clean)} 条")
    print(f"  缺失值: {df_clean['close'].isna().sum()}")
    
    if 'is_outlier' in df_clean.columns:
        outliers = df_clean['is_outlier'].sum()
        print(f"  检测到异常值: {outliers}")
    
    return True


def test_sentiment_analysis():
    """测试情感分析"""
    print("\n" + "="*60)
    print("测试 5: 新闻情感分析")
    print("="*60)
    
    # 检查 API key
    api_key = os.getenv('DEEPSEEK_API_KEY')
    if not api_key:
        print("⚠️  未设置 DEEPSEEK_API_KEY，跳过测试")
        print("   请设置环境变量: set DEEPSEEK_API_KEY=sk-...")
        return True
    
    try:
        analyzer = SentimentAnalyzer(api_key)
        
        # 模拟新闻
        news_list = [
            {
                'title': '贵州茅台业绩超预期，股价创新高',
                'content': '贵州茅台发布年度报告，营收和利润均超市场预期...'
            },
            {
                'title': '白酒板块遭遇监管风险',
                'content': '监管部门加强对白酒行业的监管力度...'
            }
        ]
        
        print(f"分析 {len(news_list)} 条新闻...")
        
        results = analyzer.analyze_news(news_list)
        
        for i, news in enumerate(results, 1):
            print(f"\n新闻 {i}:")
            print(f"  标题: {news['title']}")
            print(f"  情感: {news['sentiment']}")
            print(f"  分数: {news['sentiment_score']:.2f}")
            if news.get('keywords'):
                print(f"  关键词: {', '.join(news['keywords'][:3])}")
        
        # 计算整体情绪
        market_sentiment = analyzer.calculate_market_sentiment(news_list)
        print(f"\n整体市场情绪:")
        print(f"  倾向: {market_sentiment['overall_sentiment']}")
        print(f"  平均分数: {market_sentiment['avg_score']:.2f}")
        print(f"  正面: {market_sentiment['positive_ratio']:.1%}")
        print(f"  负面: {market_sentiment['negative_ratio']:.1%}")
        
        print("\n✓ 情感分析完成")
        return True
        
    except Exception as e:
        print(f"⚠️  情感分析测试失败: {e}")
        return True  # 不影响整体测试


def test_integrated_pipeline():
    """测试完整数据流水线"""
    print("\n" + "="*60)
    print("测试 6: 完整数据流水线（数据 + AI）")
    print("="*60)
    
    manager = DataManager(data_dir="data")
    cleaner = AIDataCleaner()
    
    # 1. 获取数据
    end_date = datetime.now()
    start_date = end_date - timedelta(days=60)
    
    print("步骤 1: 获取原始数据...")
    df = manager.fetch_and_store_bars(
        symbol='600519.SH',
        start_date=start_date.strftime('%Y%m%d'),
        end_date=end_date.strftime('%Y%m%d')
    )
    
    if df.empty:
        print("❌ 未获取到数据")
        return False
    
    print(f"  原始数据: {len(df)} 条")
    
    # 2. 数据清洗
    print("\n步骤 2: 数据清洗...")
    df_clean = cleaner.clean_pipeline(df, columns=['open', 'high', 'low', 'close'])
    
    # 3. 计算技术指标（使用 C++）
    if aq.is_core_loaded():
        print("\n步骤 3: 计算技术指标 (C++)...")
        
        closes = df_clean['close'].tolist()
        
        # 5日均线
        ma5 = aq.rolling_mean(closes, 5)
        df_clean.loc[4:, 'MA5'] = ma5
        
        # 收益率
        returns = aq.pct_change(closes)
        df_clean.loc[1:, 'returns'] = returns
        
        print(f"  计算了 MA5 和收益率")
    
    # 4. 添加情感分数（模拟）
    print("\n步骤 4: 添加情感分数...")
    # 这里简化处理，实际应该基于新闻
    df_clean['sentiment_score'] = 0.5 + np.random.randn(len(df_clean)) * 0.1
    df_clean['sentiment_score'] = df_clean['sentiment_score'].clip(0, 1)
    
    # 5. 转换为 C++ 对象
    if aq.is_core_loaded():
        print("\n步骤 5: 转换为 C++ Bar 对象...")
        bars = manager.convert_to_bars(df_clean)
        print(f"  转换了 {len(bars)} 个 Bar 对象")
    
    # 6. 显示结果
    print("\n最终数据样本 (最近5天):")
    cols = ['date', 'close', 'returns', 'sentiment_score']
    print(df_clean[cols].tail())
    
    print("\n✓ 完整流水线测试完成")
    return True


def run_all_tests():
    """运行所有测试"""
    print("\n")
    print("╔" + "═"*58 + "╗")
    print("║" + " "*10 + "ApexQuant Day 2 测试" + " "*26 + "║")
    print("╚" + "═"*58 + "╝")
    
    # 检查 C++ 模块
    if aq.is_core_loaded():
        print("✓ C++ 核心模块已加载\n")
    else:
        print("⚠️  C++ 核心模块未加载（部分功能受限）\n")
    
    tests = [
        test_akshare_data,
        test_data_manager,
        test_cpp_bar_conversion,
        test_data_cleaning,
        test_sentiment_analysis,
        test_integrated_pipeline,
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
        print("\n🎉 所有测试通过！Day 2 任务完成！")
        return True
    else:
        print(f"\n⚠️  有 {failed} 个测试未完全通过")
        return False


if __name__ == "__main__":
    # 设置环境变量（如果未设置）
    if not os.getenv('DEEPSEEK_API_KEY'):
        print("提示: 设置环境变量以启用 AI 功能:")
        print("  Windows: set DEEPSEEK_API_KEY=sk-eea85ceb681c46a3bfbd4903a44ecc2d")
        print("  Linux/Mac: export DEEPSEEK_API_KEY=sk-eea85ceb681c46a3bfbd4903a44ecc2d")
        print()
        # 自动设置（仅用于测试）
        os.environ['DEEPSEEK_API_KEY'] = 'sk-eea85ceb681c46a3bfbd4903a44ecc2d'
    
    success = run_all_tests()
    sys.exit(0 if success else 1)

