"""
Threat Memory System - Redis-First Architecture

CRITICAL: ALL data goes to Redis FIRST, then background export to Neo4j

Purpose:
- Remember important threats long-term
- Track threat evolution over time
- Detect multi-threat campaigns
- Learn from analyst validation

Redis-First Principle:
1. Memory formed → Redis Hash (source of truth)
2. Queue for export → Redis Set
3. Background worker → Neo4j (async, non-blocking)
"""

import json
import os
import uuid
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set as TypingSet, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

import redis.asyncio as redis
import os
from neo4j import AsyncGraphDatabase


class MemoryType(Enum):
    """Types of memories we form"""
    CAMPAIGN = "campaign"           # Part of multi-threat campaign
    EVOLUTION = "evolution"         # Threat that evolved
    PATTERN = "pattern"             # Recurring pattern detected
    FALSE_POSITIVE = "false_positive"  # Learn what's not a real threat
    VALIDATED = "validated"         # Analyst-validated important threat


@dataclass
class MemoryFormationDecision:
    """Result of should_form_memory analysis"""
    should_form: bool
    confidence: float  # 0.0-1.0
    factors: Dict[str, float]  # Breakdown of scoring factors
    memory_type: MemoryType
    reason: str


@dataclass
class ThreatMemory:
    """Represents a formed memory (stored in Redis)"""
    id: str
    threat_id: str
    content: str
    confidence: float
    formed_at: str
    last_updated: str
    evidence_count: int
    analyst_interactions: int
    industry: str
    severity: str
    memory_type: str
    metadata: Dict
    neo4j_exported: bool = False
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for Redis storage"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ThreatMemory':
        """Create from Redis dictionary"""
        return cls(**data)


