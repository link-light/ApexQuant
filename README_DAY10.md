# Day 10: 服务器部署 + 监控体系 ✅

## 完成内容

### 1. Docker 容器化
- **Dockerfile**: 完整构建环境（Ubuntu 22.04 + Python 3.10 + C++ 工具链）
- **docker-compose.yml**: 多服务编排
  - ApexQuant 主服务
  - Prometheus 监控
  - Grafana 可视化
  - Node Exporter 系统指标

### 2. Prometheus 监控
- **prometheus.yml**: 抓取配置
- **alert_rules.yml**: 告警规则
  - 服务宕机检测
  - CPU/内存/磁盘使用率告警
  - 自定义交易指标告警

#### 监控指标
- 系统指标：CPU、内存、磁盘、网络
- 交易指标：总资产、盈亏、胜率、回撤
- 订单指标：提交数、成交数、拒绝数
- 信号指标：信号生成次数

### 3. Grafana 仪表盘
- **数据源配置**: 自动连接 Prometheus
- **仪表盘**: ApexQuant 交易系统监控
  - 系统概览
  - CPU/内存使用趋势
  - 交易统计表格
  - 实时刷新（30秒）

### 4. 指标导出器
- **MetricsExporter**: Prometheus 格式指标导出
  - 账户指标：总资产、盈亏
  - 性能指标：胜率、回撤、夏普比率
  - 交易指标：交易次数、持仓数、订单状态
  - 自动更新和暴露

### 5. LLM 异常检测
- **AnomalyDetector**: AI 驱动的异常检测
  - 指标阈值检测
  - 日志分析
  - 交易模式分析
  - 自动告警生成

#### 异常类型
- 高回撤告警
- 低胜率告警
- 单日大额亏损
- 高订单拒绝率
- 持仓数超限

### 6. 部署脚本
- **deploy.sh**: 一键部署脚本
  - 环境检查
  - 目录创建
  - Docker 构建和启动
  - 服务状态检查

## 核心文件
```
.
├── Dockerfile                    # Docker 构建文件
├── docker-compose.yml            # 服务编排
├── deploy.sh                     # 部署脚本
├── .env.example                  # 环境变量示例
├── deployment/
│   ├── prometheus/
│   │   ├── prometheus.yml        # Prometheus 配置
│   │   └── alert_rules.yml       # 告警规则
│   └── grafana/
│       ├── provisioning/         # 自动配置
│       └── dashboards/           # 仪表盘
└── python/
    └── apexquant/
        └── monitoring/
            ├── metrics_exporter.py    # 指标导出
            └── anomaly_detector.py    # 异常检测
```

## 快速部署

### 1. 准备环境
```bash
# 安装 Docker 和 Docker Compose
# Ubuntu
sudo apt-get update
sudo apt-get install docker.io docker-compose

# 启动 Docker
sudo systemctl start docker
sudo systemctl enable docker

# 添加当前用户到 docker 组
sudo usermod -aG docker $USER
```

### 2. 配置环境变量
```bash
# 复制环境变量文件
cp .env.example .env

# 编辑 .env，填入真实值
vim .env
# 至少需要设置 DEEPSEEK_API_KEY
```

### 3. 一键部署
```bash
# 赋予执行权限
chmod +x deploy.sh

# 运行部署脚本
./deploy.sh
```

### 4. 访问服务
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)
- **ApexQuant**: http://localhost:8000

## 使用示例

### 1. 指标导出
```python
from apexquant.monitoring import MetricsExporter

exporter = MetricsExporter()

# 更新账户指标
exporter.update_account_metrics({
    'total_assets': 102000,
    'profit_loss': 2000,
    'profit_loss_pct': 0.02
})

# 更新性能指标
exporter.update_performance_metrics({
    'win_rate': 0.55,
    'max_drawdown': 0.08,
    'sharpe_ratio': 1.8
})

# 导出 Prometheus 格式
metrics_text = exporter.export_prometheus_format()
print(metrics_text)
```

### 2. 异常检测
```python
from apexquant.monitoring import AnomalyDetector

detector = AnomalyDetector(api_key="your_key")

# 检测指标异常
anomalies = detector.detect_metric_anomalies(metrics)

if anomalies:
    # 生成告警消息
    alert_msg = detector.generate_alert_message(anomalies)
    print(alert_msg)
    
    # 发送通知
    notifier.send_alert("系统异常", alert_msg, level="warning")

# 分析日志
log_analysis = detector.analyze_logs(recent_logs)
if log_analysis:
    print(log_analysis)

# 分析交易模式
pattern_analysis = detector.analyze_trading_patterns(trades, performance)
if pattern_analysis:
    print(pattern_analysis)
```

