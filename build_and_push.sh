#!/bin/bash

# Moondream VLM Server Build and Push Script

set -e

# Image name
IMAGE_NAME="friddlecooper/moondream"

# Get the current date and time as a tag
TAG=$(date +%Y%m%d%H%M)
FULL_IMAGE_NAME="${IMAGE_NAME}:${TAG}"

echo "========================================"
echo "Building Moondream VLM Server Image"
echo "========================================"
echo "Image: ${FULL_IMAGE_NAME}"
echo ""

# Check if Dockerfile exists
if [ ! -f "docker/Dockerfile" ]; then
    echo "❌ Error: docker/Dockerfile not found"
    exit 1
fi

# Build the image
echo "🔨 Building Docker image..."
docker build -t ${FULL_IMAGE_NAME} -t ${IMAGE_NAME}:latest -f docker/Dockerfile .

echo ""
echo "✅ Image built successfully!"
echo "📦 Image name: ${FULL_IMAGE_NAME}"
echo ""

# Push the image to the repository
echo "🚀 Pushing image to repository..."
docker push ${FULL_IMAGE_NAME}
docker push ${IMAGE_NAME}:latest

echo ""
echo "========================================"
echo "✅ Image successfully built and pushed!"
echo "========================================"
echo ""
echo "📦 Image name: ${FULL_IMAGE_NAME}"
echo "🏷️  Latest tag: ${IMAGE_NAME}:latest"
echo ""
