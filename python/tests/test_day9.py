"""
Day 9 测试：AI 自适应系统
"""

import sys
import os
import numpy as np
import pandas as pd
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from apexquant.adaptive import OnlineLearner, LogAnalyzer, ParameterOptimizer, NotificationManager


def test_online_learner():
    """测试在线学习"""
    print("=" * 60)
    print("测试 OnlineLearner")
    print("=" * 60)
    
    learner = OnlineLearner(model_path="test_online_model.json")
    
    # 创建模拟数据
    dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
    np.random.seed(42)
    prices = 100 * np.exp(np.cumsum(np.random.normal(0.001, 0.02, 100)))
    
    data = pd.DataFrame({
        'date': dates,
        'open': prices * 0.99,
        'high': prices * 1.02,
        'low': prices * 0.98,
        'close': prices,
        'volume': np.random.randint(1000000, 10000000, 100)
    })
    
    print("\n【提取特征】")
    features = learner.extract_features(data)
    print(f"特征维度: {features.shape}")
    print(f"特征列: {features.columns.tolist()}")
    
    if not features.empty:
        print(f"\n最新特征值:")
        for col in features.columns[:5]:
            print(f"  {col}: {features[col].iloc[-1]:.4f}")
    
    print("\n【添加训练样本】")
    for i in range(len(features) - 1):
        feature_row = features.iloc[i]
        # 标签：下一天涨跌
        label = 1 if data['close'].iloc[i+1] > data['close'].iloc[i] else 0
        learner.add_training_sample(feature_row, label)
    
    print(f"训练样本数: {len(learner.training_data)}")
    
    print("\n【更新模型】")
    success = learner.update_model(batch_size=50, force=True)
    print(f"更新{'成功' if success else '失败'}")
    
    if success and not features.empty:
        print("\n【预测】")
        latest_features = features.iloc[-1]
        pred_label, pred_prob = learner.predict(latest_features)
        
        print(f"预测标签: {pred_label} ({'上涨' if pred_label == 1 else '下跌'})")
        print(f"预测概率: {pred_prob:.3f}")
    
    print("\n【统计信息】")
    stats = learner.get_stats()
    for k, v in stats.items():
        print(f"  {k}: {v}")
    
    print("\n✓ OnlineLearner 测试完成\n")


def test_log_analyzer():
    """测试日志分析"""
    print("=" * 60)
    print("测试 LogAnalyzer")
    print("=" * 60)
    
    analyzer = LogAnalyzer()
    
    # 模拟交易记录
    trades = [
        {
            'timestamp': datetime.now(),
            'symbol': '600519',
            'action': 'buy',
            'price': 1800.0,
            'volume': 100,
            'reason': 'MA 金叉',
            'result': {'pnl': 500, 'pnl_pct': 0.028}
        },
        {
            'timestamp': datetime.now(),
            'symbol': '600036',
            'action': 'buy',
            'price': 35.0,
            'volume': 500,
            'reason': 'RSI 超卖',
            'result': {'pnl': -200, 'pnl_pct': -0.011}
        }
    ]
    
    # 记录交易
    for trade in trades:
        analyzer.log_trade(
            trade['timestamp'],
            trade['symbol'],
            trade['action'],
            trade['price'],
            trade['volume'],
            trade['reason'],
            trade['result']
        )
    
    print(f"\n已记录 {len(trades)} 笔交易")
    
    # 账户表现
    account_perf = {
        'total_assets': 102000,
        'profit_loss': 2000,
        'profit_loss_pct': 0.02,
        'win_rate': 0.50
    }
    
    print("\n【分析交易会话】")
    report = analyzer.analyze_trading_session(trades, account_perf)
    print(report)
    
    print("\n【生成每日报告】")
    positions = [
        {'symbol': '600519', 'volume': 100, 'pnl_ratio': 0.028}
    ]
    
    daily_report = analyzer.generate_daily_report(trades, positions, account_perf)
    print(daily_report)
    
    print("\n✓ LogAnalyzer 测试完成\n")


def test_param_optimizer():
    """测试参数优化"""
    print("=" * 60)
    print("测试 ParameterOptimizer")
    print("=" * 60)
    
    optimizer = ParameterOptimizer()
    
    # 当前参数
    current_params = {
        'max_position_size': 0.3,
        'stop_loss': -0.05,
        'take_profit': 0.15,
        'signal_threshold': 0.6
    }
    
    # 性能指标
    performance = {
        'win_rate': 0.45,
        'return': 0.03,
        'max_drawdown': 0.12,
        'profit_loss_ratio': 1.2
    }
    
    print("\n【当前参数】")
    for k, v in current_params.items():
        print(f"  {k}: {v}")
    
    print("\n【性能指标】")
    for k, v in performance.items():
        print(f"  {k}: {v}")
    
    print("\n【优化参数】")
    optimized = optimizer.optimize_parameters(
        current_params,
        performance,
        market_condition="震荡"
    )
    
    print("\n【优化结果】")
    for k, v in optimized.items():
        old_v = current_params[k]
        if old_v != v:
            print(f"  {k}: {old_v} -> {v}")
        else:
            print(f"  {k}: {v} (未变)")
    
    print("\n✓ ParameterOptimizer 测试完成\n")


def test_notifier():
    """测试通知系统"""
    print("=" * 60)
    print("测试 NotificationManager")
    print("=" * 60)
    
    # 注意：需要配置真实的 token 才能发送
    notifier = NotificationManager()
    
    print("\n【发送测试警报】")
    # notifier.send_alert("测试标题", "这是一条测试消息", level="info")
    print("(需要配置 Telegram/企业微信参数才能真正发送)")
    
    print("\n【交易通知示例】")
    trade_msg = notifier.send_trade_notification(
        symbol="600519",
        action="buy",
        price=1800.0,
        volume=100,
        reason="AI 信号: 多头排列"
    )
    print(f"交易通知构造完成")
    
    print("\n【风控警报示例】")
    risk_msg = notifier.send_risk_alert(
        alert_type="止损触发",
        details={
            '股票': '600036',
            '持仓成本': 35.0,
            '当前价格': 33.0,
            '亏损': -5.7
        }
    )
    print(f"风控警报构造完成")
    
    print("\n【日报示例】")
    report = """
当日交易: 5笔
盈亏: +2000 (+2%)
持仓: 3只
"""
    daily_msg = notifier.send_daily_report(report)
    print(f"日报构造完成")
    
    print("\n✓ NotificationManager 测试完成\n")
    print("提示: 配置真实 token 后可发送真实消息")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print(" Day 9 - AI 自适应系统测试")
    print("=" * 60 + "\n")
    
    # 测试在线学习
    test_online_learner()
    
    # 测试日志分析
    test_log_analyzer()
    
    # 测试参数优化
    test_param_optimizer()
    
    # 测试通知系统
    test_notifier()
    
    print("=" * 60)
    print(" 所有测试完成！")
    print("=" * 60)

