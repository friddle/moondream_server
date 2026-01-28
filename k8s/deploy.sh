#!/bin/bash

# Moondream-2B VLM Server Kubernetes 部署脚本

set -e

NAMESPACE="llm"
DEPLOYMENT_NAME="moondream-server"

echo "========================================"
echo "部署 Moondream-2B VLM Server 到 Kubernetes"
echo "========================================"
echo ""

# 检查命名空间是否存在
if ! kubectl get namespace ${NAMESPACE} >/dev/null 2>&1; then
    echo "⚠️  命名空间 ${NAMESPACE} 不存在，创建中..."
    kubectl create namespace ${NAMESPACE}
fi

# 部署
echo "📦 应用 Kubernetes 配置..."
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/ingress.yaml

echo ""
echo "⏳ 等待部署完成..."
kubectl rollout status deployment/${DEPLOYMENT_NAME} --namespace=${NAMESPACE} --timeout=600s

echo ""
echo "✅ 部署完成！"
echo ""

# 显示 Pod 状态
echo "📊 Pod 状态:"
kubectl get pods -l app=${DEPLOYMENT_NAME} --namespace=${NAMESPACE}

echo ""
echo "🔌 Service 信息:"
kubectl get service moondream-service --namespace=${NAMESPACE}

echo ""
echo "📝 查看日志:"
echo "  kubectl logs -f deployment/${DEPLOYMENT_NAME} -n ${NAMESPACE}"

echo ""
echo "🧪 测试服务:"
echo "  kubectl port-forward -n ${NAMESPACE} svc/moondream-service 5000:5000"
echo "  curl -u admin:admin123 http://localhost:5000/health"

echo ""
