"""Cascade Intelligence Layer for cyber-pi

Provides agentic AI capabilities:
- Flow tracking: Learn from analyst behavior
- Memory formation: Remember important threats
- Predictive prioritization: Proactive threat surfacing
- Semantic understanding: Deep threat comprehension
- Workflow automation: Zero-touch investigations
"""

# Import implemented and tested modules
from .flow_tracker import AnalystFlowTracker, FlowAction, ActionType
from .pattern_analyzer import PatternAnalyzer
from .memory_system import ThreatMemorySystem, MemoryType, ThreatMemory
from .predictive_engine import (
    PredictiveEngine,
    PredictionResult,
    AnalystAffinityScorer,
    ThreatCharacteristicsScorer,
    TemporalRelevanceScorer,
    OrganizationalContextScorer
)

__all__ = [
    # Flow Tracking
    'AnalystFlowTracker',
    'FlowAction',
    'ActionType',
    # Pattern Analysis
    'PatternAnalyzer',
    # Memory System
    'ThreatMemorySystem',
    'MemoryType',
    'ThreatMemory',
    # Predictive Engine
    'PredictiveEngine',
    'PredictionResult',
    'AnalystAffinityScorer',
    'ThreatCharacteristicsScorer',
    'TemporalRelevanceScorer',
    'OrganizationalContextScorer',
]

__version__ = '1.0.0'
