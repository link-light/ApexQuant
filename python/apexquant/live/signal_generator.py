"""
AI 实时信号生成器
"""

from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from apexquant.ai import DeepSeekClient


class AISignalGenerator:
    """AI 驱动的交易信号生成器"""
    
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
            print("⚠ AI 未启用，使用规则信号")
    
    def generate_signal(self,
                       symbol: str,
                       current_price: float,
                       data: pd.DataFrame,
                       news: Optional[List[str]] = None,
                       position: Optional[Dict] = None) -> Tuple[str, float, str]:
        """
        生成交易信号
        
        Args:
            symbol: 股票代码
            current_price: 当前价格
            data: 历史数据
            news: 新闻列表（可选）
            position: 当前持仓（可选）
        
        Returns:
            (action, confidence, reason)
            action: 'buy', 'sell', 'hold'
            confidence: 信号置信度 (0-1)
            reason: 信号理由
        """
        if not self.ai_enabled:
            return self._rule_based_signal(symbol, current_price, data, position)
        
        # 准备市场信息
        market_info = self._prepare_market_info(symbol, current_price, data, news, position)
        
        # AI 生成信号
        signal = self._ai_generate_signal(market_info)
        
        return signal
    
    def _prepare_market_info(self,
                            symbol: str,
                            current_price: float,
                            data: pd.DataFrame,
                            news: Optional[List[str]],
                            position: Optional[Dict]) -> str:
        """准备市场信息"""
        
        info = f"股票代码: {symbol}\n当前价格: {current_price:.2f}\n\n"
        
        # 技术指标
        if len(data) >= 20:
            close_prices = data['close'].values
            
            # 计算简单指标
            ma5 = np.mean(close_prices[-5:])
            ma10 = np.mean(close_prices[-10:])
            ma20 = np.mean(close_prices[-20:])
            
            pct_change_1d = (close_prices[-1] - close_prices[-2]) / close_prices[-2] * 100
            pct_change_5d = (close_prices[-1] - close_prices[-6]) / close_prices[-6] * 100
            
            # 成交量变化
            volume_ma5 = np.mean(data['volume'].values[-5:])
            volume_today = data['volume'].values[-1]
            volume_ratio = volume_today / volume_ma5
            
            info += f"【技术指标】\n"
            info += f"MA5: {ma5:.2f}, MA10: {ma10:.2f}, MA20: {ma20:.2f}\n"
            info += f"1日涨跌: {pct_change_1d:+.2f}%\n"
            info += f"5日涨跌: {pct_change_5d:+.2f}%\n"
            info += f"量比: {volume_ratio:.2f}\n"
            
            # 趋势判断
            if ma5 > ma10 > ma20:
                info += "趋势: 多头排列\n"
            elif ma5 < ma10 < ma20:
                info += "趋势: 空头排列\n"
            else:
                info += "趋势: 震荡\n"
            
            info += "\n"
        
        # 持仓信息
        if position:
            info += f"【持仓】\n"
            info += f"持仓量: {position.get('volume', 0)}\n"
            info += f"成本价: {position.get('avg_price', 0):.2f}\n"
            profit_loss = (current_price - position.get('avg_price', current_price)) / position.get('avg_price', current_price) * 100
            info += f"浮动盈亏: {profit_loss:+.2f}%\n\n"
        
        # 新闻情绪
        if news and len(news) > 0:
            info += f"【最新新闻】\n"
            for i, item in enumerate(news[:3], 1):
                info += f"{i}. {item}\n"
            info += "\n"
        
        return info
    
    def _ai_generate_signal(self, market_info: str) -> Tuple[str, float, str]:
        """使用 AI 生成信号"""
        
        prompt = f"""
你是一个专业的量化交易分析师。根据以下市场信息，给出交易建议。

{market_info}

请给出：
1. 交易动作（买入/卖出/持有）
2. 信号强度（0-100，表示置信度）
3. 理由（50字内）

要求：
- 综合技术面、基本面、持仓情况判断
- 考虑风险控制
- 简洁明确

格式：
动作: [买入/卖出/持有]
强度: [0-100]
理由: [具体理由]
"""
        
        messages = [
            {"role": "system", "content": "你是专业量化交易分析师。"},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = self.client.chat(messages, temperature=0.3, max_tokens=200)
            
            # 解析响应
            action = 'hold'
            confidence = 0.5
            reason = "AI 分析"
            
            lines = response.strip().split('\n')
            for line in lines:
                if '动作' in line or 'Action' in line:
                    if '买入' in line or 'buy' in line.lower():
                        action = 'buy'
                    elif '卖出' in line or 'sell' in line.lower():
                        action = 'sell'
                    else:
                        action = 'hold'
                elif '强度' in line or 'Strength' in line or 'Confidence' in line:
                    try:
                        import re
                        numbers = re.findall(r'\d+', line)
                        if numbers:
                            confidence = float(numbers[0]) / 100.0
                    except:
                        pass
                elif '理由' in line or 'Reason' in line:
                    reason = line.split(':', 1)[-1].strip()
            
            return action, confidence, reason
            
        except Exception as e:
            print(f"AI 信号生成失败: {e}")
            return self._rule_based_signal_simple()
    
    def _rule_based_signal(self,
                          symbol: str,
                          current_price: float,
                          data: pd.DataFrame,
                          position: Optional[Dict]) -> Tuple[str, float, str]:
        """基于规则的信号生成"""
        
        if len(data) < 20:
            return 'hold', 0.0, "数据不足"
        
        close_prices = data['close'].values
        
        # 计算均线
        ma5 = np.mean(close_prices[-5:])
        ma10 = np.mean(close_prices[-10:])
        ma20 = np.mean(close_prices[-20:])
        
        # 趋势判断
        if ma5 > ma10 > ma20:
            # 多头趋势
            if not position or position.get('volume', 0) == 0:
                return 'buy', 0.7, "多头排列，建议买入"
            else:
                return 'hold', 0.8, "持有待涨"
        elif ma5 < ma10 < ma20:
            # 空头趋势
            if position and position.get('volume', 0) > 0:
                return 'sell', 0.7, "空头排列，建议止损"
            else:
                return 'hold', 0.6, "观望为主"
        else:
            # 震荡
            return 'hold', 0.5, "震荡行情，观望"
    
    def _rule_based_signal_simple(self) -> Tuple[str, float, str]:
        """简单规则信号"""
        return 'hold', 0.5, "保持观望"
    
    def batch_generate_signals(self,
                              symbols: List[str],
                              market_data: Dict[str, pd.DataFrame],
                              news_data: Optional[Dict[str, List[str]]] = None) -> Dict[str, Tuple[str, float, str]]:
        """
        批量生成信号
        
        Args:
            symbols: 股票代码列表
            market_data: {symbol: DataFrame}
            news_data: {symbol: [news]}
        
        Returns:
            {symbol: (action, confidence, reason)}
        """
        signals = {}
        
        for symbol in symbols:
            if symbol not in market_data:
                continue
            
            data = market_data[symbol]
            if data.empty:
                continue
            
            current_price = data['close'].iloc[-1]
            news = news_data.get(symbol, []) if news_data else None
            
            signal = self.generate_signal(symbol, current_price, data, news)
            signals[symbol] = signal
        
        return signals
    
    def filter_signals(self,
                      signals: Dict[str, Tuple[str, float, str]],
                      min_confidence: float = 0.6,
                      max_positions: int = 5) -> List[Tuple[str, str, float, str]]:
        """
        过滤和排序信号
        
        Args:
            signals: 原始信号
            min_confidence: 最小置信度
            max_positions: 最大持仓数
        
        Returns:
            [(symbol, action, confidence, reason)]
        """
        filtered = []
        
        for symbol, (action, confidence, reason) in signals.items():
            if action != 'hold' and confidence >= min_confidence:
                filtered.append((symbol, action, confidence, reason))
        
        # 按置信度排序
        filtered.sort(key=lambda x: x[2], reverse=True)
        
        # 限制数量
        return filtered[:max_positions]

