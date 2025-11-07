# STIX 2.1 Ontology Integration for cyber-pi
# Industry-Standard Threat Intelligence Taxonomy

**Date:** October 31, 2025  
**Standard:** STIX 2.1 (OASIS Standard)  
**Purpose:** Align cyber-pi with international threat intelligence standards

---

## 🎯 Why STIX 2.1?

### **What is STIX?**

**STIX (Structured Threat Information eXpression)** is the international standard for cyber threat intelligence, maintained by OASIS (Organization for the Advancement of Structured Information Standards).

**Benefits:**
- ✅ **Industry Standard** - Used by governments, corporations, ISACs worldwide
- ✅ **Interoperability** - Exchange intelligence with any STIX-compliant platform
- ✅ **Comprehensive** - Covers all aspects of threat intelligence
- ✅ **JSON-based** - Easy to implement and parse
- ✅ **Well-documented** - Extensive specifications and examples
- ✅ **Tool Support** - Many security tools support STIX import/export
- ✅ **Future-proof** - Actively maintained and updated

### **STIX vs Our Current Schema**

| Aspect | Our Current Schema | STIX 2.1 Standard | Recommendation |
|--------|-------------------|-------------------|----------------|
| **Structure** | Custom fields | Standardized objects | Adopt STIX |
| **Relationships** | Custom relations | STIX Relationship Objects (SROs) | Adopt STIX |
| **Interoperability** | Proprietary | Universal | Need STIX |
| **Tool Integration** | Manual | Native support | Need STIX |
| **Compliance** | N/A | Industry standard | Need STIX |

---

## 📊 STIX 2.1 Core Objects

### **Domain Objects (SDOs)**

STIX defines 18 core object types that map perfectly to our needs:

#### 1. **Indicator** - Observable patterns for detection
```json
{
  "type": "indicator",
  "id": "indicator--8e2e2d2b-17d4-4cbf-938f-98ee46b3cd3f",
  "spec_version": "2.1",
  "created": "2025-10-31T17:00:00.000Z",
  "modified": "2025-10-31T17:00:00.000Z",
  "name": "Malicious IP Address",
  "description": "C2 server for Lockbit ransomware",
  "pattern": "[ipv4-addr:value = '192.0.2.1']",
  "pattern_type": "stix",
  "valid_from": "2025-10-31T17:00:00.000Z",
  "indicator_types": ["malicious-activity"]
}
```
**Maps to our:** IOC nodes in Neo4j

#### 2. **Threat Actor** - Attribution to malicious actors
```json
{
  "type": "threat-actor",
  "id": "threat-actor--56f3f0db-b5d5-431c-ae56-c18f02caf500",
  "spec_version": "2.1",
  "created": "2025-10-31T17:00:00.000Z",
  "modified": "2025-10-31T17:00:00.000Z",
  "name": "Lockbit",
  "description": "Ransomware-as-a-Service operation",
  "threat_actor_types": ["criminal-org"],
  "aliases": ["Lockbit 3.0", "Lockbit Black"],
  "sophistication": "expert",
  "resource_level": "organization",
  "primary_motivation": "personal-gain"
}
```
**Maps to our:** ThreatActor nodes in Neo4j

#### 3. **Malware** - Malicious software
```json
{
  "type": "malware",
  "id": "malware--92a78aef-b7ab-4171-9d9f-5e5b7b8e6c4f",
  "spec_version": "2.1",
  "created": "2025-10-31T17:00:00.000Z",
  "modified": "2025-10-31T17:00:00.000Z",
  "name": "Lockbit Ransomware",
  "malware_types": ["ransomware"],
  "is_family": true,
  "description": "Ransomware that encrypts files and demands payment"
}
```
**Maps to our:** CyberThreat nodes with threatType="malware"

