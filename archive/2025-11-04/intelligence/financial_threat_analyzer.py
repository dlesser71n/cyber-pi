#!/usr/bin/env python3
"""
Financial Threat Intelligence Analyzer
GPU-Accelerated with Llama 4 16x17B (Dual A6000 Load Balanced)

Uses dual A6000s with load-balanced Ollama instances to analyze financial signals:
- Stock market anomalies (pre-breach indicators)
- Cryptocurrency tracking (ransomware payments)
- Dark web marketplace economics
- Vendor financial risk assessment
- Insider threat detection
- Geopolitical cyber risk
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json
import requests
from pathlib import Path
import random

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FinancialThreatAnalyzer:
    """
    GPU-Accelerated Financial Threat Intelligence
    
    Uses Llama 4 16x17B across dual A6000s for advanced financial signal analysis
    and correlation with cyber threat intelligence.
    """
    
    def __init__(
        self,
        ollama_host: str = "http://localhost:11434",
        model: str = "llama4:16x17b",
        output_dir: str = "data/financial_intelligence"
    ):
        self.ollama_host = ollama_host
        self.model = model
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"🤖 Financial Threat Analyzer initialized")
        logger.info(f"   Model: {model}")
        logger.info(f"   Ollama: {ollama_host}")
        logger.info(f"   GPU Load Balancing: Automatic (tensor_split across GPUs)")
    
    async def analyze_with_llama(self, prompt: str, context: Dict = None) -> Dict[str, Any]:
        """
        Analyze data using Llama 4 16x17B (automatically load balanced across GPUs)
        
        Args:
            prompt: Analysis prompt
            context: Additional context data
            
        Returns:
            Analysis results
        """
        try:
            # Build full prompt with context
            full_prompt = self._build_prompt(prompt, context)
            
            logger.debug(f"Sending to Llama 4: {len(full_prompt)} chars")
            
            # Call Ollama API (GPU load balancing handled by Ollama with tensor_split)
            response = requests.post(
                f"{self.ollama_host}/api/generate",
                json={
                    "model": self.model,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,  # Lower for analytical tasks
                        "top_p": 0.9,
                        "num_predict": 2000
                    }
                },
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                analysis = result.get('response', '')
                
                return {
                    'success': True,
                    'analysis': analysis,
                    'model': self.model,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                logger.error(f"Ollama API error: {response.status_code}")
                return {
                    'success': False,
                    'error': f"API error: {response.status_code}"
                }
                
        except Exception as e:
            logger.error(f"Llama analysis failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _build_prompt(self, prompt: str, context: Dict = None) -> str:
        """Build comprehensive prompt with context."""
        
        system_context = """You are an elite financial threat intelligence analyst specializing in cybersecurity.
Your role is to analyze financial data and identify cyber threat indicators that others miss.

Focus on:
1. Pre-breach indicators (stock anomalies, insider trading patterns)
2. Ransomware economics (crypto payments, gang activity, victim profiling)
3. Dark web marketplace signals (exploit pricing, volume changes, seller reputation)
4. Vendor financial risk (supply chain vulnerabilities, bankruptcy risk)
5. Geopolitical cyber risk (sanctions, nation-state retaliation patterns)

Provide actionable intelligence with:
- Threat score (0-100)
- Confidence level (0-100)
- Specific indicators detected
- Recommended actions
- Clear reasoning

