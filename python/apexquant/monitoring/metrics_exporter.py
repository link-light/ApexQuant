"""
Prometheus 指标导出器
"""

from typing import Dict, Optional
import time
from datetime import datetime


class MetricsExporter:
    """
    Prometheus 指标导出器
    
    暴露交易系统关键指标供 Prometheus 抓取
    """
    
    def __init__(self):
        """初始化"""
        self.metrics = {
            'total_assets': 0.0,
            'profit_loss': 0.0,
            'profit_loss_pct': 0.0,
            'win_rate': 0.0,
            'max_drawdown': 0.0,
            'sharpe_ratio': 0.0,
            'trade_count': 0,
            'position_count': 0,
            'daily_pnl': 0.0,
            'orders_submitted': 0,
            'orders_filled': 0,
            'orders_rejected': 0,
            'signal_count': 0,
            'last_update': time.time()
        }
        
        self.labels = {
            'system': 'apexquant',
            'version': '1.0.0'
        }
    
    def update_account_metrics(self, account: Dict):
        """
        更新账户指标
        
        Args:
            account: 账户信息字典
        """
        self.metrics['total_assets'] = account.get('total_assets', 0.0)
        self.metrics['profit_loss'] = account.get('profit_loss', 0.0)
        self.metrics['profit_loss_pct'] = account.get('profit_loss_pct', 0.0)
        self.metrics['daily_pnl'] = account.get('daily_pnl', 0.0)
        self.metrics['last_update'] = time.time()
    
    def update_performance_metrics(self, performance: Dict):
        """
        更新性能指标
        
        Args:
            performance: 性能指标字典
        """
        self.metrics['win_rate'] = performance.get('win_rate', 0.0)
        self.metrics['max_drawdown'] = performance.get('max_drawdown', 0.0)
        self.metrics['sharpe_ratio'] = performance.get('sharpe_ratio', 0.0)
        self.metrics['last_update'] = time.time()
    
    def update_trading_metrics(self, 
                               trade_count: int,
                               position_count: int,
                               orders_submitted: int = 0,
                               orders_filled: int = 0,
                               orders_rejected: int = 0):
        """
        更新交易指标
        
        Args:
            trade_count: 交易次数
            position_count: 持仓数
            orders_submitted: 已提交订单数
            orders_filled: 已成交订单数
            orders_rejected: 已拒绝订单数
        """
        self.metrics['trade_count'] = trade_count
        self.metrics['position_count'] = position_count
        self.metrics['orders_submitted'] += orders_submitted
        self.metrics['orders_filled'] += orders_filled
        self.metrics['orders_rejected'] += orders_rejected
        self.metrics['last_update'] = time.time()
    
    def increment_signal_count(self):
        """增加信号计数"""
        self.metrics['signal_count'] += 1
    
    def export_prometheus_format(self) -> str:
        """
        导出 Prometheus 格式指标
        
        Returns:
            Prometheus 格式的指标文本
        """
        lines = []
        
        # 标签字符串
        label_str = ','.join([f'{k}="{v}"' for k, v in self.labels.items()])
        
        # 账户指标
        lines.append(f'# HELP apexquant_total_assets 总资产')
        lines.append(f'# TYPE apexquant_total_assets gauge')
        lines.append(f'apexquant_total_assets{{{label_str}}} {self.metrics["total_assets"]}')
        
        lines.append(f'# HELP apexquant_profit_loss 盈亏')
        lines.append(f'# TYPE apexquant_profit_loss gauge')
        lines.append(f'apexquant_profit_loss{{{label_str}}} {self.metrics["profit_loss"]}')
        
        lines.append(f'# HELP apexquant_profit_loss_pct 盈亏比例')
        lines.append(f'# TYPE apexquant_profit_loss_pct gauge')
        lines.append(f'apexquant_profit_loss_pct{{{label_str}}} {self.metrics["profit_loss_pct"]}')
        
        lines.append(f'# HELP apexquant_daily_pnl 当日盈亏')
        lines.append(f'# TYPE apexquant_daily_pnl gauge')
        lines.append(f'apexquant_daily_pnl{{{label_str}}} {self.metrics["daily_pnl"]}')
        
        # 性能指标
        lines.append(f'# HELP apexquant_win_rate 胜率')
        lines.append(f'# TYPE apexquant_win_rate gauge')
        lines.append(f'apexquant_win_rate{{{label_str}}} {self.metrics["win_rate"]}')
        
        lines.append(f'# HELP apexquant_max_drawdown 最大回撤')
        lines.append(f'# TYPE apexquant_max_drawdown gauge')
        lines.append(f'apexquant_max_drawdown{{{label_str}}} {self.metrics["max_drawdown"]}')
        
        lines.append(f'# HELP apexquant_sharpe_ratio 夏普比率')
        lines.append(f'# TYPE apexquant_sharpe_ratio gauge')
        lines.append(f'apexquant_sharpe_ratio{{{label_str}}} {self.metrics["sharpe_ratio"]}')
        
        # 交易指标
        lines.append(f'# HELP apexquant_trade_count 交易次数')
        lines.append(f'# TYPE apexquant_trade_count counter')
        lines.append(f'apexquant_trade_count{{{label_str}}} {self.metrics["trade_count"]}')
        
        lines.append(f'# HELP apexquant_position_count 持仓数')
        lines.append(f'# TYPE apexquant_position_count gauge')
        lines.append(f'apexquant_position_count{{{label_str}}} {self.metrics["position_count"]}')
        
        lines.append(f'# HELP apexquant_orders_submitted 已提交订单数')
        lines.append(f'# TYPE apexquant_orders_submitted counter')
        lines.append(f'apexquant_orders_submitted{{{label_str}}} {self.metrics["orders_submitted"]}')
        
        lines.append(f'# HELP apexquant_orders_filled 已成交订单数')
        lines.append(f'# TYPE apexquant_orders_filled counter')
        lines.append(f'apexquant_orders_filled{{{label_str}}} {self.metrics["orders_filled"]}')
        
        lines.append(f'# HELP apexquant_orders_rejected 已拒绝订单数')
        lines.append(f'# TYPE apexquant_orders_rejected counter')
        lines.append(f'apexquant_orders_rejected{{{label_str}}} {self.metrics["orders_rejected"]}')
        
        lines.append(f'# HELP apexquant_signal_count 信号数')
        lines.append(f'# TYPE apexquant_signal_count counter')
        lines.append(f'apexquant_signal_count{{{label_str}}} {self.metrics["signal_count"]}')
        
        # 最后更新时间
        lines.append(f'# HELP apexquant_last_update 最后更新时间戳')
        lines.append(f'# TYPE apexquant_last_update gauge')
        lines.append(f'apexquant_last_update{{{label_str}}} {self.metrics["last_update"]}')
        
        return '\n'.join(lines) + '\n'
    
    def get_metrics(self) -> Dict:
        """获取当前指标"""
        return self.metrics.copy()

