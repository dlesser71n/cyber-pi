#!/usr/bin/env python3
"""
Hybrid Query Engine - Graph + Vector + Text Fusion
Combines Neo4j (graph), Weaviate (vector), and Redis (text) for advanced threat intelligence queries
"""

import redis
from neo4j import GraphDatabase
import weaviate
from weaviate.classes.query import MetadataQuery
import json
from typing import List, Dict, Any
from datetime import datetime

class HybridQueryEngine:
    """
    Advanced query engine combining:
    - Neo4j: Graph traversal and relationship queries
    - Weaviate: Semantic similarity and vector search
    - Redis: Fast key-value lookups and text search
    """
    
    def __init__(self):
        # Connect to Redis
        self.redis = redis.Redis(
            host='redis.cyber-pi.svc.cluster.local',
            port=6379,
            password='cyber-pi-redis-2025',
            decode_responses=True
        )
        
        # Connect to Neo4j
        self.neo4j = GraphDatabase.driver(
            'bolt://neo4j.cyber-pi.svc.cluster.local:7687',
            auth=('neo4j', 'cyber-pi-neo4j-2025')
        )
        
        # Connect to Weaviate
        self.weaviate = weaviate.connect_to_custom(
            http_host='weaviate.cyber-pi.svc.cluster.local',
            http_port=8080,
            http_secure=False,
            grpc_host='weaviate.cyber-pi.svc.cluster.local',
            grpc_port=50051,
            grpc_secure=False
        )
        
        self.cve_collection = self.weaviate.collections.get("CVE")
    
    def query_1_semantic_then_graph(self, query_text: str, limit: int = 10) -> Dict[str, Any]:
        """
        Query 1: Semantic Search → Graph Expansion
        
        1. Find semantically similar CVEs using vector search (Weaviate)
        2. Expand to related entities using graph traversal (Neo4j)
        3. Enrich with metadata from Redis
        
        Use case: "Find CVEs similar to 'remote code execution in web servers' 
                   and show their exploits and threat actors"
        """
        print(f"\n{'='*80}")
        print(f"QUERY 1: SEMANTIC → GRAPH EXPANSION")
        print(f"{'='*80}")
        print(f"Query: {query_text}")
        print()
        
        # Step 1: Vector search in Weaviate
        print("🔍 Step 1: Semantic search in Weaviate...")
        response = self.cve_collection.query.near_text(
            query=query_text,
            limit=limit,
            return_metadata=MetadataQuery(distance=True)
        )
        
        cve_ids = [obj.properties.get('cve_id') for obj in response.objects if obj.properties.get('cve_id')]
        print(f"   Found {len(cve_ids)} semantically similar CVEs")
        
        # Step 2: Graph expansion in Neo4j
        print("🕸️  Step 2: Graph expansion in Neo4j...")
        with self.neo4j.session() as session:
            result = session.run("""
                UNWIND $cve_ids as cve_id
                MATCH (c:CVE {cve_id: cve_id})
                OPTIONAL MATCH (c)-[:HAS_EXPLOIT]->(e:Exploit)
                OPTIONAL MATCH (c)-[:MENTIONED_IN]->(p:ThreatPulse)<-[:PUBLISHED]-(a:ThreatActor)
                OPTIONAL MATCH (c)-[:AFFECTS_VENDOR]->(v:Vendor)
                OPTIONAL MATCH (c)-[:HAS_WEAKNESS]->(w:CWE)
                RETURN c.cve_id as cve_id,
                       c.description as description,
                       c.cvss_v3_score as cvss,
                       collect(DISTINCT e.exploit_id) as exploits,
                       collect(DISTINCT a.name) as threat_actors,
                       collect(DISTINCT v.name) as vendors,
                       collect(DISTINCT w.cwe_id) as cwes
            """, cve_ids=cve_ids)
            
            results = []
            for record in result:
                # Step 3: Enrich with Redis metadata
                cve_id = record['cve_id']
                redis_data = self.redis.hgetall(f"nvd:cve:{cve_id}")
                
                results.append({
                    'cve_id': cve_id,
                    'description': record['description'][:200] + '...',
                    'cvss_score': record['cvss'],
                    'exploits': [e for e in record['exploits'] if e],
                    'threat_actors': [a for a in record['threat_actors'] if a],
                    'vendors': record['vendors'][:5],  # Top 5 vendors
                    'cwes': record['cwes'][:3],  # Top 3 CWEs
                    'published': redis_data.get('published', 'N/A')
                })
        
        print(f"   Expanded to {len(results)} enriched results")
        return {'query': query_text, 'results': results, 'count': len(results)}
    
    def query_2_graph_then_vector(self, start_cve: str, hops: int = 2) -> Dict[str, Any]:
        """
        Query 2: Graph Traversal → Vector Clustering
        
        1. Start from a CVE and traverse graph relationships (Neo4j)
        2. Cluster related CVEs by semantic similarity (Weaviate)
        3. Identify vulnerability families
        
        Use case: "Starting from CVE-2024-1234, find all related CVEs through 
                   exploits and threat actors, then cluster by similarity"
        """
        print(f"\n{'='*80}")
        print(f"QUERY 2: GRAPH TRAVERSAL → VECTOR CLUSTERING")
        print(f"{'='*80}")
        print(f"Start CVE: {start_cve}, Hops: {hops}")
        print()
        
        # Step 1: Graph traversal
        print("🕸️  Step 1: Graph traversal...")
        with self.neo4j.session() as session:
            result = session.run("""
                MATCH path = (start:CVE {cve_id: $start_cve})-[*1..$hops]-(related:CVE)
                WHERE start <> related
                RETURN DISTINCT related.cve_id as cve_id,
                       related.description as description,
                       related.cvss_v3_score as cvss,
                       length(path) as distance
                ORDER BY distance, cvss DESC
                LIMIT 50
            """, start_cve=start_cve, hops=hops)
            
            related_cves = [{'cve_id': r['cve_id'], 'description': r['description'], 
                           'cvss': r['cvss'], 'distance': r['distance']} for r in result]
        
        print(f"   Found {len(related_cves)} related CVEs")
        
        # Step 2: Vector clustering
        print("🔍 Step 2: Semantic clustering...")
        clusters = {}
        
        for cve in related_cves[:20]:  # Limit for performance
            try:
                # Find similar CVEs
                response = self.cve_collection.query.near_text(
                    query=cve['description'][:500] if cve['description'] else cve['cve_id'],
                    limit=5,
                    return_metadata=MetadataQuery(distance=True)
                )
                
                similar_ids = [obj.properties.get('cve_id') for obj in response.objects]
                
                # Group into clusters
                cluster_key = tuple(sorted(similar_ids[:3]))  # Use top 3 as cluster key
                if cluster_key not in clusters:
                    clusters[cluster_key] = []
                clusters[cluster_key].append(cve)
            except:
                pass
        
        print(f"   Identified {len(clusters)} vulnerability clusters")
        
        return {
            'start_cve': start_cve,
            'related_count': len(related_cves),
            'clusters': len(clusters),
            'related_cves': related_cves[:10],  # Top 10
            'cluster_summary': {k: len(v) for k, v in list(clusters.items())[:5]}
        }
    
    def query_3_multi_modal_threat_hunt(self, 
                                       threat_actor: str = None,
                                       semantic_query: str = None,
                                       min_cvss: float = 7.0) -> Dict[str, Any]:
        """
        Query 3: Multi-Modal Threat Hunting
        
        1. Filter by threat actor (Graph)
        2. Semantic search within results (Vector)
        3. Enrich with IOCs and exploits (Redis + Graph)
        
        Use case: "Find all CVEs attributed to APT28 that are semantically similar 
                   to 'privilege escalation' with CVSS > 7.0, show exploits and IOCs"
        """
        print(f"\n{'='*80}")
        print(f"QUERY 3: MULTI-MODAL THREAT HUNTING")
        print(f"{'='*80}")
        print(f"Threat Actor: {threat_actor}")
        print(f"Semantic Query: {semantic_query}")
        print(f"Min CVSS: {min_cvss}")
        print()
        
        # Step 1: Graph filter by threat actor
        print("🕸️  Step 1: Filter by threat actor...")
        with self.neo4j.session() as session:
            if threat_actor:
                result = session.run("""
                    MATCH (a:ThreatActor)-[:PUBLISHED]->(p:ThreatPulse)<-[:MENTIONED_IN]-(c:CVE)
                    WHERE toLower(a.name) CONTAINS toLower($actor)
                      AND c.cvss_v3_score >= $min_cvss
                    RETURN DISTINCT c.cve_id as cve_id,
                           c.description as description,
                           c.cvss_v3_score as cvss
                    LIMIT 100
                """, actor=threat_actor, min_cvss=min_cvss)
            else:
                result = session.run("""
                    MATCH (c:CVE)
                    WHERE c.cvss_v3_score >= $min_cvss
                    RETURN c.cve_id as cve_id,
                           c.description as description,
                           c.cvss_v3_score as cvss
                    LIMIT 100
                """, min_cvss=min_cvss)
            
            candidate_cves = [dict(r) for r in result]
        
        print(f"   Found {len(candidate_cves)} candidate CVEs")
        
        # Step 2: Semantic filtering
        if semantic_query:
            print("🔍 Step 2: Semantic filtering...")
            response = self.cve_collection.query.near_text(
                query=semantic_query,
                limit=50,
                return_metadata=MetadataQuery(distance=True)
            )
            
            semantic_cve_ids = set(obj.properties.get('cve_id') for obj in response.objects)
            filtered_cves = [c for c in candidate_cves if c['cve_id'] in semantic_cve_ids]
            print(f"   Filtered to {len(filtered_cves)} semantically relevant CVEs")
        else:
            filtered_cves = candidate_cves
        
        # Step 3: Enrich with exploits and IOCs
        print("💎 Step 3: Enriching with exploits and IOCs...")
        enriched_results = []
        
        for cve in filtered_cves[:20]:  # Top 20
            cve_id = cve['cve_id']
            
            # Get exploits from Redis
            exploit_ids = self.redis.smembers(f"cve:exploits:{cve_id}")
            
            # Get IOCs from graph
            with self.neo4j.session() as session:
                result = session.run("""
                    MATCH (c:CVE {cve_id: $cve_id})-[:MENTIONED_IN]->(p:ThreatPulse)-[:HAS_IOC]->(i:IOC)
                    RETURN collect(DISTINCT i.value)[..5] as iocs
                """, cve_id=cve_id)
                
                record = result.single()
                iocs = record['iocs'] if record else []
            
            enriched_results.append({
                'cve_id': cve_id,
                'description': cve['description'][:150] + '...',
                'cvss_score': cve['cvss'],
                'exploit_count': len(exploit_ids),
                'exploits': list(exploit_ids)[:3],
                'ioc_count': len(iocs),
                'iocs': iocs
            })
        
        print(f"   Enriched {len(enriched_results)} results")
        
        return {
            'threat_actor': threat_actor,
            'semantic_query': semantic_query,
            'min_cvss': min_cvss,
            'total_found': len(filtered_cves),
            'results': enriched_results
        }
    
    def query_4_temporal_correlation(self, days_back: int = 30) -> Dict[str, Any]:
        """
        Query 4: Temporal Correlation Analysis
        
        1. Get recent CVEs from Redis (time-based)
        2. Find exploitation timeline from graph
        3. Cluster by attack pattern using vectors
        
        Use case: "Show CVEs published in last 30 days, when they were weaponized,
                   and group by attack pattern"
        """
        print(f"\n{'='*80}")
        print(f"QUERY 4: TEMPORAL CORRELATION ANALYSIS")
        print(f"{'='*80}")
        print(f"Time window: Last {days_back} days")
        print()
        
        # Step 1: Get recent CVEs
        print("📅 Step 1: Fetching recent CVEs...")
        from datetime import timedelta
        cutoff_date = (datetime.utcnow() - timedelta(days=days_back)).isoformat()
        
        with self.neo4j.session() as session:
            result = session.run("""
                MATCH (c:CVE)
                WHERE c.published >= datetime($cutoff)
                OPTIONAL MATCH (c)-[:HAS_EXPLOIT]->(e:Exploit)
                RETURN c.cve_id as cve_id,
                       c.description as description,
                       c.published as published,
                       c.cvss_v3_score as cvss,
                       count(e) as exploit_count,
                       c.weaponized as weaponized
                ORDER BY c.published DESC
                LIMIT 100
            """, cutoff=cutoff_date)
            
            recent_cves = [dict(r) for r in result]
        
        print(f"   Found {len(recent_cves)} recent CVEs")
        
        # Step 2: Analyze weaponization timeline
        weaponized = [c for c in recent_cves if c.get('weaponized')]
        print(f"   Weaponized: {len(weaponized)} CVEs")
        
        # Step 3: Cluster by attack pattern
        print("🔍 Step 3: Clustering by attack pattern...")
        
        attack_patterns = {}
        for cve in recent_cves[:30]:
            desc = cve.get('description', '')
            
            # Simple pattern detection
            if 'remote code execution' in desc.lower() or 'rce' in desc.lower():
                pattern = 'RCE'
            elif 'sql injection' in desc.lower():
                pattern = 'SQLi'
            elif 'cross-site scripting' in desc.lower() or 'xss' in desc.lower():
                pattern = 'XSS'
            elif 'privilege escalation' in desc.lower():
                pattern = 'PrivEsc'
            elif 'denial of service' in desc.lower() or 'dos' in desc.lower():
                pattern = 'DoS'
            else:
                pattern = 'Other'
            
            if pattern not in attack_patterns:
                attack_patterns[pattern] = []
            attack_patterns[pattern].append(cve)
        
        print(f"   Identified {len(attack_patterns)} attack patterns")
        
        return {
            'days_back': days_back,
            'total_cves': len(recent_cves),
            'weaponized_count': len(weaponized),
            'attack_patterns': {k: len(v) for k, v in attack_patterns.items()},
            'recent_weaponized': weaponized[:10],
            'pattern_details': {k: v[:3] for k, v in attack_patterns.items()}
        }
    
    def query_5_supply_chain_risk(self, vendor: str) -> Dict[str, Any]:
        """
        Query 5: Supply Chain Risk Analysis
        
        1. Find all CVEs affecting vendor (Graph)
        2. Find similar CVEs in other vendors (Vector)
        3. Trace to exploits and threat actors (Graph + Redis)
        
        Use case: "Analyze supply chain risk for Microsoft: show all CVEs,
                   similar vulnerabilities in other vendors, active exploits"
        """
        print(f"\n{'='*80}")
        print(f"QUERY 5: SUPPLY CHAIN RISK ANALYSIS")
        print(f"{'='*80}")
        print(f"Vendor: {vendor}")
        print()
        
        # Step 1: Get vendor CVEs
        print("🏢 Step 1: Fetching vendor CVEs...")
        with self.neo4j.session() as session:
            result = session.run("""
                MATCH (v:Vendor)<-[:AFFECTS_VENDOR]-(c:CVE)
                WHERE toLower(v.name) CONTAINS toLower($vendor)
                OPTIONAL MATCH (c)-[:HAS_EXPLOIT]->(e:Exploit)
                RETURN c.cve_id as cve_id,
                       c.description as description,
                       c.cvss_v3_score as cvss,
                       count(e) as exploits,
                       c.weaponized as weaponized
                ORDER BY c.cvss_v3_score DESC
                LIMIT 50
            """, vendor=vendor)
            
            vendor_cves = [dict(r) for r in result]
        
        print(f"   Found {len(vendor_cves)} CVEs affecting {vendor}")
        
        # Step 2: Find similar CVEs in other vendors
        print("🔍 Step 2: Finding similar CVEs in other vendors...")
        similar_in_others = []
        
        for cve in vendor_cves[:10]:  # Top 10 critical
            try:
                response = self.cve_collection.query.near_text(
                    query=cve['description'][:500] if cve['description'] else cve['cve_id'],
                    limit=5,
                    return_metadata=MetadataQuery(distance=True)
                )
                
                for obj in response.objects:
                    similar_cve_id = obj.properties.get('cve_id')
                    if similar_cve_id != cve['cve_id']:
                        # Check if it affects different vendor
                        with self.neo4j.session() as session:
                            result = session.run("""
                                MATCH (c:CVE {cve_id: $cve_id})-[:AFFECTS_VENDOR]->(v:Vendor)
                                WHERE NOT toLower(v.name) CONTAINS toLower($vendor)
                                RETURN collect(DISTINCT v.name)[..3] as other_vendors
                            """, cve_id=similar_cve_id, vendor=vendor)
                            
                            record = result.single()
                            if record and record['other_vendors']:
                                similar_in_others.append({
                                    'original_cve': cve['cve_id'],
                                    'similar_cve': similar_cve_id,
                                    'other_vendors': record['other_vendors']
                                })
            except:
                pass
        
        print(f"   Found {len(similar_in_others)} similar CVEs in other vendors")
        
        # Step 3: Risk scoring
        total_cves = len(vendor_cves)
        weaponized = len([c for c in vendor_cves if c.get('weaponized')])
        avg_cvss = sum(c['cvss'] for c in vendor_cves if c['cvss']) / len(vendor_cves) if vendor_cves else 0
        
        risk_score = (weaponized / total_cves * 50) + (avg_cvss / 10 * 50) if total_cves > 0 else 0
        
        return {
            'vendor': vendor,
            'total_cves': total_cves,
            'weaponized_count': weaponized,
            'avg_cvss': round(avg_cvss, 2),
            'risk_score': round(risk_score, 2),
            'critical_cves': vendor_cves[:10],
            'supply_chain_exposure': similar_in_others[:10]
        }
    
    def close(self):
        """Close all connections"""
        self.neo4j.close()
        self.weaviate.close()
        self.redis.close()


