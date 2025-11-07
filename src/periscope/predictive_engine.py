"""
Predictive Engine - Advanced Threat Prioritization

Multi-factor ensemble scoring system for predicting which threats
each analyst will care about.

Redis-First Architecture:
- Reads analyst patterns from Redis (Pattern Analyzer)
- Reads memories from Redis (Memory System)  
- Reads threat data from Redis (primary)
- Uses Neo4j for graph enrichment (secondary)

Industry Best Practices:
- Ensemble methods (4 independent scorers)
- Weighted averaging (40/30/20/10)
- Confidence intervals
- Explainable predictions
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import math

import redis.asyncio as redis
from neo4j import AsyncGraphDatabase

from .pattern_analyzer import PatternAnalyzer
from .memory_system import ThreatMemorySystem


@dataclass
class PredictionResult:
    """Result of threat priority prediction"""
    analyst_id: str
    threat_id: str
    predicted_priority: float  # 0.0-1.0
    confidence: float  # 0.0-1.0
    scores: Dict[str, float]  # Breakdown by scorer
    reasons: List[str]  # Human-readable explanations
    recommendation: str  # immediate_alert, priority_review, standard_queue
    timestamp: str


class AnalystAffinityScorer:
    """
    Score based on analyst behavior patterns
    
    Weight: 40% (most important)
    
    Factors:
    - Industry match (40% of scorer)
    - Historical escalation similarity (30% of scorer)
    - Specialization alignment (30% of scorer)
    """
    
    def __init__(self, pattern_analyzer: PatternAnalyzer):
        self.pattern_analyzer = pattern_analyzer
        
    async def score(self, analyst_id: str, threat_data: Dict) -> Tuple[float, List[str]]:
        """
        Calculate affinity score
        
        Returns:
            (score 0-1, list of reasons)
        """
        reasons = []
        
        # Get analyst patterns
        patterns = await self.pattern_analyzer.analyze_patterns(analyst_id, use_cache=True)
        
        if patterns['sample_size'] == 0:
            return (0.5, ["No analyst history (new analyst)"])
        
        # Factor 1: Industry Match (40%)
        industry_score = self._industry_match(patterns, threat_data, reasons)
        
        # Factor 2: Specialization Alignment (30%)
        specialization_score = self._specialization_match(patterns, threat_data, reasons)
        
        # Factor 3: Severity Preference (30%)
        severity_score = self._severity_preference(patterns, threat_data, reasons)
        
        total_score = (
            industry_score * 0.4 +
            specialization_score * 0.3 +
            severity_score * 0.3
        )
        
        return (total_score, reasons)
    
    def _industry_match(self, patterns: Dict, threat_data: Dict, reasons: List[str]) -> float:
        """Check if threat industry matches analyst focus"""
        threat_industry = threat_data.get('industry', 'unknown')
        industries = patterns.get('most_viewed_industries', {})
        
        if not industries:
            return 0.5
        
        # Get percentage for this industry
        total_views = sum(industries.values())
        industry_pct = industries.get(threat_industry, 0) / total_views if total_views > 0 else 0
        
        if industry_pct > 0.5:
            reasons.append(f"Strong focus on {threat_industry} ({industry_pct*100:.0f}% of activity)")
        elif industry_pct > 0.2:
            reasons.append(f"Moderate interest in {threat_industry}")
        
        return min(1.0, industry_pct * 2)  # Scale to 0-1
    
    def _specialization_match(self, patterns: Dict, threat_data: Dict, reasons: List[str]) -> float:
        """Match threat complexity with analyst specialization"""
        specialization = patterns.get('specialization_score', 0.5)
        threat_severity = threat_data.get('severity', 'MEDIUM')
        
        # Map severity to complexity (assumption: higher severity = more complex)
        complexity_map = {'CRITICAL': 0.9, 'HIGH': 0.7, 'MEDIUM': 0.5, 'LOW': 0.3}
        threat_complexity = complexity_map.get(threat_severity, 0.5)
        
        # Specialists match complex threats, generalists match simpler threats
        if specialization > 0.7 and threat_complexity > 0.7:
            reasons.append("Complex threat matches specialist expertise")
            return 0.9
        elif specialization < 0.4 and threat_complexity < 0.5:
            reasons.append("Standard threat appropriate for generalist")
            return 0.8
        else:
            # Partial match
            return 0.6
    
    def _severity_preference(self, patterns: Dict, threat_data: Dict, reasons: List[str]) -> float:
        """Check if threat severity matches analyst's usual focus"""
        severity_focus = patterns.get('preferred_severity_focus', {})
        threat_severity = threat_data.get('severity', 'MEDIUM')
        
        if not severity_focus:
            return 0.5
        
        total = sum(severity_focus.values())
        severity_pct = severity_focus.get(threat_severity, 0) / total if total > 0 else 0
        
        if severity_pct > 0.4:
            reasons.append(f"Typical severity level for analyst ({threat_severity})")
        
        return min(1.0, severity_pct * 2.5)


