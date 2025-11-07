#!/usr/bin/env python3
"""
Unified Threat Graph Builder v2
Enterprise-grade threat intelligence graph construction
Integrates CVEs, MITRE ATT&CK framework, and threat intelligence data
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config.settings import settings
from src.core.enterprise_base import EnterpriseBase
from src.core.monitoring import EnterpriseMonitoring
from src.core.data_validator import DataValidator

import redis
import json
import logging
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from collections import defaultdict
from datetime import datetime
import weaviate
from neo4j import GraphDatabase

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - [%(name)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.FileHandler("/tmp/threat_graph_builder.log", mode='w'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# MITRE ATT&CK Framework Constants
MITRE_TACTICS = {
    "TA0001": "Initial Access",
    "TA0002": "Execution", 
    "TA0003": "Persistence",
    "TA0004": "Privilege Escalation",
    "TA0005": "Defense Evasion",
    "TA0006": "Credential Access",
    "TA0007": "Discovery",
    "TA0008": "Lateral Movement",
    "TA0009": "Collection",
    "TA0010": "Exfiltration",
    "TA0011": "Command and Control",
    "TA0042": "Resource Development"
}

MITRE_TECHNIQUES = {
    "T1190": "Exploit Public-Facing Application",
    "T1078": "Valid Accounts",
    "T1133": "External Remote Services",
    "T1098": "Account Manipulation",
    "T1055": "Process Injection",
    "T1053": "Scheduled Task/Job",
    "T1543": "Create or Modify System Process",
    "T1548": "Abuse Elevation Control Mechanism",
    "T1068": "Exploitation for Privilege Escalation",
    "T1489": "Service Stop",
    "T1112": "Modify Registry",
    "T1565": "Data Manipulation",
    "T1070": "Indicator Removal on Host",
    "T1056": "Input Capture",
    "T1556": "Modify Authentication Process",
    "T1003": "OS Credential Dumping",
    "T1082": "System Information Discovery",
    "T1046": "Network Service Scanning",
    "T1018": "Remote System Discovery",
    "T1021": "Remote Services",
    "T1020": "Automated Exfiltration",
    "T1041": "Exfiltration Over C2 Channel",
    "T1071": "Application Layer Protocol",
    "T1095": "Non-Application Layer Protocol",
    "T1105": "Ingress Tool Transfer",
    "T1195": "Supply Chain Compromise",
    "T1136": "Create Account",
    "T1098": "Account Manipulation"
}

class UnifiedThreatGraphBuilder(EnterpriseBase):
    """
    Enterprise-grade threat intelligence graph builder
    Integrates CVEs, MITRE ATT&CK, and threat intelligence data
    """

    def __init__(self):
        """Initialize with enterprise-grade monitoring"""
        super().__init__()
        
        logger.info("="*80)
        logger.info(" UNIFIED THREAT INTELLIGENCE GRAPH - ENTERPRISE STANDARD")
        logger.info("="*80)
        
        # Initialize monitoring
        self.monitoring = EnterpriseMonitoring()
        
        # Initialize data validator
        self.validator = DataValidator()
        
        # Register circuit breakers for critical operations
        self.register_circuit_breaker("create_cve_nodes", failure_threshold=3)
        self.register_circuit_breaker("create_threat_nodes", failure_threshold=3)
        self.register_circuit_breaker("create_relationships", failure_threshold=3)
        
        # Initialize database connections using environment configuration
        self.redis_client = None
        self.neo4j_driver = None
        self.weaviate_client = None
        
        self._initialize_connections()
        
        logger.info("✅ Unified Threat Graph Builder initialized")
        logger.info(f"🔗 Redis: {settings.redis_host}:{settings.redis_port}")
        logger.info(f"🔗 Neo4j: {settings.neo4j_uri}")
        logger.info(f"🔗 Weaviate: {settings.weaviate_url}")
    
    def _initialize_connections(self):
        """Initialize database connections from environment settings"""
        try:
            # Redis connection
            self.redis_client = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                password=settings.redis_password,
                db=settings.redis_db,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            
            # Test Redis connection
            self.redis_client.ping()
            logger.info("✅ Redis connection established")
            
            # Neo4j connection
            self.neo4j_driver = GraphDatabase.driver(
                settings.neo4j_uri,
                auth=(settings.neo4j_user, settings.neo4j_password),
                max_connection_lifetime=3600,
                max_connection_pool_size=50
            )
            
            # Test Neo4j connection
            with self.neo4j_driver.session() as session:
                session.run("RETURN 1")
            logger.info("✅ Neo4j connection established")
            
            # Weaviate connection
            self.weaviate_client = weaviate.Client(
                url=settings.weaviate_url,
                auth_client_secret=weaviate.AuthApiKey(api_key=settings.weaviate_api_key) if settings.weaviate_api_key else None
            )
            
            # Test Weaviate connection
            self.weaviate_client.is_ready()
            logger.info("✅ Weaviate connection established")
            
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            raise
    
    def _init_weaviate(self, url: str):
        """Initialize Weaviate with monitoring"""
        with self.operation_context("init_weaviate") as op_id:
            try:
                self.weaviate = weaviate.Client(url)
                logger.info("✅ Weaviate connected (v3 client)")
            except Exception as e:
                logger.warning(f"Weaviate v3 client failed: {e}")
                try:
                    self.weaviate = weaviate.connect_to_local()
                    logger.info("✅ Weaviate connected (v4 client)")
                except Exception as e2:
                    logger.warning(f"Weaviate v4 client failed: {e2}")
                    self.weaviate = None
                    logger.warning("⚠️ Using mock ThreatIntel data")
    
    def close(self):
        """Close all connections with proper cleanup"""
        with self.operation_context("cleanup") as op_id:
            try:
                self.neo4j.close()
                self.redis.close()
                self.monitoring.stop()
                logger.info("✅ All connections closed")
            except Exception as e:
                logger.error(f"❌ Cleanup failed: {e}")
                raise
    
    def create_schema(self):
        """Create Neo4j schema with constraints and indexes"""
        with self.operation_context("create_schema") as op_id:
            logger.info("\n🏗️  Creating Neo4j schema...")
            
            try:
                with self.neo4j.session() as session:
                    # Create constraints
                    constraints = [
                        ("CVE", "id"),
                        ("Vendor", "name"),
                        ("Product", "name"),
                        ("CWE", "id"),
                        ("ThreatIntel", "id"),
                        ("MitreTactic", "id"),
                        ("MitreTechnique", "id"),
                        ("IOC", "value")
                    ]
                    
                    for node_type, field in constraints:
                        session.run(f"""
                            CREATE CONSTRAINT {node_type.lower()}_{field}_unique 
                            IF NOT EXISTS FOR (n:{node_type}) 
                            REQUIRE n.{field} IS UNIQUE
                        """)
                    
                    logger.info("  ✅ Constraints created")
                    
                    # Create indexes
                    indexes = [
                        ("CVE", "severity"),
                        ("CVE", "cvss_v3"),
                        ("CVE", "year"),
                        ("ThreatIntel", "severity"),
                        ("IOC", "type"),
                        ("IOC", "confidence")
                    ]
                    
                    for node_type, field in indexes:
                        session.run(f"""
                            CREATE INDEX {node_type.lower()}_{field}_idx 
                            IF NOT EXISTS FOR (n:{node_type}) 
                            ON (n.{field})
                        """)
                    
                    logger.info("  ✅ Indexes created")
                    
            except Exception as e:
                logger.error(f"❌ Schema creation failed: {e}")
                raise
    
    def load_cves_from_redis(self) -> List[CVE]:
        """Load CVEs from Redis with validation"""
        with self.operation_context("load_cves") as op_id:
            logger.info("\n📊 PHASE 1: Loading CVEs from Redis...")
            
            try:
                # Get all CVE keys
                cve_keys = [k for k in self.redis.keys("cve:CVE-*") if not k.endswith(":embedding")]
                logger.info(f"  Found {len(cve_keys):,} CVE keys")
                
                cves = []
                failed = 0
                
                for key in tqdm(cve_keys, desc="  Loading from Redis"):
                    try:
                        # Get CVE data
                        redis_data = self.redis.hgetall(key)
                        cve_dict = self._redis_hash_to_dict(redis_data)
                        
                        # Validate CVE data
                        validation = self.validator.validate_cve(cve_dict)
                        if not validation.valid:
                            logger.warning(f"  ⚠️  Invalid CVE {key}: {validation.errors}")
                            failed += 1
                            continue
                        
                        # Create CVE object
                        cve = CVE(**cve_dict)
                        cves.append(cve)
                        
                    except Exception as e:
                        failed += 1
                        if failed <= 5:
                            logger.warning(f"  ⚠️  Failed {key}: {e}")
                
                if failed > 0:
                    logger.warning(f"  ⚠️  {failed:,} CVEs failed validation")
                
                logger.info(f"  ✅ Loaded {len(cves):,} CVEs successfully")
                
                # Update metrics
                self.metrics.update_operation(
                    "load_cves",
                    op_id,
                    items_processed=len(cves)
                )
                
                return cves
                
            except Exception as e:
                logger.error(f"❌ CVE loading failed: {e}")
                raise
    
    def create_cve_nodes(self, cves: List[CVE]):
        """Create CVE nodes with resource-aware batching"""
        with self.operation_context("create_cve_nodes") as op_id:
            logger.info(f"\n💾 Creating {len(cves):,} CVE nodes...")
            
            try:
                with self.neo4j.session() as session:
                    # Calculate optimal batch size based on available memory
                    total_memory = self.resource_monitor.get_memory_usage()["available"]
                    batch_size = min(1000, max(100, total_memory // (1024 * 1024 * 10)))  # 10MB per batch
                    
                    for i in tqdm(range(0, len(cves), batch_size), desc="  CVE nodes"):
                        # Check resource limits
                        if self.should_throttle():
                            logger.warning("  ⚠️  Resource limit reached, throttling...")
                            time.sleep(1)
                        
                        # Process batch
                        batch = cves[i:i+batch_size]
                        nodes = [cve.to_neo4j_node() for cve in batch]
                        
                        session.run("""
                            UNWIND $nodes AS node
                            MERGE (c:CVE {id: node.id})
                            SET c = node
                        """, nodes=nodes)
                        
                        self.stats['cves'] += len(batch)
                        
                        # Update metrics
                        self.metrics.update_operation(
                            "create_cve_nodes",
                            op_id,
                            items_processed=self.stats['cves']
                        )
                
                logger.info(f"  ✅ {self.stats['cves']:,} CVE nodes created")
                
            except Exception as e:
                logger.error(f"❌ CVE node creation failed: {e}")
                raise

    def create_entity_nodes(self, cves: List[CVE]):
        """Create Vendor, Product, CWE nodes with validation"""
        with self.operation_context("create_entities") as op_id:
            # Extract unique entities with validation
            vendors = set()
            products = set()
            cwes = set()
            
            for cve in cves:
                # Validate vendor names
                for vendor in cve.vendor_names:
                    if self._validate_entity_name(vendor):
                        vendors.add(vendor)
                
                # Validate product names
                for product in cve.product_names:
                    if self._validate_entity_name(product):
                        products.add(product)
                
                # Validate CWE IDs
                for cwe in cve.cwes:
                    validation = self.validator.validate_relationship('CVE', 'CWE', 'HAS_WEAKNESS')
                    if validation.valid:
                        cwes.add(cwe)
            
            try:
                with self.neo4j.session() as session:
                    # Create vendor nodes
                    logger.info(f"\n🏢 Creating {len(vendors):,} Vendor nodes...")
                    vendor_list = [{'name': v} for v in vendors]
                    session.run("""
                        UNWIND $vendors AS vendor
                        MERGE (v:Vendor {name: vendor.name})
                    """, vendors=vendor_list)
                    self.stats['vendors'] = len(vendors)
                    
                    # Create product nodes
                    logger.info(f"📦 Creating {len(products):,} Product nodes...")
                    product_list = [{'name': p} for p in products]
                    session.run("""
                        UNWIND $products AS product
                        MERGE (p:Product {name: product.name})
                    """, products=product_list)
                    self.stats['products'] = len(products)
                    
                    # Create CWE nodes
                    logger.info(f"🔍 Creating {len(cwes):,} CWE nodes...")
                    cwe_list = [{'id': c} for c in cwes]
                    session.run("""
                        UNWIND $cwes AS cwe
                        MERGE (w:CWE {id: cwe.id})
                    """, cwes=cwe_list)
                    self.stats['cwes'] = len(cwes)
                    
                    logger.info(f"  ✅ All entity nodes created")
                    
                    # Update metrics
                    self.metrics.update_operation(
                        "create_entities",
                        op_id,
                        items_processed=len(vendors) + len(products) + len(cwes)
                    )
                    
            except Exception as e:
                logger.error(f"❌ Entity creation failed: {e}")
                raise
    
    def _validate_entity_name(self, name: str) -> bool:
        """Validate entity names for injection prevention"""
        if not name or len(name) > 200:
            return False
        
        # Check for potential injection characters
        dangerous_chars = {';', '"', "'", '--', '/*', '*/', '\\'}
        return not any(char in name for char in dangerous_chars)
    
    def create_cve_relationships(self, cves: List[CVE]):
        """Create CVE relationships with validation and monitoring"""
        with self.operation_context("create_relationships") as op_id:
            logger.info("\n🔗 Creating CVE relationships...")
            
            try:
                with self.neo4j.session() as session:
                    # Calculate optimal batch size
                    batch_size = self._calculate_optimal_batch_size()
                    relationships_created = 0
                    
                    # CVE-[:AFFECTS]->Product
                    logger.info("  Creating AFFECTS relationships...")
                    for i in tqdm(range(0, len(cves), batch_size), desc="    AFFECTS"):
                        if self.should_throttle():
                            time.sleep(1)
                        
                        batch = cves[i:i+batch_size]
                        rels = []
                        for cve in batch:
                            for product in cve.product_names:
                                if self._validate_entity_name(product):
                                    rels.append({'cve_id': cve.cve_id, 'product': product})
                        
                        if rels:
                            session.run("""
                                UNWIND $rels AS rel
                                MATCH (c:CVE {id: rel.cve_id})
                                MATCH (p:Product {name: rel.product})
                                MERGE (c)-[:AFFECTS]->(p)
                            """, rels=rels)
                            relationships_created += len(rels)
                    
                    # Product-[:MADE_BY]->Vendor
                    logger.info("  Creating MADE_BY relationships...")
                    for i in tqdm(range(0, len(cves), batch_size), desc="    MADE_BY"):
                        if self.should_throttle():
                            time.sleep(1)
                        
                        batch = cves[i:i+batch_size]
                        rels = []
                        for cve in batch:
                            for product in cve.product_names:
                                for vendor in cve.vendor_names:
                                    if self._validate_entity_name(product) and self._validate_entity_name(vendor):
                                        rels.append({'product': product, 'vendor': vendor})
                        
                        if rels:
                            session.run("""
                                UNWIND $rels AS rel
                                MATCH (p:Product {name: rel.product})
                                MATCH (v:Vendor {name: rel.vendor})
                                MERGE (p)-[:MADE_BY]->(v)
                            """, rels=rels)
                            relationships_created += len(rels)
                    
                    # CVE-[:HAS_WEAKNESS]->CWE
                    logger.info("  Creating HAS_WEAKNESS relationships...")
                    for i in tqdm(range(0, len(cves), batch_size), desc="    HAS_WEAKNESS"):
                        if self.should_throttle():
                            time.sleep(1)
                        
                        batch = cves[i:i+batch_size]
                        rels = []
                        for cve in batch:
                            for cwe in cve.cwes:
                                validation = self.validator.validate_relationship('CVE', 'CWE', 'HAS_WEAKNESS')
                                if validation.valid:
                                    rels.append({'cve_id': cve.cve_id, 'cwe': cwe})
                        
                        if rels:
                            session.run("""
                                UNWIND $rels AS rel
                                MATCH (c:CVE {id: rel.cve_id})
                                MATCH (w:CWE {id: rel.cwe})
                                MERGE (c)-[:HAS_WEAKNESS]->(w)
                            """, rels=rels)
                            relationships_created += len(rels)
                    
                    logger.info("  ✅ CVE relationships complete")
                    
                    # Update metrics
                    self.metrics.update_operation(
                        "create_relationships",
                        op_id,
                        items_processed=relationships_created
                    )
                    
            except Exception as e:
                logger.error(f"❌ Relationship creation failed: {e}")
                raise
    
    def _calculate_optimal_batch_size(self) -> int:
        """Calculate optimal batch size based on system resources"""
        available_memory = self.resource_monitor.get_memory_usage()["available"]
        cpu_usage = self.resource_monitor.get_cpu_usage()
        
        # Base batch size
        base_size = 1000
        
        # Adjust based on available memory (reduce if less than 2GB available)
        memory_factor = min(1.0, available_memory / (2 * 1024 * 1024 * 1024))
        
        # Adjust based on CPU usage (reduce if over 70%)
        cpu_factor = 1.0 if cpu_usage < 70 else 0.5
        
        # Calculate final batch size
        batch_size = int(base_size * memory_factor * cpu_factor)
        
        # Ensure reasonable bounds
        return max(100, min(batch_size, 5000))
    
    def _redis_hash_to_dict(self, redis_data: Dict[str, str]) -> Dict:
        """Convert Redis hash to Pydantic-compatible dict with validation"""
        try:
            # Basic data extraction with date normalization
            published = redis_data.get('published')
            if published and '.' in published:
                published = published.split('.')[0] + 'Z'
            
            modified = redis_data.get('modified')
            if modified and '.' in modified:
                modified = modified.split('.')[0] + 'Z'
            
            data = {
                'cve_id': redis_data.get('id'),
                'description': redis_data.get('description', 'No description available'),
                'cvss_v3_score': float(redis_data.get('cvss_v3', 0)) if redis_data.get('cvss_v3') else None,
                'cvss_v2_score': float(redis_data.get('cvss_v2', 0)) if redis_data.get('cvss_v2') else None,
                'severity': redis_data.get('severity', 'none'),
                'published': published,
                'modified': modified
            }
            
            # List fields with validation
            for field in ['vendors', 'products', 'cwes', 'references']:
                raw_value = redis_data.get(field, '')
                if raw_value:
                    # Split and clean values
                    values = [v.strip() for v in raw_value.split(',') if v.strip()]
                    
                    # Additional validation
                    if field == 'cwes':
                        values = [cwe for cwe in values if self.validator.CWE_PATTERN.match(cwe)]
                    elif field in ['vendors', 'products']:
                        values = [v for v in values if self._validate_entity_name(v)]
                    
                    data[f'affected_{field}' if field in ['vendors', 'products'] else field] = values
                else:
                    data[f'affected_{field}' if field in ['vendors', 'products'] else field] = []
            
            # Source validation
            data['source'] = redis_data.get('source', 'NVD')
            if not self._validate_entity_name(data['source']):
                data['source'] = 'NVD'
            
            return data
            
        except Exception as e:
            logger.warning(f"Failed to convert Redis hash: {e}")
            return None
    
    def _generate_threat_intel(self, num_threats: int = 200) -> List[Dict[str, Any]]:
        """Generate realistic threat intelligence data with validation"""
        logger.info(f"  💡 Generating {num_threats} realistic ThreatIntel objects")
        
        try:
            # Use the ThreatIntelGenerator to create realistic data
            generator = ThreatIntelGenerator(num_threats=num_threats)
            threats = generator.generate_threats()
            
            # Validate each threat
            validated_threats = []
            for threat in threats:
                validation = self.validator.validate_threat_intel(threat)
                if validation.valid:
                    validated_threats.append(threat)
                else:
                    logger.warning(f"Invalid generated threat {threat.get('id')}: {validation.errors}")
            
            logger.info(f"  ✅ Generated {len(validated_threats)} valid ThreatIntel objects")
            return validated_threats
            
        except Exception as e:
            logger.error(f"Failed to generate threat intel: {e}")
            return []
    def load_threat_intel(self) -> List[Dict[str, Any]]:
        """Load ThreatIntel data with validation and fallback"""
        with self.operation_context("load_threat_intel") as op_id:
            logger.info("\n🔍 PHASE 2: Loading ThreatIntel data...")
            
            threats = []
            
            try:
                if self.weaviate is not None:
                    # Query Weaviate with retry logic
                    max_retries = 3
                    retry_delay = 1
                    
                    for attempt in range(max_retries):
                        try:
                            result = self.weaviate.query.get(
                                "ThreatIntel", 
                                ["id", "title", "description", "severity", "type", "source",
                                 "cves", "mitreTactics", "mitreTechniques", "affectedProducts", 
                                 "affectedVendors", "publishedDate", "confidence"]
                            ).with_limit(10000).do()
                            
                            if "errors" in result:
                                logger.error(f"Weaviate query errors: {result['errors']}")
                                raise Exception("Weaviate query failed")
                            
                            threats = result["data"]["Get"]["ThreatIntel"]
                            logger.info(f"  ✅ Loaded {len(threats):,} ThreatIntel objects from Weaviate")
                            break
                            
                        except Exception as e:
                            if attempt < max_retries - 1:
                                logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying...")
                                time.sleep(retry_delay * (2 ** attempt))  # Exponential backoff
                            else:
                                logger.error(f"Failed to query Weaviate after {max_retries} attempts")
                                threats = self._generate_threat_intel()
                
                else:
                    threats = self._generate_threat_intel()
                
                # Validate all threats
                validated_threats = []
                for threat in threats:
                    validation = self.validator.validate_threat_intel(threat)
                    if validation.valid:
                        validated_threats.append(threat)
                    else:
                        logger.warning(f"Invalid threat {threat.get('id')}: {validation.errors}")
                
                # Update metrics
                self.metrics.update_operation(
                    "load_threat_intel",
                    op_id,
                    items_processed=len(validated_threats)
                )
                
                return validated_threats
                
            except Exception as e:
                logger.error(f"❌ Failed to load threat intel: {e}")
                raise
    
    def create_threat_intel_nodes(self, threats: List[Dict[str, Any]]):
        """Create ThreatIntel nodes with validation"""
        with self.operation_context("create_threat_intel") as op_id:
            logger.info(f"\n🔥 Creating {len(threats):,} ThreatIntel nodes...")
            
            try:
                with self.neo4j.session() as session:
                    # Calculate optimal batch size
                    batch_size = self._calculate_optimal_batch_size()
                    
                    for i in tqdm(range(0, len(threats), batch_size), desc="  ThreatIntel"):
                        if self.should_throttle():
                            time.sleep(1)
                        
                        batch = threats[i:i+batch_size]
                        
                        session.run("""
                            UNWIND $threats AS threat
                            MERGE (t:ThreatIntel {id: threat.id})
                            SET t.title = threat.title,
                                t.description = threat.description,
                                t.severity = threat.severity,
                                t.type = threat.type,
                                t.source = threat.source,
                                t.publishedDate = threat.publishedDate,
                                t.confidence = toFloat(threat.confidence)
                        """, threats=batch)
                        
                        self.stats['threats'] += len(batch)
                        
                        # Update metrics
                        self.metrics.update_operation(
                            "create_threat_intel",
                            op_id,
                            items_processed=self.stats['threats']
                        )
                
                logger.info(f"  ✅ {self.stats['threats']:,} ThreatIntel nodes created")
                
            except Exception as e:
                logger.error(f"❌ ThreatIntel node creation failed: {e}")
                raise
    
    def create_mitre_framework(self):
        """Create MITRE ATT&CK framework with validation"""
        with self.operation_context("create_mitre") as op_id:
            logger.info("\n⚔️ Creating MITRE ATT&CK framework...")
            
            try:
                with self.neo4j.session() as session:
                    # Create tactic nodes
                    tactics = []
                    for tactic_id, tactic_data in MITRE_TACTICS.items():
                        tactics.append({
                            "id": tactic_id,
                            "name": tactic_data["name"],
                            "description": tactic_data["description"]
                        })
                    
                    session.run("""
                        UNWIND $tactics AS tactic
                        MERGE (t:MitreTactic {id: tactic.id})
                        SET t.name = tactic.name,
                            t.description = tactic.description
                    """, tactics=tactics)
                    
                    self.stats['tactics'] = len(tactics)
                    logger.info(f"  ✅ Created {len(tactics):,} MITRE tactics")
                    
                    # Create technique nodes and relationships
                    techniques = []
                    for technique_id, technique_data in MITRE_TECHNIQUES.items():
                        # Validate relationship
                        validation = self.validator.validate_relationship(
                            'MitreTactic', 'MitreTechnique', 'USES'
                        )
                        if validation.valid:
                            techniques.append({
                                "id": technique_id,
                                "name": technique_data["name"],
                                "tactic": technique_data["tactic"]
                            })
                    
                    # Create technique nodes
                    session.run("""
                        UNWIND $techniques AS technique
                        MERGE (t:MitreTechnique {id: technique.id})
                        SET t.name = technique.name
                    """, techniques=techniques)
                    
                    # Create USES relationships
                    session.run("""
                        UNWIND $techniques AS technique
                        MATCH (tactic:MitreTactic {id: technique.tactic})
                        MATCH (tech:MitreTechnique {id: technique.id})
                        MERGE (tactic)-[:USES]->(tech)
                    """, techniques=techniques)
                    
                    self.stats['techniques'] = len(techniques)
                    logger.info(f"  ✅ Created {len(techniques):,} MITRE techniques")
                    
                    # Update metrics
                    self.metrics.update_operation(
                        "create_mitre",
                        op_id,
                        items_processed=len(tactics) + len(techniques)
                    )
                    
            except Exception as e:
                logger.error(f"❌ MITRE framework creation failed: {e}")
                raise
    
    def create_threat_relationships(self, threats: List[Dict[str, Any]]):
        """Create ThreatIntel relationships with validation"""
        with self.operation_context("create_threat_relationships") as op_id:
            logger.info("\n🔗 Creating ThreatIntel relationships...")
            
            try:
                with self.neo4j.session() as session:
                    batch_size = self._calculate_optimal_batch_size()
                    relationships_created = 0
                    
                    # ThreatIntel-[:REFERENCES]->CVE
                    logger.info("  Creating REFERENCES relationships...")
                    for i in tqdm(range(0, len(threats), batch_size), desc="    REFERENCES"):
                        if self.should_throttle():
                            time.sleep(1)
                        
                        batch = threats[i:i+batch_size]
                        refs = []
                        for threat in batch:
                            for cve_id in threat.get("cves", []):
                                if isinstance(cve_id, str) and self.validator.CVE_PATTERN.match(cve_id):
                                    refs.append({"threat_id": threat["id"], "cve_id": cve_id})
                        
                        if refs:
                            session.run("""
                                UNWIND $refs AS ref
                                MATCH (t:ThreatIntel {id: ref.threat_id})
                                MATCH (c:CVE {id: ref.cve_id})
                                MERGE (t)-[:REFERENCES]->(c)
                            """, refs=refs)
                            relationships_created += len(refs)
                            self.stats['references'] += len(refs)
                    
                    # ThreatIntel-[:USES_TACTIC]->MitreTactic
                    logger.info("  Creating USES_TACTIC relationships...")
                    for i in tqdm(range(0, len(threats), batch_size), desc="    USES_TACTIC"):
                        if self.should_throttle():
                            time.sleep(1)
                        
                        batch = threats[i:i+batch_size]
                        tactic_refs = []
                        for threat in batch:
                            for tactic_id in threat.get("mitreTactics", []):
                                if isinstance(tactic_id, str) and tactic_id in MITRE_TACTICS:
                                    tactic_refs.append({"threat_id": threat["id"], "tactic_id": tactic_id})
                        
                        if tactic_refs:
                            session.run("""
                                UNWIND $refs AS ref
                                MATCH (t:ThreatIntel {id: ref.threat_id})
                                MATCH (m:MitreTactic {id: ref.tactic_id})
                                MERGE (t)-[:USES_TACTIC]->(m)
                            """, refs=tactic_refs)
                            relationships_created += len(tactic_refs)
                            self.stats['uses_tactic'] += len(tactic_refs)
                    
                    # ThreatIntel-[:USES_TECHNIQUE]->MitreTechnique
                    logger.info("  Creating USES_TECHNIQUE relationships...")
                    for i in tqdm(range(0, len(threats), batch_size), desc="    USES_TECHNIQUE"):
                        if self.should_throttle():
                            time.sleep(1)
                        
                        batch = threats[i:i+batch_size]
                        technique_refs = []
                        for threat in batch:
                            for technique_id in threat.get("mitreTechniques", []):
                                if isinstance(technique_id, str) and technique_id in MITRE_TECHNIQUES:
                                    technique_refs.append({"threat_id": threat["id"], "technique_id": technique_id})
                        
                        if technique_refs:
                            session.run("""
                                UNWIND $refs AS ref
                                MATCH (t:ThreatIntel {id: ref.threat_id})
                                MATCH (m:MitreTechnique {id: ref.technique_id})
                                MERGE (t)-[:USES_TECHNIQUE]->(m)
                            """, refs=technique_refs)
                            relationships_created += len(technique_refs)
                            self.stats['uses_technique'] += len(technique_refs)
                    
                    # Create CWE-[:ENABLES_TECHNIQUE]->MitreTechnique relationships
                    logger.info("  Creating ENABLES_TECHNIQUE relationships...")
                    for threat in threats:
                        if "cwes" in threat and "mitreTechniques" in threat:
                            for cwe in threat.get("cwes", []):
                                for technique in threat.get("mitreTechniques", []):
                                    validation = self.validator.validate_relationship(
                                        'CWE', 'MitreTechnique', 'ENABLES_TECHNIQUE'
                                    )
                                    if validation.valid:
                                        session.run("""
                                            MATCH (w:CWE {id: $cwe})
                                            MATCH (t:MitreTechnique {id: $technique})
                                            MERGE (w)-[:ENABLES_TECHNIQUE]->(t)
                                        """, cwe=cwe, technique=technique)
                                        relationships_created += 1
                                        self.stats['enables_technique'] += 1
                    
                    logger.info("  ✅ ThreatIntel relationships created")
                    
                    # Update metrics
                    self.metrics.update_operation(
                        "create_threat_relationships",
                        op_id,
                        items_processed=relationships_created
                    )
                    
            except Exception as e:
                logger.error(f"❌ ThreatIntel relationship creation failed: {e}")
                raise
    
    def create_ioc_nodes(self, threats: List[Dict[str, Any]]):
        """Create IOC nodes with validation"""
        with self.operation_context("create_iocs") as op_id:
            logger.info("\n🔍 Creating IOC nodes...")
            
            try:
                # Generate IOCs with validation
                ioc_generator = IOCGenerator()
                iocs = ioc_generator.generate_iocs_for_threats(threats, min_iocs=3, max_iocs=8)
                
                # Validate IOCs
                validated_iocs = []
                for ioc in iocs:
                    validation = self.validator.validate_ioc(ioc)
                    if validation.valid:
                        validated_iocs.append(ioc)
                    else:
                        logger.warning(f"Invalid IOC {ioc.get('value')}: {validation.errors}")
                
                logger.info(f"  Generated {len(validated_iocs)} IOCs for {len(threats)} threats")
                
                with self.neo4j.session() as session:
                    batch_size = self._calculate_optimal_batch_size()
                    
                    # Create IOC nodes
                    for i in tqdm(range(0, len(validated_iocs), batch_size), desc="  IOC nodes"):
                        if self.should_throttle():
                            time.sleep(1)
                        
                        batch = validated_iocs[i:i+batch_size]
                        
                        session.run("""
                            UNWIND $iocs AS ioc
                            MERGE (i:IOC {value: ioc.value})
                            SET i.type = ioc.type,
                                i.confidence = ioc.confidence,
                                i.firstSeen = ioc.firstSeen
                        """, iocs=batch)
                    
                    # Create INDICATES relationships
                    for i in tqdm(range(0, len(validated_iocs), batch_size), desc="  INDICATES"):
                        if self.should_throttle():
                            time.sleep(1)
                        
                        batch = validated_iocs[i:i+batch_size]
                        
                        session.run("""
                            UNWIND $iocs AS ioc
                            MATCH (i:IOC {value: ioc.value})
                            MATCH (t:ThreatIntel {id: ioc.threatId})
                            MERGE (i)-[:INDICATES]->(t)
                        """, iocs=batch)
                        
                        self.stats['indicates'] += len(batch)
                
                self.stats['iocs'] = len(validated_iocs)
                logger.info(f"  ✅ Created {len(validated_iocs)} IOC nodes with relationships")
                
                # Update metrics
                self.metrics.update_operation(
                    "create_iocs",
                    op_id,
                    items_processed=len(validated_iocs)
                )
                
                return validated_iocs
                
            except Exception as e:
                logger.error(f"❌ IOC creation failed: {e}")
                raise
    
    def build_complete_graph(self):
        """Build the complete unified threat graph with enterprise-quality monitoring"""
        with self.operation_context("build_complete_graph") as op_id:
            start_time = time.time()
            
            try:
                # Phase 1: Schema
                self.create_schema()
                
                # Phase 1: Load CVEs
                cves = self.load_cves_from_redis()
                
                # Phase 1: Create nodes
                self.create_cve_nodes(cves)
                self.create_entity_nodes(cves)
                
                # Phase 1: Create relationships
                self.create_cve_relationships(cves)
                
                # Phase 2: ThreatIntel
                threats = self.load_threat_intel()
                self.create_threat_intel_nodes(threats)
                
                # Phase 2: MITRE ATT&CK
                self.create_mitre_framework()
                
                # Phase 2: ThreatIntel relationships
                self.create_threat_relationships(threats)
                
                # Phase 4: IOC Integration
                self.create_ioc_nodes(threats)
                
                # Report
                elapsed = time.time() - start_time
                logger.info("\n" + "="*80)
                logger.info("📊 UNIFIED THREAT GRAPH COMPLETE")
                logger.info("="*80)
                logger.info(f"CVEs:                {self.stats['cves']:,}")
                logger.info(f"Vendors:             {self.stats['vendors']:,}")
                logger.info(f"Products:            {self.stats['products']:,}")
                logger.info(f"CWEs:                {self.stats['cwes']:,}")
                logger.info(f"ThreatIntel:         {self.stats['threats']:,}")
                logger.info(f"MITRE Tactics:       {self.stats['tactics']:,}")
                logger.info(f"MITRE Techniques:    {self.stats['techniques']:,}")
                logger.info(f"IOCs:                {self.stats['iocs']:,}")
                logger.info(f"REFERENCES:          {self.stats['references']:,}")
                logger.info(f"USES_TACTIC:         {self.stats['uses_tactic']:,}")
                logger.info(f"USES_TECHNIQUE:      {self.stats['uses_technique']:,}")
                logger.info(f"ENABLES_TECHNIQUE:   {self.stats['enables_technique']:,}")
                logger.info(f"INDICATES:           {self.stats['indicates']:,}")
                logger.info(f"\n⏱️  Total time: {elapsed/60:.1f} minutes")
                logger.info("="*80)
                
                # Final monitoring report
                logger.info("\n" + "="*80)
                logger.info("⚡ SYSTEM PERFORMANCE REPORT")
                logger.info("="*80)
                logger.info(self.monitoring.resources.get_resource_summary())
                logger.info(self.monitoring.operations.get_summary())
                logger.info("="*80)
                
                # Update final metrics
                self.metrics.update_operation(
                    "build_complete_graph",
                    op_id,
                    items_processed=sum(self.stats.values())
                )
                
                # Log detailed metrics
                self.log_metrics("build_complete_graph")
                
            except Exception as e:
                logger.error(f"❌ Build failed: {e}")
                raise
            finally:
                self.close()


def main():
    """Main execution"""
    builder = UnifiedThreatGraphBuilder()
    builder.build_complete_graph()


if __name__ == "__main__":
    main()
