# ApexQuant 待完善功能清单

## 1. 数据源问题
- [ ] 确保 baostock、akshare 正确安装和配置
- [ ] 添加数据源连接状态检测
- [ ] 数据获取失败时给出明确提示
- [ ] 支持更多数据源（tushare、通联数据等）

## 2. 回测系统完善
- [ ] 完善回测指标计算（最大回撤、夏普比率等）
- [ ] 添加回测结果可视化（收益曲线、回撤曲线）
- [ ] 支持参数优化和敏感性分析
- [ ] 添加交易成本模型（滑点、冲击成本）

## 3. 交易策略升级 ✅ 已完成

- [x] **多因子选股策略** ✅
  - 市值因子、动量因子、价值因子、质量因子
  - 因子合成与权重优化
  - 实现: `strategy/multi_factor_strategy.py`

- [x] **机器学习策略** ✅
  - LSTM/GRU 价格预测
  - XGBoost/LightGBM 涨跌分类
  - 实现: `strategy/lstm_predictor.py`, `strategy/ml_model.py`

- [x] **事件驱动策略** ✅
  - 财报发布套利
  - 股东增减持跟踪
  - 大宗交易信号
  - 实现: `strategy/event_strategy.py`

- [x] **统计套利策略** ✅
  - 配对交易
  - 协整关系挖掘
  - 实现: `strategy/pairs_trading.py`

## 4. AI智能分析系统（核心亮点）✅ 已完成

将DeepSeek AI打造为智能投顾核心：

### 4.1 数据输入层
- [x] **技术指标**：MA、RSI、MACD、布林带、KDJ、ATR等 ✅
- [x] **基本面数据**：PE、PB、ROE、营收增长、净利润等 ✅
  - 实现: `data/fundamental_fetcher.py`
- [x] **资金流向**：主力资金、北向资金、融资融券 ✅
  - 实现: `data/capital_flow.py`
- [ ] **市场情绪**：涨跌家数、换手率、波动率指数
- [x] **新闻舆情**：公司公告、行业新闻、政策解读 ✅
  - 实现: `data/news_fetcher.py`
- [ ] **宏观经济**：GDP、CPI、利率、汇率

### 4.2 AI分析输出 ✅ 已完成
- [x] 买入/卖出/持有 建议
- [x] 置信度评分 (0-100%)
- [x] 仓位建议（建仓/加仓/减仓/清仓/观望）
- [x] 详细分析理由
- [x] 风险提示
- [x] 目标价/止损价

### 4.3 实现优先级
1. **P0**: 技术指标 + 基本面 → AI分析 ✅ 已完成
2. **P1**: 新闻舆情接入 ✅ 已完成
3. **P2**: 资金流向分析 ✅ 已完成
4. **P3**: 宏观经济数据

### 4.4 已实现模块
- `analysis/technical_indicators.py` - 完整技术指标计算
- `ai/smart_advisor.py` - SmartTradingAdvisor智能顾问 (支持全面分析)
- `data/news_fetcher.py` - 新闻数据获取
- `data/fundamental_fetcher.py` - 基本面数据获取
- `data/capital_flow.py` - 资金流向数据获取
- `gui/pages/5_AI智能分析.py` - GUI界面

### 4.5 交易策略模块
- `strategy/factor_engine.py` - 因子引擎（技术指标计算）
- `strategy/multi_factor_strategy.py` - 多因子选股策略
- `strategy/lstm_predictor.py` - LSTM/GRU深度学习预测
- `strategy/ml_model.py` - XGBoost机器学习模型
- `strategy/event_strategy.py` - 事件驱动策略
- `strategy/pairs_trading.py` - 配对交易/统计套利
- `strategy/ai_factor_generator.py` - AI因子生成器

---

## 开发顺序建议

1. ~~先修复数据源问题，确保回测能跑通~~
2. ~~完善AI分析系统（核心差异化）~~ ✅
3. ~~升级交易策略~~ ✅
4. 优化回测系统

**目标**：让ApexQuant成为真正的AI驱动量化交易平台，而不是又一个普通的回测工具。

---

## 下一步计划

- [ ] 添加策略GUI界面（多因子/事件驱动/配对交易）
- [ ] 完善回测系统，支持新策略
- [ ] 添加市场情绪指标
- [ ] 添加宏观经济数据接入
- [ ] 优化数据源连接和错误处理
