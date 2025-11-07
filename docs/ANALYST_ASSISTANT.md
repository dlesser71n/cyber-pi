# Analyst Assistant - AI-Powered Threat Triage Intelligence

## Overview

The **Analyst Assistant** is an AI-powered system that learns from analyst behavior to provide intelligent, context-aware recommendations for threat triage decisions.

**NOT a copilot** (automation) - **IS an assistant** (human-in-the-loop)

**Rickover Principle:** Human always in control, machine provides intelligence.

---

## Key Features

### 1. **Individual Learning**
- Learns from each analyst's unique patterns
- Tracks what actions YOU typically take
- Adapts to your expertise and decision-making style

### 2. **Team Collective Wisdom**
- Learns from entire team's patterns
- Shares knowledge across analysts
- "Analysts like you escalated similar threats 87% of the time"

### 3. **Confidence-Weighted Recommendations**
- Provides suggested action with confidence score
- Never claims 100% certainty (capped at 95%)
- Transparent about uncertainty

### 4. **Explainable Reasoning**
- Every recommendation includes evidence-based reasoning
- Shows supporting data from history
- Cites specific patterns and statistics

### 5. **Alternative Actions**
- Suggests 2-3 alternative actions with probabilities
- Analyst chooses final decision
- System learns from chosen action

---

## How It Works

### Learning Process

```python
# 1. Analyst takes action
await periscope.record_analyst_action(
    threat_id="threat_001",
    analyst_id="alice",
    action="escalate",
    outcome="true_positive"  # Optional
)

# 2. System learns patterns
# - Individual: "Alice escalates CRITICAL threats 85% of the time"
# - Team: "Team escalates CRITICAL threats 75% of the time"
# - Outcomes: "Escalations resulted in incidents 70% of the time"
```

### Recommendation Process

```python
# 1. New threat arrives
recommendation = await periscope.get_assistance(
    threat_id="threat_new",
    analyst_id="alice"
)

# 2. System provides recommendation
print(recommendation.suggested_action)  # "escalate"
print(recommendation.confidence)        # 0.87
print(recommendation.reasoning)         # ["You escalated 15 similar threats", ...]
print(recommendation.alternative_actions)  # [("investigate", 0.08), ...]
```

---

## Recommendation Weighting

The system combines multiple intelligence sources:

| Source | Weight | Description |
|--------|--------|-------------|
| **Analyst Patterns** | 40% | What YOU typically do |
| **Team Patterns** | 30% | What TEAM typically does |
| **Historical Outcomes** | 20% | What WORKED in the past |
| **Threat Characteristics** | 10% | What's SIMILAR to this |

---

## Example Recommendations

### Example 1: CRITICAL Threat for Experienced Analyst

```
🤖 Assistant Recommendation for Alice:
   Suggested Action: ESCALATE
   Confidence: 87%

   Reasoning:
   • You've taken 'escalate' action 15 times for CRITICAL threats
   • Team takes 'escalate' action 75% of the time for CRITICAL threats
   • High threat score (0.92) suggests escalation
   • CRITICAL severity requires immediate attention

   Alternative Actions:
   • investigate: 8%
   • monitor: 5%
```

### Example 2: MEDIUM Threat for Cautious Analyst

```
🤖 Assistant Recommendation for Bob:
   Suggested Action: DISMISS
   Confidence: 72%

   Reasoning:
   • You've taken 'dismiss' action 17 times for MEDIUM threats
   • Team takes 'dismiss' action 85% of the time for MEDIUM threats
   • Low threat score (0.28) suggests dismissal

   Alternative Actions:
   • monitor: 18%
   • investigate: 10%
```

### Example 3: Cross-Analyst Learning

```
🤖 Assistant Recommendation for Alice (MEDIUM threat):
   Suggested Action: DISMISS
   Confidence: 55%

   Reasoning:
   • Team takes 'dismiss' action 85% of the time for MEDIUM threats
   • (No personal history for MEDIUM threats)

   💡 Notice: Assistant learns from Bob's patterns for MEDIUM threats!
```

---

## API Reference

### Get Assistance

```python
recommendation = await periscope.get_assistance(
    threat_id="threat_001",
    analyst_id="alice"
)

# Returns: AssistanceRecommendation
# - suggested_action: str
# - confidence: float
# - reasoning: List[str]
# - supporting_evidence: List[Dict]
# - alternative_actions: List[Tuple[str, float]]
# - analyst_context: Dict
# - team_context: Dict
```

### Record Action

