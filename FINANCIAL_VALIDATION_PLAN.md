# Financial Intelligence Validation Plan

**Date:** November 4, 2025  
**Approach:** Option A - Pause and Validate  
**Duration:** 30 days  
**Cost:** $0 (Yahoo Finance free tier)

---

## 🎯 Objective

**Prove or disprove:** Financial indicators can predict cyber breaches 14-30 days in advance.

**Success Criteria:**
- Detect 2+ breach indicators before public announcement
- Correlation >70% with known breaches
- Actionable signals (not just noise)

**Failure Criteria:**
- No correlation with breaches
- Too many false positives
- Signals are not actionable

---

## 📊 What We'll Monitor

### **Ticker Selection (10-15 stocks):**

**Nexum Clients (if known):**
- Healthcare: UNH, CVS, HCA
- Financial: JPM, BAC
- Airlines: DAL, UAL

**High-Profile Targets:**
- Technology: MSFT, AAPL, GOOGL
- Cybersecurity: PANW, CRWD
- Defense: LMT

**Why These:**
- Mix of Nexum clients + high-profile targets
- Diverse industries
- Frequent breach targets
- Publicly traded (data available)

---

## 🔧 Implementation (Minimal)

### **Week 1: Setup (This Week)**

**Build Simple Collector:**
```python
# src/validation/financial_data_collector.py
# Runs every 4 hours (Yahoo Finance updates)
# Collects: put/call ratio, volume, unusual activity
# Stores in Redis with timestamp
```

**What to Collect:**
- Put/call ratio
- Volume vs 30-day average
- Unusual OTM puts
- Near-term concentration

**Storage:**
```
Redis key: validation:financial:{ticker}:{date}
Data: {
    'put_call_ratio': float,
    'volume_spike': float,
    'unusual_puts': int,
    'threat_score': int
}
TTL: 90 days
```

---

### **Weeks 2-5: Data Collection (30 Days)**

**Automated Collection:**
- Run every 4 hours (6x per day)
- 10 tickers × 6 collections × 30 days = 1,800 data points
- Store in Redis
- No analysis yet (just collect)

**Parallel: Track Breaches:**
- Monitor breach announcements (manual)
- Record: company, date announced, estimated breach date
- Store in Redis: `validation:breaches:{company}:{date}`

**Sources for Breach Data:**
- CISA alerts
- Company press releases
- Security news (Bleeping Computer, Krebs, etc.)
- Existing Cyber-PI collectors

---

### **Week 6: Analysis**

**Correlation Analysis:**
```python
# For each breach:
# 1. Look back 14-30 days in financial data
# 2. Check if threat score was elevated
# 3. Calculate correlation
# 4. Identify patterns
```

**Questions to Answer:**
1. Did financial indicators spike before breach announcement?
2. How many days in advance?
3. What was the threat score?
4. Were there false positives?
5. Is this actionable?

---

## 📈 Success Metrics

### **What We're Looking For:**

**Positive Signals:**
- ✅ Threat score >70 before 2+ breaches
- ✅ 14-30 day advance warning
- ✅ Low false positive rate (<20%)
- ✅ Clear patterns (repeatable)

**Negative Signals:**
- ❌ No correlation with breaches
- ❌ High false positive rate (>50%)
- ❌ Signals too late (after announcement)
- ❌ Random/noisy data

---

## 💰 Cost Analysis

### **30-Day Validation:**

**Infrastructure:**
- Yahoo Finance: $0 (free)
- Redis: $0 (existing)
- Compute: $0 (existing)

**Time:**
- Setup: 2-4 hours (Week 1)
- Monitoring: 30 minutes/week (automated)
- Analysis: 4-6 hours (Week 6)
- **Total: ~10 hours over 30 days**

**Total Cost: $0 + 10 hours**

---

## 🎯 Decision Framework (Week 6)

### **Scenario A: Strong Correlation (>70%)**
**Action:** Continue development
- Subscribe to Tradier ($10/month)
- Expand to 50 tickers
- Integrate with Periscope L1
- Build correlation engine

### **Scenario B: Moderate Correlation (40-70%)**
**Action:** Extended validation
- Continue free monitoring for 60 more days
- Refine threat signatures
- Test with more tickers
- Re-evaluate at 90 days

### **Scenario C: Weak/No Correlation (<40%)**
**Action:** Shelve the project
- Document findings
- Archive code
- Focus on proven threat vectors
- Revisit if new evidence emerges

