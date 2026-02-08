"""
深度学习模型缓存模块

提供模型的保存、加载和缓存管理功能
避免重复训练，提升性能
"""

import os
import pickle
import hashlib
import json
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class ModelCache:
    """模型缓存管理器"""

    def __init__(self, cache_dir: str = "model_cache", max_age_days: int = 30):
        """
        初始化模型缓存管理器

        Args:
            cache_dir: 缓存目录
            max_age_days: 缓存最大保留天数
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_age_days = max_age_days
        self.metadata_file = self.cache_dir / "cache_metadata.json"
        self._load_metadata()
        logger.info(f"[ModelCache] Initialized with directory: {self.cache_dir}")

    def _load_metadata(self):
        """加载缓存元数据"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    self.metadata = json.load(f)
            except Exception as e:
                logger.warning(f"[ModelCache] Failed to load metadata: {e}")
                self.metadata = {}
        else:
            self.metadata = {}

    def _save_metadata(self):
        """保存缓存元数据"""
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"[ModelCache] Failed to save metadata: {e}")

    def _generate_cache_key(
        self,
        model_type: str,
        symbol: str,
        data_hash: str,
        params: Dict[str, Any]
    ) -> str:
        """
        生成缓存键

        Args:
            model_type: 模型类型
            symbol: 股票代码
            data_hash: 数据哈希
            params: 模型参数

        Returns:
            str: 缓存键
        """
        # 将参数转换为字符串并排序
        params_str = json.dumps(params, sort_keys=True)

        # 生成哈希
        key_str = f"{model_type}_{symbol}_{data_hash}_{params_str}"
        cache_key = hashlib.md5(key_str.encode()).hexdigest()

        return cache_key

    def _compute_data_hash(self, data: Any) -> str:
        """
        计算数据哈希

        Args:
            data: 数据（DataFrame 或其他）

        Returns:
            str: 数据哈希
        """
        try:
            import pandas as pd
            if isinstance(data, pd.DataFrame):
                # 使用数据的形状和前后几行来生成哈希
                shape_str = str(data.shape)
                head_str = str(data.head(5).values.tobytes())
                tail_str = str(data.tail(5).values.tobytes())
                hash_str = f"{shape_str}_{head_str}_{tail_str}"
            else:
                hash_str = str(data)

            return hashlib.md5(hash_str.encode()).hexdigest()[:16]

        except Exception as e:
            logger.warning(f"[ModelCache] Failed to compute data hash: {e}")
            return "unknown"

    def save_model(
        self,
        model: Any,
        model_type: str,
        symbol: str,
        data: Any,
        params: Dict[str, Any],
        metrics: Optional[Dict[str, float]] = None,
        framework: str = "pytorch"
    ) -> bool:
        """
        保存模型到缓存

        Args:
            model: 模型对象
            model_type: 模型类型 (lstm, gru, etc.)
            symbol: 股票代码
            data: 训练数据
            params: 模型参数
            metrics: 训练指标
            framework: 框架类型 (pytorch, sklearn, etc.)

        Returns:
            bool: 是否成功
        """
        try:
            # 生成缓存键
            data_hash = self._compute_data_hash(data)
            cache_key = self._generate_cache_key(model_type, symbol, data_hash, params)

            # 保存模型
            model_file = self.cache_dir / f"{cache_key}.pkl"

            if framework == "pytorch":
                # PyTorch 模型
                try:
                    import torch
                    torch.save(model.state_dict(), model_file)
                except ImportError:
                    # 如果没有 PyTorch，使用 pickle
                    with open(model_file, 'wb') as f:
                        pickle.dump(model, f)
            else:
                # 其他框架使用 pickle
                with open(model_file, 'wb') as f:
                    pickle.dump(model, f)

            # 保存元数据
            self.metadata[cache_key] = {
                'model_type': model_type,
                'symbol': symbol,
                'data_hash': data_hash,
                'params': params,
                'metrics': metrics or {},
                'framework': framework,
                'created_at': datetime.now().isoformat(),
                'file_path': str(model_file)
            }

            self._save_metadata()

            logger.info(f"[ModelCache] Saved model: {model_type} for {symbol} (key: {cache_key})")
            return True

        except Exception as e:
            logger.error(f"[ModelCache] Failed to save model: {e}")
            return False

    def load_model(
        self,
        model_type: str,
        symbol: str,
        data: Any,
        params: Dict[str, Any],
        model_class: Optional[Any] = None
    ) -> Optional[Tuple[Any, Dict[str, Any]]]:
        """
        从缓存加载模型

        Args:
            model_type: 模型类型
            symbol: 股票代码
            data: 训练数据（用于生成哈希）
            params: 模型参数
            model_class: 模型类（PyTorch 需要）

        Returns:
            Tuple[model, metadata]: 模型对象和元数据，如果不存在返回 None
        """
        try:
            # 生成缓存键
            data_hash = self._compute_data_hash(data)
            cache_key = self._generate_cache_key(model_type, symbol, data_hash, params)

            # 检查缓存是否存在
            if cache_key not in self.metadata:
                logger.info(f"[ModelCache] Cache miss for {model_type}/{symbol}")
                return None

            metadata = self.metadata[cache_key]

            # 检查缓存是否过期
            created_at = datetime.fromisoformat(metadata['created_at'])
            age_days = (datetime.now() - created_at).days

            if age_days > self.max_age_days:
                logger.info(f"[ModelCache] Cache expired for {model_type}/{symbol} (age: {age_days} days)")
                self.delete_cache(cache_key)
                return None

            # 加载模型
            model_file = Path(metadata['file_path'])

            if not model_file.exists():
                logger.warning(f"[ModelCache] Model file not found: {model_file}")
                del self.metadata[cache_key]
                self._save_metadata()
                return None

            framework = metadata.get('framework', 'pytorch')

            if framework == "pytorch":
                try:
                    import torch
                    if model_class is None:
                        logger.error("[ModelCache] model_class required for PyTorch models")
                        return None

                    model = model_class(**params)
                    model.load_state_dict(torch.load(model_file))
                    model.eval()
                except ImportError:
                    # 回退到 pickle
                    with open(model_file, 'rb') as f:
                        model = pickle.load(f)
            else:
                with open(model_file, 'rb') as f:
                    model = pickle.load(f)

            logger.info(f"[ModelCache] Cache hit for {model_type}/{symbol} (age: {age_days} days)")
            return model, metadata

        except Exception as e:
            logger.error(f"[ModelCache] Failed to load model: {e}")
            return None

    def delete_cache(self, cache_key: str) -> bool:
        """
        删除指定缓存

        Args:
            cache_key: 缓存键

        Returns:
            bool: 是否成功
        """
        try:
            if cache_key in self.metadata:
                model_file = Path(self.metadata[cache_key]['file_path'])
                if model_file.exists():
                    model_file.unlink()

                del self.metadata[cache_key]
                self._save_metadata()

                logger.info(f"[ModelCache] Deleted cache: {cache_key}")
                return True
            else:
                logger.warning(f"[ModelCache] Cache not found: {cache_key}")
                return False

        except Exception as e:
            logger.error(f"[ModelCache] Failed to delete cache: {e}")
            return False

    def clear_expired_cache(self) -> int:
        """
        清理过期缓存

        Returns:
            int: 清理的缓存数量
        """
        cleared_count = 0
        expired_keys = []

        for cache_key, metadata in self.metadata.items():
            try:
                created_at = datetime.fromisoformat(metadata['created_at'])
                age_days = (datetime.now() - created_at).days

                if age_days > self.max_age_days:
                    expired_keys.append(cache_key)

            except Exception as e:
                logger.warning(f"[ModelCache] Error checking cache {cache_key}: {e}")

        for cache_key in expired_keys:
            if self.delete_cache(cache_key):
                cleared_count += 1

        logger.info(f"[ModelCache] Cleared {cleared_count} expired caches")
        return cleared_count

    def clear_all_cache(self) -> int:
        """
        清理所有缓存

        Returns:
            int: 清理的缓存数量
        """
        cleared_count = 0
        all_keys = list(self.metadata.keys())

        for cache_key in all_keys:
            if self.delete_cache(cache_key):
                cleared_count += 1

        logger.info(f"[ModelCache] Cleared all {cleared_count} caches")
        return cleared_count

    def get_cache_info(self) -> Dict[str, Any]:
        """
        获取缓存信息

        Returns:
            Dict: 缓存统计信息
        """
        total_count = len(self.metadata)
        total_size = 0
        expired_count = 0

        for metadata in self.metadata.values():
            try:
                model_file = Path(metadata['file_path'])
                if model_file.exists():
                    total_size += model_file.stat().st_size

                created_at = datetime.fromisoformat(metadata['created_at'])
                age_days = (datetime.now() - created_at).days

                if age_days > self.max_age_days:
                    expired_count += 1

            except Exception:
                pass

        return {
            'total_count': total_count,
            'expired_count': expired_count,
            'total_size_mb': total_size / (1024 * 1024),
            'cache_dir': str(self.cache_dir),
            'max_age_days': self.max_age_days
        }

    def list_cached_models(self, symbol: Optional[str] = None) -> list:
        """
        列出缓存的模型

        Args:
            symbol: 过滤股票代码

        Returns:
            list: 模型信息列表
        """
        models = []

        for cache_key, metadata in self.metadata.items():
            if symbol is None or metadata.get('symbol') == symbol:
                created_at = datetime.fromisoformat(metadata['created_at'])
                age_days = (datetime.now() - created_at).days

                models.append({
                    'cache_key': cache_key,
                    'model_type': metadata.get('model_type'),
                    'symbol': metadata.get('symbol'),
                    'age_days': age_days,
                    'metrics': metadata.get('metrics', {}),
                    'created_at': metadata.get('created_at')
                })

        return sorted(models, key=lambda x: x['created_at'], reverse=True)


# 全局缓存实例
_global_cache = None


def get_model_cache() -> ModelCache:
    """获取全局模型缓存实例"""
    global _global_cache
    if _global_cache is None:
        _global_cache = ModelCache()
    return _global_cache


def save_model(model: Any, model_type: str, symbol: str, data: Any, params: Dict[str, Any], **kwargs) -> bool:
    """
    便捷函数：保存模型到缓存

    Args:
        model: 模型对象
        model_type: 模型类型
        symbol: 股票代码
        data: 训练数据
        params: 模型参数
        **kwargs: 其他参数

    Returns:
        bool: 是否成功
    """
    cache = get_model_cache()
    return cache.save_model(model, model_type, symbol, data, params, **kwargs)


def load_model(model_type: str, symbol: str, data: Any, params: Dict[str, Any], **kwargs) -> Optional[Tuple[Any, Dict]]:
    """
    便捷函数：从缓存加载模型

    Args:
        model_type: 模型类型
        symbol: 股票代码
        data: 训练数据
        params: 模型参数
        **kwargs: 其他参数

    Returns:
        Tuple[model, metadata]: 模型和元数据
    """
    cache = get_model_cache()
    return cache.load_model(model_type, symbol, data, params, **kwargs)
