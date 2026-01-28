#!/bin/bash

# 快速测试脚本 - 下载图片并测试 API

API_URL="http://localhost:5000"

echo "========================================"
echo "下载测试图片并识别"
echo "========================================"

# 方法 1: 使用 wget 下载单张测试图片
echo -e "\n📥 下载测试图片..."
wget -q -O test_cat.jpg "https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?w=800" && echo "✓ 下载完成: test_cat.jpg"

# 方法 2: 使用 curl 调用 API
echo -e "\n🔍 开始识别..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

curl -X POST \
  -F "file=@test_cat.jpg" \
  -F "question=这是什么动物？详细描述一下" \
  $API_URL/identify | python3 -m json.tool

echo -e "\n✅ 测试完成！"
echo -e "\n💡 提示: 也可以在浏览器打开 http://localhost:5000 上传图片"
