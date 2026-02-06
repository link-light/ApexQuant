"""
ApexQuant Simulation Controller
模拟盘控制器 - 核心协调模块
"""

import sys
from pathlib import Path
import datetime
import logging
from typing import Optional, List, Dict, Callable, Any, TYPE_CHECKING
import pandas as pd

# 导入C++模块
if TYPE_CHECKING:
    import apexquant_simulation as sim_cpp
    import apexquant_core as core_cpp
else:
    try:
        import apexquant_simulation as sim_cpp
        import apexquant_core as core_cpp
        CPP_AVAILABLE = True
    except ImportError as e:
        print(f"警告: C++ 核心模块未加载: {e}")
        print("某些功能可能不可用。请确保已编译C++模块。")
        CPP_AVAILABLE = False
        sim_cpp = None  # type: ignore
        core_cpp = None  # type: ignore

# 导入Python模块
from .database import DatabaseManager
from .config import SimulationConfig, get_config
from .trading_calendar import TradingCalendar, get_calendar
from .data_source import SimulationDataSource
from .risk_manager import RiskManager
from .performance_analyzer import PerformanceAnalyzer

logger = logging.getLogger(__name__)


class SimulationMode:
    """模拟模式"""
    BACKTEST = "backtest"     # 回测模式
    REALTIME = "realtime"     # 实时模拟模式


