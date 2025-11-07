#!/usr/bin/env python3
"""
Cyber-Pi + Periscope Triage Integration
Adds 3-level threat memory and analyst triage to cyber-pi intelligence platform
"""

import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime

from periscope.periscope_batch_ops import PeriscopeTriageBatch
from periscope.threat_models import WorkingMemory

logger = logging.getLogger(__name__)


class CyberPiPeriscopeIntegration:
    """
    Integrates Cyber Periscope Triage with cyber-pi threat intelligence
    
    Features:
    - Automatic threat ingestion from cyber-pi collectors
    - Multi-level memory (Working/Short-Term/Long-Term)
    - Analyst interaction tracking
    - Auto-promotion based on triage
    - Threat prioritization and scoring
    """
    
    def __init__(self, redis_host: str = "localhost", redis_port: int = 32379):
        """Initialize Periscope integration"""
        self.periscope = None
        self.redis_host = redis_host
        self.redis_port = redis_port
        self._initialized = False
        
        logger.info("🧠 Cyber Periscope Triage integration initialized")
    
    async def initialize(self):
        """Initialize async Periscope system"""
        if not self._initialized:
            self.periscope = PeriscopeTriageBatch(
                redis_host=self.redis_host,
                redis_port=self.redis_port
            )
            await self.periscope.initialize()
            self._initialized = True
            logger.info("✅ Periscope Triage ready")
    
    async def ingest_cyber_pi_threats(self, items: List[Dict]) -> Dict:
        """
        Ingest threats from cyber-pi collectors into Periscope
        
        Args:
            items: List of threat intelligence items from cyber-pi
        
        Returns:
            Dict with ingestion statistics
        """
        if not self._initialized:
            await self.initialize()
        
        logger.info(f"📥 Ingesting {len(items)} threats into Periscope...")
        
        # Convert cyber-pi items to Periscope threats
        periscope_threats = []
        for item in items:
            threat = self._convert_to_periscope_threat(item)
            if threat:
                periscope_threats.append(threat)
        
        # Batch add to Periscope
        added = await self.periscope.add_threats_batch(periscope_threats)
        
        stats = {
            'total_items': len(items),
            'converted': len(periscope_threats),
            'added': len(added),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        logger.info(f"✅ Added {len(added)} threats to Periscope")
        return stats
    
    async def record_analyst_triage(
        self,
        threat_id: str,
        analyst_id: str,
        action: str = "view"
    ) -> Optional[WorkingMemory]:
        """
        Record analyst interaction with threat
        
        Args:
            threat_id: Threat identifier
            analyst_id: Analyst identifier
            action: 'view', 'escalate', or 'dismiss'
        
        Returns:
            Updated threat memory
        """
        if not self._initialized:
            await self.initialize()
        
        return await self.periscope.record_interaction(threat_id, analyst_id, action)
    
    async def get_priority_threats(
        self,
        min_score: float = 0.7,
        limit: int = 10
    ) -> List[WorkingMemory]:
        """
        Get high-priority threats for analyst review
        
        Args:
            min_score: Minimum threat score
            limit: Maximum number of threats
        
        Returns:
            List of high-priority threats
        """
        if not self._initialized:
            await self.initialize()
        
        # Get threats by score range
        threats = await self.periscope.get_threats_by_score_range(min_score=min_score)
        
        # Sort by score and limit
        threats.sort(key=lambda t: t.threat_score, reverse=True)
        return threats[:limit]
    
    async def get_hot_threats(self, min_interactions: int = 3) -> List[WorkingMemory]:
        """
        Get threats with high analyst attention
        
        Args:
            min_interactions: Minimum analyst interactions
        
        Returns:
            List of hot threats
        """
        if not self._initialized:
            await self.initialize()
        
        return await self.periscope.get_hot_threats(min_interactions=min_interactions)
    
    async def auto_promote_validated(self) -> Dict:
        """
        Auto-promote threats that meet validation criteria
        
        Returns:
            Dict with promotion statistics
        """
        if not self._initialized:
            await self.initialize()
        
        logger.info("⬆️  Auto-promoting validated threats...")
        
        stats = await self.periscope.promote_eligible_threats()
        
        logger.info(f"✅ Promoted {stats['promoted']} threats to Level 2")
        return stats
    
    async def get_triage_dashboard(self) -> Dict:
        """
        Get comprehensive triage dashboard data
        
        Returns:
            Dict with dashboard statistics
        """
        if not self._initialized:
            await self.initialize()
        
        # Get system stats
        stats = await self.periscope.get_stats()
        
        # Get priority threats
        priority = await self.get_priority_threats(min_score=0.7, limit=5)
        hot = await self.get_hot_threats(min_interactions=2)
        
        # Get threats by severity
        critical = await self.periscope.get_threats_by_severity("CRITICAL")
        high = await self.periscope.get_threats_by_severity("HIGH")
        
        dashboard = {
            'system_stats': stats,
            'priority_threats': [
                {
                    'id': t.threat_id,
                    'content': t.content[:100],
                    'severity': t.severity,
                    'score': t.threat_score,
                    'interactions': t.interaction_count
                }
                for t in priority
            ],
            'hot_threats': [
                {
                    'id': t.threat_id,
                    'content': t.content[:100],
                    'interactions': t.interaction_count,
                    'escalations': t.escalation_count
                }
                for t in hot
            ],
            'severity_breakdown': {
                'critical': len(critical),
                'high': len(high)
            },
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return dashboard
    
    def _convert_to_periscope_threat(self, item: Dict) -> Optional[Dict]:
        """
        Convert cyber-pi intelligence item to Periscope threat format
        
        Args:
            item: cyber-pi intelligence item
        
        Returns:
            Periscope threat dict or None
        """
        try:
            # Extract threat ID (use source + title hash)
            threat_id = self._generate_threat_id(item)
            
            # Extract content
            content = item.get('title', '') or item.get('description', '')
            if not content:
                return None
            
            # Determine severity from cyber-pi data
            severity = self._determine_severity(item)
            
            # Build metadata
            metadata = {
                'source': item.get('source', 'unknown'),
                'url': item.get('url', ''),
                'published': item.get('published', ''),
                'industry': item.get('industry', []),
                'tags': item.get('tags', []),
                'original_item': item
            }
            
            return {
                'threat_id': threat_id,
                'content': content,
                'severity': severity,
                'metadata': metadata
            }
            
        except Exception as e:
            logger.warning(f"Failed to convert item: {e}")
            return None
    
    def _generate_threat_id(self, item: Dict) -> str:
        """Generate unique threat ID from item"""
        import hashlib
        
        # Use source + title for uniqueness
        source = item.get('source', 'unknown')
        title = item.get('title', item.get('description', ''))
        
        # Create hash
        content = f"{source}:{title}"
        hash_obj = hashlib.md5(content.encode())
        
        return f"threat_{hash_obj.hexdigest()[:12]}"
    
    def _determine_severity(self, item: Dict) -> str:
        """
        Determine threat severity from cyber-pi item
        
        Logic:
        - CRITICAL: Exploits, 0-days, active campaigns
        - HIGH: Vulnerabilities, malware, breaches
        - MEDIUM: Advisories, patches, warnings
        - LOW: General news, updates
        """
        title = (item.get('title', '') + ' ' + item.get('description', '')).lower()
        tags = [t.lower() for t in item.get('tags', [])]
        
        # CRITICAL indicators
        critical_keywords = ['0-day', 'zero-day', 'exploit', 'ransomware', 'breach', 'compromise']
        if any(kw in title for kw in critical_keywords):
            return 'CRITICAL'
        
        if 'critical' in tags or 'exploit' in tags:
            return 'CRITICAL'
        
        # HIGH indicators
        high_keywords = ['vulnerability', 'malware', 'attack', 'threat', 'cve-']
        if any(kw in title for kw in high_keywords):
            return 'HIGH'
        
        if 'high' in tags or 'vulnerability' in tags:
            return 'HIGH'
        
        # MEDIUM indicators
        medium_keywords = ['advisory', 'patch', 'update', 'warning']
        if any(kw in title for kw in medium_keywords):
            return 'MEDIUM'
        
        # Default to LOW
        return 'LOW'
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.periscope and self._initialized:
            for client in self.periscope.redis_clients.values():
                await client.close()
            logger.info("✅ Periscope cleanup complete")


# Convenience function for sync usage
def create_periscope_integration(redis_host: str = "localhost", redis_port: int = 32379):
    """Create and return Periscope integration instance"""
    return CyberPiPeriscopeIntegration(redis_host=redis_host, redis_port=redis_port)
