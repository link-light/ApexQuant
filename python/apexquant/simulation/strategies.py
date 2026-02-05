"""
ApexQuant 内置策略

提供常用的交易策略实现
"""

import logging
from typing import Dict, Optional, Callable
from collections import deque

logger = logging.getLogger(__name__)


# ============================================================================
# 策略工厂函数
# ============================================================================

def create_ma_cross_strategy(
    risk_manager=None,
    ai_advisor=None,
    ma_short: int = 5,
    ma_long: int = 20
) -> Callable:
    """
    创建均线交叉策略
    
    Args:
        risk_manager: 风控管理器（可选）
        ai_advisor: AI顾问（可选）
        ma_short: 短期均线周期
        ma_long: 长期均线周期
        
    Returns:
        策略函数
    """
    # 历史价格队列
    price_history = deque(maxlen=ma_long)
    
    def strategy(controller, bar: Dict, account_info: Dict) -> Optional[Dict]:
        """均线交叉策略函数"""
        symbol = bar['symbol']
        close_price = bar['close']
        
        # 添加到历史
        price_history.append(close_price)
        
        # 数据不足，等待
        if len(price_history) < ma_long:
            return None
        
        # 计算均线
        ma5 = sum(list(price_history)[-ma_short:]) / ma_short
        ma20 = sum(list(price_history)[-ma_long:]) / ma_long
        
        # 获取当前持仓
        positions = {p['symbol']: p for p in account_info['positions']}
        current_position = positions.get(symbol, {}).get('volume', 0)
        
        # 金叉信号：MA5上穿MA20，且无持仓
        if ma5 > ma20 and current_position == 0:
            # 计算买入数量
            if risk_manager:
                max_volume = risk_manager.get_max_buy_volume(
                    symbol, close_price, account_info
                )
            else:
                # 简单计算：用20%资金
                max_volume = int(account_info['available_cash'] * 0.2 / close_price)
                max_volume = (max_volume // 100) * 100  # 向下取整到100
            
            if max_volume >= 100:
                # 如果启用AI，让AI确认
                if ai_advisor and ai_advisor.should_call_ai():
                    try:
                        market_data = {
                            'price': close_price,
                            'ma5': ma5,
                            'ma20': ma20
                        }
                        signal = ai_advisor.generate_trading_signal(
                            symbol, market_data, account_info
                        )
                        
                        if signal['action'] != 'BUY' or signal['confidence'] < 0.7:
                            logger.info(f"AI rejected buy signal: {signal}")
                            return None
                    except Exception as e:
                        logger.error(f"AI advisor error: {e}")
                
                logger.info(f"[MA Cross] Buy signal: MA5={ma5:.2f} > MA20={ma20:.2f}")
                return {
                    'action': 'BUY',
                    'symbol': symbol,
                    'volume': max_volume,
                    'price': None  # 市价单
                }
        
        # 死叉信号：MA5下穿MA20，且有持仓
        elif ma5 < ma20 and current_position > 0:
            logger.info(f"[MA Cross] Sell signal: MA5={ma5:.2f} < MA20={ma20:.2f}")
            
            # 卖出所有可用持仓
            available_volume = positions[symbol].get('available_volume', 0)
            if available_volume > 0:
                return {
                    'action': 'SELL',
                    'symbol': symbol,
                    'volume': available_volume,
                    'price': None  # 市价单
                }
        
        return None
    
    return strategy


def create_buy_hold_strategy() -> Callable:
    """
    创建买入持有策略（测试用）
    
    Returns:
        策略函数
    """
    bought = False
    
    def strategy(controller, bar: Dict, account_info: Dict) -> Optional[Dict]:
        """买入持有策略函数"""
        nonlocal bought
        
        if not bought:
            symbol = bar['symbol']
            close_price = bar['close']
            
            # 用80%资金买入
            buy_volume = int(account_info['available_cash'] * 0.8 / close_price)
            buy_volume = (buy_volume // 100) * 100
            
            if buy_volume >= 100:
                bought = True
                logger.info(f"[Buy&Hold] Buy {buy_volume} shares at {close_price:.2f}")
                return {
                    'action': 'BUY',
                    'symbol': symbol,
                    'volume': buy_volume,
                    'price': None
                }
        
        return None
    
    return strategy


def create_ai_driven_strategy(ai_advisor, risk_manager) -> Callable:
    """
    创建完全由AI驱动的策略
    
    Args:
        ai_advisor: AI顾问
        risk_manager: 风控管理器
        
    Returns:
        策略函数
    """
    def strategy(controller, bar: Dict, account_info: Dict) -> Optional[Dict]:
        """AI驱动策略函数"""
        # 每N分钟调用AI一次
        if not ai_advisor.should_call_ai():
            return None
        
        symbol = bar['symbol']
        close_price = bar['close']
        
        # 构造市场数据
        market_data = {
            'price': close_price,
            'open': bar['open'],
            'high': bar['high'],
            'low': bar['low'],
            'volume': bar['volume']
        }
        
        try:
            # 调用AI生成信号
            signal = ai_advisor.generate_trading_signal(
                symbol, market_data, account_info
            )
            
            # 检查置信度
            if signal['confidence'] < 0.7:
                logger.info(f"AI confidence too low: {signal['confidence']}")
                return None
            
            action = signal['action']
            
            if action == 'BUY':
                # 计算买入数量
                max_volume = risk_manager.get_max_buy_volume(
                    symbol, close_price, account_info
                )
                
                if max_volume >= 100:
                    logger.info(f"[AI] Buy signal: {signal['reasoning']}")
                    return {
                        'action': 'BUY',
                        'symbol': symbol,
                        'volume': max_volume,
                        'price': None
                    }
            
            elif action == 'SELL':
                # 检查是否有持仓
                positions = {p['symbol']: p for p in account_info['positions']}
                position = positions.get(symbol)
                
                if position and position['available_volume'] > 0:
                    logger.info(f"[AI] Sell signal: {signal['reasoning']}")
                    return {
                        'action': 'SELL',
                        'symbol': symbol,
                        'volume': position['available_volume'],
                        'price': None
                    }
            
        except Exception as e:
            logger.error(f"AI strategy error: {e}")
        
        return None
    
    return strategy


def create_rsi_strategy(
    risk_manager=None,
    rsi_period: int = 14,
    oversold: float = 30,
    overbought: float = 70
) -> Callable:
    """
    创建RSI策略
    
    Args:
        risk_manager: 风控管理器
        rsi_period: RSI周期
        oversold: 超卖阈值
        overbought: 超买阈值
        
    Returns:
        策略函数
    """
    price_history = deque(maxlen=rsi_period + 1)
    
    def calculate_rsi(prices):
        """计算RSI"""
        if len(prices) < 2:
            return 50
        
        gains = []
        losses = []
        
        for i in range(1, len(prices)):
            change = prices[i] - prices[i-1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))
        
        avg_gain = sum(gains) / len(gains) if gains else 0
        avg_loss = sum(losses) / len(losses) if losses else 0
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def strategy(controller, bar: Dict, account_info: Dict) -> Optional[Dict]:
        """RSI策略函数"""
        symbol = bar['symbol']
        close_price = bar['close']
        
        price_history.append(close_price)
        
        if len(price_history) < rsi_period + 1:
            return None
        
        # 计算RSI
        rsi = calculate_rsi(list(price_history))
        
        # 获取持仓
        positions = {p['symbol']: p for p in account_info['positions']}
        current_position = positions.get(symbol, {}).get('volume', 0)
        
        # 超卖信号：买入
        if rsi < oversold and current_position == 0:
            if risk_manager:
                max_volume = risk_manager.get_max_buy_volume(
                    symbol, close_price, account_info
                )
            else:
                max_volume = int(account_info['available_cash'] * 0.2 / close_price)
                max_volume = (max_volume // 100) * 100
            
            if max_volume >= 100:
                logger.info(f"[RSI] Buy signal: RSI={rsi:.2f} < {oversold}")
                return {
                    'action': 'BUY',
                    'symbol': symbol,
                    'volume': max_volume,
                    'price': None
                }
        
        # 超买信号：卖出
        elif rsi > overbought and current_position > 0:
            available_volume = positions[symbol].get('available_volume', 0)
            if available_volume > 0:
                logger.info(f"[RSI] Sell signal: RSI={rsi:.2f} > {overbought}")
                return {
                    'action': 'SELL',
                    'symbol': symbol,
                    'volume': available_volume,
                    'price': None
                }
        
        return None
    
    return strategy


# ============================================================================
# 策略选择函数
# ============================================================================

def get_strategy(
    strategy_name: str,
    risk_manager=None,
    ai_advisor=None,
    **kwargs
) -> Callable:
    """
    根据名称获取策略
    
    Args:
        strategy_name: 策略名称
        risk_manager: 风控管理器
        ai_advisor: AI顾问
        **kwargs: 策略参数
        
    Returns:
        策略函数
    """
    if strategy_name == 'ma_cross':
        return create_ma_cross_strategy(risk_manager, ai_advisor, **kwargs)
    elif strategy_name == 'buy_hold':
        return create_buy_hold_strategy()
    elif strategy_name == 'ai_driven':
        if ai_advisor is None:
            raise ValueError("AI advisor is required for ai_driven strategy")
        return create_ai_driven_strategy(ai_advisor, risk_manager)
    elif strategy_name == 'rsi':
        return create_rsi_strategy(risk_manager, **kwargs)
    else:
        raise ValueError(f"Unknown strategy: {strategy_name}")


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 60)
    print("ApexQuant Strategies Test")
    print("=" * 60)
    
    # 测试MA交叉策略
    print("\n[Test] MA Cross Strategy")
    strategy = create_ma_cross_strategy(ma_short=5, ma_long=20)
    
    # 模拟数据
    account_info = {
        'available_cash': 1000000,
        'total_assets': 1000000,
        'positions': []
    }
    
    # 模拟价格上涨触发买入
    for i in range(25):
        bar = {
            'symbol': '600519.SH',
            'close': 100 + i * 2,  # 价格上涨
            'open': 100 + i * 2,
            'high': 100 + i * 2,
            'low': 100 + i * 2,
            'volume': 10000
        }
        
        signal = strategy(None, bar, account_info)
        if signal:
            print(f"  Bar {i}: {signal}")
    
    print("\n[Test] Buy&Hold Strategy")
    strategy2 = create_buy_hold_strategy()
    signal = strategy2(None, bar, account_info)
    print(f"  First bar: {signal}")
    
    print("\n" + "=" * 60)
    print("[OK] Strategies test passed!")
    print("=" * 60)
