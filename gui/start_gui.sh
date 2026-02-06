#!/bin/bash
# ApexQuant GUI 启动脚本 (Linux/Mac)

echo "========================================"
echo "ApexQuant GUI 启动中..."
echo "========================================"

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python3 未安装"
    exit 1
fi

# 检查streamlit
if ! python3 -c "import streamlit" &> /dev/null; then
    echo "[INFO] 正在安装依赖包..."
    pip3 install -r requirements.txt
fi

# 启动GUI
echo "[INFO] 启动GUI界面..."
streamlit run app.py --server.port 8501

