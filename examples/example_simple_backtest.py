"""
Simple Backtest Example
简单回测示例 - 演示如何使用模拟盘系统进行回测
"""

import os
import sys
from pathlib import Path

# 设置路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "python"))
os.chdir(str(project_root / "python" / "apexquant"))

import logging

# 配置日志
logging.basicConfig(level=logging.INFO)

from simulation import SimulationController, get_config


def simple_ma_strategy(controller, date, daily_data):
    """
    简单均线策略
    
    Args:
        controller: 模拟盘控制器
        date: 当前日期
        daily_data: 当日数据 {symbol: DataFrame}
    """
    # 获取账户信息
    account = controller.get_account_info()
    available_cash = account.get('available_cash', 0)
    
    # 遍历所有股票
    for symbol, df in daily_data.items():
        if df.empty or 'close' not in df.columns:
            continue
        
        close_price = float(df.iloc[-1]['close'])
        
        # 简单策略：如果有资金且价格合理，买入100股
        if available_cash > close_price * 100 * 1.001:  # 含手续费
            # 检查是否已持仓
            positions = controller.get_positions()
            has_position = any(p['symbol'] == symbol for p in positions)
            
            if not has_position:
                print(f"[{date}] BUY {symbol} @ {close_price:.2f}")
                controller.submit_order(
                    symbol=symbol,
                    side='buy',
                    order_type='limit',
                    volume=100,
                    price=close_price
                )
                break  # 每天只买一只


def main():
    """主函数"""
    print("="*60)
    print("Simple Backtest Example")
    print("="*60)
    
    try:
        # 创建控制器
        controller = SimulationController()
        
        print("\nInitial Account:")
        account = controller.get_account_info()
        print(f"  Available Cash: {account.get('available_cash', 0):,.2f}")
        
        # 运行回测（短期测试）
        print("\nStarting backtest...")
        controller.start_backtest(
            start_date="2024-01-01",
            end_date="2024-01-31",
            symbols=["sh.600000", "sh.600036"],  # 浦发银行、招商银行
            strategy_func=simple_ma_strategy,
            bar_interval="1d"
        )
        
        print("\n[SUCCESS] Backtest completed")
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