#### 4. **Attack Pattern** - Adversary behavior
```json
{
  "type": "attack-pattern",
  "id": "attack-pattern--7e33a43e-e34b-40ec-89da-36c9bb2cacd5",
  "spec_version": "2.1",
  "created": "2025-10-31T17:00:00.000Z",
  "modified": "2025-10-31T17:00:00.000Z",
  "name": "Spearphishing Attachment",
  "description": "Adversaries use email attachments to gain access",
  "external_references": [{
    "source_name": "mitre-attack",
    "external_id": "T1566.001",
    "url": "https://attack.mitre.org/techniques/T1566/001/"
  }]
}
```
**Maps to our:** MitreTechnique nodes in Neo4j

#### 5. **Campaign** - Series of coordinated attacks
```json
{
  "type": "campaign",
  "id": "campaign--8e2e2d2b-17d4-4cbf-938f-98ee46b3cd3f",
  "spec_version": "2.1",
  "created": "2025-10-31T17:00:00.000Z",
  "modified": "2025-10-31T17:00:00.000Z",
  "name": "Operation Aviation Strike",
  "description": "Coordinated attacks on airline industry Q4 2025",
  "first_seen": "2025-10-01T00:00:00.000Z",
  "last_seen": "2025-10-31T00:00:00.000Z",
  "objective": "Financial gain through ransomware"
}
```
**Maps to our:** New Campaign nodes (we should add)

#### 6. **Intrusion Set** - Group of related behaviors
```json
{
  "type": "intrusion-set",
  "id": "intrusion-set--4e78f46f-a023-4e5f-bc24-71b3ca22ec29",
  "spec_version": "2.1",
  "created": "2025-10-31T17:00:00.000Z",
  "modified": "2025-10-31T17:00:00.000Z",
  "name": "APT28",
  "description": "Russian state-sponsored threat actor",
  "aliases": ["Fancy Bear", "Sofacy"],
  "first_seen": "2007-01-01T00:00:00.000Z",
  "goals": ["espionage", "data-theft"]
}
```
**Maps to our:** ThreatActor nodes (APT groups)

#### 7. **Vulnerability** - Software weaknesses
```json
{
  "type": "vulnerability",
  "id": "vulnerability--0c7b5b88-8ff7-4a4d-aa9d-feb398cd0061",
  "spec_version": "2.1",
  "created": "2025-10-31T17:00:00.000Z",
  "modified": "2025-10-31T17:00:00.000Z",
  "name": "CVE-2024-1234",
  "description": "Remote code execution in Apache Struts",
  "external_references": [{
    "source_name": "cve",
    "external_id": "CVE-2024-1234"
  }]
}
```
**Maps to our:** CVE nodes in Neo4j

#### 8. **Identity** - Organizations, sectors, individuals
```json
{
  "type": "identity",
  "id": "identity--311b2d2d-f010-4473-83ec-1edf84858f4c",
  "spec_version": "2.1",
  "created": "2025-10-31T17:00:00.000Z",
  "modified": "2025-10-31T17:00:00.000Z",
  "name": "Aviation Industry",
  "identity_class": "class",
  "sectors": ["transportation"]
}
```
**Maps to our:** Industry nodes in Neo4j

#### 9. **Location** - Geographic information
```json
{
  "type": "location",
  "id": "location--a6e9345f-5a66-4c94-8c13-8f6c3f5d5e9a",
  "spec_version": "2.1",
  "created": "2025-10-31T17:00:00.000Z",
  "modified": "2025-10-31T17:00:00.000Z",
  "name": "United States",
  "country": "US",
  "region": "northern-america"
}
```
**Maps to our:** New Location nodes (should add)

#### 10. **Infrastructure** - Attack infrastructure
```json
{
  "type": "infrastructure",
  "id": "infrastructure--38c47d93-d984-4fd9-b87b-d69d0841628d",
  "spec_version": "2.1",
  "created": "2025-10-31T17:00:00.000Z",
  "modified": "2025-10-31T17:00:00.000Z",
  "name": "Lockbit C2 Server",
  "infrastructure_types": ["command-and-control"],
  "description": "Command and control server at 192.0.2.1"
}
```
**Maps to our:** Infrastructure nodes (should add)

---

## 🔗 STIX Relationship Objects (SROs)

