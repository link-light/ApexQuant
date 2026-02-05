"""
ApexQuant Simple Demo
简单演示脚本 - 展示模拟盘系统的基本功能
"""

import sys
from pathlib import Path

# 添加python模块路径
sys.path.insert(0, str(Path(__file__).parent / "python"))

import datetime
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """主函数"""
    print("\n" + "="*60)
    print("ApexQuant Simulation System Demo")
    print("="*60)
    
    try:
        # 1. 导入模块
        print("\n[Step 1] Importing modules...")
        import apexquant_core as core
        import apexquant_simulation as sim
        from apexquant.simulation import SimulationController
        print("[OK] Modules imported successfully")
        
        # 2. 创建模拟盘控制器
        print("\n[Step 2] Creating simulation controller...")
        controller = SimulationController()
        print("[OK] Controller created")
        
        # 3. 获取账户信息
        print("\n[Step 3] Getting account info...")
        account_info = controller.get_account_info()
        print(f"     Account ID: {account_info.get('account_id')}")
        print(f"     Available Cash: {account_info.get('available_cash', 0):.2f}")
        print(f"     Total Assets: {account_info.get('total_assets', 0):.2f}")
        
        # 4. 测试提交订单（市价单）
        print("\n[Step 4] Testing order submission...")
        print("     Submitting a BUY order for sh.600000 (Pudong Development Bank)")
        
        order_id = controller.submit_order(
            symbol="sh.600000",
            side="buy",
            order_type="market",
            volume=100,
            price=10.0  # 市价单价格会被忽略
        )
        
        if order_id:
            print(f"[OK] Order submitted: {order_id}")
        else:
            print("[FAIL] Order submission failed (this is normal - no market data)")
        
        # 5. 查询持仓
        print("\n[Step 5] Querying positions...")
        positions = controller.get_positions()
        print(f"     Current positions: {len(positions)}")
        for pos in positions:
            print(f"     - {pos['symbol']}: {pos['volume']} shares @ {pos['avg_cost']:.2f}")
        
        # 6. 查询待成交订单
        print("\n[Step 6] Querying pending orders...")
        pending_orders = controller.get_pending_orders()
        print(f"     Pending orders: {len(pending_orders)}")
        for order in pending_orders:
            print(f"     - {order['order_id']}: {order['symbol']} {order['side']} {order['volume']}")
        
        # 7. 显示系统配置
        print("\n[Step 7] System configuration...")
        config = controller.config
        print(f"     Initial Capital: {config.get('account.initial_capital')}")
        print(f"     Commission Rate: {config.get('account.commission_rate')}")
        print(f"     Risk Control: {config.get('risk_control.enable_risk_control')}")
        print(f"     Data Source (Primary): {config.get('data_source.primary')}")
        print(f"     Data Source (Backup): {config.get('data_source.backup')}")
        
        print("\n" + "="*60)
        print("Demo completed successfully!")
        print("="*60)
        
        print("\nNext steps:")
        print("1. 修改 config/simulation_config.yaml 配置文件")
        print("2. 运行回测: python examples/run_backtest.py")
        print("3. 运行实时模拟: python examples/run_realtime.py")
        print("4. 查看文档: docs/ 目录")
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
