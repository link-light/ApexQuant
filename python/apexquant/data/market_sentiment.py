"""
市场情绪指标模块

提供市场情绪分析功能：
- 恐慌贪婪指数 (Fear & Greed Index)
- 成交量异常检测
- 市场宽度指标 (涨跌家数比)
- 波动率指数 (VIX-like)
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum


class SentimentLevel(Enum):
    """情绪等级"""
    EXTREME_FEAR = "极度恐慌"
    FEAR = "恐慌"
    NEUTRAL = "中性"
    GREED = "贪婪"
    EXTREME_GREED = "极度贪婪"


@dataclass
class SentimentIndicator:
    """情绪指标结果"""
    score: float  # 0-100分，0=极度恐慌，100=极度贪婪
    level: SentimentLevel
    components: Dict[str, float]  # 各组成部分得分
    timestamp: datetime
    description: str


@dataclass
class VolumeAnomaly:
    """成交量异常"""
    symbol: str
    date: datetime
    volume: float
    avg_volume: float
    z_score: float  # 标准差倍数
    anomaly_type: str  # 'surge' 或 'drop'
    severity: str  # 'mild', 'moderate', 'severe'


class MarketSentimentAnalyzer:
    """市场情绪分析器"""

    def __init__(self):
        """初始化"""
        pass

    def calculate_fear_greed_index(
        self,
        market_data: pd.DataFrame,
        volatility_window: int = 20,
        momentum_window: int = 125,
        volume_window: int = 20
    ) -> SentimentIndicator:
        """
        计算恐慌贪婪指数

        基于多个维度：
        1. 市场动量 (25%)
        2. 市场波动率 (25%)
        3. 成交量 (25%)
        4. 市场宽度 (25%)

        Args:
            market_data: 市场数据，需包含 close, volume, high, low 列
            volatility_window: 波动率计算窗口
            momentum_window: 动量计算窗口
            volume_window: 成交量计算窗口

        Returns:
            SentimentIndicator: 情绪指标
        """
        if len(market_data) < max(volatility_window, momentum_window, volume_window):
            raise ValueError(f"数据量不足，至少需要 {max(volatility_window, momentum_window, volume_window)} 条记录")

        components = {}

        # 1. 市场动量 (0-100)
        momentum_score = self._calculate_momentum_score(market_data, momentum_window)
        components['momentum'] = momentum_score

        # 2. 波动率 (0-100，波动率越低得分越高)
        volatility_score = self._calculate_volatility_score(market_data, volatility_window)
        components['volatility'] = volatility_score

        # 3. 成交量 (0-100)
        volume_score = self._calculate_volume_score(market_data, volume_window)
        components['volume'] = volume_score

        # 4. 市场宽度 (如果有涨跌家数数据)
        breadth_score = self._calculate_breadth_score(market_data)
        components['breadth'] = breadth_score

        # 综合得分 (加权平均)
        weights = {
            'momentum': 0.25,
            'volatility': 0.25,
            'volume': 0.25,
            'breadth': 0.25
        }

        total_score = sum(components[k] * weights[k] for k in components.keys())

        # 确定情绪等级
        level = self._score_to_level(total_score)

        # 生成描述
        description = self._generate_description(total_score, components)

        return SentimentIndicator(
            score=total_score,
            level=level,
            components=components,
            timestamp=datetime.now(),
            description=description
        )

    def _calculate_momentum_score(self, data: pd.DataFrame, window: int) -> float:
        """计算动量得分 (0-100)"""
        if len(data) < window:
            return 50.0

        # 计算收益率
        current_price = data['close'].iloc[-1]
        past_price = data['close'].iloc[-window]
        momentum = (current_price - past_price) / past_price * 100

        # 映射到0-100，假设±20%为极端值
        score = 50 + (momentum / 20) * 50
        return np.clip(score, 0, 100)

    def _calculate_volatility_score(self, data: pd.DataFrame, window: int) -> float:
        """计算波动率得分 (0-100，波动率越低得分越高)"""
        if len(data) < window:
            return 50.0

        # 计算历史波动率
        returns = data['close'].pct_change().dropna()
        recent_vol = returns.tail(window).std() * np.sqrt(252) * 100  # 年化波动率

        # 计算长期平均波动率
        long_term_vol = returns.std() * np.sqrt(252) * 100

        if long_term_vol == 0:
            return 50.0

        # 波动率比率，越低越好
        vol_ratio = recent_vol / long_term_vol

        # 映射到0-100，比率0.5=100分，2.0=0分
        score = 100 - (vol_ratio - 0.5) / 1.5 * 100
        return np.clip(score, 0, 100)

    def _calculate_volume_score(self, data: pd.DataFrame, window: int) -> float:
        """计算成交量得分 (0-100)"""
        if len(data) < window or 'volume' not in data.columns:
            return 50.0

        # 当前成交量 vs 平均成交量
        current_volume = data['volume'].iloc[-1]
        avg_volume = data['volume'].tail(window).mean()

        if avg_volume == 0:
            return 50.0

        volume_ratio = current_volume / avg_volume

        # 映射到0-100，比率0.5=0分，2.0=100分
        score = (volume_ratio - 0.5) / 1.5 * 100
        return np.clip(score, 0, 100)

    def _calculate_breadth_score(self, data: pd.DataFrame) -> float:
        """计算市场宽度得分 (0-100)"""
        # 如果数据中有涨跌家数，使用它
        if 'advance' in data.columns and 'decline' in data.columns:
            advance = data['advance'].iloc[-1]
            decline = data['decline'].iloc[-1]

            if advance + decline == 0:
                return 50.0

            advance_ratio = advance / (advance + decline)
            return advance_ratio * 100

        # 否则使用价格变化作为代理
        if len(data) < 2:
            return 50.0

        price_change = (data['close'].iloc[-1] - data['close'].iloc[-2]) / data['close'].iloc[-2]

        # 映射到0-100
        score = 50 + price_change * 1000  # 假设±5%为极端值
        return np.clip(score, 0, 100)

    def _score_to_level(self, score: float) -> SentimentLevel:
        """将得分转换为情绪等级"""
        if score <= 20:
            return SentimentLevel.EXTREME_FEAR
        elif score <= 40:
            return SentimentLevel.FEAR
        elif score <= 60:
            return SentimentLevel.NEUTRAL
        elif score <= 80:
            return SentimentLevel.GREED
        else:
            return SentimentLevel.EXTREME_GREED

    def _generate_description(self, score: float, components: Dict[str, float]) -> str:
        """生成情绪描述"""
        level = self._score_to_level(score)

        descriptions = {
            SentimentLevel.EXTREME_FEAR: "市场处于极度恐慌状态，可能存在超卖机会",
            SentimentLevel.FEAR: "市场情绪偏向恐慌，投资者较为谨慎",
            SentimentLevel.NEUTRAL: "市场情绪中性，多空力量相对平衡",
            SentimentLevel.GREED: "市场情绪偏向贪婪，投资者较为乐观",
            SentimentLevel.EXTREME_GREED: "市场处于极度贪婪状态，需警惕回调风险"
        }

        base_desc = descriptions[level]

        # 添加主要驱动因素
        max_component = max(components.items(), key=lambda x: abs(x[1] - 50))
        component_names = {
            'momentum': '市场动量',
            'volatility': '波动率',
            'volume': '成交量',
            'breadth': '市场宽度'
        }

        driver = component_names.get(max_component[0], max_component[0])

        return f"{base_desc}。主要驱动因素：{driver}"

    def detect_volume_anomalies(
        self,
        symbol: str,
        volume_data: pd.Series,
        window: int = 20,
        threshold: float = 2.0
    ) -> List[VolumeAnomaly]:
        """
        检测成交量异常

        Args:
            symbol: 股票代码
            volume_data: 成交量序列 (带日期索引)
            window: 滚动窗口大小
            threshold: Z-score阈值 (标准差倍数)

        Returns:
            List[VolumeAnomaly]: 异常列表
        """
        if len(volume_data) < window:
            return []

        anomalies = []

        # 计算滚动均值和标准差
        rolling_mean = volume_data.rolling(window=window).mean()
        rolling_std = volume_data.rolling(window=window).std()

        # 计算Z-score
        z_scores = (volume_data - rolling_mean) / rolling_std

        # 检测异常
        for idx in range(window, len(volume_data)):
            z_score = z_scores.iloc[idx]

            if abs(z_score) >= threshold:
                volume = volume_data.iloc[idx]
                avg_volume = rolling_mean.iloc[idx]

                # 确定异常类型
                anomaly_type = 'surge' if z_score > 0 else 'drop'

                # 确定严重程度
                if abs(z_score) >= 4.0:
                    severity = 'severe'
                elif abs(z_score) >= 3.0:
                    severity = 'moderate'
                else:
                    severity = 'mild'

                anomaly = VolumeAnomaly(
                    symbol=symbol,
                    date=volume_data.index[idx],
                    volume=volume,
                    avg_volume=avg_volume,
                    z_score=z_score,
                    anomaly_type=anomaly_type,
                    severity=severity
                )

                anomalies.append(anomaly)

        return anomalies

    def calculate_market_breadth(
        self,
        stock_prices: Dict[str, pd.Series],
        period: int = 1
    ) -> Dict[str, float]:
        """
        计算市场宽度指标

        Args:
            stock_prices: 股票价格字典 {symbol: price_series}
            period: 比较周期 (天数)

        Returns:
            Dict: 市场宽度指标
                - advance_count: 上涨家数
                - decline_count: 下跌家数
                - unchanged_count: 平盘家数
                - advance_decline_ratio: 涨跌比
                - advance_percentage: 上涨占比
        """
        if not stock_prices:
            return {}

        advance_count = 0
        decline_count = 0
        unchanged_count = 0

        for symbol, prices in stock_prices.items():
            if len(prices) < period + 1:
                continue

            current_price = prices.iloc[-1]
            past_price = prices.iloc[-(period + 1)]

            if current_price > past_price:
                advance_count += 1
            elif current_price < past_price:
                decline_count += 1
            else:
                unchanged_count += 1

        total_count = advance_count + decline_count + unchanged_count

        if total_count == 0:
            return {}

        # 涨跌比
        ad_ratio = advance_count / decline_count if decline_count > 0 else float('inf')

        # 上涨占比
        advance_pct = advance_count / total_count * 100

        return {
            'advance_count': advance_count,
            'decline_count': decline_count,
            'unchanged_count': unchanged_count,
            'advance_decline_ratio': ad_ratio,
            'advance_percentage': advance_pct,
            'total_count': total_count
        }

    def calculate_vix_like_index(
        self,
        price_data: pd.DataFrame,
        window: int = 20
    ) -> pd.Series:
        """
        计算类VIX波动率指数

        使用历史价格波动率作为VIX的近似

        Args:
            price_data: 价格数据，需包含 high, low, close 列
            window: 计算窗口

        Returns:
            pd.Series: 波动率指数序列
        """
        # 使用Parkinson波动率估计器 (基于高低价)
        if 'high' in price_data.columns and 'low' in price_data.columns:
            hl_ratio = np.log(price_data['high'] / price_data['low'])
            parkinson_vol = np.sqrt(1 / (4 * np.log(2)) * hl_ratio ** 2)

            # 滚动平均并年化
            vix_like = parkinson_vol.rolling(window=window).mean() * np.sqrt(252) * 100
        else:
            # 回退到简单收益率波动率
            returns = price_data['close'].pct_change()
            vix_like = returns.rolling(window=window).std() * np.sqrt(252) * 100

        return vix_like


def get_market_sentiment(
    market_data: pd.DataFrame,
    **kwargs
) -> SentimentIndicator:
    """
    便捷函数：获取市场情绪指标

    Args:
        market_data: 市场数据
        **kwargs: 传递给 calculate_fear_greed_index 的参数

    Returns:
        SentimentIndicator: 情绪指标
    """
    analyzer = MarketSentimentAnalyzer()
    return analyzer.calculate_fear_greed_index(market_data, **kwargs)


def detect_volume_anomalies(
    symbol: str,
    volume_data: pd.Series,
    **kwargs
) -> List[VolumeAnomaly]:
    """
    便捷函数：检测成交量异常

    Args:
        symbol: 股票代码
        volume_data: 成交量数据
        **kwargs: 传递给 detect_volume_anomalies 的参数

    Returns:
        List[VolumeAnomaly]: 异常列表
    """
    analyzer = MarketSentimentAnalyzer()
    return analyzer.detect_volume_anomalies(symbol, volume_data, **kwargs)
