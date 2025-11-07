#!/usr/bin/env python3
"""
Test Analyst Assistant - AI-powered threat triage assistance
"""

import asyncio
import random
from datetime import datetime

from src.periscope.periscope_batch_ops import PeriscopeTriageBatch


async def test_analyst_assistant():
    """
    Demonstrate Analyst Assistant learning and recommendations
    
    Scenario:
    1. Analyst "Alice" handles 20 CRITICAL threats (escalates most)
    2. Analyst "Bob" handles 20 MEDIUM threats (dismisses most)
    3. New threats arrive - Assistant provides recommendations
    4. Show how it learns from team patterns
    """
    
    print("=" * 80)
    print("🧠 ANALYST ASSISTANT DEMONSTRATION")
    print("   Learning from analyst behavior to provide intelligent recommendations")
    print("=" * 80)
    
    # Initialize Periscope
    periscope = PeriscopeTriageBatch(
        redis_host="localhost",
        redis_port=32379
    )
    
    await periscope.initialize()
    await periscope.initialize_assistant()
    
    print("\n⏱️  Phase 1: Training - Analyst Alice (CRITICAL threats)")
    print("   Alice is experienced with critical threats and escalates aggressively\n")
    
    # Alice handles 20 CRITICAL threats
    alice_actions = []
    for i in range(20):
        threat_id = f"critical_{i:03d}"
        
        # Add threat
        await periscope.add_threat(
            threat_id=threat_id,
            content=f"Critical security incident {i}",
            severity="CRITICAL",
            metadata={'source': 'SIEM', 'confidence': 0.9}
        )
        
        # Alice views it
        await periscope.record_interaction(threat_id, "alice", "view")
        
        # Alice escalates 85% of the time
        if random.random() < 0.85:
            action = "escalate"
            outcome = "true_positive" if random.random() < 0.7 else None
        else:
            action = "investigate"
            outcome = None
        
        await periscope.record_analyst_action(threat_id, "alice", action, outcome)
        alice_actions.append(action)
    
    escalated = alice_actions.count("escalate")
    print(f"   ✅ Alice handled 20 CRITICAL threats")
    print(f"      Escalated: {escalated} ({escalated/20*100:.0f}%)")
    print(f"      Investigated: {20-escalated}")
    
    # ========================================================================
    print("\n⏱️  Phase 2: Training - Analyst Bob (MEDIUM threats)")
    print("   Bob is cautious and dismisses most medium threats as false positives\n")
    
    # Bob handles 20 MEDIUM threats
    bob_actions = []
    for i in range(20):
        threat_id = f"medium_{i:03d}"
        
        # Add threat
        await periscope.add_threat(
            threat_id=threat_id,
            content=f"Medium security alert {i}",
            severity="MEDIUM",
            metadata={'source': 'IDS', 'confidence': 0.5}
        )
        
        # Bob views it
        await periscope.record_interaction(threat_id, "bob", "view")
        
        # Bob dismisses 70% of the time
        if random.random() < 0.70:
            action = "dismiss"
            outcome = "false_positive" if random.random() < 0.6 else None
        else:
            action = "monitor"
            outcome = None
        
        await periscope.record_analyst_action(threat_id, "bob", action, outcome)
        bob_actions.append(action)
    
    dismissed = bob_actions.count("dismiss")
    print(f"   ✅ Bob handled 20 MEDIUM threats")
    print(f"      Dismissed: {dismissed} ({dismissed/20*100:.0f}%)")
    print(f"      Monitored: {20-dismissed}")
    
    # ========================================================================
    print("\n⏱️  Phase 3: Assistance - New CRITICAL Threat")
    print("   New CRITICAL threat arrives - what should Alice do?\n")
    
    # New CRITICAL threat
    new_critical = "critical_new_001"
    await periscope.add_threat(
        threat_id=new_critical,
        content="New critical ransomware detection",
        severity="CRITICAL",
        metadata={'source': 'EDR', 'confidence': 0.95}
    )
    
    # Get assistance for Alice
    recommendation = await periscope.get_assistance(new_critical, "alice")
    
    print(f"   🤖 Assistant Recommendation for Alice:")
    print(f"      Suggested Action: {recommendation.suggested_action.upper()}")
    print(f"      Confidence: {recommendation.confidence:.1%}")
    print(f"\n      Reasoning:")
    for reason in recommendation.reasoning:
        print(f"      • {reason}")
    
    if recommendation.alternative_actions:
        print(f"\n      Alternative Actions:")
        for action, score in recommendation.alternative_actions:
            print(f"      • {action}: {score:.1%}")
    
    # ========================================================================
    print("\n⏱️  Phase 4: Assistance - New MEDIUM Threat")
    print("   New MEDIUM threat arrives - what should Bob do?\n")
    
    # New MEDIUM threat
    new_medium = "medium_new_001"
    await periscope.add_threat(
        threat_id=new_medium,
        content="Suspicious network traffic detected",
        severity="MEDIUM",
        metadata={'source': 'Firewall', 'confidence': 0.4}
    )
    
    # Get assistance for Bob
    recommendation = await periscope.get_assistance(new_medium, "bob")
    
    print(f"   🤖 Assistant Recommendation for Bob:")
    print(f"      Suggested Action: {recommendation.suggested_action.upper()}")
    print(f"      Confidence: {recommendation.confidence:.1%}")
    print(f"\n      Reasoning:")
    for reason in recommendation.reasoning:
        print(f"      • {reason}")
    
    if recommendation.alternative_actions:
        print(f"\n      Alternative Actions:")
        for action, score in recommendation.alternative_actions:
            print(f"      • {action}: {score:.1%}")
    
    # ========================================================================
    print("\n⏱️  Phase 5: Cross-Analyst Learning")
    print("   What if Alice gets a MEDIUM threat? (Bob's specialty)\n")
    
    # Alice gets a MEDIUM threat
    alice_medium = "medium_alice_001"
    await periscope.add_threat(
        threat_id=alice_medium,
        content="Port scan detected",
        severity="MEDIUM",
        metadata={'source': 'IDS', 'confidence': 0.3}
    )
    
    # Get assistance for Alice on MEDIUM threat
    recommendation = await periscope.get_assistance(alice_medium, "alice")
    
    print(f"   🤖 Assistant Recommendation for Alice (MEDIUM threat):")
    print(f"      Suggested Action: {recommendation.suggested_action.upper()}")
    print(f"      Confidence: {recommendation.confidence:.1%}")
    print(f"\n      Reasoning:")
    for reason in recommendation.reasoning:
        print(f"      • {reason}")
    print(f"\n      💡 Notice: Assistant learns from Bob's patterns for MEDIUM threats!")
    
    # ========================================================================
    print("\n⏱️  Phase 6: Analyst & Team Statistics")
    
    # Alice stats
    alice_stats = await periscope.get_analyst_stats("alice")
    print(f"\n   📊 Alice's Statistics:")
    print(f"      Total Actions: {alice_stats['total_actions']}")
    print(f"      Action Breakdown: {alice_stats['action_breakdown']}")
    
    # Bob stats
    bob_stats = await periscope.get_analyst_stats("bob")
    print(f"\n   📊 Bob's Statistics:")
    print(f"      Total Actions: {bob_stats['total_actions']}")
    print(f"      Action Breakdown: {bob_stats['action_breakdown']}")
    
    # Team stats
    team_stats = await periscope.get_team_stats()
    print(f"\n   📊 Team Statistics:")
    print(f"      Total Team Actions: {team_stats['total_actions']}")
    print(f"      Team Action Breakdown: {team_stats['action_breakdown']}")
    print(f"      Unique Patterns Learned: {team_stats['unique_patterns']}")
    
    # ========================================================================
    print("\n" + "=" * 80)
    print("🎉 ANALYST ASSISTANT DEMONSTRATION COMPLETE!")
    print("=" * 80)
    
    print("\n💡 Key Takeaways:")
    print("   ✅ Learns from individual analyst patterns")
    print("   ✅ Learns from team collective wisdom")
    print("   ✅ Provides confidence-weighted recommendations")
    print("   ✅ Explains reasoning with evidence")
    print("   ✅ Suggests alternatives for analyst consideration")
    print("   ✅ Cross-analyst learning (Alice learns from Bob's patterns)")
    print("   ✅ Human always in control (assistant, not autopilot)")
    
    print("\n🚀 Rickover Principle: 'Human in the loop, machine provides intelligence'")


if __name__ == "__main__":
    asyncio.run(test_analyst_assistant())
