# 🎓 Ollama Multi-GPU Expert Analysis

**Complete understanding based on official docs, GitHub issues, Medium articles, and community best practices**

---

## ✅ Executive Summary: You Were RIGHT

After comprehensive research, **your original approach with single Ollama instance is CORRECT**. Here's the complete picture:

---

## 🎯 How Ollama Actually Works with Multiple GPUs

### **Three Different Multi-GPU Scenarios:**

#### **Scenario 1: Model FITS on Single GPU (Your llama4:16x17b does NOT fit)**
- **Model size:** < 48GB (fits on one A6000)
- **Ollama behavior:** Loads entire model on ONE GPU
- **Best practice:** Run MULTIPLE Ollama instances (one per GPU, different ports)
- **Use case:** Parallel requests, not single-request speed
- **Example:** llama3.1:70b on H100 (80GB) - fits entirely

#### **Scenario 2: Model DOESN'T FIT on Single GPU (YOUR CASE)**
- **Model size:** 67GB (llama4:16x17b)
- **GPU capacity:** 48GB per A6000
- **Ollama behavior:** AUTOMATICALLY splits model across ALL visible GPUs
- **Configuration:** `CUDA_VISIBLE_DEVICES=0,1` + single Ollama instance
- **Result:** Ollama automatically distributes layers across both GPUs

#### **Scenario 3: Force Multi-GPU Split (Advanced)**
- **Use Modelfile with:** `PARAMETER num_gpu 999`
- **Purpose:** Force distribution even if model fits on one GPU
- **Benefit:** Can improve throughput for some workloads
- **Downside:** May reduce performance due to inter-GPU communication

---

## 🔍 Key Findings from Research

### **1. Ollama's Automatic Behavior (from GitHub issues #11986, #7104)**

```
When CUDA_VISIBLE_DEVICES=0,1 is set:
├─ Ollama detects both GPUs automatically
├─ If model fits on ONE GPU → uses that GPU only
├─ If model DOESN'T fit → automatically splits across ALL GPUs
└─ Split is done at LAYER level (not tensor level)
```

**Critical insight from issue #11986:**
> "Since version 0.11.5, models are always placed on multiple GPUs, even if one GPU has more than enough RAM"

This was actually a COMPLAINT because it slowed down smaller models!

### **2. The OLLAMA_SCHED_SPREAD Environment Variable**

From `envconfig/config.go`:
```go
// SchedSpread allows scheduling models across all GPUs.
SchedSpread = Bool("OLLAMA_SCHED_SPREAD")
```

**What it does:**
- `OLLAMA_SCHED_SPREAD=true` (default in v0.11.5+): Always spread across GPUs
- `OLLAMA_SCHED_SPREAD=false`: Only use multiple GPUs if model doesn't fit

**For your case (67GB model on 48GB GPUs):**
- Setting doesn't matter - model MUST split across both GPUs
- Ollama has no choice but to use both

### **3. How Layer Splitting Works**

From Medium article "Goodbye, VRAM Limits":
```
Ollama splits at the LAYER level:
├─ Transformer layers are the unit of distribution
├─ Each layer goes to ONE GPU (not split within layer)
├─ Roughly 50/50 split with identical GPUs
└─ Inter-GPU communication via PCIe/NVLink
```

**For llama4:16x17b:**
- Model has ~100 layers (estimate)
- GPU 0: ~50 layers (~33.5GB)
- GPU 1: ~50 layers (~33.5GB)
- Communication: Activations passed between GPUs during inference

---

## 🚫 What You DON'T Need

### **Multiple Ollama Instances (Ports 11434 + 11435)**

**When to use:**
- ✅ Model FITS on single GPU
- ✅ Want to handle PARALLEL requests
- ✅ Example: 8x H100s with llama3.1:70b

**When NOT to use (YOUR CASE):**
- ❌ Model DOESN'T fit on single GPU
- ❌ Want faster SINGLE request (layer split is automatic)
- ❌ Example: llama4:16x17b (67GB) on 2x A6000 (48GB each)

### **Manual Load Balancing**

**Not needed because:**
- Ollama handles layer distribution automatically
- No API-level load balancing required
- Single request uses both GPUs automatically

---

## ✅ Correct Setup for Your System

### **Hardware:**
- 2x NVIDIA RTX A6000 (48GB VRAM each = 96GB total)
- Model: llama4:16x17b (67GB)

### **Correct Configuration:**

```bash
# Single Ollama instance
export CUDA_VISIBLE_DEVICES=0,1  # Both GPUs visible
export OLLAMA_HOST=0.0.0.0:11434  # Single port
ollama serve
```

**What happens:**
1. Ollama detects both GPUs
2. Loads llama4:16x17b
3. Realizes 67GB doesn't fit on 48GB
4. Automatically splits ~50 layers to GPU 0, ~50 layers to GPU 1
5. During inference, activations flow between GPUs
6. Both GPUs work together on EVERY request

### **Optional: Force Even Distribution (Modelfile)**

If you want to ensure optimal layer distribution:

```bash
# Create Modelfile
cat > Modelfile << 'EOF'
FROM llama4:16x17b
PARAMETER num_gpu 999
EOF

# Create optimized model
ollama create llama4:16x17b-multi -f ./Modelfile

# Run it
ollama run llama4:16x17b-multi
```

**Note:** This is probably unnecessary since your model already doesn't fit on one GPU.

