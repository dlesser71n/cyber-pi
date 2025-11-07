# ✈️ PRE-FLIGHT CHECKLIST - NEO4J NUCLEAR DEPLOYMENT

**Before executing `./EXECUTE_NUCLEAR_DEPLOYMENT.sh`**

---

## ☑️ **SYSTEM REQUIREMENTS**

### **1. Kubernetes Cluster**
```bash
# Verify MicroK8s is running
microk8s status
# Should show: microk8s is running

# Check available resources
microk8s kubectl top nodes
# Need: 8+ CPU cores available, 32+ GB RAM available
```

### **2. Namespace Exists**
```bash
# Verify cyber-pi-intel namespace
microk8s kubectl get namespace cyber-pi-intel
# Should exist, or will be created automatically
```

### **3. Storage Available**
```bash
# Check available storage
df -h /var/snap/microk8s/common/default-storage
# Need: 250+ GB free for Neo4j data (200Gi) + logs (20Gi) + overhead
```

### **4. Network Connectivity**
```bash
# Verify internet access (for plugin downloads)
curl -I https://github.com
# Should return: HTTP/2 200

# Verify can reach GitHub releases
curl -I https://github.com/neo4j/apoc/releases/download/5.26.0/apoc-5.26.0-core.jar
# Should return: HTTP/2 302 (redirect) or 200
```

---

## ☑️ **DATA REQUIREMENTS**

### **1. CVE Data Downloaded**
```bash
# Check if file exists
ls -lh data/cve_import/all_cves_neo4j.json
# Should show: ~1.1G file

# Verify file is valid JSON
head -n 1 data/cve_import/all_cves_neo4j.json | python3 -m json.tool > /dev/null && echo "✅ Valid JSON" || echo "❌ Invalid JSON"
```

### **2. CVE Data Quality**
```bash
# Quick count
cat data/cve_import/all_cves_neo4j.json | python3 -c "import json,sys; print(f'{len(json.load(sys.stdin)):,} CVEs')"
# Should show: ~316,552 CVEs
```

### **3. Python Environment**
```bash
# Verify venv exists
ls -la .venv/bin/python3
# Should exist

# Check Python version
.venv/bin/python3 --version
# Should be: Python 3.11.x or higher

# Verify required packages
.venv/bin/python3 -c "import neo4j, redis, json, pandas; print('✅ All imports OK')"
# Should print: ✅ All imports OK
```

---

## ☑️ **SERVICE DEPENDENCIES**

### **1. Redis Running**
```bash
# Check Redis pod
microk8s kubectl get pods -n cyber-pi-intel | grep redis
# Should show: redis-0  1/1  Running

# Test Redis connectivity
redis-cli -h localhost -p 6379 PING 2>/dev/null || echo "⚠️ Redis not accessible on localhost:6379"
```

### **2. No Conflicting Neo4j**
```bash
# Verify no old Neo4j running
microk8s kubectl get pods -n cyber-pi-intel | grep neo4j
# Should return nothing (or show old pod we're about to delete)

# Check no port conflict
ss -tlnp | grep :7474
# Should be empty or only show kubectl port-forward
```

### **3. TQAKB Not Using Same Ports**
```bash
# Check if ports 7474, 7687 are available
ss -tlnp | grep -E ':(7474|7687)'
# If busy, note which process is using them
```

---

## ☑️ **DEPLOYMENT ARTIFACTS**

### **1. Kubernetes Manifests**
```bash
# Verify deployment YAML exists
ls -lh k8s/neo4j-2025-complete.yaml
# Should exist

# Validate YAML syntax
microk8s kubectl apply -f k8s/neo4j-2025-complete.yaml --dry-run=client
# Should return: statefulset.apps/neo4j created (dry run)
```

### **2. Loader Scripts**
```bash
# Check Redis loader
ls -lh src/bootstrap/redis_cve_loader.py
# Should exist

# Check Neo4j loader
ls -lh src/bootstrap/neo4j_cve_loader.py
# Should exist

# Verify execution script
ls -lh EXECUTE_NUCLEAR_DEPLOYMENT.sh
# Should show: -rwxr-xr-x (executable)
```

---

