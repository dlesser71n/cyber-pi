#!/usr/bin/env python3
"""
Correlation Engine - Vector + Graph Fusion
Links CVEs, IOCs, Exploits, and Threat Intelligence using:
- Neo4j for graph relationships
- Weaviate for semantic similarity
- Redis for fast data access
"""

import redis
import os
import sys
from pathlib import Path
from neo4j import GraphDatabase
import weaviate
from tqdm import tqdm
from datetime import datetime
import json

print("=" * 80)
print("🔗 CORRELATION ENGINE - VECTOR + GRAPH FUSION")
print("=" * 80)
print()

# Connect to Redis
redis_host = os.getenv('REDIS_HOST', 'redis.cyber-pi.svc.cluster.local')
redis_password = os.getenv('REDIS_PASSWORD', 'cyber-pi-redis-2025')

print(f"🔌 Connecting to Redis...")
r = redis.Redis(host=redis_host, port=6379, password=redis_password, decode_responses=True)
r.ping()
print("✅ Redis connected")

# Connect to Neo4j
neo4j_uri = os.getenv('NEO4J_URI', 'bolt://neo4j.cyber-pi.svc.cluster.local:7687')
neo4j_user = os.getenv('NEO4J_USER', 'neo4j')
neo4j_password = os.getenv('NEO4J_PASSWORD', 'cyber-pi-neo4j-2025')

print(f"🔌 Connecting to Neo4j...")
driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
driver.verify_connectivity()
print("✅ Neo4j connected")

# Connect to Weaviate
weaviate_url = os.getenv('WEAVIATE_URL', 'http://weaviate.cyber-pi.svc.cluster.local:8080')

print(f"🔌 Connecting to Weaviate...")
weaviate_client = weaviate.connect_to_custom(
    http_host=weaviate_url.replace('http://', '').split(':')[0],
    http_port=8080,
    http_secure=False,
    grpc_host=weaviate_url.replace('http://', '').split(':')[0],
    grpc_port=50051,
    grpc_secure=False
)
print("✅ Weaviate connected")
print()

# Statistics
stats = {
    'cve_ioc_links': 0,
    'cve_exploit_links': 0,
    'cve_pulse_links': 0,
    'semantic_links': 0,
    'threat_actor_links': 0
}

print("=" * 80)
print("PHASE 1: CVE → EXPLOIT CORRELATION")
print("=" * 80)
print()

# Link CVEs to Exploits (already have reverse mapping in Redis)
print("🔗 Linking CVEs to Exploits...")

# Get all CVE IDs from Neo4j
with driver.session() as session:
    result = session.run("MATCH (c:CVE) RETURN c.cve_id as cve_id LIMIT 1000")
    cve_ids = [record['cve_id'] for record in result]

print(f"📋 Processing {len(cve_ids):,} CVEs for exploit correlation...")

for cve_id in tqdm(cve_ids, desc="CVE→Exploit"):
    try:
        # Check if this CVE has exploits
        exploit_key = f"cve:exploits:{cve_id}"
        exploit_ids = r.smembers(exploit_key)
        
        if exploit_ids:
            # Create Exploit nodes and relationships in Neo4j
            with driver.session() as session:
                for exploit_id in exploit_ids:
                    session.run("""
                        MERGE (e:Exploit {exploit_id: $exploit_id})
                        WITH e
                        MATCH (c:CVE {cve_id: $cve_id})
                        MERGE (c)-[:HAS_EXPLOIT]->(e)
                    """, exploit_id=exploit_id, cve_id=cve_id)
                    stats['cve_exploit_links'] += 1
    except Exception as e:
        pass

print(f"✅ Created {stats['cve_exploit_links']:,} CVE→Exploit links")
print()

print("=" * 80)
print("PHASE 2: CVE → IOC CORRELATION")
print("=" * 80)
print()

# Link CVEs to IOCs from OTX pulses
print("🔗 Linking CVEs to IOCs via OTX pulses...")

# Get OTX pulses that mention CVEs
pulse_keys = r.keys('otx:pulse:*')
print(f"📋 Processing {len(pulse_keys):,} OTX pulses...")