```python
await periscope.record_analyst_action(
    threat_id="threat_001",
    analyst_id="alice",
    action="escalate",  # escalate, dismiss, monitor, investigate
    outcome="true_positive"  # Optional: true_positive, false_positive, etc
)
```

### Get Statistics

```python
# Individual analyst stats
alice_stats = await periscope.get_analyst_stats("alice")
# Returns: {
#     'total_actions': 20,
#     'action_breakdown': {'escalate': 15, 'investigate': 5},
#     'recent_actions': [...]
# }

# Team stats
team_stats = await periscope.get_team_stats()
# Returns: {
#     'total_actions': 100,
#     'action_breakdown': {'escalate': 45, 'dismiss': 30, ...},
#     'unique_patterns': 12
# }
```

---

## Integration with Cyber-PI

### Architecture

```
┌─────────────────────────────────────┐
│      Cyber-PI (Primary System)      │
│  ┌──────────────────────────────┐   │
│  │  Periscope Triage               │   │
│  │  - 3-Level Memory            │   │
│  │  - Threat Correlation        │   │
│  │  - Enrichment Pipeline       │   │
│  └──────────────────────────────┘   │
│                ↓                     │
│  ┌──────────────────────────────┐   │
│  │  Analyst Assistant           │   │
│  │  - Learn from behavior       │   │
│  │  - Provide recommendations   │   │
│  │  - Track outcomes            │   │
│  └──────────────────────────────┘   │
└─────────────────────────────────────┘
                ↓
┌─────────────────────────────────────┐
│   TQAKB (Knowledge Service)         │
│   - Historical threat data          │
│   - Playbook procedures             │
│   - Cross-system intelligence       │
└─────────────────────────────────────┘
```

### Data Flow

1. **Threat arrives** → Periscope ingests
2. **Analyst requests assistance** → Assistant provides recommendation
3. **Analyst takes action** → System learns
4. **Outcome recorded** → Success rate updated
5. **TQAKB enrichment** → Historical context added

---

## Performance

### Learning Speed
- **Immediate:** Learns from first action
- **Useful after:** 5-10 actions per threat type
- **Mature after:** 20+ actions per threat type

### Recommendation Quality
- **Cold start:** 50-60% confidence (uses defaults)
- **Warm:** 70-80% confidence (has patterns)
- **Mature:** 85-95% confidence (rich history)

### Storage
- **Per analyst:** ~1KB per action
- **1000 actions:** ~1MB
- **Redis keys:** Indexed by analyst + severity + action

---

## Rickover's Nuclear Submarine Principles Applied

### 1. **Human Always in Control**
- Assistant suggests, human decides
- Never auto-executes actions
- Transparent reasoning

### 2. **Learn from Every Operation**
- Every action is recorded
- Outcomes tracked
- Continuous improvement

### 3. **Simplicity in Design**
- Clear weighting algorithm
- Explainable recommendations
- No black box AI

### 4. **Quality Control**
- Confidence capped at 95%
- Alternative actions provided
- Evidence-based reasoning

### 5. **Continuous Monitoring**
- Track analyst patterns
- Monitor team trends
- Measure success rates

---

## Future Enhancements

### Phase 1 (Current)
- ✅ Individual analyst learning
- ✅ Team pattern learning
- ✅ Confidence-weighted recommendations
- ✅ Explainable reasoning

### Phase 2 (Next)
- 🔄 TQAKB integration for historical context
- 🔄 Threat correlation insights
- 🔄 Playbook recommendations
- 🔄 Outcome prediction

### Phase 3 (Future)
- 🔮 Predictive alerting ("This will likely escalate")
- 🔮 Anomaly detection ("This is unusual for you")
- 🔮 Workload balancing ("Alice is overloaded, assign to Bob")
- 🔮 Training recommendations ("Practice MEDIUM threats")

---

## Testing

Run the demonstration:

```bash
python tests/test_analyst_assistant.py
```

Expected output:
- Alice handles 20 CRITICAL threats (escalates 75-85%)
- Bob handles 20 MEDIUM threats (dismisses 70-80%)
- New threats get intelligent recommendations
- Cross-analyst learning demonstrated
- Statistics show learning patterns

---

## Conclusion

The **Analyst Assistant** is a production-ready AI system that:

✅ Learns from analyst behavior  
✅ Provides intelligent recommendations  
✅ Explains its reasoning  
✅ Keeps humans in control  
✅ Improves over time  

**Rickover would approve:** "The machine provides intelligence, the human makes decisions."
