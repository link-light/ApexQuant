"""
市场分析页面

展示市场情绪指标、宏观经济数据和成交量异常检测
"""

import streamlit as st
import sys
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import traceback

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "python"))

# 页面配置
st.set_page_config(
    page_title="市场分析 - ApexQuant",
    page_icon="📊",
    layout="wide"
)

st.title("📊 市场分析")
st.markdown("市场情绪指标 | 宏观经济数据 | 成交量异常检测")
st.markdown("---")


# ============================================================
# 辅助函数
# ============================================================

@st.cache_data(ttl=3600)
def get_stock_data_cached(symbol: str, days: int = 120):
    """缓存的股票数据获取"""
    try:
        from apexquant.data import get_stock_data
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        df = get_stock_data(symbol, start_date, end_date)
        if df is not None and not df.empty:
            return df
    except Exception as e:
        st.warning(f"数据获取失败: {e}")
    return None


def generate_mock_market_data(days: int = 120) -> pd.DataFrame:
    """生成模拟市场数据"""
    np.random.seed(42)
    dates = pd.date_range(end=datetime.now(), periods=days, freq='D')

    base_price = 3000
    returns = np.random.randn(days) * 0.015
    prices = base_price * np.exp(np.cumsum(returns))

    df = pd.DataFrame({
        'date': dates,
        'close': prices,
        'high': prices * (1 + abs(np.random.randn(days) * 0.01)),
        'low': prices * (1 - abs(np.random.randn(days) * 0.01)),
        'volume': np.random.randint(500000000, 2000000000, days),
        'advance': np.random.randint(1000, 3000, days),
        'decline': np.random.randint(1000, 3000, days)
    })

    return df


# ============================================================
# 标签页选择
# ============================================================

tab1, tab2, tab3 = st.tabs(["📈 市场情绪指标", "🌍 宏观经济数据", "⚠️ 成交量异常检测"])


