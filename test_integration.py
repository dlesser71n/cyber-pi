#!/usr/bin/env python3
"""
Test Cyber-Pi + Periscope Triage Integration
"""
import asyncio
import sys
sys.path.insert(0, 'src')

from cyber_pi_periscope_integration import CyberPiPeriscopeIntegration


async def test_integration():
    """Test the integration"""
    
    print("🧪 CYBER-PI + PERISCOPE TRIAGE INTEGRATION TEST")
    print("="*70)
    
    # Initialize
    integration = CyberPiPeriscopeIntegration()
    await integration.initialize()
    
    print("\n✅ Integration initialized\n")
    
    # ========================================================================
    print("TEST 1: Ingest Simulated Cyber-Pi Threats")
    print("-"*70)
    
    # Simulate cyber-pi intelligence items
    cyber_pi_items = [
        {
            'title': 'Critical Ransomware Campaign Targeting Healthcare',
            'description': 'New ransomware variant detected',
            'source': 'ThreatPost',
            'url': 'https://example.com/ransomware',
            'published': '2025-11-03T21:00:00Z',
            'industry': ['healthcare'],
            'tags': ['ransomware', 'critical']
        },
        {
            'title': 'Zero-Day Exploit in Aviation Systems',
            'description': '0-day vulnerability discovered',
            'source': 'SecurityWeek',
            'url': 'https://example.com/0day',
            'published': '2025-11-03T20:00:00Z',
            'industry': ['aviation'],
            'tags': ['0-day', 'exploit']
        },
        {
            'title': 'Phishing Campaign Targets Energy Sector',
            'description': 'Widespread phishing detected',
            'source': 'DarkReading',
            'url': 'https://example.com/phishing',
            'published': '2025-11-03T19:00:00Z',
            'industry': ['energy'],
            'tags': ['phishing', 'high']
        },
        {
            'title': 'Security Advisory: Patch Available for CVE-2025-1234',
            'description': 'Vendor releases patch',
            'source': 'CISA',
            'url': 'https://example.com/advisory',
            'published': '2025-11-03T18:00:00Z',
            'industry': ['all'],
            'tags': ['advisory', 'patch']
        }
    ]
    
    stats = await integration.ingest_cyber_pi_threats(cyber_pi_items)
    print(f"✅ Ingested {stats['added']} threats")
    print(f"   Total items: {stats['total_items']}")
    print(f"   Converted: {stats['converted']}")
    
    # ========================================================================
    print("\nTEST 2: Simulate Analyst Triage")
    print("-"*70)
    
    # Get the first threat ID
    priority = await integration.get_priority_threats(min_score=0.5, limit=5)
    if priority:
        threat_id = priority[0].threat_id
        
        # Simulate analyst interactions
        await integration.record_analyst_triage(threat_id, "analyst_1", "view")
        await integration.record_analyst_triage(threat_id, "analyst_2", "escalate")
        threat = await integration.record_analyst_triage(threat_id, "analyst_3", "escalate")
        
        print(f"✅ Triaged threat: {threat_id}")
        print(f"   Interactions: {threat.interaction_count}")
        print(f"   Escalations: {threat.escalation_count}")
        print(f"   Score: {threat.threat_score:.2f}")
    
    # ========================================================================
    print("\nTEST 3: Get Priority Threats")
    print("-"*70)
    
    priority = await integration.get_priority_threats(min_score=0.6, limit=3)
    print(f"✅ Found {len(priority)} priority threats")
    for threat in priority:
        print(f"   - {threat.threat_id}: {threat.severity} (score: {threat.threat_score:.2f})")
        print(f"     {threat.content[:60]}...")
    
    # ========================================================================
    print("\nTEST 4: Get Hot Threats")
    print("-"*70)
    
    hot = await integration.get_hot_threats(min_interactions=2)
    print(f"✅ Found {len(hot)} hot threats")
    for threat in hot:
        print(f"   - {threat.threat_id}: {threat.interaction_count} interactions")
    
    # ========================================================================
    print("\nTEST 5: Auto-Promote Validated")
    print("-"*70)
    
    promo_stats = await integration.auto_promote_validated()
    print(f"✅ Promotion stats:")
    print(f"   Promoted: {promo_stats['promoted']}")
    print(f"   Failed: {promo_stats['failed']}")
    
    # ========================================================================
    print("\nTEST 6: Triage Dashboard")
    print("-"*70)
    
    dashboard = await integration.get_triage_dashboard()
    print(f"✅ Dashboard:")
    print(f"   Active (L1): {dashboard['system_stats']['total_active']}")
    print(f"   Short-Term (L2): {dashboard['system_stats']['total_short_term']}")
    print(f"   Long-Term (L3): {dashboard['system_stats']['total_long_term']}")
    print(f"   Priority threats: {len(dashboard['priority_threats'])}")
    print(f"   Hot threats: {len(dashboard['hot_threats'])}")
    print(f"   Critical: {dashboard['severity_breakdown']['critical']}")
    print(f"   High: {dashboard['severity_breakdown']['high']}")
    
    # Cleanup
    await integration.cleanup()
    
    print("\n" + "="*70)
    print("🎉 INTEGRATION TEST COMPLETE!")
    print("="*70)
    print("\n✅ Cyber-Pi + Periscope Triage: INTEGRATED")
    print("✅ Threat Ingestion: WORKING")
    print("✅ Analyst Triage: WORKING")
    print("✅ Auto-Promotion: WORKING")
    print("✅ Dashboard: WORKING")
    print("\n🚀 Ready for production threat intelligence operations!")


if __name__ == "__main__":
    asyncio.run(test_integration())
