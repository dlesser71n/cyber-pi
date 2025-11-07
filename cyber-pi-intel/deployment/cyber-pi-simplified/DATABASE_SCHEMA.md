# Database Schema - Self-Descriptive Names
# Cyber-PI Threat Intelligence System

**Created:** October 31, 2025  
**Purpose:** Document self-descriptive database schemas for clarity and maintainability

---

## 🎯 Naming Philosophy

**Principle:** Database names, classes, and labels should be **immediately understandable** without documentation.

**Benefits:**
- New developers understand the system faster
- Queries are self-documenting
- Reduces confusion between databases
- Easier to debug and maintain

---

## 📊 Weaviate Schema

### Class Name: `CyberThreatIntelligence`

**Why this name:**
- ✅ **Self-descriptive:** Immediately clear what data is stored
- ✅ **Specific:** Not generic like "Data" or "Item"
- ✅ **Domain-relevant:** Matches cyber-pi's purpose
- ✅ **PascalCase:** Weaviate convention

**Alternative names considered:**
- ❌ `Threat` - Too generic
- ❌ `ThreatData` - Vague
- ❌ `IntelligenceItem` - Unclear domain
- ✅ `CyberThreatIntelligence` - **PERFECT**

### Properties (25 Fields)

**Core Identity:**
- `threatId` - Unique identifier (SHA-256 hash)
- `title` - Threat headline
- `content` - Full threat description
- `summary` - Brief summary

**Source Information:**
- `source` - Origin of intelligence (RSS, social, etc.)
- `sourceUrl` - Original URL
- `publishedDate` - When published
- `ingestedDate` - When ingested into cyber-pi
- `lastUpdated` - Last update time

**Classification:**
- `industry` - Target industries (array)
- `severity` - critical, high, medium, low
- `threatType` - ransomware, phishing, malware, etc. (array)
- `verificationStatus` - verified, unverified, disputed
- `confidence` - Confidence score (0.0-1.0)

**Threat Intelligence:**
- `threatActors` - Known actors/groups (array)
- `cves` - CVE identifiers (array)
- `iocs` - Indicators of Compromise (array)
- `mitreTactics` - MITRE ATT&CK tactics (array)
- `mitreTechniques` - MITRE ATT&CK techniques (array)

**Impact Assessment:**
- `affectedProducts` - Products affected (array)
- `affectedVendors` - Vendors affected (array)
- `recommendedActions` - Mitigation actions (array)

**Relationships:**
- `relatedThreats` - Related threat IDs (array)
- `tags` - Additional categorization (array)
- `metadata` - Extra data as JSON string

**Query Example:**
```python
# Self-documenting Weaviate query
result = client.query.get(
    "CyberThreatIntelligence",  # Clear what we're querying
    ["title", "severity", "industry", "threatActors"]
).with_near_text({
    "concepts": ["ransomware targeting aviation"]
}).with_limit(10).do()
```

---

## 🔗 Neo4j Graph Schema

### Node Labels (Self-Descriptive)

**Primary Nodes:**

1. **`CyberThreat`** - Individual threat intelligence items
   - Properties: `threatId`, `title`, `severity`, `publishedDate`, etc.
   - Why: Clear distinction from threat actors or tactics

2. **`ThreatActor`** - Malicious actors and groups
   - Properties: `actorName`, `aliases`, `country`, `motivation`
   - Why: Explicit "ThreatActor" vs generic "Actor"

3. **`Industry`** - Target industries (18 verticals)
   - Properties: `industryName`, `threatCount`, `description`
   - Why: Business domain concept, not technical

4. **`CVE`** - Common Vulnerabilities and Exposures
   - Properties: `cveId`, `cvssScore`, `description`
   - Why: Standard security term, immediately recognizable

5. **`TTP`** - Tactics, Techniques, and Procedures
   - Properties: `ttpId`, `name`, `description`
   - Why: Security industry standard acronym

6. **`IOC`** - Indicators of Compromise
   - Properties: `iocValue`, `iocType` (IP, domain, hash, etc.)
   - Why: Standard threat intelligence term

7. **`Vendor`** - Technology vendors
   - Properties: `vendorName`, `products`, `website`
   - Why: Clear business entity

