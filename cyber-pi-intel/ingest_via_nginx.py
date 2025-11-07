#!/usr/bin/env python3
"""
Ingest via NGINX Gateway
Uses the NGINX gateway on port 30888 for all database access
"""

import sys
from pathlib import Path

# Set environment to use NGINX gateway
import os
os.environ['USE_NGINX_GATEWAY'] = 'true'
os.environ['NGINX_HOST'] = 'localhost'
os.environ['NGINX_PORT'] = '30888'

# Now run the main ingestion
sys.path.insert(0, str(Path(__file__).parent))

from ingest_real_data import main
import asyncio

if __name__ == "__main__":
    print("="*60)
    print("🌐 INGESTION VIA NGINX GATEWAY")
    print("Using port 30888 (no port-forwards needed)")
    print("="*60)
    print()
    
    sys.exit(asyncio.run(main()))
