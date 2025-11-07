# 🚀 BYOK HANDOFF: Unified Threat Intelligence Graph Builder

**Project:** Cyber-Pi Intelligence Platform  
**Task:** Build complete Neo4j threat intelligence graph  
**Standard:** Nuclear-grade (Admiral Rickover principles)  
**Deadline:** Tonight

---

## OBJECTIVE

Create `unified_threat_graph_builder.py` that integrates:
- **316,552 CVEs** from Redis Highway
- **ThreatIntel data** from Weaviate  
- **MITRE ATT&CK** framework (14 tactics, ~200 techniques)
- **Complete graph relationships** for predictive analytics

---

## INFRASTRUCTURE

### Redis (CVE Source)
```python
host='10.152.183.253'
port=6379
password='cyber-pi-redis-2025'
decode_responses=True
```

### Neo4j (Destination)
```python
uri='bolt://10.152.183.169:7687'
user='neo4j'
password='cyber-pi-neo4j-2025'
```

### Weaviate (ThreatIntel Source)
```python
url='http://10.152.183.242:8080'
```

---

## GRAPH SCHEMA (COMPLETE)

### Node Types

```cypher
// Core CVE Data
(:CVE {
    id: 'CVE-2024-1234',
    description: 'text',
    cvss_v3: 9.8,
    cvss_v2: 7.5,
    severity: 'critical',
    published: '2024-01-15T...',
    modified: '2024-03-20T...',
    year: 2024,
    embedding_available: true,
    source: 'NVD'
})

// Vendors
(:Vendor {
    name: 'microsoft'
})

// Products
(:Product {
    name: 'windows'
})

// CWE (Common Weakness Enumeration)
(:CWE {
    id: 'CWE-79',
    name: 'Cross-Site Scripting'  // optional, if you can map it
})

// Threat Intelligence
(:ThreatIntel {
    id: 'string',
    title: 'string',
    description: 'string',
    severity: 'critical|high|medium|low',
    type: 'malware|phishing|exploit|...',
    source: 'string',
    publishedDate: 'date',
    confidence: 0.95
})

// MITRE ATT&CK Tactics
(:MitreTactic {
    id: 'TA0001',
    name: 'Initial Access',
    description: 'text'
})

// MITRE ATT&CK Techniques
(:MitreTechnique {
    id: 'T1055',
    name: 'Process Injection',
    description: 'text',
    tactic: 'TA0004'  // Link to parent tactic
})

// Indicators of Compromise
(:IOC {
    value: '192.168.1.1',
    type: 'ip_address|domain|hash|...',
    source: 'ThreatIntel ID'
})
```

### Relationship Types

```cypher
// CVE Relationships
(CVE)-[:AFFECTS]->(Product)
(Product)-[:MADE_BY]->(Vendor)
(CVE)-[:HAS_WEAKNESS]->(CWE)

// Threat Intelligence Relationships
(ThreatIntel)-[:REFERENCES]->(CVE)
(ThreatIntel)-[:TARGETS]->(Product)
(ThreatIntel)-[:USES_TECHNIQUE]->(MitreTechnique)
(ThreatIntel)-[:USES_TACTIC]->(MitreTactic)
(ThreatIntel)-[:HAS_IOC]->(IOC)

// MITRE Relationships
(MitreTechnique)-[:PART_OF_TACTIC]->(MitreTactic)
(CWE)-[:ENABLES_TECHNIQUE]->(MitreTechnique)

// Semantic Similarity (Optional for Phase 1)
(CVE)-[:SIMILAR_TO {score: 0.85}]->(CVE)
```

---

## DATA SOURCES

### 1. Redis (CVEs)

**Keys pattern:** `cve:CVE-*` (exclude `*:embedding` keys)

**Data format (Redis Hash):**
```python
{
    'id': 'CVE-2024-1234',
    'description': 'Remote code execution...',
    'cvss_v3': '9.8',
    'cvss_v2': '7.5',
    'severity': 'critical',
    'published': '2024-01-15T12:00:00',
    'modified': '2024-03-20T14:30:00',
    'vendors': 'microsoft,apache',  # comma-separated
    'products': 'windows,httpd',     # comma-separated
    'cwes': 'CWE-787,CWE-119',       # comma-separated
    'references': 'url1,url2',       # comma-separated
    'source': 'NVD'
}
```

