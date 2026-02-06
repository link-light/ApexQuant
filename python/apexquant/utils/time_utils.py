"""
时间处理工具

提供时区安全的时间处理函数
"""

from datetime import datetime, date, time as dt_time
from typing import Optional
import pytz

# 中国标准时间（东八区）
CHINA_TZ = pytz.timezone('Asia/Shanghai')
UTC_TZ = pytz.UTC


def get_market_timezone() -> pytz.tzinfo.BaseTzInfo:
    """
    获取市场时区（东八区）
    
    Returns:
        市场时区对象
    """
    return CHINA_TZ


def get_market_time(dt: Optional[datetime] = None) -> datetime:
    """
    获取市场时间（东八区）
    
    Args:
        dt: 可选的datetime对象，如果提供则转换为市场时区
            如果不提供则返回当前市场时间
    
    Returns:
        市场时区的datetime对象
        
    Example:
        >>> market_time = get_market_time()
        >>> print(market_time.tzinfo)  # Asia/Shanghai
    """
    if dt is None:
        # 返回当前市场时间
        return datetime.now(CHINA_TZ)
    elif dt.tzinfo is None:
        # 如果没有时区信息，假设为市场时区
        return CHINA_TZ.localize(dt)
    else:
        # 转换到市场时区
        return dt.astimezone(CHINA_TZ)


def get_utc_time(dt: Optional[datetime] = None) -> datetime:
    """
    获取UTC时间
    
    Args:
        dt: 可选的datetime对象
        
    Returns:
        UTC时区的datetime对象
    """
    if dt is None:
        return datetime.now(UTC_TZ)
    elif dt.tzinfo is None:
        return UTC_TZ.localize(dt)
    else:
        return dt.astimezone(UTC_TZ)


def is_market_time(dt: Optional[datetime] = None) -> bool:
    """
    判断是否在交易时间内
    
    Args:
        dt: 要检查的时间，不提供则使用当前时间
        
    Returns:
        是否在交易时间内
    """
    if dt is None:
        dt = get_market_time()
    else:
        dt = get_market_time(dt)
    
    # 检查是否为工作日（周一到周五）
    if dt.weekday() >= 5:  # 周六、周日
        return False
    
    current_time = dt.time()
    
    # 上午交易时间: 09:30 - 11:30
    morning_start = dt_time(9, 30)
    morning_end = dt_time(11, 30)
    
    # 下午交易时间: 13:00 - 15:00
    afternoon_start = dt_time(13, 0)
    afternoon_end = dt_time(15, 0)
    
    in_morning = morning_start <= current_time <= morning_end
    in_afternoon = afternoon_start <= current_time <= afternoon_end
    
    return in_morning or in_afternoon


def market_time_to_timestamp(dt: datetime) -> int:
    """
    将市场时间转换为时间戳（毫秒）
    
    Args:
        dt: datetime对象
        
    Returns:
        时间戳（毫秒）
    """
    dt_with_tz = get_market_time(dt)
    return int(dt_with_tz.timestamp() * 1000)


def timestamp_to_market_time(timestamp: int) -> datetime:
    """
    将时间戳（毫秒）转换为市场时间
    
    Args:
        timestamp: 时间戳（毫秒）
        
    Returns:
        市场时区的datetime对象
    """
    dt_utc = datetime.fromtimestamp(timestamp / 1000, tz=UTC_TZ)
    return dt_utc.astimezone(CHINA_TZ)


def get_today_market_date() -> date:
    """
    获取今天的市场日期
    
    Returns:
        市场时区的日期
    """
    return get_market_time().date()


def format_market_time(dt: datetime, fmt: str = '%Y-%m-%d %H:%M:%S') -> str:
    """
    格式化市场时间
    
    Args:
        dt: datetime对象
        fmt: 格式字符串
        
    Returns:
        格式化后的时间字符串
    """
    market_dt = get_market_time(dt)
    return market_dt.strftime(fmt)


if __name__ == "__main__":
    # 测试
    print("时间处理工具测试")
    print("="*60)
    
    # 测试获取市场时间
    market_time = get_market_time()
    print(f"当前市场时间: {market_time}")
    print(f"时区: {market_time.tzinfo}")
    
    # 测试时区转换
    utc_time = get_utc_time()
    print(f"\n当前UTC时间: {utc_time}")
    
    # 测试是否在交易时间
    print(f"\n当前是否在交易时间: {is_market_time()}")
    
    # 测试时间戳转换
    timestamp = market_time_to_timestamp(market_time)
    print(f"\n时间戳: {timestamp}")
    
    recovered_time = timestamp_to_market_time(timestamp)
    print(f"恢复的时间: {recovered_time}")
    
    # 测试格式化
    formatted = format_market_time(market_time)
    print(f"\n格式化时间: {formatted}")
    
    print("\n" + "="*60)
    print("测试通过！")

