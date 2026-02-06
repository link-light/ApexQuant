"""
策略管理页面
"""

import streamlit as st
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "python"))

# 页面配置
st.set_page_config(
    page_title="策略管理 - ApexQuant",
    page_icon="🎨",
    layout="wide"
)

st.title("🎨 策略管理")
st.markdown("管理和配置您的交易策略")
st.markdown("---")

# 策略列表
st.markdown("### 📚 内置策略")

strategies = [
    {
        'name': '均线交叉 (MA Cross)',
        'type': '趋势跟踪',
        'description': 'MA5上穿MA20买入，MA5下穿MA20卖出',
        'params': ['短期均线周期', '长期均线周期'],
        'risk': '中',
        '适用': '趋势市场'
    },
    {
        'name': 'RSI策略',
        'type': '震荡指标',
        'description': 'RSI<30超卖买入，RSI>70超买卖出',
        'params': ['RSI周期', '超卖线', '超买线'],
        'risk': '低',
        '适用': '震荡市场'
    },
    {
        'name': '买入持有 (Buy & Hold)',
        'type': '基准策略',
        'description': '开盘买入后一直持有',
        'params': [],
        'risk': '中',
        '适用': '牛市'
    },
    {
        'name': 'AI驱动策略',
        'type': 'AI智能',
        'description': '使用DeepSeek AI进行智能决策',
        'params': ['置信度阈值', '调用频率'],
        'risk': '高',
        '适用': '复杂市场'
    }
]

for strategy in strategies:
    with st.expander(f"📊 {strategy['name']} - {strategy['type']}"):
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown(f"**描述**: {strategy['description']}")
            st.markdown(f"**参数**: {', '.join(strategy['params']) if strategy['params'] else '无'}")
            st.markdown(f"**风险等级**: {strategy['risk']}")
            st.markdown(f"**适用场景**: {strategy['适用']}")
        
        with col2:
            if st.button(f"使用此策略", key=f"use_{strategy['name']}"):
                st.success(f"✅ 已选择 {strategy['name']}")
            
            if st.button(f"查看详情", key=f"detail_{strategy['name']}"):
                st.info(f"📖 {strategy['name']} 详细文档")

st.markdown("---")

# 自定义策略
st.markdown("### ✏️ 自定义策略")

st.markdown("""
您可以编写自己的策略函数。策略函数接收三个参数：
- `controller`: 模拟盘控制器
- `bar`: 当前K线数据
- `account_info`: 账户信息

返回交易信号字典或None。
""")

strategy_code = st.text_area(
    "策略代码",
    value="""def my_strategy(controller, bar, account_info):
    '''自定义策略'''
    symbol = bar['symbol']
    close_price = bar['close']
    
    # 你的策略逻辑
    if 你的买入条件:
        return {
            'action': 'BUY',
            'symbol': symbol,
            'volume': 100,
            'price': None
        }
    elif 你的卖出条件:
        return {
            'action': 'SELL',
            'symbol': symbol,
            'volume': 100,
            'price': None
        }
    
    return None
""",
    height=300
)

col1, col2 = st.columns(2)

with col1:
    if st.button("💾 保存策略", use_container_width=True):
        st.success("✅ 策略已保存")

with col2:
    if st.button("🧪 测试策略", use_container_width=True):
        st.info("🔄 正在测试策略...")

st.markdown("---")

# 策略库
st.markdown("### 📦 策略库")

st.markdown("""
更多策略正在开发中...

**即将推出**:
- MACD策略
- 布林带策略
- 网格交易策略
- 机器学习策略
- 多因子策略
""")

