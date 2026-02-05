# ApexQuant 模拟盘系统使用指南

## 🎯 简介

ApexQuant模拟盘系统是一个高性能的量化交易模拟平台，采用**C++核心引擎 + Python业务层**的混合架构。

### 核心特性

- ✅ **高性能C++引擎**：订单撮合、账户管理、持仓计算
- ✅ **完整的A股规则**：T+1、涨跌停、集合竞价、交易时间
- ✅ **多数据源支持**：Baostock（主）+ AKShare（备）自动切换
- ✅ **智能风控系统**：仓位控制、止损止盈、日亏损熔断
- ✅ **AI交易顾问**：DeepSeek API集成，智能决策辅助
- ✅ **双运行模式**：历史回测（快速）+ 实时跟盘（真实时间）
- ✅ **内置策略库**：均线交叉、RSI、买入持有、AI驱动
- ✅ **完整绩效分析**：夏普比率、最大回撤、胜率等20+指标

## 📦 安装

### 1. 安装Python依赖

```bash
cd python
pip install -r requirements.txt
```

主要依赖：
- `baostock`: 主数据源
- `akshare`: 备份数据源
- `openai`: DeepSeek API客户端
- `pandas`, `numpy`: 数据处理
- `pyyaml`: 配置文件
- `chinesecalendar`: 交易日历

### 2. 编译C++模块

**Windows**:
```bash
build.bat
```

**Linux**:
```bash
./build.sh
```

编译成功后会在 `python/apexquant/` 目录生成 `apexquant_simulation.pyd`（Windows）或 `.so`（Linux）文件。

### 3. 配置API Key（可选，启用AI时需要）

```bash
# Windows
set DEEPSEEK_API_KEY=your_api_key_here

# Linux
export DEEPSEEK_API_KEY=your_api_key_here
```

## 🚀 快速开始

### 1. 回测模式（历史数据快速回放）

```bash
cd python

# 使用均线交叉策略回测
python examples/run_simulation.py \
  --mode backtest \
  --symbol 600519.SH \
  --start-date 2024-01-01 \
  --end-date 2024-12-31 \
  --strategy ma_cross

# 使用AI辅助策略
python examples/run_simulation.py \
  --mode backtest \
  --symbol 600519.SH \
  --start-date 2024-01-01 \
  --end-date 2024-12-31 \
  --strategy ma_cross \
  --use-ai
```

### 2. 实时模式（纸上交易）

```bash
# 实时跟踪市场行情（不下真实订单）
python examples/run_simulation.py \
  --mode realtime \
  --symbol 600519.SH \
  --start-date 2025-02-06 \
  --strategy ma_cross
```

## 📊 使用示例

### Python代码调用

```python
from apexquant.simulation import (
    SimulationController,
    SimulationMode,
    RiskManager,
    get_strategy
)

# 1. 创建控制器
controller = SimulationController(
    mode=SimulationMode.BACKTEST,
    initial_capital=1000000
)

# 2. 初始化风控
risk_manager = RiskManager()

# 3. 选择策略
strategy = get_strategy('ma_cross', risk_manager=risk_manager)

# 4. 启动回测
controller.start('2024-01-01', '2024-12-31', ['600519.SH'])

# 5. 运行策略
controller.run(strategy, ['600519.SH'])

# 6. 生成报告
from apexquant.simulation import PerformanceAnalyzer
report = PerformanceAnalyzer.generate_report(
    controller.account_id,
    controller.config.database_path
)
print(report)
```

## 🎓 内置策略

### 1. 均线交叉策略（ma_cross）

```bash
python examples/run_simulation.py --strategy ma_cross
```

- MA5上穿MA20 → 买入
- MA5下穿MA20 → 卖出
- 支持AI辅助确认（--use-ai）

### 2. RSI策略（rsi）

```bash
python examples/run_simulation.py --strategy rsi
```

- RSI < 30 → 超卖，买入
- RSI > 70 → 超买，卖出

### 3. 买入持有（buy_hold）

```bash
python examples/run_simulation.py --strategy buy_hold
```

- 第一根K线用80%资金买入
- 一直持有（测试用）

### 4. AI驱动策略（ai_driven）

```bash
python examples/run_simulation.py --strategy ai_driven --use-ai
```

- 完全由AI决策
- 每5分钟调用一次
- 置信度>0.7才执行

## ⚙️ 配置文件

配置文件：`config/simulation_config.yaml`