class ThreatCharacteristicsScorer:
    """
    Score based on threat attributes
    
    Weight: 30%
    
    Factors:
    - Severity × Confidence (50% of scorer)
    - Source reliability (30% of scorer)
    - Threat recency (20% of scorer)
    """
    
    async def score(self, analyst_id: str, threat_data: Dict) -> Tuple[float, List[str]]:
        """Calculate threat characteristics score"""
        reasons = []
        
        # Factor 1: Severity × Confidence (50%)
        severity_confidence = self._severity_confidence_product(threat_data, reasons)
        
        # Factor 2: Source Reliability (30%)
        source_score = self._source_reliability(threat_data, reasons)
        
        # Factor 3: Recency (20%)
        recency_score = self._recency_score(threat_data, reasons)
        
        total_score = (
            severity_confidence * 0.5 +
            source_score * 0.3 +
            recency_score * 0.2
        )
        
        return (total_score, reasons)
    
    def _severity_confidence_product(self, threat_data: Dict, reasons: List[str]) -> float:
        """Multiply severity by confidence"""
        severity_map = {'CRITICAL': 1.0, 'HIGH': 0.7, 'MEDIUM': 0.4, 'LOW': 0.1}
        severity = threat_data.get('severity', 'MEDIUM')
        confidence = threat_data.get('confidence', 0.5)
        
        severity_val = severity_map.get(severity, 0.5)
        product = severity_val * confidence
        
        if product > 0.8:
            reasons.append(f"{severity} severity with {confidence*100:.0f}% confidence")
        
        return product
    
    def _source_reliability(self, threat_data: Dict, reasons: List[str]) -> float:
        """Score based on source trustworthiness"""
        sources = threat_data.get('sources', [])
        source_reliability = threat_data.get('source_reliability', 0.5)
        
        # Multiple sources = more reliable
        source_count = len(sources) if isinstance(sources, list) else 1
        count_factor = min(1.0, source_count / 5)
        
        combined_score = (count_factor * 0.6 + source_reliability * 0.4)
        
        if source_count >= 3:
            reasons.append(f"Validated by {source_count} sources")
        
        return combined_score
    
    def _recency_score(self, threat_data: Dict, reasons: List[str]) -> float:
        """Score based on how recent the threat is"""
        published = threat_data.get('published_date')
        
        if not published:
            return 0.5
        
        try:
            if isinstance(published, str):
                published_dt = datetime.fromisoformat(published.replace('Z', '+00:00'))
            else:
                published_dt = published
            
            age_days = (datetime.now() - published_dt.replace(tzinfo=None)).days
            
            # Exponential decay: e^(-λt), λ = 0.1
            recency = math.exp(-0.1 * age_days)
            
            if age_days < 1:
                reasons.append("Breaking threat (today)")
            elif age_days < 7:
                reasons.append(f"Recent threat ({age_days} days old)")
            
            return recency
        except:
            return 0.5


class TemporalRelevanceScorer:
    """
    Score based on time and campaign context
    
    Weight: 20%
    
    Factors:
    - Campaign membership (40% of scorer)
    - Threat evolution (30% of scorer)
    - Time decay (30% of scorer)
    """
    
    def __init__(self, memory_system: ThreatMemorySystem):
        self.memory_system = memory_system
    
    async def score(self, analyst_id: str, threat_data: Dict) -> Tuple[float, List[str]]:
        """Calculate temporal relevance score"""
        reasons = []
        
        threat_id = threat_data.get('threat_id', threat_data.get('id', 'unknown'))
        
        # Factor 1: Campaign Membership (40%)
        campaign_score = await self._campaign_relevance(threat_id, reasons)
        
        # Factor 2: Evolution Stage (30%)
        evolution_score = await self._evolution_stage(threat_id, reasons)
        
        # Factor 3: Recency (30%)
        recency_score = self._time_decay(threat_data, reasons)
        
        total_score = (
            campaign_score * 0.4 +
            evolution_score * 0.3 +
            recency_score * 0.3
        )
        
        return (total_score, reasons)
    
    async def _campaign_relevance(self, threat_id: str, reasons: List[str]) -> float:
        """Check if threat is part of active campaign"""
        # TODO: Query Redis for campaign membership
        # For now, placeholder
        return 0.5
    
    async def _evolution_stage(self, threat_id: str, reasons: List[str]) -> float:
        """Determine if threat is evolving"""
        # TODO: Query Redis for evolution chain
        # For now, placeholder
        return 0.5
    
    def _time_decay(self, threat_data: Dict, reasons: List[str]) -> float:
        """Calculate time-based relevance decay"""
        published = threat_data.get('published_date')
        
        if not published:
            return 0.5
        
        try:
            if isinstance(published, str):
                published_dt = datetime.fromisoformat(published.replace('Z', '+00:00'))
            else:
                published_dt = published
            
            days_old = (datetime.now() - published_dt.replace(tzinfo=None)).days
            
            # Exponential decay with 10-day half-life
            decay = math.exp(-0.1 * days_old)
            
            return decay
        except:
            return 0.5


