"""
ApexQuant 端到端集成测试

测试完整的交易流程
"""

import sys
import os
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from apexquant.simulation.simulation_controller import SimulationController, SimulationMode
from apexquant.simulation.data_source import MockDataSource
from apexquant.simulation.risk_manager import RiskManager
from apexquant.simulation.performance_analyzer import PerformanceAnalyzer
from apexquant.simulation.strategies import create_buy_hold_strategy

logger = logging.getLogger(__name__)


def test_full_simulation():
    """完整模拟盘测试"""
    print("=" * 60)
    print("ApexQuant Integration Test")
    print("=" * 60)
    
    try:
        # 1. 创建控制器
        print("\n[1/6] Creating simulation controller...")
        controller = SimulationController(
            mode=SimulationMode.BACKTEST,
            initial_capital=1000000,
            db_path="data/test_integration.db"
        )
        print(f"    Account ID: {controller.account_id}")
        
        # 2. 初始化数据源（使用Mock）
        print("\n[2/6] Initializing data source...")
        controller.data_source = MockDataSource(initial_price=100.0, volatility=0.02)
        print("    Mock data source ready")
        
        # 3. 创建策略
        print("\n[3/6] Creating strategy...")
        strategy = create_buy_hold_strategy()
        print("    Buy&Hold strategy created")
        
        # 4. 运行回测
        print("\n[4/6] Running backtest...")
        symbols = ['TEST.SH']
        
        # 获取测试数据
        bars = controller.data_source.get_history(
            symbols[0],
            '2024-01-01',
            '2024-01-05',
            '1min'
        )
        
        print(f"    Loaded {len(bars)} bars")
        
        # 简化的回测循环
        from apexquant.simulation.data_source import bar_to_tick
        
        for i, bar in enumerate(bars[:100]):  # 只测试前100根K线
            tick = bar_to_tick(bar)
            controller.exchange.on_tick(tick)
            
            account_info = controller.get_account_info()
            signals = strategy(controller, bar, account_info)
            
            if signals:
                controller.process_signals(signals)
            
            if i % 50 == 0:
                print(f"    Progress: {i}/{len(bars[:100])} bars")
        
        print("    Backtest completed")
        
        # 5. 检查账户状态
        print("\n[5/6] Checking account status...")
        account_info = controller.get_account_info()
        
        print(f"    Total assets: {account_info['total_assets']:.2f}")
        print(f"    Available cash: {account_info['available_cash']:.2f}")
        print(f"    Positions: {len(account_info['positions'])}")
        
        for pos in account_info['positions']:
            print(f"      {pos['symbol']}: {pos['volume']} shares, PnL: {pos['unrealized_pnl']:.2f}")
        
        # 6. 生成报告
        print("\n[6/6] Generating report...")
        controller.save_snapshot()
        
        report = PerformanceAnalyzer.generate_report(
            controller.account_id,
            "data/test_integration.db"
        )
        
        print("\n" + report)
        
        print("\n" + "=" * 60)
        print("[SUCCESS] Integration test passed!")
        print("=" * 60)
        
        return 0
        
    except Exception as e:
        print(f"\n[ERROR] Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    exit(test_full_simulation())
