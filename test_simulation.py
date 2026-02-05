"""
ApexQuant Simulation System Test Script
模拟盘系统测试脚本
"""

import sys
import logging
from pathlib import Path

# 添加python模块路径
python_path = Path(__file__).parent / "python"
apexquant_path = python_path / "apexquant"
sys.path.insert(0, str(python_path))
sys.path.insert(0, str(apexquant_path))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_cpp_modules():
    """测试C++模块导入"""
    print("\n" + "="*60)
    print("Test 1: C++ Modules Import")
    print("="*60)
    
    try:
        import apexquant_core as core
        import apexquant_simulation as sim
        
        print("[OK] apexquant_core imported successfully")
        print("[OK] apexquant_simulation imported successfully")
        
        # 测试基本功能
        print(f"\nCore module exports: {len(dir(core))} items")
        print(f"Simulation module exports: {len(dir(sim))} items")
        
        # 测试创建SimulatedExchange
        exchange = sim.SimulatedExchange("test_account", 100000.0)
        print(f"\n[OK] SimulatedExchange created")
        print(f"     Account ID: {exchange.get_account_id()}")
        print(f"     Available Cash: {exchange.get_available_cash():.2f}")
        print(f"     Total Assets: {exchange.get_total_assets():.2f}")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] {e}")
        import traceback
        traceback.print_exc()
        return False


def test_python_modules():
    """测试Python模块导入"""
    print("\n" + "="*60)
    print("Test 2: Python Modules Import")
    print("="*60)
    
    try:
        from apexquant.simulation import (
            DatabaseManager,
            SimulationConfig,
            TradingCalendar,
            SimulationDataSource,
            RiskManager,
            PerformanceAnalyzer,
            SimulationController,
        )
        
        print("[OK] All simulation modules imported successfully")
        
        # 测试配置
        config = SimulationConfig()
        print(f"\n[OK] Config loaded")
        print(f"     Initial Capital: {config.get('account.initial_capital')}")
        print(f"     Risk Control Enabled: {config.get('risk_control.enable_risk_control')}")
        
        # 测试交易日历
        calendar = TradingCalendar()
        import datetime
        today = datetime.date.today()
        is_trading = calendar.is_trading_day(today)
        print(f"\n[OK] Trading Calendar initialized")
        print(f"     Today ({today}) is trading day: {is_trading}")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] {e}")
        import traceback
        traceback.print_exc()
        return False


def test_data_source():
    """测试数据源"""
    print("\n" + "="*60)
    print("Test 3: Data Source")
    print("="*60)
    
    try:
        from apexquant.simulation import SimulationDataSource
        
        data_source = SimulationDataSource()
        print("[OK] Data source initialized")
        
        # 测试获取股票数据（小范围测试）
        print("\n[INFO] Fetching sample stock data...")
        df = data_source.get_stock_data(
            "sh.000001",  # 上证指数
            "2024-01-01",
            "2024-01-10",
            freq="d"
        )
        
        if df is not None and not df.empty:
            print(f"[OK] Fetched {len(df)} rows of data")
            print(f"     Columns: {list(df.columns)}")
            if len(df) > 0:
                print(f"     First row: {df.iloc[0].to_dict()}")
        else:
            print("[WARN] No data fetched (this might be normal if data source is unavailable)")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] {e}")
        import traceback
        traceback.print_exc()
        return False


def test_simulation_controller():
    """测试模拟盘控制器"""
    print("\n" + "="*60)
    print("Test 4: Simulation Controller")
    print("="*60)
    
    try:
        from apexquant.simulation import SimulationController
        
        controller = SimulationController()
        print("[OK] Simulation controller initialized")
        
        # 获取账户信息
        account_info = controller.get_account_info()
        print(f"\n[OK] Account Info:")
        print(f"     Account ID: {account_info.get('account_id')}")
        print(f"     Available Cash: {account_info.get('available_cash', 0):.2f}")
        print(f"     Total Assets: {account_info.get('total_assets', 0):.2f}")
        
        # 获取持仓（应该为空）
        positions = controller.get_positions()
        print(f"\n[OK] Positions: {len(positions)} positions")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("ApexQuant Simulation System Test")
    print("="*60)
    
    results = []
    
    # 运行测试
    results.append(("C++ Modules", test_cpp_modules()))
    results.append(("Python Modules", test_python_modules()))
    results.append(("Data Source", test_data_source()))
    results.append(("Simulation Controller", test_simulation_controller()))
    
    # 汇总结果
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    
    for test_name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status} {test_name}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n[SUCCESS] All tests passed!")
        return 0
    else:
        print("\n[FAILED] Some tests failed")
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
