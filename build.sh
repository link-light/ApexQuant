#!/bin/bash
# ApexQuant Linux/macOS 编译脚本

set -e  # 遇到错误立即退出

echo "========================================"
echo "ApexQuant 编译脚本 (Linux/macOS)"
echo "========================================"

# 创建构建目录
mkdir -p build
cd build

# 配置 CMake
echo ""
echo "[1/3] 配置 CMake..."
cmake .. -DCMAKE_BUILD_TYPE=Release

# 编译
echo ""
echo "[2/3] 编译 C++ 模块..."
cmake --build . -j$(nproc 2>/dev/null || sysctl -n hw.ncpu)

# 返回根目录
cd ..

# 安装 Python 依赖
echo ""
echo "[3/3] 安装 Python 依赖..."
python3 -m pip install -r python/requirements.txt

echo ""
echo "========================================"
echo "编译完成！"
echo "========================================"
echo ""
echo "运行测试:"
echo "  python3 python/tests/test_bridge.py"
echo ""

