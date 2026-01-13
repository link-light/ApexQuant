"""
Day 8 示例：实盘交易系统
"""

import sys
import os
import time
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'python'))

from apexquant.live import AISignalGenerator, RLTradingAgent, LiveTrader
from apexquant.data import AKShareWrapper


# 模拟交易接口（实际应使用 C++ 模拟盘或真实接口）
class SimulatedTradingPython:
    """Python 模拟交易接口"""
    
    def __init__(self, initial_cash=100000.0):
        self.cash = initial_cash
        self.initial_cash = initial_cash
        self.positions = {}
        self.market_prices = {}
    
    def connect(self, config):
        return True
    
    def login(self, username, password):
        return True
    
    def disconnect(self):
        pass
    
    def query_account(self):
        class Account:
            def __init__(self, cash, positions, prices):
                self.available_cash = cash
                market_value = sum(
                    pos['volume'] * prices.get(sym, pos['avg_price'])
                    for sym, pos in positions.items()
                    if pos['volume'] > 0
                )
                self.market_value = market_value
                self.total_assets = cash + market_value
                self.profit_loss = self.total_assets - 100000.0
        
        return Account(self.cash, self.positions, self.market_prices)
    
    def query_positions(self):
        class Position:
            def __init__(self, symbol, volume, avg_price, current_price):
                self.symbol = symbol
                self.total_volume = volume
                self.available_volume = volume
                self.avg_price = avg_price
                self.current_price = current_price
                self.market_value = volume * current_price
                self.profit_loss = (current_price - avg_price) * volume
                self.profit_loss_ratio = (current_price - avg_price) / avg_price if avg_price > 0 else 0
        
        positions = []
        for sym, pos in self.positions.items():
            if pos['volume'] > 0:
                current_price = self.market_prices.get(sym, pos['avg_price'])
                positions.append(Position(sym, pos['volume'], pos['avg_price'], current_price))
        
        return positions
    
    def update_price(self, symbol, price):
        """更新市场价格"""
        self.market_prices[symbol] = price
    
    def submit_order(self, order):
        """提交订单（简化版）"""
        # 这里简化处理，实际应该异步处理
        return f"ORDER_{int(time.time())}"


