"""
LLM 异常检测器
"""

import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from apexquant.ai import DeepSeekClient


class AnomalyDetector:
    """
    LLM 驱动的异常检测器
    
    分析系统日志和指标，自动识别异常并报警
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """初始化"""
        try:
            self.client = DeepSeekClient(api_key)
            self.ai_enabled = True
        except:
            self.ai_enabled = False
            print("⚠ AI 未启用，异常检测功能受限")
        
        self.anomaly_history = []
        
        # 阈值配置
        self.thresholds = {
            'max_drawdown': 0.20,
            'win_rate_min': 0.30,
            'daily_loss_pct': -0.10,
            'position_count_max': 10,
            'error_rate': 0.10
        }
    
    def detect_metric_anomalies(self, metrics: Dict) -> List[Dict]:
        """
        检测指标异常
        
        Args:
            metrics: 系统指标
        
        Returns:
            异常列表
        """
        anomalies = []
        
        # 1. 回撤异常
        if metrics.get('max_drawdown', 0) > self.thresholds['max_drawdown']:
            anomalies.append({
                'type': 'high_drawdown',
                'severity': 'critical',
                'metric': 'max_drawdown',
                'value': metrics['max_drawdown'],
                'threshold': self.thresholds['max_drawdown'],
                'message': f"最大回撤 {metrics['max_drawdown']:.2%} 超过阈值 {self.thresholds['max_drawdown']:.2%}"
            })
        
        # 2. 胜率异常
        if metrics.get('win_rate', 1.0) < self.thresholds['win_rate_min']:
            anomalies.append({
                'type': 'low_win_rate',
                'severity': 'warning',
                'metric': 'win_rate',
                'value': metrics['win_rate'],
                'threshold': self.thresholds['win_rate_min'],
                'message': f"胜率 {metrics['win_rate']:.2%} 低于阈值 {self.thresholds['win_rate_min']:.2%}"
            })
        
        # 3. 单日亏损异常
        daily_pnl_pct = metrics.get('daily_pnl', 0) / max(metrics.get('total_assets', 100000), 1)
        if daily_pnl_pct < self.thresholds['daily_loss_pct']:
            anomalies.append({
                'type': 'high_daily_loss',
                'severity': 'critical',
                'metric': 'daily_pnl',
                'value': daily_pnl_pct,
                'threshold': self.thresholds['daily_loss_pct'],
                'message': f"单日亏损 {daily_pnl_pct:.2%} 超过阈值"
            })
        
        # 4. 持仓数异常
        if metrics.get('position_count', 0) > self.thresholds['position_count_max']:
            anomalies.append({
                'type': 'high_position_count',
                'severity': 'warning',
                'metric': 'position_count',
                'value': metrics['position_count'],
                'threshold': self.thresholds['position_count_max'],
                'message': f"持仓数 {metrics['position_count']} 超过限制"
            })
        
        # 5. 订单拒绝率异常
        orders_total = metrics.get('orders_submitted', 0)
        orders_rejected = metrics.get('orders_rejected', 0)
        
        if orders_total > 0:
            rejection_rate = orders_rejected / orders_total
            if rejection_rate > self.thresholds['error_rate']:
                anomalies.append({
                    'type': 'high_rejection_rate',
                    'severity': 'warning',
                    'metric': 'rejection_rate',
                    'value': rejection_rate,
                    'threshold': self.thresholds['error_rate'],
                    'message': f"订单拒绝率 {rejection_rate:.2%} 过高"
                })
        
        # 记录异常
        for anomaly in anomalies:
            anomaly['timestamp'] = datetime.now()
            self.anomaly_history.append(anomaly)
        
        return anomalies
    
    def analyze_logs(self, logs: List[str]) -> Optional[str]:
        """
        分析日志，识别潜在问题
        
        Args:
            logs: 日志列表
        
        Returns:
            分析报告
        """
        if not self.ai_enabled or not logs:
            return None
        
        # 准备日志摘要
        log_summary = '\n'.join(logs[-50:])  # 最近50条
        
        prompt = f"""
