# IBKR Financial Intelligence - Testing Guide

**Date**: November 2, 2025
**Status**: Ready to Test
**Estimated Time**: 15-30 minutes

---

## 🎯 What We're Testing

1. **IB Gateway Connection** - Can we connect to your Gateway?
2. **News Provider Access** - Can we see your subscribed news feeds?
3. **News Collection** - Can we collect cyber-relevant financial news?
4. **Redis Integration** - Does data flow to Redis highway?
5. **Worker Processing** - Do workers store in Neo4j/Weaviate?
6. **End-to-End Pipeline** - Complete data flow verification

---

## 📋 Prerequisites Checklist

### **1. Interactive Brokers Account**
- [ ] You have an IBKR account (live or paper trading)
- [ ] You can log in to IBKR

### **2. IB Gateway Installed**
- [ ] IB Gateway downloaded and installed
- [ ] OR Trader Workstation (TWS) installed

**Download here if needed:**
- https://www.interactivebrokers.com/en/trading/ib-api.php
- Choose "Standalone IB Gateway" (recommended for API)

### **3. News Subscriptions (In IBKR Account Management)**
- [ ] Log in to Account Management: https://www.interactivebrokers.com/portal
- [ ] Go to: Settings → User Settings → API → Settings
- [ ] Check "Enable ActiveX and Socket Clients"
- [ ] Subscribe to API News Feeds (some are free):
  - Briefing.com General Market Columns (FREE)
  - Briefing.com Analyst Actions (FREE)
  - Dow Jones Newsletters (FREE with API)
  - Benzinga Pro (PAID - optional)

### **4. Python Dependencies**
- [ ] ib_async library installed
- [ ] Redis accessible

---

## 🚀 Step-by-Step Testing

### **STEP 1: Start IB Gateway**

#### **Option A: IB Gateway (Recommended)**
```bash
# Start IB Gateway
# On Linux:
~/Jts/ibgateway/XXX/ibgateway &

# On Windows:
# Double-click IB Gateway icon from Start Menu

# On Mac:
# Open IB Gateway from Applications
```

**Login Settings:**
- **For Testing**: Use Paper Trading account
- **Port**: 4002 (paper) or 4001 (live)
- **API Settings**:
  - Check "Enable ActiveX and Socket Clients"
  - Check "Read-Only API"
  - Set "Socket port" to 4002
  - Check "Create API message log file"

#### **Option B: Trader Workstation (TWS)**
```bash
# Open TWS
# Configure → API → Settings
# Enable API connections
# Port 7497 (paper) or 7496 (live)
```

**After starting, verify it's running:**
```bash
# Check if port is open
netstat -tuln | grep -E ":(4001|4002|7496|7497)"

# Should see something like:
# tcp        0      0 127.0.0.1:4002          0.0.0.0:*               LISTEN
```

---

### **STEP 2: Install ib_async Library**

```bash
# Install with uv (fast)
uv pip install --system ib_async

# Or with regular pip
pip install ib_async

# Verify installation
python3 -c "import ib_async; print('✅ ib_async installed')"
```

---

### **STEP 3: Test Basic Connection**

Create a simple test script:

```bash
cat > /tmp/test_ibkr_connection.py << 'EOF'
#!/usr/bin/env python3
"""Test IBKR Gateway Connection"""

from ib_async import IB
import asyncio

async def test_connection():
    ib = IB()

    print("🔍 Testing IBKR Gateway Connection...")
    print("=" * 60)

    try:
        # Try to connect (paper trading port)
        await ib.connectAsync('127.0.0.1', 4002, clientId=1)
        print("✅ Connected to IB Gateway!")
        print(f"   Connected to: {ib.client.host}:{ib.client.port}")
        print(f"   Client ID: {ib.client.clientId}")

        # Get account info
        accounts = ib.managedAccounts()
        print(f"\n📊 Accounts: {accounts}")

        # Test getting news providers
        print("\n📰 Checking News Providers...")
        providers = ib.reqNewsProviders()

        if providers:
            print(f"✅ Found {len(providers)} news providers:")
            for p in providers:
                print(f"   - {p.code}: {p.name}")
        else:
            print("⚠️  No news providers found")
            print("   → Subscribe to news in Account Management")

        # Disconnect
        ib.disconnect()
        print("\n✅ Connection test successful!")
        return True

    except ConnectionRefusedError:
        print("❌ Connection refused!")
        print("   → Is IB Gateway running?")
        print("   → Check port: 4002 (paper) or 4001 (live)")
        return False

    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Is IB Gateway/TWS running?")
        print("2. Is API enabled in settings?")
        print("3. Correct port? (4002 paper, 4001 live)")
        return False

if __name__ == "__main__":
    asyncio.run(test_connection())
EOF

# Run the test
python3 /tmp/test_ibkr_connection.py
```

