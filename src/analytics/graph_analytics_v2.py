#!/usr/bin/env python3
"""
Graph Analytics for Unified Threat Graph v2
Enterprise-Quality Implementation with Production-Grade Monitoring
"""

import sys
import os
import logging
import os
import time
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from neo4j import GraphDatabase
from src.core.enterprise_base import EnterpriseBase
from src.core.monitoring import EnterpriseMonitoring
from tqdm import tqdm

# Configure debug logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - [%(name)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.FileHandler("/tmp/graph_analytics.log", mode='w'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Enable Neo4j driver logging
neo4j_logger = logging.getLogger('neo4j')
neo4j_logger.setLevel(logging.DEBUG)

# Enable psutil logging
psutil_logger = logging.getLogger('psutil')
psutil_logger.setLevel(logging.DEBUG)

@dataclass
class AlgorithmMetrics:
    """Metrics for a graph algorithm run"""
    name: str
    compute_time: float
    memory_used: int
    nodes_processed: int
    relationships_processed: int
    success: bool
    error: Optional[str] = None

class EnterpriseGraphAnalytics(EnterpriseBase):
    """Enterprise-grade graph analytics"""
    
    def __init__(
        self, 
        neo4j_uri: str = "bolt://10.152.183.169:7687", 
        neo4j_user: str = "neo4j", 
        neo4j_password: Optional[str] = None
    ):
        """Initialize with enterprise monitoring"""
        super().__init__()
        
        logger.info("="*80)
        logger.info("⚛️ ENTERPRISE-GRADE GRAPH ANALYTICS")
        logger.info("="*80)
        
        # Initialize monitoring
        self.monitoring = EnterpriseMonitoring()
        
        # Initialize Neo4j
        self.neo4j = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        self.graph_name = "unified-threat-graph"
        
        # Register circuit breakers
        self.register_circuit_breaker("pagerank", failure_threshold=2)
        self.register_circuit_breaker("betweenness", failure_threshold=2)
        self.register_circuit_breaker("louvain", failure_threshold=2)
        self.register_circuit_breaker("node_similarity", failure_threshold=2)
        
        # Initialize metrics
        self.algorithm_metrics: List[AlgorithmMetrics] = []
        self.stats = {}
        
    def close(self):
        """Close connections with cleanup"""
        with self.operation_context("cleanup") as op_id:
            try:
                self.neo4j.close()
                self.monitoring.stop()
                logger.info("✅ All connections closed")
            except Exception as e:
                logger.error(f"❌ Cleanup failed: {e}")
                raise
    
    def _run_monitored_algorithm(
        self, 
        name: str, 
        query: str, 
        params: Dict[str, Any] = None
    ) -> AlgorithmMetrics:
        """Run a graph algorithm with monitoring"""
        with self.operation_context(name) as op_id:
            start_time = time.time()
            start_memory = self.monitoring.resources.get_current_metrics()["process_memory_rss"]
            
            try:
                with self.neo4j.session() as session:
                    result = session.run(query, **(params or {}))
                    info = result.single()
                    
                    # Update metrics
                    end_time = time.time()
                    end_memory = self.monitoring.resources.get_current_metrics()["process_memory_rss"]
                    
                    metrics = AlgorithmMetrics(
                        name=name,
                        compute_time=end_time - start_time,
                        memory_used=end_memory - start_memory,
                        nodes_processed=info.get("nodePropertiesWritten", 0),
                        relationships_processed=info.get("relationshipsWritten", 0),
                        success=True
                    )
                    
                    # Update monitoring
                    self.monitoring.operations.end_operation(
                        name,
                        success=True,
                        items=metrics.nodes_processed + metrics.relationships_processed
                    )
                    
                    return metrics
                    
            except Exception as e:
                # Record failure
                metrics = AlgorithmMetrics(
                    name=name,
                    compute_time=time.time() - start_time,
                    memory_used=0,
                    nodes_processed=0,
                    relationships_processed=0,
                    success=False,
                    error=str(e)
                )
                
                # Update monitoring
                self.monitoring.operations.end_operation(
                    name,
                    success=False,
                    items=0
                )
                
                raise
            finally:
                self.algorithm_metrics.append(metrics)
    
    def create_graph_projection(self):
        """Create graph projection with monitoring"""
        logger.info("\n🔍 Creating graph projection...")
        
        with self.operation_context("create_projection") as op_id:
            with self.neo4j.session() as session:
                # Check if graph exists
                result = session.run("CALL gds.graph.exists($name)", name=self.graph_name)
                exists = result.single()["exists"]
                
                if exists:
                    logger.info(f"  Graph projection '{self.graph_name}' already exists")
                    # Get graph info
                    result = session.run("CALL gds.graph.list($name)", name=self.graph_name)
                    graph_info = result.single()
                    logger.info(f"  Nodes: {graph_info['nodeCount']:,}, Relationships: {graph_info['relationshipCount']:,}")
                    
                    # Update metrics
                    self.stats["nodes"] = graph_info["nodeCount"]
                    self.stats["relationships"] = graph_info["relationshipCount"]
                    
                    self.monitoring.operations.end_operation(
                        "create_projection",
                        success=True,
                        items=graph_info["nodeCount"] + graph_info["relationshipCount"]
                    )
                    return
                
                # Create graph projection
                logger.info("  Creating new graph projection...")
                metrics = self._run_monitored_algorithm(
                    "create_projection",
                    """
                    CALL gds.graph.project(
                        $name,
                        ['CVE', 'ThreatIntel', 'Product', 'Vendor', 'CWE', 'MitreTactic', 'MitreTechnique', 'IOC'],
                        {
                            AFFECTS: {orientation: 'NATURAL'},
                            MADE_BY: {orientation: 'NATURAL'},
                            HAS_WEAKNESS: {orientation: 'NATURAL'},
                            REFERENCES: {orientation: 'NATURAL'},
                            USES_TACTIC: {orientation: 'NATURAL'},
                            USES_TECHNIQUE: {orientation: 'NATURAL'},
                            ENABLES_TECHNIQUE: {orientation: 'NATURAL'},
                            INDICATES: {orientation: 'NATURAL'}
                        }
                    )
                    """,
                    {"name": self.graph_name}
                )
                
                logger.info(f"  ✅ Graph projection created in {metrics.compute_time:.2f} seconds")
                logger.info(f"  Memory used: {metrics.memory_used / 1024 / 1024:.1f} MB")
    
    def run_pagerank(self):
        """Run PageRank with monitoring"""
        logger.info("\n🔄 Running PageRank algorithm...")
        
        with self.operation_context("pagerank") as op_id:
            try:
                # Run PageRank with monitoring
                metrics = self._run_monitored_algorithm(
                    "pagerank",
                    """
                    CALL gds.pageRank.write(
                        $name,
                        {
                            writeProperty: 'pagerank',
                            maxIterations: 20,
                            dampingFactor: 0.85,
                            concurrency: 4
                        }
                    )
                    """,
                    {"name": self.graph_name}
                )
                
                logger.info(f"  ✅ PageRank completed in {metrics.compute_time:.2f} seconds")
                logger.info(f"  Memory used: {metrics.memory_used / 1024 / 1024:.1f} MB")
                logger.info(f"  Nodes scored: {metrics.nodes_processed:,}")
                
                # Get top nodes by PageRank
                self._get_top_nodes_by_pagerank()
                
            except Exception as e:
                logger.error(f"❌ PageRank failed: {e}")
                raise
    
    def _get_top_nodes_by_pagerank(self):
        """Get top nodes by PageRank score"""
        with self.neo4j.session() as session:
            # Get top CVEs
            logger.info("\n📊 Top CVEs by PageRank:")
            result = session.run("""
                MATCH (c:CVE)
                WHERE c.pagerank IS NOT NULL
                RETURN c.id AS cve_id, c.severity AS severity, c.pagerank AS score
                ORDER BY c.pagerank DESC
                LIMIT 10
            """)
            
            for i, record in enumerate(result):
                logger.info(f"  {i+1}. {record['cve_id']} (Severity: {record['severity']}, Score: {record['score']:.6f})")
            
            # Get top ThreatIntel
            logger.info("\n📊 Top Threat Intelligence by PageRank:")
            result = session.run("""
                MATCH (t:ThreatIntel)
                WHERE t.pagerank IS NOT NULL
                RETURN t.id AS threat_id, t.title AS title, t.severity AS severity, t.pagerank AS score
                ORDER BY t.pagerank DESC
                LIMIT 10
            """)
            
            for i, record in enumerate(result):
                logger.info(f"  {i+1}. {record['threat_id']} - {record['title']} (Severity: {record['severity']}, Score: {record['score']:.6f})")
    
    def run_betweenness_centrality(self):
        """Run betweenness centrality with monitoring"""
        logger.info("\n🔄 Running Betweenness Centrality algorithm...")
        
        with self.operation_context("betweenness") as op_id:
            try:
                # Run betweenness with monitoring
                metrics = self._run_monitored_algorithm(
                    "betweenness",
                    """
                    CALL gds.betweenness.write(
                        $name,
                        {
                            writeProperty: 'betweenness',
                            samplingSize: 100,
                            concurrency: 4
                        }
                    )
                    """,
                    {"name": self.graph_name}
                )
                
                logger.info(f"  ✅ Betweenness completed in {metrics.compute_time:.2f} seconds")
                logger.info(f"  Memory used: {metrics.memory_used / 1024 / 1024:.1f} MB")
                logger.info(f"  Nodes scored: {metrics.nodes_processed:,}")
                
                # Get top bridge nodes
                self._get_top_bridge_nodes()
                
            except Exception as e:
                logger.error(f"❌ Betweenness failed: {e}")
                raise
    
    def _get_top_bridge_nodes(self):
        """Get top bridge nodes by betweenness centrality"""
        with self.neo4j.session() as session:
            logger.info("\n📊 Top Bridge Nodes:")
            result = session.run("""
                MATCH (n)
                WHERE n.betweenness IS NOT NULL AND n.betweenness > 0
                WITH labels(n)[0] AS node_type, n
                ORDER BY n.betweenness DESC
                LIMIT 20
                RETURN node_type, 
                       CASE 
                         WHEN n:CVE THEN n.id
                         WHEN n:ThreatIntel THEN n.title
                         WHEN n:Product THEN n.name
                         WHEN n:Vendor THEN n.name
                         WHEN n:CWE THEN n.id
                         WHEN n:MitreTactic THEN n.name
                         WHEN n:MitreTechnique THEN n.name
                         WHEN n:IOC THEN n.value
                         ELSE 'Unknown'
                       END AS name,
                       n.betweenness AS score
                ORDER BY n.betweenness DESC
            """)
            
            for i, record in enumerate(result):
                logger.info(f"  {i+1}. [{record['node_type']}] {record['name']} (Score: {record['score']:.2f})")
    
    def run_community_detection(self):
        """Run Louvain community detection with monitoring"""
        logger.info("\n🔄 Running Louvain Community Detection algorithm...")
        
        with self.operation_context("louvain") as op_id:
            try:
                # Run Louvain with monitoring
                metrics = self._run_monitored_algorithm(
                    "louvain",
                    """
                    CALL gds.louvain.write(
                        $name,
                        {
                            writeProperty: 'community',
                            includeIntermediateCommunities: false,
                            concurrency: 4
                        }
                    )
                    """,
                    {"name": self.graph_name}
                )
                
                logger.info(f"  ✅ Louvain completed in {metrics.compute_time:.2f} seconds")
                logger.info(f"  Memory used: {metrics.memory_used / 1024 / 1024:.1f} MB")
                logger.info(f"  Communities found: {metrics.nodes_processed:,}")
                
                # Get community statistics
                self._get_community_statistics()
                
            except Exception as e:
                logger.error(f"❌ Louvain failed: {e}")
                raise
    
    def _get_community_statistics(self):
        """Get community statistics"""
        with self.neo4j.session() as session:
            # Get community distribution
            logger.info("\n📊 Community Size Distribution:")
            result = session.run("""
                MATCH (n)
                WHERE n.community IS NOT NULL
                WITH n.community AS community, count(*) AS size
                ORDER BY size DESC
                LIMIT 10
                RETURN community, size
            """)
            
            for i, record in enumerate(result):
                logger.info(f"  Community {record['community']}: {record['size']:,} nodes")
            
            # Get node type distribution in top community
            top_community = session.run("""
                MATCH (n)
                WHERE n.community IS NOT NULL
                WITH n.community AS community, count(*) AS size
                ORDER BY size DESC
                LIMIT 1
                RETURN community
            """).single()["community"]
            
            logger.info(f"\n📊 Node Type Distribution in Top Community (ID: {top_community}):")
            result = session.run("""
                MATCH (n)
                WHERE n.community = $community
                WITH labels(n)[0] AS node_type, count(*) AS count
                ORDER BY count DESC
                RETURN node_type, count
            """, community=top_community)
            
            for record in result:
                logger.info(f"  {record['node_type']}: {record['count']:,} nodes")
    
    def run_node_similarity(self):
        """Run node similarity with monitoring"""
        logger.info("\n🔄 Running Node Similarity algorithm...")
        
        with self.operation_context("node_similarity") as op_id:
            try:
                # Create product subgraph
                product_graph = "product-similarity-graph"
                
                # Clean up existing graph first
                with self.neo4j.session() as session:
                    result = session.run("CALL gds.graph.exists($name)", name=product_graph)
                    if result.single()["exists"]:
                        logger.info(f"  Dropping existing graph '{product_graph}'")
                        session.run("CALL gds.graph.drop($name)", name=product_graph)
                
                # Create product-specific projection
                metrics = self._run_monitored_algorithm(
                    "create_product_graph",
                    """
                    CALL gds.graph.project(
                        $name,
                        ['Product', 'CVE'],
                        {
                            AFFECTS: {
                                orientation: 'REVERSE',
                                properties: {}
                            }
                        }
                    )
                    """,
                    {"name": product_graph}
                )
                
                logger.info(f"  Product graph created in {metrics.compute_time:.2f} seconds")
                
                # Run node similarity
                metrics = self._run_monitored_algorithm(
                    "node_similarity",
                    """
                    CALL gds.nodeSimilarity.write(
                        $name,
                        {
                            writeProperty: 'similarity',
                            writeRelationshipType: 'SIMILAR',
                            similarityCutoff: 0.5,
                            concurrency: 4
                        }
                    )
                    """,
                    {"name": product_graph}
                )
                
                logger.info(f"  ✅ Node Similarity completed in {metrics.compute_time:.2f} seconds")
                logger.info(f"  Memory used: {metrics.memory_used / 1024 / 1024:.1f} MB")
                logger.info(f"  Relationships created: {metrics.relationships_processed:,}")
                
                # Get similar products
                self._get_similar_products()
                
                # Clean up
                with self.neo4j.session() as session:
                    session.run("CALL gds.graph.drop($name)", name=product_graph)
                
            except Exception as e:
                logger.error(f"❌ Node Similarity failed: {e}")
                raise
    
    def _get_similar_products(self):
        """Get similar products"""
        with self.neo4j.session() as session:
            logger.info("\n📊 Top Similar Products:")
            result = session.run("""
                MATCH (p1:Product)-[s:SIMILAR]->(p2:Product)
                RETURN p1.name AS product1, p2.name AS product2, s.similarity AS similarity
                ORDER BY s.similarity DESC
                LIMIT 10
            """)
            
            for i, record in enumerate(result):
                logger.info(f"  {i+1}. {record['product1']} ⟷ {record['product2']} (Similarity: {record['similarity']:.4f})")
    
    def calculate_risk_scores(self):
        """Calculate risk scores with monitoring"""
        logger.info("\n⚠️ Calculating risk scores...")
        
        with self.operation_context("risk_scores") as op_id:
            try:
                with self.neo4j.session() as session:
                    # Calculate base risk
                    start_time = time.time()
                    session.run("""
                        MATCH (p:Product)<-[:AFFECTS]-(c:CVE)
                        WHERE c.pagerank IS NOT NULL
                        WITH p, avg(c.cvss_v3) AS base_cvss, sum(c.pagerank) AS pagerank_sum
                        SET p.base_risk = base_cvss,
                            p.pagerank_score = pagerank_sum
                    """)
                    
                    # Threat intelligence amplification
                    session.run("""
                        MATCH (p:Product)<-[:AFFECTS]-(c:CVE)<-[:REFERENCES]-(t:ThreatIntel)
                        WITH p, count(DISTINCT t) AS threat_count
                        SET p.threat_amplifier = 1 + (threat_count * 0.1)
                    """)
                    
                    # Community risk factor
                    session.run("""
                        MATCH (p:Product)
                        WHERE p.community IS NOT NULL
                        WITH p.community AS community, avg(coalesce(p.base_risk, 0)) AS avg_community_risk
                        MATCH (p:Product)
                        WHERE p.community = community
                        SET p.community_risk = avg_community_risk
                    """)
                    
                    # Final risk score
                    session.run("""
                        MATCH (p:Product)
                        WHERE p.base_risk IS NOT NULL
                        SET p.risk_score = p.base_risk * 
                                      coalesce(p.threat_amplifier, 1) * 
                                      (1 + coalesce(p.community_risk, 0) * 0.2)
                    """)
                    
                    # Get top risky products
                    logger.info("\n📊 Top High-Risk Products:")
                    result = session.run("""
                        MATCH (p:Product)
                        WHERE p.risk_score IS NOT NULL
                        RETURN p.name AS product, 
                               p.risk_score AS risk_score,
                               p.base_risk AS base_risk,
                               p.threat_amplifier AS threat_amplifier,
                               p.community_risk AS community_risk
                        ORDER BY p.risk_score DESC
                        LIMIT 10
                    """)
                    
                    for i, record in enumerate(result):
                        logger.info(f"  {i+1}. {record['product']} (Risk Score: {record['risk_score']:.2f})")
                        base_risk = record['base_risk'] if record['base_risk'] is not None else 0
                        threat_amplifier = record.get('threat_amplifier', 1) if record.get('threat_amplifier') is not None else 1
                        community_risk = record.get('community_risk', 0) if record.get('community_risk') is not None else 0
                        logger.info(f"     Base Risk: {base_risk:.2f}, Threat Amplifier: {threat_amplifier:.2f}, Community Risk: {community_risk:.2f}")
                    
                    # Update metrics
                    self.monitoring.operations.end_operation(
                        "risk_scores",
                        success=True,
                        items=self.stats.get("nodes", 0)
                    )
                    
            except Exception as e:
                logger.error(f"❌ Risk score calculation failed: {e}")
                raise
    
    def export_visualization_data(self):
        """Export visualization data with monitoring"""
        logger.info("\n📊 Exporting visualization data...")
        
        with self.operation_context("export_visualization") as op_id:
            try:
                with self.neo4j.session() as session:
                    # Export top CVEs
                    result = session.run("""
                        MATCH (c:CVE)
                        WHERE c.pagerank IS NOT NULL
                        WITH c ORDER BY c.pagerank DESC LIMIT 100
                        MATCH (c)-[:AFFECTS]->(p:Product)
                        RETURN c.id AS cve_id, 
                               c.severity AS severity, 
                               c.pagerank AS pagerank,
                               collect(p.name) AS affected_products
                    """)
                    
                    cves = [dict(record) for record in result]
                    logger.info(f"  Exported {len(cves)} top CVEs")
                    
                    # Export top threats
                    result = session.run("""
                        MATCH (t:ThreatIntel)
                        WHERE t.pagerank IS NOT NULL
                        WITH t ORDER BY t.pagerank DESC LIMIT 50
                        MATCH (i:IOC)-[:INDICATES]->(t)
                        RETURN t.id AS threat_id,
                               t.title AS title,
                               t.severity AS severity,
                               t.pagerank AS pagerank,
                               collect({type: i.type, value: i.value}) AS iocs
                    """)
                    
                    threats = [dict(record) for record in result]
                    logger.info(f"  Exported {len(threats)} top threats")
                    
                    # Export communities
                    result = session.run("""
                        MATCH (n)
                        WHERE n.community IS NOT NULL
                        WITH n.community AS community, count(*) AS size
                        ORDER BY size DESC
                        LIMIT 10
                        RETURN community, size
                    """)
                    
                    communities = [dict(record) for record in result]
                    logger.info(f"  Exported {len(communities)} communities")
                    
                    # Write to files
                    import json
                    Path("/tmp/visualization").mkdir(exist_ok=True)
                    
                    with open("/tmp/visualization/top_cves.json", "w") as f:
                        json.dump(cves, f, indent=2)
                    
                    with open("/tmp/visualization/top_threats.json", "w") as f:
                        json.dump(threats, f, indent=2)
                    
                    with open("/tmp/visualization/communities.json", "w") as f:
                        json.dump(communities, f, indent=2)
                    
                    logger.info("  ✅ Data exported to /tmp/visualization/")
                    
                    # Update metrics
                    self.monitoring.operations.end_operation(
                        "export_visualization",
                        success=True,
                        items=len(cves) + len(threats) + len(communities)
                    )
                    
            except Exception as e:
                logger.error(f"❌ Visualization export failed: {e}")
                raise
    
    def run_all_analytics(self):
        """Run all analytics with monitoring"""
        start_time = time.time()
        
        try:
            # Create graph projection
            self.create_graph_projection()
            
            # Run PageRank
            self.run_pagerank()
            
            # Run betweenness centrality
            self.run_betweenness_centrality()
            
            # Run community detection
            self.run_community_detection()
            
            # Run node similarity
            self.run_node_similarity()
            
            # Calculate risk scores
            self.calculate_risk_scores()
            
            # Export visualization data
            self.export_visualization_data()
            
            # Report
            elapsed = time.time() - start_time
            logger.info("\n" + "="*80)
            logger.info("📊 GRAPH ANALYTICS COMPLETE")
            logger.info("="*80)
            logger.info(f"Nodes analyzed:       {self.stats.get('nodes', 0):,}")
            logger.info(f"Relationships:        {self.stats.get('relationships', 0):,}")
            logger.info(f"\n⏱️  Total time: {elapsed/60:.1f} minutes")
            logger.info("="*80)
            
            # Final monitoring report
            logger.info("\n" + "="*80)
            logger.info("⚡ SYSTEM PERFORMANCE REPORT")
            logger.info("="*80)
            logger.info(self.monitoring.resources.get_resource_summary())
            logger.info(self.monitoring.operations.get_summary())
            logger.info("="*80)
            
            # Algorithm metrics summary
            logger.info("\n" + "="*80)
            logger.info("🔬 ALGORITHM PERFORMANCE")
            logger.info("="*80)
            for metrics in self.algorithm_metrics:
                logger.info(f"\n{metrics.name}:")
                logger.info(f"  Time:      {metrics.compute_time:.2f}s")
                logger.info(f"  Memory:    {metrics.memory_used / 1024 / 1024:.1f}MB")
                logger.info(f"  Processed: {metrics.nodes_processed + metrics.relationships_processed:,} items")
                if not metrics.success:
                    logger.info(f"  Error:     {metrics.error}")
            logger.info("="*80)
            
        except Exception as e:
            logger.exception("❌ Analytics failed")
            raise
        finally:
            self.close()

def main():
    """Main function"""
    analytics = EnterpriseGraphAnalytics()
    analytics.run_all_analytics()

if __name__ == "__main__":
    main()
