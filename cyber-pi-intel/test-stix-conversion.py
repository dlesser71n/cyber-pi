#!/usr/bin/env python3
"""
Test STIX 2.1 Conversion
Demonstrates cyber-pi threat → STIX 2.1 → cyber-pi roundtrip
"""

import json
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.core.stix_converter import STIXConverter

# Sample cyber-pi threat
sample_threat = {
    "title": "Lockbit Ransomware Targeting Aviation Industry",
    "content": """
    A new campaign by the Lockbit ransomware group has been observed targeting
    major airlines and aviation infrastructure. The attackers are exploiting
    CVE-2024-1234 in Apache Struts to gain initial access, followed by lateral
    movement using credential dumping techniques (MITRE T1003).
    
    The ransomware encrypts critical flight scheduling and passenger data systems,
    demanding payment in cryptocurrency. Several airlines have reported disruptions
    to their operations.
    """,
    "source": "Cyber Threat Intelligence Feed",
    "industry": ["Aviation & Airlines"],
    "severity": "critical",
    "threatType": ["ransomware", "malware"],
    "threatActors": ["Lockbit", "Lockbit 3.0"],
    "cves": ["CVE-2024-1234"],
    "iocs": [
        "192.0.2.1",
        "malicious-domain.com",
        "a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456"
    ],
    "mitreTechniques": ["T1003", "T1486", "T1566.001"],
    "mitreTactics": ["Initial Access", "Credential Access", "Impact"],
    "publishedDate": "2025-10-31T17:00:00Z",
    "confidence": 0.85,
    "verificationStatus": "verified",
    "tags": ["ransomware", "aviation", "lockbit", "critical-infrastructure"],
    "affectedProducts": ["Apache Struts"],
    "affectedVendors": ["Apache Software Foundation"],
    "recommendedActions": [
        "Patch Apache Struts immediately (CVE-2024-1234)",
        "Monitor for unusual lateral movement",
        "Implement multi-factor authentication",
        "Backup critical data systems",
        "Block IOCs at network perimeter"
    ]
}

def main():
    print("="*60)
    print("STIX 2.1 Conversion Test")
    print("="*60)
    print()
    
    # Initialize converter
    print("Initializing STIX converter...")
    try:
        converter = STIXConverter()
        print("✓ STIXConverter initialized")
    except ImportError as e:
        print(f"✗ Error: {e}")
        print("\nPlease install STIX libraries:")
        print("  pip install stix2 stix2-patterns taxii2-client")
        return 1
    print()
    
    # Convert to STIX
    print("Converting cyber-pi threat to STIX 2.1...")
    try:
        stix_bundle = converter.threat_to_stix_bundle(sample_threat)
        print(f"✓ Created STIX bundle with {len(stix_bundle.objects)} objects")
    except Exception as e:
        print(f"✗ Conversion failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    print()
    
    # Display STIX objects
    print("STIX Objects Created:")
    print("-"*60)
    for i, obj in enumerate(stix_bundle.objects, 1):
        obj_type = obj.type
        obj_name = getattr(obj, 'name', getattr(obj, 'relationship_type', 'N/A'))
        obj_id = obj.id
        print(f"{i:2d}. {obj_type:20s} | {obj_name[:30]:30s} | {obj_id}")
    print()
    
    # Display STIX JSON
    print("STIX JSON (formatted):")
    print("-"*60)
    stix_json = json.loads(stix_bundle.serialize())
    print(json.dumps(stix_json, indent=2)[:2000] + "...")
    print()
    
    # Save to file
    output_file = "sample_threat_stix.json"
    print(f"Saving STIX bundle to {output_file}...")
    with open(output_file, 'w') as f:
        f.write(stix_bundle.serialize(pretty=True))
    print(f"✓ Saved to {output_file}")
    print()
    
    # Convert back to cyber-pi format
    print("Converting STIX bundle back to cyber-pi format...")
    try:
        threat_reconstructed = converter.stix_bundle_to_threat(stix_bundle)
        print("✓ Converted back successfully")
    except Exception as e:
        print(f"✗ Reverse conversion failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    print()
    
    # Compare
    print("Reconstructed Threat:")
    print("-"*60)
    print(f"Title:        {threat_reconstructed['title']}")
    print(f"Industry:     {threat_reconstructed['industry']}")
    print(f"Threat Type:  {threat_reconstructed['threatType']}")
    print(f"Actors:       {threat_reconstructed['threatActors']}")
    print(f"CVEs:         {threat_reconstructed['cves']}")
    print(f"MITRE:        {threat_reconstructed['mitreTechniques']}")
    print(f"STIX ID:      {threat_reconstructed.get('stixId', 'N/A')}")
    print(f"STIX Type:    {threat_reconstructed.get('stixType', 'N/A')}")
    print()
    
    # Statistics
    print("="*60)
    print("Conversion Statistics:")
    print("="*60)
    print(f"Input Fields:       {len([k for k in sample_threat.keys() if sample_threat[k]])}")
    print(f"STIX Objects:       {len(stix_bundle.objects)}")
    print(f"  - Malware:        {sum(1 for o in stix_bundle.objects if o.type == 'malware')}")
    print(f"  - Indicators:     {sum(1 for o in stix_bundle.objects if o.type == 'indicator')}")
    print(f"  - Threat Actors:  {sum(1 for o in stix_bundle.objects if o.type == 'threat-actor')}")
    print(f"  - Vulnerabilities: {sum(1 for o in stix_bundle.objects if o.type == 'vulnerability')}")
    print(f"  - Attack Patterns: {sum(1 for o in stix_bundle.objects if o.type == 'attack-pattern')}")
    print(f"  - Identities:     {sum(1 for o in stix_bundle.objects if o.type == 'identity')}")
    print(f"  - Relationships:  {sum(1 for o in stix_bundle.objects if o.type == 'relationship')}")
    print(f"Output Fields:      {len([k for k in threat_reconstructed.keys() if threat_reconstructed[k]])}")
    print()
    
    print("="*60)
    print("✓ STIX Conversion Test Complete!")
    print("="*60)
    print()
    print("The STIX bundle can now be:")
    print("  - Shared with other threat intelligence platforms")
    print("  - Imported into MISP, AlienVault, Anomali, etc.")
    print("  - Published via TAXII server")
    print("  - Stored in industry-standard format")
    print()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