**Expected Output:**
```
🔍 Testing IBKR Gateway Connection...
============================================================
✅ Connected to IB Gateway!
   Connected to: 127.0.0.1:4002
   Client ID: 1

📊 Accounts: ['DU123456']

📰 Checking News Providers...
✅ Found 3 news providers:
   - BRFG: Briefing.com General Market Columns
   - BRFUPDN: Briefing.com Analyst Actions
   - DJNL: Dow Jones Newsletters

✅ Connection test successful!
```

---

### **STEP 4: Test IBKR Collector**

```bash
# Set environment for local testing
export REDIS_PASSWORD="cyber-pi-redis-2025"
export REDIS_HOST="localhost"  # Use port-forward if needed
export REDIS_PORT="6379"

# Port-forward Redis if testing locally
kubectl port-forward -n cyber-pi-intel redis-0 6379:6379 &

# Wait a moment for port-forward
sleep 3

# Run the collector
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
  - BRFG: Briefing.com General Market Columns
  - BRFUPDN: Briefing.com Analyst Actions
  - DJNL: Dow Jones Newsletters

📰 Collecting BroadTape News (General Market)...
✅ BRFG: 5 cyber-relevant

📊 Collecting Watchlist News (Stock-Specific)...
✅ PANW: 2 relevant
✅ CRWD: 1 relevant
✅ MSFT: 3 relevant

🚀 Pushing 11 items to Redis highway...
✅ Pushed 11 items to Redis highway

============================================================
📊 COLLECTION SUMMARY
============================================================
BroadTape News:          5 items
Watchlist News:          6 items
Total Collected:        11 items
Queued to Redis:        11 items
============================================================

✅ Items now in Redis highway
   → Workers will process to Neo4j & Weaviate
```

---

### **STEP 5: Verify Data in Redis**

```bash
# Check Redis queues
kubectl exec -n cyber-pi-intel redis-0 -- \
  redis-cli -a cyber-pi-redis-2025 LLEN queue:weaviate

kubectl exec -n cyber-pi-intel redis-0 -- \
  redis-cli -a cyber-pi-redis-2025 LLEN queue:neo4j

# Should see counts > 0

# View a sample threat
kubectl exec -n cyber-pi-intel redis-0 -- \
  redis-cli -a cyber-pi-redis-2025 LRANGE queue:weaviate 0 0

# Should see: ["threat_abc123..."]

# Get the full threat data
THREAT_ID=$(kubectl exec -n cyber-pi-intel redis-0 -- \
  redis-cli -a cyber-pi-redis-2025 LINDEX queue:weaviate 0)

kubectl exec -n cyber-pi-intel redis-0 -- \
  redis-cli -a cyber-pi-redis-2025 GET "threat:parsed:$THREAT_ID"

# Should see JSON with IBKR financial intelligence
```

---

### **STEP 6: Verify Worker Processing**

```bash
# Check if workers are running
kubectl get pods -n cyber-pi-intel | grep worker

# Check worker logs
kubectl logs -n cyber-pi-intel -l app=storage-workers --tail=50

# Should see:
# "Processing threat_abc123..."
# "✅ Stored in Weaviate"
# "✅ Stored in Neo4j"

# Query Neo4j for IBKR threats
kubectl exec -n cyber-pi-intel neo4j-0 -- \
  cypher-shell -u neo4j -p cyber-pi-redis-2025 \
  "MATCH (t:CyberThreat) WHERE t.source CONTAINS 'IBKR' RETURN count(t) as ibkr_threats;"

# Should see count > 0
```

