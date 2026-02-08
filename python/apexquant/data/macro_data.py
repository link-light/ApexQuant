"""
宏观经济数据模块

提供宏观经济指标获取功能：
- GDP、CPI、PPI等经济指标
- 利率、汇率数据
- 货币供应量
- PMI指数
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum


class MacroIndicatorType(Enum):
    """宏观指标类型"""
    GDP = "GDP"
    CPI = "CPI"
    PPI = "PPI"
    PMI = "PMI"
    INTEREST_RATE = "利率"
    EXCHANGE_RATE = "汇率"
    MONEY_SUPPLY = "货币供应量"
    UNEMPLOYMENT = "失业率"
    RETAIL_SALES = "社会消费品零售总额"
    FIXED_INVESTMENT = "固定资产投资"


@dataclass
class MacroIndicator:
    """宏观指标数据"""
    indicator_type: MacroIndicatorType
    value: float
    date: datetime
    unit: str
    yoy_change: Optional[float] = None  # 同比变化
    mom_change: Optional[float] = None  # 环比变化
    source: str = "akshare"


@dataclass
class MacroDataset:
    """宏观数据集"""
    indicators: Dict[str, MacroIndicator]
    update_time: datetime
    description: str


class MacroDataFetcher:
    """宏观经济数据获取器"""

    def __init__(self):
        """初始化"""
        self._check_dependencies()

    def _check_dependencies(self):
        """检查依赖"""
        try:
            import akshare as ak
            self.ak = ak
            self.has_akshare = True
        except ImportError:
            self.has_akshare = False

    def get_gdp_data(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        获取GDP数据

        Args:
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)

        Returns:
            pd.DataFrame: GDP数据
        """
        if not self.has_akshare:
            return self._generate_mock_gdp_data()

        try:
            # 使用akshare获取GDP数据
            df = self.ak.macro_china_gdp()

            if df is not None and not df.empty:
                # 数据清洗
                df = self._clean_macro_data(df, start_date, end_date)
                return df
        except Exception as e:
            print(f"获取GDP数据失败: {e}")

        return self._generate_mock_gdp_data()

    def get_cpi_data(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        获取CPI数据

        Args:
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            pd.DataFrame: CPI数据
        """
        if not self.has_akshare:
            return self._generate_mock_cpi_data()

        try:
            # 使用akshare获取CPI数据
            df = self.ak.macro_china_cpi()

            if df is not None and not df.empty:
                df = self._clean_macro_data(df, start_date, end_date)
                return df
        except Exception as e:
            print(f"获取CPI数据失败: {e}")

        return self._generate_mock_cpi_data()

    def get_ppi_data(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        获取PPI数据

        Args:
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            pd.DataFrame: PPI数据
        """
        if not self.has_akshare:
            return self._generate_mock_ppi_data()

        try:
            # 使用akshare获取PPI数据
            df = self.ak.macro_china_ppi()

            if df is not None and not df.empty:
                df = self._clean_macro_data(df, start_date, end_date)
                return df
        except Exception as e:
            print(f"获取PPI数据失败: {e}")

        return self._generate_mock_ppi_data()

    def get_pmi_data(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        获取PMI数据

        Args:
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            pd.DataFrame: PMI数据
        """
        if not self.has_akshare:
            return self._generate_mock_pmi_data()

        try:
            # 使用akshare获取PMI数据
            df = self.ak.macro_china_pmi()

            if df is not None and not df.empty:
                df = self._clean_macro_data(df, start_date, end_date)
                return df
        except Exception as e:
            print(f"获取PMI数据失败: {e}")

        return self._generate_mock_pmi_data()

    def get_interest_rate_data(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        获取利率数据

        Args:
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            pd.DataFrame: 利率数据
        """
        if not self.has_akshare:
            return self._generate_mock_interest_rate_data()

        try:
            # 使用akshare获取利率数据
            df = self.ak.macro_china_lpr()

            if df is not None and not df.empty:
                df = self._clean_macro_data(df, start_date, end_date)
                return df
        except Exception as e:
            print(f"获取利率数据失败: {e}")

        return self._generate_mock_interest_rate_data()

    def get_exchange_rate_data(
        self,
        currency_pair: str = "USDCNY",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        获取汇率数据

        Args:
            currency_pair: 货币对 (如 USDCNY)
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            pd.DataFrame: 汇率数据
        """
        if not self.has_akshare:
            return self._generate_mock_exchange_rate_data()

        try:
            # 使用akshare获取汇率数据
            df = self.ak.fx_spot_quote(symbol=currency_pair)

            if df is not None and not df.empty:
                df = self._clean_macro_data(df, start_date, end_date)
                return df
        except Exception as e:
            print(f"获取汇率数据失败: {e}")

        return self._generate_mock_exchange_rate_data()

    def get_money_supply_data(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        获取货币供应量数据

        Args:
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            pd.DataFrame: 货币供应量数据
        """
        if not self.has_akshare:
            return self._generate_mock_money_supply_data()

        try:
            # 使用akshare获取货币供应量数据
            df = self.ak.macro_china_money_supply()

            if df is not None and not df.empty:
                df = self._clean_macro_data(df, start_date, end_date)
                return df
        except Exception as e:
            print(f"获取货币供应量数据失败: {e}")

        return self._generate_mock_money_supply_data()

    def get_comprehensive_macro_data(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> MacroDataset:
        """
        获取综合宏观数据

        Args:
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            MacroDataset: 宏观数据集
        """
        indicators = {}

        # 获取各类指标的最新数据
        try:
            gdp_df = self.get_gdp_data(start_date, end_date)
            if not gdp_df.empty:
                latest_gdp = gdp_df.iloc[-1]
                indicators['GDP'] = MacroIndicator(
                    indicator_type=MacroIndicatorType.GDP,
                    value=float(latest_gdp.get('value', latest_gdp.iloc[1])),
                    date=pd.to_datetime(latest_gdp.iloc[0]),
                    unit="亿元",
                    yoy_change=float(latest_gdp.get('yoy', 0)) if 'yoy' in latest_gdp else None
                )
        except Exception as e:
            print(f"处理GDP数据失败: {e}")

        try:
            cpi_df = self.get_cpi_data(start_date, end_date)
            if not cpi_df.empty:
                latest_cpi = cpi_df.iloc[-1]
                indicators['CPI'] = MacroIndicator(
                    indicator_type=MacroIndicatorType.CPI,
                    value=float(latest_cpi.get('value', latest_cpi.iloc[1])),
                    date=pd.to_datetime(latest_cpi.iloc[0]),
                    unit="同比%",
                    yoy_change=float(latest_cpi.get('yoy', 0)) if 'yoy' in latest_cpi else None
                )
        except Exception as e:
            print(f"处理CPI数据失败: {e}")

        try:
            pmi_df = self.get_pmi_data(start_date, end_date)
            if not pmi_df.empty:
                latest_pmi = pmi_df.iloc[-1]
                indicators['PMI'] = MacroIndicator(
                    indicator_type=MacroIndicatorType.PMI,
                    value=float(latest_pmi.get('value', latest_pmi.iloc[1])),
                    date=pd.to_datetime(latest_pmi.iloc[0]),
                    unit="指数"
                )
        except Exception as e:
            print(f"处理PMI数据失败: {e}")

        return MacroDataset(
            indicators=indicators,
            update_time=datetime.now(),
            description="综合宏观经济数据"
        )

    def _clean_macro_data(
        self,
        df: pd.DataFrame,
        start_date: Optional[str],
        end_date: Optional[str]
    ) -> pd.DataFrame:
        """清洗宏观数据"""
        if df is None or df.empty:
            return df

        # 日期过滤
        if start_date or end_date:
            date_col = df.columns[0]  # 假设第一列是日期
            df[date_col] = pd.to_datetime(df[date_col])

            if start_date:
                df = df[df[date_col] >= start_date]
            if end_date:
                df = df[df[date_col] <= end_date]

        return df

    # ============================================================
    # 模拟数据生成 (用于演示和测试)
    # ============================================================

    def _generate_mock_gdp_data(self) -> pd.DataFrame:
        """生成模拟GDP数据"""
        dates = pd.date_range(end=datetime.now(), periods=20, freq='Q')
        base_gdp = 250000  # 基础GDP (亿元)

        data = []
        for i, date in enumerate(dates):
            gdp = base_gdp * (1 + 0.06) ** (i / 4)  # 年增长6%
            yoy = 6.0 + np.random.randn() * 0.5
            data.append({
                'date': date,
                'value': gdp,
                'yoy': yoy
            })

        return pd.DataFrame(data)

    def _generate_mock_cpi_data(self) -> pd.DataFrame:
        """生成模拟CPI数据"""
        dates = pd.date_range(end=datetime.now(), periods=36, freq='M')

        data = []
        for date in dates:
            cpi = 102.0 + np.random.randn() * 0.5  # 同比2%左右
            data.append({
                'date': date,
                'value': cpi,
                'yoy': cpi - 100
            })

        return pd.DataFrame(data)

    def _generate_mock_ppi_data(self) -> pd.DataFrame:
        """生成模拟PPI数据"""
        dates = pd.date_range(end=datetime.now(), periods=36, freq='M')

        data = []
        for date in dates:
            ppi = 101.5 + np.random.randn() * 1.0  # 同比1.5%左右
            data.append({
                'date': date,
                'value': ppi,
                'yoy': ppi - 100
            })

        return pd.DataFrame(data)

    def _generate_mock_pmi_data(self) -> pd.DataFrame:
        """生成模拟PMI数据"""
        dates = pd.date_range(end=datetime.now(), periods=36, freq='M')

        data = []
        for date in dates:
            pmi = 50.5 + np.random.randn() * 1.0  # 50左右
            data.append({
                'date': date,
                'value': pmi
            })

        return pd.DataFrame(data)

    def _generate_mock_interest_rate_data(self) -> pd.DataFrame:
        """生成模拟利率数据"""
        dates = pd.date_range(end=datetime.now(), periods=24, freq='M')

        data = []
        for date in dates:
            lpr_1y = 3.65 + np.random.randn() * 0.05
            lpr_5y = 4.30 + np.random.randn() * 0.05
            data.append({
                'date': date,
                'lpr_1y': lpr_1y,
                'lpr_5y': lpr_5y
            })

        return pd.DataFrame(data)

    def _generate_mock_exchange_rate_data(self) -> pd.DataFrame:
        """生成模拟汇率数据"""
        dates = pd.date_range(end=datetime.now(), periods=252, freq='D')

        data = []
        base_rate = 7.0
        for i, date in enumerate(dates):
            rate = base_rate + np.sin(i / 50) * 0.2 + np.random.randn() * 0.01
            data.append({
                'date': date,
                'rate': rate
            })

        return pd.DataFrame(data)

    def _generate_mock_money_supply_data(self) -> pd.DataFrame:
        """生成模拟货币供应量数据"""
        dates = pd.date_range(end=datetime.now(), periods=36, freq='M')

        data = []
        base_m2 = 2000000  # 基础M2 (亿元)
        for i, date in enumerate(dates):
            m2 = base_m2 * (1 + 0.08) ** (i / 12)  # 年增长8%
            m2_yoy = 8.0 + np.random.randn() * 0.5
            data.append({
                'date': date,
                'm2': m2,
                'm2_yoy': m2_yoy
            })

        return pd.DataFrame(data)


def get_macro_indicators(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> MacroDataset:
    """
    便捷函数：获取宏观经济指标

    Args:
        start_date: 开始日期
        end_date: 结束日期

    Returns:
        MacroDataset: 宏观数据集
    """
    fetcher = MacroDataFetcher()
    return fetcher.get_comprehensive_macro_data(start_date, end_date)
