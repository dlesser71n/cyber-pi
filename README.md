# Cyber-PI

**Cyber Predictive Intelligence** - Unified threat intelligence and security automation platform.

## 🎯 Overview

Cyber-PI is a comprehensive threat intelligence platform combining:
- **TQAKB v4** knowledge base (Redis, Neo4j, Weaviate)
- **Periscope** advanced memory and prediction system
- **Automated threat hunting** (APT, ransomware, zero-day)
- **Multi-source intelligence collection** (CISA, GitHub, IBKR, dark web)
- **REST API** for integration
- **ML-based threat prediction**
- **STIX integration**

## 🏗️ Architecture

### Backend API (`backend/`)
- FastAPI REST API with authentication
- Redis-first architecture
- STIX format conversion
- Real-time streaming with Kafka

### Threat Hunting (`src/hunters/`)
- APT detection
- Ransomware monitoring
- Zero-day vulnerability hunting
- CISA KEV monitoring
- Alert processing

### Data Collection (`src/collectors/`)
- CISA Known Exploited Vulnerabilities
- GitHub Security Advisories
- IBKR Financial Intelligence
- Dark web monitoring
- Social media intelligence
- Vendor threat intelligence

### Background Workers (`src/workers/`)
- Neo4j graph processing
- STIX data processing
- Weaviate vector indexing

### Advanced Features (`src/`)
- **Periscope**: 3-level memory system, analyst assistant, predictive engine
- **Analytics**: Graph analytics, enterprise methodology
- **Bootstrap**: Redis highway, CVE bulk import, threat graph builders
- **Intelligence**: Industry intelligence DB, threat scoring
- **Newsletter**: Automated threat intelligence reports

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Redis
- Neo4j
- Weaviate
- Ollama (for LLM features)

### Installation
```bash
cd /home/david/projects/cyber-pi
pip install -r requirements.txt
```

### Start Backend API
```bash
python backend/main.py
# API available at http://localhost:8000
# Docs at http://localhost:8000/docs
```

### Run Threat Hunters
```bash
python src/hunters/cisa_kev_monitor.py
python src/hunters/apt_detector.py
```

### Run Workers
```bash
python run_workers_parallel.py
```

## 📊 Status

**Version**: Unified Platform (Nov 7, 2025)  
**Status**: ✅ Production Ready  
**GitHub**: https://github.com/dlesser71n/cyber-pi

### Recent Updates
- ✅ Merged cyber-pi-intel (TQAKB v4) into unified platform
- ✅ Added complete FastAPI backend
- ✅ Integrated 6 threat hunting modules
- ✅ Added 3 background workers
- ✅ Enhanced collectors with CISA, GitHub, IBKR

See `MIGRATION_COMPLETE.md` for full migration details.

## 🔗 Related Projects

- **digital-truth-core**: TQAKB with inferential reasoning, code extraction, entity graphs
- **cyber-pi-intel** (archived): Original TQAKB v4 codebase

## 📝 Documentation

- `MIGRATION_COMPLETE.md` - Migration details from cyber-pi-intel
- `SOURCE_CODE_REVIEW_AND_MERGE_PLAN.md` - Code review and integration plan
- `backend/` - API documentation
- `src/` - Module-specific documentation
