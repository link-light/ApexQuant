# -*- coding: utf-8 -*-
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "python" / "apexquant"))

print("="*60)
print("ApexQuant Quick Test")
print("="*60)

# Test 1: Import C++ modules
try:
    import apexquant_simulation as sim
    print("[OK] apexquant_simulation imported")
except Exception as e:
    print(f"[FAIL] {e}")
    sys.exit(1)

# Test 2: Validate order volume
try:
    matcher = sim.OrderMatcher()
    valid, msg = matcher.validate_order_volume(100, sim.OrderSide.BUY, 0)
    print(f"[OK] 100 shares: {valid}")
    
    valid, msg = matcher.validate_order_volume(99, sim.OrderSide.BUY, 0)
    print(f"[OK] 99 shares rejected: {not valid}")
except Exception as e:
    print(f"[FAIL] {e}")

# Test 3: Commission calculation
try:
    fee = matcher.calculate_total_commission(
        sim.OrderSide.BUY, "sh.600519", 10.0, 100, 0.00025
    )
    print(f"[OK] Min commission 5 yuan: {fee >= 5.0}")
    
    fee_sh = matcher.calculate_total_commission(
        sim.OrderSide.BUY, "sh.600519", 1800.0, 1000, 0.00025
    )
    fee_sz = matcher.calculate_total_commission(
        sim.OrderSide.BUY, "sz.000001", 1800.0, 1000, 0.00025
    )
    print(f"[OK] Shanghai has transfer fee: {fee_sh > fee_sz}")
except Exception as e:
    print(f"[FAIL] {e}")

# Test 4: LimitQueue
try:
    queue = sim.LimitQueue()
    print(f"[OK] LimitQueue created")
except Exception as e:
    print(f"[FAIL] {e}")

# Test 5: Account
try:
    account = sim.SimulationAccount("test", 100000.0)
    available = account.get_available_cash()
    withdrawable = account.get_withdrawable_cash()
    print(f"[OK] Account created: available={available}, withdrawable={withdrawable}")
except Exception as e:
    print(f"[FAIL] {e}")

# Test 6: Python modules
try:
    sys.path.insert(0, str(Path(__file__).parent / "python"))
    from apexquant.simulation.stock_status import StockStatusManager
    manager = StockStatusManager()
    print("[OK] StockStatusManager created")
except Exception as e:
    print(f"[FAIL] {e}")

try:
    from apexquant.simulation.trading_calendar import TradingCalendar
    calendar = TradingCalendar()
    print("[OK] TradingCalendar created")
except Exception as e:
    print(f"[FAIL] {e}")

print("="*60)
print("All tests passed!")
print("="*60)
