---

## 📊 Performance Expectations

### **What You Should See:**

```bash
watch -n 1 nvidia-smi
```

**Expected output:**
```
GPU 0: ~33-35GB VRAM used, 80-100% utilization
GPU 1: ~33-35GB VRAM used, 80-100% utilization
```

**Both GPUs should show:**
- Similar memory usage (~33-35GB each)
- High utilization during inference (80-100%)
- Balanced load

### **Performance Characteristics:**

**Single Request:**
- Both GPUs work together
- Speed limited by inter-GPU communication (PCIe bandwidth)
- Expect ~3-5 seconds per analysis (as you're seeing)

**Throughput:**
- Can handle multiple requests sequentially
- Each request uses both GPUs
- ~10-20 requests/minute capacity

---

## 🔧 Troubleshooting

### **If Only ONE GPU Shows Activity:**

**Check:**
```bash
# Verify both GPUs visible
echo $CUDA_VISIBLE_DEVICES  # Should show: 0,1

# Check Ollama sees both
ollama ps  # Should show model loaded

# Monitor during inference
watch -n 0.5 nvidia-smi
```

**Fix:**
```bash
# Ensure CUDA_VISIBLE_DEVICES is set BEFORE starting Ollama
export CUDA_VISIBLE_DEVICES=0,1
ollama serve
```

### **If Performance is Slow:**

**Possible causes:**
1. **PCIe bottleneck:** Activations transferring between GPUs
2. **Unbalanced split:** Layers not evenly distributed
3. **Memory pressure:** Swapping to system RAM

**Solutions:**
1. Use Modelfile with `num_gpu 999` to force even distribution
2. Increase batch size if doing batch processing
3. Monitor with `nvidia-smi` to verify both GPUs active

---

## 🎓 Advanced: When to Use Multiple Instances

### **Scenario: Model FITS on Single GPU**

If you had a smaller model (e.g., llama3.1:8b = 4.7GB):

```bash
# Terminal 1 - GPU 0
export CUDA_VISIBLE_DEVICES=0
export OLLAMA_HOST=0.0.0.0:11434
ollama serve

# Terminal 2 - GPU 1
export CUDA_VISIBLE_DEVICES=1
export OLLAMA_HOST=0.0.0.0:11435
ollama serve
```

**Then in your code:**
```python
# Round-robin load balancing
hosts = ["http://localhost:11434", "http://localhost:11435"]
current = 0

def get_next_host():
    global current
    host = hosts[current]
    current = (current + 1) % len(hosts)
    return host

# Each request goes to different GPU
for request in requests:
    host = get_next_host()
    response = requests.post(f"{host}/api/generate", ...)
```

**Benefit:** 2x throughput for parallel requests

**But for YOUR model (67GB):** This doesn't work because model doesn't fit on one GPU!

---

## 📚 Key Learnings

### **1. Ollama is Smart**
- Automatically detects GPU configuration
- Automatically splits models that don't fit
- No manual configuration needed for basic multi-GPU

### **2. Layer-Level Splitting**
- Models split at transformer layer boundaries
- Each layer goes to ONE GPU entirely
- Inter-GPU communication for activations

### **3. Two Different Use Cases**
- **Model doesn't fit:** Automatic split (YOUR CASE)
- **Model fits:** Multiple instances for parallel requests

### **4. Version Matters**
- v0.11.5+ changed default behavior
- Now spreads across GPUs more aggressively
- Can disable with `OLLAMA_SCHED_SPREAD=false` (but doesn't help your case)

---

## ✅ Final Recommendation for Your System

### **Current Setup (CORRECT):**

```bash
# Start Ollama
export CUDA_VISIBLE_DEVICES=0,1
export OLLAMA_HOST=0.0.0.0:11434
ollama serve

# Use in Python
analyzer = FinancialThreatAnalyzer(
    ollama_host="http://localhost:11434",
    model="llama4:16x17b"
)
```

**Why this is correct:**
1. ✅ Model (67GB) doesn't fit on single GPU (48GB)
2. ✅ Ollama automatically uses both GPUs
3. ✅ No manual load balancing needed
4. ✅ Both GPUs work together on every request
5. ✅ Simplest configuration that works

### **What You DON'T Need:**
- ❌ Two Ollama instances (ports 11434 + 11435)
- ❌ Manual load balancing in Python
- ❌ Round-robin host selection
- ❌ Complex configuration

### **Optional Optimization:**

If you want to ensure optimal layer distribution:

```bash
# Create optimized model
cat > Modelfile << 'EOF'
FROM llama4:16x17b
PARAMETER num_gpu 999
EOF

ollama create llama4:16x17b-optimized -f ./Modelfile

# Use optimized model
analyzer = FinancialThreatAnalyzer(
    ollama_host="http://localhost:11434",
    model="llama4:16x17b-optimized"
)
```

---

## 🎯 Conclusion

**You were RIGHT from the beginning.** 

Your original approach with:
- Single Ollama instance
- `CUDA_VISIBLE_DEVICES=0,1`
- Single port (11434)

Is the **CORRECT** configuration for running a 67GB model across 2x 48GB GPUs.

The dual-instance approach I initially suggested is only for scenarios where the model FITS on a single GPU and you want to handle parallel requests.

**Your system is already optimized. No changes needed.**

---

**🔭 See threats before they surface... with properly configured GPU infrastructure.**
