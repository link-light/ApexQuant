"""
ApexQuant 回测模块
"""

from .strategy import Strategy
from .backtest_runner import BacktestRunner
from .performance import PerformanceAnalyzer
from .optimizer import ParameterOptimizer
from .strategy_backtester import StrategyBacktester, BacktestResult
from .plotly_charts import (
    create_equity_curve_chart,
    create_drawdown_chart,
    create_trade_analysis_chart,
    create_monthly_returns_heatmap,
    create_optimization_chart,
    create_strategy_comparison_chart,
)

__all__ = [
    'Strategy', 'BacktestRunner', 'PerformanceAnalyzer',
    'ParameterOptimizer', 'StrategyBacktester', 'BacktestResult',
    'create_equity_curve_chart', 'create_drawdown_chart',
    'create_trade_analysis_chart', 'create_monthly_returns_heatmap',
    'create_optimization_chart', 'create_strategy_comparison_chart',
]

