# 🚀 CVE Knowledge Graph Bootstrap

**Purpose:** Import all 200,000+ CVEs from NIST NVD into Neo4j to establish "critical mass" for correlation and pattern detection.

---

## 🎯 Why This Matters

**Current Problem:**
- Only collecting ~100 recent CVEs per run
- No historical context
- Neo4j can't make meaningful correlations with sparse data

**After Bootstrap:**
- **200,000+ CVEs** (1999-2024+)
- **Vendor/Product relationships** (50,000+ products)
- **CWE mappings** (800+ weakness types)
- **Similarity relationships** between CVEs
- **Critical mass** for ML and correlation analysis

---

## 📊 What You'll Get

### **Nodes:**
- **CVEs:** 200,000+ vulnerability records
  - Full CVSS v2/v3 scores
  - Descriptions, dates, severity
  - Exploitability and impact scores
  
- **Vendors:** 10,000+ affected vendors
  - Microsoft, Google, Apple, Adobe, etc.
  
- **Products:** 50,000+ affected products
  - Windows, Linux, Chrome, etc.
  
- **CWEs:** 800+ weakness types
  - CWE-79 (XSS), CWE-89 (SQL Injection), etc.

### **Relationships:**
- **(CVE)-[:AFFECTS]->(Product)** - Which CVEs affect which products
- **(Product)-[:MADE_BY]->(Vendor)** - Product ownership
- **(CVE)-[:HAS_WEAKNESS]->(CWE)** - Weakness classification
- **(CVE)-[:SIMILAR_WEAKNESS]->(CVE)** - CVEs with same CWE
- **(CVE)-[:SIMILAR_TARGET]->(CVE)** - CVEs affecting same product

### **Query Power:**
```cypher
// Find all critical CVEs affecting Microsoft products
MATCH (c:CVE)-[:AFFECTS]->(p:Product)-[:MADE_BY]->(v:Vendor {name: 'microsoft'})
WHERE c.cvss_v3_score >= 9.0
RETURN c, p

// Find CVEs similar to a specific vulnerability
MATCH (c1:CVE {id: 'CVE-2024-1234'})-[:SIMILAR_WEAKNESS|SIMILAR_TARGET]-(c2:CVE)
RETURN c2

// Track vendor vulnerability patterns over time
MATCH (v:Vendor {name: 'adobe'})<-[:MADE_BY]-(p:Product)<-[:AFFECTS]-(c:CVE)
WHERE c.published.year = 2024
RETURN c.published.month, count(c) as cve_count
ORDER BY c.published.month
```

---

## 🚀 Execution Steps

### **Step 1: Download All CVE Data**

```bash
cd /home/david/projects/cyber-pi

# Run CVE bulk download (downloads ~23 years of data)
.venv/bin/python3 src/bootstrap/cve_bulk_import.py
```

**What It Does:**
- Downloads yearly CVE feeds from NIST NVD (2002-2024+)
- Each year = 1 gzipped JSON file (~50-100 MB)
- Total download: ~2-3 GB
- Duration: 5-10 minutes (depends on network)

**Output:**
- `data/cve_import/nvdcve-1.1-2024.json.gz`
- `data/cve_import/nvdcve-1.1-2023.json.gz`
- `data/cve_import/nvdcve-1.1-2022.json.gz`
- ... (one file per year)
- `data/cve_import/all_cves_neo4j.json` (consolidated, ~500 MB)

**Expected Stats:**
```
Total CVEs: ~200,000
Critical (CVSS 9.0+): ~20,000 (10%)
High (CVSS 7.0-8.9): ~40,000 (20%)
Medium (CVSS 4.0-6.9): ~100,000 (50%)
Low (CVSS 0.1-3.9): ~40,000 (20%)

Affected Vendors: ~10,000
Affected Products: ~50,000
Unique CWEs: ~800
Total References: ~600,000
```

---

### **Step 2: Load into Neo4j**

