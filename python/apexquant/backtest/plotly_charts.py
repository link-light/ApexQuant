"""
Plotly 回测可视化图表

生成交互式图表用于 Streamlit 展示。
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional

try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False


def create_equity_curve_chart(equity_curve: pd.DataFrame,
                               initial_capital: float = 1000000,
                               benchmark_df: Optional[pd.DataFrame] = None,
                               title: str = "权益曲线") -> "go.Figure":
    """
    创建权益曲线图

    Args:
        equity_curve: DataFrame，含 date, equity 列
        initial_capital: 初始资金
        benchmark_df: 基准数据 (可选), 含 date, close 列
        title: 图表标题
    """
    if not PLOTLY_AVAILABLE:
        return None

    fig = go.Figure()

    dates = equity_curve['date'] if 'date' in equity_curve.columns else equity_curve.index

    # 权益曲线
    fig.add_trace(go.Scatter(
        x=dates,
        y=equity_curve['equity'],
        name='策略权益',
        line=dict(color='#2196F3', width=2),
        fill='tozeroy',
        fillcolor='rgba(33, 150, 243, 0.1)',
    ))

    # 初始资金线
    fig.add_hline(
        y=initial_capital,
        line_dash="dash",
        line_color="gray",
        annotation_text=f"初始资金: {initial_capital:,.0f}",
    )

    # 基准收益曲线
    if benchmark_df is not None and not benchmark_df.empty:
        bench_dates = benchmark_df['date'] if 'date' in benchmark_df.columns else benchmark_df.index
        bench_close = benchmark_df['close'].values
        bench_equity = initial_capital * bench_close / bench_close[0]

        fig.add_trace(go.Scatter(
            x=bench_dates,
            y=bench_equity,
            name='基准 (买入持有)',
            line=dict(color='#FF9800', width=1.5, dash='dot'),
        ))

    fig.update_layout(
        title=title,
        xaxis_title='日期',
        yaxis_title='权益 (元)',
        template='plotly_white',
        hovermode='x unified',
        height=400,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )

    return fig


def create_drawdown_chart(equity_curve: pd.DataFrame,
                           title: str = "回撤分析") -> "go.Figure":
    """创建回撤分析图"""
    if not PLOTLY_AVAILABLE:
        return None

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        row_heights=[0.6, 0.4],
        subplot_titles=("权益曲线与峰值", "回撤曲线"),
    )

    dates = equity_curve['date'] if 'date' in equity_curve.columns else equity_curve.index
    equity = equity_curve['equity'].values
    peak = np.maximum.accumulate(equity)
    drawdown = (equity - peak) / peak * 100

    # 上方: 权益与峰值
    fig.add_trace(go.Scatter(
        x=dates, y=equity, name='权益',
        line=dict(color='#2196F3', width=2),
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=dates, y=peak, name='峰值',
        line=dict(color='#4CAF50', width=1, dash='dash'),
    ), row=1, col=1)

    # 下方: 回撤
    fig.add_trace(go.Scatter(
        x=dates, y=drawdown, name='回撤',
        fill='tozeroy',
        fillcolor='rgba(244, 67, 54, 0.3)',
        line=dict(color='#F44336', width=1),
    ), row=2, col=1)

    # 标注最大回撤点
    max_dd_idx = np.argmin(drawdown)
    fig.add_annotation(
        x=dates.iloc[max_dd_idx] if hasattr(dates, 'iloc') else dates[max_dd_idx],
        y=drawdown[max_dd_idx],
        text=f"最大回撤: {drawdown[max_dd_idx]:.2f}%",
        showarrow=True,
        arrowhead=2,
        font=dict(color='red'),
        row=2, col=1,
    )

    fig.update_layout(
        title=title,
        template='plotly_white',
        hovermode='x unified',
        height=500,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    fig.update_yaxes(title_text="权益 (元)", row=1, col=1)
    fig.update_yaxes(title_text="回撤 (%)", row=2, col=1)

    return fig


def create_trade_analysis_chart(trades: List[Dict],
                                 title: str = "交易分析") -> "go.Figure":
    """创建交易分析图"""
    if not PLOTLY_AVAILABLE or not trades:
        return None

    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=("单笔盈亏", "累计盈亏", "盈亏分布", "盈亏占比"),
        specs=[[{"type": "bar"}, {"type": "scatter"}],
               [{"type": "histogram"}, {"type": "pie"}]],
    )

    pnl_list = [t.get('pnl', 0) for t in trades]
    colors = ['#4CAF50' if p > 0 else '#F44336' for p in pnl_list]

    # 1. 单笔盈亏条形图
    fig.add_trace(go.Bar(
        x=list(range(1, len(pnl_list) + 1)),
        y=pnl_list,
        marker_color=colors,
        name='单笔盈亏',
        showlegend=False,
    ), row=1, col=1)

    # 2. 累计盈亏
    cum_pnl = np.cumsum(pnl_list)
    fig.add_trace(go.Scatter(
        x=list(range(1, len(cum_pnl) + 1)),
        y=cum_pnl,
        line=dict(color='#2196F3', width=2),
        name='累计盈亏',
        showlegend=False,
    ), row=1, col=2)
    fig.add_hline(y=0, line_dash="dash", line_color="gray", row=1, col=2)

    # 3. 盈亏分布直方图
    fig.add_trace(go.Histogram(
        x=pnl_list,
        nbinsx=20,
        marker_color='#2196F3',
        name='分布',
        showlegend=False,
    ), row=2, col=1)

    # 4. 胜率饼图
    wins = sum(1 for p in pnl_list if p > 0)
    losses = sum(1 for p in pnl_list if p < 0)
    even = sum(1 for p in pnl_list if p == 0)

    labels, values, pie_colors = [], [], []
    if wins > 0:
        labels.append(f'盈利 ({wins})')
        values.append(wins)
        pie_colors.append('#4CAF50')
    if losses > 0:
        labels.append(f'亏损 ({losses})')
        values.append(losses)
        pie_colors.append('#F44336')
    if even > 0:
        labels.append(f'持平 ({even})')
        values.append(even)
        pie_colors.append('#9E9E9E')

    if values:
        fig.add_trace(go.Pie(
            labels=labels,
            values=values,
            marker_colors=pie_colors,
            hole=0.4,
            showlegend=False,
        ), row=2, col=2)

    fig.update_layout(
        title=title,
        template='plotly_white',
        height=600,
    )

    return fig


def create_monthly_returns_heatmap(equity_curve: pd.DataFrame,
                                    title: str = "月度收益热力图") -> "go.Figure":
    """创建月度收益热力图"""
    if not PLOTLY_AVAILABLE:
        return None

    df = equity_curve.copy()
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date')

    daily_returns = df['equity'].pct_change()
    monthly = daily_returns.resample('ME').apply(lambda x: (1 + x).prod() - 1)

    if monthly.empty:
        return None

    mdf = monthly.to_frame(name='return')
    mdf['year'] = mdf.index.year
    mdf['month'] = mdf.index.month

    pivot = mdf.pivot_table(values='return', index='year', columns='month', aggfunc='first')

    month_labels = ['1月', '2月', '3月', '4月', '5月', '6月',
                    '7月', '8月', '9月', '10月', '11月', '12月']

    # 确保有12列
    for m in range(1, 13):
        if m not in pivot.columns:
            pivot[m] = np.nan
    pivot = pivot.reindex(columns=range(1, 13))

    z_vals = pivot.values * 100  # 转百分比
    text_vals = [[f"{v:.1f}%" if not np.isnan(v) else "" for v in row] for row in z_vals]

    fig = go.Figure(data=go.Heatmap(
        z=z_vals,
        x=month_labels,
        y=[str(y) for y in pivot.index],
        text=text_vals,
        texttemplate="%{text}",
        colorscale='RdYlGn',
        zmid=0,
        colorbar=dict(title="收益率(%)"),
    ))

    fig.update_layout(
        title=title,
        template='plotly_white',
        height=max(250, len(pivot) * 50 + 100),
        xaxis_title='月份',
        yaxis_title='年份',
    )

    return fig


def create_optimization_chart(results: List[Dict],
                               param_names: List[str],
                               objective: str = 'sharpe_ratio',
                               title: str = "参数优化结果") -> "go.Figure":
    """
    创建参数优化结果可视化

    Args:
        results: 优化结果列表
        param_names: 参数名称
        objective: 优化目标
        title: 标题
    """
    if not PLOTLY_AVAILABLE or not results:
        return None

    valid = [r for r in results if 'error' not in r and r.get('score', -np.inf) > -np.inf]
    if not valid:
        return None

    scores = [r['score'] for r in valid]

    if len(param_names) == 1:
        # 一维参数: 线图
        param = param_names[0]
        x_vals = [r['params'][param] for r in valid]
        sorted_data = sorted(zip(x_vals, scores))
        x_sorted = [d[0] for d in sorted_data]
        y_sorted = [d[1] for d in sorted_data]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=x_sorted, y=y_sorted,
            mode='lines+markers',
            line=dict(color='#2196F3', width=2),
            marker=dict(size=8),
        ))
        fig.update_layout(
            xaxis_title=param,
            yaxis_title=objective,
        )

    elif len(param_names) == 2:
        # 二维参数: 热力图
        p1, p2 = param_names[0], param_names[1]
        x_vals = sorted(set(r['params'][p1] for r in valid))
        y_vals = sorted(set(r['params'][p2] for r in valid))

        z = np.full((len(y_vals), len(x_vals)), np.nan)
        for r in valid:
            xi = x_vals.index(r['params'][p1])
            yi = y_vals.index(r['params'][p2])
            z[yi][xi] = r['score']

        fig = go.Figure(data=go.Heatmap(
            z=z,
            x=[str(v) for v in x_vals],
            y=[str(v) for v in y_vals],
            colorscale='Viridis',
            colorbar=dict(title=objective),
        ))
        fig.update_layout(
            xaxis_title=p1,
            yaxis_title=p2,
        )
    else:
        # 多维参数: 排名条形图 (前20)
        sorted_valid = sorted(valid, key=lambda x: x['score'], reverse=True)[:20]
        labels = [str(r['params']) for r in sorted_valid]
        values = [r['score'] for r in sorted_valid]

        fig = go.Figure(data=go.Bar(
            x=values,
            y=labels,
            orientation='h',
            marker_color='#2196F3',
        ))
        fig.update_layout(
            xaxis_title=objective,
            yaxis_title='参数组合',
            height=max(400, len(labels) * 30),
        )

    fig.update_layout(
        title=title,
        template='plotly_white',
    )

    return fig


def create_strategy_comparison_chart(results: Dict[str, "BacktestResult"],
                                      title: str = "策略对比") -> "go.Figure":
    """
    创建多策略对比图

    Args:
        results: {策略名: BacktestResult} 字典
    """
    if not PLOTLY_AVAILABLE or not results:
        return None

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=("权益曲线对比", "关键指标对比"),
        column_widths=[0.6, 0.4],
    )

    colors = ['#2196F3', '#F44336', '#4CAF50', '#FF9800', '#9C27B0', '#00BCD4']

    # 左图: 权益曲线对比
    for i, (name, result) in enumerate(results.items()):
        if result.equity_curve is not None and not result.equity_curve.empty:
            ec = result.equity_curve
            dates = ec['date'] if 'date' in ec.columns else ec.index
            fig.add_trace(go.Scatter(
                x=dates,
                y=ec['equity'],
                name=name,
                line=dict(color=colors[i % len(colors)], width=2),
            ), row=1, col=1)

    # 右图: 指标雷达图替代为分组条形图
    metrics = ['total_return', 'sharpe_ratio', 'max_drawdown', 'win_rate']
    metric_labels = ['总收益(%)', '夏普比率', '最大回撤(%)', '胜率(%)']

    for i, (name, result) in enumerate(results.items()):
        vals = [
            result.total_return,
            result.sharpe_ratio,
            result.max_drawdown,
            result.win_rate,
        ]
        fig.add_trace(go.Bar(
            x=metric_labels,
            y=vals,
            name=name,
            marker_color=colors[i % len(colors)],
            showlegend=False,
        ), row=1, col=2)

    fig.update_layout(
        title=title,
        template='plotly_white',
        height=450,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        barmode='group',
    )

    return fig