8. **`Product`** - Software/hardware products
   - Properties: `productName`, `version`, `vendor`
   - Why: Specific to products being affected

9. **`MitreTactic`** - MITRE ATT&CK tactics
   - Properties: `tacticId`, `name`, `description`
   - Why: Explicit MITRE framework reference

10. **`MitreTechnique`** - MITRE ATT&CK techniques
    - Properties: `techniqueId`, `name`, `tactics`
    - Why: Explicit MITRE framework reference

### Relationship Types (Self-Descriptive)

**All relationships use descriptive verbs:**

1. **`TARGETS`** - CyberThreat → Industry
   - Example: `(threat:CyberThreat)-[:TARGETS]->(industry:Industry)`
   - Why: Clear action verb

2. **`ATTRIBUTED_TO`** - CyberThreat → ThreatActor
   - Example: `(threat)-[:ATTRIBUTED_TO]->(actor:ThreatActor)`
   - Why: Security industry standard term

3. **`EXPLOITS`** - CyberThreat → CVE
   - Example: `(threat)-[:EXPLOITS]->(cve:CVE)`
   - Why: Specific action, clear meaning

4. **`USES`** - ThreatActor → TTP
   - Example: `(actor)-[:USES]->(ttp:TTP)`
   - Why: Simple, clear verb

5. **`CONTAINS`** - CyberThreat → IOC
   - Example: `(threat)-[:CONTAINS]->(ioc:IOC)`
   - Why: Threat contains indicators

6. **`AFFECTS`** - CyberThreat → Vendor/Product
   - Example: `(threat)-[:AFFECTS]->(product:Product)`
   - Why: Impact relationship

7. **`INVOLVES_TACTIC`** - CyberThreat → MitreTactic
   - Example: `(threat)-[:INVOLVES_TACTIC]->(tactic:MitreTactic)`
   - Why: Explicit MITRE connection

8. **`USES_TECHNIQUE`** - CyberThreat → MitreTechnique
   - Example: `(threat)-[:USES_TECHNIQUE]->(tech:MitreTechnique)`
   - Why: Clear technique usage

9. **`RELATED_TO`** - CyberThreat → CyberThreat
   - Example: `(threat1)-[:RELATED_TO]->(threat2)`
   - Why: Generic relationship for similar threats

10. **`SIMILAR_TO`** - ThreatActor → ThreatActor
    - Example: `(actor1)-[:SIMILAR_TO]->(actor2)`
    - Why: Actor similarity/association

11. **`PART_OF`** - MitreTechnique → MitreTactic
    - Example: `(technique)-[:PART_OF]->(tactic)`
    - Why: Hierarchical MITRE structure

### Query Examples (Self-Documenting)

**Find threats targeting specific industry:**
```cypher
MATCH (t:CyberThreat)-[:TARGETS]->(i:Industry {industryName: 'Aviation & Airlines'})
RETURN t.threatId, t.title, t.severity
ORDER BY t.publishedDate DESC
```

**Find attack chain:**
```cypher
MATCH path = (t:CyberThreat)-[:USES_TECHNIQUE]->(tech:MitreTechnique)
             -[:PART_OF]->(tactic:MitreTactic)
WHERE t.threatId = 'THREAT_ID'
RETURN path
```

**Find threats by actor:**
```cypher
MATCH (actor:ThreatActor {actorName: 'Lockbit'})
      <-[:ATTRIBUTED_TO]-(t:CyberThreat)
      -[:TARGETS]->(i:Industry)
RETURN actor.actorName, t.title, i.industryName, t.severity
```

---

## 🏭 18 Industry Nodes (Pre-Created)

**All industries initialized with self-descriptive names:**

1. Aviation & Airlines
2. Healthcare & Medical
3. Energy & Utilities
4. Financial Services
5. Manufacturing
6. Retail & E-commerce
7. Technology
8. Telecommunications
9. Government & Public Sector
10. Education
11. Transportation & Logistics
12. Hospitality & Entertainment
13. Real Estate
14. Agriculture
15. Mining & Resources
16. Professional Services
17. Media & Publishing
18. Pharmaceuticals

