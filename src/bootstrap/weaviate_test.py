#!/usr/bin/env python3
"""
Weaviate Test Script
Tests connection and schema for ThreatIntel objects
"""

import sys
import logging
from pathlib import Path

import weaviate
from pprint import pprint

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_weaviate_connection(url="http://10.152.183.242:8080"):
    """Test connection to Weaviate"""
    try:
        logger.info(f"Connecting to Weaviate at {url}")
        client = weaviate.Client(url)
        
        if client.is_ready():
            logger.info("✅ Weaviate is ready")
            return client
        else:
            logger.error("❌ Weaviate is not ready")
            return None
    except Exception as e:
        logger.error(f"❌ Failed to connect to Weaviate: {e}")
        return None

def get_schema(client):
    """Get Weaviate schema"""
    try:
        schema = client.schema.get()
        logger.info("✅ Retrieved schema")
        return schema
    except Exception as e:
        logger.error(f"❌ Failed to get schema: {e}")
        return None

def count_threat_intel(client):
    """Count ThreatIntel objects"""
    try:
        result = client.query.aggregate("ThreatIntel").with_meta_count().do()
        count = result.get("data", {}).get("Aggregate", {}).get("ThreatIntel", [{}])[0].get("meta", {}).get("count")
        
        if count is not None:
            logger.info(f"✅ Found {count} ThreatIntel objects")
        else:
            logger.warning("⚠️ No ThreatIntel objects found or class doesn't exist")
            count = 0
        
        return count
    except Exception as e:
        logger.error(f"❌ Failed to count ThreatIntel objects: {e}")
        return 0

def get_threat_intel_sample(client, limit=5):
    """Get a sample of ThreatIntel objects"""
    try:
        result = client.query.get(
            "ThreatIntel", 
            ["id", "title", "description", "severity", "type", "source",
             "cves", "mitreTactics", "mitreTechniques", "affectedProducts", 
             "affectedVendors", "publishedDate", "confidence"]
        ).with_limit(limit).do()
        
        threats = result.get("data", {}).get("Get", {}).get("ThreatIntel", [])
        
        if threats:
            logger.info(f"✅ Retrieved {len(threats)} ThreatIntel samples")
            return threats
        else:
            logger.warning("⚠️ No ThreatIntel objects found")
            return []
    except Exception as e:
        logger.error(f"❌ Failed to get ThreatIntel samples: {e}")
        return []

def main():
    """Main function"""
    client = test_weaviate_connection()
    if not client:
        sys.exit(1)
    
    schema = get_schema(client)
    if schema:
        # Check if ThreatIntel class exists
        classes = [c["class"] for c in schema["classes"]] if "classes" in schema else []
        if "ThreatIntel" in classes:
            logger.info("✅ ThreatIntel class exists")
        else:
            logger.warning("⚠️ ThreatIntel class does not exist")
            logger.info(f"Available classes: {classes}")
    
    count = count_threat_intel(client)
    
    if count > 0:
        threats = get_threat_intel_sample(client)
        if threats:
            logger.info("\nSample ThreatIntel object:")
            pprint(threats[0])
    
if __name__ == "__main__":
    main()
