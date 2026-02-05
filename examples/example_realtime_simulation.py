"""
Realtime Simulation Example
实时模拟示例 - 演示如何使用系统进行实时模拟交易
"""

import os
import sys
from pathlib import Path
import datetime

# 设置路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "python"))
os.chdir(str(project_root / "python" / "apexquant"))

import logging

# 配置日志
logging.basicConfig(level=logging.INFO)

from simulation import SimulationController, get_calendar


def realtime_ma_strategy(controller, timestamp, realtime_data):
    """
    实时均线策略
    
    Args:
        controller: 模拟盘控制器
        timestamp: 当前时间戳
        realtime_data: 实时数据 {symbol: dict}
    """
    # 获取账户信息
    account = controller.get_account_info()
    available_cash = account.get('available_cash', 0)
    
    print(f"\n[{timestamp}] Market Update")
    print(f"  Available Cash: {available_cash:,.2f}")
    
    # 遍历所有股票
    for symbol, data in realtime_data.items():
        current_price = data.get('current') or data.get('price', 0)
        
        if current_price > 0:
            print(f"  {symbol}: {current_price:.2f}")
            
            # 简单策略示例：价格低于某个值时买入
            # 实际应该用更复杂的逻辑
            if available_cash > current_price * 100 * 1.001:
                positions = controller.get_positions()
                has_position = any(p['symbol'] == symbol for p in positions)
                
                if not has_position:
                    print(f"  --> BUY {symbol} @ {current_price:.2f}")
                    order_id = controller.submit_order(
                        symbol=symbol,
                        side='buy',
                        order_type='market',
                        volume=100
                    )
                    if order_id:
                        print(f"  --> Order submitted: {order_id}")
                    break


def main():
    """主函数"""
    print("="*60)
    print("Realtime Simulation Example")
    print("="*60)
    
    try:
        # 创建控制器
        controller = SimulationController()
        
        # 检查交易时间
        calendar = get_calendar()
        now = datetime.datetime.now()
        
        if not calendar.is_trading_time(now):
            print(f"\n[INFO] Not in trading hours now")
            time_until_open = calendar.get_time_until_market_open(now)
            if time_until_open:
                print(f"[INFO] Next market open in: {time_until_open}")
            
            choice = input("\nContinue anyway? (y/n): ")
            if choice.lower() != 'y':
                return 0
        
        print("\nInitial Account:")
        account = controller.get_account_info()
        print(f"  Available Cash: {account.get('available_cash', 0):,.2f}")
        
        # 运行实时模拟
        print("\n[INFO] Starting realtime simulation...")
        print("[INFO] Update interval: 60 seconds")
        print("[INFO] Press Ctrl+C to stop")
        
        controller.start_realtime(
            symbols=["sh.600000", "sh.600036"],
            strategy_func=realtime_ma_strategy,
            update_interval=60
        )
        
    except KeyboardInterrupt:
        print("\n\n[INFO] Stopped by user")
        return 0
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
