#!/usr/bin/env python3
"""
MITRE ATT&CK Loader
Loads tactics, techniques, and relationships from MITRE ATT&CK framework

Built to Rickover standards: Production-ready, type-safe, resilient
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
import aiohttp
from tenacity import retry, stop_after_attempt, wait_exponential

from models.ontology import MitreTactic, MitreTechnique, Relationship, RelationType
from graph.neo4j_schema import Neo4jSchemaManager

logger = logging.getLogger(__name__)


class MitreLoader:
    """
    Load MITRE ATT&CK data into Neo4j
    
    Features:
    - Loads from official MITRE STIX data
    - Creates tactics, techniques, sub-techniques
    - Builds tactic→technique relationships
    - Handles all platforms (Windows, Linux, macOS, etc.)
    """
    
    # MITRE ATT&CK STIX Data URLs
    ENTERPRISE_URL = "https://raw.githubusercontent.com/mitre-attack/attack-stix-data/master/enterprise-attack/enterprise-attack.json"
    MOBILE_URL = "https://raw.githubusercontent.com/mitre-attack/attack-stix-data/master/mobile-attack/mobile-attack.json"
    ICS_URL = "https://raw.githubusercontent.com/mitre-attack/attack-stix-data/master/ics-attack/ics-attack.json"
    
    def __init__(
        self,
        neo4j_uri: str,
        neo4j_user: str,
        neo4j_password: str
    ):
        """Initialize MITRE loader"""
        self.neo4j_uri = neo4j_uri
        self.neo4j_user = neo4j_user
        self.neo4j_password = neo4j_password
        
        self.schema_manager: Optional[Neo4jSchemaManager] = None
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Statistics
        self.stats = {
            "tactics_loaded": 0,
            "techniques_loaded": 0,
            "relationships_created": 0,
            "errors": 0
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
    
    async def connect(self) -> None:
        """Establish connections"""
        self.schema_manager = Neo4jSchemaManager(
            self.neo4j_uri,
            self.neo4j_user,
            self.neo4j_password
        )
        await self.schema_manager.connect()
        
        self.session = aiohttp.ClientSession()
        
        logger.info("✓ Connected to Neo4j and MITRE ATT&CK data source")
    
    async def close(self) -> None:
        """Close connections"""
        if self.schema_manager:
            await self.schema_manager.close()
        if self.session:
            await self.session.close()
        
        logger.info("✓ Closed connections")
    
    # ========================================================================
    # MITRE ATT&CK DATA FETCHING
    # ========================================================================
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True
    )
    async def fetch_attack_data(self, url: str) -> Dict[str, Any]:
        """
        Fetch MITRE ATT&CK STIX data
        
        Args:
            url: URL to STIX JSON file
            
        Returns:
            STIX bundle
        """
        try:
            async with self.session.get(url, timeout=60) as resp:
                resp.raise_for_status()
                data = await resp.json()
                
                logger.info(f"✓ Fetched MITRE ATT&CK data: {len(data.get('objects', []))} objects")
                return data
                
        except aiohttp.ClientError as e:
            logger.error(f"Failed to fetch MITRE data: {e}")
            raise
        except asyncio.TimeoutError:
            logger.error("MITRE data fetch timed out")
            raise
    
    # ========================================================================
    # DATA TRANSFORMATION
    # ========================================================================
    
    def extract_tactics(self, stix_bundle: Dict[str, Any]) -> List[MitreTactic]:
        """Extract tactics from STIX bundle"""
        tactics = []
        
        for obj in stix_bundle.get("objects", []):
            if obj.get("type") == "x-mitre-tactic":
                # Extract tactic ID from external references
                external_refs = obj.get("external_references", [])
                tactic_id = None
                url = None
                
                for ref in external_refs:
                    if ref.get("source_name") == "mitre-attack":
                        tactic_id = ref.get("external_id")
                        url = ref.get("url")
                        break
                
                if not tactic_id:
                    continue
                
                tactic = MitreTactic(
                    tactic_id=tactic_id,
                    name=obj.get("name", ""),
                    description=obj.get("description", ""),
                    url=url or f"https://attack.mitre.org/tactics/{tactic_id}",
                    platforms=obj.get("x_mitre_platforms", []),
                    version=obj.get("x_mitre_version", "1.0"),
                    source="MITRE ATT&CK",
                    confidence=100
                )
                
                tactics.append(tactic)
        
        logger.info(f"✓ Extracted {len(tactics)} tactics")
        return tactics
    
    def extract_techniques(self, stix_bundle: Dict[str, Any]) -> List[MitreTechnique]:
        """Extract techniques from STIX bundle"""
        techniques = []
        
        for obj in stix_bundle.get("objects", []):
            if obj.get("type") == "attack-pattern":
                # Extract technique ID
                external_refs = obj.get("external_references", [])
                technique_id = None
                url = None
                
                for ref in external_refs:
                    if ref.get("source_name") == "mitre-attack":
                        technique_id = ref.get("external_id")
                        url = ref.get("url")
                        break
                
                if not technique_id:
                    continue
                
                # Determine if sub-technique
                is_subtechnique = "." in technique_id
                parent_technique = technique_id.split(".")[0] if is_subtechnique else None
                
                # Extract kill chain phases (tactics)
                kill_chain_phases = obj.get("kill_chain_phases", [])
                tactic_refs = [
                    phase.get("phase_name") for phase in kill_chain_phases
                    if phase.get("kill_chain_name") == "mitre-attack"
                ]
                
                technique = MitreTechnique(
                    technique_id=technique_id,
                    name=obj.get("name", ""),
                    description=obj.get("description", ""),
                    url=url or f"https://attack.mitre.org/techniques/{technique_id}",
                    tactic_refs=tactic_refs,
                    parent_technique=parent_technique,
                    platforms=obj.get("x_mitre_platforms", []),
                    data_sources=obj.get("x_mitre_data_sources", []),
                    is_subtechnique=is_subtechnique,
                    version=obj.get("x_mitre_version", "1.0"),
                    detection=obj.get("x_mitre_detection", None),
                    source="MITRE ATT&CK",
                    confidence=100
                )
                
                techniques.append(technique)
        
        logger.info(f"✓ Extracted {len(techniques)} techniques")
        return techniques
    
    # ========================================================================
    # NEO4J LOADING
    # ========================================================================
    
    async def load_tactic(self, tactic: MitreTactic) -> None:
        """Load tactic into Neo4j"""
        async with self.schema_manager.driver.session() as session:
            query = """
            MERGE (t:MitreTactic {tactic_id: $tactic_id})
            SET t.id = $id,
                t.type = $type,
                t.name = $name,
                t.description = $description,
                t.url = $url,
                t.platforms = $platforms,
                t.version = $version,
                t.source = $source,
                t.confidence = $confidence,
                t.created = $created,
                t.modified = $modified
            RETURN t
            """
            
            await session.run(query, {
                "tactic_id": tactic.tactic_id,
                "id": tactic.id,
                "type": tactic.type,
                "name": tactic.name,
                "description": tactic.description,
                "url": tactic.url,
                "platforms": tactic.platforms,
                "version": tactic.version,
                "source": tactic.source,
                "confidence": tactic.confidence,
                "created": tactic.created.isoformat(),
                "modified": tactic.modified.isoformat()
            })
            
            self.stats["tactics_loaded"] += 1
    
    async def load_technique(self, technique: MitreTechnique) -> None:
        """Load technique into Neo4j"""
        async with self.schema_manager.driver.session() as session:
            query = """
            MERGE (t:MitreTechnique {technique_id: $technique_id})
            SET t.id = $id,
                t.type = $type,
                t.name = $name,
                t.description = $description,
                t.url = $url,
                t.tactic_refs = $tactic_refs,
                t.parent_technique = $parent_technique,
                t.platforms = $platforms,
                t.data_sources = $data_sources,
                t.is_subtechnique = $is_subtechnique,
                t.version = $version,
                t.detection = $detection,
                t.source = $source,
                t.confidence = $confidence,
                t.created = $created,
                t.modified = $modified
            RETURN t
            """
            
            await session.run(query, {
                "technique_id": technique.technique_id,
                "id": technique.id,
                "type": technique.type,
                "name": technique.name,
                "description": technique.description,
                "url": technique.url,
                "tactic_refs": technique.tactic_refs,
                "parent_technique": technique.parent_technique,
                "platforms": technique.platforms,
                "data_sources": technique.data_sources,
                "is_subtechnique": technique.is_subtechnique,
                "version": technique.version,
                "detection": technique.detection,
                "source": technique.source,
                "confidence": technique.confidence,
                "created": technique.created.isoformat(),
                "modified": technique.modified.isoformat()
            })
            
            self.stats["techniques_loaded"] += 1
    
    async def create_relationships(self) -> None:
        """Create relationships between tactics and techniques"""
        async with self.schema_manager.driver.session() as session:
            # Technique → Tactic (PART_OF)
            query = """
            MATCH (tech:MitreTechnique)
            WHERE size(tech.tactic_refs) > 0
            UNWIND tech.tactic_refs as tactic_name
            MATCH (tac:MitreTactic)
            WHERE toLower(tac.name) = toLower(replace(tactic_name, '-', ' '))
            MERGE (tech)-[:PART_OF]->(tac)
            RETURN count(*) as rel_count
            """
            
            result = await session.run(query)
            record = await result.single()
            count = record["rel_count"] if record else 0
            
            self.stats["relationships_created"] += count
            logger.info(f"✓ Created {count} PART_OF relationships")
            
            # Sub-technique → Parent Technique (DERIVES_FROM)
            query = """
            MATCH (sub:MitreTechnique)
            WHERE sub.is_subtechnique = true AND sub.parent_technique IS NOT NULL
            MATCH (parent:MitreTechnique {technique_id: sub.parent_technique})
            MERGE (sub)-[:DERIVES_FROM]->(parent)
            RETURN count(*) as rel_count
            """
            
            result = await session.run(query)
            record = await result.single()
            count = record["rel_count"] if record else 0
            
            self.stats["relationships_created"] += count
            logger.info(f"✓ Created {count} DERIVES_FROM relationships")
    
    # ========================================================================
    # HIGH-LEVEL OPERATIONS
    # ========================================================================
    
    async def load_enterprise_attack(self) -> None:
        """Load Enterprise ATT&CK matrix"""
        logger.info("Loading Enterprise ATT&CK...")
        
        # Fetch data
        data = await self.fetch_attack_data(self.ENTERPRISE_URL)
        
        # Extract entities
        tactics = self.extract_tactics(data)
        techniques = self.extract_techniques(data)
        
        # Load into Neo4j
        logger.info("Loading tactics...")
        for tactic in tactics:
            await self.load_tactic(tactic)
        
        logger.info("Loading techniques...")
        for technique in techniques:
            await self.load_technique(technique)
        
        # Create relationships
        logger.info("Creating relationships...")
        await self.create_relationships()
        
        logger.info("✓ Enterprise ATT&CK loaded")
    
    async def load_mobile_attack(self) -> None:
        """Load Mobile ATT&CK matrix"""
        logger.info("Loading Mobile ATT&CK...")
        
        data = await self.fetch_attack_data(self.MOBILE_URL)
        tactics = self.extract_tactics(data)
        techniques = self.extract_techniques(data)
        
        for tactic in tactics:
            await self.load_tactic(tactic)
        for technique in techniques:
            await self.load_technique(technique)
        
        await self.create_relationships()
        
        logger.info("✓ Mobile ATT&CK loaded")
    
    async def load_ics_attack(self) -> None:
        """Load ICS ATT&CK matrix"""
        logger.info("Loading ICS ATT&CK...")
        
        data = await self.fetch_attack_data(self.ICS_URL)
        tactics = self.extract_tactics(data)
        techniques = self.extract_techniques(data)
        
        for tactic in tactics:
            await self.load_tactic(tactic)
        for technique in techniques:
            await self.load_technique(technique)
        
        await self.create_relationships()
        
        logger.info("✓ ICS ATT&CK loaded")
    
    async def load_all(self) -> None:
        """Load all ATT&CK matrices"""
        await self.load_enterprise_attack()
        await self.load_mobile_attack()
        await self.load_ics_attack()
    
    def print_stats(self) -> None:
        """Print loading statistics"""
        print("\n" + "="*60)
        print("MITRE ATT&CK Loader Statistics")
        print("="*60)
        print(f"Tactics loaded:       {self.stats['tactics_loaded']:,}")
        print(f"Techniques loaded:    {self.stats['techniques_loaded']:,}")
        print(f"Relationships:        {self.stats['relationships_created']:,}")
        print(f"Errors:               {self.stats['errors']:,}")
        print("="*60)


# ============================================================================
# CLI INTERFACE
# ============================================================================

async def main():
    """CLI for MITRE loader"""
    import os
    import sys
    
    # Get credentials from environment
    neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD")
    
    if not neo4j_password:
        print("❌ NEO4J_PASSWORD environment variable not set")
        sys.exit(1)
    
    # Parse command
    command = sys.argv[1] if len(sys.argv) > 1 else "enterprise"
    
    async with MitreLoader(neo4j_uri, neo4j_user, neo4j_password) as loader:
        if command == "enterprise":
            await loader.load_enterprise_attack()
        
        elif command == "mobile":
            await loader.load_mobile_attack()
        
        elif command == "ics":
            await loader.load_ics_attack()
        
        elif command == "all":
            await loader.load_all()
        
        else:
            print(f"Unknown command: {command}")
            print("Available commands:")
            print("  enterprise  - Load Enterprise ATT&CK (default)")
            print("  mobile      - Load Mobile ATT&CK")
            print("  ics         - Load ICS ATT&CK")
            print("  all         - Load all matrices")
            sys.exit(1)
        
        # Print statistics
        loader.print_stats()


if __name__ == "__main__":
    asyncio.run(main())
