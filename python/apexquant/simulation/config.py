"""
ApexQuant Simulation Configuration Manager
配置文件管理器
"""

import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class SimulationConfig:
    """模拟盘配置管理器"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置管理器
        
        Args:
            config_path: 配置文件路径，默认为 config/simulation_config.yaml
        """
        if config_path is None:
            # 默认配置文件路径
            project_root = Path(__file__).parent.parent.parent.parent
            config_path = project_root / "config" / "simulation_config.yaml"
        
        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = {}
        
        # 加载配置
        self.load_config()
    
    def load_config(self) -> None:
        """加载配置文件"""
        if not self.config_path.exists():
            logger.warning(f"Config file not found: {self.config_path}, using default config")
            self.config = self._get_default_config()
            # 创建默认配置文件
            self.save_config()
        else:
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.config = yaml.safe_load(f)
                logger.info(f"Config loaded from {self.config_path}")
            except Exception as e:
                logger.error(f"Failed to load config: {e}, using default config")
                self.config = self._get_default_config()
    
    def save_config(self) -> None:
        """保存配置到文件"""
        try:
            # 确保目录存在
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, allow_unicode=True, default_flow_style=False)
            logger.info(f"Config saved to {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            # 账户配置
            "account": {
                "account_id": "simulation_001",
                "initial_capital": 100000.0,  # 初始资金10万
                "commission_rate": 0.00025,   # 手续费万2.5
                "stamp_tax_rate": 0.001,      # 印花税千一（仅卖出）
                "slippage_rate": 0.0001,      # 滑点率万一
            },
            
            # 数据源配置
            "data_source": {
                "primary": "baostock",        # 主数据源
                "backup": "akshare",          # 备用数据源
                "proxy": None,                # 代理设置（None表示不使用）
            },
            
            # 交易时间配置
            "trading_hours": {
                "morning_start": "09:30",
                "morning_end": "11:30",
                "afternoon_start": "13:00",
                "afternoon_end": "15:00",
            },
            
            # 风控配置
            "risk_control": {
                "max_single_position_pct": 0.3,      # 单只股票最大仓位30%
                "max_total_position_pct": 0.95,      # 总仓位最大95%
                "max_single_order_amount": 50000.0,  # 单笔最大下单金额5万
                "daily_loss_limit_pct": 0.05,        # 日亏损限制5%
                "stop_loss_pct": 0.1,                # 止损比例10%
                "take_profit_pct": 0.2,              # 止盈比例20%
                "enable_risk_control": True,         # 是否启用风控
            },
            
            # AI顾问配置
            "ai_advisor": {
                "enabled": True,                     # 是否启用AI顾问
                "model": "deepseek-chat",            # 模型名称
                "api_key": "",                       # API密钥（需要用户填写）
                "base_url": "https://api.deepseek.com",
                "max_calls_per_day": 100,            # 每日最大调用次数
                "temperature": 0.7,                  # 温度参数
                "max_tokens": 2000,                  # 最大token数
            },
            
            # 回测配置
            "backtest": {
                "start_date": "2023-01-01",
                "end_date": "2024-12-31",
                "bar_interval": "1m",                # K线周期：1m, 5m, 15m, 30m, 1h, 1d
            },
            
            # 实时模拟配置
            "realtime": {
                "update_interval": 60,               # 数据更新间隔（秒）
                "auto_trade": False,                 # 是否自动交易
            },
            
            # 数据库配置
            "database": {
                "path": "data/simulation.db",        # SQLite数据库路径
                "auto_backup": True,                 # 是否自动备份
                "backup_interval": 3600,             # 备份间隔（秒）
            },
            
            # 日志配置
            "logging": {
                "level": "INFO",                     # 日志级别
                "file": "logs/simulation.log",       # 日志文件
                "max_size": "10MB",                  # 单个日志文件最大大小
                "backup_count": 5,                   # 保留日志文件数
            },
        }
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        获取配置项（支持点号分隔的路径）
        
        Args:
            key_path: 配置路径，如 "account.initial_capital"
            default: 默认值
            
        Returns:
            配置值
        """
        keys = key_path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def set(self, key_path: str, value: Any) -> None:
        """
        设置配置项
        
        Args:
            key_path: 配置路径
            value: 配置值
        """
        keys = key_path.split('.')
        config = self.config
        
        # 导航到最后一级
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        # 设置值
        config[keys[-1]] = value
        logger.debug(f"Config updated: {key_path} = {value}")
    
    def get_account_config(self) -> Dict[str, Any]:
        """获取账户配置"""
        return self.config.get("account", {})
    
    def get_risk_config(self) -> Dict[str, Any]:
        """获取风控配置"""
        return self.config.get("risk_control", {})
    
    def get_ai_config(self) -> Dict[str, Any]:
        """获取AI配置"""
        return self.config.get("ai_advisor", {})
    
    def get_data_source_config(self) -> Dict[str, Any]:
        """获取数据源配置"""
        return self.config.get("data_source", {})
    
    def validate(self) -> bool:
        """
        验证配置完整性
        
        Returns:
            True if valid, False otherwise
        """
        required_sections = [
            "account", "data_source", "risk_control", 
            "ai_advisor", "database"
        ]
        
        for section in required_sections:
            if section not in self.config:
                logger.error(f"Missing required config section: {section}")
                return False
        
        # 验证初始资金
        initial_capital = self.get("account.initial_capital", 0)
        if initial_capital <= 0:
            logger.error(f"Invalid initial_capital: {initial_capital}")
            return False
        
        # 验证费率
        commission_rate = self.get("account.commission_rate", 0)
        if commission_rate < 0 or commission_rate > 0.01:  # 费率不应超过1%
            logger.error(f"Invalid commission_rate: {commission_rate}")
            return False
        
        logger.info("Config validation passed")
        return True


# 全局配置实例
_global_config: Optional[SimulationConfig] = None


def get_config(config_path: Optional[str] = None) -> SimulationConfig:
    """
    获取全局配置实例（单例模式）
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        配置实例
    """
    global _global_config
    
    if _global_config is None or config_path is not None:
        _global_config = SimulationConfig(config_path)
    
    return _global_config
