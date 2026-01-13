"""
风险计算器
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

try:
    import apexquant_core as aq
    CORE_LOADED = True
except ImportError:
    CORE_LOADED = False


class RiskCalculator:
    """风险指标计算器"""
    
    def __init__(self, use_cpp: bool = True):
        """
        初始化
        
        Args:
            use_cpp: 是否使用 C++ 加速
        """
        self.use_cpp = use_cpp and CORE_LOADED
    
    def calculate_all_metrics(self, 
                             result,
                             benchmark_returns: Optional[List[float]] = None) -> Dict:
        """
        计算所有风险指标
        
        Args:
            result: BacktestResult 对象
            benchmark_returns: 基准收益率（可选）
        
        Returns:
            风险指标字典
        """
        metrics = {}
        
        returns = result.daily_returns if hasattr(result, 'daily_returns') else []
        equity_curve = result.equity_curve if hasattr(result, 'equity_curve') else []
        
        if not returns or not equity_curve:
            return metrics
        
        # 基础指标
        metrics['total_return'] = result.total_return
        metrics['annual_return'] = result.annual_return
        metrics['sharpe_ratio'] = result.sharpe_ratio
        
        # VaR 和 CVaR
        if self.use_cpp:
            metrics['var_95'] = aq.risk.value_at_risk(returns, 0.95)
            metrics['var_99'] = aq.risk.value_at_risk(returns, 0.99)
            metrics['cvar_95'] = aq.risk.conditional_var(returns, 0.95)
            metrics['cvar_99'] = aq.risk.conditional_var(returns, 0.99)
        else:
            sorted_returns = np.sort(returns)
            metrics['var_95'] = -np.percentile(sorted_returns, 5)
            metrics['var_99'] = -np.percentile(sorted_returns, 1)
            
            var_95_threshold = np.percentile(sorted_returns, 5)
            cvar_95_values = sorted_returns[sorted_returns <= var_95_threshold]
            metrics['cvar_95'] = -np.mean(cvar_95_values) if len(cvar_95_values) > 0 else 0
            
            var_99_threshold = np.percentile(sorted_returns, 1)
            cvar_99_values = sorted_returns[sorted_returns <= var_99_threshold]
            metrics['cvar_99'] = -np.mean(cvar_99_values) if len(cvar_99_values) > 0 else 0
        
        # 回撤指标
        if self.use_cpp:
            metrics['max_drawdown'] = aq.risk.max_drawdown(equity_curve)
            metrics['max_dd_duration'] = aq.risk.max_drawdown_duration(equity_curve)
        else:
            peak = equity_curve[0]
            max_dd = 0
            max_duration = 0
            current_duration = 0
            
            for i, value in enumerate(equity_curve):
                if value > peak:
                    peak = value
                    if current_duration > max_duration:
                        max_duration = current_duration
                    current_duration = 0
                else:
                    current_duration += 1
                    dd = (peak - value) / peak
                    max_dd = max(max_dd, dd)
            
            metrics['max_drawdown'] = max_dd
            metrics['max_dd_duration'] = max_duration
        
        # Calmar 比率
        if self.use_cpp and metrics['max_drawdown'] > 0:
            metrics['calmar_ratio'] = aq.risk.calmar_ratio(
                result.annual_return,
                metrics['max_drawdown']
            )
        elif metrics['max_drawdown'] > 0:
            metrics['calmar_ratio'] = result.annual_return / metrics['max_drawdown']
        else:
            metrics['calmar_ratio'] = 0.0
        
        # Sortino 比率
        if self.use_cpp:
            metrics['sortino_ratio'] = aq.risk.sortino_ratio(returns, 0.0, 252)
        else:
            downside_returns = [r for r in returns if r < 0]
            if downside_returns:
                downside_std = np.std(downside_returns)
                annual_return = np.mean(returns) * 252
                metrics['sortino_ratio'] = annual_return / (downside_std * np.sqrt(252))
            else:
                metrics['sortino_ratio'] = 0.0
        
        # Omega 比率
        if self.use_cpp:
            metrics['omega_ratio'] = aq.risk.omega_ratio(returns, 0.0)
        else:
            gains = sum([max(0, r) for r in returns])
            losses = sum([abs(min(0, r)) for r in returns])
            metrics['omega_ratio'] = gains / losses if losses > 0 else float('inf')
        
        # 胜率和盈亏比
        if self.use_cpp:
            metrics['win_rate'] = aq.risk.win_rate(returns)
            metrics['profit_loss_ratio'] = aq.risk.profit_loss_ratio(returns)
        else:
            wins = sum(1 for r in returns if r > 0)
            metrics['win_rate'] = wins / len(returns)
            
            profits = [r for r in returns if r > 0]
            losses = [abs(r) for r in returns if r < 0]
            
            if profits and losses:
                metrics['profit_loss_ratio'] = np.mean(profits) / np.mean(losses)
            else:
                metrics['profit_loss_ratio'] = 0.0
        
        # 尾部比率
        if self.use_cpp:
            metrics['tail_ratio'] = aq.risk.tail_ratio(returns, 0.95)
        else:
            upper = np.percentile(returns, 95)
            lower = np.percentile(returns, 5)
            metrics['tail_ratio'] = abs(upper / lower) if lower != 0 else 0
        
        # 如果有基准收益率，计算 Alpha 和 Beta
        if benchmark_returns and len(benchmark_returns) == len(returns):
            if self.use_cpp:
                metrics['beta'] = aq.risk.beta(returns, benchmark_returns)
                metrics['alpha'] = aq.risk.alpha(returns, benchmark_returns, 0.0, 252)
                metrics['information_ratio'] = aq.risk.information_ratio(
                    returns, benchmark_returns, 252
                )
            else:
                # Python 实现
                returns_array = np.array(returns)
                benchmark_array = np.array(benchmark_returns)
                
                covariance = np.cov(returns_array, benchmark_array)[0, 1]
                benchmark_variance = np.var(benchmark_array)
                
                if benchmark_variance > 0:
                    metrics['beta'] = covariance / benchmark_variance
                    
                    annual_return = np.mean(returns_array) * 252
                    annual_benchmark = np.mean(benchmark_array) * 252
                    metrics['alpha'] = annual_return - metrics['beta'] * annual_benchmark
                    
                    excess_returns = returns_array - benchmark_array
                    tracking_error = np.std(excess_returns) * np.sqrt(252)
                    if tracking_error > 0:
                        metrics['information_ratio'] = np.mean(excess_returns) * 252 / tracking_error
                    else:
                        metrics['information_ratio'] = 0.0
        
        return metrics
    
    def get_risk_level(self, metrics: Dict) -> str:
        """
        评估风险等级
        
        Args:
            metrics: 风险指标字典
        
        Returns:
            风险等级 'low', 'medium', 'high', 'extreme'
        """
        risk_score = 0
        
        # 最大回撤评分
        max_dd = metrics.get('max_drawdown', 0)
        if max_dd > 0.3:
            risk_score += 3
        elif max_dd > 0.2:
            risk_score += 2
        elif max_dd > 0.1:
            risk_score += 1
        
        # VaR 评分
        var_95 = metrics.get('var_95', 0)
        if var_95 > 0.05:
            risk_score += 3
        elif var_95 > 0.03:
            risk_score += 2
        elif var_95 > 0.02:
            risk_score += 1
        
        # 夏普比率评分（负面）
        sharpe = metrics.get('sharpe_ratio', 0)
        if sharpe < 0.5:
            risk_score += 2
        elif sharpe < 1.0:
            risk_score += 1
        
        # 综合评级
        if risk_score >= 6:
            return 'extreme'
        elif risk_score >= 4:
            return 'high'
        elif risk_score >= 2:
            return 'medium'
        else:
            return 'low'

