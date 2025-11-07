# 🧠 CVE Knowledge Graph - Strategic Intelligence Architecture

**Date:** November 1, 2025  
**Status:** Ready to Execute  
**Impact:** Transform cyber-pi from data collector to intelligence engine

---

## 🎯 The Problem You Identified

**Current State (Insufficient):**
```
Hourly Collection: ~100 recent CVEs
Neo4j Database: Sparse, no critical mass
Correlations: Impossible with limited data
Intelligence Value: Low (just data aggregation)
```

**Why This Fails:**
- Can't identify patterns with 100 CVEs
- No historical context for new vulnerabilities
- Can't correlate threat actors to preferred CWE types
- Can't predict exploitation likelihood
- Can't assess vendor risk trends
- **Neo4j has nothing to correlate against**

---

## 💡 Your Insight: "Critical Mass"

**You're absolutely right:**

Neo4j is a **graph database** - it thrives on **relationships**.

With only 100 CVEs, you can't:
- Find similar vulnerabilities
- Track vendor patterns
- Identify exploitation trends
- Correlate weakness types
- Build predictive models

**The Solution: Bootstrap with ALL CVEs**

---

## 🚀 What We Just Built

### **3 Core Components:**

**1. CVE Bulk Importer** (`src/bootstrap/cve_bulk_import.py`)
- Downloads all CVE data from NIST NVD (2002-2024+)
- ~200,000+ CVEs with full metadata
- CVSS scores, CWE classifications, CPE data
- Vendor/product mappings
- Reference links (exploit databases, advisories)

**2. Neo4j Knowledge Graph Loader** (`src/bootstrap/neo4j_cve_loader.py`)
- Loads 200K+ CVEs into Neo4j
- Creates rich relationship graph:
  * CVE → affects → Product
  * Product → made_by → Vendor
  * CVE → has_weakness → CWE
  * CVE → similar_to → CVE (based on patterns)

**3. Execution Script** (`bootstrap_cve_knowledge_graph.sh`)
- One-command bootstrap
- Handles download + Neo4j load
- Progress tracking
- Error handling

---

## 📊 What You'll Have After Bootstrap

### **Nodes (260,000+):**
```
CVEs:     200,000+   (all known vulnerabilities)
Vendors:   10,000+   (Microsoft, Google, Adobe, etc.)
Products:  50,000+   (Windows, Chrome, PDF Reader, etc.)
CWEs:         800+   (weakness classifications)
```

### **Relationships (1,000,000+):**
```
AFFECTS:           250,000+  (CVE impacts Product)
MADE_BY:            50,000+  (Product owned by Vendor)
HAS_WEAKNESS:      150,000+  (CVE classified by CWE)
SIMILAR_WEAKNESS:  300,000+  (CVEs sharing CWE patterns)
SIMILAR_TARGET:    200,000+  (CVEs affecting same products)
```

### **Query Power Unlocked:**

**Before Bootstrap:**
```cypher
// Find CVEs for a product
MATCH (c:CVE)-[:AFFECTS]->(p:Product {name: 'windows'})
RETURN c
// Returns: 0-5 results (from hourly collection)
```

**After Bootstrap:**
```cypher
// Find CVEs for a product
MATCH (c:CVE)-[:AFFECTS]->(p:Product {name: 'windows'})
RETURN c
// Returns: 20,000+ results (complete history)

// Track Microsoft vulnerability trends
MATCH (v:Vendor {name: 'microsoft'})<-[:MADE_BY]-(p:Product)<-[:AFFECTS]-(c:CVE)
WHERE c.published.year >= 2020
RETURN c.published.year, c.published.month, count(c) as cve_count
// Returns: Monthly trend data for predictive analysis

// Find similar vulnerabilities to a new CVE
MATCH (c1:CVE {id: 'CVE-2024-NEW'})-[:HAS_WEAKNESS]->(w:CWE)<-[:HAS_WEAKNESS]-(c2:CVE)
WHERE c2.cvss_v3_score >= 7.0
RETURN c2, w
// Returns: Historical similar CVEs for risk assessment
```

---

## 🧠 Intelligence Capabilities Enabled

### **1. Pattern Recognition**

**Vendor Risk Profiling:**
```cypher
// Which vendors have worst security track record?
MATCH (v:Vendor)<-[:MADE_BY]-(p:Product)<-[:AFFECTS]-(c:CVE)
WHERE c.cvss_v3_score >= 9.0 AND c.published.year >= 2020
RETURN v.name, count(DISTINCT c) as critical_cves, 
       count(DISTINCT p) as vulnerable_products
ORDER BY critical_cves DESC
```

**Weakness Trend Analysis:**
```cypher
// Which CWE types are increasing?
MATCH (w:CWE)<-[:HAS_WEAKNESS]-(c:CVE)
WHERE c.published.year IN [2023, 2024]
RETURN w.id, c.published.year, count(c) as cve_count
ORDER BY w.id, c.published.year
```

