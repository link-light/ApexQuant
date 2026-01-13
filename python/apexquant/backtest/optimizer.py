"""
策略参数优化器
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any, Callable
from itertools import product
import concurrent.futures
from tqdm import tqdm


class ParameterOptimizer:
    """参数优化器"""
    
    def __init__(self, objective: str = 'sharpe_ratio'):
        """
        初始化
        
        Args:
            objective: 优化目标 'sharpe_ratio', 'total_return', 'calmar_ratio'
        """
        self.objective = objective
        self.best_params = None
        self.best_score = -np.inf
        self.results = []
    
    def grid_search(self, 
                   strategy_class,
                   param_grid: Dict[str, List],
                   runner,
                   data: pd.DataFrame,
                   n_jobs: int = 4) -> Dict:
        """
        网格搜索
        
        Args:
            strategy_class: 策略类
            param_grid: 参数网格 {'param_name': [val1, val2, ...]}
            runner: BacktestRunner
            data: 数据
            n_jobs: 并行任务数
        
        Returns:
            最佳参数和结果
        """
        # 生成所有参数组合
        param_names = list(param_grid.keys())
        param_values = list(param_grid.values())
        param_combinations = list(product(*param_values))
        
        print(f"网格搜索：{len(param_combinations)} 个参数组合")
        
        # 并行回测
        def run_single(params_tuple):
            params = dict(zip(param_names, params_tuple))
            try:
                strategy = strategy_class(**params)
                result = runner.run(strategy, data)
                
                score = self._get_score(result)
                
                return {
                    'params': params,
                    'score': score,
                    'result': result
                }
            except Exception as e:
                return {
                    'params': params,
                    'score': -np.inf,
                    'error': str(e)
                }
        
        # 执行并行回测
        with concurrent.futures.ProcessPoolExecutor(max_workers=n_jobs) as executor:
            results = list(tqdm(
                executor.map(run_single, param_combinations),
                total=len(param_combinations),
                desc="优化中"
            ))
        
        # 找出最佳参数
        self.results = results
        valid_results = [r for r in results if 'error' not in r]
        
        if valid_results:
            best = max(valid_results, key=lambda x: x['score'])
            self.best_params = best['params']
            self.best_score = best['score']
            
            return {
                'best_params': self.best_params,
                'best_score': self.best_score,
                'all_results': self.results
            }
        else:
            return {
                'best_params': None,
                'best_score': -np.inf,
                'all_results': self.results
            }
    
    def random_search(self,
                     strategy_class,
                     param_distributions: Dict[str, Callable],
                     runner,
                     data: pd.DataFrame,
                     n_iter: int = 50,
                     n_jobs: int = 4) -> Dict:
        """
        随机搜索
        
        Args:
            strategy_class: 策略类
            param_distributions: 参数分布 {'param': lambda: random_value()}
            runner: BacktestRunner
            data: 数据
            n_iter: 迭代次数
            n_jobs: 并行任务数
        
        Returns:
            最佳参数和结果
        """
        print(f"随机搜索：{n_iter} 次迭代")
        
        # 生成随机参数
        param_samples = []
        for _ in range(n_iter):
            params = {name: dist() for name, dist in param_distributions.items()}
            param_samples.append(params)
        
        # 并行回测
        def run_single(params):
            try:
                strategy = strategy_class(**params)
                result = runner.run(strategy, data)
                score = self._get_score(result)
                
                return {
                    'params': params,
                    'score': score,
                    'result': result
                }
            except Exception as e:
                return {
                    'params': params,
                    'score': -np.inf,
                    'error': str(e)
                }
        
        # 执行
        with concurrent.futures.ProcessPoolExecutor(max_workers=n_jobs) as executor:
            results = list(tqdm(
                executor.map(run_single, param_samples),
                total=n_iter,
                desc="优化中"
            ))
        
        # 找出最佳
        self.results = results
        valid_results = [r for r in results if 'error' not in r]
        
        if valid_results:
            best = max(valid_results, key=lambda x: x['score'])
            self.best_params = best['params']
            self.best_score = best['score']
            
            return {
                'best_params': self.best_params,
                'best_score': self.best_score,
                'all_results': self.results
            }
        else:
            return None
    
    def genetic_algorithm(self,
                         strategy_class,
                         param_bounds: Dict[str, Tuple[Any, Any]],
                         runner,
                         data: pd.DataFrame,
                         population_size: int = 20,
                         generations: int = 10,
                         mutation_rate: float = 0.2) -> Dict:
        """
        遗传算法优化
        
        Args:
            strategy_class: 策略类
            param_bounds: 参数范围 {'param': (min, max)}
            runner: BacktestRunner
            data: 数据
            population_size: 种群大小
            generations: 代数
            mutation_rate: 变异率
        
        Returns:
            最佳参数
        """
        print(f"遗传算法：{generations} 代，种群 {population_size}")
        
        param_names = list(param_bounds.keys())
        
        # 初始化种群
        def random_individual():
            return {
                name: np.random.uniform(bounds[0], bounds[1])
                if isinstance(bounds[0], float)
                else np.random.randint(bounds[0], bounds[1] + 1)
                for name, bounds in param_bounds.items()
            }
        
        population = [random_individual() for _ in range(population_size)]
        
        # 评估适应度
        def evaluate(individual):
            try:
                strategy = strategy_class(**individual)
                result = runner.run(strategy, data)
                return self._get_score(result)
            except:
                return -np.inf
        
        # 进化
        for gen in range(generations):
            # 评估当前种群
            fitness = [(ind, evaluate(ind)) for ind in population]
            fitness.sort(key=lambda x: x[1], reverse=True)
            
            print(f"  代 {gen+1}: 最佳适应度 = {fitness[0][1]:.4f}")
            
            # 选择（保留前50%）
            survivors = [ind for ind, _ in fitness[:population_size//2]]
            
            # 交叉和变异
            new_population = survivors.copy()
            
            while len(new_population) < population_size:
                # 随机选择两个父代
                parent1, parent2 = np.random.choice(survivors, 2, replace=False)
                
                # 交叉
                child = {}
                for name in param_names:
                    child[name] = parent1[name] if np.random.random() < 0.5 else parent2[name]
                
                # 变异
                if np.random.random() < mutation_rate:
                    mutate_param = np.random.choice(param_names)
                    bounds = param_bounds[mutate_param]
                    if isinstance(bounds[0], float):
                        child[mutate_param] = np.random.uniform(bounds[0], bounds[1])
                    else:
                        child[mutate_param] = np.random.randint(bounds[0], bounds[1] + 1)
                
                new_population.append(child)
            
            population = new_population
        
        # 最终评估
        final_fitness = [(ind, evaluate(ind)) for ind in population]
        best = max(final_fitness, key=lambda x: x[1])
        
        self.best_params = best[0]
        self.best_score = best[1]
        
        return {
            'best_params': self.best_params,
            'best_score': self.best_score
        }
    
    def _get_score(self, result) -> float:
        """获取优化目标的分数"""
        if result is None:
            return -np.inf
        
        if self.objective == 'sharpe_ratio':
            return result.sharpe_ratio
        elif self.objective == 'total_return':
            return result.total_return
        elif self.objective == 'calmar_ratio':
            if result.max_drawdown > 0:
                return result.annual_return / result.max_drawdown
            return -np.inf
        elif self.objective == 'win_rate':
            return result.win_rate
        else:
            return result.sharpe_ratio
    
    def get_top_n(self, n: int = 10) -> List[Dict]:
        """
        获取前 N 个最佳参数
        
        Args:
            n: 数量
        
        Returns:
            参数列表
        """
        if not self.results:
            return []
        
        valid = [r for r in self.results if 'error' not in r]
        sorted_results = sorted(valid, key=lambda x: x['score'], reverse=True)
        
        return sorted_results[:n]

