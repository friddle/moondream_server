#!/bin/bash

# Docker 容器测试脚本

set -e

AUTH_USER=${VLM_AUTH_USERNAME:-admin}
AUTH_PASS=${VLM_AUTH_PASSWORD:-admin}
API_URL="http://localhost:5000"

echo "========================================"
echo "Moondream-2B Docker 容器测试"
echo "========================================"
echo "认证信息: ${AUTH_USER}:${AUTH_PASS}"
echo ""

# 颜色
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

test_api() {
    local test_name=$1
    local command=$2

    echo -n "测试: ${test_name}... "

    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ 通过${NC}"
        return 0
    else
        echo -e "${RED}✗ 失败${NC}"
        return 1
    fi
}

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1. 容器状态检查"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

docker ps --filter "name=vlm-server" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" || echo "⚠️  容器未运行"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2. API 测试"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 测试健康检查（无认证）
test_api "健康检查（无认证）" "curl -s -f ${API_URL}/health"

# 测试健康检查（错误密码）
test_api "健康检查（错误密码）" "curl -s -f -u ${AUTH_USER}:wrongpass ${API_URL}/health"

# 测试健康检查（正确认证）
test_api "健康检查（正确认证）" "curl -s -f -u ${AUTH_USER}:${AUTH_PASS} ${API_URL}/health"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3. 识别功能测试"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 下载测试图片
echo -n "下载测试图片... "
if wget -q -O /tmp/test_cat.jpg "https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?w=800" 2>/dev/null; then
    echo -e "${GREEN}✓ 完成${NC}"
else
    echo -e "${RED}✗ 失败${NC}"
    exit 1
fi

# 测试图片识别
echo -n "图片识别... "
response=$(curl -s -X POST \
    -u "${AUTH_USER}:${AUTH_PASS}" \
    -F "file=@/tmp/test_cat.jpg" \
    -F "question=这是什么动物？" \
    "${API_URL}/identify")

if echo "$response" | grep -q "answer"; then
    echo -e "${GREEN}✓ 成功${NC}"
    echo "  回答: $(echo $response | python3 -c "import sys,json; print(json.load(sys.stdin).get('answer','')[:50] + '...')")"
    echo "  时间: $(echo $response | python3 -c "import sys,json; print(json.load(sys.stdin).get('inference_time',''))")"
else
    echo -e "${RED}✗ 失败${NC}"
    echo "  响应: $response"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "4. 容器日志"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
docker logs vlm-server --tail 20 2>&1 || echo "⚠️  无法获取日志"

echo ""
echo "========================================"
echo "✅ 测试完成！"
echo "========================================"
