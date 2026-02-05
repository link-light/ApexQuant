"""
ApexQuant 模拟盘系统单元测试
"""

import unittest
import sys
import os

# 添加路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from apexquant.simulation.database import DatabaseManager
from apexquant.simulation.config import SimulationConfig
from apexquant.simulation.risk_manager import RiskManager
from apexquant.simulation.trading_calendar import TradingCalendar
from apexquant.simulation.data_source import MockDataSource, bar_to_tick
import datetime


class TestDatabase(unittest.TestCase):
    """测试数据库模块"""
    
    def setUp(self):
        self.db = DatabaseManager("data/test_sim.db")
    
    def test_create_account(self):
        """测试创建账户"""
        account_id = self.db.create_account(1000000, "test_strategy")
        self.assertIsNotNone(account_id)
        self.assertTrue(account_id.startswith("SIM"))
        
        # 验证账户信息
        account_info = self.db.get_account_info(account_id)
        self.assertEqual(account_info['initial_capital'], 1000000)
        self.assertEqual(account_info['available_cash'], 1000000)
    
    def test_update_account(self):
        """测试更新账户"""
        account_id = self.db.create_account(1000000, "test")
        
        self.db.update_account(
            account_id,
            available_cash=950000,
            frozen_cash=50000,
            total_assets=1000000
        )
        
        account_info = self.db.get_account_info(account_id)
        self.assertEqual(account_info['available_cash'], 950000)
        self.assertEqual(account_info['frozen_cash'], 50000)


class TestConfig(unittest.TestCase):
    """测试配置模块"""
    
    def test_default_config(self):
        """测试默认配置"""
        config = SimulationConfig()
        
        self.assertGreater(config.initial_capital, 0)
        self.assertIsNotNone(config.database_path)
        self.assertGreater(config.commission_rate, 0)
    
    def test_get_config(self):
        """测试获取配置项"""
        config = SimulationConfig()
        
        # 点号路径
        value = config.get('risk.max_single_position_pct')
        self.assertIsNotNone(value)
        
        # 默认值
        value = config.get('non.existent.key', 'default')
        self.assertEqual(value, 'default')
    
    def test_validate_config(self):
        """测试配置验证"""
        config = SimulationConfig()
        result = config.validate_config()
        self.assertTrue(result)


class TestRiskManager(unittest.TestCase):
    """测试风控管理器"""
    
    def setUp(self):
        self.risk_mgr = RiskManager()
        self.account_info = {
            'total_assets': 1000000,
            'available_cash': 800000,
            'positions': []
        }
    
    def test_check_buy_order(self):
        """测试买单检查"""
        order = {
            'symbol': '600519.SH',
            'side': 'BUY',
            'volume': 1000,
            'price': 1800.0
        }
        
        passed, reason = self.risk_mgr.check_order(order, self.account_info)
        self.assertTrue(passed)
    
    def test_max_buy_volume(self):
        """测试最大可买数量"""
        max_vol = self.risk_mgr.get_max_buy_volume(
            '600519.SH',
            1800.0,
            self.account_info
        )
        
        self.assertGreater(max_vol, 0)
        self.assertEqual(max_vol % 100, 0)  # 应该是100的倍数
    
    def test_stop_loss_check(self):
        """测试止损检查"""
        positions = [
            {'symbol': '600519.SH', 'unrealized_pnl_pct': -12.0},
            {'symbol': '000001.SZ', 'unrealized_pnl_pct': 5.0}
        ]
        
        stop_loss_symbols = self.risk_mgr.check_stop_loss(positions)
        self.assertIn('600519.SH', stop_loss_symbols)
        self.assertNotIn('000001.SZ', stop_loss_symbols)


class TestTradingCalendar(unittest.TestCase):
    """测试交易日历"""
    
    def setUp(self):
        self.calendar = TradingCalendar()
    
    def test_trading_time(self):
        """测试交易时间判断"""
        # 周一早盘
        dt = datetime.datetime(2025, 2, 3, 10, 0)
        self.assertTrue(self.calendar.is_trading_time(dt))
        
        # 周一午盘
        dt = datetime.datetime(2025, 2, 3, 14, 0)
        self.assertTrue(self.calendar.is_trading_time(dt))
        
        # 周一午休
        dt = datetime.datetime(2025, 2, 3, 12, 0)
        self.assertFalse(self.calendar.is_trading_time(dt))
        
        # 周六
        dt = datetime.datetime(2025, 2, 8, 10, 0)
        self.assertFalse(self.calendar.is_trading_time(dt))
    
    def test_call_auction(self):
        """测试集合竞价"""
        dt = datetime.datetime(2025, 2, 3, 9, 20)
        self.assertTrue(self.calendar.is_call_auction_time(dt))
        
        dt = datetime.datetime(2025, 2, 3, 9, 35)
        self.assertFalse(self.calendar.is_call_auction_time(dt))
    
    def test_date_int(self):
        """测试日期整数转换"""
        dt = datetime.datetime(2025, 2, 3, 10, 0)
        date_int = self.calendar.get_date_int(dt)
        self.assertEqual(date_int, 20250203)


class TestDataSource(unittest.TestCase):
    """测试数据源"""
    
    def test_mock_data_source(self):
        """测试Mock数据源"""
        source = MockDataSource(initial_price=100.0, volatility=0.02)
        
        bars = source.get_history(
            'TEST.SH',
            '2024-01-01',
            '2024-01-02',
            '1min'
        )
        
        self.assertGreater(len(bars), 0)
        self.assertEqual(bars[0]['symbol'], 'TEST.SH')
        self.assertIn('close', bars[0])
    
    def test_bar_to_tick(self):
        """测试bar转tick"""
        bar = {
            'symbol': 'TEST.SH',
            'timestamp': 1234567890000,
            'close': 100.0,
            'volume': 10000
        }
        
        tick = bar_to_tick(bar, last_close=99.0)
        self.assertEqual(tick.symbol, 'TEST.SH')
        self.assertEqual(tick.last_price, 100.0)
        self.assertGreater(tick.ask_price, tick.bid_price)


def run_tests():
    """运行所有测试"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试
    suite.addTests(loader.loadTestsFromTestCase(TestDatabase))
    suite.addTests(loader.loadTestsFromTestCase(TestConfig))
    suite.addTests(loader.loadTestsFromTestCase(TestRiskManager))
    suite.addTests(loader.loadTestsFromTestCase(TestTradingCalendar))
    suite.addTests(loader.loadTestsFromTestCase(TestDataSource))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    import sys
    sys.exit(run_tests())
