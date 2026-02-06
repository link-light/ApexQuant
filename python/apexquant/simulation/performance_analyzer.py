"""
ApexQuant Performance Analyzer
绩效分析器
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """绩效指标"""
    # 基础指标
    total_return: float = 0.0         # 总收益率
    annualized_return: float = 0.0    # 年化收益率
    max_drawdown: float = 0.0         # 最大回撤
    sharpe_ratio: float = 0.0         # 夏普比率
    calmar_ratio: float = 0.0         # 卡玛比率
    
    # 胜率指标
    win_rate: float = 0.0             # 胜率
    profit_loss_ratio: float = 0.0    # 盈亏比
    
    # 交易统计
    total_trades: int = 0             # 总交易次数
    winning_trades: int = 0           # 盈利交易次数
    losing_trades: int = 0            # 亏损交易次数
    
    # 收益统计
    total_profit: float = 0.0         # 总盈利
    total_loss: float = 0.0           # 总亏损
    avg_profit: float = 0.0           # 平均盈利
    avg_loss: float = 0.0             # 平均亏损
    
    # 时间统计
    trading_days: int = 0             # 交易天数
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "total_return": f"{self.total_return:.2%}",
            "annualized_return": f"{self.annualized_return:.2%}",
            "max_drawdown": f"{self.max_drawdown:.2%}",
            "sharpe_ratio": f"{self.sharpe_ratio:.4f}",
            "calmar_ratio": f"{self.calmar_ratio:.4f}",
            "win_rate": f"{self.win_rate:.2%}",
            "profit_loss_ratio": f"{self.profit_loss_ratio:.2f}",
            "total_trades": self.total_trades,
            "winning_trades": self.winning_trades,
            "losing_trades": self.losing_trades,
            "total_profit": f"{self.total_profit:.2f}",
            "total_loss": f"{self.total_loss:.2f}",
            "avg_profit": f"{self.avg_profit:.2f}",
            "avg_loss": f"{self.avg_loss:.2f}",
            "trading_days": self.trading_days,
        }


class PerformanceAnalyzer:
    """绩效分析器"""
    
    def __init__(self, initial_capital: float, risk_free_rate: float = 0.03):
        """
        初始化绩效分析器
        
        Args:
            initial_capital: 初始资金
            risk_free_rate: 无风险利率（年化），默认3%
        """
        self.initial_capital = initial_capital
        self.risk_free_rate = risk_free_rate
        
        logger.info(f"Performance analyzer initialized with capital={initial_capital}")
    
    def analyze(
        self,
        equity_curve: pd.DataFrame,
        trades: List[dict]
    ) -> PerformanceMetrics:
        """
        分析绩效
        
        Args:
            equity_curve: 权益曲线 DataFrame，列: [date, equity]
            trades: 交易记录列表，每个dict包含: {pnl, side, ...}
            
        Returns:
            绩效指标
        """
        metrics = PerformanceMetrics()
        
        if equity_curve is None or equity_curve.empty:
            logger.warning("Empty equity curve, returning zero metrics")
            return metrics
        
        try:
            # 基础收益指标
            metrics = self._calculate_return_metrics(equity_curve, metrics)
            
            # 风险指标
            metrics = self._calculate_risk_metrics(equity_curve, metrics)
            
            # 交易统计
            metrics = self._calculate_trade_metrics(trades, metrics)
            
            logger.info("Performance analysis completed")
            
        except Exception as e:
            logger.error(f"Failed to analyze performance: {e}")
        
        return metrics
    
    def _calculate_return_metrics(
        self,
        equity_curve: pd.DataFrame,
        metrics: PerformanceMetrics
    ) -> PerformanceMetrics:
        """计算收益指标"""
        
        if len(equity_curve) == 0:
            return metrics
        
        # 确保有equity列
        if 'equity' not in equity_curve.columns:
            logger.error("equity column not found in equity_curve")
            return metrics
        
        final_equity = equity_curve['equity'].iloc[-1]
        
        # 总收益率
        metrics.total_return = (final_equity - self.initial_capital) / self.initial_capital
        
        # 交易天数
        metrics.trading_days = len(equity_curve)
        
        # 年化收益率 (假设一年252个交易日)
        if metrics.trading_days > 0:
            years = metrics.trading_days / 252.0
            if years > 0:
                metrics.annualized_return = (
                    (1 + metrics.total_return) ** (1 / years) - 1
                )
        
        return metrics
    
    def _calculate_risk_metrics(
        self,
        equity_curve: pd.DataFrame,
        metrics: PerformanceMetrics
    ) -> PerformanceMetrics:
        """计算风险指标"""
        
        if len(equity_curve) < 2:
            return metrics
        
        equity_values = equity_curve['equity'].values
        
        # 最大回撤
        metrics.max_drawdown = self._calculate_max_drawdown(equity_values)
        
        # 日收益率
        returns = np.diff(equity_values) / equity_values[:-1]
        
        if len(returns) > 0:
            # 夏普比率 (年化)
            mean_return = np.mean(returns)
            std_return = np.std(returns)
            
            if std_return > 0:
                # 将日收益率年化
                annualized_mean = mean_return * 252
                annualized_std = std_return * np.sqrt(252)
                daily_rf_rate = self.risk_free_rate / 252
                
                metrics.sharpe_ratio = (
                    (annualized_mean - self.risk_free_rate) / annualized_std
                )
            
            # 卡玛比率 (年化收益率 / 最大回撤)
            if metrics.max_drawdown > 0:
                metrics.calmar_ratio = (
                    metrics.annualized_return / metrics.max_drawdown
                )
        
        return metrics
    
    def _calculate_max_drawdown(self, equity_values: np.ndarray) -> float:
        """
        计算最大回撤
        
        Args:
            equity_values: 权益值数组
            
        Returns:
            最大回撤（正数）
        """
        if len(equity_values) == 0:
            return 0.0
        
        # 计算累计最大值
        cummax = np.maximum.accumulate(equity_values)
        
        # 计算回撤
        drawdowns = (cummax - equity_values) / cummax
        
        # 最大回撤
        max_dd = np.max(drawdowns)
        
        return max_dd
    
    def _calculate_trade_metrics(
        self,
        trades: List[dict],
        metrics: PerformanceMetrics
    ) -> PerformanceMetrics:
        """计算交易统计指标"""
        
        if not trades:
            return metrics
        
        metrics.total_trades = len(trades)
        
        profits = []
        losses = []
        
        for trade in trades:
            pnl = trade.get('pnl', 0) or trade.get('realized_pnl', 0)
            
            if pnl > 0:
                profits.append(pnl)
                metrics.winning_trades += 1
            elif pnl < 0:
                losses.append(abs(pnl))
                metrics.losing_trades += 1
        
        # 盈亏统计
        metrics.total_profit = sum(profits) if profits else 0.0
        metrics.total_loss = sum(losses) if losses else 0.0
        
        # 平均盈亏
        metrics.avg_profit = metrics.total_profit / len(profits) if profits else 0.0
        metrics.avg_loss = metrics.total_loss / len(losses) if losses else 0.0
        
        # 胜率
        if metrics.total_trades > 0:
            metrics.win_rate = metrics.winning_trades / metrics.total_trades
        
        # 盈亏比
        if metrics.avg_loss > 0:
            metrics.profit_loss_ratio = metrics.avg_profit / metrics.avg_loss
        
        return metrics
    
    def generate_report(self, metrics: PerformanceMetrics) -> str:
        """
        生成绩效报告
        
        Args:
            metrics: 绩效指标
            
        Returns:
            报告文本
        """
        report = []
        report.append("=" * 60)
        report.append("Performance Analysis Report")
        report.append("=" * 60)
        report.append("")
        
        # 收益指标
        report.append("Return Metrics:")
        report.append(f"  Total Return:        {metrics.total_return:>12.2%}")
        report.append(f"  Annualized Return:   {metrics.annualized_return:>12.2%}")
        report.append("")
        
        # 风险指标
        report.append("Risk Metrics:")
        report.append(f"  Max Drawdown:        {metrics.max_drawdown:>12.2%}")
        report.append(f"  Sharpe Ratio:        {metrics.sharpe_ratio:>12.4f}")
        report.append(f"  Calmar Ratio:        {metrics.calmar_ratio:>12.4f}")
        report.append("")
        
        # 交易统计
        report.append("Trade Statistics:")
        report.append(f"  Total Trades:        {metrics.total_trades:>12}")
        report.append(f"  Winning Trades:      {metrics.winning_trades:>12}")
        report.append(f"  Losing Trades:       {metrics.losing_trades:>12}")
        report.append(f"  Win Rate:            {metrics.win_rate:>12.2%}")
        report.append(f"  Profit/Loss Ratio:   {metrics.profit_loss_ratio:>12.2f}")
        report.append("")
        
        # 盈亏统计
        report.append("Profit/Loss Statistics:")
        report.append(f"  Total Profit:        {metrics.total_profit:>12.2f}")
        report.append(f"  Total Loss:          {metrics.total_loss:>12.2f}")
        report.append(f"  Average Profit:      {metrics.avg_profit:>12.2f}")
        report.append(f"  Average Loss:        {metrics.avg_loss:>12.2f}")
        report.append("")
        
        # 时间统计
        report.append("Time Statistics:")
        report.append(f"  Trading Days:        {metrics.trading_days:>12}")
        report.append("")
        
        report.append("=" * 60)
        
        return "\n".join(report)
    
    def plot_equity_curve(self, equity_curve: pd.DataFrame, save_path: Optional[str] = None):
        """
        绘制权益曲线
        
        Args:
            equity_curve: 权益曲线 DataFrame
            save_path: 保存路径（可选）
        """
        try:
            import matplotlib.pyplot as plt
            import matplotlib.dates as mdates
            
            if equity_curve is None or equity_curve.empty:
                logger.warning("Empty equity curve, cannot plot")
                return
            
            fig, ax = plt.subplots(figsize=(12, 6))
            
            # 绘制权益曲线
            if 'date' in equity_curve.columns:
                ax.plot(equity_curve['date'], equity_curve['equity'], label='Equity', linewidth=2)
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
                plt.xticks(rotation=45)
            else:
                ax.plot(equity_curve['equity'], label='Equity', linewidth=2)
            
            # 绘制初始资金线
            ax.axhline(y=self.initial_capital, color='r', linestyle='--', 
                      label=f'Initial Capital: {self.initial_capital:.2f}', alpha=0.7)
            
            ax.set_xlabel('Date/Time')
            ax.set_ylabel('Equity')
            ax.set_title('Equity Curve')
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            if save_path:
                plt.savefig(save_path, dpi=150)
                logger.info(f"Equity curve saved to {save_path}")
            else:
                plt.show()
                
        except ImportError:
            logger.warning("matplotlib not available, cannot plot equity curve")
        except Exception as e:
            logger.error(f"Failed to plot equity curve: {e}")
    
    def plot_drawdown(self, equity_curve: pd.DataFrame, save_path: Optional[str] = None):
        """
        绘制回撤分析图
        
        Args:
            equity_curve: 权益曲线 DataFrame
            save_path: 保存路径（可选）
        """
        try:
            import matplotlib.pyplot as plt
            import matplotlib.dates as mdates
            
            if equity_curve is None or equity_curve.empty:
                logger.warning("Empty equity curve, cannot plot drawdown")
                return
            
            # 计算回撤
            equity = equity_curve['equity'].values
            peak = np.maximum.accumulate(equity)
            drawdown = (equity - peak) / peak
            
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
            
            # 上图：权益曲线和峰值
            if 'date' in equity_curve.columns:
                dates = equity_curve['date']
                ax1.plot(dates, equity, label='Equity', linewidth=2)
                ax1.plot(dates, peak, label='Peak', linestyle='--', alpha=0.7)
                ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            else:
                ax1.plot(equity, label='Equity', linewidth=2)
                ax1.plot(peak, label='Peak', linestyle='--', alpha=0.7)
            
            ax1.set_ylabel('Equity')
            ax1.set_title('Equity and Peak')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # 下图：回撤
            if 'date' in equity_curve.columns:
                ax2.fill_between(dates, drawdown, 0, alpha=0.3, color='red')
                ax2.plot(dates, drawdown, color='red', linewidth=1)
            else:
                ax2.fill_between(range(len(drawdown)), drawdown, 0, alpha=0.3, color='red')
                ax2.plot(drawdown, color='red', linewidth=1)
            
            ax2.set_xlabel('Date/Time')
            ax2.set_ylabel('Drawdown')
            ax2.set_title('Drawdown Analysis')
            ax2.grid(True, alpha=0.3)
            ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'{y:.1%}'))
            
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            if save_path:
                plt.savefig(save_path, dpi=150)
                logger.info(f"Drawdown chart saved to {save_path}")
            else:
                plt.show()
                
        except ImportError:
            logger.warning("matplotlib not available, cannot plot drawdown")
        except Exception as e:
            logger.error(f"Failed to plot drawdown: {e}")
    
    def plot_trade_analysis(self, trades: List[Dict], save_path: Optional[str] = None):
        """
        绘制交易分析图
        
        Args:
            trades: 交易记录列表
            save_path: 保存路径（可选）
        """
        try:
            import matplotlib.pyplot as plt
            
            if not trades:
                logger.warning("No trades to plot")
                return
            
            # 准备数据
            profits = []
            dates = []
            cumulative_profit = []
            cum_sum = 0
            
            for trade in trades:
                profit = trade.get('profit', 0)
                profits.append(profit)
                dates.append(trade.get('sell_date', ''))
                cum_sum += profit
                cumulative_profit.append(cum_sum)
            
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 10))
            
            # 1. 单笔盈亏分布
            colors = ['green' if p > 0 else 'red' for p in profits]
            ax1.bar(range(len(profits)), profits, color=colors, alpha=0.6)
            ax1.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
            ax1.set_xlabel('Trade Number')
            ax1.set_ylabel('Profit/Loss')
            ax1.set_title('Individual Trade P&L')
            ax1.grid(True, alpha=0.3)
            
            # 2. 累计盈亏曲线
            ax2.plot(cumulative_profit, linewidth=2, color='blue')
            ax2.axhline(y=0, color='black', linestyle='--', linewidth=0.5)
            ax2.set_xlabel('Trade Number')
            ax2.set_ylabel('Cumulative Profit/Loss')
            ax2.set_title('Cumulative P&L')
            ax2.grid(True, alpha=0.3)
            
            # 3. 盈亏分布直方图
            ax3.hist(profits, bins=20, alpha=0.7, color='blue', edgecolor='black')
            ax3.axvline(x=0, color='red', linestyle='--', linewidth=2)
            ax3.set_xlabel('Profit/Loss')
            ax3.set_ylabel('Frequency')
            ax3.set_title('P&L Distribution')
            ax3.grid(True, alpha=0.3)
            
            # 4. 盈亏统计饼图
            winning_trades = sum(1 for p in profits if p > 0)
            losing_trades = sum(1 for p in profits if p < 0)
            breakeven_trades = sum(1 for p in profits if p == 0)
            
            labels = []
            sizes = []
            colors_pie = []
            
            if winning_trades > 0:
                labels.append(f'Winning ({winning_trades})')
                sizes.append(winning_trades)
                colors_pie.append('green')
            if losing_trades > 0:
                labels.append(f'Losing ({losing_trades})')
                sizes.append(losing_trades)
                colors_pie.append('red')
            if breakeven_trades > 0:
                labels.append(f'Breakeven ({breakeven_trades})')
                sizes.append(breakeven_trades)
                colors_pie.append('gray')
            
            if sizes:
                ax4.pie(sizes, labels=labels, colors=colors_pie, autopct='%1.1f%%', startangle=90)
                ax4.set_title('Trade Outcome Distribution')
            
            plt.tight_layout()
            
            if save_path:
                plt.savefig(save_path, dpi=150)
                logger.info(f"Trade analysis chart saved to {save_path}")
            else:
                plt.show()
                
        except ImportError:
            logger.warning("matplotlib not available, cannot plot trade analysis")
        except Exception as e:
            logger.error(f"Failed to plot trade analysis: {e}")
    
    def plot_monthly_returns(self, equity_curve: pd.DataFrame, save_path: Optional[str] = None):
        """
        绘制月度收益热力图
        
        Args:
            equity_curve: 权益曲线 DataFrame
            save_path: 保存路径（可选）
        """
        try:
            import matplotlib.pyplot as plt
            
            if equity_curve is None or equity_curve.empty or 'date' not in equity_curve.columns:
                logger.warning("Invalid equity curve for monthly returns")
                return
            
            # 转换为datetime
            df = equity_curve.copy()
            df['date'] = pd.to_datetime(df['date'])
            df = df.set_index('date')
            
            # 计算日收益率
            df['returns'] = df['equity'].pct_change()
            
            # 按月汇总
            monthly_returns = df['returns'].resample('M').apply(lambda x: (1 + x).prod() - 1)
            
            if monthly_returns.empty:
                logger.warning("No monthly returns to plot")
                return
            
            # 创建年月矩阵
            monthly_returns_df = monthly_returns.to_frame()
            monthly_returns_df['year'] = monthly_returns_df.index.year
            monthly_returns_df['month'] = monthly_returns_df.index.month
            
            pivot_table = monthly_returns_df.pivot_table(
                values='returns',
                index='year',
                columns='month',
                aggfunc='first'
            )
            
            # 绘制热力图
            fig, ax = plt.subplots(figsize=(12, max(4, len(pivot_table) * 0.5)))
            
            im = ax.imshow(pivot_table.values, cmap='RdYlGn', aspect='auto', vmin=-0.1, vmax=0.1)
            
            # 设置刻度
            ax.set_xticks(range(12))
            ax.set_xticklabels(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                               'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])
            ax.set_yticks(range(len(pivot_table)))
            ax.set_yticklabels(pivot_table.index)
            
            # 添加数值标签
            for i in range(len(pivot_table)):
                for j in range(12):
                    value = pivot_table.iloc[i, j]
                    if not np.isnan(value):
                        text = ax.text(j, i, f'{value:.1%}',
                                     ha="center", va="center", color="black", fontsize=8)
            
            ax.set_title('Monthly Returns Heatmap')
            ax.set_xlabel('Month')
            ax.set_ylabel('Year')
            
            # 添加颜色条
            cbar = plt.colorbar(im, ax=ax)
            cbar.set_label('Returns', rotation=270, labelpad=15)
            
            plt.tight_layout()
            
            if save_path:
                plt.savefig(save_path, dpi=150)
                logger.info(f"Monthly returns chart saved to {save_path}")
            else:
                plt.show()
                
        except ImportError:
            logger.warning("matplotlib not available, cannot plot monthly returns")
        except Exception as e:
            logger.error(f"Failed to plot monthly returns: {e}")
    
    def generate_all_charts(self, output_dir: str = "reports"):
        """
        生成所有图表
        
        Args:
            output_dir: 输出目录
        """
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        logger.info("Generating all performance charts...")
        
        # 加载数据
        equity_curve = self.load_equity_curve()
        trades = self.load_trades()
        
        # 生成各类图表
        if equity_curve is not None and not equity_curve.empty:
            self.plot_equity_curve(equity_curve, os.path.join(output_dir, "equity_curve.png"))
            self.plot_drawdown(equity_curve, os.path.join(output_dir, "drawdown.png"))
            self.plot_monthly_returns(equity_curve, os.path.join(output_dir, "monthly_returns.png"))
        
        if trades:
            self.plot_trade_analysis(trades, os.path.join(output_dir, "trade_analysis.png"))
        
        logger.info(f"All charts saved to {output_dir}")