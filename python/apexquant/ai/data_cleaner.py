"""
AI 驱动的数据清洗
"""

import pandas as pd
import numpy as np
from typing import Optional
from .deepseek_client import DeepSeekClient


class AIDataCleaner:
    """AI 数据清洗器"""
    
    def __init__(self, api_key: Optional[str] = None):
        try:
            self.client = DeepSeekClient(api_key)
            self.ai_enabled = True
        except:
            print("DeepSeek 未配置，使用传统方法")
            self.ai_enabled = False
    
    def detect_and_fill_missing(self, df: pd.DataFrame, 
                                column: str = 'close') -> pd.DataFrame:
        """
        检测并填充缺失值
        
        Args:
            df: 数据 DataFrame
            column: 要处理的列名
        
        Returns:
            处理后的 DataFrame
        """
        df = df.copy()
        
        # 检测缺失值
        missing_mask = df[column].isna()
        missing_count = missing_mask.sum()
        
        if missing_count == 0:
            return df
        
        print(f"发现 {missing_count} 个缺失值")
        
        # 使用线性插值填充
        df[column] = df[column].interpolate(method='linear')
        
        # 如果首尾有缺失，用前向/后向填充
        df[column] = df[column].fillna(method='ffill').fillna(method='bfill')
        
        print(f"✓ 已填充缺失值")
        
        return df
    
    def detect_outliers(self, df: pd.DataFrame, column: str = 'close',
                       threshold: float = 3.0) -> pd.DataFrame:
        """
        检测异常值
        
        Args:
            df: 数据 DataFrame
            column: 要检测的列名
            threshold: Z-score 阈值
        
        Returns:
            带异常标记的 DataFrame
        """
        df = df.copy()
        
        # 计算 Z-score
        mean = df[column].mean()
        std = df[column].std()
        
        df['z_score'] = (df[column] - mean) / std
        df['is_outlier'] = np.abs(df['z_score']) > threshold
        
        outlier_count = df['is_outlier'].sum()
        
        if outlier_count > 0:
            print(f"检测到 {outlier_count} 个异常值")
        
        return df
    
    def smooth_data(self, df: pd.DataFrame, column: str = 'close',
                   window: int = 5) -> pd.DataFrame:
        """
        数据平滑
        
        Args:
            df: 数据 DataFrame
            column: 要平滑的列名
            window: 窗口大小
        
        Returns:
            带平滑列的 DataFrame
        """
        df = df.copy()
        df[f'{column}_smooth'] = df[column].rolling(window=window, center=True).mean()
        df[f'{column}_smooth'] = df[f'{column}_smooth'].fillna(df[column])
        
        return df
    
    def clean_pipeline(self, df: pd.DataFrame, 
                      columns: list = ['open', 'high', 'low', 'close']) -> pd.DataFrame:
        """
        完整清洗流程
        
        Args:
            df: 数据 DataFrame
            columns: 要清洗的列名列表
        
        Returns:
            清洗后的 DataFrame
        """
        df = df.copy()
        
        print(f"开始数据清洗，原始数据 {len(df)} 条")
        
        for col in columns:
            if col in df.columns:
                # 填充缺失值
                df = self.detect_and_fill_missing(df, col)
                
                # 检测异常值
                df = self.detect_outliers(df, col)
        
        # 删除仍有问题的行
        before_count = len(df)
        df = df.dropna(subset=columns)
        after_count = len(df)
        
        if before_count != after_count:
            print(f"删除了 {before_count - after_count} 条无效数据")
        
        print(f"✓ 数据清洗完成，最终 {len(df)} 条")
        
        return df

