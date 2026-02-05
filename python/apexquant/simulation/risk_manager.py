"""
ApexQuant Risk Manager
风控管理器
"""

import logging
from typing import Dict, Optional, List
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class RiskCheckResult(Enum):
    """风控检查结果"""
    PASS = "pass"           # 通过
    REJECT = "reject"       # 拒绝
    WARNING = "warning"     # 警告但通过


@dataclass
class RiskCheckInfo:
    """风控检查信息"""
    result: RiskCheckResult
    reason: str = ""
    
    def is_pass(self) -> bool:
        """是否通过"""
        return self.result == RiskCheckResult.PASS
    
    def is_reject(self) -> bool:
        """是否拒绝"""
        return self.result == RiskCheckResult.REJECT


class RiskManager:
    """风控管理器"""
    
    def __init__(self, config: dict):
        """
        初始化风控管理器
        
        Args:
            config: 风控配置字典
        """
        self.enabled = config.get("enable_risk_control", True)
        
        # 持仓限制
        self.max_single_position_pct = config.get("max_single_position_pct", 0.3)
        self.max_total_position_pct = config.get("max_total_position_pct", 0.95)
        
        # 下单限制
        self.max_single_order_amount = config.get("max_single_order_amount", 50000.0)
        
        # 止损止盈
        self.daily_loss_limit_pct = config.get("daily_loss_limit_pct", 0.05)
        self.stop_loss_pct = config.get("stop_loss_pct", 0.1)
        self.take_profit_pct = config.get("take_profit_pct", 0.2)
        
        # 日内损益跟踪
        self.daily_start_assets = 0.0
        self.daily_pnl = 0.0
        
        logger.info(f"Risk manager initialized (enabled={self.enabled})")
    
    def set_daily_start_assets(self, assets: float) -> None:
        """
        设置日初资产
        
        Args:
            assets: 日初总资产
        """
        self.daily_start_assets = assets
        self.daily_pnl = 0.0
        logger.debug(f"Daily start assets set to {assets:.2f}")
    
    def update_daily_pnl(self, current_assets: float) -> None:
        """
        更新日内盈亏
        
        Args:
            current_assets: 当前总资产
        """
        if self.daily_start_assets > 0:
            self.daily_pnl = current_assets - self.daily_start_assets
    
    def check_order(
        self,
        symbol: str,
        side: str,
        price: float,
        volume: int,
        current_position: int,
        available_cash: float,
        total_assets: float,
        current_positions: Dict[str, dict]
    ) -> RiskCheckInfo:
        """
        检查订单是否符合风控规则
        
        Args:
            symbol: 股票代码
            side: 买卖方向 'buy' or 'sell'
            price: 价格
            volume: 数量
            current_position: 当前持仓
            available_cash: 可用资金
            total_assets: 总资产
            current_positions: 当前所有持仓 {symbol: {volume: int, value: float}}
            
        Returns:
            风控检查结果
        """
        if not self.enabled:
            return RiskCheckInfo(RiskCheckResult.PASS, "Risk control disabled")
        
        # 1. 检查日亏损限制
        daily_loss_check = self._check_daily_loss_limit(total_assets)
        if daily_loss_check.is_reject():
            return daily_loss_check
        
        # 2. 检查订单金额限制
        order_amount = price * volume
        if order_amount > self.max_single_order_amount:
            return RiskCheckInfo(
                RiskCheckResult.REJECT,
                f"Order amount {order_amount:.2f} exceeds max {self.max_single_order_amount:.2f}"
            )
        
        # 3. 买入时检查持仓限制
        if side.lower() == 'buy':
            # 检查资金是否足够
            if order_amount > available_cash:
                return RiskCheckInfo(
                    RiskCheckResult.REJECT,
                    f"Insufficient cash: need {order_amount:.2f}, available {available_cash:.2f}"
                )
            
            # 检查单只股票持仓比例
            future_position_value = (current_position + volume) * price
            single_position_pct = future_position_value / total_assets
            
            if single_position_pct > self.max_single_position_pct:
                return RiskCheckInfo(
                    RiskCheckResult.REJECT,
                    f"Single position ratio {single_position_pct:.2%} exceeds max {self.max_single_position_pct:.2%}"
                )
            
            # 检查总持仓比例
            total_position_value = sum(pos['value'] for pos in current_positions.values())
            total_position_value += order_amount  # 加上本次买入金额
            total_position_pct = total_position_value / total_assets
            
            if total_position_pct > self.max_total_position_pct:
                return RiskCheckInfo(
                    RiskCheckResult.REJECT,
                    f"Total position ratio {total_position_pct:.2%} exceeds max {self.max_total_position_pct:.2%}"
                )
        
        # 4. 卖出时检查持仓是否足够
        elif side.lower() == 'sell':
            if volume > current_position:
                return RiskCheckInfo(
                    RiskCheckResult.REJECT,
                    f"Insufficient position: need {volume}, available {current_position}"
                )
        
        return RiskCheckInfo(RiskCheckResult.PASS, "Risk check passed")
    
    def _check_daily_loss_limit(self, current_assets: float) -> RiskCheckInfo:
        """
        检查日亏损限制
        
        Args:
            current_assets: 当前总资产
            
        Returns:
            检查结果
        """
        if self.daily_start_assets <= 0:
            return RiskCheckInfo(RiskCheckResult.PASS, "Daily start assets not set")
        
        self.update_daily_pnl(current_assets)
        
        if self.daily_pnl < 0:
            loss_pct = abs(self.daily_pnl) / self.daily_start_assets
            
            if loss_pct >= self.daily_loss_limit_pct:
                return RiskCheckInfo(
                    RiskCheckResult.REJECT,
                    f"Daily loss {loss_pct:.2%} exceeds limit {self.daily_loss_limit_pct:.2%}"
                )
        
        return RiskCheckInfo(RiskCheckResult.PASS, "Daily loss within limit")
    
    def check_position_stop_loss(
        self,
        symbol: str,
        avg_cost: float,
        current_price: float
    ) -> RiskCheckInfo:
        """
        检查持仓是否触发止损
        
        Args:
            symbol: 股票代码
            avg_cost: 平均成本
            current_price: 当前价格
            
        Returns:
            检查结果
        """
        if not self.enabled or avg_cost <= 0:
            return RiskCheckInfo(RiskCheckResult.PASS)
        
        pnl_pct = (current_price - avg_cost) / avg_cost
        
        # 止损检查
        if pnl_pct <= -self.stop_loss_pct:
            return RiskCheckInfo(
                RiskCheckResult.WARNING,
                f"{symbol} hit stop loss: {pnl_pct:.2%} <= -{self.stop_loss_pct:.2%}"
            )
        
        # 止盈检查
        if pnl_pct >= self.take_profit_pct:
            return RiskCheckInfo(
                RiskCheckResult.WARNING,
                f"{symbol} hit take profit: {pnl_pct:.2%} >= {self.take_profit_pct:.2%}"
            )
        
        return RiskCheckInfo(RiskCheckResult.PASS)
    
    def get_position_alerts(
        self,
        positions: Dict[str, dict]
    ) -> List[str]:
        """
        获取持仓风险警报
        
        Args:
            positions: 持仓字典 {symbol: {volume, avg_cost, current_price, value}}
            
        Returns:
            警报列表
        """
        if not self.enabled:
            return []
        
        alerts = []
        
        for symbol, pos in positions.items():
            avg_cost = pos.get('avg_cost', 0)
            current_price = pos.get('current_price', 0)
            
            if avg_cost > 0 and current_price > 0:
                check_result = self.check_position_stop_loss(symbol, avg_cost, current_price)
                
                if check_result.result == RiskCheckResult.WARNING:
                    alerts.append(check_result.reason)
        
        return alerts
    
    def get_risk_metrics(self, total_assets: float, positions: Dict[str, dict]) -> dict:
        """
        获取风控指标
        
        Args:
            total_assets: 总资产
            positions: 持仓字典
            
        Returns:
            风控指标字典
        """
        total_position_value = sum(pos.get('value', 0) for pos in positions.values())
        position_pct = total_position_value / total_assets if total_assets > 0 else 0
        
        daily_pnl_pct = self.daily_pnl / self.daily_start_assets if self.daily_start_assets > 0 else 0
        
        return {
            "enabled": self.enabled,
            "total_position_pct": position_pct,
            "daily_pnl": self.daily_pnl,
            "daily_pnl_pct": daily_pnl_pct,
            "daily_loss_limit_pct": self.daily_loss_limit_pct,
            "max_single_position_pct": self.max_single_position_pct,
            "max_total_position_pct": self.max_total_position_pct,
        }
