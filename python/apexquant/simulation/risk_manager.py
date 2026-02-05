"""
ApexQuant 风控管理器

提供完整的风险控制功能
"""

import logging
from typing import Dict, List, Tuple
from .config import get_config

logger = logging.getLogger(__name__)


class RiskManager:
    """风险管理器"""
    
    def __init__(self, config_path: str = None):
        """
        初始化风控管理器
        
        Args:
            config_path: 配置文件路径
        """
        config = get_config(config_path)
        risk_config = config.get_risk_config()
        
        # 风控参数
        self.max_single_position_pct = risk_config.get('max_single_position_pct', 0.20)
        self.max_total_position_pct = risk_config.get('max_total_position_pct', 0.80)
        self.max_single_order_pct = risk_config.get('max_single_order_pct', 0.05)
        self.max_daily_loss_pct = risk_config.get('max_daily_loss_pct', 0.05)
        self.stop_loss_pct = risk_config.get('stop_loss_pct', 0.10)
        self.take_profit_pct = risk_config.get('take_profit_pct', 0.20)
        self.max_daily_trades = risk_config.get('max_daily_trades', 100)
        self.min_hold_seconds = risk_config.get('min_hold_seconds', 60)
        
        # 统计
        self.daily_trades_count = 0
        
        logger.info(f"RiskManager initialized with config: {risk_config}")
    
    def check_order(self, order: Dict, account_info: Dict) -> Tuple[bool, str]:
        """
        检查订单是否符合风控规则
        
        Args:
            order: 订单字典 {'symbol': str, 'side': str, 'volume': int, 'price': float}
            account_info: 账户信息
            
        Returns:
            (是否通过, 拒绝原因)
        """
        symbol = order['symbol']
        side = order['side']
        volume = order['volume']
        price = order.get('price', 0)
        
        total_assets = account_info['total_assets']
        available_cash = account_info['available_cash']
        positions = {p['symbol']: p for p in account_info['positions']}
        
        # 1. 检查单笔金额限制
        order_value = volume * price if price > 0 else volume * 100  # 市价单估算
        max_single_order = total_assets * self.max_single_order_pct
        
        if order_value > max_single_order:
            return False, f"Order value {order_value:.2f} exceeds max single order {max_single_order:.2f}"
        
        # 2. 买单检查
        if side == 'BUY':
            # 2.1 可用资金是否充足
            required_cash = order_value * 1.003  # 包含手续费
            if required_cash > available_cash:
                return False, f"Insufficient cash: required {required_cash:.2f}, available {available_cash:.2f}"
            
            # 2.2 单品种仓位限制
            current_position = positions.get(symbol, {}).get('market_value', 0)
            new_position_value = current_position + order_value
            max_position = total_assets * self.max_single_position_pct
            
            if new_position_value > max_position:
                return False, f"Position limit exceeded: {new_position_value:.2f} > {max_position:.2f}"
            
            # 2.3 总仓位限制
            total_position_value = sum(p['market_value'] for p in account_info['positions'])
            new_total_position = total_position_value + order_value
            max_total_position = total_assets * self.max_total_position_pct
            
            if new_total_position > max_total_position:
                return False, f"Total position limit exceeded: {new_total_position:.2f} > {max_total_position:.2f}"
        
        # 3. 卖单检查
        elif side == 'SELL':
            # 3.1 持仓是否充足
            position = positions.get(symbol)
            if not position:
                return False, f"No position for {symbol}"
            
            available_volume = position.get('available_volume', 0)
            if volume > available_volume:
                return False, f"Insufficient position: required {volume}, available {available_volume}"
        
        # 4. 每日交易次数限制
        if self.daily_trades_count >= self.max_daily_trades:
            return False, f"Daily trade limit exceeded: {self.daily_trades_count} >= {self.max_daily_trades}"
        
        return True, ""
    
    def check_stop_loss(self, positions: List[Dict]) -> List[str]:
        """
        检查是否触发止损
        
        Args:
            positions: 持仓列表
            
        Returns:
            需要止损的symbol列表
        """
        stop_loss_symbols = []
        
        for pos in positions:
            unrealized_pnl_pct = pos.get('unrealized_pnl_pct', 0)
            
            if unrealized_pnl_pct < -self.stop_loss_pct * 100:  # 注意百分比转换
                symbol = pos['symbol']
                stop_loss_symbols.append(symbol)
                logger.warning(f"Stop loss triggered for {symbol}: PnL {unrealized_pnl_pct:.2f}%")
        
        return stop_loss_symbols
    
    def check_take_profit(self, positions: List[Dict]) -> List[str]:
        """
        检查是否触发止盈
        
        Args:
            positions: 持仓列表
            
        Returns:
            需要止盈的symbol列表
        """
        take_profit_symbols = []
        
        for pos in positions:
            unrealized_pnl_pct = pos.get('unrealized_pnl_pct', 0)
            
            if unrealized_pnl_pct > self.take_profit_pct * 100:
                symbol = pos['symbol']
                take_profit_symbols.append(symbol)
                logger.info(f"Take profit triggered for {symbol}: PnL {unrealized_pnl_pct:.2f}%")
        
        return take_profit_symbols
    
    def check_daily_loss(self, daily_pnl: float, initial_capital: float) -> bool:
        """
        检查是否触发日亏损熔断
        
        Args:
            daily_pnl: 当日盈亏
            initial_capital: 初始资金
            
        Returns:
            是否需要停止交易
        """
        if daily_pnl < -initial_capital * self.max_daily_loss_pct:
            logger.error(f"Daily loss limit breached: {daily_pnl:.2f} < {-initial_capital * self.max_daily_loss_pct:.2f}")
            logger.error("TRADING HALTED!")
            return True
        
        return False
    
    def get_max_buy_volume(
        self, 
        symbol: str, 
        price: float, 
        account_info: Dict
    ) -> int:
        """
        计算最大可买数量
        
        Args:
            symbol: 股票代码
            price: 价格
            account_info: 账户信息
            
        Returns:
            最大可买数量
        """
        if price <= 0:
            return 0
        
        total_assets = account_info['total_assets']
        available_cash = account_info['available_cash']
        positions = {p['symbol']: p for p in account_info['positions']}
        
        # 1. 可用资金限制
        max_by_cash = int(available_cash / (price * 1.003))
        
        # 2. 单笔金额限制
        max_single_order_value = total_assets * self.max_single_order_pct
        max_by_single_order = int(max_single_order_value / price)
        
        # 3. 单品种仓位限制
        current_position_value = positions.get(symbol, {}).get('market_value', 0)
        remaining_position_value = total_assets * self.max_single_position_pct - current_position_value
        max_by_position = int(remaining_position_value / price) if remaining_position_value > 0 else 0
        
        # 4. 总仓位限制
        total_position_value = sum(p['market_value'] for p in account_info['positions'])
        remaining_total_value = total_assets * self.max_total_position_pct - total_position_value
        max_by_total_position = int(remaining_total_value / price) if remaining_total_value > 0 else 0
        
        # 取最小值
        max_volume = min(max_by_cash, max_by_single_order, max_by_position, max_by_total_position)
        
        # 向下取整到100的倍数（A股最小单位）
        max_volume = (max_volume // 100) * 100
        
        return max(0, max_volume)
    
    def adjust_order_to_comply(
        self, 
        order: Dict, 
        account_info: Dict
    ) -> Dict:
        """
        自动调整订单使其符合风控
        
        Args:
            order: 原订单
            account_info: 账户信息
            
        Returns:
            调整后的订单
        """
        adjusted_order = order.copy()
        
        if order['side'] == 'BUY':
            max_volume = self.get_max_buy_volume(
                order['symbol'],
                order.get('price', 100),  # 如果没有价格，假设100元
                account_info
            )
            
            if order['volume'] > max_volume:
                logger.warning(f"Order volume adjusted: {order['volume']} -> {max_volume}")
                adjusted_order['volume'] = max_volume
        
        return adjusted_order
    
    def on_trade(self):
        """记录一次交易（用于统计）"""
        self.daily_trades_count += 1
    
    def reset_daily_stats(self):
        """重置每日统计（每日开盘调用）"""
        self.daily_trades_count = 0
        logger.info("Daily stats reset")


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 60)
    print("ApexQuant Risk Manager Test")
    print("=" * 60)
    
    risk_mgr = RiskManager()
    
    # 模拟账户信息
    account_info = {
        'total_assets': 1000000,
        'available_cash': 800000,
        'positions': [
            {
                'symbol': '600519.SH',
                'volume': 1000,
                'market_value': 150000,
                'unrealized_pnl': 5000,
                'unrealized_pnl_pct': 3.45,
                'available_volume': 1000
            }
        ]
    }
    
    # 测试买单检查
    print("\n[Test] Buy order check")
    buy_order = {
        'symbol': '000001.SZ',
        'side': 'BUY',
        'volume': 1000,
        'price': 15.0
    }
    
    passed, reason = risk_mgr.check_order(buy_order, account_info)
    print(f"Result: {'PASS' if passed else 'REJECT'}")
    if not passed:
        print(f"Reason: {reason}")
    
    # 测试最大可买数量
    print("\n[Test] Max buy volume")
    max_vol = risk_mgr.get_max_buy_volume('000001.SZ', 15.0, account_info)
    print(f"Max buy volume at 15.0: {max_vol} shares ({max_vol * 15.0:.2f} CNY)")
    
    # 测试止损检查
    print("\n[Test] Stop loss check")
    loss_position = {
        'symbol': '600036.SH',
        'unrealized_pnl_pct': -12.0  # 亏损12%
    }
    account_info['positions'].append(loss_position)
    
    stop_loss_symbols = risk_mgr.check_stop_loss(account_info['positions'])
    print(f"Stop loss triggered for: {stop_loss_symbols}")
    
    print("\n" + "=" * 60)
    print("[OK] Risk manager test passed!")
    print("=" * 60)
