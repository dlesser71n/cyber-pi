#!/usr/bin/env python3
"""
Financial Threat Collector
Monitors stock/options activity for pre-breach indicators
Runs every 30 minutes, pushes high-threat findings to Periscope L1
"""

import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from intelligence.ibkr_financial_integration import IBKRFinancialThreatIntegration
from intelligence.options_threat_analyzer import OptionsThreatAnalyzer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Watchlist: Key stocks to monitor
# Prioritize: Nexum clients, Fortune 500, high-value breach targets
WATCHLIST = [
    # Healthcare (High-value breach targets)
    'UNH', 'CVS', 'CI', 'HUM', 'HCA', 'CNC', 'MOH', 'ANTM',
    
    # Financial Services (Critical infrastructure)
    'JPM', 'BAC', 'WFC', 'C', 'GS', 'MS', 'BLK', 'SCHW',
    
    # Technology (High-profile targets)
    'MSFT', 'AAPL', 'GOOGL', 'AMZN', 'META', 'ORCL', 'CRM',
    
    # Cybersecurity (Industry intelligence)
    'PANW', 'CRWD', 'ZS', 'FTNT', 'OKTA',
    
    # Energy/Utilities (Critical infrastructure)
    'NEE', 'DUK', 'SO', 'D', 'AEP',
    
    # Airlines (Nexum clients)
    'DAL', 'UAL', 'AAL', 'LUV',
    
    # Defense (High-security targets)
    'LMT', 'RTX', 'NOC', 'GD', 'BA',
]