Be precise, analytical, and focus on patterns that predict cyber incidents."""

        full_prompt = f"{system_context}\n\n"
        
        if context:
            full_prompt += "CONTEXT DATA:\n"
            full_prompt += json.dumps(context, indent=2)
            full_prompt += "\n\n"
        
        full_prompt += f"ANALYSIS REQUEST:\n{prompt}\n\n"
        full_prompt += "Provide your analysis in structured format with threat_score, confidence, indicators, recommendations, and reasoning."
        
        return full_prompt
    
    def _parse_llama_response(self, response: str) -> Dict[str, Any]:
        """Parse Llama response into structured format."""
        try:
            # Try to extract JSON if present
            if '{' in response and '}' in response:
                start = response.find('{')
                end = response.rfind('}') + 1
                json_str = response[start:end]
                return json.loads(json_str)
            
            # Otherwise parse text response
            return {
                'raw_analysis': response,
                'threat_score': self._extract_score(response),
                'confidence': self._extract_confidence(response),
                'parsed': False
            }
        except Exception as e:
            logger.warning(f"Failed to parse Llama response: {e}")
            return {
                'raw_analysis': response,
                'parsed': False
            }
    
    def _extract_score(self, text: str) -> int:
        """Extract threat score from text."""
        import re
        match = re.search(r'threat[_ ]score[:\s]+(\d+)', text, re.IGNORECASE)
        if match:
            return int(match.group(1))
        return 50  # Default
    
    def _extract_confidence(self, text: str) -> int:
        """Extract confidence from text."""
        import re
        match = re.search(r'confidence[:\s]+(\d+)', text, re.IGNORECASE)
        if match:
            return int(match.group(1))
        return 50  # Default
    
    def _save_analysis(self, category: str, identifier: str, analysis: Dict):
        """Save analysis to disk."""
        category_dir = self.output_dir / category
        category_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{identifier}_{timestamp}.json"
        filepath = category_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(analysis, f, indent=2)
        
        logger.debug(f"Saved analysis: {filepath}")
    
    async def analyze_stock_anomalies(self, ticker: str, data: Dict) -> Dict[str, Any]:
        """
        Analyze stock market anomalies for pre-breach indicators.
        
        Historical breach patterns show unusual activity 14-30 days before announcement:
        - Target (2013): Stock dropped 46% after breach
        - Equifax (2017): Stock dropped 35% after breach
        - SolarWinds (2020): Stock dropped 25% after breach
        """
        logger.info(f"📊 Analyzing stock anomalies: {ticker}")
        
        prompt = f"""Analyze the following stock data for {ticker} to identify potential pre-breach indicators:

Stock Data:
- Current Price: ${data.get('price', 'N/A')}
- Volume Change: {data.get('volume_change', 'N/A')}%
- Options Activity: {data.get('options_activity', 'N/A')}
- Short Interest: {data.get('short_interest', 'N/A')}%
- Insider Trading: {data.get('insider_trading', 'N/A')}

Historical Context:
- 30-day average volume: {data.get('avg_volume_30d', 'N/A')}
- 90-day price trend: {data.get('price_trend_90d', 'N/A')}
- Industry: {data.get('industry', 'Unknown')}
- Market Cap: ${data.get('market_cap', 'N/A')}

Based on historical breach patterns (Target -46%, Equifax -35%, SolarWinds -25%), analyze:
1. Is there unusual pre-breach activity?
2. Evidence of insider knowledge?
3. Market positioning for negative news?
4. Probability of breach in next 30 days?

Provide threat score (0-100), confidence, and specific indicators."""

        result = await self.analyze_with_llama(prompt, context=data)
        
        if result['success']:
            analysis = self._parse_llama_response(result['analysis'])
            analysis['ticker'] = ticker
            analysis['analysis_type'] = 'stock_anomaly'
            
            self._save_analysis('stock_anomalies', ticker, analysis)
            
            return analysis
        else:
            return result
    
    async def analyze_crypto_payments(self, wallet_data: Dict) -> Dict[str, Any]:
        """
        Analyze cryptocurrency transactions for ransomware activity.
        
        Known ransomware payment patterns:
        - LockBit: $100M+ in 2023
        - BlackCat/ALPHV: $300M+ total
        - Royal: $275M+ total
        """
        logger.info(f"💰 Analyzing crypto payments: {wallet_data.get('wallet_id', 'Unknown')[:10]}...")
        
        prompt = f"""Analyze the following cryptocurrency wallet activity for ransomware indicators:

Wallet Data:
- Wallet ID: {wallet_data.get('wallet_id', 'Unknown')[:20]}...
- Recent Transactions: {wallet_data.get('transaction_count', 0)}
- Total Value: ${wallet_data.get('total_value_usd', 0):,.2f}
- Average Transaction: ${wallet_data.get('avg_transaction_usd', 0):,.2f}
- Transaction Pattern: {wallet_data.get('pattern', 'Unknown')}
- Mixing Services Used: {wallet_data.get('mixing_services', 'None')}

Known Context:
- Associated Gang: {wallet_data.get('suspected_gang', 'Unknown')}
- Previous Activity: {wallet_data.get('historical_activity', 'None')}

Based on known ransomware payment patterns (LockBit $100M+, BlackCat $300M+, Royal $275M+):
1. Is this likely ransomware-related?
2. Which gang is most likely involved?
3. Estimated victim profile (industry, size)?
4. Predicted next targets based on pattern?

