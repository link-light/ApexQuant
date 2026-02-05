"""
ApexQuant 模拟盘数据库管理模块

提供完整的SQLite数据库初始化和管理功能
包含7张表：accounts, positions, orders, trades, equity_curve, ai_decisions, market_events
"""

import sqlite3
import time
import logging
from typing import Optional, Dict, List, Tuple
from contextlib import contextmanager
import os

logger = logging.getLogger(__name__)


class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, db_path: str = "data/sim_trader.db"):
        """
        初始化数据库管理器
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None
        
        # 确保目录存在
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # 初始化数据库
        self.init_database()
        
    def init_database(self):
        """初始化数据库，创建所有表"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 1. accounts 表：账户基本信息
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS accounts (
                    account_id TEXT PRIMARY KEY,
                    account_name TEXT,
                    initial_capital REAL NOT NULL,
                    available_cash REAL NOT NULL,
                    frozen_cash REAL DEFAULT 0.0,
                    total_assets REAL NOT NULL,
                    created_at INTEGER NOT NULL,
                    updated_at INTEGER NOT NULL,
                    strategy_type TEXT,
                    status TEXT DEFAULT 'active' CHECK(status IN ('active', 'paused', 'closed'))
                )
            """)
            
            # 2. positions 表：持仓信息
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS positions (
                    position_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_id TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    volume INTEGER NOT NULL,
                    available_volume INTEGER NOT NULL,
                    frozen_volume INTEGER DEFAULT 0,
                    avg_cost REAL NOT NULL,
                    current_price REAL NOT NULL,
                    market_value REAL NOT NULL,
                    unrealized_pnl REAL NOT NULL,
                    unrealized_pnl_pct REAL NOT NULL,
                    buy_date INTEGER NOT NULL,
                    updated_at INTEGER NOT NULL,
                    FOREIGN KEY (account_id) REFERENCES accounts(account_id),
                    UNIQUE(account_id, symbol)
                )
            """)
            
            # 3. orders 表：订单记录
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    order_id TEXT PRIMARY KEY,
                    account_id TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    direction TEXT NOT NULL CHECK(direction IN ('BUY', 'SELL')),
                    order_type TEXT NOT NULL CHECK(order_type IN ('MARKET', 'LIMIT')),
                    price REAL,
                    volume INTEGER NOT NULL,
                    filled_volume INTEGER DEFAULT 0,
                    status TEXT NOT NULL CHECK(status IN ('PENDING', 'PARTIAL', 'FILLED', 'CANCELLED', 'REJECTED')),
                    submit_time INTEGER NOT NULL,
                    filled_time INTEGER,
                    cancel_time INTEGER,
                    avg_filled_price REAL,
                    commission REAL DEFAULT 0.0,
                    reject_reason TEXT,
                    notes TEXT,
                    FOREIGN KEY (account_id) REFERENCES accounts(account_id)
                )
            """)
            
            # 4. trades 表：成交记录
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    trade_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id TEXT NOT NULL,
                    account_id TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    direction TEXT NOT NULL CHECK(direction IN ('BUY', 'SELL')),
                    price REAL NOT NULL,
                    volume INTEGER NOT NULL,
                    commission REAL NOT NULL,
                    trade_time INTEGER NOT NULL,
                    realized_pnl REAL DEFAULT 0.0,
                    FOREIGN KEY (order_id) REFERENCES orders(order_id),
                    FOREIGN KEY (account_id) REFERENCES accounts(account_id)
                )
            """)
            
            # 5. equity_curve 表：资金曲线快照
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS equity_curve (
                    snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_id TEXT NOT NULL,
                    timestamp INTEGER NOT NULL,
                    total_assets REAL NOT NULL,
                    cash REAL NOT NULL,
                    market_value REAL NOT NULL,
                    total_pnl REAL NOT NULL,
                    total_pnl_pct REAL NOT NULL,
                    daily_pnl REAL DEFAULT 0.0,
                    max_drawdown REAL DEFAULT 0.0,
                    position_count INTEGER DEFAULT 0,
                    FOREIGN KEY (account_id) REFERENCES accounts(account_id),
                    UNIQUE(account_id, timestamp)
                )
            """)
            
            # 6. ai_decisions 表：AI决策记录
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ai_decisions (
                    decision_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_id TEXT NOT NULL,
                    timestamp INTEGER NOT NULL,
                    prompt TEXT,
                    response TEXT,
                    action TEXT CHECK(action IN ('BUY', 'SELL', 'HOLD')),
                    confidence REAL,
                    reasoning TEXT,
                    market_context TEXT,
                    model_name TEXT,
                    tokens_used INTEGER,
                    FOREIGN KEY (account_id) REFERENCES accounts(account_id)
                )
            """)
            
            # 7. market_events 表：市场事件记录
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS market_events (
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    event_type TEXT NOT NULL CHECK(event_type IN ('HALT', 'RESUME', 'LIMIT_UP', 'LIMIT_DOWN', 'DELISTED', 'SUSPENDED')),
                    timestamp INTEGER NOT NULL,
                    description TEXT
                )
            """)
            
            # 创建索引以优化查询性能
            self._create_indexes(cursor)
            
            conn.commit()
            conn.close()
            
            logger.info(f"数据库初始化成功: {self.db_path}")
            
        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
            raise
    
    def _create_indexes(self, cursor):
        """创建索引优化查询性能"""
        indexes = [
            # positions表索引
            "CREATE INDEX IF NOT EXISTS idx_positions_account ON positions(account_id)",
            "CREATE INDEX IF NOT EXISTS idx_positions_symbol ON positions(symbol)",
            
            # orders表索引
            "CREATE INDEX IF NOT EXISTS idx_orders_account ON orders(account_id)",
            "CREATE INDEX IF NOT EXISTS idx_orders_symbol ON orders(symbol)",
            "CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status)",
            "CREATE INDEX IF NOT EXISTS idx_orders_submit_time ON orders(submit_time)",
            
            # trades表索引
            "CREATE INDEX IF NOT EXISTS idx_trades_account ON trades(account_id)",
            "CREATE INDEX IF NOT EXISTS idx_trades_order ON trades(order_id)",
            "CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol)",
            "CREATE INDEX IF NOT EXISTS idx_trades_time ON trades(trade_time)",
            
            # equity_curve表索引
            "CREATE INDEX IF NOT EXISTS idx_equity_account ON equity_curve(account_id)",
            "CREATE INDEX IF NOT EXISTS idx_equity_timestamp ON equity_curve(timestamp)",
            
            # ai_decisions表索引
            "CREATE INDEX IF NOT EXISTS idx_ai_account ON ai_decisions(account_id)",
            "CREATE INDEX IF NOT EXISTS idx_ai_timestamp ON ai_decisions(timestamp)",
            
            # market_events表索引
            "CREATE INDEX IF NOT EXISTS idx_events_symbol ON market_events(symbol)",
            "CREATE INDEX IF NOT EXISTS idx_events_timestamp ON market_events(timestamp)",
        ]
        
        for index_sql in indexes:
            cursor.execute(index_sql)
    
    def create_account(
        self, 
        initial_capital: float, 
        strategy_type: str = "unknown",
        account_name: str = None
    ) -> str:
        """
        创建新账户
        
        Args:
            initial_capital: 初始资金
            strategy_type: 策略类型
            account_name: 账户名称
            
        Returns:
            account_id: 账户ID
        """
        try:
            # 生成账户ID：SIM + 时间戳
            account_id = f"SIM{int(time.time() * 1000)}"
            current_time = int(time.time())
            
            if account_name is None:
                account_name = f"模拟账户_{account_id[-8:]}"
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO accounts (
                        account_id, account_name, initial_capital, 
                        available_cash, frozen_cash, total_assets,
                        created_at, updated_at, strategy_type, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    account_id, account_name, initial_capital,
                    initial_capital, 0.0, initial_capital,
                    current_time, current_time, strategy_type, 'active'
                ))
                conn.commit()
            
            logger.info(f"账户创建成功: {account_id}, 初始资金: {initial_capital}")
            return account_id
            
        except Exception as e:
            logger.error(f"创建账户失败: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """
        获取数据库连接（上下文管理器）
        
        使用方式:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(...)
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 支持通过列名访问
        try:
            yield conn
        finally:
            conn.close()
    
    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            self.conn = None
            logger.info("数据库连接已关闭")
    
    def get_account_info(self, account_id: str) -> Optional[Dict]:
        """
        获取账户信息
        
        Args:
            account_id: 账户ID
            
        Returns:
            账户信息字典，不存在返回None
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM accounts WHERE account_id = ?", (account_id,))
                row = cursor.fetchone()
                
                if row:
                    return dict(row)
                return None
                
        except Exception as e:
            logger.error(f"获取账户信息失败: {e}")
            return None
    
    def update_account(
        self, 
        account_id: str, 
        available_cash: float = None,
        frozen_cash: float = None,
        total_assets: float = None
    ):
        """
        更新账户信息
        
        Args:
            account_id: 账户ID
            available_cash: 可用资金
            frozen_cash: 冻结资金
            total_assets: 总资产
        """
        try:
            updates = []
            params = []
            
            if available_cash is not None:
                updates.append("available_cash = ?")
                params.append(available_cash)
            
            if frozen_cash is not None:
                updates.append("frozen_cash = ?")
                params.append(frozen_cash)
            
            if total_assets is not None:
                updates.append("total_assets = ?")
                params.append(total_assets)
            
            if not updates:
                return
            
            updates.append("updated_at = ?")
            params.append(int(time.time()))
            params.append(account_id)
            
            sql = f"UPDATE accounts SET {', '.join(updates)} WHERE account_id = ?"
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, params)
                conn.commit()
                
        except Exception as e:
            logger.error(f"更新账户失败: {e}")
            raise
    
    def execute_query(self, sql: str, params: Tuple = ()) -> List[Dict]:
        """
        执行查询SQL
        
        Args:
            sql: SQL语句
            params: 参数元组
            
        Returns:
            结果列表（字典格式）
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, params)
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"查询失败: {e}")
            return []
    
    def execute_update(self, sql: str, params: Tuple = ()):
        """
        执行更新SQL（INSERT/UPDATE/DELETE）
        
        Args:
            sql: SQL语句
            params: 参数元组
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, params)
                conn.commit()
                
        except Exception as e:
            logger.error(f"更新失败: {e}")
            raise


# 便捷函数

def create_database(db_path: str = "data/sim_trader.db") -> DatabaseManager:
    """
    创建数据库实例
    
    Args:
        db_path: 数据库路径
        
    Returns:
        DatabaseManager实例
    """
    return DatabaseManager(db_path)


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 60)
    print("ApexQuant Database Test")
    print("=" * 60)
    
    # 创建数据库
    db = DatabaseManager("data/test_sim_trader.db")
    
    # 创建测试账户
    account_id = db.create_account(
        initial_capital=1000000.0,
        strategy_type="ma_cross",
        account_name="Test Account 001"
    )
    
    print(f"\n[OK] Account created: {account_id}")
    
    # 查询账户信息
    account_info = db.get_account_info(account_id)
    print(f"\nAccount Info:")
    for key, value in account_info.items():
        print(f"  {key}: {value}")
    
    # 更新账户
    db.update_account(
        account_id,
        available_cash=950000.0,
        frozen_cash=50000.0,
        total_assets=1000000.0
    )
    
    print(f"\n[OK] Account updated")
    
    # 再次查询
    account_info = db.get_account_info(account_id)
    print(f"\nUpdated Account Info:")
    print(f"  available_cash: {account_info['available_cash']}")
    print(f"  frozen_cash: {account_info['frozen_cash']}")
    print(f"  total_assets: {account_info['total_assets']}")
    
    print("\n" + "=" * 60)
    print("[OK] All tests passed!")
    print("=" * 60)
