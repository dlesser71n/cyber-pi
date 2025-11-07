-- ============================================================
-- NEO4J GRAPH DATA SCIENCE ALGORITHMS
-- Advanced Threat Intelligence Analysis
-- Using Neo4j GDS Library v2.22
-- ============================================================

-- Based on: /home/david/projects/tqakb-research/papers/deep_expertise/
-- - high_neo4j_5_Neo4j_Graph_Data_Science.html
-- - high_neo4j_5_Neo4j_APOC_Procedures.html
-- - critical_neo4j_5_Neo4j_Cypher_Functions.html

-- ============================================================
-- 0. SETUP: Create Graph Projection for GDS Algorithms
-- ============================================================

-- Project threat intelligence graph into memory for analysis
CALL gds.graph.project(
  'threat-intel-graph',
  ['CyberThreat', 'ThreatActor', 'CVE', 'Industry'],
  {
    EXPLOITS: {orientation: 'UNDIRECTED'},
    ATTRIBUTED_TO: {orientation: 'UNDIRECTED'},
    TARGETS: {orientation: 'UNDIRECTED'}
  }
);

-- Check graph projection
CALL gds.graph.list() YIELD graphName, nodeCount, relationshipCount;

-- ============================================================
-- 1. CENTRALITY ALGORITHMS
-- Find most important threats, CVEs, and actors
-- ============================================================

