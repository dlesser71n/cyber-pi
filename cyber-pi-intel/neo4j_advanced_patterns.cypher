-- ============================================================
-- ADVANCED NEO4J PATTERN MATCHING
-- Cyber Threat Intelligence Analysis
-- ============================================================

-- Current Graph:
-- - 457 CyberThreat nodes
-- - 386 CVE nodes  
-- - 5 ThreatActor nodes
-- - 18 Industry nodes
-- - 441 EXPLOITS relationships (Threat -> CVE)
-- - 13 ATTRIBUTED_TO relationships (Threat -> Actor)

-- ============================================================
-- 1. THREAT ACTOR CAMPAIGN IDENTIFICATION
-- Find all threats attributed to same actor (campaigns)
-- ============================================================

-- Pattern: Find campaigns by threat actor
MATCH (actor:ThreatActor)<-[:ATTRIBUTED_TO]-(threat:CyberThreat)
WITH actor, collect(threat) as threats, count(threat) as threatCount
WHERE threatCount > 1  // Only actors with multiple threats
RETURN 
  actor.actorName as actor,
  threatCount as campaignSize,
  [t IN threats | t.title][0..5] as sampleThreats,
  [t IN threats | t.severity] as severities
ORDER BY threatCount DESC;

-- Pattern: Campaign timeline (when actor was active)
MATCH (actor:ThreatActor)<-[:ATTRIBUTED_TO]-(threat:CyberThreat)
WITH actor, threat
ORDER BY threat.publishedDate
RETURN 
  actor.actorName as actor,
  min(threat.publishedDate) as firstSeen,
  max(threat.publishedDate) as lastSeen,
  count(threat) as activities,
  collect(DISTINCT threat.severity) as severityProfile
ORDER BY activities DESC;

-- ============================================================
-- 2. CVE EXPLOITATION PATTERNS
-- Find most exploited vulnerabilities
-- ============================================================

-- Pattern: Most targeted CVEs
MATCH (cve:CVE)<-[:EXPLOITS]-(threat:CyberThreat)
WITH cve, collect(threat) as threats, count(threat) as exploitCount
WHERE exploitCount > 1  // CVEs exploited by multiple threats
RETURN 
  cve.cveId as cve,
  exploitCount as timesExploited,
  [t IN threats | t.severity] as severities,
  [t IN threats | t.title][0..3] as sampleThreats
ORDER BY exploitCount DESC
LIMIT 20;

-- Pattern: CVE exploitation chains (threats exploiting multiple CVEs)
MATCH (threat:CyberThreat)-[:EXPLOITS]->(cve:CVE)
WITH threat, collect(cve.cveId) as cves, count(cve) as cveCount
WHERE cveCount > 1  // Threats using multiple vulnerabilities
RETURN 
  threat.title as threat,
  threat.severity as severity,
  cveCount as vulnerabilitiesUsed,
  cves as exploitChain
ORDER BY cveCount DESC
LIMIT 20;

-- Pattern: Critical CVEs (in critical threats)
MATCH (threat:CyberThreat)-[:EXPLOITS]->(cve:CVE)
WHERE threat.severity = 'critical'
WITH cve, count(DISTINCT threat) as criticalThreats
RETURN 
  cve.cveId as cve,
  criticalThreats as appearsInCriticalThreats
ORDER BY criticalThreats DESC
LIMIT 20;

-- ============================================================
-- 3. THREAT ACTOR TTPs (Tools, Techniques, Procedures)
-- Identify actor patterns
-- ============================================================

-- Pattern: Actor's favorite CVEs
MATCH (actor:ThreatActor)<-[:ATTRIBUTED_TO]-(threat:CyberThreat)-[:EXPLOITS]->(cve:CVE)
WITH actor, cve, count(threat) as usage
RETURN 
  actor.actorName as actor,
  collect(cve.cveId)[0..10] as favoriteCVEs,
  sum(usage) as totalExploits
ORDER BY totalExploits DESC;

-- Pattern: Actor severity profile
MATCH (actor:ThreatActor)<-[:ATTRIBUTED_TO]-(threat:CyberThreat)
WITH actor, threat.severity as severity, count(*) as count
RETURN 
  actor.actorName as actor,
  collect({severity: severity, count: count}) as severityDistribution
ORDER BY actor;

-- ============================================================
-- 4. CO-OCCURRENCE PATTERNS
-- Find threats that share characteristics
-- ============================================================

