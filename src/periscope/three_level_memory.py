"""
Three-Level Memory System for Cascade Threat Intelligence

Inspired by human memory architecture:

LEVEL 1: WORKING MEMORY (Redis Strings/Hashes, TTL: 1 hour)
- Active threats being analyzed RIGHT NOW
- Real-time analyst interactions
- Immediate context for current investigations
- Fast access, volatile, high churn

LEVEL 2: SHORT-TERM MEMORY (Redis Sorted Sets, TTL: 7 days)
- Recently validated threats
- Patterns emerging this week
- Active campaigns in progress
- Consolidation from working memory

LEVEL 3: LONG-TERM MEMORY (Redis Hashes + Neo4j, TTL: 90 days+)
- Important validated threats
- Historical campaigns
- Learned patterns and evolution chains
- Permanent knowledge base

Data Flow:
Working → Short-Term (if validated) → Long-Term (if significant)
"""

import json
import os
import uuid
import os
import time
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

import redis.asyncio as redis
import os
from neo4j import AsyncGraphDatabase


class MemoryLevel(Enum):
    """Three levels of memory"""
    WORKING = "working"           # Level 1: Active now
    SHORT_TERM = "short_term"     # Level 2: Recent validated
    LONG_TERM = "long_term"       # Level 3: Permanent knowledge


class MemoryType(Enum):
    """Types of memories"""
    CAMPAIGN = "campaign"
    EVOLUTION = "evolution"
    PATTERN = "pattern"
    VALIDATED = "validated"
    FALSE_POSITIVE = "false_positive"


@dataclass
class WorkingMemory:
    """Level 1: Active threat being analyzed"""
    id: str
    threat_id: str
    content: str
    severity: str
    started_at: str
    last_activity: str
    analyst_count: int
    interaction_count: int
    metadata: Dict
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'WorkingMemory':
        return cls(**data)


@dataclass
class ShortTermMemory:
    """Level 2: Recently validated threat"""
    id: str
    threat_id: str
    content: str
    confidence: float
    severity: str
    industry: str
    formed_at: str
    last_updated: str
    evidence_count: int
    analyst_interactions: int
    memory_type: str
    score: float  # For sorted set ranking
    metadata: Dict
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ShortTermMemory':
        return cls(**data)


@dataclass
class LongTermMemory:
    """Level 3: Permanent knowledge"""
    id: str
    threat_id: str
    content: str
    confidence: float
    severity: str
    industry: str
    formed_at: str
    last_updated: str
    evidence_count: int
    analyst_interactions: int
    memory_type: str
    consolidation_count: int  # How many times reinforced
    metadata: Dict
    neo4j_exported: bool
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'LongTermMemory':
        return cls(**data)


