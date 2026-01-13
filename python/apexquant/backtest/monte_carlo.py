"""
蒙特卡洛模拟
"""

import pandas as pd
import numpy as np
from typing import Dict, List
import matplotlib.pyplot as plt


class MonteCarloSimulator:
    """蒙特卡洛模拟器"""
    
    def __init__(self, n_simulations: int = 1000, n_days: int = 252):
        """
        初始化
        
        Args:
            n_simulations: 模拟次数
            n_days: 模拟天数
        """
        self.n_simulations = n_simulations
        self.n_days = n_days
        self.simulated_paths = []
    
    def simulate_from_returns(self, 
                             daily_returns: List[float],
                             initial_value: float = 1000000.0) -> np.ndarray:
        """
        基于历史收益率模拟
        
        Args:
            daily_returns: 历史日收益率
            initial_value: 初始资金
        
        Returns:
            模拟路径 (n_simulations, n_days)
        """
        returns = np.array(daily_returns)
        mean_return = np.mean(returns)
        std_return = np.std(returns)
        
        # 生成随机收益率
        random_returns = np.random.normal(
            mean_return, 
            std_return, 
            (self.n_simulations, self.n_days)
        )
        
        # 计算累积收益
        cumulative_returns = np.cumprod(1 + random_returns, axis=1)
        simulated_paths = initial_value * cumulative_returns
        
        self.simulated_paths = simulated_paths
        
        return simulated_paths
    
    def simulate_from_strategy(self,
                               strategy_class,
                               runner,
                               data: pd.DataFrame,
                               params: Dict,
                               noise_level: float = 0.1) -> List[Dict]:
        """
        策略扰动模拟
        
        Args:
            strategy_class: 策略类
            runner: 回测运行器
            data: 数据
            params: 策略参数
            noise_level: 噪声水平
        
        Returns:
            模拟结果列表
        """
        results = []
        
        print(f"蒙特卡洛模拟：{self.n_simulations} 次")
        
        for i in range(self.n_simulations):
            # 添加价格噪声
            noisy_data = data.copy()
            noise = np.random.normal(0, noise_level, len(data))
            
            for col in ['open', 'high', 'low', 'close']:
                noisy_data[col] = noisy_data[col] * (1 + noise)
            
            # 运行回测
            try:
                strategy = strategy_class(**params)
                result = runner.run(strategy, noisy_data)
                
                results.append({
                    'simulation': i + 1,
                    'total_return': result.total_return,
                    'sharpe_ratio': result.sharpe_ratio,
                    'max_drawdown': result.max_drawdown,
                    'win_rate': result.win_rate
                })
            except:
                pass
            
            if (i + 1) % 100 == 0:
                print(f"  完成 {i+1}/{self.n_simulations}")
        
        return results
    
    def analyze_results(self, simulated_paths: np.ndarray = None) -> Dict:
        """
        分析模拟结果
        
        Args:
            simulated_paths: 模拟路径（可选）
        
        Returns:
            统计结果
        """
        if simulated_paths is None:
            simulated_paths = self.simulated_paths
        
        if len(simulated_paths) == 0:
            return {}
        
        final_values = simulated_paths[:, -1]
        
        analysis = {
            'mean_final_value': np.mean(final_values),
            'median_final_value': np.median(final_values),
            'std_final_value': np.std(final_values),
            'min_final_value': np.min(final_values),
            'max_final_value': np.max(final_values),
            'percentile_5': np.percentile(final_values, 5),
            'percentile_25': np.percentile(final_values, 25),
            'percentile_75': np.percentile(final_values, 75),
            'percentile_95': np.percentile(final_values, 95),
            'probability_loss': np.mean(final_values < simulated_paths[0, 0]),
        }
        
        return analysis
    
    def plot_paths(self, 
                   n_paths: int = 100,
                   save_path: str = None):
        """
        绘制模拟路径
        
        Args:
            n_paths: 绘制路径数
            save_path: 保存路径
        """
        if len(self.simulated_paths) == 0:
            print("没有模拟数据")
            return
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # 绘制部分路径
        sample_indices = np.random.choice(
            len(self.simulated_paths), 
            min(n_paths, len(self.simulated_paths)),
            replace=False
        )
        
        for idx in sample_indices:
            ax.plot(self.simulated_paths[idx], alpha=0.1, color='blue')
        
        # 绘制均值和分位数
        mean_path = np.mean(self.simulated_paths, axis=0)
        percentile_5 = np.percentile(self.simulated_paths, 5, axis=0)
        percentile_95 = np.percentile(self.simulated_paths, 95, axis=0)
        
        ax.plot(mean_path, color='red', linewidth=2, label='均值')
        ax.plot(percentile_5, color='orange', linestyle='--', label='5% 分位数')
        ax.plot(percentile_95, color='green', linestyle='--', label='95% 分位数')
        
        ax.set_title('蒙特卡洛模拟 - 权益曲线', fontsize=14)
        ax.set_xlabel('交易日')
        ax.set_ylabel('资产价值')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            fig.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"图表已保存: {save_path}")
        
        return fig