class OrganizationalContextScorer:
    """
    Score based on organizational factors
    
    Weight: 10%
    
    Factors:
    - Industry targeting (60% of scorer)
    - Past incident correlation (40% of scorer)
    """
    
    async def score(self, analyst_id: str, threat_data: Dict) -> Tuple[float, List[str]]:
        """Calculate organizational context score"""
        reasons = []
        
        # Factor 1: Industry Targeting (60%)
        targeting_score = self._industry_targeting(threat_data, reasons)
        
        # Factor 2: Past Incidents (40%)
        incident_score = await self._incident_correlation(threat_data, reasons)
        
        total_score = (
            targeting_score * 0.6 +
            incident_score * 0.4
        )
        
        return (total_score, reasons)
    
    def _industry_targeting(self, threat_data: Dict, reasons: List[str]) -> float:
        """Check if threat specifically targets analyst's industry"""
        industry = threat_data.get('industry', 'unknown')
        
        # Higher score if industry-specific
        if industry != 'unknown' and industry != 'general':
            reasons.append(f"Specifically targets {industry} sector")
            return 0.9
        else:
            return 0.5
    
    async def _incident_correlation(self, threat_data: Dict, reasons: List[str]) -> float:
        """Check if similar threats caused past incidents"""
        # TODO: Query Neo4j for incident history
        # For now, placeholder
        return 0.5


