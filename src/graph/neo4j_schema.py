#!/usr/bin/env python3
"""
Neo4j Schema Manager for Cyber-PI Ontology
Creates constraints, indexes, and manages graph schema

Built to Rickover standards: Production-ready, type-safe, comprehensive
"""

import logging
from typing import List, Dict, Any, Optional
from neo4j import AsyncGraphDatabase, AsyncDriver
import asyncio

logger = logging.getLogger(__name__)


class Neo4jSchemaManager:
    """
    Manages Neo4j schema for Cyber-PI ontology
    - Creates constraints (uniqueness, existence)
    - Creates indexes (performance)
    - Validates schema
    - Provides schema introspection
    """
    
    def __init__(self, uri: str, user: str, password: str):
        """Initialize schema manager"""
        self.uri = uri
        self.user = user
        self.password = password
        self.driver: Optional[AsyncDriver] = None
    
    async def connect(self) -> None:
        """Establish connection to Neo4j"""
        self.driver = AsyncGraphDatabase.driver(
            self.uri,
            auth=(self.user, self.password)
        )
        logger.info(f"Connected to Neo4j at {self.uri}")
    
    async def close(self) -> None:
        """Close connection"""
        if self.driver:
            await self.driver.close()
            logger.info("Closed Neo4j connection")
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
    
    # ========================================================================
    # CONSTRAINT CREATION
    # ========================================================================
    
    async def create_unique_constraints(self) -> None:
        """
        Create uniqueness constraints
        Ensures entity IDs are unique across the graph
        """
        constraints = [
            # Core Entities
            "CREATE CONSTRAINT cve_id IF NOT EXISTS FOR (c:CVE) REQUIRE c.id IS UNIQUE",
            "CREATE CONSTRAINT cve_cve_id IF NOT EXISTS FOR (c:CVE) REQUIRE c.cve_id IS UNIQUE",
            "CREATE CONSTRAINT vendor_id IF NOT EXISTS FOR (v:Vendor) REQUIRE v.id IS UNIQUE",
            "CREATE CONSTRAINT product_id IF NOT EXISTS FOR (p:Product) REQUIRE p.id IS UNIQUE",
            "CREATE CONSTRAINT threat_actor_id IF NOT EXISTS FOR (t:ThreatActor) REQUIRE t.id IS UNIQUE",
            "CREATE CONSTRAINT malware_id IF NOT EXISTS FOR (m:Malware) REQUIRE m.id IS UNIQUE",
            "CREATE CONSTRAINT campaign_id IF NOT EXISTS FOR (c:Campaign) REQUIRE c.id IS UNIQUE",
            
            # IOCs
            "CREATE CONSTRAINT ioc_id IF NOT EXISTS FOR (i:IOC) REQUIRE i.id IS UNIQUE",
            "CREATE CONSTRAINT ioc_value IF NOT EXISTS FOR (i:IOC) REQUIRE (i.ioc_type, i.value) IS UNIQUE",
            
            # MITRE ATT&CK
            "CREATE CONSTRAINT tactic_id IF NOT EXISTS FOR (t:MitreTactic) REQUIRE t.tactic_id IS UNIQUE",
            "CREATE CONSTRAINT technique_id IF NOT EXISTS FOR (t:MitreTechnique) REQUIRE t.technique_id IS UNIQUE",
            
            # Breaches
            "CREATE CONSTRAINT breach_id IF NOT EXISTS FOR (b:Breach) REQUIRE b.id IS UNIQUE",
        ]
        
        async with self.driver.session() as session:
            for constraint in constraints:
                try:
                    await session.run(constraint)
                    logger.info(f"✓ Created constraint: {constraint.split()[2]}")
                except Exception as e:
                    logger.warning(f"Constraint may already exist: {e}")
    
    async def create_existence_constraints(self) -> None:
        """
        Create existence constraints (Enterprise Edition only)
        Ensures required properties exist
        """
        # Note: These require Neo4j Enterprise Edition
        constraints = [
            "CREATE CONSTRAINT cve_cve_id_exists IF NOT EXISTS FOR (c:CVE) REQUIRE c.cve_id IS NOT NULL",
            "CREATE CONSTRAINT vendor_name_exists IF NOT EXISTS FOR (v:Vendor) REQUIRE v.name IS NOT NULL",
            "CREATE CONSTRAINT product_name_exists IF NOT EXISTS FOR (p:Product) REQUIRE p.name IS NOT NULL",
            "CREATE CONSTRAINT threat_actor_name_exists IF NOT EXISTS FOR (t:ThreatActor) REQUIRE t.name IS NOT NULL",
        ]
        
        async with self.driver.session() as session:
            for constraint in constraints:
                try:
                    await session.run(constraint)
                    logger.info(f"✓ Created existence constraint")
                except Exception as e:
                    logger.debug(f"Existence constraint skipped (requires Enterprise): {e}")
    
    # ========================================================================
    # INDEX CREATION
    # ========================================================================
    
    async def create_property_indexes(self) -> None:
        """
        Create property indexes for common queries
        Dramatically improves query performance
        """
        indexes = [
            # CVE Indexes
            "CREATE INDEX cve_severity IF NOT EXISTS FOR (c:CVE) ON (c.severity)",
            "CREATE INDEX cve_published IF NOT EXISTS FOR (c:CVE) ON (c.published)",
            "CREATE INDEX cve_cvss_score IF NOT EXISTS FOR (c:CVE) ON (c.cvss_v3_score)",
            
            # Vendor Indexes
            "CREATE INDEX vendor_name IF NOT EXISTS FOR (v:Vendor) ON (v.name)",
            "CREATE INDEX vendor_risk IF NOT EXISTS FOR (v:Vendor) ON (v.risk_score)",
            "CREATE INDEX vendor_industry IF NOT EXISTS FOR (v:Vendor) ON (v.industry)",
            
            # Product Indexes
            "CREATE INDEX product_name IF NOT EXISTS FOR (p:Product) ON (p.name)",
            "CREATE INDEX product_vendor IF NOT EXISTS FOR (p:Product) ON (p.vendor_id)",
            "CREATE INDEX product_cve_count IF NOT EXISTS FOR (p:Product) ON (p.cve_count)",
            
            # Threat Actor Indexes
            "CREATE INDEX threat_actor_name IF NOT EXISTS FOR (t:ThreatActor) ON (t.name)",
            "CREATE INDEX threat_actor_type IF NOT EXISTS FOR (t:ThreatActor) ON (t.threat_actor_types)",
            "CREATE INDEX threat_actor_sophistication IF NOT EXISTS FOR (t:ThreatActor) ON (t.sophistication)",
            
            # Malware Indexes
            "CREATE INDEX malware_name IF NOT EXISTS FOR (m:Malware) ON (m.name)",
            "CREATE INDEX malware_type IF NOT EXISTS FOR (m:Malware) ON (m.malware_types)",
            
            # IOC Indexes
            "CREATE INDEX ioc_type IF NOT EXISTS FOR (i:IOC) ON (i.ioc_type)",
            "CREATE INDEX ioc_first_seen IF NOT EXISTS FOR (i:IOC) ON (i.first_seen)",
            "CREATE INDEX ioc_malicious IF NOT EXISTS FOR (i:IOC) ON (i.malicious)",
            
            # Breach Indexes
            "CREATE INDEX breach_date IF NOT EXISTS FOR (b:Breach) ON (b.breach_date)",
            "CREATE INDEX breach_severity IF NOT EXISTS FOR (b:Breach) ON (b.severity)",
            "CREATE INDEX breach_vendor IF NOT EXISTS FOR (b:Breach) ON (b.vendor_id)",
            
            # Temporal Indexes
            "CREATE INDEX entity_created IF NOT EXISTS FOR (n) ON (n.created)",
            "CREATE INDEX entity_modified IF NOT EXISTS FOR (n) ON (n.modified)",
        ]
        
        async with self.driver.session() as session:
            for index in indexes:
                try:
                    await session.run(index)
                    logger.info(f"✓ Created index: {index.split()[2]}")
                except Exception as e:
                    logger.warning(f"Index may already exist: {e}")
    
    async def create_fulltext_indexes(self) -> None:
        """
        Create full-text search indexes
        Enables text search across descriptions, names, etc.
        """
        indexes = [
            # CVE full-text search
            """
            CREATE FULLTEXT INDEX cve_fulltext IF NOT EXISTS
            FOR (c:CVE)
            ON EACH [c.cve_id, c.description]
            """,
            
            # Vendor full-text search
            """
            CREATE FULLTEXT INDEX vendor_fulltext IF NOT EXISTS
            FOR (v:Vendor)
            ON EACH [v.name, v.aliases]
            """,
            
            # Product full-text search
            """
            CREATE FULLTEXT INDEX product_fulltext IF NOT EXISTS
            FOR (p:Product)
            ON EACH [p.name, p.category]
            """,
            
            # Threat Actor full-text search
            """
            CREATE FULLTEXT INDEX threat_actor_fulltext IF NOT EXISTS
            FOR (t:ThreatActor)
            ON EACH [t.name, t.aliases, t.description]
            """,
            
            # Malware full-text search
            """
            CREATE FULLTEXT INDEX malware_fulltext IF NOT EXISTS
            FOR (m:Malware)
            ON EACH [m.name, m.aliases, m.description]
            """,
        ]
        
        async with self.driver.session() as session:
            for index in indexes:
                try:
                    await session.run(index)
                    logger.info(f"✓ Created fulltext index")
                except Exception as e:
                    logger.warning(f"Fulltext index may already exist: {e}")
    
    async def create_composite_indexes(self) -> None:
        """
        Create composite indexes for multi-property queries
        """
        indexes = [
            # CVE: severity + published date (common query pattern)
            "CREATE INDEX cve_severity_published IF NOT EXISTS FOR (c:CVE) ON (c.severity, c.published)",
            
            # Vendor: industry + risk score
            "CREATE INDEX vendor_industry_risk IF NOT EXISTS FOR (v:Vendor) ON (v.industry, v.risk_score)",
            
            # IOC: type + malicious flag
            "CREATE INDEX ioc_type_malicious IF NOT EXISTS FOR (i:IOC) ON (i.ioc_type, i.malicious)",
        ]
        
        async with self.driver.session() as session:
            for index in indexes:
                try:
                    await session.run(index)
                    logger.info(f"✓ Created composite index")
                except Exception as e:
                    logger.warning(f"Composite index may already exist: {e}")
    
    # ========================================================================
    # SCHEMA INITIALIZATION
    # ========================================================================
    
    async def initialize_schema(self) -> None:
        """
        Initialize complete schema
        Creates all constraints and indexes
        """
        logger.info("🚀 Initializing Neo4j schema...")
        
        try:
            # Constraints (must be created first)
            logger.info("Creating constraints...")
            await self.create_unique_constraints()
            await self.create_existence_constraints()
            
            # Indexes
            logger.info("Creating property indexes...")
            await self.create_property_indexes()
            
            logger.info("Creating fulltext indexes...")
            await self.create_fulltext_indexes()
            
            logger.info("Creating composite indexes...")
            await self.create_composite_indexes()
            
            logger.info("✅ Schema initialization complete")
            
        except Exception as e:
            logger.error(f"❌ Schema initialization failed: {e}")
            raise
    
    # ========================================================================
    # SCHEMA INTROSPECTION
    # ========================================================================
    
    async def get_constraints(self) -> List[Dict[str, Any]]:
        """Get all constraints in the database"""
        async with self.driver.session() as session:
            result = await session.run("SHOW CONSTRAINTS")
            constraints = []
            async for record in result:
                constraints.append(dict(record))
            return constraints
    
    async def get_indexes(self) -> List[Dict[str, Any]]:
        """Get all indexes in the database"""
        async with self.driver.session() as session:
            result = await session.run("SHOW INDEXES")
            indexes = []
            async for record in result:
                indexes.append(dict(record))
            return indexes
    
    async def get_node_labels(self) -> List[str]:
        """Get all node labels in the database"""
        async with self.driver.session() as session:
            result = await session.run("CALL db.labels()")
            labels = []
            async for record in result:
                labels.append(record[0])
            return labels
    
    async def get_relationship_types(self) -> List[str]:
        """Get all relationship types in the database"""
        async with self.driver.session() as session:
            result = await session.run("CALL db.relationshipTypes()")
            types = []
            async for record in result:
                types.append(record[0])
            return types
    
    async def get_schema_summary(self) -> Dict[str, Any]:
        """Get complete schema summary"""
        return {
            "constraints": await self.get_constraints(),
            "indexes": await self.get_indexes(),
            "node_labels": await self.get_node_labels(),
            "relationship_types": await self.get_relationship_types(),
        }
    
    # ========================================================================
    # SCHEMA VALIDATION
    # ========================================================================
    
    async def validate_schema(self) -> Dict[str, Any]:
        """
        Validate schema is correctly configured
        Returns validation report
        """
        logger.info("Validating schema...")
        
        validation = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "stats": {}
        }
        
        try:
            # Check constraints
            constraints = await self.get_constraints()
            validation["stats"]["constraints"] = len(constraints)
            
            if len(constraints) < 10:
                validation["warnings"].append(
                    f"Only {len(constraints)} constraints found. Expected at least 10."
                )
            
            # Check indexes
            indexes = await self.get_indexes()
            validation["stats"]["indexes"] = len(indexes)
            
            if len(indexes) < 20:
                validation["warnings"].append(
                    f"Only {len(indexes)} indexes found. Expected at least 20."
                )
            
            # Check node labels
            labels = await self.get_node_labels()
            validation["stats"]["node_labels"] = len(labels)
            
            expected_labels = [
                "CVE", "Vendor", "Product", "ThreatActor", "Malware",
                "Campaign", "IOC", "MitreTactic", "MitreTechnique", "Breach"
            ]
            
            missing_labels = [label for label in expected_labels if label not in labels]
            if missing_labels:
                validation["warnings"].append(
                    f"Missing expected labels: {missing_labels}"
                )
            
            # Overall validation
            if validation["errors"]:
                validation["valid"] = False
            
            logger.info(f"✅ Schema validation complete: {validation['stats']}")
            
        except Exception as e:
            validation["valid"] = False
            validation["errors"].append(str(e))
            logger.error(f"❌ Schema validation failed: {e}")
        
        return validation
    
    # ========================================================================
    # UTILITY METHODS
    # ========================================================================
    
    async def drop_all_constraints(self) -> None:
        """
        Drop all constraints (USE WITH CAUTION)
        Only for development/testing
        """
        logger.warning("⚠️  Dropping all constraints...")
        
        async with self.driver.session() as session:
            constraints = await self.get_constraints()
            for constraint in constraints:
                name = constraint.get("name")
                if name:
                    try:
                        await session.run(f"DROP CONSTRAINT {name}")
                        logger.info(f"Dropped constraint: {name}")
                    except Exception as e:
                        logger.error(f"Failed to drop constraint {name}: {e}")
    
    async def drop_all_indexes(self) -> None:
        """
        Drop all indexes (USE WITH CAUTION)
        Only for development/testing
        """
        logger.warning("⚠️  Dropping all indexes...")
        
        async with self.driver.session() as session:
            indexes = await self.get_indexes()
            for index in indexes:
                name = index.get("name")
                if name and not name.startswith("constraint_"):
                    try:
                        await session.run(f"DROP INDEX {name}")
                        logger.info(f"Dropped index: {name}")
                    except Exception as e:
                        logger.error(f"Failed to drop index {name}: {e}")
    
    async def reset_schema(self) -> None:
        """
        Reset schema completely (USE WITH EXTREME CAUTION)
        Drops all constraints and indexes, then recreates
        """
        logger.warning("⚠️  RESETTING SCHEMA - THIS WILL DROP EVERYTHING")
        
        await self.drop_all_indexes()
        await self.drop_all_constraints()
        await self.initialize_schema()
        
        logger.info("✅ Schema reset complete")


