#!/usr/bin/env python3
"""Test Social Intelligence Layer"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.collectors.social_intelligence import SocialIntelligenceCollector
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')

def main():
    print("=" * 80)
    print("🌐 TESTING SOCIAL INTELLIGENCE LAYER")
    print("=" * 80)
    print()
    
    try:
        collector = SocialIntelligenceCollector()
        items = collector.collect_all()
        
        print()
        print("=" * 80)
        print("📊 RESULTS")
        print("=" * 80)
        print(f"Total items: {len(items)}")
        print()
        
        if items:
            print("Sample items:")
            for i, item in enumerate(items[:5], 1):
                print(f"\n{i}. [{item['source']['name']}]")
                print(f"   {item['title'][:80]}")
                print(f"   {item['link']}")
            
            print()
            print("✅ Social Intelligence Layer working!")
            print(f"🎯 Captured {len(items)} real-time threats")
        else:
            print("⚠️  No items collected")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