---

## 📝 Deliverables

### **Week 1:**
- ✅ Simple Yahoo Finance collector
- ✅ Redis storage schema
- ✅ Automated collection (cron)

### **Week 6:**
- ✅ 30 days of financial data
- ✅ Breach timeline (if any occurred)
- ✅ Correlation analysis report
- ✅ Go/No-Go recommendation

---

## 🔧 Technical Implementation

### **Minimal Collector (Week 1):**

```python
#!/usr/bin/env python3
"""
Financial Validation Collector
Minimal implementation for 30-day validation
"""

import yfinance as yf
import redis
import json
from datetime import datetime

# Tickers to monitor
WATCHLIST = [
    'UNH', 'CVS', 'HCA',      # Healthcare
    'JPM', 'BAC',              # Financial
    'DAL', 'UAL',              # Airlines
    'MSFT', 'AAPL', 'GOOGL',  # Tech
    'PANW', 'CRWD',            # Cybersecurity
    'LMT'                      # Defense
]

def collect_ticker(ticker):
    """Collect options data for a ticker"""
    try:
        stock = yf.Ticker(ticker)
        
        # Get first expiration
        if not stock.options:
            return None
        
        chain = stock.option_chain(stock.options[0])
        
        # Calculate metrics
        put_volume = chain.puts['volume'].sum()
        call_volume = chain.calls['volume'].sum()
        put_call_ratio = put_volume / call_volume if call_volume > 0 else 0
        
        # Simple threat score
        threat_score = 0
        if put_call_ratio > 2.0:
            threat_score += 40
        if put_volume > 10000:
            threat_score += 30
        
        return {
            'ticker': ticker,
            'timestamp': datetime.now().isoformat(),
            'put_call_ratio': put_call_ratio,
            'put_volume': int(put_volume),
            'call_volume': int(call_volume),
            'threat_score': threat_score
        }
    except Exception as e:
        print(f"Error collecting {ticker}: {e}")
        return None

def main():
    """Collect data for all tickers"""
    r = redis.Redis(host='localhost', port=32379, decode_responses=True)
    
    for ticker in WATCHLIST:
        data = collect_ticker(ticker)
        if data:
            # Store in Redis
            key = f"validation:financial:{ticker}:{datetime.now().strftime('%Y%m%d_%H%M')}"
            r.setex(key, 7776000, json.dumps(data))  # 90 day TTL
            print(f"✅ Collected {ticker}: score={data['threat_score']}")

if __name__ == "__main__":
    main()
```

### **Cron Schedule:**
```bash
# Run every 4 hours
0 */4 * * * cd /home/david/projects/cyber-pi && python3 src/validation/financial_data_collector.py
```

---

## 📊 Expected Outcomes

### **Best Case:**
- Clear correlation with 2-3 breaches
- 14-30 day advance warning
- Actionable signals
- **Decision: Continue with paid data**

### **Worst Case:**
- No correlation
- Random noise
- Not actionable
- **Decision: Shelve and focus elsewhere**

### **Most Likely:**
- Some correlation (50-60%)
- Mixed signals
- Needs refinement
- **Decision: Extended validation**

---

## 🎯 Key Principles

### **1. Minimal Investment**
- Use free data only
- Automated collection
- 10 hours total time

### **2. Clear Success Criteria**
- Objective metrics
- Go/No-Go decision
- No sunk cost fallacy

### **3. Time-Boxed**
- 30 days maximum
- Week 6 decision point
- Move on if not working

### **4. Focus on Core**
- Don't neglect Cyber-PI core features
- This is a side experiment
- Core platform is priority

---

## 💡 What We Learn Either Way

### **If It Works:**
- Proven early warning capability
- Unique competitive advantage
- Justifies investment in paid data

### **If It Doesn't Work:**
- Saved money (didn't buy Tradier/Polygon)
- Learned about financial signals
- Can focus on proven vectors
- Still have the architecture (Redis-first) for other uses

---

## 🔭 Next Steps (This Week)

1. ✅ Create validation collector script
2. ✅ Set up Redis storage
3. ✅ Configure cron job (every 4 hours)
4. ✅ Start 30-day data collection
5. ✅ Monitor breach announcements (manual)

**Then:** Wait 30 days, analyze, decide.

---

**🎯 Validation approach: Prove value before investing more!**
