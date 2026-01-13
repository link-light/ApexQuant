"""
Day 9 示例：实盘整合 + AI 自适应
"""

import sys
import os
import time
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'python'))

from apexquant.adaptive import OnlineLearner, LogAnalyzer, ParameterOptimizer, NotificationManager
from apexquant.live import AISignalGenerator, LiveTrader
from apexquant.data import AKShareWrapper


# 模拟实盘环境
class SimulatedLiveEnvironment:
    """模拟实盘环境"""
    
    def __init__(self, data: pd.DataFrame, initial_cash: float = 100000.0):
        self.data = data
        self.current_index = 60  # 从第60天开始
        self.cash = initial_cash
        self.initial_cash = initial_cash
        self.positions = {}
        self.trades = []
    
    def get_current_data(self) -> pd.DataFrame:
        """获取当前可见数据"""
        return self.data.iloc[:self.current_index+1]
    
    def step(self):
        """前进一步"""
        self.current_index += 1
        return self.current_index < len(self.data)
    
    def execute_trade(self, symbol: str, action: str, price: float, volume: int, reason: str):
        """执行交易"""
        if action == 'buy':
            cost = price * volume
            if cost <= self.cash:
                self.cash -= cost
                self.positions[symbol] = {
                    'volume': volume,
                    'avg_price': price,
                    'buy_time': datetime.now()
                }
                self.trades.append({
                    'timestamp': datetime.now(),
                    'symbol': symbol,
                    'action': action,
                    'price': price,
                    'volume': volume,
                    'reason': reason
                })
                return True
        elif action == 'sell':
            if symbol in self.positions:
                pos = self.positions[symbol]
                proceeds = price * pos['volume']
                self.cash += proceeds
                
                pnl = proceeds - pos['avg_price'] * pos['volume']
                pnl_pct = pnl / (pos['avg_price'] * pos['volume'])
                
                self.trades.append({
                    'timestamp': datetime.now(),
                    'symbol': symbol,
                    'action': action,
                    'price': price,
                    'volume': pos['volume'],
                    'reason': reason,
                    'result': {'pnl': pnl, 'pnl_pct': pnl_pct}
                })
                
                del self.positions[symbol]
                return True
        
        return False
    
    def get_account_status(self) -> dict:
        """获取账户状态"""
        current_price = self.data.iloc[self.current_index]['close']
        market_value = sum(pos['volume'] * current_price for pos in self.positions.values())
        total_assets = self.cash + market_value
        
        return {
            'total_assets': total_assets,
            'available_cash': self.cash,
            'market_value': market_value,
            'profit_loss': total_assets - self.initial_cash,
            'profit_loss_pct': (total_assets - self.initial_cash) / self.initial_cash
        }


