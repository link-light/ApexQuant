"""
ApexQuant 数据获取模块
支持 Baostock、AKShare 等多数据源自动切换
"""

from .akshare_wrapper import AKShareDataFetcher
from .data_manager import DataManager
from .multi_source import (
    MultiSourceDataFetcher,
    get_stock_data,
    get_realtime_price
)

# 推荐使用多数据源
__all__ = [
    'MultiSourceDataFetcher',
    'get_stock_data',
    'get_realtime_price',
    'AKShareDataFetcher',
    'DataManager'
]

