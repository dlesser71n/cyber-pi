# Cyber-PI Deployment Guide

**Date**: November 7, 2025  
**Version**: 1.0.0  
**Namespace**: cyber-pi

---

## Quick Start

Deploy the complete Cyber-PI threat intelligence platform:

```bash
cd /home/david/projects/cyber-pi

# 1. Create namespace (if not exists)
microk8s kubectl create namespace cyber-pi

# 2. Deploy infrastructure
microk8s kubectl apply -f cyber-pi-intel/deployment/cyber-pi-simplified/secrets.yaml
microk8s kubectl apply -f cyber-pi-intel/deployment/cyber-pi-simplified/redis-deployment.yaml
microk8s kubectl apply -f cyber-pi-intel/deployment/cyber-pi-simplified/neo4j-deployment.yaml
microk8s kubectl apply -f cyber-pi-intel/deployment/cyber-pi-simplified/weaviate-deployment.yaml

# 3. Deploy Ollama (LLM service)
microk8s kubectl apply -f k8s/ollama-deployment.yaml

# 4. Wait for services to be ready
microk8s kubectl wait --for=condition=ready pod -l app=redis -n cyber-pi --timeout=300s
microk8s kubectl wait --for=condition=ready pod -l app=neo4j -n cyber-pi --timeout=300s
microk8s kubectl wait --for=condition=ready pod -l app=weaviate -n cyber-pi --timeout=300s
microk8s kubectl wait --for=condition=ready pod -l app=ollama -n cyber-pi --timeout=300s

# 5. Pull Ollama model
microk8s kubectl exec -n cyber-pi deployment/ollama -- ollama pull llama3.1:8b

# 6. Run data collectors
microk8s kubectl apply -f k8s/cisa-kev-collector-job.yaml
microk8s kubectl apply -f k8s/github-advisories-collector-job.yaml

# 7. Run threat hunters
microk8s kubectl apply -f k8s/cisa-kev-monitor-job.yaml
microk8s kubectl apply -f k8s/apt-detector-job.yaml
microk8s kubectl apply -f k8s/ransomware-monitor-job.yaml

# 8. Generate executive report
microk8s kubectl apply -f k8s/executive-report-generator-job.yaml
```

---

## Architecture

### Infrastructure Services

#### Redis
- **Purpose**: Primary data store for threat intelligence
- **Storage**: 1,457 keys (CISA KEVs, threat analysis results)
- **Service**: `redis.cyber-pi.svc.cluster.local:6379`
- **Password**: `cyber-pi-redis-2025`

#### Neo4j
- **Purpose**: Graph database for relationship analysis
- **Service**: `neo4j.cyber-pi.svc.cluster.local:7687`
- **Browser**: `neo4j.cyber-pi.svc.cluster.local:7474`

#### Weaviate
- **Purpose**: Vector database for semantic search
- **Service**: `weaviate.cyber-pi.svc.cluster.local:8080`

#### Ollama
- **Purpose**: Local LLM for report generation
- **Model**: llama3.1:8b
- **Service**: `ollama.cyber-pi.svc.cluster.local:11434`
- **Ingress**: `ollama.cyber-pi.local`
- **Storage**: 100Gi PVC for models
- **GPU**: Supports nvidia.com/gpu

---

## Data Collectors

### 1. CISA KEV Collector
**File**: `k8s/cisa-kev-collector-job.yaml`

Collects Known Exploited Vulnerabilities from CISA:
- **Source**: https://www.cisa.gov/known-exploited-vulnerabilities
- **Frequency**: On-demand (run as Kubernetes Job)
- **Output**: Redis keys `cisa:kev:CVE-*`
- **Last Run**: 1,455 vulnerabilities collected

**Run**:
```bash
microk8s kubectl apply -f k8s/cisa-kev-collector-job.yaml
microk8s kubectl logs -n cyber-pi job/cisa-kev-collector -f
```

### 2. GitHub Advisories Collector
**File**: `k8s/github-advisories-collector-job.yaml`

Collects security advisories from GitHub:
- **Source**: GitHub Security Advisories API
- **Note**: Requires GitHub token for higher rate limits
- **Output**: Redis keys `github:advisory:GHSA-*`

**Run**:
```bash
microk8s kubectl apply -f k8s/github-advisories-collector-job.yaml
```

---

## Threat Hunters

### 1. CISA KEV Monitor
**File**: `k8s/cisa-kev-monitor-job.yaml`

Analyzes KEV data for threat patterns:
- Recent additions (last 30 days)
- Upcoming remediation deadlines
- Critical action items
- Vendor distribution

**Results**:
- 20 recent KEVs
- 14 urgent deadlines
- 487 critical actions
- Top vendor: Microsoft (348 KEVs)

### 2. APT Detector
**File**: `k8s/apt-detector-job.yaml`

Identifies Advanced Persistent Threat indicators:
- **512 APT suspects** identified
- **251 critical** (score ≥5)
- **17 potential campaigns** detected

**Top Targets**:
- Microsoft: 291 APT-related CVEs
- Cisco: 41 APT-related CVEs
- Citrix: 16 APT-related CVEs

### 3. Ransomware Monitor
**File**: `k8s/ransomware-monitor-job.yaml`

Detects ransomware attack vectors:
- **369 ransomware risks** identified
- **27 critical** (score ≥7)
- **Primary vector**: RCE (487 vulnerabilities)

**Attack Vectors**:
1. RCE: 487 vulnerabilities
2. Path Traversal: 68
3. Auth Bypass: 63
4. Deserialization: 50

---

## Executive Report Generator

**File**: `k8s/executive-report-generator-job.yaml`  
**Script**: `src/report_generator.py`

Generates comprehensive executive reports using LLM:

