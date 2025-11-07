#!/usr/bin/env python3
"""
Graph Analytics for Unified Threat Graph
Implements advanced graph algorithms using Neo4j Graph Data Science
"""

import sys
import os
import logging
import os
import time
import os
from pathlib import Path
from typing import Dict, List, Any, Optional

from neo4j import GraphDatabase
from tqdm import tqdm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("/tmp/graph_analytics.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class GraphAnalytics:
    """Graph analytics for the unified threat graph"""
    
    def __init__(
        self, 
        neo4j_uri: str = "bolt://10.152.183.169:7687", 
        neo4j_user: str = "neo4j", 
        neo4j_password: Optional[str] = None
    ):
        """Initialize the graph analytics"""
        self.neo4j = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        self.graph_name = "unified-threat-graph"
        self.stats = {}
        
    def close(self):
        """Close the Neo4j connection"""
        self.neo4j.close()
        
    def create_graph_projection(self):
        """Create a graph projection for analysis"""
        logger.info("\n🔍 Creating graph projection...")
        
        with self.neo4j.session() as session:
            # Check if graph already exists
            result = session.run("CALL gds.graph.exists($name)", name=self.graph_name)
            exists = result.single()["exists"]
            
            if exists:
                logger.info(f"  Graph projection '{self.graph_name}' already exists")
                # Get graph info
                result = session.run("CALL gds.graph.list($name)", name=self.graph_name)
                graph_info = result.single()
                logger.info(f"  Nodes: {graph_info['nodeCount']:,}, Relationships: {graph_info['relationshipCount']:,}")
                return
            
            # Create graph projection
            logger.info("  Creating new graph projection...")
            result = session.run("""
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
            """, name=self.graph_name)
            
            graph_info = result.single()
            logger.info(f"  ✅ Graph projection created with {graph_info['nodeCount']:,} nodes and {graph_info['relationshipCount']:,} relationships")
            
            # Store stats
            self.stats["nodes"] = graph_info["nodeCount"]
            self.stats["relationships"] = graph_info["relationshipCount"]
            
    def run_pagerank(self):
        """Run PageRank to identify most critical nodes"""
        logger.info("\n🔄 Running PageRank algorithm...")
        
        with self.neo4j.session() as session:
            # Run PageRank
            result = session.run("""
                CALL gds.pageRank.write(
                    $name,
                    {
                        writeProperty: 'pagerank',
                        maxIterations: 20,
                        dampingFactor: 0.85
                    }
                )
            """, name=self.graph_name)
            
            info = result.single()
            logger.info(f"  ✅ PageRank completed in {info['computeMillis']/1000:.2f} seconds")
            logger.info(f"  Nodes scored: {info['nodePropertiesWritten']:,}")
            
            # Get top CVEs by PageRank
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
                
            # Get top ThreatIntel by PageRank
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
        """Run betweenness centrality to identify bridge nodes"""
        logger.info("\n🔄 Running Betweenness Centrality algorithm...")
        
        with self.neo4j.session() as session:
            # Run betweenness centrality
            result = session.run("""
                CALL gds.betweenness.write(
                    $name,
                    {
                        writeProperty: 'betweenness',
                        samplingSize: 100
                    }
                )
            """, name=self.graph_name)
            
            info = result.single()
            logger.info(f"  ✅ Betweenness Centrality completed in {info['computeMillis']/1000:.2f} seconds")
            logger.info(f"  Nodes scored: {info['nodePropertiesWritten']:,}")
            
            # Get top bridge nodes
            logger.info("\n📊 Top Bridge Nodes (Betweenness Centrality):")
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
        """Run Louvain community detection to identify clusters"""
        logger.info("\n🔄 Running Louvain Community Detection algorithm...")
        
        with self.neo4j.session() as session:
            # Run Louvain
            result = session.run("""
                CALL gds.louvain.write(
                    $name,
                    {
                        writeProperty: 'community',
                        includeIntermediateCommunities: false
                    }
                )
            """, name=self.graph_name)
            
            info = result.single()
            logger.info(f"  ✅ Louvain completed in {info['computeMillis']/1000:.2f} seconds")
            logger.info(f"  Communities found: {info['communityCount']:,}")
            logger.info(f"  Nodes assigned: {info['nodePropertiesWritten']:,}")
            
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
        """Run node similarity to find similar products"""
        logger.info("\n🔄 Running Node Similarity algorithm for products...")
        
        with self.neo4j.session() as session:
            # Create a subgraph projection for products
            product_graph = "product-similarity-graph"
            
            # Check if graph exists
            result = session.run("CALL gds.graph.exists($name)", name=product_graph)
            if result.single()["exists"]:
                # Drop existing graph
                session.run("CALL gds.graph.drop($name)", name=product_graph)
            
            # Create product-specific projection
            result = session.run("""
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
            """, name=product_graph)
            
            graph_info = result.single()
            logger.info(f"  Product graph created with {graph_info['nodeCount']:,} nodes and {graph_info['relationshipCount']:,} relationships")
            
            # Run node similarity
            result = session.run("""
                CALL gds.nodeSimilarity.write(
                    $name,
                    {
                        writeProperty: 'similarity',
                        writeRelationshipType: 'SIMILAR',
                        similarityCutoff: 0.5
                    }
                )
            """, name=product_graph)
            
            info = result.single()
            logger.info(f"  ✅ Node Similarity completed in {info['computeMillis']/1000:.2f} seconds")
            logger.info(f"  Relationships created: {info['relationshipsWritten']:,}")
            
            # Get top similar products
            logger.info("\n📊 Top Similar Products:")
            result = session.run("""
                MATCH (p1:Product)-[s:SIMILAR]->(p2:Product)
                RETURN p1.name AS product1, p2.name AS product2, s.similarity AS similarity
                ORDER BY s.similarity DESC
                LIMIT 10
            """)
            
            for i, record in enumerate(result):
                logger.info(f"  {i+1}. {record['product1']} ⟷ {record['product2']} (Similarity: {record['similarity']:.4f})")
            
            # Clean up
            session.run("CALL gds.graph.drop($name)", name=product_graph)
    
    def calculate_risk_scores(self):
        """Calculate risk scores for products based on PageRank and community"""
        logger.info("\n⚠️ Calculating risk scores...")
        
        with self.neo4j.session() as session:
            # Calculate base risk from CVE severity and PageRank
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
            
            # Community risk factor (products in same community as high-risk products)
            session.run("""
                MATCH (p:Product)
                WHERE p.community IS NOT NULL
                WITH p.community AS community, avg(coalesce(p.base_risk, 0)) AS avg_community_risk
                MATCH (p:Product)
                WHERE p.community = community
                SET p.community_risk = avg_community_risk
            """)
            
            # Final risk score calculation
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
    
    def export_visualization_data(self):
        """Export data for visualization"""
        logger.info("\n📊 Exporting visualization data...")
        
        with self.neo4j.session() as session:
            # Export top CVEs with their connections
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
            logger.info(f"  Exported {len(cves)} top CVEs for visualization")
            
            # Export top threat intel with IOCs
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
            logger.info(f"  Exported {len(threats)} top threats for visualization")
            
            # Export community data
            result = session.run("""
                MATCH (n)
                WHERE n.community IS NOT NULL
                WITH n.community AS community, count(*) AS size
                ORDER BY size DESC
                LIMIT 10
                RETURN community, size
            """)
            
            communities = [dict(record) for record in result]
            logger.info(f"  Exported {len(communities)} communities for visualization")
            
        # Write data to files
        import json
        Path("/tmp/visualization").mkdir(exist_ok=True)
        
        with open("/tmp/visualization/top_cves.json", "w") as f:
            json.dump(cves, f, indent=2)
            
        with open("/tmp/visualization/top_threats.json", "w") as f:
            json.dump(threats, f, indent=2)
            
        with open("/tmp/visualization/communities.json", "w") as f:
            json.dump(communities, f, indent=2)
            
        logger.info("  ✅ Visualization data exported to /tmp/visualization/")
    
    def run_all_analytics(self):
        """Run all graph analytics"""
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
            
        except Exception as e:
            logger.error(f"❌ Analytics failed: {e}")
            raise
        finally:
            self.close()

def main():
    """Main function"""
    analytics = GraphAnalytics()
    analytics.run_all_analytics()

if __name__ == "__main__":
    main()
