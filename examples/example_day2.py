"""
Day 2 示例：数据获取和 AI 增强
"""

import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'python'))

import apexquant as aq
from apexquant.data import DataManager
from apexquant.ai import SentimentAnalyzer, AIDataCleaner


def main():
    print("=" * 60)
    print("Day 2 示例：AI 驱动的股票数据分析")
    print("=" * 60)
    
    # 设置 API key
    os.environ['DEEPSEEK_API_KEY'] = 'sk-eea85ceb681c46a3bfbd4903a44ecc2d'
    
    # 1. 获取数据
    print("\n[1] 获取股票数据...")
    manager = DataManager(data_dir="data")
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)
    
    df = manager.fetch_and_store_bars(
        symbol='600519.SH',
        start_date=start_date.strftime('%Y%m%d'),
        end_date=end_date.strftime('%Y%m%d')
    )
    
    print(f"✓ 获取 {len(df)} 条数据")
    
    # 2. 数据清洗
    print("\n[2] AI 数据清洗...")
    cleaner = AIDataCleaner()
    df_clean = cleaner.clean_pipeline(df)
    
    # 3. 技术指标（C++）
    if aq.is_core_loaded():
        print("\n[3] 计算技术指标 (高性能 C++)...")
        closes = df_clean['close'].tolist()
        
        # 计算多个均线
        df_clean['MA5'] = [None] * 4 + aq.rolling_mean(closes, 5)
        df_clean['MA10'] = [None] * 9 + aq.rolling_mean(closes, 10)
        df_clean['MA20'] = [None] * 19 + aq.rolling_mean(closes, 20)
        
        # 统计
        stats = manager.calculate_statistics(df_clean, 'close')
        print(f"  均值: {stats['mean']:.2f}")
        print(f"  波动率: {stats['std']:.2f}")
    
    # 4. 情感分析（示例）
    print("\n[4] 新闻情感分析...")
    try:
        analyzer = SentimentAnalyzer()
        
        # 模拟新闻
        news = [{
            'title': '贵州茅台Q4业绩超预期',
            'content': '公司营收增长稳健，利润率持续提升...'
        }]
        
        results = analyzer.analyze_news(news)
        print(f"  情感: {results[0]['sentiment']}")
        print(f"  分数: {results[0]['sentiment_score']:.2f}")
    except:
        print("  (跳过 - 需要 API)")
    
    # 5. 显示结果
    print("\n[5] 最终增强数据 (最近5天):")
    print(df_clean[['date', 'close', 'MA5', 'MA10', 'MA20']].tail().to_string(index=False))
    
    print("\n" + "=" * 60)
    print("✓ Day 2 示例完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()

