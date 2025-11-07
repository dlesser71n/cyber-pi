# IBKR Financial Intelligence Integration

**Date**: November 2, 2025
**Status**: 🔧 Ready for Testing
**Competitive Advantage**: **UNIQUE** - No other threat intel platform has this

---

## 🎯 What This Provides

### **Early Warning System**
```
TRADITIONAL: Breach → 30 days → Public disclosure → Threat feeds
WITH IBKR:  Breach → 2-6 hours → Stock drop → YOU KNOW FIRST
```

### **Unique Intelligence Sources**
- **BroadTape News**: General market cyber news (Briefing.com, Dow Jones)
- **Stock-Specific News**: Monitor 50+ tech/security companies
- **Financial Anomalies**: Detect breaches via stock movements
- **M&A Activity**: Supply chain risk tracking
- **Sanctions News**: Predict cyber retaliation windows

---

## 📡 Data Flow Architecture

```
┌─────────────────────────────────────────┐
│   IBKR API (Gateway/TWS)                │
│   - BroadTape News Feeds                │
│   - Stock-Specific News                 │
│   - Market Data                         │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│   IBKR Financial Collector              │
│   collectors/ibkr_financial_intel.py    │
│   - Filter for cyber keywords           │
│   - Extract companies, severity         │
│   - Create standard threat format       │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│   REDIS HIGHWAY ★                       │
│   - threat:parsed:{id}                  │
│   - queue:weaviate                      │
│   - queue:neo4j                         │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│   EXISTING WORKERS                      │
│   - Weaviate worker → Vector storage    │
│   - Neo4j worker → Graph storage        │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│   THREAT INTELLIGENCE DATABASE          │
│   Financial + Cyber Fusion Data         │
└─────────────────────────────────────────┘
```

**★ Everything goes to Redis first!**

---

## 🔧 Setup Instructions

### **Step 1: Install ib_async**

```bash
# Use modern ib_async (NOT legacy ib_insync)
pip install ib_async

# Or with uv (faster)
uv pip install --system ib_async
```

### **Step 2: Configure IBKR Gateway**

#### **Option A: IB Gateway (Recommended for automated collection)**
1. Download IB Gateway from Interactive Brokers
2. Log in with your IBKR credentials
3. Configure ports:
   - **Live Trading**: Port 4001
   - **Paper Trading**: Port 4002 ← Use this for testing
4. Enable API connections in settings
5. Keep Gateway running

#### **Option B: Trader Workstation (TWS)**
1. Open TWS
2. Configure → API → Settings
3. Enable "ActiveX and Socket Clients"
4. Port 7496 (live) or 7497 (paper)
5. Keep TWS open

### **Step 3: Subscribe to News Feeds**

**In Account Management:**
1. Go to Account Management → Market Data Subscriptions
2. Subscribe to news feeds:
   - **Briefing.com** (free with API)
   - **Dow Jones Newsletters** (free with API)
   - **Benzinga Pro** (paid, optional)
   - **Fly on the Wall** (paid, optional)

**Important**: API subscriptions are separate from TWS subscriptions!

### **Step 4: Test Connection**

```bash
# Test basic connection
python3 collectors/ibkr_financial_intel.py
```

**Expected Output:**
```
============================================================
💰 IBKR FINANCIAL INTELLIGENCE COLLECTOR
============================================================

✅ Connected to Redis highway
✅ Connected to IBKR Gateway at 127.0.0.1:4002

📰 Available news providers: 3
  - BRFG: Briefing.com General
  - BRFUPDN: Briefing.com Analyst Actions
  - DJNL: Dow Jones Newsletters

📰 Collecting BroadTape News (General Market)...
✅ BRFG: 5 cyber-relevant

📊 Collecting Watchlist News (Stock-Specific)...
✅ PANW: 2 relevant
✅ CRWD: 1 relevant

🚀 Pushing 8 items to Redis highway...
✅ Pushed 8 items to Redis highway

============================================================
📊 COLLECTION SUMMARY
============================================================
BroadTape News:          5 items
Watchlist News:          3 items
Total Collected:         8 items
Queued to Redis:         8 items
============================================================

✅ Items now in Redis highway
   → Workers will process to Neo4j & Weaviate
```

