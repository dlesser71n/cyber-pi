#!/usr/bin/env python3
"""
Two-Stage Financial Threat Analysis
Stage 1: Fast screening with llama3.1:8b (all stocks)
Stage 2: Deep analysis with llama4:16x17b (high threats only)
"""

import asyncio
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from collectors.financial_threat_collector import FinancialThreatCollector

# Test with 10 tickers
TEST_WATCHLIST = [
    'UNH', 'PANW', 'JPM', 'MSFT', 'DAL',
    'CVS', 'BAC', 'AAPL', 'CRWD', 'UAL'
]


class TwoStageFinancialCollector(FinancialThreatCollector):
    """
    Two-stage collector:
    1. Fast screening (no LLM, just metrics)
    2. Deep analysis (Llama 4 for high threats only)
    """
    
    async def collect_threat_fast(self, ticker: str) -> dict:
        """
        Stage 1: Fast screening - just calculate metrics, no LLM.
        
        Returns:
            Threat data with basic scoring
        """
        try:
            # Get current stock price
            market_data = await self.integration.get_stock_data(ticker)
            
            if not market_data:
                return None
            
            current_price = market_data.get('price', 0)
            
            # Analyze options activity (metrics only)
            options_metrics = await self.options_analyzer.analyze_options_activity(
                ticker,
                current_price=current_price,
                avg_volume_30d=5000
            )
            
            # Build threat data
            threat_data = {
                'type': 'financial_threat',
                'ticker': ticker,
                'company': self._get_company_name(ticker),
                'industry': self._get_industry(ticker),
                'threat_score': options_metrics.threat_score,
                'confidence': 'high' if options_metrics.threat_score >= 80 else 'medium' if options_metrics.threat_score >= 60 else 'low',
                'indicators': options_metrics.indicators,
                'metrics': {
                    'current_price': current_price,
                    'put_call_ratio': options_metrics.put_call_ratio,
                    'volume_spike': options_metrics.volume_spike,
                    'unusual_puts_count': len(options_metrics.unusual_puts),
                    'near_term_activity': options_metrics.near_expiry_activity.get('total_volume', 0) if options_metrics.near_expiry_activity else 0,
                },
                'stage': 'fast_screening',
            }
            
            return threat_data
            
        except Exception as e:
            print(f"Error in fast screening for {ticker}: {e}")
            return None
    
    async def run_two_stage_collection(self):
        """Run two-stage collection."""
        print("="*70)
        print("🚀 TWO-STAGE FINANCIAL THREAT ANALYSIS")
        print("="*70)
        print()
        
        # Connect
        await self.connect()
        
        # STAGE 1: Fast screening (all stocks)
        print("📊 STAGE 1: Fast Screening (metrics only)")
        print(f"   Analyzing {len(self.watchlist)} tickers...")
        print()
        
        stage1_start = time.time()
        
        all_threats = []
        high_priority = []
        
        for i, ticker in enumerate(self.watchlist, 1):
            print(f"   [{i}/{len(self.watchlist)}] {ticker}...", end=' ')
            
            threat = await self.collect_threat_fast(ticker)
            
            if threat:
                all_threats.append(threat)
                score = threat['threat_score']
                
                if score >= 70:
                    high_priority.append(threat)
                    print(f"🚨 {score}/100 (HIGH)")
                elif score >= 50:
                    print(f"⚠️  {score}/100 (medium)")
                else:
                    print(f"✅ {score}/100 (low)")
            else:
                print("❌ No data")
            
            # Rate limiting
            await asyncio.sleep(0.5)
        
        stage1_time = time.time() - stage1_start
        
        print()
        print(f"✅ Stage 1 complete: {stage1_time:.1f} seconds")
        print(f"   Total analyzed: {len(all_threats)}")
        print(f"   High priority: {len(high_priority)}")
        print()
        
        # STAGE 2: Deep analysis (high priority only)
        if high_priority:
            print("="*70)
            print("🔬 STAGE 2: Deep Analysis (Llama 4 16x17B)")
            print(f"   Analyzing {len(high_priority)} high-priority threats...")
            print()
            
            stage2_start = time.time()
            
            # TODO: Add Llama 4 deep analysis here
            # For now, just show what would be analyzed
            for threat in high_priority:
                print(f"   Would analyze: {threat['ticker']} ({threat['threat_score']}/100)")
            
            stage2_time = time.time() - stage2_start
            
            print()
            print(f"✅ Stage 2 complete: {stage2_time:.1f} seconds")
        else:
            print("✅ No high-priority threats - Stage 2 skipped")
            stage2_time = 0
        
        # Disconnect
        await self.disconnect()
        
        # Summary
        total_time = stage1_time + stage2_time
        
        print()
        print("="*70)
        print("📊 PERFORMANCE SUMMARY")
        print("="*70)
        print(f"Stage 1 (Fast Screening):  {stage1_time:.1f}s for {len(all_threats)} tickers")
        print(f"Stage 2 (Deep Analysis):   {stage2_time:.1f}s for {len(high_priority)} tickers")
        print(f"Total Time:                {total_time:.1f}s")
        print()
        print(f"Average per ticker:        {total_time/len(all_threats):.1f}s")
        print(f"Throughput:                {len(all_threats)/total_time*60:.1f} tickers/minute")
        print()
        
        if high_priority:
            print("🚨 HIGH PRIORITY THREATS:")
            for threat in high_priority:
                print(f"   {threat['ticker']}: {threat['threat_score']}/100 - {threat['company']}")
        
        print()
        print("="*70)
        print("✅ TWO-STAGE ANALYSIS COMPLETE")
        print("="*70)
        
        return {
            'stage1_time': stage1_time,
            'stage2_time': stage2_time,
            'total_time': total_time,
            'total_analyzed': len(all_threats),
            'high_priority': len(high_priority),
            'throughput': len(all_threats)/total_time*60,
            'threats': all_threats,
        }


async def main():
    collector = TwoStageFinancialCollector(watchlist=TEST_WATCHLIST)
    await collector.run_two_stage_collection()


if __name__ == "__main__":
    asyncio.run(main())