**Why these names:**
- ✅ Match cyber-pi's 18 industry verticals
- ✅ Business-friendly (not technical jargon)
- ✅ Immediately recognizable
- ✅ Consistent formatting (Title Case)

---

## 📝 Naming Conventions Summary

### Weaviate
```
Class:      PascalCase, descriptive noun phrase
            Example: CyberThreatIntelligence

Properties: camelCase, clear purpose
            Examples: threatId, publishedDate, affectedProducts
```

### Neo4j
```
Node Labels:   PascalCase, descriptive nouns
               Examples: CyberThreat, ThreatActor, Industry

Relationships: SCREAMING_SNAKE_CASE, action verbs
               Examples: TARGETS, ATTRIBUTED_TO, USES_TECHNIQUE

Properties:    camelCase, consistent with Weaviate
               Examples: threatId, actorName, industryName
```

### Why Consistent Naming Matters

**Before (Generic Names):**
```cypher
// What is this?
MATCH (n:Item)-[:REL]->(m:Data)
WHERE n.id = 'abc123'
RETURN n, m
```

**After (Self-Descriptive):**
```cypher
// Crystal clear!
MATCH (threat:CyberThreat)-[:TARGETS]->(industry:Industry)
WHERE threat.threatId = 'abc123'
RETURN threat, industry
```

---

## 🔄 Integration with cyber-pi

### SimplifiedRouter Updates

The `SimplifiedRouter` class uses these schemas:

```python
# Weaviate ingestion
async def ingest_threat(self, threat: Dict):
    # Store in CyberThreatIntelligence class
    self.weaviate.data_object.create(
        data_object={
            "threatId": threat_id,
            "title": threat.get('title'),
            "content": threat.get('content'),
            "industry": threat.get('industry'),
            "severity": threat.get('severity'),
            # ... all 25 properties
        },
        class_name="CyberThreatIntelligence"  # Self-descriptive!
    )

# Neo4j graph creation
async def _build_graph_relationships(self, threat_id: str, threat: Dict):
    # Create CyberThreat node
    await session.run("""
        MERGE (t:CyberThreat {threatId: $id})
        SET t.title = $title,
            t.severity = $severity
    """, id=threat_id, title=threat.get('title'), ...)
    
    # Create TARGETS relationship to Industry
    await session.run("""
        MATCH (t:CyberThreat {threatId: $threat_id})
        MERGE (i:Industry {industryName: $industry})
        MERGE (t)-[:TARGETS]->(i)
    """, threat_id=threat_id, industry=threat.get('industry'))
```

---

## 🚀 Initialization

**Run initialization:**
```bash
cd /home/david/projects/cyber-pi-intel/deployment/cyber-pi-simplified

# Initialize both databases
./initialize-all.sh

# Or initialize separately
python3 initialize-weaviate.py
python3 initialize-neo4j.py
```

**Verify schemas:**
```bash
# Weaviate
curl http://localhost:30883/v1/schema | jq

# Neo4j (in browser)
# http://localhost:30474
# Run: CALL db.schema.visualization()
```

---

## 📊 Schema Benefits

### For Developers
✅ Immediately understand what data is stored  
✅ Queries are self-documenting  
✅ No need to constantly reference docs  
✅ Easier to debug issues  
✅ Faster onboarding for new team members

### For Operations
✅ Clear database monitoring (know what each DB stores)  
✅ Better log messages (descriptive names in errors)  
✅ Easier troubleshooting  
✅ Clear backup/restore procedures

### For Integration
✅ cyber-pi can easily query threat intelligence  
✅ API responses are self-explanatory  
✅ Frontend developers understand data structure  
✅ Third-party integrations are clearer

---

## 🎯 Summary

**Weaviate:**
- Class: `CyberThreatIntelligence`
- 25 comprehensive properties
- Self-descriptive property names

**Neo4j:**
- 10 node labels (CyberThreat, ThreatActor, Industry, etc.)
- 11 relationship types (TARGETS, ATTRIBUTED_TO, etc.)
- 18 pre-created Industry nodes

**Result:**
Every query, every relationship, every property is **immediately understandable** without documentation!

---

**Last Updated:** October 31, 2025  
**Status:** Ready for initialization  
**Scripts:** initialize-weaviate.py, initialize-neo4j.py, initialize-all.sh
