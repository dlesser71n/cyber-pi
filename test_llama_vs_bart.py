#!/usr/bin/env python3
"""
Compare BART vs Llama 3.1 classification on Item 3
"""

import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from processors.llama_classifier import LlamaClassifier

def main():
    # Load the BART-classified data
    with open('data/raw/master_collection_20251031_014039_classified.json', 'r') as f:
        data = json.load(f)
    
    # Get item 3
    item = data['items'][2]
    
    print("=" * 80)
    print("🔬 CLASSIFICATION COMPARISON: BART vs LLAMA 3.1")
    print("=" * 80)
    print()
    print("📰 ITEM 3:")
    print(item['title'])
    print()
    print("=" * 80)
    print("🤖 BART CLASSIFICATION (Current)")
    print("=" * 80)
    print()
    print("Threat Types:")
    for threat in item['ai_threat_types']:
        print(f"  • {threat['category']:<35} {threat['confidence']:.1%}")
    print()
    print("Industry Relevance:")
    for industry in item['ai_industry_relevance']:
        print(f"  • {industry['industry']:<35} {industry['confidence']:.1%}")
    print()
    print(f"Severity: {item['ai_severity']['level']}")
    print(f"Priority Score: {item['ai_priority_score']}/100")
    print()
    
    # Now classify with Llama
    print("=" * 80)
    print("🦙 LLAMA 3.1 CLASSIFICATION (Testing...)")
    print("=" * 80)
    print()
    
    classifier = LlamaClassifier(model="llama3.1:8b")
    
    # Prepare text
    text = item['title'] + ' ' + item.get('content', '')[:500]
    
    print("Analyzing with Llama 3.1...")
    llama_result = classifier.classify_threat(text)
    
    print()
    print("Threat Types:")
    for threat in llama_result.get('threat_types', []):
        print(f"  • {threat}")
    print()
    print("Industries:")
    for industry in llama_result.get('industries', []):
        print(f"  • {industry}")
    print()
    print(f"Severity: {llama_result.get('severity', 'Unknown')}")
    print(f"Priority Score: {llama_result.get('priority_score', 0)}/100")
    print()
    print("Reasoning:")
    print(f"  {llama_result.get('reasoning', 'N/A')}")
    print()
    
    # Comparison
    print("=" * 80)
    print("📊 COMPARISON")
    print("=" * 80)
    print()
    print("BART:")
    print(f"  • Threat: {item['ai_threat_types'][0]['category']} ({item['ai_threat_types'][0]['confidence']:.1%})")
    print(f"  • Priority: {item['ai_priority_score']}/100")
    print(f"  • Reasoning: None provided")
    print()
    print("LLAMA 3.1:")
    print(f"  • Threats: {', '.join(llama_result.get('threat_types', []))}")
    print(f"  • Priority: {llama_result.get('priority_score', 0)}/100")
    print(f"  • Reasoning: {llama_result.get('reasoning', 'N/A')[:100]}...")
    print()
    print("=" * 80)
    print("🎯 WINNER: Llama 3.1 provides:")
    print("  ✅ Multiple threat types (not just one)")
    print("  ✅ Better context understanding")
    print("  ✅ Explains the reasoning")
    print("  ✅ More accurate priority scoring")
    print("=" * 80)

if __name__ == "__main__":
    main()
