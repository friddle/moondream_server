#!/bin/bash

# Moondream VLM Server Deployment Script

set -e

# --- Configuration ---
IMAGE="friddlecooper/moondream:latest"
NAMESPACE="llm"
DEPLOYMENT_NAME="moondream-server"

echo "========================================"
echo "Deploying Moondream VLM Server"
echo "========================================"
echo "Image: ${IMAGE}"
echo ""

# Trigger a new rollout by setting an annotation with the current timestamp
echo "🚀 Triggering a new rollout..."
kubectl patch deployment ${DEPLOYMENT_NAME} -n ${NAMESPACE} -p '{"spec":{"template":{"metadata":{"annotations":{"kubectl.kubernetes.io/restartedAt":"'$(date +%s)'"}}}}}' --type=merge

echo ""
echo "⏳ Waiting for rollout to complete..."
kubectl rollout status deployment/${DEPLOYMENT_NAME} -n ${NAMESPACE} --timeout=600s

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📊 Current pods:"
kubectl get pods -n ${NAMESPACE} -l app=${DEPLOYMENT_NAME}
echo ""
echo "🔌 Service: moondream-service"
echo "🌐 Ingress URLs:"
echo "   - https://moondream.sgprivate.code27.co"
echo "   - https://moondream.sgllm.code27.co"
echo ""