### 3. 集成到实盘系统
```python
from apexquant.monitoring import MetricsExporter, AnomalyDetector
from apexquant.adaptive import NotificationManager

# 初始化
exporter = MetricsExporter()
detector = AnomalyDetector()
notifier = NotificationManager()

# 在交易循环中
while trading:
    # 更新指标
    account = trader.get_account_status()
    exporter.update_account_metrics(account)
    
    # 检测异常
    metrics = exporter.get_metrics()
    anomalies = detector.detect_metric_anomalies(metrics)
    
    if anomalies:
        alert_msg = detector.generate_alert_message(anomalies)
        notifier.send_risk_alert("异常检测", alert_msg)
    
    # 定期分析
    if should_analyze:
        analysis = detector.analyze_trading_patterns(trades, performance)
        if analysis:
            notifier.send_alert("交易分析", analysis)
```

## Docker 命令

### 常用命令
```bash
# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f apexquant
docker-compose logs -f prometheus
docker-compose logs -f grafana

# 重启服务
docker-compose restart

# 停止服务
docker-compose down

# 停止并删除数据卷
docker-compose down -v

# 进入容器
docker-compose exec apexquant bash

# 重新构建
docker-compose build --no-cache
docker-compose up -d
```

### 更新部署
```bash
# 拉取最新代码
git pull

# 重新构建并启动
docker-compose up -d --build
```

## 监控配置

### Prometheus 查询示例
```promql
# 总资产
apexquant_total_assets

# 盈亏比例
apexquant_profit_loss_pct

# 胜率
apexquant_win_rate

# 最大回撤
apexquant_max_drawdown

# 交易次数增长率
rate(apexquant_trade_count[5m])

# CPU 使用率
100 - (avg(irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)

# 内存使用率
(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100
```

### 告警配置
编辑 `deployment/prometheus/alert_rules.yml` 添加自定义告警：

```yaml
- alert: HighDrawdown
  expr: apexquant_max_drawdown > 0.15
  for: 1m
  labels:
    severity: critical
  annotations:
    summary: "最大回撤超过 15%"
    description: "当前回撤: {{ $value }}"
```

## 云服务器部署

### 推荐配置
- **CPU**: 2核+
- **内存**: 4GB+
- **磁盘**: 40GB+
- **系统**: Ubuntu 22.04

### 部署步骤
1. 购买云服务器（阿里云/腾讯云/AWS）
2. 配置安全组，开放端口：8000, 9090, 3000
3. SSH 登录服务器
4. 克隆代码：`git clone https://github.com/your-repo/ApexQuant.git`
5. 运行部署脚本：`./deploy.sh`
6. 配置域名和 SSL（可选）

### 安全建议
1. 修改 Grafana 默认密码
2. 配置防火墙，仅开放必要端口
3. 使用 HTTPS（Nginx + Let's Encrypt）
4. 定期备份数据和模型
5. 监控系统资源使用

## 监控最佳实践

### 1. 关键指标监控
- 总资产趋势
- 日均盈亏
- 最大回撤
- 胜率趋势
- 订单成功率

### 2. 告警策略
- **Critical**: 回撤 > 15%, 单日亏损 > 10%
- **Warning**: 胜率 < 40%, 订单拒绝率 > 10%
- **Info**: 系统资源使用 > 80%

### 3. 日志管理
- 保留最近 30 天日志
- 定期归档重要日志
- LLM 定期分析日志

### 4. 性能优化
- 监控 API 调用延迟
- 优化数据库查询
- 使用缓存减少重复计算

## 故障排查

### 常见问题

**1. 服务启动失败**
```bash
# 查看日志
docker-compose logs apexquant

# 检查端口占用
netstat -tulpn | grep 8000

# 重新构建
docker-compose build --no-cache
```

**2. Prometheus 无法抓取指标**
- 检查 `prometheus.yml` 配置
- 确认 ApexQuant 暴露了 `/metrics` 端点
- 检查网络连接

**3. Grafana 无数据**
- 验证 Prometheus 数据源配置
- 检查查询语句
- 确认时间范围

## 下一步优化

### 功能增强
1. 实现 `/metrics` HTTP 端点
2. 添加更多自定义指标
3. 实现 Alertmanager 集成
4. 添加日志聚合（ELK Stack）
5. 实现分布式追踪（Jaeger）

### 性能优化
1. 使用 Redis 缓存
2. 数据库连接池
3. 异步任务队列
4. 负载均衡

## 总结

Day 10 完成了完整的部署和监控体系：
- ✅ Docker 容器化部署
- ✅ Prometheus + Grafana 监控
- ✅ 自定义指标导出
- ✅ LLM 异常检测
- ✅ 一键部署脚本
- ✅ 生产级配置

至此，ApexQuant 10 天开发计划全部完成！🎉

