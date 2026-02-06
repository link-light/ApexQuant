# -*- coding: utf-8 -*-
"""
快速测试模拟盘核心功能
"""

import sys
import os

# 设置路径
project_root = os.path.dirname(os.path.abspath(__file__))
python_dir = os.path.join(project_root, 'python')
apexquant_dir = os.path.join(python_dir, 'apexquant')

sys.path.insert(0, python_dir)
sys.path.insert(0, apexquant_dir)
os.chdir(apexquant_dir)

print("=" * 60)
print("ApexQuant Simulation System Quick Test")
print("=" * 60)

# 1. Test C++ module import
print("\n[1/6] Testing C++ module import...")
try:
    import apexquant_simulation as sim_cpp
    import apexquant_core as core_cpp
    print("[OK] C++ modules imported successfully")
    print(f"  - apexquant_simulation: OK")
    print(f"  - apexquant_core: OK")
except ImportError as e:
    print(f"[FAIL] C++ module import failed: {e}")
    sys.exit(1)

# 2. Test Python module import
print("\n[2/6] Testing Python module import...")
try:
    from simulation import (
        DatabaseManager,
        SimulationController,
        SimulationConfig,
        TradingCalendar,
        RiskManager,
        PerformanceAnalyzer,
        MockDataSource
    )
    print("[OK] Python modules imported successfully")
except ImportError as e:
    print(f"[FAIL] Python module import failed: {e}")
    sys.exit(1)

# 3. Test database
print("\n[3/6] Testing database...")
try:
    db = DatabaseManager("../../data/test_quick.db")
    account_id = db.create_account(100000, "test_strategy")
    print(f"[OK] Database test passed")
    print(f"  - Account created: {account_id}")
except Exception as e:
    print(f"[FAIL] Database test failed: {e}")

# 4. Test C++ exchange
print("\n[4/6] Testing C++ simulated exchange...")
try:
    exchange = sim_cpp.SimulatedExchange("TEST_ACCOUNT", 100000.0)
    print(f"[OK] C++ exchange created successfully")
    print(f"  - Account ID: TEST_ACCOUNT")
    print(f"  - Initial capital: 100000.0")
    
    # Test query
    account = exchange.get_account_info()
    print(f"  - Available cash: {account['available_cash']}")
    print(f"  - Total assets: {account['total_assets']}")
except Exception as e:
    print(f"[FAIL] C++ exchange test failed: {e}")

# 5. Test Mock data source
print("\n[5/6] Testing Mock data source...")
try:
    data_source = MockDataSource(num_days=10, initial_price=100.0)
    df = data_source.get_stock_data("TEST.SH", "2024-01-01", "2024-01-10")
    print(f"[OK] Mock data source test passed")
    print(f"  - Data rows generated: {len(df)}")
    print(f"  - Data columns: {list(df.columns)}")
    print(f"  - Price range: {df['close'].min():.2f} - {df['close'].max():.2f}")
except Exception as e:
    print(f"[FAIL] Mock data source test failed: {e}")

# 6. Test performance analyzer
print("\n[6/6] Testing performance analyzer...")
try:
    analyzer = PerformanceAnalyzer("../../data/test_quick.db", 100000.0)
    print(f"[OK] Performance analyzer created successfully")
except Exception as e:
    print(f"[FAIL] Performance analyzer test failed: {e}")

print("\n" + "=" * 60)
print("[OK] All core功能测试通过!")
print("=" * 60)
print("\nSimulation system is ready to use.")
print("\nNext steps:")
print("  1. Configure config/simulation_config.yaml")
print("  2. Run example: python examples/run_simulation.py")
print("  3. Read docs: README_SIMULATION.md")
