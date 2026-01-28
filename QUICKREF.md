#!/bin/bash

# Moondream-2B VLM Server - 快速参考命令
# ================================================

# 📦 Docker 镜像构建和推送
# ================================================
bash build_and_push.sh

# 🚀 Kubernetes 部署
# ================================================
bash k8s/deploy.sh

# 🧪 本地测试（带认证）
# ================================================
export VLM_AUTH_USERNAME=admin
export VLM_AUTH_PASSWORD=admin123
source venv/bin/activate
python app.py

# 🧪 测试 API（需要认证）
# ================================================
# 健康检查
curl -u admin:admin123 http://localhost:5000/health

# 图片识别
wget -O test.jpg "https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?w=800"
curl -u admin:admin123 \
  -F "file=@test.jpg" \
  -F "question=这是什么？" \
  http://localhost:5000/identify

# 🐳 Docker 运行
# ================================================
docker run -d \
  --name vlm-server \
  --gpus all \
  -p 5000:5000 \
  -e VLM_AUTH_USERNAME=admin \
  -e VLM_AUTH_PASSWORD=admin123 \
  -e HF_TOKEN=hf_your_token \
  registryaliyun.code27.co/app/vlm-server:latest

# 📊 查看日志
# ================================================
docker logs -f vlm-server
kubectl logs -f deployment/vlm-server -n llm

# 🔍 查看状态
# ================================================
docker ps | grep vlm-server
kubectl get pods -l app=vlm-server -n llm
kubectl get svc vlm-service -n llm

# 🧪 Docker 容器测试
# ================================================
bash test_docker.sh

# 🔄 更新部署
# ================================================
# 重新构建镜像
bash build_and_push.sh

# 更新 Kubernetes Deployment
kubectl set image deployment/vlm-server \
  vlm-server=registryaliyun.code27.co/app/vlm-server:latest \
  -n llm

# 等待部署完成
kubectl rollout status deployment/vlm-server -n llm

# 🗑️ 清理
# ================================================
docker stop vlm-server && docker rm vlm-server
kubectl delete deployment vlm-server -n llm
kubectl delete service vlm-service -n llm
