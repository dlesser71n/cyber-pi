#!/usr/bin/env python3
"""
Simple: Just parse threats and store in Redis
Then batch process to Weaviate/Neo4j later
"""

import json
import sys
import hashlib
import re
from datetime import datetime, timezone

# Test Redis connection first
import subprocess
result = subprocess.run(
    ['redis-cli', '-h', 'localhost', '-p', '6379', '-a', 'cyber-pi-redis-2025', 'ping'],
    capture_output=True,
    text=True
)

if 'PONG' not in result.stdout:
    print("❌ Redis not accessible. Start port forward:")
    print("  microk8s kubectl port-forward -n cyber-pi-intel svc/redis 6379:6379")
    sys.exit(1)

print("✅ Redis connected")

def parse_cyber_pi_item(item):
    """Quick parse of cyber-pi threat"""
    threat_id = item.get('id', hashlib.sha256(
        (item.get('title', '') + item.get('link', '')).encode()
    ).hexdigest()[:16])
    
    content = item.get('content', '')
    title = item.get('title', 'Unknown Threat')
    
    # Extract CVEs
    cves = list(set(re.findall(r'CVE-\d{4}-\d{4,7}', content, re.IGNORECASE)))
    
    # Simple severity
    text_lower = (title + ' ' + content).lower()
    if any(k in text_lower for k in ['critical', 'severe', 'zero-day']):
        severity = 'critical'
    elif any(k in text_lower for k in ['high', 'important']):
        severity = 'high'
    else:
        severity = 'medium'
    
    return {
        "threatId": f"threat_{threat_id}",
        "title": title,
        "content": content[:5000],
        "source": item.get('source', 'cyber-pi'),
        "sourceUrl": item.get('link', ''),
        "severity": severity,
        "cves": cves,
        "publishedDate": item.get('published', datetime.now(timezone.utc).isoformat()),
        "ingestedDate": datetime.now(timezone.utc).isoformat(),
        "tags": item.get('tags', [])
    }

def main():
    print("="*60)
    print("🔥 QUICK INGESTION TO REDIS")
    print("Parse all threats → Store in Redis")
    print("="*60)
    print()
    
    # Load data
    filepath = "/home/david/projects/cyber-pi/data/raw/master_collection_20251031_014039.json"
    print(f"📁 Loading: {filepath}")
    
    with open(filepath) as f:
        data = json.load(f)
    
    items = data['items']
    print(f"📊 Found {len(items)} threats")
    print()
    
    # Process each
    print("🚀 Storing in Redis...")
    success = 0
    failed = 0
    
    for i, item in enumerate(items):
        if (i + 1) % 100 == 0:
            print(f"  Progress: {i+1}/{len(items)} ({(i+1)/len(items)*100:.1f}%)")
        
        try:
            # Parse
            threat = parse_cyber_pi_item(item)
            threat_id = threat['threatId']
            
            # Store in Redis with 24 hour TTL
            cmd = [
                'redis-cli', '-h', 'localhost', '-p', '6379',
                '-a', 'cyber-pi-redis-2025',
                'SETEX', f'threat:{threat_id}', '86400', json.dumps(threat)
            ]
            
            result = subprocess.run(cmd, capture_output=True)
            if result.returncode == 0:
                success += 1
            else:
                failed += 1
                
        except Exception as e:
            print(f"  ✗ Failed: {e}")
            failed += 1
    
    print()
    print("="*60)
    print("📊 INGESTION COMPLETE")
    print("="*60)
    print(f"Total:     {len(items)}")
    print(f"Success:   {success}")
    print(f"Failed:    {failed}")
    print(f"Rate:      {success/len(items)*100:.1f}%")
    print()
    print("✅ All threats cached in Redis!")
    print()
    print("Next: Run batch processor to move to Weaviate/Neo4j")
    print()

if __name__ == "__main__":
    main()
