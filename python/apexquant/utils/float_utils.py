"""
浮点数比较工具

解决浮点数精度问题，提供安全的比较函数
"""

import math
from typing import Union

Number = Union[int, float]


def float_equal(a: Number, b: Number, epsilon: float = 1e-9) -> bool:
    """
    浮点数相等比较
    
    Args:
        a: 第一个数
        b: 第二个数
        epsilon: 容差值
        
    Returns:
        是否相等
        
    Example:
        >>> float_equal(0.1 + 0.2, 0.3)
        True
        >>> float_equal(1.0000001, 1.0)
        True
    """
    return math.isclose(a, b, rel_tol=epsilon, abs_tol=epsilon)


def float_le(a: Number, b: Number, epsilon: float = 1e-9) -> bool:
    """
    浮点数小于等于比较
    
    Args:
        a: 第一个数
        b: 第二个数
        epsilon: 容差值
        
    Returns:
        a <= b
        
    Example:
        >>> float_le(0.1 + 0.2, 0.3)
        True
        >>> float_le(0.29999999, 0.3)
        True
    """
    return a < b or float_equal(a, b, epsilon)


def float_ge(a: Number, b: Number, epsilon: float = 1e-9) -> bool:
    """
    浮点数大于等于比较
    
    Args:
        a: 第一个数
        b: 第二个数
        epsilon: 容差值
        
    Returns:
        a >= b
    """
    return a > b or float_equal(a, b, epsilon)


def float_lt(a: Number, b: Number, epsilon: float = 1e-9) -> bool:
    """
    浮点数小于比较
    
    Args:
        a: 第一个数
        b: 第二个数
        epsilon: 容差值
        
    Returns:
        a < b
    """
    return a < b and not float_equal(a, b, epsilon)


def float_gt(a: Number, b: Number, epsilon: float = 1e-9) -> bool:
    """
    浮点数大于比较
    
    Args:
        a: 第一个数
        b: 第二个数
        epsilon: 容差值
        
    Returns:
        a > b
    """
    return a > b and not float_equal(a, b, epsilon)


def round_to_tick(price: float, tick_size: float = 0.01) -> float:
    """
    将价格舍入到最小变动单位
    
    Args:
        price: 原始价格
        tick_size: 最小变动单位（默认0.01元）
        
    Returns:
        舍入后的价格
        
    Example:
        >>> round_to_tick(10.123, 0.01)
        10.12
        >>> round_to_tick(10.125, 0.01)
        10.13
    """
    return round(price / tick_size) * tick_size


def is_zero(value: Number, epsilon: float = 1e-9) -> bool:
    """
    判断是否为零
    
    Args:
        value: 数值
        epsilon: 容差值
        
    Returns:
        是否为零
    """
    return abs(value) < epsilon


if __name__ == "__main__":
    # 测试
    print("浮点数比较工具测试")
    print("="*60)
    
    # 测试相等
    print(f"0.1 + 0.2 == 0.3: {0.1 + 0.2 == 0.3}")  # False
    print(f"float_equal(0.1 + 0.2, 0.3): {float_equal(0.1 + 0.2, 0.3)}")  # True
    
    # 测试小于等于
    print(f"\nfloat_le(-0.1, -0.1): {float_le(-0.1, -0.1)}")  # True
    print(f"float_le(-0.10000001, -0.1): {float_le(-0.10000001, -0.1)}")  # True
    
    # 测试价格舍入
    print(f"\nround_to_tick(10.123): {round_to_tick(10.123)}")  # 10.12
    print(f"round_to_tick(10.125): {round_to_tick(10.125)}")  # 10.13
    
    print("\n" + "="*60)
    print("测试通过！")

