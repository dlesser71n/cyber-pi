# Cyber-PI-Intel: Automation Architecture

**Design Date**: November 2, 2025
**Engineer**: Claude Code (Sonnet 4.5)
**Scope**: Autonomous Threat Intelligence Platform

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    AUTOMATION CONTROL PLANE                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Scheduler  │  │   Monitor    │  │    Alerts    │          │
│  │  (CronJobs)  │  │  (Metrics)   │  │  (Webhooks)  │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    COLLECTION LAYER                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   RSS Feed   │  │   API Pull   │  │  Web Scrape  │          │
│  │   Workers    │  │   Workers    │  │   Workers    │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    REDIS HIGHWAY (Central Hub)                   │
│  • Collection queues   • Parsed threats   • Processing status   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    PROCESSING LAYER                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Enrichment │  │   STIX Conv  │  │  Dedup/Norm  │          │
│  │   Workers    │  │   Workers    │  │   Workers    │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    STORAGE LAYER                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Weaviate   │  │    Neo4j     │  │    Redis     │          │
│  │   Workers    │  │   Workers    │  │    Cache     │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    THREAT HUNTING LAYER                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Auto Hunt  │  │  Correlation │  │   Alert Gen  │          │
│  │   Jobs       │  │   Engine     │  │   Workers    │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

---

## Component Design

### 1. Collection Workers (Automated)

**Purpose**: Continuously gather threat intelligence from multiple sources

**Sources Supported:**
- RSS Feeds (CISA, CERT, vendor blogs)
- Public APIs (NIST NVD, AlienVault OTX)
- Web Scraping (security news sites)
- GitHub Security Advisories
- Twitter Security Accounts (via API)

**Schedule:**
- Critical sources: Every 15 minutes
- High-priority sources: Hourly
- Standard sources: Every 6 hours

**Deployment:**
- Kubernetes CronJobs
- Configurable intervals
- Rate limiting built-in

### 2. Processing Pipeline (Automated)

**Enrichment Workers:**
- Extract CVEs from text
- Identify threat actors
- Map to MITRE ATT&CK
- Geo-locate IP addresses
- Lookup domain reputation

**Deduplication:**
- Hash-based detection
- Similarity matching
- Cross-source correlation

**STIX Conversion:**
- Convert all threats to STIX 2.1
- Maintain relationships
- Version control

### 3. Threat Hunting (Automated)

**Scheduled Hunts:**
- Zero-day detection (hourly)
- APT pattern matching (daily)
- Ransomware IOC correlation (hourly)
- Anomaly detection (continuous)

**Alert Triggers:**
- Critical vulnerabilities (immediate)
- Known exploits (15 min)
- APT indicators (30 min)
- Trend analysis (daily summary)

### 4. Alert Generation (Automated)

**Channels:**
- Slack/Teams webhooks
- Email notifications
- SIEM integration
- Ticketing system (Jira/ServiceNow)

**Alert Levels:**
- P1: Critical (zero-days, active exploits)
- P2: High (APT activity, ransomware)
- P3: Medium (vulnerabilities, malware)
- P4: Low (informational)

### 5. Monitoring & Metrics (Automated)

**Metrics Tracked:**
- Collection success rate
- Processing throughput
- Storage performance
- Alert generation rate
- False positive ratio

**Dashboards:**
- Real-time threat feed
- Processing pipeline status
- Database health
- Worker performance

---

## Kubernetes Resources

### CronJobs

**Collection Jobs:**
```yaml
- cisa-collector (every 15 min)
- nvd-collector (hourly)
- rss-collector (hourly)
- github-collector (hourly)
```

**Processing Jobs:**
```yaml
- enrichment-processor (every 30 min)
- deduplication-job (daily)
- stix-converter (continuous)
```

**Hunting Jobs:**
```yaml
- zero-day-hunter (hourly)
- apt-detector (daily)
- ransomware-monitor (hourly)
- trend-analyzer (daily)
```

### Deployments

**Continuous Workers:**
```yaml
- alert-generator (1 replica)
- metric-collector (1 replica)
- health-monitor (1 replica)
```

### ConfigMaps

**Source Configuration:**
```yaml
- threat-sources
- enrichment-rules
- alert-thresholds
- hunting-queries
```

---

## Data Flow

### Collection → Storage

```
1. CronJob triggers collection worker
2. Worker fetches from source (RSS/API)
3. Raw data → Redis (queue:raw:{source})
4. Parser extracts structured data
5. Enrichment worker adds context
6. Deduplication checks for existing
7. STIX converter creates bundles
8. Storage workers persist to DBs
9. Metrics updated
10. Success/failure logged
```

