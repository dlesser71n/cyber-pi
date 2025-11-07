#!/usr/bin/env python3
"""
Cyber Periscope - Analyst Assistant
Real-time AI assistant that learns from analyst behavior and provides intelligent recommendations

NOT a copilot (automation) - IS an assistant (human-in-the-loop)
Rickover principle: Human always in control, machine provides intelligence
"""

import json
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import defaultdict


@dataclass
class AssistanceRecommendation:
    """Recommendation from the Analyst Assistant"""
    suggested_action: str
    confidence: float
    reasoning: List[str]
    supporting_evidence: List[Dict]
    alternative_actions: List[Tuple[str, float]]
    analyst_context: Dict
    team_context: Dict
    
    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class AnalystPattern:
    """Pattern learned from analyst behavior"""
    analyst_id: str
    threat_type: str
    severity: str
    typical_action: str
    action_count: int
    success_rate: float
    avg_response_time: float
    last_seen: str


class AnalystAssistant:
    """
    Real-time AI assistant that learns from analyst behavior
    
    Learns from:
    - Individual analyst patterns (what YOU typically do)
    - Team collective wisdom (what the TEAM typically does)
    - Historical outcomes (what WORKED in the past)
    - Threat characteristics (what's SIMILAR to this)
    
    Provides:
    - Suggested action with confidence
    - Reasoning based on evidence
    - Alternative actions with probabilities
    - Supporting evidence from history
    """
    
    def __init__(self, redis_client):
        self.redis = redis_client
        
    # ========================================================================
    # CORE ASSISTANCE
    # ========================================================================
    
    async def assist_analyst(
        self,
        threat_id: str,
        analyst_id: str,
        threat_context: Dict
    ) -> AssistanceRecommendation:
        """
        Provide intelligent assistance for threat triage
        
        Args:
            threat_id: Threat being analyzed
            analyst_id: Analyst requesting assistance
            threat_context: Current threat details (severity, type, score, etc)
        
        Returns:
            AssistanceRecommendation with suggested action and reasoning
        """
        # Gather intelligence from multiple sources
        analyst_patterns = await self._get_analyst_patterns(analyst_id, threat_context)
        team_patterns = await self._get_team_patterns(threat_context)
        historical_outcomes = await self._get_historical_outcomes(threat_context)
        similar_threats = await self._find_similar_threats(threat_id, threat_context)
        
        # Calculate recommendation
        recommendation = await self._calculate_recommendation(
            analyst_patterns,
            team_patterns,
            historical_outcomes,
            similar_threats,
            threat_context
        )
        
        return recommendation
    
    # ========================================================================
    # PATTERN LEARNING
    # ========================================================================
    
    async def learn_from_action(
        self,
        threat_id: str,
        analyst_id: str,
        action: str,
        threat_context: Dict,
        outcome: Optional[str] = None
    ):
        """
        Learn from analyst action for future recommendations
        
        Args:
            threat_id: Threat that was acted upon
            analyst_id: Analyst who took action
            action: Action taken (escalate, dismiss, monitor, etc)
            threat_context: Threat details at time of action
            outcome: Optional outcome (true_positive, false_positive, etc)
        """
        timestamp = datetime.utcnow().isoformat()
        
        # Store individual analyst pattern
        pattern_key = f"assistant:analyst:{analyst_id}:{threat_context['severity']}:{action}"
        await self.redis.hincrby(pattern_key, "count", 1)
        await self.redis.hset(pattern_key, "last_seen", timestamp)
        
        # Store team pattern
        team_key = f"assistant:team:{threat_context['severity']}:{action}"
        await self.redis.hincrby(team_key, "count", 1)
        
        # Store action history
        action_record = {
            'threat_id': threat_id,
            'analyst_id': analyst_id,
            'action': action,
            'severity': threat_context['severity'],
            'threat_score': threat_context.get('threat_score', 0.5),
            'timestamp': timestamp,
            'outcome': outcome
        }
        
        await self.redis.zadd(
            f"assistant:history:{analyst_id}",
            {json.dumps(action_record): datetime.utcnow().timestamp()}
        )
        
        # Keep only last 1000 actions per analyst
        await self.redis.zremrangebyrank(f"assistant:history:{analyst_id}", 0, -1001)
        
        # If outcome provided, update success rate
        if outcome:
            await self._update_success_rate(analyst_id, action, threat_context, outcome)
    
    async def _update_success_rate(
        self,
        analyst_id: str,
        action: str,
        threat_context: Dict,
        outcome: str
    ):
        """Update success rate for action type"""
        pattern_key = f"assistant:analyst:{analyst_id}:{threat_context['severity']}:{action}"
        
        # Track successes
        if outcome in ['true_positive', 'incident_prevented', 'correct_escalation']:
            await self.redis.hincrby(pattern_key, "successes", 1)
        
        # Calculate success rate
        count = int(await self.redis.hget(pattern_key, "count") or 0)
        successes = int(await self.redis.hget(pattern_key, "successes") or 0)
        
        if count > 0:
            success_rate = successes / count
            await self.redis.hset(pattern_key, "success_rate", success_rate)
    
    # ========================================================================
    # INTELLIGENCE GATHERING
    # ========================================================================
    
    async def _get_analyst_patterns(
        self,
        analyst_id: str,
        threat_context: Dict
    ) -> Dict[str, int]:
        """Get this analyst's typical actions for this threat type"""
        severity = threat_context['severity']
        patterns = {}
        
        # Get counts for each action type
        for action in ['escalate', 'dismiss', 'monitor', 'investigate']:
            key = f"assistant:analyst:{analyst_id}:{severity}:{action}"
            count = await self.redis.hget(key, "count")
            if count:
                patterns[action] = int(count)
        
        return patterns
    
    async def _get_team_patterns(self, threat_context: Dict) -> Dict[str, int]:
        """Get team's typical actions for this threat type"""
        severity = threat_context['severity']
        patterns = {}
        
        for action in ['escalate', 'dismiss', 'monitor', 'investigate']:
            key = f"assistant:team:{severity}:{action}"
            count = await self.redis.hget(key, "count")
            if count:
                patterns[action] = int(count)
        
        return patterns
    
    async def _get_historical_outcomes(self, threat_context: Dict) -> Dict:
        """Get historical outcomes for similar threats"""
        # Query recent history for similar severity/score
        # This would integrate with TQAKB for deep historical search
        return {
            'total_similar': 0,
            'escalated': 0,
            'dismissed': 0,
            'true_positives': 0,
            'false_positives': 0
        }
    
    async def _find_similar_threats(
        self,
        threat_id: str,
        threat_context: Dict
    ) -> List[Dict]:
        """Find similar threats from history"""
        # This would integrate with Periscope to find similar threats
        # For now, return empty list
        return []
    
    # ========================================================================
    # RECOMMENDATION CALCULATION
    # ========================================================================
    
    async def _calculate_recommendation(
        self,
        analyst_patterns: Dict[str, int],
        team_patterns: Dict[str, int],
        historical_outcomes: Dict,
        similar_threats: List[Dict],
        threat_context: Dict
    ) -> AssistanceRecommendation:
        """
        Calculate recommendation based on all intelligence
        
        Weighting:
        - Analyst patterns: 40% (what YOU typically do)
        - Team patterns: 30% (what TEAM typically does)
        - Historical outcomes: 20% (what WORKED)
        - Threat characteristics: 10% (what's SIMILAR)
        """
        # Calculate action scores
        action_scores = defaultdict(float)
        reasoning = []
        
        # Weight 1: Analyst's own patterns (40%)
        if analyst_patterns:
            total_analyst_actions = sum(analyst_patterns.values())
            for action, count in analyst_patterns.items():
                weight = (count / total_analyst_actions) * 0.4
                action_scores[action] += weight
                
                if count >= 3:  # Only mention if significant
                    reasoning.append(
                        f"You've taken '{action}' action {count} times for {threat_context['severity']} threats"
                    )
        
        # Weight 2: Team patterns (30%)
        if team_patterns:
            total_team_actions = sum(team_patterns.values())
            for action, count in team_patterns.items():
                weight = (count / total_team_actions) * 0.3
                action_scores[action] += weight
                
                if count >= 10:  # Only mention if significant
                    pct = int((count / total_team_actions) * 100)
                    reasoning.append(
                        f"Team takes '{action}' action {pct}% of the time for {threat_context['severity']} threats"
                    )
        
        # Weight 3: Threat score influence (10%)
        threat_score = threat_context.get('threat_score', 0.5)
        if threat_score > 0.7:
            action_scores['escalate'] += 0.1
            reasoning.append(f"High threat score ({threat_score:.2f}) suggests escalation")
        elif threat_score < 0.3:
            action_scores['dismiss'] += 0.1
            reasoning.append(f"Low threat score ({threat_score:.2f}) suggests dismissal")
        
        # Weight 4: Severity influence (10%)
        severity = threat_context['severity']
        if severity == 'CRITICAL':
            action_scores['escalate'] += 0.1
            reasoning.append("CRITICAL severity requires immediate attention")
        elif severity == 'LOW':
            action_scores['monitor'] += 0.05
            action_scores['dismiss'] += 0.05
        
        # Get top recommendation
        if action_scores:
            sorted_actions = sorted(action_scores.items(), key=lambda x: x[1], reverse=True)
            suggested_action = sorted_actions[0][0]
            confidence = min(sorted_actions[0][1], 0.95)  # Cap at 95%
            
            # Get alternatives (top 3)
            alternatives = [
                (action, score) for action, score in sorted_actions[1:4]
            ]
        else:
            # No patterns yet - use defaults
            if severity == 'CRITICAL':
                suggested_action = 'escalate'
                confidence = 0.6
                reasoning.append("Default recommendation for CRITICAL threats")
            else:
                suggested_action = 'investigate'
                confidence = 0.5
                reasoning.append("No historical patterns available yet")
            
            alternatives = [
                ('monitor', 0.3),
                ('dismiss', 0.2)
            ]
        
        return AssistanceRecommendation(
            suggested_action=suggested_action,
            confidence=confidence,
            reasoning=reasoning,
            supporting_evidence=similar_threats,
            alternative_actions=alternatives,
            analyst_context={
                'patterns': analyst_patterns,
                'total_actions': sum(analyst_patterns.values()) if analyst_patterns else 0
            },
            team_context={
                'patterns': team_patterns,
                'total_actions': sum(team_patterns.values()) if team_patterns else 0
            }
        )
    
    # ========================================================================
    # ANALYTICS
    # ========================================================================
    
    async def get_analyst_stats(self, analyst_id: str) -> Dict:
        """Get statistics about analyst's patterns"""
        # Get recent action history
        history = await self.redis.zrevrange(
            f"assistant:history:{analyst_id}",
            0, 99,
            withscores=False
        )
        
        if not history:
            return {
                'total_actions': 0,
                'action_breakdown': {},
                'avg_confidence': 0.0
            }
        
        # Parse history
        actions = [json.loads(h) for h in history]
        
        # Calculate stats
        action_counts = defaultdict(int)
        for action in actions:
            action_counts[action['action']] += 1
        
        return {
            'total_actions': len(actions),
            'action_breakdown': dict(action_counts),
            'recent_actions': actions[:10]
        }
    
    async def get_team_stats(self) -> Dict:
        """Get team-wide statistics"""
        # Scan for all team pattern keys
        team_keys = []
        cursor = 0
        
        while True:
            cursor, keys = await self.redis.scan(
                cursor,
                match="assistant:team:*",
                count=100
            )
            team_keys.extend(keys)
            if cursor == 0:
                break
        
        # Aggregate team patterns
        total_actions = 0
        action_breakdown = defaultdict(int)
        
        for key in team_keys:
            count = await self.redis.hget(key, "count")
            if count:
                count = int(count)
                total_actions += count
                
                # Extract action from key
                parts = key.split(':')
                if len(parts) >= 4:
                    action = parts[3]
                    action_breakdown[action] += count
        
        return {
            'total_actions': total_actions,
            'action_breakdown': dict(action_breakdown),
            'unique_patterns': len(team_keys)
        }
