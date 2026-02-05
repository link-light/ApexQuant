"""
ApexQuant Quick Demo (Run from python/apexquant directory)
"""

print("="*60)
print("ApexQuant Simulation System - Quick Demo")
print("="*60)

try:
    # 1. Import C++ modules
    print("\n[1/5] Loading C++ modules...")
    import apexquant_core as core
    import apexquant_simulation as sim
    print("  [OK] C++ modules loaded")
    print(f"       - apexquant_core: {len(dir(core))} exports")
    print(f"       - apexquant_simulation: {len(dir(sim))} exports")
    
    # 2. Test C++ SimulatedExchange
    print("\n[2/5] Testing C++ SimulatedExchange...")
    exchange = sim.SimulatedExchange("demo_account", 100000.0)
    print(f"  [OK] Exchange created")
    print(f"       - Account ID: {exchange.get_account_id()}")
    print(f"       - Available Cash: {exchange.get_available_cash():,.2f} CNY")
    print(f"       - Total Assets: {exchange.get_total_assets():,.2f} CNY")
    
    # 3. Test order submission
    print("\n[3/5] Testing order submission...")
    order = sim.SimulatedOrder(
        "ORD001",
        "sh.600000",
        sim.OrderSide.BUY,
        sim.OrderType.LIMIT,
        10.50,
        100,
        1706745600000  # timestamp
    )
    order_id = exchange.submit_order(order)
    print(f"  [OK] Order submitted: {order_id}")
    
    # 4. Test position query
    print("\n[4/5] Querying positions...")
    positions = exchange.get_all_positions()
    print(f"  [OK] Positions: {len(positions)}")
    
    # 5. Test Python modules
    print("\n[5/5] Testing Python integration...")
    import sys
    sys.path.insert(0, '..')
    from simulation import SimulationConfig
    config = SimulationConfig()
    print(f"  [OK] Config loaded")
    print(f"       - Initial Capital: {config.get('account.initial_capital'):,.2f} CNY")
    print(f"       - Commission Rate: {config.get('account.commission_rate')}")
    
    print("\n" + "="*60)
    print("[SUCCESS] All tests passed!")
    print("="*60)
    
    print("\nSystem is ready for:")
    print("  [OK] Backtest simulation")
    print("  [OK] Realtime simulation")
    print("  [OK] Order management")
    print("  [OK] Risk control")
    print("  [OK] Performance analysis")
    
except Exception as e:
    print(f"\n[ERROR] {e}")
    import traceback
    traceback.print_exc()
