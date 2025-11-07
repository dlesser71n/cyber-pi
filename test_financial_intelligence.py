#!/usr/bin/env python3
"""
Test Financial Threat Intelligence Analyzer
Dual A6000 Load Balanced with Llama 4 16x17B
"""

import asyncio
import sys
from src.intelligence.financial_threat_analyzer import FinancialThreatAnalyzer


async def test_dual_gpu_setup():
    """Test that both Ollama instances are running."""
    print("🔍 Testing Dual-GPU Ollama Setup")
    print("=" * 80)
    
    import requests
    
    hosts = ["http://localhost:11434", "http://localhost:11435"]
    
    for i, host in enumerate(hosts):
        try:
            response = requests.get(f"{host}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                llama4 = [m for m in models if 'llama4' in m.get('name', '')]
                if llama4:
                    print(f"✅ GPU {i} ({host}): Ollama running, llama4:16x17b available")
                else:
                    print(f"⚠️  GPU {i} ({host}): Ollama running, but llama4:16x17b not found")
                    print(f"   Available models: {[m.get('name') for m in models[:3]]}")
            else:
                print(f"❌ GPU {i} ({host}): Ollama not responding")
                return False
        except Exception as e:
            print(f"❌ GPU {i} ({host}): Connection failed - {e}")
            print(f"\n💡 Start Ollama instances with:")
            print(f"   Terminal 1: CUDA_VISIBLE_DEVICES=0 OLLAMA_HOST=0.0.0.0:11434 ollama serve")
            print(f"   Terminal 2: CUDA_VISIBLE_DEVICES=1 OLLAMA_HOST=0.0.0.0:11435 ollama serve")
            return False
    
    print("")
    return True


async def test_stock_analysis():
    """Test stock anomaly analysis."""
    print("📊 Test 1: Stock Market Anomaly Detection")
    print("-" * 80)
    
    analyzer = FinancialThreatAnalyzer()
    
    # Simulate suspicious pre-breach indicators
    stock_data = {
        'ticker': 'UNH',
        'price': 524.50,
        'volume_change': 245.3,  # Massive spike
        'options_activity': 'Unusual put buying (3x normal)',
        'short_interest': 12.5,  # Up from 3.2%
        'insider_trading': '3 executives sold shares (last 7 days)',
        'avg_volume_30d': 2.1e6,
        'price_trend_90d': '+8.2%',
        'industry': 'Healthcare',
        'market_cap': 485e9
    }
    
    result = await analyzer.analyze_stock_anomalies('UNH', stock_data)
    
    if result.get('success', True):
        print(f"✅ Analysis complete")
        print(f"   Threat Score: {result.get('threat_score', 'N/A')}/100")
        print(f"   Confidence: {result.get('confidence', 'N/A')}%")
        print(f"   GPU Used: {result.get('gpu_host', 'N/A')}")
        print(f"\n📝 Analysis Preview:")
        analysis_text = result.get('raw_analysis', result.get('analysis', 'N/A'))
        print(f"   {analysis_text[:300]}...")
        return True
    else:
        print(f"❌ Analysis failed: {result.get('error', 'Unknown')}")
        return False


async def test_crypto_analysis():
    """Test cryptocurrency payment analysis."""
    print("\n💰 Test 2: Cryptocurrency Ransomware Tracking")
    print("-" * 80)
    
    analyzer = FinancialThreatAnalyzer()
    
    # Simulate ransomware payment pattern
    wallet_data = {
        'wallet_id': '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb',
        'transaction_count': 47,
        'total_value_usd': 2450000,
        'avg_transaction_usd': 52127,
        'pattern': 'Multiple small inflows, single large outflow',
        'mixing_services': 'Tornado Cash detected',
        'suspected_gang': 'LockBit',
        'historical_activity': 'Similar pattern in Q3 2024'
    }
    
    result = await analyzer.analyze_crypto_payments(wallet_data)
    
    if result.get('success', True):
        print(f"✅ Analysis complete")
        print(f"   Threat Score: {result.get('threat_score', 'N/A')}/100")
        print(f"   Confidence: {result.get('confidence', 'N/A')}%")
        print(f"   GPU Used: {result.get('gpu_host', 'N/A')}")
        print(f"\n📝 Analysis Preview:")
        analysis_text = result.get('raw_analysis', result.get('analysis', 'N/A'))
        print(f"   {analysis_text[:300]}...")
        return True
    else:
        print(f"❌ Analysis failed: {result.get('error', 'Unknown')}")
        return False


async def test_vendor_risk():
    """Test vendor financial risk analysis."""
    print("\n🏢 Test 3: Vendor Financial Risk Assessment")
    print("-" * 80)
    
    analyzer = FinancialThreatAnalyzer()
    
    # Simulate financially stressed vendor
    vendor_data = {
        'company': 'Acme Security Solutions',
        'ticker': 'ACME',
        'revenue_trend': '-15% YoY',
        'debt_ratio': 0.85,  # High debt
        'cash': 12000000,
        'layoffs': '200 employees (25% of workforce) in Q4',
        'security_spending_pct': 2.1,  # Down from 4.5%
        'altman_z_score': 1.2,  # Distress zone
        'credit_rating': 'BB- (downgraded)',
        'recent_ma': 'Acquired by private equity firm'
    }
    
    result = await analyzer.analyze_vendor_risk(vendor_data)
    
    if result.get('success', True):
        print(f"✅ Analysis complete")
        print(f"   Threat Score: {result.get('threat_score', 'N/A')}/100")
        print(f"   Confidence: {result.get('confidence', 'N/A')}%")
        print(f"   GPU Used: {result.get('gpu_host', 'N/A')}")
        print(f"\n📝 Analysis Preview:")
        analysis_text = result.get('raw_analysis', result.get('analysis', 'N/A'))
        print(f"   {analysis_text[:300]}...")
        return True
    else:
        print(f"❌ Analysis failed: {result.get('error', 'Unknown')}")
        return False


async def test_parallel_processing():
    """Test parallel processing across both GPUs."""
    print("\n🚀 Test 4: Parallel Processing (Load Balanced)")
    print("-" * 80)
    
    analyzer = FinancialThreatAnalyzer()
    
    # Batch of analyses
    batch = [
        {'type': 'stock', 'data': {'ticker': 'MSFT', 'price': 380, 'volume_change': 150}},
        {'type': 'stock', 'data': {'ticker': 'GOOGL', 'price': 142, 'volume_change': 180}},
        {'type': 'crypto', 'data': {'wallet_id': '0xABC...', 'transaction_count': 23}},
        {'type': 'vendor', 'data': {'company': 'Test Corp', 'ticker': 'TEST'}},
    ]
    
    print(f"Processing {len(batch)} analyses in parallel...")
    
    import time
    start = time.time()
    results = await analyzer.analyze_batch(batch)
    duration = time.time() - start
    
    print(f"✅ Completed {len(results)}/{len(batch)} analyses in {duration:.1f}s")
    print(f"   Average: {duration/len(results):.1f}s per analysis")
    print(f"   GPUs used: {set([r.get('gpu_host') for r in results if 'gpu_host' in r])}")
    
    return len(results) > 0


async def main():
    """Run all tests."""
    print("=" * 80)
    print("🔭 FINANCIAL THREAT INTELLIGENCE - SYSTEM TEST")
    print("=" * 80)
    print("Testing Llama 4 16x17B on Dual A6000s (Load Balanced)")
    print("")
    
    # Test 1: Verify Ollama setup
    if not await test_dual_gpu_setup():
        print("\n❌ Dual-GPU setup not ready. Please start Ollama instances first.")
        sys.exit(1)
    
    print("")
    
    # Test 2: Stock analysis
    test1 = await test_stock_analysis()
    
    # Test 3: Crypto analysis
    test2 = await test_crypto_analysis()
    
    # Test 4: Vendor risk
    test3 = await test_vendor_risk()
    
    # Test 5: Parallel processing
    test4 = await test_parallel_processing()
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)
    print(f"Stock Analysis:      {'✅ PASS' if test1 else '❌ FAIL'}")
    print(f"Crypto Analysis:     {'✅ PASS' if test2 else '❌ FAIL'}")
    print(f"Vendor Risk:         {'✅ PASS' if test3 else '❌ FAIL'}")
    print(f"Parallel Processing: {'✅ PASS' if test4 else '❌ FAIL'}")
    print("")
    
    if all([test1, test2, test3, test4]):
        print("✅ ALL TESTS PASSED - Financial intelligence system ready!")
        print("")
        print("🎯 Next Steps:")
        print("   1. Integrate with Periscope triage")
        print("   2. Add real data sources (yfinance, blockchain APIs)")
        print("   3. Set up automated monitoring")
        print("   4. Deploy to production")
    else:
        print("⚠️  Some tests failed - review errors above")
    
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
