#!/usr/bin/env python3
"""
Check IBKR Market Data Subscriptions
Tests access to options and crypto futures data
"""

import asyncio
from ib_async import IB, Stock, Option, Future

async def check_subscriptions():
    ib = IB()
    
    print('='*70)
    print('CHECKING IBKR MARKET DATA SUBSCRIPTIONS')
    print('='*70)
    print()
    
    # Connect with unique client ID
    print('📡 Connecting to IB Gateway (client ID 99)...')
    try:
        await ib.connectAsync('127.0.0.1', 4002, clientId=99, timeout=10)
        print('✅ Connected')
    except Exception as e:
        print(f'❌ Connection failed: {e}')
        return
    
    print()
    
    # Test 1: Basic stock data (should always work)
    print('1️⃣  Testing Basic Stock Data (FREE):')
    try:
        stock = Stock('AAPL', 'SMART', 'USD')
        ticker = ib.reqMktData(stock, '', False, False)
        await asyncio.sleep(3)
        
        if ticker.last:
            print(f'   ✅ STOCK DATA: Working')
            print(f'      AAPL: ${ticker.last:.2f}')
        else:
            print(f'   ⚠️  STOCK DATA: No data received')
    except Exception as e:
        print(f'   ❌ Error: {e}')
    
    print()
    
    # Test 2: Options data
    print('2️⃣  Testing Options Data ($10-15/month):')
    try:
        # Try to get an AAPL option
        option = Option('AAPL', '20251219', 150, 'C', 'SMART')
        
        # Qualify the contract first
        contracts = await ib.qualifyContractsAsync(option)
        
        if contracts:
            qualified_option = contracts[0]
            ticker = ib.reqMktData(qualified_option, '', False, False)
            await asyncio.sleep(3)
            
            if ticker.last or ticker.bid or ticker.ask:
                print(f'   ✅ OPTIONS DATA: ACCESSIBLE!')
                print(f'      AAPL Dec 150 Call:')
                print(f'         Last: ${ticker.last if ticker.last else "N/A"}')
                print(f'         Bid: ${ticker.bid if ticker.bid else "N/A"}')
                print(f'         Ask: ${ticker.ask if ticker.ask else "N/A"}')
            else:
                print(f'   ❌ OPTIONS DATA: Not accessible')
                print(f'      Need to subscribe: US Options (OPRA)')
                print(f'      Cost: ~$10-15/month')
        else:
            print(f'   ⚠️  Could not qualify option contract')
            
    except Exception as e:
        print(f'   ❌ OPTIONS DATA: Error - {e}')
        print(f'      Likely need subscription')
    
    print()
    
    # Test 3: Crypto futures
    print('3️⃣  Testing Crypto Futures Data ($5-10/month):')
    try:
        # Try to get BTC future
        btc = Future('BTC', '20251226', 'CME')
        
        # Qualify the contract
        contracts = await ib.qualifyContractsAsync(btc)
        
        if contracts:
            qualified_btc = contracts[0]
            ticker = ib.reqMktData(qualified_btc, '', False, False)
            await asyncio.sleep(3)
            
            if ticker.last or ticker.bid or ticker.ask:
                print(f'   ✅ CRYPTO FUTURES: ACCESSIBLE!')
                print(f'      BTC Dec Future:')
                print(f'         Last: ${ticker.last if ticker.last else "N/A"}')
                print(f'         Bid: ${ticker.bid if ticker.bid else "N/A"}')
                print(f'         Ask: ${ticker.ask if ticker.ask else "N/A"}')
            else:
                print(f'   ❌ CRYPTO FUTURES: Not accessible')
                print(f'      Need to subscribe: CME Crypto Futures')
                print(f'      Cost: ~$5-10/month')
        else:
            print(f'   ⚠️  Could not qualify BTC future contract')
            
    except Exception as e:
        print(f'   ❌ CRYPTO FUTURES: Error - {e}')
        print(f'      Likely need subscription')
    
    print()
    print('='*70)
    print('SUBSCRIPTION CHECK COMPLETE')
    print('='*70)
    print()
    
    # Summary
    print('📊 SUMMARY:')
    print()
    print('Current Access:')
    print('  ✅ US Stocks/ETFs (Real-time, Free)')
    print()
    print('To Add (Recommended):')
    print('  🔥 US Options Data - $10-15/month')
    print('     → Best pre-breach indicator (put/call ratios)')
    print('  🔥 CME Crypto Futures - $5-10/month')
    print('     → Ransomware payment tracking')
    print()
    print('Total Cost: $15-25/month for professional threat intelligence')
    print()
    
    ib.disconnect()

if __name__ == "__main__":
    asyncio.run(check_subscriptions())
