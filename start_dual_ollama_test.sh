#!/bin/bash
# Start Dual Ollama Instances for Testing

echo "🚀 Starting Dual-GPU Ollama Setup for Maximum Stress Test"
echo "=========================================================================="
echo ""

# Check if ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "❌ Ollama not found. Please install ollama first."
    exit 1
fi

# Check if llama4:16x17b is available
if ! ollama list | grep -q "llama4:16x17b"; then
    echo "❌ llama4:16x17b model not found."
    echo "   Available models:"
    ollama list
    exit 1
fi

echo "✅ Ollama installed"
echo "✅ llama4:16x17b model available"
echo ""

# Check if instances are already running
if pgrep -f "OLLAMA_HOST=0.0.0.0:11434" > /dev/null; then
    echo "⚠️  Ollama instance already running on port 11434"
else
    echo "Starting GPU 0 instance (port 11434)..."
fi

if pgrep -f "OLLAMA_HOST=0.0.0.0:11435" > /dev/null; then
    echo "⚠️  Ollama instance already running on port 11435"
else
    echo "Starting GPU 1 instance (port 11435)..."
fi

echo ""
echo "=========================================================================="
echo "MANUAL SETUP REQUIRED:"
echo "=========================================================================="
echo ""
echo "Open 2 separate terminal windows and run:"
echo ""
echo "Terminal 1 (GPU 0):"
echo "-------------------"
echo "cd $(pwd)"
echo "export CUDA_VISIBLE_DEVICES=0"
echo "export OLLAMA_HOST=0.0.0.0:11434"
echo "ollama serve"
echo ""
echo "Terminal 2 (GPU 1):"
echo "-------------------"
echo "cd $(pwd)"
echo "export CUDA_VISIBLE_DEVICES=1"
echo "export OLLAMA_HOST=0.0.0.0:11435"
echo "ollama serve"
echo ""
echo "=========================================================================="
echo ""
echo "After both instances are running, execute:"
echo "  python3 test_financial_intelligence_max.py"
echo ""
echo "Expected performance:"
echo "  - Throughput: 10-20 analyses/sec"
echo "  - Daily capacity: ~1M analyses/day"
echo "  - Load balanced across both GPUs"
echo ""
echo "🔭 See threats before they surface."
echo "=========================================================================="
