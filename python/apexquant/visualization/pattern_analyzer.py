"""
AI 驱动的 K 线模式分析
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

try:
    from apexquant.ai import DeepSeekClient
except ImportError:
    DeepSeekClient = None


class AIPatternAnalyzer:
    """AI K 线模式分析器"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化分析器
        
        Args:
            api_key: DeepSeek API key
        """
        if DeepSeekClient:
            try:
                self.client = DeepSeekClient(api_key)
                self.ai_enabled = True
            except:
                self.ai_enabled = False
        else:
            self.ai_enabled = False
    
    def analyze_chart(self, df: pd.DataFrame, 
                     recent_days: int = 20) -> Dict:
        """
        分析 K 线图并给出解读
        
        Args:
            df: K 线数据
            recent_days: 分析最近多少天
        
        Returns:
            分析结果字典
        """
        if df.empty:
            return {'error': '数据为空'}
        
        # 基础统计
        recent_df = df.tail(recent_days)
        
        analysis = {
            'trend': self._detect_trend(recent_df),
            'volatility': self._calculate_volatility(recent_df),
            'support_resistance': self._find_support_resistance(recent_df),
            'patterns': self._detect_patterns(recent_df),
            'summary': ''
        }
        
        # AI 增强分析
        if self.ai_enabled:
            ai_summary = self._ai_analyze(recent_df, analysis)
            analysis['ai_summary'] = ai_summary
            analysis['summary'] = ai_summary
        else:
            analysis['summary'] = self._generate_summary(analysis)
        
        return analysis
    
    def _detect_trend(self, df: pd.DataFrame) -> str:
        """检测趋势"""
        closes = df['close'].values
        
        if len(closes) < 2:
            return 'unknown'
        
        # 简单线性回归
        x = np.arange(len(closes))
        slope = np.polyfit(x, closes, 1)[0]
        
        # 计算涨跌幅
        change_pct = (closes[-1] - closes[0]) / closes[0]
        
        if slope > 0 and change_pct > 0.05:
            return 'uptrend'
        elif slope < 0 and change_pct < -0.05:
            return 'downtrend'
        else:
            return 'sideways'
    
    def _calculate_volatility(self, df: pd.DataFrame) -> float:
        """计算波动率"""
        if len(df) < 2:
            return 0.0
        
        returns = df['close'].pct_change().dropna()
        return float(returns.std() * np.sqrt(252))  # 年化波动率
    
    def _find_support_resistance(self, df: pd.DataFrame) -> Dict:
        """寻找支撑位和压力位"""
        closes = df['close'].values
        highs = df['high'].values
        lows = df['low'].values
        
        # 简单方法：使用最近的高低点
        resistance = float(np.max(highs))
        support = float(np.min(lows))
        current = float(closes[-1])
        
        return {
            'resistance': resistance,
            'support': support,
            'current': current,
            'distance_to_resistance': (resistance - current) / current,
            'distance_to_support': (current - support) / current
        }
    
    def _detect_patterns(self, df: pd.DataFrame) -> List[str]:
        """检测常见形态"""
        patterns = []
        
        if len(df) < 3:
            return patterns
        
        closes = df['close'].values
        
        # 连续上涨
        if all(closes[i] < closes[i+1] for i in range(len(closes)-3, len(closes)-1)):
            patterns.append('连续上涨')
        
        # 连续下跌
        if all(closes[i] > closes[i+1] for i in range(len(closes)-3, len(closes)-1)):
            patterns.append('连续下跌')
        
        # 突破新高
        if closes[-1] == np.max(closes):
            patterns.append('突破新高')
        
        # 跌破新低
        if closes[-1] == np.min(closes):
            patterns.append('跌破新低')
        
        # 十字星（开盘收盘接近）
        last_bar = df.iloc[-1]
        body = abs(last_bar['close'] - last_bar['open'])
        range_size = last_bar['high'] - last_bar['low']
        
        if range_size > 0 and body / range_size < 0.1:
            patterns.append('十字星')
        
        return patterns
    
    def _ai_analyze(self, df: pd.DataFrame, basic_analysis: Dict) -> str:
        """使用 AI 生成分析报告"""
        # 准备数据摘要
        recent_data = df.tail(10)[['close', 'volume']].to_dict('records')
        
        prompt = f"""
作为专业的技术分析师，请分析以下股票 K 线数据：

基础分析：
- 趋势：{basic_analysis['trend']}
- 波动率：{basic_analysis['volatility']:.2%}
- 当前价：{basic_analysis['support_resistance']['current']:.2f}
- 压力位：{basic_analysis['support_resistance']['resistance']:.2f}
- 支撑位：{basic_analysis['support_resistance']['support']:.2f}
- 检测到的形态：{', '.join(basic_analysis['patterns']) if basic_analysis['patterns'] else '无'}

最近 10 日数据（收盘价和成交量）：
{recent_data}

请给出：
1. 趋势判断和理由（50字内）
2. 关键支撑压力位分析（30字内）
3. 短期操作建议（30字内）

要求：简洁专业，不超过150字。
"""
        
        messages = [
            {"role": "system", "content": "你是一个专业的股票技术分析师。"},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = self.client.chat(messages, temperature=0.5, max_tokens=300)
            return response
        except Exception as e:
            print(f"AI 分析失败: {e}")
            return self._generate_summary(basic_analysis)
    
    def _generate_summary(self, analysis: Dict) -> str:
        """生成传统分析摘要"""
        trend_desc = {
            'uptrend': '上升趋势',
            'downtrend': '下降趋势',
            'sideways': '横盘震荡',
            'unknown': '趋势不明'
        }
        
        trend = trend_desc.get(analysis['trend'], '未知')
        vol = analysis['volatility']
        sr = analysis['support_resistance']
        patterns = analysis['patterns']
        
        summary = f"当前呈现{trend}，"
        summary += f"波动率 {vol:.1%}。"
        summary += f"支撑位 {sr['support']:.2f}，压力位 {sr['resistance']:.2f}。"
        
        if patterns:
            summary += f" 检测到：{', '.join(patterns)}。"
        
        return summary
    
    def generate_annotations(self, df: pd.DataFrame, 
                           analysis: Dict) -> List[Dict]:
        """
        生成图表注释
        
        Args:
            df: K 线数据
            analysis: 分析结果
        
        Returns:
            注释列表
        """
        annotations = []
        
        # 标注最高点
        max_idx = df['high'].idxmax()
        annotations.append({
            'date': df.loc[max_idx, 'date'] if 'date' in df.columns else max_idx,
            'text': f"最高 {df.loc[max_idx, 'high']:.2f}",
            'type': 'sell'
        })
        
        # 标注最低点
        min_idx = df['low'].idxmin()
        annotations.append({
            'date': df.loc[min_idx, 'date'] if 'date' in df.columns else min_idx,
            'text': f"最低 {df.loc[min_idx, 'low']:.2f}",
            'type': 'buy'
        })
        
        # 标注形态
        if analysis['patterns']:
            last_date = df.iloc[-1]['date'] if 'date' in df.columns else df.index[-1]
            annotations.append({
                'date': last_date,
                'text': ', '.join(analysis['patterns'][:2]),
                'type': 'info'
            })
        
        return annotations

