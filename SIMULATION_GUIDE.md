# ApexQuant 模拟盘系统使用手册

## 系统概述

ApexQuant模拟盘系统是一个高性能的量化交易模拟平台，采用C++/Python混合架构：

- **C++核心引擎**：高性能订单撮合、账户管理、T+1规则
- **Python业务层**：数据源、策略、风控、AI增强、绩效分析

## 快速开始

### 1. 编译C++模块

```bash
# Windows
build.bat

# Linux/Mac
./build.sh
```

### 2. 安装Python依赖

```bash
pip install -r python/requirements.txt
```

### 3. 配置系统

编辑 `config/simulation_config.yaml`：

```yaml
account:
  initial_capital: 100000.0    # 初始资金
  
risk_control:
  max_single_position_pct: 0.3  # 单股最大仓位30%
  enable_risk_control: true     # 启用风控
  
ai_advisor:
  enabled: true                  # 启用AI顾问
  api_key: "your-api-key-here"  # DeepSeek API密钥
```

### 4. 运行演示

```bash
cd python/apexquant
python quick_demo.py
```

## 使用方式

### 方式一：命令行工具

#### 运行回测

```bash
python run_simulation.py backtest \
  --start 2023-01-01 \
  --end 2023-12-31 \
  --symbols sh.600000,sh.600036 \
  --strategy ma_cross
```

#### 运行实时模拟

```bash
python run_simulation.py realtime \
  --symbols sh.600000 \
  --strategy ma_cross \
  --interval 60
```

#### 查看账户信息

```bash
python run_simulation.py account
```

#### 生成绩效报告

```bash
python run_simulation.py performance --output report.txt
```

### 方式二：Python脚本

创建自定义策略脚本：

```python
import os
import sys
from pathlib import Path

# 设置路径
sys.path.insert(0, 'path/to/python')
os.chdir('path/to/python/apexquant')

from simulation import SimulationController

# 创建控制器
controller = SimulationController()

# 定义策略
def my_strategy(controller, date, daily_data):
    # 你的策略逻辑
    for symbol, df in daily_data.items():
        if not df.empty:
            close_price = df.iloc[-1]['close']
            
            # 买入信号
            if close_price < some_threshold:
                controller.submit_order(
                    symbol=symbol,
                    side='buy',
                    order_type='limit',
                    volume=100,
                    price=close_price
                )

# 运行回测
controller.start_backtest(
    start_date="2023-01-01",
    end_date="2023-12-31",
    symbols=["sh.600000"],
    strategy_func=my_strategy
)
```

## 核心功能

### 1. 账户管理

```python
# 获取账户信息
account = controller.get_account_info()
print(f"Available Cash: {account['available_cash']}")
print(f"Total Assets: {account['total_assets']}")

# 获取持仓
positions = controller.get_positions()
for pos in positions:
    print(f"{pos['symbol']}: {pos['volume']} @ {pos['avg_cost']}")
```

### 2. 订单管理

```python
# 提交订单
order_id = controller.submit_order(
    symbol="sh.600000",
    side="buy",          # 'buy' or 'sell'
    order_type="limit",  # 'market' or 'limit'
    volume=100,
    price=10.50
)

# 撤单
controller.cancel_order(order_id)

# 查询待成交订单
pending = controller.get_pending_orders()
```

### 3. 数据获取

```python
from simulation import SimulationDataSource

data_source = SimulationDataSource()

# 获取历史数据
df = data_source.get_stock_data(
    symbol="sh.600000",
    start_date="2023-01-01",
    end_date="2023-12-31",
    freq="d"  # 'd'=日线, 'w'=周线, 'm'=月线
)

# 获取实时行情
quotes = data_source.get_realtime_quotes(["sh.600000", "sh.600036"])

# 获取最新价格
price = data_source.get_latest_price("sh.600000")
```

### 4. 风控管理

```python
from simulation import RiskManager

risk_manager = RiskManager(config.get_risk_config())

# 检查订单风控
result = risk_manager.check_order(
    symbol="sh.600000",
    side="buy",
    price=10.0,
    volume=100,
    current_position=0,
    available_cash=100000,
    total_assets=100000,
    current_positions={}
)

if result.is_pass():
    print("Risk check passed")
else:
    print(f"Risk check failed: {result.reason}")
```

### 5. AI交易顾问

```python
from simulation import AITradingAdvisor

ai_advisor = AITradingAdvisor()

# 获取交易建议
advice = ai_advisor.get_trading_advice(
    symbol="sh.600000",
    market_data=market_data,
    account_info=account_info,
    positions=positions
)

print(f"AI Advice: {advice['action']}")
print(f"Reason: {advice['reasoning']}")
```

## 内置策略

### 1. 均线交叉策略 (ma_cross)

- 短期均线（默认5日）
- 长期均线（默认20日）
- 金叉买入，死叉卖出

### 2. RSI策略 (rsi)

- 超卖区（RSI < 30）买入
- 超买区（RSI > 70）卖出