# ============================================================================
# CLI INTERFACE
# ============================================================================

async def main():
    """CLI for schema management"""
    import os
    import sys
    
    # Get credentials from environment
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD")
    
    if not password:
        print("❌ NEO4J_PASSWORD environment variable not set")
        sys.exit(1)
    
    # Parse command
    command = sys.argv[1] if len(sys.argv) > 1 else "init"
    
    async with Neo4jSchemaManager(uri, user, password) as manager:
        if command == "init":
            await manager.initialize_schema()
        
        elif command == "validate":
            validation = await manager.validate_schema()
            print(f"\n{'='*60}")
            print(f"Schema Validation: {'✅ VALID' if validation['valid'] else '❌ INVALID'}")
            print(f"{'='*60}")
            print(f"Stats: {validation['stats']}")
            if validation['warnings']:
                print(f"\nWarnings:")
                for warning in validation['warnings']:
                    print(f"  ⚠️  {warning}")
            if validation['errors']:
                print(f"\nErrors:")
                for error in validation['errors']:
                    print(f"  ❌ {error}")
        
        elif command == "summary":
            summary = await manager.get_schema_summary()
            print(f"\n{'='*60}")
            print(f"Schema Summary")
            print(f"{'='*60}")
            print(f"Constraints: {len(summary['constraints'])}")
            print(f"Indexes: {len(summary['indexes'])}")
            print(f"Node Labels: {len(summary['node_labels'])}")
            print(f"Relationship Types: {len(summary['relationship_types'])}")
            print(f"\nNode Labels: {', '.join(summary['node_labels'])}")
            print(f"Relationship Types: {', '.join(summary['relationship_types'])}")
        
        elif command == "reset":
            confirm = input("⚠️  This will DROP ALL constraints and indexes. Continue? (yes/no): ")
            if confirm.lower() == "yes":
                await manager.reset_schema()
            else:
                print("Cancelled.")
        
        else:
            print(f"Unknown command: {command}")
            print("Available commands: init, validate, summary, reset")
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
