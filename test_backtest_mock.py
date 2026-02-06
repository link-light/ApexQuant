#!/usr/bin/env python3
"""
测试回测功能（使用Mock数据）
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "python"))

import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def simple_ma_strategy(controller, date, daily_data):
    """
    简单均线策略：
    - 如果有数据，就买入100股
    - 测试订单系统是否正常工作
    """
    for symbol, df in daily_data.items():
        if df is not None and not df.empty:
            close_price = float(df.iloc[-1]['close'])

            # 检查是否已有持仓
            position = controller._get_position_volume(symbol)

            if position == 0:
                # 买入100股
                available_cash = controller.exchange.get_available_cash()
                required = close_price * 100 * 1.001  # 包含手续费

                if available_cash >= required:
                    order_id = controller.submit_order(
                        symbol=symbol,
                        side='buy',
                        order_type='limit',
                        volume=100,
                        price=close_price
                    )
                    if order_id:
                        print(f"  [策略] 买入 {symbol} 100股 @ {close_price:.2f}")


def main():
    print("=" * 60)
    print("ApexQuant 回测测试（Mock数据）")
    print("=" * 60)

    try:
        from apexquant.simulation.simulation_controller import SimulationController

        print("\n[1] 初始化控制器...")
        controller = SimulationController()

        account = controller.get_account_info()
        print(f"    账户ID: {account.get('account_id')}")
        print(f"    初始资金: {account.get('available_cash'):,.0f}")
        print(f"    使用C++: {controller.use_cpp}")

        print("\n[2] 设置回测参数...")
        start_date = "2026-01-01"
        end_date = "2026-02-02"
        symbols = ["600519"]  # 茅台

        print(f"    起始日期: {start_date}")
        print(f"    结束日期: {end_date}")
        print(f"    标的: {symbols}")

        print("\n[3] 开始回测...")
        controller.start_backtest(
            start_date=start_date,
            end_date=end_date,
            symbols=symbols,
            strategy_func=simple_ma_strategy
        )

        print("\n[4] 回测结果:")
        account = controller.get_account_info()
        print(f"    可用资金: {account.get('available_cash', 0):,.2f}")
        print(f"    总资产: {account.get('total_assets', 0):,.2f}")

        positions = controller.get_positions()
        print(f"    持仓数: {len(positions)}")
        for pos in positions:
            print(f"      - {pos['symbol']}: {pos['volume']}股, 成本{pos['avg_cost']:.2f}, 市值{pos['market_value']:.2f}")

        trades = controller.get_trade_history()
        print(f"    成交数: {len(trades)}")
        for trade in trades[:5]:  # 只显示前5笔
            print(f"      - {trade.get('symbol')}: {trade.get('side')} {trade.get('volume')}股 @ {trade.get('price', 0):.2f}")

        print("\n" + "=" * 60)
        print("回测完成!")
        print("=" * 60)

        return True

    except Exception as e:
        import traceback
        print(f"\n错误: {e}")
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
