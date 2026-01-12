"""
因子引擎 - 计算和管理因子
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
    print("警告: C++ 核心模块未加载，使用 Python 替代实现")


class FactorEngine:
    """因子计算引擎"""
    
    def __init__(self, use_cpp: bool = True):
        """
        初始化因子引擎
        
        Args:
            use_cpp: 是否使用 C++ 加速
        """
        self.use_cpp = use_cpp and CORE_LOADED
        self.factors_cache = {}
    
    def calculate_ma(self, df: pd.DataFrame, periods: List[int]) -> pd.DataFrame:
        """
        计算移动平均
        
        Args:
            df: 数据 DataFrame
            periods: 周期列表，如 [5, 10, 20]
        
        Returns:
            带均线的 DataFrame
        """
        df = df.copy()
        closes = df['close'].tolist()
        
        for period in periods:
            col_name = f'MA{period}'
            
            if self.use_cpp:
                ma_values = aq.indicators.sma(closes, period)
                df[col_name] = ma_values
            else:
                df[col_name] = df['close'].rolling(window=period).mean()
        
        return df
    
    def calculate_macd(self, df: pd.DataFrame, 
                      fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
        """
        计算 MACD
        
        Args:
            df: 数据
            fast: 快线周期
            slow: 慢线周期
            signal: 信号线周期
        
        Returns:
            带 MACD 的 DataFrame
        """
        df = df.copy()
        closes = df['close'].tolist()
        
        if self.use_cpp:
            result = aq.indicators.macd(closes, fast, slow, signal)
            df['MACD'] = result.macd
            df['MACD_signal'] = result.signal
            df['MACD_hist'] = result.histogram
        else:
            # Python 实现
            ema_fast = df['close'].ewm(span=fast, adjust=False).mean()
            ema_slow = df['close'].ewm(span=slow, adjust=False).mean()
            df['MACD'] = ema_fast - ema_slow
            df['MACD_signal'] = df['MACD'].ewm(span=signal, adjust=False).mean()
            df['MACD_hist'] = df['MACD'] - df['MACD_signal']
        
        return df
    
    def calculate_rsi(self, df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """计算 RSI"""
        df = df.copy()
        closes = df['close'].tolist()
        
        if self.use_cpp:
            rsi_values = aq.indicators.rsi(closes, period)
            df[f'RSI{period}'] = rsi_values
        else:
            # Python 实现
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            df[f'RSI{period}'] = 100 - (100 / (1 + rs))
        
        return df
    
    def calculate_bollinger_bands(self, df: pd.DataFrame, 
                                  period: int = 20, num_std: float = 2.0) -> pd.DataFrame:
        """计算布林带"""
        df = df.copy()
        closes = df['close'].tolist()
        
        if self.use_cpp:
            result = aq.indicators.bollinger_bands(closes, period, num_std)
            df['BOLL_upper'] = result.upper
            df['BOLL_middle'] = result.middle
            df['BOLL_lower'] = result.lower
        else:
            # Python 实现
            df['BOLL_middle'] = df['close'].rolling(window=period).mean()
            std = df['close'].rolling(window=period).std()
            df['BOLL_upper'] = df['BOLL_middle'] + num_std * std
            df['BOLL_lower'] = df['BOLL_middle'] - num_std * std
        
        return df
    
    def calculate_kdj(self, df: pd.DataFrame, period: int = 9) -> pd.DataFrame:
        """计算 KDJ"""
        df = df.copy()
        
        if self.use_cpp:
            highs = df['high'].tolist()
            lows = df['low'].tolist()
            closes = df['close'].tolist()
            
            result = aq.indicators.kdj(highs, lows, closes, period, 3, 3)
            df['K'] = result.k
            df['D'] = result.d
            df['J'] = result.j
        else:
            # Python 实现
            low_min = df['low'].rolling(window=period).min()
            high_max = df['high'].rolling(window=period).max()
            rsv = (df['close'] - low_min) / (high_max - low_min) * 100
            
            df['K'] = rsv.ewm(com=2).mean()
            df['D'] = df['K'].ewm(com=2).mean()
            df['J'] = 3 * df['K'] - 2 * df['D']
        
        return df
    
    def calculate_all_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算所有常用指标
        
        Args:
            df: 原始数据
        
        Returns:
            带所有指标的 DataFrame
        """
        df = self.calculate_ma(df, [5, 10, 20, 60])
        df = self.calculate_macd(df)
        df = self.calculate_rsi(df, 14)
        df = self.calculate_bollinger_bands(df)
        df = self.calculate_kdj(df)
        
        # 成交量相关
        if self.use_cpp:
            df['OBV'] = aq.indicators.obv(df['close'].tolist(), df['volume'].tolist())
        else:
            obv = [0]
            for i in range(1, len(df)):
                if df['close'].iloc[i] > df['close'].iloc[i-1]:
                    obv.append(obv[-1] + df['volume'].iloc[i])
                elif df['close'].iloc[i] < df['close'].iloc[i-1]:
                    obv.append(obv[-1] - df['volume'].iloc[i])
                else:
                    obv.append(obv[-1])
            df['OBV'] = obv
        
        # ATR
        if self.use_cpp:
            df['ATR'] = aq.indicators.atr(
                df['high'].tolist(), 
                df['low'].tolist(), 
                df['close'].tolist(), 
                14
            )
        else:
            high_low = df['high'] - df['low']
            high_close = np.abs(df['high'] - df['close'].shift())
            low_close = np.abs(df['low'] - df['close'].shift())
            tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            df['ATR'] = tr.rolling(window=14).mean()
        
        # 动量和 ROC
        if self.use_cpp:
            df['Momentum'] = aq.indicators.momentum(df['close'].tolist(), 10)
            df['ROC'] = aq.indicators.roc(df['close'].tolist(), 10)
        else:
            df['Momentum'] = df['close'].diff(10)
            df['ROC'] = df['close'].pct_change(10) * 100
        
        return df
    
    def calculate_custom_factors(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算自定义因子
        
        Args:
            df: 带指标的数据
        
        Returns:
            带自定义因子的 DataFrame
        """
        df = df.copy()
        
        # 趋势因子
        if 'MA5' in df.columns and 'MA20' in df.columns:
            df['trend_factor'] = (df['MA5'] - df['MA20']) / df['MA20']
        
        # 动量因子
        if 'RSI14' in df.columns:
            df['momentum_factor'] = (df['RSI14'] - 50) / 50
        
        # 波动因子
        if 'BOLL_upper' in df.columns and 'BOLL_lower' in df.columns:
            bb_width = (df['BOLL_upper'] - df['BOLL_lower']) / df['BOLL_middle']
            df['volatility_factor'] = bb_width
            
            # 布林带位置
            df['bb_position'] = (df['close'] - df['BOLL_lower']) / (df['BOLL_upper'] - df['BOLL_lower'])
        
        # 成交量因子
        if 'volume' in df.columns:
            df['volume_ma5'] = df['volume'].rolling(5).mean()
            df['volume_factor'] = df['volume'] / df['volume_ma5']
        
        # MACD 强度因子
        if 'MACD_hist' in df.columns:
            df['macd_strength'] = df['MACD_hist'] / df['close']
        
        return df

