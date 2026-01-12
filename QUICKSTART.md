# ApexQuant 快速开始指南

## Day 1 - 基础框架搭建完成 ✓

恭喜！Day 1 的所有任务已完成。现在让我们编译并测试系统。

## 📦 环境准备

### Windows

1. **安装 Visual Studio 2019/2022**
   - 确保安装了 "使用 C++ 的桌面开发" 工作负载
   - 下载地址: https://visualstudio.microsoft.com/

2. **安装 Python 3.9+**
   - 下载地址: https://www.python.org/downloads/
   - 安装时勾选 "Add Python to PATH"

3. **安装 CMake**
   - 下载地址: https://cmake.org/download/
   - 或使用: `pip install cmake`

### Linux

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y build-essential cmake python3 python3-pip python3-dev

# CentOS/RHEL
sudo yum install -y gcc-c++ cmake python3 python3-pip python3-devel
```

### macOS

```bash
# 安装 Xcode Command Line Tools
xcode-select --install

# 安装 CMake
brew install cmake python@3.9
```

## 🚀 编译安装

### 方法 1: 使用编译脚本（推荐）

**Windows:**
```cmd
build.bat
```

**Linux/macOS:**
```bash
chmod +x build.sh
./build.sh
```

### 方法 2: 手动编译

**步骤 1: 配置 CMake**

Windows:
```cmd
mkdir build
cd build
cmake .. -G "Visual Studio 17 2022" -A x64
```

Linux/macOS:
```bash
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
```

**步骤 2: 编译**

Windows:
```cmd
cmake --build . --config Release
```

Linux/macOS:
```bash
cmake --build . -j$(nproc)
```

**步骤 3: 安装 Python 依赖**

```bash
cd ..
pip install -r python/requirements.txt
```

## 🧪 运行测试

编译完成后，运行测试验证安装：

```bash
python python/tests/test_bridge.py
```

如果看到以下输出，说明安装成功：

```
╔══════════════════════════════════════════════════════════╗
║          ApexQuant Day 1 桥接测试                         ║
╚══════════════════════════════════════════════════════════╝

============================================================
ApexQuant - AI 驱动的混合语言量化交易系统
============================================================
版本: 1.0.0
作者: ApexQuant Team
C++ 核心模块: 已加载 ✓
C++ 核心版本: 1.0.0
============================================================

...

🎉 所有测试通过！Day 1 任务完成！
```

## 📝 使用示例

### 示例 1: 计算均值

```python
import apexquant as aq

data = [1.0, 2.0, 3.0, 4.0, 5.0]
mean = aq.calculate_mean(data)
print(f"均值: {mean}")  # 输出: 3.0
```

### 示例 2: 创建 K 线数据

```python
from datetime import datetime
import apexquant as aq

bar = aq.Bar(
    symbol="600519.SH",
    timestamp=int(datetime.now().timestamp() * 1000),
    open=1800.0,
    high=1850.0,
    low=1790.0,
    close=1820.0,
    volume=5000000
)

print(f"涨跌幅: {bar.change_rate():.2%}")
print(f"是否阳线: {bar.is_bullish()}")
```

### 示例 3: 管理持仓

```python
import apexquant as aq

# 创建持仓
pos = aq.Position(
    symbol="600519.SH",
    quantity=1000,
    avg_price=1800.0
)

# 更新市值
pos.update_market_value(1850.0)
print(f"未实现盈亏: {pos.unrealized_pnl}")  # 50000.0
```

## ❓ 常见问题

### Q1: CMake 找不到 pybind11

**解决方案**: CMake 会自动从 GitHub 下载 pybind11。如果网络受限，可以：

```bash
pip install pybind11
```

或手动下载并解压到 `build/_deps/pybind11-src`

### Q2: Windows 编译失败 "无法找到 Python"

**解决方案**: 确保 Python 在 PATH 中，或指定 Python 路径：

```cmd
cmake .. -DPython3_ROOT_DIR="C:\Python39"
```

### Q3: Linux 提示缺少 Python 开发头文件

**解决方案**:

```bash
# Ubuntu/Debian
sudo apt install python3-dev

# CentOS/RHEL
sudo yum install python3-devel
```

### Q4: 测试时提示 "无法导入 apexquant_core"

**可能原因**:
1. C++ 模块未成功编译
2. .so/.pyd 文件不在正确位置

**解决方案**:
- 检查 `python/apexquant/` 目录下是否有 `apexquant_core.*.so` (Linux/Mac) 或 `apexquant_core.*.pyd` (Windows)
- 重新编译: `cmake --build build --config Release`

## 🎯 下一步

Day 1 完成后，您可以：

1. **查看代码**: 浏览 `cpp/` 和 `python/` 目录了解架构
2. **修改测试**: 在 `python/tests/test_bridge.py` 中添加自己的测试
3. **准备 Day 2**: 数据层开发，将使用 AKShare 获取真实市场数据

## 📚 参考资源

- **pybind11 文档**: https://pybind11.readthedocs.io/
- **CMake 教程**: https://cmake.org/cmake/help/latest/guide/tutorial/
- **AKShare 文档**: https://akshare.akfamily.xyz/
- **Eigen 文档**: https://eigen.tuxfamily.org/

---

有问题？欢迎提 Issue 或查看项目 Wiki！

