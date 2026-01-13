"""
强化学习交易代理
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
import pickle
import os


class RLTradingAgent:
    """
    强化学习交易代理
    
    使用 DQN 或 PPO 进行交易决策
    注意：这是简化版本，完整版需要集成 RLlib
    """
    
    def __init__(self, 
                 state_dim: int = 10,
                 action_dim: int = 3,
                 model_path: Optional[str] = None):
        """
        初始化
        
        Args:
            state_dim: 状态维度
            action_dim: 动作维度（0: hold, 1: buy, 2: sell）
            model_path: 模型路径
        """
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.model_path = model_path
        
        # 简单 Q-table（完整版应使用深度网络）
        self.q_table = {}
        self.learning_rate = 0.1
        self.gamma = 0.95
        self.epsilon = 0.1
        
        # 加载模型
        if model_path and os.path.exists(model_path):
            self.load_model(model_path)
    
    def get_state(self, 
                  data: pd.DataFrame,
                  position: Optional[Dict] = None) -> np.ndarray:
        """
        从市场数据提取状态
        
        Args:
            data: 市场数据
            position: 当前持仓
        
        Returns:
            状态向量
        """
        if len(data) < 20:
            return np.zeros(self.state_dim)
        
        close_prices = data['close'].values[-20:]
        volumes = data['volume'].values[-20:]
        
        # 标准化
        price_mean = np.mean(close_prices)
        price_std = np.std(close_prices) + 1e-8
        volume_mean = np.mean(volumes)
        volume_std = np.std(volumes) + 1e-8
        
        # 构造状态特征
        state = []
        
        # 1. 价格归一化特征
        current_price_norm = (close_prices[-1] - price_mean) / price_std
        state.append(current_price_norm)
        
        # 2. 短期趋势
        ma5 = np.mean(close_prices[-5:])
        ma10 = np.mean(close_prices[-10:])
        trend_5_10 = (ma5 - ma10) / price_mean
        state.append(trend_5_10)
        
        # 3. 长期趋势
        ma20 = np.mean(close_prices)
        trend_5_20 = (ma5 - ma20) / price_mean
        state.append(trend_5_20)
        
        # 4. 价格动量
        momentum = (close_prices[-1] - close_prices[-5]) / close_prices[-5]
        state.append(momentum)
        
        # 5. 波动率
        volatility = price_std / price_mean
        state.append(volatility)
        
        # 6. 成交量归一化
        volume_norm = (volumes[-1] - volume_mean) / volume_std
        state.append(volume_norm)
        
        # 7. 持仓状态
        if position and position.get('volume', 0) > 0:
            pos_ratio = position['volume'] / 1000.0  # 假设最大持仓 1000 股
            profit_ratio = (close_prices[-1] - position['avg_price']) / position['avg_price']
            state.extend([pos_ratio, profit_ratio])
        else:
            state.extend([0.0, 0.0])
        
        # 8. RSI
        rsi = self._calculate_rsi(close_prices, period=14)
        state.append(rsi / 100.0)
        
        # 9. MACD 信号
        macd_signal = self._calculate_macd_signal(close_prices)
        state.append(macd_signal)
        
        # 确保维度正确
        state = np.array(state[:self.state_dim])
        if len(state) < self.state_dim:
            state = np.pad(state, (0, self.state_dim - len(state)))
        
        return state
    
    def select_action(self, 
                     state: np.ndarray,
                     deterministic: bool = False) -> int:
        """
        选择动作
        
        Args:
            state: 当前状态
            deterministic: 是否确定性选择
        
        Returns:
            动作 (0: hold, 1: buy, 2: sell)
        """
        # 离散化状态（用于 Q-table）
        state_key = self._discretize_state(state)
        
        # ε-greedy 策略
        if not deterministic and np.random.random() < self.epsilon:
            return np.random.randint(self.action_dim)
        
        # 选择最优动作
        if state_key not in self.q_table:
            self.q_table[state_key] = np.zeros(self.action_dim)
        
        return np.argmax(self.q_table[state_key])
    
    def update(self, 
              state: np.ndarray,
              action: int,
              reward: float,
              next_state: np.ndarray,
              done: bool = False):
        """
        更新模型（Q-learning）
        
        Args:
            state: 当前状态
            action: 采取的动作
            reward: 获得的奖励
            next_state: 下一状态
            done: 是否结束
        """
        state_key = self._discretize_state(state)
        next_state_key = self._discretize_state(next_state)
        
        if state_key not in self.q_table:
            self.q_table[state_key] = np.zeros(self.action_dim)
        if next_state_key not in self.q_table:
            self.q_table[next_state_key] = np.zeros(self.action_dim)
        
        # Q-learning 更新
        current_q = self.q_table[state_key][action]
        max_next_q = np.max(self.q_table[next_state_key]) if not done else 0.0
        
        new_q = current_q + self.learning_rate * (reward + self.gamma * max_next_q - current_q)
        self.q_table[state_key][action] = new_q
    
    def train_episode(self,
                     data: pd.DataFrame,
                     initial_cash: float = 100000.0) -> Dict:
        """
        训练一个回合
        
        Args:
            data: 训练数据
            initial_cash: 初始资金
        
        Returns:
            训练结果
        """
        cash = initial_cash
        position = {'volume': 0, 'avg_price': 0.0}
        
        total_reward = 0.0
        trades = 0
        
        for i in range(20, len(data)):
            # 当前状态
            current_data = data.iloc[:i+1]
            state = self.get_state(current_data, position)
            
            # 选择动作
            action = self.select_action(state, deterministic=False)
            
            # 执行动作
            current_price = data.iloc[i]['close']
            reward = 0.0
            
            if action == 1 and position['volume'] == 0:  # Buy
                volume = int(cash * 0.9 / current_price)
                if volume > 0:
                    cost = current_price * volume
                    cash -= cost
                    position['volume'] = volume
                    position['avg_price'] = current_price
                    trades += 1
            
            elif action == 2 and position['volume'] > 0:  # Sell
                proceeds = current_price * position['volume']
                cash += proceeds
                reward = (current_price - position['avg_price']) / position['avg_price']
                position['volume'] = 0
                position['avg_price'] = 0.0
                trades += 1
            
            # 持仓奖励
            if position['volume'] > 0:
                unrealized_pnl = (current_price - position['avg_price']) / position['avg_price']
                reward += unrealized_pnl * 0.1
            
            # 下一状态
            if i < len(data) - 1:
                next_data = data.iloc[:i+2]
                next_state = self.get_state(next_data, position)
                done = False
            else:
                next_state = state
                done = True
            
            # 更新模型
            self.update(state, action, reward, next_state, done)
            total_reward += reward
        
        # 最终资产
        final_value = cash
        if position['volume'] > 0:
            final_value += position['volume'] * data.iloc[-1]['close']
        
        return {
            'total_reward': total_reward,
            'final_value': final_value,
            'return': (final_value - initial_cash) / initial_cash,
            'trades': trades
        }
    
    def save_model(self, path: str):
        """保存模型"""
        with open(path, 'wb') as f:
            pickle.dump({
                'q_table': self.q_table,
                'state_dim': self.state_dim,
                'action_dim': self.action_dim
            }, f)
    
    def load_model(self, path: str):
        """加载模型"""
        with open(path, 'rb') as f:
            data = pickle.load(f)
            self.q_table = data['q_table']
            self.state_dim = data['state_dim']
            self.action_dim = data['action_dim']
    
    def _discretize_state(self, state: np.ndarray, bins: int = 10) -> Tuple:
        """离散化状态"""
        discretized = tuple((state * bins).astype(int))
        return discretized
    
    def _calculate_rsi(self, prices: np.ndarray, period: int = 14) -> float:
        """计算 RSI"""
        if len(prices) < period + 1:
            return 50.0
        
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def _calculate_macd_signal(self, prices: np.ndarray) -> float:
        """计算 MACD 信号"""
        if len(prices) < 26:
            return 0.0
        
        ema12 = self._ema(prices, 12)
        ema26 = self._ema(prices, 26)
        macd = ema12 - ema26
        
        return np.tanh(macd / prices[-1])  # 归一化
    
    def _ema(self, prices: np.ndarray, period: int) -> float:
        """计算 EMA"""
        if len(prices) < period:
            return np.mean(prices)
        
        multiplier = 2 / (period + 1)
        ema = prices[-period]
        
        for price in prices[-period+1:]:
            ema = (price - ema) * multiplier + ema
        
        return ema

