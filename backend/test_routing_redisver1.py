"""
Test Redis-First Routing Performance - RedisVer1
Comprehensive testing to validate the Redis-first architecture
"""

import asyncio
import time
import json
import random
import statistics
from typing import Dict, List, Any
import redis.asyncio as redis
from aiokafka import AIOKafkaProducer
import structlog

from backend.core.intelligent_router import IntelligentRouter, DataPattern, WriteStrategy
from backend.core.benchmark import RoutingBenchmark
from backend.core.failover import FailoverManager, FailoverConfig

# Configure logging
structlog.configure(
    processors=[
        structlog.dev.ConsoleRenderer()
    ]
)
logger = structlog.get_logger(__name__)

class RoutingTesterRedisVer1:
    """Comprehensive routing performance tester - RedisVer1"""
    
    def __init__(self):
        self.redis_client = None
        self.kafka_producer = None
        self.router = None
        self.results = {}
        self.version = "RedisVer1"
        
    async def setup(self):
        """Setup test connections"""
        print(f"\n🔧 Setting up test environment [{self.version}]...")
        
        # Connect to Redis (V3's NodePort)
        self.redis_client = redis.Redis(
            host='localhost', 
            port=30379,
            db=2,  # Use different DB for testing
            decode_responses=True
        )
        
        # Test Redis connection
        try:
            await self.redis_client.ping()
            print(f"✅ Redis connected on port 30379 [{self.version}]")
        except Exception as e:
            print(f"❌ Redis connection failed: {e}")
            return False
        
        # Connect to Kafka (V4's service or V3's NodePort)
        self.kafka_producer = AIOKafkaProducer(
            bootstrap_servers='localhost:30092',  # V3's Kafka NodePort
            value_serializer=lambda v: json.dumps(v).encode()
        )
        
        try:
            await self.kafka_producer.start()
            print(f"✅ Kafka connected on port 30092 [{self.version}]")
        except Exception as e:
            print(f"⚠️  Kafka connection failed: {e}")
            print(f"   Continuing with Redis-only tests [{self.version}]...")
            self.kafka_producer = None
        
        # Create router
        config = {
            "size_threshold": 1_000_000,
            "batch_threshold": 100,
            "ttl_threshold": 3600
        }
        
        self.router = IntelligentRouter(
            redis_client=self.redis_client,
            kafka_producer=self.kafka_producer,
            config=config
        )
        
        # Start Kafka queue processor if available
        if self.kafka_producer:
            asyncio.create_task(self.router.process_kafka_queue())
        
        print(f"✅ Intelligent router initialized [{self.version}]\n")
        return True
    
    async def test_redis_first_performance(self):
        """Test Redis-first routing performance"""
        print("=" * 60)
        print(f"TEST 1: Redis-First Performance [{self.version}]")
        print("=" * 60)
        
        results = []
        iterations = 100
        
        print(f"\nRunning {iterations} Redis-first operations [{self.version}]...")
        
        for i in range(iterations):
            data = {
                "id": f"perf_test_{i}",
                "value": random.randint(1, 1000),
                "timestamp": time.time(),
                "type": "operational",
                "version": self.version
            }
            
            key = f"test:{self.version}:redis_first:{i}"
            
            start = time.perf_counter()
            result = await self.router.route_write(
                key, 
                data,
                {}  # Let router decide strategy (should be redis_first)
            )
            latency = (time.perf_counter() - start) * 1000
            
            results.append({
                "latency": latency,
                "strategy": result["strategy"],
                "success": len(result.get("errors", [])) == 0
            })
            
            if i % 20 == 0:
                print(f"  Progress: {i}/{iterations}")
        
        # Analyze results
        latencies = [r["latency"] for r in results if r["success"]]
        success_rate = sum(1 for r in results if r["success"]) / len(results)
        
        stats = {
            "strategy": "redis_first",
            "iterations": iterations,
            "success_rate": success_rate,
            "version": self.version,
            "latency_ms": {
                "mean": statistics.mean(latencies),
                "median": statistics.median(latencies),
                "min": min(latencies),
                "max": max(latencies),
                "stdev": statistics.stdev(latencies) if len(latencies) > 1 else 0
            }
        }
        
        self.results["redis_first"] = stats
        
        print(f"\n📊 Redis-First Results [{self.version}]:")
        print(f"  Success Rate: {success_rate * 100:.1f}%")
        print(f"  Median Latency: {stats['latency_ms']['median']:.2f}ms")
        print(f"  Mean Latency: {stats['latency_ms']['mean']:.2f}ms")
        print(f"  Min/Max: {stats['latency_ms']['min']:.2f}ms / {stats['latency_ms']['max']:.2f}ms")
        
        return stats
    
    async def test_kafka_first_performance(self):
        """Test Kafka-first routing performance for comparison"""
        if not self.kafka_producer:
            print(f"\n⚠️  Skipping Kafka-first test (Kafka not available) [{self.version}]")
            return None
        
        print("\n" + "=" * 60)
        print(f"TEST 2: Kafka-First Performance (Comparison) [{self.version}]")
        print("=" * 60)
        
        results = []
        iterations = 100
        
        print(f"\nRunning {iterations} Kafka-first operations [{self.version}]...")
        
        for i in range(iterations):
            data = {
                "id": f"kafka_test_{i}",
                "value": random.randint(1, 1000),
                "timestamp": time.time(),
                "type": "streaming",
                "version": self.version
            }
            
            key = f"test:{self.version}:kafka_first:{i}"
            
            start = time.perf_counter()
            result = await self.router.route_write(
                key,
                data,
                {"strategy": "kafka_first"}  # Force Kafka-first
            )
            latency = (time.perf_counter() - start) * 1000
            
            results.append({
                "latency": latency,
                "strategy": result["strategy"],
                "success": len(result.get("errors", [])) == 0
            })
            
            if i % 20 == 0:
                print(f"  Progress: {i}/{iterations}")
        
        # Analyze results
        latencies = [r["latency"] for r in results if r["success"]]
        success_rate = sum(1 for r in results if r["success"]) / len(results)
        
        stats = {
            "strategy": "kafka_first",
            "iterations": iterations,
            "success_rate": success_rate,
            "version": self.version,
            "latency_ms": {
                "mean": statistics.mean(latencies),
                "median": statistics.median(latencies),
                "min": min(latencies),
                "max": max(latencies),
                "stdev": statistics.stdev(latencies) if len(latencies) > 1 else 0
            }
        }
        
        self.results["kafka_first"] = stats
        
        print(f"\n📊 Kafka-First Results [{self.version}]:")
        print(f"  Success Rate: {success_rate * 100:.1f}%")
        print(f"  Median Latency: {stats['latency_ms']['median']:.2f}ms")
        print(f"  Mean Latency: {stats['latency_ms']['mean']:.2f}ms")
        print(f"  Min/Max: {stats['latency_ms']['min']:.2f}ms / {stats['latency_ms']['max']:.2f}ms")
        
        return stats
    
    async def test_data_patterns(self):
        """Test routing for different data patterns"""
        print("\n" + "=" * 60)
        print(f"TEST 3: Data Pattern Routing [{self.version}]")
        print("=" * 60)
        
        test_cases = [
            {
                "name": "Cache-only (Session)",
                "data": {"type": "session", "user_id": "123", "temp": True, "version": self.version},
                "metadata": {"ttl": 60},
                "expected_pattern": DataPattern.CACHE_ONLY,
                "expected_strategy": WriteStrategy.REDIS_ONLY
            },
            {
                "name": "Operational (User Action)",
                "data": {"action": "click", "target": "button", "user": "456", "version": self.version},
                "metadata": {},
                "expected_pattern": DataPattern.OPERATIONAL,
                "expected_strategy": WriteStrategy.REDIS_FIRST
            },
            {
                "name": "Immutable (Transaction)",
                "data": {"transaction_id": "tx789", "amount": 100, "status": "complete", "version": self.version},
                "metadata": {"immutable": True},
                "expected_pattern": DataPattern.IMMUTABLE,
                "expected_strategy": WriteStrategy.DUAL_SYNC
            },
            {
                "name": "Analytical (Large Batch)",
                "data": {"records": [{"id": i, "val": i*10} for i in range(200)], "version": self.version},
                "metadata": {"type": "analytics"},
                "expected_pattern": DataPattern.ANALYTICAL,
                "expected_strategy": WriteStrategy.KAFKA_FIRST
            }
        ]
        
        print(f"\nTesting data pattern classification and routing [{self.version}]...\n")
        
        for i, test in enumerate(test_cases):
            # Classify
            pattern = self.router.classify_data(test["data"], test["metadata"])
            strategy = self.router.determine_strategy(pattern, test["metadata"])
            
            # Route write
            key = f"test:{self.version}:pattern:{i}"
            start = time.perf_counter()
            result = await self.router.route_write(key, test["data"], test["metadata"])
            latency = (time.perf_counter() - start) * 1000
            
            # Check results
            pattern_match = pattern == test["expected_pattern"]
            strategy_match = strategy == test["expected_strategy"]
            
            print(f"{test['name']}:")
            print(f"  Pattern: {pattern.value} {'✅' if pattern_match else '❌'}")
            print(f"  Strategy: {strategy.value} {'✅' if strategy_match else '❌'}")
            print(f"  Latency: {latency:.2f}ms")
            print(f"  Redis: {'✅' if result['redis'] else '❌'}")
            print(f"  Kafka: {'✅' if result['kafka'] else '❌' if not result['queued'] else '⏳ Queued'}")
            print()
    
    async def test_read_performance(self):
        """Test read performance from Redis cache"""
        print("=" * 60)
        print(f"TEST 4: Read Performance (Cache Hits) [{self.version}]")
        print("=" * 60)
        
        # Pre-populate cache
        print(f"\nPopulating Redis cache [{self.version}]...")
        for i in range(50):
            key = f"test:{self.version}:read:{i}"
            data = {"id": i, "cached": True, "value": i * 100, "version": self.version}
            await self.redis_client.set(key, json.dumps(data))
        
        # Test reads
        print(f"Testing cache read performance [{self.version}]...")
        read_latencies = []
        
        for i in range(100):
            key = f"test:{self.version}:read:{i % 50}"  # Read from cached keys
            
            start = time.perf_counter()
            data, source = await self.router.route_read(key)
            latency = (time.perf_counter() - start) * 1000
            
            if data:
                read_latencies.append(latency)
        
        stats = {
            "reads": len(read_latencies),
            "version": self.version,
            "latency_ms": {
                "mean": statistics.mean(read_latencies),
                "median": statistics.median(read_latencies),
                "min": min(read_latencies),
                "max": max(read_latencies)
            }
        }
        
        print(f"\n📊 Read Performance Results [{self.version}]:")
        print(f"  Successful Reads: {stats['reads']}")
        print(f"  Median Latency: {stats['latency_ms']['median']:.2f}ms")
        print(f"  Mean Latency: {stats['latency_ms']['mean']:.2f}ms")
        print(f"  Min/Max: {stats['latency_ms']['min']:.2f}ms / {stats['latency_ms']['max']:.2f}ms")
        
        return stats
    
    async def compare_strategies(self):
        """Compare Redis-first vs Kafka-first performance"""
        print("\n" + "=" * 60)
        print(f"PERFORMANCE COMPARISON [{self.version}]")
        print("=" * 60)
        
        if "redis_first" in self.results and "kafka_first" in self.results:
            rf = self.results["redis_first"]["latency_ms"]
            kf = self.results["kafka_first"]["latency_ms"]
            
            speedup = {
                "median": kf["median"] / rf["median"] if rf["median"] > 0 else 0,
                "mean": kf["mean"] / rf["mean"] if rf["mean"] > 0 else 0
            }
            
            print(f"\n🏆 Redis-First vs Kafka-First [{self.version}]:")
            print(f"  Median Speedup: {speedup['median']:.2f}x faster")
            print(f"  Mean Speedup: {speedup['mean']:.2f}x faster")
            print(f"  Redis Median: {rf['median']:.2f}ms")
            print(f"  Kafka Median: {kf['median']:.2f}ms")
            
            if speedup['median'] > 2:
                print(f"\n✨ Outstanding Performance [{self.version}]!")
                print("  Redis-first shows >2x performance improvement")
                print("  Recommendation: Continue with Redis-first architecture")
            elif speedup['median'] > 1.5:
                print(f"\n👍 Good Performance [{self.version}]")
                print("  Redis-first shows significant performance improvement")
                print("  Recommendation: Redis-first is optimal for operational workloads")
            else:
                print(f"\n🤔 Performance Review Needed [{self.version}]")
                print("  Performance improvement less than expected")
                print("  Consider: Network latency, Redis configuration, or load factors")
    
    async def cleanup(self):
        """Cleanup test resources"""
        print(f"\n🧹 Cleaning up [{self.version}]...")
        
        # Clear test keys from Redis
        cursor = 0
        while True:
            cursor, keys = await self.redis_client.scan(
                cursor, match=f"test:{self.version}:*", count=100
            )
            if keys:
                await self.redis_client.delete(*keys)
            if cursor == 0:
                break
        
        # Close connections
        if self.redis_client:
            await self.redis_client.close()
        
        if self.kafka_producer:
            await self.kafka_producer.stop()
        
        print(f"✅ Cleanup complete [{self.version}]")
    
    async def run_all_tests(self):
        """Run complete test suite"""
        print("\n" + "🚀 " * 20)
        print(f"TQAKB V4 - REDIS-FIRST ROUTING PERFORMANCE TEST [{self.version}]")
        print("🚀 " * 20)
        
        try:
            # Setup
            if not await self.setup():
                return
            
            # Run tests
            await self.test_redis_first_performance()
            await self.test_kafka_first_performance()
            await self.test_data_patterns()
            await self.test_read_performance()
            
            # Compare results
            await self.compare_strategies()
            
            # Get router metrics
            metrics = self.router.get_metrics()
            print(f"\n📈 Router Metrics [{self.version}]:")
            print(f"  Total Redis Writes: {metrics['redis_writes']}")
            print(f"  Total Kafka Writes: {metrics['kafka_writes']}")
            print(f"  Cache Hit Rate: {metrics['cache_hit_rate'] * 100:.1f}%")
            print(f"  Redis-First Usage: {metrics['redis_first_percentage']:.1f}%")
            
        finally:
            await self.cleanup()
        
        print("\n" + "✅ " * 20)
        print(f"ALL TESTS COMPLETE [{self.version}]")
        print("✅ " * 20)

async def main():
    """Main test runner"""
    tester = RoutingTesterRedisVer1()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())