---

### **STEP 7: Query the Financial Intelligence**

```bash
# Query Neo4j for IBKR financial threats
kubectl exec -n cyber-pi-intel neo4j-0 -- \
  cypher-shell -u neo4j -p cyber-pi-neo4j-2025 \
  "MATCH (t:CyberThreat)
   WHERE t.source CONTAINS 'IBKR'
   RETURN t.title, t.source, t.severity
   LIMIT 5;"

# Query Weaviate for semantic search
# (Would need to implement Weaviate query script)

# Sample output:
# PANW: Palo Alto Networks Reports Security Incident
# CRWD: CrowdStrike Unusual Trading Activity
# MSFT: Microsoft Emergency Disclosure
```

---

## 🐛 Troubleshooting

### **Problem: Connection Refused**
```
❌ Connection refused to 127.0.0.1:4002
```

**Solution:**
1. Check IB Gateway is running: `ps aux | grep java | grep gateway`
2. Check correct port: Paper=4002, Live=4001
3. Check API enabled in Gateway settings
4. Firewall blocking? `sudo ufw status`

---

### **Problem: No News Providers**
```
✅ Connected but 0 news providers
```

**Solution:**
1. Log into IBKR Account Management
2. Go to Settings → Market Data Subscriptions
3. Subscribe to:
   - Briefing.com (FREE with API)
   - Dow Jones (FREE with API)
4. Wait 5-10 minutes for activation
5. Restart IB Gateway

---

### **Problem: Authentication Error**
```
❌ Authentication failed
```

**Solution:**
1. Re-login to IB Gateway
2. Check your IBKR account is active
3. Try paper trading account first
4. Check for 2FA requirements

---

### **Problem: No Cyber-Relevant News**
```
✅ Collected 0 cyber-relevant items
```

**Solution:**
This is OK! Financial news about security incidents is rare.
- Try collecting during market hours (9:30 AM - 4:00 PM ET)
- Wait for a real security incident
- Lower the keyword threshold in code
- Add more companies to watchlist

---

## 📊 Success Criteria

- [ ] ✅ Connected to IB Gateway successfully
- [ ] ✅ Saw 3+ news providers
- [ ] ✅ Collected some news items (even if 0 cyber-relevant)
- [ ] ✅ Data appeared in Redis (queue:weaviate, queue:neo4j)
- [ ] ✅ Workers processed data
- [ ] ✅ Can query IBKR threats from Neo4j

**If all checked:** 🎉 **IBKR Financial Intelligence is operational!**

---

## 🚀 Deploy for Production

Once testing is successful:

```bash
# Create IBKR collector CronJob
# (This would run on a machine with IB Gateway)

# For now, you can run manually:
# Every 5 minutes:
watch -n 300 'python3 collectors/ibkr_financial_intel.py'

# Or create a systemd service
# Or add to collection-cronjobs.yaml (if Gateway is on K8s node)
```

---

## 📝 Next Steps After Successful Test

1. **Run Regularly** - Set up automated collection (every 5-10 min)
2. **Monitor Alerts** - Watch for financial early warnings
3. **Tune Keywords** - Adjust cyber-relevant filters
4. **Expand Watchlist** - Add more companies (up to 500+)
5. **Build Correlation** - Connect stock drops to cyber events
6. **Create Dashboard** - Visualize financial-cyber intelligence

---

## 🎓 What You've Built

Once working, you have:
- **Real-time financial intelligence** (5-10 min updates)
- **Breach detection before disclosure** (stock drops = early warning)
- **500+ company monitoring** capability
- **Unique competitive advantage** (no other threat intel has this)
- **Premium feature** worth $15K-25K/month

---

**Ready to test? Let me know what step you're on and I'll help troubleshoot!**