def main():
    """完整的 AI 自适应实盘示例"""
    
    print("=" * 80)
    print("ApexQuant - Day 9: 实盘整合 + AI 自适应")
    print("=" * 80)
    
    # ==================== 1. 初始化组件 ====================
    print("\n【步骤 1：初始化组件】")
    
    # 在线学习器
    learner = OnlineLearner(model_path="adaptive_model.json")
    print("✓ 在线学习器已创建")
    
    # 日志分析器
    log_analyzer = LogAnalyzer()
    print("✓ 日志分析器已创建")
    
    # 参数优化器
    param_optimizer = ParameterOptimizer()
    print("✓ 参数优化器已创建")
    
    # 通知管理器
    notifier = NotificationManager()
    print("✓ 通知管理器已创建")
    
    # AI 信号生成器
    signal_gen = AISignalGenerator()
    print("✓ AI 信号生成器已创建")
    
    # ==================== 2. 准备数据 ====================
    print("\n【步骤 2：准备数据】")
    
    wrapper = AKShareWrapper()
    symbol = "600519"
    
    print(f"获取 {symbol} 数据...")
    data = wrapper.get_historical_data(symbol, start_date="2023-01-01", end_date="2023-12-31")
    
    if data is None or data.empty:
        print("⚠ 数据获取失败，使用模拟数据")
        dates = pd.date_range(start='2023-01-01', periods=250, freq='D')
        np.random.seed(42)
        prices = 100 * np.exp(np.cumsum(np.random.normal(0.001, 0.02, 250)))
        
        data = pd.DataFrame({
            'date': dates,
            'open': prices * 0.99,
            'high': prices * 1.02,
            'low': prices * 0.98,
            'close': prices,
            'volume': np.random.randint(1000000, 10000000, 250)
        })
    
    print(f"✓ 数据准备完成，共 {len(data)} 天")
    
    # ==================== 3. 模拟实盘运行 ====================
    print("\n【步骤 3：模拟实盘运行】")
    
    env = SimulatedLiveEnvironment(data, initial_cash=100000.0)
    
    # 参数
    params = {
        'signal_threshold': 0.6,
        'stop_loss': -0.05,
        'take_profit': 0.15,
        'max_position_size': 0.3
    }
    
    print(f"初始参数: {params}")
    print(f"模拟运行 {len(data) - 60} 天...\n")
    
    step_count = 0
    optimization_interval = 20  # 每20天优化一次
    
    while env.step():
        step_count += 1
        
        # 获取当前数据
        current_data = env.get_current_data()
        current_price = current_data['close'].iloc[-1]
        
        # 提取特征（用于在线学习）
        features = learner.extract_features(current_data)
        
        if not features.empty:
            latest_features = features.iloc[-1]
            
            # 预测
            pred_label, pred_prob = learner.predict(latest_features)
            
            # 生成 AI 信号
            position = env.positions.get(symbol)
            action, confidence, reason = signal_gen.generate_signal(
                symbol, current_price, current_data, None, position
            )
            
            # 融合预测结果
            if pred_label == 1 and action == 'hold':
                action = 'buy'
                confidence = max(confidence, pred_prob)
                reason += " + ML预测上涨"
            
            # 执行交易
            if action == 'buy' and not position and confidence >= params['signal_threshold']:
                volume = int((env.cash * params['max_position_size']) / current_price / 100) * 100
                if volume >= 100:
                    success = env.execute_trade(symbol, 'buy', current_price, volume, reason)
                    if success:
                        print(f"Day {step_count}: 买入 {symbol} @ {current_price:.2f}, 置信度 {confidence:.2%}")
                        log_analyzer.log_trade(datetime.now(), symbol, 'buy', current_price, volume, reason)
                        
                        # 发送通知
                        notifier.send_trade_notification(symbol, 'buy', current_price, volume, reason)
            
            elif action == 'sell' and position:
                success = env.execute_trade(symbol, 'sell', current_price, 0, reason)
                if success:
                    print(f"Day {step_count}: 卖出 {symbol} @ {current_price:.2f}")
            
            # 止损止盈检查
            if position:
                pnl_pct = (current_price - position['avg_price']) / position['avg_price']
                
                if pnl_pct <= params['stop_loss']:
                    env.execute_trade(symbol, 'sell', current_price, 0, f"止损 {pnl_pct:.2%}")
                    print(f"Day {step_count}: 触发止损 {pnl_pct:.2%}")
                    
                    notifier.send_risk_alert("止损触发", {
                        '股票': symbol,
                        '亏损': f"{pnl_pct:.2%}"
                    })
                
                elif pnl_pct >= params['take_profit']:
                    env.execute_trade(symbol, 'sell', current_price, 0, f"止盈 {pnl_pct:.2%}")
                    print(f"Day {step_count}: 触发止盈 {pnl_pct:.2%}")
            
            # 在线学习：添加训练样本
            if len(features) > 1:
                prev_features = features.iloc[-2]
                label = 1 if current_data['close'].iloc[-1] > current_data['close'].iloc[-2] else 0
                learner.add_training_sample(prev_features, label)
        
        # 定期优化参数
        if step_count % optimization_interval == 0:
            print(f"\n--- Day {step_count}: 参数优化 ---")
            
            # 更新在线学习模型
            learner.update_model(batch_size=30, force=True)
            
            # 计算性能
            account = env.get_account_status()
            
            wins = sum(1 for t in env.trades if 'result' in t and t['result']['pnl'] > 0)
            total_trades = sum(1 for t in env.trades if 'result' in t)
            win_rate = wins / total_trades if total_trades > 0 else 0
            
            performance = {
                'win_rate': win_rate,
                'return': account['profit_loss_pct'],
                'max_drawdown': 0.05,  # 简化
                'profit_loss_ratio': 1.5  # 简化
            }
            
            # 优化参数
            new_params = param_optimizer.optimize_parameters(params, performance, "normal")
            
            if new_params != params:
                print("参数已调整:")
                for k, v in new_params.items():
                    if params[k] != v:
                        print(f"  {k}: {params[k]} -> {v}")
                params = new_params
            
            # 账户状态
            print(f"账户: 总资产 {account['total_assets']:.2f}, 盈亏 {account['profit_loss']:.2f} ({account['profit_loss_pct']:.2%})")
            print()
    
    # ==================== 4. 最终分析 ====================
    print("\n" + "=" * 80)
    print("【最终分析】")
    print("=" * 80)
    
    final_account = env.get_account_status()
    
    print(f"\n初始资金: {env.initial_cash:.2f}")
    print(f"最终资产: {final_account['total_assets']:.2f}")
    print(f"总盈亏: {final_account['profit_loss']:.2f} ({final_account['profit_loss_pct']:.2%})")
    print(f"总交易次数: {len(env.trades)}")
    
    # 统计
    wins = [t for t in env.trades if 'result' in t and t['result']['pnl'] > 0]
    losses = [t for t in env.trades if 'result' in t and t['result']['pnl'] < 0]
    
    if wins or losses:
        win_rate = len(wins) / (len(wins) + len(losses))
        avg_win = np.mean([t['result']['pnl'] for t in wins]) if wins else 0
        avg_loss = np.mean([abs(t['result']['pnl']) for t in losses]) if losses else 0
        
        print(f"\n胜率: {win_rate:.2%}")
        print(f"平均盈利: {avg_win:.2f}")
        print(f"平均亏损: {avg_loss:.2f}")
        print(f"盈亏比: {avg_win / avg_loss if avg_loss > 0 else 0:.2f}")
    
    # 在线学习统计
    print("\n【在线学习统计】")
    learner_stats = learner.get_stats()
    for k, v in learner_stats.items():
        print(f"  {k}: {v}")
    
    # AI 分析
    print("\n【AI 交易分析】")
    account_perf = {
        'total_assets': final_account['total_assets'],
        'profit_loss': final_account['profit_loss'],
        'profit_loss_pct': final_account['profit_loss_pct'],
        'win_rate': win_rate if (wins or losses) else 0
    }
    
    analysis_report = log_analyzer.analyze_trading_session(env.trades, account_perf)
    print(analysis_report)
    
    # 生成日报
    print("\n" + "=" * 80)
    print("【每日交易报告】")
    print("=" * 80)
    
    daily_report = log_analyzer.generate_daily_report(
        trades=env.trades[-5:] if len(env.trades) >= 5 else env.trades,
        positions=[],
        account=account_perf
    )
    print(daily_report)
    
    # 发送绩效总结
    notifier.send_performance_summary({
        'total_assets': final_account['total_assets'],
        'profit_loss': final_account['profit_loss'],
        'profit_loss_pct': final_account['profit_loss_pct'],
        'win_rate': win_rate if (wins or losses) else 0,
        'max_drawdown': 0.05,
        'trade_count': len(env.trades)
    })
    
    print("\n" + "=" * 80)
    print("Day 9 示例完成！")
    print("=" * 80)


if __name__ == "__main__":
    main()

