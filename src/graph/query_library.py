#!/usr/bin/env python3
"""
Query Library - Common Threat Intelligence Queries
Pre-built Cypher queries for Cyber-PI ontology

Built to Rickover standards: Optimized, tested, production-ready
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from neo4j import AsyncDriver

logger = logging.getLogger(__name__)


class QueryLibrary:
    """
    Library of common threat intelligence queries
    
    Categories:
    - Vendor Risk Assessment
    - Attack Path Analysis
    - IOC Pivoting
    - Temporal Analysis
    - Threat Actor Attribution
    - MITRE ATT&CK Mapping
    """
    
    def __init__(self, driver: AsyncDriver):
        """
        Initialize query library
        
        Args:
            driver: Neo4j async driver
        """
        self.driver = driver
    
    # ========================================================================
    # VENDOR RISK QUERIES
    # ========================================================================
    
    async def get_vendor_risk_profile(self, vendor_name: str) -> Dict[str, Any]:
        """
        Get comprehensive risk profile for a vendor
        
        Returns:
            - CVE count by severity
            - Recent breaches
            - Affected products
            - Risk score
        """
        query = """
        MATCH (v:Vendor {name: $vendor_name})
        
        // Get CVE statistics
        OPTIONAL MATCH (v)-[:MANUFACTURES]->(p:Product)<-[:AFFECTS]-(cve:CVE)
        WITH v, p, cve
        
        RETURN v.name as vendor,
               v.risk_score as risk_score,
               v.reputation_score as reputation_score,
               v.total_breaches as total_breaches,
               v.last_breach_date as last_breach_date,
               count(DISTINCT p) as product_count,
               count(DISTINCT cve) as total_cves,
               count(DISTINCT CASE WHEN cve.severity = 'critical' THEN cve END) as critical_cves,
               count(DISTINCT CASE WHEN cve.severity = 'high' THEN cve END) as high_cves,
               count(DISTINCT CASE WHEN cve.severity = 'medium' THEN cve END) as medium_cves,
               count(DISTINCT CASE WHEN cve.severity = 'low' THEN cve END) as low_cves
        """
        
        async with self.driver.session() as session:
            result = await session.run(query, {"vendor_name": vendor_name.lower()})
            record = await result.single()
            
            if not record:
                return {"error": f"Vendor '{vendor_name}' not found"}
            
            return dict(record)
    
    async def get_vendors_by_risk(self, min_risk: float = 0.7, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get vendors with highest risk scores
        
        Args:
            min_risk: Minimum risk score (0.0-1.0)
            limit: Maximum results
            
        Returns:
            List of high-risk vendors
        """
        query = """
        MATCH (v:Vendor)
        WHERE v.risk_score >= $min_risk
        
        OPTIONAL MATCH (v)-[:MANUFACTURES]->(p:Product)<-[:AFFECTS]-(cve:CVE)
        WHERE cve.severity IN ['critical', 'high']
        
        RETURN v.name as vendor,
               v.risk_score as risk_score,
               v.industry as industry,
               count(DISTINCT cve) as critical_high_cves,
               v.last_breach_date as last_breach
        ORDER BY v.risk_score DESC
        LIMIT $limit
        """
        
        async with self.driver.session() as session:
            result = await session.run(query, {"min_risk": min_risk, "limit": limit})
            return [dict(record) async for record in result]
    
    async def get_vendor_recent_cves(
        self,
        vendor_name: str,
        days: int = 30,
        min_severity: str = "medium"
    ) -> List[Dict[str, Any]]:
        """
        Get recent CVEs affecting a vendor
        
        Args:
            vendor_name: Vendor name
            days: Days to look back
            min_severity: Minimum severity (low, medium, high, critical)
            
        Returns:
            List of recent CVEs
        """
        severity_order = {"low": 1, "medium": 2, "high": 3, "critical": 4}
        min_level = severity_order.get(min_severity, 2)
        
        query = """
        MATCH (v:Vendor {name: $vendor_name})-[:MANUFACTURES]->(p:Product)
              <-[:AFFECTS]-(cve:CVE)
        WHERE cve.published >= datetime() - duration({days: $days})
          AND (
            (cve.severity = 'critical' AND 4 >= $min_level) OR
            (cve.severity = 'high' AND 3 >= $min_level) OR
            (cve.severity = 'medium' AND 2 >= $min_level) OR
            (cve.severity = 'low' AND 1 >= $min_level)
          )
        
        RETURN cve.cve_id as cve_id,
               cve.description as description,
               cve.severity as severity,
               cve.cvss_v3_score as cvss_score,
               cve.published as published,
               collect(DISTINCT p.name) as affected_products
        ORDER BY cve.published DESC
        """
        
        async with self.driver.session() as session:
            result = await session.run(query, {
                "vendor_name": vendor_name.lower(),
                "days": days,
                "min_level": min_level
            })
            return [dict(record) async for record in result]
    
    # ========================================================================
    # ATTACK PATH ANALYSIS
    # ========================================================================
    
    async def find_attack_paths(
        self,
        vendor_name: str,
        max_hops: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find attack paths targeting a vendor
        
        Path: ThreatActor → Malware → Technique → CVE → Product → Vendor
        
        Args:
            vendor_name: Target vendor
            max_hops: Maximum path length
            
        Returns:
            List of attack paths
        """
        query = """
        MATCH path = (ta:ThreatActor)-[:USES]->(m:Malware)
                     -[:IMPLEMENTS]->(tech:MitreTechnique)
                     -[:EXPLOITS]->(cve:CVE)
                     -[:AFFECTS]->(p:Product)
                     -[:MANUFACTURED_BY]->(v:Vendor {name: $vendor_name})
        WHERE length(path) <= $max_hops
        
        RETURN ta.name as threat_actor,
               ta.sophistication as sophistication,
               m.name as malware,
               m.malware_types as malware_types,
               tech.technique_id as technique,
               tech.name as technique_name,
               cve.cve_id as cve,
               cve.severity as severity,
               p.name as product
        ORDER BY cve.cvss_v3_score DESC
        LIMIT 20
        """
        
        async with self.driver.session() as session:
            result = await session.run(query, {
                "vendor_name": vendor_name.lower(),
                "max_hops": max_hops
            })
            return [dict(record) async for record in result]
    
    async def find_vulnerable_attack_surface(
        self,
        vendor_name: str
    ) -> Dict[str, Any]:
        """
        Analyze vendor's attack surface
        
        Returns:
            - Products with critical CVEs
            - Techniques that could exploit them
            - Known threat actors using those techniques
        """
        query = """
        MATCH (v:Vendor {name: $vendor_name})-[:MANUFACTURES]->(p:Product)
              <-[:AFFECTS]-(cve:CVE)
        WHERE cve.severity IN ['critical', 'high']
        
        // Find techniques that could exploit these CVEs
        OPTIONAL MATCH (cve)<-[:EXPLOITS]-(tech:MitreTechnique)
        
        // Find threat actors using these techniques
        OPTIONAL MATCH (tech)<-[:IMPLEMENTS]-(m:Malware)<-[:USES]-(ta:ThreatActor)
        
        RETURN p.name as product,
               count(DISTINCT cve) as vulnerability_count,
               collect(DISTINCT cve.cve_id)[..5] as sample_cves,
               collect(DISTINCT tech.technique_id)[..5] as applicable_techniques,
               collect(DISTINCT ta.name)[..5] as potential_threat_actors
        ORDER BY vulnerability_count DESC
        """
        
        async with self.driver.session() as session:
            result = await session.run(query, {"vendor_name": vendor_name.lower()})
            return {"attack_surface": [dict(record) async for record in result]}
    
    # ========================================================================
    # IOC PIVOTING
    # ========================================================================
    
    async def pivot_from_ioc(
        self,
        ioc_value: str,
        max_depth: int = 3
    ) -> Dict[str, Any]:
        """
        Pivot from an IOC to related entities
        
        Finds:
        - Related IOCs (communicates_with)
        - Associated malware
        - Linked campaigns
        - Attributed threat actors
        
        Args:
            ioc_value: IOC value (IP, domain, hash, etc.)
            max_depth: Maximum relationship depth
            
        Returns:
            Related entities
        """
        query = """
        MATCH (ioc:IOC {value: $ioc_value})
        
        // Related IOCs
        OPTIONAL MATCH (ioc)-[:COMMUNICATES_WITH*1..$max_depth]-(related_ioc:IOC)
        
        // Associated malware
        OPTIONAL MATCH (ioc)-[:INDICATES]->(malware:Malware)
        
        // Linked campaigns
        OPTIONAL MATCH (ioc)-[:OBSERVED_IN]->(campaign:Campaign)
        
        // Attributed threat actors
        OPTIONAL MATCH (malware)<-[:USES]-(ta:ThreatActor)
        
        RETURN ioc.value as original_ioc,
               ioc.ioc_type as ioc_type,
               ioc.threat_types as threat_types,
               collect(DISTINCT related_ioc.value)[..10] as related_iocs,
               collect(DISTINCT malware.name) as associated_malware,
               collect(DISTINCT campaign.name) as campaigns,
               collect(DISTINCT ta.name) as threat_actors
        """
        
        async with self.driver.session() as session:
            result = await session.run(query, {
                "ioc_value": ioc_value.lower(),
                "max_depth": max_depth
            })
            record = await result.single()
            
            if not record:
                return {"error": f"IOC '{ioc_value}' not found"}
            
            return dict(record)
    
    async def find_ioc_clusters(
        self,
        min_cluster_size: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find clusters of related IOCs
        
        Useful for identifying botnets, C2 infrastructure, etc.
        
        Args:
            min_cluster_size: Minimum IOCs in cluster
            
        Returns:
            List of IOC clusters
        """
        query = """
        MATCH (ioc1:IOC)-[:COMMUNICATES_WITH*1..2]-(ioc2:IOC)
        WHERE id(ioc1) < id(ioc2)
        
        WITH ioc1, collect(DISTINCT ioc2) as cluster
        WHERE size(cluster) >= $min_cluster_size
        
        RETURN ioc1.value as seed_ioc,
               ioc1.ioc_type as ioc_type,
               size(cluster) as cluster_size,
               [ioc IN cluster | ioc.value][..10] as sample_iocs
        ORDER BY cluster_size DESC
        LIMIT 20
        """
        
        async with self.driver.session() as session:
            result = await session.run(query, {"min_cluster_size": min_cluster_size})
            return [dict(record) async for record in result]
    
    # ========================================================================
    # THREAT ACTOR ANALYSIS
    # ========================================================================
    
    async def get_threat_actor_profile(
        self,
        actor_name: str
    ) -> Dict[str, Any]:
        """
        Get comprehensive threat actor profile
        
        Returns:
            - TTPs (tactics, techniques, procedures)
            - Malware used
            - Campaigns
            - Targets
        """
        query = """
        MATCH (ta:ThreatActor {name: $actor_name})
        
        // Malware used
        OPTIONAL MATCH (ta)-[:USES]->(malware:Malware)
        
        // Techniques implemented
        OPTIONAL MATCH (malware)-[:IMPLEMENTS]->(tech:MitreTechnique)
        
        // Tactics
        OPTIONAL MATCH (tech)-[:PART_OF]->(tactic:MitreTactic)
        
        // Campaigns
        OPTIONAL MATCH (campaign:Campaign)-[:ATTRIBUTED_TO]->(ta)
        
        // Targets
        OPTIONAL MATCH (ta)-[:TARGETS]->(vendor:Vendor)
        
        RETURN ta.name as threat_actor,
               ta.threat_actor_types as actor_types,
               ta.sophistication as sophistication,
               ta.primary_motivation as motivation,
               ta.aliases as aliases,
               collect(DISTINCT malware.name) as malware_arsenal,
               collect(DISTINCT tech.technique_id) as techniques,
               collect(DISTINCT tactic.name) as tactics,
               collect(DISTINCT campaign.name) as campaigns,
               collect(DISTINCT vendor.name) as targets
        """
        
        async with self.driver.session() as session:
            result = await session.run(query, {"actor_name": actor_name})
            record = await result.single()
            
            if not record:
                return {"error": f"Threat actor '{actor_name}' not found"}
            
            return dict(record)
    
    async def find_similar_threat_actors(
        self,
        actor_name: str,
        similarity_threshold: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        Find threat actors with similar TTPs
        
        Uses Jaccard similarity on techniques used
        
        Args:
            actor_name: Reference threat actor
            similarity_threshold: Minimum similarity (0.0-1.0)
            
        Returns:
            List of similar threat actors
        """
        query = """
        MATCH (ta1:ThreatActor {name: $actor_name})-[:USES]->(m1:Malware)
              -[:IMPLEMENTS]->(tech1:MitreTechnique)
        WITH ta1, collect(DISTINCT tech1.technique_id) as techniques1
        
        MATCH (ta2:ThreatActor)-[:USES]->(m2:Malware)
              -[:IMPLEMENTS]->(tech2:MitreTechnique)
        WHERE ta1 <> ta2
        WITH ta1, techniques1, ta2, collect(DISTINCT tech2.technique_id) as techniques2
        
        // Calculate Jaccard similarity
        WITH ta1, ta2,
             [t IN techniques1 WHERE t IN techniques2] as common,
             techniques1 + [t IN techniques2 WHERE NOT t IN techniques1] as union
        WITH ta1, ta2, common, union,
             toFloat(size(common)) / size(union) as similarity
        WHERE similarity >= $threshold
        
        RETURN ta2.name as similar_actor,
               ta2.sophistication as sophistication,
               ta2.primary_motivation as motivation,
               similarity,
               common as shared_techniques
        ORDER BY similarity DESC
        LIMIT 10
        """
        
        async with self.driver.session() as session:
            result = await session.run(query, {
                "actor_name": actor_name,
                "threshold": similarity_threshold
            })
            return [dict(record) async for record in result]
    
    # ========================================================================
    # MITRE ATT&CK QUERIES
    # ========================================================================
    
    async def get_technique_coverage(
        self,
        tactic_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get technique coverage statistics
        
        Shows which techniques are most commonly used by threat actors
        
        Args:
            tactic_id: Filter by tactic (e.g., "TA0001")
            
        Returns:
            Technique usage statistics
        """
        if tactic_id:
            query = """
            MATCH (tactic:MitreTactic {tactic_id: $tactic_id})
                  <-[:PART_OF]-(tech:MitreTechnique)
            OPTIONAL MATCH (tech)<-[:IMPLEMENTS]-(malware:Malware)
                          <-[:USES]-(ta:ThreatActor)
            
            RETURN tech.technique_id as technique,
                   tech.name as technique_name,
                   count(DISTINCT malware) as malware_count,
                   count(DISTINCT ta) as threat_actor_count,
                   collect(DISTINCT ta.name)[..5] as sample_actors
            ORDER BY threat_actor_count DESC, malware_count DESC
            """
            params = {"tactic_id": tactic_id}
        else:
            query = """
            MATCH (tech:MitreTechnique)
            OPTIONAL MATCH (tech)<-[:IMPLEMENTS]-(malware:Malware)
                          <-[:USES]-(ta:ThreatActor)
            
            RETURN tech.technique_id as technique,
                   tech.name as technique_name,
                   count(DISTINCT malware) as malware_count,
                   count(DISTINCT ta) as threat_actor_count,
                   collect(DISTINCT ta.name)[..5] as sample_actors
            ORDER BY threat_actor_count DESC, malware_count DESC
            LIMIT 20
            """
            params = {}
        
        async with self.driver.session() as session:
            result = await session.run(query, params)
            return [dict(record) async for record in result]
    
    async def map_malware_to_attack(
        self,
        malware_name: str
    ) -> Dict[str, Any]:
        """
        Map malware to MITRE ATT&CK framework
        
        Returns:
            - Techniques implemented
            - Tactics covered
            - Kill chain phases
        """
        query = """
        MATCH (malware:Malware {name: $malware_name})
              -[:IMPLEMENTS]->(tech:MitreTechnique)
              -[:PART_OF]->(tactic:MitreTactic)
        
        RETURN malware.name as malware,
               malware.malware_types as malware_types,
               collect(DISTINCT {
                   technique_id: tech.technique_id,
                   technique_name: tech.name,
                   tactic: tactic.name
               }) as ttps,
               collect(DISTINCT tactic.name) as tactics_covered
        """
        
        async with self.driver.session() as session:
            result = await session.run(query, {"malware_name": malware_name})
            record = await result.single()
            
            if not record:
                return {"error": f"Malware '{malware_name}' not found"}
            
            return dict(record)
    
    # ========================================================================
    # TEMPORAL ANALYSIS
    # ========================================================================
    
    async def get_threat_timeline(
        self,
        days: int = 30,
        entity_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get timeline of threat activity
        
        Args:
            days: Days to look back
            entity_type: Filter by entity type (CVE, Breach, Campaign)
            
        Returns:
            Timeline of events
        """
        if entity_type == "CVE":
            query = """
            MATCH (cve:CVE)
            WHERE cve.published >= datetime() - duration({days: $days})
            
            RETURN 'CVE' as event_type,
                   cve.cve_id as identifier,
                   cve.description as description,
                   cve.severity as severity,
                   cve.published as timestamp
            ORDER BY cve.published DESC
            LIMIT 100
            """
        elif entity_type == "Breach":
            query = """
            MATCH (breach:Breach)
            WHERE breach.breach_date >= datetime() - duration({days: $days})
            
            RETURN 'Breach' as event_type,
                   breach.name as identifier,
                   breach.description as description,
                   breach.severity as severity,
                   breach.breach_date as timestamp
            ORDER BY breach.breach_date DESC
            LIMIT 100
            """
        else:
            query = """
            MATCH (n)
            WHERE n.created >= datetime() - duration({days: $days})
              AND (n:CVE OR n:Breach OR n:Campaign)
            
            RETURN labels(n)[0] as event_type,
                   COALESCE(n.cve_id, n.name) as identifier,
                   n.description as description,
                   n.severity as severity,
                   COALESCE(n.published, n.breach_date, n.created) as timestamp
            ORDER BY timestamp DESC
            LIMIT 100
            """
        
        async with self.driver.session() as session:
            result = await session.run(query, {"days": days})
            return [dict(record) async for record in result]
    
    # ========================================================================
    # STATISTICS
    # ========================================================================
    
    async def get_graph_statistics(self) -> Dict[str, Any]:
        """Get overall graph statistics"""
        query = """
        MATCH (n)
        WITH labels(n)[0] as label, count(*) as count
        RETURN collect({label: label, count: count}) as node_stats
        """
        
        async with self.driver.session() as session:
            result = await session.run(query)
            record = await result.single()
            
            return {
                "nodes": dict(record) if record else {},
                "timestamp": datetime.utcnow().isoformat()
            }


# ============================================================================
# EXPORT
# ============================================================================

__all__ = ["QueryLibrary"]