# Demo queries
if __name__ == "__main__":
    print("=" * 80)
    print("🚀 HYBRID QUERY ENGINE - ADVANCED DEMONSTRATIONS")
    print("=" * 80)
    print()
    
    engine = HybridQueryEngine()
    
    try:
        # Query 1: Semantic → Graph
        result1 = engine.query_1_semantic_then_graph(
            "remote code execution in web applications",
            limit=5
        )
        print(f"\n✅ Query 1 Results: {result1['count']} CVEs found")
        for r in result1['results'][:3]:
            print(f"   - {r['cve_id']}: CVSS {r['cvss_score']}, {len(r['exploits'])} exploits")
        
        # Query 2: Graph → Vector
        if result1['results']:
            start_cve = result1['results'][0]['cve_id']
            result2 = engine.query_2_graph_then_vector(start_cve, hops=2)
            print(f"\n✅ Query 2 Results: {result2['related_count']} related CVEs, {result2['clusters']} clusters")
        
        # Query 3: Multi-modal threat hunt
        result3 = engine.query_3_multi_modal_threat_hunt(
            threat_actor="apt",
            semantic_query="privilege escalation",
            min_cvss=7.0
        )
        print(f"\n✅ Query 3 Results: {result3['total_found']} CVEs found")
        
        # Query 4: Temporal correlation
        result4 = engine.query_4_temporal_correlation(days_back=365)
        print(f"\n✅ Query 4 Results: {result4['total_cves']} recent CVEs, {result4['weaponized_count']} weaponized")
        print(f"   Attack patterns: {result4['attack_patterns']}")
        
        # Query 5: Supply chain risk
        result5 = engine.query_5_supply_chain_risk("microsoft")
        print(f"\n✅ Query 5 Results: Risk score {result5['risk_score']}/100 for {result5['vendor']}")
        print(f"   {result5['total_cves']} CVEs, {result5['weaponized_count']} weaponized, avg CVSS {result5['avg_cvss']}")
        
    finally:
        engine.close()
    
    print("\n" + "=" * 80)
    print("✅ ALL HYBRID QUERIES COMPLETE")
    print("=" * 80)
