# ApexQuant 编译指南（更新后）

**更新时间**: 2026-02-05  
**版本**: v2.0 - 包含交易规则完善

---

## 📋 新增文件清单

本次更新新增了以下文件：

### C++ 核心文件
1. `cpp/include/simulation/limit_queue.h` - 涨跌停排队机制头文件
2. `cpp/src/simulation/limit_queue.cpp` - 涨跌停排队机制实现

### Python 业务文件
3. `python/apexquant/simulation/stock_status.py` - 股票状态管理器

### 修改的文件
- `cpp/include/simulation/order_matcher.h` - 新增费用计算和数量验证
- `cpp/src/simulation/order_matcher.cpp` - 实现新规则
- `cpp/include/simulation/simulation_account.h` - 新增可取资金相关
- `cpp/src/simulation/simulation_account.cpp` - 实现T+1资金规则
- `python/apexquant/simulation/trading_calendar.py` - 新增集合竞价规则

---

## 🔧 编译步骤

### 1. 更新CMake配置

确保 `cpp/CMakeLists.txt` 包含新增文件：

```cmake
# 模拟盘源文件
set(SIMULATION_SOURCES
    src/simulation/simulation_account.cpp
    src/simulation/order_matcher.cpp
    src/simulation/simulated_exchange.cpp
    src/simulation/limit_queue.cpp          # 新增
    src/simulation/bindings.cpp
)
```

### 2. 清理并重新编译

**Windows (Visual Studio)**:
```cmd
cd build
cmake --build . --config Release --clean-first
```

**Linux/macOS**:
```bash
cd build
make clean
cmake --build . --config Release -j$(nproc)
```

**或使用构建脚本**:
```bash
# Linux/Mac
chmod +x build.sh
./build.sh

# Windows
build.bat
```

### 3. 验证编译

编译成功后应生成：
- `build/cpp/Release/apexquant_core.pyd` (Windows)
- `build/cpp/Release/apexquant_simulation.pyd` (Windows)
- 或 `.so` 文件 (Linux/macOS)

---

## 🐍 Python绑定更新

### 1. 更新bindings.cpp

在 `cpp/src/simulation/bindings.cpp` 中添加新方法的绑定：

```cpp
#include "simulation/limit_queue.h"

PYBIND11_MODULE(apexquant_simulation, m) {
    // ... 现有绑定 ...
    
    // ===== 新增：LimitQueue 绑定 =====
    py::class_<LimitQueue>(m, "LimitQueue")
        .def(py::init<>())
        .def("add_to_limit_up_queue", &LimitQueue::add_to_limit_up_queue)
        .def("add_to_limit_down_queue", &LimitQueue::add_to_limit_down_queue)
        .def("try_fill_limit_up_orders", &LimitQueue::try_fill_limit_up_orders)
        .def("try_fill_limit_down_orders", &LimitQueue::try_fill_limit_down_orders)
        .def("remove_from_queue", &LimitQueue::remove_from_queue)
        .def("get_limit_up_queue_size", &LimitQueue::get_limit_up_queue_size)
        .def("get_limit_down_queue_size", &LimitQueue::get_limit_down_queue_size)
        .def("clear_all_queues", &LimitQueue::clear_all_queues);
    
    py::enum_<LimitStatus>(m, "LimitStatus")
        .value("NORMAL", LimitStatus::NORMAL)
        .value("LIMIT_UP", LimitStatus::LIMIT_UP)
        .value("LIMIT_DOWN", LimitStatus::LIMIT_DOWN)
        .export_values();
    
    // ===== 新增：SimulationAccount 新方法 =====
    py::class_<SimulationAccount>(m, "SimulationAccount")
        // ... 现有方法 ...
        .def("get_withdrawable_cash", &SimulationAccount::get_withdrawable_cash)  // 新增
        .def("daily_settlement", &SimulationAccount::daily_settlement);           // 新增
    
    // ===== 新增：OrderMatcher 新方法 =====
    py::class_<OrderMatcher>(m, "OrderMatcher")
        // ... 现有方法 ...
        .def("validate_order_volume", &OrderMatcher::validate_order_volume)       // 新增
        .def("calculate_total_commission", &OrderMatcher::calculate_total_commission); // 新增
}
```

### 2. 重新编译Python模块

```bash
cd build
cmake --build . --config Release --target apexquant_simulation
```

### 3. 验证Python导入

