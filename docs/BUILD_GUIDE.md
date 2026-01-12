# ApexQuant 构建指南

## 📋 目录

- [系统要求](#系统要求)
- [Windows 构建](#windows-构建)
- [Linux 构建](#linux-构建)
- [macOS 构建](#macos-构建)
- [常见问题](#常见问题)
- [高级配置](#高级配置)

## 系统要求

### 通用要求

- **CMake**: 3.15 或更高版本
- **Python**: 3.9 或更高版本
- **磁盘空间**: 至少 2GB（包括依赖）
- **内存**: 建议 4GB 或更多

### 编译器要求

| 平台 | 编译器 | 最低版本 |
|------|--------|----------|
| Windows | MSVC | 2019 (v142) |
| Windows | MinGW-w64 | GCC 10.0 |
| Linux | GCC | 10.0 |
| Linux | Clang | 12.0 |
| macOS | Apple Clang | 13.0 |

## Windows 构建

### 方法 1: Visual Studio（推荐）

#### 1. 安装依赖

1. **安装 Visual Studio 2019/2022**
   - 下载：https://visualstudio.microsoft.com/zh-hans/downloads/
   - 选择"使用 C++ 的桌面开发"工作负载
   - 确保安装了 CMake 工具

2. **安装 Python**
   ```cmd
   # 从 python.org 下载并安装
   # 或使用 winget
   winget install Python.Python.3.11
   ```

3. **验证安装**
   ```cmd
   python --version
   cmake --version
   ```

#### 2. 克隆项目

```cmd
git clone <repository-url>
cd ApexQuant
```

#### 3. 运行构建脚本

```cmd
build.bat
```

#### 4. 手动构建（可选）

```cmd
# 创建构建目录
mkdir build
cd build

# 配置（生成 VS 解决方案）
cmake .. -G "Visual Studio 17 2022" -A x64

# 编译
cmake --build . --config Release -j

# 返回根目录
cd ..

# 安装 Python 依赖
pip install -r python\requirements.txt
```

### 方法 2: MinGW-w64

#### 1. 安装 MinGW-w64

```cmd
# 使用 MSYS2
winget install MSYS2.MSYS2

# 在 MSYS2 终端中安装编译器
pacman -S mingw-w64-x86_64-gcc mingw-w64-x86_64-cmake
```

#### 2. 构建

```cmd
mkdir build
cd build
cmake .. -G "MinGW Makefiles" -DCMAKE_BUILD_TYPE=Release
cmake --build . -j
```

## Linux 构建

### Ubuntu/Debian

#### 1. 安装依赖

```bash
# 更新包列表
sudo apt update

# 安装构建工具
sudo apt install -y \
    build-essential \
    cmake \
    git \
    python3 \
    python3-pip \
    python3-dev

# 安装可选依赖
sudo apt install -y \
    libeigen3-dev \
    libboost-all-dev
```

#### 2. 构建

```bash
# 克隆项目
git clone <repository-url>
cd ApexQuant

# 运行构建脚本
chmod +x build.sh
./build.sh

# 或手动构建
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
cmake --build . -j$(nproc)
cd ..
pip3 install -r python/requirements.txt
```

### CentOS/RHEL 8+

#### 1. 安装依赖

```bash
# 启用 PowerTools（CentOS 8）或 CodeReady Builder（RHEL 8）
sudo dnf config-manager --set-enabled powertools  # CentOS
# 或
sudo subscription-manager repos --enable codeready-builder-for-rhel-8-x86_64-rpms  # RHEL

# 安装构建工具
sudo dnf install -y \
    gcc-c++ \
    cmake \
    git \
    python3 \
    python3-pip \
    python3-devel

# 安装可选依赖
sudo dnf install -y eigen3-devel boost-devel
```

#### 2. 构建

```bash
./build.sh
```

### Arch Linux

```bash
# 安装依赖
sudo pacman -S base-devel cmake git python python-pip eigen boost

# 构建
./build.sh
```

## macOS 构建

### 1. 安装 Xcode Command Line Tools

```bash
xcode-select --install
```

### 2. 安装 Homebrew（如果未安装）

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### 3. 安装依赖

```bash
brew install cmake python@3.11 eigen boost
```

### 4. 构建

```bash
chmod +x build.sh
./build.sh
```

## 常见问题

### Q1: CMake 找不到 Python

**错误信息**:
```
Could NOT find Python3 (missing: Python3_LIBRARIES Development Development.Module Development.Embed)
```

**解决方案**:

**Windows**:
```cmd
cmake .. -DPython3_ROOT_DIR="C:\Python311"
```

**Linux**:
```bash
sudo apt install python3-dev  # Ubuntu/Debian
sudo dnf install python3-devel  # CentOS/RHEL
```

**macOS**:
```bash
brew install python@3.11
cmake .. -DPython3_ROOT_DIR="$(brew --prefix python@3.11)"
```

### Q2: 找不到 pybind11

CMake 会自动从 GitHub 下载 pybind11。如果网络受限：

**方案 1: 使用 pip 安装**
```bash
pip install pybind11
```

**方案 2: 手动下载**
```bash
git clone https://github.com/pybind/pybind11.git
cd pybind11
git checkout v2.11.1
cd ..

# 构建时指定路径
cmake .. -Dpybind11_DIR=/path/to/pybind11/share/cmake/pybind11
```

**方案 3: 使用国内镜像**

修改 `CMakeLists.txt`，将 pybind11 的 URL 改为：
```cmake
GIT_REPOSITORY https://gitee.com/mirrors/pybind11.git
```

### Q3: Eigen 下载失败

**错误信息**:
```
Could not resolve host: gitlab.com
```

**解决方案**:

**方案 1: 系统安装**
```bash
# Ubuntu/Debian
sudo apt install libeigen3-dev

# CentOS/RHEL
sudo dnf install eigen3-devel

# macOS
brew install eigen
```

**方案 2: 手动下载**
```bash
wget https://gitlab.com/libeigen/eigen/-/archive/3.4.0/eigen-3.4.0.tar.gz
tar xzf eigen-3.4.0.tar.gz
mv eigen-3.4.0 eigen

# 构建时跳过 Eigen（Day 1 不强制需要）
cmake .. -DEIGEN3_INCLUDE_DIR=/path/to/eigen
```

### Q4: 编译错误 "C++20 is required"

**解决方案**:

确保编译器支持 C++20：

```bash
# 检查 GCC 版本
g++ --version  # 需要 >= 10.0

# 检查 Clang 版本
clang++ --version  # 需要 >= 12.0
```

如果版本过低，升级编译器或修改 `CMakeLists.txt` 降低到 C++17：
```cmake
set(CMAKE_CXX_STANDARD 17)
```

### Q5: Windows 上找不到 apexquant_core.pyd

**原因**: 编译产物未复制到正确位置

**解决方案**:

检查 `python/apexquant/` 目录：
```cmd
dir python\apexquant\*.pyd
```

如果不存在，手动复制：
```cmd
copy build\Release\apexquant_core.*.pyd python\apexquant\
```

### Q6: Linux 运行时错误 "cannot open shared object file"

**错误信息**:
```
ImportError: libapexquant_core.so: cannot open shared object file
```

**解决方案**:

```bash
# 检查文件是否存在
ls -l python/apexquant/*.so

# 添加到 Python 路径
export PYTHONPATH=$PWD/python:$PYTHONPATH

# 或安装包
cd python
pip install -e .
```

## 高级配置

### 自定义编译选项

```bash
cmake .. \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_CXX_COMPILER=g++-11 \
    -DCMAKE_C_COMPILER=gcc-11 \
    -DCMAKE_INSTALL_PREFIX=/usr/local \
    -DBUILD_TESTING=ON
```

### 启用详细输出

```bash
cmake --build . --config Release --verbose
```

### 指定线程数

```bash
# 使用 8 个线程编译
cmake --build . -j8
```

### 调试构建

```bash
cmake .. -DCMAKE_BUILD_TYPE=Debug
cmake --build . --config Debug
```

### 使用 ccache 加速编译

```bash
# 安装 ccache
sudo apt install ccache  # Linux
brew install ccache      # macOS

# 配置 CMake
cmake .. -DCMAKE_CXX_COMPILER_LAUNCHER=ccache
```

## 验证安装

### 运行测试

```bash
python python/tests/test_bridge.py
```

期望输出：
```
🎉 所有测试通过！Day 1 任务完成！
```

### 运行示例

```bash
python examples/example_basic.py
```

### 检查版本

```python
import apexquant as aq
aq.print_info()
```

## 性能优化

### 编译器优化标志

**GCC/Clang**:
```cmake
set(CMAKE_CXX_FLAGS_RELEASE "-O3 -march=native -DNDEBUG")
```

**MSVC**:
```cmake
set(CMAKE_CXX_FLAGS_RELEASE "/O2 /DNDEBUG")
```

### 链接时优化（LTO）

```cmake
set(CMAKE_INTERPROCEDURAL_OPTIMIZATION TRUE)
```

## 卸载

```bash
# 删除构建产物
rm -rf build/

# 删除 Python 包
pip uninstall apexquant

# 清理 Python 缓存
find . -type d -name __pycache__ -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
```

## 获取帮助

- **GitHub Issues**: https://github.com/yourusername/ApexQuant/issues
- **文档**: 查看 `docs/` 目录
- **示例**: 查看 `examples/` 目录

---

祝编译顺利！ 🚀

