# Day 7: 数据分析与风险评估 + AI 报告 ✅

## 完成内容

### 1. C++ 高级风险指标
- **VaR & CVaR**: 95% 和 99% 置信水平的风险价值
- **Calmar**: 年化收益/最大回撤
- **Sortino**: 仅考虑下行风险的夏普比率
- **Omega**: 收益/损失比率
- **Alpha & Beta**: 相对市场表现
- **Information Ratio**: 超额收益/跟踪误差
- **Tail Ratio**: 尾部风险比率

### 2. Python 风险管理系统
- **RiskCalculator**: 全面风险指标计算，支持 C++/Python 双模式
- **RiskReporter**: AI 驱动的风险报告生成
- **StressTestGenerator**: 压力测试场景生成和执行

### 3. AI 功能
- **风险评估报告**: DeepSeek 自动生成专业风险分析
- **风控建议**: 针对性风险控制措施
- **策略对比**: 多策略风险对比分析
- **压力场景**: AI 生成黑天鹅场景

### 4. 压力测试场景
- 市场崩盘 (-20% 冲击)
- 流动性危机 (滑点翻倍)
- 黑天鹅事件 (-30% 极端冲击)
- 波动率飙升 (6x 波动率)
- 缓慢熊市 (长期温和下跌)

## 核心文件
```
cpp/
  include/risk_metrics.h      # 风险指标接口
  src/risk_metrics.cpp         # C++ 实现
python/
  apexquant/risk/
    risk_calculator.py         # 风险计算器
    risk_reporter.py           # AI 报告生成
    stress_test.py             # 压力测试
```

## 使用示例
```python
from apexquant.risk import RiskCalculator, RiskReporter, StressTestGenerator

# 1. 计算风险指标
calculator = RiskCalculator(use_cpp=True)
metrics = calculator.calculate_all_metrics(backtest_result)

# 2. 生成 AI 报告
reporter = RiskReporter(api_key="your_key")
report = reporter.generate_risk_report(metrics, "策略名")

# 3. 压力测试
stress_tester = StressTestGenerator()
results = stress_tester.run_stress_tests(strategy, runner, data, params)
```

## 测试
```bash
# 运行测试
python python/tests/test_day7.py

# 完整示例
python examples/example_day7.py
```

## 风险指标说明
| 指标 | 含义 | 理想值 |
|------|------|--------|
| VaR 95% | 5%概率最大损失 | < 3% |
| CVaR 95% | 极端损失期望 | < 5% |
| Max Drawdown | 最大回撤 | < 20% |
| Calmar | 收益/回撤比 | > 1.0 |
| Sortino | 下行风险夏普 | > 1.5 |
| Omega | 收益/损失比 | > 1.5 |
| Tail Ratio | 尾部风险比 | > 1.0 |

## 下一步
Day 8: 实盘基础 + AI 信号生成

