"""
ApexQuant 模拟盘数据源适配器

将MultiSourceDataFetcher适配到模拟盘系统
提供统一的数据接口和Mock数据源
"""

import logging
import random
import time
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

# 尝试导入C++模拟盘模块
try:
    import apexquant_simulation as sim
    SIMULATION_MODULE_AVAILABLE = True
except ImportError:
    SIMULATION_MODULE_AVAILABLE = False
    logger.warning("apexquant_simulation module not available, using mock Tick")

# 尝试导入多数据源
try:
    from apexquant.data import MultiSourceDataFetcher, get_stock_data
    MULTI_SOURCE_AVAILABLE = True
except ImportError:
    MULTI_SOURCE_AVAILABLE = False
    logger.warning("MultiSourceDataFetcher not available")


# ============================================================================
# Tick类定义（如果C++模块未编译）
# ============================================================================

if not SIMULATION_MODULE_AVAILABLE:
    class Tick:
        """简化的Tick类（Python版）"""
        def __init__(self):
            self.symbol = ""
            self.timestamp = 0
            self.last_price = 0.0
            self.bid_price = 0.0
            self.ask_price = 0.0
            self.volume = 0
            self.last_close = 0.0
    
    # 注入到sim命名空间
    class sim:
        Tick = Tick


# ============================================================================
# 数据源抽象基类
# ============================================================================

class DataSource(ABC):
    """数据源抽象基类"""
    
    @abstractmethod
    def get_history(
        self, 
        symbol: str, 
        start_date: str, 
        end_date: str, 
        freq: str = '1min'
    ) -> List[Dict]:
        """
        获取历史K线数据
        
        Args:
            symbol: 股票代码
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            freq: 频率 (1min/5min/1d)
            
        Returns:
            K线数据列表，每个元素为字典格式
        """
        pass
    
    @abstractmethod
    def get_latest(self, symbol: str, freq: str = '1min') -> Optional[Dict]:
        """
        获取最新K线（实时模式）
        
        Args:
            symbol: 股票代码
            freq: 频率
            
        Returns:
            K线数据字典
        """
        pass


# ============================================================================
# 多数据源适配器
# ============================================================================

class MultiSourceAdapter(DataSource):
    """多数据源适配器（Baostock + AKShare）"""
    
    def __init__(self):
        """初始化多数据源"""
        if not MULTI_SOURCE_AVAILABLE:
            raise ImportError("MultiSourceDataFetcher not available")
        
        self.fetcher = MultiSourceDataFetcher()
    
    def get_history(
        self, 
        symbol: str, 
        start_date: str, 
        end_date: str, 
        freq: str = '1min'
    ) -> List[Dict]:
        """获取历史数据"""
        try:
            # 调用MultiSourceDataFetcher
            df = self.fetcher.get_stock_data(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                freq=freq
            )
            
            if df is None or df.empty:
                logger.warning(f"No data for {symbol} from {start_date} to {end_date}")
                return []
            
            # 转换为字典列表
            bars = []
            for idx, row in df.iterrows():
                bar = {
                    'symbol': symbol,
                    'timestamp': int(idx.timestamp() * 1000),  # 毫秒时间戳
                    'open': float(row['open']),
                    'high': float(row['high']),
                    'low': float(row['low']),
                    'close': float(row['close']),
                    'volume': int(row['volume'])
                }
                bars.append(bar)
            
            logger.info(f"Loaded {len(bars)} bars for {symbol}")
            return bars
            
        except Exception as e:
            logger.error(f"Failed to get history data: {e}")
            return []
    
    def get_latest(self, symbol: str, freq: str = '1min') -> Optional[Dict]:
        """获取最新数据"""
        try:
            price = self.fetcher.get_realtime_price(symbol)
            
            if price is None:
                return None
            
            # 构造简单的bar
            now = datetime.now()
            bar = {
                'symbol': symbol,
                'timestamp': int(now.timestamp() * 1000),
                'open': price,
                'high': price,
                'low': price,
                'close': price,
                'volume': 0  # 实时数据没有成交量
            }
            
            return bar
            
        except Exception as e:
            logger.error(f"Failed to get latest data: {e}")
            return None


# ============================================================================
# Mock数据源（测试用）
# ============================================================================

