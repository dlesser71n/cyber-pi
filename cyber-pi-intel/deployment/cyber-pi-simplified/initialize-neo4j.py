#!/usr/bin/env python3
"""
Initialize Neo4j with Cyber Threat Intelligence Graph Schema
Creates self-descriptive database and constraints for threat intelligence
"""

from neo4j import GraphDatabase
import sys

# Connect via internal Kubernetes service (ClusterIP)
# If running outside cluster, use: kubectl port-forward -n cyber-pi-intel svc/neo4j 7687:7687
NEO4J_URI = "bolt://neo4j.cyber-pi-intel.svc.cluster.local:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "cyber-pi-neo4j-2025"
DATABASE_NAME = "cyberpi_threat_intel"  # Self-descriptive database name

def initialize_neo4j_graph():
    """Create Neo4j graph schema for cyber-pi threat intelligence"""
    
    print("Connecting to Neo4j...")
    driver = GraphDatabase.driver(
        NEO4J_URI,
        auth=(NEO4J_USER, NEO4J_PASSWORD)
    )
    
    # Verify connection
    try:
        driver.verify_connectivity()
        print("✅ Connected to Neo4j")
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        sys.exit(1)
    
    # Note: Neo4j Community Edition uses default "neo4j" database
    # Enterprise Edition allows multiple databases
    # For now, we'll use the default database but with descriptive node labels
    
    with driver.session() as session:
        print("\n📊 Creating graph schema for Cyber Threat Intelligence...")
        
        # Create constraints for unique identifiers
        constraints = [
            ("CyberThreat", "threatId"),
            ("ThreatActor", "actorName"),
            ("Industry", "industryName"),
            ("CVE", "cveId"),
            ("TTP", "ttpId"),  # Tactics, Techniques, Procedures
            ("IOC", "iocValue"),  # Indicators of Compromise
            ("Vendor", "vendorName"),
            ("Product", "productName"),
            ("MitreTactic", "tacticId"),
            ("MitreTechnique", "techniqueId")
        ]
        
        print("\n1️⃣ Creating uniqueness constraints...")
        for node_label, property_name in constraints:
            try:
                query = f"""
                CREATE CONSTRAINT {node_label.lower()}_{property_name}_unique IF NOT EXISTS
                FOR (n:{node_label})
                REQUIRE n.{property_name} IS UNIQUE
                """
                session.run(query)
                print(f"   ✅ {node_label}.{property_name} - unique constraint")
            except Exception as e:
                print(f"   ⚠️  {node_label}.{property_name} - {str(e)[:50]}")
        
        # Create indexes for better query performance
        indexes = [
            ("CyberThreat", "severity"),
            ("CyberThreat", "publishedDate"),
            ("CyberThreat", "ingestedDate"),
            ("Industry", "industryName"),
            ("ThreatActor", "actorName"),
            ("MitreTactic", "name"),
            ("MitreTechnique", "name")
        ]
        
        print("\n2️⃣ Creating performance indexes...")
        for node_label, property_name in indexes:
            try:
                query = f"""
                CREATE INDEX {node_label.lower()}_{property_name}_index IF NOT EXISTS
                FOR (n:{node_label})
                ON (n.{property_name})
                """
                session.run(query)
                print(f"   ✅ {node_label}.{property_name} - indexed")
            except Exception as e:
                print(f"   ⚠️  {node_label}.{property_name} - {str(e)[:50]}")
        
        # Create initial industry nodes (18 verticals from cyber-pi)
        print("\n3️⃣ Creating industry nodes...")
        industries = [
            "Aviation & Airlines",
            "Healthcare & Medical",
            "Energy & Utilities",
            "Financial Services",
            "Manufacturing",
            "Retail & E-commerce",
            "Technology",
            "Telecommunications",
            "Government & Public Sector",
            "Education",
            "Transportation & Logistics",
            "Hospitality & Entertainment",
            "Real Estate",
            "Agriculture",
            "Mining & Resources",
            "Professional Services",
            "Media & Publishing",
            "Pharmaceuticals"
        ]
        
        for industry in industries:
            query = """
            MERGE (i:Industry {industryName: $name})
            ON CREATE SET 
                i.created = datetime(),
                i.threatCount = 0,
                i.description = $description
            """
            session.run(query, name=industry, description=f"Threat intelligence for {industry}")
            print(f"   ✅ {industry}")
        
        # Document the graph schema
        print("\n4️⃣ Creating schema documentation node...")
        schema_doc = """
        MERGE (schema:GraphSchema {name: 'CyberPI_ThreatIntel_Schema'})
        SET schema.version = '1.0',
            schema.created = datetime(),
            schema.description = 'Cyber threat intelligence graph for cyber-pi system',
            schema.nodeTypes = [
                'CyberThreat - Individual threat intelligence items',
                'ThreatActor - Threat actors and groups',
                'Industry - Target industries (18 verticals)',
                'CVE - Common Vulnerabilities and Exposures',
                'TTP - Tactics, Techniques, and Procedures',
                'IOC - Indicators of Compromise',
                'Vendor - Affected vendors',
                'Product - Affected products',
                'MitreTactic - MITRE ATT&CK tactics',
                'MitreTechnique - MITRE ATT&CK techniques'
            ],
            schema.relationshipTypes = [
                'TARGETS - CyberThreat targets Industry',
                'ATTRIBUTED_TO - CyberThreat attributed to ThreatActor',
                'EXPLOITS - CyberThreat exploits CVE',
                'USES - ThreatActor uses TTP',
                'CONTAINS - CyberThreat contains IOC',
                'AFFECTS - CyberThreat affects Vendor/Product',
                'INVOLVES_TACTIC - CyberThreat involves MitreTactic',
                'USES_TECHNIQUE - CyberThreat uses MitreTechnique',
                'RELATED_TO - CyberThreat related to CyberThreat',
                'SIMILAR_TO - ThreatActor similar to ThreatActor',
                'PART_OF - MitreTechnique part of MitreTactic'
            ]
        """
        session.run(schema_doc)
        print("   ✅ Schema documentation created")
        
        # Get statistics
        print("\n📊 Graph Statistics:")
        stats = session.run("""
            MATCH (n)
            RETURN labels(n)[0] as label, count(*) as count
            ORDER BY count DESC
        """).data()
        
        for stat in stats:
            print(f"   {stat['label']:20s}: {stat['count']:3d} nodes")
        
        # Get constraint count
        constraints_count = session.run("""
            SHOW CONSTRAINTS
        """).data()
        print(f"\n   Constraints: {len(constraints_count)}")
        
        # Get index count
        indexes_count = session.run("""
            SHOW INDEXES
        """).data()
        print(f"   Indexes: {len(indexes_count)}")
    
    driver.close()
    print("\n✅ Neo4j initialization complete!")
    print(f"   Graph ready for cyber threat intelligence relationships")
    
    return True

