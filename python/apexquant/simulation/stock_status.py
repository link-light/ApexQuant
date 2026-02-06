"""
ApexQuant Stock Status Manager
股票状态管理器：停牌、退市、涨跌停等
"""

from enum import Enum
from typing import Dict, Optional, Set
import datetime
import logging

logger = logging.getLogger(__name__)


class StockStatus(Enum):
    """股票状态"""
    NORMAL = "正常交易"
    SUSPENDED = "停牌"
    DELISTING = "退市整理"
    LIMIT_UP = "涨停"
    LIMIT_DOWN = "跌停"
    UNKNOWN = "未知"


class StockStatusManager:
    """
    股票状态管理器
    
    功能：
    - 检查股票是否停牌
    - 检查股票是否退市
    - 缓存状态信息避免频繁查询
    """
    
    def __init__(self, cache_ttl: int = 3600):
        """
        初始化
        
        Args:
            cache_ttl: 缓存有效期（秒），默认1小时
        """
        self.cache_ttl = cache_ttl
        self.status_cache: Dict[str, tuple] = {}  # {symbol: (status, timestamp)}
        self.suspended_stocks: Set[str] = set()
        self.delisting_stocks: Set[str] = set()
        
    def get_stock_status(self, symbol: str, force_update: bool = False) -> StockStatus:
        """
        获取股票状态
        
        Args:
            symbol: 股票代码
            force_update: 是否强制更新（不使用缓存）
            
        Returns:
            股票状态
        """
        # 检查缓存
        if not force_update and symbol in self.status_cache:
            status, timestamp = self.status_cache[symbol]
            age = (datetime.datetime.now() - timestamp).total_seconds()
            
            if age < self.cache_ttl:
                return status
        
        # 从数据源获取
        status = self._fetch_stock_status(symbol)
        
        # 更新缓存
        self.status_cache[symbol] = (status, datetime.datetime.now())
        
        # 更新停牌/退市集合
        if status == StockStatus.SUSPENDED:
            self.suspended_stocks.add(symbol)
        else:
            self.suspended_stocks.discard(symbol)
            
        if status == StockStatus.DELISTING:
            self.delisting_stocks.add(symbol)
        else:
            self.delisting_stocks.discard(symbol)
        
        return status
    
    def _fetch_stock_status(self, symbol: str) -> StockStatus:
        """
        从数据源获取股票状态
        
        Args:
            symbol: 股票代码
            
        Returns:
            股票状态
        """
        try:
            import akshare as ak
            
            # 去除市场前缀
            code = symbol.replace('sh.', '').replace('sz.', '')
            
            # 获取实时行情（包含状态信息）
            df = ak.stock_zh_a_spot_em()
            
            if df is None or df.empty:
                logger.warning(f"无法获取{symbol}实时行情")
                return StockStatus.UNKNOWN
            
            # 查找该股票
            stock_data = df[df['代码'] == code]
            
            if stock_data.empty:
                logger.warning(f"未找到{symbol}的数据")
                return StockStatus.UNKNOWN
            
            # 检查状态字段（不同数据源字段名可能不同）
            # 某些情况下可以通过涨跌幅判断
            change_pct = stock_data.iloc[0].get('涨跌幅', 0)
            
            # 检查是否涨停/跌停（根据板块不同）
            limit_pct = self._get_limit_pct(symbol)
            
            if abs(change_pct - limit_pct * 100) < 0.1:
                return StockStatus.LIMIT_UP
            elif abs(change_pct + limit_pct * 100) < 0.1:
                return StockStatus.LIMIT_DOWN
            
            # TODO: 需要更可靠的停牌检测方法
            # AKShare的实时行情如果股票停牌，可能不会出现在列表中
            # 或者成交量为0
            volume = stock_data.iloc[0].get('成交量', 0)
            if volume == 0:
                logger.info(f"{symbol}成交量为0，可能停牌")
                return StockStatus.SUSPENDED
            
            return StockStatus.NORMAL
            
        except Exception as e:
            logger.error(f"获取{symbol}状态失败: {e}")
            return StockStatus.UNKNOWN
    
    def _get_limit_pct(self, symbol: str) -> float:
        """
        获取涨跌停幅度
        
        Args:
            symbol: 股票代码
            
        Returns:
            涨跌停幅度（小数形式，如0.1表示10%）
        """
        # ST股票：5%
        if 'ST' in symbol or 'st' in symbol:
            return 0.05
        
        # 科创板（688开头）：20%
        if symbol.startswith('688') or symbol.startswith('sh.688'):
            return 0.20
        
        # 创业板（300开头）：20%
        if symbol.startswith('300') or symbol.startswith('sz.300'):
            return 0.20
        
        # 北交所（8或4开头）：30%
        if symbol.startswith('8') or symbol.startswith('4'):
            return 0.30
        
        # 普通A股：10%
        return 0.10
    
    def is_suspended(self, symbol: str) -> bool:
        """
        检查是否停牌
        
        Args:
            symbol: 股票代码
            
        Returns:
            是否停牌
        """
        status = self.get_stock_status(symbol)
        return status == StockStatus.SUSPENDED
    
    def is_tradable(self, symbol: str) -> bool:
        """
        检查是否可交易
        
        Args:
            symbol: 股票代码
            
        Returns:
            是否可交易
        """
        status = self.get_stock_status(symbol)
        return status in [StockStatus.NORMAL, StockStatus.LIMIT_UP, StockStatus.LIMIT_DOWN]
    
    def is_delisting(self, symbol: str) -> bool:
        """
        检查是否退市整理
        
        Args:
            symbol: 股票代码
            
        Returns:
            是否退市整理
        """
        status = self.get_stock_status(symbol)
        return status == StockStatus.DELISTING
    
    def get_all_suspended(self) -> Set[str]:
        """
        获取所有停牌股票列表
        
        Returns:
            停牌股票代码集合
        """
        return self.suspended_stocks.copy()
    
    def clear_cache(self):
        """清空缓存"""
        self.status_cache.clear()
        self.suspended_stocks.clear()
        self.delisting_stocks.clear()
        logger.info("股票状态缓存已清空")
    
    def mark_as_suspended(self, symbol: str):
        """
        手动标记为停牌（用于已知停牌信息）
        
        Args:
            symbol: 股票代码
        """
        self.status_cache[symbol] = (StockStatus.SUSPENDED, datetime.datetime.now())
        self.suspended_stocks.add(symbol)
        logger.info(f"手动标记{symbol}为停牌")
    
    def mark_as_normal(self, symbol: str):
        """
        手动标记为正常（用于已知复牌信息）
        
        Args:
            symbol: 股票代码
        """
        self.status_cache[symbol] = (StockStatus.NORMAL, datetime.datetime.now())
        self.suspended_stocks.discard(symbol)
        logger.info(f"手动标记{symbol}为正常交易")


# 全局实例
_global_status_manager: Optional[StockStatusManager] = None


def get_status_manager() -> StockStatusManager:
    """
    获取全局股票状态管理器（单例模式）
    
    Returns:
        状态管理器实例
    """
    global _global_status_manager
    
    if _global_status_manager is None:
        _global_status_manager = StockStatusManager()
    
    return _global_status_manager


if __name__ == "__main__":
    # 测试
    manager = StockStatusManager()
    
    test_symbols = ["600519", "000001", "688001"]
    
    for symbol in test_symbols:
        status = manager.get_stock_status(symbol)
        print(f"{symbol}: {status.value}")
        print(f"  可交易: {manager.is_tradable(symbol)}")
        print(f"  停牌: {manager.is_suspended(symbol)}")
















