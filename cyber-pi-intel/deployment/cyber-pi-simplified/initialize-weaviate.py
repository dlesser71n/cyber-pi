#!/usr/bin/env python3
"""
Initialize Weaviate with Cyber Threat Intelligence Schema
Creates self-descriptive classes for threat intelligence storage
"""

import weaviate
import weaviate.classes as wvc
import sys

def initialize_weaviate_schema():
    """Create Weaviate schema for cyber-pi threat intelligence"""
    
    print("Connecting to Weaviate...")
    client = weaviate.connect_to_local(host="localhost", port=30883)
    
    # Verify connection
    if not client.is_ready():
        print("❌ Weaviate is not ready")
        client.close()
        sys.exit(1)
    
    print("✅ Connected to Weaviate")
    
    # Check if schema already exists
    try:
        existing_schema = client.schema.get()
        existing_classes = [c['class'] for c in existing_schema.get('classes', [])]
        
        if 'CyberThreatIntelligence' in existing_classes:
            print("⚠️  Schema already exists. Deleting old schema...")
            client.schema.delete_class('CyberThreatIntelligence')
    except Exception as e:
        print(f"Note: {e}")
    
    # Create comprehensive threat intelligence schema
    schema = {
        "class": "CyberThreatIntelligence",
        "description": "Cyber threat intelligence items collected from 80+ sources for industry-specific analysis",
        "vectorizer": "none",  # Using external vectorizer (Ollama)
        "properties": [
            {
                "name": "threatId",
                "dataType": ["text"],
                "description": "Unique identifier for the threat (SHA-256 hash of content)"
            },
            {
                "name": "stixId",
                "dataType": ["text"],
                "description": "STIX 2.1 object ID (e.g., indicator--8e2e2d2b-17d4-4cbf-938f-98ee46b3cd3f)"
            },
            {
                "name": "stixType",
                "dataType": ["text"],
                "description": "STIX object type: indicator, malware, threat-actor, attack-pattern, vulnerability, etc."
            },
            {
                "name": "stixVersion",
                "dataType": ["text"],
                "description": "STIX specification version (2.1)"
            },
            {
                "name": "stixObject",
                "dataType": ["text"],
                "description": "Full STIX 2.1 JSON object for complete interoperability"
            },
            {
                "name": "title",
                "dataType": ["text"],
                "description": "Threat title or headline"
            },
            {
                "name": "content",
                "dataType": ["text"],
                "description": "Full threat description and details"
            },
            {
                "name": "summary",
                "dataType": ["text"],
                "description": "Brief summary of the threat"
            },
            {
                "name": "source",
                "dataType": ["text"],
                "description": "Source of the threat intelligence (RSS feed, social media, etc.)"
            },
            {
                "name": "sourceUrl",
                "dataType": ["text"],
                "description": "Original URL of the threat intelligence"
            },
            {
                "name": "industry",
                "dataType": ["text[]"],
                "description": "Target industries (aviation, healthcare, energy, etc.)"
            },
            {
                "name": "severity",
                "dataType": ["text"],
                "description": "Threat severity: critical, high, medium, low"
            },
            {
                "name": "threatType",
                "dataType": ["text[]"],
                "description": "Type of threat: ransomware, phishing, malware, vulnerability, etc."
            },
            {
                "name": "threatActors",
                "dataType": ["text[]"],
                "description": "Known threat actors or groups associated with this threat"
            },
            {
                "name": "cves",
                "dataType": ["text[]"],
                "description": "CVE identifiers associated with this threat"
            },
            {
                "name": "iocs",
                "dataType": ["text[]"],
                "description": "Indicators of Compromise (IPs, domains, hashes, etc.)"
            },
            {
                "name": "mitreTactics",
                "dataType": ["text[]"],
                "description": "MITRE ATT&CK tactics associated with this threat"
            },
            {
                "name": "mitreTechniques",
                "dataType": ["text[]"],
                "description": "MITRE ATT&CK techniques associated with this threat"
            },
            {
                "name": "publishedDate",
                "dataType": ["date"],
                "description": "Date the threat intelligence was published"
            },
            {
                "name": "ingestedDate",
                "dataType": ["date"],
                "description": "Date the threat was ingested into cyber-pi system"
            },
            {
                "name": "lastUpdated",
                "dataType": ["date"],
                "description": "Date the threat intelligence was last updated"
            },
            {
                "name": "confidence",
                "dataType": ["number"],
                "description": "Confidence score of the threat intelligence (0.0 to 1.0)"
            },
            {
                "name": "verificationStatus",
                "dataType": ["text"],
                "description": "Verification status: verified, unverified, disputed"
            },
            {
                "name": "tags",
                "dataType": ["text[]"],
                "description": "Additional tags for categorization"
            },
            {
                "name": "affectedProducts",
                "dataType": ["text[]"],
                "description": "Products or technologies affected by this threat"
            },
            {
                "name": "affectedVendors",
                "dataType": ["text[]"],
                "description": "Vendors affected by this threat"
            },
            {
                "name": "recommendedActions",
                "dataType": ["text[]"],
                "description": "Recommended actions to mitigate this threat"
            },
            {
                "name": "relatedThreats",
                "dataType": ["text[]"],
                "description": "IDs of related threats"
            },
            {
                "name": "metadata",
                "dataType": ["text"],
                "description": "Additional metadata as JSON string"
            }
        ]
    }
    
    # Create the schema
    print("\nCreating CyberThreatIntelligence schema...")
    client.schema.create_class(schema)
    print("✅ Schema created successfully!")
    
    # Verify schema creation
    schema_check = client.schema.get("CyberThreatIntelligence")
    print(f"\n📊 Schema Details:")
    print(f"  Class: {schema_check['class']}")
    print(f"  Description: {schema_check['description']}")
    print(f"  Properties: {len(schema_check['properties'])} fields")
    print(f"  Vectorizer: {schema_check['vectorizer']}")
    
    # Print property list
    print(f"\n📋 Properties:")
    for prop in schema_check['properties']:
        data_types = ', '.join(prop['dataType'])
        print(f"  - {prop['name']:25s} ({data_types:15s}) - {prop.get('description', 'N/A')}")
    
    print("\n✅ Weaviate initialization complete!")
    print(f"   Ready to store cyber threat intelligence")
    
    return True

if __name__ == "__main__":
    try:
        initialize_weaviate_schema()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
