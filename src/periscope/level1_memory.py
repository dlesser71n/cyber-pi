"""
Level 1 Memory System - Working Memory Only

FOCUS: Master the basics first
- Active threats being analyzed RIGHT NOW
- Real-time analyst interactions
- Fast Redis operations
- Simple, bulletproof architecture

Philosophy: Get Level 1 perfect before adding Level 2 and 3
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

import redis.asyncio as redis


@dataclass
class WorkingMemory:
    """Level 1: Active threat being analyzed RIGHT NOW"""
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


class Level1Memory:
    """
    Level 1: Working Memory System
    
    Simple Redis architecture:
    - cascade:working:{threat_id} - Hash (the memory itself)
    - cascade:working:active - Set (list of active threat IDs)
    
    That's it. No complexity. Master this first.
    """
    
    def __init__(self, redis_url: str = "redis://localhost:32379"):
        self.redis_url = redis_url
        self._redis_client: Optional[redis.Redis] = None
        
        # Configuration
        self.working_ttl = 3600  # 1 hour - then it expires
    
    async def connect(self):
        """Connect to Redis"""
        if not self._redis_client:
            self._redis_client = await redis.from_url(
                self.redis_url,
                decode_responses=True
            )
    
    async def disconnect(self):
        """Close Redis connection"""
        if self._redis_client:
            await self._redis_client.close()
            self._redis_client = None
    
    # ========================================================================
    # CORE OPERATIONS - Keep it simple
    # ========================================================================
    
    async def add_threat(
        self,
        threat_id: str,
        content: str,
        severity: str,
        metadata: Dict = None
    ) -> WorkingMemory:
        """
        Add threat to working memory
        
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
        
        # Store in Redis Hash
        key = f"cascade:working:{threat_id}"
        await self._redis_client.hset(
            key,
            mapping={k: json.dumps(v) if isinstance(v, dict) else str(v)
                    for k, v in working.to_dict().items()}
        )
        
        # Set TTL - auto-expires in 1 hour
        await self._redis_client.expire(key, self.working_ttl)
        
        # Add to active set
        await self._redis_client.sadd("cascade:working:active", threat_id)
        
        return working
    
    async def record_interaction(
        self,
        threat_id: str,
        analyst_id: str = None,
        action_type: str = None
    ) -> Optional[WorkingMemory]:
        """
        Record analyst interaction with threat
        
        Tracks who's looking at what RIGHT NOW.
        """
        await self.connect()
        
        key = f"cascade:working:{threat_id}"
        
        # Check if exists
        exists = await self._redis_client.exists(key)
        if not exists:
            return None
        
        # Increment interaction counter
        await self._redis_client.hincrby(key, "interaction_count", 1)
        
        # Increment analyst counter if new analyst
        if analyst_id:
            await self._redis_client.hincrby(key, "analyst_count", 1)
        
        # Update last activity timestamp
        await self._redis_client.hset(
            key, 
            "last_activity", 
            datetime.utcnow().isoformat()
        )
        
        # Refresh TTL - keep it alive while active
        await self._redis_client.expire(key, self.working_ttl)
        
        # Get updated memory
        return await self.get_threat(threat_id)
    
    async def get_threat(self, threat_id: str) -> Optional[WorkingMemory]:
        """Get working memory for specific threat"""
        await self.connect()
        
        key = f"cascade:working:{threat_id}"
        data = await self._redis_client.hgetall(key)
        
        if not data:
            return None
        
        # Deserialize
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
    
    async def get_all_active(self) -> List[str]:
        """Get list of all active threat IDs"""
        await self.connect()
        
        threat_ids = await self._redis_client.smembers("cascade:working:active")
        return list(threat_ids)
    
    async def get_all_threats(self) -> List[WorkingMemory]:
        """Get all active threats with full details"""
        await self.connect()
        
        threat_ids = await self.get_all_active()
        
        threats = []
        for threat_id in threat_ids:
            threat = await self.get_threat(threat_id)
            if threat:
                threats.append(threat)
        
        return threats
    
    async def remove_threat(self, threat_id: str) -> bool:
        """
        Remove threat from working memory
        
        Use when:
        - Threat resolved
        - False positive
        - Moving to next level (later)
        """
        await self.connect()
        
        key = f"cascade:working:{threat_id}"
        
        # Delete the hash
        deleted = await self._redis_client.delete(key)
        
        # Remove from active set
        await self._redis_client.srem("cascade:working:active", threat_id)
        
        return deleted > 0
    
    async def count_active(self) -> int:
        """Count how many threats are active"""
        await self.connect()
        return await self._redis_client.scard("cascade:working:active")
    
    async def clear_all(self):
        """
        Clear all working memory (for testing/reset)
        
        WARNING: This deletes everything!
        """
        await self.connect()
        
        # Get all active threats
        threat_ids = await self.get_all_active()
        
        # Delete each one
        for threat_id in threat_ids:
            await self.remove_threat(threat_id)
    
    # ========================================================================
    # INTUITION FEATURES - Simple pattern detection
    # ========================================================================
    
    async def get_hot_threats(self, min_interactions: int = 3) -> List[WorkingMemory]:
        """
        Get "hot" threats - lots of analyst attention
        
        This is intuition: if many analysts are looking, it's probably important.
        """
        await self.connect()
        
        all_threats = await self.get_all_threats()
        
        # Filter by interaction count
        hot_threats = [
            t for t in all_threats 
            if t.interaction_count >= min_interactions
        ]
        
        # Sort by interaction count (most active first)
        hot_threats.sort(key=lambda x: x.interaction_count, reverse=True)
        
        return hot_threats
    
    async def get_stale_threats(self, minutes: int = 30) -> List[WorkingMemory]:
        """
        Get "stale" threats - no recent activity
        
        Intuition: if nobody's looked at it in 30 minutes, maybe it's not important.
        """
        await self.connect()
        
        all_threats = await self.get_all_threats()
        
        cutoff = datetime.utcnow() - timedelta(minutes=minutes)
        
        stale_threats = []
        for threat in all_threats:
            last_activity = datetime.fromisoformat(threat.last_activity)
            if last_activity < cutoff:
                stale_threats.append(threat)
        
        return stale_threats
    
    async def get_stats(self) -> Dict:
        """Get simple statistics"""
        await self.connect()
        
        all_threats = await self.get_all_threats()
        
        if not all_threats:
            return {
                'total_active': 0,
                'total_interactions': 0,
                'avg_interactions': 0,
                'critical_count': 0,
                'high_count': 0
            }
        
        total_interactions = sum(t.interaction_count for t in all_threats)
        critical_count = sum(1 for t in all_threats if t.severity == 'CRITICAL')
        high_count = sum(1 for t in all_threats if t.severity == 'HIGH')
        
        return {
            'total_active': len(all_threats),
            'total_interactions': total_interactions,
            'avg_interactions': total_interactions / len(all_threats),
            'critical_count': critical_count,
            'high_count': high_count
        }


