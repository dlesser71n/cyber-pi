"""Analyst Flow Tracker - Track investigation patterns in real-time

Tracks every action analysts take to learn preferences and predict future needs.
Uses Redis Streams for high-performance real-time tracking.
"""

from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import redis.asyncio as redis
import json


class ActionType(Enum):
    """Types of analyst actions we track"""
    VIEW_THREAT = "view_threat"
    SEARCH = "search"
    ESCALATE = "escalate"
    DISMISS = "dismiss"
    DOWNLOAD_REPORT = "download_report"
    INVESTIGATE_IOC = "investigate_ioc"
    CHECK_VENDOR = "check_vendor"
    VIEW_ENRICHMENT = "view_enrichment"


@dataclass
class FlowAction:
    """Represents a single analyst action"""
    analyst_id: str
    action_type: ActionType
    timestamp: str
    threat_id: Optional[str] = None
    industry: Optional[str] = None
    severity: Optional[str] = None
    search_query: Optional[str] = None
    time_spent_seconds: Optional[int] = None
    metadata: Optional[Dict] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for Redis storage"""
        data = asdict(self)
        data['action_type'] = self.action_type.value
        return {k: str(v) if v is not None else '' for k, v in data.items()}


class AnalystFlowTracker:
    """
    Track analyst investigation patterns using Redis Streams
    
    Features:
    - Real-time action tracking (<1ms latency)
    - Pattern analysis for personalization
    - Historical replay of investigations
    - Integration with predictive engine
    """
    
    def __init__(self, redis_url: str = "redis://localhost:32379"):
        """Initialize tracker with Redis connection (NodePort 32379)"""
        self.redis_url = redis_url
        self._redis_client: Optional[redis.Redis] = None
        self.max_stream_length = 10000  # Keep last 10k actions per analyst
    
    async def connect(self):
        """Establish Redis connection"""
        if not self._redis_client:
            self._redis_client = await redis.from_url(
                self.redis_url,
                decode_responses=True
            )
    
    async def disconnect(self):
        """Close Redis connection"""
        if self._redis_client:
            await self._redis_client.aclose()  # Use aclose() instead of deprecated close()
            self._redis_client = None
    
    async def track_action(
        self, 
        analyst_id: str,
        action_type: ActionType,
        threat_id: Optional[str] = None,
        industry: Optional[str] = None,
        severity: Optional[str] = None,
        search_query: Optional[str] = None,
        time_spent_seconds: Optional[int] = None,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Track a single analyst action
        
        Args:
            analyst_id: Unique analyst identifier
            action_type: Type of action performed
            threat_id: Associated threat ID (if applicable)
            industry: Industry context
            severity: Threat severity
            search_query: Search query text (for searches)
            time_spent_seconds: Time spent on action
            metadata: Additional context
            
        Returns:
            Action ID (Redis stream message ID)
            
        Example:
            >>> tracker = AnalystFlowTracker()
            >>> await tracker.connect()
            >>> action_id = await tracker.track_action(
            ...     analyst_id="analyst_123",
            ...     action_type=ActionType.VIEW_THREAT,
            ...     threat_id="threat_abc",
            ...     industry="aviation",
            ...     severity="CRITICAL",
            ...     time_spent_seconds=45
            ... )
        """
        await self.connect()
        
        action = FlowAction(
            analyst_id=analyst_id,
            action_type=action_type,
            timestamp=datetime.utcnow().isoformat(),
            threat_id=threat_id,
            industry=industry,
            severity=severity,
            search_query=search_query,
            time_spent_seconds=time_spent_seconds,
            metadata=metadata
        )
        
        stream_key = f"analyst_flow:{analyst_id}"
        action_data = action.to_dict()
        
        # Add to Redis Stream with automatic trimming
        action_id = await self._redis_client.xadd(
            stream_key,
            action_data,
            maxlen=self.max_stream_length,
            approximate=True  # More efficient trimming
        )
        
        return action_id
    
    async def get_recent_actions(
        self, 
        analyst_id: str, 
        count: int = 50
    ) -> List[Dict]:
        """
        Get analyst's recent actions
        
        Args:
            analyst_id: Analyst identifier
            count: Number of recent actions to retrieve
            
        Returns:
            List of actions (newest first)
        """
        await self.connect()
        
        stream_key = f"analyst_flow:{analyst_id}"
        
        # Get most recent actions (XREVRANGE returns newest first)
        actions = await self._redis_client.xrevrange(
            stream_key,
            count=count
        )
        
        return [
            {
                'id': action_id,
                'timestamp': action_data.get('timestamp'),
                'action_type': action_data.get('action_type'),
                'threat_id': action_data.get('threat_id') or None,
                'industry': action_data.get('industry') or None,
                'severity': action_data.get('severity') or None,
                'search_query': action_data.get('search_query') or None,
                'time_spent': int(action_data.get('time_spent_seconds', 0)) if action_data.get('time_spent_seconds') else None
            }
            for action_id, action_data in actions
        ]
    
    async def get_actions_by_timeframe(
        self,
        analyst_id: str,
        start_timestamp: str,
        end_timestamp: str = '+'
    ) -> List[Dict]:
        """
        Get actions within a timeframe
        
        Args:
            analyst_id: Analyst identifier
            start_timestamp: Start time (Redis stream ID or '-')
            end_timestamp: End time (Redis stream ID or '+')
            
        Returns:
            Actions in timeframe
        """
        await self.connect()
        
        stream_key = f"analyst_flow:{analyst_id}"
        
        actions = await self._redis_client.xrange(
            stream_key,
            min=start_timestamp,
            max=end_timestamp
        )
        
        return [
            {'id': action_id, **action_data}
            for action_id, action_data in actions
        ]
    
    async def count_actions(
        self,
        analyst_id: str,
        action_type: Optional[ActionType] = None
    ) -> int:
        """
        Count total actions (optionally filtered by type)
        
        Args:
            analyst_id: Analyst identifier
            action_type: Filter by specific action type
            
        Returns:
            Action count
        """
        await self.connect()
        
        stream_key = f"analyst_flow:{analyst_id}"
        
        # Get stream length
        info = await self._redis_client.xinfo_stream(stream_key)
        total_length = info['length']
        
        if not action_type:
            return total_length
        
        # If filtering by type, need to read and count
        # For large streams, this could be optimized with sampling
        actions = await self.get_recent_actions(analyst_id, count=1000)
        return sum(1 for a in actions if a['action_type'] == action_type.value)
    
    async def get_action_summary(self, analyst_id: str) -> Dict:
        """
        Get quick summary of analyst activity
        
        Args:
            analyst_id: Analyst identifier
            
        Returns:
            Summary statistics
        """
        actions = await self.get_recent_actions(analyst_id, count=500)
        
        if not actions:
            return {
                'total_actions': 0,
                'action_types': {},
                'industries': {},
                'avg_time_per_action': 0
            }
        
        action_types = {}
        industries = {}
        time_spent = []
        
        for action in actions:
            # Count action types
            action_type = action.get('action_type')
            if action_type:
                action_types[action_type] = action_types.get(action_type, 0) + 1
            
            # Count industries
            industry = action.get('industry')
            if industry:
                industries[industry] = industries.get(industry, 0) + 1
            
            # Collect time spent
            if action.get('time_spent'):
                time_spent.append(action['time_spent'])
        
        return {
            'total_actions': len(actions),
            'action_types': action_types,
            'industries': industries,
            'avg_time_per_action': sum(time_spent) / len(time_spent) if time_spent else 0,
            'most_common_action': max(action_types.items(), key=lambda x: x[1])[0] if action_types else None,
            'most_viewed_industry': max(industries.items(), key=lambda x: x[1])[0] if industries else None
        }
    
    async def clear_analyst_history(self, analyst_id: str):
        """
        Clear an analyst's action history (GDPR compliance, testing)
        
        Args:
            analyst_id: Analyst identifier
        """
        await self.connect()
        
        stream_key = f"analyst_flow:{analyst_id}"
        await self._redis_client.delete(stream_key)


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def demo():
        """Demonstration of flow tracking"""
        tracker = AnalystFlowTracker()
        
        try:
            # Track some actions
            await tracker.track_action(
                analyst_id="analyst_demo",
                action_type=ActionType.SEARCH,
                search_query="aviation ransomware",
                industry="aviation"
            )
            
            await tracker.track_action(
                analyst_id="analyst_demo",
                action_type=ActionType.VIEW_THREAT,
                threat_id="threat_123",
                industry="aviation",
                severity="CRITICAL",
                time_spent_seconds=45
            )
            
            await tracker.track_action(
                analyst_id="analyst_demo",
                action_type=ActionType.ESCALATE,
                threat_id="threat_123",
                industry="aviation"
            )
            
            # Get recent actions
            recent = await tracker.get_recent_actions("analyst_demo", count=10)
            print(f"Recent actions: {len(recent)}")
            for action in recent:
                print(f"  - {action['action_type']} at {action['timestamp']}")
            
            # Get summary
            summary = await tracker.get_action_summary("analyst_demo")
            print(f"\nSummary: {json.dumps(summary, indent=2)}")
            
        finally:
            await tracker.disconnect()
    
    asyncio.run(demo())
