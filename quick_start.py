"""
ApexQuant Quick Start
快速启动脚本
"""

import os
import sys

# 设置Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
python_path = os.path.join(project_root, "python")
sys.path.insert(0, python_path)

# 切换到apexquant目录以便导入C++模块
os.chdir(os.path.join(python_path, "apexquant"))

print("="*60)
print("ApexQuant Quick Start")
print("="*60)

try:
    # 导入C++模块
    print("\n[1/4] Loading C++ modules...")
    import apexquant_core as core
    import apexquant_simulation as sim
    print("  [OK] C++ modules loaded")
    
    # 返回项目根目录
    os.chdir(project_root)
    
    # 导入Python模块
    print("\n[2/4] Loading Python modules...")
    from apexquant.simulation import SimulationController, get_config
    print("  [OK] Python modules loaded")
    
    # 创建控制器
    print("\n[3/4] Initializing simulation controller...")
    controller = SimulationController()
    print("  [OK] Controller initialized")
    
    # 显示账户信息
    print("\n[4/4] Account Information:")
    account_info = controller.get_account_info()
    print(f"  Account ID: {account_info.get('account_id')}")
    print(f"  Available Cash: ¥{account_info.get('available_cash', 0):,.2f}")
    print(f"  Total Assets: ¥{account_info.get('total_assets', 0):,.2f}")
    
    print("\n" + "="*60)
    print("[SUCCESS] System ready!")
    print("="*60)
    
    print("\nYou can now:")
    print("1. Run backtest: python -m apexquant.simulation.examples.backtest_example")
    print("2. Run realtime simulation: python -m apexquant.simulation.examples.realtime_example")
    print("3. Edit config: config/simulation_config.yaml")
    
    print("\nController object available as 'controller'")
    print("Enter 'controller.get_account_info()' to see account details")
    
    # 进入交互模式
    import code
    code.interact(local=locals(), banner="\n[Interactive Mode] Type 'exit()' to quit")
    
except Exception as e:
    print(f"\n[ERROR] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