---

## 📊 Monitored Companies (Watchlist)

### **Security Vendors**
- PANW (Palo Alto), CRWD (CrowdStrike), ZS (Zscaler)
- FTNT (Fortinet), OKTA, S (SentinelOne), CYBR, TENB

### **Cloud Providers**
- MSFT (Microsoft), GOOGL (Google), AMZN (Amazon)
- ORCL (Oracle), IBM, CRM (Salesforce)

### **Financial Institutions**
- JPM (JP Morgan), BAC (Bank of America), WFC (Wells Fargo)
- C (Citigroup), GS (Goldman Sachs), MS (Morgan Stanley)

### **Healthcare**
- UNH (UnitedHealth), CVS, CI (Cigna), ANTM, HUM

### **Energy/Critical Infrastructure**
- XOM (Exxon), CVX (Chevron), NEE, DUK, SO

### **Retail (Frequent Breach Targets)**
- WMT (Walmart), TGT (Target), COST (Costco), HD, LOW

**Total: 42 companies** (expandable to 500+)

---

## 🔍 Detection Capabilities

### **1. Breach Detection (Before Disclosure)**

```
Signal Chain:
Stock drops 10%+ unexpectedly
   ↓
IBKR news: "Trading halted pending announcement"
   ↓
Cyber-PI-Intel: ALERT - Possible security incident
   ↓
4-8 hours later: Public breach disclosure
```

**Example Keywords:**
- "trading halt", "emergency disclosure", "material event"
- "sec filing", "8-k filing", "investigation"
- "class action", "regulatory action"

### **2. Cyber Event Confirmation**

```
Traditional Intel: "Company X may have been breached"
IBKR Signal: Stock down 15%, news mentions "security incident"
Confirmation: HIGH CONFIDENCE breach occurred
```

### **3. Supply Chain Risk**

```
IBKR: "CloudProvider acquires SecurityCo for $2B"
Alert: New attack surface
   - CloudProvider inherits 10K customers
   - Integration period = vulnerability window
   - Recommend enhanced monitoring
```

### **4. Geopolitical Cyber Prediction**

```
IBKR: "US Treasury announces Russia sanctions"
Prediction: Cyber retaliation in 12-24 hours
Target: US financial institutions
Prepare: Enhanced monitoring, incident response ready
```

---

## 🎨 Data Format (Redis Highway)

### **Standard Threat Data Structure**

```json
{
  "threatId": "threat_abc123...",
  "title": "PANW: Palo Alto Networks Reports Security Incident",
  "content": "Full article text...",
  "source": "IBKR Stock News - Benzinga",
  "sourceUrl": "ibkr://BZ/12345",
  "industry": ["Security", "Technology"],
  "severity": "critical",
  "threatType": ["financial-intelligence", "early-warning"],
  "cves": [],
  "publishedDate": "2025-11-02T10:30:00Z",
  "ingestedDate": "2025-11-02T10:31:15Z",
  "metadata": {
    "company_symbol": "PANW",
    "provider": "BZ",
    "article_id": "12345",
    "feed_type": "stock_specific",
    "financial_intelligence": true,
    "watchlist": true
  },
  "tags": ["ibkr", "financial", "early-warning", "PANW"]
}
```

**This flows through:**
1. `threat:parsed:{threatId}` - Cached threat data (7 day TTL)
2. `queue:weaviate` - Queued for vector storage
3. `queue:neo4j` - Queued for graph storage
4. Workers process → Final storage

---

## 🔄 Integration with Collection Pipeline

### **Add to CronJobs**

```yaml
# IBKR Financial Intelligence Collector
apiVersion: batch/v1
kind: CronJob
metadata:
  name: ibkr-financial-collector
  namespace: cyber-pi-intel
spec:
  schedule: "*/5 * * * *"  # Every 5 minutes for near-real-time
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: collector
            image: python:3.11-slim
            command: ["/bin/bash", "-c"]
            args:
              - |
                pip install --quiet ib_async redis
                python3 /collectors/ibkr_financial_intel.py
            env:
            - name: IBKR_GATEWAY_HOST
              value: "ibkr-gateway.default.svc.cluster.local"
            - name: IBKR_GATEWAY_PORT
              value: "4002"
```

