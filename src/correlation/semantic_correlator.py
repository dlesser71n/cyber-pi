#!/usr/bin/env python3
"""
Semantic Correlator - Perfect Vector Similarity
Uses Weaviate to find semantically similar CVEs based on descriptions
Creates SIMILAR_TO relationships in Neo4j with similarity scores
"""

import redis
import os
from neo4j import GraphDatabase
import weaviate
from weaviate.classes.query import MetadataQuery
from tqdm import tqdm
from datetime import datetime

print("=" * 80)
print("🔍 SEMANTIC CORRELATOR - VECTOR SIMILARITY")
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

# Get CVE collection
print("📊 Checking Weaviate CVE collection...")
cve_collection = weaviate_client.collections.get("CVE")

# Get total count
result = cve_collection.aggregate.over_all(total_count=True)
total_cves = result.total_count
print(f"✅ Found {total_cves:,} CVEs in Weaviate")
print()

# Strategy: Sample CVEs and find their nearest neighbors
print("=" * 80)
print("SEMANTIC SIMILARITY ANALYSIS")
print("=" * 80)
print()

# Configuration
SAMPLE_SIZE = 500  # Number of CVEs to analyze
NEIGHBORS = 10     # Top N similar CVEs per CVE
MIN_SIMILARITY = 0.75  # Minimum similarity threshold (0-1)

print(f"📋 Configuration:")
print(f"   Sample size: {SAMPLE_SIZE:,} CVEs")
print(f"   Neighbors per CVE: {NEIGHBORS}")
print(f"   Similarity threshold: {MIN_SIMILARITY}")
print()

# Get sample of CVEs from Neo4j (prioritize high CVSS scores)
print("📋 Selecting high-value CVEs for analysis...")
with driver.session() as session:
    result = session.run("""
        MATCH (c:CVE)
        WHERE c.cvss_v3_score IS NOT NULL
        RETURN c.cve_id as cve_id, c.description as description, c.cvss_v3_score as score
        ORDER BY c.cvss_v3_score DESC
        LIMIT $limit
    """, limit=SAMPLE_SIZE)
    
    sample_cves = [(record['cve_id'], record['description'], record['score']) 
                   for record in result]

print(f"✅ Selected {len(sample_cves):,} CVEs (avg CVSS: {sum(s[2] for s in sample_cves)/len(sample_cves):.1f})")
print()

# Find semantic similarities
print("🔍 Finding semantic similarities...")
print()

similarity_links = []
errors = 0

for cve_id, description, cvss_score in tqdm(sample_cves, desc="Analyzing CVEs"):
    try:
        # Query Weaviate for similar CVEs using description
        response = cve_collection.query.near_text(
            query=description[:500] if description else cve_id,  # Use description or CVE ID
            limit=NEIGHBORS + 1,  # +1 because it includes itself
            return_metadata=MetadataQuery(distance=True)
        )
        
        if response.objects:
            for obj in response.objects:
                similar_cve_id = obj.properties.get('cve_id')
                
                # Skip self-matches
                if similar_cve_id == cve_id:
                    continue
                
                # Calculate similarity score (distance -> similarity)
                distance = obj.metadata.distance if hasattr(obj.metadata, 'distance') else 1.0
                similarity = 1.0 - distance
                
                # Only keep high similarity matches
                if similarity >= MIN_SIMILARITY:
                    similarity_links.append({
                        'source': cve_id,
                        'target': similar_cve_id,
                        'similarity': similarity,
                        'source_cvss': cvss_score
                    })
        
    except Exception as e:
        errors += 1
        if errors <= 5:
            print(f"\n⚠️  Error processing {cve_id}: {e}")

print()
print(f"✅ Found {len(similarity_links):,} semantic similarity relationships")
print(f"   Errors: {errors}")
print()

# Analyze similarity distribution
if similarity_links:
    similarities = [link['similarity'] for link in similarity_links]
    print("📊 Similarity Distribution:")
    print(f"   Min: {min(similarities):.3f}")
    print(f"   Max: {max(similarities):.3f}")
    print(f"   Avg: {sum(similarities)/len(similarities):.3f}")
    print()

