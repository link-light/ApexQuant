"""
性能分析页面
"""

import streamlit as st
import sys
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "python"))


def show():
    """显示性能分析页面"""
    
    st.title("📈 性能分析")
    st.markdown("全面的性能分析和可视化工具")
    st.markdown("---")
    
    # 账户选择
    st.markdown("### 📂 选择账户")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        account_id = st.selectbox(
            "账户ID",
            ["SIM1234567890", "无可用账户"]
        )
    
    with col2:
        if st.button("🔄 刷新", use_container_width=True):
            st.success("✅ 已刷新")
    
    if account_id == "无可用账户":
        st.warning("⚠️ 请先运行回测或实时模拟以生成数据")
        st.info("💡 提示：前往\"策略回测\"页面运行回测")
        return
    
    st.markdown("---")
    
    # 核心指标
    st.markdown("### 🎯 核心指标")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("总收益率", "0.00%", delta="0.00%")
    
    with col2:
        st.metric("年化收益率", "0.00%")
    
    with col3:
        st.metric("最大回撤", "0.00%", delta="0.00%", delta_color="inverse")
    
    with col4:
        st.metric("夏普比率", "0.00")
    
    st.markdown("---")
    
    # 详细指标表格
    st.markdown("### 📊 详细指标")
    
    tab1, tab2, tab3 = st.tabs(["收益指标", "风险指标", "交易指标"])
    
    with tab1:
        metrics_return = pd.DataFrame({
            '指标': ['总收益', '总收益率', '年化收益率', '累计盈利', '累计亏损'],
            '数值': ['0.00', '0.00%', '0.00%', '0.00', '0.00']
        })
        st.dataframe(metrics_return, hide_index=True, use_container_width=True)
    
    with tab2:
        metrics_risk = pd.DataFrame({
            '指标': ['最大回撤', '最大回撤率', '夏普比率', '卡玛比率', '波动率'],
            '数值': ['0.00', '0.00%', '0.00', '0.00', '0.00%']
        })
        st.dataframe(metrics_risk, hide_index=True, use_container_width=True)
    
    with tab3:
        metrics_trade = pd.DataFrame({
            '指标': ['总交易次数', '盈利次数', '亏损次数', '胜率', '盈亏比'],
            '数值': ['0', '0', '0', '0.00%', '0.00']
        })
        st.dataframe(metrics_trade, hide_index=True, use_container_width=True)
    
    st.markdown("---")
    
    # 图表
    st.markdown("### 📊 图表分析")
    
    chart_type = st.selectbox(
        "选择图表类型",
        ["资金曲线", "回撤分析", "交易分析", "月度收益热力图"]
    )
    
    if chart_type == "资金曲线":
        show_equity_curve_chart()
    elif chart_type == "回撤分析":
        show_drawdown_chart()
    elif chart_type == "交易分析":
        show_trade_analysis_chart()
    elif chart_type == "月度收益热力图":
        show_monthly_returns_chart()
    
    st.markdown("---")
    
    # 交易记录
    st.markdown("### 📝 交易记录")
    
    trades_df = pd.DataFrame({
        '时间': [],
        '股票': [],
        '方向': [],
        '价格': [],
        '数量': [],
        '金额': [],
        '手续费': [],
        '盈亏': []
    })
    
    st.dataframe(trades_df, hide_index=True, use_container_width=True)
    
    # 导出功能
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📥 导出报告", use_container_width=True):
            st.success("✅ 报告已导出")
    
    with col2:
        if st.button("📊 生成图表", use_container_width=True):
            st.info("🔄 正在生成图表...")
    
    with col3:
        if st.button("📧 发送邮件", use_container_width=True):
            st.info("📧 邮件已发送")


def show_equity_curve_chart():
    """显示资金曲线图"""
    
    import numpy as np
    
    # 示例数据
    dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
    equity = 1000000 + np.cumsum(np.random.randn(100) * 5000)
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=dates,
        y=equity,
        mode='lines',
        name='总资产',
        line=dict(color='#1f77b4', width=2)
    ))
    
    fig.update_layout(
        title='资金曲线',
        xaxis_title='日期',
        yaxis_title='资产 (元)',
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)


def show_drawdown_chart():
    """显示回撤图"""
    
    import numpy as np
    
    dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
    drawdown = -np.abs(np.cumsum(np.random.randn(100) * 0.5))
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=dates,
        y=drawdown,
        mode='lines',
        name='回撤',
        line=dict(color='#ff7f0e', width=2),
        fill='tozeroy'
    ))
    
    fig.update_layout(
        title='回撤分析',
        xaxis_title='日期',
        yaxis_title='回撤 (%)',
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)


def show_trade_analysis_chart():
    """显示交易分析图"""
    
    labels = ['盈利交易', '亏损交易']
    values = [60, 40]
    
    fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.3)])
    
    fig.update_layout(
        title='交易分析',
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)


def show_monthly_returns_chart():
    """显示月度收益热力图"""
    
    import numpy as np
    
    months = ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月']
    returns = np.random.randn(12) * 5
    
    fig = go.Figure(data=go.Bar(x=months, y=returns))
    
    fig.update_layout(
        title='月度收益',
        xaxis_title='月份',
        yaxis_title='收益率 (%)',
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)

