"""
回测运行器
"""

import pandas as pd
from typing import Optional
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

try:
    import apexquant_core as aq
    CORE_LOADED = True
except ImportError:
    CORE_LOADED = False
    print("警告: C++ 核心模块未加载")

from .strategy import Strategy
from .performance import PerformanceAnalyzer


class BacktestRunner:
    """回测运行器"""
    
    def __init__(self, initial_capital: float = 1000000.0,
                 commission_rate: float = 0.0003,
                 slippage_rate: float = 0.001):
        """
        初始化
        
        Args:
            initial_capital: 初始资金
            commission_rate: 手续费率
            slippage_rate: 滑点率
        """
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        self.slippage_rate = slippage_rate
        
        if CORE_LOADED:
            config = aq.BacktestConfig()
            config.initial_capital = initial_capital
            config.commission_rate = commission_rate
            config.slippage_rate = slippage_rate
            config.min_commission = 5.0
            
            self.engine = aq.BacktestEngine(config)
        else:
            self.engine = None
    
    def run(self, strategy: Strategy, data: pd.DataFrame):
        """
        运行回测
        
        Args:
            strategy: 策略对象
            data: 数据 DataFrame
        
        Returns:
            回测结果
        """
        if not CORE_LOADED or self.engine is None:
            print("C++ 回测引擎未加载")
            return None
        
        # 转换数据为 C++ Bar 对象
        bars = []
        for _, row in data.iterrows():
            bar = aq.Bar(
                symbol=row.get('symbol', ''),
                timestamp=int(row.get('timestamp', 0)),
                open=float(row['open']),
                high=float(row['high']),
                low=float(row['low']),
                close=float(row['close']),
                volume=int(row.get('volume', 0))
            )
            bars.append(bar)
        
        # 设置数据
        self.engine.set_data(bars)
        
        # 设置策略
        strategy.set_engine(self.engine)
        strategy.set_data(data)
        
        # 策略初始化
        strategy.on_start()
        
        # 设置回调
        def on_bar_callback(bar):
            strategy.current_bar = bar
            strategy.on_bar(bar)
        
        # Python 回调需要特殊处理
        # 这里简化：直接循环调用
        for i, bar in enumerate(bars):
            strategy.bar_index = i
            strategy.current_bar = bar
            strategy.on_bar(bar)
            
            # 手动触发引擎处理
            # （实际应该在 C++ 内部处理，这里为简化）
        
        # 运行回测
        result = self.engine.run()
        
        # 策略结束
        strategy.on_end()
        
        return result
    
    def analyze(self, result, data: pd.DataFrame):
        """
        分析回测结果
        
        Args:
            result: 回测结果
            data: 原始数据
        
        Returns:
            分析结果
        """
        analyzer = PerformanceAnalyzer()
        return analyzer.analyze(result, data)

