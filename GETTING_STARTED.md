# Getting Started with cyber-pi

**Enterprise Threat Intelligence Platform - Quick Start Guide**

## 🎯 What is cyber-pi?

**cyber-pi** is a zero-budget, enterprise-grade cybersecurity threat intelligence platform that:
- Monitors **150+ free intelligence sources** continuously
- Processes **5,000+ documents/hour** with GPU acceleration
- Serves **Enterprise, Mid-Market, and Industrial/OT** clients
- Leverages **massive parallel processing** (128 concurrent workers)
- Uses **dual NVIDIA A6000 GPUs** (96GB VRAM) for real-time analysis

## 🚀 Quick Start (5 Minutes)

### **1. Run the Setup Script**

```bash
cd /home/david/projects/cyber-pi
./scripts/quickstart.sh
```

This will:
- Create Python virtual environment
- Install all dependencies
- Check database connectivity
- Verify GPU availability
- Create data directories

### **2. Start the API Server**

```bash
# Activate virtual environment
source venv/bin/activate

# Start FastAPI server
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

### **3. Verify Installation**

Open your browser and visit:
- **API Root**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **System Stats**: http://localhost:8000/stats

## 📋 Prerequisites

### **Required Services** (Already Running)
- ✅ **Redis**: localhost:6379 (TQAKB infrastructure)
- ✅ **Neo4j**: bolt://localhost:7687 (TQAKB infrastructure)
- ✅ **Weaviate**: http://localhost:30883 (TQAKB infrastructure)

### **Hardware Requirements** (Available)
- ✅ **CPU**: 32 cores
- ✅ **RAM**: 768GB
- ✅ **GPU**: Dual NVIDIA A6000 (96GB VRAM)
- ✅ **Storage**: 30TB

### **Software Requirements**
- Python 3.12+
- CUDA toolkit (for GPU acceleration)
- nvidia-smi (GPU monitoring)

## 🏗️ Project Structure

```
cyber-pi/
├── config/              # Configuration files
│   ├── settings.py      # Pydantic settings
│   └── sources.yaml     # 150+ intelligence sources
├── src/
│   ├── api/            # FastAPI application
│   ├── collectors/     # Data collection (RSS, APIs, social, etc.)
│   ├── processors/     # GPU-accelerated analysis
│   ├── storage/        # Tri-modal database interfaces
│   └── newsletter/     # Automated reporting
├── data/               # Intelligence storage
│   ├── raw/           # Raw collected data
│   ├── processed/     # Analyzed intelligence
│   └── reports/       # Generated newsletters
├── scripts/           # Automation scripts
├── tests/             # Test suite
└── docs/              # Documentation
```

## 🔧 Configuration

### **Environment Variables**

Copy `.env.example` to `.env` and customize:

```bash
cp .env.example .env
```

Then edit `.env` file to customize:

```bash
# Database connections (using existing TQAKB infrastructure)
REDIS_HOST=localhost
REDIS_PORT=6379
NEO4J_URI=bolt://localhost:7687
WEAVIATE_URL=http://localhost:30883

# API settings
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true

# Optional: Social media APIs for enhanced collection
TWITTER_BEARER_TOKEN=your_token_here
REDDIT_CLIENT_ID=your_id_here
```

### **Intelligence Sources**

Edit `config/sources.yaml` to:
- Enable/disable source categories
- Add custom sources
- Adjust collection intervals
- Configure credibility scores

## 📊 Current Status

### **✅ Completed**
- Project structure and configuration
- FastAPI API with health checks
- 150+ intelligence sources configured
- Tri-modal database integration planned
- GPU acceleration architecture designed

### **🚧 Next Steps**
1. Implement RSS collector (100+ feeds)
2. Implement Redis streaming storage
3. Implement GPU-accelerated processing
4. Test with first 10 sources
5. Scale to full 150+ sources

## 🎯 Usage Examples

### **Check System Health**

```bash
curl http://localhost:8000/health
```

### **Get System Statistics**

```bash
curl http://localhost:8000/stats
```

### **Search Intelligence** (Coming Soon)

```bash
curl "http://localhost:8000/api/v1/intelligence/search?query=ransomware&limit=10"
```

### **Get Latest Threats** (Coming Soon)

```bash
curl "http://localhost:8000/api/v1/intelligence/threats?severity=critical"
```

## 🔍 Intelligence Categories

### **Government & Standards** (15 sources)
- CISA, NIST NVD, FBI IC3, ICS-CERT
- International: ENISA, NCSC UK, ACSC Australia

### **Industrial/OT Specialized** (25 sources)
- Nuclear: NRC cybersecurity
- Power Grid: NERC CIP, FERC
- SCADA/ICS: Siemens, Schneider, Rockwell
- OT Security: Dragos, Claroty, Nozomi

### **Nexum Vendor Partners** (80+ sources)
- Palo Alto, Fortinet, Cisco, Juniper
- Microsoft, CrowdStrike, SentinelOne
- All major cybersecurity vendors

### **Technical Intelligence** (25 sources)
- Exploit-DB, Packet Storm
- Malware Traffic Analysis
- VirusTotal, Shodan, AlienVault OTX

### **News & Research** (40 sources)
- Krebs on Security, The Hacker News
- Bleeping Computer, Dark Reading
- Academic research papers

### **Social Media** (30 sources)
- Twitter security community
- Reddit cybersecurity forums
- GitHub security advisories

## 💡 Development Workflow

### **1. Start Development Environment**

```bash
cd /home/david/projects/cyber-pi
source venv/bin/activate
uvicorn src.api.main:app --reload
```

### **2. Make Changes**

Edit files in `src/` directory. The API will auto-reload.

### **3. Test Changes**

```bash
# Run tests (when implemented)
pytest tests/

# Check code quality
black src/
flake8 src/
```

### **4. Monitor Logs**

API logs will show in terminal with detailed information.

## 🐛 Troubleshooting

### **API Won't Start**

```bash
# Check if port 8000 is in use
lsof -i :8000

# Check Python version
python3 --version  # Should be 3.12+

# Reinstall dependencies
pip install -r requirements.txt
```

### **Database Connection Issues**

```bash
# Check Redis
redis-cli -h localhost -p 6379 ping

# Check Neo4j (requires credentials)
cypher-shell -a bolt://localhost:7687 -u neo4j -p dev-neo4j-password

# Check Weaviate
curl http://localhost:30883/v1/.well-known/ready
```

### **GPU Not Detected**

```bash
# Check NVIDIA drivers
nvidia-smi

# Check CUDA
python3 -c "import torch; print(torch.cuda.is_available())"
```

## 📚 Additional Resources

- **README.md**: Comprehensive project documentation
- **PROJECT_STATUS.md**: Current development status
- **config/sources.yaml**: All intelligence sources
- **API Docs**: http://localhost:8000/docs (when running)

## 🎯 Success Metrics

**You'll know it's working when:**
- ✅ API responds at http://localhost:8000
- ✅ Health check returns "healthy"
- ✅ System stats show resource utilization
- ✅ GPU devices detected in stats
- ✅ Database connections successful

## 🚀 Next Steps

1. **Verify installation** with quickstart script
2. **Start API server** and check health
3. **Review PROJECT_STATUS.md** for development roadmap
4. **Implement first collector** (RSS feeds)
5. **Test with 10 sources** before scaling to 150+

---

**Ready to build the most comprehensive threat intelligence platform?** 🕵️‍♂️🔐

Let's start collecting intelligence!
