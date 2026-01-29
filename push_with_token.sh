#!/bin/bash
# 使用 Docker Hub Token 推送镜像（非交互式）

set -e

DATE_TAG=$(date +%Y%m%d)
IMAGE_NAME="friddlecooper/moondream"

# 如果设置了 DOCKER_HUB_TOKEN 环境变量，使用它
if [ -z "$DOCKER_HUB_TOKEN" ]; then
    echo "请设置 DOCKER_HUB_TOKEN 环境变量"
    echo "例如: export DOCKER_HUB_TOKEN=your_token"
    echo "或者运行交互式脚本: ./push_image.sh"
    exit 1
fi

echo "使用 Token 推送镜像..."
echo "日期标签: ${IMAGE_NAME}:${DATE_TAG}"
echo "Latest标签: ${IMAGE_NAME}:latest"
echo ""

# 使用 echo 和管道传递密码（buildah login 支持从 stdin 读取）
echo "$DOCKER_HUB_TOKEN" | CONTAINERS_STORAGE_CONF=/dev/null buildah --storage-driver vfs --root /tmp/buildah-storage login --username friddlecooper --password-stdin docker.io 2>&1

# 推送镜像
echo "推送日期标签..."
CONTAINERS_STORAGE_CONF=/dev/null buildah --storage-driver vfs --root /tmp/buildah-storage push docker.io/${IMAGE_NAME}:${DATE_TAG} 2>&1

echo "推送 latest 标签..."
CONTAINERS_STORAGE_CONF=/dev/null buildah --storage-driver vfs --root /tmp/buildah-storage push docker.io/${IMAGE_NAME}:latest 2>&1

echo "✅ 推送完成！"
