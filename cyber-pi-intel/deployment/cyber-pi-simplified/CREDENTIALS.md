# Cyber-PI Intelligence System Credentials
# CENTRAL CREDENTIAL REFERENCE

**Created:** October 31, 2025  
**Purpose:** Central credential management for cyber-pi-intel namespace  
**Security:** All credentials stored in Kubernetes Secrets

---

## 🔐 CREDENTIALS INVENTORY

### 1. Neo4j Graph Database

**Location:** Kubernetes Secret `cyber-pi-credentials`

```yaml
Username: neo4j
Password: cyber-pi-neo4j-2025
```

**Connection Strings:**
- **Internal (Bolt):** `bolt://neo4j:cyber-pi-neo4j-2025@neo4j:7687`
- **External (Bolt):** `bolt://neo4j:cyber-pi-neo4j-2025@localhost:30687`
- **Web UI:** `http://localhost:30474`

**Access:**
```bash
# Via kubectl
kubectl get secret cyber-pi-credentials -n cyber-pi-intel -o jsonpath='{.data.neo4j-password}' | base64 -d

# Via Neo4j Browser
URL: http://localhost:30474
User: neo4j
Pass: cyber-pi-neo4j-2025
```

---

### 2. Redis Cache

**Location:** Kubernetes Secret `cyber-pi-credentials`

```yaml
Password: cyber-pi-redis-2025
```

**Connection Strings:**
- **Internal:** `redis://:cyber-pi-redis-2025@redis:6379/0`
- **External:** `redis://:cyber-pi-redis-2025@localhost:30379/0`

**Access:**
```bash
# Via kubectl
kubectl get secret cyber-pi-credentials -n cyber-pi-intel -o jsonpath='{.data.redis-password}' | base64 -d

# Via redis-cli
redis-cli -h localhost -p 30379 -a cyber-pi-redis-2025
```

---

### 3. Weaviate Vector Database

**Location:** Kubernetes Secret `cyber-pi-credentials`

```yaml
API Key: cyber-pi-weaviate-key-2025
```

**Connection Strings:**
- **Internal:** `http://weaviate:8080`
- **External:** `http://localhost:30883`

**Access:**
```bash
# Via kubectl
kubectl get secret cyber-pi-credentials -n cyber-pi-intel -o jsonpath='{.data.weaviate-api-key}' | base64 -d

# Via curl (with API key)
curl -H "Authorization: Bearer cyber-pi-weaviate-key-2025" http://localhost:30883/v1/.well-known/ready
```

**Note:** Currently in anonymous mode for development. Enable API key in production.

---

### 4. TQAKB Backend (Future)

**Location:** Kubernetes Secret `cyber-pi-credentials`

```yaml
JWT Secret: cyber-pi-jwt-secret-change-in-production-2025
Admin User: admin
Admin Pass: cyber-pi-admin-2025
```

**Access:**
```bash
# Via kubectl
kubectl get secret cyber-pi-credentials -n cyber-pi-intel -o jsonpath='{.data.jwt-secret-key}' | base64 -d
kubectl get secret cyber-pi-credentials -n cyber-pi-intel -o jsonpath='{.data.admin-password}' | base64 -d
```

---

## 🔑 SECRET MANAGEMENT

### View All Secrets

```bash
# List secrets
kubectl get secrets -n cyber-pi-intel

# View secret contents (base64 encoded)
kubectl get secret cyber-pi-credentials -n cyber-pi-intel -o yaml

# Decode specific value
kubectl get secret cyber-pi-credentials -n cyber-pi-intel -o jsonpath='{.data.neo4j-password}' | base64 -d
```

### Update Secrets

```bash
# Edit secret directly
kubectl edit secret cyber-pi-credentials -n cyber-pi-intel

# Or update from file
kubectl apply -f secrets.yaml
```

### Delete and Recreate

```bash
# Delete existing secret
kubectl delete secret cyber-pi-credentials -n cyber-pi-intel

# Recreate from file
kubectl apply -f secrets.yaml
```

---

## 📋 CONFIGMAP (NON-SENSITIVE)

**Location:** Kubernetes ConfigMap `cyber-pi-config`

**Contents:**
- Environment settings (development/production)
- Database hostnames and ports
- Cache configuration
- Performance tuning parameters

**View ConfigMap:**
```bash
kubectl get configmap cyber-pi-config -n cyber-pi-intel -o yaml
```

---

## 🔒 SECURITY BEST PRACTICES

### Development Environment

✅ **Current Setup (Acceptable for Dev):**
- Credentials in Kubernetes Secrets
- RBAC restricts secret access to namespace
- Secrets mounted as environment variables or volumes

⚠️ **Not for Production:**
- Passwords are relatively simple
- No external secret management (Vault, etc.)
- Anonymous access enabled on Weaviate

### Production Requirements

**Before Production Deployment:**

1. **Rotate All Passwords**
   - Generate strong passwords (32+ characters)
   - Use password manager or generator
   - Update secrets.yaml with new values

