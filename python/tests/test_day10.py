"""
Day 10 测试：监控和部署
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from apexquant.monitoring import MetricsExporter, AnomalyDetector


def test_metrics_exporter():
    """测试指标导出"""
    print("=" * 60)
    print("测试 MetricsExporter")
    print("=" * 60)
    
    exporter = MetricsExporter()
    
    print("\n【更新账户指标】")
    exporter.update_account_metrics({
        'total_assets': 102000.0,
        'profit_loss': 2000.0,
        'profit_loss_pct': 0.02,
        'daily_pnl': 500.0
    })
    
    print("✓ 账户指标已更新")
    
    print("\n【更新性能指标】")
    exporter.update_performance_metrics({
        'win_rate': 0.55,
        'max_drawdown': 0.08,
        'sharpe_ratio': 1.8
    })
    
    print("✓ 性能指标已更新")
    
    print("\n【更新交易指标】")
    exporter.update_trading_metrics(
        trade_count=25,
        position_count=3,
        orders_submitted=30,
        orders_filled=28,
        orders_rejected=2
    )
    
    print("✓ 交易指标已更新")
    
    print("\n【导出 Prometheus 格式】")
    metrics_text = exporter.export_prometheus_format()
    
    lines = metrics_text.strip().split('\n')
    print(f"导出 {len(lines)} 行指标")
    print("\n示例指标（前10行）:")
    for line in lines[:10]:
        print(f"  {line}")
    
    print("\n【获取当前指标】")
    metrics = exporter.get_metrics()
    for k, v in list(metrics.items())[:8]:
        print(f"  {k}: {v}")
    
    print("\n✓ MetricsExporter 测试完成\n")


def test_anomaly_detector():
    """测试异常检测"""
    print("=" * 60)
    print("测试 AnomalyDetector")
    print("=" * 60)
    
    detector = AnomalyDetector()
    
    # 正常指标
    print("\n【测试正常指标】")
    normal_metrics = {
        'total_assets': 102000,
        'profit_loss': 2000,
        'profit_loss_pct': 0.02,
        'win_rate': 0.55,
        'max_drawdown': 0.08,
        'daily_pnl': 500,
        'position_count': 3,
        'orders_submitted': 30,
        'orders_filled': 28,
        'orders_rejected': 2
    }
    
    anomalies = detector.detect_metric_anomalies(normal_metrics)
    print(f"检测到 {len(anomalies)} 个异常")
    
    if anomalies:
        for anomaly in anomalies:
            print(f"  - {anomaly['message']}")
    else:
        print("  ✓ 无异常")
    
    # 异常指标
    print("\n【测试异常指标】")
    abnormal_metrics = {
        'total_assets': 85000,
        'profit_loss': -15000,
        'profit_loss_pct': -0.15,
        'win_rate': 0.25,
        'max_drawdown': 0.25,
        'daily_pnl': -12000,
        'position_count': 15,
        'orders_submitted': 50,
        'orders_filled': 35,
        'orders_rejected': 15
    }
    
    anomalies = detector.detect_metric_anomalies(abnormal_metrics)
    print(f"检测到 {len(anomalies)} 个异常")
    
    for anomaly in anomalies:
        print(f"  [{anomaly['severity']}] {anomaly['message']}")
    
    print("\n【生成告警消息】")
    alert_msg = detector.generate_alert_message(anomalies)
    print(alert_msg)
    
    print("\n【异常统计】")
    summary = detector.get_anomaly_summary()
    print(f"总异常数: {summary['total_count']}")
    print(f"按类型: {summary['by_type']}")
    print(f"按严重程度: {summary['by_severity']}")
    
    print("\n✓ AnomalyDetector 测试完成\n")


def test_log_analysis():
    """测试日志分析"""
    print("=" * 60)
    print("测试日志分析")
    print("=" * 60)
    
    detector = AnomalyDetector()
    
    # 模拟日志
    sample_logs = [
        "[2024-01-15 10:00:00] INFO: 系统启动",
        "[2024-01-15 10:05:00] INFO: 连接市场数据成功",
        "[2024-01-15 10:10:00] INFO: 生成买入信号: 600519 @ 1800.00",
        "[2024-01-15 10:15:00] INFO: 订单已提交: ORD001",
        "[2024-01-15 10:20:00] INFO: 订单已成交: ORD001",
        "[2024-01-15 11:00:00] WARNING: 连接超时，尝试重连",
        "[2024-01-15 11:01:00] INFO: 重连成功",
        "[2024-01-15 14:00:00] INFO: 触发止盈，平仓 600519",
        "[2024-01-15 15:00:00] INFO: 当日盈亏: +2000.00",
    ]
    
    print(f"\n分析 {len(sample_logs)} 条日志...")
    
    analysis = detector.analyze_logs(sample_logs)
    
    if analysis:
        print("\n【AI 日志分析】")
        print(analysis)
    else:
        print("\n(AI 日志分析未启用)")
    
    print("\n✓ 日志分析测试完成\n")


def test_integration():
    """测试集成场景"""
    print("=" * 60)
    print("测试集成场景")
    print("=" * 60)
    
    # 初始化
    exporter = MetricsExporter()
    detector = AnomalyDetector()
    
    print("\n【模拟交易流程】")
    
    # 更新指标
    metrics = {
        'total_assets': 95000,
        'profit_loss': -5000,
        'profit_loss_pct': -0.05,
        'win_rate': 0.40,
        'max_drawdown': 0.12,
        'daily_pnl': -2000,
        'position_count': 4,
        'orders_submitted': 20,
        'orders_filled': 18,
        'orders_rejected': 2
    }
    
    exporter.update_account_metrics(metrics)
    exporter.update_performance_metrics(metrics)
    exporter.update_trading_metrics(
        metrics['position_count'],
        metrics['position_count'],
        metrics['orders_submitted'],
        metrics['orders_filled'],
        metrics['orders_rejected']
    )
    
    print("✓ 指标已更新")
    
    # 检测异常
    print("\n【异常检测】")
    anomalies = detector.detect_metric_anomalies(metrics)
    
    if anomalies:
        alert_msg = detector.generate_alert_message(anomalies)
        print(alert_msg)
        print("(实际部署时会发送到 Telegram/企业微信)")
    else:
        print("✓ 无异常")
    
    # 导出指标
    print("\n【导出指标】")
    prometheus_metrics = exporter.export_prometheus_format()
    print(f"已生成 Prometheus 格式指标（{len(prometheus_metrics)} 字节）")
    print("(实际部署时会暴露到 /metrics 端点供 Prometheus 抓取)")
    
    print("\n✓ 集成测试完成\n")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print(" Day 10 - 监控和部署测试")
    print("=" * 60 + "\n")
    
    # 测试指标导出
    test_metrics_exporter()
    
    # 测试异常检测
    test_anomaly_detector()
    
    # 测试日志分析
    test_log_analysis()
    
    # 测试集成场景
    test_integration()
    
    print("=" * 60)
    print(" 所有测试完成！")
    print("=" * 60)
    print("\n提示: 完整部署请运行 ./deploy.sh")

