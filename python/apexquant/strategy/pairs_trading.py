"""
统计套利策略 - 配对交易

基于协整关系的配对交易策略
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

# 尝试导入统计库
try:
    from scipy import stats
    from scipy.optimize import minimize
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    logger.warning("scipy not available")

try:
    import statsmodels.api as sm
    from statsmodels.tsa.stattools import coint, adfuller
    STATSMODELS_AVAILABLE = True
except ImportError:
    STATSMODELS_AVAILABLE = False
    logger.warning("statsmodels not available, using simplified cointegration test")


class PairStatus(Enum):
    """配对状态"""
    NEUTRAL = "neutral"         # 中性
    LONG_SPREAD = "long_spread"  # 做多价差
    SHORT_SPREAD = "short_spread"  # 做空价差


@dataclass
class PairInfo:
    """配对信息"""
    stock_a: str
    stock_b: str
    hedge_ratio: float  # 对冲比率
    correlation: float  # 相关性
    cointegration_pvalue: float  # 协整p值
    half_life: float  # 均值回归半衰期
    spread_mean: float  # 价差均值
    spread_std: float  # 价差标准差
    is_cointegrated: bool

    def to_dict(self) -> Dict:
        return {
            'stock_a': self.stock_a,
            'stock_b': self.stock_b,
            'hedge_ratio': self.hedge_ratio,
            'correlation': self.correlation,
            'cointegration_pvalue': self.cointegration_pvalue,
            'half_life': self.half_life,
            'spread_mean': self.spread_mean,
            'spread_std': self.spread_std,
            'is_cointegrated': self.is_cointegrated
        }


@dataclass
class PairSignal:
    """配对交易信号"""
    pair: PairInfo
    signal: str  # 'long_spread', 'short_spread', 'close', 'hold'
    z_score: float  # 当前Z分数
    current_spread: float  # 当前价差
    entry_threshold: float
    exit_threshold: float
    stop_loss_threshold: float
    position_a: float  # 股票A仓位 (+买入, -卖出)
    position_b: float  # 股票B仓位
    reason: str

    def to_dict(self) -> Dict:
        return {
            'pair': self.pair.to_dict(),
            'signal': self.signal,
            'z_score': self.z_score,
            'current_spread': self.current_spread,
            'position_a': self.position_a,
            'position_b': self.position_b,
            'reason': self.reason
        }


class PairsTrading:
    """配对交易策略"""

    def __init__(self,
                 entry_threshold: float = 2.0,
                 exit_threshold: float = 0.5,
                 stop_loss_threshold: float = 4.0,
                 lookback_period: int = 60,
                 min_correlation: float = 0.7,
                 max_pvalue: float = 0.05):
        """
        初始化配对交易策略

        Args:
            entry_threshold: 开仓Z分数阈值
            exit_threshold: 平仓Z分数阈值
            stop_loss_threshold: 止损Z分数阈值
            lookback_period: 回溯期（天）
            min_correlation: 最小相关性要求
            max_pvalue: 协整检验最大p值
        """
        self.entry_threshold = entry_threshold
        self.exit_threshold = exit_threshold
        self.stop_loss_threshold = stop_loss_threshold
        self.lookback_period = lookback_period
        self.min_correlation = min_correlation
        self.max_pvalue = max_pvalue

        self.pairs: Dict[str, PairInfo] = {}
        self.positions: Dict[str, PairStatus] = {}

    def find_cointegrated_pairs(self,
                               price_data: Dict[str, pd.Series],
                               min_samples: int = 100) -> List[PairInfo]:
        """
        寻找协整配对

        Args:
            price_data: {symbol: price_series}
            min_samples: 最小样本数

        Returns:
            协整配对列表
        """
        symbols = list(price_data.keys())
        n_symbols = len(symbols)
        pairs = []

        logger.info(f"Testing {n_symbols * (n_symbols - 1) // 2} potential pairs...")

        for i in range(n_symbols):
            for j in range(i + 1, n_symbols):
                stock_a = symbols[i]
                stock_b = symbols[j]

                price_a = price_data[stock_a]
                price_b = price_data[stock_b]

                # 对齐数据
                common_idx = price_a.index.intersection(price_b.index)
                if len(common_idx) < min_samples:
                    continue

                price_a = price_a.loc[common_idx]
                price_b = price_b.loc[common_idx]

                # 检验相关性
                correlation = price_a.corr(price_b)
                if abs(correlation) < self.min_correlation:
                    continue

                # 协整检验
                pair_info = self._test_cointegration(
                    stock_a, stock_b, price_a, price_b
                )

                if pair_info.is_cointegrated:
                    pairs.append(pair_info)
                    logger.info(f"Found cointegrated pair: {stock_a}-{stock_b}, "
                               f"p-value={pair_info.cointegration_pvalue:.4f}")

        # 按协整p值排序
        pairs.sort(key=lambda x: x.cointegration_pvalue)

        return pairs

    def _test_cointegration(self, stock_a: str, stock_b: str,
                           price_a: pd.Series, price_b: pd.Series) -> PairInfo:
        """
        协整检验

        Args:
            stock_a, stock_b: 股票代码
            price_a, price_b: 价格序列

        Returns:
            PairInfo
        """
        # 计算相关性
        correlation = price_a.corr(price_b)

        if STATSMODELS_AVAILABLE:
            # 使用statsmodels进行协整检验
            try:
                coint_result = coint(price_a, price_b)
                p_value = coint_result[1]
            except Exception as e:
                logger.debug(f"Cointegration test failed: {e}")
                p_value = 1.0

            # 计算对冲比率（OLS回归）
            try:
                X = sm.add_constant(price_b)
                model = sm.OLS(price_a, X).fit()
                hedge_ratio = model.params.iloc[1] if len(model.params) > 1 else 1.0
            except:
                hedge_ratio = price_a.mean() / price_b.mean()
        else:
            # 简化检验
            p_value, hedge_ratio = self._simplified_cointegration_test(price_a, price_b)

        # 计算价差
        spread = price_a - hedge_ratio * price_b
        spread_mean = spread.mean()
        spread_std = spread.std()

        # 计算半衰期（均值回归速度）
        half_life = self._calculate_half_life(spread)

        is_cointegrated = (p_value < self.max_pvalue and
                          half_life > 0 and half_life < self.lookback_period)

        return PairInfo(
            stock_a=stock_a,
            stock_b=stock_b,
            hedge_ratio=hedge_ratio,
            correlation=correlation,
            cointegration_pvalue=p_value,
            half_life=half_life,
            spread_mean=spread_mean,
            spread_std=spread_std,
            is_cointegrated=is_cointegrated
        )

    def _simplified_cointegration_test(self, price_a: pd.Series,
                                       price_b: pd.Series) -> Tuple[float, float]:
        """
        简化的协整检验（无statsmodels时使用）

        Returns:
            (p_value, hedge_ratio)
        """
        # 简单回归
        hedge_ratio = np.cov(price_a, price_b)[0, 1] / np.var(price_b)

        # 计算残差
        spread = price_a - hedge_ratio * price_b

        # ADF检验的简化版本
        # 检查残差是否均值回归
        spread_diff = spread.diff().dropna()
        spread_lag = spread.shift(1).dropna()

        # 对齐
        common_idx = spread_diff.index.intersection(spread_lag.index)
        spread_diff = spread_diff.loc[common_idx]
        spread_lag = spread_lag.loc[common_idx]

        if len(spread_diff) < 20:
            return 1.0, hedge_ratio

        # 简单回归: spread_diff = alpha + beta * spread_lag
        # beta < 0 表示均值回归
        try:
            cov = np.cov(spread_diff, spread_lag)
            beta = cov[0, 1] / cov[1, 1] if cov[1, 1] > 0 else 0

            # 简单t统计量
            residuals = spread_diff - beta * spread_lag
            se = np.sqrt(np.var(residuals) / (np.var(spread_lag) * len(spread_lag)))
            t_stat = beta / se if se > 0 else 0

            # 近似p值（ADF临界值约-2.86 at 5%）
            if t_stat < -2.86:
                p_value = 0.05
            elif t_stat < -2.57:
                p_value = 0.10
            else:
                p_value = 0.5
        except:
            p_value = 1.0

        return p_value, hedge_ratio

    def _calculate_half_life(self, spread: pd.Series) -> float:
        """
        计算均值回归半衰期

        Args:
            spread: 价差序列

        Returns:
            半衰期（天）
        """
        spread_lag = spread.shift(1)
        spread_diff = spread - spread_lag

        # 对齐
        spread_lag = spread_lag.dropna()
        spread_diff = spread_diff.loc[spread_lag.index]

        if len(spread_lag) < 10:
            return -1

        # 回归: spread_diff = alpha + beta * spread_lag
        try:
            cov = np.cov(spread_diff, spread_lag)
            beta = cov[0, 1] / cov[1, 1] if cov[1, 1] > 0 else 0

            if beta >= 0:
                return -1  # 不是均值回归

            half_life = -np.log(2) / beta
            return max(0, half_life)
        except:
            return -1

    def calculate_z_score(self, pair: PairInfo,
                         current_price_a: float,
                         current_price_b: float) -> float:
        """
        计算当前Z分数

        Args:
            pair: 配对信息
            current_price_a: 股票A当前价格
            current_price_b: 股票B当前价格

        Returns:
            Z分数
        """
        current_spread = current_price_a - pair.hedge_ratio * current_price_b
        z_score = (current_spread - pair.spread_mean) / pair.spread_std if pair.spread_std > 0 else 0
        return z_score

    def generate_signal(self, pair: PairInfo,
                       current_price_a: float,
                       current_price_b: float,
                       current_position: PairStatus = PairStatus.NEUTRAL) -> PairSignal:
        """
        生成交易信号

        Args:
            pair: 配对信息
            current_price_a: 股票A当前价格
            current_price_b: 股票B当前价格
            current_position: 当前持仓状态

        Returns:
            配对交易信号
        """
        z_score = self.calculate_z_score(pair, current_price_a, current_price_b)
        current_spread = current_price_a - pair.hedge_ratio * current_price_b

        signal = 'hold'
        position_a = 0
        position_b = 0
        reason = ""

        # 无持仓时的开仓逻辑
        if current_position == PairStatus.NEUTRAL:
            if z_score > self.entry_threshold:
                # 价差过高，做空价差
                # 卖A买B
                signal = 'short_spread'
                position_a = -1
                position_b = pair.hedge_ratio
                reason = f"Z-score={z_score:.2f}超过{self.entry_threshold}，做空价差"
            elif z_score < -self.entry_threshold:
                # 价差过低，做多价差
                # 买A卖B
                signal = 'long_spread'
                position_a = 1
                position_b = -pair.hedge_ratio
                reason = f"Z-score={z_score:.2f}低于-{self.entry_threshold}，做多价差"
            else:
                signal = 'hold'
                reason = f"Z-score={z_score:.2f}在阈值内，观望"

        # 有持仓时的平仓逻辑
        elif current_position == PairStatus.LONG_SPREAD:
            if abs(z_score) < self.exit_threshold:
                signal = 'close'
                reason = f"Z-score回归至{z_score:.2f}，平仓获利"
            elif z_score < -self.stop_loss_threshold:
                signal = 'close'
                reason = f"Z-score={z_score:.2f}触及止损"
            else:
                signal = 'hold'
                position_a = 1
                position_b = -pair.hedge_ratio
                reason = f"继续持有做多价差，Z-score={z_score:.2f}"

        elif current_position == PairStatus.SHORT_SPREAD:
            if abs(z_score) < self.exit_threshold:
                signal = 'close'
                reason = f"Z-score回归至{z_score:.2f}，平仓获利"
            elif z_score > self.stop_loss_threshold:
                signal = 'close'
                reason = f"Z-score={z_score:.2f}触及止损"
            else:
                signal = 'hold'
                position_a = -1
                position_b = pair.hedge_ratio
                reason = f"继续持有做空价差，Z-score={z_score:.2f}"

        return PairSignal(
            pair=pair,
            signal=signal,
            z_score=z_score,
            current_spread=current_spread,
            entry_threshold=self.entry_threshold,
            exit_threshold=self.exit_threshold,
            stop_loss_threshold=self.stop_loss_threshold,
            position_a=position_a,
            position_b=position_b,
            reason=reason
        )

    def backtest_pair(self, pair: PairInfo,
                     price_a: pd.Series,
                     price_b: pd.Series,
                     initial_capital: float = 100000) -> Dict:
        """
        回测配对交易

        Args:
            pair: 配对信息
            price_a: 股票A价格序列
            price_b: 股票B价格序列
            initial_capital: 初始资金

        Returns:
            回测结果
        """
        # 对齐数据
        common_idx = price_a.index.intersection(price_b.index)
        price_a = price_a.loc[common_idx]
        price_b = price_b.loc[common_idx]

        # 计算价差和Z分数
        spread = price_a - pair.hedge_ratio * price_b
        z_scores = (spread - spread.rolling(self.lookback_period).mean()) / \
                   spread.rolling(self.lookback_period).std()
        z_scores = z_scores.fillna(0)

        # 模拟交易
        position = PairStatus.NEUTRAL
        trades = []
        equity = [initial_capital]
        entry_price_a = 0
        entry_price_b = 0

        for i in range(self.lookback_period, len(price_a)):
            z = z_scores.iloc[i]
            pa = price_a.iloc[i]
            pb = price_b.iloc[i]

            if position == PairStatus.NEUTRAL:
                if z > self.entry_threshold:
                    position = PairStatus.SHORT_SPREAD
                    entry_price_a = pa
                    entry_price_b = pb
                    trades.append({
                        'date': price_a.index[i],
                        'action': 'open_short_spread',
                        'z_score': z
                    })
                elif z < -self.entry_threshold:
                    position = PairStatus.LONG_SPREAD
                    entry_price_a = pa
                    entry_price_b = pb
                    trades.append({
                        'date': price_a.index[i],
                        'action': 'open_long_spread',
                        'z_score': z
                    })

            elif position == PairStatus.LONG_SPREAD:
                pnl_a = (pa - entry_price_a) / entry_price_a
                pnl_b = -(pb - entry_price_b) / entry_price_b * pair.hedge_ratio

                if abs(z) < self.exit_threshold or z < -self.stop_loss_threshold:
                    position = PairStatus.NEUTRAL
                    total_pnl = (pnl_a + pnl_b) / 2 * equity[-1]
                    equity.append(equity[-1] + total_pnl)
                    trades.append({
                        'date': price_a.index[i],
                        'action': 'close',
                        'z_score': z,
                        'pnl': total_pnl
                    })
                else:
                    equity.append(equity[-1])

            elif position == PairStatus.SHORT_SPREAD:
                pnl_a = -(pa - entry_price_a) / entry_price_a
                pnl_b = (pb - entry_price_b) / entry_price_b * pair.hedge_ratio

                if abs(z) < self.exit_threshold or z > self.stop_loss_threshold:
                    position = PairStatus.NEUTRAL
                    total_pnl = (pnl_a + pnl_b) / 2 * equity[-1]
                    equity.append(equity[-1] + total_pnl)
                    trades.append({
                        'date': price_a.index[i],
                        'action': 'close',
                        'z_score': z,
                        'pnl': total_pnl
                    })
                else:
                    equity.append(equity[-1])

            else:
                equity.append(equity[-1])

        equity = pd.Series(equity, index=price_a.index[self.lookback_period-1:])

        # 计算统计
        returns = equity.pct_change().dropna()
        total_return = (equity.iloc[-1] / initial_capital - 1) * 100
        sharpe = returns.mean() / returns.std() * np.sqrt(252) if returns.std() > 0 else 0
        max_drawdown = ((equity.cummax() - equity) / equity.cummax()).max() * 100

        winning_trades = len([t for t in trades if t.get('pnl', 0) > 0])
        total_trades = len([t for t in trades if 'pnl' in t])
        win_rate = winning_trades / total_trades * 100 if total_trades > 0 else 0

        return {
            'total_return': total_return,
            'sharpe_ratio': sharpe,
            'max_drawdown': max_drawdown,
            'total_trades': total_trades,
            'win_rate': win_rate,
            'equity_curve': equity,
            'trades': trades
        }


# 便捷函数
def find_pairs(price_data: Dict[str, pd.Series],
               min_correlation: float = 0.7,
               max_pvalue: float = 0.05) -> List[PairInfo]:
    """
    寻找协整配对

    Args:
        price_data: {symbol: price_series}
        min_correlation: 最小相关性
        max_pvalue: 最大p值

    Returns:
        配对列表
    """
    strategy = PairsTrading(min_correlation=min_correlation, max_pvalue=max_pvalue)
    return strategy.find_cointegrated_pairs(price_data)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("=" * 60)
    print("配对交易策略测试")
    print("=" * 60)

    print(f"scipy available: {SCIPY_AVAILABLE}")
    print(f"statsmodels available: {STATSMODELS_AVAILABLE}")

    # 创建模拟数据（两只相关股票）
    np.random.seed(42)
    n_samples = 252

    dates = pd.date_range('2025-01-01', periods=n_samples, freq='D')

    # 创建协整的价格序列
    common_factor = np.cumsum(np.random.randn(n_samples) * 0.5)

    price_a = 100 + common_factor + np.random.randn(n_samples) * 2
    price_b = 50 + 0.5 * common_factor + np.random.randn(n_samples) * 1

    # 非协整的股票
    price_c = 80 + np.cumsum(np.random.randn(n_samples) * 1)

    price_data = {
        'STOCK_A': pd.Series(price_a, index=dates),
        'STOCK_B': pd.Series(price_b, index=dates),
        'STOCK_C': pd.Series(price_c, index=dates)
    }

    # 测试配对发现
    strategy = PairsTrading(entry_threshold=2.0, exit_threshold=0.5)

    print("\n寻找协整配对...")
    pairs = strategy.find_cointegrated_pairs(price_data)

    print(f"\n找到 {len(pairs)} 个协整配对:")
    for pair in pairs:
        print(f"  {pair.stock_a} - {pair.stock_b}")
        print(f"    相关性: {pair.correlation:.3f}")
        print(f"    协整p值: {pair.cointegration_pvalue:.4f}")
        print(f"    对冲比率: {pair.hedge_ratio:.3f}")
        print(f"    半衰期: {pair.half_life:.1f}天")

    if pairs:
        # 测试信号生成
        pair = pairs[0]
        signal = strategy.generate_signal(
            pair,
            current_price_a=price_data[pair.stock_a].iloc[-1],
            current_price_b=price_data[pair.stock_b].iloc[-1]
        )

        print(f"\n当前信号:")
        print(f"  Z-score: {signal.z_score:.2f}")
        print(f"  信号: {signal.signal}")
        print(f"  原因: {signal.reason}")

        # 回测
        print("\n回测配对策略...")
        result = strategy.backtest_pair(
            pair,
            price_data[pair.stock_a],
            price_data[pair.stock_b]
        )

        print(f"\n回测结果:")
        print(f"  总收益: {result['total_return']:.2f}%")
        print(f"  夏普比率: {result['sharpe_ratio']:.2f}")
        print(f"  最大回撤: {result['max_drawdown']:.2f}%")
        print(f"  交易次数: {result['total_trades']}")
        print(f"  胜率: {result['win_rate']:.1f}%")

    print("\n" + "=" * 60)
