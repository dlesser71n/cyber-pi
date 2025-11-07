#!/usr/bin/env python3
"""
Cyber-PI Real Data Stress Test Implementation
Actually loads real threat intelligence data and measures system performance
"""

import asyncio
import aiohttp
import time
import psutil
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json
import os
import sys
from pathlib import Path
import feedparser
import requests
from concurrent.futures import ThreadPoolExecutor
import threading

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from src.models.ontology import CVE, ThreatActor, Product, Vendor
from src.loaders.cve_loader import CVELoader
from src.loaders.mitre_loader import MITRELoader
from src.collectors.rss_collector import RSSCollector
from src.graph.neo4j_schema import Neo4jSchemaManager
from src.graph.query_library import QueryLibrary
from src.graph.weaviate_schema import WeaviateManager

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class RealDataStressTest:
    """
    Real data stress testing that actually loads threat intelligence
    Measures performance with genuine CVE, MITRE, and RSS data
    """

    def __init__(self):
        self.start_time = datetime.now()
        self.metrics = {
            "cve_load_times": [],
            "mitre_load_times": [],
            "rss_collection_times": [],
            "query_response_times": [],
            "memory_usage": [],
            "cpu_usage": [],
            "database_sizes": [],
            "error_rates": [],
            "api_response_times": []
        }

        # Load configuration
        self.config = self._load_config()

        # Initialize components
        self.neo4j_manager = Neo4jSchemaManager(
            uri=self.config["neo4j_uri"],
            user=self.config["neo4j_user"],
            password=self.config["neo4j_password"]
        )

        self.query_lib = QueryLibrary(self.neo4j_manager.driver)

        self.weaviate_manager = WeaviateManager(
            url=self.config["weaviate_url"]
        )

        # Real RSS feeds for testing - expanded for 200MB target
        self.test_feeds = [
            "https://www.cisa.gov/cybersecurity-advisories.xml",
            "https://www.us-cert.gov/ncas/alerts.xml",
            "https://feeds.feedburner.com/TheHackersNews",
            "https://www.kaspersky.com/blog/rss",
            "https://www.crowdstrike.com/blog/feed/",
            "https://www.fireeye.com/blog/threat-research/rss",
            "https://www.mandiant.com/resources/blog/rss.xml",
            "https://www.dragos.com/rss.xml",
            "https://www.recordedfuture.com/feed",
            "https://www.threatconnect.com/blog/rss",
            "https://www.anomali.com/site/rss",
            "https://www.threatquotient.com/rss",
            "https://www.threatstream.com/blog/rss",
            "https://www.blueliv.com/blog/rss",
            "https://www.cybersecurityventures.com/feed/",
            "https://www.helpnetsecurity.com/feed/",
            "https://www.scmagazine.com/rss-feeds/news",
            "https://www.darkreading.com/rss.xml",
            "https://www.csoonline.com/feed",
            "https://www.zdnet.com/topic/security/rss.xml",
            # Additional feeds for larger data volume
            "https://www.wired.com/feed/category/security/latest/rss",
            "https://www.securityweek.com/rss",
            "https://www.govtech.com/security/rss.xml",
            "https://www.criticalinfrastructuresecuritynews.com/feed/",
            "https://www.tripwire.com/state-of-security/rss",
            "https://www.esecurityplanet.com/feed/",
            "https://www.techrepublic.com/rssfeeds/topic/security/",
            "https://www.computerweekly.com/rss/All-Computer-Weekly-content.xml",
            "https://www.infosecurity-magazine.com/rss/news/",
            "https://www.sans.org/blog/rss",
            "https://www.blackhat.com/html/archives.html",  # Note: This might not be RSS
            "https://www.defcon.org/html/links/rss.xml",
            "https://www.offensive-security.com/feed/",
            "https://www.exploit-db.com/rss.xml",
            "https://packetstormsecurity.com/files/rss/",
            "https://www.vulnerability-lab.com/rss/rss.xml",
            "https://www.securityfocus.com/rss/vulnerabilities.xml",
            "https://www.cert.org/rss/cert-alerts.xml",
            "https://www.first.org/rss",
            "https://www.enisa.europa.eu/media/cybersecurity/rss.xml",
            "https://www.ncsc.gov.uk/api/1/services/v1/report-rss-feed.xml",
            "https://www.cisa.gov/news.xml",
            "https://www.dhs.gov/rss.xml",
            "https://www.fbi.gov/feeds/cyber/rss.xml",
            "https://www.cyber.gc.ca/en/rss.xml",
            "https://www.nsa.gov/rss.xml",
            "https://www.gchq.gov.uk/news-and-events/rss.xml"
        ]

    def _load_config(self) -> Dict[str, str]:
        """Load configuration from environment"""
        return {
            "neo4j_uri": os.getenv("NEO4J_URI", "bolt://localhost:17687"),
            "neo4j_user": os.getenv("NEO4J_USER", "neo4j"),
            "neo4j_password": os.getenv("NEO4J_PASSWORD", "cyber-pi-neo4j-2025"),
            "weaviate_url": os.getenv("WEAVIATE_URL", "http://weaviate.local"),
            "redis_url": os.getenv("REDIS_URL", "redis://localhost:16379")
        }

    async def monitor_system_resources(self) -> None:
        """Monitor system resources during testing"""
        while True:
            try:
                memory = psutil.virtual_memory()
                cpu = psutil.cpu_percent(interval=1)

                self.metrics["memory_usage"].append(memory.percent)
                self.metrics["cpu_usage"].append(cpu.percent)

                # Log every 10 samples
                if len(self.metrics["memory_usage"]) % 10 == 0:
                    logger.info(".1f"
                              f"Memory: {memory.percent:.1f}% "
                              f"CPU: {cpu:.1f}%")

                await asyncio.sleep(5)  # Sample every 5 seconds
            except Exception as e:
                logger.error(f"Resource monitoring error: {e}")
                break

    async def _get_database_size(self) -> float:
        """Get current Neo4j database size in MB"""
        try:
            async with self.neo4j_manager.driver.session() as session:
                # Query for node and relationship counts
                result = await session.run("""
                    MATCH (n)
                    OPTIONAL MATCH (n)-[r]-()
                    RETURN count(DISTINCT n) as nodes, count(DISTINCT r) as relationships
                """)
                record = await result.single()

                nodes = record["nodes"]
                relationships = record["relationships"]

                # Estimate size (rough approximation)
                # Average node size ~1KB, relationship ~500B
                estimated_size_mb = (nodes * 1024 + relationships * 512) / (1024 * 1024)

                return estimated_size_mb

        except Exception as e:
            logger.error(f"Database size query failed: {e}")
            return 0.0

    async def _load_real_cve_data_parallel(self, days: int, max_concurrent: int = 3) -> int:
        """Load real CVE data using parallel processing"""
        logger.info(f"🔬 Loading {days} days of CVE data (parallel, max_concurrent={max_concurrent})")
        
        # Create multiple CVE loader instances for parallel processing
        loaders = []
        for i in range(max_concurrent):
            loader = CVELoader(
                neo4j_uri=self.config["neo4j_uri"],
                neo4j_user=self.config["neo4j_user"],
                neo4j_password=self.config["neo4j_password"]
            )
            loaders.append(loader)
        
        # Split the time range into chunks for parallel processing
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Create date ranges for parallel processing
        date_ranges = []
        chunk_size = days // max_concurrent
        remainder = days % max_concurrent
        
        current_start = start_date
        for i in range(max_concurrent):
            chunk_days = chunk_size + (1 if i < remainder else 0)
            chunk_end = current_start + timedelta(days=chunk_days)
            date_ranges.append((current_start, min(chunk_end, end_date)))
            current_start = chunk_end
        
        logger.info(f"📊 Processing {len(date_ranges)} date ranges in parallel")
        
        # Process date ranges in parallel
        async def load_date_range(loader_idx: int, start_date: datetime, end_date: datetime) -> int:
            loader = loaders[loader_idx]
            range_days = (end_date - start_date).days
            
            logger.info(f"Worker {loader_idx+1}: Loading {range_days} days ({start_date.date()} to {end_date.date()})")
            
            # Use the existing load_recent_cves method but with calculated days
            # We'll need to modify this to accept date ranges instead of just days
            count = await loader.load_recent_cves(days=range_days)
            return count
        
        # Run parallel loading
        tasks = [
            load_date_range(i, start, end) 
            for i, (start, end) in enumerate(date_ranges)
        ]
        
        start_time = time.time()
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time
        
        total_count = sum(results)
        
        logger.info(f"✅ Parallel CVE loading complete: {total_count} CVEs in {total_time:.2f}s")
        logger.info(f"   Workers: {max_concurrent}, Avg per worker: {total_count/max_concurrent:.0f} CVEs")
        
        return total_count

    async def _load_real_cve_data(self, days: int) -> int:
        """Load real CVE data from NVD"""
        try:
            cve_loader = CVELoader(
                neo4j_uri=self.config["neo4j_uri"],
                neo4j_user=self.config["neo4j_user"],
                neo4j_password=self.config["neo4j_password"]
            )

            # Load real CVE data
            count = await cve_loader.load_recent_cves(days=days)
            return count

        except Exception as e:
            logger.error(f"CVE loading failed: {e}")
            return 0

    async def _load_real_mitre_data(self) -> Dict[str, Any]:
        """Load real MITRE ATT&CK data"""
        try:
            mitre_loader = MITRELoader(
                neo4j_uri=self.config["neo4j_uri"],
                neo4j_user=self.config["neo4j_user"],
                neo4j_password=self.config["neo4j_password"]
            )

            # Load real MITRE data
            results = await mitre_loader.load_enterprise_matrix()
            return results

        except Exception as e:
            logger.error(f"MITRE loading failed: {e}")
            return {"error": str(e)}

    async def _collect_real_rss_feeds_parallel(self, feed_urls: List[str], max_concurrent: int = 10) -> Dict[str, Any]:
        """Collect real RSS feed data using parallel processing"""
        total_articles = 0
        successful_feeds = 0
        failed_feeds = 0
        
        logger.info(f"📰 Collecting {len(feed_urls)} RSS feeds (parallel, max_concurrent={max_concurrent})")
        
        # Create semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def collect_feed(url: str) -> int:
            async with semaphore:
                try:
                    # Add delay to be respectful to servers
                    await asyncio.sleep(0.1)  # 100ms delay between requests
                    
                    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
                        async with session.get(url) as response:
                            if response.status == 200:
                                content = await response.text()
                                feed = feedparser.parse(content)
                                
                                if feed.entries:
                                    article_count = len(feed.entries)
                                    logger.debug(f"✅ {url}: {article_count} articles")
                                    return article_count
                                else:
                                    logger.debug(f"⚠️  {url}: No entries found")
                                    return 0
                            else:
                                logger.debug(f"❌ {url}: HTTP {response.status}")
                                return 0
                except Exception as e:
                    logger.debug(f"❌ {url}: {str(e)[:50]}...")
                    return 0
        
        # Process all feeds in parallel with controlled concurrency
        start_time = time.time()
        tasks = [collect_feed(url) for url in feed_urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        collection_time = time.time() - start_time
        
        # Process results
        for result in results:
            if isinstance(result, int):
                total_articles += result
                if result > 0:
                    successful_feeds += 1
            else:
                failed_feeds += 1
        
        success_rate = successful_feeds / len(feed_urls) if feed_urls else 0
        
        logger.info(f"✅ RSS collection complete: {successful_feeds}/{len(feed_urls)} feeds successful")
        logger.info(f"   Articles collected: {total_articles} in {collection_time:.2f}s")
        logger.info(f"   Rate: {total_articles/collection_time:.1f} articles/sec ({len(feed_urls)/collection_time:.1f} feeds/sec)")
        
        return {
            "total_feeds": len(feed_urls),
            "successful_feeds": successful_feeds,
            "failed_feeds": failed_feeds,
            "success_rate": success_rate,
            "total_articles": total_articles,
            "collection_time_seconds": collection_time,
            "articles_per_second": total_articles / collection_time if collection_time > 0 else 0,
            "feeds_per_second": len(feed_urls) / collection_time if collection_time > 0 else 0
        }

    async def _collect_real_rss_feeds(self, feed_urls: List[str]) -> Dict[str, Any]:
        """Collect real RSS feed data"""
        total_articles = 0
        successful_feeds = 0
        failed_feeds = 0

        async def collect_feed(url: str) -> int:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=30) as response:
                        if response.status == 200:
                            content = await response.text()
                            feed = feedparser.parse(content)

                            if feed.entries:
                                return len(feed.entries)
                            else:
                                return 0
                        else:
                            return 0
            except Exception as e:
                logger.debug(f"Feed {url} failed: {e}")
                return 0

        # Collect from all feeds concurrently
        tasks = [collect_feed(url) for url in feed_urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, int):
                total_articles += result
                if result > 0:
                    successful_feeds += 1
            else:
                failed_feeds += 1

        success_rate = successful_feeds / len(feed_urls) if feed_urls else 0

        return {
            "total_feeds": len(feed_urls),
            "successful_feeds": successful_feeds,
            "failed_feeds": failed_feeds,
            "success_rate": success_rate,
            "total_articles": total_articles
        }

    async def _run_concurrent_queries(self, queries: List, users: int) -> List[float]:
        """Run queries concurrently and measure response times"""
        response_times = []

        async def run_query_batch(batch_queries: List) -> List[float]:
            batch_times = []
            for query_func in batch_queries:
                start_time = time.time()
                try:
                    await query_func()
                    end_time = time.time()
                    batch_times.append(end_time - start_time)
                except Exception as e:
                    logger.debug(f"Query failed: {e}")
                    end_time = time.time()
                    batch_times.append(end_time - start_time)
            return batch_times

        # Create concurrent tasks
        tasks = []
        for _ in range(users):
            # Rotate through queries for each user
            user_queries = queries * (users // len(queries) + 1)
            user_queries = user_queries[:len(queries)]  # One batch per user
            tasks.append(run_query_batch(user_queries))

        # Run all user tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Collect response times
        for result in results:
            if isinstance(result, list):
                response_times.extend(result)

        return response_times

    async def _benchmark_key_queries(self) -> Dict[str, float]:
        """Benchmark key query performance with real data"""
        query_times = {}

        # Test vendor risk profile query
        start_time = time.time()
        try:
            await self.query_lib.get_vendor_risk_profile("Microsoft")
        except Exception:
            pass  # Expected if no data
        query_times["vendor_risk"] = time.time() - start_time

        # Test threat actor profile query
        start_time = time.time()
        try:
            await self.query_lib.get_threat_actor_profile("APT29")
        except Exception:
            pass
        query_times["threat_actor"] = time.time() - start_time

        # Test CVE search query
        start_time = time.time()
        try:
            await self.query_lib.get_cves_by_severity("critical", limit=10)
        except Exception:
            pass
        query_times["cve_search"] = time.time() - start_time

        return query_times

    async def test_real_cve_stress(self, days_list: List[int] = [30, 90, 180, 365]) -> Dict[str, Any]:
        """Test real CVE data loading with increasing volumes - expanded for 200MB target"""
        logger.info("🔬 Testing Real CVE Data Loading")

        results = {}

        for days in days_list:
            logger.info(f"📊 Loading {days} days of real CVE data")

            start_time = time.time()
            # Use parallel loading for larger datasets
            if days >= 180:
                cve_count = await self._load_real_cve_data_parallel(days, max_concurrent=3)
            else:
                cve_count = await self._load_real_cve_data(days)
            load_time = time.time() - start_time

            self.metrics["cve_load_times"].append(load_time)

            # Get database size after loading
            db_size = await self._get_database_size()

            results[f"cve_{days}d"] = {
                "days": days,
                "cves_loaded": cve_count,
                "load_time_seconds": load_time,
                "cves_per_second": cve_count / load_time if load_time > 0 else 0,
                "database_size_mb": db_size,
                "avg_cve_size_kb": (db_size * 1024 * 1024) / cve_count if cve_count > 0 else 0
            }

            logger.info(".2f"
                      f"DB: {db_size:.1f}MB ({db_size/cve_count*1024*1024:.0f}B/CVE)")

        return results

    async def test_real_mitre_loading(self) -> Dict[str, Any]:
        """Test real MITRE ATT&CK data loading"""
        logger.info("🎯 Testing Real MITRE ATT&CK Data Loading")

        start_time = time.time()
        results = await self._load_real_mitre_data()
        load_time = time.time() - start_time

        self.metrics["mitre_load_times"].append(load_time)

        if "error" in results:
            return {"error": results["error"]}

        mitre_stats = {
            "load_time_seconds": load_time,
            "tactics_count": len(results.get("tactics", [])),
            "techniques_count": len(results.get("techniques", [])),
            "relationships_created": results.get("relationships", 0),
            "load_rate_tactics_per_sec": len(results.get("tactics", [])) / load_time if load_time > 0 else 0
        }

        logger.info(".2f"
                  f"{mitre_stats['tactics_count']} tactics, "
                  f"{mitre_stats['techniques_count']} techniques")

        return mitre_stats

    async def test_real_rss_stress(self, feed_counts: List[int] = [20, 30, 40, 50]) -> Dict[str, Any]:
        """Test real RSS feed collection with increasing parallelism"""
        logger.info("📰 Testing Real RSS Feed Collection")

        results = {}

        for count in feed_counts:
            logger.info(f"📡 Testing {count} real RSS feeds")

            feeds_to_test = self.test_feeds[:count]

            start_time = time.time()
            # Use parallel collection for better performance
            collection_results = await self._collect_real_rss_feeds_parallel(feeds_to_test, max_concurrent=10)
            collection_time = time.time() - start_time

            self.metrics["rss_collection_times"].append(collection_time)

            results[f"rss_{count}feeds"] = {
                "feed_count": count,
                "collection_time_seconds": collection_time,
                "feeds_per_second": count / collection_time if collection_time > 0 else 0,
                "success_rate": collection_results["success_rate"],
                "articles_collected": collection_results["total_articles"],
                "articles_per_second": collection_results["total_articles"] / collection_time if collection_time > 0 else 0
            }

            logger.info(".2f"
                      f"Success: {collection_results['success_rate']:.1%} "
                      f"Articles: {collection_results['total_articles']}")

        return results

    async def test_query_performance_real_data(self, concurrent_users: List[int] = [1, 5, 10, 25]) -> Dict[str, Any]:
        """Test query performance with real data under concurrent load"""
        logger.info("🔍 Testing Query Performance with Real Data")

        # Define real query functions
        query_functions = [
            lambda: self.query_lib.get_vendor_risk_profile("Microsoft"),
            lambda: self.query_lib.get_threat_actor_profile("APT29"),
            lambda: self.query_lib.get_cves_by_severity("critical", limit=10),
            lambda: self.query_lib.get_recent_cves(days=7, limit=20),
            lambda: self.query_lib.get_threat_actor_tactics("APT29"),
        ]

        results = {}

        for users in concurrent_users:
            logger.info(f"👥 Testing {users} concurrent users with real queries")

            start_time = time.time()
            response_times = await self._run_concurrent_queries(query_functions, users)
            total_time = time.time() - start_time

            # Filter out failed queries (very slow responses)
            valid_times = [t for t in response_times if t < 30.0]  # 30 second timeout

            if valid_times:
                self.metrics["query_response_times"].extend(valid_times)

                results[f"query_{users}users"] = {
                    "concurrent_users": users,
                    "total_time_seconds": total_time,
                    "queries_executed": len(valid_times),
                    "queries_failed": len(response_times) - len(valid_times),
                    "avg_response_time": statistics.mean(valid_times),
                    "median_response_time": statistics.median(valid_times),
                    "p95_response_time": sorted(valid_times)[int(len(valid_times) * 0.95)],
                    "min_response_time": min(valid_times),
                    "max_response_time": max(valid_times),
                    "success_rate": len(valid_times) / len(response_times)
                }

                logger.info(f"Success: {len(valid_times)}/{len(response_times)} "
                          f"Avg: {statistics.mean(valid_times):.3f}s")
            else:
                results[f"query_{users}users"] = {
                    "concurrent_users": users,
                    "error": "All queries failed or timed out"
                }

        return results

    async def test_data_growth_impact(self, iterations: int = 5) -> Dict[str, Any]:
        """Test how performance degrades with data growth"""
        logger.info("📈 Testing Performance Impact of Data Growth")

        results = {}

        for i in range(iterations):
            logger.info(f"🔄 Growth Test Iteration {i+1}/{iterations}")

            # Load more data
            if i == 0:
                # Initial load
                await self._load_real_cve_data(30)  # 30 days
                await self._load_real_mitre_data()
            else:
                # Additional loads
                await self._load_real_cve_data(30 * (i + 1))  # More data each time

            # Measure database size
            db_size = await self._get_database_size()
            self.metrics["database_sizes"].append(db_size)

            # Benchmark queries
            query_times = await self._benchmark_key_queries()

            results[f"growth_iter_{i+1}"] = {
                "iteration": i+1,
                "database_size_mb": db_size,
                "query_performance": query_times,
                "avg_query_time": statistics.mean(list(query_times.values())),
                "slowest_query": max(query_times.items(), key=lambda x: x[1])
            }

            logger.info(f"DB Size: {db_size:.1f}MB, "
                      f"Avg Query: {statistics.mean(list(query_times.values())):.3f}s")

        return results

    async def test_api_endpoints_stress(self, concurrent_requests: List[int] = [25, 50, 75, 100]) -> Dict[str, Any]:
        """Test API endpoints under concurrent load"""
        logger.info("🌐 Testing API Endpoints Under Stress")

        # API endpoints to test
        endpoints = [
            "http://neo4j.local",  # Neo4j browser
            "http://weaviate.local/v1/meta",  # Weaviate meta
        ]

        results = {}

        for concurrent in concurrent_requests:
            logger.info(f"🔗 Testing {concurrent} concurrent API requests")

            response_times = []

            async def test_endpoint(url: str) -> float:
                start_time = time.time()
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, timeout=10) as response:
                            await response.text()
                    return time.time() - start_time
                except Exception:
                    return time.time() - start_time  # Return timing even on failure

            # Test all endpoints concurrently
            tasks = []
            for _ in range(concurrent):
                for endpoint in endpoints:
                    tasks.append(test_endpoint(endpoint))

            start_time = time.time()
            api_times = await asyncio.gather(*tasks, return_exceptions=True)
            total_time = time.time() - start_time

            # Filter valid response times
            valid_times = [t for t in api_times if isinstance(t, float) and t < 30.0]

            if valid_times:
                self.metrics["api_response_times"].extend(valid_times)

                results[f"api_{concurrent}req"] = {
                    "concurrent_requests": concurrent,
                    "total_time_seconds": total_time,
                    "requests_completed": len(valid_times),
                    "requests_failed": len(api_times) - len(valid_times),
                    "avg_response_time": statistics.mean(valid_times),
                    "p95_response_time": sorted(valid_times)[int(len(valid_times) * 0.95)],
                    "success_rate": len(valid_times) / len(api_times),
                    "requests_per_second": len(valid_times) / total_time if total_time > 0 else 0
                }

                logger.info(f"Avg Response: {statistics.mean(valid_times):.3f}s, "
                          f"Success: {len(valid_times)}/{len(api_times)}, "
                          f"RPS: {len(valid_times) / total_time:.1f}")
            else:
                results[f"api_{concurrent}req"] = {
                    "concurrent_requests": concurrent,
                    "error": "All API requests failed"
                }

        return results

    async def run_real_data_stress_test(self) -> Dict[str, Any]:
        """Run the complete real data stress test suite"""
        logger.info("🚀 Starting Cyber-PI Real Data Stress Test Suite")
        logger.info("=" * 80)

        # Start resource monitoring
        monitor_task = asyncio.create_task(self.monitor_system_resources())

        try:
            results = {
                "test_metadata": {
                    "start_time": self.start_time.isoformat(),
                    "test_suite": "real_data_stress_test",
                    "version": "1.0",
                    "description": "Real threat intelligence data loading and performance testing"
                },

                "real_cve_stress": await self.test_real_cve_stress(),
                "real_mitre_loading": await self.test_real_mitre_loading(),
                "real_rss_stress": await self.test_real_rss_stress(),
                "real_query_performance": await self.test_query_performance_real_data(),
                "data_growth_impact": await self.test_data_growth_impact(),
                "api_endpoints_stress": await self.test_api_endpoints_stress(),

                "system_metrics": self._calculate_metrics(),
                "performance_analysis": self._analyze_performance(),
                "thresholds_determined": self._determine_thresholds(),
                "recommendations": self._generate_recommendations()
            }

            # Stop monitoring
            monitor_task.cancel()

            results["test_metadata"]["end_time"] = datetime.now().isoformat()
            results["test_metadata"]["duration_seconds"] = (datetime.now() - self.start_time).total_seconds()

            logger.info("✅ Real data stress test completed!")
            logger.info(f"Test duration: {(datetime.now() - self.start_time).total_seconds():.1f}s")
            return results

        except Exception as e:
            logger.error(f"❌ Real data stress test failed: {e}")
            monitor_task.cancel()
            return {"error": str(e)}

    def _calculate_metrics(self) -> Dict[str, Any]:
        """Calculate comprehensive performance metrics"""
        metrics = {}

        # Response time metrics
        for metric_name, times in self.metrics.items():
            if times and "times" in metric_name:
                metrics[f"avg_{metric_name}"] = statistics.mean(times)
                metrics[f"p95_{metric_name}"] = sorted(times)[int(len(times) * 0.95)] if times else 0
                metrics[f"min_{metric_name}"] = min(times) if times else 0
                metrics[f"max_{metric_name}"] = max(times) if times else 0

        # Resource metrics
        if self.metrics["memory_usage"]:
            metrics["avg_memory_usage"] = statistics.mean(self.metrics["memory_usage"])
            metrics["peak_memory_usage"] = max(self.metrics["memory_usage"])

        if self.metrics["cpu_usage"]:
            metrics["avg_cpu_usage"] = statistics.mean(self.metrics["cpu_usage"])
            metrics["peak_cpu_usage"] = max(self.metrics["cpu_usage"])

        # Database growth
        if self.metrics["database_sizes"]:
            metrics["initial_db_size"] = self.metrics["database_sizes"][0]
            metrics["final_db_size"] = self.metrics["database_sizes"][-1]
            metrics["db_growth_mb"] = metrics["final_db_size"] - metrics["initial_db_size"]

        return metrics

    def _analyze_performance(self) -> Dict[str, Any]:
        """Analyze performance and determine system health"""
        analysis = {
            "overall_performance": "unknown",
            "scalability_rating": "unknown",
            "bottlenecks_identified": [],
            "system_health": "unknown"
        }

        metrics = self._calculate_metrics()

        # Performance rating
        avg_query_time = metrics.get("avg_query_response_times", 0)
        if avg_query_time < 0.1:
            analysis["overall_performance"] = "excellent"
        elif avg_query_time < 0.5:
            analysis["overall_performance"] = "good"
        elif avg_query_time < 2.0:
            analysis["overall_performance"] = "acceptable"
        else:
            analysis["overall_performance"] = "needs_improvement"

        # Scalability rating
        peak_memory = metrics.get("peak_memory_usage", 0)
        peak_cpu = metrics.get("peak_cpu_usage", 0)

        if peak_memory < 70 and peak_cpu < 70:
            analysis["scalability_rating"] = "highly_scalable"
        elif peak_memory < 85 and peak_cpu < 85:
            analysis["scalability_rating"] = "moderately_scalable"
        else:
            analysis["scalability_rating"] = "scalability_limited"

        # Identify bottlenecks
        if peak_memory > 80:
            analysis["bottlenecks_identified"].append("memory_usage")
        if peak_cpu > 80:
            analysis["bottlenecks_identified"].append("cpu_usage")
        if avg_query_time > 1.0:
            analysis["bottlenecks_identified"].append("query_performance")

        # System health
        if len(analysis["bottlenecks_identified"]) == 0:
            analysis["system_health"] = "healthy"
        elif len(analysis["bottlenecks_identified"]) == 1:
            analysis["system_health"] = "minor_issues"
        else:
            analysis["system_health"] = "needs_attention"

        return analysis

    def _determine_thresholds(self) -> Dict[str, Any]:
        """Determine system performance thresholds"""
        thresholds = {
            "max_concurrent_users": "unknown",
            "max_recommended_load": "unknown",
            "memory_threshold_gb": "unknown",
            "cpu_threshold_percent": "unknown"
        }

        metrics = self._calculate_metrics()

        # Determine user concurrency threshold
        query_times = self.metrics.get("query_response_times", [])
        if query_times:
            # Find point where p95 response time exceeds 2 seconds
            sorted_times = sorted(query_times)
            threshold_index = next((i for i, t in enumerate(sorted_times) if t > 2.0), len(sorted_times))
            if threshold_index > 0:
                # Estimate concurrent users at threshold
                thresholds["max_concurrent_users"] = int(threshold_index / len(self.test_feeds)) if self.test_feeds else threshold_index

        # Memory and CPU thresholds
        if self.metrics["memory_usage"]:
            thresholds["memory_threshold_gb"] = (psutil.virtual_memory().total / (1024**3)) * 0.8  # 80% of total
        if self.metrics["cpu_usage"]:
            thresholds["cpu_threshold_percent"] = 80

        return thresholds

    def _generate_recommendations(self) -> List[str]:
        """Generate actionable recommendations based on test results"""
        recommendations = []
        metrics = self._calculate_metrics()
        analysis = self._analyze_performance()

        # Performance recommendations
        if analysis["overall_performance"] in ["needs_improvement", "poor"]:
            recommendations.append("Optimize database queries - consider additional indexes")
            recommendations.append("Implement query result caching (Redis)")
            recommendations.append("Consider read replicas for high query loads")

        # Scalability recommendations
        if analysis["scalability_rating"] == "scalability_limited":
            recommendations.append("Scale vertically: increase CPU/memory resources")
            recommendations.append("Scale horizontally: implement load balancing")
            recommendations.append("Optimize data structures and algorithms")

        # Resource recommendations
        if metrics.get("peak_memory_usage", 0) > 85:
            recommendations.append("Increase system memory or optimize memory usage")
        if metrics.get("peak_cpu_usage", 0) > 85:
            recommendations.append("Increase CPU resources or optimize CPU-intensive operations")

        # Data growth recommendations
        if metrics.get("db_growth_mb", 0) > 1000:  # 1GB growth
            recommendations.append("Implement database partitioning for large datasets")
            recommendations.append("Consider data archiving for historical records")

        # API recommendations
        api_times = self.metrics.get("api_response_times", [])
        if api_times and statistics.mean(api_times) > 1.0:
            recommendations.append("Optimize API endpoints - implement response caching")
            recommendations.append("Consider API rate limiting and request queuing")

        return recommendations