```yaml
simulation:
  initial_capital: 1000000
  database_path: data/sim_trader.db

trading:
  commission_rate: 0.00025  # 万2.5
  stamp_tax_rate: 0.001     # 千一（卖出）
  slippage_rate: 0.0001     # 万一

risk:
  max_single_position_pct: 0.20  # 单品种20%
  max_total_position_pct: 0.80   # 总仓位80%
  max_daily_loss_pct: 0.05       # 日亏损5%熔断
  stop_loss_pct: 0.10            # 止损10%
  take_profit_pct: 0.20          # 止盈20%

ai:
  enabled: false
  model: deepseek-chat
  call_interval_minutes: 5
  daily_call_limit: 100
  confidence_threshold: 0.7

data_source:
  provider: baostock  # 主数据源
  backup_provider: akshare  # 备份
  frequency: 1min
```

## 📈 绩效报告

运行结束后会生成详细报告：

```
============================================================
ApexQuant Performance Report
============================================================
Account ID: SIM1234567890123
Strategy: ma_cross
Trading Days: 245.0

=== Return Metrics ===
Initial Capital: 1,000,000.00
Final Assets: 1,150,000.00
Total Return: 15.00%
Annual Return: 22.35%

=== Risk Metrics ===
Max Drawdown: 8.50%
Sharpe Ratio: 1.85
Calmar Ratio: 2.63

=== Trading Statistics ===
Total Trades: 156
Win Rate: 58.50%
Avg Profit/Trade: 961.54
Profit Factor: 1.85
Max Consecutive Wins: 8
Max Consecutive Losses: 5
============================================================
```

## 🧪 测试

### 运行单元测试

```bash
cd python
python tests/test_simulation.py
```

### 运行集成测试

```bash
cd python
python tests/test_integration.py
```

## 📁 项目结构

```
ApexQuant/
├── cpp/
│   ├── include/simulation/     # C++头文件
│   │   ├── simulation_types.h       # 数据结构
│   │   ├── simulation_account.h     # 账户管理
│   │   ├── order_matcher.h          # 订单撮合
│   │   └── simulated_exchange.h     # 模拟交易所
│   └── src/simulation/          # C++源文件
│       ├── simulation_account.cpp
│       ├── order_matcher.cpp
│       ├── simulated_exchange.cpp
│       └── bindings.cpp             # Python绑定
├── python/apexquant/simulation/
│   ├── database.py              # 数据库管理
│   ├── simulation_controller.py # 核心控制器
│   ├── config.py                # 配置管理
│   ├── trading_calendar.py      # 交易日历
│   ├── data_source.py           # 数据源适配
│   ├── risk_manager.py          # 风控管理
│   ├── performance_analyzer.py  # 绩效分析
│   ├── ai_advisor.py            # AI顾问
│   └── strategies.py            # 策略库
├── config/
│   └── simulation_config.yaml   # 配置文件
└── examples/
    └── run_simulation.py        # CLI运行脚本
```

## 🔧 高级用法

### 自定义策略

```python
def my_custom_strategy(controller, bar, account_info):
    """自定义策略函数"""
    symbol = bar['symbol']
    close = bar['close']
    
    # 你的策略逻辑
    if close > some_threshold:
        return {
            'action': 'BUY',
            'symbol': symbol,
            'volume': 1000,
            'price': None  # 市价单
        }
    
    return None  # HOLD

# 使用自定义策略
controller.run(my_custom_strategy, ['600519.SH'])
```

### 多股票组合

```python
symbols = ['600519.SH', '000001.SZ', '600036.SH']
controller.start('2024-01-01', '2024-12-31', symbols)
controller.run(strategy, symbols)
```

## ❓ 常见问题

**Q: 编译失败怎么办？**

A: 确保安装了：
- Windows: Visual Studio 2019+（C++工具）
- Linux: gcc/g++ 7+
- CMake 3.15+
- pybind11

**Q: 数据获取失败？**

A: 系统自动使用Baostock（主）+ AKShare（备）双数据源，正常情况至少一个可用。如果都失败，可以使用Mock数据源测试。

**Q: AI API调用失败？**

A: 检查：
1. DEEPSEEK_API_KEY环境变量是否设置
2. 网络连接是否正常
3. API余额是否充足

**Q: 如何查看历史账户？**

A: 数据保存在SQLite数据库中（默认`data/sim_trader.db`），可以使用任何SQLite工具查看。

## 📞 技术支持

遇到问题？
1. 查看日志：`logs/simulation.log`
2. 运行测试：`python tests/test_simulation.py`
3. 查看数据库：打开 `data/sim_trader.db`

## 🎉 完成状态

✅ **所有20个核心任务已完成（100%）**

- Phase 1: C++核心引擎（7/7）
- Phase 2: Python业务层（6/6）
- Phase 3: AI增强（1/1）
- Phase 4: CLI工具（2/2）
- Phase 5: 测试（3/3）
- Phase 0: 基础设施（1/1）

---

**Happy Trading! 🚀**
