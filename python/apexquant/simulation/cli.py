"""
ApexQuant CLI Tool
命令行工具
"""

import sys
import os
import argparse
import logging
from pathlib import Path
from datetime import datetime

# 设置路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from simulation import (
    SimulationController,
    SimulationMode,
    get_config,
)

logger = logging.getLogger(__name__)


def setup_logging(log_level: str = "INFO"):
    """设置日志"""
    level = getattr(logging, log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('logs/simulation.log', encoding='utf-8')
        ]
    )


def run_backtest(args):
    """运行回测"""
    print("\n" + "="*60)
    print("ApexQuant Backtest Mode")
    print("="*60)
    
    # 加载配置
    config = get_config(args.config)
    
    # 创建控制器
    controller = SimulationController(config)
    
    # 获取回测参数
    start_date = args.start_date or config.get("backtest.start_date", "2023-01-01")
    end_date = args.end_date or config.get("backtest.end_date", "2024-12-31")
    symbols = args.symbols.split(',') if args.symbols else ["sh.600000"]
    
    print(f"\nBacktest Parameters:")
    print(f"  Start Date: {start_date}")
    print(f"  End Date: {end_date}")
    print(f"  Symbols: {symbols}")
    print(f"  Strategy: {args.strategy}")
    
    # 选择策略
    if args.strategy == "ma_cross":
        from simulation.strategies import create_ma_cross_strategy
        strategy_func = create_ma_cross_strategy(
            risk_manager=controller.risk_manager
        )
    elif args.strategy == "rsi":
        from simulation.strategies import create_rsi_strategy
        strategy_func = create_rsi_strategy(
            risk_manager=controller.risk_manager
        )
    elif args.strategy == "buy_hold":
        from simulation.strategies import create_buy_hold_strategy
        strategy_func = create_buy_hold_strategy()
    else:
        print(f"[ERROR] Unknown strategy: {args.strategy}")
        return 1
    
    # 定义回测策略包装函数
    def backtest_strategy(controller, date, daily_data):
        """回测策略包装"""
        for symbol, df in daily_data.items():
            if not df.empty:
                bar = df.iloc[-1].to_dict()
                bar['symbol'] = symbol
                account_info = controller.get_account_info()
                
                # 调用策略
                signal = strategy_func(controller, bar, account_info)
                
                # 处理信号
                if signal:
                    action = signal.get('action')
                    if action in ['buy', 'sell']:
                        controller.submit_order(
                            symbol=signal['symbol'],
                            side=action,
                            order_type=signal.get('order_type', 'limit'),
                            volume=signal.get('volume', 100),
                            price=signal.get('price', bar.get('close', 0))
                        )
    
    # 启动回测
    try:
        controller.start_backtest(
            start_date=start_date,
            end_date=end_date,
            symbols=symbols,
            strategy_func=backtest_strategy,
            bar_interval=args.interval
        )
        
        print("\n[SUCCESS] Backtest completed!")
        
    except Exception as e:
        print(f"\n[ERROR] Backtest failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


def run_realtime(args):
    """运行实时模拟"""
    print("\n" + "="*60)
    print("ApexQuant Realtime Simulation Mode")
    print("="*60)
    
    # 加载配置
    config = get_config(args.config)
    
    # 创建控制器
    controller = SimulationController(config)
    
    # 获取参数
    symbols = args.symbols.split(',') if args.symbols else ["sh.600000"]
    update_interval = args.interval or config.get("realtime.update_interval", 60)
    
    print(f"\nRealtime Parameters:")
    print(f"  Symbols: {symbols}")
    print(f"  Update Interval: {update_interval}s")
    print(f"  Strategy: {args.strategy}")
    
    # 选择策略
    if args.strategy == "ma_cross":
        from simulation.strategies import create_ma_cross_strategy
        strategy_func = create_ma_cross_strategy(
            risk_manager=controller.risk_manager
        )
    elif args.strategy == "rsi":
        from simulation.strategies import create_rsi_strategy
        strategy_func = create_rsi_strategy(
            risk_manager=controller.risk_manager
        )
    else:
        print(f"[ERROR] Unknown strategy: {args.strategy}")
        return 1
    
    # 定义实时策略包装函数
    def realtime_strategy(controller, timestamp, realtime_data):
        """实时策略包装"""
        account_info = controller.get_account_info()
        
        for symbol, data in realtime_data.items():
            signal = strategy_func(controller, data, account_info)
            
            if signal:
                action = signal.get('action')
                if action in ['buy', 'sell']:
                    controller.submit_order(
                        symbol=signal['symbol'],
                        side=action,
                        order_type=signal.get('order_type', 'market'),
                        volume=signal.get('volume', 100),
                        price=signal.get('price', 0)
                    )
    
    # 启动实时模拟
    try:
        print("\n[INFO] Starting realtime simulation...")
        print("[INFO] Press Ctrl+C to stop")
        
        controller.start_realtime(
            symbols=symbols,
            strategy_func=realtime_strategy,
            update_interval=update_interval
        )
        
    except KeyboardInterrupt:
        print("\n\n[INFO] Stopped by user")
        controller.stop()
    except Exception as e:
        print(f"\n[ERROR] Realtime simulation failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


def show_account(args):
    """显示账户信息"""
    config = get_config(args.config)
    controller = SimulationController(config)
    
    print("\n" + "="*60)
    print("Account Information")
    print("="*60)
    
    account_info = controller.get_account_info()
    print(f"\nAccount ID: {account_info.get('account_id')}")
    print(f"Available Cash: {account_info.get('available_cash', 0):,.2f}")
    print(f"Frozen Cash: {account_info.get('frozen_cash', 0):,.2f}")
    print(f"Total Assets: {account_info.get('total_assets', 0):,.2f}")
    
    # 持仓
    positions = controller.get_positions()
    if positions:
        print(f"\nPositions: {len(positions)}")
        for pos in positions:
            print(f"  {pos['symbol']}: {pos['volume']} @ {pos['avg_cost']:.2f}, "
                  f"Value: {pos['market_value']:.2f}, PnL: {pos['unrealized_pnl']:.2f}")
    else:
        print("\nNo positions")
    
    # 待成交订单
    pending_orders = controller.get_pending_orders()
    if pending_orders:
        print(f"\nPending Orders: {len(pending_orders)}")
        for order in pending_orders:
            print(f"  {order['order_id']}: {order['symbol']} {order['side']} "
                  f"{order['volume']} @ {order['price']:.2f}")
    else:
        print("\nNo pending orders")


def show_performance(args):
    """显示绩效报告"""
    from simulation import PerformanceAnalyzer
    from simulation.database import DatabaseManager
    
    config = get_config(args.config)
    db = DatabaseManager(config.get("database.path", "data/simulation.db"))
    
    # 获取权益曲线
    account_id = config.get("account.account_id", "simulation_001")
    equity_curve = db.get_equity_curve(account_id)
    
    if equity_curve is None or equity_curve.empty:
        print("[WARN] No equity curve data found")
        return 1
    
    # 获取交易记录
    trades = []  # TODO: 从数据库获取
    
    # 分析绩效
    initial_capital = config.get("account.initial_capital", 100000.0)
    analyzer = PerformanceAnalyzer(initial_capital)
    metrics = analyzer.analyze(equity_curve, trades)
    
    # 生成报告
    report = analyzer.generate_report(metrics)
    print(report)
    
    # 保存报告
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"\n[INFO] Report saved to {args.output}")
    
    return 0


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='ApexQuant Simulation CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run backtest
  python -m apexquant.simulation.cli backtest --start 2023-01-01 --end 2023-12-31 --symbols sh.600000,sh.600036

  # Run realtime simulation
  python -m apexquant.simulation.cli realtime --symbols sh.600000 --interval 60

  # Show account info
  python -m apexquant.simulation.cli account

  # Show performance report
  python -m apexquant.simulation.cli performance --output report.txt
        """
    )
    
    # 全局参数
    parser.add_argument('--config', '-c', type=str, help='Config file path')
    parser.add_argument('--log-level', '-l', default='INFO', 
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='Log level')
    
    # 子命令
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # backtest 命令
    backtest_parser = subparsers.add_parser('backtest', help='Run backtest')
    backtest_parser.add_argument('--start', dest='start_date', type=str, help='Start date (YYYY-MM-DD)')
    backtest_parser.add_argument('--end', dest='end_date', type=str, help='End date (YYYY-MM-DD)')
    backtest_parser.add_argument('--symbols', '-s', type=str, help='Symbols (comma separated)')
    backtest_parser.add_argument('--strategy', default='ma_cross', 
                                choices=['ma_cross', 'rsi', 'buy_hold'],
                                help='Strategy name')
    backtest_parser.add_argument('--interval', default='1d', help='Bar interval')
    
    # realtime 命令
    realtime_parser = subparsers.add_parser('realtime', help='Run realtime simulation')
    realtime_parser.add_argument('--symbols', '-s', type=str, help='Symbols (comma separated)')
    realtime_parser.add_argument('--strategy', default='ma_cross',
                                choices=['ma_cross', 'rsi'],
                                help='Strategy name')
    realtime_parser.add_argument('--interval', type=int, help='Update interval (seconds)')
    
    # account 命令
    account_parser = subparsers.add_parser('account', help='Show account info')
    
    # performance 命令
    perf_parser = subparsers.add_parser('performance', help='Show performance report')
    perf_parser.add_argument('--output', '-o', type=str, help='Output file path')
    
    args = parser.parse_args()
    
    # 设置日志
    setup_logging(args.log_level)
    
    # 执行命令
    if args.command == 'backtest':
        return run_backtest(args)
    elif args.command == 'realtime':
        return run_realtime(args)
    elif args.command == 'account':
        return show_account(args)
    elif args.command == 'performance':
        return show_performance(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n[FATAL ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
