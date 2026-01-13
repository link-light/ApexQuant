"""
参数自适应优化器
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from apexquant.ai import DeepSeekClient


class ParameterOptimizer:
    """
    参数自适应优化器
    
    根据实盘表现动态调整策略参数
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """初始化"""
        try:
            self.client = DeepSeekClient(api_key)
            self.ai_enabled = True
        except:
            self.ai_enabled = False
            print("⚠ AI 未启用")
        
        self.performance_history = []
        self.parameter_history = []
    
    def optimize_parameters(self,
                           current_params: Dict,
                           performance: Dict,
                           market_condition: str = "normal") -> Dict:
        """
        优化参数
        
        Args:
            current_params: 当前参数
            performance: 性能指标
            market_condition: 市场状况
        
        Returns:
            优化后的参数
        """
        # 记录历史
        self.performance_history.append(performance)
        self.parameter_history.append(current_params.copy())
        
        # AI 优化
        if self.ai_enabled:
            optimized = self._ai_optimize(current_params, performance, market_condition)
        else:
            optimized = self._rule_based_optimize(current_params, performance)
        
        return optimized
    
    def _ai_optimize(self,
                    current_params: Dict,
                    performance: Dict,
                    market_condition: str) -> Dict:
        """AI 参数优化"""
        
        # 准备数据
        param_info = "\n".join([f"{k}: {v}" for k, v in current_params.items()])
        perf_info = "\n".join([f"{k}: {v}" for k, v in performance.items()])
        
        # 历史趋势
        history_info = ""
        if len(self.performance_history) >= 3:
            recent_perf = self.performance_history[-3:]
            win_rates = [p.get('win_rate', 0) for p in recent_perf]
            returns = [p.get('return', 0) for p in recent_perf]
            
            history_info = f"""
近期表现趋势:
- 胜率: {' -> '.join([f'{w:.2%}' for w in win_rates])}
- 收益率: {' -> '.join([f'{r:.2%}' for r in returns])}
"""
        
        prompt = f"""
你是量化交易参数优化专家。请根据以下信息，建议参数调整。

【当前参数】
{param_info}

【性能表现】
{perf_info}

【市场状况】
{market_condition}

{history_info}

请给出：
1. 参数评估（60字）
2. 需要调整的参数及新值（3-5个）
3. 调整理由（每个20字）

格式：
参数名: 当前值 -> 建议值 (理由)

要求简洁明确，总字数300字内。
"""
        
        messages = [
            {"role": "system", "content": "你是量化交易参数优化专家。"},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = self.client.chat(messages, temperature=0.4, max_tokens=600)
            
            # 解析 AI 建议
            optimized_params = current_params.copy()
            
            # 简单解析（实际应使用更复杂的 NLP）
            lines = response.split('\n')
            for line in lines:
                if '->' in line and ':' in line:
                    try:
                        parts = line.split(':')
                        if len(parts) >= 2:
                            param_name = parts[0].strip()
                            value_part = parts[1].split('->')[1].split('(')[0].strip()
                            
                            # 尝试转换类型
                            if param_name in current_params:
                                current_type = type(current_params[param_name])
                                
                                if current_type == float:
                                    optimized_params[param_name] = float(value_part.replace('%', ''))
                                elif current_type == int:
                                    optimized_params[param_name] = int(float(value_part))
                                else:
                                    optimized_params[param_name] = value_part
                    except:
                        pass
            
            print(f"AI 优化建议:\n{response}\n")
            
            return optimized_params
            
        except Exception as e:
            print(f"AI 优化失败: {e}")
            return self._rule_based_optimize(current_params, performance)
    
    def _rule_based_optimize(self,
                            current_params: Dict,
                            performance: Dict) -> Dict:
        """基于规则的参数优化"""
        
        optimized = current_params.copy()
        
        win_rate = performance.get('win_rate', 0.5)
        profit_loss_ratio = performance.get('profit_loss_ratio', 1.0)
        max_drawdown = performance.get('max_drawdown', 0.0)
        
        # 1. 胜率过低，收紧买入条件
        if win_rate < 0.4:
            if 'signal_threshold' in optimized:
                optimized['signal_threshold'] = min(0.9, optimized['signal_threshold'] * 1.1)
                print(f"胜率低，提高信号阈值: {optimized['signal_threshold']:.2f}")
        
        # 2. 盈亏比差，调整止盈止损
        if profit_loss_ratio < 1.5:
            if 'stop_loss' in optimized:
                optimized['stop_loss'] = max(-0.10, optimized['stop_loss'] * 0.8)
                print(f"盈亏比低，收紧止损: {optimized['stop_loss']:.2%}")
            
            if 'take_profit' in optimized:
                optimized['take_profit'] = min(0.30, optimized['take_profit'] * 1.2)
                print(f"盈亏比低，扩大止盈: {optimized['take_profit']:.2%}")
        
        # 3. 回撤过大，降低仓位
        if max_drawdown > 0.15:
            if 'max_position_size' in optimized:
                optimized['max_position_size'] = max(0.1, optimized['max_position_size'] * 0.8)
                print(f"回撤大，降低仓位: {optimized['max_position_size']:.2%}")
        
        return optimized
    
    def adaptive_adjust(self,
                       trader,
                       performance_window: int = 20) -> bool:
        """
        自适应调整
        
        Args:
            trader: LiveTrader 实例
            performance_window: 性能评估窗口
        
        Returns:
            是否进行了调整
        """
        if len(self.performance_history) < performance_window:
            return False
        
        # 计算最近表现
        recent_perf = self.performance_history[-performance_window:]
        
        avg_win_rate = np.mean([p.get('win_rate', 0) for p in recent_perf])
        avg_return = np.mean([p.get('return', 0) for p in recent_perf])
        max_dd = max([p.get('max_drawdown', 0) for p in recent_perf])
        
        current_performance = {
            'win_rate': avg_win_rate,
            'return': avg_return,
            'max_drawdown': max_dd,
            'profit_loss_ratio': np.mean([p.get('profit_loss_ratio', 1.0) for p in recent_perf])
        }
        
        # 优化参数
        current_params = trader.risk_limits.copy()
        optimized_params = self.optimize_parameters(
            current_params,
            current_performance,
            "normal"
        )
        
        # 应用优化
        if optimized_params != current_params:
            trader.set_risk_limits(optimized_params)
            print("参数已自适应调整")
            return True
        
        return False
    
    def get_optimization_report(self) -> str:
        """获取优化报告"""
        if len(self.parameter_history) < 2:
            return "优化历史不足"
        
        report = "===== 参数优化历史 =====\n\n"
        
        for i, (params, perf) in enumerate(zip(self.parameter_history[-5:], self.performance_history[-5:]), 1):
            report += f"Version {i}:\n"
            report += f"  参数: {params}\n"
            report += f"  胜率: {perf.get('win_rate', 0):.2%}\n"
            report += f"  收益: {perf.get('return', 0):.2%}\n\n"
        
        return report

