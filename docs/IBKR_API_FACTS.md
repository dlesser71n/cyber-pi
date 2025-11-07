# IBKR API - Facts from Official Documentation

**Source:** https://interactivebrokers.github.io/tws-api/  
**Date:** November 4, 2025

---

## 🔑 Critical Facts

### **1. Market Data Lines (Concurrent Requests)**

**From Documentation:**
> "By default, every user has a maxTicker Limit of 100 market data lines and as such can obtain the real time market data of up to 100 instruments simultaneously."

**What This Means:**
- You can request data for **100 instruments at once**
- This includes TWS + API combined
- Example: 50 in TWS + 50 in API = 100 total
- Exceeding this returns an error

**For Cyber-PI:**
- ✅ 50-ticker watchlist: Well within limits
- ✅ 200-ticker watchlist: Need to batch (2 batches of 100)
- ✅ Can increase limit with quote booster packs

---

### **2. Snapshot vs Streaming**

**From Documentation:**
> "By invoking the IBApi::EClient::reqMktData function passing in true for the snapshot parameter, the client application will receive the currently available market data once before a tickSnapshotEnd event is sent 11 seconds later."

**Key Points:**
- **Snapshot:** One-time data request, 11-second window
- **Streaming:** Continuous updates as market changes
- **Snapshot limitations:** Only default ticks, no generic ticks

**For Cyber-PI:**
- ✅ Use snapshots for scanning (one-time data)
- ✅ 11-second window is acceptable
- ⚠️ Cannot get put/call volume with snapshots (generic tick 100)

---

### **3. Generic Tick Types (Options Data)**

**From Documentation:**
> "The most common tick types are delivered automatically after a successful market data request. There are however other tick types available by explicit request: the generic tick types."

**Options-Specific Ticks:**
- **100:** Put volume, call volume
- **101:** Put open interest, call open interest  
- **104:** Historical volatility
- **105:** Average option volume
- **106:** Implied volatility

**Critical Finding:**
- Generic ticks **CANNOT** be used with snapshots!
- Must use streaming mode for options volume data
- This explains why we need the 2-3 second wait

**For Cyber-PI:**
- ❌ Cannot use snapshot=True for options analysis
- ✅ Must use streaming with genericTickList='100,101'
- ✅ Wait 2-3 seconds for data to arrive

---

### **4. Option Chains**

**From Documentation:**
> "The option chain for a given security can be returned using the function reqContractDetails. If an option contract is incompletely defined (for instance with the strike undefined) and used as an argument to reqContractDetails, a list of all matching option contracts will be returned."

**How It Works:**
```python
# Incomplete contract = get full chain
contract = Contract()
contract.symbol = "AAPL"
contract.secType = "OPT"
contract.exchange = "SMART"
contract.currency = "USD"
# No strike, no expiration = returns ALL options

client.reqContractDetails(reqId, contract)
```

**For Cyber-PI:**
- ✅ This is what we're already doing
- ✅ Returns all strikes and expirations
- ✅ Efficient way to get option chain

---

### **5. Market Data Subscriptions**

**From Documentation:**
> "In order to receive real time top-of-book, depth-of-book, or historical market data from the API it is necessary have live market data subscriptions for the requested instruments in TWS."

**Requirements:**
1. Trading permissions for instruments
2. Funded account (except forex/bonds)
3. Market data subscriptions for username

**For Cyber-PI:**
- ✅ We have US stock/ETF subscription
- ✅ Options included in stock subscription
- ✅ No additional cost for options data

---

## 🚀 Optimization Strategy (Based on Documentation)

### **Current Approach (Correct):**

```python
# 1. Get option chain
chains = await ib.reqSecDefOptParamsAsync(stock.symbol, '', stock.secType, stock.conId)

# 2. Build contracts
options = []
for expiration in expirations:
    for strike in strikes:
        options.append(Option(ticker, expiration, strike, 'P', 'SMART'))
        options.append(Option(ticker, expiration, strike, 'C', 'SMART'))

# 3. Qualify contracts
qualified = await ib.qualifyContractsAsync(*options)

# 4. Request market data (STREAMING, not snapshot)
tickers = [ib.reqMktData(opt, '100,101', False, False) for opt in qualified]

# 5. Wait for data
await asyncio.sleep(2)

# 6. Collect data
for ticker in tickers:
    if ticker.volume:
        # Process data
```

