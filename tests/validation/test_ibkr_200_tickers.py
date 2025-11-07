#!/usr/bin/env python3
"""
200 Ticker Analysis with Real IBKR Data + Llama 4 16x17B
"""

import sys
import asyncio
import time
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent / 'src' / 'intelligence'))
from ibkr_financial_integration import IBKRFinancialThreatIntegration


# 200 Real Tickers - Mix of sectors for comprehensive analysis
TICKERS_200 = [
    # Mega Cap Tech (20)
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'AVGO', 'ORCL', 'ADBE',
    'CRM', 'CSCO', 'ACN', 'INTC', 'AMD', 'QCOM', 'TXN', 'INTU', 'IBM', 'NOW',
    
    # Healthcare (30) - High-value breach targets
    'UNH', 'JNJ', 'LLY', 'ABBV', 'MRK', 'TMO', 'ABT', 'DHR', 'PFE', 'BMY',
    'CVS', 'CI', 'HUM', 'ANTM', 'MOH', 'CNC', 'HCA', 'DGX', 'IDXX', 'ISRG',
    'SYK', 'BSX', 'EW', 'ZBH', 'BAX', 'BDX', 'RMD', 'ALGN', 'HOLX', 'DXCM',
    
    # Financial Services (30)
    'JPM', 'BAC', 'WFC', 'C', 'GS', 'MS', 'BLK', 'SCHW', 'AXP', 'SPGI',
    'USB', 'PNC', 'TFC', 'COF', 'BK', 'STT', 'NTRS', 'KEY', 'CFG', 'FITB',
    'HBAN', 'RF', 'CMA', 'ZION', 'SIVB', 'ALLY', 'DFS', 'SYF', 'NAVI', 'WBS',
    
    # Energy (20)
    'XOM', 'CVX', 'COP', 'SLB', 'EOG', 'MPC', 'PSX', 'VLO', 'OXY', 'HAL',
    'BKR', 'KMI', 'WMB', 'OKE', 'DVN', 'FANG', 'MRO', 'APA', 'HES', 'CTRA',
    
    # Defense & Aerospace (15)
    'LMT', 'RTX', 'NOC', 'GD', 'BA', 'HII', 'TXT', 'LHX', 'LDOS', 'SAIC',
    'HWM', 'KTOS', 'AVAV', 'AIR', 'TDG',
    
    # Cybersecurity (15)
    'PANW', 'CRWD', 'ZS', 'FTNT', 'OKTA', 'S', 'TENB', 'RPD', 'CYBR', 'QLYS',
    'VRNS', 'SAIL', 'PING', 'CHKP', 'FEYE',
    
    # Critical Infrastructure (20)
    'NEE', 'DUK', 'SO', 'D', 'AEP', 'EXC', 'SRE', 'XEL', 'ED', 'ES',
    'PEG', 'WEC', 'ETR', 'FE', 'EIX', 'PPL', 'CMS', 'DTE', 'AEE', 'CNP',
    
    # Retail (15)
    'WMT', 'HD', 'COST', 'TGT', 'LOW', 'TJX', 'ROST', 'DG', 'DLTR', 'BBY',
    'ULTA', 'KSS', 'M', 'JWN', 'BBWI',
    
    # Manufacturing (15)
    'CAT', 'DE', 'HON', 'MMM', 'GE', 'EMR', 'ETN', 'ITW', 'PH', 'ROK',
    'CMI', 'DOV', 'IR', 'CARR', 'OTIS',
    
    # Telecom & Media (10)
    'VZ', 'T', 'TMUS', 'CHTR', 'CMCSA', 'DIS', 'NFLX', 'PARA', 'WBD', 'FOX',
    
    # Insurance (10)
    'BRK.B', 'PGR', 'TRV', 'ALL', 'AIG', 'MET', 'PRU', 'AFL', 'HIG', 'CB',
]