**Conversion required:**
- Parse comma-separated strings to lists
- Convert numeric strings to floats
- Parse ISO datetime strings

### 2. Weaviate (ThreatIntel)

**Class:** `ThreatIntel`

**Query:**
```python
import weaviate
client = weaviate.Client("http://10.152.183.242:8080")

results = client.query.get(
    "ThreatIntel",
    ["id", "title", "description", "severity", "type", "source", 
     "cves", "iocs", "mitreTactics", "mitreTechniques",
     "affectedProducts", "affectedVendors", "publishedDate", "confidence"]
).with_limit(10000).do()

threats = results['data']['Get']['ThreatIntel']
```

**Fields:**
- `cves`: array of CVE IDs (e.g., ["CVE-2024-1234", ...])
- `iocs`: array of IOC strings
- `mitreTactics`: array of tactic IDs (e.g., ["TA0001", ...])
- `mitreTechniques`: array of technique IDs (e.g., ["T1055", ...])
- `affectedProducts`, `affectedVendors`: arrays

### 3. MITRE ATT&CK (Static Data)

**14 Tactics:**
```python
MITRE_TACTICS = {
    'TA0001': 'Initial Access',
    'TA0002': 'Execution',
    'TA0003': 'Persistence',
    'TA0004': 'Privilege Escalation',
    'TA0005': 'Defense Evasion',
    'TA0006': 'Credential Access',
    'TA0007': 'Discovery',
    'TA0008': 'Lateral Movement',
    'TA0009': 'Collection',
    'TA0010': 'Exfiltration',
    'TA0011': 'Command and Control',
    'TA0040': 'Impact',
    'TA0042': 'Resource Development',
    'TA0043': 'Reconnaissance'
}
```

**~200 Techniques** - Suggest creating a mapping file or using MITRE ATT&CK Navigator data.

For now, just create nodes for techniques mentioned in Weaviate ThreatIntel data.

---

## PYDANTIC MODEL (CVE)

**Location:** `src/models/cve_models.py`

**Key method:**
```python
from models.cve_models import CVE

cve = CVE(**data_dict)  # Validates
neo4j_props = cve.to_neo4j_node()  # Returns dict for Neo4j
```

**The `to_neo4j_node()` returns:**
```python
{
    'id': self.cve_id,
    'description': self.description,
    'cvss_v3': self.cvss_v3_score,
    'cvss_v2': self.cvss_v2_score,
    'severity': self.severity.value,
    'published': self.published.isoformat() if self.published else None,
    'modified': self.modified.isoformat() if self.modified else None,
    'year': self.published.year if self.published else None,
    'embedding_available': True,
    'assigner': self.assigner,
    'source': self.source
}
```

**Helper properties:**
- `cve.vendor_names` → list of vendor names
- `cve.product_names` → list of product names  
- `cve.cwes` → list of CWE IDs

---

## IMPLEMENTATION REQUIREMENTS

### Phase 1: Schema Setup (5 min)
```python
def create_schema(self):
    """Create constraints and indexes"""
    # Constraints
    CREATE CONSTRAINT cve_id_unique IF NOT EXISTS FOR (c:CVE) REQUIRE c.id IS UNIQUE
    CREATE CONSTRAINT vendor_name_unique IF NOT EXISTS FOR (v:Vendor) REQUIRE v.name IS UNIQUE
    CREATE CONSTRAINT product_name_unique IF NOT EXISTS FOR (p:Product) REQUIRE p.name IS UNIQUE
    CREATE CONSTRAINT cwe_id_unique IF NOT EXISTS FOR (w:CWE) REQUIRE w.id IS UNIQUE
    CREATE CONSTRAINT threat_id_unique IF NOT EXISTS FOR (t:ThreatIntel) REQUIRE t.id IS UNIQUE
    CREATE CONSTRAINT tactic_id_unique IF NOT EXISTS FOR (t:MitreTactic) REQUIRE t.id IS UNIQUE
    CREATE CONSTRAINT technique_id_unique IF NOT EXISTS FOR (t:MitreTechnique) REQUIRE t.id IS UNIQUE
    
    # Indexes
    CREATE INDEX cve_severity_idx IF NOT EXISTS FOR (c:CVE) ON (c.severity)
    CREATE INDEX cve_cvss_idx IF NOT EXISTS FOR (c:CVE) ON (c.cvss_v3)
    CREATE INDEX threat_severity_idx IF NOT EXISTS FOR (t:ThreatIntel) ON (t.severity)
```