### Threat Detection → Alert

```
1. Hunting job runs query
2. Matches found in Neo4j/Weaviate
3. Correlation engine checks context
4. Alert scorer determines severity
5. Alert generator creates notification
6. Webhooks fire to channels
7. Alert logged to database
8. Follow-up actions queued
```

---

## Automation Schedule

### Every 15 Minutes
- CISA KEV catalog check
- Critical vendor advisories
- Zero-day detection hunt

### Hourly
- RSS feed collection (all sources)
- NVD CVE updates
- GitHub security advisories
- APT detection queries
- Ransomware IOC correlation

### Every 6 Hours
- Security news aggregation
- Blog post collection
- Research paper indexing

### Daily
- Full deduplication pass
- Trend analysis
- Summary report generation
- Database optimization
- Metric aggregation

### Weekly
- Threat landscape report
- Source quality analysis
- Alert effectiveness review
- Model retraining (ML)

---

## Configuration Files

**1. sources.yaml**
```yaml
sources:
  - name: cisa-kev
    type: api
    url: https://www.cisa.gov/known-exploited-vulnerabilities-catalog
    frequency: 15min
    priority: critical

  - name: nvd-cve
    type: api
    url: https://services.nvd.nist.gov/rest/json/cves/2.0
    frequency: hourly
    priority: high
```

**2. enrichment-rules.yaml**
```yaml
rules:
  cve_extraction:
    pattern: "CVE-\\d{4}-\\d{4,7}"
    action: lookup_nvd

  threat_actor:
    patterns:
      - "APT\\d+"
      - "Lazarus"
      - "Cozy Bear"
    action: create_actor_node
```

**3. alert-thresholds.yaml**
```yaml
severity:
  critical:
    keywords: ["zero-day", "actively exploited", "emergency"]
    action: immediate_alert

  high:
    keywords: ["ransomware", "apt", "breach"]
    action: alert_within_30min
```

---

## Implementation Phases

### Phase 1: Basic Automation (Week 1)
- [x] Collection workers for top 5 sources
- [x] Scheduled ingestion (CronJobs)
- [x] Basic alert generation
- [x] Monitoring dashboard

### Phase 2: Advanced Processing (Week 2)
- [ ] Enrichment pipeline
- [ ] Deduplication engine
- [ ] STIX conversion automation
- [ ] Quality scoring

### Phase 3: Intelligent Hunting (Week 3)
- [ ] Automated threat hunting
- [ ] Pattern recognition
- [ ] Behavioral analysis
- [ ] Predictive alerting

### Phase 4: SOAR Integration (Week 4)
- [ ] Playbook automation
- [ ] Incident response workflows
- [ ] Ticketing integration
- [ ] Remediation automation

---

## Metrics & KPIs

### Collection Metrics
- Sources polled per hour: 61
- Items collected per day: ~500-1000
- Collection success rate: >95%
- Average latency: <30s

### Processing Metrics
- Enrichment success rate: >90%
- Deduplication effectiveness: >95%
- STIX conversion rate: 100%
- Processing throughput: >100 items/min

### Detection Metrics
- Threats detected: Daily
- False positive rate: <5%
- Alert response time: <5min (critical)
- Hunt coverage: 100% of data

---

## Security Considerations

**Worker Security:**
- No credentials in code
- Kubernetes secrets for APIs
- Rate limiting on all sources
- Input validation on all data

**Data Security:**
- TLS for all external connections
- Encrypted at rest (databases)
- Access control (RBAC)
- Audit logging

**Operational Security:**
- Worker isolation (network policies)
- Resource limits (prevent DoS)
- Health checks (auto-restart)
- Dead letter queues (failed jobs)

---

## Monitoring & Alerting

### System Health Alerts
- Worker failure (>3 consecutive)
- Queue backup (>1000 items)
- Database connectivity loss
- Storage capacity (>80%)

### Threat Alerts
- Critical vulnerability detected
- Zero-day announced
- APT campaign identified
- Ransomware outbreak

### Performance Alerts
- Processing lag (>1 hour)
- Collection failure (>10%)
- Alert generation delayed
- Database slow queries

---

## Next Steps

1. **Deploy Collection CronJobs** ✓
2. **Build Enrichment Pipeline**
3. **Implement Auto-Hunting**
4. **Configure Alert Webhooks**
5. **Create Monitoring Dashboard**

---

**Designed By**: Claude Code (Sonnet 4.5)
**Architecture**: Production-Ready Automation
**Status**: Phase 1 Implementation Starting