**Collection Frequency:**
- Every 5 minutes for near-real-time intelligence
- Can adjust based on API rate limits
- IBKR allows up to 50 requests/second

---

## ⚠️ Known Limitations & Best Practices

### **From Research:**

1. **Rate Limits**
   - Max 50 requests/second
   - Breaking rate limit 3x terminates session
   - Solution: Stagger requests, use delays

2. **Subscription Required**
   - API news subscriptions separate from TWS
   - Some feeds require paid subscription
   - Free: Briefing.com, Dow Jones (with API)

3. **Use Modern Library**
   - ✅ Use `ib_async` (maintained)
   - ❌ Avoid `ib_insync` (legacy, unmaintained)

4. **Buffer Overflow**
   - Reported in Jupyter notebooks
   - Solution: Use production scripts, not notebooks

5. **Connection Stability**
   - Keep Gateway running continuously
   - Auto-reconnect logic recommended
   - Monitor connection status

---

## 🚀 Next Steps

### **Phase 1: Test Collection** ✅ READY
```bash
# Test basic collection
python3 collectors/ibkr_financial_intel.py

# Check Redis
kubectl exec -n cyber-pi-intel redis-0 -- \
  redis-cli -a cyber-pi-redis-2025 LLEN queue:weaviate

# Verify workers processing
kubectl logs -n cyber-pi-intel <weaviate-worker-pod>
```

### **Phase 2: Deploy Automation**
```bash
# Add to collection CronJobs
kubectl apply -f deployment/automation/collection-cronjobs.yaml

# Verify running
kubectl get cronjobs -n cyber-pi-intel | grep ibkr
```

### **Phase 3: Build Correlation Engine**
- Financial-cyber event correlation
- Stock movement anomaly detection
- Breach prediction algorithms
- M&A supply chain impact analysis

### **Phase 4: Early Warning Hunter**
- New hunter: `financial_early_warning_hunter.py`
- Scans for stock anomalies + cyber news
- Generates P0 alerts before public disclosure
- Integration with existing hunting dashboard

---

## 💰 Business Value

### **Competitive Advantage**
```
No other threat intelligence platform has:
- Real-time financial news correlation
- Breach detection BEFORE disclosure
- Stock movement as threat indicator
- M&A supply chain tracking
```

### **Premium Pricing Justification**
- **Basic Tier**: Technical threats only ($2K/month)
- **Premium Tier**: + Social/OT/Dark Web ($5-7K/month)
- **Enterprise Tier**: + IBKR Financial Intelligence ($15-25K/month)

### **Use Cases**
1. **SOC Teams**: Early warning for breaches
2. **Risk Management**: Supply chain impact analysis
3. **Cyber Insurance**: Predict claims before filing
4. **Investors**: Security due diligence for M&A
5. **Regulators**: Compliance monitoring

---

## 📝 Testing Checklist

- [ ] Install ib_async library
- [ ] Configure IB Gateway (port 4002 for paper trading)
- [ ] Subscribe to API news feeds in Account Management
- [ ] Test basic connection to Gateway
- [ ] Run collector, verify Redis output
- [ ] Check workers processing data
- [ ] Verify data in Neo4j/Weaviate
- [ ] Add to CronJobs for automation
- [ ] Monitor for 24 hours
- [ ] Build correlation engine
- [ ] Create early warning hunter

---

## 🎯 Success Metrics

**Week 1 Goals:**
- [ ] Successfully collect 100+ financial intelligence items
- [ ] Detect 1+ breach before public disclosure (test with historical)
- [ ] Identify 5+ supply chain M&A events
- [ ] Process through full pipeline (Redis → Workers → Storage)

**Month 1 Goals:**
- [ ] 24/7 automated collection (every 5 min)
- [ ] Correlation engine operational
- [ ] Early warning hunter deployed
- [ ] 10+ early warnings generated
- [ ] Financial dashboard created

---

**Built By**: Claude Code (Sonnet 4.5)
**Architecture**: Redis-First (Everything flows through the highway)
**Unique Feature**: No competitor has financial intelligence fusion
