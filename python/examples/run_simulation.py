"""
ApexQuant 模拟盘运行脚本

命令行工具，支持回测和实时模式
"""

import sys
import os
import argparse
import logging

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from apexquant.simulation.simulation_controller import SimulationController, SimulationMode
from apexquant.simulation.config import get_config
from apexquant.simulation.risk_manager import RiskManager
from apexquant.simulation.performance_analyzer import PerformanceAnalyzer
from apexquant.simulation.strategies import get_strategy


def main():
    """主函数"""
    # 参数解析
    parser = argparse.ArgumentParser(
        description='ApexQuant Simulation Trading System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Backtest with MA cross strategy
  python run_simulation.py --mode backtest --symbol 600519.SH --start-date 2024-01-01 --end-date 2024-12-31 --strategy ma_cross

  # Realtime paper trading
  python run_simulation.py --mode realtime --symbol 600519.SH --start-date 2025-02-06 --strategy ma_cross

  # With AI advisor
  python run_simulation.py --mode backtest --symbol 600519.SH --start-date 2024-01-01 --end-date 2024-12-31 --strategy ma_cross --use-ai
        """
    )
    
    parser.add_argument('--mode', type=str, required=True, 
                       choices=['backtest', 'realtime'],
                       help='Running mode')
    parser.add_argument('--symbol', type=str, required=True,
                       help='Stock symbol (e.g., 600519.SH)')
    parser.add_argument('--start-date', type=str, required=True,
                       help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str, default=None,
                       help='End date (YYYY-MM-DD, required for backtest)')
    parser.add_argument('--initial-capital', type=float, default=None,
                       help='Initial capital (default: from config)')
    parser.add_argument('--strategy', type=str, required=True,
                       choices=['ma_cross', 'buy_hold', 'ai_driven', 'rsi'],
                       help='Strategy name')
    parser.add_argument('--use-ai', action='store_true',
                       help='Enable AI advisor')
    parser.add_argument('--db-path', type=str, default=None,
                       help='Database path (default: data/sim_trader.db)')
    parser.add_argument('--output-dir', type=str, default='output',
                       help='Output directory for reports')
    parser.add_argument('--config', type=str, default=None,
                       help='Config file path')
    
    args = parser.parse_args()
    
    # 配置日志
    log_level = logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('logs/simulation.log')
        ]
    )
    
    logger = logging.getLogger(__name__)
    
    # 打印启动信息
    print("=" * 60)
    print("ApexQuant Simulation Trading System")
    print("=" * 60)
    print(f"Mode: {args.mode}")
    print(f"Symbol: {args.symbol}")
    print(f"Period: {args.start_date} to {args.end_date}")
    print(f"Strategy: {args.strategy}")
    print(f"AI Advisor: {'Enabled' if args.use_ai else 'Disabled'}")
    print("=" * 60 + "\n")
    
    # 验证参数
    if args.mode == 'backtest' and args.end_date is None:
        logger.error("--end-date is required for backtest mode")
        return 1
    
    try:
        # 1. 加载配置
        config = get_config(args.config)
        
        # 2. 初始化控制器
        mode = SimulationMode.BACKTEST if args.mode == 'backtest' else SimulationMode.REALTIME
        
        controller = SimulationController(
            mode=mode,
            initial_capital=args.initial_capital,
            db_path=args.db_path,
            config_path=args.config
        )
        
        logger.info(f"Account created: {controller.account_id}")
        
        # 3. 初始化风控管理器
        risk_manager = RiskManager(args.config)
        
        # 4. 初始化AI顾问（如果启用）
        ai_advisor = None
        if args.use_ai:
            try:
                from apexquant.simulation.ai_advisor import AITradingAdvisor
                ai_advisor = AITradingAdvisor(config_path=args.config)
                logger.info("AI advisor initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize AI advisor: {e}")
                logger.warning("Continuing without AI...")
        
        # 5. 创建策略
        logger.info(f"Creating strategy: {args.strategy}")
        
        strategy_params = config.get('strategy.parameters', {})
        strategy_func = get_strategy(
            args.strategy,
            risk_manager=risk_manager,
            ai_advisor=ai_advisor,
            **strategy_params
        )
        
        # 6. 启动模拟盘
        logger.info("Starting simulation...")
        controller.start(args.start_date, args.end_date, [args.symbol])
        
        # 7. 运行策略
        logger.info("Running strategy...")
        controller.run(strategy_func, [args.symbol])
        
        # 8. 生成报告
        logger.info("\nGenerating performance report...")
        print("\n" + "=" * 60)
        
        report = PerformanceAnalyzer.generate_report(
            controller.account_id,
            args.db_path or config.database_path
        )
        
        print(report)
        
        # 保存报告
        os.makedirs(args.output_dir, exist_ok=True)
        report_path = os.path.join(args.output_dir, f"report_{controller.account_id}.txt")
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"Report saved to: {report_path}")
        
        print("\n" + "=" * 60)
        print("Simulation completed successfully!")
        print("=" * 60)
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("\nInterrupted by user")
        return 130
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
