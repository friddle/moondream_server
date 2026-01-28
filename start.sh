#!/bin/bash

# Moondream-2B VLM Server 启动脚本

set -e

echo "========================================"
echo "Moondream-2B Vision Language Server"
echo "========================================"
echo ""

# 显示配置信息
echo "📋 配置信息:"
echo "  Auth Username: ${VLM_AUTH_USERNAME:-admin}"
echo "  Auth Password: ${VLM_AUTH_PASSWORD:+(已设置)}"
echo "  HF Token: ${HF_TOKEN:+(已设置)}"
echo ""

# 启动服务
echo "🚀 启动服务..."
exec python3 app.py
