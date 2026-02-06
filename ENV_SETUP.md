# 环境变量配置指南

## 创建 .env 文件

在项目根目录创建 `.env` 文件（注意：此文件不会被提交到Git）：

```bash
# 在项目根目录执行
touch .env
```

## 配置内容

将以下内容复制到 `.env` 文件中，并替换为你的实际密钥：

```bash
# ==================== AI API 密钥 ====================
# DeepSeek API密钥 (https://platform.deepseek.com/)
DEEPSEEK_API_KEY=your_deepseek_api_key_here

# Claude API密钥 (可选)
CLAUDE_API_KEY=your_claude_api_key_here

# ==================== 数据源配置 ====================
# Tushare token (可选)
# TUSHARE_TOKEN=your_tushare_token_here

# ==================== 其他配置 ====================
LOG_LEVEL=INFO
ENABLE_MONITORING=false
METRICS_PORT=8000
```

## 验证配置

```python
# 测试环境变量是否正确加载
python -c "
from dotenv import load_dotenv
import os
load_dotenv()
print('DEEPSEEK_API_KEY:', '已设置' if os.getenv('DEEPSEEK_API_KEY') else '未设置')
"
```

## 安全提示

⚠️ **重要安全措施：**

1. **永远不要提交 .env 文件到Git**
2. **定期轮换API密钥**
3. **在生产环境使用密钥管理服务**
4. **限制 .env 文件权限** (chmod 600 .env)

## 生产环境建议

对于生产环境，建议使用更安全的密钥管理方案：

- AWS Secrets Manager
- Azure Key Vault
- HashiCorp Vault
- 系统环境变量（不使用.env文件）