-- Pattern: CVEs that appear together (vulnerability bundles)
MATCH (cve1:CVE)<-[:EXPLOITS]-(threat:CyberThreat)-[:EXPLOITS]->(cve2:CVE)
WHERE id(cve1) < id(cve2)  // Avoid duplicates
WITH cve1, cve2, count(threat) as coOccurrence
WHERE coOccurrence > 1
RETURN 
  cve1.cveId as cve1,
  cve2.cveId as cve2,
  coOccurrence as appearedTogether
ORDER BY coOccurrence DESC
LIMIT 20;

-- Pattern: Threats sharing same CVEs (similar attack vectors)
MATCH (t1:CyberThreat)-[:EXPLOITS]->(cve:CVE)<-[:EXPLOITS]-(t2:CyberThreat)
WHERE id(t1) < id(t2)
WITH t1, t2, collect(cve.cveId) as sharedCVEs, count(cve) as commonality
WHERE commonality > 1
RETURN 
  t1.title as threat1,
  t2.title as threat2,
  commonality as sharedVulnerabilities,
  sharedCVEs[0..5] as sampleSharedCVEs
ORDER BY commonality DESC
LIMIT 20;

-- ============================================================
-- 5. TEMPORAL PATTERNS
-- Identify trends over time
-- ============================================================

-- Pattern: Recent critical threats with CVEs
MATCH (threat:CyberThreat)-[:EXPLOITS]->(cve:CVE)
WHERE threat.severity = 'critical'
  AND threat.publishedDate >= '2025-10-01'
RETURN 
  threat.publishedDate as date,
  threat.title as threat,
  collect(cve.cveId) as exploitedCVEs,
  threat.source as source
ORDER BY threat.publishedDate DESC
LIMIT 20;

-- Pattern: Threat actor activity timeline
MATCH (actor:ThreatActor)<-[:ATTRIBUTED_TO]-(threat:CyberThreat)
WITH actor, 
     substring(threat.publishedDate, 0, 7) as month,  // Extract YYYY-MM
     count(*) as activities
RETURN 
  actor.actorName as actor,
  collect({month: month, count: activities}) as monthlyActivity
ORDER BY actor;

-- ============================================================
-- 6. COMPLEXITY ANALYSIS
-- Measure threat sophistication
-- ============================================================

-- Pattern: Most sophisticated threats (multiple CVEs + attributed actor)
MATCH (actor:ThreatActor)<-[:ATTRIBUTED_TO]-(threat:CyberThreat)-[:EXPLOITS]->(cve:CVE)
WITH threat, actor, collect(cve.cveId) as cves, count(cve) as cveCount
RETURN 
  threat.title as threat,
  actor.actorName as actor,
  threat.severity as severity,
  cveCount as exploitCount,
  cves[0..10] as cveList
ORDER BY cveCount DESC
LIMIT 20;

-- Pattern: Threat complexity score
MATCH (threat:CyberThreat)
OPTIONAL MATCH (threat)-[:EXPLOITS]->(cve:CVE)
OPTIONAL MATCH (threat)-[:ATTRIBUTED_TO]->(actor:ThreatActor)
WITH threat,
     count(DISTINCT cve) as cveCount,
     count(DISTINCT actor) as hasAttribution,
     CASE threat.severity 
       WHEN 'critical' THEN 3
       WHEN 'high' THEN 2
       WHEN 'medium' THEN 1
       ELSE 0
     END as severityScore
RETURN 
  threat.title as threat,
  threat.severity as severity,
  cveCount + hasAttribution + severityScore as complexityScore,
  cveCount as vulnerabilities,
  CASE WHEN hasAttribution > 0 THEN 'attributed' ELSE 'unattributed' END as attribution
ORDER BY complexityScore DESC
LIMIT 30;

-- ============================================================
-- 7. ATTACK SURFACE DISCOVERY
-- Find potential attack vectors
-- ============================================================

-- Pattern: CVEs without mitigations (frequently exploited but no attribution)
MATCH (cve:CVE)<-[:EXPLOITS]-(threat:CyberThreat)
WHERE NOT (threat)-[:ATTRIBUTED_TO]->(:ThreatActor)
WITH cve, count(threat) as anonymousExploits, collect(threat.title)[0..3] as samples
WHERE anonymousExploits > 2
RETURN 
  cve.cveId as cve,
  anonymousExploits as unattributedExploits,
  samples as sampleThreats
ORDER BY anonymousExploits DESC;

-- Pattern: High-value targets (critical threats with many CVEs)
MATCH (threat:CyberThreat)-[:EXPLOITS]->(cve:CVE)
WHERE threat.severity IN ['critical', 'high']
WITH threat, collect(cve.cveId) as cves, count(cve) as cveCount
WHERE cveCount >= 2
RETURN 
  threat.title as highValueTarget,
  threat.severity as severity,
  cveCount as attackVectors,
  cves as exploitChain
