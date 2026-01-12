# ApexQuant - AI 驱动的混合语言量化交易系统

<div align="center">

**高性能 C++ 引擎 × 智能 Python AI × 个人量化交易**

[![C++20](https://img.shields.io/badge/C++-20-blue.svg)](https://isocpp.org/)
[![Python](https://img.shields.io/badge/Python-3.9+-green.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

## 📋 项目简介

**ApexQuant** 是一个混合语言、高性能、AI 驱动的个人量化交易系统，专为对量化交易和金融市场有兴趣的开发者/投资者设计。

### 核心特点

- **🚀 混合架构**：C++ 负责高性能核心（回测引擎、实时行情处理、订单执行、风控检查），Python 负责 AI/ML 层
- **🔗 高效桥接**：使用 pybind11 实现 C++ 与 Python 双向调用
- **📊 数据丰富**：主要使用 AKShare、xtquant 等国内金融数据接口
- **🤖 AI 核心**：深度集成大语言模型（DeepSeek、Claude 3.5 Sonnet）
  - 智能选股与新闻情感分析
  - Prompt 驱动的策略生成与解释
  - 回测报告自动分析与改进建议
  - 动态风险评估与熔断判断
- **⚡ 高性能回测**：C++ 实现事件驱动 + 矢量化双模式，支持多线程并行
- **🧠 机器学习增强**：XGBoost/LightGBM 多因子模型 + RLlib 强化学习
- **📈 强大可视化**：Dear ImGui/ImPlot (C++) + Matplotlib/Plotly (Python)
- **💼 实盘能力**：对接 QMT/XTP/掘金 C++ SDK
- **🐳 容器化部署**：Docker + Prometheus + Grafana 监控

## 🏗️ 项目结构

```
ApexQuant/
├── CMakeLists.txt          # 主 CMake 配置
├── README.md               # 项目文档
├── .gitignore             # Git 忽略配置
│
├── cpp/                    # C++ 核心模块
│   ├── include/           # 头文件
│   │   ├── data_structures.h   # 核心数据结构
│   │   ├── utils.h            # 工具函数
│   │   ├── backtest_engine.h  # 回测引擎
│   │   └── market_data.h      # 行情处理
│   ├── src/               # 源文件
│   │   ├── data_structures.cpp
│   │   ├── utils.cpp
│   │   ├── bindings.cpp       # pybind11 绑定
│   │   └── backtest_engine.cpp
│   └── CMakeLists.txt     # C++ CMake 配置
│
├── python/                 # Python AI 模块
│   ├── apexquant/         # 主包
│   │   ├── __init__.py
│   │   ├── data/          # 数据获取层
│   │   ├── ai/            # AI 模型层
│   │   ├── strategy/      # 策略层
│   │   └── visualization/ # 可视化层
│   ├── tests/             # 测试
│   └── requirements.txt   # Python 依赖
│
├── data/                   # 数据存储（gitignore）
├── logs/                   # 日志（gitignore）
├── config/                 # 配置文件
└── docker/                 # Docker 配置
    ├── Dockerfile
    └── docker-compose.yml
```

## 🛠️ 技术栈

### C++ 核心
- **语言标准**：C++20/23
- **构建系统**：CMake 3.15+
- **桥接层**：pybind11
- **数值计算**：Eigen 3.4+
- **并发**：OpenMP, std::thread
- **网络**：Asio (Boost.Asio standalone)
- **可视化**：Dear ImGui + ImPlot

### Python AI/ML
- **AI 模型**：openai (DeepSeek), anthropic (Claude)
- **数据获取**：akshare, xtquant
- **机器学习**：xgboost, lightgbm, scikit-learn
- **深度学习**：torch, tensorflow
- **强化学习**：ray[rllib]
- **可视化**：matplotlib, plotly, mplfinance
- **数据处理**：pandas, numpy

### 部署运维
- **容器化**：Docker, Docker Compose
- **监控**：Prometheus, Grafana
- **日志**：spdlog (C++), loguru (Python)

## 🚀 快速开始

### 环境要求

- **操作系统**：Windows 10/11, Linux, macOS
- **编译器**：
  - Windows: MSVC 2019+ / MinGW-w64
  - Linux: GCC 10+ / Clang 12+
  - macOS: Apple Clang 13+
- **Python**：3.9+
- **CMake**：3.15+

### 编译安装

```bash
# 1. 克隆仓库
git clone <repository-url>
cd ApexQuant

# 2. 创建构建目录
mkdir build && cd build

# 3. 配置 CMake
cmake .. -DCMAKE_BUILD_TYPE=Release

# 4. 编译
cmake --build . --config Release -j$(nproc)

# 5. 安装 Python 依赖
cd ../python
pip install -r requirements.txt

# 6. 测试安装
python tests/test_bridge.py
```

### Windows 特别说明

```powershell
# 使用 Visual Studio
cmake .. -G "Visual Studio 17 2022" -A x64
cmake --build . --config Release

# 或使用 MinGW
cmake .. -G "MinGW Makefiles"
cmake --build .
```

## 📚 使用示例

### 示例 1：C++ 计算均值，Python 调用

```python
import apexquant_core as aq

# 创建数据
data = [1.0, 2.0, 3.0, 4.0, 5.0]

# 调用 C++ 高性能均值计算
mean = aq.calculate_mean(data)
print(f"均值: {mean}")  # 输出: 3.0
```

### 示例 2：创建核心数据结构

```python
import apexquant_core as aq
from datetime import datetime

# 创建 Tick 数据
tick = aq.Tick(
    symbol="600519.SH",
    timestamp=int(datetime.now().timestamp() * 1000),
    last_price=1800.50,
    bid_price=1800.30,
    ask_price=1800.70,
    volume=1000000
)

# 创建 Bar 数据
bar = aq.Bar(
    symbol="600519.SH",
    timestamp=int(datetime.now().timestamp() * 1000),
    open=1800.0,
    high=1850.0,
    low=1790.0,
    close=1820.0,
    volume=5000000
)

print(f"Bar 数据: {bar}")
```

## 📅 开发路线图

- [x] **Day 1**: 基础框架 + 混合语言桥接 ✅
- [ ] **Day 2**: 数据层 + AI 数据增强
- [ ] **Day 3**: 行情显示器 + AI 交互可视化
- [ ] **Day 4**: 技术指标 + AI 因子挖掘
- [ ] **Day 5**: 回测引擎核心实现
- [ ] **Day 6**: 回测进阶 + AI 优化
- [ ] **Day 7**: 数据分析与风险评估 + AI 报告
- [ ] **Day 8**: 实盘基础 + AI 信号生成
- [ ] **Day 9**: 实盘整合 + AI 自适应
- [ ] **Day 10**: 服务器部署 + 监控体系

## ⚠️ 免责声明

本项目仅供学习和研究使用。量化交易存在风险，使用本系统进行实盘交易前请充分测试，并了解相关风险。作者不对使用本系统造成的任何损失负责。

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

<div align="center">
Made with ❤️ by ApexQuant Team
</div>

