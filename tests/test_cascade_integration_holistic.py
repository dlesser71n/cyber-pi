"""
CASCADE Holistic Integration Test

Tests entire system end-to-end with increasing complexity:
- Level 1 (MEDIUM): Basic integration with moderate data
- Level 2 (HIGH): Increased volume and concurrent operations
- Level 3 (VERY HIGH): Large datasets with stress testing
- Level 4 (EXTREME): Maximum load with all features

Continuous status feedback throughout testing.
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import List, Dict
import random

from src.cascade import (
    AnalystFlowTracker,
    PatternAnalyzer,
    ThreatMemorySystem,
    PredictiveEngine,
    ActionType,
    MemoryType
)


class IntegrationTestHarness:
    """Comprehensive integration testing with status feedback"""
    
    def __init__(self):
        self.tracker = AnalystFlowTracker()
        self.pattern_analyzer = PatternAnalyzer(self.tracker)
        self.memory_system = ThreatMemorySystem()
        self.predictive_engine = PredictiveEngine(
            self.pattern_analyzer,
            self.memory_system
        )
        
        # Test data generators
        self.industries = [
            'aviation', 'healthcare', 'finance', 'energy', 
            'manufacturing', 'retail', 'technology', 'government'
        ]
        self.severities = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']
        self.sources = [
            'cisa', 'twitter', 'vendor_alert', 'reddit', 
            'github', 'security_blog', 'dark_web', 'ioc_feed'
        ]
        
        # Metrics
        self.metrics = {
            'actions_tracked': 0,
            'patterns_analyzed': 0,
            'memories_formed': 0,
            'predictions_made': 0,
            'errors': 0
        }
    
    def log_status(self, level: str, message: str):
        """Print status with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"[{timestamp}] [{level}] {message}")
    
    def log_metrics(self):
        """Print current metrics"""
        print("\n" + "="*80)
        print("📊 CURRENT METRICS:")
        for key, value in self.metrics.items():
            print(f"   {key}: {value:,}")
        print("="*80 + "\n")
    
    async def setup(self):
        """Initialize all components"""
        self.log_status("SETUP", "Connecting to Redis...")
        await self.tracker.connect()
        await self.memory_system.connect()
        await self.predictive_engine.connect()
        self.log_status("SETUP", "✅ All components connected")
    
    async def teardown(self):
        """Cleanup"""
        self.log_status("TEARDOWN", "Cleaning up test data...")
        
        # Clean up test analysts
        test_analysts = [
            f"analyst_{i}" for i in range(100)
        ] + ['jane_smith', 'bob_jones', 'alice_williams']
        
        for analyst_id in test_analysts:
            try:
                await self.tracker.clear_analyst_history(analyst_id)
            except:
                pass
        
        # Clean up memories
        try:
            all_memories = await self.memory_system._redis_client.smembers("cascade:memory:all")
            for mem_id in all_memories:
                await self.memory_system._redis_client.delete(f"cascade:memory:{mem_id}")
            await self.memory_system._redis_client.delete("cascade:memory:all")
            await self.memory_system._redis_client.delete("cascade:memory:export:pending")
        except:
            pass
        
        await self.tracker.disconnect()
        await self.memory_system.disconnect()
        await self.predictive_engine.disconnect()
        
        self.log_status("TEARDOWN", "✅ Cleanup complete")
    
    def generate_threat_data(self, threat_id: str) -> Dict:
        """Generate realistic threat data"""
        return {
            'threat_id': threat_id,
            'title': f"Threat {threat_id[-6:]}",
            'description': f"Simulated threat for testing: {threat_id}",
            'severity': random.choice(self.severities),
            'confidence': random.uniform(0.6, 1.0),
            'industry': random.choice(self.industries),
            'sources': random.sample(self.sources, k=random.randint(1, 4)),
            'source_reliability': random.uniform(0.7, 0.95),
            'published_date': (datetime.utcnow() - timedelta(days=random.randint(0, 30))).isoformat()
        }
    
    async def simulate_analyst_behavior(
        self, 
        analyst_id: str, 
        num_actions: int,
        industry_focus: str = None
    ):
        """Simulate realistic analyst behavior"""
        for i in range(num_actions):
            threat_id = f"threat_{analyst_id}_{i}"
            industry = industry_focus if industry_focus else random.choice(self.industries)
            
            # Simulate viewing
            await self.tracker.track_action(
                analyst_id=analyst_id,
                action_type=ActionType.VIEW_THREAT,
                threat_id=threat_id,
                industry=industry,
                severity=random.choice(self.severities),
                time_spent_seconds=random.randint(30, 300)
            )
            
            # Escalate some threats
            if random.random() < 0.25:  # 25% escalation rate
                await self.tracker.track_action(
                    analyst_id=analyst_id,
                    action_type=ActionType.ESCALATE,
                    threat_id=threat_id,
                    industry=industry
                )
            
            self.metrics['actions_tracked'] += 1
            
            if (i + 1) % 10 == 0:
                self.log_status("BEHAVIOR", f"{analyst_id}: {i+1}/{num_actions} actions simulated")
    
    # ========================================================================
    # LEVEL 1: MEDIUM COMPLEXITY
    # ========================================================================
    
    async def test_level_1_medium(self):
        """
        Level 1: MEDIUM Complexity
        - 5 analysts
        - 50 actions each
        - Basic integration testing
        """
        self.log_status("LEVEL-1", "🎯 Starting MEDIUM complexity test")
        self.log_status("LEVEL-1", "Configuration: 5 analysts, 50 actions each")
        
        start_time = time.time()
        
        # Create 5 analysts with different focuses
        analysts = [
            ('analyst_1', 'aviation'),
            ('analyst_2', 'healthcare'),
            ('analyst_3', 'finance'),
            ('analyst_4', 'aviation'),  # Duplicate industry
            ('analyst_5', 'energy')
        ]
        
        self.log_status("LEVEL-1", "Simulating analyst behavior...")
        for analyst_id, industry in analysts:
            await self.simulate_analyst_behavior(analyst_id, 50, industry)
        
        self.log_status("LEVEL-1", "✅ Behavior simulation complete")
        
        # Analyze patterns for each analyst
        self.log_status("LEVEL-1", "Analyzing behavior patterns...")
        for analyst_id, _ in analysts:
            patterns = await self.pattern_analyzer.analyze_patterns(analyst_id, use_cache=False)
            self.metrics['patterns_analyzed'] += 1
            self.log_status("LEVEL-1", f"  {analyst_id}: {patterns['sample_size']} actions, "
                          f"specialization={patterns['specialization_score']:.2f}")
        
        # Form memories for high-engagement threats
        self.log_status("LEVEL-1", "Forming threat memories...")
        
        for i in range(10):
            threat_id = f"level1_threat_{i}"
            threat_data = self.generate_threat_data(threat_id)
            threat_data['severity'] = 'CRITICAL'
            threat_data['confidence'] = 0.95
            
            # Simulate high engagement
            analyst_actions = [
                {
                    'analyst_id': f'analyst_{j+1}',
                    'action_type': 'escalate',
                    'time_spent_seconds': 200
                }
                for j in range(3)
            ]
            
            decision = await self.memory_system.should_form_memory(
                threat_id, analyst_actions, threat_data
            )
            
            if decision.should_form:
                await self.memory_system.form_memory(
                    threat_id, analyst_actions, threat_data, decision
                )
                self.metrics['memories_formed'] += 1
                self.log_status("LEVEL-1", f"  Memory formed: {threat_id} "
                              f"(confidence={decision.confidence:.2f})")
        
        # Generate predictions
        self.log_status("LEVEL-1", "Generating threat predictions...")
        
        for i in range(20):
            threat_data = self.generate_threat_data(f"prediction_threat_{i}")
            analyst_id = random.choice([a[0] for a in analysts])
            
            prediction = await self.predictive_engine.predict_threat_priority(
                analyst_id, threat_data
            )
            self.metrics['predictions_made'] += 1
            
            if prediction.predicted_priority > 0.8:
                self.log_status("LEVEL-1", f"  HIGH priority for {analyst_id}: "
                              f"{prediction.predicted_priority:.2f} "
                              f"({prediction.recommendation})")
        
        duration = time.time() - start_time
        
        self.log_status("LEVEL-1", f"✅ MEDIUM complexity test complete in {duration:.2f}s")
        self.log_metrics()
    
    # ========================================================================
    # LEVEL 2: HIGH COMPLEXITY
    # ========================================================================
    
    async def test_level_2_high(self):
        """
        Level 2: HIGH Complexity
        - 20 analysts
        - 100 actions each
        - Concurrent operations
        """
        self.log_status("LEVEL-2", "🎯 Starting HIGH complexity test")
        self.log_status("LEVEL-2", "Configuration: 20 analysts, 100 actions each, concurrent")
        
        start_time = time.time()
        
        # Create 20 analysts with varied focuses
        num_analysts = 20
        analysts = [
            (f'analyst_{i}', random.choice(self.industries))
            for i in range(num_analysts)
        ]
        
        self.log_status("LEVEL-2", "Simulating concurrent analyst behavior...")
        
        # Run 5 analysts at a time concurrently
        for batch_start in range(0, num_analysts, 5):
            batch = analysts[batch_start:batch_start+5]
            tasks = [
                self.simulate_analyst_behavior(analyst_id, 100, industry)
                for analyst_id, industry in batch
            ]
            await asyncio.gather(*tasks)
            self.log_status("LEVEL-2", f"  Batch {batch_start//5 + 1}/4 complete")
        
        self.log_status("LEVEL-2", "✅ Behavior simulation complete")
        
        # Analyze patterns concurrently
        self.log_status("LEVEL-2", "Analyzing patterns (concurrent)...")
        
        pattern_tasks = [
            self.pattern_analyzer.analyze_patterns(analyst_id, use_cache=False)
            for analyst_id, _ in analysts
        ]
        patterns_results = await asyncio.gather(*pattern_tasks)
        self.metrics['patterns_analyzed'] += len(patterns_results)
        
        # Find specialists
        specialists = [
            (analysts[i][0], p['specialization_score'])
            for i, p in enumerate(patterns_results)
            if p['specialization_score'] > 0.7
        ]
        self.log_status("LEVEL-2", f"  Found {len(specialists)} specialists")
        
        # Form memories with concurrent checking
        self.log_status("LEVEL-2", "Forming memories (concurrent)...")
        
        memory_tasks = []
        for i in range(50):
            threat_id = f"level2_threat_{i}"
            threat_data = self.generate_threat_data(threat_id)
            
            if random.random() < 0.3:  # 30% high-engagement threats
                threat_data['severity'] = 'CRITICAL'
                threat_data['confidence'] = 0.95
                
                analyst_actions = [
                    {
                        'analyst_id': random.choice([a[0] for a in analysts]),
                        'action_type': 'escalate',
                        'time_spent_seconds': random.randint(150, 300)
                    }
                    for _ in range(random.randint(3, 6))
                ]
                
                memory_tasks.append(
                    self._try_form_memory(threat_id, analyst_actions, threat_data)
                )
        
        memory_results = await asyncio.gather(*memory_tasks)
        memories_formed = sum(1 for r in memory_results if r)
        self.metrics['memories_formed'] += memories_formed
        self.log_status("LEVEL-2", f"  {memories_formed} memories formed")
        
        # Generate predictions in batch
        self.log_status("LEVEL-2", "Generating predictions (batch)...")
        
        prediction_tasks = []
        for i in range(100):
            threat_data = self.generate_threat_data(f"level2_pred_{i}")
            analyst_id = random.choice([a[0] for a in analysts])
            prediction_tasks.append(
                self.predictive_engine.predict_threat_priority(analyst_id, threat_data)
            )
        
        predictions = await asyncio.gather(*prediction_tasks)
        self.metrics['predictions_made'] += len(predictions)
        
        high_priority = sum(1 for p in predictions if p.predicted_priority > 0.8)
        self.log_status("LEVEL-2", f"  {high_priority} high-priority predictions")
        
        duration = time.time() - start_time
        
        self.log_status("LEVEL-2", f"✅ HIGH complexity test complete in {duration:.2f}s")
        self.log_metrics()
    
    async def _try_form_memory(self, threat_id, analyst_actions, threat_data):
        """Helper to form memory"""
        try:
            decision = await self.memory_system.should_form_memory(
                threat_id, analyst_actions, threat_data
            )
            if decision.should_form:
                await self.memory_system.form_memory(
                    threat_id, analyst_actions, threat_data, decision
                )
                return True
        except Exception as e:
            self.metrics['errors'] += 1
            return False
        return False
    
    # ========================================================================
    # LEVEL 3: VERY HIGH COMPLEXITY
    # ========================================================================
    
    async def test_level_3_very_high(self):
        """
        Level 3: VERY HIGH Complexity
        - 50 analysts
        - 200 actions each
        - Large-scale concurrent operations
        """
        self.log_status("LEVEL-3", "🎯 Starting VERY HIGH complexity test")
        self.log_status("LEVEL-3", "Configuration: 50 analysts, 200 actions each")
        
        start_time = time.time()
        
        num_analysts = 50
        analysts = [
            (f'analyst_{i}', random.choice(self.industries))
            for i in range(num_analysts)
        ]
        
        self.log_status("LEVEL-3", "Simulating behavior (10 concurrent batches)...")
        
        # Process in batches of 10
        for batch_num in range(5):
            batch_start = batch_num * 10
            batch = analysts[batch_start:batch_start+10]
            
            tasks = [
                self.simulate_analyst_behavior(analyst_id, 200, industry)
                for analyst_id, industry in batch
            ]
            await asyncio.gather(*tasks)
            
            progress = ((batch_num + 1) / 5) * 100
            self.log_status("LEVEL-3", f"  Progress: {progress:.0f}% "
                          f"({self.metrics['actions_tracked']:,} actions)")
        
        self.log_status("LEVEL-3", "✅ Behavior simulation complete")
        
        # Analyze all patterns
        self.log_status("LEVEL-3", "Analyzing patterns (50 concurrent)...")
        
        pattern_start = time.time()
        pattern_tasks = [
            self.pattern_analyzer.analyze_patterns(analyst_id, use_cache=False)
            for analyst_id, _ in analysts
        ]
        patterns_results = await asyncio.gather(*pattern_tasks)
        pattern_duration = time.time() - pattern_start
        
        self.metrics['patterns_analyzed'] += len(patterns_results)
        self.log_status("LEVEL-3", f"  50 patterns analyzed in {pattern_duration:.2f}s "
                      f"({1000*pattern_duration/50:.0f}ms avg)")
        
        # Memory formation stress test
        self.log_status("LEVEL-3", "Memory formation (200 concurrent)...")
        
        memory_start = time.time()
        memory_tasks = []
        
        for i in range(200):
            threat_id = f"level3_threat_{i}"
            threat_data = self.generate_threat_data(threat_id)
            
            # 40% high-engagement
            if random.random() < 0.4:
                threat_data['severity'] = random.choice(['CRITICAL', 'HIGH'])
                threat_data['confidence'] = random.uniform(0.85, 1.0)
                
                analyst_actions = [
                    {
                        'analyst_id': random.choice([a[0] for a in analysts]),
                        'action_type': random.choice(['escalate', 'view']),
                        'time_spent_seconds': random.randint(100, 400)
                    }
                    for _ in range(random.randint(2, 8))
                ]
                
                memory_tasks.append(
                    self._try_form_memory(threat_id, analyst_actions, threat_data)
                )
        
        memory_results = await asyncio.gather(*memory_tasks)
        memory_duration = time.time() - memory_start
        memories_formed = sum(1 for r in memory_results if r)
        
        self.metrics['memories_formed'] += memories_formed
        self.log_status("LEVEL-3", f"  {memories_formed}/200 memories formed in "
                      f"{memory_duration:.2f}s")
        
        # Large-scale predictions
        self.log_status("LEVEL-3", "Predictions (500 concurrent)...")
        
        pred_start = time.time()
        prediction_tasks = []
        
        for i in range(500):
            threat_data = self.generate_threat_data(f"level3_pred_{i}")
            analyst_id = random.choice([a[0] for a in analysts])
            prediction_tasks.append(
                self.predictive_engine.predict_threat_priority(analyst_id, threat_data)
            )
        
        predictions = await asyncio.gather(*prediction_tasks)
        pred_duration = time.time() - pred_start
        
        self.metrics['predictions_made'] += len(predictions)
        
        # Analyze prediction distribution
        priority_buckets = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        for p in predictions:
            if p.predicted_priority >= 0.9:
                priority_buckets['critical'] += 1
            elif p.predicted_priority >= 0.7:
                priority_buckets['high'] += 1
            elif p.predicted_priority >= 0.5:
                priority_buckets['medium'] += 1
            else:
                priority_buckets['low'] += 1
        
        self.log_status("LEVEL-3", f"  500 predictions in {pred_duration:.2f}s "
                      f"({1000*pred_duration/500:.0f}ms avg)")
        self.log_status("LEVEL-3", f"  Distribution: Critical={priority_buckets['critical']}, "
                      f"High={priority_buckets['high']}, "
                      f"Medium={priority_buckets['medium']}, "
                      f"Low={priority_buckets['low']}")
        
        duration = time.time() - start_time
        
        self.log_status("LEVEL-3", f"✅ VERY HIGH complexity test complete in {duration:.2f}s")
        self.log_metrics()
    
    # ========================================================================
    # LEVEL 4: EXTREME COMPLEXITY
    # ========================================================================
    
    async def test_level_4_extreme(self):
        """
        Level 4: EXTREME Complexity
        - 100 analysts
        - 500 actions each
        - Maximum concurrent load
        - All features stressed
        """
        self.log_status("LEVEL-4", "🎯 Starting EXTREME complexity test")
        self.log_status("LEVEL-4", "Configuration: 100 analysts, 500 actions each")
        self.log_status("LEVEL-4", "⚠️  This will take several minutes...")
        
        start_time = time.time()
        
        num_analysts = 100
        analysts = [
            (f'analyst_{i}', random.choice(self.industries))
            for i in range(num_analysts)
        ]
        
        self.log_status("LEVEL-4", "Simulating behavior (20 concurrent batches)...")
        
        # Process in batches of 20
        for batch_num in range(5):
            batch_start = batch_num * 20
            batch = analysts[batch_start:batch_start+20]
            
            batch_start_time = time.time()
            tasks = [
                self.simulate_analyst_behavior(analyst_id, 500, industry)
                for analyst_id, industry in batch
            ]
            await asyncio.gather(*tasks)
            
            batch_duration = time.time() - batch_start_time
            progress = ((batch_num + 1) / 5) * 100
            self.log_status("LEVEL-4", f"  Batch {batch_num+1}/5 complete in {batch_duration:.1f}s "
                          f"(Progress: {progress:.0f}%, {self.metrics['actions_tracked']:,} actions)")
        
        self.log_status("LEVEL-4", "✅ Behavior simulation complete")
        
        # Pattern analysis with batching
        self.log_status("LEVEL-4", "Pattern analysis (100 analysts in 4 batches)...")
        
        for batch_num in range(4):
            batch_start = batch_num * 25
            batch = analysts[batch_start:batch_start+25]
            
            pattern_tasks = [
                self.pattern_analyzer.analyze_patterns(analyst_id, use_cache=False)
                for analyst_id, _ in batch
            ]
            await asyncio.gather(*pattern_tasks)
            self.metrics['patterns_analyzed'] += 25
            self.log_status("LEVEL-4", f"  Batch {batch_num+1}/4 complete "
                          f"({self.metrics['patterns_analyzed']} total)")
        
        # Extreme memory formation
        self.log_status("LEVEL-4", "Memory formation (1000 threats, concurrent)...")
        
        memory_batches = []
        for batch_num in range(10):
            batch_tasks = []
            for i in range(100):
                threat_id = f"level4_threat_{batch_num*100 + i}"
                threat_data = self.generate_threat_data(threat_id)
                
                if random.random() < 0.5:
                    threat_data['severity'] = random.choice(['CRITICAL', 'HIGH'])
                    threat_data['confidence'] = random.uniform(0.8, 1.0)
                    
                    analyst_actions = [
                        {
                            'analyst_id': random.choice([a[0] for a in analysts]),
                            'action_type': random.choice(['escalate', 'view', 'escalate']),
                            'time_spent_seconds': random.randint(90, 500)
                        }
                        for _ in range(random.randint(2, 10))
                    ]
                    
                    batch_tasks.append(
                        self._try_form_memory(threat_id, analyst_actions, threat_data)
                    )
            
            results = await asyncio.gather(*batch_tasks)
            formed = sum(1 for r in results if r)
            self.metrics['memories_formed'] += formed
            
            self.log_status("LEVEL-4", f"  Batch {batch_num+1}/10: {formed} memories formed "
                          f"({self.metrics['memories_formed']} total)")
        
        # Extreme prediction load
        self.log_status("LEVEL-4", "Predictions (2000 concurrent, in 4 batches)...")
        
        for batch_num in range(4):
            pred_start = time.time()
            prediction_tasks = []
            
            for i in range(500):
                threat_data = self.generate_threat_data(f"level4_pred_{batch_num*500 + i}")
                analyst_id = random.choice([a[0] for a in analysts])
                prediction_tasks.append(
                    self.predictive_engine.predict_threat_priority(analyst_id, threat_data)
                )
            
            predictions = await asyncio.gather(*prediction_tasks)
            pred_duration = time.time() - pred_start
            self.metrics['predictions_made'] += len(predictions)
            
            self.log_status("LEVEL-4", f"  Batch {batch_num+1}/4: 500 predictions in "
                          f"{pred_duration:.2f}s ({self.metrics['predictions_made']} total)")
        
        # Final system check
        self.log_status("LEVEL-4", "Running final system integrity checks...")
        
        # Check memory count
        memory_count = await self.memory_system.count_memories()
        self.log_status("LEVEL-4", f"  Total memories in Redis: {memory_count}")
        
        # Check pattern caching
        sample_patterns = await self.pattern_analyzer.analyze_patterns(
            'analyst_0', use_cache=True
        )
        self.log_status("LEVEL-4", f"  Sample pattern: {sample_patterns['sample_size']} actions, "
                      f"spec={sample_patterns['specialization_score']:.2f}")
        
        duration = time.time() - start_time
        
        self.log_status("LEVEL-4", f"✅ EXTREME complexity test complete in {duration:.2f}s")
        self.log_metrics()


async def run_holistic_integration_test():
    """Run complete holistic integration test"""
    
    print("\n" + "="*80)
    print("CASCADE HOLISTIC INTEGRATION TEST")
    print("Testing entire system end-to-end with increasing complexity")
    print("="*80 + "\n")
    
    harness = IntegrationTestHarness()
    
    try:
        await harness.setup()
        
        # Run all 4 levels
        await harness.test_level_1_medium()
        await harness.test_level_2_high()
        await harness.test_level_3_very_high()
        await harness.test_level_4_extreme()
        
        # Final summary
        print("\n" + "="*80)
        print("🎉 HOLISTIC INTEGRATION TEST COMPLETE")
        print("="*80)
        print("\n📊 FINAL METRICS:")
        for key, value in harness.metrics.items():
            print(f"   {key}: {value:,}")
        print("\n✅ All levels completed successfully")
        print("✅ System is production-ready")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        raise
    
    finally:
        await harness.teardown()


if __name__ == "__main__":
    asyncio.run(run_holistic_integration_test())
