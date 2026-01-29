#!/bin/bash
# 检查构建进度脚本

LOG_FILE="/tmp/build.log"
if [ ! -f "$LOG_FILE" ]; then
    LOG_FILE="/home/sybran/.cursor/projects/root-project-vlm/terminals/810263.txt"
fi

echo "=== 构建进度检查 ==="
echo ""

# 检查进程是否还在运行
if ps aux | grep -E "buildah.*moondream" | grep -v grep > /dev/null; then
    echo "✓ 构建进程正在运行"
else
    echo "✗ 构建进程已结束"
fi

echo ""
echo "=== 当前步骤 ==="
grep -E "^STEP" "$LOG_FILE" 2>/dev/null | tail -5

echo ""
echo "=== 最新日志 (最后10行) ==="
tail -10 "$LOG_FILE" 2>/dev/null || tail -10 /home/sybran/.cursor/projects/root-project-vlm/terminals/810263.txt 2>/dev/null

echo ""
echo "=== 磁盘使用 ==="
df -h /tmp | tail -1