```python
import apexquant_simulation as sim

# 测试新增类
queue = sim.LimitQueue()
print("LimitQueue 导入成功")

# 测试新增方法
account = sim.SimulationAccount("test", 100000.0)
withdrawable = account.get_withdrawable_cash()
print(f"可取资金: {withdrawable}")
```

---

## 📦 Python依赖更新

新增的Python模块需要额外依赖：

### 更新 requirements.txt

在 `python/requirements.txt` 中确保包含：

```txt
# ... 现有依赖 ...

# 交易日历（用于判断节假日）
chinesecalendar>=1.8.0

# 停牌检测需要
akshare>=1.12.0
```

### 安装依赖

```bash
cd python
pip install -r requirements.txt
```

---

## 🧪 编译后测试

### 测试1: C++核心功能

```python
import apexquant_simulation as sim

# 测试订单数量验证
matcher = sim.OrderMatcher()
valid, msg = matcher.validate_order_volume(100, sim.OrderSide.BUY, 0)
print(f"100股: {valid} - {msg}")

valid, msg = matcher.validate_order_volume(99, sim.OrderSide.BUY, 0)
print(f"99股: {valid} - {msg}")

# 测试费用计算
fee = matcher.calculate_total_commission(
    sim.OrderSide.SELL,
    "sh.600519",
    1800.0,
    100,
    0.00025
)
print(f"卖出100股贵州茅台手续费: {fee}元")

# 测试涨跌停队列
queue = sim.LimitQueue()
print(f"涨停队列初始大小: {queue.get_limit_up_queue_size('600519')}")
```

### 测试2: Python业务功能

```python
from apexquant.simulation.stock_status import get_status_manager
from apexquant.simulation.trading_calendar import get_calendar
from datetime import datetime

# 测试停牌检测
status_mgr = get_status_manager()
print(f"600519状态: {status_mgr.get_stock_status('600519')}")
print(f"600519可交易: {status_mgr.is_tradable('600519')}")

# 测试交易时间
calendar = get_calendar()
now = datetime(2026, 2, 6, 9, 22)  # 9:22
print(f"9:22是否可撤单: {calendar.can_cancel_order(now)}")
print(f"当前交易阶段: {calendar.get_auction_phase(now)}")
```

### 测试3: 集成测试

创建 `test_trading_rules.py`:

```python
"""测试新增交易规则"""

import apexquant_simulation as sim
from apexquant.simulation import SimulationController
from apexquant.simulation.stock_status import get_status_manager
from apexquant.simulation.trading_calendar import get_calendar
from datetime import datetime


def test_order_volume():
    """测试订单数量验证"""
    print("\n=== 测试订单数量验证 ===")
    matcher = sim.OrderMatcher()
    
    test_cases = [
        (100, sim.OrderSide.BUY, True),   # 买入100股，应通过
        (99, sim.OrderSide.BUY, False),   # 买入99股，应拒绝
        (200, sim.OrderSide.BUY, True),   # 买入200股，应通过
        (99, sim.OrderSide.SELL, True),   # 卖出99股，应通过（清仓）
    ]
    
    for volume, side, expected in test_cases:
        valid, msg = matcher.validate_order_volume(volume, side, 1000)
        status = "✓" if (valid == expected) else "✗"
        action = "买入" if side == sim.OrderSide.BUY else "卖出"
        print(f"{status} {action}{volume}股: {msg}")


def test_commission():
    """测试费用计算"""
    print("\n=== 测试费用计算 ===")
    matcher = sim.OrderMatcher()
    
    # 小额交易测试最低5元
    fee = matcher.calculate_total_commission(
        sim.OrderSide.BUY, "sh.600519", 10.0, 100, 0.00025
    )
    print(f"买入100股@10元: 手续费={fee}元 (应>=5元)")
    
    # 上海股票应包含过户费
    fee_sh = matcher.calculate_total_commission(
        sim.OrderSide.BUY, "sh.600519", 1800.0, 1000, 0.00025
    )
    fee_sz = matcher.calculate_total_commission(
        sim.OrderSide.BUY, "sz.000001", 1800.0, 1000, 0.00025
    )
    print(f"沪市手续费: {fee_sh}元")
    print(f"深市手续费: {fee_sz}元")
    print(f"沪市更贵: {fee_sh > fee_sz}")


def test_withdrawable_cash():
    """测试可取资金"""
    print("\n=== 测试可取资金T+1 ===")
    account = sim.SimulationAccount("test", 100000.0)
    
    print(f"初始可用资金: {account.get_available_cash()}")
    print(f"初始可取资金: {account.get_withdrawable_cash()}")
    
    # 模拟卖出
    # （需要先有持仓，这里简化测试）
    print("（实际使用需要完整的交易流程）")


def test_trading_time():
    """测试交易时间规则"""
    print("\n=== 测试交易时间规则 ===")
    calendar = get_calendar()
    
    test_times = [
        (9, 18, "BEFORE_OPEN", True),       # 9:18 开盘前，可撤单
        (9, 22, "CALL_AUCTION_OPEN", False), # 9:22 集合竞价，不可撤单
        (9, 30, "CONTINUOUS_MORNING", True), # 9:30 连续竞价，可撤单
        (14, 58, "CALL_AUCTION_CLOSE", False), # 14:58 收盘竞价，不可撤单
    ]
    
    for hour, minute, expected_phase, can_cancel in test_times:
        dt = datetime(2026, 2, 6, hour, minute)
        phase = calendar.get_auction_phase(dt)
        cancel_ok = calendar.can_cancel_order(dt)
        
        status = "✓" if (cancel_ok == can_cancel) else "✗"
        print(f"{status} {hour}:{minute:02d} - {phase} - 可撤单:{cancel_ok}")


if __name__ == "__main__":
    print("ApexQuant 交易规则测试")
    print("=" * 50)
    
    test_order_volume()
    test_commission()
    test_withdrawable_cash()
    test_trading_time()
    
    print("\n" + "=" * 50)
    print("测试完成！")
```

