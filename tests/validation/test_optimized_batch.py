#!/usr/bin/env python3
"""
Test REAL batch optimization
The key: Use asyncio.gather to request ALL contracts in parallel
"""

import asyncio
import time
from ib_async import IB, Stock, Option

async def test_batch_optimization():
    """Test batch vs sequential"""
    
    ib = IB()
    await ib.connectAsync('127.0.0.1', 4002, clientId=1)
    
    print("="*70)
    print("🧪 TESTING BATCH OPTIMIZATION")
    print("="*70)
    print()
    
    # Get UNH options chain
    stock = Stock('UNH', 'SMART', 'USD')
    stock = await ib.qualifyContractsAsync(stock)
    stock = stock[0]
    
    chains = await ib.reqSecDefOptParamsAsync(
        stock.symbol, '', stock.secType, stock.conId
    )
    chain = chains[0]
    
    # Get first 20 contracts (10 puts + 10 calls)
    expiration = chain.expirations[0]
    strikes = sorted(chain.strikes)[:10]
    
    contracts = []
    for strike in strikes:
        contracts.append(Option('UNH', expiration, strike, 'P', 'SMART'))
        contracts.append(Option('UNH', expiration, strike, 'C', 'SMART'))
    
    print(f"Testing with {len(contracts)} contracts")
    print()
    
    # Qualify all contracts
    qualified = await ib.qualifyContractsAsync(*contracts)
    print(f"✅ Qualified {len(qualified)} contracts")
    print()
    
    # TEST 1: Sequential (OLD WAY)
    print("TEST 1: Sequential requests (current method)")
    print("-" * 70)
    
    start = time.time()
    
    tickers_seq = []
    for contract in qualified:
        ticker = ib.reqMktData(contract, '', snapshot=True, regulatorySnapshot=False)
        tickers_seq.append(ticker)
    
    await asyncio.sleep(2)
    
    # Count results
    results_seq = sum(1 for t in tickers_seq if hasattr(t, 'volume') and t.volume)
    
    # Cancel
    for ticker in tickers_seq:
        ib.cancelMktData(ticker.contract)
    
    time_seq = time.time() - start
    
    print(f"Time: {time_seq:.2f}s")
    print(f"Results: {results_seq}/{len(qualified)} contracts")
    print()
    
    # Wait a bit
    await asyncio.sleep(1)
    
    # TEST 2: Parallel with asyncio.gather (NEW WAY)
    print("TEST 2: Parallel with asyncio.gather (optimized)")
    print("-" * 70)
    
    start = time.time()
    
    # Request all at once using async functions
    async def get_ticker_data(contract):
        ticker = ib.reqMktData(contract, '', snapshot=True, regulatorySnapshot=False)
        await asyncio.sleep(2)  # Wait for data
        return ticker
    
    # Execute all in parallel
    tickers_par = await asyncio.gather(*[get_ticker_data(c) for c in qualified])
    
    # Count results
    results_par = sum(1 for t in tickers_par if hasattr(t, 'volume') and t.volume)
    
    # Cancel
    for ticker in tickers_par:
        ib.cancelMktData(ticker.contract)
    
    time_par = time.time() - start
    
    print(f"Time: {time_par:.2f}s")
    print(f"Results: {results_par}/{len(qualified)} contracts")
    print()
    
    # Summary
    print("="*70)
    print("📊 RESULTS")
    print("="*70)
    print(f"Sequential:  {time_seq:.2f}s ({results_seq} results)")
    print(f"Parallel:    {time_par:.2f}s ({results_par} results)")
    print(f"Speedup:     {time_seq/time_par:.1f}x faster")
    print()
    
    if time_par < time_seq:
        print(f"✅ Parallel is {time_seq/time_par:.1f}x faster!")
    else:
        print("⚠️  No speedup - IBKR may be rate limiting")
    
    ib.disconnect()


if __name__ == "__main__":
    asyncio.run(test_batch_optimization())
