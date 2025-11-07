"""
Performance Benchmarks for Redis-First vs Kafka-First Routing
"""

import asyncio
import time
import json
import random
import string
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
import statistics
import structlog

logger = structlog.get_logger(__name__)

@dataclass
class BenchmarkResult:
    """Benchmark result for a single operation"""
    operation: str
    strategy: str
    latency_ms: float
    success: bool
    data_size: int

class RoutingBenchmark:
    """
    Benchmark suite comparing routing strategies
    """
    
    def __init__(self, router, redis_client, kafka_producer):
        self.router = router
        self.redis = redis_client
        self.kafka = kafka_producer
        self.results: List[BenchmarkResult] = []
    
    def generate_data(self, size: str = "small") -> Tuple[Dict[str, Any], int]:
        """Generate test data of various sizes"""
        if size == "small":
            # ~100 bytes
            data = {
                "id": ''.join(random.choices(string.ascii_letters, k=10)),
                "value": random.randint(1, 1000),
                "timestamp": time.time()
            }
        elif size == "medium":
            # ~10 KB
            data = {
                "id": ''.join(random.choices(string.ascii_letters, k=10)),
                "records": [
                    {"field": f"value_{i}", "data": ''.join(random.choices(string.ascii_letters, k=100))}
                    for i in range(100)
                ]
            }
        elif size == "large":
            # ~1 MB
            data = {
                "id": ''.join(random.choices(string.ascii_letters, k=10)),
                "payload": ''.join(random.choices(string.ascii_letters, k=1_000_000))
            }
        else:
            data = {"test": "data"}
        
        return data, len(json.dumps(data))
    
    async def benchmark_write_strategy(self, 
                                      strategy: str,
                                      iterations: int = 100,
                                      data_size: str = "small") -> Dict[str, Any]:
        """Benchmark a specific write strategy"""
        latencies = []
        successes = 0
        
        for i in range(iterations):
            data, size_bytes = self.generate_data(data_size)
            key = f"bench:{strategy}:{data_size}:{i}"
            
            # Force specific strategy
            metadata = {"strategy": strategy}
            
            start = time.perf_counter()
            try:
                result = await self.router.route_write(key, data, metadata)
                latency = (time.perf_counter() - start) * 1000  # ms
                
                success = len(result.get("errors", [])) == 0
                successes += success
                
                self.results.append(BenchmarkResult(
                    operation="write",
                    strategy=strategy,
                    latency_ms=latency,
                    success=success,
                    data_size=size_bytes
                ))
                
                latencies.append(latency)
                
            except Exception as e:
                logger.error(f"Benchmark error: {e}")
                continue
            
            # Small delay between operations
            await asyncio.sleep(0.001)
        
        return {
            "strategy": strategy,
            "data_size": data_size,
            "iterations": iterations,
            "success_rate": successes / iterations,
            "latency": {
                "mean": statistics.mean(latencies) if latencies else 0,
                "median": statistics.median(latencies) if latencies else 0,
                "p95": statistics.quantiles(latencies, n=20)[18] if len(latencies) > 20 else max(latencies, default=0),
                "p99": statistics.quantiles(latencies, n=100)[98] if len(latencies) > 100 else max(latencies, default=0),
                "min": min(latencies, default=0),
                "max": max(latencies, default=0)
            }
        }
    
    async def benchmark_read_performance(self,
                                        iterations: int = 100,
                                        cache_hit_ratio: float = 0.8) -> Dict[str, Any]:
        """Benchmark read performance with various cache hit ratios"""
        latencies_hit = []
        latencies_miss = []
        
        # Pre-populate some keys in Redis
        cached_keys = []
        for i in range(int(iterations * cache_hit_ratio)):
            key = f"bench:read:cached:{i}"
            data = {"cached": True, "id": i}
            await self.redis.set(key, json.dumps(data))
            cached_keys.append(key)
        
        # Keys that will miss (not in Redis)
        miss_keys = [f"bench:read:miss:{i}" for i in range(int(iterations * (1 - cache_hit_ratio)))]
        
        all_keys = cached_keys + miss_keys
        random.shuffle(all_keys)
        
        for key in all_keys[:iterations]:
            start = time.perf_counter()
            try:
                data, source = await self.router.route_read(key, {"check_kafka": False})
                latency = (time.perf_counter() - start) * 1000
                
                if source == "redis":
                    latencies_hit.append(latency)
                else:
                    latencies_miss.append(latency)
                    
            except Exception:
                # Not found
                latency = (time.perf_counter() - start) * 1000
                latencies_miss.append(latency)
        
        return {
            "operation": "read",
            "iterations": iterations,
            "target_hit_ratio": cache_hit_ratio,
            "actual_hit_ratio": len(latencies_hit) / iterations if iterations > 0 else 0,
            "cache_hit_latency": {
                "mean": statistics.mean(latencies_hit) if latencies_hit else 0,
                "median": statistics.median(latencies_hit) if latencies_hit else 0,
                "p95": statistics.quantiles(latencies_hit, n=20)[18] if len(latencies_hit) > 20 else max(latencies_hit, default=0)
            },
            "cache_miss_latency": {
                "mean": statistics.mean(latencies_miss) if latencies_miss else 0,
                "median": statistics.median(latencies_miss) if latencies_miss else 0,
                "p95": statistics.quantiles(latencies_miss, n=20)[18] if len(latencies_miss) > 20 else max(latencies_miss, default=0)
            }
        }
    
    async def run_full_benchmark(self) -> Dict[str, Any]:
        """Run comprehensive benchmark suite"""
        logger.info("Starting comprehensive routing benchmark")
        
        results = {
            "timestamp": time.time(),
            "write_benchmarks": {},
            "read_benchmark": {},
            "comparison": {}
        }
        
        # Benchmark write strategies with different data sizes
        strategies = ["redis_only", "redis_first", "dual_sync", "kafka_first"]
        sizes = ["small", "medium"]
        
        for strategy in strategies:
            results["write_benchmarks"][strategy] = {}
            for size in sizes:
                logger.info(f"Benchmarking {strategy} with {size} data")
                result = await self.benchmark_write_strategy(strategy, 50, size)
                results["write_benchmarks"][strategy][size] = result
        
        # Benchmark read performance
        logger.info("Benchmarking read performance")
        results["read_benchmark"] = await self.benchmark_read_performance(100, 0.8)
        
        # Generate comparison
        results["comparison"] = self._generate_comparison(results["write_benchmarks"])
        
        return results
    
    def _generate_comparison(self, write_benchmarks: Dict) -> Dict[str, Any]:
        """Generate strategy comparison"""
        comparison = {
            "redis_first_advantage": {},
            "recommendations": []
        }
        
        # Compare Redis-first vs Kafka-first for small data
        if "redis_first" in write_benchmarks and "kafka_first" in write_benchmarks:
            rf_small = write_benchmarks["redis_first"].get("small", {})
            kf_small = write_benchmarks["kafka_first"].get("small", {})
            
            if rf_small and kf_small:
                rf_latency = rf_small.get("latency", {}).get("median", 0)
                kf_latency = kf_small.get("latency", {}).get("median", 0)
                
                if kf_latency > 0:
                    speedup = kf_latency / rf_latency if rf_latency > 0 else 0
                    comparison["redis_first_advantage"]["small_data_speedup"] = f"{speedup:.2f}x"
                    
                    if speedup > 2:
                        comparison["recommendations"].append(
                            "Redis-first shows significant performance advantage for small operational data"
                        )
        
        # Compare dual-sync overhead
        if "dual_sync" in write_benchmarks and "redis_only" in write_benchmarks:
            ds_small = write_benchmarks["dual_sync"].get("small", {})
            ro_small = write_benchmarks["redis_only"].get("small", {})
            
            if ds_small and ro_small:
                ds_latency = ds_small.get("latency", {}).get("median", 0)
                ro_latency = ro_small.get("latency", {}).get("median", 0)
                
                if ro_latency > 0:
                    overhead = (ds_latency - ro_latency) / ro_latency
                    comparison["redis_first_advantage"]["dual_sync_overhead"] = f"{overhead * 100:.1f}%"
                    
                    if overhead > 0.5:
                        comparison["recommendations"].append(
                            "Reserve dual-sync for critical data only due to overhead"
                        )
        
        # Overall recommendation
        comparison["recommendations"].append(
            "Redis-first strategy optimal for majority of operational workloads"
        )
        
        return comparison

