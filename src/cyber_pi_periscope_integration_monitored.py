#!/usr/bin/env python3
"""
Cyber-Pi + Periscope Integration with Production Monitoring
Includes comprehensive metrics, error tracking, and health monitoring
"""

import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime

from periscope.periscope_batch_ops import PeriscopeTriageBatch
from periscope.threat_models import WorkingMemory
from monitoring.periscope_monitor import PeriscopeMonitor, get_monitor

logger = logging.getLogger(__name__)


class MonitoredCyberPiPeriscopeIntegration:
    """
    Cyber-Pi + Periscope integration with production-grade monitoring
    
    Features:
    - Automatic threat ingestion with retry logic
    - Multi-level memory (Working/Short-Term/Long-Term)
    - Circuit breaker for fault tolerance
    - Dead letter queue for failed items
    - Real-time metrics collection
    - GPU and system resource monitoring
    - Health checks and alerts
    """
    
    def __init__(
        self,
        redis_host: str = "localhost",
        redis_port: int = 32379,
        enable_monitoring: bool = True
    ):
        """Initialize monitored integration"""
        self.periscope = None
        self.redis_host = redis_host
        self.redis_port = redis_port
        self._initialized = False
        
        # Initialize monitoring
        self.monitor: Optional[PeriscopeMonitor] = None
        if enable_monitoring:
            self.monitor = get_monitor()
        
        logger.info("🧠 Monitored Cyber-Pi Periscope integration initialized")
    
    async def initialize(self):
        """Initialize async components"""
        if not self._initialized:
            # Initialize Periscope
            self.periscope = PeriscopeTriageBatch(
                redis_host=self.redis_host,
                redis_port=self.redis_port
            )
            await self.periscope.initialize()
            
            # Initialize monitoring
            if self.monitor:
                await self.monitor.initialize()
            
            self._initialized = True
            logger.info("✅ Monitored Periscope integration ready")
    
    async def ingest_cyber_pi_threats(
        self,
        items: List[Dict],
        auto_retry: bool = True
    ) -> Dict:
        """
        Ingest threats with monitoring and retry logic
        
        Args:
            items: List of threat intelligence items
            auto_retry: Enable automatic retry on failure
        
        Returns:
            Dict with ingestion statistics and metrics
        """
        if not self._initialized:
            await self.initialize()
        
        logger.info(f"📥 Ingesting {len(items)} threats with monitoring...")
        
        if self.monitor and auto_retry:
            # Use monitored execution with retry
            return await self.monitor.execute_with_retry(
                self._ingest_threats_internal,
                items,
                operation_name="ingest_threats"
            )
        else:
            # Direct execution without monitoring
            return await self._ingest_threats_internal(items)
    
    async def _ingest_threats_internal(self, items: List[Dict]) -> Dict:
        """Internal threat ingestion logic"""
        # Convert cyber-pi items to Periscope threats
        periscope_threats = []
        conversion_failures = 0
        
        for item in items:
            try:
                threat = self._convert_to_periscope_threat(item)
                if threat:
                    periscope_threats.append(threat)
                    if self.monitor:
                        self.monitor.record_threat_converted()
                else:
                    if self.monitor:
                        self.monitor.record_threat_skipped("no_content")
            except Exception as e:
                conversion_failures += 1
                if self.monitor:
                    self.monitor.record_threat_failed(item, e)
                logger.warning(f"Failed to convert item: {e}")
        
        # Batch add to Periscope
        added = await self.periscope.add_threats_batch(periscope_threats)
        
        # Record successful ingestions
        if self.monitor:
            for _ in added:
                self.monitor.record_threat_ingested()
        
        stats = {
            'total_items': len(items),
            'converted': len(periscope_threats),
            'added': len(added),
            'conversion_failures': conversion_failures,
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
        """Record analyst interaction with monitoring"""
        if not self._initialized:
            await self.initialize()
        
        if self.monitor:
            return await self.monitor.execute_with_retry(
                self.periscope.record_interaction,
                threat_id,
                analyst_id,
                action,
                operation_name="record_triage"
            )
        else:
            return await self.periscope.record_interaction(threat_id, analyst_id, action)
    
    async def get_priority_threats(
        self,
        min_score: float = 0.7,
        limit: int = 10
    ) -> List[WorkingMemory]:
        """Get high-priority threats with monitoring"""
        if not self._initialized:
            await self.initialize()
        
        if self.monitor:
            return await self.monitor.execute_with_retry(
                self._get_priority_threats_internal,
                min_score,
                limit,
                operation_name="get_priority_threats"
            )
        else:
            return await self._get_priority_threats_internal(min_score, limit)
    
    async def _get_priority_threats_internal(
        self,
        min_score: float,
        limit: int
    ) -> List[WorkingMemory]:
        """Internal priority threats logic"""
        threats = await self.periscope.get_threats_by_score_range(min_score=min_score)
        threats.sort(key=lambda t: t.threat_score, reverse=True)
        return threats[:limit]
    
    async def get_hot_threats(
        self,
        min_interactions: int = 3
    ) -> List[WorkingMemory]:
        """Get hot threats with monitoring"""
        if not self._initialized:
            await self.initialize()
        
        if self.monitor:
            return await self.monitor.execute_with_retry(
                self.periscope.get_hot_threats,
                min_interactions=min_interactions,
                operation_name="get_hot_threats"
            )
        else:
            return await self.periscope.get_hot_threats(min_interactions=min_interactions)
    
    async def auto_promote_validated(self) -> Dict:
        """Auto-promote threats with monitoring"""
        if not self._initialized:
            await self.initialize()
        
        logger.info("⬆️  Auto-promoting validated threats...")
        
        if self.monitor:
            stats = await self.monitor.execute_with_retry(
                self.periscope.promote_eligible_threats,
                operation_name="auto_promote"
            )
        else:
            stats = await self.periscope.promote_eligible_threats()
        
        logger.info(f"✅ Promoted {stats['promoted']} threats to Level 2")
        return stats
    
    async def get_comprehensive_health(self) -> Dict:
        """
        Get comprehensive health status including:
        - Periscope metrics
        - System resources
        - GPU utilization
        - Circuit breaker status
        - Error statistics
        """
        if not self._initialized:
            await self.initialize()
        
        health = {}
        
        # Periscope stats
        if self.periscope:
            health['periscope'] = await self.periscope.get_stats()
        
        # Monitoring metrics
        if self.monitor:
            health['monitoring'] = self.monitor.get_health_status()
            health['system'] = self.monitor.get_system_stats()
            health['gpu'] = await self.monitor.get_gpu_stats()
            health['recent_errors'] = self.monitor.get_recent_errors(limit=10)
            health['dead_letter_queue_size'] = len(self.monitor.dead_letter_queue)
        
        health['timestamp'] = datetime.utcnow().isoformat()
        
        return health
    
    def print_metrics_report(self):
        """Print formatted metrics report to console"""
        if self.monitor:
            self.monitor.log_metrics()
        else:
            logger.info("Monitoring disabled - no metrics available")
    
    def _convert_to_periscope_threat(self, item: Dict) -> Optional[Dict]:
        """Convert cyber-pi intelligence item to Periscope threat format"""
        try:
            # Extract threat ID
            threat_id = self._generate_threat_id(item)
            
            # Extract content
            content = item.get('title', '') or item.get('description', '')
            if not content:
                return None
            
            # Determine severity
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
            raise
    
    def _generate_threat_id(self, item: Dict) -> str:
        """Generate unique threat ID from item"""
        import hashlib
        
        source = item.get('source', 'unknown')
        title = item.get('title', item.get('description', ''))
        
        content = f"{source}:{title}"
        hash_obj = hashlib.md5(content.encode())
        
        return f"threat_{hash_obj.hexdigest()[:12]}"
    
    def _determine_severity(self, item: Dict) -> str:
        """Determine threat severity from cyber-pi item"""
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
        
        return 'LOW'
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.periscope and self._initialized:
            for client in self.periscope.redis_clients.values():
                await client.close()
        
        if self.monitor and self.monitor._initialized:
            await self.monitor.redis.close()
        
        logger.info("✅ Cleanup complete")


# Example usage
async def main():
    """Example demonstrating monitored integration"""
    from rich.console import Console
    console = Console()
    
    console.print("\n" + "=" * 80, style="bold blue")
    console.print("🔭 MONITORED CYBER-PI + PERISCOPE INTEGRATION", style="bold blue")
    console.print("=" * 80 + "\n", style="bold blue")
    
    # Initialize integration with monitoring
    integration = MonitoredCyberPiPeriscopeIntegration(
        redis_host="localhost",
        redis_port=32379,
        enable_monitoring=True
    )
    
    await integration.initialize()
    
    # Example threat data
    test_threats = [
        {
            'source': 'test',
            'title': 'Critical Zero-Day Exploit in VMware',
            'description': 'Active exploitation detected',
            'tags': ['critical', 'exploit'],
            'url': 'https://example.com/vuln1'
        },
        {
            'source': 'test',
            'title': 'Ransomware Campaign Targeting Healthcare',
            'description': 'New variant detected',
            'tags': ['ransomware', 'healthcare'],
            'url': 'https://example.com/vuln2'
        }
    ]
    
    # Ingest threats with monitoring
    console.print("📥 Ingesting test threats...\n", style="cyan")
    stats = await integration.ingest_cyber_pi_threats(test_threats)
    
    console.print(f"\n✅ Ingestion complete:", style="green")
    console.print(f"   Total: {stats['total_items']}", style="green")
    console.print(f"   Converted: {stats['converted']}", style="green")
    console.print(f"   Added: {stats['added']}", style="green")
    
    # Get priority threats
    console.print("\n🎯 Fetching priority threats...\n", style="cyan")
    priority = await integration.get_priority_threats(min_score=0.7, limit=5)
    console.print(f"Found {len(priority)} priority threats", style="green")
    
    # Print metrics report
    integration.print_metrics_report()
    
    # Get comprehensive health
    console.print("\n🏥 System Health Check...\n", style="cyan")
    health = await integration.get_comprehensive_health()
    
    console.print(f"Status: {health.get('monitoring', {}).get('status', 'unknown')}", style="green")
    console.print(f"Circuit Breaker: {health.get('monitoring', {}).get('circuit_breaker', {}).get('state', 'unknown')}", style="green")
    
    if 'gpu' in health and 'gpus' in health['gpu']:
        console.print(f"\n🎮 GPU Status:", style="magenta")
        for gpu in health['gpu']['gpus']:
            console.print(f"   GPU {gpu['index']}: {gpu['utilization']}% | "
                         f"{gpu['memory_used_mb']}/{gpu['memory_total_mb']} MB | "
                         f"{gpu['temperature_c']}°C", style="magenta")
    
    # Cleanup
    await integration.cleanup()
    
    console.print("\n" + "=" * 80, style="bold blue")
    console.print("✅ DEMO COMPLETE", style="bold green")
    console.print("=" * 80 + "\n", style="bold blue")


if __name__ == "__main__":
    asyncio.run(main())
