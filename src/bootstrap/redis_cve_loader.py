#!/usr/bin/env python3
"""
Redis CVE Loader - Load 316K CVEs into Redis first
Following the Redis-first architecture pattern
"""

import json
import redis
import logging
from pathlib import Path
from tqdm import tqdm
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RedisCVELoader:
    """
    Load CVEs into Redis with proper indexing
    Redis-first architecture: Fast ingestion, then sync to Neo4j
    """
    
    def __init__(self, redis_host='localhost', redis_port=6379, redis_db=0):
        self.redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            decode_responses=False  # Keep as bytes for JSON storage
        )
        
    def load_cves_to_redis(self, cve_file: Path, batch_size=1000):
        """
        Load CVEs into Redis with batching for performance
        
        Redis Structure:
        - cve:{cve_id} -> JSON blob of CVE data
        - cve:index:vendor:{vendor} -> Set of CVE IDs
        - cve:index:severity:{severity} -> Set of CVE IDs
        - cve:index:cwe:{cwe} -> Set of CVE IDs
        - cve:stats -> Hash of statistics
        """
        
        logger.info(f"📖 Loading CVEs from {cve_file}...")
        with open(cve_file) as f:
            cves = json.load(f)
        
        total_cves = len(cves)
        logger.info(f"✓ Loaded {total_cves:,} CVEs from file")
        
        logger.info("🔄 Loading CVEs into Redis...")
        start_time = time.time()
        
        # Statistics
        stats = {
            'total': 0,
            'critical': 0,
            'high': 0,
            'medium': 0,
            'low': 0,
            'vendors': set(),
            'cwes': set()
        }
        
        # Batch processing for Redis pipeline
        pipe = self.redis_client.pipeline()
        batch_count = 0
        
        for i, cve in enumerate(tqdm(cves, desc="Loading to Redis")):
            cve_id = cve['cve_id']
            
            # Store CVE data
            cve_key = f"cve:{cve_id}"
            pipe.set(cve_key, json.dumps(cve))
            
            # Index by severity
            cvss_score = cve.get('cvss_v3_score') or cve.get('cvss_v2_score') or 0
            if cvss_score and cvss_score >= 9.0:
                severity = 'critical'
                stats['critical'] += 1
            elif cvss_score and cvss_score >= 7.0:
                severity = 'high'
                stats['high'] += 1
            elif cvss_score and cvss_score >= 4.0:
                severity = 'medium'
                stats['medium'] += 1
            else:
                severity = 'low'
                stats['low'] += 1
            
            pipe.sadd(f"cve:index:severity:{severity}", cve_id)
            
            # Index by vendors
            for vendor in cve.get('affected_vendors', []):
                pipe.sadd(f"cve:index:vendor:{vendor}", cve_id)
                stats['vendors'].add(vendor)
            
            # Index by CWEs
            for cwe in cve.get('cwes', []):
                pipe.sadd(f"cve:index:cwe:{cwe}", cve_id)
                stats['cwes'].add(cwe)
            
            # Index by year
            if cve.get('published'):
                year = cve['published'][:4]
                pipe.sadd(f"cve:index:year:{year}", cve_id)
            
            batch_count += 1
            stats['total'] += 1
            
            # Execute pipeline every batch_size items
            if batch_count >= batch_size:
                pipe.execute()
                pipe = self.redis_client.pipeline()
                batch_count = 0
        
        # Execute remaining items
        if batch_count > 0:
            pipe.execute()
        
        # Store statistics
        self.redis_client.hset('cve:stats', mapping={
            'total': stats['total'],
            'critical': stats['critical'],
            'high': stats['high'],
            'medium': stats['medium'],
            'low': stats['low'],
            'vendors': len(stats['vendors']),
            'cwes': len(stats['cwes']),
            'last_updated': time.strftime('%Y-%m-%d %H:%M:%S')
        })
        
        elapsed = time.time() - start_time
        rate = total_cves / elapsed
        
        logger.info(f"\n✅ Redis Load Complete!")
        logger.info(f"   Total CVEs: {stats['total']:,}")
        logger.info(f"   Time: {elapsed:.1f} seconds")
        logger.info(f"   Rate: {rate:.0f} CVEs/second")
        logger.info(f"\n📊 Severity Distribution:")
        logger.info(f"   Critical: {stats['critical']:,}")
        logger.info(f"   High: {stats['high']:,}")
        logger.info(f"   Medium: {stats['medium']:,}")
        logger.info(f"   Low: {stats['low']:,}")
        logger.info(f"\n🏢 Unique Vendors: {len(stats['vendors']):,}")
        logger.info(f"🔍 Unique CWEs: {len(stats['cwes']):,}")
        
        return stats
    
    def verify_redis_data(self):
        """Verify CVEs are loaded correctly"""
        logger.info("\n🔍 Verifying Redis data...")
        
        # Check stats
        stats = self.redis_client.hgetall('cve:stats')
        if stats:
            logger.info("✅ Statistics found:")
            for key, value in stats.items():
                logger.info(f"   {key.decode()}: {value.decode()}")
        
        # Sample CVE
        sample_cves = self.redis_client.keys('cve:CVE-2024-*')
        if sample_cves:
            sample_key = sample_cves[0].decode()
            sample_data = json.loads(self.redis_client.get(sample_key))
            logger.info(f"\n✅ Sample CVE: {sample_data['cve_id']}")
            logger.info(f"   CVSS: {sample_data.get('cvss_v3_score', 'N/A')}")
            logger.info(f"   Description: {sample_data['description'][:100]}...")
        
        # Check indexes
        critical_count = self.redis_client.scard('cve:index:severity:critical')
        logger.info(f"\n✅ Critical CVE index: {critical_count:,} entries")
        
        return True


def main():
    """Main execution"""
    cve_file = Path("data/cve_import/all_cves_neo4j.json")
    
    if not cve_file.exists():
        logger.error(f"❌ CVE file not found: {cve_file}")
        return
    
    logger.info("🚀 Redis CVE Loader - Redis-First Architecture")
    logger.info("="*60)
    
    loader = RedisCVELoader(redis_host='localhost', redis_port=6379, redis_db=0)
    
    # Load CVEs
    stats = loader.load_cves_to_redis(cve_file, batch_size=1000)
    
    # Verify
    loader.verify_redis_data()
    
    logger.info("\n" + "="*60)
    logger.info("🎉 Redis Load Complete - Ready for Neo4j Sync!")
    logger.info("="*60)


if __name__ == "__main__":
    main()
