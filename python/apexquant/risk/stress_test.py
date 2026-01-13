"""
压力测试场景生成器
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from apexquant.ai import DeepSeekClient


class StressTestGenerator:
    """压力测试场景生成器"""
    
    def __init__(self, api_key: Optional[str] = None):
        """初始化"""
        try:
            self.client = DeepSeekClient(api_key)
            self.ai_enabled = True
        except:
            self.ai_enabled = False
    
    def generate_scenarios(self, market_condition: str = "normal") -> List[Dict]:
        """
        生成压力测试场景
        
        Args:
            market_condition: 市场状况
        
        Returns:
            场景列表
        """
        scenarios = []
        
        # 1. 市场崩盘场景
        scenarios.append({
            'name': '市场崩盘',
            'description': '市场连续大幅下跌',
            'shock': -0.20,  # -20% 冲击
            'volatility_multiplier': 3.0,
            'duration': 10  # 持续10天
        })
        
        # 2. 流动性危机
        scenarios.append({
            'name': '流动性危机',
            'description': '市场流动性枯竭',
            'shock': -0.15,
            'volatility_multiplier': 4.0,
            'duration': 5,
            'liquidity_impact': 2.0  # 滑点翻倍
        })
        
        # 3. 黑天鹅事件
        scenarios.append({
            'name': '黑天鹅事件',
            'description': '突发极端事件',
            'shock': -0.30,
            'volatility_multiplier': 5.0,
            'duration': 3
        })
        
        # 4. 波动率飙升
        scenarios.append({
            'name': '波动率飙升',
            'description': '市场剧烈震荡',
            'shock': 0.0,
            'volatility_multiplier': 6.0,
            'duration': 20
        })
        
        # 5. 缓慢熊市
        scenarios.append({
            'name': '缓慢熊市',
            'description': '长期温和下跌',
            'shock': -0.05,
            'volatility_multiplier': 1.5,
            'duration': 60
        })
        
        return scenarios
    
    def apply_scenario(self,
                      data: pd.DataFrame,
                      scenario: Dict) -> pd.DataFrame:
        """
        将场景应用到数据
        
        Args:
            data: 原始数据
            scenario: 场景定义
        
        Returns:
            压力测试后的数据
        """
        stressed_data = data.copy()
        
        shock = scenario.get('shock', 0)
        vol_multiplier = scenario.get('volatility_multiplier', 1.0)
        duration = scenario.get('duration', len(data))
        
        # 应用冲击
        if shock != 0:
            for col in ['open', 'high', 'low', 'close']:
                stressed_data[col] = stressed_data[col] * (1 + shock)
        
        # 增加波动率
        if vol_multiplier > 1.0:
            for i in range(1, min(duration, len(stressed_data))):
                noise = np.random.normal(0, 0.02 * vol_multiplier)
                for col in ['open', 'high', 'low', 'close']:
                    stressed_data.loc[i, col] = stressed_data.loc[i, col] * (1 + noise)
        
        # 确保 OHLC 逻辑一致
        for i in range(len(stressed_data)):
            row = stressed_data.iloc[i]
            stressed_data.loc[i, 'high'] = max(row['open'], row['close'], row['high'])
            stressed_data.loc[i, 'low'] = min(row['open'], row['close'], row['low'])
        
        return stressed_data
    
    def run_stress_tests(self,
                        strategy_class,
                        runner,
                        data: pd.DataFrame,
                        params: Dict) -> List[Dict]:
        """
        运行所有压力测试
        
        Args:
            strategy_class: 策略类
            runner: 回测运行器
            data: 数据
            params: 策略参数
        
        Returns:
            测试结果列表
        """
        scenarios = self.generate_scenarios()
        results = []
        
        print(f"运行 {len(scenarios)} 个压力测试场景...")
        
        for scenario in scenarios:
            print(f"\n测试场景: {scenario['name']}")
            
            # 应用场景
            stressed_data = self.apply_scenario(data, scenario)
            
            # 运行回测
            try:
                strategy = strategy_class(**params)
                result = runner.run(strategy, stressed_data)
                
                results.append({
                    'scenario': scenario['name'],
                    'description': scenario['description'],
                    'total_return': result.total_return,
                    'max_drawdown': result.max_drawdown,
                    'sharpe_ratio': result.sharpe_ratio
                })
                
                print(f"  收益: {result.total_return:.2%}")
                print(f"  回撤: {result.max_drawdown:.2%}")
                
            except Exception as e:
                print(f"  失败: {e}")
                results.append({
                    'scenario': scenario['name'],
                    'description': scenario['description'],
                    'error': str(e)
                })
        
        return results
    
    def ai_generate_scenarios(self, market_context: str) -> str:
        """
        使用 AI 生成压力测试场景
        
        Args:
            market_context: 市场背景描述
        
        Returns:
            AI 生成的场景描述
        """
        if not self.ai_enabled:
            return "AI 不可用"
        
        prompt = f"""
当前市场环境：{market_context}

作为风险管理专家，请设计 3-5 个针对性的压力测试场景。

每个场景包含：
1. 场景名称
2. 触发条件/事件
3. 预期市场反应
4. 对策略的潜在影响

要求简洁专业，总字数 400 字内。
"""
        
        messages = [
            {"role": "system", "content": "你是系统性风险专家，擅长设计压力测试场景。"},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = self.client.chat(messages, temperature=0.7, max_tokens=800)
            return response
        except Exception as e:
            return f"AI 生成失败: {e}"

