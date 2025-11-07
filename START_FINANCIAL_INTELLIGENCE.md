# 🚀 Start Financial Intelligence System

**Quick Start Guide for GPU-Accelerated Financial Threat Analysis**

---

## ✅ Prerequisites

1. **Ollama installed** with llama4:16x17b model
2. **Dual NVIDIA RTX A6000 GPUs** (96GB total VRAM)
3. **Python 3.8+** with required packages

---

## 🚀 Start Ollama (Single Instance, Dual GPU)

```bash
# Set both GPUs visible to Ollama
export CUDA_VISIBLE_DEVICES=0,1
export OLLAMA_HOST=0.0.0.0:11434

# Start Ollama (it will automatically load balance across both GPUs)
ollama serve
```

**How it works:**
- Ollama sees both GPUs (CUDA_VISIBLE_DEVICES=0,1)
- llama4:16x17b model (67GB) automatically splits across GPUs using tensor_split
- No manual load balancing needed - Ollama handles it internally

---

## 🧪 Test the System

### **Option 1: Quick Test**

```bash
python3 test_financial_intelligence.py
```

Expected output:
```
✅ GPU 0 (http://localhost:11434): Ollama running, llama4:16x17b available
📊 Test 1: Stock Market Anomaly Detection
✅ Analysis complete
   Threat Score: 85/100
   Confidence: 78%
```

### **Option 2: Maximum Stress Test**

```bash
python3 test_financial_intelligence_max.py
```

This will:
- Test parallel processing capacity (5-50 analyses)
- Run complex multi-factor analysis
- Sustained load test (50 analyses over 5 minutes)
- Real-world threat detection scenarios
- Verify GPU utilization

---

## 📊 Monitor GPU Usage

```bash
# Watch GPU utilization in real-time
watch -n 1 nvidia-smi
```

You should see:
```
+-----------------------------------------------------------------------------+
| NVIDIA-SMI 535.xx       Driver Version: 535.xx       CUDA Version: 12.2   |
|-------------------------------+----------------------+----------------------+
| GPU  Name        Persistence-M| Bus-Id        Disp.A | Volatile Uncorr. ECC |
| Fan  Temp  Perf  Pwr:Usage/Cap|         Memory-Usage | GPU-Util  Compute M. |
|===============================+======================+======================|
|   0  NVIDIA RTX A6000    On   | 00000000:17:00.0 Off |                  Off |
| 30%   45C    P2    75W / 300W |  35000MiB / 49140MiB |     95%      Default |
|   1  NVIDIA RTX A6000    On   | 00000000:65:00.0 Off |                  Off |
| 30%   44C    P2    70W / 300W |  32000MiB / 49140MiB |     92%      Default |
+-------------------------------+----------------------+----------------------+
```

**Good signs:**
- Both GPUs showing memory usage (~33-35GB each for 67GB model)
- Both GPUs showing high utilization (80-100% during inference)
- Balanced load across both GPUs

---

## 🎯 Usage Examples

### **Stock Market Anomaly Detection:**

```python
from src.intelligence.financial_threat_analyzer import FinancialThreatAnalyzer

analyzer = FinancialThreatAnalyzer()

# Analyze suspicious stock activity
result = await analyzer.analyze_stock_anomalies('UNH', {
    'ticker': 'UNH',
    'price': 524.50,
    'volume_change': 245.3,  # 245% spike!
    'options_activity': 'Unusual put buying (3x normal)',
    'short_interest': 12.5,  # High
    'insider_trading': '3 executives sold shares'
})

print(f"Threat Score: {result['threat_score']}/100")
print(f"Analysis: {result['raw_analysis']}")
```

### **Cryptocurrency Ransomware Tracking:**

```python
# Track ransomware payment
result = await analyzer.analyze_crypto_payments({
    'wallet_id': '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb',
    'transaction_count': 47,
    'total_value_usd': 2450000,
    'pattern': 'Multiple small inflows, single large outflow',
    'mixing_services': 'Tornado Cash',
    'suspected_gang': 'LockBit'
})
```

### **Vendor Financial Risk:**

```python
# Assess vendor cyber risk
result = await analyzer.analyze_vendor_risk({
    'company': 'Acme Security Solutions',
    'ticker': 'ACME',
    'revenue_trend': '-15% YoY',
    'debt_ratio': 0.85,
    'layoffs': '200 employees (25% of workforce)',
    'security_spending_pct': 2.1  # Down from 4.5%
})
```

---

## 📈 Expected Performance

### **Single Analysis:**
- Stock anomaly: 3-5 seconds
- Crypto tracking: 3-5 seconds
- Vendor risk: 4-6 seconds

### **Parallel Processing:**
- Batch of 10: ~12-15 seconds
- Batch of 20: ~25-30 seconds
- Batch of 50: ~60-75 seconds

### **Daily Capacity:**
- ~10-20 analyses/second
- ~864,000 - 1,728,000 analyses/day
- More than sufficient for real-time monitoring

---

## 🔧 Troubleshooting

### **Problem: Ollama not found**
```bash
# Check if Ollama is installed
which ollama

# If not installed, install from https://ollama.ai
curl -fsSL https://ollama.com/install.sh | sh
```

### **Problem: llama4:16x17b not found**
```bash
# Check available models
ollama list

# If llama4:16x17b not listed, it should already be downloaded
# Check with: ollama show llama4:16x17b
```

### **Problem: Out of memory**
```bash
# Check GPU memory
nvidia-smi

# llama4:16x17b needs ~67GB total
# With dual A6000s (96GB total), you have plenty of room
```

### **Problem: Slow performance**
```bash
# Verify both GPUs are visible
echo $CUDA_VISIBLE_DEVICES  # Should show: 0,1

# Check GPU utilization
nvidia-smi

# Both GPUs should show ~80-100% utilization during inference
```

---

## 🎯 Integration with Periscope

To integrate financial intelligence with Periscope triage:

```python
from src.intelligence.financial_threat_analyzer import FinancialThreatAnalyzer
from src.periscope.periscope_batch_ops import PeriscopeTriageBatch

analyzer = FinancialThreatAnalyzer()
periscope = PeriscopeTriageBatch()
await periscope.initialize()

# Analyze financial threat
result = await analyzer.analyze_stock_anomalies('UNH', stock_data)

# Ingest to Periscope if high threat
if result['threat_score'] >= 70:
    await periscope.add_threat(
        threat_id=f"fin_stock_UNH_{timestamp}",
        content=result['raw_analysis'],
        severity='CRITICAL' if result['threat_score'] >= 80 else 'HIGH',
        metadata={
            'type': 'financial_intelligence',
            'ticker': 'UNH',
            'threat_score': result['threat_score']
        }
    )
```

---

## 📚 Documentation

- **Complete Guide:** `FINANCIAL_INTELLIGENCE_COMPLETE.md`
- **API Reference:** `src/intelligence/financial_threat_analyzer.py`
- **Test Suite:** `test_financial_intelligence.py`
- **Stress Test:** `test_financial_intelligence_max.py`

---

**🔭 See threats before they surface... from financial signals no one else is watching.**
