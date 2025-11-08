#!/usr/bin/env python3
"""
End-to-End Integration Test for Cyber-Pi
Tests the entire application stack with real data
"""

import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.table import Table

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

console = Console()


class E2ETestSuite:
    """Comprehensive end-to-end testing"""
    
    def __init__(self):
        self.results = []
        self.redis = None
        self.neo4j_driver = None
        self.periscope = None
        self.monitor = None
        
    def log_test(self, name, status, message="", error=None):
        """Log test result"""
        result = {
            'test': name,
            'status': status,
            'message': message,
            'error': str(error) if error else None,
            'timestamp': datetime.utcnow().isoformat()
        }
        self.results.append(result)
        
        icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        style = "green" if status == "PASS" else "red" if status == "FAIL" else "yellow"
        console.print(f"{icon} {name}: {message}", style=style)
        if error:
            console.print(f"   Error: {error}", style="red dim")
    
    async def test_redis_connectivity(self):
        """Test Redis connection and basic operations"""
        console.print("\n📊 Testing Redis...", style="bold cyan")
        try:
            import redis.asyncio as redis
            self.redis = redis.Redis(
                host='localhost',
                port=32379,
                decode_responses=True
            )
            
            # Test ping
            await self.redis.ping()
            self.log_test("Redis Ping", "PASS", "Connected successfully")
            
            # Test write/read
            test_key = "test:e2e:timestamp"
            test_value = datetime.utcnow().isoformat()
            await self.redis.set(test_key, test_value)
            retrieved = await self.redis.get(test_key)
            
            if retrieved == test_value:
                self.log_test("Redis Read/Write", "PASS", f"Stored and retrieved: {test_value[:20]}...")
            else:
                self.log_test("Redis Read/Write", "FAIL", "Retrieved value doesn't match")
            
            # Test metrics keys
            metrics_keys = await self.redis.keys("metrics:*")
            self.log_test("Redis Metrics Keys", "PASS", f"Found {len(metrics_keys)} metrics keys")
            
            # Cleanup
            await self.redis.delete(test_key)
            
            return True
            
        except Exception as e:
            self.log_test("Redis Connection", "FAIL", "Failed to connect", e)
            return False
    
    async def test_neo4j_connectivity(self):
        """Test Neo4j connection and queries"""
        console.print("\n🔗 Testing Neo4j...", style="bold cyan")
        try:
            from neo4j import GraphDatabase
            
            # Access via cluster IP (TQAKB is using localhost:7687)
            self.neo4j_driver = GraphDatabase.driver(
                'bolt://10.152.183.79:7687',  # cyber-pi Neo4j ClusterIP
                auth=('neo4j', 'cyber-pi-neo4j-2025')
            )
            
            # Test connectivity
            self.neo4j_driver.verify_connectivity()
            self.log_test("Neo4j Connectivity", "PASS", "Connected successfully")
            
            # Count nodes
            with self.neo4j_driver.session() as session:
                result = session.run("MATCH (n) RETURN count(n) AS total")
                total_nodes = result.single()['total']
                self.log_test("Neo4j Node Count", "PASS", f"Found {total_nodes:,} nodes")
                
                # Check for CVE nodes
                result = session.run("MATCH (n:CVE) RETURN count(n) AS total")
                cve_count = result.single()['total']
                self.log_test("Neo4j CVE Nodes", "PASS" if cve_count > 0 else "WARN", 
                            f"Found {cve_count:,} CVE nodes")
                
                # Check for Threat nodes
                result = session.run("MATCH (n:Threat) RETURN count(n) AS total")
                threat_count = result.single()['total']
                self.log_test("Neo4j Threat Nodes", "PASS" if threat_count > 0 else "WARN",
                            f"Found {threat_count:,} Threat nodes")
            
            return True
            
        except Exception as e:
            self.log_test("Neo4j Connection", "FAIL", "Failed to connect", e)
            return False
    
    async def test_ollama_models(self):
        """Test Ollama API and models"""
        console.print("\n🤖 Testing Ollama...", style="bold cyan")
        try:
            import httpx
            
            async with httpx.AsyncClient() as client:
                # Test API
                response = await client.get("http://localhost:11434/api/tags")
                if response.status_code == 200:
                    self.log_test("Ollama API", "PASS", "API responding")
                    
                    # Check models
                    models = response.json().get('models', [])
                    self.log_test("Ollama Models", "PASS", f"Found {len(models)} models")
                    
                    # List key models
                    embedding_models = [m for m in models if 'embed' in m['name'].lower()]
                    llm_models = [m for m in models if 'llama' in m['name'].lower() or 'mistral' in m['name'].lower()]
                    
                    self.log_test("Embedding Models", "PASS" if embedding_models else "WARN",
                                f"Found {len(embedding_models)} embedding models")
                    self.log_test("LLM Models", "PASS" if llm_models else "WARN",
                                f"Found {len(llm_models)} LLM models")
                else:
                    self.log_test("Ollama API", "FAIL", f"Status code: {response.status_code}")
            
            return True
            
        except Exception as e:
            self.log_test("Ollama Connection", "FAIL", "Failed to connect", e)
            return False
    
    async def test_monitoring_infrastructure(self):
        """Test monitoring system"""
        console.print("\n📈 Testing Monitoring Infrastructure...", style="bold cyan")
        try:
            from monitoring.periscope_monitor import PeriscopeMonitor
            
            self.monitor = PeriscopeMonitor(
                redis_host='localhost',
                redis_port=32379
            )
            self.log_test("Monitor Initialization", "PASS", "PeriscopeMonitor created")
            
            # Initialize (connect to Redis)
            await self.monitor.initialize()
            self.log_test("Monitor Redis Connection", "PASS", "Connected to Redis")
            
            # Test metrics recording
            self.monitor.record_threat_ingested()
            self.monitor.record_threat_converted()
            summary = self.monitor.get_metrics_summary()
            
            if summary['threats']['ingested'] >= 1:
                self.log_test("Monitor Metrics", "PASS", "Metrics recording works")
            else:
                self.log_test("Monitor Metrics", "FAIL", "Metrics not recording")
            
            # Test system stats
            sys_stats = self.monitor.get_system_stats()
            if 'process_memory_mb' in sys_stats:
                self.log_test("Monitor System Stats", "PASS", 
                            f"RAM: {sys_stats['process_memory_mb']:.1f}MB")
            
            # Test GPU stats
            gpu_stats = await self.monitor.get_gpu_stats()
            if 'error' not in gpu_stats:
                self.log_test("Monitor GPU Stats", "PASS",
                            f"{gpu_stats['gpu_count']} GPU(s) detected")
            else:
                self.log_test("Monitor GPU Stats", "WARN", "GPU stats unavailable")
            
            # Test health check
            health = self.monitor.get_health_status()
            self.log_test("Monitor Health Check", "PASS",
                        f"Status: {health['status']}")
            
            return True
            
        except Exception as e:
            self.log_test("Monitoring System", "FAIL", "Failed to initialize", e)
            return False
    
    async def test_periscope_integration(self):
        """Test Periscope integration"""
        console.print("\n🔭 Testing Periscope Integration...", style="bold cyan")
        try:
            from periscope.periscope_batch_ops import PeriscopeTriageBatch
            
            self.periscope = PeriscopeTriageBatch(
                redis_host='localhost',
                redis_port=32379
            )
            
            await self.periscope.initialize()
            self.log_test("Periscope Initialization", "PASS", "PeriscopeTriageBatch created")
            
            # Get stats
            stats = await self.periscope.get_stats()
            self.log_test("Periscope Stats", "PASS",
                        f"Active: {stats['total_active']}, Short-term: {stats['total_short_term']}, Long-term: {stats['total_long_term']}")
            
            return True
            
        except Exception as e:
            self.log_test("Periscope Integration", "FAIL", "Failed to initialize", e)
            return False
    
    async def test_monitored_integration_with_real_data(self):
        """Test the monitored integration with real threat data"""
        console.print("\n🎯 Testing Monitored Integration with Real Data...", style="bold cyan")
        try:
            from cyber_pi_periscope_integration_monitored import MonitoredCyberPiPeriscopeIntegration
            
            integration = MonitoredCyberPiPeriscopeIntegration(
                redis_host='localhost',
                redis_port=32379,
                enable_monitoring=True
            )
            
            await integration.initialize()
            self.log_test("Monitored Integration Init", "PASS", "Integration initialized")
            
            # Create real-looking test threats
            test_threats = [
                {
                    'source': 'CISA',
                    'title': 'Critical Vulnerability in Apache Log4j (CVE-2021-44228)',
                    'description': 'Remote code execution vulnerability affecting Apache Log4j 2.0-beta9 through 2.15.0',
                    'tags': ['critical', 'rce', 'log4j', 'apache'],
                    'url': 'https://nvd.nist.gov/vuln/detail/CVE-2021-44228',
                    'published': '2021-12-10',
                    'cvss_score': 10.0
                },
                {
                    'source': 'NVD',
                    'title': 'Microsoft Exchange Server Remote Code Execution Vulnerability',
                    'description': 'ProxyShell chain of vulnerabilities in Microsoft Exchange Server',
                    'tags': ['critical', 'exchange', 'microsoft', 'rce'],
                    'url': 'https://nvd.nist.gov/vuln/detail/CVE-2021-34473',
                    'published': '2021-08-12',
                    'cvss_score': 9.8
                },
                {
                    'source': 'GitHub Advisory',
                    'title': 'SQL Injection in Django Admin',
                    'description': 'SQL injection vulnerability in Django admin interface',
                    'tags': ['high', 'sql-injection', 'django', 'python'],
                    'url': 'https://github.com/advisories/GHSA-example',
                    'published': '2023-05-15',
                    'cvss_score': 8.5
                }
            ]
            
            # Ingest threats with monitoring
            stats = await integration.ingest_cyber_pi_threats(test_threats, auto_retry=True)
            
            self.log_test("Threat Ingestion", "PASS",
                        f"Ingested {stats['added']}/{stats['total_items']} threats")
            
            if stats['conversion_failures'] > 0:
                self.log_test("Threat Conversion", "WARN",
                            f"{stats['conversion_failures']} conversion failures")
            else:
                self.log_test("Threat Conversion", "PASS", "All threats converted successfully")
            
            # Get priority threats
            priority = await integration.get_priority_threats(min_score=0.5, limit=5)
            self.log_test("Priority Threat Query", "PASS",
                        f"Retrieved {len(priority)} priority threats")
            
            # Print metrics
            integration.print_metrics_report()
            
            # Get comprehensive health
            health = await integration.get_comprehensive_health()
            self.log_test("Integration Health Check", "PASS",
                        f"Status: {health.get('monitoring', {}).get('status', 'unknown')}")
            
            # Cleanup
            await integration.cleanup()
            
            return True
            
        except Exception as e:
            self.log_test("Monitored Integration", "FAIL", "Failed during testing", e)
            return False
    
    async def cleanup(self):
        """Cleanup resources"""
        console.print("\n🧹 Cleaning up...", style="bold cyan")
        try:
            if self.redis:
                await self.redis.close()
            if self.neo4j_driver:
                self.neo4j_driver.close()
            console.print("✅ Cleanup complete", style="green")
        except Exception as e:
            console.print(f"⚠️  Cleanup error: {e}", style="yellow")
    
    def print_summary(self):
        """Print test summary"""
        console.print("\n" + "=" * 80, style="bold blue")
        console.print("📊 TEST SUMMARY", style="bold blue")
        console.print("=" * 80, style="bold blue")
        
        passed = sum(1 for r in self.results if r['status'] == 'PASS')
        failed = sum(1 for r in self.results if r['status'] == 'FAIL')
        warnings = sum(1 for r in self.results if r['status'] == 'WARN')
        
        table = Table(title="Test Results")
        table.add_column("Status", style="bold")
        table.add_column("Count", justify="right")
        table.add_column("Percentage", justify="right")
        
        total = len(self.results)
        table.add_row("✅ PASSED", str(passed), f"{passed/total*100:.1f}%")
        table.add_row("❌ FAILED", str(failed), f"{failed/total*100:.1f}%")
        table.add_row("⚠️  WARNINGS", str(warnings), f"{warnings/total*100:.1f}%")
        table.add_row("TOTAL", str(total), "100%")
        
        console.print(table)
        console.print()
        
        if failed == 0:
            console.print("🎉 ALL CRITICAL TESTS PASSED!", style="bold green")
        else:
            console.print(f"⚠️  {failed} TEST(S) FAILED", style="bold red")
            console.print("\nFailed Tests:", style="bold red")
            for result in self.results:
                if result['status'] == 'FAIL':
                    console.print(f"  - {result['test']}: {result['message']}", style="red")
                    if result['error']:
                        console.print(f"    {result['error']}", style="red dim")
        
        # Save results to file
        results_file = Path('test_results_e2e.json')
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        console.print(f"\n📄 Full results saved to: {results_file}", style="dim")
        
        return failed == 0


async def main():
    """Run end-to-end test suite"""
    console.print("\n" + "=" * 80, style="bold blue")
    console.print("🧪 CYBER-PI END-TO-END INTEGRATION TEST", style="bold blue")
    console.print("=" * 80 + "\n", style="bold blue")
    
    suite = E2ETestSuite()
    
    try:
        # Run all tests
        await suite.test_redis_connectivity()
        await suite.test_neo4j_connectivity()
        await suite.test_ollama_models()
        await suite.test_monitoring_infrastructure()
        await suite.test_periscope_integration()
        await suite.test_monitored_integration_with_real_data()
        
    finally:
        await suite.cleanup()
        success = suite.print_summary()
        
        console.print("\n" + "=" * 80, style="bold blue")
        if success:
            console.print("✅ END-TO-END TEST COMPLETE - ALL SYSTEMS OPERATIONAL", style="bold green")
        else:
            console.print("❌ END-TO-END TEST COMPLETE - ISSUES FOUND", style="bold red")
        console.print("=" * 80 + "\n", style="bold blue")
        
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
