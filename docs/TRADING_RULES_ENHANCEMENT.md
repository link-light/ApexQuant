# ApexQuant 交易规则完善文档

**完成时间**: 2026-02-05  
**版本**: v1.0

---

## 📋 概述

本次更新完善了ApexQuant模拟盘系统的7项重要交易规则和市场规则，使其更加符合A股真实交易环境。

---

## ✅ 完成的改进清单

### 1. 最小交易单位100股验证 ✓

**位置**: `cpp/src/simulation/order_matcher.cpp`

**改进内容**:
- 新增 `validate_order_volume()` 方法
- 买入必须是100股的整数倍
- 卖出可以不是100股整数倍（清仓时最后不足一手）
- 单笔最大100万股限制

**代码示例**:
```cpp
std::pair<bool, std::string> OrderMatcher::validate_order_volume(
    int64_t volume, OrderSide side, int64_t available_volume
) {
    if (volume <= 0) return {false, "Order volume must be positive"};
    if (volume > 1000000) return {false, "Order volume exceeds maximum"};
    
    // 买入必须100的整数倍
    if (side == OrderSide::BUY && volume % 100 != 0) {
        return {false, "Buy volume must be multiple of 100"};
    }
    
    return {true, "OK"};
}
```

**测试用例**:
- ✓ 买入100股: 通过
- ✗ 买入99股: 拒绝
- ✓ 卖出99股（清仓）: 通过
- ✗ 买入1000001股: 拒绝

---

### 2. 佣金最低5元限制 ✓

**位置**: `cpp/src/simulation/order_matcher.cpp`

**改进内容**:
- 修改 `calculate_total_commission()` 方法
- 佣金计算公式：`max(amount * commission_rate, 5.0)`
- 即使小额交易，也需支付最低5元佣金

**示例**:
```cpp
// 交易1000元，佣金率万2.5
// 应收佣金 = 1000 * 0.00025 = 0.25元
// 实际收取 = max(0.25, 5.0) = 5元
```

**影响**:
- 小额交易成本显著增加
- 更真实地模拟A股交易成本

---

### 3. 过户费计算（上海A股） ✓

**位置**: `cpp/src/simulation/order_matcher.cpp`

**改进内容**:
- 新增过户费计算逻辑
- 仅上海A股（代码以6开头或sh.6开头）收取
- 费率：每股0.002分 = 0.00002元
- 买卖双向收取

**完整费用构成**:
```
总费用 = 佣金 + 印花税 + 过户费

1. 佣金（买卖都有，最低5元）：amount * 0.00025
2. 印花税（仅卖出）：amount * 0.001
3. 过户费（仅沪市，买卖都有）：volume * 0.00002
```

**示例**:
```cpp
// 买入 sh.600519 贵州茅台 1000股 @ 1800元
// 金额 = 1,800,000元
// 佣金 = max(1,800,000 * 0.00025, 5) = 450元
// 过户费 = 1000 * 0.00002 = 0.02元
// 总费用 = 450 + 0.02 = 450.02元

// 卖出 sh.600519 贵州茅台 1000股 @ 1800元
// 佣金 = 450元
// 印花税 = 1,800,000 * 0.001 = 1,800元
// 过户费 = 0.02元
// 总费用 = 450 + 1,800 + 0.02 = 2,250.02元
```

---

### 4. 涨跌停排队机制 ✓

**位置**: 
- `cpp/include/simulation/limit_queue.h`
- `cpp/src/simulation/limit_queue.cpp`

**改进内容**:
- 新建 `LimitQueue` 类管理涨跌停排队
- 涨停时买单排队，跌停时卖单排队
- 价格打开时按时间优先成交
- 仍在涨跌停时，模拟部分成交（10%概率）

**工作流程**:
```
1. 订单提交 → 检测涨跌停
2. 如果涨停 → 买单加入涨停队列
3. 如果跌停 → 卖单加入跌停队列
4. 每个tick检查：
   - 价格打开 → 全部成交
   - 仍涨停/跌停 → 部分成交（模拟市场深度）
```

**API**:
```cpp
LimitQueue queue;

// 加入排队
queue.add_to_limit_up_queue(order);
queue.add_to_limit_down_queue(order);

// 尝试成交
auto filled = queue.try_fill_limit_up_orders(symbol, tick);

// 撤单（从队列移除）
queue.remove_from_queue(order_id);
```

**涨跌停幅度**:
- 普通A股：±10%
- ST股票：±5%
- 科创板（688）：±20%
- 创业板（300）：±20%
- 北交所（8/4开头）：±30%

---

### 5. 停牌处理 ✓

**位置**: `python/apexquant/simulation/stock_status.py`

**改进内容**:
- 新建 `StockStatusManager` 类
- 检测股票状态：正常/停牌/退市/涨停/跌停
- 状态缓存机制（TTL=1小时）
- 停牌期间禁止交易

**股票状态**:
```python
class StockStatus(Enum):
    NORMAL = "正常交易"
    SUSPENDED = "停牌"
    DELISTING = "退市整理"
    LIMIT_UP = "涨停"
    LIMIT_DOWN = "跌停"
    UNKNOWN = "未知"
```