async def run_benchmark_cli(router, redis_client, kafka_producer):
    """CLI function to run benchmarks"""
    benchmark = RoutingBenchmark(router, redis_client, kafka_producer)
    
    print("\n" + "="*60)
    print("TQAKB V4 - Redis-First Routing Benchmark")
    print("="*60)
    
    results = await benchmark.run_full_benchmark()
    
    # Display results
    print("\n📊 Write Performance by Strategy:")
    print("-" * 40)
    
    for strategy, sizes in results["write_benchmarks"].items():
        print(f"\n{strategy.upper()}:")
        for size, metrics in sizes.items():
            latency = metrics.get("latency", {})
            print(f"  {size}: median={latency.get('median', 0):.2f}ms, "
                  f"p95={latency.get('p95', 0):.2f}ms, "
                  f"success={metrics.get('success_rate', 0)*100:.1f}%")
    
    print("\n📖 Read Performance:")
    print("-" * 40)
    read_bench = results["read_benchmark"]
    hit_latency = read_bench.get("cache_hit_latency", {})
    print(f"Cache Hit Ratio: {read_bench.get('actual_hit_ratio', 0)*100:.1f}%")
    print(f"Hit Latency: median={hit_latency.get('median', 0):.2f}ms")
    
    print("\n🎯 Strategy Comparison:")
    print("-" * 40)
    comparison = results["comparison"]
    
    for key, value in comparison.get("redis_first_advantage", {}).items():
        print(f"{key}: {value}")
    
    print("\n💡 Recommendations:")
    for rec in comparison.get("recommendations", []):
        print(f"• {rec}")
    
    return results