# Example usage and testing
if __name__ == "__main__":
    import asyncio
    
    async def demo():
        """Demonstrate Level 1 memory system"""
        print("🧠 Level 1 Memory System - Working Memory Only\n")
        
        memory = Level1Memory()
        
        try:
            # Clear any old data
            await memory.clear_all()
            
            # Add some threats
            print("📝 Adding threats to working memory...")
            
            threat1 = await memory.add_threat(
                threat_id="threat_001",
                content="Suspicious PowerShell activity on server-01",
                severity="HIGH",
                metadata={'source': 'EDR', 'host': 'server-01'}
            )
            print(f"   ✅ Added: {threat1.threat_id}")
            
            threat2 = await memory.add_threat(
                threat_id="threat_002",
                content="Multiple failed login attempts",
                severity="MEDIUM",
                metadata={'source': 'SIEM', 'user': 'admin'}
            )
            print(f"   ✅ Added: {threat2.threat_id}")
            
            threat3 = await memory.add_threat(
                threat_id="threat_003",
                content="Ransomware signature detected",
                severity="CRITICAL",
                metadata={'source': 'AV', 'file': 'malware.exe'}
            )
            print(f"   ✅ Added: {threat3.threat_id}")
            
            # Simulate analyst interactions
            print("\n👤 Simulating analyst activity...")
            await memory.record_interaction("threat_001", "analyst_1", "view")
            await memory.record_interaction("threat_001", "analyst_2", "view")
            await memory.record_interaction("threat_003", "analyst_1", "escalate")
            await memory.record_interaction("threat_003", "analyst_2", "escalate")
            await memory.record_interaction("threat_003", "analyst_3", "escalate")
            await memory.record_interaction("threat_003", "analyst_4", "escalate")
            print("   ✅ Recorded 6 interactions")
            
            # Get all active
            print("\n📊 Active threats:")
            active = await memory.get_all_threats()
            for threat in active:
                print(f"   - {threat.threat_id}: {threat.severity} ({threat.interaction_count} interactions)")
            
            # Get hot threats
            print("\n🔥 Hot threats (3+ interactions):")
            hot = await memory.get_hot_threats(min_interactions=3)
            for threat in hot:
                print(f"   - {threat.threat_id}: {threat.interaction_count} interactions")
            
            # Get statistics
            print("\n📈 Statistics:")
            stats = await memory.get_stats()
            for key, value in stats.items():
                print(f"   {key}: {value}")
            
            # Count active
            count = await memory.count_active()
            print(f"\n✅ Total active threats: {count}")
            
            print("\n🎯 Level 1 mastered! Ready for Level 2 when you are.")
            
        finally:
            await memory.disconnect()
    
    asyncio.run(demo())
