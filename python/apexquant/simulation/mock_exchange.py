"""
MockExchange - 纯Python模拟交易所
当C++模块不可用时的备选方案
"""

import logging
import time
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class OrderSide(Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"


class OrderStatus(Enum):
    PENDING = "PENDING"
    FILLED = "FILLED"
    PARTIAL_FILLED = "PARTIAL_FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


@dataclass
class Position:
    symbol: str
    volume: int = 0
    available_volume: int = 0
    avg_cost: float = 0.0
    market_value: float = 0.0
    unrealized_pnl: float = 0.0


@dataclass
class Order:
    order_id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    price: float
    volume: int
    filled_volume: int = 0
    status: OrderStatus = OrderStatus.PENDING
    timestamp: int = 0


@dataclass
class Trade:
    trade_id: str
    order_id: str
    symbol: str
    side: str
    price: float
    volume: int
    commission: float
    timestamp: int


class MockExchange:
    """纯Python模拟交易所"""

    def __init__(self, account_id: str, initial_capital: float):
        self.account_id = account_id
        self.initial_capital = initial_capital
        self.available_cash = initial_capital
        self.frozen_cash = 0.0

        self.positions: Dict[str, Position] = {}
        self.orders: Dict[str, Order] = {}
        self.trades: List[Trade] = []
        self.equity_curve: List[Dict] = []

        self._order_counter = 0
        self._trade_counter = 0

        # 费率
        self.commission_rate = 0.00025  # 万2.5
        self.stamp_tax_rate = 0.001     # 千一（仅卖出）
        self.slippage_rate = 0.0001     # 万一

        logger.info(f"MockExchange initialized: {account_id}, capital={initial_capital}")

    def get_account_id(self) -> str:
        return self.account_id

    def get_available_cash(self) -> float:
        return self.available_cash

    def get_frozen_cash(self) -> float:
        return self.frozen_cash

    def get_total_assets(self) -> float:
        """计算总资产"""
        position_value = sum(p.market_value for p in self.positions.values())
        return self.available_cash + self.frozen_cash + position_value

    def get_position(self, symbol: str) -> Optional[Dict]:
        """获取单个持仓"""
        pos = self.positions.get(symbol)
        if pos:
            return {
                'symbol': pos.symbol,
                'volume': pos.volume,
                'available_volume': pos.available_volume,
                'avg_cost': pos.avg_cost,
                'market_value': pos.market_value,
                'unrealized_pnl': pos.unrealized_pnl
            }
        return None

    def get_all_positions(self) -> List[Dict]:
        """获取所有持仓"""
        return [self.get_position(s) for s in self.positions if self.positions[s].volume > 0]

    def get_pending_orders(self) -> List[Dict]:
        """获取待成交订单"""
        result = []
        for order in self.orders.values():
            if order.status == OrderStatus.PENDING:
                result.append({
                    'order_id': order.order_id,
                    'symbol': order.symbol,
                    'side': order.side.value,
                    'order_type': order.order_type.value,
                    'price': order.price,
                    'volume': order.volume,
                    'filled_volume': order.filled_volume,
                    'status': order.status.value
                })
        return result

    def get_trades(self) -> List[Dict]:
        """获取成交记录"""
        return [
            {
                'trade_id': t.trade_id,
                'order_id': t.order_id,
                'symbol': t.symbol,
                'side': t.side,
                'price': t.price,
                'volume': t.volume,
                'commission': t.commission,
                'timestamp': t.timestamp
            }
            for t in self.trades
        ]

    def get_equity_curve(self) -> List[Dict]:
        """获取权益曲线"""
        return self.equity_curve

    def submit_order(self, order) -> str:
        """提交订单"""
        self._order_counter += 1
        timestamp = int(time.time() * 1000)

        # 创建订单ID
        order_id = f"ORDER_{timestamp}_{order.symbol}_{self._order_counter}"

        # 解析订单参数
        symbol = order.symbol
        side = OrderSide.BUY if order.side.name == "BUY" else OrderSide.SELL
        order_type = OrderType.LIMIT if order.order_type.name == "LIMIT" else OrderType.MARKET
        price = order.price
        volume = order.volume

        # 计算所需资金
        if side == OrderSide.BUY:
            required_cash = price * volume * (1 + self.commission_rate)
            if required_cash > self.available_cash:
                logger.warning(f"Insufficient cash for order {order_id}")
                return ""

            # 冻结资金
            self.available_cash -= required_cash
            self.frozen_cash += required_cash
        else:
            # 卖出：检查持仓
            pos = self.positions.get(symbol)
            if not pos or pos.available_volume < volume:
                logger.warning(f"Insufficient position for order {order_id}")
                return ""

            # 冻结持仓
            pos.available_volume -= volume

        # 创建订单
        new_order = Order(
            order_id=order_id,
            symbol=symbol,
            side=side,
            order_type=order_type,
            price=price,
            volume=volume,
            timestamp=timestamp
        )
        self.orders[order_id] = new_order

        # 立即撮合（简化处理）
        self._match_order(new_order)

        return order_id

    def _match_order(self, order: Order):
        """撮合订单（简化版本，假设立即全部成交）"""
        timestamp = int(time.time() * 1000)

        # 计算滑点后的成交价
        if order.side == OrderSide.BUY:
            fill_price = order.price * (1 + self.slippage_rate)
        else:
            fill_price = order.price * (1 - self.slippage_rate)

        # 计算手续费
        commission = fill_price * order.volume * self.commission_rate
        if order.side == OrderSide.SELL:
            commission += fill_price * order.volume * self.stamp_tax_rate

        # 更新订单状态
        order.filled_volume = order.volume
        order.status = OrderStatus.FILLED

        # 创建成交记录
        self._trade_counter += 1
        trade = Trade(
            trade_id=f"TRADE_{timestamp}_{self._trade_counter}",
            order_id=order.order_id,
            symbol=order.symbol,
            side=order.side.value,
            price=fill_price,
            volume=order.volume,
            commission=commission,
            timestamp=timestamp
        )
        self.trades.append(trade)

        # 更新持仓和资金
        if order.side == OrderSide.BUY:
            # 解冻并扣除资金
            cost = fill_price * order.volume + commission
            self.frozen_cash -= order.price * order.volume * (1 + self.commission_rate)
            self.available_cash += order.price * order.volume * (1 + self.commission_rate) - cost

            # 更新持仓
            if order.symbol not in self.positions:
                self.positions[order.symbol] = Position(symbol=order.symbol)

            pos = self.positions[order.symbol]
            total_cost = pos.avg_cost * pos.volume + fill_price * order.volume
            pos.volume += order.volume
            pos.available_volume += order.volume  # T+1规则应该是0，这里简化
            pos.avg_cost = total_cost / pos.volume if pos.volume > 0 else 0
            pos.market_value = pos.volume * fill_price
        else:
            # 卖出
            pos = self.positions[order.symbol]
            pos.volume -= order.volume

            # 计算收益
            proceeds = fill_price * order.volume - commission
            self.available_cash += proceeds

            if pos.volume > 0:
                pos.market_value = pos.volume * fill_price
            else:
                pos.market_value = 0
                pos.avg_cost = 0

        # 记录权益
        self.equity_curve.append({
            'timestamp': timestamp,
            'total_assets': self.get_total_assets(),
            'available_cash': self.available_cash,
            'position_value': sum(p.market_value for p in self.positions.values())
        })

    def cancel_order(self, order_id: str) -> bool:
        """撤销订单"""
        order = self.orders.get(order_id)
        if not order or order.status != OrderStatus.PENDING:
            return False

        order.status = OrderStatus.CANCELLED

        # 解冻资金或持仓
        if order.side == OrderSide.BUY:
            unfrozen = order.price * (order.volume - order.filled_volume) * (1 + self.commission_rate)
            self.frozen_cash -= unfrozen
            self.available_cash += unfrozen
        else:
            pos = self.positions.get(order.symbol)
            if pos:
                pos.available_volume += order.volume - order.filled_volume

        return True

    def update_price(self, symbol: str, price: float):
        """更新股票价格（用于计算市值）"""
        pos = self.positions.get(symbol)
        if pos and pos.volume > 0:
            pos.market_value = pos.volume * price
            pos.unrealized_pnl = pos.market_value - pos.avg_cost * pos.volume

    def on_tick(self, tick):
        """处理Tick数据"""
        symbol = tick.get('symbol', '')
        price = tick.get('price', tick.get('close', 0))
        if symbol and price > 0:
            self.update_price(symbol, price)

    def update_daily(self):
        """日终处理（T+1解冻等）"""
        for pos in self.positions.values():
            pos.available_volume = pos.volume
