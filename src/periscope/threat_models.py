#!/usr/bin/env python3
"""
Threat Data Models for Cascade Memory System
Adapted from TQAKB golden config patterns
"""

from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum


class ThreatSeverity(Enum):
    """Threat severity levels"""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


@dataclass
class WorkingMemory:
    """
    Level 1: Active threat being analyzed NOW
    (Adapted from TQAKB golden config)
    """
    id: str
    threat_id: str
    content: str
    severity: str
    started_at: str
    last_activity: str
    
    # Analyst interaction tracking
    analyst_count: int = 0
    interaction_count: int = 0
    escalation_count: int = 0
    view_count: int = 0
    dismiss_count: int = 0
    analyst_actions: Dict[str, str] = field(default_factory=dict)
    
    # Threat scoring
    threat_score: float = 0.5
    
    # Metadata
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Serialize to dict"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'WorkingMemory':
        """Deserialize from dict"""
        return cls(**data)


@dataclass
class ShortTermMemory:
    """
    Level 2: Recently validated threat
    (Adapted from TQAKB golden config)
    """
    id: str
    threat_id: str
    content: str
    confidence: float
    severity: str
    industry: str
    formed_at: str
    last_updated: str
    
    # Evidence tracking
    evidence_count: int
    analyst_interactions: int
    memory_type: str  # "validated", "pattern", "false_positive"
    
    # Scoring and ranking
    score: float
    validated: bool = False
    consolidation_count: int = 1
    
    # Metadata
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Serialize to dict"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ShortTermMemory':
        """Deserialize from dict"""
        return cls(**data)


@dataclass
class LongTermMemory:
    """
    Level 3: Permanent knowledge
    (Adapted from TQAKB golden config with "facts don't decay" principle)
    """
    id: str
    threat_id: str
    content: str
    confidence: float
    severity: str
    industry: str
    formed_at: str
    last_updated: str
    
    # Evidence tracking
    evidence_count: int
    analyst_interactions: int
    memory_type: str
    consolidation_count: int
    
    # Validation (like "facts" in TQAKB)
    validated: bool
    decay_protected: bool = False  # Validated threats don't decay (golden pattern)
    
    # Export tracking
    neo4j_exported: bool = False
    
    # Metadata
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Serialize to dict"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'LongTermMemory':
        """Deserialize from dict"""
        return cls(**data)


def calculate_threat_score(threat: WorkingMemory) -> float:
    """
    Calculate multi-factor threat score (0.0 - 1.0)
    
    Factors:
    - Severity weight (30%)
    - Engagement score (20%)
    - Escalation score (30%)
    - Recency score (20%)
    """
    import math
    
    # Severity weight
    severity_weight = {
        'CRITICAL': 1.0,
        'HIGH': 0.7,
        'MEDIUM': 0.4,
        'LOW': 0.1
    }.get(threat.severity, 0.5)
    
    # Engagement score (interactions)
    engagement = min(1.0, threat.interaction_count / 10)
    
    # Escalation score (more important than views)
    escalation_score = min(1.0, threat.escalation_count / 3)
    
    # Recency score (exponential decay)
    try:
        last_activity = datetime.fromisoformat(threat.last_activity)
        age_minutes = (datetime.utcnow() - last_activity).total_seconds() / 60
        recency = math.exp(-age_minutes / 30)  # 30min half-life
    except:
        recency = 0.5
    
    # Composite score
    score = (
        severity_weight * 0.3 +
        engagement * 0.2 +
        escalation_score * 0.3 +
        recency * 0.2
    )
    
    return min(1.0, score)


def should_promote_to_level2(threat: WorkingMemory) -> bool:
    """
    Check if threat should be promoted to Level 2
    (Adapted from TQAKB golden config promotion criteria)
    """
    score = calculate_threat_score(threat)
    
    # Multiple validation signals
    has_validation = threat.analyst_count >= 2
    has_engagement = threat.interaction_count >= 3
    has_escalations = threat.escalation_count >= 2
    is_severe = threat.severity in ['CRITICAL', 'HIGH']
    
    return (
        score >= 0.7 and
        has_validation and
        (has_escalations or is_severe)
    )


def should_promote_to_level3(memory: ShortTermMemory) -> bool:
    """
    Check if memory should be promoted to Level 3
    (Adapted from TQAKB golden config promotion criteria)
    """
    return (
        memory.confidence >= 0.8 and
        memory.consolidation_count >= 3 and
        memory.validated
    )


def determine_memory_type(threat: WorkingMemory) -> str:
    """Determine memory type based on analyst actions"""
    if threat.escalation_count >= 2:
        return "validated"
    elif threat.dismiss_count > threat.escalation_count:
        return "false_positive"
    else:
        return "pattern"


def calculate_decay(
    initial_confidence: float,
    decay_rate: float,
    days_elapsed: float,
    is_validated: bool = False
) -> float:
    """
    Calculate decayed confidence (TQAKB Golden Pattern)
    
    CRITICAL: Validated threats don't decay (like "facts" in TQAKB)
    """
    
    # VALIDATED THREATS DO NOT DECAY (golden pattern)
    if is_validated:
        return initial_confidence
    
    if days_elapsed <= 0:
        return initial_confidence
    
    # Exponential decay
    decayed = initial_confidence * ((1 - decay_rate) ** days_elapsed)
    
    # Floor at 0.3 (don't decay below 30%)
    return max(0.3, decayed)