# ============================================================
# 标签页 1: 市场情绪指标
# ============================================================
with tab1:
    st.markdown("### 📈 恐慌贪婪指数")
    st.markdown("基于市场动量、波动率、成交量和市场宽度的综合情绪指标")

    col1, col2 = st.columns([2, 1])

    with col1:
        sentiment_symbol = st.text_input(
            "股票代码或指数",
            value="000001",
            help="输入股票代码（如 600519）或使用 000001 代表市场指数",
            key="sentiment_symbol"
        )

    with col2:
        sentiment_days = st.slider("分析天数", 60, 500, 120, key="sentiment_days")

    # 参数配置
    with st.expander("⚙️ 高级参数"):
        col1, col2, col3 = st.columns(3)
        with col1:
            volatility_window = st.number_input("波动率窗口", 10, 60, 20, key="vol_window")
        with col2:
            momentum_window = st.number_input("动量窗口", 60, 250, 125, key="mom_window")
        with col3:
            volume_window = st.number_input("成交量窗口", 10, 60, 20, key="vol_window2")

    if st.button("🚀 分析市场情绪", type="primary", use_container_width=True):
        with st.spinner("正在分析市场情绪..."):
            try:
                from apexquant.data import get_market_sentiment

                # 获取数据
                df = get_stock_data_cached(sentiment_symbol, sentiment_days)

                if df is None or df.empty:
                    st.info("使用模拟市场数据进行演示")
                    df = generate_mock_market_data(sentiment_days)

                # 计算情绪指标
                sentiment = get_market_sentiment(
                    df,
                    volatility_window=volatility_window,
                    momentum_window=momentum_window,
                    volume_window=volume_window
                )

                st.success("分析完成！")

                # 显示结果
                st.markdown("### 📊 情绪指标结果")

                # 情绪得分和等级
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric(
                        "情绪得分",
                        f"{sentiment.score:.1f}",
                        help="0-100分，0=极度恐慌，100=极度贪婪"
                    )

                with col2:
                    level_colors = {
                        "极度恐慌": "🔴",
                        "恐慌": "🟠",
                        "中性": "🟡",
                        "贪婪": "🟢",
                        "极度贪婪": "🔵"
                    }
                    level_icon = level_colors.get(sentiment.level.value, "⚪")
                    st.metric("情绪等级", f"{level_icon} {sentiment.level.value}")

                with col3:
                    st.metric("分析时间", sentiment.timestamp.strftime("%Y-%m-%d %H:%M"))

                # 描述
                st.info(f"**分析结论**: {sentiment.description}")

                # 各组成部分得分
                st.markdown("### 📋 组成部分得分")

                component_names = {
                    'momentum': '市场动量',
                    'volatility': '波动率',
                    'volume': '成交量',
                    'breadth': '市场宽度'
                }

                cols = st.columns(4)
                for i, (key, value) in enumerate(sentiment.components.items()):
                    with cols[i]:
                        st.metric(
                            component_names.get(key, key),
                            f"{value:.1f}",
                            delta=f"{value - 50:.1f}" if value != 50 else None
                        )

                # 可视化
                st.markdown("### 📈 情绪得分可视化")

                # 创建仪表盘样式的可视化
                import plotly.graph_objects as go

                fig = go.Figure(go.Indicator(
                    mode="gauge+number+delta",
                    value=sentiment.score,
                    domain={'x': [0, 1], 'y': [0, 1]},
                    title={'text': "市场情绪指数"},
                    delta={'reference': 50},
                    gauge={
                        'axis': {'range': [None, 100]},
                        'bar': {'color': "darkblue"},
                        'steps': [
                            {'range': [0, 20], 'color': "red"},
                            {'range': [20, 40], 'color': "orange"},
                            {'range': [40, 60], 'color': "yellow"},
                            {'range': [60, 80], 'color': "lightgreen"},
                            {'range': [80, 100], 'color': "green"}
                        ],
                        'threshold': {
                            'line': {'color': "black", 'width': 4},
                            'thickness': 0.75,
                            'value': sentiment.score
                        }
                    }
                ))

                st.plotly_chart(fig, use_container_width=True)

            except Exception as e:
                st.error(f"分析失败: {str(e)}")
                with st.expander("查看错误详情"):
                    st.code(traceback.format_exc())


