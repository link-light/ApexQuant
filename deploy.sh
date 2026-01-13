#!/bin/bash

# ApexQuant 部署脚本

set -e

echo "================================"
echo "ApexQuant 部署脚本"
echo "================================"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}错误: Docker 未安装${NC}"
    echo "请先安装 Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}错误: Docker Compose 未安装${NC}"
    echo "请先安装 Docker Compose"
    exit 1
fi

# 检查环境变量
if [ -z "$DEEPSEEK_API_KEY" ]; then
    echo -e "${YELLOW}警告: DEEPSEEK_API_KEY 未设置${NC}"
    echo "请设置环境变量: export DEEPSEEK_API_KEY=your_key"
    echo "或创建 .env 文件"
fi

# 创建必要的目录
echo -e "${GREEN}创建必要的目录...${NC}"
mkdir -p data logs models config
mkdir -p deployment/prometheus
mkdir -p deployment/grafana/provisioning/datasources
mkdir -p deployment/grafana/provisioning/dashboards
mkdir -p deployment/grafana/dashboards

# 构建镜像
echo -e "${GREEN}构建 Docker 镜像...${NC}"
docker-compose build

# 启动服务
echo -e "${GREEN}启动服务...${NC}"
docker-compose up -d

# 等待服务启动
echo -e "${GREEN}等待服务启动...${NC}"
sleep 10

# 检查服务状态
echo ""
echo "================================"
echo "服务状态"
echo "================================"
docker-compose ps

# 显示访问地址
echo ""
echo "================================"
echo "访问地址"
echo "================================"
echo -e "${GREEN}Prometheus:${NC} http://localhost:9090"
echo -e "${GREEN}Grafana:${NC}    http://localhost:3000 (admin/admin)"
echo -e "${GREEN}ApexQuant:${NC}  http://localhost:8000"

echo ""
echo -e "${GREEN}部署完成！${NC}"
echo ""
echo "常用命令:"
echo "  查看日志: docker-compose logs -f"
echo "  停止服务: docker-compose down"
echo "  重启服务: docker-compose restart"
echo "  进入容器: docker-compose exec apexquant bash"

