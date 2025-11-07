#!/usr/bin/env python3
"""
Cyber-Pi 256GB Memory Stress Test
Push the 768GB system to 256GB memory usage
"""

import time
import psutil
import gc
import logging
import threading
import numpy as np
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
class MemoryStressResults:
    """Results from memory stress testing"""
    test_name: str
    target_gb: float
    allocated_gb: float
    peak_memory_gb: float
    duration_seconds: float
    allocation_rate_mb_per_sec: float
    system_stability: str
    success: bool

class CyberPiMemoryStressTest(EnterpriseBase):
    """256GB Memory stress testing for 768GB system"""
    
    def __init__(self):
        super().__init__()
        self.monitoring = EnterpriseMonitoring()
        self.results: List[MemoryStressResults] = []
        
        logger.info("🔥🔥🔥 CYBER-PI 256GB MEMORY STRESS TEST INITIALIZED 🔥🔥🔥")
        logger.info(f"System RAM: {settings.total_ram}GB")
        logger.info(f"Target: 256GB (33% of total capacity)")
        logger.info("⚠️  WARNING: This will allocate massive amounts of memory!")
    
    def gradual_memory_allocation(self, target_gb: float = 256.0, chunk_size_mb: int = 500) -> MemoryStressResults:
        """Gradually allocate memory up to target with monitoring"""
        logger.info(f"💾 GRADUAL MEMORY ALLOCATION - {target_gb}GB TARGET")
        
        start_time = time.time()
        allocated_mb = 0
        memory_chunks = []
        system_stability = "STABLE"
        
        try:
            target_mb = target_gb * 1024
            
            while allocated_mb < target_mb and system_stability == "STABLE":
                try:
                    # Allocate memory chunk
                    chunk_size_bytes = chunk_size_mb * 1024 * 1024
                    
                    # Create numpy array for efficient memory usage
                    chunk = np.random.bytes(chunk_size_bytes)
                    memory_chunks.append(chunk)
                    
                    allocated_mb += chunk_size_mb
                    
                    # Monitor system health
                    memory_info = psutil.virtual_memory()
                    current_memory_percent = memory_info.percent
                    current_memory_gb = memory_info.used / 1024 / 1024 / 1024
                    
                    # Check stability thresholds
                    if current_memory_percent > 95:
                        system_stability = "CRITICAL"
                        logger.warning(f"CRITICAL: Memory at {current_memory_percent:.1f}%")
                        break
                    elif current_memory_percent > 85:
                        system_stability = "WARNING"
                        logger.warning(f"WARNING: Memory at {current_memory_percent:.1f}%")
                    elif current_memory_percent > 75:
                        system_stability = "CAUTION"
                        logger.info(f"CAUTION: Memory at {current_memory_percent:.1f}%")
                    
                    # Progress reporting
                    if allocated_mb % 5000 == 0:  # Every 5GB
                        logger.info(f"Allocated: {allocated_mb/1024:.1f}GB / {target_gb}GB ({allocated_mb/target_mb*100:.1f}%)")
                        logger.info(f"System Memory: {current_memory_gb:.1f}GB ({current_memory_percent:.1f}%)")
                        logger.info(f"Available: {memory_info.available/1024/1024/1024:.1f}GB")
                    
                    # Brief pause to allow system stabilization
                    time.sleep(0.1)
                    
                except MemoryError:
                    system_stability = "OUT_OF_MEMORY"
                    logger.error("MemoryError: Cannot allocate more memory")
                    break
                except Exception as e:
                    logger.error(f"Allocation error: {e}")
                    system_stability = "UNSTABLE"
                    break
        
        except Exception as e:
            logger.error(f"Critical error in memory allocation: {e}")
            system_stability = "CRITICAL"
        
        end_time = time.time()
        duration = end_time - start_time
        allocated_gb = allocated_mb / 1024
        peak_memory_gb = psutil.virtual_memory().used / 1024 / 1024 / 1024
        allocation_rate = allocated_mb / duration if duration > 0 else 0
        
        result = MemoryStressResults(
            test_name="Gradual Memory Allocation",
            target_gb=target_gb,
            allocated_gb=allocated_gb,
            peak_memory_gb=peak_memory_gb,
            duration_seconds=duration,
            allocation_rate_mb_per_sec=allocation_rate,
            system_stability=system_stability,
            success=allocated_gb >= target_gb * 0.9 and system_stability != "CRITICAL"
        )
        
        self.results.append(result)
        
        # Memory cleanup
        logger.info("Starting memory cleanup...")
        self.cleanup_memory_chunks(memory_chunks)
        
        return result
    
    def burst_memory_test(self, burst_gb: float = 50.0, num_bursts: int = 5) -> MemoryStressResults:
        """Test memory with sudden burst allocations"""
        logger.info(f"💥 BURST MEMORY TEST - {burst_gb}GB x {num_bursts} bursts")
        
        start_time = time.time()
        total_allocated_gb = 0
        memory_bursts = []
        system_stability = "STABLE"
        
        try:
            for burst_num in range(num_bursts):
                logger.info(f"Executing burst {burst_num + 1}/{num_bursts}")
                
                # Allocate large burst
                burst_size_mb = burst_gb * 1024
                burst_chunks = []
                
                for chunk_mb in range(0, int(burst_size_mb), 1000):  # 1GB chunks
                    try:
                        chunk = np.random.bytes(1000 * 1024 * 1024)  # 1GB
                        burst_chunks.append(chunk)
                        
                        # Monitor during burst
                        memory_percent = psutil.virtual_memory().percent
                        if memory_percent > 95:
                            system_stability = "CRITICAL"
                            logger.warning(f"CRITICAL during burst: {memory_percent:.1f}%")
                            break
                            
                    except MemoryError:
                        system_stability = "OUT_OF_MEMORY"
                        logger.warning(f"Out of memory during burst {burst_num + 1}")
                        break
                
                memory_bursts.extend(burst_chunks)
                burst_allocated_gb = len(burst_chunks) * 1000 / 1024
                total_allocated_gb += burst_allocated_gb
                
                current_memory_gb = psutil.virtual_memory().used / 1024 / 1024 / 1024
                logger.info(f"Burst {burst_num + 1} completed: {burst_allocated_gb:.1f}GB allocated")
                logger.info(f"Current system memory: {current_memory_gb:.1f}GB")
                
                # Hold burst for 10 seconds
                time.sleep(10)
                
                if system_stability == "CRITICAL":
                    break
        
        except Exception as e:
            logger.error(f"Burst test error: {e}")
            system_stability = "CRITICAL"
        
        end_time = time.time()
        duration = end_time - start_time
        peak_memory_gb = psutil.virtual_memory().used / 1024 / 1024 / 1024
        allocation_rate = total_allocated_gb * 1024 / duration if duration > 0 else 0
        
        result = MemoryStressResults(
            test_name="Burst Memory Test",
            target_gb=burst_gb * num_bursts,
            allocated_gb=total_allocated_gb,
            peak_memory_gb=peak_memory_gb,
            duration_seconds=duration,
            allocation_rate_mb_per_sec=allocation_rate,
            system_stability=system_stability,
            success=total_allocated_gb >= (burst_gb * num_bursts) * 0.8 and system_stability != "CRITICAL"
        )
        
        self.results.append(result)
        
        # Cleanup
        self.cleanup_memory_chunks(memory_bursts)
        
        return result
    
    def sustained_memory_pressure(self, target_gb: float = 200.0, hold_time: int = 300) -> MemoryStressResults:
        """Allocate memory and hold for sustained period"""
        logger.info(f"⏱️ SUSTAINED MEMORY PRESSURE - {target_gb}GB for {hold_time}s")
        
        start_time = time.time()
        allocated_mb = 0
        memory_chunks = []
        system_stability = "STABLE"
        
        try:
            target_mb = target_gb * 1024
            
            # Allocation phase
            logger.info("Allocation phase starting...")
            while allocated_mb < target_mb and system_stability == "STABLE":
                try:
                    chunk = np.random.bytes(100 * 1024 * 1024)  # 100MB chunks
                    memory_chunks.append(chunk)
                    allocated_mb += 100
                    
                    memory_percent = psutil.virtual_memory().percent
                    if memory_percent > 90:
                        system_stability = "WARNING"
                        logger.warning(f"High memory usage: {memory_percent:.1f}%")
                    elif memory_percent > 95:
                        system_stability = "CRITICAL"
                        break
                    
                    if allocated_mb % 10000 == 0:  # Every 10GB
                        logger.info(f"Allocated: {allocated_mb/1024:.1f}GB")
                    
                except MemoryError:
                    system_stability = "OUT_OF_MEMORY"
                    break
            
            allocated_gb = allocated_mb / 1024
            logger.info(f"Allocation complete: {allocated_gb:.1f}GB allocated")
            logger.info(f"Holding memory for {hold_time} seconds...")
            
            # Hold phase
            hold_start = time.time()
            last_check = hold_start
            
            while time.time() - hold_start < hold_time and system_stability != "CRITICAL":
                time.sleep(5)  # Check every 5 seconds
                
                current_time = time.time()
                if current_time - last_check >= 30:  # Report every 30 seconds
                    memory_percent = psutil.virtual_memory().percent
                    current_memory_gb = psutil.virtual_memory().used / 1024 / 1024 / 1024
                    elapsed = current_time - hold_start
                    remaining = hold_time - elapsed
                    
                    logger.info(f"Holding: {elapsed:.0f}s elapsed, {remaining:.0f}s remaining")
                    logger.info(f"Memory: {current_memory_gb:.1f}GB ({memory_percent:.1f}%)")
                    
                    if memory_percent > 95:
                        system_stability = "CRITICAL"
                        logger.error("CRITICAL: Memory usage too high during hold")
                        break
                    
                    last_check = current_time
        
        except Exception as e:
            logger.error(f"Sustained pressure test error: {e}")
            system_stability = "CRITICAL"
        
        end_time = time.time()
        duration = end_time - start_time
        peak_memory_gb = psutil.virtual_memory().used / 1024 / 1024 / 1024
        allocation_rate = allocated_mb / duration if duration > 0 else 0
        
        result = MemoryStressResults(
            test_name="Sustained Memory Pressure",
            target_gb=target_gb,
            allocated_gb=allocated_mb / 1024,
            peak_memory_gb=peak_memory_gb,
            duration_seconds=duration,
            allocation_rate_mb_per_sec=allocation_rate,
            system_stability=system_stability,
            success=allocated_mb / 1024 >= target_gb * 0.9 and system_stability != "CRITICAL"
        )
        
        self.results.append(result)
        
        # Cleanup
        logger.info("Cleaning up sustained memory allocation...")
        self.cleanup_memory_chunks(memory_chunks)
        
        return result
    
    def cleanup_memory_chunks(self, chunks: List):
        """Clean up memory chunks safely"""
        logger.info("Cleaning up memory chunks...")
        total_chunks = len(chunks)
        
        # Clean up in batches to avoid system shock
        batch_size = 100
        for i in range(0, total_chunks, batch_size):
            batch_end = min(i + batch_size, total_chunks)
            del chunks[i:batch_end]
            
            # Force garbage collection
            gc.collect()
            
            # Brief pause
            time.sleep(0.1)
            
            if batch_end % 1000 == 0:
                memory_percent = psutil.virtual_memory().percent
                logger.info(f"Cleanup progress: {batch_end}/{total_chunks}, Memory: {memory_percent:.1f}%")
        
        # Final cleanup
        chunks.clear()
        gc.collect()
        
        final_memory = psutil.virtual_memory().used / 1024 / 1024 / 1024
        logger.info(f"Cleanup complete. Final memory usage: {final_memory:.1f}GB")
    
    def run_256gb_memory_tests(self) -> List[MemoryStressResults]:
        """Run comprehensive 256GB memory test suite"""
        logger.info("🔥🔥🔥 STARTING 256GB MEMORY STRESS TEST SUITE 🔥🔥🔥")
        logger.info("⚠️  WARNING: This will test up to 1/3 of system capacity!")
        
        # Test 1: Gradual allocation to 256GB
        gradual_result = self.gradual_memory_allocation(target_gb=256.0, chunk_size_mb=1000)
        self.print_memory_result(gradual_result)
        
        # Wait for system recovery
        logger.info("Waiting 30 seconds for system recovery...")
        time.sleep(30)
        
        # Test 2: Burst tests (smaller scale to be safe)
        burst_result = self.burst_memory_test(burst_gb=20.0, num_bursts=3)
        self.print_memory_result(burst_result)
        
        # Wait for system recovery
        logger.info("Waiting 30 seconds for system recovery...")
        time.sleep(30)
        
        # Test 3: Sustained pressure at 150GB
        sustained_result = self.sustained_memory_pressure(target_gb=150.0, hold_time=120)
        self.print_memory_result(sustained_result)
        
        logger.info("🔥🔥🔥 256GB MEMORY STRESS TEST SUITE COMPLETED 🔥🔥🔥")
        return self.results
    
    def print_memory_result(self, result: MemoryStressResults):
        """Print memory test result"""
        status = "✅ PASS" if result.success else "❌ FAIL"
        stability_emoji = "✅" if result.system_stability == "STABLE" else "⚠️" if "WARNING" in result.system_stability else "❌"
        
        logger.info(f"\n{status} {result.test_name}")
        logger.info(f"  Target: {result.target_gb:.1f}GB")
        logger.info(f"  Allocated: {result.allocated_gb:.1f}GB ({result.allocated_gb/result.target_gb*100:.1f}%)")
        logger.info(f"  Peak Memory: {result.peak_memory_gb:.1f}GB")
        logger.info(f"  Duration: {result.duration_seconds:.1f}s")
        logger.info(f"  Allocation Rate: {result.allocation_rate_mb_per_sec:.1f}MB/s")
        logger.info(f"  Stability: {stability_emoji} {result.system_stability}")
    
    def print_memory_summary(self):
        """Print memory stress test summary"""
        logger.info("\n" + "="*80)
        logger.info("🔥🔥🔥 256GB MEMORY STRESS TEST SUMMARY 🔥🔥🔥")
        logger.info("="*80)
        
        total_allocated_gb = sum(r.allocated_gb for r in self.results)
        total_duration = sum(r.duration_seconds for r in self.results)
        
        logger.info(f"Total Memory Allocated: {total_allocated_gb:.1f}GB")
        logger.info(f"Total Duration: {total_duration:.1f}s")
        logger.info(f"Peak Memory Usage: {max(r.peak_memory_gb for r in self.results):.1f}GB")
        
        logger.info("\nMemory Test Results:")
        for result in self.results:
            status = "✅" if result.success else "❌"
            stability = "✅" if result.system_stability == "STABLE" else "⚠️" if "WARNING" in result.system_stability else "❌"
            logger.info(f"  {status} {result.test_name}: {result.allocated_gb:.1f}GB {stability}")
        
        logger.info("\n🎯 MEMORY LIMITS DISCOVERED:")
        for result in self.results:
            logger.info(f"  {result.test_name}:")
            logger.info(f"    Max Allocated: {result.allocated_gb:.1f}GB")
            logger.info(f"    Peak System: {result.peak_memory_gb:.1f}GB ({result.peak_memory_gb/settings.total_ram*100:.1f}%)")
            logger.info(f"    Allocation Rate: {result.allocation_rate_mb_per_sec:.1f}MB/s")
            logger.info(f"    System Stability: {result.system_stability}")

def main():
    """Main 256GB memory stress test execution"""
    logger.info("🚀 STARTING CYBER-PI 256GB MEMORY STRESS TESTS")
    logger.info(f"Testing system with {settings.total_ram}GB total RAM")
    logger.info("⚠️  WARNING: This will push memory usage to 256GB!")
    
    stress_test = CyberPiMemoryStressTest()
    results = stress_test.run_256gb_memory_tests()
    stress_test.print_memory_summary()
    
    # Save results to file
    import json
    with open('memory_stress_test_256gb_results.json', 'w') as f:
        json.dump([vars(r) for r in results], f, indent=2)
    
    logger.info("\n📊 256GB memory test results saved to memory_stress_test_256gb_results.json")
    logger.info("🔥🔥🔥 256GB MEMORY STRESS TESTING COMPLETED 🔥🔥🔥")

if __name__ == "__main__":
    main()
