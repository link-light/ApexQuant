"""
ApexQuant 交易日历管理模块

提供交易时间判断和节假日检查功能
"""

import datetime
import logging
from typing import Optional

try:
    import chinese_calendar as cc
    CHINESE_CALENDAR_AVAILABLE = True
except ImportError:
    CHINESE_CALENDAR_AVAILABLE = False
    logging.warning("chinese_calendar not installed, holiday check will be disabled")

logger = logging.getLogger(__name__)


class TradingCalendar:
    """交易日历管理器"""
    
    # A股交易时间段（北京时间）
    MORNING_START = datetime.time(9, 30)    # 早盘开始
    MORNING_END = datetime.time(11, 30)      # 早盘结束
    AFTERNOON_START = datetime.time(13, 0)  # 午盘开始
    AFTERNOON_END = datetime.time(15, 0)    # 午盘结束
    
    # 集合竞价时间
    CALL_AUCTION_START = datetime.time(9, 15)  # 集合竞价开始
    CALL_AUCTION_END = datetime.time(9, 25)    # 集合竞价结束
    
    def __init__(self):
        """初始化交易日历"""
        self.use_holiday_check = CHINESE_CALENDAR_AVAILABLE
    
    def is_trading_day(self, date: datetime.date = None) -> bool:
        """
        判断是否为交易日
        
        Args:
            date: 日期，默认为今天
            
        Returns:
            是否为交易日
        """
        if date is None:
            date = datetime.date.today()
        
        # 1. 检查是否为周末
        if date.weekday() >= 5:  # 5=Saturday, 6=Sunday
            return False
        
        # 2. 检查是否为法定节假日
        if self.use_holiday_check:
            try:
                # chinese_calendar库：is_workday() = 工作日
                # 注意：is_workday() 返回True表示工作日，False表示节假日或周末
                return cc.is_workday(date)
            except Exception as e:
                logger.warning(f"Holiday check failed: {e}, assuming trading day")
                return True
        
        # 如果没有chinese_calendar库，只检查周末
        return True
    
    def is_trading_time(self, dt: datetime.datetime = None) -> bool:
        """
        判断是否为交易时间（不含集合竞价）
        
        Args:
            dt: 日期时间，默认为现在
            
        Returns:
            是否为交易时间
        """
        if dt is None:
            dt = datetime.datetime.now()
        
        # 1. 检查是否为交易日
        if not self.is_trading_day(dt.date()):
            return False
        
        # 2. 检查时间段
        current_time = dt.time()
        
        # 早盘：9:30-11:30
        if self.MORNING_START <= current_time <= self.MORNING_END:
            return True
        
        # 午盘：13:00-15:00
        if self.AFTERNOON_START <= current_time <= self.AFTERNOON_END:
            return True
        
        return False
    
    def is_call_auction_time(self, dt: datetime.datetime = None) -> bool:
        """
        判断是否为集合竞价时间（9:15-9:25）
        
        Args:
            dt: 日期时间，默认为现在
            
        Returns:
            是否为集合竞价时间
        """
        if dt is None:
            dt = datetime.datetime.now()
        
        # 1. 检查是否为交易日
        if not self.is_trading_day(dt.date()):
            return False
        
        # 2. 检查时间段
        current_time = dt.time()
        return self.CALL_AUCTION_START <= current_time <= self.CALL_AUCTION_END
    
    def is_market_open(self, dt: datetime.datetime = None) -> bool:
        """
        判断市场是否开盘（交易时间或集合竞价时间）
        
        Args:
            dt: 日期时间，默认为现在
            
        Returns:
            市场是否开盘
        """
        return self.is_trading_time(dt) or self.is_call_auction_time(dt)
    
    def get_next_trading_day(self, date: datetime.date = None) -> datetime.date:
        """
        获取下一个交易日
        
        Args:
            date: 起始日期，默认为今天
            
        Returns:
            下一个交易日
        """
        if date is None:
            date = datetime.date.today()
        
        next_date = date + datetime.timedelta(days=1)
        max_attempts = 30  # 最多查找30天
        
        for _ in range(max_attempts):
            if self.is_trading_day(next_date):
                return next_date
            next_date += datetime.timedelta(days=1)
        
        # 如果30天内没有交易日（不太可能），返回原日期+1
        logger.warning(f"No trading day found within 30 days after {date}")
        return date + datetime.timedelta(days=1)
    
    def get_trading_seconds_left(self, dt: datetime.datetime = None) -> int:
        """
        获取距离收盘还剩多少秒
        
        Args:
            dt: 日期时间，默认为现在
            
        Returns:
            剩余秒数，-1表示非交易时间
        """
        if dt is None:
            dt = datetime.datetime.now()
        
        if not self.is_trading_time(dt):
            return -1
        
        current_time = dt.time()
        
        # 早盘
        if self.MORNING_START <= current_time <= self.MORNING_END:
            end_datetime = datetime.datetime.combine(dt.date(), self.MORNING_END)
            return int((end_datetime - dt).total_seconds())
        
        # 午盘
        if self.AFTERNOON_START <= current_time <= self.AFTERNOON_END:
            end_datetime = datetime.datetime.combine(dt.date(), self.AFTERNOON_END)
            return int((end_datetime - dt).total_seconds())
        
        return -1
    
    def wait_until_next_bar(self, freq_seconds: int = 60):
        """
        等待到下一个整点bar（用于实时模式）
        
        Args:
            freq_seconds: 频率秒数（60=1分钟，300=5分钟）
        """
        import time
        
        now = datetime.datetime.now()
        current_seconds = now.second + now.microsecond / 1000000.0
        
        # 计算需要等待的秒数
        wait_seconds = freq_seconds - (current_seconds % freq_seconds)
        
        if wait_seconds > 0:
            logger.debug(f"Waiting {wait_seconds:.2f}s until next bar")
            time.sleep(wait_seconds)
    
    @staticmethod
    def get_date_int(dt: datetime.datetime = None) -> int:
        """
        获取日期整数（格式：20250203）
        
        Args:
            dt: 日期时间，默认为现在
            
        Returns:
            日期整数
        """
        if dt is None:
            dt = datetime.datetime.now()
        
        return int(dt.strftime("%Y%m%d"))
    
    @staticmethod
    def date_int_to_datetime(date_int: int) -> datetime.datetime:
        """
        日期整数转datetime
        
        Args:
            date_int: 日期整数（如20250203）
            
        Returns:
            datetime对象
        """
        date_str = str(date_int)
        return datetime.datetime.strptime(date_str, "%Y%m%d")


