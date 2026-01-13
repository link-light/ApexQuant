# Day 8: 实盘基础 + AI 信号生成 ✅

## 完成内容

### 1. C++ 交易接口
- **ITradingInterface**: 统一交易接口抽象层
- **SimulatedTrading**: 模拟盘实现（完整订单、持仓、账户管理）
- **ConnectionManager**: 心跳检测和断线重连机制

#### 核心功能
- 订单管理：提交、撤销、查询
- 账户管理：资金、持仓、成交查询
- 回调机制：订单、成交、错误回调
- 风控检查：资金、持仓验证

### 2. 心跳和重连
- 自动心跳检测（可配置间隔）
- 超时检测和断线回调
- 指数退避重连策略
- 重连次数限制

### 3. AI 信号生成器
- **AISignalGenerator**: 基于 DeepSeek 的实时信号生成
- 综合技术指标、新闻、持仓信息
- 批量信号生成和过滤
- 规则信号回退机制

### 4. 强化学习代理
- **RLTradingAgent**: 简化版 Q-learning 交易代理
- 状态提取：价格、均线、动量、RSI、MACD 等
- 动作选择：持有、买入、卖出
- 在线学习和模型持久化

### 5. 实盘交易管理器
- **LiveTrader**: 完整交易流程管理
- 多策略信号融合（AI + RL）
- 全面风控系统
- 自动化交易执行

#### 风控机制
- 单仓位大小限制
- 最大持仓数量限制
- 止损止盈自动触发
- 单日亏损限制

## 核心文件
```
cpp/
  include/
    trading_interface.h        # 交易接口定义
    connection_manager.h       # 连接管理器
  src/
    trading_interface.cpp      # 模拟盘实现
    connection_manager.cpp     # 心跳重连实现
python/
  apexquant/live/
    signal_generator.py        # AI 信号生成
    rl_agent.py                # RL 交易代理
    live_trader.py             # 实盘管理器
```

## 使用示例

### 1. AI 信号生成
```python
from apexquant.live import AISignalGenerator

generator = AISignalGenerator(api_key="your_key")
action, confidence, reason = generator.generate_signal(
    symbol="600519",
    current_price=1800.0,
    data=historical_data,
    news=recent_news,
    position=current_position
)
```

### 2. RL 代理
```python
from apexquant.live import RLTradingAgent

agent = RLTradingAgent(state_dim=10, action_dim=3)

# 训练
result = agent.train_episode(data)

# 推理
state = agent.get_state(data, position)
action = agent.select_action(state)
```

### 3. 实盘交易
```python
from apexquant.live import LiveTrader

trader = LiveTrader(
    trading_interface=trading,
    signal_generator=signal_gen,
    rl_agent=rl_agent
)

trader.set_watch_list(["600519", "600036"])
trader.set_risk_limits({
    'max_position_size': 0.3,
    'stop_loss': -0.05,
    'take_profit': 0.15
})

trader.start(interval=60)  # 每60秒检查
```

## 测试
```bash
# 运行测试
python python/tests/test_day8.py

# 完整示例
python examples/example_day8.py
```

## 风险提示
⚠️ **重要提醒**：
1. 本系统为学习和研究用途
2. 实盘交易有风险，请谨慎使用
3. 务必先在模拟盘充分测试
4. 不要投入超过可承受范围的资金
5. 建议咨询专业投资顾问

## 接口对接说明
要对接真实交易接口（QMT/XTP等）：
1. 继承 `ITradingInterface` 基类
2. 实现所有虚函数
3. 处理异步回调
4. 实现订单薄管理
5. 添加真实的错误处理

## 下一步
Day 9: 实盘整合 + AI 自适应

