"""
AI智能分析页面
"""

import streamlit as st
import sys
from pathlib import Path
import pandas as pd
from datetime import datetime, timedelta

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "python"))

# 页面配置
st.set_page_config(
    page_title="AI智能分析 - ApexQuant",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 AI智能分析")
st.markdown("基于DeepSeek大模型的智能交易分析")
st.markdown("---")

# 检查API配置
import os
api_key = os.getenv('DEEPSEEK_API_KEY')

if not api_key:
    st.warning("""
    ⚠️ **DeepSeek API未配置**

    请设置环境变量 `DEEPSEEK_API_KEY` 后重启应用。

    **设置方法：**
    ```bash
    # Windows PowerShell
    $env:DEEPSEEK_API_KEY="your-api-key"

    # Linux/Mac
    export DEEPSEEK_API_KEY="your-api-key"
    ```

    或在项目根目录创建 `.env` 文件：
    ```
    DEEPSEEK_API_KEY=your-api-key
    ```

    **获取API Key：** https://platform.deepseek.com/
    """)
    st.info("💡 即使没有API Key，也可以使用快速技术分析功能")
    st.markdown("---")

# 股票输入
col1, col2 = st.columns([2, 1])

with col1:
    symbol = st.text_input(
        "股票代码",
        value="600519",
        help="输入股票代码，如 600519"
    )

with col2:
    analysis_type = st.selectbox(
        "分析类型",
        ["快速技术分析", "完整AI分析"],
        help="快速分析不需要API，完整分析需要DeepSeek API"
    )

# 分析参数
st.markdown("### ⚙️ 分析参数")

col1, col2, col3 = st.columns(3)

with col1:
    lookback_days = st.slider("回溯天数", 30, 120, 60)

with col2:
    initial_capital = st.number_input(
        "模拟资金",
        min_value=10000,
        max_value=10000000,
        value=100000,
        step=10000
    )

with col3:
    current_position = st.number_input(
        "当前持仓(股)",
        min_value=0,
        max_value=100000,
        value=0,
        step=100
    )

st.markdown("---")

# 分析按钮
if st.button("🚀 开始分析", type="primary", use_container_width=True):
    with st.spinner("正在分析..."):
        try:
            # 导入模块
            from apexquant.analysis import TechnicalAnalyzer, calculate_indicators
            from apexquant.ai import SmartTradingAdvisor, MarketContext, FundamentalData
            from apexquant.data.news_fetcher import NewsFetcher, get_stock_news

            # 获取数据
            st.info(f"正在获取 {symbol} 的历史数据...")

            # 尝试获取真实数据
            try:
                from apexquant.simulation.data_source import SimulationDataSource
                data_source = SimulationDataSource()
                end_date = datetime.now().strftime('%Y-%m-%d')
                start_date = (datetime.now() - timedelta(days=lookback_days)).strftime('%Y-%m-%d')
                df = data_source.get_stock_data(symbol, start_date, end_date)
            except:
                df = None

            # 如果没有数据，使用模拟数据
            if df is None or df.empty:
                import numpy as np
                st.warning("无法获取真实数据，使用模拟数据进行演示")
                np.random.seed(int(symbol) if symbol.isdigit() else 42)
                base_price = 100
                returns = np.random.randn(lookback_days) * 0.02
                prices = base_price * np.exp(np.cumsum(returns))

                df = pd.DataFrame({
                    'date': pd.date_range(end=datetime.now(), periods=lookback_days, freq='D'),
                    'open': prices * (1 + np.random.randn(lookback_days) * 0.005),
                    'high': prices * (1 + abs(np.random.randn(lookback_days) * 0.01)),
                    'low': prices * (1 - abs(np.random.randn(lookback_days) * 0.01)),
                    'close': prices,
                    'volume': np.random.randint(1000000, 5000000, lookback_days)
                })

            current_price = float(df['close'].iloc[-1])

            # 账户信息
            account_info = {
                'total_assets': initial_capital,
                'available_cash': initial_capital - current_position * current_price,
                'positions': []
            }

            if current_position > 0:
                account_info['positions'].append({
                    'symbol': symbol,
                    'volume': current_position,
                    'avg_cost': current_price * 0.95,  # 假设成本
                    'unrealized_pnl': current_position * current_price * 0.05
                })

            # 初始化分析器
            advisor = SmartTradingAdvisor()

            # 执行分析
            if analysis_type == "快速技术分析":
                # 快速分析（不需要API）
                signal = advisor.get_quick_signal(symbol, df, current_price)
                indicators = signal['indicators']

                # 显示结果
                st.success("✅ 技术分析完成！")

                # 信号卡片
                st.markdown("### 📊 分析结果")

                col1, col2, col3, col4 = st.columns(4)

                action_color = {
                    'BUY': '🟢',
                    'SELL': '🔴',
                    'HOLD': '🟡'
                }

                with col1:
                    st.metric(
                        "交易信号",
                        f"{action_color.get(signal['action'], '⚪')} {signal['action']}",
                        f"置信度 {signal['confidence']}%"
                    )

                with col2:
                    st.metric("当前价格", f"¥{current_price:.2f}")

                with col3:
                    st.metric("买入信号数", signal['buy_signals'])

                with col4:
                    st.metric("卖出信号数", signal['sell_signals'])

                # 技术指标详情
                st.markdown("### 📈 技术指标")

                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("**趋势指标**")
                    trend_data = {
                        '指标': ['MA5', 'MA10', 'MA20', 'MA60', '趋势'],
                        '数值': [
                            f"{indicators['ma5']:.2f}",
                            f"{indicators['ma10']:.2f}",
                            f"{indicators['ma20']:.2f}",
                            f"{indicators['ma60']:.2f}",
                            f"{indicators['trend']} ({indicators['trend_strength']}%)"
                        ]
                    }
                    st.table(pd.DataFrame(trend_data))

                with col2:
                    st.markdown("**动量指标**")
                    momentum_data = {
                        '指标': ['RSI', 'KDJ-K', 'KDJ-D', 'KDJ-J', 'MACD'],
                        '数值': [
                            f"{indicators['rsi']:.1f} ({indicators['rsi_signal']})",
                            f"{indicators['kdj_k']:.1f}",
                            f"{indicators['kdj_d']:.1f}",
                            f"{indicators['kdj_j']:.1f}",
                            f"{indicators['macd']:.4f}"
                        ]
                    }
                    st.table(pd.DataFrame(momentum_data))

                # 布林带和波动率
                st.markdown("**布林带 & 波动率**")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("上轨", f"{indicators['boll_upper']:.2f}")
                with col2:
                    st.metric("中轨", f"{indicators['boll_middle']:.2f}")
                with col3:
                    st.metric("下轨", f"{indicators['boll_lower']:.2f}")
                with col4:
                    st.metric("波动率", f"{indicators['volatility']:.1f}%")

            else:
                # 完整AI分析
                if not api_key:
                    st.error("❌ 完整AI分析需要配置DeepSeek API Key")
                else:
                    # 获取新闻
                    news = get_stock_news(symbol, limit=5)
                    news_titles = [n['title'] for n in news]

                    # 调用AI分析
                    result = advisor.analyze(
                        symbol=symbol,
                        price_data=df,
                        current_price=current_price,
                        account_info=account_info,
                        news=news_titles
                    )

                    st.success("✅ AI分析完成！")

                    # 显示结果
                    st.markdown("### 🤖 AI分析结果")

                    col1, col2, col3, col4 = st.columns(4)

                    action_color = {
                        'BUY': '🟢',
                        'SELL': '🔴',
                        'HOLD': '🟡'
                    }

                    with col1:
                        st.metric(
                            "交易建议",
                            f"{action_color.get(result.action, '⚪')} {result.action}",
                            f"置信度 {result.confidence:.0f}%"
                        )

                    with col2:
                        st.metric("仓位建议", result.position_advice)

                    with col3:
                        st.metric("风险等级", result.risk_level)

                    with col4:
                        st.metric("时间周期", result.time_horizon)

                    # 价格目标
                    if result.target_price > 0 or result.stop_loss > 0:
                        st.markdown("### 🎯 价格目标")
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("当前价格", f"¥{current_price:.2f}")
                        with col2:
                            if result.target_price > 0:
                                gain = (result.target_price - current_price) / current_price * 100
                                st.metric("目标价", f"¥{result.target_price:.2f}", f"+{gain:.1f}%")
                        with col3:
                            if result.stop_loss > 0:
                                loss = (result.stop_loss - current_price) / current_price * 100
                                st.metric("止损价", f"¥{result.stop_loss:.2f}", f"{loss:.1f}%")

                    # 分析理由
                    st.markdown("### 📝 分析理由")
                    st.info(result.reasoning)

                    # 关键因素
                    if result.key_factors:
                        st.markdown("### 🔑 关键因素")
                        for factor in result.key_factors:
                            st.markdown(f"- {factor}")

                    # 风险提示
                    if result.warnings:
                        st.markdown("### ⚠️ 风险提示")
                        for warning in result.warnings:
                            st.warning(warning)

                    # 参考新闻
                    if news:
                        st.markdown("### 📰 参考新闻")
                        for n in news[:3]:
                            st.markdown(f"- {n['title']}")

        except Exception as e:
            st.error(f"❌ 分析失败: {str(e)}")
            import traceback
            with st.expander("查看错误详情"):
                st.code(traceback.format_exc())

st.markdown("---")

# 使用说明
with st.expander("📖 使用说明"):
    st.markdown("""
    ### AI智能分析功能说明

    **1. 快速技术分析（无需API）**
    - 基于技术指标的快速信号判断
    - 计算MA、RSI、MACD、KDJ、布林带等指标
    - 综合多个指标给出买卖信号

    **2. 完整AI分析（需要DeepSeek API）**
    - 调用DeepSeek大模型进行深度分析
    - 综合技术面、基本面、新闻舆情
    - 给出详细的分析理由和风险提示

    **技术指标说明：**
    - **RSI < 30**: 超卖信号，可能反弹
    - **RSI > 70**: 超买信号，可能回调
    - **MACD金叉**: DIF上穿DEA，买入信号
    - **MACD死叉**: DIF下穿DEA，卖出信号
    - **布林带突破上轨**: 强势，但注意回调
    - **布林带跌破下轨**: 弱势，但可能超跌反弹
    """)