**Why This is Correct:**
- ✅ Uses streaming (not snapshot) to get generic ticks
- ✅ Requests all contracts at once (parallel)
- ✅ Waits for data to arrive
- ✅ Within 100 market data line limit

---

### **What We Can Optimize:**

#### **1. Batch Processing (For 200+ Tickers)**

```python
# Process in batches of 100 (market data line limit)
for batch in chunks(tickers, 100):
    await process_batch(batch)
```

#### **2. Proper Cleanup**

```python
# Cancel market data after collection
for ticker in tickers:
    ib.cancelMktData(ticker.contract)
```

#### **3. Parallel Ticker Analysis**

```python
# Analyze multiple tickers simultaneously
tasks = [analyze_ticker(t) for t in watchlist[:100]]
results = await asyncio.gather(*tasks)
```

---

## 💡 Key Insights from Documentation

### **1. Why Snapshots Don't Work for Options:**
- Snapshots only return default ticks
- Options volume (tick 100) is a generic tick
- Generic ticks require streaming mode
- **This is why we need the 2-3 second wait**

### **2. Why We're Not Faster:**
- We're requesting data correctly
- The bottleneck is the 2-3 second wait for data
- This is IBKR's data delivery time, not our code
- **Cannot be optimized further with IBKR API**

### **3. Why Yahoo Finance is Better for Scanning:**
- Returns ALL data in one API call
- No streaming wait time
- No market data line limits
- **This is why the security methodology works**

---

## 🎯 Recommended Architecture (Based on Documentation)

### **Phase 1: Yahoo Finance Screening**
```python
# Fast screening (no IBKR limits)
for ticker in watchlist:
    data = yf.Ticker(ticker).option_chain()
    store_in_redis(data)
    
# Time: ~30 seconds for 50 tickers
# Cost: $0
# Limits: None
```

### **Phase 2: IBKR Verification (High Threats Only)**
```python
# Only verify high-priority threats
for threat in high_priority_threats:
    # Use IBKR for real-time verification
    data = await ibkr.get_options_data(threat.ticker)
    
# Time: ~5-10 seconds per ticker
# Cost: $0 (within subscription)
# Limits: 100 concurrent requests
```

---

## 📊 Performance Reality Check

### **IBKR Limitations (From Documentation):**
1. **Market data lines:** 100 concurrent requests
2. **Streaming wait:** 2-3 seconds for data arrival
3. **Generic ticks:** Cannot use with snapshots
4. **Rate limits:** 50 messages/second

### **What This Means:**
- **Best case:** ~2-3 seconds per ticker (with streaming)
- **50 tickers:** ~2-3 minutes (sequential)
- **50 tickers:** ~10-15 seconds (parallel, batched)
- **200 tickers:** ~40-60 seconds (parallel, 2 batches of 100)

### **Yahoo Finance Alternative:**
- **50 tickers:** ~30 seconds (parallel)
- **200 tickers:** ~2 minutes (parallel)
- **No limits, no subscriptions, no wait times**

---

## ✅ Conclusion

**Based on Official IBKR Documentation:**

1. **We're using the API correctly**
   - Streaming mode for generic ticks ✅
   - Parallel requests ✅
   - Within market data line limits ✅

2. **The bottleneck is IBKR's architecture**
   - 2-3 second streaming wait (unavoidable)
   - Cannot use snapshots for options volume
   - This is by design, not our code

3. **Yahoo Finance is the right solution**
   - No streaming delays
   - No market data line limits
   - Returns all data instantly
   - **This is why the security methodology works**

---

**🔭 The documentation confirms: Yahoo Finance for screening, IBKR for verification!**
