@echo off
REM ApexQuant Quick Start Script for Windows
REM 快速启动脚本

echo ========================================
echo ApexQuant Simulation System
echo ========================================
echo.

cd /d "%~dp0python\apexquant"

echo [INFO] Running quick demo...
echo.

python quick_demo.py

echo.
echo ========================================
echo.
echo Next steps:
echo   1. Edit config: config\simulation_config.yaml
echo   2. Run backtest: python ..\..\ run_simulation.py backtest
echo   3. Check docs: SIMULATION_GUIDE.md
echo.

pause
