"""
策略回测页面
"""

import streamlit as st
import sys
from pathlib import Path
import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "python"))

# 页面配置
st.set_page_config(
    page_title="策略回测 - ApexQuant",
    page_icon="📊",
    layout="wide"
)

st.title("📊 策略回测")
st.markdown("使用历史数据测试您的交易策略")
st.markdown("---")

# 回测配置
st.markdown("### ⚙️ 回测配置")

col1, col2 = st.columns(2)

with col1:
    # 策略选择
    strategy = st.selectbox(
        "选择策略",
        [
            "均线交叉 (MA Cross)",
            "RSI策略",
            "买入持有 (Buy & Hold)",
            "AI驱动策略"
        ]
    )
    
    # 日期范围
    start_date = st.date_input(
        "开始日期",
        value=datetime.now() - timedelta(days=365)
    )
    
    end_date = st.date_input(
        "结束日期",
        value=datetime.now()
    )
    
    # 初始资金
    initial_capital = st.number_input(
        "初始资金 (元)",
        min_value=10000,
        max_value=100000000,
        value=1000000,
        step=10000
    )

with col2:
    # 股票选择
    symbols_input = st.text_area(
        "股票代码 (每行一个)",
        value="sh.600519\nsh.600036",
        height=100
    )
    
    # K线周期
    bar_interval = st.selectbox(
        "K线周期",
        ["1d", "1h", "30m", "15m", "5m", "1m"],
        index=0
    )
    
    # 滑点设置
    slippage = st.slider(
        "滑点率 (%)",
        min_value=0.0,
        max_value=1.0,
        value=0.1,
        step=0.01
    )
    
    # 手续费
    commission = st.slider(
        "手续费率 (%)",
        min_value=0.0,
        max_value=0.5,
        value=0.03,
        step=0.01
    )

st.markdown("---")

# 策略参数
st.markdown("### 🎛️ 策略参数")

if strategy == "均线交叉 (MA Cross)":
    col1, col2 = st.columns(2)
    with col1:
        ma_short = st.number_input("短期均线", min_value=2, max_value=50, value=5)
    with col2:
        ma_long = st.number_input("长期均线", min_value=10, max_value=200, value=20)

elif strategy == "RSI策略":
    col1, col2, col3 = st.columns(3)
    with col1:
        rsi_period = st.number_input("RSI周期", min_value=5, max_value=30, value=14)
    with col2:
        oversold = st.number_input("超卖线", min_value=10, max_value=40, value=30)
    with col3:
        overbought = st.number_input("超买线", min_value=60, max_value=90, value=70)

st.markdown("---")

# 开始回测按钮
col1, col2, col3 = st.columns([1, 1, 1])

with col2:
    if st.button("🚀 开始回测", type="primary", use_container_width=True):
        with st.spinner("🔄 正在运行回测，请稍候..."):
            try:
                # 导入必要的模块
                from apexquant.simulation import SimulationController
                from apexquant.simulation.strategies import (
                    create_ma_cross_strategy,
                    create_rsi_strategy,
                    create_buy_hold_strategy
                )
                from apexquant.simulation import PerformanceAnalyzer
                
                # 创建控制器
                controller = SimulationController()
                
                # 选择策略
                if strategy == "均线交叉 (MA Cross)":
                    strategy_func = create_ma_cross_strategy(
                        risk_manager=controller.risk_manager
                    )
                elif strategy == "RSI策略":
                    strategy_func = create_rsi_strategy()
                else:
                    strategy_func = create_buy_hold_strategy()
                
                # 运行回测
                symbols = symbols_input.strip().split('\n')
                controller.start_backtest(
                    start_date=start_date.strftime('%Y-%m-%d'),
                    end_date=end_date.strftime('%Y-%m-%d'),
                    symbols=symbols,
                    strategy_func=strategy_func,
                    bar_interval=bar_interval
                )
                
                # 获取性能分析
                analyzer = PerformanceAnalyzer(controller.db, controller.account_id)
                metrics = analyzer.calculate_performance_metrics()
                
                # 保存结果到session state
                st.session_state['backtest_result'] = {
                    'metrics': metrics,
                    'analyzer': analyzer,
                    'controller': controller
                }
                
                st.success("✅ 回测完成！")
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ 回测失败: {str(e)}")
                import traceback
                with st.expander("查看错误详情"):
                    st.code(traceback.format_exc())

st.markdown("---")

# 显示回测结果（如果存在）
if 'backtest_result' in st.session_state:
    result = st.session_state['backtest_result']
    metrics = result['metrics']
    
    st.markdown("## 📈 回测结果")
    
    # 核心指标
    st.markdown("### 🎯 核心指标")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "总收益率",
            f"{metrics.get('total_return_pct', 0):.2f}%",
            delta=f"{metrics.get('total_return_pct', 0):.2f}%"
        )
    
    with col2:
        st.metric(
            "年化收益率",
            f"{metrics.get('annual_return_pct', 0):.2f}%"
        )
    
    with col3:
        st.metric(
            "最大回撤",
            f"{metrics.get('max_drawdown_pct', 0):.2f}%",
            delta=f"{metrics.get('max_drawdown_pct', 0):.2f}%",
            delta_color="inverse"
        )
    
    with col4:
        st.metric(
            "夏普比率",
            f"{metrics.get('sharpe_ratio', 0):.2f}"
        )
    
    # 详细指标
    st.markdown("### 📊 详细指标")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**收益指标**")
        metrics_df1 = pd.DataFrame({
            '指标': [
                '总收益',
                '总收益率',
                '年化收益率',
                '最大回撤',
                '最大回撤率'
            ],
            '数值': [
                f"{metrics.get('total_return', 0):,.2f}",
                f"{metrics.get('total_return_pct', 0):.2f}%",
                f"{metrics.get('annual_return_pct', 0):.2f}%",
                f"{metrics.get('max_drawdown', 0):,.2f}",
                f"{metrics.get('max_drawdown_pct', 0):.2f}%"
            ]
        })
        st.dataframe(metrics_df1, hide_index=True, use_container_width=True)
    
    with col2:
        st.markdown("**交易指标**")
        metrics_df2 = pd.DataFrame({
            '指标': [
                '总交易次数',
                '盈利次数',
                '亏损次数',
                '胜率',
                '盈亏比'
            ],
            '数值': [
                f"{metrics.get('total_trades', 0)}",
                f"{metrics.get('winning_trades', 0)}",
                f"{metrics.get('losing_trades', 0)}",
                f"{metrics.get('win_rate', 0):.2f}%",
                f"{metrics.get('profit_loss_ratio', 0):.2f}"
            ]
        })
        st.dataframe(metrics_df2, hide_index=True, use_container_width=True)

