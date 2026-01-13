"""
在线学习模块
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
import pickle
import os

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    print("⚠ XGBoost 未安装，在线学习功能受限")


class OnlineLearner:
    """
    在线学习模块
    
    支持 XGBoost 增量学习，实时更新模型
    """
    
    def __init__(self, 
                 model_path: Optional[str] = None,
                 feature_cols: Optional[List[str]] = None):
        """
        初始化
        
        Args:
            model_path: 模型保存路径
            feature_cols: 特征列名
        """
        self.model_path = model_path or "online_model.json"
        self.feature_cols = feature_cols or self._default_features()
        
        self.model = None
        self.training_data = []
        self.training_labels = []
        
        self.update_count = 0
        self.performance_history = []
        
        # 加载已有模型
        if os.path.exists(self.model_path):
            self.load_model()
        else:
            self._initialize_model()
    
    def _default_features(self) -> List[str]:
        """默认特征列"""
        return [
            'ma5', 'ma10', 'ma20', 'ma60',
            'rsi', 'macd', 'signal', 'histogram',
            'volume_ratio', 'price_change_1d', 'price_change_5d',
            'volatility_5d', 'volatility_20d'
        ]
    
    def _initialize_model(self):
        """初始化模型"""
        if not XGBOOST_AVAILABLE:
            self.model = None
            return
        
        self.model = xgb.XGBClassifier(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            objective='binary:logistic',
            random_state=42
        )
    
    def extract_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        从市场数据提取特征
        
        Args:
            data: 市场数据（需要包含 OHLCV）
        
        Returns:
            特征 DataFrame
        """
        if len(data) < 60:
            return pd.DataFrame()
        
        features = pd.DataFrame(index=data.index)
        
        # 价格特征
        close = data['close'].values
        
        # 均线
        features['ma5'] = data['close'].rolling(5).mean()
        features['ma10'] = data['close'].rolling(10).mean()
        features['ma20'] = data['close'].rolling(20).mean()
        features['ma60'] = data['close'].rolling(60).mean()
        
        # RSI
        features['rsi'] = self._calculate_rsi(data['close'])
        
        # MACD
        macd, signal, histogram = self._calculate_macd(data['close'])
        features['macd'] = macd
        features['signal'] = signal
        features['histogram'] = histogram
        
        # 成交量比率
        features['volume_ratio'] = data['volume'] / data['volume'].rolling(5).mean()
        
        # 价格变化
        features['price_change_1d'] = data['close'].pct_change(1)
        features['price_change_5d'] = data['close'].pct_change(5)
        
        # 波动率
        features['volatility_5d'] = data['close'].rolling(5).std()
        features['volatility_20d'] = data['close'].rolling(20).std()
        
        # 去除 NaN
        features = features.dropna()
        
        return features
    
    def add_training_sample(self, 
                           features: pd.Series, 
                           label: int):
        """
        添加训练样本
        
        Args:
            features: 特征向量
            label: 标签 (1: 上涨, 0: 下跌)
        """
        # 确保特征顺序一致
        feature_vector = [features.get(col, 0.0) for col in self.feature_cols]
        
        self.training_data.append(feature_vector)
        self.training_labels.append(label)
    
    def update_model(self, 
                    batch_size: int = 50,
                    force: bool = False) -> bool:
        """
        更新模型（增量学习）
        
        Args:
            batch_size: 批次大小
            force: 强制更新
        
        Returns:
            是否成功更新
        """
        if not XGBOOST_AVAILABLE or self.model is None:
            return False
        
        # 检查数据量
        if len(self.training_data) < batch_size and not force:
            return False
        
        if len(self.training_data) == 0:
            return False
        
        print(f"更新模型，样本数: {len(self.training_data)}")
        
        X = np.array(self.training_data)
        y = np.array(self.training_labels)
        
        try:
            # XGBoost 增量学习
            if self.update_count == 0:
                # 首次训练
                self.model.fit(X, y)
            else:
                # 增量更新
                self.model.fit(X, y, xgb_model=self.model.get_booster())
            
            self.update_count += 1
            
            # 评估性能
            if len(X) > 10:
                score = self.model.score(X, y)
                self.performance_history.append(score)
                print(f"  模型准确率: {score:.3f}")
            
            # 保存模型
            self.save_model()
            
            # 清空缓存（保留最近的样本）
            keep_size = batch_size // 2
            if len(self.training_data) > keep_size:
                self.training_data = self.training_data[-keep_size:]
                self.training_labels = self.training_labels[-keep_size:]
            
            return True
            
        except Exception as e:
            print(f"模型更新失败: {e}")
            return False
    
    def predict(self, features: pd.Series) -> Tuple[int, float]:
        """
        预测
        
        Args:
            features: 特征向量
        
        Returns:
            (预测标签, 概率)
        """
        if not XGBOOST_AVAILABLE or self.model is None:
            return 0, 0.5
        
        try:
            feature_vector = np.array([[features.get(col, 0.0) for col in self.feature_cols]])
            
            pred_proba = self.model.predict_proba(feature_vector)[0]
            pred_label = int(pred_proba[1] > 0.5)
            
            return pred_label, pred_proba[1]
            
        except Exception as e:
            print(f"预测失败: {e}")
            return 0, 0.5
    
    def save_model(self):
        """保存模型"""
        if not XGBOOST_AVAILABLE or self.model is None:
            return
        
        try:
            # 保存 XGBoost 模型
            self.model.save_model(self.model_path)
            
            # 保存元数据
            meta_path = self.model_path.replace('.json', '_meta.pkl')
            with open(meta_path, 'wb') as f:
                pickle.dump({
                    'feature_cols': self.feature_cols,
                    'update_count': self.update_count,
                    'performance_history': self.performance_history
                }, f)
            
        except Exception as e:
            print(f"保存模型失败: {e}")
    
    def load_model(self):
        """加载模型"""
        if not XGBOOST_AVAILABLE:
            return
        
        try:
            if os.path.exists(self.model_path):
                self.model = xgb.XGBClassifier()
                self.model.load_model(self.model_path)
                
                # 加载元数据
                meta_path = self.model_path.replace('.json', '_meta.pkl')
                if os.path.exists(meta_path):
                    with open(meta_path, 'rb') as f:
                        meta = pickle.load(f)
                        self.feature_cols = meta.get('feature_cols', self.feature_cols)
                        self.update_count = meta.get('update_count', 0)
                        self.performance_history = meta.get('performance_history', [])
                
                print(f"模型已加载，更新次数: {self.update_count}")
            
        except Exception as e:
            print(f"加载模型失败: {e}")
            self._initialize_model()
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            'update_count': self.update_count,
            'training_samples': len(self.training_data),
            'avg_accuracy': np.mean(self.performance_history) if self.performance_history else 0.0,
            'recent_accuracy': self.performance_history[-5:] if len(self.performance_history) >= 5 else self.performance_history
        }
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """计算 RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def _calculate_macd(self, 
                       prices: pd.Series,
                       fast: int = 12,
                       slow: int = 26,
                       signal_period: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """计算 MACD"""
        ema_fast = prices.ewm(span=fast, adjust=False).mean()
        ema_slow = prices.ewm(span=slow, adjust=False).mean()
        
        macd = ema_fast - ema_slow
        signal = macd.ewm(span=signal_period, adjust=False).mean()
        histogram = macd - signal
        
        return macd, signal, histogram

