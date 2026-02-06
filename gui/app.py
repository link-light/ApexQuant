#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ApexQuant GUI 主应用
基于 Streamlit 构建的量化交易系统控制面板
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "python"))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import logging

# 页面配置
st.set_page_config(
    page_title="ApexQuant - 量化交易系统",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        padding: 1rem 0;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .success-text {
        color: #00ff00;
        font-weight: bold;
    }
    .error-text {
        color: #ff0000;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# 标题
st.markdown('<h1 class="main-header">📈 ApexQuant 量化交易系统</h1>', unsafe_allow_html=True)
st.markdown("---")

# 导入页面模块
from pages import (
    backtest_page,
    realtime_page,
    strategy_page,
    performance_page,
    config_page
)

def main():
    """主函数"""
    
    # 侧边栏导航
    st.sidebar.title("🎯 导航")
    page = st.sidebar.radio(
        "选择功能模块",
        [
            "🏠 首页",
            "📊 策略回测",
            "⚡ 实时模拟",
            "🎨 策略管理",
            "📈 性能分析",
            "⚙️ 系统配置"
        ]
    )
    
    # 侧边栏信息
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📋 系统信息")
    st.sidebar.info(f"""
    **版本**: v1.0.0  
    **状态**: 🟢 运行中  
    **时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    """)
    
    # 路由到不同页面
    if page == "🏠 首页":
        show_home_page()
    elif page == "📊 策略回测":
        backtest_page.show()
    elif page == "⚡ 实时模拟":
        realtime_page.show()
    elif page == "🎨 策略管理":
        strategy_page.show()
    elif page == "📈 性能分析":
        performance_page.show()
    elif page == "⚙️ 系统配置":
        config_page.show()


def show_home_page():
    """显示首页"""
    
    # 欢迎信息
    st.markdown("""
    ## 👋 欢迎使用 ApexQuant
    
    ApexQuant 是一个功能强大的量化交易系统，提供完整的策略开发、回测和实盘交易功能。
    """)
    
    # 功能卡片
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <h3>📊 策略回测</h3>
            <p>使用历史数据测试您的交易策略，评估性能表现</p>
            <ul>
                <li>多种内置策略</li>
                <li>自定义策略支持</li>
                <li>详细的性能指标</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
            <h3>⚡ 实时模拟</h3>
            <p>模拟实时交易环境，验证策略的实战能力</p>
            <ul>
                <li>实时行情接入</li>
                <li>完整风控系统</li>
                <li>性能实时监控</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-card">
            <h3>📈 性能分析</h3>
            <p>全面的性能分析和可视化工具</p>
            <ul>
                <li>20+ 核心指标</li>
                <li>交互式图表</li>
                <li>详细交易记录</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 快速开始
    st.markdown("## 🚀 快速开始")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### 新手指南
        
        1. **配置系统** - 前往"系统配置"设置API密钥和参数
        2. **选择策略** - 在"策略管理"中选择或创建策略
        3. **运行回测** - 在"策略回测"中测试策略表现
        4. **查看结果** - 在"性能分析"中查看详细报告
        """)
    
    with col2:
        st.markdown("""
        ### 内置策略
        
        - **均线交叉** (MA Cross) - 经典趋势策略
        - **RSI策略** - 震荡指标策略
        - **买入持有** (Buy & Hold) - 基准策略
        - **AI驱动** - DeepSeek AI 智能决策
        """)
    
    st.markdown("---")
    
    # 系统状态
    st.markdown("## 📊 系统状态")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("策略数量", "4", delta="+0")
    
    with col2:
        st.metric("回测次数", "0", delta="今日")
    
    with col3:
        st.metric("实时交易", "0", delta="活跃")
    
    with col4:
        st.metric("系统状态", "正常", delta=None)
    
    st.markdown("---")
    
    # 最近活动
    st.markdown("## 📝 最近活动")
    
    activities = pd.DataFrame({
        '时间': [datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
        '类型': ['系统启动'],
        '描述': ['GUI界面已启动'],
        '状态': ['✅ 成功']
    })
    
    st.dataframe(activities, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    # 帮助信息
    with st.expander("❓ 帮助与支持"):
        st.markdown("""
        ### 常见问题
        
        **Q: 如何配置API密钥？**  
        A: 前往"系统配置"页面，按照提示配置环境变量。
        
        **Q: 如何运行回测？**  
        A: 前往"策略回测"页面，选择策略和参数后点击"开始回测"。
        
        **Q: 数据从哪里来？**  
        A: 系统支持Baostock和AKShare两个数据源，自动切换。
        
        ### 文档链接
        
        - [快速启动指南](../快速启动指南.md)
        - [策略开发文档](../项目功能说明.md)
        - [API参考文档](../README.md)
        
        ### 问题反馈
        
        如遇到问题，请查看日志文件或联系技术支持。
        """)


if __name__ == "__main__":
    main()