class ThreatMemorySystem:
    """
    Redis-First Threat Memory System
    
    Architecture:
    - Redis Hashes: Primary storage (cascade:memory:{id})
    - Redis Sets: Indexing and queuing
    - Neo4j: Secondary (async background export)
    
    Based on existing patterns:
    - EnterpriseBase monitoring
    - Redis-First architecture (redis_first_cyberpi_importer.py)
    - Graph patterns (unified_threat_graph_builder.py)
    """
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:32379",
        neo4j_uri: str = "bolt://localhost:7687",
        neo4j_user: str = "neo4j",
        neo4j_password: Optional[str] = None
    ):
        """
        Initialize memory system
        
        Args:
            redis_url: Redis connection (NodePort 32379)
            neo4j_uri: Neo4j for graph queries (optional)
            neo4j_user: Neo4j username
            neo4j_password: Neo4j password
        """
        self.redis_url = redis_url
        self.neo4j_uri = neo4j_uri
        self.neo4j_auth = (neo4j_user, neo4j_password)
        
        self._redis_client: Optional[redis.Redis] = None
        self._neo4j_driver = None
        
        # Configuration
        self.formation_threshold = 0.7  # Conservative (nuclear-grade)
        self.memory_ttl = 90 * 24 * 3600  # 90 days
        
    async def connect(self):
        """Establish Redis connection (Neo4j lazy-loaded)"""
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
    
    async def should_form_memory(
        self,
        threat_id: str,
        analyst_actions: List[Dict],
        threat_data: Dict
    ) -> MemoryFormationDecision:
        """
        Decide if threat warrants long-term memory
        
        Multi-factor scoring (nuclear engineering principle):
        - Multiple independent signals
        - Conservative thresholds
        - False positive suppression
        
        Args:
            threat_id: Threat identifier
            analyst_actions: List of analyst interactions
            threat_data: Threat metadata
            
        Returns:
            Decision with confidence and reasoning
        """
        
        # Factor 1: Analyst Engagement (35% weight)
        engagement_score = self._calculate_engagement_score(analyst_actions)
        
        # Factor 2: Source Validation (25% weight)
        source_score = self._calculate_source_score(threat_data)
        
        # Factor 3: Temporal Pattern (25% weight)
        temporal_score = await self._calculate_temporal_score(threat_id, threat_data)
        
        # Factor 4: Impact Evidence (15% weight)
        impact_score = self._calculate_impact_score(threat_data)
        
        # Weighted composite score
        composite = (
            engagement_score * 0.35 +
            source_score * 0.25 +
            temporal_score * 0.25 +
            impact_score * 0.15
        )
        
        # Determine memory type
        memory_type = self._determine_memory_type(
            analyst_actions, threat_data, temporal_score
        )
        
        # Reason generation
        reason = self._generate_formation_reason(
            engagement_score, source_score, temporal_score, impact_score, memory_type
        )
        
        return MemoryFormationDecision(
            should_form=composite >= self.formation_threshold,
            confidence=composite,
            factors={
                'engagement': engagement_score,
                'source': source_score,
                'temporal': temporal_score,
                'impact': impact_score
            },
            memory_type=memory_type,
            reason=reason
        )
    
    def _calculate_engagement_score(self, analyst_actions: List[Dict]) -> float:
        """
        Score based on analyst engagement
        
        Factors:
        - Unique analysts (more = more important)
        - Escalations (validation)
        - Time spent (serious investigation)
        """
        if not analyst_actions:
            return 0.0
        
        # Unique analysts
        unique_analysts = len(set(a.get('analyst_id') for a in analyst_actions))
        analyst_score = min(1.0, unique_analysts / 5)  # 5+ analysts = 1.0
        
        # Escalations
        escalations = sum(1 for a in analyst_actions if a.get('action_type') == 'escalate')
        escalation_score = min(1.0, escalations / 3)  # 3+ escalations = 1.0
        
        # Total time spent
        total_time = sum(a.get('time_spent_seconds', 0) for a in analyst_actions)
        time_score = min(1.0, total_time / 600)  # 10+ minutes = 1.0
        
        return (analyst_score * 0.4 + escalation_score * 0.4 + time_score * 0.2)
    
    def _calculate_source_score(self, threat_data: Dict) -> float:
        """
        Score based on source validation
        
        Factors:
        - Multiple sources (cross-validation)
        - Source reliability
        """
        sources = threat_data.get('sources', [])
        source_count = len(sources) if isinstance(sources, list) else 1
        count_score = min(1.0, source_count / 5)  # 5+ sources = 1.0
        
        reliability = threat_data.get('source_reliability', 0.5)
        
        return (count_score * 0.6 + reliability * 0.4)
    
    async def _calculate_temporal_score(self, threat_id: str, threat_data: Dict) -> float:
        """
        Score based on temporal patterns
        
        Factors:
        - Recurrence (seen before)
        - Evolution (changing threat)
        - Campaign membership
        """
        # Check recurrence (how many times seen in last 30 days)
        recurrence = await self._check_recurrence(threat_id, days=30)
        recurrence_score = min(1.0, recurrence / 3)  # 3+ times = 1.0
        
        # Check evolution (has this threat evolved?)
        evolution_detected = await self._check_evolution(threat_id)
        evolution_score = 1.0 if evolution_detected else 0.0
        
        # Check campaign membership
        campaign_member = await self._check_campaign_membership(threat_id)
        campaign_score = 1.0 if campaign_member else 0.0
        
        return (
            recurrence_score * 0.4 +
            evolution_score * 0.3 +
            campaign_score * 0.3
        )
    
    def _calculate_impact_score(self, threat_data: Dict) -> float:
        """
        Score based on impact evidence
        
        Factors:
        - Severity level
        - Confidence in threat
        """
        severity_map = {
            'CRITICAL': 1.0,
            'HIGH': 0.7,
            'MEDIUM': 0.4,
            'LOW': 0.1
        }
        severity_score = severity_map.get(threat_data.get('severity', 'MEDIUM'), 0.5)
        confidence_score = threat_data.get('confidence', 0.5)
        
        return severity_score * confidence_score
    
    def _determine_memory_type(
        self,
        analyst_actions: List[Dict],
        threat_data: Dict,
        temporal_score: float
    ) -> MemoryType:
        """Determine what type of memory this is"""
        
        # Check if validated by analysts
        escalations = sum(1 for a in analyst_actions if a.get('action_type') == 'escalate')
        if escalations >= 2:
            return MemoryType.VALIDATED
        
        # Check if part of campaign (high temporal score)
        if temporal_score > 0.8:
            return MemoryType.CAMPAIGN
        
        # Check if evolution
        # (Would check Redis for related memories here)
        
        # Default to pattern
        return MemoryType.PATTERN
    
    def _generate_formation_reason(
        self,
        engagement: float,
        source: float,
        temporal: float,
        impact: float,
        memory_type: MemoryType
    ) -> str:
        """Generate human-readable reason for memory formation"""
        reasons = []
        
        if engagement > 0.7:
            reasons.append("high analyst engagement")
        if source > 0.7:
            reasons.append("multiple validated sources")
        if temporal > 0.7:
            reasons.append("recurring or campaign-related")
        if impact > 0.7:
            reasons.append("high severity and confidence")
        
        reason_str = ", ".join(reasons) if reasons else "composite factors"
        return f"Memory formed ({memory_type.value}): {reason_str}"
    
    async def _check_recurrence(self, threat_id: str, days: int = 30) -> int:
        """Check how many times threat seen recently (placeholder)"""
        # TODO: Query Redis for related threats
        return 0
    
    async def _check_evolution(self, threat_id: str) -> bool:
        """Check if threat has evolved (placeholder)"""
        # TODO: Check Redis for evolution chain
        return False
    
    async def _check_campaign_membership(self, threat_id: str) -> bool:
        """Check if threat is part of campaign (placeholder)"""
        # TODO: Check Redis Sets for campaign membership
        return False
    
    async def form_memory(
        self,
        threat_id: str,
        analyst_actions: List[Dict],
        threat_data: Dict,
        decision: MemoryFormationDecision
    ) -> ThreatMemory:
        """
        Create memory in Redis (Redis-First!)
        
        Process:
        1. Create memory object
        2. Write to Redis Hash
        3. Update index Sets
        4. Queue for Neo4j export
        
        Args:
            threat_id: Threat identifier
            analyst_actions: Analyst interactions
            threat_data: Threat metadata
            decision: Formation decision
            
        Returns:
            Created memory object
        """
        await self.connect()
        
        # Create memory ID
        memory_id = f"mem_{uuid.uuid4().hex[:12]}"
        
        # Build memory object
        memory = ThreatMemory(
            id=memory_id,
            threat_id=threat_id,
            content=threat_data.get('description', threat_data.get('title', 'Unknown')),
            confidence=decision.confidence,
            formed_at=datetime.utcnow().isoformat(),
            last_updated=datetime.utcnow().isoformat(),
            evidence_count=len(analyst_actions) + len(threat_data.get('sources', [])),
            analyst_interactions=len(analyst_actions),
            industry=threat_data.get('industry', 'unknown'),
            severity=threat_data.get('severity', 'MEDIUM'),
            memory_type=decision.memory_type.value,
            metadata={
                'formation_factors': decision.factors,
                'reason': decision.reason
            },
            neo4j_exported=False
        )
        
        # REDIS-FIRST: Write to Redis Hash
        memory_key = f"cascade:memory:{memory_id}"
        await self._redis_client.hset(
            memory_key,
            mapping={k: json.dumps(v) if isinstance(v, dict) else str(v) 
                    for k, v in memory.to_dict().items()}
        )
        
        # Set TTL
        await self._redis_client.expire(memory_key, self.memory_ttl)
        
        # Update index Sets
        await self._redis_client.sadd("cascade:memory:all", memory_id)
        await self._redis_client.sadd(
            f"cascade:memory:industry:{memory.industry}",
            memory_id
        )
        await self._redis_client.sadd(
            f"cascade:memory:type:{memory.memory_type}",
            memory_id
        )
        
        # Queue for Neo4j export (background worker will handle)
        await self._redis_client.sadd("cascade:memory:export:pending", memory_id)
        
        return memory
    
    async def get_memory(self, memory_id: str) -> Optional[ThreatMemory]:
        """
        Retrieve memory from Redis
        
        Args:
            memory_id: Memory identifier
            
        Returns:
            Memory object or None
        """
        await self.connect()
        
        memory_key = f"cascade:memory:{memory_id}"
        data = await self._redis_client.hgetall(memory_key)
        
        if not data:
            return None
        
        # Deserialize
        deserialized = {}
        for k, v in data.items():
            if k in ['metadata', 'formation_factors']:
                deserialized[k] = json.loads(v) if v else {}
            elif k in ['confidence', 'evidence_count', 'analyst_interactions']:
                deserialized[k] = float(v) if k == 'confidence' else int(v)
            elif k == 'neo4j_exported':
                deserialized[k] = v.lower() == 'true'
            else:
                deserialized[k] = v
        
        return ThreatMemory.from_dict(deserialized)
    
    async def get_memories_by_industry(
        self,
        industry: str,
        limit: int = 100
    ) -> List[ThreatMemory]:
        """
        Get all memories for an industry
        
        Args:
            industry: Industry name
            limit: Maximum memories to return
            
        Returns:
            List of memories
        """
        await self.connect()
        
        # Get memory IDs from Set
        memory_ids = await self._redis_client.smembers(
            f"cascade:memory:industry:{industry}"
        )
        
        # Fetch memories
        memories = []
        for mem_id in list(memory_ids)[:limit]:
            memory = await self.get_memory(mem_id)
            if memory:
                memories.append(memory)
        
        return memories
    
    async def count_memories(self) -> int:
        """Get total memory count"""
        await self.connect()
        return await self._redis_client.scard("cascade:memory:all")


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def demo():
        """Demonstration of memory formation"""
        system = ThreatMemorySystem()
        
        try:
            # Sample threat data
            threat_data = {
                'threat_id': 'threat_lockbit_001',
                'title': 'Lockbit Ransomware targeting aviation',
                'description': 'New Lockbit variant detected targeting airlines',
                'severity': 'CRITICAL',
                'confidence': 0.9,
                'industry': 'aviation',
                'sources': ['cisa', 'twitter', 'vendor_alert']
            }
            
            # Sample analyst actions
            analyst_actions = [
                {'analyst_id': 'analyst_1', 'action_type': 'view', 'time_spent_seconds': 120},
                {'analyst_id': 'analyst_2', 'action_type': 'escalate', 'time_spent_seconds': 180},
                {'analyst_id': 'analyst_3', 'action_type': 'escalate', 'time_spent_seconds': 90},
            ]
            
            # Check if we should form memory
            decision = await system.should_form_memory(
                'threat_lockbit_001',
                analyst_actions,
                threat_data
            )
            
            print(f"Should form memory: {decision.should_form}")
            print(f"Confidence: {decision.confidence:.2f}")
            print(f"Factors: {decision.factors}")
            print(f"Reason: {decision.reason}")
            
            if decision.should_form:
                # Form memory in Redis
                memory = await system.form_memory(
                    'threat_lockbit_001',
                    analyst_actions,
                    threat_data,
                    decision
                )
                print(f"\nMemory formed: {memory.id}")
                print(f"Stored in Redis: cascade:memory:{memory.id}")
                
                # Retrieve it back
                retrieved = await system.get_memory(memory.id)
                print(f"Retrieved confidence: {retrieved.confidence:.2f}")
                
                # Count memories
                count = await system.count_memories()
                print(f"Total memories: {count}")
        
        finally:
            await system.disconnect()
    
    asyncio.run(demo())
