"""
通知推送系统
"""

import requests
from typing import Dict, List, Optional
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))


class NotificationManager:
    """
    通知推送管理器
    
    支持 Telegram、企业微信等推送渠道
    """
    
    def __init__(self,
                 telegram_token: Optional[str] = None,
                 telegram_chat_id: Optional[str] = None,
                 wechat_webhook: Optional[str] = None):
        """
        初始化
        
        Args:
            telegram_token: Telegram Bot Token
            telegram_chat_id: Telegram Chat ID
            wechat_webhook: 企业微信 Webhook URL
        """
        self.telegram_token = telegram_token
        self.telegram_chat_id = telegram_chat_id
        self.wechat_webhook = wechat_webhook
        
        self.telegram_enabled = bool(telegram_token and telegram_chat_id)
        self.wechat_enabled = bool(wechat_webhook)
        
        if not self.telegram_enabled and not self.wechat_enabled:
            print("⚠ 未配置推送渠道")
    
    def send_alert(self, 
                  title: str,
                  message: str,
                  level: str = "info") -> bool:
        """
        发送警报
        
        Args:
            title: 标题
            message: 消息内容
            level: 级别 (info/warning/error)
        
        Returns:
            是否成功
        """
        # 添加级别标识
        emoji = {
            'info': 'ℹ️',
            'warning': '⚠️',
            'error': '❌'
        }.get(level, 'ℹ️')
        
        full_message = f"{emoji} {title}\n\n{message}"
        
        success = False
        
        # Telegram
        if self.telegram_enabled:
            success |= self._send_telegram(full_message)
        
        # 企业微信
        if self.wechat_enabled:
            success |= self._send_wechat(title, message, level)
        
        return success
    
    def send_trade_notification(self,
                               symbol: str,
                               action: str,
                               price: float,
                               volume: int,
                               reason: str) -> bool:
        """
        发送交易通知
        
        Args:
            symbol: 股票代码
            action: 动作
            price: 价格
            volume: 数量
            reason: 理由
        
        Returns:
            是否成功
        """
        title = f"交易提醒: {symbol}"
        
        action_emoji = "🟢" if action == "buy" else "🔴"
        
        message = f"""
{action_emoji} 动作: {action.upper()}
💰 价格: {price:.2f}
📊 数量: {volume}
📝 理由: {reason}
⏰ 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        return self.send_alert(title, message, level="info")
    
    def send_risk_alert(self,
                       alert_type: str,
                       details: Dict) -> bool:
        """
        发送风控警报
        
        Args:
            alert_type: 警报类型
            details: 详细信息
        
        Returns:
            是否成功
        """
        title = f"⚠️ 风控警报: {alert_type}"
        
        message = "\n".join([f"{k}: {v}" for k, v in details.items()])
        
        return self.send_alert(title, message, level="warning")
    
    def send_daily_report(self,
                         report: str) -> bool:
        """
        发送日报
        
        Args:
            report: 报告内容
        
        Returns:
            是否成功
        """
        title = f"📊 交易日报 - {datetime.now().strftime('%Y-%m-%d')}"
        
        return self.send_alert(title, report, level="info")
    
    def send_performance_summary(self,
                                performance: Dict) -> bool:
        """
        发送绩效总结
        
        Args:
            performance: 绩效数据
        
        Returns:
            是否成功
        """
        title = "📈 交易绩效总结"
        
        message = f"""
总资产: {performance.get('total_assets', 0):.2f}
盈亏: {performance.get('profit_loss', 0):.2f} ({performance.get('profit_loss_pct', 0):.2%})
胜率: {performance.get('win_rate', 0):.2%}
最大回撤: {performance.get('max_drawdown', 0):.2%}
交易次数: {performance.get('trade_count', 0)}
"""
        
        return self.send_alert(title, message, level="info")
    
    def _send_telegram(self, message: str) -> bool:
        """发送 Telegram 消息"""
        if not self.telegram_enabled:
            return False
        
        url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
        
        payload = {
            'chat_id': self.telegram_chat_id,
            'text': message,
            'parse_mode': 'HTML'
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                print("✓ Telegram 消息已发送")
                return True
            else:
                print(f"✗ Telegram 发送失败: {response.text}")
                return False
                
        except Exception as e:
            print(f"✗ Telegram 发送异常: {e}")
            return False
    
    def _send_wechat(self, 
                    title: str,
                    message: str,
                    level: str) -> bool:
        """发送企业微信消息"""
        if not self.wechat_enabled:
            return False
        
        # 企业微信 Markdown 格式
        color_map = {
            'info': 'info',
            'warning': 'warning',
            'error': 'comment'
        }
        
        content = f"""
### {title}

{message}

> 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        payload = {
            "msgtype": "markdown",
            "markdown": {
                "content": content
            }
        }
        
        try:
            response = requests.post(self.wechat_webhook, json=payload, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('errcode') == 0:
                    print("✓ 企业微信消息已发送")
                    return True
                else:
                    print(f"✗ 企业微信发送失败: {result}")
                    return False
            else:
                print(f"✗ 企业微信 HTTP 错误: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"✗ 企业微信发送异常: {e}")
            return False
    
    def test_notification(self) -> Dict[str, bool]:
        """测试通知"""
        results = {}
        
        test_message = f"ApexQuant 通知测试\n时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        if self.telegram_enabled:
            results['telegram'] = self._send_telegram(test_message)
        
        if self.wechat_enabled:
            results['wechat'] = self._send_wechat("通知测试", test_message, "info")
        
        return results

