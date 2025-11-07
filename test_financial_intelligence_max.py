#!/usr/bin/env python3
"""
Financial Threat Intelligence - MAXIMUM STRESS TEST
Push dual A6000s + Llama 4 16x17B to the limit

Tests:
1. Parallel processing capacity (max throughput)
2. Complex multi-factor analysis
3. Large batch processing
4. Real-world scenario simulation
5. GPU memory utilization
6. Load balancing efficiency
7. Error handling under stress
"""

import asyncio
import sys
import time
import json
from datetime import datetime, timedelta
from typing import List, Dict
import random
from pathlib import Path

from src.intelligence.financial_threat_analyzer import FinancialThreatAnalyzer


class StressTestRunner:
    """Maximum stress test for financial intelligence system."""
    
    def __init__(self):
        self.analyzer = FinancialThreatAnalyzer()
        self.results = {
            'tests': [],
            'total_analyses': 0,
            'total_time': 0,
            'errors': 0,
            'gpu_distribution': {'http://localhost:11434': 0, 'http://localhost:11435': 0}
        }
    
    def generate_stock_data(self, count: int) -> List[Dict]:
        """Generate realistic stock data for testing."""
        tickers = [
            # Healthcare (high-value targets)
            'UNH', 'CVS', 'CI', 'HUM', 'ANTM', 'MOH', 'CNC', 'WCG',
            # Financial services
            'JPM', 'BAC', 'WFC', 'C', 'GS', 'MS', 'BLK', 'SCHW',
            # Tech (supply chain)
            'MSFT', 'GOOGL', 'AMZN', 'ORCL', 'SAP', 'CRM', 'ADBE', 'INTU',
            # Critical infrastructure
            'NEE', 'DUK', 'SO', 'D', 'AEP', 'EXC', 'SRE', 'XEL',
            # Defense contractors
            'LMT', 'RTX', 'NOC', 'GD', 'BA', 'HII', 'TXT', 'LHX',
            # Cybersecurity vendors
            'PANW', 'CRWD', 'ZS', 'FTNT', 'OKTA', 'S', 'TENB', 'RPD'
        ]
        
        data = []
        for i in range(count):
            ticker = random.choice(tickers)
            
            # Generate realistic anomaly patterns
            is_suspicious = random.random() > 0.7  # 30% suspicious
            
            if is_suspicious:
                # Pre-breach indicators
                volume_change = random.uniform(150, 350)  # High volume
                short_interest = random.uniform(8, 15)    # High short interest
                insider_trades = random.randint(2, 5)     # Multiple insiders
            else:
                # Normal activity
                volume_change = random.uniform(80, 120)
                short_interest = random.uniform(2, 5)
                insider_trades = random.randint(0, 1)
            
            data.append({
                'ticker': ticker,
                'data': {
                    'ticker': ticker,
                    'price': random.uniform(50, 500),
                    'volume_change': volume_change,
                    'options_activity': f"Put/Call ratio: {random.uniform(0.5, 2.5):.2f}",
                    'short_interest': short_interest,
                    'insider_trading': f"{insider_trades} executives traded in last 7 days",
                    'avg_volume_30d': random.uniform(1e6, 10e6),
                    'price_trend_90d': f"{random.uniform(-20, 20):+.1f}%",
                    'industry': random.choice(['Healthcare', 'Finance', 'Tech', 'Energy', 'Defense']),
                    'market_cap': random.uniform(10e9, 500e9)
                }
            })
        
        return data
    
    def generate_crypto_data(self, count: int) -> List[Dict]:
        """Generate realistic crypto wallet data."""
        gangs = ['LockBit', 'BlackCat', 'Royal', 'Play', 'Cl0p', 'ALPHV', 'Hive', 'Conti']
        
        data = []
        for i in range(count):
            is_ransomware = random.random() > 0.6  # 40% ransomware
            
            if is_ransomware:
                # Ransomware payment pattern
                tx_count = random.randint(20, 100)
                total_value = random.uniform(500000, 5000000)
                avg_tx = total_value / tx_count
                pattern = 'Multiple small inflows, single large outflow'
                mixing = random.choice(['Tornado Cash', 'ChipMixer', 'Wasabi Wallet'])
                gang = random.choice(gangs)
            else:
                # Normal activity
                tx_count = random.randint(5, 30)
                total_value = random.uniform(10000, 200000)
                avg_tx = total_value / tx_count
                pattern = 'Regular trading activity'
                mixing = 'None'
                gang = 'Unknown'
            
            wallet_id = f"0x{''.join(random.choices('0123456789abcdef', k=40))}"
            
            data.append({
                'wallet_id': wallet_id,
                'data': {
                    'wallet_id': wallet_id,
                    'transaction_count': tx_count,
                    'total_value_usd': total_value,
                    'avg_transaction_usd': avg_tx,
                    'pattern': pattern,
                    'mixing_services': mixing,
                    'suspected_gang': gang,
                    'historical_activity': 'Similar pattern in previous quarter' if is_ransomware else 'None'
                }
            })
        
        return data
    
    def generate_vendor_data(self, count: int) -> List[Dict]:
        """Generate realistic vendor financial data."""
        companies = [
            'Acme Security', 'GlobalTech Solutions', 'CyberDefense Corp', 'SecureNet Inc',
            'DataGuard Systems', 'ThreatShield LLC', 'InfoSec Partners', 'CloudSafe Technologies',
            'NetProtect Group', 'CyberWatch International', 'SafeData Solutions', 'TechGuard Inc'
        ]
        
        data = []
        for i in range(count):
            company = f"{random.choice(companies)} {i+1}"
            ticker = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=4))
            
            is_risky = random.random() > 0.5  # 50% risky
            
            if is_risky:
                # Financial stress indicators
                revenue_trend = f"{random.uniform(-25, -5):.1f}% YoY"
                debt_ratio = random.uniform(0.7, 0.95)
                cash = random.uniform(5e6, 20e6)
                layoffs = f"{random.randint(50, 300)} employees ({random.randint(15, 40)}% of workforce)"
                security_pct = random.uniform(1.5, 3.0)
                altman_z = random.uniform(0.5, 1.8)  # Distress zone
                credit = random.choice(['BB-', 'B+', 'B', 'B-', 'CCC+'])
            else:
                # Healthy company
                revenue_trend = f"{random.uniform(5, 25):+.1f}% YoY"
                debt_ratio = random.uniform(0.2, 0.5)
                cash = random.uniform(50e6, 200e6)
                layoffs = 'None'
                security_pct = random.uniform(4.0, 8.0)
                altman_z = random.uniform(2.5, 4.0)  # Safe zone
                credit = random.choice(['A-', 'BBB+', 'BBB', 'BBB-'])
            
            data.append({
                'company': company,
                'data': {
                    'company': company,
                    'ticker': ticker,
                    'revenue_trend': revenue_trend,
                    'debt_ratio': debt_ratio,
                    'cash': cash,
                    'layoffs': layoffs,
                    'security_spending_pct': security_pct,
                    'altman_z_score': altman_z,
                    'credit_rating': credit,
                    'recent_ma': 'Private equity acquisition' if is_risky and random.random() > 0.5 else 'None'
                }
            })
        
        return data
    
    async def test_1_parallel_capacity(self):
        """Test 1: Maximum parallel processing capacity."""
        print("\n" + "=" * 80)
        print("🚀 TEST 1: MAXIMUM PARALLEL PROCESSING CAPACITY")
        print("=" * 80)
        print("Goal: Find maximum throughput with dual GPUs")
        print()
        
        batch_sizes = [5, 10, 20, 30, 40, 50]
        
        for batch_size in batch_sizes:
            print(f"\n📊 Testing batch size: {batch_size}")
            print("-" * 80)
            
            # Generate mixed workload
            stock_data = self.generate_stock_data(batch_size // 3)
            crypto_data = self.generate_crypto_data(batch_size // 3)
            vendor_data = self.generate_vendor_data(batch_size // 3)
            
            batch = []
            batch.extend([{'type': 'stock', 'data': d['data']} for d in stock_data])
            batch.extend([{'type': 'crypto', 'data': d['data']} for d in crypto_data])
            batch.extend([{'type': 'vendor', 'data': d['data']} for d in vendor_data])
            
            start = time.time()
            results = await self.analyzer.analyze_batch(batch)
            duration = time.time() - start
            
            throughput = len(results) / duration
            avg_time = duration / len(results) if results else 0
            
            print(f"✅ Completed: {len(results)}/{len(batch)} analyses")
            print(f"   Duration: {duration:.2f}s")
            print(f"   Throughput: {throughput:.2f} analyses/sec")
            print(f"   Average: {avg_time:.2f}s per analysis")
            
            # Track GPU distribution
            for r in results:
                gpu = r.get('gpu_host', 'unknown')
                if gpu in self.results['gpu_distribution']:
                    self.results['gpu_distribution'][gpu] += 1
            
            self.results['tests'].append({
                'test': 'parallel_capacity',
                'batch_size': batch_size,
                'completed': len(results),
                'duration': duration,
                'throughput': throughput
            })
            
            self.results['total_analyses'] += len(results)
            self.results['total_time'] += duration
            
            # Brief pause between batches
            await asyncio.sleep(2)
        
        print(f"\n🏆 Best throughput: {max([t['throughput'] for t in self.results['tests'] if t['test'] == 'parallel_capacity']):.2f} analyses/sec")
    
    async def test_2_complex_analysis(self):
        """Test 2: Complex multi-factor analysis."""
        print("\n" + "=" * 80)
        print("🧠 TEST 2: COMPLEX MULTI-FACTOR ANALYSIS")
        print("=" * 80)
        print("Goal: Test Llama 4's analytical capabilities with complex scenarios")
        print()
        
        # Create complex, realistic scenario
        complex_stock = {
            'ticker': 'UNH',
            'price': 524.50,
            'volume_change': 287.5,  # Extreme spike
            'options_activity': 'Unusual put buying (5x normal), Put/Call ratio: 2.8',
            'short_interest': 14.2,  # Very high
            'insider_trading': '5 C-level executives sold 80% of holdings in 48 hours',
            'avg_volume_30d': 2.3e6,
            'price_trend_90d': '+12.3%',
            'industry': 'Healthcare',
            'market_cap': 485e9,
            'recent_news': 'Regulatory investigation announced, IT system outage reported',
            'analyst_downgrades': '3 major firms downgraded in last week',
            'institutional_selling': 'Hedge funds reduced positions by 15%'
        }
        
        print("📊 Analyzing complex pre-breach scenario...")
        print(f"   Ticker: {complex_stock['ticker']}")
        print(f"   Volume spike: {complex_stock['volume_change']}%")
        print(f"   Insider selling: {complex_stock['insider_trading']}")
        print()
        
        start = time.time()
        result = await self.analyzer.analyze_stock_anomalies('UNH', complex_stock)
        duration = time.time() - start
        
        if result.get('success', True):
            print(f"✅ Analysis complete in {duration:.2f}s")
            print(f"   Threat Score: {result.get('threat_score', 'N/A')}/100")
            print(f"   Confidence: {result.get('confidence', 'N/A')}%")
            print(f"   GPU: {result.get('gpu_host', 'N/A')}")
            print()
            print("📝 Analysis:")
            analysis = result.get('raw_analysis', result.get('analysis', ''))
            print(f"   {analysis[:500]}...")
            
            self.results['tests'].append({
                'test': 'complex_analysis',
                'duration': duration,
                'threat_score': result.get('threat_score', 0),
                'confidence': result.get('confidence', 0)
            })
        else:
            print(f"❌ Analysis failed: {result.get('error')}")
            self.results['errors'] += 1
    
    async def test_3_sustained_load(self):
        """Test 3: Sustained load over time."""
        print("\n" + "=" * 80)
        print("⏱️  TEST 3: SUSTAINED LOAD TEST")
        print("=" * 80)
        print("Goal: Test system stability under continuous load")
        print()
        
        duration_minutes = 5
        analyses_per_minute = 10
        total_analyses = duration_minutes * analyses_per_minute
        
        print(f"Running {total_analyses} analyses over {duration_minutes} minutes...")
        print(f"Target rate: {analyses_per_minute} analyses/minute")
        print()
        
        start_time = time.time()
        completed = 0
        errors = 0
        
        for i in range(total_analyses):
            # Generate random analysis
            analysis_type = random.choice(['stock', 'crypto', 'vendor'])
            
            try:
                if analysis_type == 'stock':
                    data = self.generate_stock_data(1)[0]
                    result = await self.analyzer.analyze_stock_anomalies(
                        data['ticker'], data['data']
                    )
                elif analysis_type == 'crypto':
                    data = self.generate_crypto_data(1)[0]
                    result = await self.analyzer.analyze_crypto_payments(data['data'])
                else:
                    data = self.generate_vendor_data(1)[0]
                    result = await self.analyzer.analyze_vendor_risk(data['data'])
                
                if result.get('success', True):
                    completed += 1
                    if (i + 1) % 10 == 0:
                        elapsed = time.time() - start_time
                        rate = completed / (elapsed / 60)
                        print(f"   Progress: {completed}/{total_analyses} ({rate:.1f}/min) - {elapsed:.0f}s elapsed")
                else:
                    errors += 1
                    
            except Exception as e:
                errors += 1
                print(f"   ⚠️  Error on analysis {i+1}: {e}")
            
            # Small delay to simulate realistic workload
            await asyncio.sleep(0.5)
        
        total_time = time.time() - start_time
        actual_rate = completed / (total_time / 60)
        
        print()
        print(f"✅ Sustained load test complete")
        print(f"   Completed: {completed}/{total_analyses}")
        print(f"   Errors: {errors}")
        print(f"   Duration: {total_time:.1f}s ({total_time/60:.1f} minutes)")
        print(f"   Actual rate: {actual_rate:.1f} analyses/minute")
        print(f"   Success rate: {(completed/total_analyses)*100:.1f}%")
        
        self.results['tests'].append({
            'test': 'sustained_load',
            'completed': completed,
            'errors': errors,
            'duration': total_time,
            'rate': actual_rate
        })
        
        self.results['total_analyses'] += completed
        self.results['total_time'] += total_time
        self.results['errors'] += errors
    
    async def test_4_real_world_scenario(self):
        """Test 4: Real-world threat detection scenario."""
        print("\n" + "=" * 80)
        print("🎯 TEST 4: REAL-WORLD THREAT DETECTION SCENARIO")
        print("=" * 80)
        print("Scenario: Multi-vector attack detection")
        print()
        
        print("📋 Scenario: Healthcare provider under attack")
        print("   - Stock anomalies detected")
        print("   - Ransomware payment observed")
        print("   - Vendor showing financial stress")
        print()
        
        # Simulate coordinated attack indicators
        scenarios = [
            {
                'type': 'stock',
                'name': 'Target: UnitedHealth Group',
                'data': {
                    'ticker': 'UNH',
                    'price': 524.50,
                    'volume_change': 245.3,
                    'options_activity': 'Unusual put buying (3x normal)',
                    'short_interest': 12.5,
                    'insider_trading': '3 executives sold shares',
                    'avg_volume_30d': 2.1e6,
                    'price_trend_90d': '+8.2%',
                    'industry': 'Healthcare',
                    'market_cap': 485e9
                }
            },
            {
                'type': 'crypto',
                'name': 'Ransomware Payment Detected',
                'data': {
                    'wallet_id': '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb',
                    'transaction_count': 47,
                    'total_value_usd': 2450000,
                    'avg_transaction_usd': 52127,
                    'pattern': 'Multiple small inflows, single large outflow',
                    'mixing_services': 'Tornado Cash',
                    'suspected_gang': 'LockBit',
                    'historical_activity': 'Similar pattern in Q3 2024'
                }
            },
            {
                'type': 'vendor',
                'name': 'IT Vendor Financial Stress',
                'data': {
                    'company': 'Healthcare IT Solutions Inc',
                    'ticker': 'HITS',
                    'revenue_trend': '-18% YoY',
                    'debt_ratio': 0.88,
                    'cash': 8500000,
                    'layoffs': '180 employees (30% of workforce)',
                    'security_spending_pct': 1.8,
                    'altman_z_score': 1.1,
                    'credit_rating': 'B-',
                    'recent_ma': 'Private equity acquisition'
                }
            }
        ]
        
        results = []
        for scenario in scenarios:
            print(f"\n🔍 Analyzing: {scenario['name']}")
            print("-" * 80)
            
            start = time.time()
            
            if scenario['type'] == 'stock':
                result = await self.analyzer.analyze_stock_anomalies(
                    scenario['data']['ticker'], scenario['data']
                )
            elif scenario['type'] == 'crypto':
                result = await self.analyzer.analyze_crypto_payments(scenario['data'])
            else:
                result = await self.analyzer.analyze_vendor_risk(scenario['data'])
            
            duration = time.time() - start
            
            if result.get('success', True):
                threat_score = result.get('threat_score', 0)
                confidence = result.get('confidence', 0)
                
                print(f"✅ Analysis complete ({duration:.2f}s)")
                print(f"   Threat Score: {threat_score}/100")
                print(f"   Confidence: {confidence}%")
                
                if threat_score >= 80:
                    print(f"   🚨 CRITICAL THREAT DETECTED")
                elif threat_score >= 60:
                    print(f"   ⚠️  HIGH RISK")
                
                results.append({
                    'name': scenario['name'],
                    'threat_score': threat_score,
                    'confidence': confidence,
                    'duration': duration
                })
            else:
                print(f"❌ Analysis failed: {result.get('error')}")
        
        print("\n" + "=" * 80)
        print("📊 SCENARIO SUMMARY")
        print("=" * 80)
        
        avg_threat = sum([r['threat_score'] for r in results]) / len(results) if results else 0
        critical_count = len([r for r in results if r['threat_score'] >= 80])
        
        print(f"Analyses completed: {len(results)}/3")
        print(f"Average threat score: {avg_threat:.1f}/100")
        print(f"Critical threats: {critical_count}")
        print()
        
        if avg_threat >= 70:
            print("🚨 RECOMMENDATION: IMMEDIATE ACTION REQUIRED")
            print("   - Activate incident response team")
            print("   - Increase monitoring on all vectors")
            print("   - Prepare breach containment procedures")
        elif avg_threat >= 50:
            print("⚠️  RECOMMENDATION: ELEVATED MONITORING")
            print("   - Increase security posture")
            print("   - Review vendor access controls")
            print("   - Monitor for additional indicators")
        
        self.results['tests'].append({
            'test': 'real_world_scenario',
            'avg_threat_score': avg_threat,
            'critical_count': critical_count,
            'completed': len(results)
        })
    
    async def test_5_gpu_utilization(self):
        """Test 5: GPU load balancing verification."""
        print("\n" + "=" * 80)
        print("🖥️  TEST 5: GPU LOAD BALANCING VERIFICATION")
        print("=" * 80)
        print("Goal: Verify even distribution across both GPUs")
        print()
        
        # Run 100 analyses to check distribution
        batch_size = 100
        print(f"Running {batch_size} analyses to verify load balancing...")
        print()
        
        stock_data = self.generate_stock_data(batch_size)
        batch = [{'type': 'stock', 'data': d['data']} for d in stock_data]
        
        start = time.time()
        results = await self.analyzer.analyze_batch(batch)
        duration = time.time() - start
        
        # Count GPU distribution
        gpu_counts = {}
        for r in results:
            gpu = r.get('gpu_host', 'unknown')
            gpu_counts[gpu] = gpu_counts.get(gpu, 0) + 1
        
        print(f"✅ Completed {len(results)} analyses in {duration:.2f}s")
        print()
        print("GPU Distribution:")
        for gpu, count in gpu_counts.items():
            percentage = (count / len(results)) * 100
            print(f"   {gpu}: {count} analyses ({percentage:.1f}%)")
        
        # Check if balanced (within 10%)
        if len(gpu_counts) == 2:
            counts = list(gpu_counts.values())
            diff = abs(counts[0] - counts[1])
            diff_pct = (diff / len(results)) * 100
            
            if diff_pct <= 10:
                print(f"\n✅ Load balancing: EXCELLENT (difference: {diff_pct:.1f}%)")
            elif diff_pct <= 20:
                print(f"\n⚠️  Load balancing: GOOD (difference: {diff_pct:.1f}%)")
            else:
                print(f"\n❌ Load balancing: POOR (difference: {diff_pct:.1f}%)")
        
        self.results['tests'].append({
            'test': 'gpu_utilization',
            'gpu_distribution': gpu_counts,
            'completed': len(results),
            'duration': duration
        })
    
    def generate_report(self):
        """Generate final stress test report."""
        print("\n" + "=" * 80)
        print("📊 FINAL STRESS TEST REPORT")
        print("=" * 80)
        print()
        
        print("🎯 Overall Statistics:")
        print(f"   Total analyses: {self.results['total_analyses']}")
        print(f"   Total time: {self.results['total_time']:.1f}s ({self.results['total_time']/60:.1f} minutes)")
        print(f"   Total errors: {self.results['errors']}")
        print(f"   Success rate: {((self.results['total_analyses']-self.results['errors'])/self.results['total_analyses']*100):.1f}%")
        print()
        
        if self.results['total_time'] > 0:
            avg_throughput = self.results['total_analyses'] / self.results['total_time']
            print(f"   Average throughput: {avg_throughput:.2f} analyses/sec")
            print(f"   Daily capacity: {avg_throughput * 86400:,.0f} analyses/day")
        
        print()
        print("🖥️  GPU Load Distribution:")
        total_gpu = sum(self.results['gpu_distribution'].values())
        for gpu, count in self.results['gpu_distribution'].items():
            if total_gpu > 0:
                pct = (count / total_gpu) * 100
                print(f"   {gpu}: {count} ({pct:.1f}%)")
        
        print()
        print("📋 Test Results:")
        for test in self.results['tests']:
            print(f"   ✅ {test['test']}: {json.dumps({k: v for k, v in test.items() if k != 'test'}, indent=6)}")
        
        # Save detailed report
        report_file = Path('data/financial_intelligence/stress_test_report.json')
        report_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_file, 'w') as f:
            json.dump({
                **self.results,
                'timestamp': datetime.now().isoformat(),
                'system': 'Dual A6000 + Llama 4 16x17B'
            }, f, indent=2)
        
        print()
        print(f"📄 Detailed report saved: {report_file}")
        print()
        print("=" * 80)


async def main():
    """Run maximum stress test."""
    print("=" * 80)
    print("🔭 FINANCIAL THREAT INTELLIGENCE - MAXIMUM STRESS TEST")
    print("=" * 80)
    print("System: Dual NVIDIA RTX A6000 + Llama 4 16x17B")
    print("Goal: Push the system to its absolute limits")
    print()
    
    # Check Ollama instances
    import requests
    hosts = ["http://localhost:11434", "http://localhost:11435"]
    
    print("🔍 Checking Ollama instances...")
    for i, host in enumerate(hosts):
        try:
            response = requests.get(f"{host}/api/tags", timeout=5)
            if response.status_code == 200:
                print(f"   ✅ GPU {i} ({host}): Ready")
            else:
                print(f"   ❌ GPU {i} ({host}): Not responding")
                print("\n⚠️  Please start Ollama instances first:")
                print("   Terminal 1: CUDA_VISIBLE_DEVICES=0 OLLAMA_HOST=0.0.0.0:11434 ollama serve")
                print("   Terminal 2: CUDA_VISIBLE_DEVICES=1 OLLAMA_HOST=0.0.0.0:11435 ollama serve")
                sys.exit(1)
        except Exception as e:
            print(f"   ❌ GPU {i} ({host}): Connection failed")
            print("\n⚠️  Please start Ollama instances first")
            sys.exit(1)
    
    print()
    input("Press ENTER to start maximum stress test...")
    
    # Run stress tests
    runner = StressTestRunner()
    
    try:
        await runner.test_1_parallel_capacity()
        await runner.test_2_complex_analysis()
        await runner.test_3_sustained_load()
        await runner.test_4_real_world_scenario()
        await runner.test_5_gpu_utilization()
        
        # Generate final report
        runner.generate_report()
        
        print()
        print("✅ MAXIMUM STRESS TEST COMPLETE")
        print("🔭 See threats before they surface.")
        print("=" * 80)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        runner.generate_report()
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        runner.generate_report()


if __name__ == "__main__":
    asyncio.run(main())
