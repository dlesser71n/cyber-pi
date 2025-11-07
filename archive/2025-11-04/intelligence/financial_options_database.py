#!/usr/bin/env python3
"""
Financial Options Database (Security-Inspired)
Treats options data like network traffic: capture, store, query instantly

Architecture:
- Ingest from free APIs (Yahoo Finance)
- Store in Redis (like SIEM database)
- Query instantly (<1ms)
- Pattern matching (like IDS signatures)
"""

import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict

import redis.asyncio as redis
import yfinance as yf

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class OptionsSnapshot:
    """Options data snapshot"""
    ticker: str
    expiration: str
    timestamp: str
    puts: Dict
    calls: Dict
    
    def to_dict(self):
        return asdict(self)


class FinancialOptionsDatabase:
    """
    Redis-based options database
    Like a SIEM for financial data
    """
    
    def __init__(self, redis_url: str = "redis://localhost:32379"):
        self.redis_url = redis_url
        self._redis: Optional[redis.Redis] = None
        self.ttl = 900  # 15 minutes (Yahoo Finance update frequency)
        
        logger.info("📊 Financial Options Database initialized")
        logger.info(f"   Redis: {redis_url}")
        logger.info(f"   TTL: {self.ttl}s (15 minutes)")
    
    async def connect(self):
        """Connect to Redis"""
        if not self._redis:
            self._redis = await redis.from_url(
                self.redis_url,
                decode_responses=True
            )
            logger.info("✅ Connected to Redis")
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self._redis:
            await self._redis.close()
            self._redis = None
    
    async def ingest_ticker(self, ticker: str) -> int:
        """
        Ingest options data for a ticker
        
        Args:
            ticker: Stock symbol
            
        Returns:
            Number of expirations ingested
        """
        try:
            # Get options data from Yahoo Finance (FREE!)
            stock = yf.Ticker(ticker)
            
            # Get all expirations
            expirations = stock.options
            
            if not expirations:
                logger.warning(f"No options data for {ticker}")
                return 0
            
            count = 0
            for expiration in expirations:
                # Get options chain
                chain = stock.option_chain(expiration)
                
                # Create snapshot
                snapshot = OptionsSnapshot(
                    ticker=ticker,
                    expiration=expiration,
                    timestamp=datetime.now().isoformat(),
                    puts=self._serialize_dataframe(chain.puts),
                    calls=self._serialize_dataframe(chain.calls)
                )
                
                # Store in Redis
                key = f"options:{ticker}:{expiration}"
                await self._redis.hset(
                    key,
                    mapping={
                        'ticker': snapshot.ticker,
                        'expiration': snapshot.expiration,
                        'timestamp': snapshot.timestamp,
                        'puts': json.dumps(snapshot.puts),
                        'calls': json.dumps(snapshot.calls)
                    }
                )
                
                # Set TTL
                await self._redis.expire(key, self.ttl)
                
                count += 1
            
            logger.info(f"✅ Ingested {ticker}: {count} expirations")
            return count
            
        except Exception as e:
            logger.error(f"Error ingesting {ticker}: {e}")
            return 0
    
    async def ingest_watchlist(self, watchlist: List[str]) -> Dict:
        """
        Ingest options data for entire watchlist (parallel)
        
        Args:
            watchlist: List of tickers
            
        Returns:
            Ingestion summary
        """
        logger.info(f"📥 Ingesting {len(watchlist)} tickers...")
        
        start = datetime.now()
        
        # Ingest all tickers in parallel
        results = await asyncio.gather(*[
            self.ingest_ticker(ticker)
            for ticker in watchlist
        ], return_exceptions=True)
        
        # Count successes
        successful = sum(1 for r in results if isinstance(r, int) and r > 0)
        failed = len(watchlist) - successful
        total_expirations = sum(r for r in results if isinstance(r, int))
        
        elapsed = (datetime.now() - start).total_seconds()
        
        summary = {
            'total_tickers': len(watchlist),
            'successful': successful,
            'failed': failed,
            'total_expirations': total_expirations,
            'elapsed_seconds': elapsed,
            'tickers_per_second': len(watchlist) / elapsed if elapsed > 0 else 0
        }
        
        logger.info(f"✅ Ingestion complete: {successful}/{len(watchlist)} tickers in {elapsed:.1f}s")
        
        return summary
    
    async def query_ticker(self, ticker: str) -> List[OptionsSnapshot]:
        """
        Query options data for a ticker (instant!)
        
        Args:
            ticker: Stock symbol
            
        Returns:
            List of options snapshots
        """
        # Get all keys for this ticker
        pattern = f"options:{ticker}:*"
        keys = []
        async for key in self._redis.scan_iter(match=pattern):
            keys.append(key)
        
        if not keys:
            return []
        
        # Get all snapshots
        snapshots = []
        for key in keys:
            data = await self._redis.hgetall(key)
            if data:
                snapshot = OptionsSnapshot(
                    ticker=data['ticker'],
                    expiration=data['expiration'],
                    timestamp=data['timestamp'],
                    puts=json.loads(data['puts']),
                    calls=json.loads(data['calls'])
                )
                snapshots.append(snapshot)
        
        return snapshots
    
    async def scan_all_tickers(self) -> List[str]:
        """
        Get list of all tickers in database
        
        Returns:
            List of ticker symbols
        """
        tickers = set()
        async for key in self._redis.scan_iter(match="options:*"):
            # Extract ticker from key (options:TICKER:expiration)
            parts = key.split(':')
            if len(parts) >= 2:
                tickers.add(parts[1])
        
        return sorted(list(tickers))
    
    async def get_stats(self) -> Dict:
        """
        Get database statistics
        
        Returns:
            Statistics dictionary
        """
        tickers = await self.scan_all_tickers()
        
        # Count total keys
        total_keys = 0
        async for _ in self._redis.scan_iter(match="options:*"):
            total_keys += 1
        
        return {
            'total_tickers': len(tickers),
            'total_snapshots': total_keys,
            'tickers': tickers
        }
    
    def _serialize_dataframe(self, df) -> Dict:
        """Convert pandas DataFrame to dict"""
        if df is None or df.empty:
            return {}
        
        # Convert to dict with relevant columns
        return {
            'strikes': df['strike'].tolist() if 'strike' in df else [],
            'volumes': df['volume'].tolist() if 'volume' in df else [],
            'open_interest': df['openInterest'].tolist() if 'openInterest' in df else [],
            'last_price': df['lastPrice'].tolist() if 'lastPrice' in df else [],
            'bid': df['bid'].tolist() if 'bid' in df else [],
            'ask': df['ask'].tolist() if 'ask' in df else [],
            'implied_volatility': df['impliedVolatility'].tolist() if 'impliedVolatility' in df else [],
        }


