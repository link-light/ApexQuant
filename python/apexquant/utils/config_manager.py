"""
策略参数持久化模块

提供策略配置的保存、加载和管理功能
支持 JSON 和 SQLite 两种存储方式
"""

import json
import sqlite3
import os
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class StrategyConfig:
    """策略配置"""
    name: str
    strategy_type: str
    parameters: Dict[str, Any]
    created_at: str
    updated_at: str
    description: str = ""
    version: str = "1.0"
    is_active: bool = True


class ConfigManager:
    """配置管理器 - JSON 存储"""

    def __init__(self, config_dir: str = "configs"):
        """
        初始化配置管理器

        Args:
            config_dir: 配置文件目录
        """
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"[ConfigManager] Initialized with directory: {self.config_dir}")

    def save_strategy_config(
        self,
        name: str,
        strategy_type: str,
        parameters: Dict[str, Any],
        description: str = "",
        overwrite: bool = False
    ) -> bool:
        """
        保存策略配置

        Args:
            name: 配置名称
            strategy_type: 策略类型
            parameters: 策略参数
            description: 描述
            overwrite: 是否覆盖已存在的配置

        Returns:
            bool: 是否成功
        """
        config_file = self.config_dir / f"{name}.json"

        # 检查是否已存在
        if config_file.exists() and not overwrite:
            logger.warning(f"[ConfigManager] Config '{name}' already exists. Use overwrite=True to replace.")
            return False

        # 创建配置对象
        now = datetime.now().isoformat()
        config = StrategyConfig(
            name=name,
            strategy_type=strategy_type,
            parameters=parameters,
            created_at=now if not config_file.exists() else self._get_created_time(config_file),
            updated_at=now,
            description=description
        )

        try:
            # 保存为 JSON
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(config), f, indent=2, ensure_ascii=False)

            logger.info(f"[ConfigManager] Saved config '{name}' to {config_file}")
            return True

        except Exception as e:
            logger.error(f"[ConfigManager] Failed to save config '{name}': {e}")
            return False

    def load_strategy_config(self, name: str) -> Optional[StrategyConfig]:
        """
        加载策略配置

        Args:
            name: 配置名称

        Returns:
            StrategyConfig: 配置对象，如果不存在返回 None
        """
        config_file = self.config_dir / f"{name}.json"

        if not config_file.exists():
            logger.warning(f"[ConfigManager] Config '{name}' not found")
            return None

        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            config = StrategyConfig(**data)
            logger.info(f"[ConfigManager] Loaded config '{name}'")
            return config

        except Exception as e:
            logger.error(f"[ConfigManager] Failed to load config '{name}': {e}")
            return None

    def list_configs(self, strategy_type: Optional[str] = None) -> List[str]:
        """
        列出所有配置

        Args:
            strategy_type: 过滤策略类型

        Returns:
            List[str]: 配置名称列表
        """
        configs = []

        for config_file in self.config_dir.glob("*.json"):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                if strategy_type is None or data.get('strategy_type') == strategy_type:
                    configs.append(config_file.stem)

            except Exception as e:
                logger.warning(f"[ConfigManager] Failed to read {config_file}: {e}")

        return sorted(configs)

    def delete_config(self, name: str) -> bool:
        """
        删除配置

        Args:
            name: 配置名称

        Returns:
            bool: 是否成功
        """
        config_file = self.config_dir / f"{name}.json"

        if not config_file.exists():
            logger.warning(f"[ConfigManager] Config '{name}' not found")
            return False

        try:
            config_file.unlink()
            logger.info(f"[ConfigManager] Deleted config '{name}'")
            return True

        except Exception as e:
            logger.error(f"[ConfigManager] Failed to delete config '{name}': {e}")
            return False

    def export_config(self, name: str, export_path: str) -> bool:
        """
        导出配置到指定路径

        Args:
            name: 配置名称
            export_path: 导出路径

        Returns:
            bool: 是否成功
        """
        config = self.load_strategy_config(name)
        if config is None:
            return False

        try:
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(asdict(config), f, indent=2, ensure_ascii=False)

            logger.info(f"[ConfigManager] Exported config '{name}' to {export_path}")
            return True

        except Exception as e:
            logger.error(f"[ConfigManager] Failed to export config '{name}': {e}")
            return False

    def import_config(self, import_path: str, name: Optional[str] = None) -> bool:
        """
        从文件导入配置

        Args:
            import_path: 导入路径
            name: 新配置名称（如果为 None，使用原名称）

        Returns:
            bool: 是否成功
        """
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            config = StrategyConfig(**data)

            if name:
                config.name = name

            return self.save_strategy_config(
                name=config.name,
                strategy_type=config.strategy_type,
                parameters=config.parameters,
                description=config.description,
                overwrite=True
            )

        except Exception as e:
            logger.error(f"[ConfigManager] Failed to import config from {import_path}: {e}")
            return False

    def _get_created_time(self, config_file: Path) -> str:
        """获取配置创建时间"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data.get('created_at', datetime.now().isoformat())
        except:
            return datetime.now().isoformat()


class SQLiteConfigManager:
    """配置管理器 - SQLite 存储"""

    def __init__(self, db_path: str = "configs/strategy_configs.db"):
        """
        初始化 SQLite 配置管理器

        Args:
            db_path: 数据库文件路径
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
        logger.info(f"[SQLiteConfigManager] Initialized with database: {self.db_path}")

    def _init_database(self):
        """初始化数据库表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS strategy_configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                strategy_type TEXT NOT NULL,
                parameters TEXT NOT NULL,
                description TEXT,
                version TEXT DEFAULT '1.0',
                is_active INTEGER DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        conn.commit()
        conn.close()

    def save_strategy_config(
        self,
        name: str,
        strategy_type: str,
        parameters: Dict[str, Any],
        description: str = "",
        overwrite: bool = False
    ) -> bool:
        """
        保存策略配置到数据库

        Args:
            name: 配置名称
            strategy_type: 策略类型
            parameters: 策略参数
            description: 描述
            overwrite: 是否覆盖已存在的配置

        Returns:
            bool: 是否成功
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            now = datetime.now().isoformat()
            params_json = json.dumps(parameters, ensure_ascii=False)

            # 检查是否已存在
            cursor.execute("SELECT id, created_at FROM strategy_configs WHERE name = ?", (name,))
            existing = cursor.fetchone()

            if existing and not overwrite:
                logger.warning(f"[SQLiteConfigManager] Config '{name}' already exists")
                conn.close()
                return False

            if existing:
                # 更新
                cursor.execute("""
                    UPDATE strategy_configs
                    SET strategy_type = ?, parameters = ?, description = ?, updated_at = ?
                    WHERE name = ?
                """, (strategy_type, params_json, description, now, name))
            else:
                # 插入
                cursor.execute("""
                    INSERT INTO strategy_configs (name, strategy_type, parameters, description, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (name, strategy_type, params_json, description, now, now))

            conn.commit()
            logger.info(f"[SQLiteConfigManager] Saved config '{name}'")
            return True

        except Exception as e:
            logger.error(f"[SQLiteConfigManager] Failed to save config '{name}': {e}")
            conn.rollback()
            return False

        finally:
            conn.close()

    def load_strategy_config(self, name: str) -> Optional[StrategyConfig]:
        """
        从数据库加载策略配置

        Args:
            name: 配置名称

        Returns:
            StrategyConfig: 配置对象
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT name, strategy_type, parameters, description, version, is_active, created_at, updated_at
                FROM strategy_configs
                WHERE name = ?
            """, (name,))

            row = cursor.fetchone()

            if row is None:
                logger.warning(f"[SQLiteConfigManager] Config '{name}' not found")
                return None

            config = StrategyConfig(
                name=row[0],
                strategy_type=row[1],
                parameters=json.loads(row[2]),
                description=row[3],
                version=row[4],
                is_active=bool(row[5]),
                created_at=row[6],
                updated_at=row[7]
            )

            logger.info(f"[SQLiteConfigManager] Loaded config '{name}'")
            return config

        except Exception as e:
            logger.error(f"[SQLiteConfigManager] Failed to load config '{name}': {e}")
            return None

        finally:
            conn.close()

    def list_configs(self, strategy_type: Optional[str] = None, active_only: bool = False) -> List[str]:
        """
        列出所有配置

        Args:
            strategy_type: 过滤策略类型
            active_only: 只列出激活的配置

        Returns:
            List[str]: 配置名称列表
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            query = "SELECT name FROM strategy_configs WHERE 1=1"
            params = []

            if strategy_type:
                query += " AND strategy_type = ?"
                params.append(strategy_type)

            if active_only:
                query += " AND is_active = 1"

            query += " ORDER BY updated_at DESC"

            cursor.execute(query, params)
            configs = [row[0] for row in cursor.fetchall()]

            return configs

        except Exception as e:
            logger.error(f"[SQLiteConfigManager] Failed to list configs: {e}")
            return []

        finally:
            conn.close()

    def delete_config(self, name: str) -> bool:
        """
        删除配置

        Args:
            name: 配置名称

        Returns:
            bool: 是否成功
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("DELETE FROM strategy_configs WHERE name = ?", (name,))
            conn.commit()

            if cursor.rowcount > 0:
                logger.info(f"[SQLiteConfigManager] Deleted config '{name}'")
                return True
            else:
                logger.warning(f"[SQLiteConfigManager] Config '{name}' not found")
                return False

        except Exception as e:
            logger.error(f"[SQLiteConfigManager] Failed to delete config '{name}': {e}")
            conn.rollback()
            return False

        finally:
            conn.close()

    def set_active(self, name: str, is_active: bool) -> bool:
        """
        设置配置激活状态

        Args:
            name: 配置名称
            is_active: 是否激活

        Returns:
            bool: 是否成功
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                UPDATE strategy_configs
                SET is_active = ?, updated_at = ?
                WHERE name = ?
            """, (int(is_active), datetime.now().isoformat(), name))

            conn.commit()

            if cursor.rowcount > 0:
                logger.info(f"[SQLiteConfigManager] Set config '{name}' active={is_active}")
                return True
            else:
                logger.warning(f"[SQLiteConfigManager] Config '{name}' not found")
                return False

        except Exception as e:
            logger.error(f"[SQLiteConfigManager] Failed to set active for '{name}': {e}")
            conn.rollback()
            return False

        finally:
            conn.close()


# 便捷函数
def save_config(name: str, strategy_type: str, parameters: Dict[str, Any], **kwargs) -> bool:
    """
    保存策略配置（使用 JSON 存储）

    Args:
        name: 配置名称
        strategy_type: 策略类型
        parameters: 策略参数
        **kwargs: 其他参数

    Returns:
        bool: 是否成功
    """
    manager = ConfigManager()
    return manager.save_strategy_config(name, strategy_type, parameters, **kwargs)


def load_config(name: str) -> Optional[StrategyConfig]:
    """
    加载策略配置（使用 JSON 存储）

    Args:
        name: 配置名称

    Returns:
        StrategyConfig: 配置对象
    """
    manager = ConfigManager()
    return manager.load_strategy_config(name)
