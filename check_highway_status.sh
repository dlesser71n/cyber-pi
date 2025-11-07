#!/bin/bash
# Quick Redis Highway Build Status Checker

echo "🔍 REDIS HIGHWAY BUILD STATUS"
echo "=============================="

# Check if process is running
PID=$(pgrep -f "build_redis_highway_gpu.py")
if [ -n "$PID" ]; then
    echo "✅ Process Running: PID $PID"
else
    echo "❌ Process Not Running"
fi

# Show latest progress
echo ""
echo "📊 Latest Progress:"
tail -20 /tmp/redis_highway_complete.log | grep -E "(Building Highway|Validated|Processing|complete)" | tail -5

# Show GPU usage
echo ""
echo "🎮 GPU Status:"
nvidia-smi --query-gpu=index,utilization.gpu,memory.used,memory.total --format=csv,noheader

# Check Redis
echo ""
echo "💾 Redis Status:"
redis-cli -h 10.152.183.253 -a cyber-pi-redis-2025 DBSIZE 2>/dev/null || echo "Redis check skipped"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Run: tail -f /tmp/redis_highway_complete.log"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
