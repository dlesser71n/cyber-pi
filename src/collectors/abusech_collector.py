#!/usr/bin/env python3
"""
Abuse.ch Collector
Collects malicious URLs, malware samples, and threat intel from Abuse.ch feeds
- URLhaus: Malicious URLs
- MalwareBazaar: Malware samples
- ThreatFox: IOCs
"""

import asyncio
import aiohttp
import redis
import json
import os
from datetime import datetime
from tqdm import tqdm

print("=" * 80)
print("🦠 ABUSE.CH COLLECTOR")
print("=" * 80)
print()

# Connect to Redis
redis_host = os.getenv('REDIS_HOST', 'redis.cyber-pi.svc.cluster.local')
redis_password = os.getenv('REDIS_PASSWORD', 'cyber-pi-redis-2025')

print(f"🔌 Connecting to Redis...")
r = redis.Redis(host=redis_host, port=6379, password=redis_password, decode_responses=True)
r.ping()
print("✅ Redis connected")
print()

async def fetch_urlhaus(session):
    """Fetch malicious URLs from URLhaus"""
    url = "https://urlhaus-api.abuse.ch/v1/urls/recent/"
    
    print("📡 Fetching URLhaus data...")
    try:
        async with session.post(url) as response:
            if response.status == 200:
                data = await response.json()
                urls = data.get('urls', [])
                print(f"✅ Fetched {len(urls):,} malicious URLs")
                return urls
    except Exception as e:
        print(f"❌ URLhaus error: {e}")
    
    return []

async def fetch_malwarebazaar(session):
    """Fetch recent malware samples from MalwareBazaar"""
    url = "https://mb-api.abuse.ch/api/v1/"
    
    print("📡 Fetching MalwareBazaar data...")
    try:
        payload = {'query': 'get_recent', 'selector': '100'}
        async with session.post(url, data=payload) as response:
            if response.status == 200:
                data = await response.json()
                samples = data.get('data', [])
                print(f"✅ Fetched {len(samples):,} malware samples")
                return samples
    except Exception as e:
        print(f"❌ MalwareBazaar error: {e}")
    
    return []

async def fetch_threatfox(session):
    """Fetch IOCs from ThreatFox"""
    url = "https://threatfox-api.abuse.ch/api/v1/"
    
    print("📡 Fetching ThreatFox data...")
    try:
        payload = {'query': 'get_iocs', 'days': 7}
        async with session.post(url, json=payload) as response:
            if response.status == 200:
                data = await response.json()
                iocs = data.get('data', [])
                print(f"✅ Fetched {len(iocs):,} IOCs")
                return iocs
    except Exception as e:
        print(f"❌ ThreatFox error: {e}")
    
    return []

async def main():
    async with aiohttp.ClientSession() as session:
        # Fetch all data sources
        urlhaus_data = await fetch_urlhaus(session)
        malware_data = await fetch_malwarebazaar(session)
        threatfox_data = await fetch_threatfox(session)
        print()
        
        # Store URLhaus data
        print("💾 Storing URLhaus URLs...")
        stored_urls = 0
        for url_entry in tqdm(urlhaus_data, desc="URLhaus"):
            try:
                url_id = url_entry.get('id')
                url_key = f"abuse:urlhaus:{url_id}"
                
                r.hset(url_key, mapping={
                    'id': url_id,
                    'url': url_entry.get('url', '')[:500],
                    'url_status': url_entry.get('url_status', ''),
                    'threat': url_entry.get('threat', ''),
                    'tags': ','.join(url_entry.get('tags', [])),
                    'date_added': url_entry.get('date_added', ''),
                    'reporter': url_entry.get('reporter', ''),
                    'source': 'abuse.ch_urlhaus'
                })
                stored_urls += 1
            except Exception as e:
                pass
        
        # Store MalwareBazaar data
        print("💾 Storing MalwareBazaar samples...")
        stored_malware = 0
        for sample in tqdm(malware_data, desc="MalwareBazaar"):
            try:
                sha256 = sample.get('sha256_hash', '')
                if sha256:
                    malware_key = f"abuse:malware:{sha256}"
                    
                    r.hset(malware_key, mapping={
                        'sha256': sha256,
                        'md5': sample.get('md5_hash', ''),
                        'sha1': sample.get('sha1_hash', ''),
                        'file_name': sample.get('file_name', ''),
                        'file_type': sample.get('file_type', ''),
                        'file_size': str(sample.get('file_size', '')),
                        'signature': sample.get('signature', ''),
                        'tags': ','.join(sample.get('tags', [])),
                        'first_seen': sample.get('first_seen', ''),
                        'source': 'abuse.ch_malwarebazaar'
                    })
                    stored_malware += 1
            except Exception as e:
                pass
        
        # Store ThreatFox IOCs
        print("💾 Storing ThreatFox IOCs...")
        stored_iocs = 0
        for ioc in tqdm(threatfox_data, desc="ThreatFox"):
            try:
                ioc_id = ioc.get('id')
                ioc_key = f"abuse:threatfox:{ioc_id}"
                
                r.hset(ioc_key, mapping={
                    'id': ioc_id,
                    'ioc': ioc.get('ioc', ''),
                    'ioc_type': ioc.get('ioc_type', ''),
                    'threat_type': ioc.get('threat_type', ''),
                    'malware': ioc.get('malware', ''),
                    'malware_alias': ioc.get('malware_alias', ''),
                    'confidence_level': str(ioc.get('confidence_level', '')),
                    'first_seen': ioc.get('first_seen', ''),
                    'tags': ','.join(ioc.get('tags', [])),
                    'source': 'abuse.ch_threatfox'
                })
                stored_iocs += 1
            except Exception as e:
                pass
        
        print()
        print("=" * 80)
        print("✅ ABUSE.CH COLLECTION COMPLETE")
        print("=" * 80)
        print(f"   URLhaus URLs: {stored_urls:,}")
        print(f"   Malware samples: {stored_malware:,}")
        print(f"   ThreatFox IOCs: {stored_iocs:,}")
        print(f"   Total: {stored_urls + stored_malware + stored_iocs:,}")
        print()
        
        # Store metadata
        r.set('abuse:import:urlhaus', stored_urls)
        r.set('abuse:import:malware', stored_malware)
        r.set('abuse:import:iocs', stored_iocs)
        r.set('abuse:import:timestamp', datetime.utcnow().isoformat())

if __name__ == "__main__":
    asyncio.run(main())
