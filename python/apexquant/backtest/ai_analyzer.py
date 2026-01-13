"""
AI 回测分析器
"""

import pandas as pd
from typing import Dict, List, Optional
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from apexquant.ai import DeepSeekClient


class AIBacktestAnalyzer:
    """AI 驱动的回测分析器"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化
        
        Args:
            api_key: DeepSeek API key
        """
        try:
            self.client = DeepSeekClient(api_key)
            self.ai_enabled = True
        except:
            self.ai_enabled = False
            print("AI 未启用")
    
    def analyze_result(self, result, strategy_name: str = "策略") -> str:
        """
        分析回测结果并给出建议
        
        Args:
            result: BacktestResult 对象
            strategy_name: 策略名称
        
        Returns:
            AI 分析报告
        """
        if not self.ai_enabled:
            return "AI 分析不可用"
        
        # 准备数据摘要
        summary = f"""
策略：{strategy_name}

回测结果：
- 总收益率：{result.total_return:.2%}
- 年化收益率：{result.annual_return:.2%}
- 夏普比率：{result.sharpe_ratio:.3f}
- 最大回撤：{result.max_drawdown:.2%}
- 交易次数：{result.total_trades}
- 胜率：{result.win_rate:.2%}
- 盈利交易：{result.winning_trades}
- 亏损交易：{result.losing_trades}
- 总手续费：{result.total_commission:.2f}
- 总滑点：{result.total_slippage:.2f}
"""
        
        prompt = f"""
你是一个专业的量化策略分析师。请分析以下回测结果，并给出改进建议。

{summary}

请从以下角度分析：
1. 整体表现评价（50字内）
2. 主要优点（2-3点）
3. 主要问题（2-3点）
4. 改进建议（3-5点，具体可操作）

要求：
- 专业、简洁
- 建议要具体，可直接执行
- 总字数控制在300字内
"""
        
        messages = [
            {"role": "system", "content": "你是一个专业的量化策略分析师。"},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = self.client.chat(messages, temperature=0.6, max_tokens=600)
            return response
        except Exception as e:
            return f"AI 分析失败: {e}"
    
    def compare_strategies(self, 
                          results: List[Dict],
                          names: List[str]) -> str:
        """
        对比多个策略
        
        Args:
            results: 回测结果列表
            names: 策略名称列表
        
        Returns:
            对比分析报告
        """
        if not self.ai_enabled:
            return "AI 分析不可用"
        
        # 准备对比数据
        comparison_data = []
        for name, result in zip(names, results):
            comparison_data.append(f"""
{name}：
  收益率: {result.total_return:.2%}
  夏普比率: {result.sharpe_ratio:.3f}
  最大回撤: {result.max_drawdown:.2%}
  胜率: {result.win_rate:.2%}
""")
        
        comparison_text = "\n".join(comparison_data)
        
        prompt = f"""
请对比以下策略的回测结果，给出分析和推荐：

{comparison_text}

要求：
1. 综合评价各策略（100字内）
2. 推荐最佳策略并说明理由（80字内）
3. 给出优化方向（3点建议）

总字数250字内。
"""
        
        messages = [
            {"role": "system", "content": "你是一个量化策略专家。"},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = self.client.chat(messages, temperature=0.6, max_tokens=500)
            return response
        except Exception as e:
            return f"AI 对比失败: {e}"
    
    def suggest_parameters(self,
                          result,
                          current_params: Dict,
                          param_ranges: Dict) -> str:
        """
        建议参数调整
        
        Args:
            result: 当前回测结果
            current_params: 当前参数
            param_ranges: 参数范围
        
        Returns:
            参数调整建议
        """
        if not self.ai_enabled:
            return "AI 分析不可用"
        
        params_text = "\n".join([f"- {k}: {v}" for k, v in current_params.items()])
        ranges_text = "\n".join([f"- {k}: {v}" for k, v in param_ranges.items()])
        
        prompt = f"""
当前策略参数：
{params_text}

参数范围：
{ranges_text}

回测表现：
- 夏普比率：{result.sharpe_ratio:.3f}
- 最大回撤：{result.max_drawdown:.2%}
- 胜率：{result.win_rate:.2%}

请分析参数设置，并建议如何调整以提升表现。

要求：
1. 分析当前参数的问题（50字）
2. 给出 3-5 个具体的参数调整建议
3. 每个建议说明理由（20字内）

总字数200字内。
"""
        
        messages = [
            {"role": "system", "content": "你是一个参数优化专家。"},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = self.client.chat(messages, temperature=0.7, max_tokens=400)
            return response
        except Exception as e:
            return f"AI 建议失败: {e}"
    
    def explain_drawdown(self,
                        equity_curve: List[float],
                        trades: List) -> str:
        """
        解释回撤原因
        
        Args:
            equity_curve: 权益曲线
            trades: 交易记录
        
        Returns:
            回撤分析
        """
        if not self.ai_enabled:
            return "AI 分析不可用"
        
        # 找出最大回撤区间
        equity = np.array(equity_curve)
        peak = equity[0]
        max_dd = 0
        max_dd_start = 0
        max_dd_end = 0
        
        for i, value in enumerate(equity):
            if value > peak:
                peak = value
                peak_idx = i
            
            dd = (peak - value) / peak
            if dd > max_dd:
                max_dd = dd
                max_dd_start = peak_idx
                max_dd_end = i
        
        # 统计这段时间的交易
        dd_trades = [t for t in trades if max_dd_start <= trades.index(t) <= max_dd_end]
        
        prompt = f"""
策略在第 {max_dd_start} 到 {max_dd_end} 天经历了最大回撤 {max_dd:.2%}。

这段时间：
- 交易次数：{len(dd_trades)}
- 起始权益：{equity[max_dd_start]:.2f}
- 最低权益：{equity[max_dd_end]:.2f}

请分析可能的回撤原因，并给出应对建议。

要求简洁（150字内）。
"""
        
        messages = [
            {"role": "system", "content": "你是风险管理专家。"},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = self.client.chat(messages, temperature=0.6, max_tokens=300)
            return response
        except Exception as e:
            return f"AI 分析失败: {e}"

