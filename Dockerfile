# ApexQuant Dockerfile
# 混合语言量化交易系统

FROM ubuntu:22.04

LABEL maintainer="ApexQuant Team"
LABEL description="AI-Driven Quantitative Trading System"

# 避免交互式提示
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Asia/Shanghai

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    wget \
    curl \
    vim \
    python3.10 \
    python3.10-dev \
    python3-pip \
    libssl-dev \
    libboost-all-dev \
    libeigen3-dev \
    && rm -rf /var/lib/apt/lists/*

# 设置 Python 别名
RUN ln -s /usr/bin/python3.10 /usr/bin/python

# 升级 pip
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# 创建工作目录
WORKDIR /app

# 复制项目文件
COPY . /app

# 安装 Python 依赖
RUN pip install --no-cache-dir -r python/requirements.txt

# 编译 C++ 核心
RUN mkdir -p build && cd build && \
    cmake .. && \
    cmake --build . --config Release && \
    cd ..

# 设置 Python 路径
ENV PYTHONPATH=/app/python:$PYTHONPATH

# 创建数据和日志目录
RUN mkdir -p /app/data /app/logs /app/models

# 暴露端口
EXPOSE 8000 9090 3000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# 默认命令
CMD ["python", "examples/example_day9.py"]

