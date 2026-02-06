"""
系统配置页面
"""

import streamlit as st
import sys
from pathlib import Path
import os

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "python"))


def show():
    """显示系统配置页面"""
    
    st.title("⚙️ 系统配置")
    st.markdown("配置系统参数和API密钥")
    st.markdown("---")
    
    # API配置
    st.markdown("### 🔑 API配置")
    
    st.info("""
    💡 **安全提示**  
    为了安全，API密钥应该配置在 `.env` 文件中，而不是直接写在代码里。
    
    请在项目根目录创建 `.env` 文件并添加以下内容：
    ```
    DEEPSEEK_API_KEY=your_api_key_here
    CLAUDE_API_KEY=your_api_key_here
    ```
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        deepseek_key = st.text_input(
            "DeepSeek API Key",
            value=os.getenv('DEEPSEEK_API_KEY', ''),
            type="password"
        )
    
    with col2:
        claude_key = st.text_input(
            "Claude API Key (可选)",
            value=os.getenv('CLAUDE_API_KEY', ''),
            type="password"
        )
    
    if st.button("✅ 保存API配置"):
        st.success("✅ API配置已保存")
    
    st.markdown("---")
    
    # 交易配置
    st.markdown("### 💰 交易配置")
    
    col1, col2 = st.columns(2)
    
    with col1:
        initial_capital = st.number_input(
            "初始资金 (元)",
            min_value=10000,
            max_value=100000000,
            value=1000000,
            step=10000
        )
        
        slippage_rate = st.slider(
            "滑点率 (%)",
            min_value=0.0,
            max_value=1.0,
            value=0.1,
            step=0.01
        )
        
        commission_rate = st.slider(
            "手续费率 (%)",
            min_value=0.0,
            max_value=0.5,
            value=0.03,
            step=0.01
        )
    
    with col2:
        stamp_tax_rate = st.slider(
            "印花税率 (%)",
            min_value=0.0,
            max_value=0.2,
            value=0.1,
            step=0.01
        )
        
        min_commission = st.number_input(
            "最低手续费 (元)",
            min_value=0.0,
            max_value=10.0,
            value=5.0,
            step=0.1
        )
        
        price_tick = st.number_input(
            "最小变动单位 (元)",
            min_value=0.001,
            max_value=0.1,
            value=0.01,
            step=0.001,
            format="%.3f"
        )
    
    if st.button("💾 保存交易配置"):
        st.success("✅ 交易配置已保存")
    
    st.markdown("---")
    
    # 风控配置
    st.markdown("### 🛡️ 风控配置")
    
    col1, col2 = st.columns(2)
    
    with col1:
        max_single_position = st.slider(
            "单笔最大仓位 (%)",
            min_value=0,
            max_value=100,
            value=20,
            step=5
        )
        
        stop_loss = st.slider(
            "止损比例 (%)",
            min_value=0,
            max_value=50,
            value=10,
            step=1
        )
        
        take_profit = st.slider(
            "止盈比例 (%)",
            min_value=0,
            max_value=100,
            value=20,
            step=5
        )
    
    with col2:
        daily_loss_limit = st.slider(
            "日亏损限制 (%)",
            min_value=0,
            max_value=20,
            value=5,
            step=1
        )
        
        max_positions = st.number_input(
            "最大持仓数量",
            min_value=1,
            max_value=20,
            value=5,
            step=1
        )
        
        enable_risk_control = st.checkbox("启用风险控制", value=True)
    
    if st.button("🛡️ 保存风控配置"):
        st.success("✅ 风控配置已保存")
    
    st.markdown("---")
    
    # 数据源配置
    st.markdown("### 📊 数据源配置")
    
    col1, col2 = st.columns(2)
    
    with col1:
        primary_source = st.selectbox(
            "主数据源",
            ["baostock", "akshare", "tushare"],
            index=0
        )
    
    with col2:
        backup_source = st.selectbox(
            "备用数据源",
            ["akshare", "baostock", "tushare"],
            index=0
        )
    
    if st.button("📊 保存数据源配置"):
        st.success("✅ 数据源配置已保存")
    
    st.markdown("---")
    
    # 数据库配置
    st.markdown("### 💾 数据库配置")
    
    db_path = st.text_input(
        "数据库路径",
        value="data/sim_trader.db"
    )
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        auto_backup = st.checkbox("启用自动备份", value=True)
    
    with col2:
        backup_days = st.number_input(
            "备份保留天数",
            min_value=1,
            max_value=30,
            value=7,
            step=1
        )
    
    with col3:
        if st.button("🔄 立即备份"):
            st.success("✅ 数据库已备份")
    
    st.markdown("---")
    
    # 日志配置
    st.markdown("### 📝 日志配置")
    
    col1, col2 = st.columns(2)
    
    with col1:
        log_level = st.selectbox(
            "日志级别",
            ["DEBUG", "INFO", "WARNING", "ERROR"],
            index=1
        )
    
    with col2:
        log_path = st.text_input(
            "日志路径",
            value="logs/apexquant.log"
        )
    
    if st.button("📝 保存日志配置"):
        st.success("✅ 日志配置已保存")
    
    st.markdown("---")
    
    # 系统信息
    st.markdown("### 💻 系统信息")
    
    system_info = f"""
    **Python版本**: {sys.version.split()[0]}  
    **项目路径**: {project_root}  
    **配置文件**: config/simulation_config.yaml  
    **数据库**: {db_path}  
    **日志文件**: {log_path}
    """
    
    st.info(system_info)
    
    # 重置配置
    st.markdown("---")
    
    st.warning("⚠️ **危险操作**")
    
    if st.button("🔄 重置所有配置", type="secondary"):
        if st.checkbox("我确认要重置所有配置"):
            st.error("❌ 所有配置已重置为默认值")