ORDER BY cveCount DESC, threat.severity
LIMIT 20;

-- ============================================================
-- 8. SHORTEST PATH QUERIES
-- Find connections between threats
-- ============================================================

-- Pattern: Connection between two threat actors through CVEs
MATCH path = shortestPath(
  (actor1:ThreatActor)<-[:ATTRIBUTED_TO]-(:CyberThreat)-[:EXPLOITS]->(:CVE)
  <-[:EXPLOITS]-(:CyberThreat)-[:ATTRIBUTED_TO]->(actor2:ThreatActor)
)
WHERE actor1 <> actor2
RETURN 
  actor1.actorName as actor1,
  actor2.actorName as actor2,
  length(path) as pathLength,
  [n IN nodes(path) WHERE n:CVE | n.cveId][0] as sharedCVE
LIMIT 10;

-- Pattern: Find all paths from actor to specific CVE
MATCH path = (actor:ThreatActor)<-[:ATTRIBUTED_TO]-(threat:CyberThreat)-[:EXPLOITS]->(cve:CVE)
WHERE cve.cveId STARTS WITH 'CVE-2025'  // Recent CVEs
RETURN 
  actor.actorName as actor,
  threat.title as threat,
  cve.cveId as cve,
  length(path) as pathLength
LIMIT 20;

-- ============================================================
-- 9. AGGREGATION PATTERNS
-- Statistical analysis
-- ============================================================

-- Pattern: Global threat landscape summary
MATCH (threat:CyberThreat)
OPTIONAL MATCH (threat)-[:EXPLOITS]->(cve:CVE)
OPTIONAL MATCH (threat)-[:ATTRIBUTED_TO]->(actor:ThreatActor)
RETURN 
  count(DISTINCT threat) as totalThreats,
  count(DISTINCT cve) as uniqueCVEs,
  count(DISTINCT actor) as activeActors,
  count(DISTINCT CASE WHEN threat.severity = 'critical' THEN threat END) as criticalThreats,
  count(DISTINCT CASE WHEN threat.severity = 'high' THEN threat END) as highThreats,
  avg(CASE WHEN cve IS NOT NULL THEN 1 ELSE 0 END) * 100 as pctWithCVEs,
  avg(CASE WHEN actor IS NOT NULL THEN 1 ELSE 0 END) * 100 as pctAttributed;

-- Pattern: CVE risk distribution
MATCH (cve:CVE)<-[:EXPLOITS]-(threat:CyberThreat)
WITH cve, 
     collect(DISTINCT threat.severity) as severities,
     count(threat) as threatCount
RETURN 
  CASE 
    WHEN threatCount > 5 THEN 'Very High Risk'
    WHEN threatCount > 3 THEN 'High Risk'
    WHEN threatCount > 1 THEN 'Medium Risk'
    ELSE 'Low Risk'
  END as riskLevel,
  count(cve) as cveCount,
  avg(threatCount) as avgThreatsPerCVE
ORDER BY riskLevel;

-- ============================================================
-- 10. RECOMMENDATION ENGINE
-- Suggest connections and patterns
-- ============================================================

-- Pattern: Similar threats (share CVEs but different actors)
MATCH (t1:CyberThreat)-[:EXPLOITS]->(cve:CVE)<-[:EXPLOITS]-(t2:CyberThreat)
OPTIONAL MATCH (t1)-[:ATTRIBUTED_TO]->(a1:ThreatActor)
OPTIONAL MATCH (t2)-[:ATTRIBUTED_TO]->(a2:ThreatActor)
WHERE id(t1) < id(t2)
  AND (a1 IS NULL OR a2 IS NULL OR a1 <> a2)
WITH t1, t2, collect(cve.cveId) as sharedCVEs, count(cve) as similarity
WHERE similarity >= 2
RETURN 
  t1.title as threat1,
  t2.title as threat2,
  similarity as sharedVulnerabilities,
  sharedCVEs[0..5] as commonCVEs,
  'Possible related campaigns' as insight
ORDER BY similarity DESC
LIMIT 15;

-- Pattern: Emerging CVE patterns (recent high-frequency)
MATCH (threat:CyberThreat)-[:EXPLOITS]->(cve:CVE)
WHERE threat.publishedDate >= '2025-10-01'
WITH cve, count(threat) as recentExploits, collect(threat.title)[0..3] as recentThreats
WHERE recentExploits >= 2
RETURN 
  cve.cveId as emergingCVE,
  recentExploits as exploitFrequency,
  recentThreats as recentlySeenIn,
  'High priority for patching' as recommendation
ORDER BY recentExploits DESC;
