#!/usr/bin/env python3
"""
Real Data Ingestion Pipeline
Ingest cyber-pi threat intelligence + external sources
"""

import json
import sys
import asyncio
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Any
import hashlib
import re

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from backend.core.stix_converter import STIXConverter
    from backend.core.simple_router import SimplifiedRouter
    STIX_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Some imports failed: {e}")
    STIX_AVAILABLE = False

# Database clients (will be imported when available)
try:
    import weaviate
    import weaviate.classes.config as wvcc
    from neo4j import GraphDatabase
    import redis.asyncio as redis
    DB_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Database clients not available: {e}")
    DB_AVAILABLE = False


class RealDataIngestionPipeline:
    """
    Production ingestion pipeline for real threat intelligence
    """
    
    def __init__(self):
        self.stats = {
            "total": 0,
            "processed": 0,
            "failed": 0,
            "stix_conversions": 0,
            "weaviate_stored": 0,
            "neo4j_stored": 0,
            "redis_cached": 0
        }
        
        # Initialize clients
        self.weaviate_client = None
        self.neo4j_driver = None
        self.redis_client = None
        self.stix_converter = None
        
    async def connect_databases(self):
        """Connect to all databases"""
        print("Connecting to databases...")
        
        # Check if using localhost (port-forward mode)
        import os
        use_localhost = os.getenv('USE_LOCALHOST', 'false').lower() == 'true'
        
        if use_localhost:
            print("📍 Using localhost (port-forward mode)")
            weaviate_host = "localhost"
            neo4j_host = "localhost"
            redis_host = "localhost"
        else:
            print("📍 Using internal cluster DNS")
            weaviate_host = "weaviate.cyber-pi-intel.svc.cluster.local"
            neo4j_host = "neo4j.cyber-pi-intel.svc.cluster.local"
            redis_host = "redis.cyber-pi-intel.svc.cluster.local"
        
        # Weaviate
        try:
            self.weaviate_client = weaviate.connect_to_custom(
                http_host=weaviate_host,
                http_port=8080,
                http_secure=False,
                grpc_host=weaviate_host,
                grpc_port=50051,
                grpc_secure=False,
                skip_init_checks=False
            )
            print("✅ Connected to Weaviate")
        except Exception as e:
            print(f"⚠️  Weaviate connection failed: {e}")
        
        # Neo4j
        try:
            self.neo4j_driver = GraphDatabase.driver(
                f"bolt://{neo4j_host}:7687",
                auth=("neo4j", "cyber-pi-neo4j-2025")
            )
            self.neo4j_driver.verify_connectivity()
            print("✅ Connected to Neo4j")
        except Exception as e:
            print(f"⚠️  Neo4j connection failed: {e}")
        
        # Redis
        try:
            self.redis_client = await redis.from_url(
                f"redis://{redis_host}:6379",
                password="cyber-pi-redis-2025",
                encoding="utf-8",
                decode_responses=True
            )
            await self.redis_client.ping()
            print("✅ Connected to Redis")
        except Exception as e:
            print(f"⚠️  Redis connection failed: {e}")
        
        # STIX Converter
        if STIX_AVAILABLE:
            try:
                self.stix_converter = STIXConverter()
                print("✅ STIX converter initialized")
            except Exception as e:
                print(f"⚠️  STIX converter failed: {e}")
    
    def parse_cyber_pi_item(self, item: Dict) -> Dict[str, Any]:
        """Convert cyber-pi item to our threat intelligence schema"""
        
        # Extract basic info
        threat_id = item.get('id', hashlib.sha256(
            (item.get('title', '') + item.get('link', '')).encode()
        ).hexdigest()[:16])
        
        # Parse content for threat intelligence
        content = item.get('content', '')
        title = item.get('title', 'Unknown Threat')
        
        # Extract threat type from content/title
        threat_types = []
        keywords = {
            'ransomware': 'ransomware',
            'phishing': 'phishing',
            'malware': 'malware',
            'vulnerability': 'vulnerability',
            'ddos': 'ddos',
            'botnet': 'botnet',
            'trojan': 'trojan',
            'apt': 'apt',
            'zero-day': 'zero-day',
            'exploit': 'exploit'
        }
        
        text_lower = (title + ' ' + content).lower()
        for keyword, threat_type in keywords.items():
            if keyword in text_lower:
                threat_types.append(threat_type)
        
        if not threat_types:
            threat_types = ['unknown']
        
        # Extract CVEs
        cves = re.findall(r'CVE-\d{4}-\d{4,7}', content, re.IGNORECASE)
        cves = list(set([cve.upper() for cve in cves]))
        
        # Extract IP addresses and domains (IOCs)
        iocs = []
        ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
        domain_pattern = r'\b[a-z0-9][a-z0-9-]{0,61}[a-z0-9]\.[a-z]{2,}\b'
        
        ips = re.findall(ip_pattern, content)
        domains = re.findall(domain_pattern, content)
        iocs.extend(ips[:10])  # Limit to avoid false positives
        iocs.extend(domains[:10])
        
        # Determine severity
        severity = 'medium'
        if any(k in text_lower for k in ['critical', 'severe', 'high-severity', 'zero-day']):
            severity = 'critical'
        elif any(k in text_lower for k in ['high', 'important', 'significant']):
            severity = 'high'
        elif any(k in text_lower for k in ['low', 'minor', 'informational']):
            severity = 'low'
        
        # Build threat object
        threat = {
            "threatId": f"threat_{threat_id}",
            "title": title,
            "content": content[:10000],  # Limit content length
            "summary": content[:500] if content else title,
            "source": item.get('source', 'cyber-pi'),
            "sourceUrl": item.get('link', ''),
            "industry": self._extract_industries(text_lower),
            "severity": severity,
            "threatType": threat_types,
            "threatActors": self._extract_threat_actors(content),
            "cves": cves,
            "iocs": iocs,
            "mitreTechniques": self._extract_mitre(content),
            "mitreTactics": [],
            "publishedDate": item.get('published', datetime.now(timezone.utc).isoformat()),
            "ingestedDate": datetime.now(timezone.utc).isoformat(),
            "lastUpdated": datetime.now(timezone.utc).isoformat(),
            "confidence": 0.7,  # Default confidence
            "verificationStatus": "unverified",
            "tags": item.get('tags', []),
            "affectedProducts": [],
            "affectedVendors": [],
            "recommendedActions": [],
            "relatedThreats": [],
            "metadata": json.dumps(item.get('metadata', {}))
        }
        
        return threat
    
    def _extract_industries(self, text: str) -> List[str]:
        """Extract target industries from text"""
        industries = []
        industry_keywords = {
            "Aviation & Airlines": ["aviation", "airline", "aircraft", "airport"],
            "Healthcare & Medical": ["healthcare", "hospital", "medical", "health"],
            "Financial Services": ["bank", "financial", "finance", "credit card"],
            "Energy & Utilities": ["energy", "utility", "power grid", "oil", "gas"],
            "Government & Public Sector": ["government", "federal", "public sector"],
            "Technology": ["tech", "software", "cloud", "saas"],
            "Manufacturing": ["manufacturing", "factory", "industrial"],
            "Education": ["education", "university", "school"],
            "Retail & E-commerce": ["retail", "ecommerce", "shopping"],
            "Telecommunications": ["telecom", "5g", "network provider"]
        }
        
        for industry, keywords in industry_keywords.items():
            if any(kw in text for kw in keywords):
                industries.append(industry)
        
        return industries if industries else ["General"]
    
    def _extract_threat_actors(self, text: str) -> List[str]:
        """Extract known threat actors from text"""
        actors = []
        known_actors = [
            "Lockbit", "BlackCat", "ALPHV", "Lazarus", "APT28", "APT29",
            "Fancy Bear", "Cozy Bear", "Sandworm", "Volt Typhoon",
            "APT41", "Kimsuky", "Anonymous Sudan", "Killnet"
        ]
        
        for actor in known_actors:
            if actor.lower() in text.lower():
                actors.append(actor)
        
        return list(set(actors))
    
    def _extract_mitre(self, text: str) -> List[str]:
        """Extract MITRE ATT&CK techniques from text"""
        techniques = re.findall(r'T\d{4}(?:\.\d{3})?', text, re.IGNORECASE)
        return list(set([t.upper() for t in techniques]))
    
    async def ingest_threat(self, threat: Dict) -> bool:
        """Ingest a single threat into all databases"""
        try:
            threat_id = threat['threatId']
            
            # 1. Convert to STIX (if available)
            stix_bundle = None
            if self.stix_converter:
                try:
                    stix_bundle = self.stix_converter.threat_to_stix_bundle(threat)
                    self.stats["stix_conversions"] += 1
                except Exception as e:
                    print(f"   STIX conversion failed: {e}")
            
            # 2. Store in Weaviate
            if self.weaviate_client:
                try:
                    collection = self.weaviate_client.collections.get("CyberThreatIntelligence")
                    
                    data_obj = {
                        "threatId": threat['threatId'],
                        "stixId": stix_bundle.objects[0].id if stix_bundle else "",
                        "stixType": stix_bundle.objects[0].type if stix_bundle else "",
                        "stixVersion": "2.1" if stix_bundle else "",
                        "stixObject": stix_bundle.serialize() if stix_bundle else "",
                        "title": threat['title'],
                        "content": threat['content'],
                        "summary": threat['summary'],
                        "source": threat['source'],
                        "sourceUrl": threat['sourceUrl'],
                        "industry": threat['industry'],
                        "severity": threat['severity'],
                        "threatType": threat['threatType'],
                        "threatActors": threat['threatActors'],
                        "cves": threat['cves'],
                        "iocs": threat['iocs'],
                        "mitreTactics": threat['mitreTactics'],
                        "mitreTechniques": threat['mitreTechniques'],
                        "publishedDate": threat['publishedDate'],
                        "ingestedDate": threat['ingestedDate'],
                        "lastUpdated": threat['lastUpdated'],
                        "confidence": threat['confidence'],
                        "verificationStatus": threat['verificationStatus'],
                        "tags": threat['tags'],
                        "affectedProducts": threat['affectedProducts'],
                        "affectedVendors": threat['affectedVendors'],
                        "recommendedActions": threat['recommendedActions'],
                        "relatedThreats": threat['relatedThreats'],
                        "metadata": threat['metadata']
                    }
                    
                    collection.data.insert(data_obj)
                    self.stats["weaviate_stored"] += 1
                except Exception as e:
                    print(f"   Weaviate storage failed: {e}")
            
            # 3. Cache in Redis
            if self.redis_client:
                try:
                    await self.redis_client.setex(
                        f"threat:{threat_id}",
                        3600,  # 1 hour TTL
                        json.dumps(threat)
                    )
                    self.stats["redis_cached"] += 1
                except Exception as e:
                    print(f"   Redis caching failed: {e}")
            
            # 4. Build graph in Neo4j
            if self.neo4j_driver:
                try:
                    with self.neo4j_driver.session() as session:
                        # Create threat node
                        session.run("""
                            MERGE (t:CyberThreat {threatId: $threatId})
                            SET t.title = $title,
                                t.severity = $severity,
                                t.publishedDate = $publishedDate,
                                t.source = $source
                        """, threatId=threat_id, title=threat['title'],
                            severity=threat['severity'],
                            publishedDate=threat['publishedDate'],
                            source=threat['source'])
                        
                        # Create relationships to industries
                        for industry in threat['industry']:
                            session.run("""
                                MATCH (t:CyberThreat {threatId: $threatId})
                                MERGE (i:Industry {industryName: $industry})
                                MERGE (t)-[:TARGETS]->(i)
                            """, threatId=threat_id, industry=industry)
                        
                        # Create threat actor relationships
                        for actor in threat['threatActors']:
                            session.run("""
                                MATCH (t:CyberThreat {threatId: $threatId})
                                MERGE (a:ThreatActor {actorName: $actor})
                                MERGE (t)-[:ATTRIBUTED_TO]->(a)
                            """, threatId=threat_id, actor=actor)
                        
                        self.stats["neo4j_stored"] += 1
                except Exception as e:
                    print(f"   Neo4j storage failed: {e}")
            
            self.stats["processed"] += 1
            return True
            
        except Exception as e:
            print(f"❌ Failed to ingest {threat.get('threatId', 'unknown')}: {e}")
            self.stats["failed"] += 1
            return False
    
    async def ingest_cyber_pi_file(self, filepath: str):
        """Ingest threats from cyber-pi collection file"""
        print(f"\n📁 Loading: {filepath}")
        
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        items = data.get('items', [])
        self.stats["total"] = len(items)
        
        print(f"📊 Found {len(items)} threat items")
        print(f"🚀 Starting ingestion...\n")
        
        for i, item in enumerate(items, 1):
            if i % 100 == 0:
                print(f"   Progress: {i}/{len(items)} ({i/len(items)*100:.1f}%)")
            
            # Parse item
            threat = self.parse_cyber_pi_item(item)
            
            # Ingest
            await self.ingest_threat(threat)
        
        print(f"\n✅ Ingestion complete!")
    
    async def close(self):
        """Close all connections"""
        if self.weaviate_client:
            self.weaviate_client.close()
        if self.neo4j_driver:
            self.neo4j_driver.close()
        if self.redis_client:
            await self.redis_client.close()
    
    def print_stats(self):
        """Print ingestion statistics"""
        print("\n" + "="*60)
        print("📊 Ingestion Statistics")
        print("="*60)
        print(f"Total items:          {self.stats['total']}")
        print(f"Successfully processed: {self.stats['processed']}")
        print(f"Failed:               {self.stats['failed']}")
        print(f"STIX conversions:     {self.stats['stix_conversions']}")
        print(f"Weaviate stored:      {self.stats['weaviate_stored']}")
        print(f"Neo4j stored:         {self.stats['neo4j_stored']}")
        print(f"Redis cached:         {self.stats['redis_cached']}")
        if self.stats['total'] > 0:
            print(f"\nSuccess rate: {self.stats['processed']/self.stats['total']*100:.1f}%")
        print("="*60)


async def main():
    """Main ingestion pipeline"""
    print("="*60)
    print("🔥 REAL DATA INGESTION PIPELINE")
    print("cyber-pi Threat Intelligence → TQAKB")
    print("="*60)
    
    # Initialize pipeline
    pipeline = RealDataIngestionPipeline()
    
    # Connect to databases
    await pipeline.connect_databases()
    
    # Ingest cyber-pi data
    cyber_pi_file = "/home/david/projects/cyber-pi/data/raw/master_collection_20251031_014039.json"
    
    if Path(cyber_pi_file).exists():
        await pipeline.ingest_cyber_pi_file(cyber_pi_file)
    else:
        print(f"❌ File not found: {cyber_pi_file}")
        return 1
    
    # Print statistics
    pipeline.print_stats()
    
    # Close connections
    await pipeline.close()
    
    print("\n✅ Pipeline complete!")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
