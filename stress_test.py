#!/usr/bin/env python3
"""
Cyber-Pi System Stress Test
Push the system to its absolute limits
"""

import asyncio
import time
import psutil
import threading
import multiprocessing
import concurrent.futures
import json
import logging
from typing import List, Dict, Any
from dataclasses import dataclass
import sys
import os

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
class StressTestResults:
    """Results from stress testing"""
    test_name: str
    duration: float
    operations_completed: int
    operations_per_second: float
    memory_peak_mb: float
    cpu_peak_percent: float
    errors: int
    success: bool

class CyberPiStressTest(EnterpriseBase):
    """Comprehensive stress testing suite"""
    
    def __init__(self):
        super().__init__()
        self.monitoring = EnterpriseMonitoring()
        self.results: List[StressTestResults] = []
        
        logger.info("🔥 CYBER-PI STRESS TEST INITIALIZED")
        logger.info(f"CPU Cores: {settings.cpu_cores}")
        logger.info(f"Max Workers: {settings.max_workers}")
        logger.info(f"GPU Devices: {settings.gpu_devices}")
        logger.info(f"Total RAM: {settings.total_ram}GB")
    
    def cpu_stress_test(self, duration_seconds: int = 60) -> StressTestResults:
        """Max out all CPU cores"""
        logger.info(f"🔥 CPU STRESS TEST - {duration_seconds}s")
        
        start_time = time.time()
        operations = 0
        errors = 0
        
        def cpu_burn():
            """Intensive CPU calculation"""
            nonlocal operations
            try:
                # Prime number calculation - CPU intensive
                def is_prime(n):
                    if n < 2:
                        return False
                    for i in range(2, int(n ** 0.5) + 1):
                        if n % i == 0:
                            return False
                    return True
                
                count = 0
                num = 2
                while time.time() - start_time < duration_seconds:
                    if is_prime(num):
                        count += 1
                    num += 1
                    operations += 1
                    
            except Exception as e:
                nonlocal errors
                errors += 1
                logger.error(f"CPU worker error: {e}")
        
        # Start CPU burn on all cores
        threads = []
        for _ in range(settings.cpu_cores):
            t = threading.Thread(target=cpu_burn)
            t.start()
            threads.append(t)
        
        # Monitor resources
        peak_cpu = 0
        peak_memory = 0
        
        while any(t.is_alive() for t in threads):
            current_cpu = psutil.cpu_percent(interval=0.1)
            current_memory = psutil.virtual_memory().used / 1024 / 1024
            
            peak_cpu = max(peak_cpu, current_cpu)
            peak_memory = max(peak_memory, current_memory)
            time.sleep(0.1)
        
        # Wait for all threads
        for t in threads:
            t.join()
        
        end_time = time.time()
        actual_duration = end_time - start_time
        
        result = StressTestResults(
            test_name="CPU Stress Test",
            duration=actual_duration,
            operations_completed=operations,
            operations_per_second=operations / actual_duration,
            memory_peak_mb=peak_memory,
            cpu_peak_percent=peak_cpu,
            errors=errors,
            success=errors == 0
        )
        
        self.results.append(result)
        return result
    
    def memory_stress_test(self, target_gb: float = 100) -> StressTestResults:
        """Allocate massive amounts of memory"""
        logger.info(f"💾 MEMORY STRESS TEST - {target_gb}GB target")
        
        start_time = time.time()
        operations = 0
        errors = 0
        memory_chunks = []
        
        try:
            # Allocate memory in chunks
            chunk_size_mb = 100  # 100MB chunks
            chunk_size_bytes = chunk_size_mb * 1024 * 1024
            target_bytes = target_gb * 1024 * 1024 * 1024
            
            allocated = 0
            while allocated < target_bytes:
                # Allocate memory chunk
                chunk = bytearray(chunk_size_bytes)
                memory_chunks.append(chunk)
                allocated += chunk_size_bytes
                operations += 1
                
                # Fill with random data to ensure actual allocation
                for i in range(0, len(chunk), 4096):
                    chunk[i] = operations % 256
                
                # Monitor memory usage
                current_memory = psutil.virtual_memory().percent
                if current_memory > 95:  # Don't crash the system
                    logger.warning(f"Memory usage at {current_memory}%, stopping allocation")
                    break
                
                if operations % 10 == 0:
                    logger.info(f"Allocated {allocated / 1024 / 1024 / 1024:.1f}GB")
        
        except MemoryError:
            logger.warning("MemoryError caught - system limit reached")
        except Exception as e:
            errors += 1
            logger.error(f"Memory stress test error: {e}")
        
        end_time = time.time()
        peak_memory = psutil.virtual_memory().used / 1024 / 1024
        
        # Clean up memory
        memory_chunks.clear()
        
        result = StressTestResults(
            test_name="Memory Stress Test",
            duration=end_time - start_time,
            operations_completed=operations,
            operations_per_second=operations / (end_time - start_time),
            memory_peak_mb=peak_memory,
            cpu_peak_percent=psutil.cpu_percent(),
            errors=errors,
            success=errors == 0
        )
        
        self.results.append(result)
        return result
    
    def concurrent_operations_test(self, concurrent_operations: int = 1000) -> StressTestResults:
        """Test massive concurrent operations"""
        logger.info(f"⚡ CONCURRENT OPERATIONS TEST - {concurrent_operations} concurrent ops")
        
        start_time = time.time()
        operations = 0
        errors = 0
        
        def intensive_operation():
            """Simulate intensive threat intelligence processing"""
            nonlocal operations, errors
            try:
                # Simulate complex data processing
                data = []
                for i in range(1000):
                    # Complex string operations
                    text = "THREAT_INTELLIGENCE_DATA_" * 100
                    processed = text.lower().replace('_', ' ').strip()
                    data.append(processed)
                    operations += 1
                
                # Simulate JSON processing
                for i in range(100):
                    json_data = {
                        "cve_id": f"CVE-2024-{i:04d}",
                        "severity": "HIGH",
                        "description": "Test vulnerability data",
                        "indicators": [f"indicator_{j}" for j in range(50)]
                    }
                    json.dumps(json_data)
                    operations += 1
                    
            except Exception as e:
                errors += 1
        
        # Execute with ThreadPoolExecutor
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_operations) as executor:
            futures = [executor.submit(intensive_operation) for _ in range(concurrent_operations)]
            
            # Monitor while executing
            peak_cpu = 0
            peak_memory = 0
            
            for future in concurrent.futures.as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    errors += 1
                
                current_cpu = psutil.cpu_percent()
                current_memory = psutil.virtual_memory().used / 1024 / 1024
                peak_cpu = max(peak_cpu, current_cpu)
                peak_memory = max(peak_memory, current_memory)
        
        end_time = time.time()
        
        result = StressTestResults(
            test_name="Concurrent Operations Test",
            duration=end_time - start_time,
            operations_completed=operations,
            operations_per_second=operations / (end_time - start_time),
            memory_peak_mb=peak_memory,
            cpu_peak_percent=peak_cpu,
            errors=errors,
            success=errors == 0
        )
        
        self.results.append(result)
        return result
    
    def async_io_stress_test(self, concurrent_connections: int = 10000) -> StressTestResults:
        """Test async I/O limits"""
        logger.info(f"🌐 ASYNC I/O STRESS TEST - {concurrent_connections} concurrent connections")
        
        async def simulate_network_operation():
            """Simulate network I/O operation"""
            try:
                # Simulate network delay
                await asyncio.sleep(0.01)
                
                # Simulate data processing
                data = "x" * 10000  # 10KB of data
                processed = data.encode('utf-8')
                processed = processed.decode('utf-8')
                return True
            except Exception:
                return False
        
        async def run_stress_test():
            """Run the async stress test"""
            start_time = time.time()
            operations = 0
            errors = 0
            
            # Create massive concurrent tasks
            tasks = []
            for _ in range(concurrent_connections):
                task = asyncio.create_task(simulate_network_operation())
                tasks.append(task)
            
            # Execute all tasks concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, Exception):
                    errors += 1
                elif result:
                    operations += 1
                else:
                    errors += 1
            
            return operations, errors
        
        # Run the test
        start_time = time.time()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            operations, errors = loop.run_until_complete(run_stress_test())
        finally:
            loop.close()
        
        end_time = time.time()
        
        result = StressTestResults(
            test_name="Async I/O Stress Test",
            duration=end_time - start_time,
            operations_completed=operations,
            operations_per_second=operations / (end_time - start_time),
            memory_peak_mb=psutil.virtual_memory().used / 1024 / 1024,
            cpu_peak_percent=psutil.cpu_percent(),
            errors=errors,
            success=errors == 0
        )
        
        self.results.append(result)
        return result
    
    def run_all_stress_tests(self) -> List[StressTestResults]:
        """Run comprehensive stress test suite"""
        logger.info("🔥🔥🔥 STARTING COMPREHENSIVE STRESS TEST SUITE 🔥🔥🔥")
        
        # Test 1: CPU Stress
        cpu_result = self.cpu_stress_test(duration_seconds=30)
        self.print_result(cpu_result)
        
        # Test 2: Memory Stress
        memory_result = self.memory_stress_test(target_gb=50)  # Conservative to avoid crash
        self.print_result(memory_result)
        
        # Test 3: Concurrent Operations
        concurrent_result = self.concurrent_operations_test(concurrent_operations=500)
        self.print_result(concurrent_result)
        
        # Test 4: Async I/O Stress
        async_result = self.async_io_stress_test(concurrent_connections=5000)
        self.print_result(async_result)
        
        logger.info("🔥🔥🔥 STRESS TEST SUITE COMPLETED 🔥🔥🔥")
        return self.results
    
    def print_result(self, result: StressTestResults):
        """Print individual test result"""
        status = "✅ PASS" if result.success else "❌ FAIL"
        logger.info(f"\n{status} {result.test_name}")
        logger.info(f"  Duration: {result.duration:.2f}s")
        logger.info(f"  Operations: {result.operations_completed:,}")
        logger.info(f"  Throughput: {result.operations_per_second:.2f} ops/sec")
        logger.info(f"  Peak Memory: {result.memory_peak_mb:.1f}MB")
        logger.info(f"  Peak CPU: {result.cpu_peak_percent:.1f}%")
        logger.info(f"  Errors: {result.errors}")
    
    def print_summary(self):
        """Print comprehensive summary"""
        logger.info("\n" + "="*80)
        logger.info("🔥 CYBER-PI STRESS TEST SUMMARY")
        logger.info("="*80)
        
        total_ops = sum(r.operations_completed for r in self.results)
        total_errors = sum(r.errors for r in self.results)
        total_duration = sum(r.duration for r in self.results)
        
        logger.info(f"Total Operations: {total_ops:,}")
        logger.info(f"Total Errors: {total_errors}")
        logger.info(f"Total Duration: {total_duration:.2f}s")
        logger.info(f"Average Throughput: {total_ops / total_duration:.2f} ops/sec")
        
        logger.info("\nIndividual Test Results:")
        for result in self.results:
            status = "✅" if result.success else "❌"
            logger.info(f"  {status} {result.test_name}: {result.operations_per_second:.2f} ops/sec")
        
        # System limits discovered
        logger.info("\n🎯 SYSTEM LIMITS DISCOVERED:")
        for result in self.results:
            logger.info(f"  {result.test_name}:")
            logger.info(f"    Max Operations/sec: {result.operations_per_second:.2f}")
            logger.info(f"    Peak Memory: {result.memory_peak_mb:.1f}MB")
            logger.info(f"    Peak CPU: {result.cpu_peak_percent:.1f}%")

def main():
    """Main stress test execution"""
    stress_test = CyberPiStressTest()
    results = stress_test.run_all_stress_tests()
    stress_test.print_summary()
    
    # Save results to file
    with open('stress_test_results.json', 'w') as f:
        json.dump([vars(r) for r in results], f, indent=2)
    
    logger.info("\n📊 Results saved to stress_test_results.json")

if __name__ == "__main__":
    main()
