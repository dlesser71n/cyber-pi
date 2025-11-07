#!/usr/bin/env python3
"""
Comprehensive Threat Analysis
Analyzes 1,525 threats across multiple dimensions
"""

import json
import requests
from collections import Counter, defaultdict
from datetime import datetime
import re

print("="*70)
print("🔍 CYBER-PI-INTEL THREAT ANALYSIS")
print("="*70)
print()

# Fetch all threats from API
print("📡 Fetching threat data from API...")
threats = []
offset = 0
limit = 100

while True:
    response = requests.get(f"http://localhost:30888/api/threats?limit={limit}&offset={offset}")
    data = response.json()
    batch = data.get('threats', [])
    if not batch:
        break
    threats.extend(batch)
    offset += limit
    print(f"   Loaded {len(threats)} threats...")
    if len(batch) < limit:
        break

print(f"\n✅ Loaded {len(threats)} total threats")
print()

# ============================================================================
# 1. THREAT CATEGORIZATION
# ============================================================================
print("="*70)
print("📊 THREAT CATEGORIZATION")
print("="*70)
print()

categories = {
    'ransomware': [],
    'apt': [],
    'zero_day': [],
    'malware': [],
    'phishing': [],
    'ddos': [],
    'vulnerability': [],
    'data_breach': [],
    'supply_chain': [],
    'botnet': []
}

for threat in threats:
    title = threat.get('title', '').lower()

    if 'ransomware' in title:
        categories['ransomware'].append(threat)
    if 'apt' in title or 'lazarus' in title or 'apt28' in title or 'apt29' in title:
        categories['apt'].append(threat)
    if 'zero-day' in title or '0-day' in title:
        categories['zero_day'].append(threat)
    if 'malware' in title or 'trojan' in title or 'rat' in title:
        categories['malware'].append(threat)
    if 'phish' in title:
        categories['phishing'].append(threat)
    if 'ddos' in title or 'denial-of-service' in title:
        categories['ddos'].append(threat)
    if 'vulnerability' in title or 'cve-' in title or 'exploit' in title:
        categories['vulnerability'].append(threat)
    if 'breach' in title or 'leak' in title:
        categories['data_breach'].append(threat)
    if 'supply chain' in title or 'supply-chain' in title:
        categories['supply_chain'].append(threat)
    if 'botnet' in title:
        categories['botnet'].append(threat)

# Print category breakdown
for cat, items in sorted(categories.items(), key=lambda x: len(x[1]), reverse=True):
    if items:
        print(f"   {cat.upper().replace('_', ' ')}: {len(items)} threats")

print()

# ============================================================================
# 2. SOURCE ANALYSIS
# ============================================================================
print("="*70)
print("📰 TOP THREAT INTELLIGENCE SOURCES")
print("="*70)
print()

source_counter = Counter([t.get('source', 'Unknown') for t in threats])
for source, count in source_counter.most_common(10):
    pct = (count / len(threats)) * 100
    print(f"   {source:<40} {count:>4} ({pct:>5.1f}%)")

print()

# ============================================================================
# 3. HIGH-PRIORITY THREATS
# ============================================================================
print("="*70)
print("🚨 HIGH-PRIORITY THREATS (Active Exploits & Zero-Days)")
print("="*70)
print()

high_priority_keywords = [
    'active', 'exploited', 'zero-day', '0-day', 'in the wild',
    'under attack', 'actively exploited', 'urgent'
]

high_priority = []
for threat in threats:
    title = threat.get('title', '').lower()
    if any(keyword in title for keyword in high_priority_keywords):
        high_priority.append(threat)

print(f"Found {len(high_priority)} high-priority threats\n")

for i, threat in enumerate(high_priority[:15], 1):
    title = threat.get('title', 'Unknown')
    if len(title) > 80:
        title = title[:77] + "..."
    source = threat.get('source', 'Unknown')
    print(f"{i:2}. {title}")
    print(f"    Source: {source}")
    print()

# ============================================================================
# 4. ATTACK PATTERN ANALYSIS
# ============================================================================
print("="*70)
print("🎯 ATTACK PATTERNS & TECHNIQUES")
print("="*70)
print()

