# -*- coding: utf-8 -*-
"""
AKShare Data Fetcher Wrapper
"""

import pandas as pd
from datetime import datetime
import os


class AKShareDataFetcher:
    """AKShare数据获取包装器"""

    def __init__(self):
        # 禁用代理
        for key in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
            os.environ.pop(key, None)

    def get_stock_data(self, symbol, start_date=None, end_date=None):
        """
        获取股票历史数据

        参数:
            symbol: 股票代码 (如 "600519")
            start_date: 开始日期
            end_date: 结束日期
        """
        try:
            import akshare as ak

            # 转换日期格式
            if start_date and len(start_date) == 10:
                start_date = start_date.replace('-', '')
            if end_date and len(end_date) == 10:
                end_date = end_date.replace('-', '')

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

            df['date'] = pd.to_datetime(df['date'])
            return df

        except Exception as e:
            print(f"[AKShare] Error: {e}")
            return None

    def get_realtime_quote(self, symbol):
        """获取实时行情"""
        try:
            import akshare as ak
            df = ak.stock_zh_a_spot_em()
            row = df[df['代码'] == symbol]
            if row.empty:
                return None
            row = row.iloc[0]
            return {
                'symbol': symbol,
                'name': row['名称'],
                'price': float(row['最新价']),
                'change_pct': float(row['涨跌幅']),
                'volume': int(row['成交量']),
                'amount': float(row['成交额']),
            }
        except Exception as e:
            print(f"[AKShare] Realtime error: {e}")
            return None