class ThreeLevelMemorySystem:
    """
    Three-Level Memory Architecture
    
    Redis Keys:
    - cascade:working:{threat_id} - Hash (Level 1)
    - cascade:working:active - Set of active threat IDs
    - cascade:short:{memory_id} - Hash (Level 2)
    - cascade:short:ranked - Sorted Set by score (Level 2)
    - cascade:long:{memory_id} - Hash (Level 3)
    - cascade:long:all - Set of all long-term memory IDs
    - cascade:long:industry:{industry} - Set by industry
    """
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:32379",
        neo4j_uri: str = "bolt://localhost:7687",
        neo4j_user: str = "neo4j",
        neo4j_password: Optional[str] = None
    ):
        self.redis_url = redis_url
        self.neo4j_uri = neo4j_uri
        self.neo4j_auth = (neo4j_user, neo4j_password)
        
        self._redis_client: Optional[redis.Redis] = None
        self._neo4j_driver = None
        
        # TTL Configuration (nuclear-grade: explicit lifetimes)
        self.working_ttl = 3600  # 1 hour
        self.short_term_ttl = 7 * 24 * 3600  # 7 days
        self.long_term_ttl = 90 * 24 * 3600  # 90 days
        
        # Promotion thresholds
        self.working_to_short_threshold = 0.6  # Moderate confidence
        self.short_to_long_threshold = 0.8  # High confidence
    
    async def connect(self):
        """Establish Redis connection"""
        if not self._redis_client:
            self._redis_client = await redis.from_url(
                self.redis_url,
                decode_responses=True
            )
    
    async def disconnect(self):
        """Close connections"""
        if self._redis_client:
            await self._redis_client.close()
            self._redis_client = None
        
        if self._neo4j_driver:
            await self._neo4j_driver.close()
            self._neo4j_driver = None
    
    # ========================================================================
    # LEVEL 1: WORKING MEMORY
    # ========================================================================
    
    async def add_to_working_memory(
        self,
        threat_id: str,
        content: str,
        severity: str,
        metadata: Dict = None
    ) -> WorkingMemory:
        """
        Add threat to working memory (Level 1)
        
        This is for threats being actively analyzed RIGHT NOW.
        """
        await self.connect()
        
        memory_id = f"work_{uuid.uuid4().hex[:8]}"
        now = datetime.utcnow().isoformat()
        
        working = WorkingMemory(
            id=memory_id,
            threat_id=threat_id,
            content=content,
            severity=severity,
            started_at=now,
            last_activity=now,
            analyst_count=0,
            interaction_count=0,
            metadata=metadata or {}
        )
        
        # Store in Redis Hash with TTL
        key = f"cascade:working:{threat_id}"
        await self._redis_client.hset(
            key,
            mapping={k: json.dumps(v) if isinstance(v, dict) else str(v)
                    for k, v in working.to_dict().items()}
        )
        await self._redis_client.expire(key, self.working_ttl)
        
        # Add to active set
        await self._redis_client.sadd("cascade:working:active", threat_id)
        await self._redis_client.expire("cascade:working:active", self.working_ttl)
        
        return working
    
    async def update_working_memory(
        self,
        threat_id: str,
        analyst_id: str = None,
        action_type: str = None
    ) -> Optional[WorkingMemory]:
        """
        Update working memory with analyst interaction
        
        Tracks who's looking at what RIGHT NOW.
        """
        await self.connect()
        
        key = f"cascade:working:{threat_id}"
        data = await self._redis_client.hgetall(key)
        
        if not data:
            return None
        
        # Increment counters
        await self._redis_client.hincrby(key, "interaction_count", 1)
        if analyst_id:
            await self._redis_client.hincrby(key, "analyst_count", 1)
        
        # Update last activity
        await self._redis_client.hset(key, "last_activity", datetime.utcnow().isoformat())
        
        # Refresh TTL
        await self._redis_client.expire(key, self.working_ttl)
        
        # Get updated data
        updated_data = await self._redis_client.hgetall(key)
        return self._deserialize_working(updated_data)
    
    async def get_working_memory(self, threat_id: str) -> Optional[WorkingMemory]:
        """Get working memory for threat"""
        await self.connect()
        
        key = f"cascade:working:{threat_id}"
        data = await self._redis_client.hgetall(key)
        
        if not data:
            return None
        
        return self._deserialize_working(data)
    
    async def get_active_threats(self) -> List[str]:
        """Get all threats in working memory"""
        await self.connect()
        return list(await self._redis_client.smembers("cascade:working:active"))
    
    # ========================================================================
    # LEVEL 2: SHORT-TERM MEMORY
    # ========================================================================
    
    async def promote_to_short_term(
        self,
        threat_id: str,
        confidence: float,
        industry: str,
        evidence_count: int,
        analyst_interactions: int,
        memory_type: MemoryType
    ) -> ShortTermMemory:
        """
        Promote from working to short-term memory (Level 2)
        
        This happens when threat is validated but we're still watching it.
        """
        await self.connect()
        
        # Get working memory data
        working = await self.get_working_memory(threat_id)
        if not working:
            raise ValueError(f"No working memory for {threat_id}")
        
        memory_id = f"short_{uuid.uuid4().hex[:10]}"
        now = datetime.utcnow().isoformat()
        
        # Calculate score for ranking (higher = more important)
        score = self._calculate_short_term_score(
            confidence, evidence_count, analyst_interactions
        )
        
        short_term = ShortTermMemory(
            id=memory_id,
            threat_id=threat_id,
            content=working.content,
            confidence=confidence,
            severity=working.severity,
            industry=industry,
            formed_at=now,
            last_updated=now,
            evidence_count=evidence_count,
            analyst_interactions=analyst_interactions,
            memory_type=memory_type.value,
            score=score,
            metadata=working.metadata
        )
        
        # Store in Redis Hash
        key = f"cascade:short:{memory_id}"
        await self._redis_client.hset(
            key,
            mapping={k: json.dumps(v) if isinstance(v, dict) else str(v)
                    for k, v in short_term.to_dict().items()}
        )
        await self._redis_client.expire(key, self.short_term_ttl)
        
        # Add to ranked sorted set
        await self._redis_client.zadd(
            "cascade:short:ranked",
            {memory_id: score}
        )
        
        # Remove from working memory (promoted!)
        await self._redis_client.delete(f"cascade:working:{threat_id}")
        await self._redis_client.srem("cascade:working:active", threat_id)
        
        return short_term
    
    async def get_short_term_memory(self, memory_id: str) -> Optional[ShortTermMemory]:
        """Get short-term memory"""
        await self.connect()
        
        key = f"cascade:short:{memory_id}"
        data = await self._redis_client.hgetall(key)
        
        if not data:
            return None
        
        return self._deserialize_short_term(data)
    
    async def get_top_short_term(self, limit: int = 10) -> List[ShortTermMemory]:
        """Get top-ranked short-term memories"""
        await self.connect()
        
        # Get top memory IDs from sorted set (highest scores first)
        memory_ids = await self._redis_client.zrevrange(
            "cascade:short:ranked", 0, limit - 1
        )
        
        memories = []
        for mem_id in memory_ids:
            memory = await self.get_short_term_memory(mem_id)
            if memory:
                memories.append(memory)
        
        return memories
    
    # ========================================================================
    # LEVEL 3: LONG-TERM MEMORY
    # ========================================================================
    
    async def promote_to_long_term(
        self,
        short_term_id: str
    ) -> LongTermMemory:
        """
        Promote from short-term to long-term memory (Level 3)
        
        This is permanent knowledge - important threats we must remember.
        """
        await self.connect()
        
        # Get short-term memory
        short_term = await self.get_short_term_memory(short_term_id)
        if not short_term:
            raise ValueError(f"No short-term memory: {short_term_id}")
        
        memory_id = f"long_{uuid.uuid4().hex[:12]}"
        now = datetime.utcnow().isoformat()
        
        long_term = LongTermMemory(
            id=memory_id,
            threat_id=short_term.threat_id,
            content=short_term.content,
            confidence=short_term.confidence,
            severity=short_term.severity,
            industry=short_term.industry,
            formed_at=short_term.formed_at,
            last_updated=now,
            evidence_count=short_term.evidence_count,
            analyst_interactions=short_term.analyst_interactions,
            memory_type=short_term.memory_type,
            consolidation_count=1,
            metadata=short_term.metadata,
            neo4j_exported=False
        )
        
        # Store in Redis Hash
        key = f"cascade:long:{memory_id}"
        await self._redis_client.hset(
            key,
            mapping={k: json.dumps(v) if isinstance(v, dict) else str(v)
                    for k, v in long_term.to_dict().items()}
        )
        await self._redis_client.expire(key, self.long_term_ttl)
        
        # Add to indexes
        await self._redis_client.sadd("cascade:long:all", memory_id)
        await self._redis_client.sadd(
            f"cascade:long:industry:{long_term.industry}",
            memory_id
        )
        
        # Queue for Neo4j export
        await self._redis_client.sadd("cascade:long:export:pending", memory_id)
        
        # Remove from short-term (promoted!)
        await self._redis_client.delete(f"cascade:short:{short_term_id}")
        await self._redis_client.zrem("cascade:short:ranked", short_term_id)
        
        return long_term
    
    async def get_long_term_memory(self, memory_id: str) -> Optional[LongTermMemory]:
        """Get long-term memory"""
        await self.connect()
        
        key = f"cascade:long:{memory_id}"
        data = await self._redis_client.hgetall(key)
        
        if not data:
            return None
        
        return self._deserialize_long_term(data)
    
    async def get_long_term_by_industry(
        self,
        industry: str,
        limit: int = 100
    ) -> List[LongTermMemory]:
        """Get long-term memories for industry"""
        await self.connect()
        
        memory_ids = await self._redis_client.smembers(
            f"cascade:long:industry:{industry}"
        )
        
        memories = []
        for mem_id in list(memory_ids)[:limit]:
            memory = await self.get_long_term_memory(mem_id)
            if memory:
                memories.append(memory)
        
        return memories
    
    async def consolidate_long_term(self, memory_id: str):
        """
        Consolidate/reinforce long-term memory
        
        Called when we see the same threat again - strengthens the memory.
        """
        await self.connect()
        
        key = f"cascade:long:{memory_id}"
        await self._redis_client.hincrby(key, "consolidation_count", 1)
        await self._redis_client.hset(key, "last_updated", datetime.utcnow().isoformat())
        
        # Refresh TTL (important memories stay longer)
        await self._redis_client.expire(key, self.long_term_ttl)
    
    # ========================================================================
    # STATISTICS & MONITORING
    # ========================================================================
    
    async def get_memory_stats(self) -> Dict:
        """Get statistics across all three levels"""
        await self.connect()
        
        working_count = await self._redis_client.scard("cascade:working:active")
        short_term_count = await self._redis_client.zcard("cascade:short:ranked")
        long_term_count = await self._redis_client.scard("cascade:long:all")
        
        return {
            'level_1_working': working_count,
            'level_2_short_term': short_term_count,
            'level_3_long_term': long_term_count,
            'total': working_count + short_term_count + long_term_count
        }
    
    # ========================================================================
    # HELPER METHODS
    # ========================================================================
    
    def _calculate_short_term_score(
        self,
        confidence: float,
        evidence_count: int,
        analyst_interactions: int
    ) -> float:
        """Calculate ranking score for short-term memory"""
        # Normalize evidence and interactions
        evidence_score = min(1.0, evidence_count / 10)
        interaction_score = min(1.0, analyst_interactions / 5)
        
        # Weighted composite
        return (confidence * 0.5 + evidence_score * 0.3 + interaction_score * 0.2)
    
    def _deserialize_working(self, data: Dict) -> WorkingMemory:
        """Deserialize working memory from Redis"""
        return WorkingMemory(
            id=data['id'],
            threat_id=data['threat_id'],
            content=data['content'],
            severity=data['severity'],
            started_at=data['started_at'],
            last_activity=data['last_activity'],
            analyst_count=int(data['analyst_count']),
            interaction_count=int(data['interaction_count']),
            metadata=json.loads(data['metadata']) if data.get('metadata') else {}
        )
    
    def _deserialize_short_term(self, data: Dict) -> ShortTermMemory:
        """Deserialize short-term memory from Redis"""
        return ShortTermMemory(
            id=data['id'],
            threat_id=data['threat_id'],
            content=data['content'],
            confidence=float(data['confidence']),
            severity=data['severity'],
            industry=data['industry'],
            formed_at=data['formed_at'],
            last_updated=data['last_updated'],
            evidence_count=int(data['evidence_count']),
            analyst_interactions=int(data['analyst_interactions']),
            memory_type=data['memory_type'],
            score=float(data['score']),
            metadata=json.loads(data['metadata']) if data.get('metadata') else {}
        )
    
    def _deserialize_long_term(self, data: Dict) -> LongTermMemory:
        """Deserialize long-term memory from Redis"""
        return LongTermMemory(
            id=data['id'],
            threat_id=data['threat_id'],
            content=data['content'],
            confidence=float(data['confidence']),
            severity=data['severity'],
            industry=data['industry'],
            formed_at=data['formed_at'],
            last_updated=data['last_updated'],
            evidence_count=int(data['evidence_count']),
            analyst_interactions=int(data['analyst_interactions']),
            memory_type=data['memory_type'],
            consolidation_count=int(data['consolidation_count']),
            metadata=json.loads(data['metadata']) if data.get('metadata') else {},
            neo4j_exported=data['neo4j_exported'].lower() == 'true'
        )


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def demo():
        """Demonstrate three-level memory system"""
        system = ThreeLevelMemorySystem()
        
        try:
            print("🧠 Three-Level Memory System Demo\n")
            
            # LEVEL 1: Add to working memory
            print("📝 LEVEL 1: Adding threat to working memory...")
            working = await system.add_to_working_memory(
                threat_id="threat_001",
                content="Suspicious PowerShell activity detected",
                severity="HIGH",
                metadata={'source': 'EDR', 'host': 'server-01'}
            )
            print(f"   ✅ Working memory: {working.id}")
            
            # Simulate analyst interactions
            print("\n👤 Analysts investigating...")
            await system.update_working_memory("threat_001", "analyst_1", "view")
            await system.update_working_memory("threat_001", "analyst_2", "escalate")
            await system.update_working_memory("threat_001", "analyst_3", "escalate")
            
            # LEVEL 2: Promote to short-term
            print("\n⬆️  LEVEL 2: Promoting to short-term memory...")
            short_term = await system.promote_to_short_term(
                threat_id="threat_001",
                confidence=0.75,
                industry="finance",
                evidence_count=5,
                analyst_interactions=3,
                memory_type=MemoryType.VALIDATED
            )
            print(f"   ✅ Short-term memory: {short_term.id} (score: {short_term.score:.2f})")
            
            # LEVEL 3: Promote to long-term
            print("\n⬆️  LEVEL 3: Promoting to long-term memory...")
            long_term = await system.promote_to_long_term(short_term.id)
            print(f"   ✅ Long-term memory: {long_term.id}")
            
            # Get statistics
            print("\n📊 Memory Statistics:")
            stats = await system.get_memory_stats()
            for level, count in stats.items():
                print(f"   {level}: {count}")
            
            print("\n✅ Demo complete!")
            
        finally:
            await system.disconnect()
    
    asyncio.run(demo())
