# MicroK8s Database Setup for Cyber-PI

**Date:** November 5, 2025  
**Status:** Port Forwarding Active ✅

---

## Current Status

### **Databases Running in MicroK8s** ✅

**Namespace:** `cyber-pi-intel`

| Database | Pod Status | Service IP | Ports |
|----------|------------|------------|-------|
| **Neo4j** | Running (3d5h) | 10.152.183.169 | 7474, 7687 |
| **Redis** | Running (4d8h) | 10.152.183.253 | 6379 |
| **Weaviate** | Running (4d8h) | 10.152.183.191 | 8080, 50051 |

---

## Port Forwarding (Alternative Ports)

**Script:** `k8s-port-forward.sh`

### **Active Ports:**
- **Neo4j HTTP:** `http://localhost:17474` (instead of 7474)
- **Neo4j Bolt:** `bolt://localhost:17687` (instead of 7687)
- **Redis:** `localhost:16379` (instead of 6379)
- **Weaviate:** `http://localhost:18080` (instead of 8080)

### **Start Port Forwarding:**
```bash
./k8s-port-forward.sh
```

### **Stop Port Forwarding:**
```bash
pkill -f 'kubectl port-forward.*cyber-pi-intel'
```

---

## Environment Configuration

**File:** `.env.k8s`

```bash
# Neo4j
export NEO4J_URI="bolt://localhost:17687"
export NEO4J_HTTP_URI="http://localhost:17474"
export NEO4J_USER="neo4j"
export NEO4J_PASSWORD="<your-password>"

# Redis
export REDIS_HOST="localhost"
export REDIS_PORT="16379"
export REDIS_PASSWORD="<your-password>"

# Weaviate
export WEAVIATE_URL="http://localhost:18080"

# Load environment
source .env.k8s
```

---

## Initialize Neo4j Schema

### **Step 1: Get Neo4j Password**

```bash
# Get password from Kubernetes secret
microk8s kubectl get secret -n cyber-pi-intel neo4j-auth -o jsonpath='{.data.NEO4J_AUTH}' | base64 -d
```

### **Step 2: Set Environment**

```bash
export NEO4J_URI="bolt://localhost:17687"
export NEO4J_USER="neo4j"
export NEO4J_PASSWORD="<password-from-step-1>"
```

### **Step 3: Initialize Schema**

```bash
# Create constraints and indexes
python src/graph/neo4j_schema.py init

# Validate
python src/graph/neo4j_schema.py validate

# View summary
python src/graph/neo4j_schema.py summary
```

**Expected Output:**
```
🚀 Initializing Neo4j schema...
Creating constraints...
✓ Created constraint: cve_id
✓ Created constraint: vendor_id
...
Creating property indexes...
✓ Created index: cve_severity
✓ Created index: vendor_name
...
✅ Schema initialization complete
```

---

## Load Data

### **Load Recent CVEs (Last 30 Days)**

```bash
export NVD_API_KEY="<optional>"  # Improves rate limits

python src/loaders/cve_loader.py recent
```

### **Load MITRE ATT&CK**

```bash
python src/loaders/mitre_loader.py enterprise
```

### **Test with 10 CVEs**

```bash
python src/loaders/cve_loader.py test
```

---

## Verify Connections

### **Neo4j**

```bash
# Test connection
curl http://localhost:17474

# Or use Cypher shell
microk8s kubectl exec -n cyber-pi-intel neo4j-0 -- cypher-shell -u neo4j -p <password> "MATCH (n) RETURN count(n);"
```

### **Redis**

```bash
# Test connection
redis-cli -h localhost -p 16379 -a <password> PING
```

### **Weaviate**

```bash
# Test connection
curl http://localhost:18080/v1/meta
```

---

## Schema Status

### **Neo4j** ⏳ Pending
- **Code Ready:** ✅ Yes
- **Schema Deployed:** ❌ No (auth issue)
- **Action Needed:** Get correct password and run init

### **Weaviate** ⏳ Pending
- **Code Ready:** ❌ No (partially created)
- **Schema Deployed:** ❌ No
- **Action Needed:** Complete schema code

### **Redis** ⏳ Pending
- **Code Ready:** ❌ No
- **Schema Deployed:** ❌ No
- **Action Needed:** Create schema code

---

## Next Steps

1. **Get Neo4j Password:**
   ```bash
   microk8s kubectl get secret -n cyber-pi-intel neo4j-auth -o jsonpath='{.data.NEO4J_AUTH}' | base64 -d
   ```

2. **Initialize Neo4j Schema:**
   ```bash
   export NEO4J_PASSWORD="<password>"
   python src/graph/neo4j_schema.py init
   ```

3. **Load Sample Data:**
   ```bash
   python src/loaders/cve_loader.py test
   python src/loaders/mitre_loader.py enterprise
   ```

4. **Verify:**
   ```bash
   python src/graph/neo4j_schema.py validate
   ```

---

## Troubleshooting

### **Port Forward Not Working**

```bash
# Check if port forward is running
ps aux | grep "kubectl port-forward"

# Restart port forwarding
pkill -f 'kubectl port-forward.*cyber-pi-intel'
./k8s-port-forward.sh
```

### **Authentication Failed**

```bash
# Get correct password
microk8s kubectl get secret -n cyber-pi-intel neo4j-auth -o jsonpath='{.data.NEO4J_AUTH}' | base64 -d

# Or check pod logs
microk8s kubectl logs -n cyber-pi-intel neo4j-0
```

### **Connection Refused**

```bash
# Check if pods are running
microk8s kubectl get pods -n cyber-pi-intel

# Check if services exist
microk8s kubectl get svc -n cyber-pi-intel

# Restart port forwarding
./k8s-port-forward.sh
```

---

## Files Created

- `k8s-port-forward.sh` - Port forwarding script
- `.env.k8s` - Environment configuration
- `K8S_DATABASE_SETUP.md` - This documentation

---

**Status:** Port forwarding active. Need Neo4j password to initialize schema.