-- PageRank: Find most "important" CVEs (like Google's PageRank)
CALL gds.pageRank.stream('threat-intel-graph')
YIELD nodeId, score
WITH gds.util.asNode(nodeId) AS node, score
WHERE node:CVE
RETURN 
  node.cveId AS cve,
  score AS importance,
  'High-value target for attackers' AS insight
ORDER BY score DESC
LIMIT 20;

-- Degree Centrality: Find most connected threat actors
CALL gds.degree.stream('threat-intel-graph')
YIELD nodeId, score
WITH gds.util.asNode(nodeId) AS node, score
WHERE node:ThreatActor
RETURN 
  node.actorName AS actor,
  score AS connections,
  'Active threat actor with many campaigns' AS insight
ORDER BY score DESC;

-- Betweenness Centrality: Find "bridge" CVEs connecting different threat campaigns
CALL gds.betweenness.stream('threat-intel-graph')
YIELD nodeId, score
WITH gds.util.asNode(nodeId) AS node, score
WHERE node:CVE AND score > 0
RETURN 
  node.cveId AS cve,
  score AS bridgeScore,
  'CVE connecting multiple threat campaigns' AS insight
ORDER BY score DESC
LIMIT 15;

-- Closeness Centrality: Find threats that can quickly reach other threats
CALL gds.closenessCentrality.stream('threat-intel-graph')
YIELD nodeId, score
WITH gds.util.asNode(nodeId) AS node, score
WHERE node:CyberThreat
RETURN 
  node.title AS threat,
  score AS reachability,
  'Threat with many related attack vectors' AS insight
ORDER BY score DESC
LIMIT 20;

-- ============================================================
-- 2. COMMUNITY DETECTION
-- Find clusters of related threats
-- ============================================================

-- Louvain: Detect communities of related threats/CVEs
CALL gds.louvain.stream('threat-intel-graph')
YIELD nodeId, communityId
WITH gds.util.asNode(nodeId) AS node, communityId
WHERE node:CyberThreat
WITH communityId, collect(node.title)[0..5] AS threats, count(node) AS size
WHERE size > 2
RETURN 
  communityId,
  size AS campaignSize,
  threats AS sampleThreats,
  'Related threat campaign cluster' AS insight
ORDER BY size DESC;

-- Label Propagation: Fast community detection
CALL gds.labelPropagation.stream('threat-intel-graph')
YIELD nodeId, communityId
WITH gds.util.asNode(nodeId) AS node, communityId
WHERE node:CVE
WITH communityId, collect(node.cveId)[0..10] AS cves, count(node) AS size
WHERE size > 3
RETURN 
  communityId,
  size AS vulnerabilityCluster,
  cves,
  'CVE exploitation pattern' AS insight
ORDER BY size DESC
LIMIT 10;

-- Triangle Count: Find tightly connected threat triangles
CALL gds.triangleCount.stream('threat-intel-graph')
YIELD nodeId, triangleCount
WITH gds.util.asNode(nodeId) AS node, triangleCount
WHERE triangleCount > 0
RETURN 
  CASE 
    WHEN node:CyberThreat THEN 'Threat'
    WHEN node:CVE THEN 'CVE'
    WHEN node:ThreatActor THEN 'Actor'
  END AS nodeType,
  COALESCE(node.title, node.cveId, node.actorName) AS name,
  triangleCount,
  'Part of tightly connected threat pattern' AS insight
ORDER BY triangleCount DESC
LIMIT 20;

-- ============================================================
-- 3. PATH FINDING
-- Discover attack paths and relationships
-- ============================================================

-- Shortest Path: From specific actor to industry
MATCH (source:ThreatActor {actorName: 'Lazarus'})
MATCH (target:Industry {industryName: 'Financial Services'})
CALL gds.shortestPath.dijkstra.stream('threat-intel-graph', {
  sourceNode: source,
  targetNode: target
})
YIELD index, sourceNode, targetNode, totalCost, nodeIds, costs, path
RETURN 
  [nodeId IN nodeIds | gds.util.asNode(nodeId).name] AS attackPath,
  totalCost AS pathCost,
  length(nodeIds) AS pathLength;

-- All Shortest Paths: Multiple attack vectors
MATCH (actor:ThreatActor)
MATCH (industry:Industry)
CALL gds.allShortestPaths.stream('threat-intel-graph', {
  sourceNode: actor,
  targetNode: industry
})
YIELD sourceNode, targetNode, distance
WHERE distance < 5
RETURN 
  gds.util.asNode(sourceNode).actorName AS actor,
  gds.util.asNode(targetNode).industryName AS industry,
  distance AS attackVectorDistance
ORDER BY distance
LIMIT 20;

-- ============================================================
-- 4. SIMILARITY ALGORITHMS
-- Find similar threats based on graph structure
-- ============================================================

-- Node Similarity: Find threats with similar CVE exploitation patterns
CALL gds.nodeSimilarity.stream('threat-intel-graph')
YIELD node1, node2, similarity
WITH gds.util.asNode(node1) AS t1, gds.util.asNode(node2) AS t2, similarity
WHERE t1:CyberThreat AND t2:CyberThreat AND similarity > 0.3
RETURN 
  t1.title AS threat1,
  t2.title AS threat2,
  similarity AS similarityScore,
  'Similar attack patterns - possibly same campaign' AS insight
ORDER BY similarity DESC
LIMIT 15;

-- K-Nearest Neighbors: Find threats similar to a specific one
MATCH (target:CyberThreat)
WHERE target.severity = 'critical'
WITH target LIMIT 1
CALL gds.knn.stream('threat-intel-graph', {
  nodeLabels: ['CyberThreat'],
  topK: 10,
  nodeProperties: ['similarity']
})
YIELD node1, node2, similarity
WHERE id(node1) = id(target)
WITH gds.util.asNode(node2) AS similar, similarity
RETURN 
  similar.title AS similarThreat,
  similar.severity AS severity,
  similarity AS similarityScore
ORDER BY similarity DESC;

-- ============================================================
-- 5. LINK PREDICTION
-- Predict potential future threat relationships
-- ============================================================

-- Adamic Adar: Predict which CVEs actor might exploit next
MATCH (actor:ThreatActor {actorName: 'Lazarus'})
CALL gds.alpha.linkprediction.adamicAdar.stream('threat-intel-graph', {
  sourceNode: actor,
  targetLabels: ['CVE']
})
YIELD node1, node2, score
WITH gds.util.asNode(node2) AS cve, score
WHERE NOT (actor)-[:EXPLOITS]->(cve)
RETURN 
  cve.cveId AS predictedTarget,
  score AS likelihood,
  'Potential next exploitation target' AS insight
ORDER BY score DESC
LIMIT 10;

-- Common Neighbors: Threats that might start using same CVEs
MATCH (t1:CyberThreat)-[:EXPLOITS]->(cve:CVE)<-[:EXPLOITS]-(t2:CyberThreat)
WHERE t1 <> t2
WITH t1, t2, count(cve) AS commonCVEs
WHERE commonCVEs > 1
RETURN 
  t1.title AS threat1,
  t2.title AS threat2,
  commonCVEs,
  'May share same threat actor or tooling' AS prediction
ORDER BY commonCVEs DESC
LIMIT 15;

-- ============================================================
-- 6. GRAPH TOPOLOGY
-- Analyze overall graph structure
-- ============================================================

-- Connected Components: Find isolated threat clusters
CALL gds.wcc.stream('threat-intel-graph')
YIELD nodeId, componentId
WITH gds.util.asNode(nodeId) AS node, componentId
WITH componentId, count(node) AS size, collect(DISTINCT labels(node)[0]) AS types
WHERE size > 5
RETURN 
  componentId,
  size AS clusterSize,
  types AS nodeTypes,
  'Connected threat ecosystem' AS insight
ORDER BY size DESC;

-- Graph Density: How interconnected is the threat landscape
CALL gds.graph.list('threat-intel-graph')
YIELD nodeCount, relationshipCount
WITH nodeCount, relationshipCount,
     toFloat(relationshipCount) / (nodeCount * (nodeCount - 1)) AS density
RETURN 
  nodeCount,
  relationshipCount,
  density,
  CASE 
    WHEN density > 0.5 THEN 'Highly interconnected threat landscape'
    WHEN density > 0.2 THEN 'Moderately connected threats'
    ELSE 'Sparse threat connections'
  END AS interpretation;

-- ============================================================
-- 7. TEMPORAL ANALYSIS WITH APOC
-- Time-based patterns using APOC procedures
-- ============================================================

-- Threats over time (requires APOC)
MATCH (threat:CyberThreat)
WHERE threat.publishedDate IS NOT NULL
WITH date(threat.publishedDate) AS date, count(*) AS threats
ORDER BY date
RETURN 
  date,
  threats,
  sum(threats) OVER (ORDER BY date) AS cumulativeThreats;

-- Recent threat velocity (last 30 days)
MATCH (threat:CyberThreat)
WHERE threat.publishedDate >= date() - duration('P30D')
WITH date(threat.publishedDate) AS day, threat.severity AS severity, count(*) AS count
RETURN 
  day,
  severity,
  count,
  sum(count) OVER (PARTITION BY severity ORDER BY day) AS runningTotal
ORDER BY day DESC, severity;

-- ============================================================
-- 8. CUSTOM SCORING
-- Create composite threat scores
-- ============================================================

-- Advanced Threat Score: Combine multiple centrality metrics
CALL gds.pageRank.stream('threat-intel-graph') YIELD nodeId AS id1, score AS pageRankScore
WITH id1, pageRankScore
CALL gds.degree.stream('threat-intel-graph') YIELD nodeId AS id2, score AS degreeScore
WITH id1, pageRankScore, id2, degreeScore
WHERE id1 = id2
WITH gds.util.asNode(id1) AS node, pageRankScore, degreeScore
WHERE node:CyberThreat
WITH node,
     pageRankScore * 0.4 + degreeScore * 0.3 AS threatScore,
     CASE node.severity
       WHEN 'critical' THEN 3
       WHEN 'high' THEN 2
       WHEN 'medium' THEN 1
       ELSE 0
     END AS severityWeight
RETURN 
  node.title AS threat,
  node.severity AS severity,
  threatScore * severityWeight AS compositeScore,
  'Multi-dimensional threat importance' AS metric
ORDER BY compositeScore DESC
LIMIT 20;

-- ============================================================
-- 9. ANOMALY DETECTION
-- Find unusual patterns
-- ============================================================

-- Outlier CVEs: Unusual exploitation frequency
MATCH (cve:CVE)<-[:EXPLOITS]-(threat:CyberThreat)
WITH cve, count(threat) AS exploits
WITH collect(exploits) AS exploitCounts
WITH exploitCounts, 
     reduce(sum = 0.0, x IN exploitCounts | sum + x) / size(exploitCounts) AS mean
WITH exploitCounts, mean,
     sqrt(reduce(sum = 0.0, x IN exploitCounts | sum + (x - mean)^2) / size(exploitCounts)) AS stdDev
MATCH (cve:CVE)<-[:EXPLOITS]-(threat:CyberThreat)
WITH cve, count(threat) AS exploits, mean, stdDev
WHERE exploits > mean + (2 * stdDev)
RETURN 
  cve.cveId AS outlierCVE,
  exploits AS exploitCount,
  mean + (2 * stdDev) AS threshold,
  'Anomalously high exploitation - investigate' AS alert
ORDER BY exploits DESC;

-- ============================================================
-- 10. CLEANUP
-- ============================================================

-- Drop graph projection when done
CALL gds.graph.drop('threat-intel-graph');
