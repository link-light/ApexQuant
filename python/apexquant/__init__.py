"""
ApexQuant - AI 驱动的混合语言量化交易系统
高性能 C++ 引擎 × 智能 Python AI
"""

__version__ = "1.0.0"
__author__ = "ApexQuant Team"

# 尝试导入 C++ 核心模块
try:
    from . import apexquant_core
    
    # 导出核心数据结构
    Tick = apexquant_core.Tick
    Bar = apexquant_core.Bar
    Position = apexquant_core.Position
    Order = apexquant_core.Order
    
    # 导出枚举
    OrderSide = apexquant_core.OrderSide
    OrderType = apexquant_core.OrderType
    OrderStatus = apexquant_core.OrderStatus
    
    # 导出工具函数
    calculate_mean = apexquant_core.calculate_mean
    calculate_std = apexquant_core.calculate_std
    calculate_max = apexquant_core.calculate_max
    calculate_min = apexquant_core.calculate_min
    calculate_median = apexquant_core.calculate_median
    calculate_covariance = apexquant_core.calculate_covariance
    calculate_correlation = apexquant_core.calculate_correlation
    cumulative_sum = apexquant_core.cumulative_sum
    rolling_mean = apexquant_core.rolling_mean
    pct_change = apexquant_core.pct_change
    
    __all__ = [
        # 数据结构
        'Tick', 'Bar', 'Position', 'Order',
        # 枚举
        'OrderSide', 'OrderType', 'OrderStatus',
        # 工具函数
        'calculate_mean', 'calculate_std', 'calculate_max', 'calculate_min',
        'calculate_median', 'calculate_covariance', 'calculate_correlation',
        'cumulative_sum', 'rolling_mean', 'pct_change',
    ]
    
    _core_loaded = True
    
except ImportError as e:
    import warnings
    warnings.warn(
        f"无法导入 C++ 核心模块: {e}\n"
        "请先编译 C++ 模块: mkdir build && cd build && cmake .. && cmake --build .",
        ImportWarning
    )
    _core_loaded = False
    __all__ = []


def is_core_loaded():
    """检查 C++ 核心模块是否成功加载"""
    return _core_loaded


def get_version():
    """获取版本信息"""
    info = {
        'python_version': __version__,
        'core_loaded': _core_loaded,
    }
    
    if _core_loaded:
        info['core_version'] = apexquant_core.__version__
    
    return info


def print_info():
    """打印系统信息"""
    print("=" * 60)
    print("ApexQuant - AI 驱动的混合语言量化交易系统")
    print("=" * 60)
    print(f"版本: {__version__}")
    print(f"作者: {__author__}")
    print(f"C++ 核心模块: {'已加载 ✓' if _core_loaded else '未加载 ✗'}")
    
    if _core_loaded:
        print(f"C++ 核心版本: {apexquant_core.__version__}")
    
    print("=" * 60)