for pulse_key in tqdm(pulse_keys[:1000], desc="Pulse→CVE"):  # Limit to 1000 for speed
    try:
        pulse_data = r.hgetall(pulse_key)
        pulse_id = pulse_data.get('id', '')
        pulse_name = pulse_data.get('name', '')
        pulse_desc = pulse_data.get('description', '')
        
        # Search for CVE mentions in pulse name/description
        import re
        cve_pattern = r'CVE-\d{4}-\d{4,}'
        mentioned_cves = set(re.findall(cve_pattern, pulse_name + ' ' + pulse_desc))
        
        if mentioned_cves:
            # Get IOCs for this pulse
            ioc_keys = r.keys(f'otx:ioc:*:{pulse_id}')
            
            # Link CVEs to IOCs via Pulse
            with driver.session() as session:
                for cve_id in mentioned_cves:
                    # Create Pulse node
                    session.run("""
                        MERGE (p:ThreatPulse {pulse_id: $pulse_id})
                        SET p.name = $name
                        WITH p
                        MATCH (c:CVE {cve_id: $cve_id})
                        MERGE (c)-[:MENTIONED_IN]->(p)
                    """, pulse_id=pulse_id, name=pulse_name[:200], cve_id=cve_id)
                    stats['cve_pulse_links'] += 1
                    
                    # Link IOCs to Pulse
                    for ioc_key in ioc_keys[:10]:  # Limit IOCs per pulse
                        ioc_value = ioc_key.split(':')[-1]
                        session.run("""
                            MERGE (i:IOC {value: $ioc_value})
                            WITH i
                            MATCH (p:ThreatPulse {pulse_id: $pulse_id})
                            MERGE (p)-[:HAS_IOC]->(i)
                        """, ioc_value=ioc_value, pulse_id=pulse_id)
                        stats['cve_ioc_links'] += 1
    except Exception as e:
        pass

print(f"✅ Created {stats['cve_pulse_links']:,} CVE→Pulse links")
print(f"✅ Created {stats['cve_ioc_links']:,} Pulse→IOC links")
print()

print("=" * 80)
print("PHASE 3: SEMANTIC SIMILARITY (VECTOR)")
print("=" * 80)
print()

# Find semantically similar CVEs using Weaviate
print("🔍 Finding semantically similar CVEs...")

try:
    cve_collection = weaviate_client.collections.get("CVE")
    
    # Sample 100 CVEs and find their nearest neighbors
    sample_cves = cve_ids[:100]
    
    for cve_id in tqdm(sample_cves, desc="Semantic Links"):
        try:
            # Query Weaviate for similar CVEs
            response = cve_collection.query.near_text(
                query=cve_id,
                limit=5,
                return_metadata=['distance']
            )
            
            # Create similarity relationships in Neo4j
            if response.objects:
                with driver.session() as session:
                    for obj in response.objects:
                        similar_cve_id = obj.properties.get('cve_id')
                        distance = obj.metadata.distance if hasattr(obj.metadata, 'distance') else 0.5
                        similarity = 1.0 - distance
                        
                        if similar_cve_id and similar_cve_id != cve_id and similarity > 0.7:
                            session.run("""
                                MATCH (c1:CVE {cve_id: $cve_id1})
                                MATCH (c2:CVE {cve_id: $cve_id2})
                                MERGE (c1)-[r:SIMILAR_TO]->(c2)
                                SET r.similarity = $similarity
                            """, cve_id1=cve_id, cve_id2=similar_cve_id, similarity=similarity)
                            stats['semantic_links'] += 1
        except Exception as e:
            pass
    
    print(f"✅ Created {stats['semantic_links']:,} semantic similarity links")
except Exception as e:
    print(f"⚠️  Semantic linking: {e}")

print()

print("=" * 80)
print("PHASE 4: THREAT ACTOR ATTRIBUTION")
print("=" * 80)
print()

# Extract threat actors from OTX pulses
print("🎭 Extracting threat actor attribution...")