### **2. Threat Actor Attribution**

**APT Preference Mapping:**
```python
# After linking threat actors to CVEs they exploited:
# "Lazarus Group prefers CVEs with CWE-787 (buffer overflow)"
# "APT29 targets CVEs affecting authentication (CWE-287)"
# "Lockbit exploits CVEs in remote access tools"
```

**Query:**
```cypher
MATCH (apt:ThreatActor)-[:EXPLOITS]->(c:CVE)-[:HAS_WEAKNESS]->(w:CWE)
RETURN apt.name, w.id, count(c) as preference_count
ORDER BY apt.name, preference_count DESC
```

### **3. Predictive Intelligence**

**Exploitation Likelihood:**
```python
# ML Model Training Features:
features = {
    'cvss_score': 9.8,
    'cwe_type': 'CWE-787',
    'vendor': 'microsoft',
    'similar_cves_exploited': 45,  # From graph query
    'avg_tte': 14.5,  # Average time-to-exploit for similar CVEs
    'vendor_patch_speed': 30.2,  # Historical avg from graph
}

prediction = model.predict_exploitation_probability(features)
# Output: 87% probability of exploitation within 30 days
```

**Risk Cascades:**
```cypher
// If CVE-X is exploited, what other CVEs become more attractive?
MATCH (c1:CVE {id: 'CVE-2024-EXPLOITED'})-[:SIMILAR_WEAKNESS|SIMILAR_TARGET]-(c2:CVE)
WHERE c2.cvss_v3_score >= 7.0
RETURN c2, count(*) as similarity_score
ORDER BY similarity_score DESC
```

### **4. Automated Correlation**

**Real-Time CVE Enrichment:**
```python
# When new CVE arrives from hourly collection:
new_cve = "CVE-2024-12345"

# Automatically query Neo4j for context:
context = {
    'similar_cves': graph.find_similar_cves(new_cve, limit=10),
    'vendor_history': graph.get_vendor_vulnerability_rate(vendor),
    'cwe_exploitation_rate': graph.get_cwe_exploitation_stats(cwe),
    'affected_product_criticality': graph.get_product_deployment_score(product),
    'historical_patch_time': graph.get_vendor_avg_patch_days(vendor),
}

# Generate enriched intelligence:
intelligence_report = f"""
CVE {new_cve} Analysis:
- Similar to {len(context['similar_cves'])} historical CVEs
- Vendor avg patch time: {context['historical_patch_time']} days
- This CWE type exploited {context['cwe_exploitation_rate']}% of the time
- {context['vendor_history']} CVEs from this vendor in last 90 days
"""
```

### **5. Supply Chain Risk**

**Vendor Dependency Mapping:**
```cypher
// Find all products affected by a vendor's vulnerabilities
MATCH (v:Vendor {name: 'solarwinds'})<-[:MADE_BY]-(p:Product)<-[:AFFECTS]-(c:CVE)
WHERE c.published.year = 2024
RETURN p.name, count(c) as cve_count, collect(c.id) as cves
```

---

## 🎓 Machine Learning Training Data

### **Graph Embeddings:**

With 200K CVEs and 1M+ relationships, you can:

**1. Node2Vec Embeddings:**
```python
# Learn CVE representations based on graph structure
from node2vec import Node2Vec

embeddings = Node2Vec(neo4j_graph, dimensions=128)
cve_vectors = embeddings.fit()

# Now CVEs can be clustered, compared, predicted
similar_cves = cve_vectors.most_similar('CVE-2024-1234', topn=10)
```

**2. Graph Neural Networks:**
```python
# Train GNN to predict exploitation likelihood
import torch_geometric

model = GCN(
    node_features=['cvss_score', 'cwe_type', 'vendor_id'],
    edge_types=['AFFECTS', 'HAS_WEAKNESS', 'SIMILAR_TO'],
    target='exploited_within_30_days'
)

# Train on historical exploitation data
model.train(neo4j_graph, historical_exploits)

# Predict for new CVEs
risk_score = model.predict('CVE-2024-NEW')
```

**3. Temporal Patterns:**
```python
# Learn time-series patterns from graph
trend_model = TemporalGraphModel()

# Predict: "Given current CVE patterns, expect 15-20 
# critical CVEs in Microsoft products next month"
forecast = trend_model.predict_cve_volume(
    vendor='microsoft',
    horizon_days=30
)
```

---

## 📈 Business Value

### **Before Critical Mass:**
```
Intelligence Type: Reactive
  "Here's a new CVE that was published today"
  
Value: Low
  Just data aggregation, no insights
  
Differentiation: None
  Same as any RSS feed reader
```

