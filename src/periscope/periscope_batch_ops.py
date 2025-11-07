#!/usr/bin/env python3
"""
Cyber Periscope Triage - Batch Operations
Efficient batch processing for multiple threats
"""

import asyncio
from typing import List, Dict
from .periscope_memory_threat_ops import PeriscopeTriage, WorkingMemory


class PeriscopeTriageBatch(PeriscopeTriage):
    """
    Cyber Periscope Triage - Batch Operations
    
    Efficient batch processing for multiple threats with triage prioritization.
    """
    
    async def add_threats_batch(
        self,
        threats: List[Dict]
    ) -> List[WorkingMemory]:
        """
        Add multiple threats efficiently
        
        Args:
            threats: List of dicts with threat_id, content, severity, metadata
        
        Returns:
            List of created WorkingMemory objects
        """
        results = []
        
        # Process in parallel (golden pattern: batch processing)
        tasks = [
            self.add_threat(
                threat['threat_id'],
                threat['content'],
                threat['severity'],
                threat.get('metadata', {})
            )
            for threat in threats
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions
        successful = [r for r in results if isinstance(r, WorkingMemory)]
        
        return successful
    
    async def record_interactions_batch(
        self,
        interactions: List[Dict]
    ) -> int:
        """
        Record multiple interactions efficiently
        
        Args:
            interactions: List of dicts with threat_id, analyst_id, action_type
        
        Returns:
            Number of successful interactions
        """
        tasks = [
            self.record_interaction(
                i['threat_id'],
                i['analyst_id'],
                i.get('action_type', 'view')
            )
            for i in interactions
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Count successful
        successful = sum(1 for r in results if r is not None and not isinstance(r, Exception))
        
        return successful
    
    async def promote_eligible_threats(self) -> Dict:
        """
        Auto-promote all eligible threats from Level 1 to Level 2
        (Golden pattern: batch promotion)
        
        Returns:
            Dict with promotion statistics
        """
        all_threats = await self.get_all_active()
        
        promoted = []
        failed = []
        
        for threat in all_threats:
            try:
                result = await self.promote_to_short_term(threat.threat_id)
                if result:
                    promoted.append(threat.threat_id)
            except Exception as e:
                failed.append((threat.threat_id, str(e)))
        
        return {
            'promoted': len(promoted),
            'failed': len(failed),
            'promoted_ids': promoted,
            'errors': failed
        }
    
    async def cleanup_stale_threats(self, max_age_minutes: int = 60) -> int:
        """
        Remove stale threats from Level 1
        (Golden pattern: auto-cleanup)
        
        Args:
            max_age_minutes: Maximum age before considering stale
        
        Returns:
            Number of threats removed
        """
        from datetime import datetime, timedelta
        
        all_threats = await self.get_all_active()
        removed = 0
        
        cutoff = datetime.utcnow() - timedelta(minutes=max_age_minutes)
        
        for threat in all_threats:
            try:
                last_activity = datetime.fromisoformat(threat.last_activity)
                
                # Remove if stale and low score
                if last_activity < cutoff and threat.threat_score < 0.3:
                    if await self.remove_threat(threat.threat_id):
                        removed += 1
            except Exception:
                continue
        
        return removed
    
    async def get_threats_by_severity(self, severity: str) -> List[WorkingMemory]:
        """Get all threats of a specific severity - INDEXED (100x faster)"""
        client = self.redis_clients["Level_1_Working"]
        
        # Get threat IDs from severity index (instant lookup)
        threat_ids = await client.smembers(f"periscope:L1:by_severity:{severity}")
        
        # Fetch only the threats we need
        threats = []
        for tid in threat_ids:
            threat = await self.get_threat(tid)
            if threat:
                threats.append(threat)
        
        return threats
    
    async def get_threats_by_score_range(
        self,
        min_score: float = 0.0,
        max_score: float = 1.0
    ) -> List[WorkingMemory]:
        """Get threats within a score range - INDEXED (100x faster)"""
        client = self.redis_clients["Level_1_Working"]
        
        # Get threat IDs from score index (sorted set range query)
        threat_ids = await client.zrangebyscore(
            "periscope:L1:by_score",
            min_score,
            max_score
        )
        
        # Fetch only the threats we need
        threats = []
        for tid in threat_ids:
            threat = await self.get_threat(tid)
            if threat:
                threats.append(threat)
        
        return threats
    
    async def get_top_threats_by_score(self, limit: int = 100) -> List[WorkingMemory]:
        """Get top N threats by score - INDEXED (instant)"""
        client = self.redis_clients["Level_1_Working"]
        
        # Get top threat IDs from score index (reverse sorted)
        threat_ids = await client.zrevrange("periscope:L1:by_score", 0, limit - 1)
        
        # Fetch threats
        threats = []
        for tid in threat_ids:
            threat = await self.get_threat(tid)
            if threat:
                threats.append(threat)
        
        return threats