**使用示例**:
```python
from apexquant.simulation.stock_status import get_status_manager

manager = get_status_manager()

# 检查状态
status = manager.get_stock_status("600519")

# 检查是否可交易
if not manager.is_tradable("600519"):
    print("该股票不可交易（停牌或退市）")

# 手动标记停牌
manager.mark_as_suspended("600000")
```

**停牌检测方法**:
1. 从AKShare实时行情中获取数据
2. 如果成交量为0 → 可能停牌
3. 如果股票不在行情列表中 → 可能停牌或退市
4. 支持手动标记（用于已知停牌信息）

---

### 6. 集合竞价特殊规则 ✓

**位置**: `python/apexquant/simulation/trading_calendar.py`

**改进内容**:
- 新增 `can_cancel_order()` 方法：判断是否可撤单
- 新增 `is_continuous_auction_time()` 方法
- 新增 `get_auction_phase()` 方法：获取当前交易阶段

**集合竞价时间**:
```
开盘集合竞价: 9:15 - 9:25
  - 9:15-9:20: 可以挂单和撤单
  - 9:20-9:25: 只能挂单，不能撤单！⚠️
  - 9:25: 统一撮合

收盘集合竞价（深圳）: 14:57 - 15:00
  - 14:57-15:00: 只能挂单，不能撤单！⚠️
  - 15:00: 统一撮合
```

**交易阶段**:
```python
phases = [
    "BEFORE_OPEN",           # 开盘前
    "CALL_AUCTION_OPEN",     # 开盘集合竞价 9:15-9:25
    "CONTINUOUS_MORNING",    # 上午连续竞价 9:30-11:30
    "NOON_BREAK",            # 午休 11:30-13:00
    "CONTINUOUS_AFTERNOON",  # 下午连续竞价 13:00-14:57
    "CALL_AUCTION_CLOSE",    # 收盘集合竞价 14:57-15:00
    "AFTER_CLOSE",           # 收盘后
    "NON_TRADING_DAY"        # 非交易日
]
```

**使用示例**:
```python
from apexquant.simulation.trading_calendar import get_calendar

calendar = get_calendar()

# 检查是否可以撤单
if calendar.can_cancel_order(datetime.now()):
    # 执行撤单操作
    pass
else:
    print("当前时间不允许撤单（9:20-9:25 或 14:57-15:00）")

# 获取当前交易阶段
phase = calendar.get_auction_phase(datetime.now())
print(f"当前阶段: {phase}")
```

---

### 7. 可用资金 vs 可取资金分离 ✓

**位置**: 
- `cpp/include/simulation/simulation_account.h`
- `cpp/src/simulation/simulation_account.cpp`

**改进内容**:
- 新增 `withdrawable_cash_` 成员变量
- 新增 `get_withdrawable_cash()` 方法
- 新增 `daily_settlement()` 方法处理T+1结算
- 卖出股票后：当日可用，次日可取

**资金类型**:
```cpp
class SimulationAccount {
private:
    double available_cash_;      // 可用资金（可交易）
    double withdrawable_cash_;   // 可取资金（可提现，T+1）
    double frozen_cash_;         // 冻结资金
    double today_sell_amount_;   // 今日卖出金额
};
```

**T+1资金规则**:
```
Day 0: 持有股票1000股
Day 1: 
  - 卖出股票，收入10万元
  - available_cash += 10万（可用于再次买入）
  - withdrawable_cash 不变（今日不可取）
  - today_sell_amount = 10万
  
Day 2 开盘:
  - 调用 daily_settlement()
  - withdrawable_cash += 10万（昨日卖出的钱今日可取）
  - today_sell_amount = 0（清零）
```

**使用场景**:
- `available_cash`: 用于判断是否可以下单买入
- `withdrawable_cash`: 用于判断是否可以提现
- 真实交易中：卖出股票后当日可用资金买股票，但不能提现

**API**:
```cpp
// 获取可用资金
double cash = account.get_available_cash();

// 获取可取资金
double withdrawable = account.get_withdrawable_cash();

// 每日结算（在每日开盘时调用）
account.daily_settlement(20260206);
```

---

## 📊 改进前后对比

| 规则项 | 改进前 | 改进后 | 符合A股规则 |
|-------|--------|--------|------------|
| **最小交易单位** | 可以买1股 | 买入必须100整数倍 | ✅ |
| **佣金计算** | 按比例，可能<5元 | 最低5元 | ✅ |
| **过户费** | 无 | 沪市收取0.002分/股 | ✅ |
| **涨跌停处理** | 直接拒绝 | 排队等待，部分成交 | ✅ |
| **停牌检测** | 无 | 自动检测+手动标记 | ✅ |
| **集合竞价** | 仅时间判断 | 9:20-9:25不能撤单 | ✅ |
| **资金T+1** | 无区分 | 可用vs可取分离 | ✅ |

---

## 🔧 使用指南

### 编译更新

```bash
cd build
cmake --build . --config Release

# 或者使用构建脚本
cd ..
./build.sh  # Linux/Mac
# 或
build.bat   # Windows
```

### Python绑定更新

