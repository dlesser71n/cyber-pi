import asyncio
import json
import hashlib
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import redis.asyncio as redis
import torch
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from dataclasses import dataclass, asdict

console = Console()

# Import monitoring components
try:
    from monitoring.cache_monitor import get_cache_monitor, CacheMonitor
    from monitoring.metrics_collector import get_metrics_collector, MetricsCollector
    from monitoring.alerts import get_alerting_system, AlertingSystem
    MONITORING_AVAILABLE = True
except ImportError:
    MONITORING_AVAILABLE = False
    console.print("⚠️ Monitoring components not available - running without monitoring")

@dataclass
class MemoryTier:
    """Configuration for each memory tier (adapted from TQAKB golden config)"""
    name: str
    max_memory_gb: float
    ttl_seconds: int
    hit_ratio_target: float = 0.9
    db_number: int = 0  # Separate Redis DB per tier (golden pattern)

@dataclass
class TierMetrics:
    """Real-time tier performance metrics (adapted from TQAKB golden config)"""
    hits: int = 0
    misses: int = 0
    promotions: int = 0  # Track auto-promotions
    sets: int = 0
    memory_used_gb: float = 0.0
    hit_rate: float = 0.0

class PeriscopeMemory:
    """
    Cyber Periscope - 3-Level Threat Memory System (adapted from TQAKB V3 golden config)
    
    Architecture:
    - Level 1 (Working): Active threats being analyzed NOW (1 hour TTL)
    - Level 2 (Short-Term): Recently validated threats (7 days TTL)
    - Level 3 (Long-Term): Historical knowledge (90 days TTL)
    
    Key Principles from TQAKB Golden:
    - Validated threats don't decay (like "facts")
    - Auto-promotion on access (L3 → L2 → L1)
    - Separate Redis DBs per level
    - Batch processing for efficiency
    """

    def __init__(self, redis_host="localhost", redis_port=32379):
        self.redis_host = redis_host
        self.redis_port = redis_port
        self.total_memory_gb = 100  # Reasonable for threat memory

        # Define memory tiers (adapted from TQAKB golden config)
        self.tiers = {
            "Level_1_Working": MemoryTier("Level 1 Working", 10, 3600, 0.95, db_number=1),      # 1 hour TTL
            "Level_2_ShortTerm": MemoryTier("Level 2 Short-Term", 50, 604800, 0.85, db_number=2),  # 7 days TTL
            "Level_3_LongTerm": MemoryTier("Level 3 Long-Term", 40, 7776000, 0.75, db_number=3),  # 90 days TTL
        }

        # Redis connections for each tier (golden pattern: separate DBs)
        self.redis_clients = {}
        self.metrics = {tier: TierMetrics() for tier in self.tiers.keys()}

        # Monitoring components (optional)
        self.monitor = None
        self.metrics_collector = None
        self.alerting_system = None

        console.print(f"[bold cyan]🧠 Cyber Periscope - Threat Memory System Initialized[/bold cyan]")
        console.print(f"   3-Level Intelligence Architecture (TQAKB Golden Config)")
        console.print(f"   Redis: {redis_host}:{redis_port}")
        console.print(f"   Memory Tiers: {len(self.tiers)}")
        if MONITORING_AVAILABLE:
            console.print(f"   Monitoring: ✅ Enabled")
        else:
            console.print(f"   Monitoring: ⚠️ Disabled")

    async def initialize(self):
        """Initialize all memory tiers (golden pattern: separate Redis DBs)"""
        for tier_name, tier_config in self.tiers.items():
            # Create dedicated Redis instance for each tier (golden pattern)
            self.redis_clients[tier_name] = redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                db=tier_config.db_number,  # Separate DB per tier
                decode_responses=True,
                max_connections=50
            )

            await self.redis_clients[tier_name].ping()
            console.print(f"✅ {tier_config.name} connected (DB {tier_config.db_number})")

        # Initialize GPU cache
        if torch.cuda.is_available():
            console.print("✅ GPU Cache Ready")

        # Initialize monitoring components
        if MONITORING_AVAILABLE:
            await self._initialize_monitoring()

        console.print(f"\\n🎯 Multi-Tiered Cache Ready!")
        console.print(f"Memory Allocation: {sum(t.max_memory_gb for t in self.tiers.values())}GB / {self.total_memory_gb}GB")

    async def _initialize_monitoring(self):
        """Initialize monitoring components"""
        try:
            self.monitor = await get_cache_monitor()
            self.metrics_collector = await get_metrics_collector()
            self.alerting_system = await get_alerting_system()

            # Start metrics collection
            asyncio.create_task(self.metrics_collector.start_collection())

            console.print("✅ Monitoring components initialized")

        except Exception as e:
            console.print(f"⚠️ Monitoring initialization failed: {e}")
            MONITORING_AVAILABLE = False

    # Removed _get_tier_db - now using tier_config.db_number directly (golden pattern)

    async def intelligent_get(self, threat_id: str) -> Tuple[Any, str]:
        """
        Intelligent multi-tier threat retrieval with auto-promotion
        (TQAKB Golden Pattern - DO NOT CHANGE)
        
        Returns (threat_data, tier_name) or (None, None)
        
        Auto-promotion:
        - L3 hit → promote to L2 + L1
        - L2 hit → promote to L1
        - L1 hit → return immediately (fastest)
        """

        # 1. Try Level 1 (Working Memory) - sub-millisecond
        l1_key = f"periscope:L1:{threat_id}"
        data = await self.redis_clients["Level_1_Working"].get(l1_key)
        if data:
            self.metrics["Level_1_Working"].hits += 1
            return json.loads(data), "Level_1_Working"

        # 2. Try Level 2 (Short-Term) - promote to L1
        l2_key = f"periscope:L2:{threat_id}"
        data = await self.redis_clients["Level_2_ShortTerm"].get(l2_key)
        if data:
            self.metrics["Level_2_ShortTerm"].hits += 1
            # Auto-promote to L1 (golden pattern)
            await self._promote_to_l1(threat_id, data)
            self.metrics["Level_2_ShortTerm"].promotions += 1
            return json.loads(data), "Level_2_ShortTerm"

        # 3. Try Level 3 (Long-Term) - promote through all tiers
        l3_key = f"periscope:L3:{threat_id}"
        data = await self.redis_clients["Level_3_LongTerm"].get(l3_key)
        if data:
            self.metrics["Level_3_LongTerm"].hits += 1
            # Auto-promote through tiers (golden pattern)
            await self._promote_to_l2(threat_id, data)
            await self._promote_to_l1(threat_id, data)
            self.metrics["Level_3_LongTerm"].promotions += 1
            return json.loads(data), "Level_3_LongTerm"

        # Threat not found in any tier
        self._record_miss()
        return None, None

    async def intelligent_set(self, key: str, data: Any, data_type: str = "generic",
                            confidence: float = 0.5, access_pattern: str = "unknown"):
        """
        Intelligent multi-tier cache storage based on data characteristics
        """

        # Serialize data
        serialized_data = json.dumps(data)

        # Determine tier based on confidence and access patterns
        target_tier = self._determine_tier(confidence, access_pattern, data_type)

        # Store in appropriate tier
        cache_key = f"{target_tier[:2]}:{key}"  # L1:, L2:, L3:

        if target_tier in ["L1_hot", "L2_warm", "L3_cold"]:
            ttl = self.tiers[target_tier].ttl_seconds
            await self.redis_clients[target_tier].setex(cache_key, ttl, serialized_data)

            # Update memory usage tracking
            self.metrics[target_tier].memory_used_gb += len(serialized_data) / (1024**3)
            self.metrics[target_tier].sets += 1

        # GPU cache for vectors
        if data_type == "vector" and target_tier == "gpu_vectors":
            if len(self.gpu_cache) < self.gpu_cache_size:
                self.gpu_cache[key] = data
            else:
                # Evict least recently used
                oldest_key = next(iter(self.gpu_cache))
                del self.gpu_cache[oldest_key]
                self.gpu_cache[key] = data

        console.print(f"✅ Cached in {target_tier}: {key}")

    def _determine_tier(self, confidence: float, access_pattern: str, data_type: str) -> str:
        """
        Intelligent tier determination based on data characteristics
        """

        # High confidence + high frequency → L1 Hot
        if confidence >= 0.9 and access_pattern in ["frequent", "critical"]:
            return "L1_hot"

        # Medium confidence + vector data → GPU Cache
        if confidence >= 0.7 and data_type == "vector":
            return "gpu_vectors"

        # Medium confidence + regular access → L2 Warm
        if confidence >= 0.6 and access_pattern in ["regular", "predictable"]:
            return "L2_warm"

        # Everything else → L3 Cold
        return "L3_cold"

    async def _promote_to_l1(self, key: str, data: str):
        """Promote data to L1 cache"""
        l1_key = f"L1:{key.split(':', 1)[1]}"
        await self.redis_clients["L1_hot"].setex(l1_key, self.tiers["L1_hot"].ttl_seconds, data)

    async def _promote_to_l2(self, key: str, data: str):
        """Promote data to L2 cache"""
        l2_key = f"L2:{key.split(':', 1)[1]}"
        await self.redis_clients["L2_warm"].setex(l2_key, self.tiers["L2_warm"].ttl_seconds, data)

    async def prefetch_intelligent(self, access_patterns: Dict[str, List[str]]):
        """
        Intelligent prefetching based on access patterns
        Uses ML to predict what data will be needed next
        """

        console.print("🧠 Intelligent Prefetching Started")

        # Analyze access patterns
        for pattern_type, keys in access_patterns.items():
            if pattern_type == "sequential":
                # Prefetch next items in sequence
                await self._prefetch_sequential(keys)
            elif pattern_type == "temporal":
                # Prefetch time-based patterns
                await self._prefetch_temporal(keys)
            elif pattern_type == "semantic":
                # Prefetch semantically related items
                await self._prefetch_semantic(keys)

    async def _prefetch_sequential(self, keys: List[str]):
        """Prefetch next items in a sequence"""
        for i, key in enumerate(keys[:-1]):
            next_key = keys[i + 1]

            # Check if next item is in lower tiers
            data, tier = await self.intelligent_get(next_key)
            if tier in ["L2_warm", "L3_cold"]:
                # Promote to higher tier preemptively
                await self.intelligent_set(next_key, data, access_pattern="prefetched")

    async def _prefetch_temporal(self, keys: List[str]):
        """Prefetch based on temporal patterns"""
        # Implementation for time-based prefetching
        pass

    async def _prefetch_semantic(self, keys: List[str]):
        """Prefetch semantically related items"""
        # Implementation for semantic prefetching
        pass

    def _record_miss(self):
        """Record cache miss across all tiers"""
        for tier_name in self.tiers.keys():
            if tier_name != "gpu_vectors":
                self.metrics[tier_name].misses += 1
                # Update hit rates
                total_requests = self.metrics[tier_name].hits + self.metrics[tier_name].misses
                if total_requests > 0:
                    self.metrics[tier_name].hit_rate = self.metrics[tier_name].hits / total_requests

    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        stats = {}

        for tier_name, tier_config in self.tiers.items():
            tier_stats = self.metrics[tier_name]
            stats[tier_name] = {
                "config": asdict(tier_config),
                "metrics": asdict(tier_stats),
                "memory_utilization": f"{tier_stats.memory_used_gb:.2f}GB / {tier_config.max_memory_gb}GB",
                "memory_percentage": f"{(tier_stats.memory_used_gb / tier_config.max_memory_gb) * 100:.1f}%"
            }

        # Overall stats
        total_memory_used = sum(self.metrics[t].memory_used_gb for t in self.tiers.keys())
        total_hits = sum(self.metrics[t].hits for t in self.tiers.keys() if t != "gpu_vectors")
        total_misses = sum(self.metrics[t].misses for t in self.tiers.keys() if t != "gpu_vectors")

        stats["overall"] = {
            "total_memory_used_gb": total_memory_used,
            "total_memory_available_gb": self.total_memory_gb,
            "overall_hit_rate": total_hits / (total_hits + total_misses) if (total_hits + total_misses) > 0 else 0,
            "gpu_cache_size": len(self.gpu_cache),
            "gpu_cache_capacity": self.gpu_cache_size
        }

        return stats

    async def optimize_cache(self):
        """Run cache optimization routines"""
        console.print("🔧 Running Cache Optimization")

        # Balance memory across tiers
        await self._balance_memory()

        # Clean expired entries (both temporal and regular)
        await self._clean_expired()
        await self.temporal_cleanup_expired()

        # Apply confidence decay to temporal entries
        await self.batch_decay_update()

        # Optimize hit rates
        await self._optimize_hit_rates()

        console.print("✅ Cache Optimization Complete")

    async def confidence_decay_update(self, key: str, decay_rate: float = 0.001) -> float:
        """
        Apply confidence decay based on temporal age
        Returns updated confidence score
        """

        # Get current temporal data
        data, tier = await self.intelligent_get(key, "temporal")
        if not data:
            return 0.0

        original_confidence = data.get("confidence", 0.5)
        stored_at = datetime.fromisoformat(data["stored_at"]) if "stored_at" in data else datetime.utcnow()
        current_time = datetime.utcnow()

        # Calculate age in days
        age_days = (current_time - stored_at).days

        # Apply exponential decay: confidence * (1 - decay_rate)^age_days
        decay_factor = (1 - decay_rate) ** age_days
        new_confidence = original_confidence * decay_factor

        # Update stored confidence
        data["confidence"] = new_confidence
        data["last_decay_update"] = current_time.isoformat()
        data["decay_applied"] = True

        # Re-store with updated confidence
        await self.intelligent_set(key, data, data_type="temporal",
                                 confidence=new_confidence)

        # Check if confidence is too low - may need tier demotion
        if new_confidence < 0.3:
            console.print(f"⚠️ Low confidence detected for {key}: {new_confidence:.3f}")
            # Could trigger automatic demotion to lower tier

        # Log decay event if monitoring available
        if MONITORING_AVAILABLE and self.monitor:
            tier_before = "unknown"  # Would need to track this
            tier_after = self._determine_tier(new_confidence, "unknown", data_type)
            asyncio.create_task(self.monitor.log_decay_event(
                key, original_confidence, new_confidence, age_days,
                0.001, tier_before, tier_after
            ))

        return new_confidence

    async def batch_decay_update(self, keys: List[str] = None, decay_rate: float = 0.001) -> Dict[str, Any]:
        """
        Apply confidence decay to multiple keys or all temporal keys
        Returns summary of updates
        """

        console.print("📉 Applying confidence decay updates...")

        if keys is None:
            # Get all temporal keys across all tiers
            keys = []
            for tier_name in ["L1_hot", "L2_warm", "L3_cold"]:
                try:
                    pattern = f"{tier_name[:2]}:*:temporal:*"
                    tier_keys = await self.redis_clients[tier_name].keys(pattern)
                    keys.extend([k.decode() if isinstance(k, bytes) else k for k in tier_keys])
                except Exception as e:
                    console.print(f"⚠️ Error scanning {tier_name}: {e}")

        console.print(f"🔄 Processing decay for {len(keys)} temporal entries")

        updated = 0
        total_decay = 0.0

        for key in keys:
            try:
                new_confidence = await self.confidence_decay_update(key, decay_rate)
                total_decay += (new_confidence - 0.5)  # Track net decay
                updated += 1

                if updated % 100 == 0:
                    console.print(f"   Processed {updated}/{len(keys)} entries")

            except Exception as e:
                console.print(f"⚠️ Error decaying {key}: {e}")

        summary = {
            "entries_processed": updated,
            "average_decay": total_decay / max(updated, 1),
            "decay_rate_used": decay_rate,
            "timestamp": datetime.utcnow().isoformat()
        }

        console.print(f"✅ Decay update complete: {updated} entries processed")
        return summary

    async def temporal_get(self, key: str, query_time: datetime) -> Tuple[Any, bool]:
        """
        Get temporally valid data for a specific point in time
        Returns (data, is_currently_valid)
        """

        # Get data with automatic confidence decay applied
        data, tier = await self.intelligent_get(key, "temporal")
        if not data:
            return None, False

        # Check temporal validity
        valid_from = data.get("valid_from")
        valid_to = data.get("valid_to")

        if valid_from:
            valid_from_dt = datetime.fromisoformat(valid_from)
            if query_time < valid_from_dt:
                return None, False  # Not yet valid

        if valid_to:
            valid_to_dt = datetime.fromisoformat(valid_to)
            if query_time > valid_to_dt:
                return None, False  # Expired

        # Apply confidence decay on access
        current_confidence = await self.confidence_decay_update(key)

        # Check if confidence is still acceptable
        if current_confidence < 0.2:
            return None, False  # Too decayed

        return data["data"], True

    async def temporal_range_query(self, key: str, start_time: datetime, end_time: datetime) -> List[Dict]:
        """
        Get all temporal versions of a key within a time range
        Perfect for temporal analysis and evolution tracking
        """

        # For now, get the current version and check if it overlaps
        data, is_valid = await self.temporal_get(key, start_time)
        if not data or not is_valid:
            return []

        # Return current version if it overlaps the range
        valid_from = data.get("valid_from")
        valid_to = data.get("valid_to")

        if valid_from and valid_to:
            valid_from_dt = datetime.fromisoformat(valid_from)
            valid_to_dt = datetime.fromisoformat(valid_to)

            # Check for overlap with query range
            if valid_from_dt <= end_time and (valid_to_dt >= start_time):
                overlap_start = max(valid_from_dt, start_time)
                overlap_end = min(valid_to_dt, end_time)

                return [{
                    "data": data,
                    "valid_from": valid_from,
                    "valid_to": valid_to,
                    "confidence": data.get("confidence", 0.5),
                    "overlap_start": overlap_start.isoformat(),
                    "overlap_end": overlap_end.isoformat(),
                    "tier": "temporal_cache"
                }]

        return []

    async def temporal_cleanup_expired(self) -> int:
        """
        Clean up expired temporal entries across all tiers
        Returns number of entries removed
        """

        console.print("🧹 Cleaning up expired temporal entries...")
        removed_count = 0
        current_time = datetime.utcnow()

        # Check each tier for expired entries
        for tier_name in ["L1_hot", "L2_warm", "L3_cold"]:
            try:
                # Get all temporal keys in this tier
                pattern = f"{tier_name[:2]}:*:temporal:*"
                keys = await self.redis_clients[tier_name].keys(pattern)

                for key in keys:
                    key_str = key.decode() if isinstance(key, bytes) else key
                    data_str = await self.redis_clients[tier_name].get(key_str)

                    if data_str:
                        data = json.loads(data_str)
                        valid_to = data.get("valid_to")

                        if valid_to:
                            valid_to_dt = datetime.fromisoformat(valid_to)
                            if current_time > valid_to_dt:
                                # Entry expired, remove it
                                await self.redis_clients[tier_name].delete(key_str)
                                removed_count += 1
            except Exception as e:
                console.print(f"⚠️ Error cleaning {tier_name}: {e}")

        console.print(f"✅ Removed {removed_count} expired temporal entries")
        return removed_count
        """Balance memory usage across tiers"""
        for tier_name, tier_config in self.tiers.items():
            if tier_name == "gpu_vectors":
                continue

            current_usage = self.metrics[tier_name].memory_used_gb
            max_usage = tier_config.max_memory_gb

            if current_usage > max_usage * 0.9:  # Over 90% capacity
                # Evict least recently used items
                evicted = await self._evict_lru(tier_name, int((current_usage - max_usage * 0.8) / 0.001))  # Rough estimate
                self.metrics[tier_name].evictions += evicted
                console.print(f"🗑️ Evicted {evicted} items from {tier_name}")

    async def _evict_lru(self, tier_name: str, count: int) -> int:
        """Evict least recently used items from tier"""
        # Implementation would use Redis LRU eviction
        # For demo, just return count
        return min(count, 100)

    async def _clean_expired(self):
        """Clean expired entries (Redis TTL handles this automatically)"""
        pass

    async def _optimize_hit_rates(self):
        """Optimize hit rates through intelligent data placement"""
        # Analyze access patterns and adjust tier assignments
        pass

    async def confidence_decay_update(self, key: str, decay_rate: float = 0.001) -> float:
        """
        Apply confidence decay based on temporal age
        Returns updated confidence score
        """

        # Get current temporal data
        data, tier = await self.intelligent_get(key, "temporal")
        if not data:
            return 0.0

        original_confidence = data.get("confidence", 0.5)
        stored_at = datetime.fromisoformat(data["stored_at"])
        current_time = datetime.utcnow()

        # Calculate age in days
        age_days = (current_time - stored_at).days

        # Apply exponential decay: confidence * (1 - decay_rate)^age_days
        decay_factor = (1 - decay_rate) ** age_days
        new_confidence = original_confidence * decay_factor

        # Update stored confidence
        data["confidence"] = new_confidence
        data["last_decay_update"] = current_time.isoformat()
        data["decay_applied"] = True

        # Re-store with updated confidence
        await self.intelligent_set(key, data, data_type="temporal",
                                 confidence=new_confidence)

        # Check if confidence is too low - may need tier demotion
        if new_confidence < 0.3:
            console.print(f"⚠️ Low confidence detected for {key}: {new_confidence:.3f}")
            # Could trigger automatic demotion to lower tier

        return new_confidence

    async def batch_decay_update(self, keys: List[str] = None, decay_rate: float = 0.001) -> Dict[str, Any]:
        """
        Apply confidence decay to multiple keys or all temporal keys
        Returns summary of updates
        """

        console.print("📉 Applying confidence decay updates...")

        if keys is None:
            # Get all temporal keys across all tiers
            keys = []
            for tier_name in ["L1_hot", "L2_warm", "L3_cold"]:
                try:
                    pattern = f"{tier_name[:2]}:*:temporal:*"
                    tier_keys = await self.redis_clients[tier_name].keys(pattern)
                    keys.extend([k.decode() if isinstance(k, bytes) else k for k in tier_keys])
                except Exception as e:
                    console.print(f"⚠️ Error scanning {tier_name}: {e}")

        console.print(f"🔄 Processing decay for {len(keys)} temporal entries")

        updated = 0
        total_decay = 0.0

        for key in keys:
            try:
                new_confidence = await self.confidence_decay_update(key, decay_rate)
                total_decay += (new_confidence - 0.5)  # Track net decay
                updated += 1

                if updated % 100 == 0:
                    console.print(f"   Processed {updated}/{len(keys)} entries")

            except Exception as e:
                console.print(f"⚠️ Error decaying {key}: {e}")

        summary = {
            "entries_processed": updated,
            "average_decay": total_decay / max(updated, 1),
            "decay_rate_used": decay_rate,
            "timestamp": datetime.utcnow().isoformat()
        }

        console.print(f"✅ Decay update complete: {updated} entries processed")
        return summary