2. **Enable Authentication Everywhere**
   - Redis: Enable requirepass
   - Weaviate: Disable anonymous, use API keys
   - Neo4j: Strong password

3. **External Secret Management**
   - Consider HashiCorp Vault
   - Or AWS Secrets Manager
   - Or Azure Key Vault
   - Or Sealed Secrets for GitOps

4. **TLS/SSL Encryption**
   - Enable TLS for Neo4j Bolt connections
   - Enable TLS for Redis connections
   - Use HTTPS for Weaviate

5. **Network Policies**
   - Restrict pod-to-pod communication
   - Only allow necessary traffic
   - Block external access except through ingress

---

## 🚨 PRODUCTION PASSWORD ROTATION CHECKLIST

**When moving to production:**

- [ ] Generate strong Neo4j password (32+ chars)
- [ ] Generate strong Redis password (32+ chars)
- [ ] Generate strong Weaviate API key (64+ chars)
- [ ] Generate strong JWT secret (64+ chars)
- [ ] Generate strong admin password (32+ chars)
- [ ] Update secrets.yaml with new passwords
- [ ] Apply updated secrets: `kubectl apply -f secrets.yaml`
- [ ] Restart all pods to use new secrets
- [ ] Verify all connections working with new credentials
- [ ] Document new passwords in password manager
- [ ] Delete old credentials from version control
- [ ] Enable TLS on all database connections
- [ ] Configure network policies
- [ ] Enable audit logging for secret access

---

## 📊 SECRET ACCESS PATTERNS

### From Application Code

**Python Example:**
```python
import os

# Read from environment variables (populated from secrets)
neo4j_password = os.environ.get('NEO4J_PASSWORD')
redis_password = os.environ.get('REDIS_PASSWORD')
weaviate_api_key = os.environ.get('WEAVIATE_API_KEY')

# Or read from mounted secret files
with open('/etc/secrets/neo4j-password', 'r') as f:
    neo4j_password = f.read().strip()
```

**Deployment Example:**
```yaml
spec:
  containers:
  - name: backend
    env:
    - name: NEO4J_PASSWORD
      valueFrom:
        secretKeyRef:
          name: cyber-pi-credentials
          key: neo4j-password
    - name: REDIS_PASSWORD
      valueFrom:
        secretKeyRef:
          name: cyber-pi-credentials
          key: redis-password
```

---

## 🔍 TROUBLESHOOTING

### Secret Not Found

```bash
# Check if secret exists
kubectl get secret cyber-pi-credentials -n cyber-pi-intel

# If not, create it
kubectl apply -f secrets.yaml
```

### Wrong Password

```bash
# View current password (base64 encoded)
kubectl get secret cyber-pi-credentials -n cyber-pi-intel -o jsonpath='{.data.neo4j-password}'

# Decode to verify
kubectl get secret cyber-pi-credentials -n cyber-pi-intel -o jsonpath='{.data.neo4j-password}' | base64 -d
```

### Pod Can't Access Secret

```bash
# Check pod environment variables
kubectl exec -n cyber-pi-intel <pod-name> -- env | grep NEO4J

# Check pod secret mount
kubectl exec -n cyber-pi-intel <pod-name> -- ls -la /etc/secrets/

# Check RBAC permissions
kubectl auth can-i get secrets --namespace cyber-pi-intel
```

---

## 📝 CREDENTIAL CHANGE LOG

**Version 1.0 (October 31, 2025):**
- Initial credential setup
- Development environment passwords
- All passwords in Kubernetes Secrets

**Future Changes:**
- Document all password rotations here
- Include date, who changed, and why
- Reference incident tickets if applicable

---

## 🎯 QUICK REFERENCE

**Get All Credentials at Once:**
```bash
# Decode all secrets to a file (DO NOT COMMIT)
kubectl get secret cyber-pi-credentials -n cyber-pi-intel -o json | \
  jq -r '.data | to_entries[] | "\(.key): \(.value | @base64d)"' > credentials.txt

# View file
cat credentials.txt

# DELETE FILE AFTER VIEWING
rm credentials.txt
```

**Connection Test Script:**
```bash
#!/bin/bash
# Test all database connections with credentials

# Redis
redis-cli -h localhost -p 30379 -a cyber-pi-redis-2025 ping

# Neo4j (requires cypher-shell)
cypher-shell -a bolt://localhost:30687 -u neo4j -p cyber-pi-neo4j-2025 "RETURN 1"

# Weaviate
curl -H "Authorization: Bearer cyber-pi-weaviate-key-2025" \
  http://localhost:30883/v1/.well-known/ready
```

---

**IMPORTANT:** 
- **Never commit real production passwords to git**
- **Rotate all passwords before production**
- **Use external secret management for production**
- **Enable audit logging for secret access**

---

**Last Updated:** October 31, 2025  
**Next Review:** Before production deployment  
**Owner:** cyber-pi infrastructure team
