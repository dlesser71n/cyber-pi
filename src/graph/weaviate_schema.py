#!/usr/bin/env python3
"""
Weaviate Schema Manager for Cyber-PI
Vector database schema for semantic search and embeddings

Built to Rickover standards: Production-ready, type-safe
"""

import logging
from typing import List, Dict, Any, Optional
import weaviate

logger = logging.getLogger(__name__)


class WeaviateSchemaManager:
    """
    Manages Weaviate schema for Cyber-PI ontology
    
    Collections:
    - CVE (vulnerabilities with embeddings)
    - ThreatIntel (threat intelligence reports)
    - Article (news articles, blog posts)
    - IOC (indicators with context)
    - ThreatActor (adversary profiles)
    """
    
    def __init__(self, url: str = "http://localhost:18080", api_key: Optional[str] = None):
        """
        Initialize Weaviate schema manager
        
        Args:
            url: Weaviate instance URL
            api_key: Optional API key for authentication
        """
        self.url = url
        self.api_key = api_key
        self.client: Optional[weaviate.Client] = None
    
    def connect(self) -> None:
        """Establish connection to Weaviate"""
        try:
            if self.api_key:
                auth_config = weaviate.AuthApiKey(api_key=self.api_key)
                self.client = weaviate.Client(
                    url=self.url,
                    auth_client_secret=auth_config
                )
            else:
                self.client = weaviate.Client(url=self.url)
            
            # Test connection
            self.client.schema.get()
            logger.info(f"✓ Connected to Weaviate at {self.url}")
        except Exception as e:
            logger.error(f"Failed to connect to Weaviate: {e}")
            raise
    
    def close(self) -> None:
        """Close connection"""
        if self.client:
            self.client.close()
            logger.info("✓ Closed Weaviate connection")
    
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
    
    # ========================================================================
    # SCHEMA DEFINITIONS
    # ========================================================================
    
    def create_cve_class(self) -> None:
        """
        Create CVE class for vulnerability semantic search (Weaviate v3 API)
        """
        class_obj = {
            "class": "CVE",
            "description": "Common Vulnerabilities and Exposures with semantic embeddings",
            "vectorizer": "text2vec-transformers",
            "moduleConfig": {
                "text2vec-transformers": {
                    "poolingStrategy": "masked_mean"
                }
            },
            "properties": [
                {
                    "name": "cve_id",
                    "dataType": ["text"],
                    "description": "CVE identifier",
                    "tokenization": "field",
                    "moduleConfig": {
                        "text2vec-transformers": {
                            "skip": True
                        }
                    }
                },
                {
                    "name": "description",
                    "dataType": ["text"],
                    "description": "Vulnerability description (vectorized)"
                },
                {
                    "name": "severity",
                    "dataType": ["text"],
                    "description": "Severity level",
                    "moduleConfig": {"text2vec-transformers": {"skip": True}}
                },
                {
                    "name": "cvss_score",
                    "dataType": ["number"],
                    "description": "CVSS v3 score"
                },
                {
                    "name": "published",
                    "dataType": ["date"],
                    "description": "Publication date"
                },
                {
                    "name": "affected_vendors",
                    "dataType": ["text[]"],
                    "description": "Affected vendors"
                },
                {
                    "name": "affected_products",
                    "dataType": ["text[]"],
                    "description": "Affected products"
                },
                {
                    "name": "cwes",
                    "dataType": ["text[]"],
                    "description": "CWE identifiers"
                },
                {
                    "name": "neo4j_id",
                    "dataType": ["text"],
                    "description": "Reference to Neo4j node",
                    "moduleConfig": {"text2vec-transformers": {"skip": True}}
                }
            ]
        }
        
        try:
            self.client.schema.create_class(class_obj)
            logger.info("✓ Created CVE class")
        except Exception as e:
            logger.warning(f"CVE class may already exist: {e}")
    
    def create_threat_intel_collection(self) -> None:
        """
        Create ThreatIntel collection for threat reports
        
        Properties:
        - title: Report title
        - content: Report content (vectorized)
        - source: Intelligence source
        - published: Publication date
        - threat_types: Types of threats
        - severity: Threat severity
        - iocs: Associated IOCs
        - neo4j_id: Reference to Neo4j node
        """
        try:
            self.client.collections.create(
                name="ThreatIntel",
                description="Threat intelligence reports with semantic embeddings",
                vectorizer_config=Configure.Vectorizer.text2vec_transformers(
                    pooling_strategy="masked_mean",
                    vectorize_collection_name=False
                ),
                vector_index_config=Configure.VectorIndex.hnsw(
                    distance_metric=VectorDistances.COSINE
                ),
                properties=[
                    Property(
                        name="title",
                        data_type=DataType.TEXT,
                        description="Report title"
                    ),
                    Property(
                        name="content",
                        data_type=DataType.TEXT,
                        description="Report content (vectorized)"
                    ),
                    Property(
                        name="source",
                        data_type=DataType.TEXT,
                        description="Intelligence source",
                        skip_vectorization=True
                    ),
                    Property(
                        name="published",
                        data_type=DataType.DATE,
                        description="Publication date",
                        skip_vectorization=True
                    ),
                    Property(
                        name="threat_types",
                        data_type=DataType.TEXT_ARRAY,
                        description="Types of threats mentioned",
                        skip_vectorization=True
                    ),
                    Property(
                        name="severity",
                        data_type=DataType.TEXT,
                        description="Threat severity",
                        skip_vectorization=True
                    ),
                    Property(
                        name="iocs",
                        data_type=DataType.TEXT_ARRAY,
                        description="Associated IOCs",
                        skip_vectorization=True
                    ),
                    Property(
                        name="neo4j_id",
                        data_type=DataType.TEXT,
                        description="Reference to Neo4j node",
                        skip_vectorization=True
                    )
                ]
            )
            logger.info("✓ Created ThreatIntel collection")
        except Exception as e:
            logger.warning(f"ThreatIntel collection may already exist: {e}")
    
    def create_article_collection(self) -> None:
        """
        Create Article collection for news/blog posts
        
        Properties:
        - title: Article title
        - content: Article content (vectorized)
        - url: Article URL
        - author: Author name
        - published: Publication date
        - tags: Article tags
        - neo4j_id: Reference to Neo4j node
        """
        try:
            self.client.collections.create(
                name="Article",
                description="News articles and blog posts with semantic embeddings",
                vectorizer_config=Configure.Vectorizer.text2vec_transformers(
                    pooling_strategy="masked_mean",
                    vectorize_collection_name=False
                ),
                vector_index_config=Configure.VectorIndex.hnsw(
                    distance_metric=VectorDistances.COSINE
                ),
                properties=[
                    Property(
                        name="title",
                        data_type=DataType.TEXT,
                        description="Article title"
                    ),
                    Property(
                        name="content",
                        data_type=DataType.TEXT,
                        description="Article content (vectorized)"
                    ),
                    Property(
                        name="url",
                        data_type=DataType.TEXT,
                        description="Article URL",
                        skip_vectorization=True
                    ),
                    Property(
                        name="author",
                        data_type=DataType.TEXT,
                        description="Author name",
                        skip_vectorization=True
                    ),
                    Property(
                        name="published",
                        data_type=DataType.DATE,
                        description="Publication date",
                        skip_vectorization=True
                    ),
                    Property(
                        name="tags",
                        data_type=DataType.TEXT_ARRAY,
                        description="Article tags",
                        skip_vectorization=True
                    ),
                    Property(
                        name="neo4j_id",
                        data_type=DataType.TEXT,
                        description="Reference to Neo4j node",
                        skip_vectorization=True
                    )
                ]
            )
            logger.info("✓ Created Article collection")
        except Exception as e:
            logger.warning(f"Article collection may already exist: {e}")
    
    def create_ioc_collection(self) -> None:
        """
        Create IOC collection for indicators of compromise
        
        Properties:
        - ioc_type: Type of IOC (ip, domain, hash, etc.)
        - value: IOC value
        - context: Context description (vectorized)
        - threat_types: Associated threat types
        - first_seen: First observation
        - last_seen: Last observation
        - malicious: Whether confirmed malicious
        - confidence: Confidence score
        - neo4j_id: Reference to Neo4j node
        """
        try:
            self.client.collections.create(
                name="IOC",
                description="Indicators of Compromise with context embeddings",
                vectorizer_config=Configure.Vectorizer.text2vec_transformers(
                    pooling_strategy="masked_mean",
                    vectorize_collection_name=False
                ),
                vector_index_config=Configure.VectorIndex.hnsw(
                    distance_metric=VectorDistances.COSINE
                ),
                properties=[
                    Property(
                        name="ioc_type",
                        data_type=DataType.TEXT,
                        description="Type: ipv4, ipv6, domain, hash, email, url",
                        skip_vectorization=True
                    ),
                    Property(
                        name="value",
                        data_type=DataType.TEXT,
                        description="IOC value",
                        skip_vectorization=True,
                        tokenization="field"
                    ),
                    Property(
                        name="context",
                        data_type=DataType.TEXT,
                        description="Context description (vectorized)"
                    ),
                    Property(
                        name="threat_types",
                        data_type=DataType.TEXT_ARRAY,
                        description="Associated threat types",
                        skip_vectorization=True
                    ),
                    Property(
                        name="first_seen",
                        data_type=DataType.DATE,
                        description="First observation",
                        skip_vectorization=True
                    ),
                    Property(
                        name="last_seen",
                        data_type=DataType.DATE,
                        description="Last observation",
                        skip_vectorization=True
                    ),
                    Property(
                        name="malicious",
                        data_type=DataType.BOOL,
                        description="Confirmed malicious",
                        skip_vectorization=True
                    ),
                    Property(
                        name="confidence",
                        data_type=DataType.INT,
                        description="Confidence score 0-100",
                        skip_vectorization=True
                    ),
                    Property(
                        name="neo4j_id",
                        data_type=DataType.TEXT,
                        description="Reference to Neo4j node",
                        skip_vectorization=True
                    )
                ]
            )
            logger.info("✓ Created IOC collection")
        except Exception as e:
            logger.warning(f"IOC collection may already exist: {e}")
    
    def create_threat_actor_collection(self) -> None:
        """
        Create ThreatActor collection for adversary profiles
        
        Properties:
        - name: Threat actor name
        - description: Actor description (vectorized)
        - aliases: Known aliases
        - sophistication: Sophistication level
        - motivation: Primary motivation
        - targets: Target industries/sectors
        - ttps: Tactics, techniques, procedures summary
        - neo4j_id: Reference to Neo4j node
        """
        try:
            self.client.collections.create(
                name="ThreatActor",
                description="Threat actor profiles with semantic embeddings",
                vectorizer_config=Configure.Vectorizer.text2vec_transformers(
                    pooling_strategy="masked_mean",
                    vectorize_collection_name=False
                ),
                vector_index_config=Configure.VectorIndex.hnsw(
                    distance_metric=VectorDistances.COSINE
                ),
                properties=[
                    Property(
                        name="name",
                        data_type=DataType.TEXT,
                        description="Threat actor name",
                        skip_vectorization=True,
                        tokenization="field"
                    ),
                    Property(
                        name="description",
                        data_type=DataType.TEXT,
                        description="Actor description (vectorized)"
                    ),
                    Property(
                        name="aliases",
                        data_type=DataType.TEXT_ARRAY,
                        description="Known aliases",
                        skip_vectorization=True
                    ),
                    Property(
                        name="sophistication",
                        data_type=DataType.TEXT,
                        description="Sophistication level",
                        skip_vectorization=True
                    ),
                    Property(
                        name="motivation",
                        data_type=DataType.TEXT,
                        description="Primary motivation",
                        skip_vectorization=True
                    ),
                    Property(
                        name="targets",
                        data_type=DataType.TEXT_ARRAY,
                        description="Target industries/sectors",
                        skip_vectorization=True
                    ),
                    Property(
                        name="ttps",
                        data_type=DataType.TEXT,
                        description="TTPs summary (vectorized)"
                    ),
                    Property(
                        name="neo4j_id",
                        data_type=DataType.TEXT,
                        description="Reference to Neo4j node",
                        skip_vectorization=True
                    )
                ]
            )
            logger.info("✓ Created ThreatActor collection")
        except Exception as e:
            logger.warning(f"ThreatActor collection may already exist: {e}")
    
    # ========================================================================
    # SCHEMA INITIALIZATION
    # ========================================================================
    
    def initialize_schema(self) -> None:
        """
        Initialize complete Weaviate schema
        Creates all classes
        """
        logger.info("🚀 Initializing Weaviate schema...")
        
        try:
            self.create_cve_class()
            # Add other classes here as needed
            
            logger.info("✅ Weaviate schema initialization complete")
            
        except Exception as e:
            logger.error(f"❌ Schema initialization failed: {e}")
            raise
    
    # ========================================================================
    # SCHEMA INTROSPECTION
    # ========================================================================
    
    def get_classes(self) -> List[str]:
        """Get all class names"""
        try:
            schema = self.client.schema.get()
            return [c["class"] for c in schema.get("classes", [])]
        except Exception as e:
            logger.error(f"Failed to list classes: {e}")
            return []
    
    def get_class_info(self, class_name: str) -> Dict[str, Any]:
        """Get detailed info about a class"""
        try:
            schema = self.client.schema.get()
            for c in schema.get("classes", []):
                if c["class"] == class_name:
                    return c
            return {}
        except Exception as e:
            logger.error(f"Failed to get class info: {e}")
            return {}
    
    def get_schema_summary(self) -> Dict[str, Any]:
        """Get complete schema summary"""
        classes = self.get_classes()
        
        return {
            "classes": classes,
            "class_count": len(classes),
            "schema": self.client.schema.get()
        }
    
    # ========================================================================
    # UTILITY METHODS
    # ========================================================================
    
    def drop_class(self, class_name: str) -> None:
        """
        Drop a class (USE WITH CAUTION)
        Only for development/testing
        """
        logger.warning(f"⚠️  Dropping class: {class_name}")
        
        try:
            self.client.schema.delete_class(class_name)
            logger.info(f"Dropped class: {class_name}")
        except Exception as e:
            logger.error(f"Failed to drop class: {e}")
    
    def drop_all_classes(self) -> None:
        """
        Drop all classes (USE WITH EXTREME CAUTION)
        Only for development/testing
        """
        logger.warning("⚠️  DROPPING ALL CLASSES")
        
        classes = self.get_classes()
        for class_name in classes:
            self.drop_class(class_name)
        
        logger.info("✅ All classes dropped")
    
    def reset_schema(self) -> None:
        """
        Reset schema completely (USE WITH EXTREME CAUTION)
        Drops all classes and recreates
        """
        logger.warning("⚠️  RESETTING SCHEMA - THIS WILL DROP EVERYTHING")
        
        self.drop_all_classes()
        self.initialize_schema()
        
        logger.info("✅ Schema reset complete")


# ============================================================================
# CLI INTERFACE
# ============================================================================

async def main():
    """CLI for Weaviate schema management"""
    import os
    import sys
    
    # Get configuration from environment
    url = os.getenv("WEAVIATE_URL", "http://localhost:18080")
    api_key = os.getenv("WEAVIATE_API_KEY")  # Optional
    
    # Parse command
    command = sys.argv[1] if len(sys.argv) > 1 else "init"
    
    with WeaviateSchemaManager(url, api_key) as manager:
        if command == "init":
            manager.initialize_schema()
        
        elif command == "summary":
            summary = manager.get_schema_summary()
            print(f"\n{'='*60}")
            print(f"Weaviate Schema Summary")
            print(f"{'='*60}")
            print(f"Classes: {summary['class_count']}")
            print(f"Names: {', '.join(summary['classes'])}")
            print(f"{'='*60}")
        
        elif command == "reset":
            confirm = input("⚠️  This will DROP ALL collections. Continue? (yes/no): ")
            if confirm.lower() == "yes":
                manager.reset_schema()
            else:
                print("Cancelled.")
        
        else:
            print(f"Unknown command: {command}")
            print("Available commands: init, summary, reset")
            sys.exit(1)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
