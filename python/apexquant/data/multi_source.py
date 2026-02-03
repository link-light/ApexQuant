# -*- coding: utf-8 -*-
"""
ApexQuant Multi-Source Data Fetcher
支持多个数据源自动切换：AKShare, Baostock
"""

import pandas as pd
from datetime import datetime
import time


class MultiSourceDataFetcher:
    """
    多数据源获取器
    支持：AKShare, Baostock
    自动切换和失败重试
    """
    
    def __init__(self):
        self.sources = ['baostock', 'akshare']  # Baostock优先（不需要代理）
        self.current_source = None
        self.baostock_login = False
        
    def _login_baostock(self):
        """登录Baostock"""
        if not self.baostock_login:
            try:
                import baostock as bs
                lg = bs.login()
                if lg.error_code == '0':
                    self.baostock_login = True
                    print("[DataSource] Baostock login success")
                    return True
                else:
                    print(f"[DataSource] Baostock login failed: {lg.error_msg}")
                    return False
            except ImportError:
                print("[DataSource] Baostock not installed: pip install baostock")
                return False
            except Exception as e:
                print(f"[DataSource] Baostock login error: {e}")
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
        从Baostock获取数据
        """
        try:
            import baostock as bs
            
            # 确保登录
            if not self._login_baostock():
                return None
            
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
                print(f"[Baostock] Error: {rs.error_msg}")
                return None
            
            # 转换为DataFrame
            data_list = []
            while rs.next():
                data_list.append(rs.get_row_data())
            
            if not data_list:
                return None
            
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
            
            print(f"[Baostock] Fetched {len(df)} records for {symbol}")
            return df
            
        except ImportError:
            print("[Baostock] Not installed. Run: pip install baostock")
            return None
        except Exception as e:
            print(f"[Baostock] Error: {e}")
            return None
    
    def _fetch_from_akshare(self, symbol, start_date=None, end_date=None):
        """
        从AKShare获取数据
        """
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
                return None
            
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
            
            print(f"[AKShare] Fetched {len(df)} records for {symbol}")
            return df
            
        except Exception as e:
            print(f"[AKShare] Error: {e}")
            return None
    
    def get_stock_data(self, symbol, start_date=None, end_date=None, 
                       preferred_source=None, retry=True):
        """
        获取股票数据（自动切换数据源）
        
        参数:
            symbol: 股票代码 (如 "600519", "000001")
            start_date: 开始日期 ("2023-01-01" 或 "20230101")
            end_date: 结束日期
            preferred_source: 首选数据源 ('akshare' 或 'baostock')
            retry: 失败后是否尝试其他数据源
        
        返回:
            DataFrame 包含: date, open, high, low, close, volume, change_pct等
        """
        # 确定尝试顺序
        if preferred_source:
            sources = [preferred_source] + [s for s in self.sources if s != preferred_source]
        else:
            sources = self.sources
        
        # 尝试每个数据源
        for source in sources:
            print(f"[DataSource] Trying {source}...")
            
            try:
                if source == 'baostock':
                    df = self._fetch_from_baostock(symbol, start_date, end_date)
                elif source == 'akshare':
                    df = self._fetch_from_akshare(symbol, start_date, end_date)
                else:
                    continue
                
                if df is not None and not df.empty:
                    self.current_source = source
                    print(f"[DataSource] Success with {source}")
                    return df
                
            except Exception as e:
                print(f"[DataSource] {source} failed: {e}")
            
            if not retry:
                break
        
        print(f"[DataSource] All sources failed for {symbol}")
        return None
    
    def get_realtime_price(self, symbol):
        """
        获取实时价格（简化版）
        返回最新的收盘价和涨跌幅
        """
        df = self.get_stock_data(symbol, 
                                 start_date=(datetime.now() - pd.Timedelta(days=5)).strftime("%Y%m%d"),
                                 end_date=datetime.now().strftime("%Y%m%d"))
        
        if df is not None and not df.empty:
            latest = df.iloc[-1]
            return {
                'price': float(latest['close']),
                'change': float(latest.get('change_pct', 0)),
                'date': latest['date']
            }
        return None
    
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
