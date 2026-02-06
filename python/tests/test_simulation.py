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
        
        self.assertGreater(config.get('account.initial_capital', 0), 0)
        self.assertIsNotNone(config.get('database.path'))
        self.assertGreater(config.get('account.commission_rate', 0), 0)
    
    def test_get_config(self):
        """测试获取配置项"""
        config = SimulationConfig()
        
        # 点号路径
        value = config.get('risk_control.max_single_position_pct')
        self.assertIsNotNone(value)
        
        # 默认值
        value = config.get('non.existent.key', 'default')
        self.assertEqual(value, 'default')
    
    def test_validate_config(self):
        """测试配置验证"""
        config = SimulationConfig()
        result = config.validate()
        self.assertTrue(result)


class TestRiskManager(unittest.TestCase):
    """测试风控管理器"""
    
    def setUp(self):
        config = {
            'enable_risk_control': True,
            'max_single_position_pct': 0.3,
            'max_total_position_pct': 0.95,
            'max_single_order_amount': 50000.0,
            'daily_loss_limit_pct': 0.05,
            'stop_loss_pct': 0.1,
            'take_profit_pct': 0.2
        }
        self.risk_mgr = RiskManager(config)
    
    def test_check_buy_order(self):
        """测试买单检查"""
        result = self.risk_mgr.check_order(
            symbol='600519.SH',
            side='BUY',
            price=100.0,
            volume=100,
            current_position=0,
            available_cash=800000,
            total_assets=1000000,
            current_positions={}
        )
        
        self.assertTrue(result.is_pass())
    
    def test_daily_loss_limit(self):
        """测试日亏损限制"""
        self.risk_mgr.set_daily_start_assets(1000000)
        
        # 亏损未超限
        self.risk_mgr.update_daily_pnl(980000)
        self.assertLess(abs(self.risk_mgr.daily_pnl), 1000000 * 0.05)
        
        # 亏损超限
        self.risk_mgr.update_daily_pnl(940000)
        self.assertGreater(abs(self.risk_mgr.daily_pnl), 1000000 * 0.05)
    
    def test_stop_loss_check(self):
        """测试止损检查"""
        from apexquant.simulation.risk_manager import RiskCheckResult
        
        # 测试止损 - 价格下跌15%，超过10%止损线，返回WARNING
        result = self.risk_mgr.check_position_stop_loss(
            symbol='600519.SH',
            avg_cost=100.0,
            current_price=85.0
        )
        self.assertEqual(result.result, RiskCheckResult.WARNING)
        
        # 未触发止损 - 价格下跌5%，未超过10%止损线
        result = self.risk_mgr.check_position_stop_loss(
            symbol='600519.SH',
            avg_cost=100.0,
            current_price=95.0
        )
        self.assertTrue(result.is_pass())


class TestTradingCalendar(unittest.TestCase):
    """测试交易日历"""
    
    def setUp(self):
        self.calendar = TradingCalendar()
    
    def test_trading_time(self):
        """测试交易时间判断"""
        # 使用2024年的交易日（2024年1月2日是周二）
        dt = datetime.datetime(2024, 1, 2, 10, 0)
        self.assertTrue(self.calendar.is_trading_time(dt))
        
        # 周二午盘
        dt = datetime.datetime(2024, 1, 2, 14, 0)
        self.assertTrue(self.calendar.is_trading_time(dt))
        
        # 周二午休
        dt = datetime.datetime(2024, 1, 2, 12, 0)
        self.assertFalse(self.calendar.is_trading_time(dt))
        
        # 周六
        dt = datetime.datetime(2024, 1, 6, 10, 0)
        self.assertFalse(self.calendar.is_trading_time(dt))
    
    def test_call_auction(self):
        """测试集合竞价"""
        dt = datetime.datetime(2024, 1, 2, 9, 20)
        self.assertTrue(self.calendar.is_call_auction_time(dt))
        
        dt = datetime.datetime(2024, 1, 2, 9, 35)
        self.assertFalse(self.calendar.is_call_auction_time(dt))
    
    def test_is_trading_day(self):
        """测试交易日判断"""
        # 2024年1月2日是周二，应该是交易日
        date = datetime.date(2024, 1, 2)
        self.assertTrue(self.calendar.is_trading_day(date))
        
        # 周六不是交易日
        date = datetime.date(2024, 1, 6)
        self.assertFalse(self.calendar.is_trading_day(date))


class TestDataSource(unittest.TestCase):
    """测试数据源"""
    
    def test_mock_data_source(self):
        """测试Mock数据源"""
        source = MockDataSource(num_days=5, initial_price=100.0)
        
        df = source.get_stock_data(
            'TEST.SH',
            '2024-01-01',
            '2024-01-05',
            'd'
        )
        
        self.assertIsNotNone(df)
        self.assertGreater(len(df), 0)
        self.assertIn('close', df.columns)
        self.assertIn('open', df.columns)
    
    def test_bar_to_tick(self):
        """测试bar转tick"""
        import pandas as pd
        bar = pd.Series({
            'symbol': 'TEST.SH',
            'open': 99.0,
            'high': 101.0,
            'low': 98.0,
            'close': 100.0,
            'volume': 10000
        })
        
        ticks = bar_to_tick(bar, num_ticks=5)
        self.assertIsInstance(ticks, list)
        self.assertGreater(len(ticks), 0)
        self.assertIn('price', ticks[0])
        self.assertIn('volume', ticks[0])


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
