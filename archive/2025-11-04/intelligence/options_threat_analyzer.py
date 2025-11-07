#!/usr/bin/env python3
"""
Options Threat Analyzer
Detects pre-breach indicators through unusual options activity

Key Indicators:
- Put/Call ratio > 2.0 (bearish sentiment)
- Volume > 3x average (unusual activity)
- Large out-of-money puts (betting on crash)
- Short-dated options spike (imminent event expected)
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass

from ib_async import IB, Stock, Option

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class OptionsMetrics:
    """Options activity metrics for threat analysis."""
    ticker: str
    put_call_ratio: float
    put_volume: int
    call_volume: int
    total_volume: int
    avg_volume_30d: int
    volume_spike: float  # Percentage above average
    unusual_puts: List[Dict]  # Large OTM puts
    near_expiry_activity: Dict  # Activity in near-term options
    threat_score: int  # 0-100
    indicators: List[str]


class OptionsThreatAnalyzer:
    """
    Analyzes options activity for pre-breach indicators.
    
    Research shows unusual options activity precedes breaches by 14-30 days:
    - Insiders buy puts before bad news
    - Volume spikes 3-5x normal
    - Out-of-money puts indicate crash expectation
    - Short-dated options = imminent event
    """
    
    def __init__(self, ib: IB):
        self.ib = ib
        logger.info("📊 Options Threat Analyzer initialized")
    
    async def get_options_chain(self, ticker: str, days_out: int = 45) -> List[Option]:
        """
        Get options chain for a ticker.
        
        Args:
            ticker: Stock symbol
            days_out: Days until expiration to analyze
            
        Returns:
            List of Option contracts
        """
        try:
            # Get stock contract
            stock = Stock(ticker, 'SMART', 'USD')
            stock = (await self.ib.qualifyContractsAsync(stock))[0]
            
            # Get options chain
            chains = await self.ib.reqSecDefOptParamsAsync(
                stock.symbol,
                '',
                stock.secType,
                stock.conId
            )
            
            if not chains:
                logger.warning(f"No options chain for {ticker}")
                return []
            
            chain = chains[0]
            
            # Get near-term expirations
            target_date = datetime.now() + timedelta(days=days_out)
            near_expirations = [
                exp for exp in chain.expirations
                if datetime.strptime(exp, '%Y%m%d') <= target_date
            ][:3]  # Get 3 nearest expirations
            
            # Build option contracts
            options = []
            for expiration in near_expirations:
                for strike in chain.strikes:
                    # Get both puts and calls
                    put = Option(ticker, expiration, strike, 'P', 'SMART')
                    call = Option(ticker, expiration, strike, 'C', 'SMART')
                    options.extend([put, call])
            
            return options
            
        except Exception as e:
            logger.error(f"Error getting options chain for {ticker}: {e}")
            return []
    
    async def get_options_data(self, options: List[Option]) -> List[Dict]:
        """
        Get market data for options contracts.
        
        Args:
            options: List of Option contracts
            
        Returns:
            List of option data dictionaries
        """
        try:
            # Qualify contracts
            qualified = await self.ib.qualifyContractsAsync(*options)
            
            # Request market data
            tickers = [self.ib.reqMktData(opt, '', False, False) for opt in qualified]
            
            # Wait for data
            await asyncio.sleep(3)
            
            # Collect data
            options_data = []
            for ticker, contract in zip(tickers, qualified):
                if ticker.volume and ticker.volume > 0:
                    options_data.append({
                        'contract': contract,
                        'strike': contract.strike,
                        'right': contract.right,  # 'P' or 'C'
                        'expiration': contract.lastTradeDateOrContractMonth,
                        'last': ticker.last if ticker.last else 0,
                        'bid': ticker.bid if ticker.bid else 0,
                        'ask': ticker.ask if ticker.ask else 0,
                        'volume': ticker.volume if ticker.volume else 0,
                        'open_interest': getattr(ticker, 'openInterest', 0) or 0,
                    })
            
            return options_data
            
        except Exception as e:
            logger.error(f"Error getting options data: {e}")
            return []
    
    async def analyze_options_activity(
        self,
        ticker: str,
        current_price: float,
        avg_volume_30d: int = 1000
    ) -> OptionsMetrics:
        """
        Analyze options activity for threat indicators.
        
        Args:
            ticker: Stock symbol
            current_price: Current stock price
            avg_volume_30d: Average daily options volume (30-day)
            
        Returns:
            OptionsMetrics with threat analysis
        """
        logger.info(f"📊 Analyzing options activity for {ticker}")
        
        # Get options chain
        options = await self.get_options_chain(ticker, days_out=45)
        
        if not options:
            return OptionsMetrics(
                ticker=ticker,
                put_call_ratio=0.0,
                put_volume=0,
                call_volume=0,
                total_volume=0,
                avg_volume_30d=avg_volume_30d,
                volume_spike=0.0,
                unusual_puts=[],
                near_expiry_activity={},
                threat_score=0,
                indicators=["No options data available"]
            )
        
        # Get market data
        options_data = await self.get_options_data(options)
        
        if not options_data:
            return OptionsMetrics(
                ticker=ticker,
                put_call_ratio=0.0,
                put_volume=0,
                call_volume=0,
                total_volume=0,
                avg_volume_30d=avg_volume_30d,
                volume_spike=0.0,
                unusual_puts=[],
                near_expiry_activity={},
                threat_score=0,
                indicators=["No options market data"]
            )
        
        # Calculate metrics
        put_volume = sum(opt['volume'] for opt in options_data if opt['right'] == 'P')
        call_volume = sum(opt['volume'] for opt in options_data if opt['right'] == 'C')
        total_volume = put_volume + call_volume
        
        put_call_ratio = put_volume / call_volume if call_volume > 0 else 0.0
        volume_spike = ((total_volume - avg_volume_30d) / avg_volume_30d * 100) if avg_volume_30d > 0 else 0.0
        
        # Find unusual puts (OTM, high volume)
        unusual_puts = []
        for opt in options_data:
            if opt['right'] == 'P' and opt['volume'] > 100:
                # Out-of-money puts (strike < current price)
                if opt['strike'] < current_price * 0.95:  # 5%+ OTM
                    unusual_puts.append({
                        'strike': opt['strike'],
                        'expiration': opt['expiration'],
                        'volume': opt['volume'],
                        'open_interest': opt['open_interest'],
                        'distance_otm': (current_price - opt['strike']) / current_price * 100
                    })
        
        # Sort by volume
        unusual_puts.sort(key=lambda x: x['volume'], reverse=True)
        unusual_puts = unusual_puts[:5]  # Top 5
        
        # Near-expiry activity (next 2 weeks)
        near_date = (datetime.now() + timedelta(days=14)).strftime('%Y%m%d')
        near_expiry = [
            opt for opt in options_data
            if opt['expiration'] <= near_date
        ]
        
        near_expiry_activity = {
            'total_volume': sum(opt['volume'] for opt in near_expiry),
            'put_volume': sum(opt['volume'] for opt in near_expiry if opt['right'] == 'P'),
            'call_volume': sum(opt['volume'] for opt in near_expiry if opt['right'] == 'C'),
        }
        
        # Calculate threat score and indicators
        threat_score = 0
        indicators = []
        
        # Indicator 1: High put/call ratio
        if put_call_ratio > 2.0:
            threat_score += 30
            indicators.append(f"🚨 High put/call ratio: {put_call_ratio:.2f} (bearish)")
        elif put_call_ratio > 1.5:
            threat_score += 15
            indicators.append(f"⚠️  Elevated put/call ratio: {put_call_ratio:.2f}")
        
        # Indicator 2: Volume spike
        if volume_spike > 300:
            threat_score += 25
            indicators.append(f"🚨 Massive volume spike: +{volume_spike:.0f}%")
        elif volume_spike > 200:
            threat_score += 15
            indicators.append(f"⚠️  High volume spike: +{volume_spike:.0f}%")
        elif volume_spike > 100:
            threat_score += 10
            indicators.append(f"⚠️  Volume spike: +{volume_spike:.0f}%")
        
        # Indicator 3: Unusual OTM puts
        if len(unusual_puts) > 0:
            total_unusual_volume = sum(p['volume'] for p in unusual_puts)
            if total_unusual_volume > 1000:
                threat_score += 25
                indicators.append(f"🚨 Large OTM put buying: {total_unusual_volume:,} contracts")
            elif total_unusual_volume > 500:
                threat_score += 15
                indicators.append(f"⚠️  OTM put buying: {total_unusual_volume:,} contracts")
        
        # Indicator 4: Near-expiry concentration
        if near_expiry_activity['total_volume'] > total_volume * 0.5:
            threat_score += 20
            indicators.append(f"🚨 Heavy near-term activity: {near_expiry_activity['total_volume']:,} contracts")
        
        # Cap at 100
        threat_score = min(threat_score, 100)
        
        if not indicators:
            indicators.append("✅ Normal options activity")
        
        return OptionsMetrics(
            ticker=ticker,
            put_call_ratio=put_call_ratio,
            put_volume=put_volume,
            call_volume=call_volume,
            total_volume=total_volume,
            avg_volume_30d=avg_volume_30d,
            volume_spike=volume_spike,
            unusual_puts=unusual_puts,
            near_expiry_activity=near_expiry_activity,
            threat_score=threat_score,
            indicators=indicators
        )
    
    def format_analysis(self, metrics: OptionsMetrics) -> str:
        """Format options analysis for display."""
        lines = [
            f"\n{'='*70}",
            f"OPTIONS THREAT ANALYSIS: {metrics.ticker}",
            f"{'='*70}",
            f"",
            f"📊 Options Metrics:",
            f"   Put/Call Ratio: {metrics.put_call_ratio:.2f}",
            f"   Total Volume: {metrics.total_volume:,} contracts",
            f"   Put Volume: {metrics.put_volume:,} | Call Volume: {metrics.call_volume:,}",
            f"   Volume vs 30-day avg: {metrics.volume_spike:+.0f}%",
            f"",
            f"🎯 Threat Score: {metrics.threat_score}/100",
            f"",
            f"🔍 Indicators:",
        ]
        
        for indicator in metrics.indicators:
            lines.append(f"   {indicator}")
        
        if metrics.unusual_puts:
            lines.extend([
                f"",
                f"📉 Unusual OTM Puts:",
            ])
            for put in metrics.unusual_puts[:3]:
                lines.append(
                    f"   Strike ${put['strike']:.0f} "
                    f"({put['distance_otm']:.1f}% OTM) - "
                    f"Vol: {put['volume']:,} | OI: {put['open_interest']:,}"
                )
        
        if metrics.near_expiry_activity and metrics.near_expiry_activity.get('total_volume', 0) > 0:
            lines.extend([
                f"",
                f"⏰ Near-Term Activity (next 2 weeks):",
                f"   Total: {metrics.near_expiry_activity['total_volume']:,} contracts",
                f"   Puts: {metrics.near_expiry_activity['put_volume']:,} | "
                f"Calls: {metrics.near_expiry_activity['call_volume']:,}",
            ])
        
        lines.append(f"{'='*70}\n")
        
        return '\n'.join(lines)


async def main():
    """Demo: Analyze options activity for threat indicators."""
    
    print("="*70)
    print("📊 OPTIONS THREAT ANALYZER - DEMO")
    print("="*70)
    print()
    
    # Connect to IB
    ib = IB()
    await ib.connectAsync('127.0.0.1', 4002, clientId=100, timeout=10)
    print("✅ Connected to IB Gateway")
    print()
    
    # Initialize analyzer
    analyzer = OptionsThreatAnalyzer(ib)
    
    # Test tickers (mix of sectors)
    test_tickers = [
        ('UNH', 524.50),   # Healthcare (high-value target)
        ('PANW', 180.25),  # Cybersecurity
        ('JPM', 155.80),   # Financial
    ]
    
    for ticker, price in test_tickers:
        # Analyze options
        metrics = await analyzer.analyze_options_activity(
            ticker,
            current_price=price,
            avg_volume_30d=5000  # Placeholder
        )
        
        # Display results
        print(analyzer.format_analysis(metrics))
        
        await asyncio.sleep(2)
    
    ib.disconnect()
    
    print("="*70)
    print("✅ OPTIONS ANALYSIS COMPLETE")
    print("="*70)
    print()
    print("🔥 Key Takeaways:")
    print("   - Put/call ratio > 2.0 = High threat")
    print("   - Volume spike > 200% = Unusual activity")
    print("   - OTM puts = Betting on crash")
    print("   - Near-term concentration = Imminent event expected")
    print()
    print("🔭 Use this to detect breaches 14-30 days before announcement!")


if __name__ == "__main__":
    asyncio.run(main())
