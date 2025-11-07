#!/usr/bin/env python3
"""
Fast Options Threat Analyzer
Uses IBKR snapshot API + batching + parallel processing
Rickover-approved: No scope reduction, just better engineering
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict
from dataclasses import dataclass

from ib_async import IB, Option

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class OptionsMetrics:
    """Options threat metrics"""
    ticker: str
    put_call_ratio: float
    volume_spike: float
    unusual_puts: List[Dict]
    near_expiry_activity: Dict
    threat_score: int
    indicators: List[str]


class FastOptionsThreatAnalyzer:
    """
    Fast options threat analyzer using:
    1. Snapshot API (not streaming)
    2. Batch requests (all at once)
    3. Parallel processing (multiple tickers)
    """
    
    def __init__(self, ib: IB):
        self.ib = ib
        logger.info("🚀 Fast Options Threat Analyzer initialized")
    
    async def get_options_chain_fast(self, ticker: str, days_out: int = 45) -> List[Option]:
        """
        Get options chain (same as before, this part is already fast).
        """
        try:
            # Create stock contract
            from ib_async import Stock
            stock = Stock(ticker, 'SMART', 'USD')
            
            # Qualify
            stock = await self.ib.qualifyContractsAsync(stock)
            if not stock:
                return []
            stock = stock[0]
            
            # Get options chain
            chains = await self.ib.reqSecDefOptParamsAsync(
                stock.symbol, '', stock.secType, stock.conId
            )
            
            if not chains:
                return []
            
            chain = chains[0]
            
            # Get near-term expirations
            target_date = datetime.now() + timedelta(days=days_out)
            near_expirations = [
                exp for exp in chain.expirations
                if datetime.strptime(exp, '%Y%m%d') <= target_date
            ][:3]
            
            # Build option contracts
            options = []
            for expiration in near_expirations:
                for strike in chain.strikes:
                    put = Option(ticker, expiration, strike, 'P', 'SMART')
                    call = Option(ticker, expiration, strike, 'C', 'SMART')
                    options.extend([put, call])
            
            return options
            
        except Exception as e:
            logger.error(f"Error getting options chain for {ticker}: {e}")
            return []
    
    async def get_options_data_fast(self, options: List[Option]) -> List[Dict]:
        """
        OPTIMIZED: Get market data using snapshots + batching.
        
        Key improvements:
        1. Use reqMktData with snapshot=True (faster)
        2. Batch all requests at once (parallel)
        3. Shorter wait time (1s vs 3s)
        
        Args:
            options: List of Option contracts
            
        Returns:
            List of option data dictionaries
        """
        try:
            if not options:
                return []
            
            # Qualify contracts (batch)
            qualified = await self.ib.qualifyContractsAsync(*options)
            
            if not qualified:
                return []
            
            # Request market data for ALL contracts at once (SNAPSHOT mode)
            # snapshot=True means one-time data request, not streaming
            tickers = []
            for opt in qualified:
                ticker = self.ib.reqMktData(
                    opt, 
                    '', 
                    snapshot=True,  # KEY: Snapshot mode (faster)
                    regulatorySnapshot=False
                )
                tickers.append(ticker)
            
            # Wait for snapshots
            await asyncio.sleep(2)  # Balanced: fast but gets data
            
            # Collect data
            options_data = []
            for ticker, contract in zip(tickers, qualified):
                # Check if we got data
                if hasattr(ticker, 'volume') and ticker.volume and ticker.volume > 0:
                    options_data.append({
                        'contract': contract,
                        'strike': contract.strike,
                        'right': contract.right,
                        'expiration': contract.lastTradeDateOrContractMonth,
                        'last': ticker.last if ticker.last else 0,
                        'bid': ticker.bid if ticker.bid else 0,
                        'ask': ticker.ask if ticker.ask else 0,
                        'volume': ticker.volume if ticker.volume else 0,
                        'open_interest': getattr(ticker, 'openInterest', 0) or 0,
                    })
            
            # Cancel market data subscriptions (cleanup)
            for ticker in tickers:
                self.ib.cancelMktData(ticker.contract)
            
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
        Same logic as before, but uses fast data fetching.
        """
        # Get options chain
        options = await self.get_options_chain_fast(ticker)
        
        if not options:
            return OptionsMetrics(
                ticker=ticker,
                put_call_ratio=0,
                volume_spike=0,
                unusual_puts=[],
                near_expiry_activity={},
                threat_score=0,
                indicators=[]
            )
        
        # Get options data (FAST)
        options_data = await self.get_options_data_fast(options)
        
        if not options_data:
            return OptionsMetrics(
                ticker=ticker,
                put_call_ratio=0,
                volume_spike=0,
                unusual_puts=[],
                near_expiry_activity={},
                threat_score=0,
                indicators=[]
            )
        
        # Calculate metrics (same as before)
        puts = [opt for opt in options_data if opt['right'] == 'P']
        calls = [opt for opt in options_data if opt['right'] == 'C']
        
        put_volume = sum(opt['volume'] for opt in puts)
        call_volume = sum(opt['volume'] for opt in calls)
        
        put_call_ratio = put_volume / call_volume if call_volume > 0 else 0
        
        # Volume spike
        total_volume = put_volume + call_volume
        volume_spike = (total_volume / avg_volume_30d - 1) * 100 if avg_volume_30d > 0 else 0
        
        # Unusual OTM puts
        unusual_puts = []
        for opt in puts:
            distance_otm = ((current_price - opt['strike']) / current_price) * 100
            if distance_otm > 5 and opt['volume'] > 100:
                unusual_puts.append({
                    'strike': opt['strike'],
                    'distance_otm': distance_otm,
                    'volume': opt['volume'],
                    'open_interest': opt['open_interest']
                })
        
        unusual_puts.sort(key=lambda x: x['volume'], reverse=True)
        
        # Near-term activity
        two_weeks = (datetime.now() + timedelta(days=14)).strftime('%Y%m%d')
        near_term = [opt for opt in options_data if opt['expiration'] <= two_weeks]
        
        near_expiry_activity = {
            'total_volume': sum(opt['volume'] for opt in near_term),
            'put_volume': sum(opt['volume'] for opt in near_term if opt['right'] == 'P'),
            'call_volume': sum(opt['volume'] for opt in near_term if opt['right'] == 'C'),
        }
        
        # Threat scoring
        threat_score = 0
        indicators = []
        
        if put_call_ratio > 2.0:
            threat_score += 30
            indicators.append(f"🚨 High put/call ratio: {put_call_ratio:.2f} (bearish)")
        
        if volume_spike > 200:
            threat_score += 25
            indicators.append(f"🚨 Massive volume spike: +{volume_spike:.0f}%")
        elif volume_spike > 100:
            threat_score += 15
            indicators.append(f"⚠️  Volume spike: +{volume_spike:.0f}%")
        
        if len(unusual_puts) > 0:
            threat_score += 25
            total_unusual = sum(p['volume'] for p in unusual_puts[:5])
            indicators.append(f"🚨 Large OTM put buying: {total_unusual:,.1f} contracts")
        
        if near_expiry_activity['total_volume'] > 1000:
            threat_score += 20
            indicators.append(f"🚨 Heavy near-term activity: {near_expiry_activity['total_volume']:,.1f} contracts")
        
        return OptionsMetrics(
            ticker=ticker,
            put_call_ratio=put_call_ratio,
            volume_spike=volume_spike,
            unusual_puts=unusual_puts,
            near_expiry_activity=near_expiry_activity,
            threat_score=min(threat_score, 100),
            indicators=indicators
        )


async def test_fast_analyzer():
    """Test the fast analyzer"""
    from ib_async import IB
    
    ib = IB()
    await ib.connectAsync('127.0.0.1', 4002, clientId=1)
    
    analyzer = FastOptionsThreatAnalyzer(ib)
    
    # Test with UNH
    print("Testing fast analyzer with UNH...")
    
    import time
    start = time.time()
    
    metrics = await analyzer.analyze_options_activity('UNH', 329.55)
    
    elapsed = time.time() - start
    
    print(f"\n✅ Analysis complete in {elapsed:.1f}s")
    print(f"Threat Score: {metrics.threat_score}/100")
    print(f"Indicators: {len(metrics.indicators)}")
    
    ib.disconnect()


if __name__ == "__main__":
    asyncio.run(test_fast_analyzer())
