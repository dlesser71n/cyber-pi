#!/usr/bin/env python3
"""
Cascade Memory - Threat Operations
High-level threat operations built on golden config base

This module provides threat-specific operations on top of the
TQAKB golden config multi-tier architecture.
"""

import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import redis.asyncio as redis

from .periscope_memory_base import PeriscopeMemory
from .threat_models import (
    WorkingMemory,
    ShortTermMemory,
    LongTermMemory,
    calculate_threat_score,
    should_promote_to_level2,
    should_promote_to_level3,
    determine_memory_type,
    calculate_decay
)
from .analyst_assistant import AnalystAssistant, AssistanceRecommendation


class PeriscopeTriage(PeriscopeMemory):
    """
    Cyber Periscope Triage - Threat Intelligence Operations
    
    Extends Periscope memory base with threat triage and analyst workflow features.
    Implements intelligent threat prioritization and multi-level memory management.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Initialize Analyst Assistant
        self.assistant = None  # Will be initialized after Redis clients are ready
    
    async def initialize_assistant(self):
        """Initialize Analyst Assistant after Redis clients are ready"""
        if self.redis_clients and "Level_1_Working" in self.redis_clients:
            self.assistant = AnalystAssistant(self.redis_clients["Level_1_Working"])
    
    # ========================================================================
    # LEVEL 1: WORKING MEMORY OPERATIONS
    # ========================================================================
    
    async def add_threat(
        self,
        threat_id: str,
        content: str,
        severity: str,
        metadata: Dict = None
    ) -> WorkingMemory:
        """Add threat to Level 1 (Working Memory)"""
        
        memory_id = f"work_{uuid.uuid4().hex[:8]}"
        now = datetime.utcnow().isoformat()
        
        threat = WorkingMemory(
            id=memory_id,
            threat_id=threat_id,
            content=content,
            severity=severity,
            started_at=now,
            last_activity=now,
            metadata=metadata or {}
        )
        
        # Calculate initial threat score
        threat.threat_score = calculate_threat_score(threat)
        
        # Store in Level 1 (DB 1) with INDEXES
        key = f"periscope:L1:{threat_id}"
        client = self.redis_clients["Level_1_Working"]
        
        # Use pipeline for atomic batch operations
        pipe = client.pipeline()
        
        # Store threat data
        pipe.set(key, json.dumps(threat.to_dict()))
        pipe.expire(key, self.tiers["Level_1_Working"].ttl_seconds)
        
        # Add to active set
        pipe.sadd("periscope:L1:active", threat_id)
        
        # ADD INDEXES for instant lookups
        pipe.sadd(f"periscope:L1:by_severity:{severity}", threat_id)
        pipe.zadd("periscope:L1:by_score", {threat_id: threat.threat_score})
        pipe.zadd("periscope:L1:by_time", {threat_id: datetime.utcnow().timestamp()})
        
        # Execute all at once
        await pipe.execute()
        
        self.metrics["Level_1_Working"].sets += 1
        
        return threat
    
    async def record_interaction(
        self,
        threat_id: str,
        analyst_id: str,
        action_type: str = "view"
    ) -> Optional[WorkingMemory]:
        """Record analyst interaction on threat"""
        
        client = self.redis_clients["Level_1_Working"]
        key = f"periscope:L1:{threat_id}"
        
        data = await client.get(key)
        if not data:
            return None
        
        threat = WorkingMemory.from_dict(json.loads(data))
        
        # Update counters
        threat.interaction_count += 1
        if action_type == "escalate":
            threat.escalation_count += 1
        elif action_type == "view":
            threat.view_count += 1
        elif action_type == "dismiss":
            threat.dismiss_count += 1
        
        # Track analyst
        threat.analyst_actions[analyst_id] = action_type
        threat.analyst_count = len(threat.analyst_actions)
        
        # Update activity time
        threat.last_activity = datetime.utcnow().isoformat()
        
        # Recalculate score
        threat.threat_score = calculate_threat_score(threat)
        
        # Save
        await client.set(key, json.dumps(threat.to_dict()))
        await client.expire(key, self.tiers["Level_1_Working"].ttl_seconds)
        
        return threat
    
    async def get_threat(self, threat_id: str) -> Optional[WorkingMemory]:
        """Get threat from Level 1"""
        
        client = self.redis_clients["Level_1_Working"]
        key = f"periscope:L1:{threat_id}"
        
        data = await client.get(key)
        if not data:
            return None
        
        self.metrics["Level_1_Working"].hits += 1
        return WorkingMemory.from_dict(json.loads(data))
    
    async def get_all_active(self) -> List[WorkingMemory]:
        """Get all active threats from Level 1"""
        
        client = self.redis_clients["Level_1_Working"]
        threat_ids = await client.smembers("periscope:L1:active")
        
        threats = []
        for threat_id in threat_ids:
            threat = await self.get_threat(threat_id)
            if threat:
                threats.append(threat)
        
        return threats
    
    async def get_hot_threats(self, min_interactions: int = 3) -> List[WorkingMemory]:
        """Get hot threats (lots of analyst attention)"""
        
        all_threats = await self.get_all_active()
        hot = [t for t in all_threats if t.interaction_count >= min_interactions]
        
        # Sort by interaction count
        hot.sort(key=lambda t: t.interaction_count, reverse=True)
        
        return hot
    
    # ========================================================================
    # LEVEL 2: SHORT-TERM MEMORY OPERATIONS
    # ========================================================================
    
    async def promote_to_short_term(self, threat_id: str) -> Optional[ShortTermMemory]:
        """Promote from Level 1 to Level 2"""
        
        # Get from Level 1
        threat = await self.get_threat(threat_id)
        if not threat:
            return None
        
        # Check promotion criteria (golden pattern)
        if not should_promote_to_level2(threat):
            return None
        
        memory_id = f"short_{uuid.uuid4().hex[:10]}"
        now = datetime.utcnow().isoformat()
        
        # Create Level 2 memory
        short_term = ShortTermMemory(
            id=memory_id,
            threat_id=threat_id,
            content=threat.content,
            confidence=threat.threat_score,
            severity=threat.severity,
            industry=threat.metadata.get('industry', 'unknown'),
            formed_at=now,
            last_updated=now,
            evidence_count=threat.interaction_count,
            analyst_interactions=threat.analyst_count,
            memory_type=determine_memory_type(threat),
            score=threat.threat_score,
            validated=(threat.escalation_count >= 2),
            metadata=threat.metadata
        )
        
        # Store in Level 2 (DB 2)
        client = self.redis_clients["Level_2_ShortTerm"]
        key = f"periscope:L2:{memory_id}"
        
        await client.set(key, json.dumps(short_term.to_dict()))
        await client.expire(key, self.tiers["Level_2_ShortTerm"].ttl_seconds)
        
        # Add to ranked sorted set
        await client.zadd("periscope:L2:ranked", {memory_id: short_term.score})
        
        # Remove from Level 1 (promoted!)
        await self._remove_from_level1(threat_id)
        
        self.metrics["Level_2_ShortTerm"].sets += 1
        self.metrics["Level_1_Working"].promotions += 1
        
        return short_term
    
    async def get_top_threats(self, limit: int = 10) -> List[ShortTermMemory]:
        """Get top-ranked threats from Level 2"""
        
        client = self.redis_clients["Level_2_ShortTerm"]
        
        # Get top memory IDs from sorted set
        memory_ids = await client.zrevrange("periscope:L2:ranked", 0, limit - 1)
        
        memories = []
        for mem_id in memory_ids:
            key = f"periscope:L2:{mem_id}"
            data = await client.get(key)
            if data:
                memories.append(ShortTermMemory.from_dict(json.loads(data)))
        
        return memories
    
    # ========================================================================
    # LEVEL 3: LONG-TERM MEMORY OPERATIONS
    # ========================================================================
    
    async def promote_to_long_term(self, short_term_id: str) -> Optional[LongTermMemory]:
        """Promote from Level 2 to Level 3"""
        
        # Get from Level 2
        client_l2 = self.redis_clients["Level_2_ShortTerm"]
        key_l2 = f"periscope:L2:{short_term_id}"
        
        data = await client_l2.get(key_l2)
        if not data:
            return None
        
        short_term = ShortTermMemory.from_dict(json.loads(data))
        
        # Check promotion criteria
        if not should_promote_to_level3(short_term):
            return None
        
        memory_id = f"long_{uuid.uuid4().hex[:12]}"
        now = datetime.utcnow().isoformat()
        
        # Create Level 3 memory
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
            consolidation_count=short_term.consolidation_count,
            validated=short_term.validated,
            decay_protected=(short_term.validated or short_term.consolidation_count >= 3),
            metadata=short_term.metadata
        )
        
        # Store in Level 3 (DB 3)
        client_l3 = self.redis_clients["Level_3_LongTerm"]
        key_l3 = f"periscope:L3:{memory_id}"
        
        await client_l3.set(key_l3, json.dumps(long_term.to_dict()))
        await client_l3.expire(key_l3, self.tiers["Level_3_LongTerm"].ttl_seconds)
        
        # Add to indexes
        await client_l3.sadd("periscope:L3:all", memory_id)
        await client_l3.sadd(f"periscope:L3:industry:{long_term.industry}", memory_id)
        
        # Queue for Neo4j export
        await client_l3.sadd("periscope:L3:export:pending", memory_id)
        
        # Remove from Level 2 (promoted!)
        await client_l2.delete(key_l2)
        await client_l2.zrem("periscope:L2:ranked", short_term_id)
        
        self.metrics["Level_3_LongTerm"].sets += 1
        self.metrics["Level_2_ShortTerm"].promotions += 1
        
        return long_term
    
    # ========================================================================
    # DECAY OPERATIONS (GOLDEN PATTERN)
    # ========================================================================
    
    async def apply_decay_to_level3(self):
        """Apply confidence decay to Level 3 memories (golden pattern)"""
        
        client = self.redis_clients["Level_3_LongTerm"]
        memory_ids = await client.smembers("periscope:L3:all")
        
        updated = 0
        protected = 0
        
        for memory_id in memory_ids:
            key = f"periscope:L3:{memory_id}"
            data = await client.get(key)
            
            if not data:
                continue
            
            memory = LongTermMemory.from_dict(json.loads(data))
            
            # Calculate age
            formed_at = datetime.fromisoformat(memory.formed_at)
            age_days = (datetime.utcnow() - formed_at).days
            
            # Apply decay (golden pattern: validated threats don't decay)
            new_confidence = calculate_decay(
                memory.confidence,
                decay_rate=0.001,  # 0.1% per day
                days_elapsed=age_days,
                is_validated=memory.decay_protected
            )
            
            if memory.decay_protected:
                protected += 1
            elif abs(new_confidence - memory.confidence) > 0.01:
                # Update confidence
                memory.confidence = new_confidence
                memory.last_updated = datetime.utcnow().isoformat()
                await client.set(key, json.dumps(memory.to_dict()))
                updated += 1
        
        return {"updated": updated, "protected": protected}
    
    # ========================================================================
    # HELPER METHODS
    # ========================================================================
    
    async def _remove_from_level1(self, threat_id: str):
        """Remove threat from Level 1"""
        client = self.redis_clients["Level_1_Working"]
        await client.delete(f"periscope:L1:{threat_id}")
        await client.srem("periscope:L1:active", threat_id)
    
    async def intelligent_get_threat(self, threat_id: str) -> Tuple[Optional[WorkingMemory], str]:
        """
        Intelligent threat retrieval with auto-promotion (FIXED)
        Returns (threat, tier_name) or (None, None)
        """
        
        # Try Level 1 first
        threat = await self.get_threat(threat_id)
        if threat:
            self.metrics["Level_1_Working"].hits += 1
            return threat, "Level_1_Working"
        
        # Try Level 2 - search by threat_id
        client_l2 = self.redis_clients["Level_2_ShortTerm"]
        
        # Scan for threat_id in Level 2 (skip sorted set keys)
        cursor = 0
        while True:
            cursor, keys = await client_l2.scan(cursor, match="periscope:L2:short_*", count=100)
            
            for key in keys:
                try:
                    # Check key type first
                    key_type = await client_l2.type(key)
                    if key_type != 'string':
                        continue
                    
                    data = await client_l2.get(key)
                    if data:
                        memory = ShortTermMemory.from_dict(json.loads(data))
                        if memory.threat_id == threat_id:
                            self.metrics["Level_2_ShortTerm"].hits += 1
                            # Auto-promote to Level 1
                            await self.add_threat(
                                threat_id=memory.threat_id,
                                content=memory.content,
                                severity=memory.severity,
                                metadata=memory.metadata
                            )
                            self.metrics["Level_2_ShortTerm"].promotions += 1
                            
                            # Return as WorkingMemory
                            promoted = await self.get_threat(threat_id)
                            return promoted, "Level_2_ShortTerm"
                except Exception:
                    continue
            
            if cursor == 0:
                break
        
        # Try Level 3 - search by threat_id
        client_l3 = self.redis_clients["Level_3_LongTerm"]
        
        cursor = 0
        while True:
            cursor, keys = await client_l3.scan(cursor, match="periscope:L3:long_*", count=100)
            
            for key in keys:
                try:
                    # Check key type first
                    key_type = await client_l3.type(key)
                    if key_type != 'string':
                        continue
                    
                    data = await client_l3.get(key)
                    if data:
                        memory = LongTermMemory.from_dict(json.loads(data))
                        if memory.threat_id == threat_id:
                            self.metrics["Level_3_LongTerm"].hits += 1
                            # Auto-promote to Level 1
                            await self.add_threat(
                                threat_id=memory.threat_id,
                                content=memory.content,
                                severity=memory.severity,
                                metadata=memory.metadata
                            )
                            self.metrics["Level_3_LongTerm"].promotions += 1
                            
                            promoted = await self.get_threat(threat_id)
                            return promoted, "Level_3_LongTerm"
                except Exception:
                    continue
            
            if cursor == 0:
                break
        
        # Not found
        self._record_miss()
        return None, None
    
    async def remove_threat(self, threat_id: str) -> bool:
        """Remove threat from Level 1"""
        try:
            await self._remove_from_level1(threat_id)
            return True
        except Exception as e:
            return False
    
    async def update_threat(self, threat_id: str, **updates) -> Optional[WorkingMemory]:
        """Update threat fields"""
        try:
            threat = await self.get_threat(threat_id)
            if not threat:
                return None
            
            # Update fields
            for key, value in updates.items():
                if hasattr(threat, key):
                    setattr(threat, key, value)
            
            # Recalculate score
            threat.threat_score = calculate_threat_score(threat)
            
            # Save
            client = self.redis_clients["Level_1_Working"]
            key = f"periscope:L1:{threat_id}"
            await client.set(key, json.dumps(threat.to_dict()))
            await client.expire(key, self.tiers["Level_1_Working"].ttl_seconds)
            
            return threat
        except Exception as e:
            return None
    
    def _record_miss(self):
        """Record cache miss (golden pattern)"""
        for tier in self.metrics.values():
            tier.misses += 1
    
    async def get_stats(self) -> Dict:
        """Get system statistics"""
        
        stats = {
            "tiers": {},
            "total_active": len(await self.redis_clients["Level_1_Working"].smembers("periscope:L1:active")),
            "total_short_term": await self.redis_clients["Level_2_ShortTerm"].zcard("periscope:L2:ranked"),
            "total_long_term": await self.redis_clients["Level_3_LongTerm"].scard("periscope:L3:all"),
        }
        
        for tier_name, metrics in self.metrics.items():
            stats["tiers"][tier_name] = {
                "hits": metrics.hits,
                "misses": metrics.misses,
                "promotions": metrics.promotions,
                "sets": metrics.sets,
                "hit_rate": metrics.hit_rate
            }
        
        return stats
    
    # ========================================================================
    # ANALYST ASSISTANT INTEGRATION
    # ========================================================================
    
    async def get_assistance(
        self,
        threat_id: str,
        analyst_id: str
    ) -> Optional[AssistanceRecommendation]:
        """
        Get AI assistance for threat triage decision
        
        Args:
            threat_id: Threat to get assistance for
            analyst_id: Analyst requesting assistance
        
        Returns:
            AssistanceRecommendation with suggested action and reasoning
        """
        if not self.assistant:
            await self.initialize_assistant()
        
        # Get threat context
        threat = await self.get_threat(threat_id)
        if not threat:
            return None
        
        threat_context = {
            'severity': threat.severity,
            'threat_score': threat.threat_score,
            'analyst_count': threat.analyst_count,
            'escalation_count': threat.escalation_count,
            'metadata': threat.metadata
        }
        
        # Get assistance
        recommendation = await self.assistant.assist_analyst(
            threat_id,
            analyst_id,
            threat_context
        )
        
        return recommendation
    
    async def record_analyst_action(
        self,
        threat_id: str,
        analyst_id: str,
        action: str,
        outcome: Optional[str] = None
    ):
        """
        Record analyst action for learning
        
        Args:
            threat_id: Threat that was acted upon
            analyst_id: Analyst who took action
            action: Action taken (escalate, dismiss, monitor, investigate)
            outcome: Optional outcome (true_positive, false_positive, etc)
        """
        if not self.assistant:
            await self.initialize_assistant()
        
        # Get threat context
        threat = await self.get_threat(threat_id)
        if not threat:
            return
        
        threat_context = {
            'severity': threat.severity,
            'threat_score': threat.threat_score,
            'analyst_count': threat.analyst_count,
            'escalation_count': threat.escalation_count
        }
        
        # Learn from action
        await self.assistant.learn_from_action(
            threat_id,
            analyst_id,
            action,
            threat_context,
            outcome
        )
    
    async def get_analyst_stats(self, analyst_id: str) -> Dict:
        """Get statistics about analyst's patterns"""
        if not self.assistant:
            await self.initialize_assistant()
        
        return await self.assistant.get_analyst_stats(analyst_id)
    
    async def get_team_stats(self) -> Dict:
        """Get team-wide statistics"""
        if not self.assistant:
            await self.initialize_assistant()
        
        return await self.assistant.get_team_stats()