**Prerequisites:**
1. Neo4j running (check `neo4j status`)
2. Update Neo4j password in `neo4j_cve_loader.py`

```bash
# Load CVEs into Neo4j knowledge graph
.venv/bin/python3 src/bootstrap/neo4j_cve_loader.py
```

**What It Does:**
- Creates indexes for fast lookups (CVE ID, Vendor, Product, CWE)
- Loads 200,000+ CVE nodes (batches of 1,000)
- Creates vendor and product nodes
- Establishes relationships (AFFECTS, MADE_BY, HAS_WEAKNESS)
- Creates similarity links between CVEs
- Duration: 30-60 minutes

**Progress:**
```
1️⃣  Loading CVE nodes... [=========>] 200 batches
2️⃣  Loading Vendor nodes... [=========>] 200 batches
3️⃣  Loading Products and relationships... [=========>] 200 batches
4️⃣  Loading CWEs and weakness relationships... [=========>] 200 batches
5️⃣  Creating CVE similarity relationships... ✓
```

**Final Stats:**
```
Nodes:
  CVEs:     200,000
  Vendors:  10,000
  Products: 50,000
  CWEs:     800
  TOTAL:    260,800

Relationships:
  AFFECTS:       250,000+
  HAS_WEAKNESS:  150,000+
  MADE_BY:       50,000+
  SIMILAR_*:     500,000+
```

---

## 🔍 Example Queries After Bootstrap

### **1. Find Most Vulnerable Vendors**
```cypher
MATCH (v:Vendor)<-[:MADE_BY]-(p:Product)<-[:AFFECTS]-(c:CVE)
WHERE c.cvss_v3_score >= 7.0
RETURN v.name as vendor, 
       count(DISTINCT c) as high_severity_cves,
       count(DISTINCT p) as affected_products
ORDER BY high_severity_cves DESC
LIMIT 20
```

### **2. Track Vulnerability Trends Over Time**
```cypher
MATCH (c:CVE)
WHERE c.published.year >= 2020
RETURN c.published.year as year,
       c.published.month as month,
       c.cvss_v3_severity as severity,
       count(c) as cve_count
ORDER BY year, month, severity
```

### **3. Find Related Vulnerabilities**
```cypher
// Given a CVE, find similar ones for correlation
MATCH (c1:CVE {id: 'CVE-2024-1234'})
MATCH (c1)-[:HAS_WEAKNESS]->(w:CWE)<-[:HAS_WEAKNESS]-(c2:CVE)
MATCH (c2)-[:AFFECTS]->(p:Product)
RETURN c2.id, c2.description, w.id as common_weakness, p.name
LIMIT 10
```

### **4. Identify Exploit Chains**
```cypher
// Find CVEs that could be chained together
MATCH path = (c1:CVE)-[:AFFECTS]->(p:Product)<-[:AFFECTS]-(c2:CVE)
WHERE c1.id <> c2.id
  AND c1.cvss_v3_score >= 7.0
  AND c2.cvss_v3_score >= 7.0
RETURN c1.id, c2.id, p.name, c1.cvss_v3_score, c2.cvss_v3_score
LIMIT 50
```

### **5. Weakness Pattern Analysis**
```cypher
// Which CWEs are most common?
MATCH (w:CWE)<-[:HAS_WEAKNESS]-(c:CVE)
RETURN w.id as weakness_type,
       count(c) as cve_count,
       avg(c.cvss_v3_score) as avg_severity
ORDER BY cve_count DESC
LIMIT 20
```

---

## 💡 Use Cases Enabled

### **1. ML Training Data**
- 200K+ labeled vulnerabilities
- CVSS scores for severity prediction
- CWE classifications for weakness categorization
- Temporal data for trend analysis

### **2. Threat Intelligence Correlation**
- Link real-time CVE feeds to historical patterns
- Identify vendor-specific vulnerability trends
- Predict exploitation likelihood based on similar CVEs
- Track attacker TTPs via CWE patterns

