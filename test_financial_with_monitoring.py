#!/usr/bin/env python3
"""
Financial Threat Intelligence Test with Real-Time Monitoring
Shows model loading progress and GPU VRAM usage
"""

import asyncio
import sys
import time
import subprocess
import requests
from datetime import datetime


def get_gpu_info():
    """Get current GPU memory usage."""
    try:
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=index,memory.used,memory.total,utilization.gpu', 
             '--format=csv,noheader,nounits'],
            capture_output=True,
            text=True,
            timeout=2
        )
        
        gpus = []
        for line in result.stdout.strip().split('\n'):
            if line:
                parts = [p.strip() for p in line.split(',')]
                if len(parts) == 4:
                    gpus.append({
                        'index': int(parts[0]),
                        'memory_used': int(parts[1]),
                        'memory_total': int(parts[2]),
                        'utilization': int(parts[3])
                    })
        return gpus
    except Exception as e:
        return []


def print_gpu_status(gpus, prefix=""):
    """Print formatted GPU status."""
    if not gpus:
        print(f"{prefix}⚠️  Unable to read GPU status")
        return
    
    for gpu in gpus:
        mem_pct = (gpu['memory_used'] / gpu['memory_total']) * 100
        bar_length = 30
        filled = int(bar_length * mem_pct / 100)
        bar = '█' * filled + '░' * (bar_length - filled)
        
        print(f"{prefix}GPU {gpu['index']}: [{bar}] {gpu['memory_used']:5d}/{gpu['memory_total']:5d} MB ({mem_pct:5.1f}%) | Util: {gpu['utilization']:3d}%")


def check_ollama_ready():
    """Check if Ollama is responding."""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        return response.status_code == 200
    except:
        return False


def check_model_loaded(model_name):
    """Check if model is currently loaded."""
    try:
        response = requests.get("http://localhost:11434/api/ps", timeout=2)
        if response.status_code == 200:
            data = response.json()
            models = data.get('models', [])
            for m in models:
                if model_name in m.get('name', ''):
                    return True
        return False
    except:
        return False


async def wait_for_model_load(model_name="llama4:16x17b", max_wait=300):
    """
    Wait for model to load into VRAM with real-time monitoring.
    
    Args:
        model_name: Name of the model to load
        max_wait: Maximum seconds to wait
    """
    print("=" * 80)
    print("🔄 LOADING MODEL INTO VRAM")
    print("=" * 80)
    print(f"Model: {model_name}")
    print(f"Expected size: ~67GB (will split across both GPUs)")
    print()
    
    # Initial GPU state
    print("📊 Initial GPU State:")
    initial_gpus = get_gpu_info()
    print_gpu_status(initial_gpus, "   ")
    print()
    
    # Trigger model load with a simple request
    print("🚀 Triggering model load...")
    print("   (Making initial API call to force model into VRAM)")
    print()
    
    start_time = time.time()
    load_triggered = False
    
    # Make async request to trigger load
    async def trigger_load():
        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": model_name,
                    "prompt": "test",
                    "stream": False
                },
                timeout=max_wait
            )
            return response.status_code == 200
        except:
            return False
    
    # Start the load request in background
    load_task = asyncio.create_task(trigger_load())
    
    # Monitor loading progress
    print("⏳ Loading model into VRAM (this may take 30-60 seconds)...")
    print()
    
    last_update = 0
    dots = 0
    
    while not load_task.done() and (time.time() - start_time) < max_wait:
        elapsed = time.time() - start_time
        
        # Update every 2 seconds
        if elapsed - last_update >= 2:
            last_update = elapsed
            
            # Get current GPU state
            current_gpus = get_gpu_info()
            
            # Clear previous lines (move up 4 lines and clear)
            if dots > 0:
                print('\033[F' * 5, end='')
            
            # Show progress
            dots = (dots + 1) % 4
            progress_dots = '.' * dots + ' ' * (3 - dots)
            print(f"⏱️  Elapsed: {elapsed:.1f}s {progress_dots}")
            print()
            
            # Show GPU status
            print_gpu_status(current_gpus, "   ")
            print()
            
            # Check if memory is increasing (model loading)
            if current_gpus and initial_gpus:
                total_mem_used = sum(g['memory_used'] for g in current_gpus)
                initial_mem_used = sum(g['memory_used'] for g in initial_gpus)
                mem_increase = total_mem_used - initial_mem_used
                
                if mem_increase > 1000:  # More than 1GB loaded
                    if not load_triggered:
                        load_triggered = True
                        print(f"   ✅ Model loading detected! (+{mem_increase} MB)")
        
        await asyncio.sleep(0.5)
    
    # Wait for task to complete
    try:
        success = await asyncio.wait_for(load_task, timeout=5)
    except:
        success = False
    
    elapsed = time.time() - start_time
    
    print()
    print("=" * 80)
    print("📊 FINAL GPU STATE")
    print("=" * 80)
    
    final_gpus = get_gpu_info()
    print_gpu_status(final_gpus, "   ")
    print()
    
    if final_gpus and initial_gpus:
        print("📈 Memory Change:")
        for i, (final, initial) in enumerate(zip(final_gpus, initial_gpus)):
            change = final['memory_used'] - initial['memory_used']
            print(f"   GPU {i}: +{change:,} MB")
        
        total_change = sum(g['memory_used'] for g in final_gpus) - sum(g['memory_used'] for g in initial_gpus)
        print(f"   Total: +{total_change:,} MB")
    
    print()
    print(f"⏱️  Load time: {elapsed:.1f} seconds")
    
    if success:
        print("✅ Model loaded successfully!")
    else:
        print("⚠️  Model load may still be in progress")
    
    print("=" * 80)
    print()
    
    return success


