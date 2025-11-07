# 🚀 Cyber-PI-Intel Quick Start Guide

## 📍 Access Points

### **Backend API**
```bash
# Port forward (from host)
microk8s kubectl port-forward -n cyber-pi-intel svc/backend-api 8000:8000

# Access
curl http://localhost:8000/

# API Documentation
http://localhost:8000/docs
```

### **Neo4j Browser**
```bash
# Via NGINX Gateway
http://localhost:30888/neo4j/

# Direct port forward
microk8s kubectl port-forward -n cyber-pi-intel svc/neo4j 7474:7474

# Credentials
Username: neo4j
Password: cyber-pi-neo4j-2025
```

### **Weaviate**
```bash
# Via NGINX Gateway
http://localhost:30888/weaviate/v1/schema

# Direct port forward
microk8s kubectl port-forward -n cyber-pi-intel svc/weaviate 8080:8080
```

### **Redis**
```bash
# Port forward
microk8s kubectl port-forward -n cyber-pi-intel svc/redis 6380:6379

# Connect
redis-cli -h localhost -p 6380 -a cyber-pi-redis-2025

# Check data
redis-cli -h localhost -p 6380 -a cyber-pi-redis-2025 --no-auth-warning LLEN queue:weaviate
```

---

## 🔥 API Endpoints (All Working)

### **Health & Status**
```bash
# API Info
curl http://localhost:8000/

# Health Check
curl http://localhost:8000/health
```

### **Analytics**
```bash
# Threat Landscape Summary
curl http://localhost:8000/analytics/summary

# Top Exploited CVEs
curl http://localhost:8000/analytics/top-cves?limit=10
```

### **Threat Actors**
```bash
# List All Actors
curl http://localhost:8000/actors

# Actor Profile
curl http://localhost:8000/actors/Lazarus
```

### **CVE Management**
```bash
# Priority Patching List
curl http://localhost:8000/cves/priority?limit=20
```

### **Campaign Detection**
```bash
# Detect Related Threats
curl http://localhost:8000/campaigns?min_shared_cves=3
```

### **Source-Specific Queries**
```bash
# OT/ICS Threats
curl http://localhost:8000/sources/ot-ics?limit=20

# Dark Web Intelligence
curl http://localhost:8000/sources/dark-web
```

### **Threat Search**
```bash
# Get Recent Threats
curl http://localhost:8000/threats?limit=50

# Filter by Severity
curl http://localhost:8000/threats?severity=critical&limit=20
```

---

## 📊 Neo4j Queries

### **Quick Stats**
```cypher
// Threat landscape
MATCH (threat:CyberThreat)
OPTIONAL MATCH (threat)-[:EXPLOITS]->(cve:CVE)
OPTIONAL MATCH (threat)-[:ATTRIBUTED_TO]->(actor:ThreatActor)
RETURN 
  count(DISTINCT threat) as totalThreats,
  count(DISTINCT cve) as uniqueCVEs,
  count(DISTINCT actor) as activeActors
```

### **Most Exploited CVEs**
```cypher
MATCH (cve:CVE)<-[:EXPLOITS]-(threat:CyberThreat)
WITH cve, count(threat) as exploitCount
WHERE exploitCount > 1
RETURN cve.cveId as cve, exploitCount
ORDER BY exploitCount DESC
LIMIT 10
```

### **Threat Actor Campaigns**
```cypher
MATCH (actor:ThreatActor)<-[:ATTRIBUTED_TO]-(threat:CyberThreat)
WITH actor, collect(threat.title) as campaigns, count(threat) as count
RETURN actor.actorName as actor, count as campaignCount, campaigns[0..3] as sampleCampaigns
ORDER BY count DESC
```

### **Campaign Detection (Similar Threats)**
```cypher
MATCH (t1:CyberThreat)-[:EXPLOITS]->(cve:CVE)<-[:EXPLOITS]-(t2:CyberThreat)
WHERE id(t1) < id(t2)
WITH t1, t2, collect(cve.cveId) as sharedCVEs, count(cve) as commonality
WHERE commonality >= 3
RETURN 
  t1.title as threat1,
  t2.title as threat2,
  commonality as sharedVulnerabilities,
  sharedCVEs[0..5] as samples
ORDER BY commonality DESC
LIMIT 20
```

---

## 🔧 Management Commands

### **Check Pod Status**
```bash
microk8s kubectl get pods -n cyber-pi-intel
```

### **View API Logs**
```bash
microk8s kubectl logs -n cyber-pi-intel -l app=backend-api --tail=50
```

### **Restart API**
```bash
microk8s kubectl rollout restart deployment/backend-api -n cyber-pi-intel
```