### Phase 2: Load CVEs from Redis (15 min)
```python
def load_cves_from_redis(self):
    """
    1. Get all cve:CVE-* keys (exclude :embedding)
    2. Load each hash
    3. Reconstruct as Pydantic CVE
    4. Convert to Neo4j properties
    5. Batch insert (1000 per batch)
    """
```

### Phase 3: Load Supporting Entities (10 min)
```python
def load_vendors(self, cves):
    """Extract unique vendors, create Vendor nodes"""
    
def load_products(self, cves):
    """Extract unique products, create Product nodes"""
    
def load_cwes(self, cves):
    """Extract unique CWEs, create CWE nodes"""
```

### Phase 4: CVE Relationships (10 min)
```python
def create_cve_relationships(self, cves, batch_size=1000):
    """
    Create:
    - (CVE)-[:AFFECTS]->(Product)
    - (Product)-[:MADE_BY]->(Vendor)
    - (CVE)-[:HAS_WEAKNESS]->(CWE)
    """
```

### Phase 5: Load ThreatIntel from Weaviate (15 min)
```python
def load_threat_intel_from_weaviate(self):
    """
    1. Query all ThreatIntel objects from Weaviate
    2. Create ThreatIntel nodes in Neo4j
    3. Create IOC nodes
    4. Return for relationship building
    """
```

### Phase 6: Load MITRE Framework (10 min)
```python
def load_mitre_framework(self, threat_intel_data):
    """
    1. Extract unique tactic IDs from threat data
    2. Create MitreTactic nodes
    3. Extract unique technique IDs
    4. Create MitreTechnique nodes
    5. Create (Technique)-[:PART_OF_TACTIC]->(Tactic)
    """
```

### Phase 7: ThreatIntel Relationships (15 min)
```python
def create_threat_relationships(self, threat_intel_data, batch_size=1000):
    """
    Create:
    - (ThreatIntel)-[:REFERENCES]->(CVE)
    - (ThreatIntel)-[:TARGETS]->(Product)
    - (ThreatIntel)-[:USES_TECHNIQUE]->(MitreTechnique)
    - (ThreatIntel)-[:USES_TACTIC]->(MitreTactic)
    - (ThreatIntel)-[:HAS_IOC]->(IOC)
    """
```

### Phase 8: Verification & Stats (5 min)
```python
def verify_and_report(self):
    """
    Query Neo4j for:
    - Node counts by type
    - Relationship counts by type
    - Top 10 vendors by CVE count
    - Top 10 CWEs
    - ThreatIntel with most CVE references
    - Sample graph queries
    """
```

---

## CODE PATTERNS TO FOLLOW

### Pattern 1: Batch Loading
```python
def load_nodes_batch(self, nodes, node_type, batch_size=1000):
    """Generic batch loader"""
    with self.neo4j.session() as session:
        for i in tqdm(range(0, len(nodes), batch_size), desc=f"  {node_type}"):
            batch = nodes[i:i+batch_size]
            session.run(f"""
                UNWIND $nodes AS node
                MERGE (n:{node_type} {{id: node.id}})
                SET n = node
            """, nodes=batch)
```

### Pattern 2: Redis Hash to Dict
```python
def redis_hash_to_dict(self, redis_data):
    """Convert Redis hash to Python dict with proper types"""
    return {
        'cve_id': redis_data.get('id'),
        'description': redis_data.get('description'),
        'cvss_v3_score': float(redis_data.get('cvss_v3', 0)) if redis_data.get('cvss_v3') else None,
        'cvss_v2_score': float(redis_data.get('cvss_v2', 0)) if redis_data.get('cvss_v2') else None,
        'severity': redis_data.get('severity'),
        'published': redis_data.get('published'),
        'modified': redis_data.get('modified'),
        'affected_vendors': [v.strip() for v in redis_data.get('vendors', '').split(',') if v.strip()],
        'affected_products': [p.strip() for p in redis_data.get('products', '').split(',') if p.strip()],
        'cwes': [c.strip() for c in redis_data.get('cwes', '').split(',') if c.strip()],
        'references': [r.strip() for r in redis_data.get('references', '').split(',') if r.strip()],
        'source': redis_data.get('source', 'NVD')
    }
```