STIX defines standardized relationships between objects:

### Common Relationships:

```json
{
  "type": "relationship",
  "id": "relationship--44298a74-ba52-4f0c-87a3-1824e67d7fad",
  "spec_version": "2.1",
  "created": "2025-10-31T17:00:00.000Z",
  "modified": "2025-10-31T17:00:00.000Z",
  "relationship_type": "uses",
  "source_ref": "threat-actor--56f3f0db-b5d5-431c-ae56-c18f02caf500",
  "target_ref": "malware--92a78aef-b7ab-4171-9d9f-5e5b7b8e6c4f"
}
```

**Standard Relationship Types:**
- `uses` - Threat actor uses malware/tool/technique
- `targets` - Campaign/threat actor targets identity/location
- `indicates` - Indicator indicates malware/threat actor
- `mitigates` - Course of action mitigates vulnerability
- `attributed-to` - Campaign/malware attributed to threat actor
- `based-on` - Derived from another object
- `consists-of` - Composite relationship
- `controls` - Infrastructure controlled by threat actor
- `delivers` - Malware delivers other malware
- `derived-from` - Intelligence derived from source
- `duplicate-of` - Duplicate detection
- `exploits` - Malware exploits vulnerability
- `has` - Composite ownership
- `hosts` - Infrastructure hosts malware
- `originates-from` - Location origin
- `owns` - Ownership relationship
- `related-to` - Generic relation
- `targets` - Attack targets
- `uses` - Usage relationship
- `variant-of` - Variant relationship

**Maps to our:** Neo4j relationships (TARGETS, USES, ATTRIBUTED_TO, etc.)

---

## 🏗️ Proposed STIX Integration Architecture

### **Option 1: STIX as Primary Format (Recommended)**

```
┌─────────────────────────────────────┐
│   Threat Collection (80 sources)    │
└─────────────┬───────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│   Convert to STIX 2.1 Objects       │
│   - Parse source data               │
│   - Map to STIX types               │
│   - Generate STIX IDs               │
│   - Create relationships            │
└─────────────┬───────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│   Store STIX in Weaviate            │
│   Class: STIXCyberObservable        │
│   - Full STIX JSON in property      │
│   - Vector embedding for search     │
└─────────────┬───────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│   Build Graph in Neo4j              │
│   - STIX objects → Neo4j nodes      │
│   - STIX relationships → Neo4j rels │
│   - Preserve STIX IDs               │
└─────────────────────────────────────┘
```

### **Option 2: STIX Export Layer**

```
┌─────────────────────────────────────┐
│   Use Current Schema (Internal)     │
│   - CyberThreatIntelligence class   │
│   - Custom Neo4j graph              │
└─────────────┬───────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│   STIX Export API                   │
│   - Convert on-demand to STIX       │
│   - Share with external systems     │
│   - Import STIX feeds               │
└─────────────────────────────────────┘
```

---

## 📋 Mapping Our Schema to STIX

### Current → STIX Mapping

| Our Schema | STIX 2.1 Object | Notes |
|------------|-----------------|-------|
| **CyberThreatIntelligence** | Multiple STIX types | Need to classify by type |
| threatId | id | Use STIX ID format |
| title | name | Direct mapping |
| content | description | Direct mapping |
| severity | (custom property) | STIX uses threat-actor.sophistication |
| threatType | malware.malware_types | If malware |
| threatActors | threat-actor | Separate object + relationship |
| cves | vulnerability | Separate object + relationship |
| iocs | indicator | Separate object + relationship |
| mitreTactics | attack-pattern | Via external_references |
| mitreTechniques | attack-pattern | Via external_references |
| industry | identity.sectors | Map to STIX sectors |
| publishedDate | created | Timestamp format |
| source | x_source (custom) | Or external_references |

### STIX Sector Taxonomy (for Industries)

