# ApexQuant 模拟盘系统

## 项目概述

ApexQuant是一个高性能量化交易模拟平台，采用C++/Python混合架构，专为A股市场设计。

### 核心特性

- **C++高性能引擎** - 订单撮合、账户管理、T+1规则
- **Python灵活业务层** - 数据源、策略、风控、AI增强
- **多数据源支持** - Baostock + AKShare双备份
- **A股规则完整实现** - T+1、涨跌停、手续费/印花税
- **AI交易顾问** - DeepSeek API集成
- **完整风控系统** - 仓位控制、止损止盈、日亏损限制
- **绩效分析** - 夏普比率、最大回撤、胜率等

## 快速开始

### 1. 编译C++模块

```bash
# Windows
build.bat

# Linux/Mac
./build.sh
```

**编译结果**:
- `apexquant_core.cp39-win_amd64.pyd` (353 KB)
- `apexquant_simulation.cp39-win_amd64.pyd` (275 KB)

### 2. 安装依赖

```bash
pip install -r python/requirements.txt
```

### 3. 配置系统

编辑 `config/simulation_config.yaml`:

```yaml
account:
  initial_capital: 100000.0    # 初始资金10万

ai_advisor:
  api_key: "your-deepseek-api-key"  # 填写你的API密钥
```

### 4. 运行演示

```bash
cd python/apexquant
python quick_demo.py
```

## 使用方式

### 方式1: 命令行工具

```bash
# 回测
python run_simulation.py backtest --start 2023-01-01 --end 2023-12-31 --symbols sh.600000

# 实时模拟
python run_simulation.py realtime --symbols sh.600000 --interval 60

# 查看账户
python run_simulation.py account

# 绩效报告
python run_simulation.py performance
```

### 方式2: Python脚本

查看示例: `examples/example_simple_backtest.py`

```python
from simulation import SimulationController

controller = SimulationController()

def my_strategy(controller, date, daily_data):
    # 你的策略逻辑
    pass

controller.start_backtest(
    start_date="2023-01-01",
    end_date="2023-12-31",
    symbols=["sh.600000"],
    strategy_func=my_strategy
)
```

## 系统架构

```
ApexQuant Simulation System
├── C++ Core (High Performance)
│   ├── SimulatedExchange      # 模拟交易所
│   ├── OrderMatcher            # 订单撮合引擎
│   ├── SimulationAccount       # 账户管理
│   └── T+1/Commission/Tax      # A股规则
│
├── Python Business Layer
│   ├── SimulationController    # 核心控制器
│   ├── DataSource              # 多数据源（Baostock+AKShare）
│   ├── RiskManager             # 风控管理
│   ├── PerformanceAnalyzer     # 绩效分析
│   ├── AITradingAdvisor        # AI顾问（DeepSeek）
│   ├── TradingCalendar         # 交易日历
│   └── DatabaseManager         # SQLite数据库
│
└── CLI & Examples
    ├── run_simulation.py       # 命令行工具
    ├── quick_demo.py           # 快速演示
    └── examples/               # 示例脚本
```

## 内置策略

1. **ma_cross** - 均线交叉策略
2. **rsi** - RSI超买超卖策略
3. **buy_hold** - 买入持有策略
4. **ai_driven** - AI驱动策略（需API密钥）

## A股特殊规则

系统完整实现A股规则：

- **T+1** - 当日买入次日可卖
- **涨跌停** - 主板±10%，ST±5%，科创板±20%
- **交易时间** - 09:30-11:30, 13:00-15:00
- **手续费** - 万2.5双向
- **印花税** - 千一卖出

## 数据源说明

### Baostock（主）
- 不受代理影响
- 稳定可靠
- 历史数据完整

### AKShare（备）
- 数据丰富
- 实时行情
- 作为备用

系统自动切换，无需手动干预。

## 风控系统

- 单股最大仓位30%
- 总仓位最大95%
- 单笔最大下单5万元
- 日亏损限制5%
- 止损10%，止盈20%

## 绩效指标

- 总收益率 / 年化收益率
- 最大回撤
- 夏普比率 / 卡玛比率
- 胜率 / 盈亏比
- 交易统计

## 目录结构

```
ApexQuant/
├── cpp/                           # C++核心引擎
│   ├── include/simulation/        # 模拟盘头文件
│   └── src/simulation/            # 模拟盘源文件
├── python/apexquant/
│   ├── simulation/                # 模拟盘Python模块
│   │   ├── config.py              # 配置管理
│   │   ├── database.py            # 数据库
│   │   ├── trading_calendar.py   # 交易日历
│   │   ├── data_source.py         # 数据源适配器
│   │   ├── risk_manager.py        # 风控
│   │   ├── performance_analyzer.py # 绩效分析
│   │   ├── simulation_controller.py # 核心控制器
│   │   ├── ai_advisor.py          # AI顾问
│   │   ├── strategies.py          # 内置策略
│   │   └── cli.py                 # 命令行工具
│   └── data/                      # 数据模块
│       └── multi_source.py        # 多数据源
├── config/
│   └── simulation_config.yaml     # 配置文件
├── examples/                      # 示例脚本
├── data/                          # SQLite数据库
├── logs/                          # 日志文件
└── reports/                       # 绩效报告
```

## 常见问题

### Q1: 如何运行演示？

```bash
cd python/apexquant
python quick_demo.py
```

### Q2: 如何开始回测？

```bash
python run_simulation.py backtest \
  --start 2023-01-01 \
  --end 2023-12-31 \
  --symbols sh.600000 \
  --strategy ma_cross
```

### Q3: 如何配置API密钥？

编辑 `config/simulation_config.yaml`：

```yaml
ai_advisor:
  api_key: "sk-your-deepseek-api-key-here"
```

### Q4: 模块导入失败怎么办？

必须从 `python/apexquant` 目录运行脚本：

```bash
cd python/apexquant
python your_script.py
```

## 下一步

1. 配置API密钥（如需AI功能）
2. 运行快速演示验证系统
3. 尝试运行回测示例
4. 开发自定义策略
5. 开始实时模拟交易

## 技术栈

- **C++17** - 核心引擎
- **Python 3.9+** - 业务逻辑
- **pybind11** - C++/Python绑定
- **SQLite** - 数据存储
- **Baostock/AKShare** - 数据源
- **DeepSeek API** - AI增强
- **CMake** - 编译系统

## 许可证

MIT License

## 联系方式

- GitHub: https://github.com/link-light/ApexQuant
- 问题反馈: GitHub Issues
