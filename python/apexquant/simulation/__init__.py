"""
ApexQuant 模拟盘交易系统

混合语言架构：
- C++ 核心引擎：高性能订单撮合、账户管理
- Python 业务层：数据源、策略、风控、AI增强
"""

__version__ = "1.0.0"

# 核心模块
from .database import DatabaseManager, create_database
from .simulation_controller import SimulationController, SimulationMode
from .config import SimulationConfig, get_config
from .trading_calendar import TradingCalendar, get_calendar

# 数据源
from .data_source import (
    DataSource,
    MultiSourceAdapter,
    MockDataSource,
    create_data_source,
    bar_to_tick
)

# 风控和分析
from .risk_manager import RiskManager
from .performance_analyzer import PerformanceAnalyzer

# AI增强（可选）
try:
    from .ai_advisor import AITradingAdvisor
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False

# 策略
from .strategies import (
    create_ma_cross_strategy,
    create_buy_hold_strategy,
    create_ai_driven_strategy,
    create_rsi_strategy,
    get_strategy
)

__all__ = [
    # 核心
    'DatabaseManager',
    'create_database',
    'SimulationController',
    'SimulationMode',
    'SimulationConfig',
    'get_config',
    'TradingCalendar',
    'get_calendar',
    
    # 数据源
    'DataSource',
    'MultiSourceAdapter',
    'MockDataSource',
    'create_data_source',
    'bar_to_tick',
    
    # 风控和分析
    'RiskManager',
    'PerformanceAnalyzer',
    
    # 策略
    'create_ma_cross_strategy',
    'create_buy_hold_strategy',
    'create_ai_driven_strategy',
    'create_rsi_strategy',
    'get_strategy',
]

if AI_AVAILABLE:
    __all__.append('AITradingAdvisor')