## ☑️ **CREDENTIALS & ACCESS**

### **1. Neo4j Password Set**
```bash
# Verify password in deployment YAML
grep "NEO4J_AUTH" k8s/neo4j-2025-complete.yaml
# Should show: value: "neo4j/cyber-pi-neo4j-2025"
```

### **2. Can Access Services**
```bash
# Test ClusterIP access (from pod)
microk8s kubectl run test-pod --rm -i --tty --image=busybox --restart=Never -- sh -c "nslookup neo4j.cyber-pi-intel.svc.cluster.local" 2>/dev/null || echo "⚠️ DNS resolution test skipped"
```

---

## ☑️ **CLEANUP VERIFICATION**

### **1. Old PVCs Identified**
```bash
# List old Neo4j PVCs
microk8s kubectl get pvc -n cyber-pi-intel | grep neo4j
# Note: These will be deleted during deployment

# Check PVC sizes
microk8s kubectl get pvc -n cyber-pi-intel -o jsonpath='{range .items[?(@.metadata.name=="neo4j-data-neo4j-0")]}{.spec.resources.requests.storage}{"\n"}{end}'
# Note current size if exists
```

### **2. Backup Confirmation**
```bash
# If old Neo4j has data, confirm backup
echo "⚠️  IMPORTANT: Old Neo4j PVCs will be DELETED"
echo "   If you have important data, back it up first!"
echo ""
read -p "Confirm: No important data to backup (yes/no): " BACKUP_CONFIRM
```

---

## ☑️ **PERFORMANCE BASELINE**

### **1. System Load**
```bash
# Check current system load
uptime
# Load should be reasonable (not maxed out)

# Check memory pressure
free -h
# Should have 32+ GB available

# Check disk I/O
iostat -x 1 3 | tail -n 4
# Verify not saturated
```

### **2. Network Throughput**
```bash
# Test download speed (GitHub)
curl -o /dev/null -s -w '%{speed_download}\n' https://github.com/neo4j/apoc/releases/download/5.26.0/apoc-5.26.0-core.jar | awk '{print $1/1024/1024 " MB/s"}'
# Should be > 1 MB/s for reasonable download time
```

---

## ☑️ **FINAL CHECKS**

### **1. Time Availability**
```bash
echo "Deployment will take approximately 15-20 minutes:"
echo "  • Cleanup: 2 minutes"
echo "  • Neo4j deployment: 5 minutes"
echo "  • Plugin download: 3 minutes"
echo "  • Verification: 2 minutes"
echo "  • Redis load: 3 minutes"
echo ""
read -p "Confirm: I have 20+ minutes available (yes/no): " TIME_CONFIRM
```

### **2. Monitoring Ready**
```bash
# Open additional terminal for monitoring
echo "Recommended: Open another terminal to watch pod status"
echo "  Terminal 2: microk8s kubectl get pods -n cyber-pi-intel -w"
echo ""
read -p "Press Enter when ready to proceed..."
```

---

## ✅ **PRE-FLIGHT COMPLETE**

If all checks pass, you're ready to execute:

```bash
./EXECUTE_NUCLEAR_DEPLOYMENT.sh
```

---

## 🚨 **TROUBLESHOOTING PRE-FLIGHT FAILURES**

### **Insufficient Storage**
```bash
# Free up space
sudo microk8s kubectl delete pvc <old-pvc-name> -n <namespace>

# Or expand storage
sudo lvextend -L +100G /dev/mapper/ubuntu--vg-ubuntu--lv
sudo resize2fs /dev/mapper/ubuntu--vg-ubuntu--lv
```

### **Port Conflicts**
```bash
# Kill conflicting process
sudo ss -tlnp | grep :7474
sudo kill <PID>

# Or use different ports (update YAML)
```

### **Network Issues**
```bash
# Test with different mirror
curl -I https://repo1.maven.org/maven2/

# Or download plugins manually and place in /tmp
```

### **Python Package Issues**
```bash
# Reinstall packages
cd /home/david/projects/cyber-pi
source .venv/bin/activate
uv pip install --force-reinstall neo4j redis pandas
```

---

**Run this checklist before deployment to ensure smooth execution!**
