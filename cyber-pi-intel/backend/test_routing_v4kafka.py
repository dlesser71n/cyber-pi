"""
Test Redis-First vs Kafka-First with V4 Kafka
Performance comparison using port-forwarded Kafka
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

# Configure logging
structlog.configure(
    processors=[
        structlog.dev.ConsoleRenderer()
    ]
)
logger = structlog.get_logger(__name__)

class V4KafkaRoutingTest:
    """Test with V4's Kafka via port-forward"""
    
    def __init__(self):
        self.redis_client = None
        self.kafka_producer = None
        self.router = None
        self.results = {}
        
    async def setup(self):
        """Setup connections to V4 infrastructure"""
        print("\n🔧 Setting up V4 Kafka test environment...")
        
        # Connect to Redis (V3's NodePort for now)
        self.redis_client = redis.Redis(
            host='localhost', 
            port=30379,
            db=3,  # Different DB for V4 tests
            decode_responses=True
        )
        
        try:
            await self.redis_client.ping()
            print("✅ Redis connected on port 30379")
        except Exception as e:
            print(f"❌ Redis connection failed: {e}")
            return False
        
        # Connect to V4's Kafka (port-forwarded)
        self.kafka_producer = AIOKafkaProducer(
            bootstrap_servers='localhost:9093',
            value_serializer=lambda v: json.dumps(v).encode() if not isinstance(v, bytes) else v
        )
        
        try:
            await self.kafka_producer.start()
            print("✅ V4 Kafka connected on port 9093 (port-forwarded)")
        except Exception as e:
            print(f"❌ V4 Kafka connection failed: {e}")
            print("   Make sure port-forward is running: kubectl port-forward -n tqakb-v4 kafka-0 9093:9092")
            return False
        
        # Create router with V4 configuration
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
        
        # Start Kafka queue processor
        asyncio.create_task(self.router.process_kafka_queue())
        
        print("✅ V4 Intelligent router initialized\n")
        return True
    
    async def test_redis_first_performance(self, iterations=100):
        """Test Redis-first routing performance"""
        print("=" * 60)
        print("TEST: Redis-First Performance (V4)")
        print("=" * 60)
        
        results = []
        
        print(f"\nRunning {iterations} Redis-first operations...")
        
        for i in range(iterations):
            data = {
                "id": f"v4_test_{i}",
                "value": random.randint(1, 1000),
                "timestamp": time.time(),
                "type": "operational"
            }
            
            key = f"v4:redis_first:{i}"
            
            start = time.perf_counter()
            result = await self.router.route_write(
                key, 
                data,
                {}  # Let router decide (should choose redis_first)
            )
            latency = (time.perf_counter() - start) * 1000
            
            results.append({
                "latency": latency,
                "strategy": result["strategy"],
                "success": len(result.get("errors", [])) == 0,
                "redis": result.get("redis", False),
                "kafka": result.get("kafka", False) or result.get("queued", False)
            })
            
            if i % 25 == 0:
                print(f"  Progress: {i}/{iterations}")
        
        # Analyze
        latencies = [r["latency"] for r in results if r["success"]]
        redis_writes = sum(1 for r in results if r["redis"])
        kafka_writes = sum(1 for r in results if r["kafka"])
        
        stats = {
            "strategy": "redis_first",
            "iterations": iterations,
            "success_rate": sum(1 for r in results if r["success"]) / len(results),
            "redis_writes": redis_writes,
            "kafka_writes": kafka_writes,
            "latency_ms": {
                "mean": statistics.mean(latencies),
                "median": statistics.median(latencies),
                "min": min(latencies),
                "max": max(latencies),
                "p95": statistics.quantiles(latencies, n=20)[18] if len(latencies) > 20 else max(latencies)
            }
        }
        
        self.results["redis_first"] = stats
        
        print(f"\n📊 Redis-First Results:")
        print(f"  Success Rate: {stats['success_rate'] * 100:.1f}%")
        print(f"  Redis Writes: {redis_writes}")
        print(f"  Kafka Writes/Queued: {kafka_writes}")
        print(f"  Median Latency: {stats['latency_ms']['median']:.2f}ms")
        print(f"  P95 Latency: {stats['latency_ms']['p95']:.2f}ms")
        
        return stats
    
    async def test_kafka_first_performance(self, iterations=100):
        """Test Kafka-first routing for comparison"""
        print("\n" + "=" * 60)
        print("TEST: Kafka-First Performance (V4)")
        print("=" * 60)
        
        results = []
        
        print(f"\nRunning {iterations} Kafka-first operations...")
        
        for i in range(iterations):
            data = {
                "id": f"v4_kafka_{i}",
                "value": random.randint(1, 1000),
                "timestamp": time.time(),
                "type": "streaming"
            }
            
            key = f"v4:kafka_first:{i}"
            
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
            
            if i % 25 == 0:
                print(f"  Progress: {i}/{iterations}")
        
        # Analyze
        latencies = [r["latency"] for r in results if r["success"]]
        
        stats = {
            "strategy": "kafka_first",
            "iterations": iterations,
            "success_rate": sum(1 for r in results if r["success"]) / len(results) if results else 0,
            "latency_ms": {
                "mean": statistics.mean(latencies) if latencies else 0,
                "median": statistics.median(latencies) if latencies else 0,
                "min": min(latencies) if latencies else 0,
                "max": max(latencies) if latencies else 0,
                "p95": statistics.quantiles(latencies, n=20)[18] if len(latencies) > 20 else max(latencies, default=0)
            }
        }
        
        self.results["kafka_first"] = stats
        
        print(f"\n📊 Kafka-First Results:")
        print(f"  Success Rate: {stats['success_rate'] * 100:.1f}%")
        print(f"  Median Latency: {stats['latency_ms']['median']:.2f}ms")
        print(f"  P95 Latency: {stats['latency_ms']['p95']:.2f}ms")
        
        return stats
    
    async def test_dual_sync_performance(self, iterations=50):
        """Test dual-sync for critical data"""
        print("\n" + "=" * 60)
        print("TEST: Dual-Sync Performance (Critical Path)")
        print("=" * 60)
        
        results = []
        
        print(f"\nRunning {iterations} dual-sync operations...")
        
        for i in range(iterations):
            data = {
                "transaction_id": f"tx_{i}",
                "amount": random.randint(100, 10000),
                "timestamp": time.time(),
                "critical": True
            }
            
            key = f"v4:transaction:{i}"
            
            start = time.perf_counter()
            result = await self.router.route_write(
                key,
                data,
                {"strategy": "dual_sync"}  # Force dual-sync
            )
            latency = (time.perf_counter() - start) * 1000
            
            results.append({
                "latency": latency,
                "success": len(result.get("errors", [])) == 0,
                "redis": result.get("redis", False),
                "kafka": result.get("kafka", False)
            })
        
        # Analyze
        latencies = [r["latency"] for r in results if r["success"]]
        both_succeeded = sum(1 for r in results if r["redis"] and r["kafka"])
        
        stats = {
            "strategy": "dual_sync",
            "iterations": iterations,
            "success_rate": sum(1 for r in results if r["success"]) / len(results),
            "both_succeeded": both_succeeded / len(results),
            "latency_ms": {
                "mean": statistics.mean(latencies) if latencies else 0,
                "median": statistics.median(latencies) if latencies else 0,
                "p95": statistics.quantiles(latencies, n=20)[18] if len(latencies) > 20 else max(latencies, default=0)
            }
        }
        
        self.results["dual_sync"] = stats
        
        print(f"\n📊 Dual-Sync Results:")
        print(f"  Both Services Success: {stats['both_succeeded'] * 100:.1f}%")
        print(f"  Median Latency: {stats['latency_ms']['median']:.2f}ms")
        print(f"  P95 Latency: {stats['latency_ms']['p95']:.2f}ms")
        
        return stats
    
    async def compare_all_strategies(self):
        """Compare all routing strategies"""
        print("\n" + "=" * 60)
        print("🏆 PERFORMANCE COMPARISON - V4 KAFKA")
        print("=" * 60)
        
        if "redis_first" in self.results and "kafka_first" in self.results:
            rf = self.results["redis_first"]["latency_ms"]
            kf = self.results["kafka_first"]["latency_ms"]
            
            speedup = {
                "median": kf["median"] / rf["median"] if rf["median"] > 0 else 0,
                "p95": kf["p95"] / rf["p95"] if rf["p95"] > 0 else 0
            }
            
            print(f"\n📈 Redis-First vs Kafka-First:")
            print(f"  Median Speedup: {speedup['median']:.2f}x faster")
            print(f"  P95 Speedup: {speedup['p95']:.2f}x faster")
            print(f"  Redis Median: {rf['median']:.2f}ms")
            print(f"  Kafka Median: {kf['median']:.2f}ms")
            
            if "dual_sync" in self.results:
                ds = self.results["dual_sync"]["latency_ms"]
                print(f"\n📈 Dual-Sync Overhead:")
                print(f"  Dual-Sync Median: {ds['median']:.2f}ms")
                print(f"  vs Redis-only: {(ds['median'] / rf['median']):.2f}x slower")
                print(f"  vs Kafka-only: {(ds['median'] / kf['median']):.2f}x")
            
            # Performance verdict
            if speedup['median'] > 2:
                print("\n✨ OUTSTANDING PERFORMANCE!")
                print("  Redis-first shows >2x performance improvement")
                print("  ✅ Recommendation: Redis-first architecture validated")
            elif speedup['median'] > 1.5:
                print("\n👍 GOOD PERFORMANCE")
                print("  Redis-first shows significant improvement")
                print("  ✅ Recommendation: Use Redis-first for operational workloads")
            else:
                print("\n🤔 PERFORMANCE NEEDS REVIEW")
                print("  Consider network latency or configuration issues")
    
    async def cleanup(self):
        """Cleanup test resources"""
        print("\n🧹 Cleaning up V4 test data...")
        
        # Clear test keys
        cursor = 0
        while True:
            cursor, keys = await self.redis_client.scan(
                cursor, match="v4:*", count=100
            )
            if keys:
                await self.redis_client.delete(*keys)
            if cursor == 0:
                break
        
        # Close connections
        if self.redis_client:
            await self.redis_client.aclose()
        
        if self.kafka_producer:
            await self.kafka_producer.stop()
        
        print("✅ Cleanup complete")
    
    async def run_all_tests(self):
        """Run complete V4 test suite"""
        print("\n" + "🚀 " * 20)
        print("TQAKB V4 - REDIS-FIRST vs KAFKA-FIRST PERFORMANCE TEST")
        print("Using V4 Kafka Infrastructure")
        print("🚀 " * 20)
        
        try:
            if not await self.setup():
                return
            
            # Run performance tests
            await self.test_redis_first_performance(100)
            await self.test_kafka_first_performance(100)
            await self.test_dual_sync_performance(50)
            
            # Compare results
            await self.compare_all_strategies()
            
            # Get final metrics
            metrics = self.router.get_metrics()
            print(f"\n📊 Final Router Metrics:")
            print(f"  Total Redis Writes: {metrics['redis_writes']}")
            print(f"  Total Kafka Writes: {metrics['kafka_writes']}")
            print(f"  Cache Hit Rate: {metrics['cache_hit_rate'] * 100:.1f}%")
            
        finally:
            await self.cleanup()
        
        print("\n" + "✅ " * 20)
        print("V4 KAFKA TESTS COMPLETE")
        print("✅ " * 20)

async def main():
    """Main test runner"""
    tester = V4KafkaRoutingTest()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())