"""
机器学习模型 - XGBoost 多因子模型
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import pickle
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# 可选导入
try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    logger.warning("xgboost not available")

try:
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score, precision_score, recall_score
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("sklearn not available")


class MultiFactorModel:
    """XGBoost 多因子模型"""
    
    def __init__(self):
        self.model = None
        self.feature_cols = []
        self.is_trained = False
    
    def prepare_training_data(self, df: pd.DataFrame, 
                             target_col: str = 'target',
                             feature_cols: Optional[List[str]] = None,
                             forward_days: int = 5) -> Tuple[pd.DataFrame, pd.Series]:
        """
        准备训练数据
        
        Args:
            df: 带因子的数据
            target_col: 目标列名
            feature_cols: 特征列（None 则自动选择）
            forward_days: 预测未来多少天的收益
        
        Returns:
            (特征 DataFrame, 目标 Series)
        """
        df = df.copy()
        
        # 计算未来收益作为目标
        if target_col not in df.columns:
            df[target_col] = df['close'].pct_change(forward_days).shift(-forward_days)
            # 二分类：涨跌
            df[target_col] = (df[target_col] > 0).astype(int)
        
        # 选择特征列
        if feature_cols is None:
            # 自动选择数值型列作为特征
            exclude_cols = ['date', 'symbol', 'timestamp', target_col, 
                          'open', 'high', 'low', 'close', 'volume', 'amount']
            feature_cols = [col for col in df.columns 
                          if col not in exclude_cols and df[col].dtype in ['float64', 'int64']]
        
        self.feature_cols = feature_cols
        
        # 删除缺失值
        df = df.dropna(subset=feature_cols + [target_col])
        
        X = df[feature_cols]
        y = df[target_col]
        
        return X, y
    
    def train(self, X: pd.DataFrame, y: pd.Series,
             test_size: float = 0.2,
             params: Optional[Dict] = None) -> Dict:
        """
        训练模型

        Args:
            X: 特征
            y: 目标
            test_size: 测试集比例
            params: XGBoost 参数

        Returns:
            训练结果字典
        """
        if not XGBOOST_AVAILABLE or not SKLEARN_AVAILABLE:
            return {
                'error': 'xgboost or sklearn not available',
                'train_accuracy': 0,
                'test_accuracy': 0
            }

        # 划分训练集和测试集
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, shuffle=False
        )

        # 默认参数
        if params is None:
            params = {
                'objective': 'binary:logistic',
                'max_depth': 6,
                'learning_rate': 0.1,
                'n_estimators': 100,
                'subsample': 0.8,
                'colsample_bytree': 0.8,
                'random_state': 42
            }

        # 训练模型
        self.model = xgb.XGBClassifier(**params)
        self.model.fit(
            X_train, y_train,
            eval_set=[(X_test, y_test)],
            verbose=False
        )
        
        # 评估
        y_pred_train = self.model.predict(X_train)
        y_pred_test = self.model.predict(X_test)
        
        results = {
            'train_accuracy': accuracy_score(y_train, y_pred_train),
            'test_accuracy': accuracy_score(y_test, y_pred_test),
            'train_precision': precision_score(y_train, y_pred_train, zero_division=0),
            'test_precision': precision_score(y_test, y_pred_test, zero_division=0),
            'train_recall': recall_score(y_train, y_pred_train, zero_division=0),
            'test_recall': recall_score(y_test, y_pred_test, zero_division=0),
            'feature_importance': dict(zip(
                self.feature_cols,
                self.model.feature_importances_
            ))
        }
        
        self.is_trained = True
        
        return results
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        预测
        
        Args:
            X: 特征数据
        
        Returns:
            预测结果（0或1）
        """
        if not self.is_trained or self.model is None:
            raise ValueError("模型未训练")
        
        return self.model.predict(X)
    
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """
        预测概率
        
        Args:
            X: 特征数据
        
        Returns:
            预测概率 [P(0), P(1)]
        """
        if not self.is_trained or self.model is None:
            raise ValueError("模型未训练")
        
        return self.model.predict_proba(X)
    
    def get_top_features(self, n: int = 10) -> List[Tuple[str, float]]:
        """
        获取最重要的特征
        
        Args:
            n: 返回前 n 个
        
        Returns:
            [(特征名, 重要性)] 列表
        """
        if not self.is_trained or self.model is None:
            return []
        
        importance = dict(zip(self.feature_cols, self.model.feature_importances_))
        sorted_features = sorted(importance.items(), key=lambda x: x[1], reverse=True)
        
        return sorted_features[:n]
    
    def save(self, path: str):
        """保存模型"""
        if not self.is_trained:
            raise ValueError("模型未训练")
        
        model_data = {
            'model': self.model,
            'feature_cols': self.feature_cols
        }
        
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'wb') as f:
            pickle.dump(model_data, f)
        
        print(f"模型已保存: {path}")
    
    def load(self, path: str):
        """加载模型"""
        with open(path, 'rb') as f:
            model_data = pickle.load(f)
        
        self.model = model_data['model']
        self.feature_cols = model_data['feature_cols']
        self.is_trained = True
        
        print(f"模型已加载: {path}")

