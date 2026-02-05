"""
ApexQuant 模拟盘配置管理模块

提供统一的配置加载和访问接口
"""

import yaml
import os
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class SimulationConfig:
    """模拟盘配置管理类"""
    
    def __init__(self, config_path: str = "config/simulation_config.yaml"):
        """
        初始化配置
        
        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self.config: Dict[str, Any] = {}
        self.load_config()
    
    def load_config(self):
        """加载配置文件"""
        try:
            if not os.path.exists(self.config_path):
                logger.warning(f"Config file not found: {self.config_path}, using defaults")
                self.config = self._get_default_config()
                return
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
            
            logger.info(f"Config loaded from: {self.config_path}")
            
            # 验证配置
            if not self.validate_config():
                logger.warning("Config validation failed, some settings may be incorrect")
                
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            self.config = self._get_default_config()
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        获取配置项（支持点号分隔的路径）
        
        Args:
            key_path: 配置键路径，如 'risk.max_single_position_pct'
            default: 默认值
            
        Returns:
            配置值
        """
        keys = key_path.split('.')
        value = self.config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def get_trading_config(self) -> Dict:
        """获取交易配置"""
        return self.get('trading', {})
    
    def get_risk_config(self) -> Dict:
        """获取风控配置"""
        return self.get('risk', {})
    
    def get_ai_config(self) -> Dict:
        """
        获取AI配置
        
        特别处理：从环境变量读取API Key
        """
        ai_config = self.get('ai', {}).copy()
        
        # 从环境变量读取API Key
        api_key_env = ai_config.get('api_key_env', 'DEEPSEEK_API_KEY')
        api_key = os.getenv(api_key_env)
        
        if api_key:
            ai_config['api_key'] = api_key
        else:
            logger.warning(f"API Key not found in environment variable: {api_key_env}")
            ai_config['api_key'] = None
        
        return ai_config
    
    def get_data_source_config(self) -> Dict:
        """获取数据源配置"""
        return self.get('data_source', {})
    
    def get_logging_config(self) -> Dict:
        """获取日志配置"""
        return self.get('logging', {})
    
    def get_strategy_config(self) -> Dict:
        """获取策略配置"""
        return self.get('strategy', {})
    
    # ========================================================================
    # 常用配置项的快捷访问（property）
    # ========================================================================
    
    @property
    def initial_capital(self) -> float:
        """初始资金"""
        return self.get('simulation.initial_capital', 1000000.0)
    
    @property
    def database_path(self) -> str:
        """数据库路径"""
        return self.get('simulation.database_path', 'data/sim_trader.db')
    
    @property
    def commission_rate(self) -> float:
        """手续费率"""
        return self.get('trading.commission_rate', 0.00025)
    
    @property
    def slippage_rate(self) -> float:
        """滑点率"""
        return self.get('trading.slippage_rate', 0.0001)
    
    @property
    def max_single_position_pct(self) -> float:
        """单品种最大仓位"""
        return self.get('risk.max_single_position_pct', 0.20)
    
    @property
    def max_total_position_pct(self) -> float:
        """总仓位上限"""
        return self.get('risk.max_total_position_pct', 0.80)
    
    @property
    def ai_enabled(self) -> bool:
        """AI是否启用"""
        return self.get('ai.enabled', False)
    
    @property
    def data_provider(self) -> str:
        """数据提供商"""
        return self.get('data_source.provider', 'baostock')
    
    @property
    def log_level(self) -> str:
        """日志级别"""
        return self.get('logging.level', 'INFO')
    
    # ========================================================================
    # 配置验证
    # ========================================================================
    
    def validate_config(self) -> bool:
        """
        验证配置合法性
        
        Returns:
            是否验证通过
        """
        valid = True
        
        # 检查百分比值在0-1之间
        pct_keys = [
            'risk.max_single_position_pct',
            'risk.max_total_position_pct',
            'risk.max_single_order_pct',
            'risk.max_daily_loss_pct',
            'risk.stop_loss_pct',
            'risk.take_profit_pct',
        ]
        
        for key in pct_keys:
            value = self.get(key)
            if value is not None and (value < 0 or value > 1):
                logger.error(f"Invalid percentage value for {key}: {value}")
                valid = False
        
        # 检查初始资金为正
        if self.initial_capital <= 0:
            logger.error(f"Initial capital must be positive: {self.initial_capital}")
            valid = False
        
        # 检查数据源
        provider = self.data_provider
        if provider not in ['baostock', 'akshare', 'mock']:
            logger.warning(f"Unknown data provider: {provider}")
        
        return valid
    
    # ========================================================================
    # 默认配置
    # ========================================================================
    
    @staticmethod
    def _get_default_config() -> Dict:
        """获取默认配置"""
        return {
            'simulation': {
                'mode': 'backtest',
                'initial_capital': 1000000,
                'database_path': 'data/sim_trader.db'
            },
            'trading': {
                'commission_rate': 0.00025,
                'stamp_tax_rate': 0.001,
                'slippage_rate': 0.0001,
                'min_order_volume': 100
            },
            'risk': {
                'max_single_position_pct': 0.20,
                'max_total_position_pct': 0.80,
                'max_single_order_pct': 0.05,
                'max_daily_loss_pct': 0.05,
                'stop_loss_pct': 0.10,
                'take_profit_pct': 0.20,
                'max_daily_trades': 100,
                'min_hold_seconds': 60
            },
            'ai': {
                'enabled': False,
                'api_key_env': 'DEEPSEEK_API_KEY',
                'model': 'deepseek-chat',
                'base_url': 'https://api.deepseek.com',
                'call_interval_minutes': 5,
                'daily_call_limit': 100,
                'confidence_threshold': 0.7,
                'timeout': 10
            },
            'data_source': {
                'provider': 'baostock',
                'backup_provider': 'akshare',
                'frequency': '1min',
                'cache_enabled': True,
                'cache_dir': 'data/cache',
                'retry_times': 3,
                'retry_interval': 1
            },
            'logging': {
                'level': 'INFO',
                'file': 'logs/simulation.log',
                'console': True,
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                'max_bytes': 10485760,
                'backup_count': 5
            },
            'strategy': {
                'name': 'ma_cross',
                'parameters': {
                    'ma_short': 5,
                    'ma_long': 20,
                    'rsi_period': 14,
                    'buy_threshold': 30,
                    'sell_threshold': 70
                }
            }
        }