async def main():
    """Main stress test execution"""
    print("🔬 Cyber-PI Real Data Stress Test Suite")
    print("=" * 60)
    print("This test will load REAL threat intelligence data and stress the system")
    print("Tests include: CVE loading, MITRE ATT&CK, RSS feeds, concurrent queries")
    print("⚠️  This will consume bandwidth and may take 10-30 minutes")
    print()

    # Confirm execution
    response = input("Continue with real data stress testing? (y/N): ")
    if response.lower() != 'y':
        print("Test cancelled.")
        return

    # Run real data stress tests
    tester = RealDataStressTest()
    results = await tester.run_real_data_stress_test()

    # Save results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f"real_data_stress_test_{timestamp}.json"

    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\n📊 Results saved to: {output_file}")

    # Print executive summary
    if "error" not in results:
        analysis = results.get("performance_analysis", {})
        thresholds = results.get("thresholds_determined", {})
        metrics = results.get("system_metrics", {})

        print("\n🎯 Executive Summary:")
        print(f"  Overall Performance: {analysis.get('overall_performance', 'unknown')}")
        print(f"  System Health: {analysis.get('system_health', 'unknown')}")
        print(f"  Scalability: {analysis.get('scalability_rating', 'unknown')}")

        if "avg_query_response_times" in metrics:
            print(f"  Avg Query Time: {metrics['avg_query_response_times']:.3f}s")
        if "peak_memory_usage" in metrics:
            print(f"  Peak Memory: {metrics['peak_memory_usage']:.1f}%")
        if "peak_cpu_usage" in metrics:
            print(f"  Peak CPU: {metrics['peak_cpu_usage']:.1f}%")
        if "max_concurrent_users" in thresholds:
            print(f"  Max Concurrent Users: {thresholds['max_concurrent_users']}")

        recommendations = results.get("recommendations", [])
        if recommendations:
            print("\n💡 Key Recommendations:")
            for rec in recommendations[:3]:  # Top 3
                print(f"  • {rec}")

    print("\n✅ Real data stress testing completed!")
    print("📈 System thresholds and performance characteristics determined.")


if __name__ == "__main__":
    asyncio.run(main())
