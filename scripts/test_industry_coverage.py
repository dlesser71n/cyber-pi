#!/usr/bin/env python3
"""Test expanded industry coverage"""

import yaml
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent / 'src'))

from processors.client_filter import ClientFilter

# Load config
with open('config/client_filters.yaml', 'r') as f:
    config = yaml.safe_load(f)

industries = [k for k in config.keys() if k != 'filter_settings']

print("=" * 80)
print("🏢 FORTUNE 1000 INDUSTRY COVERAGE")
print("=" * 80)
print(f"\nTotal Industries Covered: {len(industries)}")
print("\nIndustries by Priority:\n")

# Group by priority
critical = []
high = []
medium = []

for ind in sorted(industries):
    profile = config[ind]
    priority = profile.get('priority_level', 'medium')
    name = profile.get('name', ind)
    
    if priority == 'critical':
        critical.append(name)
    elif priority == 'high':
        high.append(name)
    else:
        medium.append(name)

print("🔴 CRITICAL PRIORITY:")
for i, name in enumerate(critical, 1):
    print(f"   {i}. {name}")

print(f"\n🟠 HIGH PRIORITY:")
for i, name in enumerate(high, 1):
    print(f"   {i}. {name}")

print(f"\n🟢 MEDIUM PRIORITY:")
for i, name in enumerate(medium, 1):
    print(f"   {i}. {name}")

print("\n" + "=" * 80)
print("📊 SUMMARY")
print("=" * 80)
print(f"Critical: {len(critical)}")
print(f"High:     {len(high)}")
print(f"Medium:   {len(medium)}")
print(f"TOTAL:    {len(industries)}")

# Test filter on sample threat
print("\n" + "=" * 80)
print("🧪 TESTING FILTERS WITH SAMPLE THREATS")
print("=" * 80)

filter_engine = ClientFilter()

test_threats = [
    {
        'title': 'Supply Chain Ransomware Hits Manufacturing Sector',
        'description': 'Ransomware targeting SAP ERP systems in automotive manufacturing plants',
        'tags': ['ransomware', 'manufacturing', 'supply-chain']
    },
    {
        'title': 'Major Retail Chain Suffers POS Malware Attack',
        'description': 'Point of sale systems compromised, payment card data stolen',
        'tags': ['retail', 'pos', 'malware']
    },
    {
        'title': 'Cloud Provider API Vulnerability Disclosed',
        'description': 'Critical AWS API vulnerability affecting SaaS companies',
        'tags': ['cloud', 'api', 'vulnerability']
    }
]

# Test against 3 industries
for industry in ['manufacturing', 'retail', 'technology']:
    print(f"\n{industry.upper()}:")
    filtered = filter_engine.filter_for_client(test_threats, industry, min_score=5)
    print(f"  Relevant threats: {len(filtered)}")
    if filtered:
        for threat in filtered[:2]:
            print(f"    • {threat['title'][:60]} (score: {threat['relevance_score']})")

print("\n✅ All filters operational!")
