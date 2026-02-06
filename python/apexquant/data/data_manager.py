# -*- coding: utf-8 -*-
"""
Data Manager - 数据管理器
"""

import pandas as pd
from datetime import datetime
from pathlib import Path


class DataManager:
    """数据管理器，支持缓存和多数据源"""

    def __init__(self, cache_dir=None):
        self.cache_dir = Path(cache_dir) if cache_dir else Path("data/cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._fetcher = None

    @property
    def fetcher(self):
        if self._fetcher is None:
            from .multi_source import MultiSourceDataFetcher
            self._fetcher = MultiSourceDataFetcher()
        return self._fetcher

    def get_stock_data(self, symbol, start_date=None, end_date=None, use_cache=True):
        """
        获取股票数据（支持缓存）
        """
        cache_file = self.cache_dir / f"{symbol}_{start_date}_{end_date}.parquet"

        # 尝试从缓存加载
        if use_cache and cache_file.exists():
            try:
                df = pd.read_parquet(cache_file)
                print(f"[Cache] Loaded {symbol} from cache")
                return df
            except Exception as e:
                print(f"[Cache] Failed to load: {e}")

        # 从网络获取
        df = self.fetcher.get_stock_data(symbol, start_date, end_date)

        # 保存到缓存
        if df is not None and use_cache:
            try:
                df.to_parquet(cache_file)
                print(f"[Cache] Saved {symbol} to cache")
            except Exception as e:
                print(f"[Cache] Failed to save: {e}")

        return df

    def get_realtime_price(self, symbol):
        """获取实时价格"""
        return self.fetcher.get_realtime_price(symbol)

    def clear_cache(self, symbol=None):
        """清除缓存"""
        if symbol:
            for f in self.cache_dir.glob(f"{symbol}_*.parquet"):
                f.unlink()
        else:
            for f in self.cache_dir.glob("*.parquet"):
                f.unlink()
        print("[Cache] Cleared")
