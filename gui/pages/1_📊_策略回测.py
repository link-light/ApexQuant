"""
策略回测页面

支持多种策略回测、Plotly 交互图表、参数优化、策略对比
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
    page_title="策略回测 - ApexQuant",
    page_icon="📊",
    layout="wide"
)

st.title("📊 策略回测")
st.markdown("使用历史数据测试交易策略，支持 Plotly 交互图表与参数优化")
st.markdown("---")


# ============================================================
# 辅助函数
# ============================================================

def generate_mock_price_data(symbol: str, days: int = 252) -> pd.DataFrame:
    """生成模拟价格数据"""
    seed = int(symbol.replace('.', '').replace('sh', '').replace('sz', ''))
    np.random.seed(seed % 10000)
    base = 50 + np.random.rand() * 150
    returns = np.random.randn(days) * 0.018
    prices = base * np.exp(np.cumsum(returns))
    dates = pd.date_range(end=datetime.now(), periods=days, freq='B')

    df = pd.DataFrame({
        'date': dates,
        'open': prices * (1 + np.random.randn(days) * 0.005),
        'high': prices * (1 + abs(np.random.randn(days) * 0.012)),
        'low': prices * (1 - abs(np.random.randn(days) * 0.012)),
        'close': prices,
        'volume': np.random.randint(500000, 8000000, days),
    })
    return df


def get_stock_data_safe(symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
    """安全获取数据，失败则返回 None"""
    try:
        from apexquant.data import get_stock_data
        df = get_stock_data(symbol, start_date, end_date)
        if df is not None and not df.empty:
            return df
    except Exception:
        pass
    try:
        from apexquant.simulation.data_source import SimulationDataSource
        df = SimulationDataSource().get_stock_data(symbol, start_date, end_date)
        if df is not None and not df.empty:
            return df
    except Exception:
        pass
    return None


# ============================================================
# 功能模式选择
# ============================================================

mode = st.radio(
    "功能模式",
    ["策略回测", "参数优化", "策略对比"],
    horizontal=True,
)

st.markdown("---")


# ============================================================
# 公共输入: 数据配置
# ============================================================

st.markdown("### ⚙️ 数据配置")

col1, col2 = st.columns(2)

with col1:
    bt_symbol = st.text_input("股票代码", value="600519", key="bt_symbol")
    start_date = st.date_input("开始日期", value=datetime.now() - timedelta(days=500))
    end_date = st.date_input("结束日期", value=datetime.now())

with col2:
    initial_capital = st.number_input("初始资金 (元)", 10000, 100000000, 1000000, 10000)
    commission = st.slider("手续费率 (%)", 0.0, 0.5, 0.03, 0.01)
    slippage = st.slider("滑点率 (%)", 0.0, 1.0, 0.1, 0.01)

st.markdown("---")


# ============================================================
# 模式 1: 策略回测
# ============================================================
if mode == "策略回测":

    st.markdown("### 🎛️ 策略配置")

    strategy_choice = st.selectbox(
        "选择策略",
        ["均线交叉 (MA Cross)", "RSI策略", "买入持有 (Buy & Hold)",
         "多因子策略", "深度学习预测"]
    )

    # 策略参数
    strategy_params = {}

    if strategy_choice == "均线交叉 (MA Cross)":
        col1, col2 = st.columns(2)
        with col1:
            strategy_params['ma_short'] = st.number_input("短期均线", 2, 50, 5)
        with col2:
            strategy_params['ma_long'] = st.number_input("长期均线", 10, 200, 20)

    elif strategy_choice == "RSI策略":
        col1, col2, col3 = st.columns(3)
        with col1:
            strategy_params['rsi_period'] = st.number_input("RSI周期", 5, 30, 14)
        with col2:
            strategy_params['oversold'] = st.number_input("超卖线", 10, 40, 30)
        with col3:
            strategy_params['overbought'] = st.number_input("超买线", 60, 90, 70)

    elif strategy_choice == "多因子策略":
        col1, col2 = st.columns(2)
        with col1:
            strategy_params['rebalance_freq'] = st.number_input("调仓频率 (天)", 5, 60, 20)
            strategy_params['buy_threshold'] = st.slider("买入阈值", -1.0, 3.0, 0.5, 0.1)
        with col2:
            strategy_params['sell_threshold'] = st.slider("卖出阈值", -3.0, 1.0, -0.5, 0.1)

        with st.expander("因子权重"):
            col1, col2, col3 = st.columns(3)
            with col1:
                w_mom = st.slider("动量", 0.0, 1.0, 0.25, 0.05, key="bt_w_mom")
                w_val = st.slider("价值", 0.0, 1.0, 0.25, 0.05, key="bt_w_val")
            with col2:
                w_qual = st.slider("质量", 0.0, 1.0, 0.20, 0.05, key="bt_w_qual")
                w_grow = st.slider("成长", 0.0, 1.0, 0.15, 0.05, key="bt_w_grow")
            with col3:
                w_vol = st.slider("波动", 0.0, 1.0, 0.10, 0.05, key="bt_w_vol")
                w_liq = st.slider("流动性", 0.0, 1.0, 0.05, 0.05, key="bt_w_liq")
            strategy_params['weights'] = {
                'momentum': w_mom, 'value': w_val, 'quality': w_qual,
                'growth': w_grow, 'volatility': w_vol, 'size': w_liq,
            }

    elif strategy_choice == "深度学习预测":
        col1, col2 = st.columns(2)
        with col1:
            strategy_params['model_type'] = st.selectbox("模型类型", ["lstm", "gru", "attention_lstm"],
                                                          format_func=lambda x: {'lstm': 'LSTM', 'gru': 'GRU',
                                                                                  'attention_lstm': 'Attention LSTM'}[x])
            strategy_params['predict_days'] = st.selectbox("预测周期 (天)", [3, 5, 10, 20], index=1)
        with col2:
            strategy_params['train_ratio'] = st.slider("训练集比例", 0.3, 0.8, 0.6, 0.05)
            strategy_params['threshold'] = st.slider("信号置信度阈值", 0.5, 0.9, 0.55, 0.05)

    st.markdown("---")

    # 运行回测
    if st.button("🚀 开始回测", type="primary", use_container_width=True):
        with st.spinner("正在运行回测..."):
            try:
                from apexquant.backtest.strategy_backtester import StrategyBacktester

                backtester = StrategyBacktester(
                    initial_capital=initial_capital,
                    commission_rate=commission / 100,
                    slippage_rate=slippage / 100,
                )

                s_date = start_date.strftime('%Y-%m-%d')
                e_date = end_date.strftime('%Y-%m-%d')
                days = (end_date - start_date).days

                df = get_stock_data_safe(bt_symbol, s_date, e_date)
                if df is None or df.empty:
                    st.warning("使用模拟数据进行回测演示")
                    df = generate_mock_price_data(bt_symbol, days)

                df = df.reset_index(drop=True)
                st.info(f"数据量: {len(df)} 条 ({bt_symbol})")

                # 运行策略
                if strategy_choice == "均线交叉 (MA Cross)":
                    result = backtester.backtest_ma_cross(df, **strategy_params)
                elif strategy_choice == "RSI策略":
                    result = backtester.backtest_rsi(df, **strategy_params)
                elif strategy_choice == "买入持有 (Buy & Hold)":
                    result = backtester.backtest_buy_hold(df)
                elif strategy_choice == "多因子策略":
                    result = backtester.backtest_multi_factor(df, **strategy_params)
                elif strategy_choice == "深度学习预测":
                    result = backtester.backtest_dl_prediction(df, **strategy_params)
                else:
                    result = backtester.backtest_buy_hold(df)

                st.session_state['backtest_result'] = result
                st.session_state['backtest_price_df'] = df
                st.success("回测完成！")
                st.rerun()

            except Exception as e:
                st.error(f"回测失败: {str(e)}")
                with st.expander("查看错误详情"):
                    st.code(traceback.format_exc())

    # 显示结果
    if 'backtest_result' in st.session_state:
        result = st.session_state['backtest_result']
        _show_backtest_result(result, st.session_state.get('backtest_price_df'))


# ============================================================
# 模式 2: 参数优化
# ============================================================
elif mode == "参数优化":

    st.markdown("### 🔧 参数优化")

    opt_strategy = st.selectbox(
        "优化策略",
        ["均线交叉 (MA Cross)", "RSI策略"],
        key="opt_strategy"
    )

    objective = st.selectbox(
        "优化目标",
        ["sharpe_ratio", "total_return", "win_rate", "calmar_ratio"],
        format_func=lambda x: {
            'sharpe_ratio': '夏普比率', 'total_return': '总收益率',
            'win_rate': '胜率', 'calmar_ratio': 'Calmar比率',
        }[x]
    )

    st.markdown("**参数搜索范围**")

    if opt_strategy == "均线交叉 (MA Cross)":
        col1, col2 = st.columns(2)
        with col1:
            ma_short_range = st.text_input("短期均线范围", value="3,5,8,10,13")
        with col2:
            ma_long_range = st.text_input("长期均线范围", value="15,20,30,40,60")

    elif opt_strategy == "RSI策略":
        col1, col2, col3 = st.columns(3)
        with col1:
            rsi_period_range = st.text_input("RSI周期范围", value="7,10,14,20")
        with col2:
            oversold_range = st.text_input("超卖线范围", value="20,25,30,35")
        with col3:
            overbought_range = st.text_input("超买线范围", value="65,70,75,80")

    st.markdown("---")

    if st.button("🚀 开始参数优化", type="primary", use_container_width=True):
        with st.spinner("正在优化参数..."):
            try:
                from apexquant.backtest.strategy_backtester import StrategyBacktester

                backtester = StrategyBacktester(
                    initial_capital=initial_capital,
                    commission_rate=commission / 100,
                    slippage_rate=slippage / 100,
                )

                s_date = start_date.strftime('%Y-%m-%d')
                e_date = end_date.strftime('%Y-%m-%d')
                days = (end_date - start_date).days

                df = get_stock_data_safe(bt_symbol, s_date, e_date)
                if df is None or df.empty:
                    st.warning("使用模拟数据")
                    df = generate_mock_price_data(bt_symbol, days)
                df = df.reset_index(drop=True)

                if opt_strategy == "均线交叉 (MA Cross)":
                    param_grid = {
                        'ma_short': [int(x.strip()) for x in ma_short_range.split(',')],
                        'ma_long': [int(x.strip()) for x in ma_long_range.split(',')],
                    }
                    strategy_func = backtester.backtest_ma_cross

                elif opt_strategy == "RSI策略":
                    param_grid = {
                        'rsi_period': [int(x.strip()) for x in rsi_period_range.split(',')],
                        'oversold': [float(x.strip()) for x in oversold_range.split(',')],
                        'overbought': [float(x.strip()) for x in overbought_range.split(',')],
                    }
                    strategy_func = backtester.backtest_rsi

                total = 1
                for v in param_grid.values():
                    total *= len(v)
                st.info(f"共 {total} 个参数组合")

                progress_bar = st.progress(0)
                opt_result = backtester.run_parameter_optimization(
                    strategy_func, param_grid, df, objective=objective
                )
                progress_bar.empty()

                st.session_state['opt_result'] = opt_result
                st.session_state['opt_param_names'] = list(param_grid.keys())
                st.session_state['opt_objective'] = objective
                st.success("优化完成！")
                st.rerun()

            except Exception as e:
                st.error(f"优化失败: {str(e)}")
                with st.expander("查看错误详情"):
                    st.code(traceback.format_exc())

    # 显示优化结果
    if 'opt_result' in st.session_state:
        opt_result = st.session_state['opt_result']
        param_names = st.session_state.get('opt_param_names', [])
        obj = st.session_state.get('opt_objective', 'sharpe_ratio')

        st.markdown("### 🏆 优化结果")

        if opt_result.get('best_params'):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**最佳参数**")
                for k, v in opt_result['best_params'].items():
                    st.metric(k, v)
            with col2:
                st.metric(f"最佳 {obj}", f"{opt_result['best_score']:.4f}")
                st.metric("总组合数", opt_result.get('total_combinations', 0))

            # 优化图表
            try:
                from apexquant.backtest.plotly_charts import create_optimization_chart
                fig = create_optimization_chart(
                    opt_result['all_results'], param_names, obj
                )
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
            except Exception:
                pass

            # Top 10 结果表
            valid = [r for r in opt_result['all_results']
                     if 'error' not in r and r.get('score', float('-inf')) > float('-inf')]
            if valid:
                top_n = sorted(valid, key=lambda x: x['score'], reverse=True)[:10]
                table_data = []
                for i, r in enumerate(top_n, 1):
                    row = {'排名': i, **r['params'], obj: f"{r['score']:.4f}"}
                    if 'result' in r and isinstance(r['result'], dict):
                        row['总收益(%)'] = f"{r['result'].get('total_return', 0):.2f}"
                        row['最大回撤(%)'] = f"{r['result'].get('max_drawdown', 0):.2f}"
                    table_data.append(row)
                st.dataframe(pd.DataFrame(table_data), hide_index=True, use_container_width=True)

            # 用最优参数回测按钮
            if opt_result.get('best_result') and opt_result['best_result'].equity_curve is not None:
                st.markdown("### 📈 最优参数回测结果")
                _show_backtest_result(opt_result['best_result'])
        else:
            st.warning("未找到有效的参数组合")


# ============================================================
# 模式 3: 策略对比
# ============================================================
elif mode == "策略对比":

    st.markdown("### 📊 策略对比")

    cmp_strategies = st.multiselect(
        "选择要对比的策略 (至少2个)",
        ["均线交叉 (5/20)", "均线交叉 (10/30)", "均线交叉 (10/60)",
         "RSI (14/30/70)", "RSI (7/25/75)",
         "买入持有",
         "多因子策略"],
        default=["均线交叉 (5/20)", "RSI (14/30/70)", "买入持有"],
    )

    if len(cmp_strategies) < 2:
        st.warning("请选择至少2个策略进行对比")
    else:
        if st.button("🚀 开始对比", type="primary", use_container_width=True):
            with st.spinner("正在运行策略对比..."):
                try:
                    from apexquant.backtest.strategy_backtester import StrategyBacktester

                    backtester = StrategyBacktester(
                        initial_capital=initial_capital,
                        commission_rate=commission / 100,
                        slippage_rate=slippage / 100,
                    )

                    s_date = start_date.strftime('%Y-%m-%d')
                    e_date = end_date.strftime('%Y-%m-%d')
                    days = (end_date - start_date).days

                    df = get_stock_data_safe(bt_symbol, s_date, e_date)
                    if df is None or df.empty:
                        st.warning("使用模拟数据")
                        df = generate_mock_price_data(bt_symbol, days)
                    df = df.reset_index(drop=True)

                    results = {}
                    progress_bar = st.progress(0)

                    strategy_map = {
                        "均线交叉 (5/20)": lambda d: backtester.backtest_ma_cross(d, 5, 20, "MA(5/20)"),
                        "均线交叉 (10/30)": lambda d: backtester.backtest_ma_cross(d, 10, 30, "MA(10/30)"),
                        "均线交叉 (10/60)": lambda d: backtester.backtest_ma_cross(d, 10, 60, "MA(10/60)"),
                        "RSI (14/30/70)": lambda d: backtester.backtest_rsi(d, 14, 30, 70, "RSI(14/30/70)"),
                        "RSI (7/25/75)": lambda d: backtester.backtest_rsi(d, 7, 25, 75, "RSI(7/25/75)"),
                        "买入持有": lambda d: backtester.backtest_buy_hold(d),
                        "多因子策略": lambda d: backtester.backtest_multi_factor(d),
                    }

                    for idx, name in enumerate(cmp_strategies):
                        progress_bar.progress((idx + 1) / len(cmp_strategies))
                        if name in strategy_map:
                            results[name] = strategy_map[name](df)

                    progress_bar.empty()
                    st.session_state['cmp_results'] = results
                    st.success("对比完成！")
                    st.rerun()

                except Exception as e:
                    st.error(f"对比失败: {str(e)}")
                    with st.expander("查看错误详情"):
                        st.code(traceback.format_exc())

        # 显示对比结果
        if 'cmp_results' in st.session_state:
            results = st.session_state['cmp_results']

            # 对比图表
            try:
                from apexquant.backtest.plotly_charts import create_strategy_comparison_chart
                fig = create_strategy_comparison_chart(results)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
            except Exception:
                pass

            # 对比表格
            st.markdown("### 📋 指标对比")

            table_data = []
            for name, r in results.items():
                table_data.append({
                    '策略': name,
                    '总收益(%)': f"{r.total_return:.2f}",
                    '年化收益(%)': f"{r.annualized_return:.2f}",
                    '最大回撤(%)': f"{r.max_drawdown:.2f}",
                    '夏普比率': f"{r.sharpe_ratio:.2f}",
                    'Sortino': f"{r.sortino_ratio:.2f}",
                    'Calmar': f"{r.calmar_ratio:.2f}",
                    '总交易': r.total_trades,
                    '胜率(%)': f"{r.win_rate:.1f}",
                    '盈亏比': f"{r.profit_loss_ratio:.2f}",
                    '平均持有(天)': f"{r.avg_holding_days:.0f}",
                })

            st.dataframe(pd.DataFrame(table_data), hide_index=True, use_container_width=True)

            # 每个策略的权益曲线
            for name, r in results.items():
                with st.expander(f"{name} 详情"):
                    _show_backtest_result(r, show_title=False)


# ============================================================
# 结果展示函数
# ============================================================

def _show_backtest_result(result, price_df=None, show_title=True):
    """展示回测结果"""
    if show_title:
        st.markdown("## 📈 回测结果")

    # 核心指标
    st.markdown("#### 核心指标")
    col1, col2, col3, col4, col5, col6 = st.columns(6)

    with col1:
        delta_color = "normal" if result.total_return >= 0 else "inverse"
        st.metric("总收益率", f"{result.total_return:.2f}%",
                  delta=f"{result.total_return:.2f}%", delta_color=delta_color)
    with col2:
        st.metric("年化收益率", f"{result.annualized_return:.2f}%")
    with col3:
        st.metric("最大回撤", f"{result.max_drawdown:.2f}%", delta_color="inverse")
    with col4:
        st.metric("夏普比率", f"{result.sharpe_ratio:.2f}")
    with col5:
        st.metric("胜率", f"{result.win_rate:.1f}%")
    with col6:
        st.metric("总交易次数", f"{result.total_trades}")

    # Plotly 图表
    if result.equity_curve is not None and not result.equity_curve.empty:
        try:
            from apexquant.backtest.plotly_charts import (
                create_equity_curve_chart,
                create_drawdown_chart,
                create_trade_analysis_chart,
                create_monthly_returns_heatmap,
            )

            tab1, tab2, tab3, tab4 = st.tabs(
                ["权益曲线", "回撤分析", "交易分析", "月度收益"]
            )

            with tab1:
                fig = create_equity_curve_chart(
                    result.equity_curve, result.initial_capital,
                    benchmark_df=price_df,
                )
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    _fallback_equity_chart(result.equity_curve)

            with tab2:
                fig = create_drawdown_chart(result.equity_curve)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    _fallback_drawdown_chart(result.equity_curve)

            with tab3:
                if result.trades:
                    fig = create_trade_analysis_chart(result.trades)
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("无法生成交易分析图 (需安装 plotly)")
                else:
                    st.info("无交易记录")

            with tab4:
                fig = create_monthly_returns_heatmap(result.equity_curve)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("数据不足以生成月度热力图")

        except ImportError:
            _fallback_equity_chart(result.equity_curve)

    # 详细指标
    with st.expander("详细指标"):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**收益指标**")
            st.dataframe(pd.DataFrame({
                '指标': ['总收益率', '年化收益率', '最大回撤', '夏普比率', 'Sortino比率', 'Calmar比率'],
                '数值': [f"{result.total_return:.2f}%", f"{result.annualized_return:.2f}%",
                         f"{result.max_drawdown:.2f}%", f"{result.sharpe_ratio:.4f}",
                         f"{result.sortino_ratio:.4f}", f"{result.calmar_ratio:.4f}"],
            }), hide_index=True, use_container_width=True)
        with col2:
            st.markdown("**交易统计**")
            st.dataframe(pd.DataFrame({
                '指标': ['总交易次数', '盈利次数', '亏损次数', '胜率', '盈亏比', '平均持有天数'],
                '数值': [f"{result.total_trades}", f"{result.winning_trades}",
                         f"{result.losing_trades}", f"{result.win_rate:.1f}%",
                         f"{result.profit_loss_ratio:.2f}", f"{result.avg_holding_days:.0f}"],
            }), hide_index=True, use_container_width=True)

    # 交易明细
    if result.trades:
        with st.expander(f"交易明细 ({len(result.trades)} 笔)"):
            trade_df = pd.DataFrame(result.trades)
            display_cols = ['buy_date', 'sell_date', 'buy_price', 'sell_price',
                            'volume', 'pnl', 'return_pct', 'holding_days']
            available_cols = [c for c in display_cols if c in trade_df.columns]
            rename_map = {
                'buy_date': '买入日期', 'sell_date': '卖出日期',
                'buy_price': '买入价', 'sell_price': '卖出价',
                'volume': '数量', 'pnl': '盈亏',
                'return_pct': '收益率(%)', 'holding_days': '持有天数',
            }
            display_df = trade_df[available_cols].rename(columns=rename_map)
            st.dataframe(display_df, hide_index=True, use_container_width=True)


def _fallback_equity_chart(equity_curve):
    """Plotly 不可用时的简单折线图"""
    if equity_curve is not None and 'equity' in equity_curve.columns:
        chart_data = pd.DataFrame({
            '权益': equity_curve['equity'].values
        })
        st.line_chart(chart_data)


def _fallback_drawdown_chart(equity_curve):
    """Plotly 不可用时的简单回撤图"""
    if equity_curve is not None and 'equity' in equity_curve.columns:
        eq = equity_curve['equity'].values
        peak = np.maximum.accumulate(eq)
        dd = (eq - peak) / peak * 100
        chart_data = pd.DataFrame({'回撤(%)': dd})
        st.area_chart(chart_data)


# ============================================================
# 页脚
# ============================================================
st.markdown("---")

with st.expander("📖 使用说明"):
    st.markdown("""
    ### 策略回测功能说明

    **策略回测模式**
    - 均线交叉: 短期均线上穿/下穿长期均线产生交易信号
    - RSI策略: RSI超卖买入、超买卖出
    - 买入持有: 首日买入并持有到期
    - 多因子策略: 基于33个量化因子周期性评分交易
    - 深度学习预测: LSTM/GRU模型预测未来走势

    **参数优化模式**
    - 网格搜索遍历所有参数组合
    - 支持按夏普比率/总收益/胜率/Calmar比率优化
    - 展示参数热力图和Top10排名

    **策略对比模式**
    - 同时运行多个策略在相同数据上回测
    - 权益曲线叠加对比
    - 核心指标横向比较
    """)