需要确保pybind11绑定暴露了新的方法：

```cpp
// 在 bindings.cpp 中添加
py::class_<SimulationAccount>(m, "SimulationAccount")
    .def("get_available_cash", &SimulationAccount::get_available_cash)
    .def("get_withdrawable_cash", &SimulationAccount::get_withdrawable_cash)  // 新增
    .def("daily_settlement", &SimulationAccount::daily_settlement);  // 新增
```

### 集成到模拟盘控制器

```python
from apexquant.simulation import SimulationController
from apexquant.simulation.stock_status import get_status_manager
from apexquant.simulation.trading_calendar import get_calendar

controller = SimulationController()
status_mgr = get_status_manager()
calendar = get_calendar()

# 下单前检查
def submit_order(symbol, side, volume, price):
    # 1. 检查停牌
    if not status_mgr.is_tradable(symbol):
        return None, "股票停牌或退市"
    
    # 2. 检查交易时间
    if not calendar.is_trading_time(datetime.now()):
        return None, "非交易时间"
    
    # 3. 检查数量（100整数倍）
    if side == "BUY" and volume % 100 != 0:
        return None, "买入数量必须是100的整数倍"
    
    # 4. 提交订单
    order_id = controller.submit_order(symbol, side, volume, price)
    return order_id, "成功"

# 撤单前检查
def cancel_order(order_id):
    # 检查是否可以撤单
    if not calendar.can_cancel_order(datetime.now()):
        return False, "当前时间不允许撤单（9:20-9:25或14:57-15:00）"
    
    success = controller.cancel_order(order_id)
    return success, "成功" if success else "失败"

# 每日结算
def on_day_end(current_date):
    # 调用每日结算
    controller.daily_settlement(current_date)
    
    # 清空状态缓存
    status_mgr.clear_cache()
```

---

## 📝 待完善项（未来版本）

以下规则已识别但暂未实现，可在后续版本中添加：

### P1 重要
1. **融资融券规则**
2. **大宗交易规则**
3. **分红派息自动处理**
4. **配股和增发**

### P2 次要
5. **盘后定价交易**
6. **新股申购**
7. **ETF申赎机制**
8. **异常波动监控**（如日内振幅>20%预警）

---

## 🧪 测试建议

### 单元测试

```python
def test_order_volume_validation():
    """测试100股整数倍验证"""
    assert validate_order_volume(100, "BUY") == True
    assert validate_order_volume(99, "BUY") == False
    assert validate_order_volume(99, "SELL") == True  # 卖出可以

def test_minimum_commission():
    """测试最低5元佣金"""
    # 小额交易
    fee = calculate_commission(1000, 0.00025)
    assert fee >= 5.0

def test_transfer_fee():
    """测试过户费"""
    # 上海股票
    fee_sh = calculate_total_commission("SELL", "sh.600519", 10, 1000, 0.00025)
    # 深圳股票
    fee_sz = calculate_total_commission("SELL", "sz.000001", 10, 1000, 0.00025)
    # 上海应该更贵（多了过户费）
    assert fee_sh > fee_sz

def test_limit_queue():
    """测试涨跌停排队"""
    queue = LimitQueue()
    order = create_test_order("BUY", "600519", 1800, 100)
    
    # 加入涨停队列
    queue.add_to_limit_up_queue(order)
    assert queue.get_limit_up_queue_size("600519") == 1
    
    # 价格打开后成交
    tick = create_test_tick("600519", 1790)  # 不再涨停
    filled = queue.try_fill_limit_up_orders("600519", tick)
    assert len(filled) == 1

def test_stock_suspension():
    """测试停牌检测"""
    manager = StockStatusManager()
    
    # 手动标记停牌
    manager.mark_as_suspended("600000")
    assert manager.is_suspended("600000") == True
    assert manager.is_tradable("600000") == False

def test_cannot_cancel_in_auction():
    """测试集合竞价期间不能撤单"""
    calendar = TradingCalendar()
    
    # 9:22，在9:20-9:25期间
    dt = datetime(2026, 2, 6, 9, 22)
    assert calendar.can_cancel_order(dt) == False
    
    # 9:30，可以撤单
    dt = datetime(2026, 2, 6, 9, 30)
    assert calendar.can_cancel_order(dt) == True

def test_withdrawable_cash():
    """测试可取资金T+1"""
    account = SimulationAccount("test", 100000)
    
    # Day 1: 卖出获得10000元
    account.reduce_position("600519", 100, 100, realized_pnl)
    assert account.get_available_cash() == 110000  # 可用
    assert account.get_withdrawable_cash() == 100000  # 不可取
    
    # Day 2: 结算后可取
    account.daily_settlement(20260207)
    assert account.get_withdrawable_cash() == 110000  # 可取
```

---

## 📚 参考资料

- [上海证券交易所交易规则](http://www.sse.com.cn/)
- [深圳证券交易所交易规则](http://www.szse.cn/)
- [中国证券登记结算有限责任公司收费标准](http://www.chinaclear.cn/)

---

## 📞 联系方式

如有问题或建议，请提交Issue或PR。

**更新日期**: 2026-02-05  
**文档版本**: v1.0
















