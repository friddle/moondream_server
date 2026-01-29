#!/bin/bash
# 推送镜像脚本 - 带日期标签

set -e

# 获取日期标签
DATE_TAG=$(date +%Y%m%d)
IMAGE_NAME="friddlecooper/moondream"
FULL_IMAGE_DATE="${IMAGE_NAME}:${DATE_TAG}"
FULL_IMAGE_LATEST="${IMAGE_NAME}:latest"

echo "========================================"
echo "推送 Moondream 镜像到 Docker Hub"
echo "========================================"
echo "日期标签: ${FULL_IMAGE_DATE}"
echo "Latest标签: ${FULL_IMAGE_LATEST}"
echo ""

# 检查镜像是否存在
echo "检查镜像..."
CONTAINERS_STORAGE_CONF=/dev/null buildah --storage-driver vfs --root /tmp/buildah-storage images 2>&1 | grep -q "moondream" || {
    echo "❌ 错误: 未找到 moondream 镜像"
    echo "请先运行构建: docker build 或 buildah bud"
    exit 1
}

# 提示登录
echo "⚠️  需要 Docker Hub 认证"
echo "请输入 Docker Hub 用户名和密码（或使用访问令牌）"
echo ""

# 登录 Docker Hub
CONTAINERS_STORAGE_CONF=/dev/null buildah --storage-driver vfs --root /tmp/buildah-storage login docker.io

# 推送日期标签镜像
echo ""
echo "🚀 推送镜像: ${FULL_IMAGE_DATE}"
CONTAINERS_STORAGE_CONF=/dev/null buildah --storage-driver vfs --root /tmp/buildah-storage push docker.io/${FULL_IMAGE_DATE} 2>&1

# 推送 latest 标签镜像
echo ""
echo "🚀 推送镜像: ${FULL_IMAGE_LATEST}"
CONTAINERS_STORAGE_CONF=/dev/null buildah --storage-driver vfs --root /tmp/buildah-storage push docker.io/${FULL_IMAGE_LATEST} 2>&1

echo ""
echo "========================================"
echo "✅ 镜像推送完成！"
echo "========================================"
echo "📦 日期标签: ${FULL_IMAGE_DATE}"
echo "📦 Latest标签: ${FULL_IMAGE_LATEST}"
echo ""