**Process**:
1. Collects threat data from Redis
2. Aggregates statistics and trends
3. Sends prompt to Ollama (llama3.1:8b)
4. Generates business-focused report
5. Stores in Redis (`report:executive:latest`)

**Report Sections**:
1. Executive Summary
2. Key Findings
3. Critical Threats
4. Immediate Actions Required
5. Strategic Recommendations
6. Risk Assessment

**Run**:
```bash
microk8s kubectl apply -f k8s/executive-report-generator-job.yaml
microk8s kubectl logs -n cyber-pi job/executive-report-generator -f
```

**Retrieve Report**:
```bash
microk8s kubectl exec -n cyber-pi redis-0 -- redis-cli -a cyber-pi-redis-2025 --no-auth-warning GET report:executive:latest
```

---

## Monitoring

### Check Service Status
```bash
microk8s kubectl get all -n cyber-pi
```

### View Logs
```bash
# Collectors
microk8s kubectl logs -n cyber-pi job/cisa-kev-collector
microk8s kubectl logs -n cyber-pi job/github-advisories-collector

# Hunters
microk8s kubectl logs -n cyber-pi job/cisa-kev-monitor
microk8s kubectl logs -n cyber-pi job/apt-detector
microk8s kubectl logs -n cyber-pi job/ransomware-monitor

# Report Generator
microk8s kubectl logs -n cyber-pi job/executive-report-generator
```

### Query Redis Data
```bash
# Total keys
microk8s kubectl exec -n cyber-pi redis-0 -- redis-cli -a cyber-pi-redis-2025 --no-auth-warning DBSIZE

# List KEVs
microk8s kubectl exec -n cyber-pi redis-0 -- redis-cli -a cyber-pi-redis-2025 --no-auth-warning KEYS "cisa:kev:*"

# Get specific vulnerability
microk8s kubectl exec -n cyber-pi redis-0 -- redis-cli -a cyber-pi-redis-2025 --no-auth-warning HGETALL "cisa:kev:CVE-2024-43451"

# Get threat hunting results
microk8s kubectl exec -n cyber-pi redis-0 -- redis-cli -a cyber-pi-redis-2025 --no-auth-warning GET threat:apt:suspects_count
microk8s kubectl exec -n cyber-pi redis-0 -- redis-cli -a cyber-pi-redis-2025 --no-auth-warning GET threat:ransomware:risks_count
```

---

## Cleanup

### Delete Jobs
```bash
microk8s kubectl delete job -n cyber-pi cisa-kev-collector
microk8s kubectl delete job -n cyber-pi github-advisories-collector
microk8s kubectl delete job -n cyber-pi cisa-kev-monitor
microk8s kubectl delete job -n cyber-pi apt-detector
microk8s kubectl delete job -n cyber-pi ransomware-monitor
microk8s kubectl delete job -n cyber-pi executive-report-generator
```

### Delete All Resources
```bash
microk8s kubectl delete namespace cyber-pi
```

---

## Troubleshooting

### Ollama Not Ready
```bash
# Check Ollama status
microk8s kubectl get pods -n cyber-pi -l app=ollama

# View Ollama logs
microk8s kubectl logs -n cyber-pi deployment/ollama

# Manually pull model
microk8s kubectl exec -n cyber-pi deployment/ollama -- ollama pull llama3.1:8b
```

### Redis Connection Issues
```bash
# Test Redis connection
microk8s kubectl exec -n cyber-pi redis-0 -- redis-cli -a cyber-pi-redis-2025 --no-auth-warning PING

# Check Redis logs
microk8s kubectl logs -n cyber-pi redis-0
```

### Job Failures
```bash
# Check job status
microk8s kubectl get jobs -n cyber-pi

# View failed job logs
microk8s kubectl logs -n cyber-pi job/<job-name>

# Delete and recreate
microk8s kubectl delete job -n cyber-pi <job-name>
microk8s kubectl apply -f k8s/<job-name>-job.yaml
```

---

## Automation

### Scheduled Data Collection (CronJob)

Create a CronJob for daily KEV collection:

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: daily-kev-collection
  namespace: cyber-pi
spec:
  schedule: "0 6 * * *"  # Daily at 6 AM
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
                pip install --quiet aiohttp redis
                # ... (collector script)
          restartPolicy: OnFailure
```

### Weekly Threat Hunting

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: weekly-threat-hunting
  namespace: cyber-pi
spec:
  schedule: "0 8 * * 1"  # Monday at 8 AM
  jobTemplate:
    # Run all hunters sequentially
```

---

## Performance Tuning

### Ollama
- **GPU**: Ensure GPU is available for faster inference
- **Memory**: Increase to 32Gi for larger models
- **Parallel**: Adjust `OLLAMA_NUM_PARALLEL` for concurrent requests

### Redis
- **Memory**: Monitor usage with `INFO memory`
- **Persistence**: Configure RDB/AOF for data durability
- **Eviction**: Set `maxmemory-policy` appropriately

### Neo4j
- **Heap**: Adjust `dbms.memory.heap.max_size`
- **Page Cache**: Tune `dbms.memory.pagecache.size`
- **Indexes**: Create indexes on frequently queried properties

---

## Security

### Secrets Management
- Store credentials in Kubernetes Secrets
- Use RBAC for access control
- Rotate passwords regularly

### Network Policies
- Restrict pod-to-pod communication
- Use NetworkPolicies for isolation
- Enable mTLS for service mesh

### Data Protection
- Encrypt data at rest (PVC encryption)
- Use TLS for all external connections
- Implement backup and disaster recovery

---

## Support

**GitHub**: https://github.com/dlesser71n/cyber-pi  
**Documentation**: See README.md and MIGRATION_COMPLETE.md

---

**Last Updated**: November 7, 2025  
**Version**: 1.0.0
