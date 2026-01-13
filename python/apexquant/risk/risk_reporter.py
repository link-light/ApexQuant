"""
AI 风险报告生成器
"""

from typing import Dict, Optional
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from apexquant.ai import DeepSeekClient


class RiskReporter:
    """AI 驱动的风险报告生成器"""
    
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
    
    def generate_risk_report(self, 
                            metrics: Dict,
                            strategy_name: str = "策略") -> str:
        """
        生成完整风险评估报告
        
        Args:
            metrics: 风险指标字典
            strategy_name: 策略名称
        
        Returns:
            风险报告
        """
        if not self.ai_enabled:
            return self._generate_simple_report(metrics, strategy_name)
        
        # 准备数据
        report_data = f"""
策略：{strategy_name}

收益指标：
- 总收益率：{metrics.get('total_return', 0):.2%}
- 年化收益率：{metrics.get('annual_return', 0):.2%}
- 夏普比率：{metrics.get('sharpe_ratio', 0):.3f}
- Sortino 比率：{metrics.get('sortino_ratio', 0):.3f}
- Calmar 比率：{metrics.get('calmar_ratio', 0):.3f}
- Omega 比率：{metrics.get('omega_ratio', 0):.3f}

风险指标：
- 最大回撤：{metrics.get('max_drawdown', 0):.2%}
- 回撤持续：{metrics.get('max_dd_duration', 0)} 天
- VaR (95%)：{metrics.get('var_95', 0):.2%}
- CVaR (95%)：{metrics.get('cvar_95', 0):.2%}
- VaR (99%)：{metrics.get('var_99', 0):.2%}
- CVaR (99%)：{metrics.get('cvar_99', 0):.2%}

交易统计：
- 胜率：{metrics.get('win_rate', 0):.2%}
- 盈亏比：{metrics.get('profit_loss_ratio', 0):.2f}
- 尾部比率：{metrics.get('tail_ratio', 0):.2f}
"""
        
        if 'alpha' in metrics:
            report_data += f"\n相对表现：\n- Alpha：{metrics['alpha']:.2%}\n- Beta：{metrics['beta']:.3f}\n- 信息比率：{metrics.get('information_ratio', 0):.3f}\n"
        
        prompt = f"""
你是一个专业的风险管理分析师。请根据以下风险指标，生成一份详细的风险评估报告。

{report_data}

报告要求：
1. 风险等级评定（低/中/高/极高）及理由（80字）
2. 主要风险点分析（3-4点，每点40字）
3. 风险承受能力评估（60字）
4. 风险控制建议（4-5点，每点30字）
5. 综合评价（60字）

要求：
- 专业、准确、具体
- 建议可操作
- 总字数500字内
"""
        
        messages = [
            {"role": "system", "content": "你是一个专业的风险管理分析师，擅长量化风险评估。"},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = self.client.chat(messages, temperature=0.5, max_tokens=1000)
            return response
        except Exception as e:
            print(f"AI 报告生成失败: {e}")
            return self._generate_simple_report(metrics, strategy_name)
    
    def _generate_simple_report(self, metrics: Dict, strategy_name: str) -> str:
        """生成简单报告（无 AI）"""
        report = f"""
===== 风险评估报告 =====
策略：{strategy_name}

【收益表现】
总收益率：{metrics.get('total_return', 0):.2%}
年化收益率：{metrics.get('annual_return', 0):.2%}
夏普比率：{metrics.get('sharpe_ratio', 0):.3f}

【风险指标】
最大回撤：{metrics.get('max_drawdown', 0):.2%}
VaR (95%)：{metrics.get('var_95', 0):.2%}
CVaR (95%)：{metrics.get('cvar_95', 0):.2%}

【风险等级】
"""
        
        # 简单评级
        max_dd = metrics.get('max_drawdown', 0)
        if max_dd > 0.3:
            report += "极高风险"
        elif max_dd > 0.2:
            report += "高风险"
        elif max_dd > 0.1:
            report += "中等风险"
        else:
            report += "低风险"
        
        return report
    
    def compare_strategies_risk(self,
                               strategies_metrics: Dict[str, Dict]) -> str:
        """
        对比多个策略的风险
        
        Args:
            strategies_metrics: {策略名: 风险指标} 字典
        
        Returns:
            对比报告
        """
        if not self.ai_enabled:
            return "AI 对比不可用"
        
        # 准备对比数据
        comparison_text = ""
        for name, metrics in strategies_metrics.items():
            comparison_text += f"""
{name}：
  收益/风险：年化 {metrics.get('annual_return', 0):.2%} / 回撤 {metrics.get('max_drawdown', 0):.2%}
  夏普比率：{metrics.get('sharpe_ratio', 0):.3f}
  VaR (95%)：{metrics.get('var_95', 0):.2%}
  CVaR (95%)：{metrics.get('cvar_95', 0):.2%}
  胜率：{metrics.get('win_rate', 0):.2%}
"""
        
        prompt = f"""
请对比以下策略的风险特征，给出分析和推荐：

{comparison_text}

要求：
1. 风险对比分析（120字）
2. 推荐最优策略及理由（80字）
3. 风险分散建议（60字）

总字数260字内。
"""
        
        messages = [
            {"role": "system", "content": "你是风险管理专家。"},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = self.client.chat(messages, temperature=0.6, max_tokens=500)
            return response
        except Exception as e:
            return f"AI 对比失败: {e}"
    
    def suggest_risk_controls(self, metrics: Dict) -> str:
        """
        建议风险控制措施
        
        Args:
            metrics: 风险指标
        
        Returns:
            风控建议
        """
        if not self.ai_enabled:
            return "AI 建议不可用"
        
        prompt = f"""
策略风险状况：
- 最大回撤：{metrics.get('max_drawdown', 0):.2%}
- VaR (95%)：{metrics.get('var_95', 0):.2%}
- 胜率：{metrics.get('win_rate', 0):.2%}
- 盈亏比：{metrics.get('profit_loss_ratio', 0):.2f}

请针对这些风险指标，提供具体的风险控制措施。

要求：
1. 5-6 个具体可执行的风控措施
2. 每个措施包含：措施名称 + 具体参数/阈值 + 理由
3. 总字数 300 字内
"""
        
        messages = [
            {"role": "system", "content": "你是风险控制专家。"},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = self.client.chat(messages, temperature=0.6, max_tokens=600)
            return response
        except Exception as e:
            return f"AI 建议失败: {e}"

