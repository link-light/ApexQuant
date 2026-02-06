@echo off
REM ApexQuant GUI 启动脚本 (Windows)

echo ========================================
echo ApexQuant GUI 启动中...
echo ========================================

REM 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python 未安装或不在PATH中
    pause
    exit /b 1
)

REM 检查streamlit
python -c "import streamlit" >nul 2>&1
if errorlevel 1 (
    echo [INFO] 正在安装依赖包...
    pip install -r requirements.txt
)

REM 启动GUI
echo [INFO] 启动GUI界面...
streamlit run app.py --server.port 8501

pause

