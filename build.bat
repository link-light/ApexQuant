@echo off
REM ApexQuant Windows 编译脚本

echo ========================================
echo ApexQuant 编译脚本 (Windows)
echo ========================================

REM 创建构建目录
if not exist build mkdir build
cd build

REM 配置 CMake（使用 Visual Studio）
echo.
echo [1/3] 配置 CMake...
cmake .. -G "Visual Studio 17 2022" -A x64
if %ERRORLEVEL% NEQ 0 (
    echo 错误: CMake 配置失败
    cd ..
    exit /b 1
)

REM 编译
echo.
echo [2/3] 编译 C++ 模块...
cmake --build . --config Release -j
if %ERRORLEVEL% NEQ 0 (
    echo 错误: 编译失败
    cd ..
    exit /b 1
)

REM 返回根目录
cd ..

REM 安装 Python 依赖
echo.
echo [3/3] 安装 Python 依赖...
python -m pip install -r python/requirements.txt

echo.
echo ========================================
echo 编译完成！
echo ========================================
echo.
echo 运行测试:
echo   python python/tests/test_bridge.py
echo.

pause