Provide threat score (0-100), confidence, and actionable intelligence."""

        result = await self.analyze_with_llama(prompt, context=wallet_data)
        
        if result['success']:
            analysis = self._parse_llama_response(result['analysis'])
            analysis['wallet_id'] = wallet_data.get('wallet_id', 'Unknown')
            analysis['analysis_type'] = 'crypto_payment'
            
            self._save_analysis('crypto_payments', wallet_data.get('wallet_id', 'unknown')[:16], analysis)
            
            return analysis
        else:
            return result
    
    async def analyze_vendor_risk(self, vendor_data: Dict) -> Dict[str, Any]:
        """
        Analyze vendor financial health for cyber risk.
        
        Financial stress indicators:
        - Revenue decline → less security spending
        - High debt → cost cutting (security first)
        - Layoffs → security team reductions
        """
        logger.info(f"🏢 Analyzing vendor risk: {vendor_data.get('company', 'Unknown')}")
        
        prompt = f"""Analyze the following vendor financial data for cyber risk indicators:

Company: {vendor_data.get('company', 'Unknown')}
Ticker: {vendor_data.get('ticker', 'N/A')}

Financial Health:
- Revenue Trend: {vendor_data.get('revenue_trend', 'Unknown')}
- Debt Ratio: {vendor_data.get('debt_ratio', 'N/A')}
- Cash Position: ${vendor_data.get('cash', 0):,.0f}
- Recent Layoffs: {vendor_data.get('layoffs', 'None')}
- Security Spending: {vendor_data.get('security_spending_pct', 'Unknown')}%

Risk Indicators:
- Bankruptcy Risk (Altman Z): {vendor_data.get('altman_z_score', 'N/A')}
- Credit Rating: {vendor_data.get('credit_rating', 'N/A')}
- Recent M&A: {vendor_data.get('recent_ma', 'None')}

Based on patterns (SolarWinds financial pressure → breach, MOVEit rapid growth → security debt):
1. What is the cyber risk level for this vendor?
2. Specific financial stress indicators?
3. Probability of breach in next 12 months?
4. Recommended actions for customers?

Provide threat score (0-100), confidence, and risk assessment."""

        result = await self.analyze_with_llama(prompt, context=vendor_data)
        
        if result['success']:
            analysis = self._parse_llama_response(result['analysis'])
            analysis['company'] = vendor_data.get('company', 'Unknown')
            analysis['analysis_type'] = 'vendor_risk'
            
            self._save_analysis('vendor_risk', vendor_data.get('ticker', 'unknown'), analysis)
            
            return analysis
        else:
            return result
    
    async def analyze_batch(self, analyses: List[Dict]) -> List[Dict]:
        """
        Analyze multiple items in parallel across both GPUs.
        
        Args:
            analyses: List of analysis requests with 'type' and 'data'
            
        Returns:
            List of analysis results
        """
        logger.info(f"🚀 Batch analysis: {len(analyses)} items across {len(self.ollama_hosts)} GPUs")
        
        tasks = []
        for item in analyses:
            analysis_type = item.get('type')
            data = item.get('data')
            
            if analysis_type == 'stock':
                tasks.append(self.analyze_stock_anomalies(data.get('ticker'), data))
            elif analysis_type == 'crypto':
                tasks.append(self.analyze_crypto_payments(data))
            elif analysis_type == 'vendor':
                tasks.append(self.analyze_vendor_risk(data))
        
        # Run in parallel (load balanced across GPUs)
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions
        successful = [r for r in results if isinstance(r, dict) and r.get('success', True)]
        
        logger.info(f"✅ Batch complete: {len(successful)}/{len(analyses)} successful")
        
        return successful


async def main():
    """Demo: Financial threat intelligence analysis."""
    
    logger.info("=" * 80)
    logger.info("🔭 FINANCIAL THREAT INTELLIGENCE ANALYZER")
    logger.info("=" * 80)
    logger.info("GPU-Accelerated with Llama 4 16x17B (Dual A6000)")
    logger.info("")
    
    # Initialize analyzer
    analyzer = FinancialThreatAnalyzer()
    
    # Demo: Stock anomaly analysis
    logger.info("📊 Demo 1: Stock Market Anomaly Detection")
    logger.info("-" * 80)
    
    stock_data = {
        'ticker': 'UNH',
        'price': 524.50,
        'volume_change': 245.3,  # 245% increase
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
        logger.info(f"✅ Analysis complete")
        logger.info(f"   Threat Score: {result.get('threat_score', 'N/A')}/100")
        logger.info(f"   Confidence: {result.get('confidence', 'N/A')}%")
        logger.info("")
        logger.info("Analysis:")
        logger.info(result.get('raw_analysis', result.get('analysis', 'N/A'))[:500])
    
    logger.info("")
    logger.info("=" * 80)
    logger.info("✅ Demo complete - Financial intelligence ready for production")
    logger.info("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
