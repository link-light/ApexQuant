"""
数据库备份功能扩展模块

为DatabaseManager添加备份、恢复和清理功能
"""

import shutil
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)


class DatabaseBackupMixin:
    """数据库备份功能混入类"""
    
    def backup(self, backup_name: Optional[str] = None) -> Optional[str]:
        """
        创建数据库备份
        
        Args:
            backup_name: 备份文件名，不提供则自动生成
            
        Returns:
            备份文件路径，如果失败返回None
        """
        try:
            # 检查数据库文件是否存在
            if not self.db_path.exists():
                logger.warning(f"Database file not found: {self.db_path}")
                return None
            
            # 生成备份文件名
            if backup_name is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_name = f"{self.db_path.stem}_{timestamp}.db"
            
            backup_path = self.backup_dir / backup_name
            
            # 创建备份
            shutil.copy2(self.db_path, backup_path)
            
            logger.info(f"Database backed up to: {backup_path}")
            logger.info(f"Backup size: {backup_path.stat().st_size / 1024:.2f} KB")
            
            # 清理旧备份
            self._cleanup_old_backups(days=7)
            
            return str(backup_path)
            
        except Exception as e:
            logger.error(f"Failed to backup database: {e}")
            return None
    
    def _cleanup_old_backups(self, days: int = 7):
        """
        清理旧备份文件
        
        Args:
            days: 保留最近几天的备份
        """
        try:
            cutoff = datetime.now() - timedelta(days=days)
            cleaned_count = 0
            
            for backup_file in self.backup_dir.glob('*.db'):
                try:
                    # 从文件名解析时间戳
                    # 格式: sim_trader_20260206_120000.db
                    parts = backup_file.stem.split('_')
                    if len(parts) >= 3:
                        date_str = parts[-2]  # 日期部分
                        time_str = parts[-1]  # 时间部分
                        
                        file_time = datetime.strptime(
                            f"{date_str}_{time_str}", 
                            '%Y%m%d_%H%M%S'
                        )
                        
                        if file_time < cutoff:
                            backup_file.unlink()
                            cleaned_count += 1
                            logger.debug(f"Removed old backup: {backup_file.name}")
                            
                except (ValueError, IndexError) as e:
                    # 无法解析文件名，跳过
                    logger.debug(f"Skip cleanup for {backup_file.name}: {e}")
                    continue
            
            if cleaned_count > 0:
                logger.info(f"Cleaned up {cleaned_count} old backup(s)")
                
        except Exception as e:
            logger.error(f"Failed to cleanup old backups: {e}")
    
    def auto_backup_on_start(self):
        """启动时自动备份（每天首次启动时）"""
        try:
            # 获取最后备份日期
            last_backup_date = self._get_last_backup_date()
            today = datetime.now().date()
            
            # 如果今天还没备份过，则创建备份
            if last_backup_date is None or last_backup_date < today:
                logger.info("Performing daily auto-backup...")
                backup_path = self.backup()
                if backup_path:
                    logger.info("Daily backup completed successfully")
                else:
                    logger.warning("Daily backup failed")
            else:
                logger.debug(f"Already backed up today ({last_backup_date})")
                
        except Exception as e:
            logger.error(f"Auto backup failed: {e}")
    
    def _get_last_backup_date(self) -> Optional[datetime.date]:
        """
        获取最后备份日期
        
        Returns:
            最后备份的日期，如果没有备份返回None
        """
        try:
            # 获取所有备份文件并按时间排序
            backups = sorted(self.backup_dir.glob('*.db'), reverse=True)
            
            if not backups:
                return None
            
            # 从最新备份文件名解析日期
            latest_backup = backups[0]
            parts = latest_backup.stem.split('_')
            
            if len(parts) >= 3:
                date_str = parts[-2]
                time_str = parts[-1]
                
                file_time = datetime.strptime(
                    f"{date_str}_{time_str}", 
                    '%Y%m%d_%H%M%S'
                )
                return file_time.date()
                
        except Exception as e:
            logger.debug(f"Failed to get last backup date: {e}")
        
        return None
    
    def list_backups(self) -> List[Dict[str, any]]:
        """
        列出所有备份文件
        
        Returns:
            备份文件信息列表
        """
        backups = []
        
        try:
            for backup_file in sorted(self.backup_dir.glob('*.db'), reverse=True):
                stat = backup_file.stat()
                
                backups.append({
                    'name': backup_file.name,
                    'path': str(backup_file),
                    'size': stat.st_size,
                    'created': datetime.fromtimestamp(stat.st_ctime),
                    'modified': datetime.fromtimestamp(stat.st_mtime)
                })
                
        except Exception as e:
            logger.error(f"Failed to list backups: {e}")
        
        return backups
    
    def restore_backup(self, backup_path: str) -> bool:
        """
        从备份恢复数据库
        
        Args:
            backup_path: 备份文件路径
            
        Returns:
            是否成功
        """
        try:
            backup_file = Path(backup_path)
            
            if not backup_file.exists():
                logger.error(f"Backup file not found: {backup_path}")
                return False
            
            # 关闭当前连接
            self.close()
            
            # 备份当前数据库（以防恢复失败）
            if self.db_path.exists():
                emergency_backup = self.db_path.parent / f"{self.db_path.stem}_before_restore.db"
                shutil.copy2(self.db_path, emergency_backup)
                logger.info(f"Created emergency backup: {emergency_backup}")
            
            # 恢复备份
            shutil.copy2(backup_file, self.db_path)
            
            # 重新初始化连接
            self.init_database()
            
            logger.info(f"Database restored from: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to restore backup: {e}")
            return False

