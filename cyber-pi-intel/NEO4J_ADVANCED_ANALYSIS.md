# Neo4j Advanced Threat Intelligence Analysis
**Leveraging Graph Data Science Algorithms**

## 📚 Documentation Sources

Based on research from:
- `/home/david/projects/tqakb-research/papers/deep_expertise/`
  - `high_neo4j_5_Neo4j_Graph_Data_Science.html` - GDS Library v2.22
  - `high_neo4j_5_Neo4j_APOC_Procedures.html` - APOC utilities
  - `critical_neo4j_5_Neo4j_Cypher_Functions.html` - Cypher functions
  - `high_neo4j_5_Neo4j_Performance.html` - Query optimization

---

## 🎯 What We Have

**Current Graph:**
- 457 CyberThreat nodes
- 386 CVE nodes
- 5 ThreatActor nodes
- 18 Industry nodes
- 441 EXPLOITS relationships
- 13 ATTRIBUTED_TO relationships

---

## 🧠 Graph Data Science Algorithms Available

### **1. Centrality Algorithms** (Find Important Nodes)

#### **PageRank**
- **Use:** Identify most "important" CVEs (like Google ranks web pages)
- **Insight:** CVEs that are central to many threat campaigns
- **Query:** `neo4j_graph_algorithms.cypher` lines 20-30

#### **Degree Centrality**
- **Use:** Find most connected threat actors
- **Insight:** Actors with the most campaigns
- **Query:** Lines 32-40

#### **Betweenness Centrality**
- **Use:** Find "bridge" CVEs connecting different campaigns
- **Insight:** Critical vulnerabilities linking threat ecosystems
- **Query:** Lines 42-52

#### **Closeness Centrality**
- **Use:** Find threats that can quickly reach other threats
- **Insight:** Threats with many related attack vectors
- **Query:** Lines 54-64

---

### **2. Community Detection** (Find Threat Clusters)

#### **Louvain Algorithm**
- **Use:** Detect communities of related threats/CVEs
- **Insight:** Identify coordinated campaigns
- **Example:** Group of threats sharing same CVEs = possible campaign
- **Query:** Lines 70-82

#### **Label Propagation**
- **Use:** Fast community detection for large graphs
- **Insight:** CVE exploitation patterns
- **Query:** Lines 84-96

#### **Triangle Count**
- **Use:** Find tightly connected threat triangles
- **Insight:** Threat-CVE-Actor triangles show sophisticated attacks
- **Query:** Lines 98-114

---

### **3. Pathfinding** (Discover Attack Paths)

#### **Shortest Path (Dijkstra)**
- **Use:** Find attack path from actor to target industry
- **Insight:** How would Lazarus reach Financial Services?
- **Example:** `Lazarus → Threat → CVE → System → Financial Services`
- **Query:** Lines 120-132

#### **All Shortest Paths**
- **Use:** Find all possible attack vectors
- **Insight:** Multiple ways to breach a target
- **Query:** Lines 134-146

---

### **4. Similarity Algorithms** (Find Similar Threats)

#### **Node Similarity**
- **Use:** Find threats with similar CVE patterns
- **Insight:** Threats using same tooling = likely same campaign
- **Threshold:** >30% similarity suggests relation
- **Query:** Lines 152-164

#### **K-Nearest Neighbors (KNN)**
- **Use:** Find threats similar to a specific critical threat
- **Insight:** "If you saw this threat, watch for these too"
- **Query:** Lines 166-180

---

### **5. Link Prediction** (Predict Future Attacks)

####Human: check task