# ============================================================
# 标签页 2: 宏观经济数据
# ============================================================
with tab2:
    st.markdown("### 🌍 宏观经济指标")
    st.markdown("获取最新的宏观经济数据，包括 GDP、CPI、PMI 等")

    col1, col2 = st.columns(2)

    with col1:
        macro_start_date = st.date_input(
            "开始日期",
            value=datetime.now() - timedelta(days=365),
            key="macro_start"
        )

    with col2:
        macro_end_date = st.date_input(
            "结束日期",
            value=datetime.now(),
            key="macro_end"
        )

    # 选择指标
    indicators = st.multiselect(
        "选择指标",
        ["GDP", "CPI", "PPI", "PMI", "利率", "汇率", "货币供应量"],
        default=["GDP", "CPI", "PMI"],
        help="选择要查看的宏观经济指标"
    )

    if st.button("🚀 获取宏观数据", type="primary", use_container_width=True):
        with st.spinner("正在获取宏观经济数据..."):
            try:
                from apexquant.data import get_macro_indicators, MacroDataFetcher

                # 获取综合数据
                macro_data = get_macro_indicators(
                    start_date=macro_start_date.strftime('%Y-%m-%d'),
                    end_date=macro_end_date.strftime('%Y-%m-%d')
                )

                st.success(f"数据获取完成！更新时间: {macro_data.update_time.strftime('%Y-%m-%d %H:%M')}")

                # 显示指标
                if macro_data.indicators:
                    st.markdown("### 📊 最新指标")

                    cols = st.columns(min(len(macro_data.indicators), 3))

                    for i, (name, indicator) in enumerate(macro_data.indicators.items()):
                        with cols[i % 3]:
                            delta_str = None
                            if indicator.yoy_change is not None:
                                delta_str = f"同比 {indicator.yoy_change:+.2f}%"

                            st.metric(
                                indicator.indicator_type.value,
                                f"{indicator.value:.2f} {indicator.unit}",
                                delta=delta_str
                            )
                            st.caption(f"日期: {indicator.date.strftime('%Y-%m-%d')}")

                    # 详细数据表
                    with st.expander("📋 详细数据"):
                        detail_data = []
                        for name, indicator in macro_data.indicators.items():
                            detail_data.append({
                                '指标': indicator.indicator_type.value,
                                '数值': f"{indicator.value:.2f}",
                                '单位': indicator.unit,
                                '同比变化': f"{indicator.yoy_change:.2f}%" if indicator.yoy_change else "N/A",
                                '日期': indicator.date.strftime('%Y-%m-%d'),
                                '数据源': indicator.source
                            })

                        st.dataframe(
                            pd.DataFrame(detail_data),
                            hide_index=True,
                            use_container_width=True
                        )
                else:
                    st.warning("未获取到宏观数据")

                # 获取单个指标的历史数据
                if indicators:
                    st.markdown("### 📈 历史趋势")

                    fetcher = MacroDataFetcher()

                    for indicator_name in indicators:
                        with st.expander(f"📊 {indicator_name} 历史数据"):
                            try:
                                if indicator_name == "GDP":
                                    df = fetcher.get_gdp_data(
                                        macro_start_date.strftime('%Y-%m-%d'),
                                        macro_end_date.strftime('%Y-%m-%d')
                                    )
                                elif indicator_name == "CPI":
                                    df = fetcher.get_cpi_data(
                                        macro_start_date.strftime('%Y-%m-%d'),
                                        macro_end_date.strftime('%Y-%m-%d')
                                    )
                                elif indicator_name == "PPI":
                                    df = fetcher.get_ppi_data(
                                        macro_start_date.strftime('%Y-%m-%d'),
                                        macro_end_date.strftime('%Y-%m-%d')
                                    )
                                elif indicator_name == "PMI":
                                    df = fetcher.get_pmi_data(
                                        macro_start_date.strftime('%Y-%m-%d'),
                                        macro_end_date.strftime('%Y-%m-%d')
                                    )
                                elif indicator_name == "利率":
                                    df = fetcher.get_interest_rate_data(
                                        macro_start_date.strftime('%Y-%m-%d'),
                                        macro_end_date.strftime('%Y-%m-%d')
                                    )
                                elif indicator_name == "汇率":
                                    df = fetcher.get_exchange_rate_data(
                                        start_date=macro_start_date.strftime('%Y-%m-%d'),
                                        end_date=macro_end_date.strftime('%Y-%m-%d')
                                    )
                                elif indicator_name == "货币供应量":
                                    df = fetcher.get_money_supply_data(
                                        macro_start_date.strftime('%Y-%m-%d'),
                                        macro_end_date.strftime('%Y-%m-%d')
                                    )
                                else:
                                    continue

                                if df is not None and not df.empty:
                                    st.dataframe(df.tail(10), use_container_width=True)

                                    # 简单图表
                                    if len(df) > 1:
                                        chart_col = df.columns[1] if len(df.columns) > 1 else df.columns[0]
                                        st.line_chart(df.set_index(df.columns[0])[chart_col])
                                else:
                                    st.info("暂无数据")

                            except Exception as e:
                                st.warning(f"获取 {indicator_name} 数据失败: {e}")

            except Exception as e:
                st.error(f"获取失败: {str(e)}")
                with st.expander("查看错误详情"):
                    st.code(traceback.format_exc())


