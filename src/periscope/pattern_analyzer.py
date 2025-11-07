"""Pattern Analyzer - Analyze analyst behavior to understand preferences

Analyzes flow data to identify:
- Industry preferences
- Severity focus
- Investigation patterns
- Escalation tendencies
- Time allocation
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import Counter
import redis.asyncio as redis
from .flow_tracker import AnalystFlowTracker, ActionType


class PatternAnalyzer:
    """
    Analyze analyst behavior patterns from flow data
    
    Provides insights for:
    - Personalized threat prioritization
    - Proactive alert generation
    - Workflow optimization
    - Team analytics
    """
    
    def __init__(
        self, 
        flow_tracker: AnalystFlowTracker,
        redis_url: str = "redis://localhost:32379"
    ):
        """Initialize pattern analyzer (NodePort 32379)"""
        self.flow_tracker = flow_tracker
        self.redis_url = redis_url
        self._redis_client: Optional[redis.Redis] = None
        self.pattern_cache_ttl = 3600  # Cache patterns for 1 hour
    
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
    
    async def analyze_patterns(
        self, 
        analyst_id: str,
        lookback_actions: int = 500,
        use_cache: bool = True
    ) -> Dict:
        """
        Comprehensive pattern analysis for an analyst
        
        Args:
            analyst_id: Analyst identifier
            lookback_actions: Number of recent actions to analyze
            use_cache: Whether to use cached patterns
            
        Returns:
            Dict with pattern insights
            
        Example output:
            {
                'most_viewed_industries': {'aviation': 45, 'healthcare': 23},
                'escalation_rate': 0.23,
                'avg_time_per_threat': 180,
                'preferred_severity_focus': {'CRITICAL': 67, 'HIGH': 45},
                'common_search_terms': ['ransomware', 'phishing', 'APT'],
                'investigation_velocity': 'high',  # high/medium/low
                'specialization_score': 0.78,  # 0-1, higher = more specialized
                'active_hours': [9, 10, 11, 14, 15, 16],
                'last_analyzed': '2025-11-03T18:29:00Z'
            }
        """
        await self.connect()
        
        # Check cache first
        if use_cache:
            cached = await self._get_cached_patterns(analyst_id)
            if cached:
                return cached
        
        # Get recent actions
        actions = await self.flow_tracker.get_recent_actions(
            analyst_id,
            count=lookback_actions
        )
        
        if not actions:
            return self._empty_pattern_result()
        
        # Analyze all dimensions
        patterns = {
            'most_viewed_industries': self._analyze_industry_focus(actions),
            'escalation_rate': self._calculate_escalation_rate(actions),
            'avg_time_per_threat': self._calculate_avg_time_per_threat(actions),
            'preferred_severity_focus': self._analyze_severity_preference(actions),
            'common_search_terms': self._extract_common_searches(actions),
            'investigation_velocity': self._assess_velocity(actions),
            'specialization_score': self._calculate_specialization(actions),
            'active_hours': self._identify_active_hours(actions),
            'action_distribution': self._analyze_action_distribution(actions),
            'threat_view_to_escalation_ratio': self._calculate_view_escalation_ratio(actions),
            'last_analyzed': datetime.utcnow().isoformat(),
            'sample_size': len(actions)
        }
        
        # Cache results
        await self._cache_patterns(analyst_id, patterns)
        
        return patterns
    
    def _analyze_industry_focus(self, actions: List[Dict]) -> Dict[str, int]:
        """Count actions per industry"""
        industries = [
            a.get('industry') for a in actions 
            if a.get('industry')
        ]
        
        if not industries:
            return {}
        
        counts = Counter(industries)
        return dict(counts.most_common(10))  # Top 10 industries
    
    def _calculate_escalation_rate(self, actions: List[Dict]) -> float:
        """Calculate percentage of threats that were escalated"""
        views = sum(1 for a in actions if a.get('action_type') == ActionType.VIEW_THREAT.value)
        escalations = sum(1 for a in actions if a.get('action_type') == ActionType.ESCALATE.value)
        
        return round(escalations / views * 100, 2) if views > 0 else 0.0
    
    def _calculate_avg_time_per_threat(self, actions: List[Dict]) -> int:
        """Average time spent investigating threats (seconds)"""
        times = [
            a.get('time_spent') 
            for a in actions 
            if a.get('time_spent') and a.get('action_type') == ActionType.VIEW_THREAT.value
        ]
        
        return int(sum(times) / len(times)) if times else 0
    
    def _analyze_severity_preference(self, actions: List[Dict]) -> Dict[str, int]:
        """Which severities does analyst focus on?"""
        severities = [
            a.get('severity') 
            for a in actions 
            if a.get('severity')
        ]
        
        if not severities:
            return {}
        
        counts = Counter(severities)
        return dict(counts.most_common())
    
    def _extract_common_searches(self, actions: List[Dict], top_n: int = 10) -> List[str]:
        """Extract most common search queries"""
        searches = [
            a.get('search_query') 
            for a in actions 
            if a.get('search_query') and a.get('action_type') == ActionType.SEARCH.value
        ]
        
        if not searches:
            return []
        
        # Get unique searches, sorted by frequency
        counts = Counter(searches)
        return [search for search, _ in counts.most_common(top_n)]
    
    def _assess_velocity(self, actions: List[Dict]) -> str:
        """Assess investigation speed: high/medium/low"""
        avg_time = self._calculate_avg_time_per_threat(actions)
        
        if avg_time == 0:
            return 'unknown'
        elif avg_time < 60:  # Less than 1 minute
            return 'high'
        elif avg_time < 180:  # 1-3 minutes
            return 'medium'
        else:
            return 'low'
    
    def _calculate_specialization(self, actions: List[Dict]) -> float:
        """
        Calculate specialization score (0-1)
        Higher = more specialized (focused on specific industries/types)
        Lower = more generalist
        """
        industries = self._analyze_industry_focus(actions)
        
        if not industries:
            return 0.0
        
        total_actions = sum(industries.values())
        
        # Calculate entropy (lower entropy = more specialized)
        if len(industries) == 1:
            return 1.0  # Completely specialized
        
        # Simple specialization: % of actions in top industry
        top_industry_count = max(industries.values())
        specialization = top_industry_count / total_actions
        
        return round(specialization, 2)
    
    def _identify_active_hours(self, actions: List[Dict]) -> List[int]:
        """Identify hours of day when analyst is most active (0-23)"""
        hours = []
        
        for action in actions:
            timestamp_str = action.get('timestamp')
            if timestamp_str:
                try:
                    dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    hours.append(dt.hour)
                except (ValueError, AttributeError):
                    continue
        
        if not hours:
            return []
        
        # Get hours with significant activity (>5% of total)
        hour_counts = Counter(hours)
        threshold = len(hours) * 0.05
        active_hours = [
            hour for hour, count in hour_counts.items()
            if count >= threshold
        ]
        
        return sorted(active_hours)
    
    def _analyze_action_distribution(self, actions: List[Dict]) -> Dict[str, float]:
        """Distribution of action types as percentages"""
        action_types = [a.get('action_type') for a in actions if a.get('action_type')]
        
        if not action_types:
            return {}
        
        total = len(action_types)
        counts = Counter(action_types)
        
        return {
            action_type: round(count / total * 100, 2)
            for action_type, count in counts.items()
        }
    
    def _calculate_view_escalation_ratio(self, actions: List[Dict]) -> Optional[float]:
        """Ratio of views to escalations (higher = more selective)"""
        views = sum(1 for a in actions if a.get('action_type') == ActionType.VIEW_THREAT.value)
        escalations = sum(1 for a in actions if a.get('action_type') == ActionType.ESCALATE.value)
        
        if escalations == 0:
            return None
        
        return round(views / escalations, 2)
    
    def _empty_pattern_result(self) -> Dict:
        """Return empty pattern structure"""
        return {
            'most_viewed_industries': {},
            'escalation_rate': 0.0,
            'avg_time_per_threat': 0,
            'preferred_severity_focus': {},
            'common_search_terms': [],
            'investigation_velocity': 'unknown',
            'specialization_score': 0.0,
            'active_hours': [],
            'action_distribution': {},
            'threat_view_to_escalation_ratio': None,
            'last_analyzed': datetime.utcnow().isoformat(),
            'sample_size': 0
        }
    
    async def _get_cached_patterns(self, analyst_id: str) -> Optional[Dict]:
        """Retrieve cached patterns from Redis"""
        cache_key = f"analyst_patterns:{analyst_id}"
        
        try:
            cached_data = await self._redis_client.hgetall(cache_key)
            if cached_data:
                # Convert string values back to appropriate types
                return self._deserialize_patterns(cached_data)
        except Exception:
            pass
        
        return None
    
    async def _cache_patterns(self, analyst_id: str, patterns: Dict):
        """Cache patterns in Redis"""
        cache_key = f"analyst_patterns:{analyst_id}"
        
        # Serialize patterns for storage
        serialized = self._serialize_patterns(patterns)
        
        # Store in Redis with TTL
        await self._redis_client.hset(cache_key, mapping=serialized)
        await self._redis_client.expire(cache_key, self.pattern_cache_ttl)
    
    def _serialize_patterns(self, patterns: Dict) -> Dict[str, str]:
        """Convert patterns to string values for Redis storage"""
        import json
        serialized = {}
        
        for key, value in patterns.items():
            if isinstance(value, (dict, list)):
                serialized[key] = json.dumps(value)
            else:
                serialized[key] = str(value)
        
        return serialized
    
    def _deserialize_patterns(self, cached_data: Dict[str, str]) -> Dict:
        """Convert Redis cached data back to proper types"""
        import json
        patterns = {}
        
        for key, value in cached_data.items():
            # Try to parse as JSON first
            try:
                patterns[key] = json.loads(value)
            except (json.JSONDecodeError, TypeError):
                # Handle primitive types
                if value.replace('.', '').replace('-', '').isdigit():
                    patterns[key] = float(value) if '.' in value else int(value)
                else:
                    patterns[key] = value
        
        return patterns
    
    async def compare_analysts(
        self,
        analyst_id_1: str,
        analyst_id_2: str
    ) -> Dict:
        """
        Compare patterns between two analysts
        
        Useful for:
        - Finding similar analysts for recommendations
        - Team benchmarking
        - Training insights
        """
        patterns_1 = await self.analyze_patterns(analyst_id_1)
        patterns_2 = await self.analyze_patterns(analyst_id_2)
        
        # Calculate similarity metrics
        industry_overlap = self._calculate_industry_overlap(
            patterns_1['most_viewed_industries'],
            patterns_2['most_viewed_industries']
        )
        
        return {
            'analyst_1': analyst_id_1,
            'analyst_2': analyst_id_2,
            'industry_overlap': industry_overlap,
            'escalation_rate_diff': abs(
                patterns_1['escalation_rate'] - patterns_2['escalation_rate']
            ),
            'specialization_diff': abs(
                patterns_1['specialization_score'] - patterns_2['specialization_score']
            ),
            'velocity_match': patterns_1['investigation_velocity'] == patterns_2['investigation_velocity']
        }
    
    def _calculate_industry_overlap(self, industries_1: Dict, industries_2: Dict) -> float:
        """Calculate Jaccard similarity between industry sets"""
        set_1 = set(industries_1.keys())
        set_2 = set(industries_2.keys())
        
        if not set_1 or not set_2:
            return 0.0
        
        intersection = len(set_1 & set_2)
        union = len(set_1 | set_2)
        
        return round(intersection / union, 2) if union > 0 else 0.0


# Example usage
if __name__ == "__main__":
    import asyncio
    from .flow_tracker import AnalystFlowTracker, ActionType
    
    async def demo():
        """Demonstration of pattern analysis"""
        tracker = AnalystFlowTracker()
        analyzer = PatternAnalyzer(tracker)
        
        try:
            # Simulate some analyst activity
            analyst_id = "analyst_demo"
            
            # Simulate aviation-focused analyst
            for i in range(20):
                await tracker.track_action(
                    analyst_id=analyst_id,
                    action_type=ActionType.VIEW_THREAT,
                    industry="aviation",
                    severity="CRITICAL" if i % 3 == 0 else "HIGH",
                    time_spent_seconds=120 + (i * 10)
                )
                
                # Escalate some
                if i % 4 == 0:
                    await tracker.track_action(
                        analyst_id=analyst_id,
                        action_type=ActionType.ESCALATE,
                        industry="aviation"
                    )
            
            # Add some searches
            await tracker.track_action(
                analyst_id=analyst_id,
                action_type=ActionType.SEARCH,
                search_query="aviation ransomware",
                industry="aviation"
            )
            
            # Analyze patterns
            patterns = await analyzer.analyze_patterns(analyst_id)
            
            print("Analyst Patterns:")
            print(f"  Industries: {patterns['most_viewed_industries']}")
            print(f"  Escalation Rate: {patterns['escalation_rate']}%")
            print(f"  Avg Time: {patterns['avg_time_per_threat']}s")
            print(f"  Velocity: {patterns['investigation_velocity']}")
            print(f"  Specialization: {patterns['specialization_score']}")
            print(f"  Active Hours: {patterns['active_hours']}")
            
        finally:
            await tracker.disconnect()
            await analyzer.disconnect()
    
    asyncio.run(demo())