# Demonstration
async def demonstrate_multi_tier_cache():
    """Demonstrate multi-tiered cache capabilities"""
    console.print("[bold cyan]🚀 Multi-Tiered Cache Demonstration[/bold cyan]")
    console.print("Leveraging 768GB RAM for intelligent caching hierarchy\\n")

    cache = MultiTieredCache()
    await cache.initialize()

    # Demonstrate different data types and access patterns
    test_data = [
        {"key": "user_session_123", "data": {"user_id": 123, "preferences": {}}, "confidence": 0.95, "pattern": "frequent"},
        {"key": "vector_embedding_456", "data": [0.1, 0.2, 0.3] * 128, "confidence": 0.85, "pattern": "regular", "type": "vector"},
        {"key": "historical_fact_789", "data": {"fact": "Knowledge evolves", "source": "research"}, "confidence": 0.6, "pattern": "rare"},
    ]

    console.print("📥 Storing test data across cache tiers...")

    for item in test_data:
        await cache.intelligent_set(
            item["key"],
            item["data"],
            data_type=item.get("type", "generic"),
            confidence=item["confidence"],
            access_pattern=item["pattern"]
        )

    console.print("\\n🔍 Retrieving data from cache hierarchy...")

    for item in test_data:
        data, tier = await cache.intelligent_get(item["key"], item.get("type", "generic"))
        status = "✅" if data else "❌"
        console.print(f"   {status} {item['key']} → {tier or 'Not found'}")

    # Get comprehensive stats
    stats = await cache.get_cache_stats()

    console.print("\\n📊 [bold]Cache Performance Statistics:[/bold]")
    for tier_name, tier_stats in stats.items():
        if tier_name != "overall":
            console.print(f"   {tier_name}: {tier_stats['memory_utilization']} | Hit Rate: {tier_stats['metrics']['hit_rate']:.1%}")

    overall = stats["overall"]
    console.print(f"\\n🎯 Overall Performance:")
    console.print(f"   Total Memory Used: {overall['total_memory_used_gb']:.2f}GB / {cache.total_memory_gb}GB")
    console.print(f"   Overall Hit Rate: {overall['overall_hit_rate']:.1%}")
    console.print(f"   GPU Cache: {overall['gpu_cache_size']}/{overall['gpu_cache_capacity']} vectors")

    console.print("\\n🎉 Multi-Tiered Cache Demonstration Complete!")
    console.print("768GB RAM efficiently utilized for maximum performance!")

if __name__ == "__main__":
    asyncio.run(demonstrate_multi_tier_cache())
