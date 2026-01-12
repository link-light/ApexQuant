"""
AI 因子生成器
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from apexquant.ai import DeepSeekClient


class AIFactorGenerator:
    """AI 驱动的因子生成器"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化
        
        Args:
            api_key: DeepSeek API key
        """
        try:
            self.client = DeepSeekClient(api_key)
            self.ai_enabled = True
        except:
            self.ai_enabled = False
            print("AI 未启用")
    
    def generate_factor_code(self, description: str) -> str:
        """
        根据描述生成因子代码
        
        Args:
            description: 因子描述，如"计算最近5日涨跌幅的标准差"
        
        Returns:
            Python 代码字符串
        """
        if not self.ai_enabled:
            return "# AI 未启用"
        
        prompt = f"""
你是一个量化因子工程师。请根据以下描述生成 Python 函数来计算因子。

因子描述：{description}

要求：
1. 函数名为 calculate_factor
2. 输入参数为 df (pandas DataFrame)，包含 open, high, low, close, volume 列
3. 返回一个 pandas Series，索引与 df 相同
4. 只使用 pandas 和 numpy
5. 处理缺失值和边界情况
6. 添加简洁注释

示例格式：
```python
def calculate_factor(df):
    \"\"\"因子说明\"\"\"
    # 计算逻辑
    factor = ...
    return factor
```

请只返回代码，不要额外说明。
"""
        
        messages = [
            {"role": "system", "content": "你是一个专业的量化因子工程师。"},
            {"role": "user", "content": prompt}
        ]
        
        response = self.client.chat(messages, temperature=0.3, max_tokens=500)
        
        # 提取代码
        if "```python" in response:
            code = response.split("```python")[1].split("```")[0].strip()
        elif "```" in response:
            code = response.split("```")[1].split("```")[0].strip()
        else:
            code = response.strip()
        
        return code
    
    def evaluate_factor(self, factor_series: pd.Series, 
                       returns: pd.Series) -> Dict:
        """
        评估因子质量
        
        Args:
            factor_series: 因子值
            returns: 未来收益率
        
        Returns:
            评估指标字典
        """
        # 对齐数据
        factor = factor_series.dropna()
        ret = returns.loc[factor.index]
        
        # 去除无效值
        valid_mask = ~np.isnan(factor) & ~np.isnan(ret) & ~np.isinf(factor) & ~np.isinf(ret)
        factor = factor[valid_mask]
        ret = ret[valid_mask]
        
        if len(factor) < 10:
            return {'ic': 0.0, 'rank_ic': 0.0, 'error': 'insufficient_data'}
        
        # IC (信息系数)
        ic = factor.corr(ret)
        
        # Rank IC
        rank_ic = factor.rank().corr(ret.rank())
        
        # 因子分组回报
        try:
            factor_quantiles = pd.qcut(factor, 5, labels=False, duplicates='drop')
            group_returns = ret.groupby(factor_quantiles).mean()
            
            # 多空组合收益
            if len(group_returns) >= 2:
                long_short_return = group_returns.iloc[-1] - group_returns.iloc[0]
            else:
                long_short_return = 0.0
        except:
            long_short_return = 0.0
        
        return {
            'ic': float(ic) if not np.isnan(ic) else 0.0,
            'rank_ic': float(rank_ic) if not np.isnan(rank_ic) else 0.0,
            'long_short_return': float(long_short_return),
            'sample_size': len(factor)
        }
    
    def suggest_factors(self, df: pd.DataFrame, 
                       market_condition: str = "normal") -> List[str]:
        """
        AI 推荐因子
        
        Args:
            df: 数据
            market_condition: 市场状况 'bull', 'bear', 'normal', 'volatile'
        
        Returns:
            因子描述列表
        """
        if not self.ai_enabled:
            return []
        
        # 分析数据特征
        volatility = df['close'].pct_change().std()
        trend = (df['close'].iloc[-1] / df['close'].iloc[0] - 1)
        
        prompt = f"""
作为量化策略专家，请针对以下市场环境推荐 3-5 个有效的技术因子。

市场环境：{market_condition}
近期波动率：{volatility:.2%}
近期趋势：{trend:.2%}

要求：
1. 每个因子用一句话描述
2. 因子应该适合当前市场环境
3. 包含不同维度（趋势、动量、波动、成交量等）
4. 可计算且有实际意义

格式：
1. 因子描述1
2. 因子描述2
...

只返回因子列表，不要额外解释。
"""
        
        messages = [
            {"role": "system", "content": "你是一个量化因子专家。"},
            {"role": "user", "content": prompt}
        ]
        
        response = self.client.chat(messages, temperature=0.7, max_tokens=400)
        
        # 解析因子列表
        factors = []
        for line in response.split('\n'):
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('-') or line.startswith('•')):
                # 去除序号
                factor_desc = line.split('.', 1)[-1].strip()
                if factor_desc:
                    factors.append(factor_desc)
        
        return factors[:5]  # 最多返回 5 个

