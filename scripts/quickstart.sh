#!/bin/bash
# cyber-pi Quick Start Script
# Sets up the development environment and starts the system

set -e

echo "🚀 cyber-pi Quick Start"
echo "========================"
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo -e "${BLUE}Project root: $PROJECT_ROOT${NC}"
echo ""

# Check Python version
echo -e "${BLUE}Checking Python version...${NC}"
python3 --version
echo ""

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${GREEN}✓ Virtual environment already exists${NC}"
fi
echo ""

# Activate virtual environment
echo -e "${BLUE}Activating virtual environment...${NC}"
source venv/bin/activate
echo -e "${GREEN}✓ Virtual environment activated${NC}"
echo ""

# Upgrade pip
echo -e "${BLUE}Upgrading pip...${NC}"
pip install --upgrade pip
echo ""

# Install dependencies
echo -e "${BLUE}Installing dependencies...${NC}"
echo -e "${YELLOW}This may take a few minutes...${NC}"
pip install -r requirements.txt
echo -e "${GREEN}✓ Dependencies installed${NC}"
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Creating .env from .env.example...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✓ .env file created${NC}"
    echo -e "${YELLOW}⚠️  Please edit .env with your configuration${NC}"
else
    echo -e "${GREEN}✓ .env file exists${NC}"
fi
echo ""

# Create data directories
echo -e "${BLUE}Creating data directories...${NC}"
mkdir -p data/raw data/processed data/reports
echo -e "${GREEN}✓ Data directories created${NC}"
echo ""

# Check database connectivity
echo -e "${BLUE}Checking database connectivity...${NC}"

# Redis
if command -v redis-cli &> /dev/null; then
    if redis-cli -h localhost -p 6379 ping &> /dev/null; then
        echo -e "${GREEN}✓ Redis: Connected (localhost:6379)${NC}"
    else
        echo -e "${YELLOW}⚠️  Redis: Not responding (localhost:6379)${NC}"
        echo -e "${YELLOW}   Start Redis with: docker run -d -p 6379:6379 redis${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  redis-cli not found, skipping Redis check${NC}"
fi

# Neo4j
echo -e "${YELLOW}⚠️  Neo4j: Check manually at bolt://localhost:7687${NC}"

# Weaviate
if curl -s http://localhost:30883/v1/.well-known/ready &> /dev/null; then
    echo -e "${GREEN}✓ Weaviate: Connected (localhost:30883)${NC}"
else
    echo -e "${YELLOW}⚠️  Weaviate: Not responding (localhost:30883)${NC}"
fi
echo ""

# Check GPU availability
echo -e "${BLUE}Checking GPU availability...${NC}"
if command -v nvidia-smi &> /dev/null; then
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
    echo -e "${GREEN}✓ NVIDIA GPUs detected${NC}"
else
    echo -e "${YELLOW}⚠️  nvidia-smi not found, GPU acceleration may not be available${NC}"
fi
echo ""

# Display system info
echo -e "${BLUE}System Information:${NC}"
echo "  CPU Cores: $(nproc)"
echo "  Total RAM: $(free -h | awk '/^Mem:/ {print $2}')"
echo "  Disk Space: $(df -h . | awk 'NR==2 {print $4}') available"
echo ""

# Start the API
echo -e "${GREEN}========================${NC}"
echo -e "${GREEN}Setup Complete!${NC}"
echo -e "${GREEN}========================${NC}"
echo ""
echo -e "${BLUE}To start the API server:${NC}"
echo -e "  ${YELLOW}cd $PROJECT_ROOT${NC}"
echo -e "  ${YELLOW}source venv/bin/activate${NC}"
echo -e "  ${YELLOW}uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload${NC}"
echo ""
echo -e "${BLUE}API will be available at:${NC}"
echo -e "  ${GREEN}http://localhost:8000${NC}"
echo -e "  ${GREEN}http://localhost:8000/docs${NC} (API documentation)"
echo ""
echo -e "${BLUE}To start intelligence collection:${NC}"
echo -e "  ${YELLOW}python src/collectors/parallel_master.py${NC}"
echo ""
