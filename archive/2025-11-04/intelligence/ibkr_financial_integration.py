#!/usr/bin/env python3
"""
IBKR Financial Intelligence Integration
Connects Interactive Brokers real-time data to Financial Threat Analyzer
"""

import sys
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

# Add ibkr-financial-intel to path
ibkr_path = Path(__file__).parent.parent.parent.parent / 'ibkr-financial-intel'
sys.path.insert(0, str(ibkr_path / 'src'))
sys.path.insert(0, str(ibkr_path))

# Add current directory to path for local imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from src.connection_manager import IBKRConnectionManager

# Import financial threat analyzer from same directory
try:
    from financial_threat_analyzer import FinancialThreatAnalyzer
except ImportError:
    # Fallback: direct import
    import importlib.util
    fta_path = current_dir / "financial_threat_analyzer.py"
    spec = importlib.util.spec_from_file_location("financial_threat_analyzer", fta_path)
    fta_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fta_module)
    FinancialThreatAnalyzer = fta_module.FinancialThreatAnalyzer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IBKRFinancialThreatIntegration:
    """
    Integration between IBKR real-time data and Financial Threat Analyzer.
    
    Pulls real market data from Interactive Brokers and analyzes for
    pre-breach indicators using Llama 4 16x17B.
    """
    
    def __init__(
        self,
        ibkr_host: str = "127.0.0.1",
        ibkr_port: int = 4002,  # IB Gateway paper trading
        client_id: int = 1
    ):
        self.ibkr = IBKRConnectionManager(
            host=ibkr_host,
            port=ibkr_port,
            client_id=client_id
        )
        self.analyzer = FinancialThreatAnalyzer()
        
        logger.info("🔗 IBKR Financial Threat Integration initialized")
        logger.info(f"   IBKR: {ibkr_host}:{ibkr_port}")
        logger.info(f"   Analyzer: Llama 4 16x17B on dual A6000s")
    
    async def connect(self):
        """Connect to IBKR Gateway/TWS."""
        logger.info("📡 Connecting to IBKR...")
        success = await self.ibkr.connect()
        
        if success:
            logger.info("✅ Connected to IBKR")
            return True
        else:
            logger.error("❌ Failed to connect to IBKR")
            return False
    
    async def get_stock_data(self, ticker: str) -> Optional[Dict]:
        """
        Get real-time stock data from IBKR.
        
        Returns data suitable for financial threat analysis.
        """
        try:
            # Get contract
            from ib_async import Stock
            contract = Stock(ticker, 'SMART', 'USD')
            
            # Request market data
            ib = self.ibkr.ib
            ticker_data = ib.reqMktData(contract, '', False, False)
            
            # Wait for data
            await asyncio.sleep(2)
            
            if ticker_data.last:
                return {
                    'ticker': ticker,
                    'price': ticker_data.last,
                    'volume': ticker_data.volume if ticker_data.volume else 0,
                    'bid': ticker_data.bid,
                    'ask': ticker_data.ask,
                    'high': ticker_data.high,
                    'low': ticker_data.low,
                    'close': ticker_data.close,
                }
            else:
                logger.warning(f"⚠️  No data received for {ticker}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error getting data for {ticker}: {e}")
            return None
    
    async def analyze_ticker_with_ibkr_data(self, ticker: str) -> Optional[Dict]:
        """
        Analyze a ticker using real IBKR data.
        
        Args:
            ticker: Stock symbol (e.g., 'UNH', 'AAPL')
            
        Returns:
            Analysis results with threat score
        """
        logger.info(f"📊 Analyzing {ticker} with real IBKR data...")
        
        # Get real market data
        market_data = await self.get_stock_data(ticker)
        
        if not market_data:
            logger.warning(f"⚠️  Skipping {ticker} - no market data")
            return None
        
        # TODO: Add real-time calculations for:
        # - volume_change (compare to 30-day average)
        # - options_activity (put/call ratio)
        # - short_interest (from IBKR)
        # - insider_trading (from external API)
        
        # For now, use market data + placeholder indicators
        analysis_data = {
            **market_data,
            'volume_change': 100.0,  # Placeholder - need historical comparison
            'options_activity': 'Data pending',
            'short_interest': 0.0,  # Placeholder
            'insider_trading': 'Data pending',
            'avg_volume_30d': market_data.get('volume', 0),
            'price_trend_90d': '+0.0%',  # Placeholder
            'industry': 'Unknown',  # Need lookup
            'market_cap': 0,  # Need lookup
        }
        
        # Analyze with Llama 4
        result = await self.analyzer.analyze_stock_anomalies(ticker, analysis_data)
        
        return result
    
    async def batch_analyze(self, tickers: List[str]) -> List[Dict]:
        """
        Analyze multiple tickers with real IBKR data.
        
        Args:
            tickers: List of stock symbols
            
        Returns:
            List of analysis results
        """
        logger.info(f"🚀 Batch analyzing {len(tickers)} tickers with IBKR data")
        
        results = []
        for i, ticker in enumerate(tickers, 1):
            logger.info(f"   [{i}/{len(tickers)}] {ticker}")
            
            result = await self.analyze_ticker_with_ibkr_data(ticker)
            
            if result:
                results.append({
                    'ticker': ticker,
                    'threat_score': result.get('threat_score', 0),
                    'confidence': result.get('confidence', 0),
                    'timestamp': datetime.now().isoformat()
                })
            
            # Rate limiting
            await asyncio.sleep(1)
        
        logger.info(f"✅ Batch complete: {len(results)}/{len(tickers)} analyzed")
        
        return results
    
    async def disconnect(self):
        """Disconnect from IBKR."""
        logger.info("📡 Disconnecting from IBKR...")
        await self.ibkr.disconnect()
        logger.info("✅ Disconnected")


async def main():
    """Demo: Analyze stocks with real IBKR data."""
    
    print("=" * 80)
    print("🔭 IBKR FINANCIAL THREAT INTELLIGENCE")
    print("=" * 80)
    print("Real-time market data + Llama 4 16x17B analysis")
    print()
    
    # Initialize
    integration = IBKRFinancialThreatIntegration()
    
    # Connect to IBKR
    connected = await integration.connect()
    
    if not connected:
        print("❌ Failed to connect to IBKR Gateway/TWS")
        print()
        print("Please ensure:")
        print("  1. IB Gateway or TWS is running")
        print("  2. API connections are enabled")
        print("  3. Port 4002 (paper) or 4001 (live) is accessible")
        return
    
    # Test tickers
    test_tickers = ['AAPL', 'MSFT', 'UNH', 'JPM', 'GOOGL']
    
    print(f"\n📊 Analyzing {len(test_tickers)} tickers with real IBKR data:")
    for ticker in test_tickers:
        print(f"   - {ticker}")
    print()
    
    # Analyze
    results = await integration.batch_analyze(test_tickers)
    
    # Results
    print("\n" + "=" * 80)
    print("📊 RESULTS")
    print("=" * 80)
    
    for result in results:
        print(f"\n{result['ticker']}:")
        print(f"  Threat Score: {result['threat_score']}/100")
        print(f"  Confidence: {result['confidence']}%")
        print(f"  Timestamp: {result['timestamp']}")
    
    # Disconnect
    await integration.disconnect()
    
    print("\n" + "=" * 80)
    print("✅ Analysis complete")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