class FinancialThreatCollector:
    """
    Collects financial threat intelligence and pushes to Periscope.
    
    Monitors stock/options activity for unusual patterns that indicate
    potential breaches 14-30 days before public announcement.
    """
    
    def __init__(self, watchlist: List[str] = None):
        self.watchlist = watchlist or WATCHLIST
        self.integration = None
        self.options_analyzer = None
        
        # Output directory for threat data
        self.output_dir = Path('data/financial_threats')
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("📊 Financial Threat Collector initialized")
        logger.info(f"   Watchlist: {len(self.watchlist)} tickers")
    
    async def connect(self):
        """Connect to IBKR Gateway."""
        self.integration = IBKRFinancialThreatIntegration()
        
        connected = await self.integration.connect()
        if not connected:
            raise ConnectionError("Failed to connect to IBKR Gateway")
        
        self.options_analyzer = OptionsThreatAnalyzer(self.integration.ibkr.ib)
        logger.info("✅ Connected to IBKR Gateway")
    
    async def disconnect(self):
        """Disconnect from IBKR Gateway."""
        if self.integration:
            await self.integration.disconnect()
    
    async def collect_threat(self, ticker: str) -> Dict:
        """
        Collect threat intelligence for a single ticker.
        
        Args:
            ticker: Stock symbol
            
        Returns:
            Threat data dictionary
        """
        try:
            # Get current stock price
            market_data = await self.integration.get_stock_data(ticker)
            
            if not market_data:
                logger.warning(f"No market data for {ticker}")
                return None
            
            current_price = market_data.get('price', 0)
            
            # Analyze options activity
            options_metrics = await self.options_analyzer.analyze_options_activity(
                ticker,
                current_price=current_price,
                avg_volume_30d=5000  # Placeholder - could fetch historical
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
                'timestamp': datetime.now().isoformat(),
                'source': 'IBKR Financial Intelligence',
                'collection_run': datetime.now().strftime('%Y%m%d_%H%M'),
            }
            
            return threat_data
            
        except Exception as e:
            logger.error(f"Error collecting threat for {ticker}: {e}")
            return None
    
    async def collect_all_threats(self) -> List[Dict]:
        """
        Collect threats for entire watchlist.
        
        Returns:
            List of threat data dictionaries
        """
        logger.info(f"🔍 Collecting threats for {len(self.watchlist)} tickers...")
        
        threats = []
        high_threats = []
        
        for i, ticker in enumerate(self.watchlist, 1):
            logger.info(f"   [{i}/{len(self.watchlist)}] Analyzing {ticker}...")
            
            threat = await self.collect_threat(ticker)
            
            if threat:
                threats.append(threat)
                
                if threat['threat_score'] >= 70:
                    high_threats.append(threat)
                    logger.warning(f"   🚨 HIGH THREAT: {ticker} - Score: {threat['threat_score']}/100")
            
            # Rate limiting
            await asyncio.sleep(1)
        
        logger.info(f"✅ Collection complete: {len(threats)} threats, {len(high_threats)} high-priority")
        
        return threats
    
    async def push_to_periscope(self, threat_data: Dict):
        """
        Push threat to Periscope L1 working memory.
        
        Args:
            threat_data: Threat data dictionary
        """
        try:
            # Import Periscope L1
            from periscope.level1_memory import Level1Memory
            
            # Connect to Periscope
            l1 = Level1Memory()
            await l1.connect()
            
            # Create threat ID
            threat_id = f"financial_{threat_data['ticker']}_{threat_data['collection_run']}"
            
            # Build content summary
            content = f"""Financial Threat Detected: {threat_data['company']} ({threat_data['ticker']})

Industry: {threat_data['industry']}
Threat Score: {threat_data['threat_score']}/100
Confidence: {threat_data['confidence']}

Indicators:
{chr(10).join('- ' + ind for ind in threat_data['indicators'])}

Metrics:
- Current Price: ${threat_data['metrics']['current_price']:.2f}
- Put/Call Ratio: {threat_data['metrics']['put_call_ratio']:.2f}
- Volume Spike: {threat_data['metrics']['volume_spike']:.0f}%
- Unusual Puts: {threat_data['metrics']['unusual_puts_count']} contracts
- Near-Term Activity: {threat_data['metrics']['near_term_activity']:,.0f} contracts

Source: {threat_data['source']}
Timestamp: {threat_data['timestamp']}
"""
            
            # Determine severity
            if threat_data['threat_score'] >= 80:
                severity = 'critical'
            elif threat_data['threat_score'] >= 70:
                severity = 'high'
            elif threat_data['threat_score'] >= 50:
                severity = 'medium'
            else:
                severity = 'low'
            
            # Push to Periscope L1
            working_memory = await l1.add_threat(
                threat_id=threat_id,
                content=content,
                severity=severity,
                metadata={
                    'type': 'financial_threat',
                    'ticker': threat_data['ticker'],
                    'company': threat_data['company'],
                    'industry': threat_data['industry'],
                    'threat_score': threat_data['threat_score'],
                    'confidence': threat_data['confidence'],
                    'source': threat_data['source'],
                    'collection_run': threat_data['collection_run'],
                    'raw_data': threat_data
                }
            )
            
            await l1.disconnect()
            
            logger.info(f"✅ Pushed to Periscope L1: {threat_id}")
            
        except Exception as e:
            logger.error(f"Failed to push to Periscope: {e}")
            # Fallback: save to file
            output_file = self.output_dir / f"threat_{threat_data['ticker']}_{threat_data['collection_run']}.json"
            with open(output_file, 'w') as f:
                json.dump(threat_data, f, indent=2)
            logger.info(f"💾 Saved threat to file: {output_file}")
    
    async def run_collection(self):
        """Run full collection cycle."""
        try:
            # Connect
            await self.connect()
            
            # Collect threats
            threats = await self.collect_all_threats()
            
            # Push high-priority threats to Periscope
            high_threats = [t for t in threats if t['threat_score'] >= 70]
            
            for threat in high_threats:
                await self.push_to_periscope(threat)
            
            # Save summary
            summary = {
                'timestamp': datetime.now().isoformat(),
                'total_analyzed': len(self.watchlist),
                'threats_found': len(threats),
                'high_priority': len(high_threats),
                'high_threat_tickers': [t['ticker'] for t in high_threats],
                'threats': threats,
            }
            
            summary_file = self.output_dir / f"summary_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
            with open(summary_file, 'w') as f:
                json.dump(summary, f, indent=2)
            
            logger.info(f"📊 Summary saved to: {summary_file}")
            
            # Disconnect
            await self.disconnect()
            
            return summary
            
        except Exception as e:
            logger.error(f"❌ Collection failed: {e}")
            if self.integration:
                await self.disconnect()
            raise
    
    def _get_company_name(self, ticker: str) -> str:
        """Get company name from ticker (placeholder)."""
        # TODO: Implement actual company name lookup
        company_map = {
            'UNH': 'UnitedHealth Group',
            'JPM': 'JPMorgan Chase',
            'MSFT': 'Microsoft',
            'PANW': 'Palo Alto Networks',
            'DAL': 'Delta Air Lines',
            'LMT': 'Lockheed Martin',
        }
        return company_map.get(ticker, ticker)
    
    def _get_industry(self, ticker: str) -> str:
        """Get industry from ticker (placeholder)."""
        # TODO: Implement actual industry lookup
        industry_map = {
            'UNH': 'Healthcare',
            'CVS': 'Healthcare',
            'JPM': 'Financial Services',
            'BAC': 'Financial Services',
            'MSFT': 'Technology',
            'AAPL': 'Technology',
            'PANW': 'Cybersecurity',
            'CRWD': 'Cybersecurity',
            'DAL': 'Airlines',
            'UAL': 'Airlines',
            'LMT': 'Defense',
            'RTX': 'Defense',
        }
        return industry_map.get(ticker, 'Unknown')


async def main():
    """Run financial threat collection."""
    
    print("="*70)
    print("🔭 FINANCIAL THREAT COLLECTOR")
    print("="*70)
    print()
    
    collector = FinancialThreatCollector()
    
    summary = await collector.run_collection()
    
    print()
    print("="*70)
    print("📊 COLLECTION SUMMARY")
    print("="*70)
    print(f"Total Analyzed: {summary['total_analyzed']}")
    print(f"Threats Found: {summary['threats_found']}")
    print(f"High Priority: {summary['high_priority']}")
    
    if summary['high_threat_tickers']:
        print()
        print("🚨 HIGH THREAT TICKERS:")
        for ticker in summary['high_threat_tickers']:
            threat = next(t for t in summary['threats'] if t['ticker'] == ticker)
            print(f"   {ticker}: {threat['threat_score']}/100 - {threat['company']}")
    
    print()
    print("="*70)
    print("✅ COLLECTION COMPLETE")
    print("="*70)


if __name__ == "__main__":
    asyncio.run(main())
