"""
Day 8 测试：实盘交易系统
"""

import sys
import os
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from apexquant.live import AISignalGenerator, RLTradingAgent, LiveTrader


def test_signal_generator():
    """测试 AI 信号生成器"""
    print("=" * 60)
    print("测试 AISignalGenerator")
    print("=" * 60)
    
    generator = AISignalGenerator()
    
    # 创建模拟数据
    dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
    np.random.seed(42)
    prices = 100 * np.exp(np.cumsum(np.random.normal(0.001, 0.02, 100)))
    
    data = pd.DataFrame({
        'date': dates,
        'open': prices * 0.99,
        'high': prices * 1.02,
        'low': prices * 0.98,
        'close': prices,
        'volume': np.random.randint(1000000, 10000000, 100)
    })
    
    print("\n【生成单个信号】")
    symbol = "600519"
    current_price = data['close'].iloc[-1]
    
    action, confidence, reason = generator.generate_signal(
        symbol, current_price, data, None, None
    )
    
    print(f"股票: {symbol}")
    print(f"当前价格: {current_price:.2f}")
    print(f"信号动作: {action}")
    print(f"置信度: {confidence:.2%}")
    print(f"理由: {reason}")
    
    print("\n【批量生成信号】")
    symbols = ["600519", "600036", "000001"]
    market_data = {sym: data for sym in symbols}
    
    signals = generator.batch_generate_signals(symbols, market_data)
    
    for sym, (act, conf, rsn) in signals.items():
        print(f"{sym}: {act} (置信度 {conf:.2%}) - {rsn}")
    
    print("\n【过滤信号】")
    filtered = generator.filter_signals(signals, min_confidence=0.5, max_positions=2)
    
    print(f"过滤后信号数: {len(filtered)}")
    for sym, act, conf, rsn in filtered:
        print(f"  {sym}: {act} (置信度 {conf:.2%})")
    
    print("\n✓ AISignalGenerator 测试完成\n")


def test_rl_agent():
    """测试 RL 交易代理"""
    print("=" * 60)
    print("测试 RLTradingAgent")
    print("=" * 60)
    
    agent = RLTradingAgent(state_dim=10, action_dim=3)
    
    # 创建模拟数据
    dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
    np.random.seed(42)
    prices = 100 * np.exp(np.cumsum(np.random.normal(0.001, 0.02, 100)))
    
    data = pd.DataFrame({
        'date': dates,
        'open': prices * 0.99,
        'high': prices * 1.02,
        'low': prices * 0.98,
        'close': prices,
        'volume': np.random.randint(1000000, 10000000, 100)
    })
    
    print("\n【提取状态】")
    state = agent.get_state(data)
    print(f"状态维度: {len(state)}")
    print(f"状态向量: {state}")
    
    print("\n【选择动作】")
    action = agent.select_action(state, deterministic=True)
    action_names = ['持有', '买入', '卖出']
    print(f"选择动作: {action} ({action_names[action]})")
    
    print("\n【训练回合】")
    result = agent.train_episode(data, initial_cash=100000.0)
    
    print(f"总奖励: {result['total_reward']:.4f}")
    print(f"最终资产: {result['final_value']:.2f}")
    print(f"收益率: {result['return']:.2%}")
    print(f"交易次数: {result['trades']}")
    
    print("\n✓ RLTradingAgent 测试完成\n")


def test_live_trader():
    """测试实盘交易管理器"""
    print("=" * 60)
    print("测试 LiveTrader（模拟模式）")
    print("=" * 60)
    
    # 创建模拟交易接口
    class MockTradingInterface:
        def __init__(self):
            self.connected = False
            self.logged_in = False
        
        def connect(self, config):
            self.connected = True
            return True
        
        def login(self, username, password):
            self.logged_in = True
            return True
        
        def query_account(self):
            class Account:
                total_assets = 100000.0
                available_cash = 80000.0
                market_value = 20000.0
                profit_loss = 0.0
            return Account()
        
        def query_positions(self):
            return []
        
        def disconnect(self):
            self.connected = False
    
    # 创建交易器
    trading = MockTradingInterface()
    signal_gen = AISignalGenerator()
    rl_agent = RLTradingAgent()
    
    trader = LiveTrader(
        trading_interface=trading,
        signal_generator=signal_gen,
        rl_agent=rl_agent
    )
    
    print("\n【设置监控列表】")
    symbols = ["600519", "600036", "000001"]
    trader.set_watch_list(symbols)
    print(f"监控股票: {', '.join(symbols)}")
    
    print("\n【设置风控参数】")
    trader.set_risk_limits({
        'max_position_size': 0.3,
        'stop_loss': -0.05,
        'take_profit': 0.15
    })
    print("风控参数已设置")
    
    print("\n【获取状态】")
    status = trader.get_status()
    print(f"运行状态: {status['running']}")
    print(f"总资产: {status['total_assets']:.2f}")
    print(f"可用资金: {status['available_cash']:.2f}")
    print(f"持仓数量: {status['positions_count']}")
    
    print("\n✓ LiveTrader 测试完成\n")
    print("注意: 实际启动需要真实交易接口和市场数据")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print(" Day 8 - 实盘交易系统测试")
    print("=" * 60 + "\n")
    
    # 测试信号生成器
    test_signal_generator()
    
    # 测试 RL 代理
    test_rl_agent()
    
    # 测试实盘交易器
    test_live_trader()
    
    print("=" * 60)
    print(" 所有测试完成！")
    print("=" * 60)