class MockDataSource(DataSource):
    """Mock数据源（生成随机游走数据）"""
    
    def __init__(self, initial_price: float = 100.0, volatility: float = 0.01):
        """
        初始化Mock数据源
        
        Args:
            initial_price: 初始价格
            volatility: 波动率
        """
        self.initial_price = initial_price
        self.volatility = volatility
        self.current_price = initial_price
    
    def get_history(
        self, 
        symbol: str, 
        start_date: str, 
        end_date: str, 
        freq: str = '1min'
    ) -> List[Dict]:
        """生成历史模拟数据"""
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        
        # 计算需要多少根K线
        delta_days = (end_dt - start_dt).days + 1
        
        if freq == '1min':
            bars_per_day = 240  # 4小时交易
            total_bars = delta_days * bars_per_day
        elif freq == '5min':
            bars_per_day = 48
            total_bars = delta_days * bars_per_day
        elif freq == '1d':
            total_bars = delta_days
        else:
            total_bars = delta_days * 240
        
        bars = []
        price = self.initial_price
        current_time = int(start_dt.timestamp() * 1000)
        
        for i in range(total_bars):
            # 随机游走
            change = random.gauss(0, self.volatility)
            open_price = price
            close_price = price * (1 + change)
            high_price = max(open_price, close_price) * (1 + abs(random.gauss(0, self.volatility/2)))
            low_price = min(open_price, close_price) * (1 - abs(random.gauss(0, self.volatility/2)))
            
            bar = {
                'symbol': symbol,
                'timestamp': current_time + i * 60000,  # 每分钟
                'open': round(open_price, 2),
                'high': round(high_price, 2),
                'low': round(low_price, 2),
                'close': round(close_price, 2),
                'volume': random.randint(10000, 100000)
            }
            
            bars.append(bar)
            price = close_price  # 下一根K线从这个价格开始
        
        logger.info(f"Generated {len(bars)} mock bars for {symbol}")
        return bars
    
    def get_latest(self, symbol: str, freq: str = '1min') -> Optional[Dict]:
        """生成最新模拟数据"""
        change = random.gauss(0, self.volatility)
        self.current_price *= (1 + change)
        
        bar = {
            'symbol': symbol,
            'timestamp': int(datetime.now().timestamp() * 1000),
            'open': round(self.current_price, 2),
            'high': round(self.current_price * 1.001, 2),
            'low': round(self.current_price * 0.999, 2),
            'close': round(self.current_price, 2),
            'volume': random.randint(10000, 100000)
        }
        
        return bar


# ============================================================================
# K线转Tick辅助函数
# ============================================================================

def bar_to_tick(bar: Dict, last_close: float = 0.0) -> sim.Tick:
    """
    将K线数据转换为C++ Tick对象
    
    Args:
        bar: K线数据字典
        last_close: 昨收价（用于涨跌停判断）
        
    Returns:
        Tick对象
    """
    tick = sim.Tick()
    tick.symbol = bar['symbol']
    tick.timestamp = bar['timestamp']
    tick.last_price = bar['close']
    tick.bid_price = bar['close'] * 0.999  # 简化：买一价
    tick.ask_price = bar['close'] * 1.001  # 简化：卖一价
    tick.volume = bar.get('volume', 0)
    tick.last_close = last_close
    
    return tick


# ============================================================================
# 工厂函数
# ============================================================================

def create_data_source(provider: str = 'baostock') -> DataSource:
    """
    创建数据源实例
    
    Args:
        provider: 数据提供商 (baostock/akshare/mock)
        
    Returns:
        DataSource实例
    """
    if provider == 'mock':
        return MockDataSource()
    else:
        # 使用多数据源（baostock主，akshare备）
        return MultiSourceAdapter()


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 60)
    print("ApexQuant Data Source Test")
    print("=" * 60)
    
    # 测试Mock数据源
    print("\n[Test] MockDataSource")
    mock_source = MockDataSource(initial_price=100.0, volatility=0.02)
    
    bars = mock_source.get_history(
        symbol="TEST.SH",
        start_date="2025-01-01",
        end_date="2025-01-02",
        freq="1min"
    )
    
    print(f"Generated {len(bars)} bars")
    print(f"First bar: {bars[0]}")
    print(f"Last bar: {bars[-1]}")
    
    latest = mock_source.get_latest("TEST.SH")
    print(f"Latest bar: {latest}")
    
    # 测试bar_to_tick转换
    print("\n[Test] bar_to_tick conversion")
    tick = bar_to_tick(bars[0], last_close=99.0)
    print(f"Tick: symbol={tick.symbol}, price={tick.last_price}, bid={tick.bid_price}, ask={tick.ask_price}")
    
    # 测试多数据源（如果可用）
    if MULTI_SOURCE_AVAILABLE:
        print("\n[Test] MultiSourceAdapter")
        try:
            multi_source = MultiSourceAdapter()
            print("[OK] MultiSourceAdapter created")
        except Exception as e:
            print(f"[SKIP] MultiSourceAdapter: {e}")
    
    print("\n" + "=" * 60)
    print("[OK] Data source test passed!")
    print("=" * 60)
