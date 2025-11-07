# TQAKB V4 - The Question Answer Knowledge Base

## Next Generation Event-Driven Knowledge Management System

TQAKB V4 represents a complete architectural evolution, combining cutting-edge streaming technologies with AI-powered knowledge processing.

### Key Features

- **Event-Driven Architecture**: Apache Kafka at the core for durability and scalability
- **Hybrid Storage**: Redis (cache), Neo4j (graph), Weaviate (vectors)
- **Local AI**: Ollama for privacy-preserving embeddings and LLM processing
- **Cloud-Native**: Built for Kubernetes with MicroK8s optimizations
- **Real-Time Processing**: Sub-millisecond response times with Redis caching

### Quick Start

1. **Install Dependencies**
```bash
# Install uv for fast package management
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install Python dependencies
uv pip install --system -e ".[dev]"
```

2. **Configure Environment**
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. **Deploy to MicroK8s**
```bash
kubectl apply -k deployment/k8s/
```

4. **Run Development Server**
```bash
uvicorn backend.api.main:app --reload --host 0.0.0.0 --port 8000
```

### Architecture

- **Kafka**: Event backbone for all knowledge operations
- **Redis Stack**: High-speed cache and streaming
- **Neo4j**: Knowledge graph for relationships
- **Weaviate**: Vector database for semantic search
- **Ollama**: Local LLM for embeddings and AI

### Development

```bash
# Run tests
pytest

# Format code
black backend/
ruff check backend/ --fix

# Type checking
mypy backend/
```

### License

Apache License 2.0