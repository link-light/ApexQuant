"""
ApexQuant AI交易顾问

集成DeepSeek API提供智能交易建议
"""

import json
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# 尝试导入环境变量支持
try:
    from dotenv import load_dotenv
    load_dotenv()  # 加载.env文件
except ImportError:
    logger.debug("python-dotenv not installed, using system environment variables only")

# 尝试导入OpenAI库（DeepSeek API兼容）
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("openai library not available, AI advisor disabled")

from .config import get_config
from .database import DatabaseManager


class AITradingAdvisor:
    """AI交易顾问"""
    
    def __init__(self, config_path: str = None):
        """
        初始化AI顾问
        
        Args:
            config_path: 配置文件路径
        """
        if not OPENAI_AVAILABLE:
            raise ImportError("openai library is required for AI advisor")
        
        # 加载配置
        config = get_config(config_path)
        ai_config = config.get_ai_config()
        
        # API配置 - 优先使用环境变量
        self.api_key = os.getenv('DEEPSEEK_API_KEY') or ai_config.get('api_key')
        self.model = ai_config.get('model', 'deepseek-chat')
        self.base_url = ai_config.get('base_url', 'https://api.deepseek.com')
        self.timeout = ai_config.get('timeout', 10)
        
        # 调用控制
        self.call_interval_minutes = ai_config.get('call_interval_minutes', 5)
        self.daily_call_limit = ai_config.get('daily_call_limit', 100)
        self.confidence_threshold = ai_config.get('confidence_threshold', 0.7)
        
        # 状态
        self.last_call_time: Optional[datetime] = None
        self.daily_calls = 0
        self.last_reset_date = datetime.now().date()
        self.call_history: List[Dict] = []
        
        # 初始化客户端
        if self.api_key:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=self.timeout
            )
            logger.info(f"AI advisor initialized with model: {self.model}")
        else:
            logger.warning(
                "API key not found. Please set DEEPSEEK_API_KEY environment variable "
                "or configure api_key in simulation_config.yaml. AI advisor disabled."
            )
            self.client = None
    
    def should_call_ai(self, current_time: datetime = None) -> bool:
        """
        判断是否需要调用AI
        
        Args:
            current_time: 当前时间
            
        Returns:
            是否应该调用
        """
        if not self.client:
            return False
        
        if current_time is None:
            current_time = datetime.now()
        
        # 检查日期是否变更，重置计数
        if current_time.date() != self.last_reset_date:
            self.daily_calls = 0
            self.last_reset_date = current_time.date()
        
        # 检查每日调用限制
        if self.daily_calls >= self.daily_call_limit:
            logger.warning(f"Daily call limit reached: {self.daily_calls}/{self.daily_call_limit}")
            return False
        
        # 检查调用间隔
        if self.last_call_time:
            elapsed = (current_time - self.last_call_time).total_seconds() / 60
            if elapsed < self.call_interval_minutes:
                return False
        
        return True
    
    def generate_trading_signal(
        self,
        symbol: str,
        market_data: Dict,
        account_info: Dict,
        news: List[str] = None
    ) -> Dict:
        """
        生成交易信号
        
        Args:
            symbol: 股票代码
            market_data: 市场数据
            account_info: 账户信息
            news: 新闻列表（可选）
            
        Returns:
            信号字典 {
                'action': 'BUY'|'SELL'|'HOLD',
                'volume': int,
                'confidence': float,
                'reasoning': str,
                'risk_level': 'LOW'|'MEDIUM'|'HIGH'
            }
        """
        if not self.client:
            return self._default_signal("AI client not available")
        
        try:
            # 构造prompt
            prompt = self._build_prompt(symbol, market_data, account_info, news)
            
            # 调用API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a professional quantitative trading AI. Always respond with valid JSON only, no markdown or extra text."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            # 解析响应
            content = response.choices[0].message.content
            signal = self._parse_json_response(content)
            
            # 记录调用
            self.last_call_time = datetime.now()
            self.daily_calls += 1
            
            tokens_used = response.usage.total_tokens if hasattr(response, 'usage') else 0
            
            self.call_history.append({
                'timestamp': int(time.time()),
                'symbol': symbol,
                'prompt_length': len(prompt),
                'response': signal,
                'tokens_used': tokens_used
            })
            
            logger.info(f"AI signal: {signal['action']} (confidence: {signal['confidence']:.2f})")
            
            return signal
            
        except Exception as e:
            logger.error(f"AI API error: {e}")
            return self._default_signal(f"API error: {str(e)}")
    
    def _build_prompt(
        self,
        symbol: str,
        market_data: Dict,
        account_info: Dict,
        news: List[str] = None
    ) -> str:
        """构造prompt"""
        # 获取持仓信息
        positions = {p['symbol']: p for p in account_info['positions']}
        position = positions.get(symbol, {})
        
        has_position = position.get('volume', 0) > 0
        position_summary = f"{position['volume']} shares at cost {position.get('avg_cost', 0):.2f}" if has_position else "No position"
        
        # 构造简洁的prompt
        prompt = f"""You are a quantitative trading AI. Respond with JSON only.

Current Market:
Stock: {symbol}
Price: {market_data.get('price', 0):.2f}
"""
        
        # 添加技术指标（如果有）
        if 'ma5' in market_data:
            prompt += f"MA5: {market_data['ma5']:.2f}, MA20: {market_data.get('ma20', 0):.2f}\n"
        
        if 'rsi' in market_data:
            prompt += f"RSI: {market_data['rsi']:.1f}\n"
        
        prompt += f"""
Account Status:
Total Assets: {account_info['total_assets']:.0f}
Available Cash: {account_info['available_cash']:.0f}
Position: {position_summary}
"""
        
        # 添加新闻（如果有）
        if news:
            prompt += f"\nRecent News:\n"
            for item in news[:3]:  # 最多3条
                prompt += f"- {item}\n"
        
        prompt += """
Based on above information, provide trading advice. Respond in JSON format (no markdown):
{
  "action": "BUY" or "SELL" or "HOLD",
  "volume": suggested quantity,
  "confidence": 0.0-1.0 confidence score,
  "reasoning": "brief reason (max 30 words)",
  "risk_level": "LOW" or "MEDIUM" or "HIGH"
}
"""
        
        return prompt
    
    def _parse_json_response(self, text: str) -> Dict:
        """解析JSON响应"""
        try:
            # 移除可能的markdown标记
            text = text.strip()
            if text.startswith('```json'):
                text = text[7:]
            if text.startswith('```'):
                text = text[3:]
            if text.endswith('```'):
                text = text[:-3]
            text = text.strip()
            
            # 解析JSON
            data = json.loads(text)
            
            # 验证必需字段
            required_fields = ['action', 'confidence']
            for field in required_fields:
                if field not in data:
                    logger.warning(f"Missing field: {field}")
                    return self._default_signal("Invalid response format")
            
            # 标准化
            return {
                'action': data.get('action', 'HOLD').upper(),
                'volume': int(data.get('volume', 0)),
                'confidence': float(data.get('confidence', 0)),
                'reasoning': str(data.get('reasoning', 'No reasoning provided')),
                'risk_level': data.get('risk_level', 'MEDIUM').upper()
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            logger.debug(f"Response text: {text}")
            return self._default_signal("JSON parse error")
        except Exception as e:
            logger.error(f"Parse error: {e}")
            return self._default_signal(f"Parse error: {str(e)}")
    
    def _default_signal(self, reason: str) -> Dict:
        """返回默认HOLD信号"""
        return {
            'action': 'HOLD',
            'volume': 0,
            'confidence': 0.0,
            'reasoning': reason,
            'risk_level': 'HIGH'
        }
    
    def get_statistics(self) -> Dict:
        """获取调用统计"""
        total_calls = len(self.call_history)
        total_tokens = sum(h.get('tokens_used', 0) for h in self.call_history)
        
        if total_calls > 0:
            avg_tokens = total_tokens / total_calls
        else:
            avg_tokens = 0
        
        return {
            'total_calls': total_calls,
            'daily_calls': self.daily_calls,
            'total_tokens': total_tokens,
            'avg_tokens_per_call': round(avg_tokens, 1)
        }


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 60)
    print("ApexQuant AI Advisor Test")
    print("=" * 60)
    
    try:
        advisor = AITradingAdvisor()
        
        # 模拟数据
        market_data = {
            'price': 1800.0,
            'ma5': 1795.0,
            'ma20': 1780.0,
            'rsi': 65.0
        }
        
        account_info = {
            'total_assets': 1000000,
            'available_cash': 800000,
            'positions': []
        }
        
        print("\n[Test] Generate trading signal")
        if advisor.should_call_ai():
            signal = advisor.generate_trading_signal(
                '600519.SH',
                market_data,
                account_info
            )
            
            print(f"Action: {signal['action']}")
            print(f"Confidence: {signal['confidence']:.2f}")
            print(f"Reasoning: {signal['reasoning']}")
            print(f"Risk Level: {signal['risk_level']}")
        else:
            print("AI call not allowed (check interval/limit)")
        
        print("\n[Test] Statistics")
        stats = advisor.get_statistics()
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
    except Exception as e:
        print(f"[ERROR] {e}")
        print("Note: API key may not be configured")
    
    print("\n" + "=" * 60)
    print("[OK] AI advisor test completed!")
    print("=" * 60)
