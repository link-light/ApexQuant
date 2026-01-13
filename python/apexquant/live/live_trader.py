"""
实盘交易管理器
"""

import time
import threading
from typing import Dict, List, Optional, Callable
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from apexquant.live.signal_generator import AISignalGenerator
from apexquant.live.rl_agent import RLTradingAgent
from apexquant.data import AKShareWrapper


class LiveTrader:
    """实盘交易管理器"""
    
    def __init__(self,
                 trading_interface,
                 signal_generator: Optional[AISignalGenerator] = None,
                 rl_agent: Optional[RLTradingAgent] = None,
                 data_wrapper: Optional[AKShareWrapper] = None):
        """
        初始化
        
        Args:
            trading_interface: 交易接口（C++ 或 Python）
            signal_generator: AI 信号生成器
            rl_agent: RL 交易代理
            data_wrapper: 数据接口
        """
        self.trading = trading_interface
        self.signal_gen = signal_generator
        self.rl_agent = rl_agent
        self.data_wrapper = data_wrapper or AKShareWrapper()
        
        self.running = False
        self.thread = None
        
        self.watch_list = []
        self.positions = {}
        self.orders = {}
        
        self.risk_limits = {
            'max_position_size': 0.3,      # 单仓位最大 30%
            'max_total_positions': 5,       # 最多 5 个持仓
            'stop_loss': -0.05,             # 止损 -5%
            'take_profit': 0.15,            # 止盈 15%
            'max_daily_loss': -0.10         # 单日最大亏损 -10%
        }
        
        self.daily_pnl = 0.0
        self.initial_value = 0.0
        
        # 回调
        self.on_signal_callback = None
        self.on_order_callback = None
        self.on_trade_callback = None
    
    def set_watch_list(self, symbols: List[str]):
        """设置监控列表"""
        self.watch_list = symbols
    
    def set_risk_limits(self, limits: Dict):
        """设置风控参数"""
        self.risk_limits.update(limits)
    
    def start(self, interval: int = 60):
        """
        启动实盘交易
        
        Args:
            interval: 检查间隔（秒）
        """
        if self.running:
            print("交易器已在运行")
            return
        
        # 连接交易接口
        if hasattr(self.trading, 'connect'):
            if not self.trading.connect(""):
                print("连接交易接口失败")
                return
        
        if hasattr(self.trading, 'login'):
            if not self.trading.login("", ""):
                print("登录失败")
                return
        
        # 获取初始账户价值
        account = self.trading.query_account()
        self.initial_value = account.total_assets
        print(f"初始资产: {self.initial_value:.2f}")
        
        self.running = True
        self.thread = threading.Thread(target=self._trading_loop, args=(interval,))
        self.thread.start()
        
        print("实盘交易已启动")
    
    def stop(self):
        """停止实盘交易"""
        if not self.running:
            return
        
        self.running = False
        
        if self.thread:
            self.thread.join()
        
        if hasattr(self.trading, 'disconnect'):
            self.trading.disconnect()
        
        print("实盘交易已停止")
    
    def _trading_loop(self, interval: int):
        """交易循环"""
        while self.running:
            try:
                # 1. 更新持仓
                self._update_positions()
                
                # 2. 风控检查
                if not self._risk_check():
                    print("⚠ 触发风控，暂停交易")
                    time.sleep(interval)
                    continue
                
                # 3. 生成信号
                signals = self._generate_signals()
                
                # 4. 执行交易
                self._execute_signals(signals)
                
                # 5. 处理挂单
                if hasattr(self.trading, 'process_orders'):
                    self.trading.process_orders()
                
            except Exception as e:
                print(f"交易循环错误: {e}")
            
            time.sleep(interval)
    
    def _update_positions(self):
        """更新持仓信息"""
        try:
            positions = self.trading.query_positions()
            self.positions = {pos.symbol: pos for pos in positions}
            
            # 更新每日盈亏
            account = self.trading.query_account()
            self.daily_pnl = account.total_assets - self.initial_value
            
        except Exception as e:
            print(f"更新持仓失败: {e}")
    
    def _risk_check(self) -> bool:
        """风控检查"""
        # 1. 单日亏损限制
        account = self.trading.query_account()
        daily_loss_pct = self.daily_pnl / self.initial_value
        
        if daily_loss_pct < self.risk_limits['max_daily_loss']:
            print(f"触发单日止损: {daily_loss_pct:.2%}")
            return False
        
        # 2. 持仓数量限制
        if len(self.positions) >= self.risk_limits['max_total_positions']:
            print("持仓数量已达上限")
            return False
        
        # 3. 单仓位止损/止盈
        for symbol, pos in self.positions.items():
            if pos.total_volume == 0:
                continue
            
            pnl_ratio = pos.profit_loss_ratio
            
            # 止损
            if pnl_ratio < self.risk_limits['stop_loss']:
                print(f"{symbol} 触发止损 ({pnl_ratio:.2%})，平仓")
                self._close_position(symbol)
            
            # 止盈
            elif pnl_ratio > self.risk_limits['take_profit']:
                print(f"{symbol} 触发止盈 ({pnl_ratio:.2%})，平仓")
                self._close_position(symbol)
        
        return True
    
    def _generate_signals(self) -> Dict:
        """生成交易信号"""
        signals = {}
        
        for symbol in self.watch_list:
            try:
                # 获取数据
                data = self.data_wrapper.get_historical_data(
                    symbol, 
                    start_date=None,
                    end_date=None
                )
                
                if data is None or data.empty:
                    continue
                
                current_price = data['close'].iloc[-1]
                position = self.positions.get(symbol)
                
                # AI 信号
                if self.signal_gen:
                    action, confidence, reason = self.signal_gen.generate_signal(
                        symbol, current_price, data, None, position
                    )
                    
                    signals[symbol] = {
                        'action': action,
                        'confidence': confidence,
                        'reason': reason,
                        'price': current_price
                    }
                
                # RL 信号（可选）
                if self.rl_agent:
                    state = self.rl_agent.get_state(data, position)
                    rl_action = self.rl_agent.select_action(state, deterministic=True)
                    
                    # 转换动作
                    rl_action_str = ['hold', 'buy', 'sell'][rl_action]
                    
                    # 融合 AI 和 RL 信号（简单投票）
                    if symbol in signals:
                        if signals[symbol]['action'] == rl_action_str:
                            signals[symbol]['confidence'] = min(1.0, signals[symbol]['confidence'] + 0.2)
                    else:
                        signals[symbol] = {
                            'action': rl_action_str,
                            'confidence': 0.6,
                            'reason': 'RL 决策',
                            'price': current_price
                        }
            
            except Exception as e:
                print(f"生成 {symbol} 信号失败: {e}")
        
        return signals
    
    def _execute_signals(self, signals: Dict):
        """执行交易信号"""
        account = self.trading.query_account()
        available_cash = account.available_cash
        
        for symbol, signal in signals.items():
            action = signal['action']
            confidence = signal['confidence']
            price = signal['price']
            
            # 置信度过滤
            if confidence < 0.6:
                continue
            
            # 回调
            if self.on_signal_callback:
                self.on_signal_callback(symbol, signal)
            
            # 执行动作
            if action == 'buy':
                self._open_position(symbol, price, available_cash)
            elif action == 'sell':
                self._close_position(symbol)
    
    def _open_position(self, symbol: str, price: float, available_cash: float):
        """开仓"""
        # 检查是否已有持仓
        if symbol in self.positions and self.positions[symbol].total_volume > 0:
            return
        
        # 计算仓位
        max_position_value = self.initial_value * self.risk_limits['max_position_size']
        position_value = min(max_position_value, available_cash * 0.9)
        volume = int(position_value / price / 100) * 100  # 整手
        
        if volume < 100:
            return
        
        # 提交订单
        try:
            # 构造订单（需要根据实际接口调整）
            if hasattr(self.trading, 'submit_order'):
                from apexquant_core import Order  # 假设有这个
                order = Order()
                order.symbol = symbol
                order.direction = 0  # BUY
                order.price = price
                order.volume = volume
                
                order_id = self.trading.submit_order(order)
                print(f"开仓 {symbol}: 价格 {price:.2f}, 数量 {volume}")
                
                if self.on_order_callback:
                    self.on_order_callback(symbol, 'buy', price, volume, order_id)
            
        except Exception as e:
            print(f"开仓 {symbol} 失败: {e}")
    
    def _close_position(self, symbol: str):
        """平仓"""
        if symbol not in self.positions:
            return
        
        pos = self.positions[symbol]
        if pos.total_volume == 0:
            return
        
        # 提交卖单
        try:
            if hasattr(self.trading, 'submit_order'):
                from apexquant_core import Order
                order = Order()
                order.symbol = symbol
                order.direction = 1  # SELL
                order.price = pos.current_price
                order.volume = pos.total_volume
                
                order_id = self.trading.submit_order(order)
                print(f"平仓 {symbol}: 价格 {pos.current_price:.2f}, 数量 {pos.total_volume}")
                
                if self.on_order_callback:
                    self.on_order_callback(symbol, 'sell', pos.current_price, pos.total_volume, order_id)
        
        except Exception as e:
            print(f"平仓 {symbol} 失败: {e}")
    
    def get_status(self) -> Dict:
        """获取交易状态"""
        account = self.trading.query_account()
        
        return {
            'running': self.running,
            'total_assets': account.total_assets,
            'available_cash': account.available_cash,
            'market_value': account.market_value,
            'profit_loss': account.profit_loss,
            'daily_pnl': self.daily_pnl,
            'positions_count': len(self.positions),
            'positions': [
                {
                    'symbol': pos.symbol,
                    'volume': pos.total_volume,
                    'avg_price': pos.avg_price,
                    'current_price': pos.current_price,
                    'pnl': pos.profit_loss,
                    'pnl_ratio': pos.profit_loss_ratio
                }
                for pos in self.positions.values()
                if pos.total_volume > 0
            ]
        }

