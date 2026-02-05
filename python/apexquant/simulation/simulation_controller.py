"""
ApexQuant 模拟盘控制器

整合C++引擎、数据源、数据库，提供双模式运行（回测/实时）
"""

import logging
import time
from enum import Enum
from typing import Callable, List, Dict, Optional
from datetime import datetime

# 导入各模块
from .database import DatabaseManager
from .data_source import DataSource, create_data_source, bar_to_tick
from .trading_calendar import TradingCalendar, get_calendar
from .config import get_config

logger = logging.getLogger(__name__)

# 尝试导入C++模拟盘模块
try:
    import apexquant_simulation as sim
    SIMULATION_MODULE_AVAILABLE = True
except ImportError:
    SIMULATION_MODULE_AVAILABLE = False
    logger.error("apexquant_simulation module not compiled, please run build.bat first")


class SimulationMode(Enum):
    """模拟模式"""
    BACKTEST = "backtest"  # 历史回放（快速）
    REALTIME = "realtime"  # 实时跟盘（真实时间）


class SimulationController:
    """模拟盘控制器"""
    
    def __init__(
        self,
        mode: SimulationMode,
        account_id: str = None,
        initial_capital: float = None,
        db_path: str = None,
        config_path: str = None
    ):
        """
        初始化控制器
        
        Args:
            mode: 运行模式
            account_id: 账户ID（None则自动生成）
            initial_capital: 初始资金（None则从配置读取）
            db_path: 数据库路径（None则从配置读取）
            config_path: 配置文件路径
        """
        # 加载配置
        self.config = get_config(config_path)
        
        # 模式
        self.mode = mode
        
        # 初始化参数
        if initial_capital is None:
            initial_capital = self.config.initial_capital
        if db_path is None:
            db_path = self.config.database_path
        
        # 初始化数据库
        self.db = DatabaseManager(db_path)
        
        # 创建账户
        if account_id is None:
            strategy_type = self.config.get('strategy.name', 'unknown')
            self.account_id = self.db.create_account(
                initial_capital=initial_capital,
                strategy_type=strategy_type
            )
        else:
            self.account_id = account_id
        
        logger.info(f"Account ID: {self.account_id}")
        
        # 初始化C++模拟交易所
        if not SIMULATION_MODULE_AVAILABLE:
            raise RuntimeError("C++ simulation module not available")
        
        self.exchange = sim.SimulatedExchange(self.account_id, initial_capital)
        
        # 数据源和日历
        self.data_source: Optional[DataSource] = None
        self.calendar = get_calendar()
        
        # 运行状态
        self.is_running = False
        self.current_time: Optional[datetime] = None
        self.bar_count = 0
        self.last_save_time: Optional[datetime] = None
        
        logger.info(f"SimulationController initialized in {mode.value} mode")
    
    def start(self, start_date: str, end_date: str = None, symbols: List[str] = None):
        """
        启动模拟盘
        
        Args:
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期（BACKTEST模式必填）
            symbols: 股票代码列表
        """
        # 初始化数据源
        provider = self.config.data_provider
        self.data_source = create_data_source(provider)
        
        logger.info(f"Simulation started: {start_date} to {end_date}")
        logger.info(f"Symbols: {symbols}")
        
        self.is_running = True
    
    def run(self, strategy_func: Callable, symbols: List[str]):
        """
        运行策略主循环
        
        Args:
            strategy_func: 策略函数，签名：func(controller, bar, account_info) -> signals
            symbols: 股票代码列表
        """
        if not self.is_running:
            raise RuntimeError("Please call start() first")
        
        if self.mode == SimulationMode.BACKTEST:
            self._run_backtest(strategy_func, symbols)
        else:
            self._run_realtime(strategy_func, symbols)
    
    def _run_backtest(self, strategy_func: Callable, symbols: List[str]):
        """回测模式运行"""
        logger.info("Running in BACKTEST mode...")
        
        # 获取历史数据（这里简化为单个symbol）
        symbol = symbols[0]
        start_date = self.config.get('simulation.start_date', '2024-01-01')
        end_date = self.config.get('simulation.end_date', '2024-12-31')
        
        bars = self.data_source.get_history(symbol, start_date, end_date)
        
        if not bars:
            logger.error(f"No data for {symbol}")
            return
        
        logger.info(f"Loaded {len(bars)} bars")
        
        # 快速回放
        last_close = 0.0
        
        for i, bar in enumerate(bars):
            self.bar_count = i + 1
            
            # 转换为Tick并发送给交易所
            tick = bar_to_tick(bar, last_close)
            self.exchange.on_tick(tick)
            
            # 获取账户信息
            account_info = self.get_account_info()
            
            # 调用策略
            try:
                signals = strategy_func(self, bar, account_info)
                if signals:
                    self.process_signals(signals)
            except Exception as e:
                logger.error(f"Strategy error: {e}")
            
            # 每100根K线保存一次快照
            if i % 100 == 0:
                self.save_snapshot()
                logger.info(f"Progress: {i}/{len(bars)} bars, Total assets: {account_info['total_assets']:.2f}")
            
            last_close = bar['close']
        
        # 最终保存
        self.save_snapshot()
        logger.info(f"Backtest completed! Total bars: {len(bars)}")
        self._print_summary()
    
    def _run_realtime(self, strategy_func: Callable, symbols: List[str]):
        """实时模式运行"""
        logger.info("Running in REALTIME mode...")
        logger.info("Press Ctrl+C to stop")
        
        symbol = symbols[0]
        
        try:
            while self.is_running:
                # 检查交易时间
                if not self.calendar.is_trading_time():
                    logger.info("Market closed, waiting...")
                    time.sleep(60)
                    continue
                
                # 获取最新数据
                bar = self.data_source.get_latest(symbol)
                
                if bar is None:
                    logger.warning("Failed to get latest bar")
                    time.sleep(5)
                    continue
                
                # 转换为Tick
                tick = bar_to_tick(bar)
                self.exchange.on_tick(tick)
                
                # 获取账户信息
                account_info = self.get_account_info()
                
                # 调用策略
                try:
                    signals = strategy_func(self, bar, account_info)
                    if signals:
                        self.process_signals(signals)
                except Exception as e:
                    logger.error(f"Strategy error: {e}")
                
                # 每分钟保存快照
                self.save_snapshot()
                
                # 等待下一分钟
                self.calendar.wait_until_next_bar(60)
                
        except KeyboardInterrupt:
            logger.info("Interrupted by user")
        finally:
            self.stop()
    
    def process_signals(self, signals: Dict):
        """
        处理策略信号
        
        Args:
            signals: 信号字典 {
                'action': 'BUY' | 'SELL' | 'HOLD',
                'symbol': str,
                'volume': int,
                'price': float (optional)
            }
        """
        action = signals.get('action')
        
        if action == 'BUY':
            self.buy(signals['symbol'], signals['volume'], signals.get('price'))
        elif action == 'SELL':
            self.sell(signals['symbol'], signals['volume'], signals.get('price'))
        # HOLD: do nothing
    
    def buy(self, symbol: str, volume: int, price: float = None) -> str:
        """下买单"""
        order = sim.SimulatedOrder()
        order.symbol = symbol
        order.side = sim.OrderSide.BUY
        order.type = sim.OrderType.MARKET if price is None else sim.OrderType.LIMIT
        order.price = price if price else 0.0
        order.volume = volume
        
        order_id = self.exchange.submit_order(order)
        logger.info(f"Buy order submitted: {order_id}, {symbol} x{volume}")
        
        return order_id
    
    def sell(self, symbol: str, volume: int, price: float = None) -> str:
        """下卖单"""
        order = sim.SimulatedOrder()
        order.symbol = symbol
        order.side = sim.OrderSide.SELL
        order.type = sim.OrderType.MARKET if price is None else sim.OrderType.LIMIT
        order.price = price if price else 0.0
        order.volume = volume
        
        order_id = self.exchange.submit_order(order)
        logger.info(f"Sell order submitted: {order_id}, {symbol} x{volume}")
        
        return order_id
    
    def cancel_order(self, order_id: str) -> bool:
        """撤单"""
        return self.exchange.cancel_order(order_id)
    
    def get_account_info(self) -> Dict:
        """获取账户信息"""
        positions = self.exchange.get_all_positions()
        
        pos_list = []
        for pos in positions:
            pos_list.append({
                'symbol': pos.symbol,
                'volume': pos.volume,
                'available_volume': pos.available_volume,
                'avg_cost': pos.avg_cost,
                'current_price': pos.current_price,
                'market_value': pos.market_value,
                'unrealized_pnl': pos.unrealized_pnl,
                'unrealized_pnl_pct': pos.unrealized_pnl / (pos.avg_cost * pos.volume) * 100 if pos.volume > 0 else 0
            })
        
        return {
            'total_assets': self.exchange.get_total_assets(),
            'available_cash': self.exchange.get_available_cash(),
            'frozen_cash': self.exchange.get_frozen_cash(),
            'positions': pos_list
        }
    
    def save_snapshot(self):
        """保存账户快照到数据库"""
        try:
            account_info = self.get_account_info()
            
            # 计算市值和盈亏
            market_value = sum(p['market_value'] for p in account_info['positions'])
            total_assets = account_info['total_assets']
            initial_capital = self.config.initial_capital
            total_pnl = total_assets - initial_capital
            total_pnl_pct = (total_pnl / initial_capital) * 100
            
            # 插入equity_curve表
            self.db.execute_update("""
                INSERT OR REPLACE INTO equity_curve (
                    account_id, timestamp, total_assets, cash, market_value,
                    total_pnl, total_pnl_pct, position_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                self.account_id,
                int(time.time()),
                total_assets,
                account_info['available_cash'],
                market_value,
                total_pnl,
                total_pnl_pct,
                len(account_info['positions'])
            ))
            
        except Exception as e:
            logger.error(f"Failed to save snapshot: {e}")
    
    def stop(self):
        """停止运行"""
        self.is_running = False
        self.save_snapshot()
        logger.info("Simulation stopped")
    
    def _print_summary(self):
        """打印汇总信息"""
        account_info = self.get_account_info()
        
        print("\n" + "=" * 60)
        print("Simulation Summary")
        print("=" * 60)
        print(f"Total assets: {account_info['total_assets']:.2f}")
        print(f"Available cash: {account_info['available_cash']:.2f}")
        print(f"Market value: {sum(p['market_value'] for p in account_info['positions']):.2f}")
        print(f"Positions: {len(account_info['positions'])}")
        
        for pos in account_info['positions']:
            print(f"  {pos['symbol']}: {pos['volume']} shares, PnL: {pos['unrealized_pnl']:.2f} ({pos['unrealized_pnl_pct']:.2f}%)")
        
        print("=" * 60 + "\n")


if __name__ == "__main__":
    # 简单测试
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 60)
    print("ApexQuant Simulation Controller Test")
    print("=" * 60)
    
    # 创建控制器
    try:
        controller = SimulationController(
            mode=SimulationMode.BACKTEST,
            initial_capital=1000000
        )
        
        print(f"\n[OK] Controller created, account: {controller.account_id}")
        print(f"Initial cash: {controller.exchange.get_available_cash():.2f}")
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        print("Note: C++ module needs to be compiled first")
    
    print("\n" + "=" * 60)