# ============================================================================
# 全局配置实例（单例模式）
# ============================================================================

_config: Optional[SimulationConfig] = None


def get_config(config_path: Optional[str] = None) -> SimulationConfig:
    """
    获取全局配置实例（单例）
    
    Args:
        config_path: 配置文件路径（仅首次调用有效）
        
    Returns:
        SimulationConfig实例
    """
    global _config
    
    if _config is None:
        if config_path is None:
            config_path = "config/simulation_config.yaml"
        _config = SimulationConfig(config_path)
    
    return _config


def reset_config():
    """重置全局配置（主要用于测试）"""
    global _config
    _config = None


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 60)
    print("ApexQuant Config Test")
    print("=" * 60)
    
    config = get_config()
    
    print(f"\nInitial capital: {config.initial_capital}")
    print(f"Database path: {config.database_path}")
    print(f"Commission rate: {config.commission_rate}")
    print(f"Max single position: {config.max_single_position_pct * 100}%")
    print(f"AI enabled: {config.ai_enabled}")
    print(f"Data provider: {config.data_provider}")
    
    print("\nRisk config:")
    risk_config = config.get_risk_config()
    for key, value in risk_config.items():
        print(f"  {key}: {value}")
    
    print("\nStrategy config:")
    strategy_config = config.get_strategy_config()
    print(f"  name: {strategy_config.get('name')}")
    print(f"  parameters: {strategy_config.get('parameters')}")
    
    print("\nValidation result:", config.validate_config())
    
    print("\n" + "=" * 60)
    print("[OK] Config test passed!")
    print("=" * 60)
