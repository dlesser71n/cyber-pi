#!/usr/bin/env python3
"""
AlienVault OTX (Open Threat Exchange) Collector
Collects threat intelligence pulses and IOCs
"""

import asyncio
import aiohttp
import redis
import json
import os
from datetime import datetime
from tqdm import tqdm

print("=" * 80)
print("🔍 ALIENVAULT OTX COLLECTOR")
print("=" * 80)
print()

# Configuration
OTX_API_KEY = os.getenv('OTX_API_KEY', '')
OTX_BASE_URL = "https://otx.alienvault.com/api/v1"

if not OTX_API_KEY:
    print("❌ OTX_API_KEY environment variable not set!")
    print("   Sign up at https://otx.alienvault.com/")
    print("   Then set: export OTX_API_KEY='your_key_here'")
    exit(1)

# Connect to Redis
redis_host = os.getenv('REDIS_HOST', 'redis.cyber-pi.svc.cluster.local')
redis_password = os.getenv('REDIS_PASSWORD', 'cyber-pi-redis-2025')

print(f"🔌 Connecting to Redis...")
r = redis.Redis(host=redis_host, port=6379, password=redis_password, decode_responses=True)
r.ping()
print("✅ Redis connected")
print()

async def fetch_subscribed_pulses(session):
    """Fetch pulses from subscribed feeds"""
    headers = {'X-OTX-API-KEY': OTX_API_KEY}
    pulses = []
    page = 1
    
    print("📡 Fetching subscribed pulses...")
    
    while True:
        url = f"{OTX_BASE_URL}/pulses/subscribed"
        params = {'page': page, 'limit': 50}
        
        try:
            async with session.get(url, headers=headers, params=params) as response:
                if response.status != 200:
                    print(f"⚠️  HTTP {response.status}")
                    break
                
                data = await response.json()
                results = data.get('results', [])
                
                if not results:
                    break
                
                pulses.extend(results)
                print(f"   Page {page}: {len(results)} pulses")
                page += 1
                
                if page > 100:  # Safety limit
                    break
                
        except Exception as e:
            print(f"❌ Error: {e}")
            break
    
    return pulses

async def fetch_pulse_indicators(session, pulse_id):
    """Fetch indicators for a specific pulse"""
    headers = {'X-OTX-API-KEY': OTX_API_KEY}
    url = f"{OTX_BASE_URL}/pulses/{pulse_id}/indicators"
    
    try:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                return data.get('results', [])
    except:
        pass
    
    return []

async def main():
    async with aiohttp.ClientSession() as session:
        # Fetch pulses
        pulses = await fetch_subscribed_pulses(session)
        print(f"✅ Fetched {len(pulses):,} pulses")
        print()
        
        # Store pulses and collect IOCs
        print("💾 Storing pulses and IOCs in Redis...")
        stored_pulses = 0
        stored_iocs = 0
        
        for pulse in tqdm(pulses, desc="Processing pulses"):
            try:
                pulse_id = pulse.get('id')
                
                # Store pulse metadata
                pulse_key = f"otx:pulse:{pulse_id}"
                pulse_data = {
                    'id': pulse_id,
                    'name': pulse.get('name', ''),
                    'description': pulse.get('description', '')[:1000],
                    'author': pulse.get('author_name', ''),
                    'created': pulse.get('created', ''),
                    'modified': pulse.get('modified', ''),
                    'tags': ','.join(pulse.get('tags', [])),
                    'references': ','.join(pulse.get('references', []))[:500],
                    'targeted_countries': ','.join(pulse.get('targeted_countries', [])),
                    'industries': ','.join(pulse.get('industries', [])),
                    'source': 'otx'
                }
                
                r.hset(pulse_key, mapping=pulse_data)
                stored_pulses += 1
                
                # Store indicators (IOCs)
                indicators = pulse.get('indicators', [])
                for indicator in indicators:
                    ioc_type = indicator.get('type', '')
                    ioc_value = indicator.get('indicator', '')
                    
                    if ioc_type and ioc_value:
                        # Store IOC with reference to pulse
                        ioc_key = f"otx:ioc:{ioc_type}:{ioc_value}"
                        r.sadd(ioc_key, pulse_id)
                        
                        # Store IOC metadata
                        ioc_meta_key = f"otx:ioc:meta:{ioc_value}"
                        r.hset(ioc_meta_key, mapping={
                            'type': ioc_type,
                            'value': ioc_value,
                            'created': indicator.get('created', ''),
                            'source': 'otx'
                        })
                        stored_iocs += 1
                
            except Exception as e:
                print(f"\n⚠️  Error processing pulse {pulse.get('id')}: {e}")
        
        print()
        print("=" * 80)
        print("✅ OTX COLLECTION COMPLETE")
        print("=" * 80)
        print(f"   Pulses stored: {stored_pulses:,}")
        print(f"   IOCs stored: {stored_iocs:,}")
        print()
        
        # Store metadata
        r.set('otx:import:total_pulses', stored_pulses)
        r.set('otx:import:total_iocs', stored_iocs)
        r.set('otx:import:timestamp', datetime.utcnow().isoformat())

if __name__ == "__main__":
    asyncio.run(main())