# ============================================================
# 标签页 3: 成交量异常检测
# ============================================================
with tab3:
    st.markdown("### ⚠️ 成交量异常检测")
    st.markdown("检测成交量的异常波动，识别潜在的市场信号")

    col1, col2 = st.columns(2)

    with col1:
        anomaly_symbol = st.text_input(
            "股票代码",
            value="600519",
            key="anomaly_symbol"
        )

    with col2:
        anomaly_days = st.slider("分析天数", 60, 500, 120, key="anomaly_days")

    # 参数配置
    col1, col2 = st.columns(2)

    with col1:
        anomaly_window = st.slider("滚动窗口", 10, 60, 20, help="计算均值和标准差的窗口大小")

    with col2:
        anomaly_threshold = st.slider(
            "异常阈值 (Z-Score)",
            1.0, 5.0, 2.0, 0.5,
            help="标准差倍数，超过此值视为异常"
        )

    if st.button("🚀 检测成交量异常", type="primary", use_container_width=True):
        with st.spinner("正在检测成交量异常..."):
            try:
                from apexquant.data import detect_volume_anomalies

                # 获取数据
                df = get_stock_data_cached(anomaly_symbol, anomaly_days)

                if df is None or df.empty:
                    st.warning("数据获取失败，使用模拟数据")
                    df = generate_mock_market_data(anomaly_days)

                # 检测异常
                if 'date' in df.columns:
                    volume_series = df.set_index('date')['volume']
                else:
                    volume_series = df['volume']

                anomalies = detect_volume_anomalies(
                    symbol=anomaly_symbol,
                    volume_data=volume_series,
                    window=anomaly_window,
                    threshold=anomaly_threshold
                )

                st.success(f"检测完成！发现 {len(anomalies)} 个异常")

                if anomalies:
                    # 异常统计
                    st.markdown("### 📊 异常统计")

                    surge_count = sum(1 for a in anomalies if a.anomaly_type == 'surge')
                    drop_count = sum(1 for a in anomalies if a.anomaly_type == 'drop')

                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.metric("总异常数", len(anomalies))
                    with col2:
                        st.metric("放量异常", surge_count, delta="🔺")
                    with col3:
                        st.metric("缩量异常", drop_count, delta="🔻")

                    # 异常列表
                    st.markdown("### 📋 异常详情")

                    anomaly_data = []
                    for a in anomalies:
                        anomaly_data.append({
                            '日期': a.date.strftime('%Y-%m-%d'),
                            '类型': '🔺 放量' if a.anomaly_type == 'surge' else '🔻 缩量',
                            '成交量': f"{a.volume:,.0f}",
                            '平均成交量': f"{a.avg_volume:,.0f}",
                            'Z-Score': f"{a.z_score:.2f}",
                            '严重程度': a.severity,
                            '倍数': f"{a.volume / a.avg_volume:.2f}x"
                        })

                    st.dataframe(
                        pd.DataFrame(anomaly_data),
                        hide_index=True,
                        use_container_width=True
                    )

                    # 可视化
                    st.markdown("### 📈 成交量趋势")

                    chart_df = pd.DataFrame({
                        '成交量': volume_series.values
                    }, index=volume_series.index)

                    st.line_chart(chart_df)

                else:
                    st.info("未检测到成交量异常")

            except Exception as e:
                st.error(f"检测失败: {str(e)}")
                with st.expander("查看错误详情"):
                    st.code(traceback.format_exc())


# ============================================================
# 页脚
# ============================================================
st.markdown("---")

with st.expander("📖 使用说明"):
    st.markdown("""
    ### 市场分析功能说明

    **1. 市场情绪指标**
    - **恐慌贪婪指数**: 综合市场动量、波动率、成交量和市场宽度的情绪指标
    - **得分范围**: 0-100，0表示极度恐慌，100表示极度贪婪
    - **应用场景**: 识别市场情绪极端点，辅助逆向投资决策

    **2. 宏观经济数据**
    - **支持指标**: GDP、CPI、PPI、PMI、利率、汇率、货币供应量
    - **数据来源**: AKShare（自动降级为模拟数据）
    - **应用场景**: 宏观经济分析，把握经济周期

    **3. 成交量异常检测**
    - **检测方法**: 基于Z-Score的统计异常检测
    - **异常类型**: 放量异常（surge）和缩量异常（drop）
    - **应用场景**: 识别异常交易活动，捕捉潜在机会或风险
    """)
