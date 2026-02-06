"""
ApexQuant 技术指标计算模块

提供全面的技术分析指标计算，用于AI分析决策
"""

import numpy as np
import pandas as pd
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class TechnicalIndicators:
    """技术指标数据类"""
    # 趋势指标
    ma5: float = 0.0
    ma10: float = 0.0
    ma20: float = 0.0
    ma60: float = 0.0
    ema12: float = 0.0
    ema26: float = 0.0

    # MACD
    macd: float = 0.0
    macd_signal: float = 0.0
    macd_hist: float = 0.0

    # 动量指标
    rsi: float = 50.0
    rsi_signal: str = "中性"  # 超买/超卖/中性

    # KDJ
    kdj_k: float = 50.0
    kdj_d: float = 50.0
    kdj_j: float = 50.0
    kdj_signal: str = "中性"

    # 布林带
    boll_upper: float = 0.0
    boll_middle: float = 0.0
    boll_lower: float = 0.0
    boll_position: str = "中轨"  # 上轨/中轨/下轨

    # 波动率
    atr: float = 0.0
    volatility: float = 0.0

    # 成交量
    volume_ma5: float = 0.0
    volume_ma20: float = 0.0
    volume_ratio: float = 1.0  # 量比

    # 价格位置
    price_position: float = 0.5  # 0-1，当前价格在近期高低点的位置
    distance_from_high: float = 0.0  # 距离最高点百分比
    distance_from_low: float = 0.0   # 距离最低点百分比

    # 趋势判断
    trend: str = "震荡"  # 上涨/下跌/震荡
    trend_strength: float = 0.0  # 趋势强度 0-100

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'ma5': round(self.ma5, 2),
            'ma10': round(self.ma10, 2),
            'ma20': round(self.ma20, 2),
            'ma60': round(self.ma60, 2),
            'macd': round(self.macd, 4),
            'macd_signal': round(self.macd_signal, 4),
            'macd_hist': round(self.macd_hist, 4),
            'rsi': round(self.rsi, 1),
            'rsi_signal': self.rsi_signal,
            'kdj_k': round(self.kdj_k, 1),
            'kdj_d': round(self.kdj_d, 1),
            'kdj_j': round(self.kdj_j, 1),
            'kdj_signal': self.kdj_signal,
            'boll_upper': round(self.boll_upper, 2),
            'boll_middle': round(self.boll_middle, 2),
            'boll_lower': round(self.boll_lower, 2),
            'boll_position': self.boll_position,
            'atr': round(self.atr, 2),
            'volatility': round(self.volatility, 2),
            'volume_ratio': round(self.volume_ratio, 2),
            'trend': self.trend,
            'trend_strength': round(self.trend_strength, 1),
            'price_position': round(self.price_position, 2),
        }

    def to_text(self) -> str:
        """转换为文本描述，用于AI分析"""
        lines = [
            f"【趋势指标】",
            f"  MA5={self.ma5:.2f}, MA10={self.ma10:.2f}, MA20={self.ma20:.2f}, MA60={self.ma60:.2f}",
            f"  趋势: {self.trend} (强度: {self.trend_strength:.0f}%)",
            f"",
            f"【MACD】",
            f"  DIF={self.macd:.4f}, DEA={self.macd_signal:.4f}, 柱状={self.macd_hist:.4f}",
            f"",
            f"【RSI】 {self.rsi:.1f} - {self.rsi_signal}",
            f"",
            f"【KDJ】 K={self.kdj_k:.1f}, D={self.kdj_d:.1f}, J={self.kdj_j:.1f} - {self.kdj_signal}",
            f"",
            f"【布林带】",
            f"  上轨={self.boll_upper:.2f}, 中轨={self.boll_middle:.2f}, 下轨={self.boll_lower:.2f}",
            f"  当前位置: {self.boll_position}",
            f"",
            f"【波动率】 ATR={self.atr:.2f}, 波动率={self.volatility:.1f}%",
            f"",
            f"【量比】 {self.volume_ratio:.2f}",
            f"",
            f"【价格位置】 近期高低点位置={self.price_position:.0%}",
        ]
        return '\n'.join(lines)


