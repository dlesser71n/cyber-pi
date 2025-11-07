#!/usr/bin/env python3
"""
Financial Validation Collector
Minimal implementation for 30-day validation

Purpose: Collect options data to validate if financial indicators
         can predict cyber breaches 14-30 days in advance.

Approach: Simple, automated, free (Yahoo Finance)
Duration: 30 days
Cost: $0
"""

import yfinance as yf
import redis
import json
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ETFs to track for holdings
CYBERSECURITY_ETFS = ['HACK', 'CIBR', 'BUG', 'IHAK']  # Cybersecurity ETFs
AI_ETFS = ['BOTZ', 'ROBO', 'IRBO', 'AIQ']  # AI/Robotics ETFs

# Tickers to monitor
# Will be populated from ETF holdings + manual additions
WATCHLIST = [
    # Cybersecurity Companies (from HACK, CIBR, BUG ETFs)
    'PANW',  # Palo Alto Networks
    'CRWD',  # CrowdStrike
    'ZS',    # Zscaler
    'FTNT',  # Fortinet
    'OKTA',  # Okta
    'S',     # SentinelOne
    'CHKP',  # Check Point
    'CYBR',  # CyberArk
    'TENB',  # Tenable
    'RPD',   # Rapid7
    'QLYS',  # Qualys
    'VRNS',  # Varonis
    
    # AI/Tech Companies (from AI ETFs)
    'NVDA',  # NVIDIA
    'MSFT',  # Microsoft
    'GOOGL', # Google
    'AMZN',  # Amazon
    'META',  # Meta
    'TSLA',  # Tesla
    'PLTR',  # Palantir
    
    # High-Value Breach Targets
    'UNH',   # UnitedHealth (healthcare)
    'CVS',   # CVS Health
    'JPM',   # JPMorgan (financial)
    'BAC',   # Bank of America
    'DAL',   # Delta (airlines)
    'LMT',   # Lockheed Martin (defense)
]


def collect_ticker(ticker: str) -> dict:
    """
    Collect options data for a ticker
    
    Args:
        ticker: Stock symbol
        
    Returns:
        Dictionary with metrics or None if error
    """
    try:
        logger.info(f"Collecting {ticker}...")
        
        stock = yf.Ticker(ticker)
        
        # Get options expirations
        if not stock.options:
            logger.warning(f"No options data for {ticker}")
            return None
        
        # Get first expiration (nearest term)
        chain = stock.option_chain(stock.options[0])
        
        # Calculate basic metrics
        put_volume = chain.puts['volume'].sum()
        call_volume = chain.calls['volume'].sum()
        put_oi = chain.puts['openInterest'].sum()
        call_oi = chain.calls['openInterest'].sum()
        
        put_call_ratio = put_volume / call_volume if call_volume > 0 else 0
        
        # Count unusual OTM puts (simple heuristic)
        current_price = stock.history(period='1d')['Close'].iloc[-1]
        otm_threshold = current_price * 0.90  # 10% OTM
        unusual_puts = len(chain.puts[
            (chain.puts['strike'] < otm_threshold) & 
            (chain.puts['volume'] > 100)
        ])
        
        # Simple threat score (0-100)
        threat_score = 0
        
        if put_call_ratio > 2.0:
            threat_score += 40
        elif put_call_ratio > 1.5:
            threat_score += 20
        
        if put_volume > 10000:
            threat_score += 30
        elif put_volume > 5000:
            threat_score += 15
        
        if unusual_puts > 5:
            threat_score += 30
        elif unusual_puts > 2:
            threat_score += 15
        
        data = {
            'ticker': ticker,
            'timestamp': datetime.now().isoformat(),
            'put_call_ratio': float(put_call_ratio),
            'put_volume': int(put_volume),
            'call_volume': int(call_volume),
            'put_oi': int(put_oi),
            'call_oi': int(call_oi),
            'unusual_puts': int(unusual_puts),
            'threat_score': min(threat_score, 100),
            'current_price': float(current_price)
        }
        
        logger.info(f"✅ {ticker}: score={data['threat_score']}, P/C={data['put_call_ratio']:.2f}")
        
        return data
        
    except Exception as e:
        logger.error(f"Error collecting {ticker}: {e}")
        return None


def main():
    """Collect data for all tickers and store in Redis"""
    
    logger.info("="*70)
    logger.info("📊 FINANCIAL VALIDATION COLLECTOR")
    logger.info("="*70)
    logger.info(f"Monitoring {len(WATCHLIST)} tickers")
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    logger.info("")
    
    # Connect to Redis
    try:
        r = redis.Redis(host='localhost', port=32379, decode_responses=True)
        r.ping()
        logger.info("✅ Connected to Redis")
    except Exception as e:
        logger.error(f"❌ Failed to connect to Redis: {e}")
        return
    
    # Collect data for each ticker
    collected = 0
    high_threats = []
    
    for ticker in WATCHLIST:
        data = collect_ticker(ticker)
        
        if data:
            # Store in Redis with 90-day TTL
            key = f"validation:financial:{ticker}:{datetime.now().strftime('%Y%m%d_%H%M')}"
            r.setex(key, 7776000, json.dumps(data))  # 90 days = 7776000 seconds
            
            collected += 1
            
            if data['threat_score'] >= 70:
                high_threats.append(data)
    
    logger.info("")
    logger.info("="*70)
    logger.info("📊 COLLECTION SUMMARY")
    logger.info("="*70)
    logger.info(f"Total tickers: {len(WATCHLIST)}")
    logger.info(f"Collected: {collected}")
    logger.info(f"High threats (≥70): {len(high_threats)}")
    
    if high_threats:
        logger.info("")
        logger.info("🚨 HIGH THREAT SIGNALS:")
        for threat in high_threats:
            logger.info(f"   {threat['ticker']}: {threat['threat_score']}/100 (P/C={threat['put_call_ratio']:.2f})")
    
    logger.info("")
    logger.info("✅ Collection complete")
    logger.info("="*70)


if __name__ == "__main__":
    main()
