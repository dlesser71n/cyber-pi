#!/usr/bin/env python3
"""
Simple manual tests for Level 1 Memory
No pytest - just direct async testing
"""
import asyncio
import sys
sys.path.insert(0, '.')

from src.cascade.level1_memory import Level1Memory


async def run_tests():
    """Run all tests"""
    print("🧪 Testing Level 1 Memory System\n")
    
    memory = Level1Memory()
    passed = 0
    failed = 0
    
    try:
        # Test 1: Add threat
        print("Test 1: Add threat...")
        threat = await memory.add_threat("test_001", "Test content", "HIGH")
        assert threat.threat_id == "test_001"
        print("   ✅ PASS\n")
        passed += 1
        
        # Test 2: Get threat
        print("Test 2: Get threat...")
        retrieved = await memory.get_threat("test_001")
        assert retrieved is not None
        assert retrieved.threat_id == "test_001"
        print("   ✅ PASS\n")
        passed += 1
        
        # Test 3: Record interaction
        print("Test 3: Record interaction...")
        updated = await memory.record_interaction("test_001", "analyst_1")
        assert updated.interaction_count == 1
        print("   ✅ PASS\n")
        passed += 1
        
        # Test 4: Multiple interactions
        print("Test 4: Multiple interactions...")
        await memory.record_interaction("test_001", "analyst_2")
        await memory.record_interaction("test_001", "analyst_3")
        threat = await memory.get_threat("test_001")
        assert threat.interaction_count == 3
        print("   ✅ PASS\n")
        passed += 1
        
        # Test 5: Get all active
        print("Test 5: Get all active...")
        await memory.add_threat("test_002", "Content 2", "CRITICAL")
        await memory.add_threat("test_003", "Content 3", "MEDIUM")
        active = await memory.get_all_active()
        assert len(active) >= 3
        print(f"   ✅ PASS ({len(active)} active threats)\n")
        passed += 1
        
        # Test 6: Count active
        print("Test 6: Count active...")
        count = await memory.count_active()
        assert count >= 3
        print(f"   ✅ PASS (count: {count})\n")
        passed += 1
        
        # Test 7: Hot threats
        print("Test 7: Hot threats...")
        await memory.add_threat("hot_threat", "Hot content", "CRITICAL")
        for i in range(5):
            await memory.record_interaction("hot_threat", f"analyst_{i}")
        hot = await memory.get_hot_threats(min_interactions=3)
        assert len(hot) >= 1
        assert any(t.threat_id == "hot_threat" for t in hot)
        print(f"   ✅ PASS ({len(hot)} hot threats)\n")
        passed += 1
        
        # Test 8: Statistics
        print("Test 8: Statistics...")
        stats = await memory.get_stats()
        assert stats['total_active'] > 0
        assert stats['total_interactions'] > 0
        print(f"   ✅ PASS (stats: {stats})\n")
        passed += 1
        
        # Test 9: Remove threat
        print("Test 9: Remove threat...")
        removed = await memory.remove_threat("test_002")
        assert removed is True
        retrieved = await memory.get_threat("test_002")
        assert retrieved is None
        print("   ✅ PASS\n")
        passed += 1
        
        # Test 10: Get non-existent
        print("Test 10: Get non-existent threat...")
        retrieved = await memory.get_threat("does_not_exist")
        assert retrieved is None
        print("   ✅ PASS\n")
        passed += 1
        
        # Cleanup
        print("Cleaning up...")
        await memory.clear_all()
        count = await memory.count_active()
        assert count == 0
        print("   ✅ Cleanup complete\n")
        
    except AssertionError as e:
        print(f"   ❌ FAIL: {e}\n")
        failed += 1
    except Exception as e:
        print(f"   ❌ ERROR: {e}\n")
        failed += 1
    finally:
        await memory.disconnect()
    
    # Summary
    print("=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed == 0:
        print("\n🎉 All tests passed! Level 1 is working perfectly.")
        print("Ready to add Level 2 when you want.")
    else:
        print(f"\n⚠️  {failed} test(s) failed. Need to fix before proceeding.")
    
    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(run_tests())
    sys.exit(0 if success else 1)
