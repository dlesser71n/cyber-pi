# Quick Reference - cyber-pi

**Fast access to common commands and patterns for this project.**

---

## 🚀 Fast Commands

### Testing
```bash
# Run monitoring validation
python3 test_monitoring_validation.py

# Run integration tests  
python3 test_integration_quick.py

# Full test suite
pytest -v
```

### Redis Operations
```bash
# Connect to Redis
redis-cli -p 32379

# Check Redis
redis-cli -p 32379 ping

# Monitor metrics
redis-cli -p 32379 --scan --pattern "metrics:periscope:*"

# Clear metrics (if needed)
redis-cli -p 32379 --scan --pattern "metrics:*" | xargs redis-cli -p 32379 DEL
```

### Neo4j Operations
```bash
# Check Neo4j status
cypher-shell -a bolt://localhost:7687 -u neo4j -p cyber-pi-neo4j-2025 "MATCH (n) RETURN count(n);"

# Query threats
cypher-shell -a bolt://localhost:7687 -u neo4j -p cyber-pi-neo4j-2025 "MATCH (t:Threat) RETURN t LIMIT 10;"
```

### GPU Monitoring
```bash
# Watch GPU usage
nvidia-smi -l 1

# GPU memory
nvidia-smi --query-gpu=memory.used,memory.total --format=csv

# Ollama status
curl http://localhost:11434/api/tags
```

### Git Workflow
```bash
# Status
git status --short

# Stage monitoring files
git add src/monitoring/ src/cyber_pi_periscope_integration_monitored.py *.md test_*.py

# Commit with conventional format
git commit -m "feat: Add monitoring infrastructure"

# Push
git push origin master
```

---

## 📋 Common Patterns

### Create New Feature
```bash
# 1. Create implementation
# 2. Create tests
# 3. Create documentation
# 4. Verify all tests pass
# 5. Git add, commit, push
```

### Deploy to Production
```bash
# NOT YET - still in development
# TODO: Create k8s deployment manifests
```

### Monitor System Health
```python
from cyber_pi_periscope_integration_monitored import MonitoredCyberPiPeriscopeIntegration

integration = MonitoredCyberPiPeriscopeIntegration()
await integration.initialize()

# Get health
health = await integration.get_comprehensive_health()
print(health['monitoring']['status'])

# Print metrics
integration.print_metrics_report()
```

---

## 🔧 Development Setup

### Install Dependencies
```bash
# Use uv pip (10-100x faster)
uv pip install --system -r requirements.txt

# Never use plain pip!
```

### Run Services
```bash
# Redis (should already be running)
systemctl status redis

# Neo4j
sudo systemctl status neo4j

# Ollama
systemctl status ollama
```

### Check Ports
```bash
# Redis: 32379
# Neo4j Bolt: 7687
# Neo4j HTTP: 7474
# Weaviate: 8080 (when deployed)
# Ollama: 11434
```

---

## 🎯 Project Structure

```
cyber-pi/
├── src/
│   ├── monitoring/              # Production monitoring
│   │   ├── __init__.py
│   │   └── periscope_monitor.py
│   ├── periscope/               # Periscope integration
│   ├── collectors/              # Threat intelligence collectors
│   └── cyber_pi_periscope_integration_monitored.py
├── test_monitoring_validation.py
├── test_integration_quick.py
├── requirements.txt
├── MONITORING_INFRASTRUCTURE.md
├── MONITORING_COMPLETE.md
└── VERIFICATION_COMPLETE.md
```

---

## 📊 Key Metrics

### Performance Targets
- **Redis latency**: <1ms
- **Neo4j query**: <100ms
- **Threat ingestion**: >100/second
- **Success rate**: >98%

### Current Status (Nov 8, 2025)
- ✅ Monitoring infrastructure complete
- ✅ All tests passing
- ⏳ Weaviate deployment pending
- ⏳ Full integration testing pending

---

## 🐛 Debugging

### Enable Debug Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check Monitoring
```python
from monitoring.periscope_monitor import get_monitor

monitor = get_monitor()
await monitor.initialize()

# Check metrics
print(monitor.get_metrics_summary())

# Check health
print(monitor.get_health_status())

# Get recent errors
print(monitor.get_recent_errors())
```

### View Dead Letter Queue
```python
monitor = get_monitor()
failed_items = monitor.get_dead_letter_queue()
print(f"Failed items: {len(failed_items)}")
```

---

## 🔗 Useful Links

- **GitHub**: https://github.com/dlesser71n/cyber-pi
- **Neo4j UI**: http://localhost:7474
- **System Context**: `.windsurf/SYSTEM_CONTEXT.md`
- **Full Docs**: `MONITORING_INFRASTRUCTURE.md`

---

**Last Updated**: November 8, 2025
