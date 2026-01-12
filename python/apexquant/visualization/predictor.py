"""
简单预测模型
"""

import pandas as pd
import numpy as np
from typing import Tuple, Optional
from sklearn.linear_model import LinearRegression


class SimplePredictor:
    """简单预测器"""
    
    def __init__(self):
        self.model = None
        self.last_value = None
    
    def predict_ma(self, df: pd.DataFrame, 
                   periods: int = 5,
                   forecast_days: int = 5) -> pd.Series:
        """
        移动平均预测
        
        Args:
            df: 历史数据
            periods: 移动平均周期
            forecast_days: 预测天数
        
        Returns:
            预测值 Series
        """
        closes = df['close'].values
        
        # 计算最近的移动平均
        ma = np.mean(closes[-periods:])
        
        # 简单假设：未来价格围绕移动平均波动
        predictions = [ma] * forecast_days
        
        # 生成未来日期
        last_date = df.index[-1] if isinstance(df.index, pd.DatetimeIndex) else pd.to_datetime(df['date'].iloc[-1])
        future_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), 
                                     periods=forecast_days, freq='D')
        
        return pd.Series(predictions, index=future_dates, name='prediction')
    
    def predict_linear(self, df: pd.DataFrame,
                      forecast_days: int = 5) -> pd.Series:
        """
        线性回归预测
        
        Args:
            df: 历史数据
            forecast_days: 预测天数
        
        Returns:
            预测值 Series
        """
        closes = df['close'].values
        
        # 准备训练数据
        X = np.arange(len(closes)).reshape(-1, 1)
        y = closes
        
        # 训练模型
        model = LinearRegression()
        model.fit(X, y)
        
        # 预测
        future_X = np.arange(len(closes), len(closes) + forecast_days).reshape(-1, 1)
        predictions = model.predict(future_X)
        
        # 生成未来日期
        last_date = df.index[-1] if isinstance(df.index, pd.DatetimeIndex) else pd.to_datetime(df['date'].iloc[-1])
        future_dates = pd.date_range(start=last_date + pd.Timedelta(days=1),
                                     periods=forecast_days, freq='D')
        
        self.model = model
        
        return pd.Series(predictions, index=future_dates, name='prediction')
    
    def predict_trend_following(self, df: pd.DataFrame,
                               short_window: int = 5,
                               long_window: int = 20,
                               forecast_days: int = 5) -> pd.Series:
        """
        趋势跟随预测
        
        Args:
            df: 历史数据
            short_window: 短期窗口
            long_window: 长期窗口
            forecast_days: 预测天数
        
        Returns:
            预测值 Series
        """
        closes = df['close'].values
        
        # 计算短期和长期均线
        ma_short = np.mean(closes[-short_window:])
        ma_long = np.mean(closes[-long_window:])
        
        # 判断趋势
        trend = 1 if ma_short > ma_long else -1
        
        # 计算平均变化率
        recent_changes = np.diff(closes[-10:])
        avg_change = np.mean(recent_changes)
        
        # 预测：当前价格 + 趋势 * 平均变化
        predictions = []
        last_price = closes[-1]
        
        for i in range(forecast_days):
            next_price = last_price + trend * avg_change
            predictions.append(next_price)
            last_price = next_price
        
        # 生成未来日期
        last_date = df.index[-1] if isinstance(df.index, pd.DatetimeIndex) else pd.to_datetime(df['date'].iloc[-1])
        future_dates = pd.date_range(start=last_date + pd.Timedelta(days=1),
                                     periods=forecast_days, freq='D')
        
        return pd.Series(predictions, index=future_dates, name='prediction')
    
    def predict_ensemble(self, df: pd.DataFrame,
                        forecast_days: int = 5) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        集成预测（多个模型的平均）
        
        Args:
            df: 历史数据
            forecast_days: 预测天数
        
        Returns:
            (预测均值, 上界, 下界)
        """
        # 三种方法预测
        pred_ma = self.predict_ma(df, forecast_days=forecast_days)
        pred_linear = self.predict_linear(df, forecast_days=forecast_days)
        pred_trend = self.predict_trend_following(df, forecast_days=forecast_days)
        
        # 取平均
        predictions = (pred_ma + pred_linear + pred_trend) / 3
        
        # 计算标准差作为不确定性估计
        std = np.std([pred_ma.values, pred_linear.values, pred_trend.values], axis=0)
        
        upper = predictions + std
        lower = predictions - std
        
        return predictions, upper, lower