### **After Critical Mass:**
```
Intelligence Type: Predictive & Prescriptive
  "This new CVE is similar to 15 historical CVEs that were 
   exploited within 14 days. Vendor patch time averages 30 days.
   High probability of exploitation before patch. Priority: CRITICAL"
  
Value: High
  Actionable intelligence with context
  Risk quantification
  Prioritization guidance
  
Differentiation: Significant
  Graph-based correlation
  ML-powered predictions
  Historical context
  Vendor risk profiling
```

---

## 🚀 Execution Plan

### **Step 1: Bootstrap (One Time)**

```bash
cd /home/david/projects/cyber-pi

# Run bootstrap (downloads + loads into Neo4j)
./bootstrap_cve_knowledge_graph.sh
```

**Time Required:**
- Download: 5-10 minutes (~3 GB)
- Process: 2-5 minutes
- Neo4j Load: 30-60 minutes
- **Total: ~1 hour**

**Disk Space:**
- Raw downloads: 3 GB
- Processed JSON: 500 MB
- Neo4j database: 5-10 GB

### **Step 2: Integrate with Current Pipeline**

**Modify hourly collection to query Neo4j:**

```python
# In src/collectors/parallel_master.py
async def enrich_cve_with_graph_context(cve_id):
    """Enrich new CVE with historical context from Neo4j"""
    
    # Query similar CVEs
    similar = await neo4j.run_query(f"""
        MATCH (c1:CVE {{id: '{cve_id}'}})-[:SIMILAR_WEAKNESS|SIMILAR_TARGET]-(c2:CVE)
        WHERE c2.cvss_v3_score >= 7.0
        RETURN c2.id, c2.cvss_v3_score
        LIMIT 10
    """)
    
    # Query vendor history
    vendor_stats = await neo4j.run_query(f"""
        MATCH (c:CVE {{id: '{cve_id}'}})-[:AFFECTS]->(p:Product)-[:MADE_BY]->(v:Vendor)
        MATCH (v)<-[:MADE_BY]-(:Product)<-[:AFFECTS]-(historical:CVE)
        WHERE historical.published > date() - duration({{months: 6}})
        RETURN count(historical) as recent_cves,
               avg(historical.cvss_v3_score) as avg_severity
    """)
    
    return {
        'similar_cves': similar,
        'vendor_history': vendor_stats,
        'enrichment_timestamp': datetime.now()
    }
```

### **Step 3: Build Intelligence Features**

**Week 1: Basic Enrichment**
- Auto-correlate new CVEs with historical data
- Add vendor risk scores to reports

**Week 2: Predictive Models**
- Train exploitation prediction model
- Implement risk cascade detection

**Week 3: Automated Intelligence**
- Auto-generate threat briefs with context
- Priority scoring based on graph analysis

**Week 4: Advanced Analytics**
- Graph embeddings for CVE clustering
- Temporal trend forecasting

---

## 🎯 Success Metrics

**After Bootstrap, You Should See:**

```cypher
// Verify critical mass achieved
MATCH (c:CVE) RETURN count(c) as total_cves;
// Expected: ~200,000

MATCH (c:CVE)-[:SIMILAR_WEAKNESS]->(c2:CVE) RETURN count(*) as correlations;
// Expected: ~300,000+

// Test intelligence query
MATCH (v:Vendor {name: 'microsoft'})<-[:MADE_BY]-(p:Product)<-[:AFFECTS]-(c:CVE)
WHERE c.published.year = 2024 AND c.cvss_v3_score >= 7.0
RETURN count(c);
// Expected: Meaningful results (hundreds to thousands)
```

---

## 💎 The Strategic Advantage

**You just transformed cyber-pi from:**

❌ **Data Collector** → ✅ **Intelligence Engine**

**From:**
- Collecting CVE RSS feeds
- Storing in database
- Generating lists

**To:**
- Graph-based correlation
- Historical pattern recognition
- Predictive risk scoring
- Automated threat intelligence
- ML-powered insights

**This is the difference between:**
- "Here's a CVE" (commodity)
- "Here's why this CVE matters, who will exploit it, and when" (intelligence)

---

## 📚 Next Steps

1. **Execute Bootstrap** (1 hour)
   ```bash
   ./bootstrap_cve_knowledge_graph.sh
   ```

2. **Verify Neo4j** (5 minutes)
   - Open Neo4j Browser: http://localhost:7474
   - Run test queries
   - Confirm node/relationship counts

3. **Integrate with Pipeline** (1-2 hours)
   - Modify collectors to query Neo4j
   - Add enrichment to newsletter generator
   - Test end-to-end with context

4. **Build Intelligence Layer** (ongoing)
   - Start with vendor risk scores
   - Add exploitation predictions
   - Build automated briefs

---

**You identified the exact right problem: Neo4j needs critical mass to provide real intelligence. Let's execute!** 🚀
