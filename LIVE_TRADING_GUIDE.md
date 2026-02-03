# ApexQuant 实盘交易部署指南

## 准备清单

### 1. 券商接口申请

#### 推荐选择：QMT (国金)

**申请步骤：**
1. 开通国金证券账户
2. 申请QMT程序化交易权限
   - 需要50万资产或者满足其他条件
   - 联系客户经理申请
3. 获取API接口文档和SDK
4. 获取账户配置信息

**所需信息：**
- 账号
- 密码
- 服务器地址
- 资产账户ID

#### 其他选择对比

| 券商 | 优点 | 缺点 | 适合场景 |
|------|------|------|----------|
| QMT | API完善，稳定 | 需要50万资产 | 中低频交易 |
| XTP | 低延迟 | 配置复杂 | 高频交易 |
| 掘金 | 文档好 | 费用较高 | 初学者 |

### 2. 代码对接

#### 修改交易接口

需要在 `cpp/src/trading_interface.cpp` 中实现真实接口：

```cpp
class QMTTradingInterface : public ITradingInterface {
public:
    bool connect(const std::string& server, int port) override {
        // 连接到QMT服务器
        // 实现连接逻辑
    }
    
    bool login(const std::string& account, const std::string& password) override {
        // 登录逻辑
    }
    
    std::string submit_order(const Order& order) override {
        // 提交真实订单到QMT
        // 返回订单ID
    }
    
    // 其他接口实现...
};
```

#### Python层调用

```python
from apexquant.live import LiveTrader
from apexquant_core import QMTTradingInterface  # C++接口

# 创建真实交易接口
trading = QMTTradingInterface()
trading.connect("qmt_server_address", 7777)
trading.login("your_account", "your_password")

# 创建实盘交易器
trader = LiveTrader(
    trading_interface=trading,
    signal_generator=signal_gen,
    mode="live"  # 真实模式
)

# 设置风控（重要！）
trader.set_risk_limits({
    'max_position_size': 0.2,      # 单仓位最大20%
    'max_total_positions': 3,      # 最多3个持仓
    'stop_loss': -0.03,            # 止损3%
    'take_profit': 0.10,           # 止盈10%
    'max_daily_loss': -0.05,       # 日亏损5%熔断
    'max_order_value': 50000       # 单笔最大5万
})

# 启动交易
trader.start(interval=60)  # 每60秒检查一次
```

### 3. 配置文件

创建 `config/live.yaml`:

```yaml
trading:
  mode: live  # live / paper / simulation
  
broker:
  name: qmt
  server: "xxx.xxx.xxx.xxx"
  port: 7777
  account: "your_account"
  password: "***"  # 从环境变量读取
  
risk_control:
  max_position_pct: 0.2
  max_positions: 3
  stop_loss_pct: -0.03
  take_profit_pct: 0.10
  daily_loss_limit_pct: -0.05
  max_order_value: 50000
  
watchlist:
  - "600519"  # 贵州茅台
  - "600036"  # 招商银行
  - "000001"  # 平安银行
```

### 4. 安全措施

#### 环境变量存储密码

```bash
# Windows
set BROKER_PASSWORD=your_password

# Linux
export BROKER_PASSWORD=your_password
```

#### 代码中读取

```python
import os
password = os.getenv("BROKER_PASSWORD")
```

### 5. 测试流程

#### 阶段1：模拟盘测试（2-4周）
- 当前纸上交易系统
- 验证策略有效性
- 调整参数

#### 阶段2：券商模拟盘（2-4周）
```python
trader.set_mode("paper")  # 券商提供的模拟盘
```
- 测试API对接
- 验证订单执行
- 测试异常处理

#### 阶段3：小资金实盘（4-8周）
```python
trader.set_mode("live")
trader.set_capital_limit(10000)  # 限制使用1万资金
```
- 小额真实交易
- 观察实际滑点和成本
- 验证系统稳定性

#### 阶段4：正式实盘
- 逐步增加资金
- 持续监控和优化

### 6. 风险控制清单

- [ ] 设置止损止盈
- [ ] 限制单笔交易金额
- [ ] 限制日内亏损
- [ ] 设置持仓上限
- [ ] 配置异常熔断
- [ ] 设置紧急止损按钮
- [ ] 配置实时监控
- [ ] 设置告警通知

### 7. 监控和告警

#### 实时监控
- Grafana仪表盘（已有配置）
- 实时盈亏
- 持仓状态
- 系统状态

#### 告警设置
```python
from apexquant.adaptive import NotificationManager

notifier = NotificationManager(
    telegram_token="your_token",
    wechat_webhook="your_webhook"
)

# 触发条件
- 单日亏损超过5%
- 单笔亏损超过3%
- 系统异常
- 连接断开
```

## 部署步骤

### Step 1: 编译C++核心（包含真实接口）

```bash
# 编译带QMT接口的版本
cmake .. -DBUILD_QMT=ON
cmake --build . --config Release
```

### Step 2: 配置环境

```bash
# 安装依赖
pip install -r requirements_live.txt

# 设置环境变量
set BROKER_PASSWORD=***
set DEEPSEEK_API_KEY=***
```

### Step 3: 先在模拟盘测试

```bash
python examples/example_live_paper.py
```

### Step 4: 连接真实接口

```bash
# 编辑配置
nano config/live.yaml

# 运行
python live_trader.py --config config/live.yaml --mode paper
```

### Step 5: 小资金实盘

```bash
python live_trader.py --config config/live.yaml --mode live --capital 10000
```

## 常见问题

### Q1: 需要多少资金？
A: 建议至少5-10万，初期测试可以1-2万

### Q2: 需要什么技术水平？
A: 
- 了解Python编程
- 了解C++（如需自定义接口）
- 了解股票交易规则
- 了解风险管理

### Q3: 预期收益？
A: 
- 不保证盈利
- 建议目标：年化10-20%
- 实际可能亏损

### Q4: 主要风险？
A:
- 策略失效
- 技术故障
- 市场极端波动
- 操作失误

## 重要提醒

⚠️ **风险警告**
1. 量化交易存在风险，可能亏损全部本金
2. 历史回测不代表未来表现
3. 建议只投入可承受损失的资金
4. 建议咨询专业投资顾问
5. 遵守法律法规，不进行违规交易

⚠️ **法律合规**
1. 确保券商API使用合法
2. 不进行市场操纵
3. 遵守T+1等交易规则
4. 依法纳税

## 联系支持

- 技术问题：查看项目文档
- 券商接口：联系券商客户经理
- 法律问题：咨询专业律师

---

**准备好了吗？**

如果以上都理解并准备就绪，可以开始申请券商API接口！