async def main():
    """Run 200-ticker analysis with real IBKR data."""
    
    print("=" * 80)
    print("🔭 MASSIVE SCALE IBKR FINANCIAL THREAT INTELLIGENCE")
    print("=" * 80)
    print(f"Tickers: {len(TICKERS_200)}")
    print("Data Source: Interactive Brokers (Real-Time)")
    print("Analysis: Llama 4 16x17B on Dual NVIDIA RTX A6000")
    print("=" * 80)
    print()
    
    # Initialize
    integration = IBKRFinancialThreatIntegration()
    
    # Connect
    print("📡 Connecting to IB Gateway...")
    connected = await integration.connect()
    
    if not connected:
        print("❌ Failed to connect to IB Gateway")
        print()
        print("Ensure IB Gateway is running:")
        print("  cd ~/Jts/ibgateway/1040")
        print("  ./ibgateway &")
        return
    
    print("✅ Connected to IB Gateway")
    print()
    
    # Start analysis
    start_time = time.time()
    
    print(f"🚀 Starting analysis of {len(TICKERS_200)} tickers...")
    print(f"   Estimated time: ~{len(TICKERS_200) * 15 / 60:.0f} minutes")
    print()
    
    # Analyze in batches of 20 for progress reporting
    batch_size = 20
    all_results = []
    high_threat_tickers = []
    
    for batch_num in range(0, len(TICKERS_200), batch_size):
        batch = TICKERS_200[batch_num:batch_num + batch_size]
        batch_start = time.time()
        
        print(f"📊 Batch {batch_num//batch_size + 1}/{(len(TICKERS_200) + batch_size - 1)//batch_size}")
        print(f"   Tickers: {', '.join(batch)}")
        
        # Analyze batch
        results = await integration.batch_analyze(batch)
        all_results.extend(results)
        
        # Track high threats
        for result in results:
            if result['threat_score'] >= 70:
                high_threat_tickers.append(result)
        
        batch_elapsed = time.time() - batch_start
        total_elapsed = time.time() - start_time
        
        # Progress stats
        completed = len(all_results)
        remaining = len(TICKERS_200) - completed
        rate = completed / total_elapsed if total_elapsed > 0 else 0
        eta_seconds = remaining / rate if rate > 0 else 0
        
        print(f"   ✅ Batch complete: {len(results)}/{len(batch)} analyzed in {batch_elapsed:.1f}s")
        print(f"   📈 Progress: {completed}/{len(TICKERS_200)} ({completed/len(TICKERS_200)*100:.1f}%)")
        print(f"   ⏱️  Rate: {rate:.2f} tickers/sec | ETA: {eta_seconds/60:.1f} min")
        print(f"   🚨 High threats found: {len(high_threat_tickers)}")
        print()
    
    # Final stats
    total_time = time.time() - start_time
    
    print("=" * 80)
    print("📊 FINAL RESULTS")
    print("=" * 80)
    print(f"Total Tickers: {len(all_results)}/{len(TICKERS_200)}")
    print(f"Total Time: {total_time/60:.1f} minutes ({total_time:.1f} seconds)")
    print(f"Average per Ticker: {total_time/len(all_results):.1f} seconds")
    print(f"Throughput: {len(all_results)/total_time:.2f} tickers/second")
    print()
    
    # Threat distribution
    threat_levels = {
        'CRITICAL (80-100)': [r for r in all_results if r['threat_score'] >= 80],
        'HIGH (70-79)': [r for r in all_results if 70 <= r['threat_score'] < 80],
        'MEDIUM (50-69)': [r for r in all_results if 50 <= r['threat_score'] < 70],
        'LOW (0-49)': [r for r in all_results if r['threat_score'] < 50],
    }
    
    print("🎯 Threat Distribution:")
    for level, tickers in threat_levels.items():
        print(f"   {level}: {len(tickers)} tickers")
        if len(tickers) > 0 and len(tickers) <= 10:
            ticker_list = ', '.join([t['ticker'] for t in tickers])
            print(f"      → {ticker_list}")
    print()
    
    # High threat details
    if high_threat_tickers:
        print("🚨 HIGH THREAT TICKERS (≥70):")
        print()
        for result in sorted(high_threat_tickers, key=lambda x: x['threat_score'], reverse=True):
            print(f"   {result['ticker']}: {result['threat_score']}/100 (Confidence: {result['confidence']}%)")
        print()
    
    # Top 10 highest threats
    print("🔝 TOP 10 HIGHEST THREAT SCORES:")
    top_10 = sorted(all_results, key=lambda x: x['threat_score'], reverse=True)[:10]
    for i, result in enumerate(top_10, 1):
        print(f"   {i:2d}. {result['ticker']:6s} - {result['threat_score']}/100")
    print()
    
    # Save results
    output_file = Path('data/financial_intelligence/ibkr_200_ticker_analysis.json')
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    import json
    with open(output_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'total_tickers': len(all_results),
            'total_time_seconds': total_time,
            'throughput_per_second': len(all_results) / total_time,
            'results': all_results,
            'high_threats': high_threat_tickers,
        }, f, indent=2)
    
    print(f"💾 Results saved to: {output_file}")
    print()
    
    # Disconnect
    await integration.disconnect()
    
    print("=" * 80)
    print("✅ ANALYSIS COMPLETE")
    print("=" * 80)
    print()
    print("🎯 Key Findings:")
    print(f"   - Analyzed {len(all_results)} tickers in {total_time/60:.1f} minutes")
    print(f"   - Throughput: {len(all_results)/total_time:.2f} tickers/second")
    print(f"   - High threats: {len(high_threat_tickers)} tickers")
    print(f"   - Real IBKR data + Llama 4 16x17B analysis")
    print()
    print("🔭 Financial intelligence system at scale - OPERATIONAL!")
    print("=" * 80)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Analysis interrupted by user")
        sys.exit(0)
