#!/bin/bash

# Caption API 测试脚本

API_URL="http://8.219.14.29:5000"

echo "========================================"
echo "Moondream-2B Caption API 测试"
echo "========================================"
echo ""

# 下载测试图片
if [ ! -f "/tmp/test_cat.jpg" ]; then
    echo "📥 下载测试图片..."
    wget -q -O /tmp/test_cat.jpg "https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?w=800"
    echo "✓ 下载完成"
    echo ""
fi

# 颜色
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

test_caption() {
    local length=$1
    local description=$2

    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}测试: $description${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    start_time=$(date +%s.%N)
    response=$(curl -s -X POST \
        -F "file=@/tmp/test_cat.jpg" \
        -F "length=$length" \
        $API_URL/caption)
    end_time=$(date +%s.%N)

    api_time=$(echo "$end_time - $start_time" | bc)

    echo "$response" | python3 -m json.tool
    echo -e "\n⏱️  API 响应时间: $(printf "%.3fs" $api_time)"
    echo ""
}

# 测试三种长度
test_caption "short" "简短描述"
test_caption "normal" "标准描述"
test_caption "long" "详细描述"

echo "========================================"
echo "✅ 测试完成！"
echo "========================================"
echo ""
echo "💡 使用说明:"
echo "  curl -X POST \\"
echo "    -F 'file=@photo.jpg' \\"
echo "    -F 'length=short' \\"
echo "    $API_URL/caption"
echo ""
echo "📝 length 参数:"
echo "  - short:  简短描述"
echo "  - normal: 标准描述 (默认)"
echo "  - long:   详细描述"
echo ""
