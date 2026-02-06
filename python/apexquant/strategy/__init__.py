"""
ApexQuant 策略模块

包含：
- 因子引擎: 技术指标计算
- AI因子生成器: AI驱动的因子生成
- 多因子策略: 市值/动量/价值/质量因子综合
- 深度学习预测: LSTM/GRU价格预测
- 事件驱动策略: 财报/增减持/大宗交易
- 配对交易: 统计套利
- 机器学习模型: XGBoost多因子模型
"""

from .factor_engine import FactorEngine
from .ai_factor_generator import AIFactorGenerator
from .multi_factor_strategy import MultiFactorStrategy, StockScore, calculate_stock_score
from .lstm_predictor import DeepLearningPredictor, PredictionResult, predict_stock_trend
from .event_strategy import (
    EventDrivenStrategy, Event, EventSignal, EventType,
    create_earnings_event, create_holder_change_event
)
from .pairs_trading import PairsTrading, PairInfo, PairSignal, find_pairs
from .ml_model import MultiFactorModel

__all__ = [
    # 因子引擎
    'FactorEngine',
    'AIFactorGenerator',

    # 多因子策略
    'MultiFactorStrategy',
    'StockScore',
    'calculate_stock_score',

    # 深度学习预测
    'DeepLearningPredictor',
    'PredictionResult',
    'predict_stock_trend',

    # 事件驱动
    'EventDrivenStrategy',
    'Event',
    'EventSignal',
    'EventType',
    'create_earnings_event',
    'create_holder_change_event',

    # 配对交易
    'PairsTrading',
    'PairInfo',
    'PairSignal',
    'find_pairs',

    # 机器学习
    'MultiFactorModel',
]

