"""
ApexQuant Simulation Runner
模拟盘运行脚本（项目根目录运行）
"""

import os
import sys
from pathlib import Path

# 设置路径
project_root = Path(__file__).parent
python_path = project_root / "python"
sys.path.insert(0, str(python_path))

# 切换工作目录
os.chdir(str(python_path / "apexquant"))

# 导入CLI模块
from simulation.cli import main

if __name__ == "__main__":
    sys.exit(main())
