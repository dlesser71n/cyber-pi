# Graph Analytics for Unified Threat Graph

This module implements advanced graph analytics for the unified threat graph using Neo4j Graph Data Science.

## Algorithms Implemented

### 1. PageRank

PageRank identifies the most influential nodes in the graph based on the number and quality of connections. In the context of the unified threat graph:

- High PageRank CVEs represent vulnerabilities that are connected to many products or referenced by many threat intelligence sources
- High PageRank threat intelligence objects represent threats that reference many critical CVEs
- High PageRank products represent software with many vulnerabilities

### 2. Betweenness Centrality

Betweenness centrality identifies "bridge nodes" that connect different parts of the graph. These nodes are critical for information flow and represent:

- CVEs that bridge between different vendor ecosystems
- Threat intelligence that connects different types of vulnerabilities
- MITRE techniques that bridge between different tactics

### 3. Louvain Community Detection

Community detection identifies clusters of densely connected nodes. In the unified threat graph, communities might represent:

- Vulnerability clusters affecting similar products
- Threat intelligence clusters using similar techniques
- Product clusters with similar vulnerability profiles

### 4. Node Similarity

Node similarity identifies products that are affected by similar vulnerabilities, which can be used for:

- Identifying products with similar risk profiles
- Recommending similar products for vulnerability assessment
- Finding potential substitutes with better security profiles

### 5. Risk Scoring

The risk scoring system combines multiple factors:

- Base risk from CVE severity and PageRank
- Threat intelligence amplification factor
- Community risk factor (products in the same community as high-risk products)

## Usage

Run the analytics with:

```bash
python src/analytics/graph_analytics.py
```

The script will:

1. Create a graph projection in Neo4j
2. Run all analytics algorithms
3. Calculate risk scores
4. Export visualization data to `/tmp/visualization/`
5. Log results to `/tmp/graph_analytics.log`

## Visualization Data

The script exports the following data for visualization:

- `top_cves.json`: Top CVEs by PageRank with their affected products
- `top_threats.json`: Top threat intelligence objects with their IOCs
- `communities.json`: Community size distribution

## Example Queries

### Find Critical Bridge Nodes

```cypher
MATCH (n)
WHERE n.betweenness > 1000
RETURN labels(n)[0] AS type, 
       CASE 
         WHEN n:CVE THEN n.id
         WHEN n:ThreatIntel THEN n.title
         ELSE toString(id(n))
       END AS name,
       n.betweenness AS score
ORDER BY score DESC
LIMIT 10
```

### Find High-Risk Products

```cypher
MATCH (p:Product)
WHERE p.risk_score > 8
RETURN p.name AS product,
       p.risk_score AS risk_score,
       p.base_risk AS base_risk,
       p.threat_amplifier AS threat_amplifier
ORDER BY risk_score DESC
```

### Find Products in the Same Community

```cypher
MATCH (p:Product {name: 'windows_10'})
WHERE p.community IS NOT NULL
MATCH (p2:Product)
WHERE p2.community = p.community AND p2 <> p
RETURN p2.name AS similar_product,
       p2.risk_score AS risk_score
ORDER BY risk_score DESC
```