### **Check Database Health**
```bash
# Redis
redis-cli -h localhost -p 6380 -a cyber-pi-redis-2025 --no-auth-warning PING

# Neo4j
curl -u neo4j:cyber-pi-neo4j-2025 http://localhost:30888/neo4j/db/neo4j/tx/commit \
  -H "Content-Type: application/json" \
  -d '{"statements":[{"statement":"RETURN 1"}]}'

# Weaviate
curl http://localhost:30888/weaviate/v1/.well-known/ready
```

---

## 📈 Data Ingestion

### **Re-ingest Threats**
```bash
cd /home/david/projects/cyber-pi-intel
python3 ingest_redis_first.py
```

### **Run Workers**
```bash
# Deploy all workers
microk8s kubectl apply -f deployment/cyber-pi-simplified/worker-jobs.yaml

# Check worker status
microk8s kubectl get jobs -n cyber-pi-intel

# View worker logs
microk8s kubectl logs -n cyber-pi-intel job/weaviate-worker-1
```

---

## 🎯 Common Use Cases

### **1. Get CVE Priority List**
```bash
curl -s http://localhost:8000/cves/priority?limit=10 | python3 -m json.tool
```

### **2. Track Threat Actor Activity**
```bash
curl -s http://localhost:8000/actors/Lazarus | python3 -m json.tool
```

### **3. Detect Campaigns**
```bash
curl -s http://localhost:8000/campaigns?min_shared_cves=5 | python3 -m json.tool
```

### **4. Monitor OT/ICS Threats**
```bash
curl -s http://localhost:8000/sources/ot-ics?limit=20 | python3 -m json.tool
```

### **5. Dark Web Monitoring**
```bash
curl -s http://localhost:8000/sources/dark-web | python3 -m json.tool
```

---

## 📁 Important Files

```
/home/david/projects/cyber-pi-intel/
├── backend/api/threat_intel_api.py          # FastAPI server
├── backend/core/stix_converter.py           # STIX 2.1 converter
├── src/collectors/                          # Intelligence collectors
│   ├── ot_ics_collector.py                 # Industrial threats
│   ├── social_media_expansion.py           # Social intelligence
│   ├── dark_web_monitor.py                 # Underground intel
│   └── unified_threat_collector.py         # Master orchestrator
├── deployment/cyber-pi-simplified/          # Kubernetes configs
│   ├── backend-api-deployment.yaml
│   ├── worker-jobs.yaml
│   └── deploy-all.sh
├── neo4j_advanced_patterns.cypher           # Graph queries
├── ingest_redis_first.py                    # Data ingestion
└── SESSION_COMPLETE_OCT31.md                # Full documentation
```

---

## 🆘 Troubleshooting

### **API Not Responding**
```bash
# Check pods
microk8s kubectl get pods -n cyber-pi-intel -l app=backend-api

# Restart if needed
microk8s kubectl rollout restart deployment/backend-api -n cyber-pi-intel

# Check logs
microk8s kubectl logs -n cyber-pi-intel -l app=backend-api --tail=100
```

### **Database Connection Issues**
```bash
# Test Redis
redis-cli -h localhost -p 6380 -a cyber-pi-redis-2025 --no-auth-warning PING

# Test Neo4j
microk8s kubectl exec -n cyber-pi-intel neo4j-0 -- cypher-shell -u neo4j -p cyber-pi-neo4j-2025 "RETURN 1"

# Test Weaviate
curl http://localhost:30888/weaviate/v1/.well-known/ready
```

### **Port Forwards Died**
```bash
# Kill old port forwards
pkill -f "port-forward.*cyber-pi-intel"

# Restart
microk8s kubectl port-forward -n cyber-pi-intel svc/backend-api 8000:8000 &
microk8s kubectl port-forward -n cyber-pi-intel svc/redis 6380:6379 &
```

---

## 📚 Documentation

- **Full Session Report:** `SESSION_COMPLETE_OCT31.md`
- **STIX Integration:** `STIX_ONTOLOGY_INTEGRATION.md`
- **Multi-Source Collection:** `COMPREHENSIVE_INTELLIGENCE_COLLECTION.md`
- **Neo4j Patterns:** `neo4j_advanced_patterns.cypher`
- **API Docs:** `http://localhost:8000/docs` (when running)

---

## 🎉 Quick Demo Commands

```bash
# 1. Check system health
curl http://localhost:8000/health | python3 -m json.tool

# 2. Get threat landscape
curl http://localhost:8000/analytics/summary | python3 -m json.tool

# 3. See top CVEs
curl http://localhost:8000/analytics/top-cves?limit=5 | python3 -m json.tool

# 4. Track threat actors
curl http://localhost:8000/actors | python3 -m json.tool

# 5. Detect campaigns
curl http://localhost:8000/campaigns | python3 -m json.tool
```

---

**STATUS: ✅ ALL SYSTEMS OPERATIONAL**

**Access API:** `http://localhost:8000` (after port-forward)  
**Access Docs:** `http://localhost:8000/docs`  
**Access Neo4j:** `http://localhost:30888/neo4j/`
