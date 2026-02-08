# -*- coding: utf-8 -*-
"""
ApexQuant Multi-Source Data Fetcher
支持多个数据源自动切换：AKShare, Baostock
增强错误处理和重试机制
"""

import pandas as pd
from datetime import datetime
import time
import logging
from typing import Optional, Dict, List
from enum import Enum


# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataSourceStatus(Enum):
    """数据源状态"""
    AVAILABLE = "可用"
    UNAVAILABLE = "不可用"
    ERROR = "错误"
    NOT_INSTALLED = "未安装"


class DataSourceError(Exception):
    """数据源错误基类"""
    pass


class DataNotFoundError(DataSourceError):
    """数据未找到错误"""
    pass


class DataSourceUnavailableError(DataSourceError):
    """数据源不可用错误"""
    pass


class MultiSourceDataFetcher:
    """
    多数据源获取器
    支持：AKShare, Baostock
    自动切换和失败重试，增强错误处理
    """

    def __init__(self, max_retries: int = 3, retry_delay: float = 1.0):
        """
        初始化多数据源获取器

        Args:
            max_retries: 最大重试次数
            retry_delay: 重试延迟（秒）
        """
        self.sources = ['baostock', 'akshare']  # Baostock优先（不需要代理）
        self.current_source = None
        self.baostock_login = False
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.source_status: Dict[str, DataSourceStatus] = {}
        self._check_sources_availability()
        self._check_sources_availability()

    def _check_sources_availability(self):
        """检查各数据源的可用性"""
        # 检查 baostock
        try:
            import baostock as bs
            self.source_status['baostock'] = DataSourceStatus.AVAILABLE
            logger.info("[DataSource] Baostock is available")
        except ImportError:
            self.source_status['baostock'] = DataSourceStatus.NOT_INSTALLED
            logger.warning("[DataSource] Baostock not installed: pip install baostock")

        # 检查 akshare
        try:
            import akshare as ak
            self.source_status['akshare'] = DataSourceStatus.AVAILABLE
            logger.info("[DataSource] AKShare is available")
        except ImportError:
            self.source_status['akshare'] = DataSourceStatus.NOT_INSTALLED
            logger.warning("[DataSource] AKShare not installed: pip install akshare")

    def get_source_status(self) -> Dict[str, str]:
        """获取所有数据源状态"""
        return {source: status.value for source, status in self.source_status.items()}

    def _login_baostock(self):
        """登录Baostock"""
        if self.source_status.get('baostock') == DataSourceStatus.NOT_INSTALLED:
            return False

        if not self.baostock_login:
            try:
                import baostock as bs
                lg = bs.login()
                if lg.error_code == '0':
                    self.baostock_login = True
                    self.source_status['baostock'] = DataSourceStatus.AVAILABLE
                    logger.info("[DataSource] Baostock login success")
                    return True
                else:
                    self.source_status['baostock'] = DataSourceStatus.ERROR
                    logger.error(f"[DataSource] Baostock login failed: {lg.error_msg}")
                    return False
            except ImportError:
                self.source_status['baostock'] = DataSourceStatus.NOT_INSTALLED
                logger.error("[DataSource] Baostock not installed: pip install baostock")
                return False
            except Exception as e:
                self.source_status['baostock'] = DataSourceStatus.ERROR
                logger.error(f"[DataSource] Baostock login error: {e}")
                return False
        return True
    
    def _logout_baostock(self):
        """登出Baostock"""
        if self.baostock_login:
            try:
                import baostock as bs
                bs.logout()
                self.baostock_login = False
            except:
                pass
    
    def _fetch_from_baostock(self, symbol, start_date=None, end_date=None):
        """
        从Baostock获取数据（增强错误处理）
        """
        if self.source_status.get('baostock') == DataSourceStatus.NOT_INSTALLED:
            raise DataSourceUnavailableError("Baostock not installed")

        try:
            import baostock as bs

            # 确保登录
            if not self._login_baostock():
                raise DataSourceUnavailableError("Baostock login failed")

            # 转换股票代码格式
            # 600519 -> sh.600519
            # 000001 -> sz.000001
            if symbol.startswith('6'):
                bs_code = f'sh.{symbol}'
            elif symbol.startswith('0') or symbol.startswith('3'):
                bs_code = f'sz.{symbol}'
            else:
                bs_code = symbol

            # 设置日期
            if end_date is None:
                end_date = datetime.now().strftime('%Y-%m-%d')
            if start_date is None:
                start_date = '2020-01-01'

            # 转换日期格式
            if len(start_date) == 8:  # 20230101
                start_date = f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:]}"
            if len(end_date) == 8:
                end_date = f"{end_date[:4]}-{end_date[4:6]}-{end_date[6:]}"

            # 获取数据
            rs = bs.query_history_k_data_plus(
                bs_code,
                "date,open,high,low,close,volume,amount,turn,pctChg",
                start_date=start_date,
                end_date=end_date,
                frequency="d",
                adjustflag="2"  # 前复权
            )

            if rs.error_code != '0':
                logger.error(f"[Baostock] Error: {rs.error_msg}")
                raise DataSourceError(f"Baostock query error: {rs.error_msg}")

            # 转换为DataFrame
            data_list = []
            while rs.next():
                data_list.append(rs.get_row_data())

            if not data_list:
                raise DataNotFoundError(f"No data found for {symbol}")

            df = pd.DataFrame(data_list, columns=rs.fields)

            # 转换数据类型
            df['date'] = pd.to_datetime(df['date'])
            for col in ['open', 'high', 'low', 'close', 'volume', 'amount', 'turn', 'pctChg']:
                df[col] = pd.to_numeric(df[col], errors='coerce')

            # 统一列名
            df.rename(columns={
                'pctChg': 'change_pct',
                'turn': 'turnover_rate'
            }, inplace=True)

            # 添加涨跌幅（百分比形式）
            df['change_pct'] = df['change_pct']

            logger.info(f"[Baostock] Fetched {len(df)} records for {symbol}")
            self.source_status['baostock'] = DataSourceStatus.AVAILABLE
            return df

        except ImportError:
            self.source_status['baostock'] = DataSourceStatus.NOT_INSTALLED
            logger.error("[Baostock] Not installed. Run: pip install baostock")
            raise DataSourceUnavailableError("Baostock not installed")
        except (DataSourceError, DataNotFoundError):
            raise
        except Exception as e:
            self.source_status['baostock'] = DataSourceStatus.ERROR
            logger.error(f"[Baostock] Error: {e}")
            raise DataSourceError(f"Baostock error: {e}")
    
    def _fetch_from_akshare(self, symbol, start_date=None, end_date=None):
        """
        从AKShare获取数据（增强错误处理）
        """
        if self.source_status.get('akshare') == DataSourceStatus.NOT_INSTALLED:
            raise DataSourceUnavailableError("AKShare not installed")

        try:
            # 禁用代理
            import os
            for key in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
                os.environ.pop(key, None)

            import akshare as ak

            # 转换日期格式
            if start_date and len(start_date) == 10:  # 2023-01-01
                start_date = start_date.replace('-', '')
            if end_date and len(end_date) == 10:
                end_date = end_date.replace('-', '')

            # 获取数据
            df = ak.stock_zh_a_hist(
                symbol=symbol,
                period="daily",
                start_date=start_date or "20200101",
                end_date=end_date or datetime.now().strftime("%Y%m%d"),
                adjust="qfq"
            )

            if df is None or df.empty:
                raise DataNotFoundError(f"No data found for {symbol}")

            # 统一列名
            df.rename(columns={
                '日期': 'date',
                '开盘': 'open',
                '收盘': 'close',
                '最高': 'high',
                '最低': 'low',
                '成交量': 'volume',
                '成交额': 'amount',
                '涨跌幅': 'change_pct',
                '换手率': 'turnover_rate'
            }, inplace=True)

            # 转换日期
            df['date'] = pd.to_datetime(df['date'])

            logger.info(f"[AKShare] Fetched {len(df)} records for {symbol}")
            self.source_status['akshare'] = DataSourceStatus.AVAILABLE
            return df

        except ImportError:
            self.source_status['akshare'] = DataSourceStatus.NOT_INSTALLED
            logger.error("[AKShare] Not installed. Run: pip install akshare")
            raise DataSourceUnavailableError("AKShare not installed")
        except (DataSourceError, DataNotFoundError):
            raise
        except Exception as e:
            self.source_status['akshare'] = DataSourceStatus.ERROR
            logger.error(f"[AKShare] Error: {e}")
            raise DataSourceError(f"AKShare error: {e}")
    
    def get_stock_data(self, symbol, start_date=None, end_date=None,
                       preferred_source=None, retry=True):
        """
        获取股票数据（自动切换数据源，增强错误处理）

        参数:
            symbol: 股票代码 (如 "600519", "000001")
            start_date: 开始日期 ("2023-01-01" 或 "20230101")
            end_date: 结束日期
            preferred_source: 首选数据源 ('akshare' 或 'baostock')
            retry: 失败后是否尝试其他数据源

        返回:
            DataFrame 包含: date, open, high, low, close, volume, change_pct等

        异常:
            DataSourceUnavailableError: 所有数据源不可用
            DataNotFoundError: 未找到数据
        """
        # 确定尝试顺序
        if preferred_source:
            sources = [preferred_source] + [s for s in self.sources if s != preferred_source]
        else:
            sources = self.sources

        last_error = None
        attempted_sources = []

        # 尝试每个数据源
        for attempt in range(self.max_retries):
            for source in sources:
                # 跳过不可用的数据源
                if self.source_status.get(source) == DataSourceStatus.NOT_INSTALLED:
                    continue

                logger.info(f"[DataSource] Trying {source} (attempt {attempt + 1}/{self.max_retries})...")
                attempted_sources.append(source)

                try:
                    if source == 'baostock':
                        df = self._fetch_from_baostock(symbol, start_date, end_date)
                    elif source == 'akshare':
                        df = self._fetch_from_akshare(symbol, start_date, end_date)
                    else:
                        continue

                    if df is not None and not df.empty:
                        self.current_source = source
                        logger.info(f"[DataSource] Success with {source}")
                        return df

                except DataNotFoundError as e:
                    last_error = e
                    logger.warning(f"[DataSource] {source} - data not found: {e}")
                    # 数据未找到，不需要重试其他源
                    if not retry:
                        raise
                    continue

                except DataSourceUnavailableError as e:
                    last_error = e
                    logger.warning(f"[DataSource] {source} unavailable: {e}")
                    continue

                except DataSourceError as e:
                    last_error = e
                    logger.warning(f"[DataSource] {source} error: {e}")
                    if not retry:
                        raise
                    continue

                except Exception as e:
                    last_error = e
                    logger.error(f"[DataSource] {source} unexpected error: {e}")
                    continue

            # 如果不重试，跳出循环
            if not retry:
                break

            # 重试延迟
            if attempt < self.max_retries - 1:
                logger.info(f"[DataSource] Retrying in {self.retry_delay} seconds...")
                time.sleep(self.retry_delay)

        # 所有尝试都失败
        error_msg = f"All sources failed for {symbol}. Attempted: {', '.join(set(attempted_sources))}"
        if last_error:
            error_msg += f". Last error: {last_error}"

        logger.error(f"[DataSource] {error_msg}")

        # 检查是否所有源都不可用
        all_unavailable = all(
            self.source_status.get(s) in [DataSourceStatus.NOT_INSTALLED, DataSourceStatus.UNAVAILABLE]
            for s in self.sources
        )

        if all_unavailable:
            raise DataSourceUnavailableError(error_msg)
        else:
            raise DataNotFoundError(error_msg)
    
    def get_realtime_price(self, symbol):
        """
        获取实时价格（简化版）
        返回最新的收盘价和涨跌幅

        Args:
            symbol: 股票代码

        Returns:
            Dict: 包含 price, change, date 的字典

        异常:
            DataSourceError: 获取失败
        """
        try:
            df = self.get_stock_data(
                symbol,
                start_date=(datetime.now() - pd.Timedelta(days=5)).strftime("%Y%m%d"),
                end_date=datetime.now().strftime("%Y%m%d")
            )

            if df is not None and not df.empty:
                latest = df.iloc[-1]
                return {
                    'price': float(latest['close']),
                    'change': float(latest.get('change_pct', 0)),
                    'date': latest['date']
                }
        except Exception as e:
            logger.error(f"[DataSource] Failed to get realtime price for {symbol}: {e}")
            raise DataSourceError(f"Failed to get realtime price: {e}")

        raise DataNotFoundError(f"No realtime price data for {symbol}")
    
    def __del__(self):
        """清理"""
        self._logout_baostock()


