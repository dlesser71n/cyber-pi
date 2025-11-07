#!/usr/bin/env python3
"""
Validate all RSS sources in sources.yaml
Tests connectivity and basic parsing
"""

import yaml
import requests
import feedparser
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import sys

def test_source(name, url, timeout=10):
    """Test a single RSS source"""
    try:
        # Try to fetch the feed
        response = requests.get(url, timeout=timeout, headers={
            'User-Agent': 'cyber-pi/1.0 (Source Validation)'
        })
        
        if response.status_code != 200:
            return {
                'name': name,
                'url': url,
                'status': 'FAIL',
                'error': f'HTTP {response.status_code}'
            }
        
        # Try to parse as RSS
        feed = feedparser.parse(response.content)
        
        if feed.bozo:  # Parse error
            return {
                'name': name,
                'url': url,
                'status': 'WARN',
                'error': f'Parse warning: {feed.bozo_exception}'
            }
        
        # Check if we got any entries
        entry_count = len(feed.entries)
        if entry_count == 0:
            return {
                'name': name,
                'url': url,
                'status': 'WARN',
                'error': 'No entries found'
            }
        
        return {
            'name': name,
            'url': url,
            'status': 'OK',
            'entries': entry_count
        }
        
    except requests.exceptions.Timeout:
        return {
            'name': name,
            'url': url,
            'status': 'FAIL',
            'error': 'Timeout'
        }
    except requests.exceptions.ConnectionError:
        return {
            'name': name,
            'url': url,
            'status': 'FAIL',
            'error': 'Connection failed'
        }
    except Exception as e:
        return {
            'name': name,
            'url': url,
            'status': 'FAIL',
            'error': str(e)[:50]
        }

def main():
    print("=" * 80)
    print("🔍 CYBER-PI SOURCE VALIDATION")
    print("=" * 80)
    print()
    
    # Load sources
    with open('config/sources.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # Collect all sources
    all_sources = []
    for category, data in config.items():
        if category != 'collection_settings' and isinstance(data, dict) and 'sources' in data:
            for source in data['sources']:
                all_sources.append({
                    'category': category,
                    'name': source['name'],
                    'url': source['url']
                })
    
    print(f"Testing {len(all_sources)} sources...")
    print()
    
    # Test sources in parallel
    results = []
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {
            executor.submit(test_source, s['name'], s['url']): s 
            for s in all_sources
        }
        
        completed = 0
        for future in as_completed(futures):
            completed += 1
            result = future.result()
            results.append(result)
            
            # Show progress
            status_icon = {
                'OK': '✅',
                'WARN': '⚠️',
                'FAIL': '❌'
            }.get(result['status'], '?')
            
            print(f"{status_icon} [{completed:3}/{len(all_sources)}] {result['name'][:50]:<50} {result['status']}")
    
    print()
    print("=" * 80)
    print("📊 VALIDATION SUMMARY")
    print("=" * 80)
    print()
    
    # Count by status
    ok = [r for r in results if r['status'] == 'OK']
    warn = [r for r in results if r['status'] == 'WARN']
    fail = [r for r in results if r['status'] == 'FAIL']
    
    print(f"✅ Working:  {len(ok):3} sources ({len(ok)/len(results)*100:.1f}%)")
    print(f"⚠️  Warnings: {len(warn):3} sources ({len(warn)/len(results)*100:.1f}%)")
    print(f"❌ Failed:   {len(fail):3} sources ({len(fail)/len(results)*100:.1f}%)")
    print(f"{'':10} {'-'*3}")
    print(f"{'Total:':10} {len(results):3} sources")
    print()
    
    # Show failures in detail
    if fail:
        print("=" * 80)
        print("❌ FAILED SOURCES")
        print("=" * 80)
        print()
        for r in fail:
            print(f"Source: {r['name']}")
            print(f"URL: {r['url']}")
            print(f"Error: {r['error']}")
            print()
    
    # Show warnings
    if warn:
        print("=" * 80)
        print("⚠️  WARNING SOURCES")
        print("=" * 80)
        print()
        for r in warn:
            print(f"Source: {r['name']}")
            print(f"URL: {r['url']}")
            print(f"Issue: {r['error']}")
            print()
    
    # Exit code based on results
    if len(ok) >= len(results) * 0.8:  # 80% success rate
        print("✅ Validation PASSED (80%+ sources working)")
        return 0
    else:
        print("⚠️  Validation WARNING (less than 80% sources working)")
        return 1

if __name__ == "__main__":
    sys.exit(main())