### Pattern 3: Progress Tracking
```python
from tqdm import tqdm
import time

start = time.time()
# do work
elapsed = time.time() - start
logger.info(f"✅ Completed in {elapsed/60:.1f} minutes")
```

---

## ERROR HANDLING

```python
# Be resilient
try:
    cve = CVE(**data)
except Exception as e:
    logger.warning(f"Failed to validate {data.get('id')}: {e}")
    continue
```

---

## EXPECTED OUTPUT

```
================================================================================
⚓ UNIFIED THREAT INTELLIGENCE GRAPH - RICKOVER STANDARD
================================================================================
✅ All systems connected

📊 PHASE 1: Loading CVEs from Redis...
  Found 316,552 CVE keys
  Loading from Redis: 100%|██████████| 316552/316552 [01:00<00:00, 5295/s]
  ✅ Loaded 316,552 CVEs
  
💾 Creating CVE nodes...
  CVE nodes: 100%|██████████| 317/317 [15:23<00:00, 2.21s/it]
  ✅ 316,552 CVE nodes created

🏢 Loading Vendors...
  ✅ 35,102 unique vendors
  
📦 Loading Products...
  ✅ 87,445 unique products
  
🔍 Loading CWEs...
  ✅ 744 CWEs loaded
  
🔗 Creating CVE relationships...
  AFFECTS: 100%|██████████| 317/317 [05:12<00:00]
  MADE_BY: 100%|██████████| 317/317 [03:45<00:00]
  HAS_WEAKNESS: 100%|██████████| 317/317 [02:30<00:00]
  ✅ All CVE relationships created

🔍 PHASE 2: Loading ThreatIntel from Weaviate...
  ✅ Loaded 12,447 ThreatIntel objects
  ✅ Created 8,923 IOC nodes
  
⚔️  PHASE 3: Building MITRE ATT&CK framework...
  ✅ Created 14 tactic nodes
  ✅ Created 187 technique nodes
  ✅ Created tactic-technique relationships
  
🔗 PHASE 4: Creating ThreatIntel relationships...
  REFERENCES: 100%|██████████| 125/125 [02:15<00:00]
  USES_TECHNIQUE: 100%|██████████| 125/125 [01:30<00:00]
  ✅ All threat relationships created

📊 FINAL STATISTICS
================================================================================
Nodes:
  CVEs:              316,552
  Vendors:            35,102
  Products:           87,445
  CWEs:                  744
  ThreatIntel:        12,447
  IOCs:                8,923
  MitreTactics:           14
  MitreTechniques:       187
  TOTAL:             461,414

Relationships:
  AFFECTS:           892,334
  MADE_BY:           187,221
  HAS_WEAKNESS:      243,745
  REFERENCES:         28,992
  USES_TECHNIQUE:     45,223
  USES_TACTIC:        38,441
  HAS_IOC:            22,334
  TOTAL:           1,458,290

✅ COMPLETE in 74.3 minutes
================================================================================
```

---

## SUCCESS CRITERIA

1. ✅ All 316,552 CVEs loaded
2. ✅ Complete graph schema (8 node types, 7+ relationship types)
3. ✅ ThreatIntel integrated from Weaviate
4. ✅ MITRE ATT&CK framework present
5. ✅ No data loss
6. ✅ All relationships correct
7. ✅ Verification queries pass
8. ✅ Total time < 90 minutes

---

## NOTES

- Use `tqdm` for all progress bars
- Log everything with `logger.info()`
- Batch size: 1000 for most operations
- Handle errors gracefully (log and continue)
- Close connections properly
- Follow Pydantic patterns from existing code

---

**RICKOVER STANDARD: No shortcuts. Do it right. Do it once.** ⚓
