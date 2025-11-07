#!/usr/bin/env python3
"""
EXTREME Cyber-Pi System Stress Test
Push the system beyond its design limits
"""

import asyncio
import time
import psutil
import threading
import multiprocessing
import concurrent.futures
import json
import logging
import numpy as np
from typing import List, Dict, Any
from dataclasses import dataclass
import sys
import os
import gc

sys.path.append('src')
from src.core.enterprise_base import EnterpriseBase
from src.core.monitoring import EnterpriseMonitoring
from config.settings import settings

# Configure aggressive logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class ExtremeStressTestResults:
    """Results from extreme stress testing"""
    test_name: str
    duration: float
    operations_completed: int
    operations_per_second: float
    memory_peak_mb: float
    cpu_peak_percent: float
    system_stability: str
    errors: int
    success: bool

class ExtremeCyberPiStressTest(EnterpriseBase):
    """Extreme stress testing suite - push beyond limits"""
    
    def __init__(self):
        super().__init__()
        self.monitoring = EnterpriseMonitoring()
        self.results: List[ExtremeStressTestResults] = []
        
        logger.info("🔥🔥🔥 EXTREME CYBER-PI STRESS TEST INITIALIZED 🔥🔥🔥")
        logger.info(f"CPU Cores: {settings.cpu_cores}")
        logger.info(f"Max Workers: {settings.max_workers}")
        logger.info(f"GPU Devices: {settings.gpu_devices}")
        logger.info(f"Total RAM: {settings.total_ram}GB")
        logger.info("⚠️  WARNING: This test will push the system to its absolute limits!")
    
    def extreme_cpu_burn(self, duration_seconds: int = 120) -> ExtremeStressTestResults:
        """Extreme CPU stress - max all cores with complex calculations"""
        logger.info(f"🔥🔥 EXTREME CPU BURN - {duration_seconds}s MAX INTENSITY")
        
        start_time = time.time()
        operations = 0
        errors = 0
        system_stability = "STABLE"
        
        def extreme_cpu_work():
            """Extremely CPU intensive calculations"""
            nonlocal operations, errors, system_stability
            try:
                # Multiple intensive algorithms running simultaneously
                def prime_sieve(limit):
                    """Prime number sieve - very CPU intensive"""
                    sieve = [True] * (limit + 1)
                    sieve[0] = sieve[1] = False
                    for i in range(2, int(limit ** 0.5) + 1):
                        if sieve[i]:
                            sieve[i*i::i] = [False] * len(sieve[i*i::i])
                    return [i for i, is_prime in enumerate(sieve) if is_prime]
                
                def fibonacci_sequence(n):
                    """Fibonacci calculation - CPU intensive"""
                    a, b = 0, 1
                    for _ in range(n):
                        a, b = b, a + b
                    return a
                
                def matrix_multiply(size):
                    """Matrix multiplication - CPU intensive"""
                    matrix_a = np.random.rand(size, size)
                    matrix_b = np.random.rand(size, size)
                    return np.dot(matrix_a, matrix_b)
                
                # Run all algorithms continuously
                count = 0
                while time.time() - start_time < duration_seconds:
                    try:
                        # Prime calculations
                        primes = prime_sieve(10000)
                        operations += len(primes)
                        
                        # Fibonacci calculations
                        fib = fibonacci_sequence(100)
                        operations += 100
                        
                        # Matrix operations
                        if count % 10 == 0:  # Every 10 iterations, do matrix math
                            result = matrix_multiply(50)
                            operations += 50 * 50 * 50  # Number of operations
                        
                        count += 1
                        
                    except Exception as e:
                        errors += 1
                        if errors > 100:
                            system_stability = "UNSTABLE"
                            break
                            
            except Exception as e:
                errors += 1
                system_stability = "CRITICAL"
                logger.error(f"Extreme CPU worker critical error: {e}")
        
        # Start extreme CPU burn on all cores + hyperthreading
        threads = []
        worker_count = settings.cpu_cores * 2  # Use hyperthreading
        
        for i in range(worker_count):
            t = threading.Thread(target=extreme_cpu_work)
            t.start()
            threads.append(t)
        
        # Monitor resources aggressively
        peak_cpu = 0
        peak_memory = 0
        stability_checks = 0
        
        while any(t.is_alive() for t in threads):
            current_cpu = psutil.cpu_percent(interval=0.1)
            current_memory = psutil.virtual_memory().used / 1024 / 1024
            
            peak_cpu = max(peak_cpu, current_cpu)
            peak_memory = max(peak_memory, current_memory)
            stability_checks += 1
            
            # Check system stability
            if current_memory / 1024 > settings.total_ram * 0.95:  # 95% of RAM
                system_stability = "MEMORY_CRITICAL"
                logger.warning("System approaching memory limit!")
            
            if stability_checks % 10 == 0:
                logger.info(f"CPU: {current_cpu:.1f}%, Memory: {current_memory/1024:.1f}GB")
            
            time.sleep(0.1)
        
        # Wait for all threads
        for t in threads:
            t.join()
        
        end_time = time.time()
        actual_duration = end_time - start_time
        
        result = ExtremeStressTestResults(
            test_name="Extreme CPU Burn",
            duration=actual_duration,
            operations_completed=operations,
            operations_per_second=operations / actual_duration,
            memory_peak_mb=peak_memory,
            cpu_peak_percent=peak_cpu,
            system_stability=system_stability,
            errors=errors,
            success=errors < 50 and system_stability != "CRITICAL"
        )
        
        self.results.append(result)
        return result
    
    def extreme_memory_pressure(self, target_gb: float = 200) -> ExtremeStressTestResults:
        """Extreme memory pressure - try to allocate massive amounts"""
        logger.info(f"💾💾 EXTREME MEMORY PRESSURE - {target_gb}GB TARGET")
        
        start_time = time.time()
        operations = 0
        errors = 0
        system_stability = "STABLE"
        memory_chunks = []
        
        try:
            # Allocate memory in different sizes to find system limits
            chunk_sizes = [1, 10, 50, 100, 500]  # MB
            chunk_index = 0
            allocated_mb = 0
            
            while allocated_mb < target_gb * 1024 and system_stability == "STABLE":
                chunk_size_mb = chunk_sizes[chunk_index % len(chunk_sizes)]
                chunk_size_bytes = chunk_size_mb * 1024 * 1024
                
                try:
                    # Allocate and fill memory chunk
                    chunk = bytearray(chunk_size_bytes)
                    
                    # Fill with pseudo-random data to ensure actual allocation
                    for i in range(0, len(chunk), 4096):
                        chunk[i] = (allocated_mb + i) % 256
                    
                    memory_chunks.append(chunk)
                    allocated_mb += chunk_size_mb
                    operations += 1
                    
                    # Monitor system health
                    current_memory_percent = psutil.virtual_memory().percent
                    if current_memory_percent > 98:
                        system_stability = "MEMORY_CRITICAL"
                        logger.warning(f"Memory at {current_memory_percent}% - CRITICAL LEVEL")
                        break
                    elif current_memory_percent > 90:
                        system_stability = "MEMORY_WARNING"
                        logger.warning(f"Memory at {current_memory_percent}% - WARNING LEVEL")
                    
                    # Progress reporting
                    if operations % 20 == 0:
                        logger.info(f"Allocated: {allocated_mb/1024:.1f}GB, Memory: {current_memory_percent:.1f}%")
                    
                    chunk_index += 1
                    
                except MemoryError:
                    system_stability = "OUT_OF_MEMORY"
                    logger.warning("MemoryError - system out of memory!")
                    break
                except Exception as e:
                    errors += 1
                    if errors > 10:
                        system_stability = "UNSTABLE"
                        break
                    
        except Exception as e:
            errors += 1
            system_stability = "CRITICAL"
            logger.error(f"Extreme memory test critical error: {e}")
        
        end_time = time.time()
        peak_memory = psutil.virtual_memory().used / 1024 / 1024
        
        # Force garbage collection
        gc.collect()
        
        # Clean up memory gradually to avoid system crash
        logger.info("Cleaning up allocated memory...")
        for i in range(0, len(memory_chunks), 10):
            del memory_chunks[i:i+10]
            gc.collect()
            time.sleep(0.1)
        
        memory_chunks.clear()
        gc.collect()
        
        result = ExtremeStressTestResults(
            test_name="Extreme Memory Pressure",
            duration=end_time - start_time,
            operations_completed=operations,
            operations_per_second=operations / (end_time - start_time) if end_time > start_time else 0,
            memory_peak_mb=peak_memory,
            cpu_peak_percent=psutil.cpu_percent(),
            system_stability=system_stability,
            errors=errors,
            success=system_stability != "CRITICAL"
        )
        
        self.results.append(result)
        return result
    
    def extreme_concurrent_bombardment(self, concurrent_tasks: int = 2000) -> ExtremeStressTestResults:
        """Extreme concurrent operations - system bombardment"""
        logger.info(f"⚡⚡ EXTREME CONCURRENT BOMBARDMENT - {concurrent_tasks} CONCURRENT")
        
        start_time = time.time()
        operations = 0
        errors = 0
        system_stability = "STABLE"
        
        def extreme_intensive_task():
            """Extremely intensive task combining CPU, memory, and I/O"""
            nonlocal operations, errors
            try:
                # CPU intensive work
                for i in range(1000):
                    _ = i * i * i * i  # Power calculations
                
                # Memory intensive work
                data = []
                for i in range(100):
                    chunk = "x" * 10000
                    data.append(chunk)
                    operations += 1
                
                # I/O intensive work
                for i in range(50):
                    json_data = {
                        "id": i,
                        "data": "x" * 1000,
                        "nested": {"level1": {"level2": {"level3": "x" * 100}}}
                    }
                    serialized = json.dumps(json_data)
                    deserialized = json.loads(serialized)
                    operations += 1
                
                # Clean up
                del data
                
            except Exception as e:
                errors += 1
        
        # Execute extreme bombardment
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_tasks) as executor:
            # Submit all tasks
            futures = [executor.submit(extreme_intensive_task) for _ in range(concurrent_tasks)]
            
            # Monitor system health during execution
            peak_cpu = 0
            peak_memory = 0
            completed_tasks = 0
            
            for future in concurrent.futures.as_completed(futures):
                try:
                    future.result(timeout=30)  # 30 second timeout
                    completed_tasks += 1
                except concurrent.futures.TimeoutError:
                    errors += 1
                    system_stability = "TIMEOUT_ISSUES"
                except Exception as e:
                    errors += 1
                    if errors > 100:
                        system_stability = "UNSTABLE"
                
                # Monitor resources
                current_cpu = psutil.cpu_percent()
                current_memory = psutil.virtual_memory().used / 1024 / 1024
                peak_cpu = max(peak_cpu, current_cpu)
                peak_memory = max(peak_memory, current_memory)
                
                # Check system stability
                if current_memory / 1024 > settings.total_ram * 0.9:
                    system_stability = "MEMORY_PRESSURE"
                
                if completed_tasks % 100 == 0:
                    logger.info(f"Completed: {completed_tasks}/{concurrent_tasks}, CPU: {current_cpu:.1f}%")
        
        end_time = time.time()
        
        result = ExtremeStressTestResults(
            test_name="Extreme Concurrent Bombardment",
            duration=end_time - start_time,
            operations_completed=operations,
            operations_per_second=operations / (end_time - start_time),
            memory_peak_mb=peak_memory,
            cpu_peak_percent=peak_cpu,
            system_stability=system_stability,
            errors=errors,
            success=errors < concurrent_tasks * 0.1  # Less than 10% error rate
        )
        
        self.results.append(result)
        return result
    
    def extreme_async_tidal_wave(self, concurrent_connections: int = 20000) -> ExtremeStressTestResults:
        """Extreme async I/O - tidal wave of connections"""
        logger.info(f"🌊🌊 EXTREME ASYNC TIDAL WAVE - {concurrent_connections} CONNECTIONS")
        
        async def tidal_wave_operation():
            """Extreme async operation"""
            try:
                # Simulate complex network operations
                await asyncio.sleep(0.001)  # 1ms delay
                
                # Simulate data processing
                data = "THREAT_DATA_" * 1000
                processed = data.lower().replace('_', ' ')
                
                # Simulate JSON serialization
                json_data = {"threat": processed, "size": len(processed)}
                serialized = json.dumps(json_data)
                
                return True
            except Exception:
                return False
        
        async def run_tidal_wave():
            """Execute tidal wave of async operations"""
            start_time = time.time()
            operations = 0
            errors = 0
            
            # Create massive number of concurrent tasks
            tasks = []
            batch_size = 1000  # Process in batches to avoid overwhelming
            
            for batch_start in range(0, concurrent_connections, batch_size):
                batch_end = min(batch_start + batch_size, concurrent_connections)
                batch_tasks = []
                
                for i in range(batch_start, batch_end):
                    task = asyncio.create_task(tidal_wave_operation())
                    batch_tasks.append(task)
                
                # Execute batch
                results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                
                for result in results:
                    if isinstance(result, Exception):
                        errors += 1
                    elif result:
                        operations += 1
                    else:
                        errors += 1
                
                # Brief pause between batches
                await asyncio.sleep(0.01)
                
                if batch_end % 5000 == 0:
                    logger.info(f"Processed {batch_end}/{concurrent_connections} connections")
            
            return operations, errors
        
        # Run the tidal wave test
        start_time = time.time()
        
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            operations, errors = loop.run_until_complete(run_tidal_wave())
            loop.close()
        except Exception as e:
            logger.error(f"Tidal wave test error: {e}")
            errors += concurrent_connections  # Assume all failed
        
        end_time = time.time()
        
        result = ExtremeStressTestResults(
            test_name="Extreme Async Tidal Wave",
            duration=end_time - start_time,
            operations_completed=operations,
            operations_per_second=operations / (end_time - start_time),
            memory_peak_mb=psutil.virtual_memory().used / 1024 / 1024,
            cpu_peak_percent=psutil.cpu_percent(),
            system_stability="STABLE" if errors < concurrent_connections * 0.1 else "UNSTABLE",
            errors=errors,
            success=errors < concurrent_connections * 0.1
        )
        
        self.results.append(result)
        return result
    
    def run_extreme_stress_tests(self) -> List[ExtremeStressTestResults]:
        """Run extreme stress test suite"""
        logger.info("🔥🔥🔥🔥 STARTING EXTREME STRESS TEST SUITE 🔥🔥🔥🔥")
        logger.info("⚠️  WARNING: These tests will push the system to its absolute limits!")
        
        # Test 1: Extreme CPU Burn
        cpu_result = self.extreme_cpu_burn(duration_seconds=60)
        self.print_extreme_result(cpu_result)
        
        # Test 2: Extreme Memory Pressure
        memory_result = self.extreme_memory_pressure(target_gb=100)
        self.print_extreme_result(memory_result)
        
        # Test 3: Extreme Concurrent Bombardment
        concurrent_result = self.extreme_concurrent_bombardment(concurrent_tasks=1000)
        self.print_extreme_result(concurrent_result)
        
        # Test 4: Extreme Async Tidal Wave
        async_result = self.extreme_async_tidal_wave(concurrent_connections=10000)
        self.print_extreme_result(async_result)
        
        logger.info("🔥🔥🔥🔥 EXTREME STRESS TEST SUITE COMPLETED 🔥🔥🔥🔥")
        return self.results
    
    def print_extreme_result(self, result: ExtremeStressTestResults):
        """Print extreme test result"""
        status = "🔥 EXTREME PASS" if result.success else "💥 EXTREME FAIL"
        stability_emoji = "✅" if result.system_stability == "STABLE" else "⚠️" if "WARNING" in result.system_stability else "❌"
        
        logger.info(f"\n{status} {result.test_name}")
        logger.info(f"  Stability: {stability_emoji} {result.system_stability}")
        logger.info(f"  Duration: {result.duration:.2f}s")
        logger.info(f"  Operations: {result.operations_completed:,}")
        logger.info(f"  Throughput: {result.operations_per_second:.2f} ops/sec")
        logger.info(f"  Peak Memory: {result.memory_peak_mb:.1f}MB")
        logger.info(f"  Peak CPU: {result.cpu_peak_percent:.1f}%")
        logger.info(f"  Errors: {result.errors}")
    
    def print_extreme_summary(self):
        """Print extreme summary"""
        logger.info("\n" + "="*80)
        logger.info("🔥🔥🔥 EXTREME CYBER-PI STRESS TEST SUMMARY 🔥🔥🔥")
        logger.info("="*80)
        
        total_ops = sum(r.operations_completed for r in self.results)
        total_errors = sum(r.errors for r in self.results)
        total_duration = sum(r.duration for r in self.results)
        
        logger.info(f"Total Operations: {total_ops:,}")
        logger.info(f"Total Errors: {total_errors}")
        logger.info(f"Total Duration: {total_duration:.2f}s")
        logger.info(f"Average Throughput: {total_ops / total_duration:.2f} ops/sec")
        
        logger.info("\nExtreme Test Results:")
        for result in self.results:
            status = "🔥" if result.success else "💥"
            stability = "✅" if result.system_stability == "STABLE" else "⚠️" if "WARNING" in result.system_stability else "❌"
            logger.info(f"  {status} {result.test_name}: {result.operations_per_second:.2f} ops/sec {stability}")
        
        logger.info("\n🎯 SYSTEM EXTREME LIMITS DISCOVERED:")
        for result in self.results:
            logger.info(f"  {result.test_name}:")
            logger.info(f"    Max Operations/sec: {result.operations_per_second:.2f}")
            logger.info(f"    Peak Memory: {result.memory_peak_mb:.1f}MB ({result.memory_peak_mb/1024:.1f}GB)")
            logger.info(f"    Peak CPU: {result.cpu_peak_percent:.1f}%")
            logger.info(f"    System Stability: {result.system_stability}")

def main():
    """Main extreme stress test execution"""
    logger.info("🚀 STARTING EXTREME CYBER-PI STRESS TESTS")
    logger.info("⚠️  WARNING: This will push your system to its absolute limits!")
    
    stress_test = ExtremeCyberPiStressTest()
    results = stress_test.run_extreme_stress_tests()
    stress_test.print_extreme_summary()
    
    # Save results to file
    with open('extreme_stress_test_results.json', 'w') as f:
        json.dump([vars(r) for r in results], f, indent=2)
    
    logger.info("\n📊 Extreme results saved to extreme_stress_test_results.json")
    logger.info("🔥🔥🔥 EXTREME STRESS TESTING COMPLETED 🔥🔥🔥")

if __name__ == "__main__":
    main()