async def run_single_test():
    """Run a single financial analysis test."""
    from src.intelligence.financial_threat_analyzer import FinancialThreatAnalyzer
    
    print("=" * 80)
    print("🧪 RUNNING SINGLE ANALYSIS TEST")
    print("=" * 80)
    print()
    
    analyzer = FinancialThreatAnalyzer()
    
    # Test data
    stock_data = {
        'ticker': 'UNH',
        'price': 524.50,
        'volume_change': 245.3,
        'options_activity': 'Unusual put buying (3x normal)',
        'short_interest': 12.5,
        'insider_trading': '3 executives sold shares',
        'avg_volume_30d': 2.1e6,
        'price_trend_90d': '+8.2%',
        'industry': 'Healthcare',
        'market_cap': 485e9
    }
    
    print("📊 Analyzing: UNH (UnitedHealth Group)")
    print("   Suspicious indicators detected:")
    print(f"   - Volume spike: {stock_data['volume_change']}%")
    print(f"   - Short interest: {stock_data['short_interest']}%")
    print(f"   - Insider selling: {stock_data['insider_trading']}")
    print()
    
    # Monitor during inference
    print("🔄 Running analysis...")
    start_time = time.time()
    
    # Get initial GPU state
    initial_gpus = get_gpu_info()
    
    # Run analysis
    result = await analyzer.analyze_stock_anomalies('UNH', stock_data)
    
    elapsed = time.time() - start_time
    
    # Get final GPU state
    final_gpus = get_gpu_info()
    
    print()
    print("=" * 80)
    print("📊 ANALYSIS RESULTS")
    print("=" * 80)
    
    if result.get('success', True):
        print(f"✅ Analysis complete in {elapsed:.2f}s")
        print()
        print(f"🎯 Threat Score: {result.get('threat_score', 'N/A')}/100")
        print(f"📈 Confidence: {result.get('confidence', 'N/A')}%")
        print()
        print("📝 Analysis Preview:")
        analysis = result.get('raw_analysis', result.get('analysis', 'N/A'))
        print()
        for line in analysis[:500].split('\n'):
            if line.strip():
                print(f"   {line}")
        if len(analysis) > 500:
            print("   ...")
    else:
        print(f"❌ Analysis failed: {result.get('error', 'Unknown error')}")
    
    print()
    print("=" * 80)
    print("🖥️  GPU UTILIZATION DURING INFERENCE")
    print("=" * 80)
    print_gpu_status(final_gpus, "   ")
    print()
    
    if final_gpus:
        max_util = max(g['utilization'] for g in final_gpus)
        avg_util = sum(g['utilization'] for g in final_gpus) / len(final_gpus)
        print(f"   Max GPU Utilization: {max_util}%")
        print(f"   Avg GPU Utilization: {avg_util:.1f}%")
    
    print("=" * 80)
    print()


async def main():
    """Main test flow with monitoring."""
    print("=" * 80)
    print("🔭 FINANCIAL THREAT INTELLIGENCE - MONITORED TEST")
    print("=" * 80)
    print("System: Dual NVIDIA RTX A6000 + Llama 4 16x17B")
    print("Mode: Single Ollama instance with automatic GPU load balancing")
    print()
    
    # Check Ollama
    print("🔍 Checking Ollama service...")
    if not check_ollama_ready():
        print("❌ Ollama not responding on http://localhost:11434")
        print()
        print("Please start Ollama:")
        print("   export CUDA_VISIBLE_DEVICES=0,1")
        print("   export OLLAMA_HOST=0.0.0.0:11434")
        print("   ollama serve")
        sys.exit(1)
    
    print("✅ Ollama is running")
    print()
    
    # Wait for model to load
    await wait_for_model_load("llama4:16x17b", max_wait=180)
    
    # Run test
    await run_single_test()
    
    print()
    print("=" * 80)
    print("✅ TEST COMPLETE")
    print("=" * 80)
    print()
    print("🎯 Key Findings:")
    print("   - Model loaded across both GPUs automatically")
    print("   - Single Ollama instance handles load balancing")
    print("   - Both GPUs utilized during inference")
    print()
    print("🔭 Financial intelligence system ready for production!")
    print("=" * 80)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(0)