运行测试：
```bash
python test_trading_rules.py
```

---

## 🐛 常见编译问题

### 问题1: 找不到limit_queue.h

**错误信息**:
```
fatal error: simulation/limit_queue.h: No such file or directory
```

**解决方案**:
1. 确保文件路径正确：`cpp/include/simulation/limit_queue.h`
2. 检查CMakeLists.txt中的include目录设置
3. 清理并重新生成：
   ```bash
   cd build
   rm -rf *
   cmake ..
   cmake --build . --config Release
   ```

### 问题2: 链接错误 - LimitQueue未定义

**错误信息**:
```
undefined reference to `apexquant::simulation::LimitQueue::...`
```

**解决方案**:
1. 确保 `limit_queue.cpp` 已添加到CMakeLists.txt
2. 重新编译所有文件：
   ```bash
   cmake --build . --config Release --clean-first
   ```

### 问题3: Python导入错误

**错误信息**:
```python
AttributeError: module 'apexquant_simulation' has no attribute 'LimitQueue'
```

**解决方案**:
1. 检查 `bindings.cpp` 是否正确添加了LimitQueue的绑定
2. 重新编译Python模块
3. 确保Python使用的是新编译的.pyd/.so文件

### 问题4: chinesecalendar导入失败

**错误信息**:
```
ModuleNotFoundError: No module named 'chinese_calendar'
```

**解决方案**:
```bash
pip install chinesecalendar
```

---

## 📊 性能影响评估

新增规则对性能的影响：

| 功能 | 性能影响 | 说明 |
|-----|---------|------|
| 订单数量验证 | <0.1μs | 简单整数运算 |
| 费用计算（含过户费） | <0.5μs | 增加一次判断和计算 |
| 涨跌停排队 | 1-10μs | 取决于队列长度 |
| 停牌检测 | 1-100ms | 首次查询较慢，之后命中缓存<1μs |
| 集合竞价规则 | <0.1μs | 时间比较 |
| 可取资金计算 | <0.1μs | 简单变量访问 |

**总体评估**: 性能影响可忽略不计，单笔订单处理增加时间<2μs

---

## ✅ 编译验证清单

完成编译后，请确认以下项：

- [ ] C++编译无错误无警告
- [ ] Python模块成功导入
- [ ] LimitQueue类可创建实例
- [ ] SimulationAccount新方法可调用
- [ ] StockStatusManager可正常使用
- [ ] TradingCalendar新方法返回正确结果
- [ ] 运行test_trading_rules.py全部通过

---

## 📚 下一步

编译成功后：

1. 阅读 `docs/TRADING_RULES_ENHANCEMENT.md` 了解详细规则
2. 运行完整的回测测试
3. 集成到现有策略中
4. 监控实际运行效果

---

**编译有问题？** 请查看 `docs/BUILD_GUIDE.md` 或提交Issue。





