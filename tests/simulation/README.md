# ApexQuant C++ Simulation Module Tests

## 测试说明

C++模拟盘模块的测试需要在编译后进行。

## 测试方式

### 方式1：通过Python测试C++模块

编译完成后，运行Python测试即可验证C++模块：

```bash
# 编译C++模块
build.bat  # Windows
# 或
./build.sh  # Linux

# 运行Python集成测试
cd python
python tests/test_integration.py
```

### 方式2：使用示例脚本测试

```bash
# 使用Mock数据源测试（不需要网络）
python examples/run_simulation.py \
  --mode backtest \
  --symbol TEST.SH \
  --start-date 2024-01-01 \
  --end-date 2024-01-31 \
  --strategy buy_hold
```

## C++单元测试框架（可选）

如需要单独测试C++模块，可以使用以下测试框架：

### 使用Google Test

1. 安装Google Test
2. 在 `cpp/CMakeLists.txt` 中添加：

```cmake
enable_testing()
find_package(GTest REQUIRED)

add_executable(simulation_tests
    tests/test_account.cpp
    tests/test_matcher.cpp
    tests/test_exchange.cpp
)

target_link_libraries(simulation_tests
    GTest::GTest
    GTest::Main
)

add_test(NAME simulation_tests COMMAND simulation_tests)
```

### 测试示例

```cpp
// tests/test_account.cpp
#include <gtest/gtest.h>
#include "simulation/simulation_account.h"

TEST(SimulationAccountTest, InitialCapital) {
    SimulationAccount account("TEST001", 1000000.0);
    EXPECT_EQ(account.get_available_cash(), 1000000.0);
    EXPECT_EQ(account.get_total_assets(), 1000000.0);
}

TEST(SimulationAccountTest, FreezeCash) {
    SimulationAccount account("TEST001", 1000000.0);
    EXPECT_TRUE(account.freeze_cash(500000.0));
    EXPECT_EQ(account.get_available_cash(), 500000.0);
    EXPECT_EQ(account.get_frozen_cash(), 500000.0);
}
```

## 当前测试覆盖

✅ Python业务层完整测试  
✅ 端到端集成测试  
✅ Mock数据源测试  
⏸️ C++单元测试（可选，通过Python集成测试已覆盖核心功能）

## 快速验证

最快的验证方式是运行集成测试：

```bash
cd python
python tests/test_integration.py
```

如果测试通过，说明C++模块工作正常。
