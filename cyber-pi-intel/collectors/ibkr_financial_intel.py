#!/usr/bin/env python3
"""
Interactive Brokers Financial Intelligence Collector
Collects cyber-relevant financial news through IBKR Gateway

ARCHITECTURE:
IBKR API → Redis Highway → Workers → Neo4j/Weaviate

Data Flow:
1. Connect to IBKR Gateway
2. Subscribe to news feeds (BroadTape + Stock-specific)
3. Filter for cyber-relevant content
4. Push to Redis: threat:parsed:{id}
5. Queue to: queue:weaviate, queue:neo4j
6. Workers process (existing infrastructure)
"""

import asyncio
import json
import hashlib
import os
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional
import logging
import redis.asyncio as redis

# IBKR API - using modern ib_async (not legacy ib_insync)
try:
    from ib_async import IB, Stock, Contract, util
    IBKR_AVAILABLE = True
except ImportError:
    IBKR_AVAILABLE = False
    logging.warning("ib_async not installed. Run: pip install ib_async")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IBKRFinancialCollector:
    """
    Collect financial intelligence from Interactive Brokers
    Feeds everything to Redis highway for worker processing
    """

    def __init__(self,
                 gateway_host: str = None,
                 gateway_port: int = None):

        # IBKR Gateway configuration (from environment or defaults)
        self.gateway_host = gateway_host or os.getenv('IBKR_GATEWAY_HOST', '127.0.0.1')
        self.gateway_port = gateway_port or int(os.getenv('IBKR_GATEWAY_PORT', '4002'))

        # Redis configuration (from Kubernetes secrets via environment)
        redis_password = os.getenv('REDIS_PASSWORD', '')
        redis_host = os.getenv('REDIS_HOST', 'redis.cyber-pi-intel.svc.cluster.local')
        redis_port = os.getenv('REDIS_PORT', '6379')

        # Build Redis URL securely
        self.redis_url = f"redis://:{redis_password}@{redis_host}:{redis_port}"

        self.redis_client = None
        self.ib = None if not IBKR_AVAILABLE else IB()

        # Cyber-relevant keywords for filtering
        self.cyber_keywords = [
            'breach', 'hack', 'ransomware', 'cyberattack', 'cyber attack',
            'data leak', 'security incident', 'unauthorized access',
            'malware', 'phishing', 'vulnerability', 'exploit',
            'ddos', 'botnet', 'threat actor', 'apt', 'zero-day',
            'credential theft', 'supply chain attack', 'backdoor'
        ]

        # Financial-cyber correlation keywords
        self.correlation_keywords = [
            'trading halt', 'emergency disclosure', 'material event',
            'sec filing', '8-k filing', 'investigation', 'regulatory',
            'class action', 'lawsuit', 'compliance', 'gdpr', 'hipaa',
            'stock drop', 'unusual activity', 'insider trading'
        ]

        # Tech/Security companies to monitor (stock-specific news)
        self.watchlist = [
            # Security Vendors
            'PANW', 'CRWD', 'ZS', 'FTNT', 'OKTA', 'S', 'CYBR', 'TENB',
            # Cloud Providers
            'MSFT', 'GOOGL', 'AMZN', 'ORCL', 'IBM', 'CRM',
            # Financial Institutions
            'JPM', 'BAC', 'WFC', 'C', 'GS', 'MS',
            # Healthcare
            'UNH', 'CVS', 'CI', 'ANTM', 'HUM',
            # Energy/Critical Infrastructure
            'XOM', 'CVX', 'NEE', 'DUK', 'SO',
            # Retail (breach targets)
            'WMT', 'TGT', 'COST', 'HD', 'LOW'
        ]

        # BroadTape news feeds (general market news)
        self.broadtape_feeds = [
            'BRFG',    # Briefing.com General
            'BRFUPDN', # Briefing.com Analyst Actions
            'DJNL'     # Dow Jones Newsletters (free with API)
        ]

    async def connect(self):
        """Connect to Redis and IBKR Gateway"""
        # Connect to Redis (THE HIGHWAY)
        self.redis_client = await redis.from_url(
            self.redis_url,
            encoding="utf-8",
            decode_responses=True
        )
        await self.redis_client.ping()
        logger.info("✅ Connected to Redis highway")

        # Connect to IBKR Gateway
        if not IBKR_AVAILABLE:
            logger.error("❌ ib_async not available")
            return False

        try:
            await self.ib.connectAsync(self.gateway_host, self.gateway_port, clientId=1)
            logger.info(f"✅ Connected to IBKR Gateway at {self.gateway_host}:{self.gateway_port}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect to IBKR Gateway: {e}")
            logger.info("Make sure IB Gateway is running and port is correct")
            logger.info("TWS: port 7496/7497, Gateway: port 4001/4002")
            return False

    async def get_news_providers(self) -> List:
        """Get list of subscribed news providers"""
        try:
            providers = self.ib.reqNewsProviders()
            logger.info(f"📰 Available news providers: {len(providers)}")
            for provider in providers:
                logger.info(f"  - {provider.code}: {provider.name}")
            return providers
        except Exception as e:
            logger.error(f"Failed to get news providers: {e}")
            return []

    async def collect_broadtape_news(self) -> List[Dict]:
        """
        Collect general market news (BroadTape)
        NOT tied to specific stocks - general cyber/security news
        """
        items = []

        for feed_code in self.broadtape_feeds:
            try:
                # Create news contract for BroadTape
                contract = Contract()
                contract.symbol = feed_code
                contract.secType = 'NEWS'
                contract.exchange = 'NEWS'

                # Get recent news (last 24 hours)
                news_articles = self.ib.reqHistoricalNews(
                    conId=0,
                    providerCodes=feed_code,
                    startDateTime='',
                    endDateTime='',
                    totalResults=50
                )

                for article in news_articles:
                    # Filter for cyber-relevant content
                    if not self._is_cyber_relevant(article.headline + ' ' + article.text):
                        continue

                    # Create threat data following Cyber-PI standard format
                    threat_data = await self._create_threat_data(
                        title=article.headline,
                        content=article.text,
                        source=f"IBKR {feed_code}",
                        article_url=f"ibkr://{article.providerCode}/{article.articleId}",
                        metadata={
                            'provider': article.providerCode,
                            'article_id': article.articleId,
                            'sentiment': article.sentiment,
                            'feed_type': 'broadtape',
                            'financial_intelligence': True
                        }
                    )

                    items.append(threat_data)

                logger.info(f"✅ {feed_code}: {len([i for i in items if feed_code in i.get('source', '')])} cyber-relevant")

            except Exception as e:
                logger.error(f"Failed to collect from {feed_code}: {e}")

        return items

    async def collect_watchlist_news(self) -> List[Dict]:
        """
        Collect stock-specific news for monitored companies
        Detects potential breaches via stock movement + news
        """
        items = []

        for symbol in self.watchlist[:10]:  # Start with first 10, can expand
            try:
                # Qualify the stock contract
                stock = Stock(symbol, 'SMART', 'USD')
                await self.ib.qualifyContractsAsync(stock)

                # Get all available news providers
                providers = await self.get_news_providers()
                provider_codes = '+'.join(p.code for p in providers)

                # Get recent news for this stock
                headlines = self.ib.reqHistoricalNews(
                    conId=stock.conId,
                    providerCodes=provider_codes,
                    startDateTime='',
                    endDateTime='',
                    totalResults=10
                )

                for article in headlines:
                    # Check if cyber-relevant OR financial-anomaly
                    if not (self._is_cyber_relevant(article.headline) or
                            self._is_financial_anomaly(article.headline)):
                        continue

                    # Fetch full article if available
                    try:
                        full_article = self.ib.reqNewsArticle(
                            article.providerCode,
                            article.articleId
                        )
                        content = full_article.articleText if full_article else article.headline
                    except:
                        content = article.headline

                    # Create threat data
                    threat_data = await self._create_threat_data(
                        title=f"{symbol}: {article.headline}",
                        content=content,
                        source=f"IBKR Stock News - {article.providerCode}",
                        article_url=f"ibkr://{article.providerCode}/{article.articleId}",
                        metadata={
                            'company_symbol': symbol,
                            'provider': article.providerCode,
                            'article_id': article.articleId,
                            'feed_type': 'stock_specific',
                            'financial_intelligence': True,
                            'watchlist': True
                        }
                    )

                    items.append(threat_data)

                logger.info(f"✅ {symbol}: {len([i for i in items if symbol in i.get('title', '')])} relevant")

            except Exception as e:
                logger.error(f"Failed to collect news for {symbol}: {e}")

        return items

    async def _create_threat_data(self,
                                   title: str,
                                   content: str,
                                   source: str,
                                   article_url: str,
                                   metadata: Dict) -> Dict:
        """
        Create standardized threat data following Cyber-PI format
        Returns dict ready for Redis highway
        """
        # Generate threat ID
        id_string = title + article_url + datetime.now(timezone.utc).isoformat()
        threat_id = f"threat_{hashlib.sha256(id_string.encode()).hexdigest()[:16]}"

        # Determine severity
        severity = self._assess_severity(title, content)

        # Extract companies mentioned
        companies = self._extract_companies(title, content)

        # Build standardized threat data
        threat_data = {
            "threatId": threat_id,
            "title": title[:500],
            "content": content[:10000],
            "source": source,
            "sourceUrl": article_url,
            "industry": self._infer_industry(companies),
            "severity": severity,
            "threatType": ["financial-intelligence", "early-warning"],
            "cves": [],  # Financial news won't have CVEs initially
            "publishedDate": datetime.now(timezone.utc).isoformat(),
            "ingestedDate": datetime.now(timezone.utc).isoformat(),
            "metadata": metadata,
            "tags": ["ibkr", "financial", "early-warning"] + companies
        }

        return threat_data

    async def push_to_redis_highway(self, items: List[Dict]) -> int:
        """
        Push collected items to Redis highway
        Pattern: threat:parsed:{id} + queue:weaviate + queue:neo4j
        """
        queued = 0

        for threat_data in items:
            threat_id = threat_data['threatId']

            # Check if already processed
            existing = await self.redis_client.get(f"threat:parsed:{threat_id}")
            if existing:
                continue

            try:
                # 1. Store parsed threat data (7 day TTL)
                await self.redis_client.setex(
                    f"threat:parsed:{threat_id}",
                    86400 * 7,
                    json.dumps(threat_data)
                )

                # 2. Queue for Weaviate (vector storage)
                await self.redis_client.lpush("queue:weaviate", threat_id)

                # 3. Queue for Neo4j (graph storage)
                await self.redis_client.lpush("queue:neo4j", threat_id)

                queued += 1

            except Exception as e:
                logger.error(f"Failed to push {threat_id} to Redis: {e}")

        logger.info(f"✅ Pushed {queued} items to Redis highway")
        return queued

    def _is_cyber_relevant(self, text: str) -> bool:
        """Check if content is cyber-security relevant"""
        text_lower = text.lower()
        return any(kw in text_lower for kw in self.cyber_keywords)

    def _is_financial_anomaly(self, text: str) -> bool:
        """Check if content indicates potential security incident via financial signals"""
        text_lower = text.lower()
        return any(kw in text_lower for kw in self.correlation_keywords)

    def _assess_severity(self, title: str, content: str) -> str:
        """Assess threat severity based on content"""
        combined = (title + ' ' + content).lower()

        # Critical indicators
        if any(kw in combined for kw in ['breach', 'ransomware', 'trading halt', 'emergency']):
            return 'critical'

        # High indicators
        if any(kw in combined for kw in ['hack', 'attack', 'investigation', 'lawsuit']):
            return 'high'

        # Medium indicators
        if any(kw in combined for kw in ['vulnerability', 'patch', 'update', 'incident']):
            return 'medium'

        return 'low'

    def _extract_companies(self, title: str, content: str) -> List[str]:
        """Extract company mentions (tickers from watchlist)"""
        combined = title + ' ' + content
        mentioned = []

        for symbol in self.watchlist:
            if symbol in combined:
                mentioned.append(symbol)

        return mentioned

    def _infer_industry(self, companies: List[str]) -> List[str]:
        """Infer industry from company symbols"""
        industries = set()

        # Simple mapping (can be expanded)
        security_vendors = ['PANW', 'CRWD', 'ZS', 'FTNT', 'OKTA', 'S', 'CYBR', 'TENB']
        financial = ['JPM', 'BAC', 'WFC', 'C', 'GS', 'MS']
        healthcare = ['UNH', 'CVS', 'CI', 'ANTM', 'HUM']
        energy = ['XOM', 'CVX', 'NEE', 'DUK', 'SO']
        retail = ['WMT', 'TGT', 'COST', 'HD', 'LOW']

        for company in companies:
            if company in security_vendors:
                industries.add("Security")
            elif company in financial:
                industries.add("Financial")
            elif company in healthcare:
                industries.add("Healthcare")
            elif company in energy:
                industries.add("Energy")
            elif company in retail:
                industries.add("Retail")

        return list(industries) if industries else ["General"]

    async def collect_all(self) -> int:
        """
        Main collection method
        Collects from all sources and pushes to Redis highway
        """
        print("\n" + "="*60)
        print("💰 IBKR FINANCIAL INTELLIGENCE COLLECTOR")
        print("="*60)
        print()

        # Connect to infrastructure
        connected = await self.connect()
        if not connected:
            logger.error("❌ Failed to establish connections")
            return 0

        all_items = []

        # 1. Collect BroadTape news (general market)
        print("📰 Collecting BroadTape News (General Market)...")
        broadtape = await self.collect_broadtape_news()
        all_items.extend(broadtape)

        # 2. Collect Watchlist news (company-specific)
        print("📊 Collecting Watchlist News (Stock-Specific)...")
        watchlist = await self.collect_watchlist_news()
        all_items.extend(watchlist)

        # 3. Push everything to Redis highway
        print(f"\n🚀 Pushing {len(all_items)} items to Redis highway...")
        queued = await self.push_to_redis_highway(all_items)

        # Summary
        print("\n" + "="*60)
        print("📊 COLLECTION SUMMARY")
        print("="*60)
        print(f"BroadTape News:     {len(broadtape):>6} items")
        print(f"Watchlist News:     {len(watchlist):>6} items")
        print(f"Total Collected:    {len(all_items):>6} items")
        print(f"Queued to Redis:    {queued:>6} items")
        print("="*60)
        print()
        print("✅ Items now in Redis highway")
        print("   → Workers will process to Neo4j & Weaviate")
        print()

        return queued

    async def close(self):
        """Clean up connections"""
        if self.redis_client:
            await self.redis_client.aclose()
        if self.ib and self.ib.isConnected():
            self.ib.disconnect()


async def main():
    """Test the collector"""
    collector = IBKRFinancialCollector()

    try:
        total = await collector.collect_all()
        print(f"✅ Successfully collected and queued {total} financial intelligence items")
    except Exception as e:
        logger.error(f"Collection failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await collector.close()


if __name__ == "__main__":
    asyncio.run(main())
