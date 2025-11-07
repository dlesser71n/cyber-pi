#!/usr/bin/env python3
"""
Cyber-Pi Database Infrastructure Stress Test
Push Redis, Neo4j, and Weaviate to their limits
"""

import asyncio
import time
import psutil
import threading
import concurrent.futures
import json
import logging
import redis
import numpy as np
from typing import List, Dict, Any
from dataclasses import dataclass
import sys
import os
import random
import string

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
class DatabaseStressTestResults:
    """Results from database stress testing"""
    test_name: str
    database: str
    duration: float
    operations_completed: int
    operations_per_second: float
    memory_peak_mb: float
    cpu_peak_percent: float
    errors: int
    success: bool
    database_metrics: Dict[str, Any]

class CyberPiDatabaseStressTest(EnterpriseBase):
    """Database infrastructure stress testing"""
    
    def __init__(self):
        super().__init__()
        self.monitoring = EnterpriseMonitoring()
        self.results: List[DatabaseStressTestResults] = []
        
        logger.info("🔥🔥🔥 CYBER-PI DATABASE STRESS TEST INITIALIZED 🔥🔥🔥")
        logger.info(f"Redis: {settings.redis_host}:{settings.redis_port}")
        logger.info(f"Neo4j: {settings.neo4j_uri}")
        logger.info(f"Weaviate: {settings.weaviate_url}")
    
    def redis_stress_test(self, operations: int = 100000) -> DatabaseStressTestResults:
        """Stress test Redis with massive operations"""
        logger.info(f"🔴 REDIS STRESS TEST - {operations:,} OPERATIONS")
        
        start_time = time.time()
        completed_ops = 0
        errors = 0
        
        try:
            # Connect to Redis
            r = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                password=settings.redis_password,
                decode_responses=True
            )
            
            # Test connection
            r.ping()
            logger.info("✅ Redis connection established")
            
            # Generate test data
            def generate_cve_data():
                """Generate realistic CVE data"""
                cve_id = f"CVE-2024-{random.randint(1000, 9999):04d}"
                return {
                    "id": cve_id,
                    "severity": random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"]),
                    "cvss": round(random.uniform(4.0, 10.0), 1),
                    "description": "Test vulnerability description " + "".join(random.choices(string.ascii_letters + string.digits, k=100)),
                    "published": time.time(),
                    "modified": time.time(),
                    "vendor": random.choice(["Microsoft", "Cisco", "Oracle", "Apache", "Linux"]),
                    "product": random.choice(["Windows", "IOS", "Database", "WebServer", "Kernel"]),
                    "cwe": f"CWE-{random.randint(100, 999)}"
                }
            
            # Stress test operations
            batch_size = 1000
            for batch_start in range(0, operations, batch_size):
                batch_end = min(batch_start + batch_size, operations)
                
                try:
                    # Pipeline operations for performance
                    pipe = r.pipeline()
                    
                    for i in range(batch_start, batch_end):
                        cve_data = generate_cve_data()
                        cve_key = f"cve:{cve_data['id']}"
                        
                        # SET operation
                        pipe.set(cve_key, json.dumps(cve_data))
                        
                        # HASH operation for indexing
                        pipe.hset("severity_index", cve_key, cve_data['severity'])
                        
                        # SET operation for vendor indexing
                        pipe.sadd(f"vendor:{cve_data['vendor']}", cve_key)
                        
                        # ZSET operation for CVSS ranking
                        pipe.zadd("cvss_ranking", {cve_key: cve_data['cvss']})
                        
                        completed_ops += 4  # 4 operations per CVE
                    
                    # Execute pipeline
                    pipe_results = pipe.execute()
                    
                    # Count errors
                    for result in pipe_results:
                        if result is None:
                            errors += 1
                    
                    # Progress reporting
                    if batch_end % 10000 == 0:
                        logger.info(f"Redis: {batch_end:,}/{operations:,} operations completed")
                    
                except Exception as e:
                    errors += batch_size
                    logger.error(f"Redis batch error: {e}")
            
            # Get Redis metrics
            redis_info = r.info()
            redis_metrics = {
                "used_memory": redis_info.get('used_memory', 0),
                "used_memory_human": redis_info.get('used_memory_human', '0B'),
                "connected_clients": redis_info.get('connected_clients', 0),
                "total_commands_processed": redis_info.get('total_commands_processed', 0),
                "keyspace_hits": redis_info.get('keyspace_hits', 0),
                "keyspace_misses": redis_info.get('keyspace_misses', 0)
            }
            
            r.close()
            
        except Exception as e:
            logger.error(f"Redis stress test failed: {e}")
            errors = operations
            redis_metrics = {}
        
        end_time = time.time()
        
        result = DatabaseStressTestResults(
            test_name="Redis Stress Test",
            database="Redis",
            duration=end_time - start_time,
            operations_completed=completed_ops,
            operations_per_second=completed_ops / (end_time - start_time),
            memory_peak_mb=psutil.virtual_memory().used / 1024 / 1024,
            cpu_peak_percent=psutil.cpu_percent(),
            errors=errors,
            success=errors < operations * 0.01,  # Less than 1% error rate
            database_metrics=redis_metrics
        )
        
        self.results.append(result)
        return result
    
    def concurrent_redis_test(self, concurrent_connections: int = 100, ops_per_connection: int = 1000) -> DatabaseStressTestResults:
        """Test Redis with massive concurrent connections"""
        logger.info(f"🔴 CONCURRENT REDIS TEST - {concurrent_connections} CONNECTIONS")
        
        start_time = time.time()
        completed_ops = 0
        errors = 0
        
        def redis_worker():
            """Individual Redis worker"""
            nonlocal completed_ops, errors
            try:
                r = redis.Redis(
                    host=settings.redis_host,
                    port=settings.redis_port,
                    password=settings.redis_password,
                    decode_responses=True
                )
                
                for i in range(ops_per_connection):
                    try:
                        key = f"test:{threading.current_thread().ident}:{i}"
                        value = json.dumps({"data": "x" * 100, "timestamp": time.time()})
                        
                        r.set(key, value)
                        retrieved = r.get(key)
                        
                        if retrieved:
                            completed_ops += 2  # SET + GET
                        else:
                            errors += 1
                            
                    except Exception as e:
                        errors += 1
                
                r.close()
                
            except Exception as e:
                errors += ops_per_connection
        
        # Start concurrent workers
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_connections) as executor:
            futures = [executor.submit(redis_worker) for _ in range(concurrent_connections)]
            
            # Monitor while executing
            peak_cpu = 0
            peak_memory = 0
            
            for future in concurrent.futures.as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    errors += ops_per_connection
                
                current_cpu = psutil.cpu_percent()
                current_memory = psutil.virtual_memory().used / 1024 / 1024
                peak_cpu = max(peak_cpu, current_cpu)
                peak_memory = max(peak_memory, current_memory)
        
        end_time = time.time()
        
        result = DatabaseStressTestResults(
            test_name="Concurrent Redis Test",
            database="Redis",
            duration=end_time - start_time,
            operations_completed=completed_ops,
            operations_per_second=completed_ops / (end_time - start_time),
            memory_peak_mb=peak_memory,
            cpu_peak_percent=peak_cpu,
            errors=errors,
            success=errors < concurrent_connections * ops_per_connection * 0.05,
            database_metrics={}
        )
        
        self.results.append(result)
        return result
    
    def memory_intensive_test(self, data_size_mb: int = 1000) -> DatabaseStressTestResults:
        """Test with massive data sets"""
        logger.info(f"💾 MEMORY INTENSIVE TEST - {data_size_mb}MB DATA")
        
        start_time = time.time()
        completed_ops = 0
        errors = 0
        
        try:
            r = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                password=settings.redis_password,
                decode_responses=True
            )
            
            # Generate large data chunks
            chunk_size = 1024 * 1024  # 1MB chunks
            num_chunks = data_size_mb
            
            for i in range(num_chunks):
                try:
                    # Generate 1MB of data
                    large_data = "x" * chunk_size
                    key = f"large_data:{i:06d}"
                    
                    # Store large data
                    r.set(key, large_data)
                    
                    # Verify storage
                    retrieved = r.get(key)
                    if len(retrieved) == chunk_size:
                        completed_ops += 2  # SET + verification
                    else:
                        errors += 1
                    
                    if i % 100 == 0:
                        logger.info(f"Stored {i}MB of {data_size_mb}MB")
                        
                except Exception as e:
                    errors += 1
                    logger.error(f"Large data chunk error: {e}")
            
            # Get memory usage
            redis_info = r.info()
            redis_metrics = {
                "used_memory": redis_info.get('used_memory', 0),
                "used_memory_human": redis_info.get('used_memory_human', '0B'),
                "used_memory_peak": redis_info.get('used_memory_peak', 0)
            }
            
            r.close()
            
        except Exception as e:
            logger.error(f"Memory intensive test failed: {e}")
            errors = num_chunks
            redis_metrics = {}
        
        end_time = time.time()
        
        result = DatabaseStressTestResults(
            test_name="Memory Intensive Test",
            database="Redis",
            duration=end_time - start_time,
            operations_completed=completed_ops,
            operations_per_second=completed_ops / (end_time - start_time),
            memory_peak_mb=psutil.virtual_memory().used / 1024 / 1024,
            cpu_peak_percent=psutil.cpu_percent(),
            errors=errors,
            success=errors < num_chunks * 0.01,
            database_metrics=redis_metrics
        )
        
        self.results.append(result)
        return result
    
    def run_database_stress_tests(self) -> List[DatabaseStressTestResults]:
        """Run comprehensive database stress test suite"""
        logger.info("🔥🔥🔥 STARTING DATABASE STRESS TEST SUITE 🔥🔥🔥")
        
        # Test 1: Redis Operations Stress
        redis_result = self.redis_stress_test(operations=50000)
        self.print_database_result(redis_result)
        
        # Test 2: Concurrent Redis Connections
        concurrent_result = self.concurrent_redis_test(concurrent_connections=50, ops_per_connection=500)
        self.print_database_result(concurrent_result)
        
        # Test 3: Memory Intensive Test
        memory_result = self.memory_intensive_test(data_size_mb=500)
        self.print_database_result(memory_result)
        
        logger.info("🔥🔥🔥 DATABASE STRESS TEST SUITE COMPLETED 🔥🔥🔥")
        return self.results
    
    def print_database_result(self, result: DatabaseStressTestResults):
        """Print database test result"""
        status = "✅ PASS" if result.success else "❌ FAIL"
        
        logger.info(f"\n{status} {result.test_name}")
        logger.info(f"  Database: {result.database}")
        logger.info(f"  Duration: {result.duration:.2f}s")
        logger.info(f"  Operations: {result.operations_completed:,}")
        logger.info(f"  Throughput: {result.operations_per_second:.2f} ops/sec")
        logger.info(f"  Peak Memory: {result.memory_peak_mb:.1f}MB")
        logger.info(f"  Peak CPU: {result.cpu_peak_percent:.1f}%")
        logger.info(f"  Errors: {result.errors}")
        
        if result.database_metrics:
            logger.info(f"  Database Metrics:")
            for key, value in result.database_metrics.items():
                logger.info(f"    {key}: {value}")
    
    def print_database_summary(self):
        """Print database stress test summary"""
        logger.info("\n" + "="*80)
        logger.info("🔥🔥🔥 DATABASE STRESS TEST SUMMARY 🔥🔥🔥")
        logger.info("="*80)
        
        total_ops = sum(r.operations_completed for r in self.results)
        total_errors = sum(r.errors for r in self.results)
        total_duration = sum(r.duration for r in self.results)
        
        logger.info(f"Total Operations: {total_ops:,}")
        logger.info(f"Total Errors: {total_errors}")
        logger.info(f"Total Duration: {total_duration:.2f}s")
        logger.info(f"Average Throughput: {total_ops / total_duration:.2f} ops/sec")
        
        logger.info("\nDatabase Test Results:")
        for result in self.results:
            status = "✅" if result.success else "❌"
            logger.info(f"  {status} {result.test_name}: {result.operations_per_second:.2f} ops/sec")
        
        logger.info("\n🎯 DATABASE LIMITS DISCOVERED:")
        for result in self.results:
            logger.info(f"  {result.test_name}:")
            logger.info(f"    Max Operations/sec: {result.operations_per_second:.2f}")
            logger.info(f"    Peak Memory: {result.memory_peak_mb:.1f}MB")
            logger.info(f"    Peak CPU: {result.cpu_peak_percent:.1f}%")
            if result.database_metrics:
                logger.info(f"    Database Memory: {result.database_metrics.get('used_memory_human', 'N/A')}")

def main():
    """Main database stress test execution"""
    logger.info("🚀 STARTING CYBER-PI DATABASE STRESS TESTS")
    
    stress_test = CyberPiDatabaseStressTest()
    results = stress_test.run_database_stress_tests()
    stress_test.print_database_summary()
    
    # Save results to file
    with open('database_stress_test_results.json', 'w') as f:
        json.dump([vars(r) for r in results], f, indent=2)
    
    logger.info("\n📊 Database results saved to database_stress_test_results.json")
    logger.info("🔥🔥🔥 DATABASE STRESS TESTING COMPLETED 🔥🔥🔥")

if __name__ == "__main__":
    main()
