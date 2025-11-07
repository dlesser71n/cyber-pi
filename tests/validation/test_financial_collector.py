#!/usr/bin/env python3
"""
Test Financial Threat Collector
Quick test with 5 tickers
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from collectors.financial_threat_collector import FinancialThreatCollector

# Test with just 5 tickers
TEST_WATCHLIST = ['UNH', 'PANW', 'JPM', 'MSFT', 'DAL']


async def main():
    print("="*70)
    print("🧪 TESTING FINANCIAL THREAT COLLECTOR")
    print("="*70)
    print(f"Test watchlist: {', '.join(TEST_WATCHLIST)}")
    print()
    
    collector = FinancialThreatCollector(watchlist=TEST_WATCHLIST)
    
    try:
        summary = await collector.run_collection()
        
        print()
        print("="*70)
        print("✅ TEST COMPLETE")
        print("="*70)
        print(f"Analyzed: {summary['total_analyzed']} tickers")
        print(f"Threats: {summary['threats_found']}")
        print(f"High Priority: {summary['high_priority']}")
        
        if summary['high_threat_tickers']:
            print()
            print("🚨 High Threats:")
            for ticker in summary['high_threat_tickers']:
                threat = next(t for t in summary['threats'] if t['ticker'] == ticker)
                print(f"   {ticker}: {threat['threat_score']}/100")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
