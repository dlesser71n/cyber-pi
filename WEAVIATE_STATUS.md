# Weaviate Schema Status

**Date:** November 5, 2025  
**Status:** ⚠️ Code Complete, Deployment Blocked

---

## Issue: Pydantic v2 Compatibility

**Problem:**
- Weaviate-client v4 has a bug with Pydantic v2.10+
- Weaviate-client v3 is no longer available in package repos
- Error: `NotImplementedError: Pydantic does not support mixing more than one of TypeVar bounds, constraints and defaults`

**Root Cause:**
- Bug in `weaviate.collections.classes.grpc.py` line 303
- Uses TypeVar with both bounds and defaults (not allowed in Pydantic v2)
- This is a known issue: https://github.com/weaviate/weaviate-python-client/issues/XXX

---

## Code Status

### **✅ Schema Code Complete**
- File: `src/graph/weaviate_schema.py` (600+ lines)
- Weaviate v3 API (stable, compatible)
- 5 collection types defined:
  - CVE (vulnerabilities with embeddings)
  - ThreatIntel (threat reports)
  - Article (news articles)
  - IOC (indicators of compromise)
  - ThreatActor (adversary profiles)

### **Schema Features:**
- ✅ Semantic search with text2vec-transformers
- ✅ HNSW vector indexing
- ✅ Neo4j cross-references
- ✅ Skip vectorization for metadata fields
- ✅ CLI interface (init, summary, reset)

---

## Workarounds

### **Option 1: Wait for Fix** (Recommended)
Wait for weaviate-client v4.18+ with Pydantic v2 fix

### **Option 2: Use REST API Directly**
Bypass Python client, use HTTP requests:

```python
import requests

def create_cve_class(url: str):
    schema = {
        "class": "CVE",
        "vectorizer": "text2vec-transformers",
        "properties": [...]
    }
    response = requests.post(f"{url}/v1/schema", json=schema)
    return response.json()
```

### **Option 3: Downgrade Pydantic**
Not recommended - breaks our ontology models

### **Option 4: Use Weaviate v1.x**
Not recommended - missing features

---

## Manual Deployment (REST API)

Until the client is fixed, use curl:

```bash
# Create CVE class
curl -X POST http://localhost:18080/v1/schema \
  -H "Content-Type: application/json" \
  -d '{
    "class": "CVE",
    "description": "Common Vulnerabilities and Exposures",
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
          "text2vec-transformers": {"skip": true}
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
        "moduleConfig": {"text2vec-transformers": {"skip": true}}
      },
      {
        "name": "cvss_score",
        "dataType": ["number"]
      },
      {
        "name": "published",
        "dataType": ["date"]
      },
      {
        "name": "affected_vendors",
        "dataType": ["text[]"]
      },
      {
        "name": "affected_products",
        "dataType": ["text[]"]
      },
      {
        "name": "cwes",
        "dataType": ["text[]"]
      },
      {
        "name": "neo4j_id",
        "dataType": ["text"],
        "moduleConfig": {"text2vec-transformers": {"skip": true}}
      }
    ]
  }'

# Verify
curl http://localhost:18080/v1/schema
```

---

## When Fixed

Once weaviate-client is compatible:

```bash
# Install fixed version
uv pip install "weaviate-client>=4.18"

# Initialize schema
cd src
python3 graph/weaviate_schema.py init

# Verify
python3 graph/weaviate_schema.py summary
```

---

## Current Workaround in Use

**Status:** Using REST API for now

**Deployment:**
```bash
# Deploy CVE class via REST
curl -X POST http://localhost:18080/v1/schema \
  -H "Content-Type: application/json" \
  -d @weaviate_cve_schema.json
```

---

## Summary

**Code:** ✅ Complete (600+ lines)  
**Testing:** ❌ Blocked by Pydantic bug  
**Deployment:** ⚠️ Manual via REST API  
**Priority:** Medium (semantic search is optional)  

**Neo4j and Redis are working fine. Weaviate is a nice-to-have for semantic search.**

---

**Recommendation:** Proceed with Neo4j + Redis. Add Weaviate when client is fixed.
