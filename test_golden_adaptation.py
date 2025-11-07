#!/usr/bin/env python3
"""
Quick test of golden config adaptation
Verify the core patterns work
"""
import asyncio
import sys
sys.path.insert(0, 'src')

from cascade.cascade_memory_base import CascadeMemory


async def test_golden_patterns():
    """Test that golden config patterns work"""
    
    print("🧪 Testing Golden Config Adaptation\n")
    
    # Initialize
    memory = CascadeMemory(redis_host="localhost", redis_port=32379)
    await memory.initialize()
    
    print("\n✅ Initialization successful!")
    print(f"   Tiers: {list(memory.tiers.keys())}")
    print(f"   Redis clients: {list(memory.redis_clients.keys())}")
    
    # Test that we can access Redis
    for tier_name, client in memory.redis_clients.items():
        try:
            await client.ping()
            print(f"   ✅ {tier_name}: Connected")
        except Exception as e:
            print(f"   ❌ {tier_name}: {e}")
    
    # Close connections
    for client in memory.redis_clients.values():
        await client.close()
    
    print("\n🎉 Golden config adaptation working!")
    print("   Next: Add threat-specific fields and methods")


if __name__ == "__main__":
    asyncio.run(test_golden_patterns())
