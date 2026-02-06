"""
实时模拟页面
"""

import streamlit as st
import sys
from pathlib import Path
import pandas as pd
from datetime import datetime

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "python"))

# 页面配置
st.set_page_config(
    page_title="实时模拟 - ApexQuant",
    page_icon="⚡",
    layout="wide"
)

st.title("⚡ 实时模拟")
st.markdown("实时交易环境模拟，验证策略实战能力")
st.markdown("---")

# 实时监控面板
st.markdown("### 📊 实时监控")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("总资产", "1,000,000.00", delta="+0.00")

with col2:
    st.metric("可用资金", "1,000,000.00", delta="0.00%")

with col3:
    st.metric("持仓市值", "0.00", delta="0")

with col4:
    st.metric("今日盈亏", "0.00", delta="0.00%")

st.markdown("---")

# 控制面板
st.markdown("### 🎮 控制面板")

col1, col2 = st.columns(2)

with col1:
    strategy = st.selectbox(
        "选择策略",
        ["均线交叉", "RSI策略", "买入持有", "AI驱动"]
    )
    
    symbols = st.multiselect(
        "选择股票",
        ["sh.600519", "sh.600036", "sh.600000", "sh.601398"],
        default=["sh.600519"]
    )

with col2:
    mode = st.radio(
        "运行模式",
        ["模拟模式", "实盘模式（暂未开放）"],
        index=0
    )
    
    auto_trade = st.checkbox("启用自动交易", value=False)

st.markdown("---")

# 启动/停止按钮
col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    if st.button("🚀 启动", type="primary", use_container_width=True):
        st.success("✅ 实时模拟已启动")

with col2:
    if st.button("⏸️ 暂停", use_container_width=True):
        st.info("⏸️ 实时模拟已暂停")

with col3:
    if st.button("🛑 停止", use_container_width=True):
        st.warning("🛑 实时模拟已停止")

st.markdown("---")

# 实时行情
st.markdown("### 📈 实时行情")

quotes_df = pd.DataFrame({
    '代码': ['sh.600519', 'sh.600036'],
    '名称': ['贵州茅台', '招商银行'],
    '现价': [1850.00, 42.50],
    '涨跌幅': ['+1.20%', '+0.50%'],
    '涨跌': ['+22.00', '+0.21'],
    '成交量': ['1.2万手', '25.6万手'],
    '成交额': ['2.2亿', '10.9亿'],
    '昨收': [1828.00, 42.29]
})

st.dataframe(quotes_df, hide_index=True, use_container_width=True)

st.markdown("---")

# 持仓信息
st.markdown("### 💼 当前持仓")

positions_df = pd.DataFrame({
    '股票代码': [],
    '股票名称': [],
    '持仓数量': [],
    '可用数量': [],
    '成本价': [],
    '现价': [],
    '市值': [],
    '盈亏': [],
    '盈亏率': []
})

st.dataframe(positions_df, hide_index=True, use_container_width=True)

st.markdown("---")

# 今日委托
st.markdown("### 📝 今日委托")

orders_df = pd.DataFrame({
    '时间': [],
    '股票代码': [],
    '方向': [],
    '类型': [],
    '委托价': [],
    '委托量': [],
    '成交量': [],
    '状态': []
})

st.dataframe(orders_df, hide_index=True, use_container_width=True)