class SimulationController:
    """模拟盘控制器"""
    
    def __init__(self, config: Optional[SimulationConfig] = None):
        """
        初始化控制器
        
        Args:
            config: 配置对象，默认使用全局配置
        """
        self.config = config or get_config()
        self.calendar = get_calendar()
        
        # 获取配置
        account_config = self.config.get_account_config()
        risk_config = self.config.get_risk_config()
        data_config = self.config.get_data_source_config()
        
        # 初始化账户ID和初始资金
        self.account_id = account_config.get("account_id", "simulation_001")
        self.initial_capital = account_config.get("initial_capital", 100000.0)
        
        # 初始化模拟交易所
        if CPP_AVAILABLE and sim_cpp is not None:
            self.exchange = sim_cpp.SimulatedExchange(
                self.account_id,
                self.initial_capital
            )
            self.use_cpp = True
        else:
            # 使用纯Python Mock交易所
            from .mock_exchange import MockExchange
            self.exchange = MockExchange(
                self.account_id,
                self.initial_capital
            )
            self.use_cpp = False
            logger.warning("使用纯Python模拟交易所（C++模块未加载）")
        
        # 配置手续费率等参数
        commission_rate = account_config.get("commission_rate", 0.00025)
        stamp_tax_rate = account_config.get("stamp_tax_rate", 0.001)
        slippage_rate = account_config.get("slippage_rate", 0.0001)
        
        # TODO: 设置费率到exchange（需要C++接口支持）
        # self.exchange.set_commission_rate(commission_rate)
        
        # 初始化其他组件
        self.database = DatabaseManager(self.config.get("database.path", "data/simulation.db"))
        self.data_source = SimulationDataSource(
            primary_source=data_config.get("primary", "baostock"),
            backup_source=data_config.get("backup", "akshare")
        )
        self.risk_manager = RiskManager(risk_config)
        self.performance_analyzer = PerformanceAnalyzer(self.initial_capital)
        
        # 运行状态
        self.mode: Optional[str] = None
        self.is_running = False
        self.current_date: Optional[datetime.date] = None
        
        # 回调函数
        self.on_order_callback: Optional[Callable] = None
        self.on_trade_callback: Optional[Callable] = None
        self.on_tick_callback: Optional[Callable] = None
        
        logger.info(f"Simulation controller initialized: account={self.account_id}, capital={self.initial_capital}")
    
    def start_backtest(
        self,
        start_date: str,
        end_date: str,
        symbols: List[str],
        strategy_func: Callable,
        bar_interval: str = "1d"
    ) -> None:
        """
        启动回测
        
        Args:
            start_date: 开始日期 'YYYY-MM-DD'
            end_date: 结束日期 'YYYY-MM-DD'
            symbols: 股票代码列表
            strategy_func: 策略函数，签名: strategy_func(controller, date, data)
            bar_interval: K线周期 '1m', '5m', '1d' etc.
        """
        logger.info(f"Starting backtest: {start_date} to {end_date}, symbols={symbols}")
        
        self.mode = SimulationMode.BACKTEST
        self.is_running = True
        
        try:
            # 获取交易日列表
            start_dt = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
            end_dt = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
            trading_days = self.calendar.get_trading_days(start_dt, end_dt)
            
            logger.info(f"Found {len(trading_days)} trading days")
            
            # 获取历史数据
            historical_data = self._load_historical_data(symbols, start_date, end_date, bar_interval)
            
            if not historical_data:
                logger.error("Failed to load historical data")
                return
            
            # 逐日回测
            for trade_date in trading_days:
                if not self.is_running:
                    logger.info("Backtest stopped by user")
                    break
                
                self.current_date = trade_date
                date_str = trade_date.strftime("%Y-%m-%d")
                
                # 更新日初资产（用于风控）
                total_assets = self.exchange.get_total_assets()
                self.risk_manager.set_daily_start_assets(total_assets)
                
                # 提取当日数据
                daily_data = {}
                for symbol, df in historical_data.items():
                    if 'date' in df.columns:
                        day_data = df[df['date'] == date_str]
                        if not day_data.empty:
                            daily_data[symbol] = day_data
                
                # 调用策略
                try:
                    strategy_func(self, trade_date, daily_data)
                except Exception as e:
                    logger.error(f"Strategy error on {date_str}: {e}")
                
                # 更新持仓市值（使用收盘价）
                self._update_positions_value(daily_data)
                
                # T+1处理
                date_timestamp = int(trade_date.strftime("%Y%m%d"))
                self.exchange.update_daily(date_timestamp)
                
                # 记录权益曲线
                self._record_equity(trade_date)
                
                logger.debug(f"Backtest progress: {date_str}, equity={total_assets:.2f}")
            
            logger.info("Backtest completed")
            
            # 生成绩效报告
            self._generate_performance_report()
            
        except Exception as e:
            logger.error(f"Backtest failed: {e}", exc_info=True)
        finally:
            self.is_running = False
    
    def start_realtime(
        self,
        symbols: List[str],
        strategy_func: Callable,
        update_interval: int = 60
    ) -> None:
        """
        启动实时模拟
        
        Args:
            symbols: 股票代码列表
            strategy_func: 策略函数
            update_interval: 更新间隔（秒）
        """
        import time
        
        logger.info(f"Starting realtime simulation: symbols={symbols}, interval={update_interval}s")
        
        self.mode = SimulationMode.REALTIME
        self.is_running = True
        
        try:
            while self.is_running:
                now = datetime.datetime.now()
                
                # 检查是否在交易时间
                if not self.calendar.is_trading_time(now):
                    logger.debug(f"Not in trading hours, waiting...")
                    time.sleep(update_interval)
                    continue
                
                self.current_date = now.date()
                
                # 获取实时行情
                realtime_data = self._fetch_realtime_data(symbols)
                
                if not realtime_data:
                    logger.warning("Failed to fetch realtime data")
                    time.sleep(update_interval)
                    continue
                
                # 调用策略
                try:
                    strategy_func(self, now, realtime_data)
                except Exception as e:
                    logger.error(f"Strategy error: {e}")
                
                # 更新持仓市值
                self._update_positions_value_realtime(realtime_data)
                
                # 记录权益
                self._record_equity(now.date())
                
                time.sleep(update_interval)
                
        except KeyboardInterrupt:
            logger.info("Realtime simulation stopped by user")
        except Exception as e:
            logger.error(f"Realtime simulation failed: {e}", exc_info=True)
        finally:
            self.is_running = False
    
    def stop(self) -> None:
        """停止模拟"""
        logger.info("Stopping simulation...")
        self.is_running = False
    
    def submit_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        volume: int,
        price: float = 0.0
    ) -> Optional[str]:
        """
        提交订单
        
        Args:
            symbol: 股票代码
            side: 买卖方向 'buy' or 'sell'
            order_type: 订单类型 'market' or 'limit'
            volume: 数量
            price: 价格（限价单使用）
            
        Returns:
            订单ID，失败返回None
        """
        try:
            # 风控检查
            current_position = self._get_position_volume(symbol)
            available_cash = self.exchange.get_available_cash()
            total_assets = self.exchange.get_total_assets()
            current_positions = self._get_current_positions_dict()
            
            risk_check = self.risk_manager.check_order(
                symbol=symbol,
                side=side,
                price=price if price > 0 else self._get_latest_price(symbol),
                volume=volume,
                current_position=current_position,
                available_cash=available_cash,
                total_assets=total_assets,
                current_positions=current_positions
            )
            
            if risk_check.is_reject():
                logger.warning(f"Order rejected by risk control: {risk_check.reason}")
                return None
            
            # 创建C++订单对象
            cpp_side = sim_cpp.OrderSide.BUY if side.lower() == 'buy' else sim_cpp.OrderSide.SELL
            cpp_type = sim_cpp.OrderType.MARKET if order_type.lower() == 'market' else sim_cpp.OrderType.LIMIT
            
            order_id = f"ORD_{datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')}"
            submit_time = int(datetime.datetime.now().timestamp() * 1000)
            
            order = sim_cpp.SimulatedOrder(
                order_id,
                symbol,
                cpp_side,
                cpp_type,
                price,
                volume,
                submit_time
            )
            
            # 提交到C++交易所
            result_order_id = self.exchange.submit_order(order)
            
            if result_order_id:
                logger.info(f"Order submitted: {result_order_id}, {symbol} {side} {volume}@{price:.2f}")
                
                # 记录到数据库
                self._save_order_to_db(order)
                
                # 回调
                if self.on_order_callback:
                    self.on_order_callback(order)
                
                return result_order_id
            else:
                logger.warning(f"Order submission failed")
                return None
                
        except Exception as e:
            logger.error(f"Failed to submit order: {e}")
            return None
    
    def cancel_order(self, order_id: str) -> bool:
        """
        撤单
        
        Args:
            order_id: 订单ID
            
        Returns:
            是否成功
        """
        try:
            success = self.exchange.cancel_order(order_id)
            
            if success:
                logger.info(f"Order cancelled: {order_id}")
            else:
                logger.warning(f"Failed to cancel order: {order_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to cancel order: {e}")
            return False
    
    def get_account_info(self) -> dict:
        """
        获取账户信息
        
        Returns:
            账户信息字典
        """
        try:
            return {
                "account_id": self.exchange.get_account_id(),
                "available_cash": self.exchange.get_available_cash(),
                "frozen_cash": self.exchange.get_frozen_cash(),
                "total_assets": self.exchange.get_total_assets(),
            }
        except Exception as e:
            logger.error(f"Failed to get account info: {e}")
            return {}
    
    def get_positions(self) -> List[dict]:
        """
        获取持仓列表
        
        Returns:
            持仓列表
        """
        try:
            cpp_positions = self.exchange.get_all_positions()
            
            positions = []
            for pos in cpp_positions:
                positions.append({
                    "symbol": pos.symbol,
                    "volume": pos.volume,
                    "available_volume": pos.available_volume,
                    "frozen_volume": pos.frozen_volume,
                    "avg_cost": pos.avg_cost,
                    "current_price": pos.current_price,
                    "market_value": pos.market_value,
                    "unrealized_pnl": pos.unrealized_pnl,
                    "buy_date": pos.buy_date,
                })
            
            return positions
            
        except Exception as e:
            logger.error(f"Failed to get positions: {e}")
            return []
    
    def get_pending_orders(self, symbol: Optional[str] = None) -> List[dict]:
        """
        获取待成交订单
        
        Args:
            symbol: 股票代码（可选）
            
        Returns:
            订单列表
        """
        try:
            if symbol:
                cpp_orders = self.exchange.get_pending_orders(symbol)
            else:
                cpp_orders = self.exchange.get_pending_orders()
            
            orders = []
            for order in cpp_orders:
                orders.append(self._cpp_order_to_dict(order))
            
            return orders
            
        except Exception as e:
            logger.error(f"Failed to get pending orders: {e}")
            return []
    
    def get_trade_history(self) -> List[dict]:
        """
        获取成交历史
        
        Returns:
            成交记录列表
        """
        try:
            cpp_trades = self.exchange.get_trade_history()
            
            trades = []
            for trade in cpp_trades:
                trades.append({
                    "trade_id": trade.trade_id,
                    "order_id": trade.order_id,
                    "symbol": trade.symbol,
                    "side": "buy" if trade.side == sim_cpp.OrderSide.BUY else "sell",
                    "price": trade.price,
                    "volume": trade.volume,
                    "commission": trade.commission,
                    "timestamp": trade.timestamp,
                    "realized_pnl": trade.realized_pnl,
                })
            
            return trades
            
        except Exception as e:
            logger.error(f"Failed to get trade history: {e}")
            return []
    
    # ========================================================================
    # 私有辅助方法
    # ========================================================================
    
    def _load_historical_data(
        self,
        symbols: List[str],
        start_date: str,
        end_date: str,
        freq: str = "d"
    ) -> Dict[str, pd.DataFrame]:
        """加载历史数据"""
        data = {}
        
        for symbol in symbols:
            df = self.data_source.get_stock_data(symbol, start_date, end_date, freq)
            if df is not None and not df.empty:
                data[symbol] = df
                logger.info(f"Loaded {len(df)} rows for {symbol}")
            else:
                logger.warning(f"No data for {symbol}")
        
        return data
    
    def _fetch_realtime_data(self, symbols: List[str]) -> Dict[str, dict]:
        """获取实时数据"""
        quotes_df = self.data_source.get_realtime_quotes(symbols)
        
        if quotes_df is None or quotes_df.empty:
            return {}
        
        data = {}
        for _, row in quotes_df.iterrows():
            symbol = row.get('symbol') or row.get('code')
            if symbol:
                data[symbol] = row.to_dict()
        
        return data
    
    def _update_positions_value(self, daily_data: Dict[str, pd.DataFrame]) -> None:
        """更新持仓市值（回测模式）"""
        positions = self.get_positions()
        
        for pos in positions:
            symbol = pos['symbol']
            if symbol in daily_data:
                df = daily_data[symbol]
                if not df.empty and 'close' in df.columns:
                    close_price = float(df.iloc[-1]['close'])
                    # TODO: 更新持仓价格到C++
                    # self.exchange.update_position_price(symbol, close_price)
    
    def _update_positions_value_realtime(self, realtime_data: Dict[str, dict]) -> None:
        """更新持仓市值（实时模式）"""
        positions = self.get_positions()
        
        for pos in positions:
            symbol = pos['symbol']
            if symbol in realtime_data:
                price = realtime_data[symbol].get('current') or realtime_data[symbol].get('price')
                if price:
                    # TODO: 更新持仓价格到C++
                    pass
    
    def _record_equity(self, date: datetime.date) -> None:
        """记录权益曲线"""
        try:
            total_assets = self.exchange.get_total_assets()
            self.database.save_equity_curve(self.account_id, date, total_assets)
        except Exception as e:
            logger.error(f"Failed to record equity: {e}")
    
    def _get_position_volume(self, symbol: str) -> int:
        """获取持仓数量"""
        try:
            pos = self.exchange.get_position(symbol)
            return pos.volume
        except:
            return 0
    
    def _get_latest_price(self, symbol: str) -> float:
        """获取最新价格"""
        price = self.data_source.get_latest_price(symbol)
        return price if price else 0.0
    
    def _get_current_positions_dict(self) -> Dict[str, dict]:
        """获取当前持仓字典"""
        positions = self.get_positions()
        return {
            pos['symbol']: {
                'volume': pos['volume'],
                'value': pos['market_value'],
                'avg_cost': pos['avg_cost'],
                'current_price': pos['current_price'],
            }
            for pos in positions
        }
    
    def _save_order_to_db(self, order: Any) -> None:
        """保存订单到数据库"""
        try:
            self.database.save_order(
                account_id=self.account_id,
                order_id=order.order_id,
                symbol=order.symbol,
                side="buy" if order.side == sim_cpp.OrderSide.BUY else "sell",
                order_type="market" if order.type == sim_cpp.OrderType.MARKET else "limit",
                price=order.price,
                volume=order.volume,
                status="pending"
            )
        except Exception as e:
            logger.error(f"Failed to save order to db: {e}")
    
    def _cpp_order_to_dict(self, order: Any) -> dict:
        """将C++订单转为字典"""
        return {
            "order_id": order.order_id,
            "symbol": order.symbol,
            "side": "buy" if order.side == sim_cpp.OrderSide.BUY else "sell",
            "type": "market" if order.type == sim_cpp.OrderType.MARKET else "limit",
            "price": order.price,
            "volume": order.volume,
            "filled_volume": order.filled_volume,
            "status": self._cpp_status_to_str(order.status),
            "submit_time": order.submit_time,
        }
    
    def _cpp_status_to_str(self, status) -> str:
        """将C++订单状态转为字符串"""
        if status == sim_cpp.OrderStatus.PENDING:
            return "pending"
        elif status == sim_cpp.OrderStatus.PARTIAL_FILLED:
            return "partial_filled"
        elif status == sim_cpp.OrderStatus.FILLED:
            return "filled"
        elif status == sim_cpp.OrderStatus.CANCELLED:
            return "cancelled"
        elif status == sim_cpp.OrderStatus.REJECTED:
            return "rejected"
        else:
            return "unknown"
    
    def _generate_performance_report(self) -> None:
        """生成绩效报告"""
        try:
            # 从数据库获取权益曲线
            equity_curve = self.database.get_equity_curve(self.account_id)
            
            # 获取交易记录
            trades = self.get_trade_history()
            
            # 分析绩效
            metrics = self.performance_analyzer.analyze(equity_curve, trades)
            
            # 生成报告
            report = self.performance_analyzer.generate_report(metrics)
            
            # 打印报告
            print(report)
            
            # 保存到文件
            report_path = Path("reports") / f"performance_{self.account_id}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            report_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report)
            
            logger.info(f"Performance report saved to {report_path}")
            
        except Exception as e:
            logger.error(f"Failed to generate performance report: {e}")