### **3. Risk Assessment**
- "What CVEs affect our technology stack?"
- "Which vendors have the worst security track record?"
- "What are the most exploited CWE types?"
- "Are there similar CVEs to this new disclosure?"

### **4. Automated Attribution**
- Link threat actors to preferred CWE types
- Correlate exploited CVEs with APT campaigns
- Build vendor risk profiles
- Predict next likely targets

---

## 📁 File Structure

```
src/bootstrap/
├── cve_bulk_import.py       # Download all CVEs from NIST NVD
├── neo4j_cve_loader.py       # Load CVEs into Neo4j graph
└── README.md                 # This file

data/cve_import/
├── nvdcve-1.1-2024.json.gz   # Yearly feeds (downloaded)
├── nvdcve-1.1-2023.json.gz
├── ...
└── all_cves_neo4j.json       # Consolidated CVEs (500 MB)
```

---

## ⚙️ Configuration

**Neo4j Connection:**
Edit `neo4j_cve_loader.py`:
```python
loader = Neo4jCVELoader(
    uri="bolt://localhost:7687",  # Your Neo4j URI
    user="neo4j",                  # Your username
    password="your_password"       # Your password
)
```

**Or use environment variables:**
```bash
export NEO4J_URI="bolt://localhost:7687"
export NEO4J_USER="neo4j"
export NEO4J_PASSWORD="your_password"
```

---

## 🎯 Success Criteria

After running both scripts, verify:

```cypher
// Check node counts
MATCH (c:CVE) RETURN count(c) as cves;        // Should be ~200,000
MATCH (v:Vendor) RETURN count(v) as vendors;  // Should be ~10,000
MATCH (p:Product) RETURN count(p) as products;// Should be ~50,000
MATCH (w:CWE) RETURN count(w) as cwes;        // Should be ~800

// Check relationships
MATCH ()-[r:AFFECTS]->() RETURN count(r);      // Should be ~250,000+
MATCH ()-[r:HAS_WEAKNESS]->() RETURN count(r); // Should be ~150,000+

// Test a query
MATCH (c:CVE {id: 'CVE-2024-1234'}) RETURN c;  // Should return data
```

---

## 🚨 Troubleshooting

**Download fails:**
- Check network connectivity to nvd.nist.gov
- NIST sometimes rate-limits; script handles retries
- Can resume - skips already downloaded files

**Neo4j out of memory:**
- Increase heap size in neo4j.conf: `dbms.memory.heap.max_size=8G`
- Reduce batch_size in loader (default 1000 → try 500)

**Slow loading:**
- Normal for 200K CVEs (30-60 minutes)
- Check Neo4j query performance with `PROFILE` command
- Ensure indexes are created (Step 1 of loader)

---

## 📊 Monitoring Progress

**During Download:**
```bash
ls -lh data/cve_import/*.gz | wc -l  # Number of downloaded years
```

**During Neo4j Load:**
```cypher
// Real-time node count
MATCH (c:CVE) RETURN count(c);
```

**Check Logs:**
```bash
# Download progress
tail -f data/cve_import/download.log

# Neo4j load progress
tail -f data/cve_import/neo4j_load.log
```

---

## 🎓 Next Steps After Bootstrap

1. **Run current collection:** Now CVEs from hourly collection will correlate with 200K historical CVEs
2. **ML Training:** Use graph embeddings for CVE similarity
3. **Risk Scoring:** Build vendor risk scores based on historical patterns
4. **Threat Hunting:** Query for exploitation patterns
5. **Auto-Attribution:** Link incoming CVEs to likely threat actors based on CWE preferences

---

**Estimated Total Time:**
- Download: 5-10 minutes
- Processing: 2-5 minutes  
- Neo4j Load: 30-60 minutes
- **Total: ~1 hour**

**Disk Space Required:**
- Raw downloads: ~3 GB
- Processed JSON: ~500 MB
- Neo4j database: ~5-10 GB

---

*Bootstrap the knowledge graph once, get intelligence forever* 🚀
