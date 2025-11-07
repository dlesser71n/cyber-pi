#!/usr/bin/env python3
"""
Clean up sources.yaml to only include working sources
"""

import yaml
import requests
import feedparser

def test_source(url, timeout=10):
    """Quick test if source works"""
    try:
        response = requests.get(url, timeout=timeout, headers={
            'User-Agent': 'cyber-pi/1.0'
        })
        if response.status_code != 200:
            return False
        feed = feedparser.parse(response.content)
        return len(feed.entries) > 0
    except:
        return False

# Load current config
with open('config/sources.yaml', 'r') as f:
    config = yaml.safe_load(f)

working_sources = []
broken_sources = []

print("Testing sources...")

for category, data in config.items():
    if category == 'collection_settings':
        continue
    if not isinstance(data, dict) or 'sources' not in data:
        continue
    
    cleaned_sources = []
    for source in data['sources']:
        name = source['name']
        url = source['url']
        
        print(f"Testing {name}...", end=" ")
        if test_source(url):
            print("✅ OK")
            cleaned_sources.append(source)
            working_sources.append(name)
        else:
            print("❌ FAIL")
            broken_sources.append((name, url))
    
    # Update category with only working sources
    if cleaned_sources:
        data['sources'] = cleaned_sources

# Save cleaned config
with open('config/sources_cleaned.yaml', 'w') as f:
    yaml.dump(config, f, default_flow_style=False, allow_unicode=True)

print()
print(f"✅ Working: {len(working_sources)}")
print(f"❌ Broken: {len(broken_sources)}")
print()
print("Cleaned config saved to: config/sources_cleaned.yaml")