你是系统运维专家。请分析以下交易系统日志，识别潜在问题。

【日志内容】
{log_summary}

请识别：
1. 异常模式（3-4点，每点30字）
2. 潜在风险（2-3点，每点30字）
3. 建议措施（2-3点，每点25字）

要求简洁，总字数250字内。如无明显异常，说明"系统运行正常"。
"""
        
        messages = [
            {"role": "system", "content": "你是系统运维和异常检测专家。"},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = self.client.chat(messages, temperature=0.3, max_tokens=500)
            return response
        except Exception as e:
            print(f"日志分析失败: {e}")
            return None
    
    def analyze_trading_patterns(self, 
                                 trades: List[Dict],
                                 performance: Dict) -> Optional[str]:
        """
        分析交易模式，识别异常行为
        
        Args:
            trades: 交易记录
            performance: 性能指标
        
        Returns:
            分析报告
        """
        if not self.ai_enabled or not trades:
            return None
        
        # 准备交易摘要
        trade_summary = f"""
交易次数: {len(trades)}
胜率: {performance.get('win_rate', 0):.2%}
盈亏: {performance.get('profit_loss', 0):.2f}
最大回撤: {performance.get('max_drawdown', 0):.2%}

最近交易:
"""
        
        for i, trade in enumerate(trades[-10:], 1):
            pnl = trade.get('result', {}).get('pnl', 0) if 'result' in trade else 0
            trade_summary += f"{i}. {trade['symbol']} {trade['action']} @ {trade['price']:.2f}, 盈亏 {pnl:.2f}\n"
        
        prompt = f"""
你是量化交易风控专家。请分析以下交易模式，识别异常行为。

{trade_summary}

请识别：
1. 交易行为是否正常（50字）
2. 潜在异常模式（2-3点，每点40字）
3. 风控建议（2点，每点30字）

总字数200字内。
"""
        
        messages = [
            {"role": "system", "content": "你是量化交易风控专家。"},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = self.client.chat(messages, temperature=0.3, max_tokens=400)
            return response
        except Exception as e:
            print(f"交易模式分析失败: {e}")
            return None
    
    def generate_alert_message(self, anomalies: List[Dict]) -> str:
        """
        生成告警消息
        
        Args:
            anomalies: 异常列表
        
        Returns:
            告警消息
        """
        if not anomalies:
            return "系统运行正常"
        
        message = f"⚠️ 检测到 {len(anomalies)} 个异常\n\n"
        
        for i, anomaly in enumerate(anomalies, 1):
            severity_emoji = {
                'critical': '🔴',
                'warning': '⚠️',
                'info': 'ℹ️'
            }.get(anomaly['severity'], 'ℹ️')
            
            message += f"{severity_emoji} {i}. {anomaly['message']}\n"
            message += f"   类型: {anomaly['type']}\n"
            message += f"   当前值: {anomaly['value']}\n"
            message += f"   阈值: {anomaly['threshold']}\n\n"
        
        return message
    
    def get_anomaly_summary(self) -> Dict:
        """获取异常统计"""
        if not self.anomaly_history:
            return {
                'total_count': 0,
                'by_type': {},
                'by_severity': {},
                'recent': []
            }
        
        by_type = {}
        by_severity = {}
        
        for anomaly in self.anomaly_history:
            anomaly_type = anomaly['type']
            severity = anomaly['severity']
            
            by_type[anomaly_type] = by_type.get(anomaly_type, 0) + 1
            by_severity[severity] = by_severity.get(severity, 0) + 1
        
        return {
            'total_count': len(self.anomaly_history),
            'by_type': by_type,
            'by_severity': by_severity,
            'recent': self.anomaly_history[-10:]
        }
    
    def set_thresholds(self, thresholds: Dict):
        """设置阈值"""
        self.thresholds.update(thresholds)