for pulse_key in tqdm(pulse_keys[:500], desc="Threat Actors"):
    try:
        pulse_data = r.hgetall(pulse_key)
        pulse_id = pulse_data.get('id', '')
        pulse_name = pulse_data.get('name', '')
        tags = pulse_data.get('tags', '').split(',')
        
        # Common threat actor keywords
        actor_keywords = ['apt', 'lazarus', 'fancy bear', 'cozy bear', 'equation', 
                         'turla', 'carbanak', 'fin7', 'fin8', 'wizard spider', 
                         'sandworm', 'kimsuky', 'mustang panda']
        
        # Check if pulse mentions threat actors
        detected_actors = []
        for keyword in actor_keywords:
            if keyword in pulse_name.lower() or keyword in ' '.join(tags).lower():
                detected_actors.append(keyword.title())
        
        if detected_actors:
            with driver.session() as session:
                for actor in detected_actors:
                    # Create ThreatActor node
                    session.run("""
                        MERGE (a:ThreatActor {name: $actor})
                        WITH a
                        MATCH (p:ThreatPulse {pulse_id: $pulse_id})
                        MERGE (a)-[:PUBLISHED]->(p)
                    """, actor=actor, pulse_id=pulse_id)
                    stats['threat_actor_links'] += 1
    except Exception as e:
        pass

print(f"✅ Created {stats['threat_actor_links']:,} threat actor links")
print()

print("=" * 80)
print("PHASE 5: GRAPH ENRICHMENT")
print("=" * 80)
print()

# Add metadata and computed properties
print("📊 Computing graph metrics...")

with driver.session() as session:
    # Count exploits per CVE
    session.run("""
        MATCH (c:CVE)-[:HAS_EXPLOIT]->(e:Exploit)
        WITH c, count(e) as exploit_count
        SET c.exploit_count = exploit_count
    """)
    
    # Count IOCs per CVE (via pulses)
    session.run("""
        MATCH (c:CVE)-[:MENTIONED_IN]->(p:ThreatPulse)-[:HAS_IOC]->(i:IOC)
        WITH c, count(DISTINCT i) as ioc_count
        SET c.ioc_count = ioc_count
    """)
    
    # Mark weaponized CVEs (have exploits)
    session.run("""
        MATCH (c:CVE)-[:HAS_EXPLOIT]->()
        SET c.weaponized = true
    """)
    
    print("✅ Graph enrichment complete")

print()

# Final statistics
print("=" * 80)
print("✅ CORRELATION ENGINE COMPLETE")
print("=" * 80)
print()
print("📊 Correlation Statistics:")
print(f"   CVE → Exploit links: {stats['cve_exploit_links']:,}")
print(f"   CVE → Pulse links: {stats['cve_pulse_links']:,}")
print(f"   Pulse → IOC links: {stats['cve_ioc_links']:,}")
print(f"   Semantic similarity links: {stats['semantic_links']:,}")
print(f"   Threat actor links: {stats['threat_actor_links']:,}")
print(f"   Total relationships: {sum(stats.values()):,}")
print()

# Store correlation metadata
r.hset('correlation:stats', mapping={
    'cve_exploit_links': stats['cve_exploit_links'],
    'cve_pulse_links': stats['cve_pulse_links'],
    'cve_ioc_links': stats['cve_ioc_links'],
    'semantic_links': stats['semantic_links'],
    'threat_actor_links': stats['threat_actor_links'],
    'timestamp': datetime.utcnow().isoformat()
})

# Verify graph
print("🔍 Graph Verification:")
with driver.session() as session:
    result = session.run("""
        MATCH (c:CVE) 
        OPTIONAL MATCH (c)-[:HAS_EXPLOIT]->(e:Exploit)
        OPTIONAL MATCH (c)-[:MENTIONED_IN]->(p:ThreatPulse)
        OPTIONAL MATCH (c)-[:SIMILAR_TO]->(s:CVE)
        RETURN 
            count(DISTINCT c) as cves,
            count(DISTINCT e) as exploits,
            count(DISTINCT p) as pulses,
            count(DISTINCT s) as similar_cves
    """)
    
    record = result.single()
    print(f"   CVE nodes: {record['cves']:,}")
    print(f"   Exploit nodes: {record['exploits']:,}")
    print(f"   Pulse nodes: {record['pulses']:,}")
    print(f"   Similar CVE links: {record['similar_cves']:,}")

print()
print("✅ Correlation engine ready for threat hunting!")

# Cleanup
driver.close()
weaviate_client.close()
r.close()