### 3. 买入持有策略 (buy_hold)

- 开始时全仓买入
- 持有到结束

### 4. AI驱动策略 (ai_driven)

- 使用DeepSeek API分析市场
- 智能决策买卖时机

## 配置说明

### 账户配置

```yaml
account:
  account_id: simulation_001      # 账户ID
  initial_capital: 100000.0       # 初始资金（元）
  commission_rate: 0.00025        # 手续费率（万2.5）
  stamp_tax_rate: 0.001           # 印花税率（千一，仅卖出）
  slippage_rate: 0.0001           # 滑点率（万一）
```

### 风控配置

```yaml
risk_control:
  max_single_position_pct: 0.3         # 单股最大仓位30%
  max_total_position_pct: 0.95         # 总仓位最大95%
  max_single_order_amount: 50000.0     # 单笔最大下单5万元
  daily_loss_limit_pct: 0.05           # 日亏损限制5%
  stop_loss_pct: 0.1                   # 止损比例10%
  take_profit_pct: 0.2                 # 止盈比例20%
  enable_risk_control: true            # 是否启用风控
```

### 数据源配置

```yaml
data_source:
  primary: baostock      # 主数据源（不受代理影响）
  backup: akshare        # 备用数据源
  proxy: null            # 代理设置
```

### AI顾问配置

```yaml
ai_advisor:
  enabled: true                        # 是否启用
  model: deepseek-chat                 # 模型
  api_key: ""                          # API密钥
  base_url: "https://api.deepseek.com"
  max_calls_per_day: 100               # 每日最大调用次数
  temperature: 0.7
  max_tokens: 2000
```

## 数据源说明

系统支持双数据源自动切换：

1. **Baostock（主）** - 不受代理影响，稳定可靠
2. **AKShare（备）** - 数据丰富，作为备用

系统会自动尝试主数据源，失败后切换到备用数据源。

## A股特殊规则

系统已实现以下A股规则：

1. **T+1规则** - 当日买入次日才能卖出
2. **涨跌停限制**：
   - 主板：±10%
   - ST股票：±5%
   - 科创板/创业板注册制：±20%
   - 新股首日：±30% 或更高
3. **交易时间**：
   - 上午：09:30 - 11:30
   - 下午：13:00 - 15:00
4. **手续费/印花税**：
   - 手续费：双向收取（万2.5）
   - 印花税：仅卖出收取（千一）

## 数据库结构

系统使用SQLite存储数据：

- **accounts** - 账户信息
- **positions** - 持仓记录
- **orders** - 订单记录
- **trades** - 成交记录
- **equity_curve** - 权益曲线
- **ai_decisions** - AI决策记录
- **market_events** - 市场事件

## 性能指标

系统会计算以下绩效指标：

- **收益率**：总收益率、年化收益率
- **风险指标**：最大回撤、夏普比率、卡玛比率
- **交易统计**：胜率、盈亏比、交易次数
- **时间统计**：交易天数、持仓天数

## 常见问题

### Q1: 模块导入失败

**问题**：`ModuleNotFoundError: No module named 'apexquant_core'`

**解决**：
```bash
# 方式1：在python/apexquant目录运行
cd python/apexquant
python your_script.py

# 方式2：设置PYTHONPATH
set PYTHONPATH=d:\ApexQuant\python
cd python\apexquant
python your_script.py
```

### Q2: 编码错误

**问题**：`UnicodeEncodeError: 'gbk' codec can't encode`

**解决**：避免在脚本中使用非ASCII字符（如中文、特殊符号）

### Q3: 数据源连接失败

**问题**：无法获取数据

**解决**：
- 检查网络连接
- 系统会自动切换到备用数据源
- 如果使用代理，Baostock通常不受影响

### Q4: AI顾问调用失败

**问题**：`No API key provided`

**解决**：在 `config/simulation_config.yaml` 中设置API密钥

## 目录结构

```
ApexQuant/
├── cpp/                    # C++核心引擎
│   ├── include/
│   │   └── simulation/    # 模拟盘头文件
│   └── src/
│       └── simulation/    # 模拟盘源文件
├── python/
│   └── apexquant/
│       └── simulation/    # 模拟盘Python模块
│           ├── config.py
│           ├── database.py
│           ├── trading_calendar.py
│           ├── data_source.py
│           ├── risk_manager.py
│           ├── performance_analyzer.py
│           ├── simulation_controller.py
│           ├── ai_advisor.py
│           ├── strategies.py
│           └── cli.py
├── config/                # 配置文件
├── examples/              # 示例脚本
├── data/                  # 数据库存储
└── logs/                  # 日志文件
```

## 下一步

1. 修改配置文件设置初始资金和API密钥
2. 运行简单回测示例测试系统
3. 开发自定义策略
4. 进行完整回测和性能评估
5. 开始实时模拟交易

## 技术支持

- 查看示例：`examples/` 目录
- 查看文档：`docs/` 目录
- 问题反馈：GitHub Issues
