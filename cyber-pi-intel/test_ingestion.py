#!/usr/bin/env python3
"""
Test ingestion with first 5 items
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from ingest_real_data import RealDataIngestionPipeline
import asyncio

async def test_ingestion():
    """Test with first 5 items"""
    print("🧪 TEST: Ingesting first 5 items\n")
    
    # Initialize
    pipeline = RealDataIngestionPipeline()
    await pipeline.connect_databases()
    
    # Load data
    filepath = "/home/david/projects/cyber-pi/data/raw/master_collection_20251031_014039.json"
    with open(filepath) as f:
        data = json.load(f)
    
    items = data['items'][:5]  # First 5 only
    print(f"📊 Testing with {len(items)} items\n")
    
    for i, item in enumerate(items, 1):
        print(f"\n--- Item {i}/5 ---")
        print(f"Title: {item['title'][:80]}")
        
        # Parse
        threat = pipeline.parse_cyber_pi_item(item)
        print(f"Threat ID: {threat['threatId']}")
        print(f"Severity: {threat['severity']}")
        print(f"Type: {threat['threatType']}")
        print(f"Industries: {threat['industry']}")
        print(f"CVEs: {threat['cves']}")
        print(f"Actors: {threat['threatActors']}")
        
        # Ingest
        success = await pipeline.ingest_threat(threat)
        print(f"✅ Ingested successfully" if success else "❌ Failed")
    
    # Stats
    pipeline.print_stats()
    
    # Close
    await pipeline.close()
    
    print("\n✅ Test complete!")

if __name__ == "__main__":
    asyncio.run(test_ingestion())
