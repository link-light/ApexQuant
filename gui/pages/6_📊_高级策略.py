"""
高级策略分析页面

包含多因子分析、事件驱动策略、配对交易、深度学习预测
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
    page_title="高级策略 - ApexQuant",
    page_icon="📊",
    layout="wide"
)

st.title("📊 高级策略分析")
st.markdown("多因子选股 | 事件驱动 | 配对交易 | 深度学习预测")
st.markdown("---")


# ============================================================
# 辅助函数
# ============================================================

def generate_mock_price_data(symbol: str, days: int = 120) -> pd.DataFrame:
    """生成模拟价格数据"""
    np.random.seed(int(symbol) if symbol.isdigit() else hash(symbol) % 10000)
    base_price = 50 + np.random.rand() * 150
    returns = np.random.randn(days) * 0.02
    prices = base_price * np.exp(np.cumsum(returns))

    dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
    df = pd.DataFrame({
        'date': dates,
        'open': prices * (1 + np.random.randn(days) * 0.005),
        'high': prices * (1 + abs(np.random.randn(days) * 0.01)),
        'low': prices * (1 - abs(np.random.randn(days) * 0.01)),
        'close': prices,
        'volume': np.random.randint(500000, 8000000, days)
    })
    return df


def get_stock_data_safe(symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
    """安全获取股票数据，失败则使用模拟数据"""
    try:
        from apexquant.data import get_stock_data
        df = get_stock_data(symbol, start_date, end_date)
        if df is not None and not df.empty:
            return df
    except Exception:
        pass

    try:
        from apexquant.simulation.data_source import SimulationDataSource
        data_source = SimulationDataSource()
        df = data_source.get_stock_data(symbol, start_date, end_date)
        if df is not None and not df.empty:
            return df
    except Exception:
        pass

    return None


def signal_badge(signal: str) -> str:
    """信号徽章"""
    badges = {
        'buy': '🟢 买入',
        'sell': '🔴 卖出',
        'hold': '🟡 持有',
        'long_spread': '🟢 做多价差',
        'short_spread': '🔴 做空价差',
        'close': '⚪ 平仓',
        'up': '🟢 上涨',
        'down': '🔴 下跌',
        'neutral': '🟡 中性',
        'add': '🟢 加仓',
    }
    return badges.get(signal, f'⚪ {signal}')


def _display_event_signal(signal, eps_actual=None, eps_estimate=None):
    """显示事件信号结果"""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("交易信号", signal_badge(signal.signal))
    with col2:
        st.metric("信号强度", f"{signal.strength:.0%}")
    with col3:
        st.metric("入场窗口", f"{signal.entry_window} 天")
    with col4:
        st.metric("持有期", f"{signal.holding_period} 天")

    # EPS超预期指标
    if eps_actual is not None and eps_estimate is not None and eps_estimate != 0:
        eps_surprise = (eps_actual - eps_estimate) / abs(eps_estimate) * 100
        st.metric("EPS超预期", f"{eps_surprise:.1f}%",
                  f"实际 {eps_actual:.2f} vs 预期 {eps_estimate:.2f}")

    # 风控参数
    st.markdown("**风控参数**")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("止损线", f"{signal.stop_loss:.1%}")
    with col2:
        st.metric("止盈线", f"{signal.take_profit:.1%}")

    # 分析理由
    st.info(f"**分析结论**: {signal.reason}")

    # 事件详情
    with st.expander("事件详情"):
        event_dict = signal.event.to_dict()
        for k, v in event_dict.items():
            st.markdown(f"- **{k}**: {v}")


# ============================================================
# 策略选择
# ============================================================

strategy_tab = st.selectbox(
    "选择策略模块",
    ["多因子选股分析", "事件驱动策略", "配对交易 / 统计套利", "深度学习预测"],
    help="选择要使用的高级策略"
)

st.markdown("---")

# ============================================================
# 1. 多因子选股分析
# ============================================================
if strategy_tab == "多因子选股分析":
    st.markdown("### 🎯 多因子选股分析")
    st.markdown("基于动量、价值、质量、成长等多维因子综合评分")

    # 输入配置
    col1, col2 = st.columns(2)

    with col1:
        mf_symbols_input = st.text_area(
            "股票代码 (每行一个)",
            value="600519\n000858\n600036\n601318\n000001",
            height=120,
            help="输入多只股票进行横向比较，至少2只"
        )
        lookback_days = st.slider("回溯天数", 30, 250, 120)

    with col2:
        st.markdown("**因子权重配置**")
        w_momentum = st.slider("动量因子", 0.0, 1.0, 0.25, 0.05)
        w_value = st.slider("价值因子", 0.0, 1.0, 0.25, 0.05)
        w_quality = st.slider("质量因子", 0.0, 1.0, 0.20, 0.05)
        w_growth = st.slider("成长因子", 0.0, 1.0, 0.15, 0.05)
        w_volatility = st.slider("波动因子", 0.0, 1.0, 0.10, 0.05)
        w_liquidity = st.slider("流动性因子", 0.0, 1.0, 0.05, 0.05)

    # 基本面数据输入(可选)
    with st.expander("📋 基本面数据 (可选，提升分析精度)"):
        st.markdown("留空则仅使用价量因子分析")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            fund_pe = st.number_input("PE (市盈率)", value=0.0, step=1.0, format="%.1f")
            fund_pb = st.number_input("PB (市净率)", value=0.0, step=0.1, format="%.1f")
        with col2:
            fund_roe = st.number_input("ROE (%)", value=0.0, step=1.0, format="%.1f")
            fund_gross_margin = st.number_input("毛利率 (%)", value=0.0, step=1.0, format="%.1f")
        with col3:
            fund_revenue_growth = st.number_input("营收增长率 (%)", value=0.0, step=1.0, format="%.1f")
            fund_profit_growth = st.number_input("净利润增长率 (%)", value=0.0, step=1.0, format="%.1f")
        with col4:
            fund_dividend_yield = st.number_input("股息率 (%)", value=0.0, step=0.1, format="%.1f")
            fund_debt_ratio = st.number_input("资产负债率 (%)", value=0.0, step=1.0, format="%.1f")

    st.markdown("---")

    if st.button("🚀 开始多因子分析", type="primary", use_container_width=True):
        with st.spinner("正在计算因子得分..."):
            try:
                from apexquant.strategy import MultiFactorStrategy, StockScore, calculate_stock_score

                symbols = [s.strip() for s in mf_symbols_input.strip().split('\n') if s.strip()]

                if len(symbols) < 1:
                    st.error("请至少输入1只股票")
                else:
                    strategy = MultiFactorStrategy(weights={
                        'momentum': w_momentum,
                        'value': w_value,
                        'quality': w_quality,
                        'growth': w_growth,
                        'volatility': w_volatility,
                        'size': w_liquidity,
                    })

                    end_date = datetime.now().strftime('%Y-%m-%d')
                    start_date = (datetime.now() - timedelta(days=lookback_days)).strftime('%Y-%m-%d')

                    # 构建基本面数据
                    fundamental = None
                    if fund_pe > 0 or fund_roe > 0:
                        fundamental = {}
                        if fund_pe > 0: fundamental['pe_ttm'] = fund_pe
                        if fund_pb > 0: fundamental['pb'] = fund_pb
                        if fund_roe > 0: fundamental['roe'] = fund_roe
                        if fund_gross_margin > 0: fundamental['gross_margin'] = fund_gross_margin
                        if fund_revenue_growth != 0: fundamental['revenue_growth'] = fund_revenue_growth
                        if fund_profit_growth != 0: fundamental['profit_growth'] = fund_profit_growth
                        if fund_dividend_yield > 0: fundamental['dividend_yield'] = fund_dividend_yield
                        if fund_debt_ratio > 0: fundamental['debt_ratio'] = fund_debt_ratio

                    # 获取数据并计算因子
                    progress_bar = st.progress(0)
                    stocks_data = {}
                    all_scores = []
                    failed_symbols = []

                    for idx, symbol in enumerate(symbols):
                        progress_bar.progress((idx + 1) / len(symbols))

                        df = get_stock_data_safe(symbol, start_date, end_date)
                        if df is None or df.empty:
                            st.info(f"{symbol}: 使用模拟数据")
                            df = generate_mock_price_data(symbol, lookback_days)

                        stocks_data[symbol] = {
                            'price_data': df,
                            'fundamental': fundamental,
                            'capital_flow': None
                        }

                    progress_bar.empty()

                    # 多股票排名
                    if len(symbols) >= 2:
                        scores = strategy.rank_stocks(stocks_data, top_n=len(symbols))
                    else:
                        # 单股票评分
                        sym = symbols[0]
                        data = stocks_data[sym]
                        score = calculate_stock_score(
                            sym, data['price_data'],
                            data.get('fundamental'),
                            data.get('capital_flow')
                        )
                        scores = [score]
                        scores[0].rank = 1

                    st.success(f"分析完成！共分析 {len(scores)} 只股票")

                    # 综合排名表
                    st.markdown("### 🏆 综合排名")

                    ranking_data = []
                    for s in scores:
                        ranking_data.append({
                            '排名': s.rank,
                            '股票代码': s.symbol,
                            '综合得分': f"{s.total_score:.4f}",
                            '信号': signal_badge(s.signal),
                            '因子数': len(s.factors),
                        })

                    st.dataframe(
                        pd.DataFrame(ranking_data),
                        hide_index=True,
                        use_container_width=True
                    )

                    # 每只股票的因子详情
                    st.markdown("### 📋 因子详情")

                    for s in scores:
                        with st.expander(f"**{s.symbol}** - 排名第{s.rank} | 得分: {s.total_score:.4f} | {signal_badge(s.signal)}"):
                            if s.factors:
                                # 按类型分组
                                factor_groups = {}
                                for fname, fval in s.factors.items():
                                    ftype = fval.factor_type.value
                                    if ftype not in factor_groups:
                                        factor_groups[ftype] = []
                                    factor_groups[ftype].append({
                                        '因子名': fval.name,
                                        '原始值': f"{fval.raw_value:.4f}",
                                        'Z-Score': f"{fval.z_score:.4f}",
                                        '权重': f"{fval.weight:.4f}",
                                        '加权得分': f"{fval.weighted_score:.4f}",
                                    })

                                type_names = {
                                    'momentum': '动量因子',
                                    'volatility': '波动因子',
                                    'liquidity': '流动性因子',
                                    'technical': '技术因子',
                                    'value': '价值因子',
                                    'quality': '质量因子',
                                    'growth': '成长因子',
                                }

                                cols = st.columns(min(len(factor_groups), 3))
                                for i, (ftype, factors_list) in enumerate(factor_groups.items()):
                                    with cols[i % 3]:
                                        st.markdown(f"**{type_names.get(ftype, ftype)}**")
                                        st.dataframe(
                                            pd.DataFrame(factors_list),
                                            hide_index=True,
                                            use_container_width=True
                                        )
                            else:
                                st.info("无因子数据")

            except Exception as e:
                st.error(f"分析失败: {str(e)}")
                with st.expander("查看错误详情"):
                    st.code(traceback.format_exc())


# ============================================================
# 2. 事件驱动策略
# ============================================================
elif strategy_tab == "事件驱动策略":
    st.markdown("### 🎯 事件驱动策略")
    st.markdown("基于财报发布、股东增减持、大宗交易等事件的交易信号")

    event_type = st.selectbox(
        "事件类型",
        ["财报分析", "股东增减持", "大宗交易", "财报前策略"]
    )

    col1, col2 = st.columns(2)

    with col1:
        event_symbol = st.text_input("股票代码", value="600519", key="event_symbol")

    with col2:
        event_date = st.date_input("事件日期", value=datetime.now())

    st.markdown("---")

    # 财报分析
    if event_type == "财报分析":
        st.markdown("#### 📄 财报数据输入")
        col1, col2, col3 = st.columns(3)
        with col1:
            eps_actual = st.number_input("实际EPS", value=2.50, step=0.01, format="%.2f")
            eps_estimate = st.number_input("预期EPS", value=2.20, step=0.01, format="%.2f")
        with col2:
            er_revenue_growth = st.number_input("营收增长率 (%)", value=15.0, step=1.0, key="er_rg")
            er_profit_growth = st.number_input("净利增长率 (%)", value=20.0, step=1.0, key="er_pg")
        with col3:
            revenue_actual = st.number_input("实际营收 (亿)", value=0.0, step=1.0)
            revenue_estimate = st.number_input("预期营收 (亿)", value=0.0, step=1.0)

        if st.button("🚀 分析财报事件", type="primary", use_container_width=True):
            with st.spinner("正在分析..."):
                try:
                    from apexquant.strategy import (
                        EventDrivenStrategy, create_earnings_event
                    )

                    event = create_earnings_event(
                        symbol=event_symbol,
                        date=datetime.combine(event_date, datetime.min.time()),
                        eps_actual=eps_actual,
                        eps_estimate=eps_estimate,
                        revenue_growth=er_revenue_growth,
                        profit_growth=er_profit_growth,
                    )

                    strategy = EventDrivenStrategy()
                    signal = strategy.analyze_event(event)

                    st.success("分析完成！")
                    _display_event_signal(signal, eps_actual, eps_estimate)

                except Exception as e:
                    st.error(f"分析失败: {str(e)}")
                    with st.expander("查看错误详情"):
                        st.code(traceback.format_exc())

    # 股东增减持
    elif event_type == "股东增减持":
        st.markdown("#### 📋 增减持信息")
        col1, col2, col3 = st.columns(3)
        with col1:
            holder_type = st.selectbox("股东类型", ["major", "executive", "fund"],
                                       format_func=lambda x: {'major': '大股东', 'executive': '高管', 'fund': '基金'}[x])
        with col2:
            change_type = st.selectbox("变动方向", ["increase", "decrease"],
                                       format_func=lambda x: {'increase': '增持', 'decrease': '减持'}[x])
        with col3:
            change_ratio = st.number_input("变动比例 (%)", value=3.0, step=0.5, format="%.1f")

        holder_name = st.text_input("股东名称 (可选)", value="")

        if st.button("🚀 分析增减持", type="primary", use_container_width=True):
            with st.spinner("正在分析..."):
                try:
                    from apexquant.strategy import (
                        EventDrivenStrategy, create_holder_change_event
                    )

                    event = create_holder_change_event(
                        symbol=event_symbol,
                        date=datetime.combine(event_date, datetime.min.time()),
                        holder_type=holder_type,
                        change_type=change_type,
                        change_ratio=change_ratio,
                        holder_name=holder_name,
                    )

                    strategy = EventDrivenStrategy()
                    signal = strategy.analyze_event(event)

                    st.success("分析完成！")
                    _display_event_signal(signal)

                except Exception as e:
                    st.error(f"分析失败: {str(e)}")
                    with st.expander("查看错误详情"):
                        st.code(traceback.format_exc())

    # 大宗交易
    elif event_type == "大宗交易":
        st.markdown("#### 📋 大宗交易信息")
        col1, col2 = st.columns(2)
        with col1:
            trade_price = st.number_input("成交价格", value=100.0, step=1.0, format="%.2f")
            close_price = st.number_input("收盘价格", value=105.0, step=1.0, format="%.2f")
        with col2:
            trade_amount = st.number_input("成交金额 (万元)", value=5000.0, step=100.0)
            recent_avg_volume = st.number_input("日均成交额 (万元)", value=10000.0, step=100.0)

        if st.button("🚀 分析大宗交易", type="primary", use_container_width=True):
            with st.spinner("正在分析..."):
                try:
                    from apexquant.strategy import (
                        EventDrivenStrategy, Event, EventType
                    )

                    event = Event(
                        event_type=EventType.BLOCK_TRADE,
                        symbol=event_symbol,
                        date=datetime.combine(event_date, datetime.min.time()),
                        title=f"大宗交易: 成交价{trade_price:.2f}",
                        data={
                            'trade_price': trade_price,
                            'close_price': close_price,
                            'trade_amount': trade_amount * 10000,
                        }
                    )

                    strategy = EventDrivenStrategy()
                    signal = strategy.analyze_event(
                        event,
                        context={'recent_avg_volume': recent_avg_volume * 10000}
                    )

                    st.success("分析完成！")
                    _display_event_signal(signal)

                except Exception as e:
                    st.error(f"分析失败: {str(e)}")
                    with st.expander("查看错误详情"):
                        st.code(traceback.format_exc())

    # 财报前策略
    elif event_type == "财报前策略":
        st.markdown("#### 📋 历史财报表现")
        col1, col2 = st.columns(2)
        with col1:
            total_quarters = st.number_input("统计季度数", value=8, min_value=1, max_value=40, step=1)
        with col2:
            historical_beats = st.number_input("超预期次数", value=6, min_value=0,
                                               max_value=total_quarters, step=1)

        if st.button("🚀 分析财报前策略", type="primary", use_container_width=True):
            with st.spinner("正在分析..."):
                try:
                    from apexquant.strategy import EventDrivenStrategy

                    strategy = EventDrivenStrategy()
                    signal = strategy.earnings_strategy.pre_earnings_strategy(
                        symbol=event_symbol,
                        earnings_date=datetime.combine(event_date, datetime.min.time()),
                        historical_beats=historical_beats,
                        total_quarters=total_quarters,
                    )

                    st.success("分析完成！")

                    beat_ratio = historical_beats / total_quarters * 100
                    st.metric("历史超预期率", f"{beat_ratio:.0f}%",
                              f"{historical_beats}/{total_quarters} 季度")

                    _display_event_signal(signal)

                except Exception as e:
                    st.error(f"分析失败: {str(e)}")
                    with st.expander("查看错误详情"):
                        st.code(traceback.format_exc())


# ============================================================
# 3. 配对交易
# ============================================================
elif strategy_tab == "配对交易 / 统计套利":
    st.markdown("### 🎯 配对交易 / 统计套利")
    st.markdown("基于协整关系的配对交易策略，寻找均值回归机会")

    col1, col2 = st.columns(2)

    with col1:
        pair_symbols_input = st.text_area(
            "股票代码 (每行一个，至少2只)",
            value="600519\n000858\n600036\n601318",
            height=100,
            help="输入多只股票寻找协整配对"
        )
        pair_lookback = st.slider("回溯天数", 60, 500, 252, key="pair_lookback")

    with col2:
        st.markdown("**策略参数**")
        entry_threshold = st.slider("开仓阈值 (Z-Score)", 1.0, 4.0, 2.0, 0.1)
        exit_threshold = st.slider("平仓阈值 (Z-Score)", 0.0, 2.0, 0.5, 0.1)
        stop_loss_threshold = st.slider("止损阈值 (Z-Score)", 2.0, 6.0, 4.0, 0.1)
        min_correlation = st.slider("最小相关性", 0.3, 0.95, 0.7, 0.05)

    st.markdown("---")

    if st.button("🚀 寻找配对并分析", type="primary", use_container_width=True):
        with st.spinner("正在进行协整检验..."):
            try:
                from apexquant.strategy import PairsTrading, PairInfo

                symbols = [s.strip() for s in pair_symbols_input.strip().split('\n') if s.strip()]

                if len(symbols) < 2:
                    st.error("请至少输入2只股票")
                else:
                    end_date = datetime.now().strftime('%Y-%m-%d')
                    start_date = (datetime.now() - timedelta(days=pair_lookback)).strftime('%Y-%m-%d')

                    # 获取价格数据
                    price_data = {}
                    progress_bar = st.progress(0)

                    for idx, symbol in enumerate(symbols):
                        progress_bar.progress((idx + 1) / len(symbols))
                        df = get_stock_data_safe(symbol, start_date, end_date)
                        if df is None or df.empty:
                            df = generate_mock_price_data(symbol, pair_lookback)

                        if 'date' in df.columns:
                            df = df.set_index('date')
                        price_data[symbol] = df['close']

                    progress_bar.empty()

                    # 配对交易策略
                    pt_strategy = PairsTrading(
                        entry_threshold=entry_threshold,
                        exit_threshold=exit_threshold,
                        stop_loss_threshold=stop_loss_threshold,
                        min_correlation=min_correlation,
                        lookback_period=min(60, pair_lookback // 2)
                    )

                    # 寻找协整配对
                    pairs = pt_strategy.find_cointegrated_pairs(price_data, min_samples=60)

                    if not pairs:
                        st.warning("未找到协整配对。可以尝试降低最小相关性或增加回溯天数。")

                        # 仍然显示相关性矩阵
                        st.markdown("### 相关性矩阵")
                        price_df = pd.DataFrame(price_data)
                        corr_matrix = price_df.corr()
                        st.dataframe(
                            corr_matrix.style.format("{:.3f}").background_gradient(cmap='RdYlGn'),
                            use_container_width=True
                        )
                    else:
                        st.success(f"找到 {len(pairs)} 个协整配对！")

                        # 配对信息表
                        st.markdown("### 🔗 协整配对")

                        pair_table = []
                        for p in pairs:
                            pair_table.append({
                                '股票A': p.stock_a,
                                '股票B': p.stock_b,
                                '相关性': f"{p.correlation:.3f}",
                                '协整P值': f"{p.cointegration_pvalue:.4f}",
                                '对冲比率': f"{p.hedge_ratio:.4f}",
                                '半衰期(天)': f"{p.half_life:.1f}",
                                '价差均值': f"{p.spread_mean:.2f}",
                                '价差标准差': f"{p.spread_std:.2f}",
                            })

                        st.dataframe(
                            pd.DataFrame(pair_table),
                            hide_index=True,
                            use_container_width=True
                        )

                        # 每个配对的详细分析
                        for pair in pairs:
                            with st.expander(f"**{pair.stock_a} - {pair.stock_b}** | 协整P值: {pair.cointegration_pvalue:.4f}"):
                                # 当前信号
                                current_a = price_data[pair.stock_a].iloc[-1]
                                current_b = price_data[pair.stock_b].iloc[-1]

                                signal = pt_strategy.generate_signal(pair, current_a, current_b)

                                col1, col2, col3, col4 = st.columns(4)
                                with col1:
                                    st.metric("当前Z-Score", f"{signal.z_score:.2f}")
                                with col2:
                                    st.metric("交易信号", signal_badge(signal.signal))
                                with col3:
                                    st.metric(f"{pair.stock_a} 价格", f"{current_a:.2f}")
                                with col4:
                                    st.metric(f"{pair.stock_b} 价格", f"{current_b:.2f}")

                                st.info(f"**分析**: {signal.reason}")

                                if signal.signal in ('long_spread', 'short_spread'):
                                    st.markdown("**建议操作:**")
                                    if signal.signal == 'long_spread':
                                        st.markdown(f"- 买入 **{pair.stock_a}** (仓位系数: {signal.position_a:.2f})")
                                        st.markdown(f"- 卖出 **{pair.stock_b}** (仓位系数: {abs(signal.position_b):.2f})")
                                    else:
                                        st.markdown(f"- 卖出 **{pair.stock_a}** (仓位系数: {abs(signal.position_a):.2f})")
                                        st.markdown(f"- 买入 **{pair.stock_b}** (仓位系数: {signal.position_b:.2f})")

                                # 回测
                                st.markdown("---")
                                st.markdown("**回测结果**")

                                try:
                                    bt_result = pt_strategy.backtest_pair(
                                        pair,
                                        price_data[pair.stock_a],
                                        price_data[pair.stock_b],
                                        initial_capital=100000
                                    )

                                    col1, col2, col3, col4 = st.columns(4)
                                    with col1:
                                        st.metric("总收益", f"{bt_result['total_return']:.2f}%")
                                    with col2:
                                        st.metric("夏普比率", f"{bt_result['sharpe_ratio']:.2f}")
                                    with col3:
                                        st.metric("最大回撤", f"{bt_result['max_drawdown']:.2f}%")
                                    with col4:
                                        st.metric("胜率", f"{bt_result['win_rate']:.1f}%")

                                    # 权益曲线
                                    if 'equity_curve' in bt_result and bt_result['equity_curve'] is not None:
                                        st.markdown("**权益曲线**")
                                        equity_df = pd.DataFrame({
                                            '权益': bt_result['equity_curve'].values
                                        }, index=bt_result['equity_curve'].index)
                                        st.line_chart(equity_df)

                                except Exception as bt_err:
                                    st.warning(f"回测计算异常: {bt_err}")

            except Exception as e:
                st.error(f"分析失败: {str(e)}")
                with st.expander("查看错误详情"):
                    st.code(traceback.format_exc())


# ============================================================
# 4. 深度学习预测
# ============================================================
elif strategy_tab == "深度学习预测":
    st.markdown("### 🎯 深度学习趋势预测")
    st.markdown("使用 LSTM/GRU 神经网络预测价格走势")

    col1, col2 = st.columns(2)

    with col1:
        dl_symbol = st.text_input("股票代码", value="600519", key="dl_symbol")
        dl_lookback = st.slider("训练数据天数", 100, 1000, 500, key="dl_lookback")

    with col2:
        model_type = st.selectbox("模型类型", ["lstm", "gru", "attention_lstm"],
                                   format_func=lambda x: {
                                       'lstm': 'LSTM (长短期记忆)',
                                       'gru': 'GRU (门控循环单元)',
                                       'attention_lstm': 'Attention LSTM (注意力机制)'
                                   }[x])
        predict_days = st.selectbox("预测周期", [3, 5, 10, 20],
                                     index=1,
                                     format_func=lambda x: f"未来 {x} 天")

    with st.expander("🔧 模型参数"):
        col1, col2, col3 = st.columns(3)
        with col1:
            seq_length = st.number_input("序列长度", value=20, min_value=5, max_value=60, step=5)
            hidden_size = st.number_input("隐藏层大小", value=64, min_value=16, max_value=256, step=16)
        with col2:
            num_layers = st.number_input("网络层数", value=2, min_value=1, max_value=4, step=1)
            dropout_rate = st.slider("Dropout率", 0.0, 0.5, 0.2, 0.05)
        with col3:
            epochs = st.number_input("训练轮数", value=50, min_value=10, max_value=500, step=10)
            batch_size = st.selectbox("批大小", [16, 32, 64, 128], index=1)

    st.markdown("---")

    if st.button("🚀 训练并预测", type="primary", use_container_width=True):
        with st.spinner("正在获取数据并训练模型..."):
            try:
                from apexquant.strategy import DeepLearningPredictor, PredictionResult

                end_date = datetime.now().strftime('%Y-%m-%d')
                start_date = (datetime.now() - timedelta(days=dl_lookback)).strftime('%Y-%m-%d')

                df = get_stock_data_safe(dl_symbol, start_date, end_date)
                if df is None or df.empty:
                    st.warning("使用模拟数据进行演示")
                    df = generate_mock_price_data(dl_symbol, dl_lookback)

                st.info(f"数据量: {len(df)} 条记录")

                # 创建预测器
                predictor = DeepLearningPredictor(
                    model_type=model_type,
                    sequence_length=seq_length,
                    hidden_size=hidden_size,
                    num_layers=num_layers,
                    dropout=dropout_rate,
                )

                # 训练
                st.info("正在训练模型...")
                train_result = predictor.train(
                    df,
                    target_days=predict_days,
                    epochs=epochs,
                    batch_size=batch_size,
                )

                if 'error' in train_result:
                    st.error(f"训练失败: {train_result['error']}")
                else:
                    # 训练结果
                    st.markdown("### 📊 训练结果")

                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("模型类型", train_result.get('model_type', model_type))
                    with col2:
                        st.metric("训练准确率",
                                  f"{train_result.get('train_accuracy', 0)*100:.1f}%")
                    with col3:
                        st.metric("验证准确率",
                                  f"{train_result.get('val_accuracy', 0)*100:.1f}%")
                    with col4:
                        st.metric("训练样本数",
                                  f"{train_result.get('train_samples', 0)}")

                    # 预测
                    st.markdown("### 🔮 预测结果")
                    prediction = predictor.predict(df, symbol=dl_symbol)

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric(f"未来{predict_days}天趋势",
                                  signal_badge(prediction.prediction))
                    with col2:
                        st.metric("预测置信度",
                                  f"{prediction.probability*100:.1f}%")
                    with col3:
                        st.metric("预测收益率",
                                  f"{prediction.predicted_return:.2f}%")

                    # 特征信息
                    if prediction.features_used:
                        with st.expander(f"使用了 {len(prediction.features_used)} 个特征"):
                            cols = st.columns(4)
                            for i, feat in enumerate(prediction.features_used):
                                with cols[i % 4]:
                                    st.markdown(f"- `{feat}`")

                    # 价格走势图
                    st.markdown("### 📈 近期价格走势")
                    recent_df = df.tail(60)
                    chart_data = pd.DataFrame({
                        '收盘价': recent_df['close'].values
                    }, index=range(len(recent_df)))
                    st.line_chart(chart_data)

            except Exception as e:
                st.error(f"预测失败: {str(e)}")
                with st.expander("查看错误详情"):
                    st.code(traceback.format_exc())


# ============================================================
# 页脚
# ============================================================
st.markdown("---")

with st.expander("📖 使用说明"):
    st.markdown("""
    ### 高级策略分析功能说明

    **1. 多因子选股分析**
    - 输入多只股票进行横向对比
    - 基于33个量化因子（动量/波动/流动性/技术/价值/质量/成长）计算综合得分
    - 支持自定义因子权重和基本面数据输入
    - 前20%标记为买入信号，后20%标记为卖出信号

    **2. 事件驱动策略**
    - **财报分析**: 根据EPS超预期程度、营收增长等判断交易信号
    - **股东增减持**: 分析大股东/高管/基金的增减持影响
    - **大宗交易**: 分析溢价/折价交易的信号含义
    - **财报前策略**: 根据历史超预期率制定财报前建仓策略

    **3. 配对交易 / 统计套利**
    - 自动寻找协整配对（均值回归特性）
    - Z-Score信号：超过开仓阈值时开仓，回归至平仓阈值时平仓
    - 内置配对回测，展示收益曲线和风险指标

    **4. 深度学习预测**
    - 支持LSTM、GRU、Attention LSTM三种模型
    - 自动生成20+技术特征用于训练
    - 无PyTorch时自动回退为sklearn GradientBoosting
    - 输出上涨/下跌预测及置信度
    """)
