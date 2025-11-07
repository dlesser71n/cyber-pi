# IBKR After-Hours Trading Reference

**Date:** November 4, 2025

---

## 🕐 Trading Hours

### **Regular Market Hours:**
- **Pre-market:** 4:00 AM - 9:30 AM ET
- **Regular:** 9:30 AM - 4:00 PM ET
- **After-hours:** 4:00 PM - 8:00 PM ET

### **Options Trading Hours:**
- **Regular:** 9:30 AM - 4:00 PM ET
- **After-hours:** Limited (some exchanges)
- **Note:** Most options only trade during regular hours

---

## 🔧 IBKR API Inputs for After-Hours

### **1. reqMktData() Parameters:**

```python
from ib_async import IB, Stock, TagValue

ib = IB()
await ib.connectAsync('127.0.0.1', 4002, clientId=1)

# Create contract
stock = Stock('AAPL', 'SMART', 'USD')

# Request market data with after-hours
ticker = ib.reqMktData(
    contract=stock,
    genericTickList='',  # Empty for basic data
    snapshot=False,      # False = streaming, True = snapshot
    regulatorySnapshot=False,
    mktDataOptions=[
        TagValue('RTH', '0')  # RTH=0 means include after-hours
    ]
)
```

### **Key Parameter: mktDataOptions**

```python
# Regular trading hours ONLY
mktDataOptions=[TagValue('RTH', '1')]

# Include after-hours (pre-market + after-hours)
mktDataOptions=[TagValue('RTH', '0')]
```

---

## 📊 Generic Tick List (Options-Specific)

### **For Options Analysis:**

```python
# Get put/call volume and open interest
genericTickList='100,101'

# Detailed options data
genericTickList='100,101,104,105,106'
```

### **Tick IDs:**
- **100:** Put volume, call volume
- **101:** Put open interest, call open interest
- **104:** Historical volatility
- **105:** Average option volume
- **106:** Implied volatility

---

## 🚀 Usage in Financial Threat Collector

### **Current Implementation:**

```python
# In options_threat_analyzer.py
ticker = self.ib.reqMktData(
    opt,
    '',
    snapshot=True,  # Snapshot mode
    regulatorySnapshot=False
)
```

### **Enhanced for After-Hours:**

```python
# Include after-hours data
ticker = self.ib.reqMktData(
    opt,
    '100,101',  # Put/call volume and OI
    snapshot=True,
    regulatorySnapshot=False,
    mktDataOptions=[
        TagValue('RTH', '0')  # Include after-hours
    ]
)
```

---

## ⏰ When to Use After-Hours

### **Use Cases:**

1. **Breaking News Response**
   - Earnings announcements (after 4 PM)
   - Security breaches announced after hours
   - Emergency trading activity

2. **Pre-Market Intelligence**
   - Overnight developments
   - Asian/European market reactions
   - Early warning signals

3. **Continuous Monitoring**
   - 24/7 threat detection
   - No gaps in coverage
   - Real-time response

### **Limitations:**

1. **Options Trading**
   - Most options only trade 9:30 AM - 4:00 PM ET
   - Limited after-hours options activity
   - Volume is much lower

2. **Data Quality**
   - Wider spreads after hours
   - Lower liquidity
   - Higher volatility

---

## 🎯 Recommendation for Cyber-PI

### **Strategy:**

**For Stock Monitoring:**
```python
# Include after-hours for continuous monitoring
mktDataOptions=[TagValue('RTH', '0')]
```

**For Options Analysis:**
```python
# Regular hours only (most activity)
# Run during 9:30 AM - 4:00 PM ET
# OR use Yahoo Finance (15-min delayed, 24/7 available)
```

### **Collection Schedule:**

**Optimal:**
- **Every 30 minutes during market hours** (9:30 AM - 4:00 PM ET)
- **Every 2 hours after hours** (4:00 PM - 9:30 AM ET)
- **Use Yahoo Finance for off-hours screening**

**Why:**
- Options volume is highest during regular hours
- After-hours options data is sparse
- Yahoo Finance provides 24/7 data (delayed)

---

## 💡 Best Practice

### **Hybrid Approach:**

```python
import datetime

def should_use_ibkr():
    """Determine if we should use IBKR or Yahoo Finance"""
    now = datetime.datetime.now()
    hour = now.hour
    
    # Market hours (9:30 AM - 4:00 PM ET)
    if 9 <= hour < 16:
        return True  # Use IBKR (real-time)
    else:
        return False  # Use Yahoo Finance (delayed but available)

# In collector
if should_use_ibkr():
    # Use IBKR with RTH=0 (include after-hours)
    data = await ibkr_collector.collect()
else:
    # Use Yahoo Finance (always available)
    data = await yahoo_collector.collect()
```

---

## 🔧 Implementation Example

### **Enhanced Options Analyzer:**

```python
class EnhancedOptionsAnalyzer:
    """Options analyzer with after-hours support"""
    
    async def get_market_data(self, contract, include_after_hours=True):
        """
        Get market data with optional after-hours
        
        Args:
            contract: Option contract
            include_after_hours: Include pre/post market data
        """
        # Build options
        mkt_options = []
        if include_after_hours:
            mkt_options.append(TagValue('RTH', '0'))
        else:
            mkt_options.append(TagValue('RTH', '1'))
        
        # Request data
        ticker = self.ib.reqMktData(
            contract,
            '100,101',  # Put/call volume and OI
            snapshot=True,
            regulatorySnapshot=False,
            mktDataOptions=mkt_options
        )
        
        return ticker
```

---

## 📊 Data Availability

### **What's Available After Hours:**

**Stock Data:**
- ✅ Price (bid/ask/last)
- ✅ Volume
- ✅ Time & sales

**Options Data:**
- ⚠️ Limited (most exchanges closed)
- ⚠️ Sparse volume
- ⚠️ Wide spreads

**Recommendation:**
- Use IBKR for stocks (24/7 with RTH=0)
- Use Yahoo Finance for options (always available, 15-min delayed)

---

## 🎯 Summary

### **Key Inputs:**

1. **mktDataOptions=[TagValue('RTH', '0')]** - Include after-hours
2. **mktDataOptions=[TagValue('RTH', '1')]** - Regular hours only
3. **genericTickList='100,101'** - Put/call volume and OI

### **Best Practice:**

- **Stocks:** Use IBKR with RTH=0 (24/7 monitoring)
- **Options:** Use Yahoo Finance (always available) + IBKR verification during market hours
- **Hybrid:** Switch based on time of day

### **For Cyber-PI:**

**Current:** IBKR only, market hours only  
**Recommended:** Yahoo Finance (screening) + IBKR (verification)  
**Result:** 24/7 coverage, 40x faster, $0 cost

---

**🔭 After-hours capability enables continuous threat monitoring!**
