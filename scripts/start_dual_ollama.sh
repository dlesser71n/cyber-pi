#!/bin/bash
# Start multiple Ollama instances on different GPUs

echo "🚀 Starting Dual-GPU Ollama Setup"
echo "=================================="
echo ""

echo "This will start 2 Ollama instances:"
echo "  Instance 1: GPU 0, Port 11434"
echo "  Instance 2: GPU 1, Port 11435"
echo ""

echo "Open 2 terminal windows and run these commands:"
echo ""

echo "Terminal 1 (GPU 0):"
echo "-------------------"
echo "export CUDA_VISIBLE_DEVICES=0"
echo "export OLLAMA_HOST=0.0.0.0:11434"
echo "ollama serve"
echo ""

echo "Terminal 2 (GPU 1):"
echo "-------------------"
echo "export CUDA_VISIBLE_DEVICES=1"
echo "export OLLAMA_HOST=0.0.0.0:11435"
echo "ollama serve"
echo ""

echo "After both are running, execute:"
echo "python3 src/processors/llama_dual_gpu.py"
echo ""

echo "Expected speedup: 2x faster!"
echo "  Single GPU: 0.8 items/sec = 32 minutes"
echo "  Dual GPU: 1.6 items/sec = 16 minutes"
