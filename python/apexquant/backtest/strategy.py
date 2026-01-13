"""
策略基类
"""

from abc import ABC, abstractmethod
import pandas as pd
from typing import Optional
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

try:
    import apexquant_core as aq
except ImportError:
    aq = None


class Strategy(ABC):
    """策略基类"""
    
    def __init__(self, name: str = "Strategy"):
        """
        初始化策略
        
        Args:
            name: 策略名称
        """
        self.name = name
        self.engine = None  # 回测引擎（运行时注入）
        self.data = pd.DataFrame()  # 当前数据
        self.current_bar = None  # 当前 Bar
        self.bar_index = 0  # 当前 Bar 索引
    
    def set_engine(self, engine):
        """设置回测引擎"""
        self.engine = engine
    
    def set_data(self, data: pd.DataFrame):
        """设置数据"""
        self.data = data
    
    @abstractmethod
    def on_bar(self, bar):
        """
        Bar 数据回调（必须实现）
        
        Args:
            bar: Bar 对象
        """
        pass
    
    def on_start(self):
        """策略开始前回调（可选）"""
        pass
    
    def on_end(self):
        """策略结束后回调（可选）"""
        pass
    
    # 交易接口
    def buy(self, symbol: str, quantity: int, price: float = 0.0):
        """
        买入
        
        Args:
            symbol: 证券代码
            quantity: 数量
            price: 限价（0 表示市价）
        """
        if self.engine:
            self.engine.buy(symbol, quantity, price)
    
    def sell(self, symbol: str, quantity: int, price: float = 0.0):
        """
        卖出
        
        Args:
            symbol: 证券代码
            quantity: 数量
            price: 限价（0 表示市价）
        """
        if self.engine:
            self.engine.sell(symbol, quantity, price)
    
    def close_position(self, symbol: str):
        """
        平仓
        
        Args:
            symbol: 证券代码
        """
        if self.engine:
            self.engine.close_position(symbol)
    
    # 查询接口
    def get_cash(self) -> float:
        """获取现金"""
        if self.engine:
            return self.engine.get_cash()
        return 0.0
    
    def get_total_value(self) -> float:
        """获取总资产"""
        if self.engine:
            return self.engine.get_total_value()
        return 0.0
    
    def get_position(self, symbol: str):
        """
        获取持仓
        
        Args:
            symbol: 证券代码
        
        Returns:
            Position 对象
        """
        if self.engine:
            return self.engine.get_position(symbol)
        return None
    
    def has_position(self, symbol: str) -> bool:
        """
        是否有持仓
        
        Args:
            symbol: 证券代码
        """
        if self.engine:
            return self.engine.has_position(symbol)
        return False


class MAStrategy(Strategy):
    """双均线策略示例"""
    
    def __init__(self, short_window: int = 5, long_window: int = 20):
        """
        初始化
        
        Args:
            short_window: 短期均线周期
            long_window: 长期均线周期
        """
        super().__init__("MA Strategy")
        self.short_window = short_window
        self.long_window = long_window
    
    def on_bar(self, bar):
        """Bar 回调"""
        # 获取历史数据
        if self.bar_index < self.long_window:
            self.bar_index += 1
            return
        
        # 计算均线
        closes = self.data['close'].iloc[max(0, self.bar_index - self.long_window):self.bar_index + 1]
        
        if len(closes) < self.long_window:
            self.bar_index += 1
            return
        
        ma_short = closes.iloc[-self.short_window:].mean()
        ma_long = closes.mean()
        
        prev_closes = self.data['close'].iloc[max(0, self.bar_index - self.long_window - 1):self.bar_index]
        if len(prev_closes) >= self.long_window:
            prev_ma_short = prev_closes.iloc[-self.short_window:].mean()
            prev_ma_long = prev_closes.mean()
            
            # 金叉：买入
            if prev_ma_short <= prev_ma_long and ma_short > ma_long:
                if not self.has_position(bar.symbol):
                    # 计算买入数量（使用 50% 资金）
                    cash = self.get_cash()
                    quantity = int(cash * 0.5 / bar.close / 100) * 100  # 整百股
                    if quantity > 0:
                        self.buy(bar.symbol, quantity)
            
            # 死叉：卖出
            elif prev_ma_short >= prev_ma_long and ma_short < ma_long:
                if self.has_position(bar.symbol):
                    self.close_position(bar.symbol)
        
        self.bar_index += 1

