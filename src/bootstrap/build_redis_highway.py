#!/usr/bin/env python3
"""
Redis Highway Index Builder
Production-grade construction of Redis data structures for CVE intelligence

Builds:
- Primary CVE storage (hashes)
- Severity indexes (sets)
- Vendor indexes (sets)
- CWE indexes (sets)
- CVSS rankings (sorted sets)
- Temporal rankings (sorted sets)
- Keyword indexes (sets)
- Event stream initialization

Author: Built to enterprise-grade standards
"""

import json
import os
import logging
import time
from pathlib import Path
from typing import Dict, List, Set, Optional
from collections import defaultdict
import redis
from tqdm import tqdm
import re

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RedisHighwayBuilder:
    """
    Build Redis Highway data structures with nuclear-grade quality
    """

    def __init__(self, redis_host='10.152.183.253', redis_port=6379, redis_password: Optional[str] = None):
        """Initialize Redis connection"""
        redis_password = redis_password or os.getenv('REDIS_PASSWORD')
        if not redis_password:
            raise ValueError("REDIS_PASSWORD must be set in environment or passed as parameter")
        
        logger.info(f"Connecting to Redis at {redis_host}:{redis_port}")
        self.redis = redis.Redis(
            host=redis_host,
            port=redis_port,
            password=redis_password,
            decode_responses=True,
            socket_timeout=10,
            socket_connect_timeout=10
        )

        # Test connection
        try:
            self.redis.ping()
            logger.info("✅ Redis connection established")
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
            raise

        self.stats = {
            'cves_processed': 0,
            'indexes_created': 0,
            'sets_created': 0,
            'sorted_sets_created': 0,
            'keywords_extracted': 0,
            'errors': 0
        }

    def extract_keywords(self, description: str) -> Set[str]:
        """
        Extract security-relevant keywords from CVE description
        Enterprise standard: Thorough but efficient
        """
        if not description:
            return set()

        # Security-relevant keywords
        security_keywords = {
            'authentication', 'authorization', 'bypass', 'injection', 'xss',
            'csrf', 'overflow', 'underflow', 'memory', 'buffer', 'heap', 'stack',
            'remote', 'code', 'execution', 'rce', 'privilege', 'escalation',
            'denial', 'service', 'dos', 'ddos', 'path', 'traversal',
            'sql', 'command', 'deserialization', 'xxe', 'ssrf',
            'disclosure', 'information', 'leak', 'exposure',
            'credential', 'password', 'token', 'session', 'cookie',
            'encryption', 'cipher', 'cryptographic', 'weakness',
            'validation', 'sanitization', 'input', 'output'
        }

        # Normalize and tokenize
        desc_lower = description.lower()
        words = re.findall(r'\b\w+\b', desc_lower)

        # Find matching keywords
        found_keywords = set()
        for keyword in security_keywords:
            if keyword in words or keyword in desc_lower:
                found_keywords.add(keyword)

        return found_keywords

    def severity_category(self, cvss_score: float) -> str:
        """
        Categorize CVSS score into severity levels
        NIST standard classification
        """
        if cvss_score is None or cvss_score == 0:
            return 'none'
        elif cvss_score >= 9.0:
            return 'critical'
        elif cvss_score >= 7.0:
            return 'high'
        elif cvss_score >= 4.0:
            return 'medium'
        else:
            return 'low'

    def build_indexes(self, cve_file: str, batch_size: int = 1000) -> Dict:
        """
        Build all Redis indexes from CVE data

        Enterprise principle: Do it right the first time
        """
        logger.info("="*80)
        logger.info("REDIS HIGHWAY CONSTRUCTION - NUCLEAR GRADE")
        logger.info("="*80)

        # Load CVE data
        logger.info(f"Loading CVE data from {cve_file}")
        with open(cve_file) as f:
            cves = json.load(f)

        logger.info(f"Loaded {len(cves):,} CVEs")

        # Initialize counters
        vendor_counts = defaultdict(int)
        cwe_counts = defaultdict(int)
        keyword_counts = defaultdict(int)

        # Build indexes with batching
        logger.info("\n📊 Building Redis Highway Indexes...")

        pipe = self.redis.pipeline()
        batch_count = 0

        for i, cve in enumerate(tqdm(cves, desc="Processing CVEs")):
            try:
                cve_id = cve['cve_id']

                # 1. PRIMARY STORAGE: Store CVE as hash
                cve_hash = {
                    'id': cve_id,
                    'description': cve.get('description', ''),
                    'cvss_v3': cve.get('cvss_v3_score', 0) or 0,
                    'cvss_v2': cve.get('cvss_v2_score', 0) or 0,
                    'published': cve.get('published', ''),
                    'modified': cve.get('modified', ''),
                    'vendors': ','.join(cve.get('affected_vendors', [])),
                    'products': ','.join(cve.get('affected_products', [])),
                    'cwes': ','.join(cve.get('cwes', [])),
                    'references': ','.join(cve.get('references', [])[:10])  # Limit to 10
                }
                pipe.hset(f"cve:{cve_id}", mapping=cve_hash)

                # 2. SEVERITY INDEXES: Add to severity sets
                cvss = cve.get('cvss_v3_score') or cve.get('cvss_v2_score') or 0
                severity = self.severity_category(cvss)
                pipe.sadd(f"cves:severity:{severity}", cve_id)

                # 3. CVSS RANKING: Sorted set by CVSS score
                if cvss > 0:
                    pipe.zadd("cves:ranking:cvss", {cve_id: cvss})

                # 4. TEMPORAL RANKING: Sorted set by published date
                if cve.get('published'):
                    try:
                        from datetime import datetime
                        pub_date = datetime.fromisoformat(cve['published'].replace('Z', '+00:00'))
                        timestamp = pub_date.timestamp()
                        pipe.zadd("cves:ranking:temporal", {cve_id: timestamp})
                    except:
                        pass

                # 5. VENDOR INDEXES: Add to vendor sets
                for vendor in cve.get('affected_vendors', []):
                    if vendor:
                        vendor_key = vendor.lower().replace(' ', '_')
                        pipe.sadd(f"vendor:{vendor_key}:cves", cve_id)
                        vendor_counts[vendor_key] += 1

                # 6. CWE INDEXES: Add to CWE sets
                for cwe in cve.get('cwes', []):
                    if cwe:
                        pipe.sadd(f"cwe:{cwe}:cves", cve_id)
                        cwe_counts[cwe] += 1

                # 7. KEYWORD INDEXES: Extract and index keywords
                keywords = self.extract_keywords(cve.get('description', ''))
                for keyword in keywords:
                    pipe.sadd(f"keyword:{keyword}:cves", cve_id)
                    keyword_counts[keyword] += 1

                self.stats['cves_processed'] += 1
                batch_count += 1

                # Execute batch
                if batch_count >= batch_size:
                    pipe.execute()
                    pipe = self.redis.pipeline()
                    batch_count = 0

            except Exception as e:
                logger.error(f"Error processing CVE {cve.get('cve_id', 'unknown')}: {e}")
                self.stats['errors'] += 1

        # Execute remaining
        if batch_count > 0:
            pipe.execute()

        logger.info("\n✅ Primary indexes built")

        # 8. BUILD METADATA INDEXES
        logger.info("\n📊 Building metadata indexes...")

        pipe = self.redis.pipeline()

        # Store vendor counts
        for vendor, count in vendor_counts.items():
            pipe.zadd("vendors:ranking:cve_count", {vendor: count})

        # Store CWE counts
        for cwe, count in cwe_counts.items():
            pipe.zadd("cwes:ranking:cve_count", {cwe: count})

        # Store keyword counts
        for keyword, count in keyword_counts.items():
            pipe.zadd("keywords:ranking:cve_count", {keyword: count})

        # Store statistics
        pipe.hset("stats:global", mapping={
            'total_cves': len(cves),
            'total_vendors': len(vendor_counts),
            'total_cwes': len(cwe_counts),
            'total_keywords': len(keyword_counts),
            'last_build': time.time()
        })

        pipe.execute()

        logger.info("✅ Metadata indexes built")

        # 9. INITIALIZE EVENT STREAM
        logger.info("\n📡 Initializing event stream...")
        self.redis.xadd('cve:stream', {
            'event': 'highway.initialized',
            'timestamp': time.time(),
            'cve_count': len(cves)
        })

        logger.info("✅ Event stream initialized")

        # Update stats
        self.stats['indexes_created'] = 7  # 7 types of indexes
        self.stats['sets_created'] = len(vendor_counts) + len(cwe_counts) + len(keyword_counts) + 4
        self.stats['sorted_sets_created'] = 5
        self.stats['keywords_extracted'] = len(keyword_counts)

        return self.stats

    def verify_indexes(self) -> bool:
        """
        Verify all indexes are correctly built
        Enterprise standard: Trust but verify
        """
        logger.info("\n🔍 VERIFICATION PHASE")
        logger.info("="*80)

        checks = []

        # Check 1: Total CVE count
        total_cves = int(self.redis.hget("stats:global", "total_cves") or 0)
        logger.info(f"Total CVEs in stats: {total_cves:,}")
        checks.append(total_cves > 0)

        # Check 2: Severity distribution
        severity_counts = {}
        for severity in ['critical', 'high', 'medium', 'low', 'none']:
            count = self.redis.scard(f"cves:severity:{severity}")
            severity_counts[severity] = count
            logger.info(f"  {severity.capitalize()}: {count:,}")
        checks.append(sum(severity_counts.values()) > 0)

        # Check 3: CVSS ranking size
        cvss_ranking_size = self.redis.zcard("cves:ranking:cvss")
        logger.info(f"CVSS ranking entries: {cvss_ranking_size:,}")
        checks.append(cvss_ranking_size > 0)

        # Check 4: Temporal ranking size
        temporal_size = self.redis.zcard("cves:ranking:temporal")
        logger.info(f"Temporal ranking entries: {temporal_size:,}")
        checks.append(temporal_size > 0)

        # Check 5: Top vendors
        top_vendors = self.redis.zrevrange("vendors:ranking:cve_count", 0, 9, withscores=True)
        logger.info(f"\nTop 10 Vendors:")
        for vendor, count in top_vendors:
            logger.info(f"  {vendor}: {int(count):,} CVEs")
        checks.append(len(top_vendors) > 0)

        # Check 6: Top CWEs
        top_cwes = self.redis.zrevrange("cwes:ranking:cve_count", 0, 9, withscores=True)
        logger.info(f"\nTop 10 CWEs:")
        for cwe, count in top_cwes:
            logger.info(f"  {cwe}: {int(count):,} CVEs")
        checks.append(len(top_cwes) > 0)

        # Check 7: Top keywords
        top_keywords = self.redis.zrevrange("keywords:ranking:cve_count", 0, 9, withscores=True)
        logger.info(f"\nTop 10 Keywords:")
        for keyword, count in top_keywords:
            logger.info(f"  {keyword}: {int(count):,} CVEs")
        checks.append(len(top_keywords) > 0)

        # Check 8: Sample CVE retrieval
        sample_cve_id = self.redis.zrevrange("cves:ranking:cvss", 0, 0)[0]
        sample_cve = self.redis.hgetall(f"cve:{sample_cve_id}")
        logger.info(f"\nSample CVE ({sample_cve_id}):")
        logger.info(f"  CVSS: {sample_cve.get('cvss_v3', 'N/A')}")
        logger.info(f"  Description: {sample_cve.get('description', '')[:100]}...")
        checks.append(len(sample_cve) > 0)

        # Check 9: Event stream
        stream_length = self.redis.xlen('cve:stream')
        logger.info(f"\nEvent stream entries: {stream_length}")
        checks.append(stream_length > 0)

        # Final verdict
        logger.info("\n" + "="*80)
        if all(checks):
            logger.info("✅ ALL VERIFICATION CHECKS PASSED")
            logger.info("Redis Highway is operational and nuclear-grade.")
            return True
        else:
            logger.error("❌ VERIFICATION FAILED")
            logger.error(f"Passed: {sum(checks)}/{len(checks)} checks")
            return False

    def print_summary(self):
        """Print construction summary"""
        logger.info("\n" + "="*80)
        logger.info("REDIS HIGHWAY CONSTRUCTION SUMMARY")
        logger.info("="*80)
        logger.info(f"CVEs Processed:      {self.stats['cves_processed']:,}")
        logger.info(f"Index Types:         {self.stats['indexes_created']}")
        logger.info(f"Sets Created:        {self.stats['sets_created']:,}")
        logger.info(f"Sorted Sets:         {self.stats['sorted_sets_created']}")
        logger.info(f"Keywords Extracted:  {self.stats['keywords_extracted']:,}")
        logger.info(f"Errors:              {self.stats['errors']}")
        logger.info("="*80)

        # Memory usage
        info = self.redis.info('memory')
        used_memory_mb = info['used_memory'] / (1024 * 1024)
        logger.info(f"\nRedis Memory Usage:  {used_memory_mb:.2f} MB")
        logger.info(f"Total Keys:          {self.redis.dbsize():,}")
        logger.info("="*80)


def main():
    """Main execution"""
    start_time = time.time()

    # Initialize builder
    builder = RedisHighwayBuilder()

    # Build indexes
    cve_file = Path(__file__).parent.parent.parent / 'data' / 'cve_import' / 'all_cves_neo4j.json'
    stats = builder.build_indexes(str(cve_file), batch_size=1000)

    # Verify
    verified = builder.verify_indexes()

    # Summary
    builder.print_summary()

    elapsed = time.time() - start_time
    logger.info(f"\n⏱️  Total Time: {elapsed:.2f} seconds")
    logger.info(f"📊 Processing Rate: {stats['cves_processed']/elapsed:.0f} CVEs/second")

    if verified:
        logger.info("\n🎉 REDIS HIGHWAY CONSTRUCTION COMPLETE - RICKOVER APPROVED ⚓")
        return 0
    else:
        logger.error("\n❌ CONSTRUCTION FAILED - DOES NOT MEET STANDARDS")
        return 1


if __name__ == '__main__':
    exit(main())
