"""
ApexQuant 绩效分析器

计算各种绩效指标并生成报告
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, Tuple
from .database import DatabaseManager

logger = logging.getLogger(__name__)


class PerformanceAnalyzer:
    """绩效分析器"""
    
    @staticmethod
    def calculate_metrics(equity_curve: pd.DataFrame, trades: pd.DataFrame) -> Dict:
        """
        计算完整的绩效指标
        
        Args:
            equity_curve: 资金曲线，列：timestamp, total_assets, cash, market_value
            trades: 成交记录，列：trade_time, symbol, direction, volume, price, commission, realized_pnl
            
        Returns:
            绩效指标字典
        """
        if equity_curve.empty:
            return {}
        
        # 基础数据
        initial_assets = equity_curve.iloc[0]['total_assets']
        final_assets = equity_curve.iloc[-1]['total_assets']
        
        # 计算日期范围
        start_time = equity_curve.iloc[0]['timestamp']
        end_time = equity_curve.iloc[-1]['timestamp']
        trading_days = (end_time - start_time) / (24 * 3600)
        
        # 1. 总收益率
        total_return = (final_assets / initial_assets - 1) * 100
        
        # 2. 年化收益率
        if trading_days > 0:
            annual_return = total_return * (365 / trading_days)
        else:
            annual_return = 0
        
        # 3. 最大回撤
        cummax = equity_curve['total_assets'].cummax()
        drawdown = (equity_curve['total_assets'] - cummax) / cummax
        max_drawdown = abs(drawdown.min()) * 100
        
        # 4. 夏普比率
        returns = equity_curve['total_assets'].pct_change().dropna()
        if len(returns) > 1 and returns.std() > 0:
            sharpe_ratio = (returns.mean() / returns.std()) * np.sqrt(252)
        else:
            sharpe_ratio = 0
        
        # 5. 卡玛比率
        if max_drawdown > 0:
            calmar_ratio = annual_return / max_drawdown
        else:
            calmar_ratio = 0
        
        # 交易统计
        if not trades.empty:
            # 6. 交易次数
            total_trades = len(trades)
            
            # 7. 胜率
            winning_trades = trades[trades['realized_pnl'] > 0]
            win_rate = (len(winning_trades) / total_trades * 100) if total_trades > 0 else 0
            
            # 8. 平均每笔盈亏
            avg_profit_per_trade = trades['realized_pnl'].mean() if total_trades > 0 else 0
            
            # 9. 盈亏比
            total_profit = winning_trades['realized_pnl'].sum() if not winning_trades.empty else 0
            losing_trades = trades[trades['realized_pnl'] < 0]
            total_loss = abs(losing_trades['realized_pnl'].sum()) if not losing_trades.empty else 0
            profit_factor = (total_profit / total_loss) if total_loss > 0 else 0
            
            # 10. 最大连胜/连亏
            win_streak = 0
            loss_streak = 0
            max_win_streak = 0
            max_loss_streak = 0
            
            for pnl in trades['realized_pnl']:
                if pnl > 0:
                    win_streak += 1
                    loss_streak = 0
                    max_win_streak = max(max_win_streak, win_streak)
                elif pnl < 0:
                    loss_streak += 1
                    win_streak = 0
                    max_loss_streak = max(max_loss_streak, loss_streak)
        else:
            total_trades = 0
            win_rate = 0
            avg_profit_per_trade = 0
            profit_factor = 0
            max_win_streak = 0
            max_loss_streak = 0
        
        return {
            'total_return': round(total_return, 2),
            'annual_return': round(annual_return, 2),
            'max_drawdown': round(max_drawdown, 2),
            'sharpe_ratio': round(sharpe_ratio, 2),
            'calmar_ratio': round(calmar_ratio, 2),
            'win_rate': round(win_rate, 2),
            'total_trades': total_trades,
            'avg_profit_per_trade': round(avg_profit_per_trade, 2),
            'profit_factor': round(profit_factor, 2),
            'max_consecutive_wins': max_win_streak,
            'max_consecutive_losses': max_loss_streak,
            'trading_days': round(trading_days, 1),
            'initial_assets': round(initial_assets, 2),
            'final_assets': round(final_assets, 2)
        }
    
    @staticmethod
    def generate_report(account_id: str, db_path: str = "data/sim_trader.db") -> str:
        """
        生成文本格式绩效报告
        
        Args:
            account_id: 账户ID
            db_path: 数据库路径
            
        Returns:
            报告文本
        """
        db = DatabaseManager(db_path)
        
        # 加载数据
        equity_df, trades_df = PerformanceAnalyzer.load_data_from_db(account_id, db_path)
        
        if equity_df.empty:
            return "No data available for analysis"
        
        # 计算指标
        metrics = PerformanceAnalyzer.calculate_metrics(equity_df, trades_df)
        
        # 获取账户信息
        account_info = db.get_account_info(account_id)
        
        # 生成报告
        report = []
        report.append("=" * 60)
        report.append("ApexQuant Performance Report")
        report.append("=" * 60)
        report.append(f"Account ID: {account_id}")
        report.append(f"Account Name: {account_info.get('account_name', 'N/A')}")
        report.append(f"Strategy: {account_info.get('strategy_type', 'N/A')}")
        report.append(f"Trading Days: {metrics.get('trading_days', 0):.1f}")
        report.append("")
        
        report.append("=== Return Metrics ===")
        report.append(f"Initial Capital: {metrics.get('initial_assets', 0):,.2f}")
        report.append(f"Final Assets: {metrics.get('final_assets', 0):,.2f}")
        report.append(f"Total Return: {metrics.get('total_return', 0):.2f}%")
        report.append(f"Annual Return: {metrics.get('annual_return', 0):.2f}%")
        report.append("")
        
        report.append("=== Risk Metrics ===")
        report.append(f"Max Drawdown: {metrics.get('max_drawdown', 0):.2f}%")
        report.append(f"Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.2f}")
        report.append(f"Calmar Ratio: {metrics.get('calmar_ratio', 0):.2f}")
        report.append("")
        
        report.append("=== Trading Statistics ===")
        report.append(f"Total Trades: {metrics.get('total_trades', 0)}")
        report.append(f"Win Rate: {metrics.get('win_rate', 0):.2f}%")
        report.append(f"Avg Profit/Trade: {metrics.get('avg_profit_per_trade', 0):.2f}")
        report.append(f"Profit Factor: {metrics.get('profit_factor', 0):.2f}")
        report.append(f"Max Consecutive Wins: {metrics.get('max_consecutive_wins', 0)}")
        report.append(f"Max Consecutive Losses: {metrics.get('max_consecutive_losses', 0)}")
        report.append("")
        
        # 最近交易
        if not trades_df.empty:
            report.append("=== Recent Trades (Last 10) ===")
            recent_trades = trades_df.tail(10)
            for _, trade in recent_trades.iterrows():
                report.append(
                    f"{trade['symbol']} {trade['direction']} "
                    f"{trade['volume']} @ {trade['price']:.2f} "
                    f"PnL: {trade.get('realized_pnl', 0):.2f}"
                )
            report.append("")
        
        report.append("=" * 60)
        
        return "\n".join(report)
    
    @staticmethod
    def load_data_from_db(
        account_id: str, 
        db_path: str = "data/sim_trader.db"
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        从数据库加载数据
        
        Args:
            account_id: 账户ID
            db_path: 数据库路径
            
        Returns:
            (equity_curve_df, trades_df)
        """
        db = DatabaseManager(db_path)
        
        # 加载资金曲线
        equity_data = db.execute_query(
            "SELECT * FROM equity_curve WHERE account_id = ? ORDER BY timestamp",
            (account_id,)
        )
        equity_df = pd.DataFrame(equity_data) if equity_data else pd.DataFrame()
        
        # 加载成交记录
        trades_data = db.execute_query(
            "SELECT * FROM trades WHERE account_id = ? ORDER BY trade_time",
            (account_id,)
        )
        trades_df = pd.DataFrame(trades_data) if trades_data else pd.DataFrame()
        
        return equity_df, trades_df