def main():
    """实盘交易系统示例"""
    
    print("=" * 80)
    print("ApexQuant - Day 8: 实盘交易系统")
    print("=" * 80)
    
    # ==================== 1. 初始化组件 ====================
    print("\n【步骤 1：初始化组件】")
    
    # 模拟交易接口
    trading = SimulatedTradingPython(initial_cash=100000.0)
    print("✓ 模拟交易接口已创建")
    
    # AI 信号生成器
    signal_gen = AISignalGenerator()
    print("✓ AI 信号生成器已创建")
    
    # RL 交易代理
    rl_agent = RLTradingAgent(state_dim=10, action_dim=3)
    print("✓ RL 交易代理已创建")
    
    # 数据接口
    data_wrapper = AKShareWrapper()
    print("✓ 数据接口已创建")
    
    # ==================== 2. 训练 RL 代理（可选）====================
    print("\n【步骤 2：训练 RL 代理】")
    
    symbol = "600519"
    print(f"获取训练数据: {symbol}")
    
    training_data = data_wrapper.get_historical_data(
        symbol, 
        start_date="2023-01-01",
        end_date="2023-12-31"
    )
    
    if training_data is not None and not training_data.empty:
        print(f"数据条数: {len(training_data)}")
        print("开始训练...")
        
        # 训练 5 个回合
        for episode in range(5):
            result = rl_agent.train_episode(training_data)
            print(f"  Episode {episode+1}: 收益率 {result['return']:.2%}, "
                  f"交易次数 {result['trades']}")
        
        # 保存模型
        model_path = "rl_model.pkl"
        rl_agent.save_model(model_path)
        print(f"✓ 模型已保存: {model_path}")
    else:
        print("⚠ 无法获取训练数据，使用未训练的代理")
    
    # ==================== 3. 创建实盘交易器 ====================
    print("\n【步骤 3：创建实盘交易器】")
    
    trader = LiveTrader(
        trading_interface=trading,
        signal_generator=signal_gen,
        rl_agent=rl_agent,
        data_wrapper=data_wrapper
    )
    
    # 设置监控列表
    watch_list = ["600519", "600036", "000001"]
    trader.set_watch_list(watch_list)
    print(f"监控股票: {', '.join(watch_list)}")
    
    # 设置风控参数
    trader.set_risk_limits({
        'max_position_size': 0.3,       # 单仓位最大 30%
        'max_total_positions': 3,       # 最多 3 个持仓
        'stop_loss': -0.05,             # 止损 -5%
        'take_profit': 0.15,            # 止盈 15%
        'max_daily_loss': -0.10         # 单日最大亏损 -10%
    })
    print("风控参数已设置")
    
    # 设置回调
    def on_signal(symbol, signal):
        print(f"[信号] {symbol}: {signal['action']} (置信度 {signal['confidence']:.2%})")
    
    def on_order(symbol, action, price, volume, order_id):
        print(f"[订单] {symbol} {action} @ {price:.2f} x {volume}, ID: {order_id}")
    
    trader.on_signal_callback = on_signal
    trader.on_order_callback = on_order
    
    # ==================== 4. 模拟信号生成 ====================
    print("\n【步骤 4：模拟信号生成】")
    
    # 获取实时数据
    for sym in watch_list[:2]:  # 仅测试前2个
        print(f"\n分析 {sym}:")
        
        data = data_wrapper.get_historical_data(sym, start_date="2023-01-01")
        
        if data is None or data.empty:
            print(f"  ⚠ 无法获取数据")
            continue
        
        current_price = data['close'].iloc[-1]
        
        # AI 信号
        action, confidence, reason = signal_gen.generate_signal(
            sym, current_price, data, None, None
        )
        
        print(f"  当前价格: {current_price:.2f}")
        print(f"  AI 信号: {action} (置信度 {confidence:.2%})")
        print(f"  理由: {reason}")
        
        # RL 信号
        state = rl_agent.get_state(data)
        rl_action = rl_agent.select_action(state, deterministic=True)
        rl_action_name = ['持有', '买入', '卖出'][rl_action]
        print(f"  RL 信号: {rl_action_name}")
    
    # ==================== 5. 查看状态 ====================
    print("\n【步骤 5：交易状态】")
    
    status = trader.get_status()
    
    print(f"总资产: {status['total_assets']:.2f}")
    print(f"可用资金: {status['available_cash']:.2f}")
    print(f"持仓市值: {status['market_value']:.2f}")
    print(f"盈亏: {status['profit_loss']:.2f} ({status['profit_loss']/100000*100:.2f}%)")
    print(f"持仓数量: {status['positions_count']}")
    
    if status['positions']:
        print("\n持仓明细:")
        for pos in status['positions']:
            print(f"  {pos['symbol']}: {pos['volume']}股 @ {pos['avg_price']:.2f}, "
                  f"现价 {pos['current_price']:.2f}, 盈亏 {pos['pnl']:.2f} ({pos['pnl_ratio']:.2%})")
    
    # ==================== 6. 注意事项 ====================
    print("\n" + "=" * 80)
    print("【注意事项】")
    print("=" * 80)
    print("""
1. 本示例使用模拟交易接口，实际部署需要对接真实接口
2. 实盘交易需要：
   - 有效的券商账号和 API 接口
   - 稳定的网络连接
   - 完善的风控系统
   - 充分的测试和验证
3. 风险提示：
   - 量化交易存在风险，请谨慎使用
   - 建议先在模拟盘充分测试
   - 实盘前务必设置好止损止盈
   - 不要投入超过可承受范围的资金
4. 启动实盘交易（示例）:
   # trader.start(interval=60)  # 每60秒检查一次
   # time.sleep(3600)  # 运行1小时
   # trader.stop()
    """)
    
    print("=" * 80)
    print("示例完成！")
    print("=" * 80)


if __name__ == "__main__":
    main()