STIX defines standard sectors:
- `aerospace` → Aviation & Airlines
- `healthcare` → Healthcare & Medical
- `energy` → Energy & Utilities
- `financial-services` → Financial Services
- `manufacturing` → Manufacturing
- `retail` → Retail & E-commerce
- `technology` → Technology
- `telecommunications` → Telecommunications
- `government` → Government & Public Sector
- `education` → Education
- `transportation` → Transportation & Logistics
- `hospitality-leisure` → Hospitality & Entertainment

---

## 🛠️ Implementation Plan

### Phase 1: Add STIX Support to Schema

**Weaviate Schema Enhancement:**
```python
{
    "class": "STIXCyberObservable",
    "description": "STIX 2.1 compliant cyber threat intelligence",
    "properties": [
        {
            "name": "stixType",
            "dataType": ["text"],
            "description": "STIX object type (indicator, malware, threat-actor, etc.)"
        },
        {
            "name": "stixId",
            "dataType": ["text"],
            "description": "STIX ID (e.g., malware--8e2e2d2b...)"
        },
        {
            "name": "stixVersion",
            "dataType": ["text"],
            "description": "STIX specification version (2.1)"
        },
        {
            "name": "stixObject",
            "dataType": ["text"],
            "description": "Full STIX JSON object"
        },
        {
            "name": "name",
            "dataType": ["text"],
            "description": "STIX object name"
        },
        {
            "name": "description",
            "dataType": ["text"],
            "description": "STIX object description"
        },
        # ... existing properties
    ]
}
```

**Neo4j Labels from STIX:**
```cypher
// Create nodes with STIX types as labels
CREATE (n:STIXObject:Indicator {
    stixId: 'indicator--8e2e2d2b...',
    name: 'Malicious IP',
    pattern: '[ipv4-addr:value = "192.0.2.1"]',
    stixType: 'indicator'
})

CREATE (m:STIXObject:Malware {
    stixId: 'malware--92a78aef...',
    name: 'Lockbit',
    malwareTypes: ['ransomware'],
    stixType: 'malware'
})

// STIX relationships
CREATE (n)-[:STIX_INDICATES]->(m)
```

### Phase 2: STIX Conversion Library

```python
# stix_converter.py
from stix2 import Indicator, Malware, ThreatActor, Relationship
import uuid

class STIXConverter:
    """Convert cyber-pi data to STIX 2.1 format"""
    
    def threat_to_stix(self, threat: Dict) -> List[STIXObject]:
        """Convert threat intelligence to STIX objects"""
        stix_objects = []
        
        # Determine STIX type based on threat characteristics
        if threat.get('threatType') == 'malware':
            malware = Malware(
                name=threat['title'],
                description=threat['content'],
                malware_types=[threat['threatType']],
                is_family=True
            )
            stix_objects.append(malware)
        
        # Create indicators for IOCs
        for ioc in threat.get('iocs', []):
            indicator = Indicator(
                name=f"IOC: {ioc}",
                pattern=f"[ipv4-addr:value = '{ioc}']",
                pattern_type="stix",
                valid_from=threat['publishedDate']
            )
            stix_objects.append(indicator)
        
        # Create threat actor
        for actor_name in threat.get('threatActors', []):
            actor = ThreatActor(
                name=actor_name,
                threat_actor_types=["criminal-org"]
            )
            stix_objects.append(actor)
            
            # Create relationship
            if stix_objects:
                rel = Relationship(
                    relationship_type="uses",
                    source_ref=actor.id,
                    target_ref=stix_objects[0].id
                )
                stix_objects.append(rel)
        
        return stix_objects
    
    def stix_to_threat(self, stix_objects: List) -> Dict:
        """Convert STIX objects back to cyber-pi format"""
        # Parse STIX bundle and extract relevant fields
        pass
```

### Phase 3: STIX Bundle Generation

```python
from stix2 import Bundle

def create_stix_bundle(threats: List[Dict]) -> Bundle:
    """Create STIX bundle for sharing"""
    stix_objects = []
    
    for threat in threats:
        converter = STIXConverter()
        objects = converter.threat_to_stix(threat)
        stix_objects.extend(objects)
    
    bundle = Bundle(objects=stix_objects)
    return bundle

# Export for sharing
bundle = create_stix_bundle(aviation_threats)
with open('aviation_threats_stix.json', 'w') as f:
    f.write(bundle.serialize(pretty=True))
```