# Create relationships in Neo4j
print("🔗 Creating SIMILAR_TO relationships in Neo4j...")

batch_size = 100
created = 0

with driver.session() as session:
    for i in tqdm(range(0, len(similarity_links), batch_size), desc="Creating links"):
        batch = similarity_links[i:i + batch_size]
        
        # Batch create relationships
        session.run("""
            UNWIND $links as link
            MATCH (c1:CVE {cve_id: link.source})
            MATCH (c2:CVE {cve_id: link.target})
            MERGE (c1)-[r:SIMILAR_TO]->(c2)
            SET r.similarity = link.similarity,
                r.method = 'vector_embedding',
                r.created_at = datetime()
        """, links=batch)
        
        created += len(batch)

print(f"✅ Created {created:,} SIMILAR_TO relationships")
print()

# Verify and analyze the graph
print("=" * 80)
print("GRAPH ANALYSIS")
print("=" * 80)
print()

with driver.session() as session:
    # Count similar relationships
    result = session.run("""
        MATCH ()-[r:SIMILAR_TO]->()
        RETURN count(r) as total,
               avg(r.similarity) as avg_similarity,
               min(r.similarity) as min_similarity,
               max(r.similarity) as max_similarity
    """)
    
    record = result.single()
    print(f"📊 Similarity Relationships:")
    print(f"   Total: {record['total']:,}")
    print(f"   Avg similarity: {record['avg_similarity']:.3f}")
    print(f"   Min similarity: {record['min_similarity']:.3f}")
    print(f"   Max similarity: {record['max_similarity']:.3f}")
    print()
    
    # Find CVEs with most similar neighbors
    result = session.run("""
        MATCH (c:CVE)-[r:SIMILAR_TO]->()
        WITH c, count(r) as similar_count, avg(r.similarity) as avg_sim
        ORDER BY similar_count DESC
        LIMIT 10
        RETURN c.cve_id as cve_id, 
               c.cvss_v3_score as cvss,
               similar_count,
               avg_sim
    """)
    
    print("🔝 Top 10 CVEs by similarity connections:")
    for record in result:
        print(f"   {record['cve_id']}: {record['similar_count']} similar CVEs (avg sim: {record['avg_sim']:.3f}, CVSS: {record['cvss']})")
    print()
    
    # Find similarity clusters (CVEs that are mutually similar)
    result = session.run("""
        MATCH (c1:CVE)-[r1:SIMILAR_TO]->(c2:CVE)-[r2:SIMILAR_TO]->(c1)
        WHERE r1.similarity > 0.85 AND r2.similarity > 0.85
        RETURN count(*) as mutual_pairs
    """)
    
    record = result.single()
    print(f"🔄 Mutual similarity pairs (>0.85): {record['mutual_pairs']:,}")
    print()

# Store metadata
r.hset('semantic:stats', mapping={
    'total_analyzed': len(sample_cves),
    'links_created': created,
    'avg_similarity': sum(similarities)/len(similarities) if similarities else 0,
    'min_threshold': MIN_SIMILARITY,
    'timestamp': datetime.utcnow().isoformat()
})

print("=" * 80)
print("✅ SEMANTIC CORRELATION COMPLETE")
print("=" * 80)
print()
print(f"📊 Summary:")
print(f"   CVEs analyzed: {len(sample_cves):,}")
print(f"   Similarity links: {created:,}")
print(f"   Avg similarity: {sum(similarities)/len(similarities):.3f}" if similarities else "   Avg similarity: N/A")
print()
print("🎯 Use cases enabled:")
print("   - Find CVEs with similar attack patterns")
print("   - Cluster vulnerabilities by semantic similarity")
print("   - Predict exploitation based on similar CVEs")
print("   - Identify vulnerability families")
print()

# Cleanup
driver.close()
weaviate_client.close()
r.close()

print("✅ Done!")