def print_example_queries():
    """Print example Cypher queries for the schema"""
    print("\n" + "="*60)
    print("📝 Example Cypher Queries")
    print("="*60)
    
    examples = [
        ("Find all threats targeting Aviation", """
        MATCH (t:CyberThreat)-[:TARGETS]->(i:Industry {industryName: 'Aviation & Airlines'})
        RETURN t.threatId, t.title, t.severity, t.publishedDate
        ORDER BY t.publishedDate DESC
        LIMIT 10
        """),
        
        ("Find threats by specific actor", """
        MATCH (actor:ThreatActor {actorName: 'Lockbit'})-[:ATTRIBUTED_TO]-(t:CyberThreat)
        RETURN t.threatId, t.title, t.severity
        """),
        
        ("Find attack chain for a threat", """
        MATCH path = (t:CyberThreat {threatId: 'THREAT_ID'})
                     -[:USES_TECHNIQUE]->(tech:MitreTechnique)
                     -[:PART_OF]->(tactic:MitreTactic)
        RETURN path
        """),
        
        ("Find related threats", """
        MATCH (t1:CyberThreat {threatId: 'THREAT_ID'})
              -[:RELATED_TO]-(t2:CyberThreat)
        RETURN t2.threatId, t2.title, t2.severity
        """),
        
        ("Find all IOCs for an industry", """
        MATCH (t:CyberThreat)-[:TARGETS]->(i:Industry {industryName: 'Healthcare & Medical'})
        MATCH (t)-[:CONTAINS]->(ioc:IOC)
        RETURN DISTINCT ioc.iocValue, ioc.iocType
        """),
        
        ("Industry threat statistics", """
        MATCH (i:Industry)
        OPTIONAL MATCH (t:CyberThreat)-[:TARGETS]->(i)
        RETURN i.industryName,
               count(t) as threatCount,
               count(CASE WHEN t.severity = 'critical' THEN 1 END) as criticalCount,
               count(CASE WHEN t.severity = 'high' THEN 1 END) as highCount
        ORDER BY threatCount DESC
        """)
    ]
    
    for i, (description, query) in enumerate(examples, 1):
        print(f"\n{i}. {description}:")
        print("-" * 60)
        print(query.strip())

if __name__ == "__main__":
    try:
        initialize_neo4j_graph()
        print_example_queries()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