### Phase 4: STIX Import from External Feeds

```python
def import_stix_feed(stix_bundle: Bundle):
    """Import STIX bundle from external source"""
    for obj in stix_bundle.objects:
        if obj.type == 'indicator':
            # Store indicator in Weaviate
            client.data_object.create({
                "stixId": obj.id,
                "stixType": "indicator",
                "name": obj.name,
                "pattern": obj.pattern,
                "stixObject": obj.serialize()
            }, class_name="STIXCyberObservable")
        
        elif obj.type == 'relationship':
            # Create Neo4j relationship
            create_neo4j_relationship(obj)
```

---

## 📚 STIX Resources

### Official Specifications
- **STIX 2.1 Spec**: https://docs.oasis-open.org/cti/stix/v2.1/stix-v2.1.html
- **STIX Examples**: https://oasis-open.github.io/cti-documentation/stix/examples
- **STIX Patterning**: https://docs.oasis-open.org/cti/stix/v2.1/cs01/stix-v2.1-cs01.html#_e8slinrhxcc9

### Python Libraries
```bash
pip install stix2        # Official STIX 2 library
pip install taxii2-client  # For TAXII feeds
pip install stix2-patterns  # Pattern matching
```

### Example STIX Feeds
- **MISP**: Open-source threat intelligence platform (STIX export)
- **AlienVault OTX**: Community threat intelligence (STIX format)
- **CISA AIS**: US government threat feeds (STIX/TAXII)
- **FS-ISAC**: Financial sector ISAC (STIX feeds)

---

## 🎯 Recommendation

### **Short Term (Next Sprint):**
1. ✅ **Keep current schema** for rapid development
2. ✅ **Add STIX export API** for interoperability
3. ✅ **Store STIX ID** in our objects for mapping

### **Medium Term (Q1 2026):**
1. 🔄 **Migrate to STIX-first** architecture
2. 🔄 **Import external STIX feeds** (MISP, OTX, etc.)
3. 🔄 **Export cyber-pi data** as STIX bundles

### **Long Term (Q2 2026+):**
1. 🚀 **Full STIX 2.1 compliance**
2. 🚀 **TAXII server** for feed sharing
3. 🚀 **Industry partnerships** via STIX exchange

---

## 💡 Why This Matters

### **Business Value:**
- ✅ **Interoperability** with other threat intel platforms
- ✅ **Industry credibility** using recognized standards
- ✅ **Compliance** with security frameworks (NIST, etc.)
- ✅ **Vendor partnerships** easier with STIX support
- ✅ **Data portability** can import/export anywhere

### **Technical Value:**
- ✅ **Standardized data model** less custom code
- ✅ **Community tools** leverage existing STIX ecosystem
- ✅ **Better deduplication** using STIX IDs
- ✅ **Rich semantics** STIX defines relationships formally
- ✅ **Future-proof** maintained by OASIS standards body

---

## 🔧 Immediate Action Items

1. **Add STIX properties to Weaviate schema**
   - stixId, stixType, stixObject fields

2. **Install STIX libraries**
   ```bash
   pip install stix2 stix2-patterns taxii2-client
   ```

3. **Create STIX converter utility**
   - Convert cyber-pi → STIX
   - Convert STIX → cyber-pi

4. **Document STIX mapping**
   - Our fields → STIX properties
   - Our relationships → STIX relationships

5. **Test with sample STIX feed**
   - Import from AlienVault OTX
   - Verify conversion works

---

**Conclusion:** STIX 2.1 is the **right ontology** for cyber-pi. We should adopt it incrementally to gain interoperability while maintaining development velocity.

---

**Created:** October 31, 2025  
**Standard:** STIX 2.1 (OASIS)  
**Status:** Recommended for adoption  
**Priority:** High (enables industry integration)
