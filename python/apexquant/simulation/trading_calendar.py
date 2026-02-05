"""
ApexQuant Trading Calendar
A股交易日历管理器
"""

import datetime
from typing import List, Optional, Set
from chinese_calendar import is_workday, is_holiday
import logging

logger = logging.getLogger(__name__)


class TradingCalendar:
    """A股交易日历管理器"""
    
    def __init__(self):
        """初始化交易日历"""
        # A股交易时间段（小时:分钟）
        self.morning_start = datetime.time(9, 30)
        self.morning_end = datetime.time(11, 30)
        self.afternoon_start = datetime.time(13, 0)
        self.afternoon_end = datetime.time(15, 0)
        
        # 集合竞价时间
        self.call_auction_start = datetime.time(9, 15)
        self.call_auction_end = datetime.time(9, 25)
        
        # 尾盘集合竞价
        self.close_auction_start = datetime.time(14, 57)
        self.close_auction_end = datetime.time(15, 0)
    
    def is_trading_day(self, date: datetime.date) -> bool:
        """
        判断是否为交易日
        
        Args:
            date: 日期
            
        Returns:
            True if trading day, False otherwise
        """
        try:
            # 使用chinesecalendar判断（已考虑节假日调休）
            return is_workday(date)
        except Exception as e:
            logger.warning(f"Failed to check if {date} is workday: {e}, fallback to weekday check")
            # 降级为简单的工作日判断
            return date.weekday() < 5  # 周一到周五
    
    def is_trading_time(self, dt: datetime.datetime) -> bool:
        """
        判断是否在交易时间内
        
        Args:
            dt: 日期时间
            
        Returns:
            True if in trading hours, False otherwise
        """
        # 首先检查是否为交易日
        if not self.is_trading_day(dt.date()):
            return False
        
        current_time = dt.time()
        
        # 检查是否在上午或下午交易时段
        in_morning = self.morning_start <= current_time <= self.morning_end
        in_afternoon = self.afternoon_start <= current_time <= self.afternoon_end
        
        return in_morning or in_afternoon
    
    def is_call_auction_time(self, dt: datetime.datetime) -> bool:
        """
        判断是否在集合竞价时间
        
        Args:
            dt: 日期时间
            
        Returns:
            True if in call auction time
        """
        if not self.is_trading_day(dt.date()):
            return False
        
        current_time = dt.time()
        
        # 开盘集合竞价
        in_morning_auction = self.call_auction_start <= current_time <= self.call_auction_end
        
        # 尾盘集合竞价
        in_close_auction = self.close_auction_start <= current_time <= self.close_auction_end
        
        return in_morning_auction or in_close_auction
    
    def get_next_trading_day(self, date: datetime.date) -> datetime.date:
        """
        获取下一个交易日
        
        Args:
            date: 当前日期
            
        Returns:
            下一个交易日
        """
        next_day = date + datetime.timedelta(days=1)
        
        # 最多查找30天
        for _ in range(30):
            if self.is_trading_day(next_day):
                return next_day
            next_day += datetime.timedelta(days=1)
        
        # 如果30天内没有交易日，返回原日期+1
        logger.warning(f"No trading day found within 30 days from {date}")
        return date + datetime.timedelta(days=1)
    
    def get_previous_trading_day(self, date: datetime.date) -> datetime.date:
        """
        获取上一个交易日
        
        Args:
            date: 当前日期
            
        Returns:
            上一个交易日
        """
        prev_day = date - datetime.timedelta(days=1)
        
        # 最多查找30天
        for _ in range(30):
            if self.is_trading_day(prev_day):
                return prev_day
            prev_day -= datetime.timedelta(days=1)
        
        # 如果30天内没有交易日，返回原日期-1
        logger.warning(f"No trading day found within 30 days before {date}")
        return date - datetime.timedelta(days=1)
    
    def get_trading_days(self, start_date: datetime.date, end_date: datetime.date) -> List[datetime.date]:
        """
        获取时间范围内的所有交易日
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            交易日列表
        """
        trading_days = []
        current_date = start_date
        
        while current_date <= end_date:
            if self.is_trading_day(current_date):
                trading_days.append(current_date)
            current_date += datetime.timedelta(days=1)
        
        return trading_days
    
    def get_trading_minutes(self, date: datetime.date) -> List[datetime.datetime]:
        """
        获取某一交易日的所有交易分钟时间点
        
        Args:
            date: 日期
            
        Returns:
            交易分钟时间点列表
        """
        if not self.is_trading_day(date):
            return []
        
        minutes = []
        
        # 上午交易时段（09:30 - 11:30，共120分钟）
        morning_start = datetime.datetime.combine(date, self.morning_start)
        for i in range(120):
            minutes.append(morning_start + datetime.timedelta(minutes=i))
        
        # 下午交易时段（13:00 - 15:00，共120分钟）
        afternoon_start = datetime.datetime.combine(date, self.afternoon_start)
        for i in range(120):
            minutes.append(afternoon_start + datetime.timedelta(minutes=i))
        
        return minutes
    
    def get_market_open_time(self, date: datetime.date) -> datetime.datetime:
        """
        获取开盘时间
        
        Args:
            date: 日期
            
        Returns:
            开盘时间
        """
        return datetime.datetime.combine(date, self.morning_start)
    
    def get_market_close_time(self, date: datetime.date) -> datetime.datetime:
        """
        获取收盘时间
        
        Args:
            date: 日期
            
        Returns:
            收盘时间
        """
        return datetime.datetime.combine(date, self.afternoon_end)
    
    def get_time_until_market_open(self, dt: datetime.datetime) -> Optional[datetime.timedelta]:
        """
        获取距离开盘的时间
        
        Args:
            dt: 当前时间
            
        Returns:
            距离开盘的时间间隔，如果已开盘则返回None
        """
        if self.is_trading_time(dt):
            return None
        
        # 获取下一个开盘时间
        if dt.time() < self.morning_start:
            # 今天还未开盘
            next_open = datetime.datetime.combine(dt.date(), self.morning_start)
        elif dt.time() < self.afternoon_start:
            # 今天上午已结束，等待下午开盘
            next_open = datetime.datetime.combine(dt.date(), self.afternoon_start)
        else:
            # 今天已收盘，等待下一个交易日
            next_day = self.get_next_trading_day(dt.date())
            next_open = datetime.datetime.combine(next_day, self.morning_start)
        
        return next_open - dt
    
    def get_time_until_market_close(self, dt: datetime.datetime) -> Optional[datetime.timedelta]:
        """
        获取距离收盘的时间
        
        Args:
            dt: 当前时间
            
        Returns:
            距离收盘的时间间隔，如果已收盘则返回None
        """
        if not self.is_trading_day(dt.date()):
            return None
        
        close_time = self.get_market_close_time(dt.date())
        
        if dt >= close_time:
            return None
        
        return close_time - dt


# 全局交易日历实例
_global_calendar: Optional[TradingCalendar] = None


def get_calendar() -> TradingCalendar:
    """
    获取全局交易日历实例（单例模式）
    
    Returns:
        交易日历实例
    """
    global _global_calendar
    
    if _global_calendar is None:
        _global_calendar = TradingCalendar()
    
    return _global_calendar
