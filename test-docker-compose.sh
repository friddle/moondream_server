#!/bin/bash

# Moondream Docker Compose API Test Script

echo "========================================="
echo "Moondream API 测试"
echo "========================================="

API_URL="http://localhost:5000"

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "\n${BLUE}1. 测试健康检查${NC}"
curl -s $API_URL/health | python3 -m json.tool

echo -e "\n${BLUE}2. 下载测试图片${NC}"
wget -q -O /tmp/test_cat.jpg "https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?w=400" && echo "✓ 下载完成"

echo -e "\n${BLUE}3. 转换图片为 base64${NC}"
IMAGE_BASE64=$(base64 -w 0 /tmp/test_cat.jpg)
echo "✓ Base64 编码完成 (长度: ${#IMAGE_BASE64})"

echo -e "\n${BLUE}4. 测试 v1/caption 端点${NC}"
curl -s -X POST \
  -H 'Content-Type: application/json' \
  -d "{
    \"image_url\": \"data:image/jpeg;base64,$IMAGE_BASE64\",
    \"length\": \"normal\",
    \"stream\": false
  }" \
  $API_URL/v1/caption | python3 -m json.tool

echo -e "\n${BLUE}5. 测试 v1/query 端点${NC}"
curl -s -X POST \
  -H 'Content-Type: application/json' \
  -d "{
    \"image_url\": \"data:image/jpeg;base64,$IMAGE_BASE64\",
    \"question\": \"这是什么动物？\"
  }" \
  $API_URL/v1/query | python3 -m json.tool

echo -e "\n${GREEN}=========================================${NC}"
echo -e "${GREEN}测试完成！${NC}"
echo -e "${GREEN}=========================================${NC}"
