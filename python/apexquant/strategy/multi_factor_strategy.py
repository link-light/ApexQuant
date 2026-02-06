"""
多因子选股策略

包含市值、动量、价值、质量等因子的合成策略
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class FactorType(Enum):
    """因子类型"""
    SIZE = "size"           # 市值因子
    MOMENTUM = "momentum"   # 动量因子
    VALUE = "value"         # 价值因子
    QUALITY = "quality"     # 质量因子
    VOLATILITY = "volatility"  # 波动因子
    LIQUIDITY = "liquidity"    # 流动性因子
    GROWTH = "growth"          # 成长因子
    TECHNICAL = "technical"    # 技术因子


@dataclass
class FactorValue:
    """单个因子值"""
    name: str
    factor_type: FactorType
    raw_value: float
    z_score: float = 0.0
    percentile: float = 50.0
    weight: float = 1.0

    @property
    def weighted_score(self) -> float:
        return self.z_score * self.weight


@dataclass
class StockScore:
    """股票综合评分"""
    symbol: str
    factors: Dict[str, FactorValue] = field(default_factory=dict)
    total_score: float = 0.0
    rank: int = 0
    signal: str = "hold"  # buy, sell, hold

    def add_factor(self, factor: FactorValue):
        self.factors[factor.name] = factor
        self._calculate_total()

    def _calculate_total(self):
        if self.factors:
            self.total_score = sum(f.weighted_score for f in self.factors.values())

    def to_dict(self) -> Dict:
        return {
            'symbol': self.symbol,
            'total_score': self.total_score,
            'rank': self.rank,
            'signal': self.signal,
            'factors': {k: {
                'raw': v.raw_value,
                'z_score': v.z_score,
                'weight': v.weight,
                'weighted': v.weighted_score
            } for k, v in self.factors.items()}
        }


class MultiFactorStrategy:
    """多因子选股策略"""

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        """
        初始化多因子策略

        Args:
            weights: 因子权重字典，如 {'momentum': 0.3, 'value': 0.3, ...}
        """
        self.weights = weights or {
            'size': 0.1,
            'momentum': 0.25,
            'value': 0.25,
            'quality': 0.2,
            'volatility': 0.1,
            'growth': 0.1
        }
        self._factor_data = {}

    def calculate_factors(self,
                         price_data: pd.DataFrame,
                         fundamental_data: Optional[Dict] = None,
                         capital_flow: Optional[Dict] = None) -> Dict[str, float]:
        """
        计算单只股票的所有因子

        Args:
            price_data: 价格数据 DataFrame (需包含 date, open, high, low, close, volume)
            fundamental_data: 基本面数据字典 (pe, pb, roe, etc.)
            capital_flow: 资金流向数据

        Returns:
            因子值字典
        """
        factors = {}

        if price_data is None or len(price_data) < 20:
            return factors

        # 确保数据按日期排序
        df = price_data.sort_values('date' if 'date' in price_data.columns else price_data.index.name or 'index')
        closes = df['close'].values
        volumes = df['volume'].values if 'volume' in df.columns else np.ones(len(df))
        highs = df['high'].values if 'high' in df.columns else closes
        lows = df['low'].values if 'low' in df.columns else closes

        # 1. 动量因子
        factors.update(self._calc_momentum_factors(closes))

        # 2. 波动因子
        factors.update(self._calc_volatility_factors(closes, highs, lows))

        # 3. 流动性因子
        factors.update(self._calc_liquidity_factors(closes, volumes))

        # 4. 技术因子
        factors.update(self._calc_technical_factors(closes, highs, lows, volumes))

        # 5. 价值因子 (需要基本面数据)
        if fundamental_data:
            factors.update(self._calc_value_factors(fundamental_data))

        # 6. 质量因子 (需要基本面数据)
        if fundamental_data:
            factors.update(self._calc_quality_factors(fundamental_data))

        # 7. 成长因子 (需要基本面数据)
        if fundamental_data:
            factors.update(self._calc_growth_factors(fundamental_data))

        # 8. 资金因子 (需要资金流向数据)
        if capital_flow:
            factors.update(self._calc_capital_factors(capital_flow))

        return factors

    def _calc_momentum_factors(self, closes: np.ndarray) -> Dict[str, float]:
        """计算动量因子"""
        factors = {}
        n = len(closes)

        # 短期动量 (5日收益率)
        if n >= 5:
            factors['momentum_5d'] = (closes[-1] / closes[-5] - 1) * 100

        # 中期动量 (20日收益率)
        if n >= 20:
            factors['momentum_20d'] = (closes[-1] / closes[-20] - 1) * 100

        # 长期动量 (60日收益率)
        if n >= 60:
            factors['momentum_60d'] = (closes[-1] / closes[-60] - 1) * 100

        # 动量加速度 (短期动量 - 长期动量)
        if 'momentum_5d' in factors and 'momentum_20d' in factors:
            factors['momentum_acceleration'] = factors['momentum_5d'] - factors['momentum_20d']

        # 动量反转因子 (过去涨幅越大，越可能回调)
        if n >= 20:
            max_close = np.max(closes[-20:])
            factors['reversal_20d'] = (max_close - closes[-1]) / max_close * 100

        return factors

    def _calc_volatility_factors(self, closes: np.ndarray,
                                  highs: np.ndarray, lows: np.ndarray) -> Dict[str, float]:
        """计算波动因子"""
        factors = {}
        n = len(closes)

        if n < 20:
            return factors

        # 日收益率
        returns = np.diff(closes) / closes[:-1]

        # 波动率 (20日)
        factors['volatility_20d'] = np.std(returns[-20:]) * np.sqrt(252) * 100

        # ATR (平均真实波幅)
        tr = np.maximum(
            highs[-20:] - lows[-20:],
            np.maximum(
                np.abs(highs[-20:] - np.roll(closes, 1)[-20:]),
                np.abs(lows[-20:] - np.roll(closes, 1)[-20:])
            )
        )
        factors['atr_20d'] = np.mean(tr[1:]) / closes[-1] * 100

        # 波动率变化
        if n >= 40:
            vol_recent = np.std(returns[-10:])
            vol_past = np.std(returns[-40:-20])
            factors['volatility_change'] = (vol_recent / vol_past - 1) * 100 if vol_past > 0 else 0

        # 下行波动率
        neg_returns = returns[returns < 0]
        if len(neg_returns) > 5:
            factors['downside_volatility'] = np.std(neg_returns) * np.sqrt(252) * 100

        return factors

    def _calc_liquidity_factors(self, closes: np.ndarray, volumes: np.ndarray) -> Dict[str, float]:
        """计算流动性因子"""
        factors = {}
        n = len(closes)

        if n < 20:
            return factors

        # 平均成交量
        avg_volume_20d = np.mean(volumes[-20:])

        # 换手率变化 (用成交量代理)
        if n >= 40:
            recent_volume = np.mean(volumes[-5:])
            past_volume = np.mean(volumes[-40:-20])
            factors['volume_change'] = (recent_volume / past_volume - 1) * 100 if past_volume > 0 else 0

        # 量价相关性 (正相关说明有资金推动)
        if n >= 21:
            returns = np.diff(closes[-21:]) / closes[-21:-1]
            vol_changes = np.diff(volumes[-21:]) / (volumes[-21:-1] + 1e-10)
            # 防止除零和无效值
            vol_changes = np.where(np.isinf(vol_changes) | np.isnan(vol_changes), 0, vol_changes)
            returns = np.where(np.isinf(returns) | np.isnan(returns), 0, returns)
            if len(returns) > 0 and len(vol_changes) > 0:
                try:
                    corr = np.corrcoef(returns, vol_changes)[0, 1]
                    factors['price_volume_corr'] = corr * 100 if not np.isnan(corr) else 0
                except:
                    factors['price_volume_corr'] = 0

        # Amihud 非流动性因子
        if n >= 21:
            amounts = closes[-20:] * volumes[-20:]
            returns_abs = np.abs(np.diff(closes[-21:]) / (closes[-21:-1] + 1e-10))
            returns_abs = returns_abs[-19:]  # 对齐长度
            amounts_slice = amounts[1:]
            if len(returns_abs) == len(amounts_slice) and np.sum(amounts_slice) > 0:
                factors['amihud_illiquidity'] = np.mean(returns_abs / (amounts_slice + 1e-10)) * 1e9

        return factors

    def _calc_technical_factors(self, closes: np.ndarray, highs: np.ndarray,
                                 lows: np.ndarray, volumes: np.ndarray) -> Dict[str, float]:
        """计算技术因子"""
        factors = {}
        n = len(closes)

        if n < 20:
            return factors

        # RSI
        returns = np.diff(closes)
        gains = np.where(returns > 0, returns, 0)
        losses = np.where(returns < 0, -returns, 0)

        if n >= 14:
            avg_gain = np.mean(gains[-14:])
            avg_loss = np.mean(losses[-14:])
            if avg_loss > 0:
                rs = avg_gain / avg_loss
                factors['rsi_14'] = 100 - (100 / (1 + rs))
            else:
                factors['rsi_14'] = 100

        # 布林带位置
        if n >= 20:
            ma20 = np.mean(closes[-20:])
            std20 = np.std(closes[-20:])
            if std20 > 0:
                factors['bollinger_position'] = (closes[-1] - ma20) / (2 * std20)

        # 均线偏离度
        if n >= 5:
            ma5 = np.mean(closes[-5:])
            factors['ma5_deviation'] = (closes[-1] / ma5 - 1) * 100

        if n >= 20:
            ma20 = np.mean(closes[-20:])
            factors['ma20_deviation'] = (closes[-1] / ma20 - 1) * 100

        # 均线趋势 (短期均线 vs 长期均线)
        if n >= 60:
            ma5 = np.mean(closes[-5:])
            ma20 = np.mean(closes[-20:])
            ma60 = np.mean(closes[-60:])
            factors['ma_trend'] = ((ma5 > ma20) + (ma20 > ma60)) - 1  # -1, 0, 1

        # 创新高/新低
        if n >= 60:
            high_60d = np.max(highs[-60:])
            low_60d = np.min(lows[-60:])
            factors['near_high_60d'] = (closes[-1] / high_60d) * 100
            factors['near_low_60d'] = (closes[-1] / low_60d - 1) * 100

        # OBV 趋势
        if n >= 20:
            obv = [0]
            for i in range(1, len(closes)):
                if closes[i] > closes[i-1]:
                    obv.append(obv[-1] + volumes[i])
                elif closes[i] < closes[i-1]:
                    obv.append(obv[-1] - volumes[i])
                else:
                    obv.append(obv[-1])

            obv = np.array(obv)
            obv_ma5 = np.mean(obv[-5:])
            obv_ma20 = np.mean(obv[-20:])
            if obv_ma20 != 0:
                factors['obv_trend'] = (obv_ma5 / obv_ma20 - 1) * 100

        return factors

    def _calc_value_factors(self, fundamental: Dict) -> Dict[str, float]:
        """计算价值因子"""
        factors = {}

        # PE (市盈率) - 越低越好，取负值
        pe = fundamental.get('pe_ttm', 0)
        if pe > 0:
            factors['pe_inverse'] = -np.log(pe) if pe > 1 else -pe

        # PB (市净率) - 越低越好，取负值
        pb = fundamental.get('pb', 0)
        if pb > 0:
            factors['pb_inverse'] = -np.log(pb) if pb > 1 else -pb

        # PS (市销率) - 越低越好
        ps = fundamental.get('ps_ttm', 0)
        if ps > 0:
            factors['ps_inverse'] = -np.log(ps) if ps > 1 else -ps

        # 股息率 - 越高越好
        div_yield = fundamental.get('dividend_yield', 0)
        factors['dividend_yield'] = div_yield

        # EP (盈利收益率) = 1/PE
        if pe > 0:
            factors['earnings_yield'] = 100 / pe

        return factors

    def _calc_quality_factors(self, fundamental: Dict) -> Dict[str, float]:
        """计算质量因子"""
        factors = {}

        # ROE (净资产收益率)
        roe = fundamental.get('roe', 0)
        factors['roe'] = roe

        # ROA (总资产收益率)
        roa = fundamental.get('roa', 0)
        factors['roa'] = roa

        # 毛利率
        gross_margin = fundamental.get('gross_margin', 0)
        factors['gross_margin'] = gross_margin

        # 净利率
        net_margin = fundamental.get('net_margin', 0)
        factors['net_margin'] = net_margin

        # 资产负债率 - 越低越好，取负值
        debt_ratio = fundamental.get('debt_ratio', 50)
        factors['debt_ratio_inverse'] = -debt_ratio

        # 流动比率
        current_ratio = fundamental.get('current_ratio', 1)
        factors['current_ratio'] = min(current_ratio, 5)  # 截断极值

        return factors

    def _calc_growth_factors(self, fundamental: Dict) -> Dict[str, float]:
        """计算成长因子"""
        factors = {}

        # 营收增长率
        revenue_growth = fundamental.get('revenue_growth', 0)
        factors['revenue_growth'] = np.clip(revenue_growth, -100, 200)

        # 净利润增长率
        profit_growth = fundamental.get('profit_growth', 0)
        factors['profit_growth'] = np.clip(profit_growth, -100, 300)

        # ROE变化
        roe_growth = fundamental.get('roe_growth', 0)
        factors['roe_growth'] = np.clip(roe_growth, -50, 50)

        return factors

    def _calc_capital_factors(self, capital_flow: Dict) -> Dict[str, float]:
        """计算资金因子"""
        factors = {}

        # 主力净流入
        main_net = capital_flow.get('main_net_inflow', 0)
        factors['main_money_flow'] = main_net

        # 超大单净流入
        super_large = capital_flow.get('super_large_net', 0)
        factors['super_large_flow'] = super_large

        # 主力净流入占比
        main_ratio = capital_flow.get('main_net_ratio', 0)
        factors['main_flow_ratio'] = main_ratio

        return factors

    def normalize_factors(self, factor_matrix: pd.DataFrame) -> pd.DataFrame:
        """
        对因子进行标准化 (Z-Score)

        Args:
            factor_matrix: 因子矩阵 (index=symbol, columns=factors)

        Returns:
            标准化后的因子矩阵
        """
        normalized = factor_matrix.copy()

        for col in normalized.columns:
            values = normalized[col]
            mean = values.mean()
            std = values.std()

            if std > 0:
                normalized[col] = (values - mean) / std
            else:
                normalized[col] = 0

            # 去极值 (MAD法)
            median = normalized[col].median()
            mad = np.abs(normalized[col] - median).median()
            if mad > 0:
                normalized[col] = normalized[col].clip(
                    lower=median - 3 * 1.4826 * mad,
                    upper=median + 3 * 1.4826 * mad
                )

        return normalized

    def calculate_composite_score(self,
                                  factors: Dict[str, float],
                                  factor_weights: Optional[Dict[str, float]] = None) -> float:
        """
        计算综合得分

        Args:
            factors: 因子值字典
            factor_weights: 因子权重 (可选，使用默认权重)

        Returns:
            综合得分
        """
        weights = factor_weights or self._get_default_factor_weights()

        total_score = 0.0
        total_weight = 0.0

        for factor_name, value in factors.items():
            if factor_name in weights and not np.isnan(value):
                weight = weights[factor_name]
                total_score += value * weight
                total_weight += abs(weight)

        return total_score / total_weight if total_weight > 0 else 0.0

    def _get_default_factor_weights(self) -> Dict[str, float]:
        """获取默认因子权重"""
        return {
            # 动量因子
            'momentum_5d': 0.05,
            'momentum_20d': 0.10,
            'momentum_60d': 0.05,
            'momentum_acceleration': 0.05,
            'reversal_20d': -0.03,  # 反转因子权重为负

            # 波动因子
            'volatility_20d': -0.05,  # 低波动更好
            'atr_20d': -0.03,

            # 技术因子
            'rsi_14': 0.03,  # RSI接近中性更好
            'bollinger_position': -0.02,
            'ma5_deviation': 0.02,
            'ma20_deviation': 0.03,
            'ma_trend': 0.05,
            'obv_trend': 0.05,

            # 价值因子
            'pe_inverse': 0.08,
            'pb_inverse': 0.06,
            'dividend_yield': 0.05,
            'earnings_yield': 0.06,

            # 质量因子
            'roe': 0.10,
            'roa': 0.05,
            'gross_margin': 0.04,
            'net_margin': 0.04,
            'debt_ratio_inverse': 0.03,

            # 成长因子
            'revenue_growth': 0.08,
            'profit_growth': 0.08,

            # 资金因子
            'main_money_flow': 0.06,
            'main_flow_ratio': 0.04,
        }

    def rank_stocks(self,
                   stocks_data: Dict[str, Dict],
                   top_n: int = 10) -> List[StockScore]:
        """
        对股票池进行排名

        Args:
            stocks_data: {symbol: {'price_data': df, 'fundamental': dict, 'capital_flow': dict}}
            top_n: 返回前N只股票

        Returns:
            排序后的StockScore列表
        """
        scores = []

        # 计算所有股票的因子
        all_factors = {}
        for symbol, data in stocks_data.items():
            factors = self.calculate_factors(
                price_data=data.get('price_data'),
                fundamental_data=data.get('fundamental'),
                capital_flow=data.get('capital_flow')
            )
            all_factors[symbol] = factors

        # 转换为DataFrame进行标准化
        factor_df = pd.DataFrame(all_factors).T
        factor_df = factor_df.fillna(0)

        if len(factor_df) > 1:
            normalized_df = self.normalize_factors(factor_df)
        else:
            normalized_df = factor_df

        # 计算综合得分
        for symbol in stocks_data.keys():
            if symbol in normalized_df.index:
                factors_dict = normalized_df.loc[symbol].to_dict()
                score = self.calculate_composite_score(factors_dict)

                stock_score = StockScore(symbol=symbol, total_score=score)

                # 添加原始因子值
                raw_factors = all_factors.get(symbol, {})
                for name, raw_value in raw_factors.items():
                    z_score = normalized_df.loc[symbol, name] if name in normalized_df.columns else 0
                    factor = FactorValue(
                        name=name,
                        factor_type=self._get_factor_type(name),
                        raw_value=raw_value,
                        z_score=z_score,
                        weight=self._get_default_factor_weights().get(name, 0)
                    )
                    stock_score.add_factor(factor)

                scores.append(stock_score)

        # 排序
        scores.sort(key=lambda x: x.total_score, reverse=True)

        # 分配排名和信号
        for i, score in enumerate(scores):
            score.rank = i + 1
            if i < len(scores) * 0.2:  # 前20%
                score.signal = 'buy'
            elif i > len(scores) * 0.8:  # 后20%
                score.signal = 'sell'
            else:
                score.signal = 'hold'

        return scores[:top_n] if top_n else scores

    def _get_factor_type(self, factor_name: str) -> FactorType:
        """根据因子名获取因子类型"""
        if 'momentum' in factor_name or 'reversal' in factor_name:
            return FactorType.MOMENTUM
        elif 'volatility' in factor_name or 'atr' in factor_name:
            return FactorType.VOLATILITY
        elif 'volume' in factor_name or 'liquidity' in factor_name or 'amihud' in factor_name:
            return FactorType.LIQUIDITY
        elif 'pe' in factor_name or 'pb' in factor_name or 'dividend' in factor_name or 'earnings' in factor_name:
            return FactorType.VALUE
        elif 'roe' in factor_name or 'roa' in factor_name or 'margin' in factor_name or 'debt' in factor_name:
            return FactorType.QUALITY
        elif 'growth' in factor_name:
            return FactorType.GROWTH
        else:
            return FactorType.TECHNICAL

    def generate_signals(self, stock_scores: List[StockScore],
                        current_positions: Optional[Dict[str, float]] = None) -> Dict[str, Dict]:
        """
        生成交易信号

        Args:
            stock_scores: 股票评分列表
            current_positions: 当前持仓 {symbol: weight}

        Returns:
            交易信号字典 {symbol: {'action': 'buy/sell/hold', 'weight': float, 'reason': str}}
        """
        signals = {}
        current_positions = current_positions or {}

        for score in stock_scores:
            symbol = score.symbol
            current_weight = current_positions.get(symbol, 0)

            if score.signal == 'buy':
                if current_weight == 0:
                    target_weight = min(0.1, 1.0 / max(len(stock_scores), 10))  # 等权或最大10%
                    signals[symbol] = {
                        'action': 'buy',
                        'weight': target_weight,
                        'score': score.total_score,
                        'rank': score.rank,
                        'reason': f'多因子得分排名第{score.rank}位'
                    }
                elif current_weight < 0.1:  # 加仓
                    signals[symbol] = {
                        'action': 'add',
                        'weight': 0.1 - current_weight,
                        'score': score.total_score,
                        'rank': score.rank,
                        'reason': f'得分较高，建议加仓'
                    }

            elif score.signal == 'sell':
                if current_weight > 0:
                    signals[symbol] = {
                        'action': 'sell',
                        'weight': -current_weight,
                        'score': score.total_score,
                        'rank': score.rank,
                        'reason': f'多因子得分排名靠后(第{score.rank}位)'
                    }

        return signals


# 便捷函数
def calculate_stock_score(symbol: str,
                         price_data: pd.DataFrame,
                         fundamental_data: Optional[Dict] = None,
                         capital_flow: Optional[Dict] = None) -> StockScore:
    """计算单只股票的多因子得分"""
    strategy = MultiFactorStrategy()
    factors = strategy.calculate_factors(price_data, fundamental_data, capital_flow)

    score = StockScore(symbol=symbol, total_score=strategy.calculate_composite_score(factors))

    for name, value in factors.items():
        factor = FactorValue(
            name=name,
            factor_type=strategy._get_factor_type(name),
            raw_value=value
        )
        score.add_factor(factor)

    return score


if __name__ == "__main__":
    # 测试代码
    import logging
    logging.basicConfig(level=logging.INFO)

    # 创建模拟数据
    np.random.seed(42)
    dates = pd.date_range('2025-01-01', periods=100, freq='D')
    price_data = pd.DataFrame({
        'date': dates,
        'open': 100 + np.cumsum(np.random.randn(100) * 2),
        'high': 102 + np.cumsum(np.random.randn(100) * 2),
        'low': 98 + np.cumsum(np.random.randn(100) * 2),
        'close': 100 + np.cumsum(np.random.randn(100) * 2),
        'volume': np.random.randint(1000000, 5000000, 100)
    })

    fundamental = {
        'pe_ttm': 25.5,
        'pb': 3.2,
        'roe': 18.5,
        'gross_margin': 45.2,
        'revenue_growth': 15.3,
        'profit_growth': 22.1
    }

    capital_flow = {
        'main_net_inflow': 5.5,
        'main_net_ratio': 12.3
    }

    # 测试单股票评分
    print("=" * 60)
    print("多因子策略测试")
    print("=" * 60)

    strategy = MultiFactorStrategy()
    factors = strategy.calculate_factors(price_data, fundamental, capital_flow)

    print(f"\n计算了 {len(factors)} 个因子:")
    for name, value in factors.items():
        print(f"  {name}: {value:.4f}")

    score = strategy.calculate_composite_score(factors)
    print(f"\n综合得分: {score:.4f}")

    print("\n" + "=" * 60)