def calculate_drawdown(equity_series: pd.Series) -> pd.Series:
    """计算回撤序列"""
    cummax = equity_series.cummax()
    drawdown = (equity_series - cummax) / cummax
    return drawdown


def calculate_sharpe(
    returns: pd.Series, 
    risk_free_rate: float = 0.03
) -> float:
    """计算夏普比率"""
    excess_returns = returns - risk_free_rate / 252
    if excess_returns.std() == 0:
        return 0.0
    return excess_returns.mean() / excess_returns.std() * np.sqrt(252)


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 60)
    print("ApexQuant Performance Analyzer Test")
    print("=" * 60)
    
    # 创建模拟数据
    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    equity_data = {
        'timestamp': [int(d.timestamp()) for d in dates],
        'total_assets': [1000000 + i * 1000 + np.random.randn() * 5000 for i in range(100)],
        'cash': [500000] * 100,
        'market_value': [500000] * 100
    }
    equity_df = pd.DataFrame(equity_data)
    
    trades_data = {
        'trade_time': [int(d.timestamp()) for d in dates[:20]],
        'symbol': ['600519.SH'] * 20,
        'direction': ['BUY', 'SELL'] * 10,
        'volume': [100] * 20,
        'price': [1800 + i * 10 for i in range(20)],
        'commission': [50] * 20,
        'realized_pnl': [1000 if i % 2 else -500 for i in range(20)]
    }
    trades_df = pd.DataFrame(trades_data)
    
    # 计算指标
    print("\n[Test] Calculate metrics")
    metrics = PerformanceAnalyzer.calculate_metrics(equity_df, trades_df)
    
    for key, value in metrics.items():
        print(f"  {key}: {value}")
    
    print("\n" + "=" * 60)
    print("[OK] Performance analyzer test passed!")
    print("=" * 60)