# 便捷函数
def get_stock_data(symbol, start_date=None, end_date=None):
    """
    快速获取股票数据
    
    示例:
        df = get_stock_data("600519", "2023-01-01", "2023-12-31")
    """
    fetcher = MultiSourceDataFetcher()
    return fetcher.get_stock_data(symbol, start_date, end_date)


def get_realtime_price(symbol):
    """
    快速获取实时价格
    
    示例:
        data = get_realtime_price("600519")
        print(f"价格: {data['price']}, 涨跌: {data['change']}%")
    """
    fetcher = MultiSourceDataFetcher()
    return fetcher.get_realtime_price(symbol)


if __name__ == "__main__":
    # 测试
    print("=" * 80)
    print("Multi-Source Data Fetcher Test")
    print("=" * 80 + "\n")
    
    fetcher = MultiSourceDataFetcher()
    
    # 测试获取数据
    symbol = "600519"
    print(f"Fetching {symbol} data...\n")
    
    df = fetcher.get_stock_data(symbol, start_date="2024-01-01")
    
    if df is not None:
        print(f"\nData preview:")
        print(df.tail())
        print(f"\nTotal records: {len(df)}")
        print(f"Data source: {fetcher.current_source}")
    else:
        print("Failed to fetch data")
    
    # 测试实时价格
    print(f"\n{'='*80}")
    print("Getting realtime price...")
    price_data = fetcher.get_realtime_price(symbol)
    
    if price_data:
        print(f"Symbol: {symbol}")
        print(f"Price: {price_data['price']:.2f} CNY")
        print(f"Change: {price_data['change']:+.2f}%")
        print(f"Date: {price_data['date']}")
    else:
        print("Failed to get price")