class TechnicalAnalyzer:
    """技术分析计算器"""

    def __init__(self):
        logger.info("TechnicalAnalyzer initialized")

    def calculate(self, df: pd.DataFrame, current_price: float = None) -> TechnicalIndicators:
        """
        计算全部技术指标

        Args:
            df: OHLCV数据，需要包含 open, high, low, close, volume 列
            current_price: 当前价格（可选，默认使用最后一个收盘价）

        Returns:
            TechnicalIndicators 对象
        """
        if df is None or len(df) < 5:
            logger.warning("Insufficient data for technical analysis")
            return TechnicalIndicators()

        # 标准化列名
        df = self._standardize_columns(df)

        if current_price is None:
            current_price = float(df['close'].iloc[-1])

        indicators = TechnicalIndicators()

        try:
            # 计算各类指标
            self._calc_ma(df, indicators)
            self._calc_macd(df, indicators)
            self._calc_rsi(df, indicators)
            self._calc_kdj(df, indicators)
            self._calc_boll(df, indicators, current_price)
            self._calc_volatility(df, indicators)
            self._calc_volume(df, indicators)
            self._calc_price_position(df, indicators, current_price)
            self._calc_trend(df, indicators)

        except Exception as e:
            logger.error(f"Error calculating indicators: {e}")

        return indicators

    def _standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """标准化列名"""
        df = df.copy()
        column_map = {
            'Open': 'open', 'High': 'high', 'Low': 'low',
            'Close': 'close', 'Volume': 'volume',
            'OPEN': 'open', 'HIGH': 'high', 'LOW': 'low',
            'CLOSE': 'close', 'VOLUME': 'volume'
        }
        df.rename(columns=column_map, inplace=True)
        return df

    def _calc_ma(self, df: pd.DataFrame, ind: TechnicalIndicators):
        """计算移动平均线"""
        close = df['close']

        if len(close) >= 5:
            ind.ma5 = float(close.rolling(5).mean().iloc[-1])
        if len(close) >= 10:
            ind.ma10 = float(close.rolling(10).mean().iloc[-1])
        if len(close) >= 20:
            ind.ma20 = float(close.rolling(20).mean().iloc[-1])
        if len(close) >= 60:
            ind.ma60 = float(close.rolling(60).mean().iloc[-1])

        # EMA
        if len(close) >= 12:
            ind.ema12 = float(close.ewm(span=12, adjust=False).mean().iloc[-1])
        if len(close) >= 26:
            ind.ema26 = float(close.ewm(span=26, adjust=False).mean().iloc[-1])

    def _calc_macd(self, df: pd.DataFrame, ind: TechnicalIndicators):
        """计算MACD"""
        close = df['close']

        if len(close) < 26:
            return

        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()

        dif = ema12 - ema26
        dea = dif.ewm(span=9, adjust=False).mean()
        macd_hist = (dif - dea) * 2

        ind.macd = float(dif.iloc[-1])
        ind.macd_signal = float(dea.iloc[-1])
        ind.macd_hist = float(macd_hist.iloc[-1])

    def _calc_rsi(self, df: pd.DataFrame, ind: TechnicalIndicators, period: int = 14):
        """计算RSI"""
        close = df['close']

        if len(close) < period + 1:
            return

        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss.replace(0, np.inf)
        rsi = 100 - (100 / (1 + rs))

        ind.rsi = float(rsi.iloc[-1])

        # RSI信号
        if ind.rsi > 80:
            ind.rsi_signal = "超买"
        elif ind.rsi > 70:
            ind.rsi_signal = "偏强"
        elif ind.rsi < 20:
            ind.rsi_signal = "超卖"
        elif ind.rsi < 30:
            ind.rsi_signal = "偏弱"
        else:
            ind.rsi_signal = "中性"

    def _calc_kdj(self, df: pd.DataFrame, ind: TechnicalIndicators, n: int = 9):
        """计算KDJ"""
        if len(df) < n:
            return

        low_min = df['low'].rolling(window=n).min()
        high_max = df['high'].rolling(window=n).max()

        rsv = (df['close'] - low_min) / (high_max - low_min) * 100
        rsv = rsv.fillna(50)

        k = rsv.ewm(com=2, adjust=False).mean()
        d = k.ewm(com=2, adjust=False).mean()
        j = 3 * k - 2 * d

        ind.kdj_k = float(k.iloc[-1])
        ind.kdj_d = float(d.iloc[-1])
        ind.kdj_j = float(j.iloc[-1])

        # KDJ信号
        if ind.kdj_j > 100 and ind.kdj_k > 80:
            ind.kdj_signal = "超买"
        elif ind.kdj_j < 0 and ind.kdj_k < 20:
            ind.kdj_signal = "超卖"
        elif ind.kdj_k > ind.kdj_d and ind.kdj_j > ind.kdj_k:
            ind.kdj_signal = "金叉向上"
        elif ind.kdj_k < ind.kdj_d and ind.kdj_j < ind.kdj_k:
            ind.kdj_signal = "死叉向下"
        else:
            ind.kdj_signal = "中性"

    def _calc_boll(self, df: pd.DataFrame, ind: TechnicalIndicators,
                   current_price: float, period: int = 20, std_dev: float = 2):
        """计算布林带"""
        close = df['close']

        if len(close) < period:
            return

        ma = close.rolling(window=period).mean()
        std = close.rolling(window=period).std()

        ind.boll_middle = float(ma.iloc[-1])
        ind.boll_upper = float(ma.iloc[-1] + std_dev * std.iloc[-1])
        ind.boll_lower = float(ma.iloc[-1] - std_dev * std.iloc[-1])

        # 判断位置
        if current_price >= ind.boll_upper:
            ind.boll_position = "突破上轨"
        elif current_price > ind.boll_middle + (ind.boll_upper - ind.boll_middle) * 0.5:
            ind.boll_position = "上轨附近"
        elif current_price < ind.boll_lower:
            ind.boll_position = "跌破下轨"
        elif current_price < ind.boll_middle - (ind.boll_middle - ind.boll_lower) * 0.5:
            ind.boll_position = "下轨附近"
        else:
            ind.boll_position = "中轨震荡"

    def _calc_volatility(self, df: pd.DataFrame, ind: TechnicalIndicators, period: int = 14):
        """计算波动率和ATR"""
        if len(df) < period:
            return

        high = df['high']
        low = df['low']
        close = df['close']

        # ATR
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()

        ind.atr = float(atr.iloc[-1])

        # 波动率（年化）
        returns = close.pct_change()
        ind.volatility = float(returns.std() * np.sqrt(252) * 100)

    def _calc_volume(self, df: pd.DataFrame, ind: TechnicalIndicators):
        """计算成交量指标"""
        volume = df['volume']

        if len(volume) >= 5:
            ind.volume_ma5 = float(volume.rolling(5).mean().iloc[-1])
        if len(volume) >= 20:
            ind.volume_ma20 = float(volume.rolling(20).mean().iloc[-1])

        # 量比
        if ind.volume_ma5 > 0 and len(volume) >= 1:
            current_vol = float(volume.iloc[-1])
            ind.volume_ratio = current_vol / ind.volume_ma5

    def _calc_price_position(self, df: pd.DataFrame, ind: TechnicalIndicators,
                             current_price: float, lookback: int = 60):
        """计算价格位置"""
        if len(df) < 5:
            return

        period = min(lookback, len(df))
        high_max = df['high'].tail(period).max()
        low_min = df['low'].tail(period).min()

        if high_max > low_min:
            ind.price_position = (current_price - low_min) / (high_max - low_min)

        ind.distance_from_high = (high_max - current_price) / high_max * 100
        ind.distance_from_low = (current_price - low_min) / low_min * 100

    def _calc_trend(self, df: pd.DataFrame, ind: TechnicalIndicators):
        """判断趋势"""
        if len(df) < 20:
            return

        close = df['close']

        # 基于均线排列判断趋势
        ma5 = close.rolling(5).mean().iloc[-1]
        ma10 = close.rolling(10).mean().iloc[-1]
        ma20 = close.rolling(20).mean().iloc[-1]

        # 趋势判断
        if ma5 > ma10 > ma20:
            ind.trend = "上涨"
            # 计算趋势强度
            spread = (ma5 - ma20) / ma20 * 100
            ind.trend_strength = min(100, spread * 10)
        elif ma5 < ma10 < ma20:
            ind.trend = "下跌"
            spread = (ma20 - ma5) / ma20 * 100
            ind.trend_strength = min(100, spread * 10)
        else:
            ind.trend = "震荡"
            ind.trend_strength = 30

        # 结合MACD调整
        if ind.macd > 0 and ind.macd_hist > 0:
            ind.trend_strength = min(100, ind.trend_strength + 20)
        elif ind.macd < 0 and ind.macd_hist < 0:
            ind.trend_strength = min(100, ind.trend_strength + 20)


# 便捷函数
def calculate_indicators(df: pd.DataFrame, current_price: float = None) -> TechnicalIndicators:
    """便捷函数：计算技术指标"""
    analyzer = TechnicalAnalyzer()
    return analyzer.calculate(df, current_price)


if __name__ == "__main__":
    # 测试代码
    import numpy as np

    # 生成测试数据
    np.random.seed(42)
    dates = pd.date_range('2025-01-01', periods=100, freq='D')

    # 模拟价格走势
    base_price = 100
    returns = np.random.randn(100) * 0.02
    prices = base_price * np.exp(np.cumsum(returns))

    df = pd.DataFrame({
        'date': dates,
        'open': prices * (1 + np.random.randn(100) * 0.005),
        'high': prices * (1 + abs(np.random.randn(100) * 0.01)),
        'low': prices * (1 - abs(np.random.randn(100) * 0.01)),
        'close': prices,
        'volume': np.random.randint(1000000, 5000000, 100)
    })

    print("=" * 60)
    print("技术指标计算测试")
    print("=" * 60)

    analyzer = TechnicalAnalyzer()
    indicators = analyzer.calculate(df)

    print(indicators.to_text())
    print("\n" + "=" * 60)
    print("计算完成!")
