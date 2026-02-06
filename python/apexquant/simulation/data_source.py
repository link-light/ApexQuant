"""
ApexQuant Data Source Adapter for Simulation
模拟盘数据源适配器（使用已有的MultiSource）
"""

import sys
from pathlib import Path
import pandas as pd
import datetime
from typing import Optional, List
import logging

# 导入已有的多数据源模块
try:
    from apexquant.data.multi_source import MultiSourceDataFetcher
except ImportError:
    # 如果导入失败，添加路径重试
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from apexquant.data.multi_source import MultiSourceDataFetcher

logger = logging.getLogger(__name__)


class SimulationDataSource:
    """模拟盘数据源适配器"""
    
    def __init__(self, primary_source: str = "baostock", backup_source: str = "akshare"):
        """
        初始化数据源
        
        Args:
            primary_source: 主数据源
            backup_source: 备用数据源
        """
        self.fetcher = MultiSourceDataFetcher(
            primary_source=primary_source,
            backup_source=backup_source
        )
        logger.info(f"Data source initialized: primary={primary_source}, backup={backup_source}")
    
    def get_stock_data(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        freq: str = "d"
    ) -> Optional[pd.DataFrame]:
        """
        获取股票历史数据
        
        Args:
            symbol: 股票代码（如 '000001' 或 'sh.000001'）
            start_date: 开始日期 'YYYY-MM-DD'
            end_date: 结束日期 'YYYY-MM-DD'
            freq: 频率 'd'=日线, 'w'=周线, 'm'=月线
            
        Returns:
            DataFrame with columns: date, open, high, low, close, volume
        """
        try:
            # 标准化股票代码
            symbol = self._normalize_symbol(symbol)
            
            df = self.fetcher.get_stock_data(symbol, start_date, end_date, freq)
            
            if df is not None and not df.empty:
                # 确保列名标准化
                df = self._standardize_columns(df)
                logger.debug(f"Fetched {len(df)} rows for {symbol}")
                return df
            else:
                logger.warning(f"No data fetched for {symbol}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to fetch stock data for {symbol}: {e}")
            return None
    
    def get_realtime_quotes(self, symbols: List[str]) -> Optional[pd.DataFrame]:
        """
        获取实时行情
        
        Args:
            symbols: 股票代码列表
            
        Returns:
            DataFrame with realtime quotes
        """
        try:
            # 标准化股票代码
            symbols = [self._normalize_symbol(s) for s in symbols]
            
            df = self.fetcher.get_realtime_quotes(symbols)
            
            if df is not None and not df.empty:
                logger.debug(f"Fetched realtime quotes for {len(symbols)} symbols")
                return df
            else:
                logger.warning("No realtime quotes fetched")
                return None
                
        except Exception as e:
            logger.error(f"Failed to fetch realtime quotes: {e}")
            return None
    
    def get_latest_price(self, symbol: str) -> Optional[float]:
        """
        获取最新价格
        
        Args:
            symbol: 股票代码
            
        Returns:
            最新价格，如果失败返回None
        """
        try:
            symbol = self._normalize_symbol(symbol)
            quotes = self.get_realtime_quotes([symbol])
            
            if quotes is not None and not quotes.empty:
                # 尝试获取价格列
                price_columns = ['current', 'price', 'last_price', 'close']
                for col in price_columns:
                    if col in quotes.columns:
                        return float(quotes.iloc[0][col])
                
                logger.warning(f"No price column found in realtime quotes for {symbol}")
                return None
            else:
                return None
                
        except Exception as e:
            logger.error(f"Failed to get latest price for {symbol}: {e}")
            return None
    
    def get_stock_info(self, symbol: str) -> Optional[dict]:
        """
        获取股票基本信息
        
        Args:
            symbol: 股票代码
            
        Returns:
            股票信息字典
        """
        try:
            symbol = self._normalize_symbol(symbol)
            info = self.fetcher.get_stock_info(symbol)
            
            if info:
                logger.debug(f"Fetched info for {symbol}")
                return info
            else:
                logger.warning(f"No info fetched for {symbol}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to fetch stock info for {symbol}: {e}")
            return None
    
    def _normalize_symbol(self, symbol: str) -> str:
        """
        标准化股票代码
        
        Args:
            symbol: 原始股票代码
            
        Returns:
            标准化后的代码
        """
        # 去除空格
        symbol = symbol.strip()
        
        # 如果已经有市场前缀，直接返回
        if '.' in symbol:
            return symbol
        
        # 根据代码判断市场
        if symbol.startswith('6'):
            # 上海主板
            return f"sh.{symbol}"
        elif symbol.startswith('0') or symbol.startswith('3'):
            # 深圳主板/创业板
            return f"sz.{symbol}"
        else:
            # 默认深圳
            return f"sz.{symbol}"
    
    def _standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        标准化DataFrame列名
        
        Args:
            df: 原始DataFrame
            
        Returns:
            标准化后的DataFrame
        """
        # 列名映射
        column_mapping = {
            '日期': 'date',
            '开盘价': 'open',
            '最高价': 'high',
            '最低价': 'low',
            '收盘价': 'close',
            '成交量': 'volume',
            '成交额': 'amount',
            'code': 'symbol',
            '代码': 'symbol',
        }
        
        # 重命名列
        df = df.rename(columns=column_mapping)
        
        # 确保必要的列存在
        required_columns = ['date', 'open', 'high', 'low', 'close', 'volume']
        for col in required_columns:
            if col not in df.columns:
                logger.warning(f"Missing required column: {col}")
        
        return df
    
    def get_trading_days(self, start_date: str, end_date: str) -> List[str]:
        """
        获取交易日列表
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            交易日列表
        """
        try:
            # 使用某个股票的日线数据来获取交易日
            # 选择一个稳定存在的股票，如上证指数
            df = self.get_stock_data("sh.000001", start_date, end_date, freq="d")
            
            if df is not None and not df.empty and 'date' in df.columns:
                dates = df['date'].tolist()
                logger.debug(f"Fetched {len(dates)} trading days")
                return dates
            else:
                logger.warning("Failed to fetch trading days")
                return []
                
        except Exception as e:
            logger.error(f"Failed to fetch trading days: {e}")
            return []


def create_data_source(config: dict) -> SimulationDataSource:
    """
    创建数据源实例
    
    Args:
        config: 配置字典
        
    Returns:
        数据源实例
    """
    primary = config.get("primary", "baostock")
    backup = config.get("backup", "akshare")
    
    return SimulationDataSource(primary_source=primary, backup_source=backup)


class MockDataSource:
    """Mock数据源，用于测试"""
    
    def __init__(self, num_days: int = 100, initial_price: float = 100.0):
        """
        初始化Mock数据源
        
        Args:
            num_days: 生成数据天数
            initial_price: 初始价格
        """
        self.num_days = num_days
        self.initial_price = initial_price
        logger.info(f"MockDataSource initialized: {num_days} days, initial_price={initial_price}")
    
    def get_stock_data(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        freq: str = "d"
    ) -> Optional[pd.DataFrame]:
        """
        生成随机游走数据
        
        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            freq: 频率
            
        Returns:
            DataFrame with columns: date, open, high, low, close, volume
        """
        import numpy as np
        
        try:
            # 生成日期序列
            start = pd.to_datetime(start_date)
            end = pd.to_datetime(end_date)
            dates = pd.date_range(start, end, freq='D')
            
            # 限制数量
            if len(dates) > self.num_days:
                dates = dates[:self.num_days]
            
            # 生成随机游走价格
            np.random.seed(42)  # 固定种子以便测试
            returns = np.random.normal(0.001, 0.02, len(dates))  # 日均收益0.1%，波动2%
            prices = self.initial_price * np.cumprod(1 + returns)
            
            # 生成OHLC数据
            data = []
            for i, (date, close) in enumerate(zip(dates, prices)):
                # 生成开高低收
                daily_volatility = close * 0.02  # 2%日内波动
                open_price = close * (1 + np.random.normal(0, 0.005))
                high = max(open_price, close) * (1 + abs(np.random.normal(0, 0.01)))
                low = min(open_price, close) * (1 - abs(np.random.normal(0, 0.01)))
                
                # 生成成交量
                volume = np.random.randint(1000000, 10000000)
                
                data.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'open': round(open_price, 2),
                    'high': round(high, 2),
                    'low': round(low, 2),
                    'close': round(close, 2),
                    'volume': volume
                })
            
            df = pd.DataFrame(data)
            logger.debug(f"Generated {len(df)} mock data rows for {symbol}")
            return df
            
        except Exception as e:
            logger.error(f"Failed to generate mock data: {e}")
            return None
    
    def get_realtime_quotes(self, symbols: List[str]) -> Optional[pd.DataFrame]:
        """获取实时行情（Mock）"""
        import numpy as np
        
        data = []
        for symbol in symbols:
            price = self.initial_price * (1 + np.random.normal(0, 0.01))
            data.append({
                'symbol': symbol,
                'current': round(price, 2),
                'price': round(price, 2)
            })
        
        return pd.DataFrame(data)
    
    def get_latest_price(self, symbol: str) -> Optional[float]:
        """获取最新价格（Mock）"""
        import numpy as np
        return self.initial_price * (1 + np.random.normal(0, 0.01))


def bar_to_tick(bar: pd.Series, num_ticks: int = 10) -> List[dict]:
    """
    将K线数据转换为Tick数据
    
    Args:
        bar: K线数据（Series），包含 open, high, low, close, volume
        num_ticks: 生成的tick数量
        
    Returns:
        Tick数据列表，每个tick包含 price, volume, timestamp
    """
    import numpy as np
    
    try:
        open_price = float(bar['open'])
        high = float(bar['high'])
        low = float(bar['low'])
        close = float(bar['close'])
        volume = int(bar['volume'])
        
        # 生成价格序列：open -> high/low -> close
        prices = []
        
        # 开盘价
        prices.append(open_price)
        
        # 中间价格在high和low之间随机游走
        for i in range(num_ticks - 2):
            # 随机在high和low之间
            price = low + (high - low) * np.random.random()
            prices.append(price)
        
        # 收盘价
        prices.append(close)
        
        # 分配成交量
        volumes = np.random.dirichlet(np.ones(num_ticks)) * volume
        volumes = volumes.astype(int)
        
        # 生成时间戳（假设在一分钟内均匀分布）
        base_time = datetime.datetime.now()
        timestamps = [base_time + datetime.timedelta(seconds=i*6) for i in range(num_ticks)]
        
        # 组装tick数据
        ticks = []
        for price, vol, ts in zip(prices, volumes, timestamps):
            ticks.append({
                'price': round(price, 2),
                'volume': int(vol),
                'timestamp': ts.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return ticks
        
    except Exception as e:
        logger.error(f"Failed to convert bar to ticks: {e}")
        return []