attack_patterns = {
    'Social Engineering': ['phishing', 'spear phishing', 'social engineering'],
    'Exploitation': ['exploit', 'vulnerability', 'cve-'],
    'Credential Attacks': ['credential', 'password', 'brute force', 'token'],
    'Malware Delivery': ['malware', 'trojan', 'ransomware', 'rat', 'loader'],
    'Supply Chain': ['supply chain', 'npm', 'package', 'dependency'],
    'Infrastructure': ['ddos', 'dns', 'botnet', 'c2', 'command and control'],
    'Data Exfiltration': ['breach', 'leak', 'exfiltration', 'stolen'],
    'Cloud Attacks': ['cloud', 'aws', 'azure', 'gcp', 's3'],
}

pattern_counts = {}
for pattern_name, keywords in attack_patterns.items():
    count = 0
    for threat in threats:
        title = threat.get('title', '').lower()
        if any(keyword in title for keyword in keywords):
            count += 1
    pattern_counts[pattern_name] = count

for pattern, count in sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True):
    if count > 0:
        pct = (count / len(threats)) * 100
        print(f"   {pattern:<25} {count:>4} ({pct:>5.1f}%)")

print()

# ============================================================================
# 5. TARGETED SECTORS
# ============================================================================
print("="*70)
print("🏢 TARGETED SECTORS & INDUSTRIES")
print("="*70)
print()

sector_keywords = {
    'Government': ['government', 'federal', 'agency', 'military'],
    'Healthcare': ['healthcare', 'hospital', 'medical', 'health'],
    'Financial': ['bank', 'financial', 'finance', 'credit card'],
    'Technology': ['tech', 'software', 'it ', 'saas'],
    'Energy': ['energy', 'power', 'oil', 'gas', 'utility'],
    'Education': ['university', 'school', 'education', 'academic'],
    'Retail': ['retail', 'e-commerce', 'shopping'],
    'Manufacturing': ['manufacturing', 'industrial', 'factory'],
}

sector_counts = {}
for sector_name, keywords in sector_keywords.items():
    count = 0
    for threat in threats:
        title = threat.get('title', '').lower()
        if any(keyword in title for keyword in keywords):
            count += 1
    sector_counts[sector_name] = count

for sector, count in sorted(sector_counts.items(), key=lambda x: x[1], reverse=True):
    if count > 0:
        print(f"   {sector:<20} {count:>3} threats")

print()

# ============================================================================
# 6. KEY FINDINGS & RECOMMENDATIONS
# ============================================================================
print("="*70)
print("💡 KEY FINDINGS & RECOMMENDATIONS")
print("="*70)
print()

print("🔴 CRITICAL FINDINGS:")
print()

if categories['zero_day']:
    print(f"   ⚠️  {len(categories['zero_day'])} ZERO-DAY vulnerabilities detected")
    print(f"       → Immediate patching required for affected systems")
    print()

if categories['ransomware']:
    print(f"   ⚠️  {len(categories['ransomware'])} RANSOMWARE campaigns active")
    print(f"       → Ensure backups are offline and tested")
    print()

if categories['apt']:
    print(f"   ⚠️  {len(categories['apt'])} APT (Advanced Persistent Threat) activities")
    print(f"       → Review network logs for indicators of compromise")
    print()

if categories['supply_chain']:
    print(f"   ⚠️  {len(categories['supply_chain'])} SUPPLY CHAIN attacks")
    print(f"       → Audit third-party dependencies and vendors")
    print()

print()
print("📋 RECOMMENDED ACTIONS:")
print()
print("   1. Prioritize patching for actively exploited vulnerabilities")
print("   2. Implement MFA across all critical systems")
print("   3. Review and update incident response procedures")
print("   4. Conduct threat hunting for APT indicators")
print("   5. Verify backup integrity and restore procedures")
print("   6. Update EDR/XDR signatures with latest IOCs")
print("   7. Review supply chain security controls")
print()

print("="*70)
print("Analysis Complete")
print("="*70)
