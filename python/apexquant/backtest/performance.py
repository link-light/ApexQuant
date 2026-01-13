"""
性能分析器
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))


class PerformanceAnalyzer:
    """性能分析器"""
    
    def __init__(self):
        pass
    
    def analyze(self, result, data: pd.DataFrame) -> Dict:
        """
        分析回测结果
        
        Args:
            result: BacktestResult 对象
            data: 原始数据
        
        Returns:
            分析结果字典
        """
        analysis = {
            'basic_stats': self._basic_stats(result),
            'risk_metrics': self._risk_metrics(result),
            'trade_stats': self._trade_stats(result),
            'monthly_returns': self._monthly_returns(result, data),
        }
        
        return analysis
    
    def _basic_stats(self, result) -> Dict:
        """基础统计"""
        return {
            'total_return': result.total_return,
            'annual_return': result.annual_return,
            'total_trades': result.total_trades,
            'winning_trades': result.winning_trades,
            'losing_trades': result.losing_trades,
            'win_rate': result.win_rate,
        }
    
    def _risk_metrics(self, result) -> Dict:
        """风险指标"""
        metrics = {
            'sharpe_ratio': result.sharpe_ratio,
            'max_drawdown': result.max_drawdown,
            'volatility': 0.0,
            'calmar_ratio': 0.0,
            'sortino_ratio': 0.0,
        }
        
        # 波动率
        if result.daily_returns:
            metrics['volatility'] = np.std(result.daily_returns) * np.sqrt(252)
        
        # Calmar 比率
        if result.max_drawdown > 0:
            metrics['calmar_ratio'] = result.annual_return / result.max_drawdown
        
        # Sortino 比率（只考虑下行风险）
        if result.daily_returns:
            returns = np.array(result.daily_returns)
            downside_returns = returns[returns < 0]
            if len(downside_returns) > 0:
                downside_std = np.std(downside_returns)
                if downside_std > 0:
                    mean_return = np.mean(returns)
                    metrics['sortino_ratio'] = (mean_return / downside_std) * np.sqrt(252)
        
        return metrics
    
    def _trade_stats(self, result) -> Dict:
        """交易统计"""
        stats = {
            'total_commission': result.total_commission,
            'total_slippage': result.total_slippage,
            'avg_commission_per_trade': 0.0,
            'avg_slippage_per_trade': 0.0,
        }
        
        if result.total_trades > 0:
            stats['avg_commission_per_trade'] = result.total_commission / result.total_trades
            stats['avg_slippage_per_trade'] = result.total_slippage / result.total_trades
        
        return stats
    
    def _monthly_returns(self, result, data: pd.DataFrame) -> pd.Series:
        """月度收益率"""
        if not hasattr(result, 'equity_curve') or len(result.equity_curve) == 0:
            return pd.Series()
        
        # 转换为 DataFrame
        equity_df = pd.DataFrame({
            'equity': result.equity_curve
        })
        
        if 'date' in data.columns:
            equity_df['date'] = pd.to_datetime(data['date'].iloc[:len(result.equity_curve)])
            equity_df.set_index('date', inplace=True)
            
            # 计算月度收益
            monthly = equity_df.resample('M').last()
            monthly_returns = monthly['equity'].pct_change()
            
            return monthly_returns
        
        return pd.Series()
    
    def print_report(self, analysis: Dict):
        """
        打印报告
        
        Args:
            analysis: 分析结果
        """
        print("\n" + "="*60)
        print("回测报告")
        print("="*60)
        
        # 基础统计
        basic = analysis['basic_stats']
        print("\n基础统计:")
        print(f"  总收益率: {basic['total_return']:.2%}")
        print(f"  年化收益率: {basic['annual_return']:.2%}")
        print(f"  总交易次数: {basic['total_trades']}")
        print(f"  盈利交易: {basic['winning_trades']}")
        print(f"  亏损交易: {basic['losing_trades']}")
        print(f"  胜率: {basic['win_rate']:.2%}")
        
        # 风险指标
        risk = analysis['risk_metrics']
        print("\n风险指标:")
        print(f"  夏普比率: {risk['sharpe_ratio']:.3f}")
        print(f"  最大回撤: {risk['max_drawdown']:.2%}")
        print(f"  波动率: {risk['volatility']:.2%}")
        print(f"  Calmar 比率: {risk['calmar_ratio']:.3f}")
        print(f"  Sortino 比率: {risk['sortino_ratio']:.3f}")
        
        # 交易成本
        trade = analysis['trade_stats']
        print("\n交易成本:")
        print(f"  总手续费: {trade['total_commission']:.2f}")
        print(f"  总滑点: {trade['total_slippage']:.2f}")
        print(f"  平均手续费/笔: {trade['avg_commission_per_trade']:.2f}")
        print(f"  平均滑点/笔: {trade['avg_slippage_per_trade']:.2f}")
        
        print("\n" + "="*60)