class PredictiveEngine:
    """
    Advanced threat prioritization engine
    
    Combines 4 independent scorers with weighted ensemble method.
    Provides confidence intervals and explainable predictions.
    
    Redis-First: Reads from Redis primarily, Neo4j for enrichment.
    """
    
    def __init__(
        self,
        pattern_analyzer: PatternAnalyzer,
        memory_system: ThreatMemorySystem,
        redis_url: str = "redis://localhost:32379"  # NodePort for tqakb/redis-82
    ):
        """
        Initialize predictive engine
        
        Args:
            pattern_analyzer: For analyst behavior patterns
            memory_system: For threat memories
            redis_url: Redis connection (default: port 32379 - NodePort)
        """
        self.pattern_analyzer = pattern_analyzer
        self.memory_system = memory_system
        self.redis_url = redis_url
        
        # Initialize scorers
        self.scorers = {
            'analyst_affinity': AnalystAffinityScorer(pattern_analyzer),
            'threat_characteristics': ThreatCharacteristicsScorer(),
            'temporal_relevance': TemporalRelevanceScorer(memory_system),
            'organizational_context': OrganizationalContextScorer()
        }
        
        # Weights (sum to 1.0)
        self.weights = {
            'analyst_affinity': 0.40,
            'threat_characteristics': 0.30,
            'temporal_relevance': 0.20,
            'organizational_context': 0.10
        }
        
        self._redis_client: Optional[redis.Redis] = None
    
    async def connect(self):
        """Connect to Redis"""
        if not self._redis_client:
            self._redis_client = await redis.from_url(
                self.redis_url,
                decode_responses=True
            )
    
    async def disconnect(self):
        """Close connections"""
        if self._redis_client:
            await self._redis_client.aclose()
            self._redis_client = None
    
    async def predict_threat_priority(
        self,
        analyst_id: str,
        threat_data: Dict
    ) -> PredictionResult:
        """
        Predict threat priority for analyst
        
        Args:
            analyst_id: Analyst identifier
            threat_data: Threat metadata (from Redis)
            
        Returns:
            Prediction with priority, confidence, and explanations
        """
        await self.connect()
        
        # Run all scorers in parallel
        scorer_tasks = {
            name: scorer.score(analyst_id, threat_data)
            for name, scorer in self.scorers.items()
        }
        
        results = await asyncio.gather(*scorer_tasks.values())
        
        # Extract scores and reasons
        scores = {}
        all_reasons = []
        
        for name, (score, reasons) in zip(scorer_tasks.keys(), results):
            scores[name] = score
            all_reasons.extend(reasons)
        
        # Calculate weighted average
        predicted_priority = sum(
            scores[name] * self.weights[name]
            for name in scores
        )
        
        # Calculate confidence based on data quality
        confidence = self._calculate_confidence(analyst_id, threat_data, scores)
        
        # Determine recommendation
        recommendation = self._determine_recommendation(predicted_priority, confidence)
        
        # Filter top reasons (max 5)
        top_reasons = all_reasons[:5] if all_reasons else ["Standard prioritization"]
        
        return PredictionResult(
            analyst_id=analyst_id,
            threat_id=threat_data.get('threat_id', threat_data.get('id', 'unknown')),
            predicted_priority=predicted_priority,
            confidence=confidence,
            scores=scores,
            reasons=top_reasons,
            recommendation=recommendation,
            timestamp=datetime.utcnow().isoformat()
        )
    
    def _calculate_confidence(
        self,
        analyst_id: str,
        threat_data: Dict,
        scores: Dict[str, float]
    ) -> float:
        """
        Calculate confidence in prediction
        
        Based on:
        - Data availability
        - Score agreement (low variance = high confidence)
        """
        # Factor 1: Data completeness
        required_fields = ['severity', 'confidence', 'industry', 'sources']
        completeness = sum(1 for f in required_fields if threat_data.get(f)) / len(required_fields)
        
        # Factor 2: Score variance (low variance = high confidence)
        score_values = list(scores.values())
        mean_score = sum(score_values) / len(score_values)
        variance = sum((s - mean_score) ** 2 for s in score_values) / len(score_values)
        agreement = 1.0 - min(1.0, variance * 2)  # Scale variance to 0-1
        
        # Combine
        confidence = (completeness * 0.6 + agreement * 0.4)
        
        return confidence
    
    def _determine_recommendation(self, priority: float, confidence: float) -> str:
        """Determine action recommendation"""
        if priority >= 0.9 and confidence >= 0.8:
            return 'immediate_alert'
        elif priority >= 0.7:
            return 'priority_review'
        else:
            return 'standard_queue'


# Example usage
if __name__ == "__main__":
    import asyncio
    from .flow_tracker import AnalystFlowTracker, ActionType
    
    async def demo():
        """Demonstration of predictive engine"""
        
        # Initialize components
        tracker = AnalystFlowTracker()
        pattern_analyzer = PatternAnalyzer(tracker)
        memory_system = ThreatMemorySystem()
        engine = PredictiveEngine(pattern_analyzer, memory_system)
        
        try:
            # Simulate analyst behavior (aviation focus)
            for i in range(10):
                await tracker.track_action(
                    analyst_id="analyst_demo",
                    action_type=ActionType.VIEW_THREAT,
                    threat_id=f"threat_{i}",
                    industry="aviation",
                    severity="CRITICAL",
                    time_spent_seconds=120
                )
            
            # New threat arrives
            threat_data = {
                'threat_id': 'threat_new',
                'title': 'Lockbit ransomware targeting airlines',
                'severity': 'CRITICAL',
                'confidence': 0.95,
                'industry': 'aviation',
                'sources': ['cisa', 'twitter', 'vendor'],
                'source_reliability': 0.9,
                'published_date': datetime.utcnow().isoformat()
            }
            
            # Predict priority
            prediction = await engine.predict_threat_priority("analyst_demo", threat_data)
            
            print(f"\n✓ Predicted Priority: {prediction.predicted_priority:.3f}")
            print(f"✓ Confidence: {prediction.confidence:.3f}")
            print(f"✓ Recommendation: {prediction.recommendation}")
            print(f"\n✓ Score Breakdown:")
            for name, score in prediction.scores.items():
                print(f"  - {name}: {score:.3f}")
            print(f"\n✓ Reasons:")
            for reason in prediction.reasons:
                print(f"  - {reason}")
        
        finally:
            await tracker.disconnect()
            await memory_system.disconnect()
            await engine.disconnect()
    
    asyncio.run(demo())
