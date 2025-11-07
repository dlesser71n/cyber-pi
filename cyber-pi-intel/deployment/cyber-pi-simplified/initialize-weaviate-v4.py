#!/usr/bin/env python3
"""
Initialize Weaviate v4 with Cyber Threat Intelligence Schema
Creates self-descriptive collections for threat intelligence storage
"""

import weaviate
import weaviate.classes.config as wvcc
import sys

def initialize_weaviate_schema():
    """Create Weaviate schema for cyber-pi threat intelligence"""
    
    print("Connecting to Weaviate...")
    # Connect via internal Kubernetes service (ClusterIP)
    # If running outside cluster, use: kubectl port-forward -n cyber-pi-intel svc/weaviate 8080:8080 50051:50051
    client = weaviate.connect_to_custom(
        http_host="weaviate.cyber-pi-intel.svc.cluster.local",
        http_port=8080,
        http_secure=False,
        grpc_host="weaviate.cyber-pi-intel.svc.cluster.local",
        grpc_port=50051,
        grpc_secure=False,
        skip_init_checks=False
    )
    
    # Verify connection
    if not client.is_ready():
        print("❌ Weaviate is not ready")
        client.close()
        sys.exit(1)
    
    print("✅ Connected to Weaviate")
    
    # Check if collection already exists
    try:
        if client.collections.exists("CyberThreatIntelligence"):
            print("⚠️  Collection already exists. Deleting...")
            client.collections.delete("CyberThreatIntelligence")
    except Exception as e:
        print(f"Note: {e}")
    
    # Create collection with properties
    print("\nCreating CyberThreatIntelligence collection...")
    
    collection = client.collections.create(
        name="CyberThreatIntelligence",
        description="Cyber threat intelligence items collected from 80+ sources for industry-specific analysis with STIX 2.1 support",
        
        # Vectorizer: none (using external Ollama)
        vectorizer_config=wvcc.Configure.Vectorizer.none(),
        
        # Properties
        properties=[
            # Unique identifiers
            wvcc.Property(name="threatId", data_type=wvcc.DataType.TEXT, description="Unique identifier for the threat (SHA-256 hash of content)"),
            
            # STIX 2.1 fields
            wvcc.Property(name="stixId", data_type=wvcc.DataType.TEXT, description="STIX 2.1 object ID (e.g., indicator--8e2e2d2b-17d4-4cbf-938f-98ee46b3cd3f)"),
            wvcc.Property(name="stixType", data_type=wvcc.DataType.TEXT, description="STIX object type: indicator, malware, threat-actor, attack-pattern, vulnerability, etc."),
            wvcc.Property(name="stixVersion", data_type=wvcc.DataType.TEXT, description="STIX specification version (2.1)"),
            wvcc.Property(name="stixObject", data_type=wvcc.DataType.TEXT, description="Full STIX 2.1 JSON object for complete interoperability"),
            
            # Core fields
            wvcc.Property(name="title", data_type=wvcc.DataType.TEXT, description="Threat title or headline"),
            wvcc.Property(name="content", data_type=wvcc.DataType.TEXT, description="Full threat description and details"),
            wvcc.Property(name="summary", data_type=wvcc.DataType.TEXT, description="Brief summary of the threat"),
            
            # Source information
            wvcc.Property(name="source", data_type=wvcc.DataType.TEXT, description="Source of the threat intelligence (RSS feed, social media, etc.)"),
            wvcc.Property(name="sourceUrl", data_type=wvcc.DataType.TEXT, description="Original URL of the threat intelligence"),
            
            # Classification
            wvcc.Property(name="industry", data_type=wvcc.DataType.TEXT_ARRAY, description="Target industries (aviation, healthcare, energy, etc.)"),
            wvcc.Property(name="severity", data_type=wvcc.DataType.TEXT, description="Threat severity: critical, high, medium, low"),
            wvcc.Property(name="threatType", data_type=wvcc.DataType.TEXT_ARRAY, description="Type of threat: ransomware, phishing, malware, vulnerability, etc."),
            wvcc.Property(name="threatActors", data_type=wvcc.DataType.TEXT_ARRAY, description="Known threat actors or groups associated with this threat"),
            
            # Technical indicators
            wvcc.Property(name="cves", data_type=wvcc.DataType.TEXT_ARRAY, description="CVE identifiers associated with this threat"),
            wvcc.Property(name="iocs", data_type=wvcc.DataType.TEXT_ARRAY, description="Indicators of Compromise (IPs, domains, hashes, etc.)"),
            wvcc.Property(name="mitreTactics", data_type=wvcc.DataType.TEXT_ARRAY, description="MITRE ATT&CK tactics associated with this threat"),
            wvcc.Property(name="mitreTechniques", data_type=wvcc.DataType.TEXT_ARRAY, description="MITRE ATT&CK techniques associated with this threat"),
            
            # Timestamps
            wvcc.Property(name="publishedDate", data_type=wvcc.DataType.DATE, description="Date the threat intelligence was published"),
            wvcc.Property(name="ingestedDate", data_type=wvcc.DataType.DATE, description="Date the threat was ingested into cyber-pi system"),
            wvcc.Property(name="lastUpdated", data_type=wvcc.DataType.DATE, description="Date the threat intelligence was last updated"),
            
            # Assessment
            wvcc.Property(name="confidence", data_type=wvcc.DataType.NUMBER, description="Confidence score of the threat intelligence (0.0 to 1.0)"),
            wvcc.Property(name="verificationStatus", data_type=wvcc.DataType.TEXT, description="Verification status: verified, unverified, disputed"),
            
            # Additional metadata
            wvcc.Property(name="tags", data_type=wvcc.DataType.TEXT_ARRAY, description="Additional tags for categorization"),
            wvcc.Property(name="affectedProducts", data_type=wvcc.DataType.TEXT_ARRAY, description="Products or technologies affected by this threat"),
            wvcc.Property(name="affectedVendors", data_type=wvcc.DataType.TEXT_ARRAY, description="Vendors affected by this threat"),
            wvcc.Property(name="recommendedActions", data_type=wvcc.DataType.TEXT_ARRAY, description="Recommended actions to mitigate this threat"),
            wvcc.Property(name="relatedThreats", data_type=wvcc.DataType.TEXT_ARRAY, description="IDs of related threats"),
            wvcc.Property(name="metadata", data_type=wvcc.DataType.TEXT, description="Additional metadata as JSON string"),
        ]
    )
    
    print("✅ Collection created successfully!")
    
    # Verify collection creation
    print(f"\n📊 Collection Details:")
    print(f"  Name: CyberThreatIntelligence")
    print(f"  Description: Cyber threat intelligence with STIX 2.1 support")
    print(f"  Properties: 29 fields (4 STIX + 25 threat intel)")
    print(f"  Vectorizer: External (Ollama)")
    
    # Print property list
    print(f"\n📋 Properties:")
    properties = [
        "threatId", "stixId", "stixType", "stixVersion", "stixObject",
        "title", "content", "summary", "source", "sourceUrl",
        "industry", "severity", "threatType", "threatActors",
        "cves", "iocs", "mitreTactics", "mitreTechniques",
        "publishedDate", "ingestedDate", "lastUpdated",
        "confidence", "verificationStatus",
        "tags", "affectedProducts", "affectedVendors", 
        "recommendedActions", "relatedThreats", "metadata"
    ]
    
    for i, prop in enumerate(properties, 1):
        stix_marker = " (STIX)" if prop.startswith("stix") else ""
        print(f"  {i:2d}. {prop:25s}{stix_marker}")
    
    client.close()
    print("\n✅ Weaviate initialization complete!")
    print(f"   Ready to store cyber threat intelligence with STIX 2.1 support")
    
    return True

if __name__ == "__main__":
    try:
        initialize_weaviate_schema()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
