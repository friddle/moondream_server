#!/bin/bash

# Moondream Docker Compose Quick Start

echo "🚀 Moondream Docker Compose 快速启动"
echo "======================================"

# 1. 准备环境
echo -e "\n📋 步骤 1: 准备环境"
if [ ! -f .env ]; then
    cp .env.docker-compose .env
    echo "✓ 创建 .env 文件"
else
    echo "✓ .env 文件已存在"
fi

# 2. 创建缓存目录
echo -e "\n📁 步骤 2: 创建缓存目录"
mkdir -p huggingface-cache
echo "✓ 缓存目录: $(pwd)/huggingface-cache"

# 3. 复制本地缓存（如果存在）
if [ -d ~/.cache/huggingface/hub ] && [ -z "$(ls -A huggingface-cache/)" ]; then
    echo -e "\n📦 步骤 3: 复制本地模型缓存"
    cp -r ~/.cache/huggingface/* huggingface-cache/
    echo "✓ 已复制本地缓存"
fi

# 4. 启动服务
echo -e "\n🎯 步骤 4: 启动服务"
docker-compose -f docker-compose-demo.yaml up -d

# 5. 等待服务就绪
echo -e "\n⏳ 等待服务启动..."
for i in {1..30}; do
    if curl -s http://localhost:5000/health > /dev/null 2>&1; then
        echo "✓ 服务已就绪!"
        break
    fi
    echo -n "."
    sleep 2
done

# 6. 显示状态
echo -e "\n\n📊 服务状态:"
docker-compose -f docker-compose-demo.yaml ps

# 7. 显示访问信息
echo -e "\n\n🌐 访问信息:"
echo "======================================"
echo "健康检查: curl http://localhost:5000/health"
echo "Web 界面: http://localhost:5000"
echo "API 端点: http://localhost:5000/v1/query"
echo "          http://localhost:5000/v1/caption"
echo ""
echo "查看日志: docker-compose -f docker-compose-demo.yaml logs -f"
echo "停止服务: docker-compose -f docker-compose-demo.yaml down"
echo "运行测试: ./test-docker-compose.sh"
echo "======================================"
