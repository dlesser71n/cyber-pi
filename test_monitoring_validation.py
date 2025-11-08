#!/usr/bin/env python3
"""
Quick validation test for monitoring infrastructure
Tests basic functionality without requiring full integration
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from monitoring.periscope_monitor import PeriscopeMonitor, HealthStatus, CircuitState


async def test_monitor_basic():
    """Test basic monitor functionality"""
    print("🧪 Testing basic monitor functionality...")
    
    # Initialize monitor (without Redis for quick test)
    monitor = PeriscopeMonitor(
        redis_host="localhost",
        redis_port=32379,
        enable_circuit_breaker=True
    )
    
    print("✅ Monitor created")
    
    # Test metrics recording
    monitor.record_threat_ingested()
    monitor.record_threat_converted()
    monitor.record_threat_skipped("test")
    
    print("✅ Metrics recording works")
    
    # Test metrics retrieval
    summary = monitor.get_metrics_summary()
    assert summary['threats']['ingested'] == 1
    assert summary['threats']['converted'] == 1
    assert summary['threats']['skipped'] == 1
    
    print("✅ Metrics retrieval works")
    
    # Test system stats
    sys_stats = monitor.get_system_stats()
    assert 'process_memory_mb' in sys_stats
    assert 'process_cpu_percent' in sys_stats
    
    print("✅ System stats work")
    
    # Test health status (without Redis initialization)
    health = monitor.get_health_status()
    assert 'status' in health
    assert 'metrics' in health
    
    print("✅ Health status works")
    
    # Test circuit breaker
    assert monitor.circuit_breaker.state == CircuitState.CLOSED
    print("✅ Circuit breaker initialized")
    
    return True


async def test_async_operation():
    """Test async operation wrapper"""
    print("\n🧪 Testing async operation wrapper...")
    
    monitor = PeriscopeMonitor()
    
    # Test successful operation
    async def successful_op():
        await asyncio.sleep(0.01)
        return "success"
    
    result = await monitor.execute_with_retry(
        successful_op,
        operation_name="test_success"
    )
    
    assert result == "success"
    print("✅ Successful operation works")
    
    # Test failing operation
    async def failing_op():
        raise ValueError("Test error")
    
    try:
        await monitor.execute_with_retry(
            failing_op,
            operation_name="test_failure"
        )
        assert False, "Should have raised exception"
    except ValueError:
        print("✅ Failing operation handled correctly")
    
    # Check metrics
    summary = monitor.get_metrics_summary()
    assert summary['requests']['successful'] >= 1
    assert summary['requests']['failed'] >= 1
    
    print("✅ Retry logic works")
    
    return True


async def test_gpu_stats():
    """Test GPU monitoring (may fail if no GPU)"""
    print("\n🧪 Testing GPU monitoring...")
    
    monitor = PeriscopeMonitor()
    
    gpu_stats = await monitor.get_gpu_stats()
    
    if 'error' in gpu_stats:
        print("⚠️  GPU stats unavailable (expected if no nvidia-smi)")
    else:
        assert 'gpu_count' in gpu_stats
        print(f"✅ GPU monitoring works ({gpu_stats['gpu_count']} GPUs detected)")
    
    return True


async def main():
    """Run all validation tests"""
    print("=" * 80)
    print("🔬 MONITORING INFRASTRUCTURE VALIDATION")
    print("=" * 80)
    
    tests = [
        ("Basic Monitor", test_monitor_basic),
        ("Async Operations", test_async_operation),
        ("GPU Stats", test_gpu_stats),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            await test_func()
            passed += 1
        except Exception as e:
            print(f"❌ {name} failed: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 80)
    print(f"📊 RESULTS: {passed} passed, {failed} failed")
    print("=" * 80)
    
    if failed == 0:
        print("\n✅ ALL TESTS PASSED - Monitoring infrastructure is working!")
        return 0
    else:
        print(f"\n❌ {failed} test(s) failed - needs attention")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
