"""
LSTM/GRU 价格预测模型

使用深度学习进行股价趋势预测
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
import logging
from pathlib import Path
import pickle
import json

logger = logging.getLogger(__name__)

# 尝试导入深度学习库
try:
    import torch
    import torch.nn as nn
    from torch.utils.data import DataLoader, TensorDataset
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger.warning("PyTorch not available, using sklearn fallback")

try:
    from sklearn.preprocessing import MinMaxScaler, StandardScaler
    from sklearn.ensemble import GradientBoostingClassifier
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


@dataclass
class PredictionResult:
    """预测结果"""
    symbol: str
    prediction: str  # 'up', 'down', 'neutral'
    probability: float  # 预测置信度
    predicted_return: float  # 预测收益率
    features_used: List[str]
    model_type: str

    def to_dict(self) -> Dict:
        return {
            'symbol': self.symbol,
            'prediction': self.prediction,
            'probability': self.probability,
            'predicted_return': self.predicted_return,
            'features_used': self.features_used,
            'model_type': self.model_type
        }


if TORCH_AVAILABLE:
    class LSTMModel(nn.Module):
        """LSTM 模型"""

        def __init__(self, input_size: int, hidden_size: int = 64,
                     num_layers: int = 2, output_size: int = 1,
                     dropout: float = 0.2):
            super(LSTMModel, self).__init__()

            self.hidden_size = hidden_size
            self.num_layers = num_layers

            self.lstm = nn.LSTM(
                input_size=input_size,
                hidden_size=hidden_size,
                num_layers=num_layers,
                batch_first=True,
                dropout=dropout if num_layers > 1 else 0
            )

            self.fc = nn.Sequential(
                nn.Linear(hidden_size, hidden_size // 2),
                nn.ReLU(),
                nn.Dropout(dropout),
                nn.Linear(hidden_size // 2, output_size)
            )

        def forward(self, x):
            # LSTM层
            lstm_out, _ = self.lstm(x)
            # 取最后一个时间步的输出
            out = self.fc(lstm_out[:, -1, :])
            return out

    class GRUModel(nn.Module):
        """GRU 模型"""

        def __init__(self, input_size: int, hidden_size: int = 64,
                     num_layers: int = 2, output_size: int = 1,
                     dropout: float = 0.2):
            super(GRUModel, self).__init__()

            self.hidden_size = hidden_size
            self.num_layers = num_layers

            self.gru = nn.GRU(
                input_size=input_size,
                hidden_size=hidden_size,
                num_layers=num_layers,
                batch_first=True,
                dropout=dropout if num_layers > 1 else 0
            )

            self.fc = nn.Sequential(
                nn.Linear(hidden_size, hidden_size // 2),
                nn.ReLU(),
                nn.Dropout(dropout),
                nn.Linear(hidden_size // 2, output_size)
            )

        def forward(self, x):
            gru_out, _ = self.gru(x)
            out = self.fc(gru_out[:, -1, :])
            return out

    class AttentionLSTM(nn.Module):
        """带注意力机制的LSTM"""

        def __init__(self, input_size: int, hidden_size: int = 64,
                     num_layers: int = 2, output_size: int = 1,
                     dropout: float = 0.2):
            super(AttentionLSTM, self).__init__()

            self.hidden_size = hidden_size
            self.num_layers = num_layers

            self.lstm = nn.LSTM(
                input_size=input_size,
                hidden_size=hidden_size,
                num_layers=num_layers,
                batch_first=True,
                dropout=dropout if num_layers > 1 else 0
            )

            # 注意力层
            self.attention = nn.Sequential(
                nn.Linear(hidden_size, hidden_size),
                nn.Tanh(),
                nn.Linear(hidden_size, 1)
            )

            self.fc = nn.Sequential(
                nn.Linear(hidden_size, hidden_size // 2),
                nn.ReLU(),
                nn.Dropout(dropout),
                nn.Linear(hidden_size // 2, output_size)
            )

        def forward(self, x):
            lstm_out, _ = self.lstm(x)

            # 计算注意力权重
            attention_weights = torch.softmax(
                self.attention(lstm_out).squeeze(-1), dim=1
            )

            # 加权求和
            context = torch.bmm(
                attention_weights.unsqueeze(1),
                lstm_out
            ).squeeze(1)

            out = self.fc(context)
            return out


class DeepLearningPredictor:
    """深度学习价格预测器"""

    def __init__(self, model_type: str = 'lstm',
                 sequence_length: int = 20,
                 hidden_size: int = 64,
                 num_layers: int = 2,
                 dropout: float = 0.2,
                 device: str = None):
        """
        初始化预测器

        Args:
            model_type: 模型类型 'lstm', 'gru', 'attention_lstm'
            sequence_length: 输入序列长度
            hidden_size: 隐藏层大小
            num_layers: 层数
            dropout: dropout率
            device: 计算设备 ('cpu' or 'cuda')
        """
        self.model_type = model_type
        self.sequence_length = sequence_length
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.dropout = dropout

        if TORCH_AVAILABLE:
            self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        else:
            self.device = 'cpu'

        self.model = None
        self.scaler = MinMaxScaler() if SKLEARN_AVAILABLE else None
        self.feature_cols = []
        self.is_trained = False

        # 回退到sklearn
        if not TORCH_AVAILABLE and SKLEARN_AVAILABLE:
            self.fallback_model = GradientBoostingClassifier(
                n_estimators=100,
                max_depth=5,
                random_state=42
            )
            logger.info("Using sklearn GradientBoosting as fallback")

    def prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        准备特征

        Args:
            df: 原始数据

        Returns:
            带特征的DataFrame
        """
        df = df.copy()

        # 基础价格特征
        df['return_1d'] = df['close'].pct_change()
        df['return_5d'] = df['close'].pct_change(5)
        df['return_10d'] = df['close'].pct_change(10)

        # 技术指标
        # MA
        for period in [5, 10, 20]:
            df[f'ma{period}'] = df['close'].rolling(period).mean()
            df[f'ma{period}_ratio'] = df['close'] / df[f'ma{period}']

        # 波动率
        df['volatility_10d'] = df['return_1d'].rolling(10).std()
        df['volatility_20d'] = df['return_1d'].rolling(20).std()

        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))

        # MACD
        ema12 = df['close'].ewm(span=12, adjust=False).mean()
        ema26 = df['close'].ewm(span=26, adjust=False).mean()
        df['macd'] = ema12 - ema26
        df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
        df['macd_hist'] = df['macd'] - df['macd_signal']

        # 布林带
        df['bb_middle'] = df['close'].rolling(20).mean()
        bb_std = df['close'].rolling(20).std()
        df['bb_upper'] = df['bb_middle'] + 2 * bb_std
        df['bb_lower'] = df['bb_middle'] - 2 * bb_std
        df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])

        # 成交量特征
        if 'volume' in df.columns:
            df['volume_ma5'] = df['volume'].rolling(5).mean()
            df['volume_ratio'] = df['volume'] / df['volume_ma5']

        # 高低价位置
        if 'high' in df.columns and 'low' in df.columns:
            df['hl_range'] = (df['high'] - df['low']) / df['close']
            df['close_position'] = (df['close'] - df['low']) / (df['high'] - df['low'])

        return df

    def create_sequences(self, data: np.ndarray,
                        target: np.ndarray = None) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """
        创建序列数据

        Args:
            data: 特征数据 (n_samples, n_features)
            target: 目标数据 (n_samples,)

        Returns:
            (X, y) 序列数据
        """
        X = []
        y = [] if target is not None else None

        for i in range(len(data) - self.sequence_length):
            X.append(data[i:i + self.sequence_length])
            if target is not None:
                y.append(target[i + self.sequence_length])

        X = np.array(X)
        if y is not None:
            y = np.array(y)

        return X, y

    def train(self, df: pd.DataFrame,
             target_days: int = 5,
             epochs: int = 100,
             batch_size: int = 32,
             learning_rate: float = 0.001,
             validation_split: float = 0.2) -> Dict:
        """
        训练模型

        Args:
            df: 训练数据
            target_days: 预测未来多少天
            epochs: 训练轮数
            batch_size: 批大小
            learning_rate: 学习率
            validation_split: 验证集比例

        Returns:
            训练结果字典
        """
        # 准备特征
        df = self.prepare_features(df)

        # 创建目标: 未来N天的收益方向 (分类任务)
        df['target'] = (df['close'].shift(-target_days) / df['close'] - 1)
        df['target_class'] = (df['target'] > 0).astype(int)

        # 选择特征列
        self.feature_cols = [col for col in df.columns
                           if col not in ['date', 'timestamp', 'symbol', 'target', 'target_class',
                                        'open', 'high', 'low', 'close', 'volume', 'amount']]

        # 去除NaN
        df = df.dropna()

        if len(df) < self.sequence_length + 10:
            return {'error': 'insufficient_data', 'samples': len(df)}

        # 特征矩阵
        features = df[self.feature_cols].values
        target = df['target_class'].values

        # 标准化
        if self.scaler:
            features = self.scaler.fit_transform(features)

        # PyTorch训练
        if TORCH_AVAILABLE:
            return self._train_pytorch(features, target, epochs, batch_size,
                                       learning_rate, validation_split)
        elif SKLEARN_AVAILABLE:
            return self._train_sklearn(features, target, validation_split)
        else:
            return {'error': 'no_ml_library'}

    def _train_pytorch(self, features: np.ndarray, target: np.ndarray,
                       epochs: int, batch_size: int, learning_rate: float,
                       validation_split: float) -> Dict:
        """PyTorch训练"""
        # 创建序列
        X, y = self.create_sequences(features, target)

        # 划分训练/验证集
        split_idx = int(len(X) * (1 - validation_split))
        X_train, X_val = X[:split_idx], X[split_idx:]
        y_train, y_val = y[:split_idx], y[split_idx:]

        # 转换为tensor
        X_train = torch.FloatTensor(X_train).to(self.device)
        y_train = torch.FloatTensor(y_train).to(self.device)
        X_val = torch.FloatTensor(X_val).to(self.device)
        y_val = torch.FloatTensor(y_val).to(self.device)

        # 创建模型
        input_size = X_train.shape[2]
        if self.model_type == 'lstm':
            self.model = LSTMModel(input_size, self.hidden_size, self.num_layers,
                                  output_size=1, dropout=self.dropout)
        elif self.model_type == 'gru':
            self.model = GRUModel(input_size, self.hidden_size, self.num_layers,
                                 output_size=1, dropout=self.dropout)
        elif self.model_type == 'attention_lstm':
            self.model = AttentionLSTM(input_size, self.hidden_size, self.num_layers,
                                       output_size=1, dropout=self.dropout)

        self.model = self.model.to(self.device)

        # 损失函数和优化器
        criterion = nn.BCEWithLogitsLoss()
        optimizer = torch.optim.Adam(self.model.parameters(), lr=learning_rate)
        scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
            optimizer, mode='min', factor=0.5, patience=10
        )

        # 训练循环
        train_losses = []
        val_losses = []
        best_val_loss = float('inf')
        best_model_state = None

        for epoch in range(epochs):
            # 训练
            self.model.train()
            train_loss = 0

            # Mini-batch训练
            indices = torch.randperm(len(X_train))
            for i in range(0, len(X_train), batch_size):
                batch_idx = indices[i:i + batch_size]
                batch_X = X_train[batch_idx]
                batch_y = y_train[batch_idx]

                optimizer.zero_grad()
                outputs = self.model(batch_X).squeeze()
                loss = criterion(outputs, batch_y)
                loss.backward()
                optimizer.step()

                train_loss += loss.item()

            train_loss /= (len(X_train) // batch_size + 1)
            train_losses.append(train_loss)

            # 验证
            self.model.eval()
            with torch.no_grad():
                val_outputs = self.model(X_val).squeeze()
                val_loss = criterion(val_outputs, y_val).item()
                val_losses.append(val_loss)

                # 计算准确率
                val_preds = (torch.sigmoid(val_outputs) > 0.5).float()
                val_accuracy = (val_preds == y_val).float().mean().item()

            scheduler.step(val_loss)

            # 保存最佳模型
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                best_model_state = self.model.state_dict().copy()

            if (epoch + 1) % 10 == 0:
                logger.info(f"Epoch {epoch+1}/{epochs}, Train Loss: {train_loss:.4f}, "
                           f"Val Loss: {val_loss:.4f}, Val Acc: {val_accuracy:.4f}")

        # 恢复最佳模型
        if best_model_state:
            self.model.load_state_dict(best_model_state)

        self.is_trained = True

        # 最终评估
        self.model.eval()
        with torch.no_grad():
            train_preds = (torch.sigmoid(self.model(X_train).squeeze()) > 0.5).float()
            train_accuracy = (train_preds == y_train).float().mean().item()

            val_preds = (torch.sigmoid(self.model(X_val).squeeze()) > 0.5).float()
            val_accuracy = (val_preds == y_val).float().mean().item()

        return {
            'model_type': self.model_type,
            'train_accuracy': train_accuracy,
            'val_accuracy': val_accuracy,
            'train_samples': len(X_train),
            'val_samples': len(X_val),
            'best_val_loss': best_val_loss,
            'epochs_trained': epochs,
            'features': self.feature_cols
        }

    def _train_sklearn(self, features: np.ndarray, target: np.ndarray,
                       validation_split: float) -> Dict:
        """Sklearn回退训练"""
        # 简单划分
        split_idx = int(len(features) * (1 - validation_split))
        X_train, X_val = features[:split_idx], features[split_idx:]
        y_train, y_val = target[:split_idx], target[split_idx:]

        # 训练
        self.fallback_model.fit(X_train, y_train)
        self.is_trained = True

        # 评估
        train_accuracy = self.fallback_model.score(X_train, y_train)
        val_accuracy = self.fallback_model.score(X_val, y_val)

        return {
            'model_type': 'gradient_boosting_fallback',
            'train_accuracy': train_accuracy,
            'val_accuracy': val_accuracy,
            'train_samples': len(X_train),
            'val_samples': len(X_val)
        }

    def predict(self, df: pd.DataFrame, symbol: str = "") -> PredictionResult:
        """
        预测

        Args:
            df: 最近的价格数据 (至少需要sequence_length + 30天)
            symbol: 股票代码

        Returns:
            预测结果
        """
        if not self.is_trained:
            return PredictionResult(
                symbol=symbol,
                prediction='neutral',
                probability=0.5,
                predicted_return=0.0,
                features_used=[],
                model_type='not_trained'
            )

        # 准备特征
        df = self.prepare_features(df)
        df = df.dropna()

        if len(df) < self.sequence_length:
            return PredictionResult(
                symbol=symbol,
                prediction='neutral',
                probability=0.5,
                predicted_return=0.0,
                features_used=[],
                model_type='insufficient_data'
            )

        # 获取特征
        features = df[self.feature_cols].values[-self.sequence_length:]

        if self.scaler:
            features = self.scaler.transform(features)

        if TORCH_AVAILABLE and self.model is not None:
            return self._predict_pytorch(features, symbol)
        elif SKLEARN_AVAILABLE and hasattr(self, 'fallback_model'):
            return self._predict_sklearn(features, symbol)
        else:
            return PredictionResult(
                symbol=symbol,
                prediction='neutral',
                probability=0.5,
                predicted_return=0.0,
                features_used=self.feature_cols,
                model_type='no_model'
            )

    def _predict_pytorch(self, features: np.ndarray, symbol: str) -> PredictionResult:
        """PyTorch预测"""
        self.model.eval()

        # 转换为tensor
        X = torch.FloatTensor(features).unsqueeze(0).to(self.device)

        with torch.no_grad():
            output = self.model(X).squeeze()
            prob = torch.sigmoid(output).item()

        # 判断预测方向
        if prob > 0.6:
            prediction = 'up'
        elif prob < 0.4:
            prediction = 'down'
        else:
            prediction = 'neutral'

        # 估计收益率 (简单估计)
        predicted_return = (prob - 0.5) * 10  # 假设概率映射到-5%到+5%

        return PredictionResult(
            symbol=symbol,
            prediction=prediction,
            probability=prob if prediction == 'up' else (1 - prob),
            predicted_return=predicted_return,
            features_used=self.feature_cols,
            model_type=self.model_type
        )

    def _predict_sklearn(self, features: np.ndarray, symbol: str) -> PredictionResult:
        """Sklearn预测"""
        # 使用最后一个时间点的特征
        X = features[-1:].reshape(1, -1)

        pred = self.fallback_model.predict(X)[0]
        prob = self.fallback_model.predict_proba(X)[0]

        if pred == 1:
            prediction = 'up'
            probability = prob[1]
        else:
            prediction = 'down'
            probability = prob[0]

        return PredictionResult(
            symbol=symbol,
            prediction=prediction,
            probability=probability,
            predicted_return=(probability - 0.5) * 10,
            features_used=self.feature_cols,
            model_type='gradient_boosting'
        )

    def save(self, path: str):
        """保存模型"""
        if not self.is_trained:
            raise ValueError("Model not trained")

        save_path = Path(path)
        save_path.parent.mkdir(parents=True, exist_ok=True)

        save_data = {
            'model_type': self.model_type,
            'sequence_length': self.sequence_length,
            'hidden_size': self.hidden_size,
            'num_layers': self.num_layers,
            'feature_cols': self.feature_cols,
            'scaler': self.scaler
        }

        if TORCH_AVAILABLE and self.model is not None:
            save_data['model_state'] = self.model.state_dict()
            save_data['model_class'] = type(self.model).__name__

        with open(path, 'wb') as f:
            pickle.dump(save_data, f)

        logger.info(f"Model saved to {path}")

    def load(self, path: str):
        """加载模型"""
        with open(path, 'rb') as f:
            save_data = pickle.load(f)

        self.model_type = save_data['model_type']
        self.sequence_length = save_data['sequence_length']
        self.hidden_size = save_data['hidden_size']
        self.num_layers = save_data['num_layers']
        self.feature_cols = save_data['feature_cols']
        self.scaler = save_data['scaler']

        if TORCH_AVAILABLE and 'model_state' in save_data:
            input_size = len(self.feature_cols)
            if save_data['model_class'] == 'LSTMModel':
                self.model = LSTMModel(input_size, self.hidden_size, self.num_layers)
            elif save_data['model_class'] == 'GRUModel':
                self.model = GRUModel(input_size, self.hidden_size, self.num_layers)
            elif save_data['model_class'] == 'AttentionLSTM':
                self.model = AttentionLSTM(input_size, self.hidden_size, self.num_layers)

            self.model.load_state_dict(save_data['model_state'])
            self.model = self.model.to(self.device)

        self.is_trained = True
        logger.info(f"Model loaded from {path}")


# 便捷函数
def predict_stock_trend(df: pd.DataFrame, symbol: str = "",
                       model_path: Optional[str] = None) -> PredictionResult:
    """
    预测股票趋势

    Args:
        df: 价格数据
        symbol: 股票代码
        model_path: 预训练模型路径

    Returns:
        预测结果
    """
    predictor = DeepLearningPredictor()

    if model_path and Path(model_path).exists():
        predictor.load(model_path)
    else:
        # 使用数据训练
        result = predictor.train(df)
        if 'error' in result:
            return PredictionResult(
                symbol=symbol,
                prediction='neutral',
                probability=0.5,
                predicted_return=0.0,
                features_used=[],
                model_type='training_failed'
            )

    return predictor.predict(df, symbol)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("=" * 60)
    print("LSTM/GRU 预测器测试")
    print("=" * 60)

    print(f"PyTorch available: {TORCH_AVAILABLE}")
    print(f"sklearn available: {SKLEARN_AVAILABLE}")

    # 创建模拟数据
    np.random.seed(42)
    n_samples = 500
    dates = pd.date_range('2024-01-01', periods=n_samples, freq='D')

    # 模拟带趋势的价格数据
    trend = np.linspace(0, 50, n_samples)
    noise = np.cumsum(np.random.randn(n_samples) * 2)
    price = 100 + trend + noise

    df = pd.DataFrame({
        'date': dates,
        'open': price - np.random.rand(n_samples) * 2,
        'high': price + np.random.rand(n_samples) * 3,
        'low': price - np.random.rand(n_samples) * 3,
        'close': price,
        'volume': np.random.randint(1000000, 5000000, n_samples)
    })

    # 测试
    predictor = DeepLearningPredictor(model_type='lstm', sequence_length=20)

    print("\n训练模型...")
    result = predictor.train(df, epochs=50)

    print(f"\n训练结果:")
    for key, value in result.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.4f}")
        elif key != 'features':
            print(f"  {key}: {value}")

    print("\n预测...")
    pred = predictor.predict(df, symbol="TEST")
    print(f"预测结果: {pred.to_dict()}")

    print("\n" + "=" * 60)
