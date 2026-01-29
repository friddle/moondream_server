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

# 显示优化配置
echo "⚡ 优化配置:"
echo "  Preprocess Workers: ${PREPROCESS_WORKERS:-4}"
echo "  Batch Enabled: ${BATCH_ENABLED:-false}"
echo "  Gunicorn Workers: ${GUNICORN_WORKERS:-1}"
echo "  Gunicorn Threads: ${GUNICORN_THREADS:-4}"
echo ""

# 启动服务
echo "🚀 启动服务 (Gunicorn + Gevent)..."

# 使用 Gunicorn with gevent worker
exec gunicorn \
    --worker-class gevent \
    --workers ${GUNICORN_WORKERS:-1} \
    --threads ${GUNICORN_THREADS:-4} \
    --timeout ${GUNICORN_TIMEOUT:-120} \
    --bind 0.0.0.0:5000 \
    --access-logfile - \
    --error-logfile - \
    app:app