async def test_database():
    """Test the database"""
    
    print("="*70)
    print("🧪 TESTING FINANCIAL OPTIONS DATABASE")
    print("="*70)
    print()
    
    db = FinancialOptionsDatabase()
    await db.connect()
    
    # Test with 5 tickers
    watchlist = ['UNH', 'PANW', 'JPM', 'MSFT', 'DAL']
    
    # Ingest
    print("📥 Ingesting watchlist...")
    summary = await db.ingest_watchlist(watchlist)
    
    print()
    print("📊 Ingestion Summary:")
    print(f"   Tickers: {summary['successful']}/{summary['total_tickers']}")
    print(f"   Expirations: {summary['total_expirations']}")
    print(f"   Time: {summary['elapsed_seconds']:.1f}s")
    print(f"   Speed: {summary['tickers_per_second']:.1f} tickers/sec")
    print()
    
    # Query
    print("🔍 Querying UNH...")
    snapshots = await db.query_ticker('UNH')
    print(f"   Found {len(snapshots)} expirations")
    
    if snapshots:
        snap = snapshots[0]
        puts_count = len(snap.puts.get('strikes', []))
        calls_count = len(snap.calls.get('strikes', []))
        print(f"   Expiration: {snap.expiration}")
        print(f"   Puts: {puts_count} strikes")
        print(f"   Calls: {calls_count} strikes")
    
    print()
    
    # Stats
    stats = await db.get_stats()
    print("📊 Database Stats:")
    print(f"   Total tickers: {stats['total_tickers']}")
    print(f"   Total snapshots: {stats['total_snapshots']}")
    print(f"   Tickers: {', '.join(stats['tickers'])}")
    
    await db.disconnect()
    
    print()
    print("="*70)
    print("✅ TEST COMPLETE")
    print("="*70)


if __name__ == "__main__":
    asyncio.run(test_database())
