"""
K 线图绘制器
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
import mplfinance as mpf
import pandas as pd
import numpy as np
from typing import Optional, List, Tuple
from pathlib import Path


class ChartPlotter:
    """K 线图绘制器"""
    
    def __init__(self, style: str = 'charles'):
        """
        初始化绘图器
        
        Args:
            style: mplfinance 样式 'charles', 'yahoo', 'binance' 等
        """
        self.style = style
        self.fig = None
        self.axes = None
    
    def plot_candlestick(self, df: pd.DataFrame, 
                        title: str = "K线图",
                        volume: bool = True,
                        ma_periods: Optional[List[int]] = None,
                        figsize: Tuple[int, int] = (14, 8),
                        save_path: Optional[str] = None) -> plt.Figure:
        """
        绘制蜡烛图
        
        Args:
            df: 数据 DataFrame（必须包含 OHLCV）
            title: 图表标题
            volume: 是否显示成交量
            ma_periods: 均线周期列表，如 [5, 10, 20]
            figsize: 图表大小
            save_path: 保存路径（可选）
        
        Returns:
            matplotlib Figure 对象
        """
        # 准备数据
        df = df.copy()
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
        
        # 确保列名正确
        required_cols = ['open', 'high', 'low', 'close']
        if not all(col in df.columns for col in required_cols):
            raise ValueError(f"数据必须包含列: {required_cols}")
        
        # 添加均线
        mav = None
        if ma_periods:
            mav = tuple(ma_periods)
        
        # 绘图
        kwargs = {
            'type': 'candle',
            'style': self.style,
            'title': title,
            'ylabel': '价格',
            'volume': volume,
            'figsize': figsize,
            'warn_too_much_data': len(df) + 1
        }
        
        if mav:
            kwargs['mav'] = mav
        
        fig, axes = mpf.plot(df, **kwargs, returnfig=True)
        
        self.fig = fig
        self.axes = axes
        
        # 保存
        if save_path:
            fig.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"图表已保存: {save_path}")
        
        return fig
    
    def plot_with_prediction(self, df: pd.DataFrame,
                            predictions: pd.Series,
                            title: str = "K线图 + 预测",
                            ma_periods: Optional[List[int]] = None,
                            figsize: Tuple[int, int] = (14, 8),
                            save_path: Optional[str] = None) -> plt.Figure:
        """
        绘制带预测的 K 线图
        
        Args:
            df: 历史数据
            predictions: 预测数据
            title: 标题
            ma_periods: 均线周期
            figsize: 图表大小
            save_path: 保存路径
        
        Returns:
            Figure 对象
        """
        # 先绘制基础 K 线图
        fig = self.plot_candlestick(df, title=title, ma_periods=ma_periods, 
                                    figsize=figsize, save_path=None)
        
        # 在主图上添加预测线
        ax = self.axes[0]  # 主图（价格）
        
        # 预测数据
        pred_dates = predictions.index
        pred_values = predictions.values
        
        ax.plot(pred_dates, pred_values, 'r--', linewidth=2, 
                label='预测', alpha=0.7)
        ax.legend()
        
        # 保存
        if save_path:
            fig.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"图表已保存: {save_path}")
        
        return fig
    
    def plot_with_annotations(self, df: pd.DataFrame,
                             annotations: List[dict],
                             title: str = "K线图 + AI分析",
                             ma_periods: Optional[List[int]] = None,
                             figsize: Tuple[int, int] = (14, 8),
                             save_path: Optional[str] = None) -> plt.Figure:
        """
        绘制带 AI 注释的 K 线图
        
        Args:
            df: 数据
            annotations: 注释列表 [{'date': date, 'text': 'xxx', 'type': 'buy/sell'}]
            title: 标题
            ma_periods: 均线周期
            figsize: 图表大小
            save_path: 保存路径
        
        Returns:
            Figure 对象
        """
        fig = self.plot_candlestick(df, title=title, ma_periods=ma_periods,
                                    figsize=figsize, save_path=None)
        
        ax = self.axes[0]
        
        # 添加注释
        for anno in annotations:
            date = pd.to_datetime(anno['date'])
            if date not in df.index:
                continue
            
            price = df.loc[date, 'close']
            text = anno.get('text', '')
            anno_type = anno.get('type', 'info')
            
            # 根据类型选择颜色和符号
            if anno_type == 'buy':
                color = 'green'
                marker = '^'
                y_offset = -20
            elif anno_type == 'sell':
                color = 'red'
                marker = 'v'
                y_offset = 20
            else:
                color = 'blue'
                marker = 'o'
                y_offset = 0
            
            # 绘制标记
            ax.plot(date, price, marker=marker, markersize=10, 
                   color=color, zorder=10)
            
            # 添加文字
            if text:
                ax.annotate(text, xy=(date, price), 
                           xytext=(0, y_offset), textcoords='offset points',
                           ha='center', fontsize=8, color=color,
                           bbox=dict(boxstyle='round,pad=0.3', 
                                   facecolor='white', alpha=0.8))
        
        if save_path:
            fig.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"图表已保存: {save_path}")
        
        return fig
    
    def plot_comparison(self, data_dict: dict,
                       title: str = "多股票对比",
                       normalize: bool = True,
                       figsize: Tuple[int, int] = (14, 6),
                       save_path: Optional[str] = None) -> plt.Figure:
        """
        绘制多只股票对比图
        
        Args:
            data_dict: {symbol: DataFrame} 字典
            title: 标题
            normalize: 是否归一化（基准=100）
            figsize: 图表大小
            save_path: 保存路径
        
        Returns:
            Figure 对象
        """
        fig, ax = plt.subplots(figsize=figsize)
        
        for symbol, df in data_dict.items():
            df = df.copy()
            if 'date' in df.columns:
                dates = pd.to_datetime(df['date'])
            else:
                dates = df.index
            
            prices = df['close'].values
            
            if normalize:
                prices = (prices / prices[0]) * 100
                ylabel = '相对价格（基准=100）'
            else:
                ylabel = '价格'
            
            ax.plot(dates, prices, label=symbol, linewidth=2)
        
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_xlabel('日期', fontsize=12)
        ax.set_ylabel(ylabel, fontsize=12)
        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.3)
        
        # 格式化日期
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        plt.xticks(rotation=45)
        
        plt.tight_layout()
        
        if save_path:
            fig.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"图表已保存: {save_path}")
        
        return fig
    
    @staticmethod
    def show():
        """显示图表"""
        plt.show()
    
    @staticmethod
    def close_all():
        """关闭所有图表"""
        plt.close('all')

