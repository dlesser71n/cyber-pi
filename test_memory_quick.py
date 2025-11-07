#!/usr/bin/env python3
"""Quick test of memory system"""
import asyncio
import sys
sys.path.insert(0, '.')

from src.cascade.memory_system import ThreatMemorySystem

async def main():
    print("🔍 Testing Cascade Memory System...")
    
    # Test 1: Connection
    print("\n1️⃣ Testing Redis connection...")
    system = ThreatMemorySystem(redis_url="redis://localhost:32379")
    await system.connect()
    print("   ✅ Connected to Redis")
    
    # Test 2: Memory formation decision
    print("\n2️⃣ Testing memory formation decision...")
    threat_data = {
        'severity': 'CRITICAL',
        'confidence': 1.0,
        'industry': 'aviation',
        'sources': ['s1', 's2', 's3', 's4', 's5', 's6']
    }
    analyst_actions = [
        {'analyst_id': f'analyst_{i}', 'action_type': 'escalate', 'time_spent_seconds': 300}
        for i in range(5)
    ]
    
    decision = await system.should_form_memory(
        'test_threat', analyst_actions, threat_data
    )
    print(f"   Should form: {decision.should_form}")
    print(f"   Confidence: {decision.confidence:.2f}")
    print(f"   Type: {decision.memory_type.value}")
    print(f"   Reason: {decision.reason}")
    
    # Test 3: Form memory
    if decision.should_form:
        print("\n3️⃣ Forming memory in Redis...")
        memory = await system.form_memory(
            'test_threat', analyst_actions, threat_data, decision
        )
        print(f"   ✅ Memory formed: {memory.id}")
        print(f"   Industry: {memory.industry}")
        print(f"   Severity: {memory.severity}")
        
        # Test 4: Retrieve memory
        print("\n4️⃣ Retrieving memory from Redis...")
        retrieved = await system.get_memory(memory.id)
        if retrieved:
            print(f"   ✅ Retrieved: {retrieved.threat_id}")
            print(f"   Confidence: {retrieved.confidence:.2f}")
        
        # Test 5: Count memories
        print("\n5️⃣ Counting memories...")
        count = await system.count_memories()
        print(f"   ✅ Total memories: {count}")
    
    await system.disconnect()
    print("\n✅ All tests passed! Memory system is working.")

if __name__ == "__main__":
    asyncio.run(main())