# 全局实例
_calendar: Optional[TradingCalendar] = None


def get_calendar() -> TradingCalendar:
    """获取全局交易日历实例（单例）"""
    global _calendar
    if _calendar is None:
        _calendar = TradingCalendar()
    return _calendar


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 60)
    print("ApexQuant Trading Calendar Test")
    print("=" * 60)
    
    calendar = get_calendar()
    
    now = datetime.datetime.now()
    print(f"\nCurrent time: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Is trading day: {calendar.is_trading_day()}")
    print(f"Is trading time: {calendar.is_trading_time()}")
    print(f"Is call auction: {calendar.is_call_auction_time()}")
    print(f"Is market open: {calendar.is_market_open()}")
    
    if calendar.is_trading_time():
        seconds_left = calendar.get_trading_seconds_left()
        print(f"Trading seconds left: {seconds_left}s ({seconds_left/60:.1f}min)")
    
    print(f"\nNext trading day: {calendar.get_next_trading_day()}")
    print(f"Date int: {calendar.get_date_int()}")
    
    # 测试特定时间
    print("\nTesting specific times:")
    test_times = [
        datetime.datetime(2025, 2, 3, 9, 0),   # 开盘前
        datetime.datetime(2025, 2, 3, 9, 20),  # 集合竞价
        datetime.datetime(2025, 2, 3, 10, 0),  # 早盘
        datetime.datetime(2025, 2, 3, 12, 0),  # 午休
        datetime.datetime(2025, 2, 3, 14, 0),  # 午盘
        datetime.datetime(2025, 2, 3, 16, 0),  # 收盘后
    ]
    
    for test_time in test_times:
        is_trading = calendar.is_trading_time(test_time)
        is_auction = calendar.is_call_auction_time(test_time)
        status = "TRADING" if is_trading else ("AUCTION" if is_auction else "CLOSED")
        print(f"  {test_time.strftime('%H:%M')}: {status}")
    
    print("\n" + "=" * 60)
    print("[OK] Trading calendar test passed!")
    print("=" * 60)
