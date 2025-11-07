# 📊 Unified Threat Graph Visualizations

## 🔗 Access Neo4j Browser

To view these visualizations:

1. Access Neo4j Browser at: http://10.152.183.169:7474/
2. Login with:
   - Username: `neo4j`
   - Password: `cyber-pi-neo4j-2025`
3. Copy and paste any of the Cypher queries below into the command bar at the top

## 🌐 Visualization 1: ThreatIntel to CVE to CWE Chain
```cypher
// Shows how threat intelligence connects to CVEs and their weaknesses
MATCH path = (t:ThreatIntel)-[:REFERENCES]->(c:CVE)-[:HAS_WEAKNESS]->(w:CWE)
WHERE t.id IN ['mock-threat-1', 'mock-threat-2', 'mock-threat-3', 'mock-threat-4']
RETURN path
LIMIT 20
```

## ⚔️ Visualization 2: MITRE ATT&CK Framework Usage
```cypher
// Shows which threat intel uses which MITRE tactics
MATCH path = (t:ThreatIntel)-[:USES_TACTIC]->(m:MitreTactic)
WHERE m.id IN ['TA0001', 'TA0002', 'TA0003', 'TA0004', 'TA0005']
RETURN path
LIMIT 15
```

## 🏢 Visualization 3: Vendor Attack Surface
```cypher
// Shows Microsoft products and their CVEs
MATCH (v:Vendor {name: 'microsoft'})<-[:MADE_BY]-(p:Product)<-[:AFFECTS]-(c:CVE)
WITH p, v, collect(c)[0..5] as cves
MATCH path = (v)<-[:MADE_BY]-(p)<-[:AFFECTS]-(c)
WHERE c IN cves
RETURN path
LIMIT 30
```

## 🔄 Visualization 4: Complete Threat Intelligence Chain
```cypher
// Shows the complete chain from ThreatIntel to MITRE to CVEs to Products
MATCH tacticPath = (t:ThreatIntel)-[:USES_TACTIC]->(m:MitreTactic)
WHERE t.id IN ['mock-threat-1', 'mock-threat-4']
WITH t, collect(tacticPath) as tacticPaths
MATCH vulnPath = (t)-[:REFERENCES]->(c:CVE)-[:AFFECTS]->(p:Product)
RETURN tacticPaths, collect(vulnPath)
LIMIT 20
```

## 🔍 Visualization 5: Critical Weakness Types
```cypher
// Shows the most common weakness types
MATCH (c:CVE)-[:HAS_WEAKNESS]->(w:CWE)
WITH w, count(c) as cve_count
ORDER BY cve_count DESC
LIMIT 5
MATCH path = (c:CVE)-[:HAS_WEAKNESS]->(w)
RETURN path
LIMIT 25
```

## 📈 Visualization 6: Vendor CVE Distribution
```cypher
// Shows the top vendors by CVE count
MATCH (v:Vendor)<-[:MADE_BY]-(p:Product)<-[:AFFECTS]-(c:CVE)
WITH v, count(DISTINCT c) as cve_count
ORDER BY cve_count DESC
LIMIT 10
RETURN v.name as vendor, cve_count
```

## 🔗 Visualization 7: Product Relationships
```cypher
// Shows products affected by the same CVEs
MATCH (c:CVE)-[:AFFECTS]->(p1:Product)
MATCH (c)-[:AFFECTS]->(p2:Product)
WHERE p1 <> p2
WITH p1, p2, count(c) as shared_cves
WHERE shared_cves > 1000
RETURN p1.name as product1, p2.name as product2, shared_cves
ORDER BY shared_cves DESC
LIMIT 10
```

## 🔥 Visualization 8: Critical CVEs with Threat Intel
```cypher
// Shows critical CVEs that have threat intelligence
MATCH (t:ThreatIntel)-[:REFERENCES]->(c:CVE)
WHERE t.severity = 'critical'
WITH c, collect(t) as threats
MATCH path = (t)-[:REFERENCES]->(c)-[:HAS_WEAKNESS]->(w:CWE)
WHERE t IN threats
RETURN path
LIMIT 20
```
