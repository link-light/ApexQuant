"""
交易日志分析器
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from apexquant.ai import DeepSeekClient


class LogAnalyzer:
    """
    交易日志分析器
    
    使用 LLM 分析交易日志，给出优化建议
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """初始化"""
        try:
            self.client = DeepSeekClient(api_key)
            self.ai_enabled = True
        except:
            self.ai_enabled = False
            print("⚠ AI 未启用")
        
        self.logs = []
    
    def log_trade(self, 
                  timestamp: datetime,
                  symbol: str,
                  action: str,
                  price: float,
                  volume: int,
                  reason: str,
                  result: Optional[Dict] = None):
        """
        记录交易
        
        Args:
            timestamp: 时间戳
            symbol: 股票代码
            action: 动作 (buy/sell)
            price: 价格
            volume: 数量
            reason: 原因
            result: 结果（平仓时提供）
        """
        log_entry = {
            'timestamp': timestamp,
            'symbol': symbol,
            'action': action,
            'price': price,
            'volume': volume,
            'reason': reason,
            'result': result
        }
        
        self.logs.append(log_entry)
    
    def log_signal(self,
                  timestamp: datetime,
                  symbol: str,
                  signal: Dict):
        """记录信号"""
        log_entry = {
            'timestamp': timestamp,
            'type': 'signal',
            'symbol': symbol,
            'signal': signal
        }
        
        self.logs.append(log_entry)
    
    def log_error(self,
                 timestamp: datetime,
                 error_msg: str):
        """记录错误"""
        log_entry = {
            'timestamp': timestamp,
            'type': 'error',
            'message': error_msg
        }
        
        self.logs.append(log_entry)
    
    def analyze_trading_session(self, 
                               trades: List[Dict],
                               account_performance: Dict) -> str:
        """
        分析交易会话
        
        Args:
            trades: 交易记录列表
            account_performance: 账户表现
        
        Returns:
            分析报告
        """
        if not self.ai_enabled:
            return self._simple_analysis(trades, account_performance)
        
        # 准备分析数据
        analysis_data = self._prepare_analysis_data(trades, account_performance)
        
        # AI 分析
        report = self._ai_analyze(analysis_data)
        
        return report
    
    def _prepare_analysis_data(self, 
                               trades: List[Dict],
                               account_performance: Dict) -> str:
        """准备分析数据"""
        data = f"""
【账户表现】
总资产: {account_performance.get('total_assets', 0):.2f}
盈亏: {account_performance.get('profit_loss', 0):.2f} ({account_performance.get('profit_loss_pct', 0):.2%})
胜率: {account_performance.get('win_rate', 0):.2%}
总交易次数: {len(trades)}

【交易记录】
"""
        
        # 成功和失败的交易
        wins = []
        losses = []
        
        for trade in trades:
            if 'result' in trade and trade['result']:
                result = trade['result']
                pnl = result.get('pnl', 0)
                
                trade_summary = f"{trade['symbol']}: {trade['action']} @ {trade['price']:.2f}, " \
                               f"盈亏 {pnl:.2f} ({result.get('pnl_pct', 0):.2%}), " \
                               f"理由: {trade['reason']}"
                
                if pnl > 0:
                    wins.append(trade_summary)
                else:
                    losses.append(trade_summary)
        
        if wins:
            data += f"\n成功交易 ({len(wins)}):\n"
            for i, w in enumerate(wins[:5], 1):  # 最多显示5个
                data += f"{i}. {w}\n"
        
        if losses:
            data += f"\n失败交易 ({len(losses)}):\n"
            for i, l in enumerate(losses[:5], 1):
                data += f"{i}. {l}\n"
        
        # 常见信号
        signal_reasons = {}
        for trade in trades:
            reason = trade.get('reason', 'unknown')
            signal_reasons[reason] = signal_reasons.get(reason, 0) + 1
        
        data += f"\n【信号统计】\n"
        for reason, count in sorted(signal_reasons.items(), key=lambda x: x[1], reverse=True)[:5]:
            data += f"{reason}: {count}次\n"
        
        return data
    
    def _ai_analyze(self, analysis_data: str) -> str:
        """AI 分析"""
        prompt = f"""
你是一个专业的量化交易顾问。请分析以下交易数据，给出改进建议。

{analysis_data}

请提供：
1. 交易表现评价（80字）
2. 主要问题分析（3-4点，每点40字）
3. 优化建议（4-5点，每点30字）
4. 参数调整建议（如止损、仓位、信号阈值等）

要求简洁实用，总字数500字内。
"""
        
        messages = [
            {"role": "system", "content": "你是专业量化交易顾问。"},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = self.client.chat(messages, temperature=0.5, max_tokens=1000)
            return response
        except Exception as e:
            return f"AI 分析失败: {e}"
    
    def _simple_analysis(self, 
                        trades: List[Dict],
                        account_performance: Dict) -> str:
        """简单分析（无 AI）"""
        report = f"""
===== 交易分析报告 =====

【账户表现】
总资产: {account_performance.get('total_assets', 0):.2f}
盈亏: {account_performance.get('profit_loss', 0):.2f}
胜率: {account_performance.get('win_rate', 0):.2%}
交易次数: {len(trades)}

【建议】
- 建议增加样本量以获得更准确的分析
- 关注胜率和盈亏比
- 考虑优化止损止盈参数
"""
        
        return report
    
    def generate_daily_report(self, 
                             trades: List[Dict],
                             positions: List[Dict],
                             account: Dict) -> str:
        """
        生成每日报告
        
        Args:
            trades: 当日交易
            positions: 当前持仓
            account: 账户信息
        
        Returns:
            日报
        """
        if not self.ai_enabled:
            return self._simple_daily_report(trades, positions, account)
        
        # 准备数据
        report_data = f"""
日期: {datetime.now().strftime('%Y-%m-%d')}

【账户概况】
总资产: {account.get('total_assets', 0):.2f}
可用资金: {account.get('available_cash', 0):.2f}
持仓市值: {account.get('market_value', 0):.2f}
当日盈亏: {account.get('daily_pnl', 0):.2f} ({account.get('daily_pnl_pct', 0):.2%})

【当日交易】
交易次数: {len(trades)}
"""
        
        if trades:
            report_data += "主要操作:\n"
            for trade in trades[:5]:
                report_data += f"- {trade['symbol']} {trade['action']} @ {trade['price']:.2f}\n"
        
        report_data += f"\n【当前持仓】\n持仓数: {len(positions)}\n"
        
        if positions:
            for pos in positions:
                report_data += f"- {pos['symbol']}: {pos['volume']}股, 盈亏 {pos.get('pnl_ratio', 0):.2%}\n"
        
        # AI 生成日报
        prompt = f"""
根据以下交易数据，生成简洁的每日交易总结。

{report_data}

要求：
1. 总结当日表现（60字）
2. 主要交易亮点或问题（2-3点）
3. 明日建议（40字）

总字数200字内，简洁专业。
"""
        
        messages = [
            {"role": "system", "content": "你是量化交易助手。"},
            {"role": "user", "content": prompt}
        ]
        
        try:
            summary = self.client.chat(messages, temperature=0.6, max_tokens=400)
            return f"===== 每日交易报告 =====\n\n{report_data}\n\n【AI 总结】\n{summary}"
        except Exception as e:
            return f"{report_data}\n\nAI 总结失败: {e}"
    
    def _simple_daily_report(self,
                            trades: List[Dict],
                            positions: List[Dict],
                            account: Dict) -> str:
        """简单日报"""
        return f"""
===== 每日交易报告 =====
日期: {datetime.now().strftime('%Y-%m-%d')}

总资产: {account.get('total_assets', 0):.2f}
当日盈亏: {account.get('daily_pnl', 0):.2f}
交易次数: {len(trades)}
持仓数: {len(positions)}
"""
    
    def save_logs(self, filepath: str):
        """保存日志"""
        df = pd.DataFrame(self.logs)
        df.to_csv(filepath, index=False)
        print(f"日志已保存: {filepath}")
    
    def clear_logs(self):
        """清空日志"""
        self.logs = []

