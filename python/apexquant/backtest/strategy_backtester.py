"""
独立策略回测器

支持对 MultiFactorStrategy / EventDrivenStrategy / PairsTrading / DeepLearningPredictor
直接在 DataFrame 上回测，无需完整 SimulationController 基础设施。
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class BacktestResult:
    """回测结果"""
    # 收益指标
    total_return: float = 0.0
    annualized_return: float = 0.0
    max_drawdown: float = 0.0
    sharpe_ratio: float = 0.0
    calmar_ratio: float = 0.0
    sortino_ratio: float = 0.0

    # 交易统计
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    profit_loss_ratio: float = 0.0
    avg_holding_days: float = 0.0

    # 资金曲线
    equity_curve: Optional[pd.DataFrame] = None  # [date, equity, drawdown]
    trades: List[Dict] = field(default_factory=list)
    daily_returns: Optional[pd.Series] = None

    # 元数据
    strategy_name: str = ""
    initial_capital: float = 0.0
    params: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            'total_return': self.total_return,
            'annualized_return': self.annualized_return,
            'max_drawdown': self.max_drawdown,
            'sharpe_ratio': self.sharpe_ratio,
            'calmar_ratio': self.calmar_ratio,
            'sortino_ratio': self.sortino_ratio,
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'win_rate': self.win_rate,
            'profit_loss_ratio': self.profit_loss_ratio,
            'avg_holding_days': self.avg_holding_days,
            'strategy_name': self.strategy_name,
            'initial_capital': self.initial_capital,
        }


class StrategyBacktester:
    """
    独立策略回测器

    支持多种信号生成模式的统一回测框架。
    """

    def __init__(self,
                 initial_capital: float = 1000000,
                 commission_rate: float = 0.0003,
                 stamp_tax_rate: float = 0.001,
                 slippage_rate: float = 0.001,
                 position_pct: float = 0.2,
                 risk_free_rate: float = 0.03):
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        self.stamp_tax_rate = stamp_tax_rate
        self.slippage_rate = slippage_rate
        self.position_pct = position_pct
        self.risk_free_rate = risk_free_rate

    def backtest_signal_series(self,
                               price_df: pd.DataFrame,
                               signals: pd.Series,
                               strategy_name: str = "Custom",
                               params: Dict = None) -> BacktestResult:
        """
        基于信号序列回测

        Args:
            price_df: 价格数据 (需含 date, close 列)
            signals: 信号序列 (1=买入, -1=卖出, 0=持有), index 与 price_df 对齐
            strategy_name: 策略名称
            params: 参数字典

        Returns:
            BacktestResult
        """
        if price_df is None or price_df.empty or signals is None:
            return BacktestResult(strategy_name=strategy_name, initial_capital=self.initial_capital)

        df = price_df.copy()
        if 'date' in df.columns:
            dates = df['date'].values
        else:
            dates = df.index.values

        closes = df['close'].values
        n = len(closes)

        # 模拟交易
        cash = self.initial_capital
        position = 0
        avg_cost = 0.0
        equity_list = []
        trades = []
        buy_date_idx = 0

        sig_vals = signals.values if hasattr(signals, 'values') else np.array(signals)
        if len(sig_vals) < n:
            sig_vals = np.pad(sig_vals, (0, n - len(sig_vals)), constant_values=0)

        for i in range(n):
            price = closes[i]
            sig = sig_vals[i] if i < len(sig_vals) else 0

            # 买入信号
            if sig > 0 and position == 0:
                buy_amount = cash * self.position_pct
                buy_price = price * (1 + self.slippage_rate)
                commission = buy_amount * self.commission_rate
                shares = int(buy_amount / buy_price / 100) * 100
                if shares >= 100:
                    cost = shares * buy_price + commission
                    cash -= cost
                    position = shares
                    avg_cost = buy_price
                    buy_date_idx = i

            # 卖出信号
            elif sig < 0 and position > 0:
                sell_price = price * (1 - self.slippage_rate)
                revenue = position * sell_price
                commission = revenue * self.commission_rate
                stamp_tax = revenue * self.stamp_tax_rate
                cash += revenue - commission - stamp_tax

                pnl = (sell_price - avg_cost) * position - commission - stamp_tax
                trades.append({
                    'buy_date': dates[buy_date_idx] if buy_date_idx < len(dates) else '',
                    'sell_date': dates[i],
                    'buy_price': avg_cost,
                    'sell_price': sell_price,
                    'volume': position,
                    'pnl': pnl,
                    'return_pct': (sell_price / avg_cost - 1) * 100,
                    'holding_days': i - buy_date_idx,
                })
                position = 0
                avg_cost = 0.0

            # 记录权益
            market_value = position * price
            equity = cash + market_value
            equity_list.append({
                'date': dates[i],
                'equity': equity,
                'cash': cash,
                'market_value': market_value,
            })

        return self._compute_result(equity_list, trades, strategy_name, params)

    def backtest_multi_factor(self,
                              price_df: pd.DataFrame,
                              fundamental: Optional[Dict] = None,
                              capital_flow: Optional[Dict] = None,
                              rebalance_freq: int = 20,
                              buy_threshold: float = 0.5,
                              sell_threshold: float = -0.5,
                              weights: Optional[Dict] = None,
                              strategy_name: str = "多因子策略") -> BacktestResult:
        """
        多因子策略回测

        Args:
            price_df: 价格数据
            fundamental: 基本面数据
            capital_flow: 资金流向数据
            rebalance_freq: 调仓频率(天)
            buy_threshold: 买入阈值
            sell_threshold: 卖出阈值
            weights: 因子权重
        """
        from apexquant.strategy import MultiFactorStrategy

        strategy = MultiFactorStrategy(weights=weights)

        closes = price_df['close'].values
        n = len(closes)
        signals = np.zeros(n)

        # 滚动窗口计算因子
        window_size = 60
        for i in range(window_size, n, rebalance_freq):
            window_df = price_df.iloc[max(0, i - window_size):i + 1].copy()
            factors = strategy.calculate_factors(window_df, fundamental, capital_flow)
            if factors:
                score = strategy.calculate_composite_score(factors)
                if score > buy_threshold:
                    signals[i] = 1
                elif score < sell_threshold:
                    signals[i] = -1

        return self.backtest_signal_series(
            price_df, pd.Series(signals, index=price_df.index if hasattr(price_df, 'index') else range(n)),
            strategy_name=strategy_name,
            params={
                'rebalance_freq': rebalance_freq,
                'buy_threshold': buy_threshold,
                'sell_threshold': sell_threshold,
                'weights': weights or {},
            }
        )

    def backtest_ma_cross(self,
                          price_df: pd.DataFrame,
                          ma_short: int = 5,
                          ma_long: int = 20,
                          strategy_name: str = "均线交叉") -> BacktestResult:
        """MA交叉策略回测"""
        closes = price_df['close']
        ma_s = closes.rolling(ma_short).mean()
        ma_l = closes.rolling(ma_long).mean()

        signals = pd.Series(0, index=price_df.index)

        # 金叉买入，死叉卖出
        for i in range(1, len(closes)):
            if ma_s.iloc[i] > ma_l.iloc[i] and ma_s.iloc[i-1] <= ma_l.iloc[i-1]:
                signals.iloc[i] = 1
            elif ma_s.iloc[i] < ma_l.iloc[i] and ma_s.iloc[i-1] >= ma_l.iloc[i-1]:
                signals.iloc[i] = -1

        return self.backtest_signal_series(
            price_df, signals,
            strategy_name=strategy_name,
            params={'ma_short': ma_short, 'ma_long': ma_long}
        )

    def backtest_rsi(self,
                     price_df: pd.DataFrame,
                     rsi_period: int = 14,
                     oversold: float = 30,
                     overbought: float = 70,
                     strategy_name: str = "RSI策略") -> BacktestResult:
        """RSI策略回测"""
        closes = price_df['close']
        delta = closes.diff()
        gain = delta.where(delta > 0, 0).rolling(rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(rsi_period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        signals = pd.Series(0, index=price_df.index)
        for i in range(rsi_period, len(closes)):
            if rsi.iloc[i] < oversold:
                signals.iloc[i] = 1
            elif rsi.iloc[i] > overbought:
                signals.iloc[i] = -1

        return self.backtest_signal_series(
            price_df, signals,
            strategy_name=strategy_name,
            params={'rsi_period': rsi_period, 'oversold': oversold, 'overbought': overbought}
        )

    def backtest_buy_hold(self,
                          price_df: pd.DataFrame,
                          strategy_name: str = "买入持有") -> BacktestResult:
        """买入持有策略回测"""
        signals = pd.Series(0, index=price_df.index)
        signals.iloc[0] = 1  # 首日买入
        return self.backtest_signal_series(
            price_df, signals,
            strategy_name=strategy_name,
            params={}
        )

    def backtest_dl_prediction(self,
                               price_df: pd.DataFrame,
                               model_type: str = 'lstm',
                               train_ratio: float = 0.6,
                               predict_days: int = 5,
                               threshold: float = 0.55,
                               strategy_name: str = "深度学习预测") -> BacktestResult:
        """
        深度学习预测策略回测

        使用前 train_ratio 数据训练，后面数据回测。
        """
        from apexquant.strategy import DeepLearningPredictor

        n = len(price_df)
        train_end = int(n * train_ratio)

        if train_end < 100:
            return BacktestResult(strategy_name=strategy_name, initial_capital=self.initial_capital)

        train_df = price_df.iloc[:train_end].copy()
        test_df = price_df.iloc[train_end:].copy()

        if len(test_df) < 20:
            return BacktestResult(strategy_name=strategy_name, initial_capital=self.initial_capital)

        predictor = DeepLearningPredictor(model_type=model_type, sequence_length=20)
        train_result = predictor.train(train_df, target_days=predict_days, epochs=30)

        if 'error' in train_result:
            return BacktestResult(strategy_name=strategy_name, initial_capital=self.initial_capital)

        # 滚动预测生成信号
        signals = pd.Series(0, index=test_df.index)
        seq_len = predictor.sequence_length + 30

        for i in range(0, len(test_df), predict_days):
            if i < seq_len:
                lookback = pd.concat([train_df.iloc[-(seq_len - i):], test_df.iloc[:i + 1]])
            else:
                lookback = test_df.iloc[max(0, i - seq_len):i + 1]

            if len(lookback) < seq_len:
                continue

            pred = predictor.predict(lookback)
            if pred.prediction == 'up' and pred.probability > threshold:
                signals.iloc[i] = 1
            elif pred.prediction == 'down' and pred.probability > threshold:
                signals.iloc[i] = -1

        return self.backtest_signal_series(
            test_df, signals,
            strategy_name=strategy_name,
            params={
                'model_type': model_type,
                'train_ratio': train_ratio,
                'predict_days': predict_days,
                'threshold': threshold,
                'train_accuracy': train_result.get('val_accuracy', 0),
            }
        )

    def run_parameter_optimization(self,
                                   strategy_func: Callable,
                                   param_grid: Dict[str, List],
                                   price_df: pd.DataFrame,
                                   objective: str = 'sharpe_ratio') -> Dict:
        """
        参数优化 (网格搜索)

        Args:
            strategy_func: 回测函数，签名 func(price_df, **params) -> BacktestResult
            param_grid: 参数网格 {'param': [v1, v2, ...]}
            price_df: 价格数据
            objective: 优化目标

        Returns:
            {'best_params': Dict, 'best_score': float, 'all_results': List}
        """
        from itertools import product

        param_names = list(param_grid.keys())
        param_values = list(param_grid.values())
        combinations = list(product(*param_values))

        results = []
        best_score = -np.inf
        best_params = None
        best_result = None

        for combo in combinations:
            params = dict(zip(param_names, combo))
            try:
                result = strategy_func(price_df, **params)
                score = getattr(result, objective, -np.inf)
                if isinstance(score, float) and np.isnan(score):
                    score = -np.inf

                results.append({
                    'params': params,
                    'score': score,
                    'result': result.to_dict(),
                })

                if score > best_score:
                    best_score = score
                    best_params = params
                    best_result = result

            except Exception as e:
                results.append({
                    'params': params,
                    'score': -np.inf,
                    'error': str(e),
                })

        return {
            'best_params': best_params,
            'best_score': best_score,
            'best_result': best_result,
            'all_results': results,
            'total_combinations': len(combinations),
        }

    def _compute_result(self, equity_list: List[Dict], trades: List[Dict],
                        strategy_name: str, params: Optional[Dict]) -> BacktestResult:
        """计算回测结果指标"""
        result = BacktestResult(
            strategy_name=strategy_name,
            initial_capital=self.initial_capital,
            params=params or {},
            trades=trades,
        )

        if not equity_list:
            return result

        equity_df = pd.DataFrame(equity_list)
        result.equity_curve = equity_df

        equity_vals = equity_df['equity'].values
        n = len(equity_vals)

        # 总收益
        result.total_return = (equity_vals[-1] / self.initial_capital - 1) * 100

        # 年化收益
        trading_days = n
        if trading_days > 0:
            years = trading_days / 252
            if years > 0:
                result.annualized_return = ((equity_vals[-1] / self.initial_capital) ** (1 / years) - 1) * 100

        # 最大回撤
        peak = np.maximum.accumulate(equity_vals)
        drawdown = (peak - equity_vals) / peak
        result.max_drawdown = np.max(drawdown) * 100

        # 添加回撤到equity_curve
        equity_df['drawdown'] = drawdown * 100

        # 日收益率
        daily_returns = np.diff(equity_vals) / equity_vals[:-1]
        result.daily_returns = pd.Series(daily_returns)

        # 夏普比率
        if len(daily_returns) > 1 and np.std(daily_returns) > 0:
            ann_mean = np.mean(daily_returns) * 252
            ann_std = np.std(daily_returns) * np.sqrt(252)
            result.sharpe_ratio = (ann_mean - self.risk_free_rate) / ann_std

        # Sortino比率
        neg_returns = daily_returns[daily_returns < 0]
        if len(neg_returns) > 0:
            downside_std = np.std(neg_returns) * np.sqrt(252)
            if downside_std > 0:
                ann_mean = np.mean(daily_returns) * 252
                result.sortino_ratio = (ann_mean - self.risk_free_rate) / downside_std

        # Calmar比率
        if result.max_drawdown > 0:
            result.calmar_ratio = result.annualized_return / result.max_drawdown

        # 交易统计
        result.total_trades = len(trades)
        result.winning_trades = sum(1 for t in trades if t.get('pnl', 0) > 0)
        result.losing_trades = sum(1 for t in trades if t.get('pnl', 0) < 0)
        if result.total_trades > 0:
            result.win_rate = result.winning_trades / result.total_trades * 100

        # 盈亏比
        avg_profit = np.mean([t['pnl'] for t in trades if t.get('pnl', 0) > 0]) if result.winning_trades > 0 else 0
        avg_loss = abs(np.mean([t['pnl'] for t in trades if t.get('pnl', 0) < 0])) if result.losing_trades > 0 else 0
        if avg_loss > 0:
            result.profit_loss_ratio = avg_profit / avg_loss

        # 平均持有天数
        holding_days = [t.get('holding_days', 0) for t in trades]
        if holding_days:
            result.avg_holding_days = np.mean(holding_days)

        return result
