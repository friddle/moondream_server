#!/bin/bash

# Moondream-2B API 测试脚本
# 先下载测试图片，然后调用 API

echo "========================================="
echo "Moondream-2B API 测试"
echo "========================================="

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# API 地址
API_URL="http://localhost:5000"

# 1. 下载测试图片
echo -e "\n${BLUE}1. 下载测试图片...${NC}"

# 猫咪图片
wget -q -O test_cat.jpg "https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?w=800" && echo "✓ 下载: test_cat.jpg (猫咪)"

# 狗狗图片
wget -q -O test_dog.jpg "https://images.unsplash.com/photo-1587300003388-59208cc962cb?w=800" && echo "✓ 下载: test_dog.jpg (狗狗)"

# 风景图片
wget -q -O test_landscape.jpg "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800" && echo "✓ 下载: test_landscape.jpg (风景)"

# 城市图片
wget -q -O test_city.jpg "https://images.unsplash.com/photo-1480714378408-67cf0d13bc1b?w=800" && echo "✓ 下载: test_city.jpg (城市)"

# 食物图片
wget -q -O test_food.jpg "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=800" && echo "✓ 下载: test_food.jpg (汉堡)"

echo -e "\n${GREEN}所有图片下载完成！${NC}"

# 2. 测试 API
echo -e "\n${BLUE}2. 测试 API 识别...${NC}"

test_image() {
    local image=$1
    local question=$2

    echo -e "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "${GREEN}测试图片:${NC} $image"
    echo -e "${GREEN}问题:${NC} $question"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    start_time=$(date +%s.%N)
    response=$(curl -s -X POST \
        -F "file=@$image" \
        -F "question=$question" \
        $API_URL/identify)
    end_time=$(date +%s.%N)

    # 计算 API 时间
    api_time=$(echo "$end_time - $start_time" | bc)

    # 解析 JSON
    answer=$(echo $response | python3 -c "import sys, json; print(json.load(sys.stdin).get('answer', 'Error'))" 2>/dev/null)
    inference_time=$(echo $response | python3 -c "import sys, json; print(json.load(sys.stdin).get('inference_time', 'N/A'))" 2>/dev/null)

    echo -e "${GREEN}回答:${NC} $answer"
    echo -e "${GREEN}识别时间:${NC} $inference_time (模型)"
    echo -e "${GREEN}API 时间:${NC} $(printf "%.3fs" $api_time) (包含网络)"
}

# 测试不同的图片和问题
test_image "test_cat.jpg" "这是什么动物？"
test_image "test_dog.jpg" "描述这只狗"
test_image "test_landscape.jpg" "这是什么地方？描述一下景色"
test_image "test_city.jpg" "这是城市还是乡村？有些建筑吗？"
test_image "test_food.jpg" "这是什么食物？看起来好吃吗？"

echo -e "\n${BLUE}3. 健康检查${NC}"
curl -s $API_URL/health | python3 -m json.tool

echo -e "\n${GREEN}=========================================${NC}"
echo -e "${GREEN}测试完成！${NC}"
echo -e "${GREEN}=========================================${NC}"
