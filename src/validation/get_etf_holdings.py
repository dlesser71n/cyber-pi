#!/usr/bin/env python3
"""
Get ETF Holdings
Extract top holdings from cybersecurity and AI ETFs

Purpose: Identify which companies to monitor based on ETF composition
"""

import yfinance as yf
import json

# ETFs to analyze
CYBERSECURITY_ETFS = {
    'HACK': 'ETFMG Prime Cyber Security ETF',
    'CIBR': 'First Trust NASDAQ Cybersecurity ETF',
    'BUG': 'Global X Cybersecurity ETF',
    'IHAK': 'iShares Cybersecurity and Tech ETF'
}

AI_ETFS = {
    'BOTZ': 'Global X Robotics & AI ETF',
    'ROBO': 'ROBO Global Robotics & Automation ETF',
    'IRBO': 'iShares Robotics and AI ETF',
    'AIQ': 'Global X AI & Technology ETF'
}


def get_etf_holdings(ticker: str, name: str):
    """Get top holdings for an ETF"""
    print(f"\n{'='*70}")
    print(f"📊 {ticker}: {name}")
    print('='*70)
    
    try:
        etf = yf.Ticker(ticker)
        
        # Get holdings (if available)
        # Note: Yahoo Finance may not always have holdings data
        info = etf.info
        
        print(f"Category: {info.get('category', 'N/A')}")
        print(f"Total Assets: ${info.get('totalAssets', 0):,.0f}")
        print(f"YTD Return: {info.get('ytdReturn', 0)*100:.2f}%")
        
        # Try to get holdings
        # Note: This may not work for all ETFs via yfinance
        print("\nTop Holdings:")
        print("(Note: Holdings data may not be available via Yahoo Finance)")
        print("Recommend checking ETF provider website for full holdings")
        
    except Exception as e:
        print(f"Error: {e}")


def main():
    """Analyze all ETFs"""
    
    print("="*70)
    print("🔍 CYBERSECURITY & AI ETF ANALYSIS")
    print("="*70)
    
    print("\n" + "="*70)
    print("🛡️  CYBERSECURITY ETFs")
    print("="*70)
    
    for ticker, name in CYBERSECURITY_ETFS.items():
        get_etf_holdings(ticker, name)
    
    print("\n" + "="*70)
    print("🤖 AI/ROBOTICS ETFs")
    print("="*70)
    
    for ticker, name in AI_ETFS.items():
        get_etf_holdings(ticker, name)
    
    print("\n" + "="*70)
    print("📝 RECOMMENDED WATCHLIST")
    print("="*70)
    print("""
Based on common holdings in these ETFs, monitor:

CYBERSECURITY:
- PANW (Palo Alto Networks)
- CRWD (CrowdStrike)
- ZS (Zscaler)
- FTNT (Fortinet)
- OKTA (Okta)
- S (SentinelOne)
- CHKP (Check Point)
- CYBR (CyberArk)
- TENB (Tenable)
- RPD (Rapid7)
- QLYS (Qualys)
- VRNS (Varonis)

AI/TECH:
- NVDA (NVIDIA)
- MSFT (Microsoft)
- GOOGL (Google)
- AMZN (Amazon)
- META (Meta)
- TSLA (Tesla)
- PLTR (Palantir)

BREACH TARGETS:
- UNH (Healthcare)
- CVS (Healthcare)
- JPM (Financial)
- BAC (Financial)
- DAL (Airlines)
- LMT (Defense)

Total: 25 tickers
    """)
    
    print("="*70)
    print("✅ Analysis complete")
    print("="*70)
    print("\nFor detailed holdings, visit:")
    print("- HACK: https://www.etfmg.com/funds/HACK")
    print("- CIBR: https://www.ftportfolios.com/retail/etf/etfsummary.aspx?Ticker=CIBR")
    print("- BUG: https://www.globalxetfs.com/funds/bug/")
    print("- BOTZ: https://www.globalxetfs.com/funds/botz/")


if __name__ == "__main__":
    main()
