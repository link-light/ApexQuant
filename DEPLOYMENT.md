# ApexQuant 部署指南

## 快速开始

### 方式一：Docker 部署（推荐）

```bash
# 1. 克隆项目
git clone https://github.com/link-light/ApexQuant.git
cd ApexQuant

# 2. 配置环境变量
cp .env.example .env
vim .env  # 填入 DEEPSEEK_API_KEY

# 3. 一键部署
chmod +x deploy.sh
./deploy.sh

# 4. 访问服务
# Prometheus: http://localhost:9090
# Grafana: http://localhost:3000 (admin/admin)
```

### 方式二：本地开发

```bash
# 1. 安装依赖
pip install -r python/requirements.txt

# 2. 编译 C++ 核心
mkdir build && cd build
cmake ..
cmake --build . --config Release

# 3. 运行示例
cd ..
python examples/example_day9.py
```

## 系统要求

### 最低配置
- CPU: 2核
- 内存: 4GB
- 磁盘: 20GB
- 系统: Ubuntu 20.04+ / macOS / Windows

### 推荐配置
- CPU: 4核+
- 内存: 8GB+
- 磁盘: 50GB+
- 系统: Ubuntu 22.04

## 服务架构

```
ApexQuant 主服务 (8000)
    ↓
Prometheus (9090) ← 指标抓取
    ↓
Grafana (3000) ← 可视化展示
```

## 环境变量

| 变量名 | 说明 | 必需 |
|--------|------|------|
| DEEPSEEK_API_KEY | DeepSeek API 密钥 | 是 |
| TELEGRAM_BOT_TOKEN | Telegram Bot Token | 否 |
| TELEGRAM_CHAT_ID | Telegram Chat ID | 否 |
| WECHAT_WEBHOOK | 企业微信 Webhook | 否 |
| TZ | 时区 | 否 |

## 端口说明

| 端口 | 服务 | 说明 |
|------|------|------|
| 8000 | ApexQuant | 主服务 |
| 9090 | Prometheus | 监控数据 |
| 3000 | Grafana | 可视化 |
| 9100 | Node Exporter | 系统指标 |

## 数据持久化

Docker 卷：
- `./data` - 市场数据
- `./logs` - 系统日志
- `./models` - 模型文件
- `prometheus-data` - Prometheus 数据
- `grafana-data` - Grafana 配置

## 监控告警

### 配置告警
编辑 `deployment/prometheus/alert_rules.yml`

### 查看告警
访问 http://localhost:9090/alerts

### 接收通知
配置 Telegram 或企业微信环境变量

## 常见问题

### Q: Docker 构建失败？
A: 检查网络连接，尝试使用镜像加速

### Q: 服务无法访问？
A: 检查防火墙和端口占用

### Q: Grafana 无数据？
A: 检查 Prometheus 数据源配置

## 更多信息

- 详细文档：README_DAY10.md
- 项目主页：README.md
- 问题反馈：GitHub Issues

