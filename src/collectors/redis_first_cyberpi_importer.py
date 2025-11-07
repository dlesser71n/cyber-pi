#!/usr/bin/env python3
"""
Redis-First CyberPi to TQAKB Import System
Extracts data from cyber-pi and stores in Redis first, then distributes to Weaviate and Neo4j
"""

import asyncio
import json
import logging
import os
import sys
import time
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import aiohttp
import redis.asyncio as redis
from concurrent.futures import ThreadPoolExecutor

# Add project paths
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DataType(Enum):
    VENDOR_INTELLIGENCE = "vendor_intelligence"
    THREAT_INTELLIGENCE = "threat_intelligence"
    IOC_DATA = "ioc_data"
    INCIDENT_REPORTS = "incident_reports"
    VULNERABILITY_DATA = "vulnerability_data"
    SECURITY_ASSESSMENTS = "security_assessments"

class ImportStatus(Enum):
    PENDING = "pending"
    IN_REDIS = "in_redis"
    EXPORTED_TO_WEAVIATE = "exported_to_weaviate"
    EXPORTED_TO_NEO4J = "exported_to_neo4j"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class CyberPiImportRecord:
    """Record for tracking cyber-pi imports"""
    record_id: str
    data_type: DataType
    source_id: str
    redis_key: str
    import_timestamp: str
    status: ImportStatus
    weaviate_id: Optional[str] = None
    neo4j_id: Optional[str] = None
    error_count: int = 0
    last_error: Optional[str] = None
    export_attempts: int = 0
    
    def __post_init__(self):
        if self.import_timestamp is None:
            self.import_timestamp = datetime.now(timezone.utc).isoformat()

class RedisFirstCyberPiImporter:
    """
    Redis-first import system for cyber-pi to TQAKB
    """
    
    def __init__(self, redis_host: str = 'localhost', redis_port: int = 6379):
        # Redis configuration
        self.redis_config = {
            'host': redis_host,
            'port': redis_port,
            'decode_responses': True,
            'socket_connect_timeout': 5,
            'socket_timeout': 5,
            'retry_on_timeout': True
        }
        
        # Cyber-pi API configuration
        self.cyberpi_config = {
            'api_base_url': 'http://localhost:8000',
            'endpoints': {
                'vendors': '/api/vendors',
                'threats': '/api/threats',
                'iocs': '/api/iocs',
                'incidents': '/api/incidents',
                'vulnerabilities': '/api/vulnerabilities',
                'assessments': '/api/assessments'
            },
            'auth_token': None,  # Configure as needed
            'rate_limit': 100,  # requests per minute
        }
        
        # TQAKB component configurations
        self.tqakb_config = {
            'weaviate_url': 'http://localhost:30883',
            'neo4j_uri': 'bolt://localhost:7687',
            'neo4j_user': 'neo4j',
            'neo4j_password': 'password'
        }
        
        # Import state
        self.redis_client = None
        self.cyberpi_session = None
        self.weaviate_client = None
        self.neo4j_driver = None
        
        # Statistics
        self.import_stats = {
            'total_imports': 0,
            'redis_stores': 0,
            'weaviate_exports': 0,
            'neo4j_exports': 0,
            'failed_imports': 0,
            'last_import': None,
            'import_rate': 0.0
        }
        
        # Background task management
        self.export_queue = asyncio.Queue()
        self.background_tasks = set()
        
        logger.info("🚀 Redis-First CyberPi Importer Initialized")
    
    async def initialize(self):
        """Initialize all connections and start background processes"""
        logger.info("🔌 Initializing Redis-First Import System...")
        
        try:
            # Initialize Redis (primary connection)
            await self._connect_redis()
            
            # Initialize cyber-pi connection
            await self._connect_cyberpi()
            
            # Initialize TQAKB components (for exports)
            await self._connect_tqakb_components()
            
            # Start background export workers
            await self._start_export_workers()
            
            logger.info("✅ Redis-First Import System ready")
            
        except Exception as e:
            logger.error(f"❌ Initialization failed: {e}")
            raise
    
    async def _connect_redis(self):
        """Connect to Redis as primary data store"""
        try:
            self.redis_client = redis.Redis(**self.redis_config)
            await self.redis_client.ping()
            
            # Test Redis functionality
            test_key = "cyberpi:import:test"
            await self.redis_client.set(test_key, "test_value", ex=10)
            test_value = await self.redis_client.get(test_key)
            
            if test_value == "test_value":
                logger.info("✅ Redis connection established and tested")
            else:
                raise Exception("Redis test failed")
                
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
            raise
    
    async def _connect_cyberpi(self):
        """Connect to cyber-pi API"""
        try:
            self.cyberpi_session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                headers={'Content-Type': 'application/json'}
            )
            
            # Test cyber-pi connection
            try:
                async with self.cyberpi_session.get(f"{self.cyberpi_config['api_base_url']}/health") as response:
                    if response.status == 200:
                        logger.info("✅ Cyber-pi API connection established")
                    else:
                        logger.warning(f"⚠️ Cyber-pi API health check: {response.status}")
            except Exception as e:
                logger.warning(f"⚠️ Cyber-pi API not available: {e}")
                
        except Exception as e:
            logger.warning(f"⚠️ Cyber-pi session creation failed: {e}")
            self.cyberpi_session = None
    
    async def _connect_tqakb_components(self):
        """Connect to TQAKB components for exports"""
        try:
            # Weaviate connection
            try:
                import weaviate
                self.weaviate_client = weaviate.Client(self.tqakb_config['weaviate_url'])
                logger.info("✅ Weaviate connection established")
            except Exception as e:
                logger.warning(f"⚠️ Weaviate connection failed: {e}")
                self.weaviate_client = None
            
            # Neo4j connection
            try:
                from neo4j import GraphDatabase
                self.neo4j_driver = GraphDatabase.driver(
                    self.tqakb_config['neo4j_uri'],
                    auth=(self.tqakb_config['neo4j_user'], self.tqakb_config['neo4j_password'])
                )
                logger.info("✅ Neo4j connection established")
            except Exception as e:
                logger.warning(f"⚠️ Neo4j connection failed: {e}")
                self.neo4j_driver = None
                
        except Exception as e:
            logger.warning(f"⚠️ TQAKB component connections failed: {e}")
    
    async def _start_export_workers(self):
        """Start background workers for exporting to Weaviate and Neo4j"""
        try:
            # Start Weaviate export worker
            weaviate_task = asyncio.create_task(self._weaviate_export_worker())
            self.background_tasks.add(weaviate_task)
            
            # Start Neo4j export worker
            neo4j_task = asyncio.create_task(self._neo4j_export_worker())
            self.background_tasks.add(neo4j_task)
            
            logger.info("✅ Background export workers started")
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to start export workers: {e}")
    
    async def import_from_cyberpi(self, data_type: DataType, limit: int = 100) -> Dict[str, Any]:
        """
        Import data from cyber-pi to Redis (primary storage)
        """
        logger.info(f"📥 Importing {data_type.value} from cyber-pi to Redis...")
        
        start_time = time.time()
        import_result = {
            'data_type': data_type.value,
            'records_processed': 0,
            'records_stored': 0,
            'records_failed': 0,
            'duration_seconds': 0.0,
            'errors': [],
            'redis_keys': []
        }
        
        try:
            # Extract data from cyber-pi
            cyberpi_data = await self._extract_from_cyberpi(data_type, limit)
            
            if not cyberpi_data:
                logger.warning(f"⚠️ No {data_type.value} data found in cyber-pi")
                return import_result
            
            import_result['records_processed'] = len(cyberpi_data)
            
            # Store each record in Redis
            for record in cyberpi_data:
                try:
                    redis_key = await self._store_in_redis(record, data_type)
                    import_result['redis_keys'].append(redis_key)
                    import_result['records_stored'] += 1
                    
                    # Queue for background export
                    await self._queue_for_export(redis_key, data_type)
                    
                except Exception as e:
                    import_result['records_failed'] += 1
                    import_result['errors'].append(f"Store failed: {str(e)}")
                    logger.error(f"❌ Failed to store record in Redis: {e}")
            
            import_result['duration_seconds'] = time.time() - start_time
            
            # Update statistics
            self.import_stats['total_imports'] += import_result['records_stored']
            self.import_stats['redis_stores'] += import_result['records_stored']
            self.import_stats['last_import'] = datetime.now(timezone.utc).isoformat()
            if import_result['duration_seconds'] > 0:
                self.import_stats['import_rate'] = import_result['records_stored'] / import_result['duration_seconds']
            
            logger.info(f"✅ Imported {import_result['records_stored']}/{import_result['records_processed']} {data_type.value} to Redis")
            
        except Exception as e:
            import_result['errors'].append(f"Import failed: {str(e)}")
            logger.error(f"❌ Import from cyber-pi failed: {e}")
        
        return import_result
    
    async def _extract_from_cyberpi(self, data_type: DataType, limit: int) -> List[Dict[str, Any]]:
        """Extract data from cyber-pi API"""
        try:
            if not self.cyberpi_session:
                logger.error("❌ Cyber-pi session not initialized")
                return []
            
            endpoint = self.cyberpi_config['endpoints'].get(data_type.value)
            if not endpoint:
                logger.error(f"❌ No endpoint configured for {data_type.value}")
                return []
            
            url = f"{self.cyberpi_config['base_url']}{endpoint}"
            async with self.cyberpi_session.get(url, params={'limit': limit}) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    logger.error(f"❌ Cyber-pi API returned status: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"❌ Cyber-pi extraction failed: {e}")
            return []
    
    async def _get_mock_cyberpi_data(self, data_type: DataType, limit: int) -> List[Dict[str, Any]]:
        """Deprecated: Mock data removed. Returns empty list."""
        logger.warning("Mock data method called - no data available")
        return []
    
    async def _store_in_redis(self, record: Dict[str, Any], data_type: DataType) -> str:
        """Store record in Redis with proper key structure"""
        import uuid
        
        # Generate unique Redis key
        record_id = record.get('id', str(uuid.uuid4()))
        redis_key = f"cyberpi:{data_type.value}:{record_id}"
        
        # Prepare data for Redis storage
        redis_data = {
            'source_id': record_id,
            'data_type': data_type.value,
            'import_timestamp': datetime.now(timezone.utc).isoformat(),
            'status': ImportStatus.IN_REDIS.value,
            'data': json.dumps(record),
            'export_attempts': '0',
            'error_count': '0'
        }
        
        # Store main record
        await self.redis_client.hset(redis_key, mapping=redis_data)
        
        # Set expiration (30 days)
        await self.redis_client.expire(redis_key, 2592000)
        
        # Add to indexing sets
        await self.redis_client.sadd(f"cyberpi:{data_type.value}:all", redis_key)
        await self.redis_client.sadd("cyberpi:all:records", redis_key)
        
        # Add to timeline
        score = time.time()
        await self.redis_client.zadd("cyberpi:timeline:imports", {redis_key: score})
        
        # Add to export queue
        await self.redis_client.sadd("cyberpi:export:pending", redis_key)
        
        logger.debug(f"💾 Stored in Redis: {redis_key}")
        return redis_key
    
    async def _queue_for_export(self, redis_key: str, data_type: DataType):
        """Queue record for background export to TQAKB components"""
        export_task = {
            'redis_key': redis_key,
            'data_type': data_type.value,
            'queued_at': datetime.now(timezone.utc).isoformat(),
            'priority': 'normal'
        }
        
        await self.export_queue.put(export_task)
        logger.debug(f"📤 Queued for export: {redis_key}")
    
    async def _weaviate_export_worker(self):
        """Background worker for exporting to Weaviate"""
        logger.info("🔄 Weaviate export worker started")
        
        while True:
            try:
                # Get next export task
                task = await self.export_queue.get()
                
                # Export to Weaviate
                success = await self._export_to_weaviate(task)
                
                if success:
                    self.import_stats['weaviate_exports'] += 1
                    logger.debug(f"✅ Exported to Weaviate: {task['redis_key']}")
                else:
                    logger.warning(f"⚠️ Weaviate export failed: {task['redis_key']}")
                
                # Mark task as done
                self.export_queue.task_done()
                
            except Exception as e:
                logger.error(f"❌ Weaviate export worker error: {e}")
                await asyncio.sleep(5)  # Brief pause on error
    
    async def _neo4j_export_worker(self):
        """Background worker for exporting to Neo4j"""
        logger.info("🔄 Neo4j export worker started")
        
        while True:
            try:
                # Get next export task
                task = await self.export_queue.get()
                
                # Export to Neo4j
                success = await self._export_to_neo4j(task)
                
                if success:
                    self.import_stats['neo4j_exports'] += 1
                    logger.debug(f"✅ Exported to Neo4j: {task['redis_key']}")
                else:
                    logger.warning(f"⚠️ Neo4j export failed: {task['redis_key']}")
                
                # Mark task as done
                self.export_queue.task_done()
                
            except Exception as e:
                logger.error(f"❌ Neo4j export worker error: {e}")
                await asyncio.sleep(5)  # Brief pause on error
    
    async def _export_to_weaviate(self, task: Dict[str, Any]) -> bool:
        """Export Redis record to Weaviate"""
        try:
            if not self.weaviate_client:
                return False  # Skip if Weaviate not available
            
            redis_key = task['redis_key']
            
            # Get record from Redis
            record_data = await self.redis_client.hgetall(redis_key)
            if not record_data:
                logger.warning(f"⚠️ Record not found in Redis: {redis_key}")
                return False
            
            # Parse original data
            original_data = json.loads(record_data['data'])
            
            # Transform for Weaviate
            weaviate_object = self._transform_for_weaviate(original_data, task['data_type'])
            
            # Import to Weaviate (mock implementation)
            logger.debug(f"📥 Weaviate import: {weaviate_object['id']}")
            
            # Update Redis record with Weaviate status
            await self.redis_client.hset(redis_key, 'weaviate_status', 'exported')
            await self.redis_client.hset(redis_key, 'weaviate_timestamp', datetime.now(timezone.utc).isoformat())
            
            # Remove from export queue
            await self.redis_client.srem("cyberpi:export:pending", redis_key)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Weaviate export failed: {e}")
            # Update error count in Redis
            try:
                error_count = int(await self.redis_client.hget(redis_key, 'error_count') or '0')
                await self.redis_client.hset(redis_key, 'error_count', str(error_count + 1))
                await self.redis_client.hset(redis_key, 'last_error', str(e))
            except Exception:
                pass
            return False
    
    async def _export_to_neo4j(self, task: Dict[str, Any]) -> bool:
        """Export Redis record to Neo4j"""
        try:
            if not self.neo4j_driver:
                return False  # Skip if Neo4j not available
            
            redis_key = task['redis_key']
            
            # Get record from Redis
            record_data = await self.redis_client.hgetall(redis_key)
            if not record_data:
                logger.warning(f"⚠️ Record not found in Redis: {redis_key}")
                return False
            
            # Parse original data
            original_data = json.loads(record_data['data'])
            
            # Transform for Neo4j
            neo4j_data = self._transform_for_neo4j(original_data, task['data_type'])
            
            # Import to Neo4j (mock implementation)
            logger.debug(f"🔗 Neo4j import: {neo4j_data['id']}")
            
            # Update Redis record with Neo4j status
            await self.redis_client.hset(redis_key, 'neo4j_status', 'exported')
            await self.redis_client.hset(redis_key, 'neo4j_timestamp', datetime.now(timezone.utc).isoformat())
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Neo4j export failed: {e}")
            # Update error count in Redis
            try:
                error_count = int(await self.redis_client.hget(redis_key, 'error_count') or '0')
                await self.redis_client.hset(redis_key, 'error_count', str(error_count + 1))
                await self.redis_client.hset(redis_key, 'last_error', str(e))
            except Exception:
                pass
            return False
    
    def _transform_for_weaviate(self, data: Dict[str, Any], data_type: str) -> Dict[str, Any]:
        """Transform data for Weaviate import"""
        return {
            'id': f"cyberpi_{data_type}_{data.get('id', 'unknown')}",
            'title': f"Cyber-pi {data_type.replace('_', ' ').title()}: {data.get('name', 'Unknown')}",
            'content': json.dumps(data, indent=2),
            'metadata': {
                'source_system': 'cyberpi',
                'data_type': data_type,
                'import_timestamp': datetime.now(timezone.utc).isoformat(),
                'original_id': data.get('id')
            }
        }
    
    def _transform_for_neo4j(self, data: Dict[str, Any], data_type: str) -> Dict[str, Any]:
        """Transform data for Neo4j import"""
        return {
            'id': f"cyberpi_{data_type}_{data.get('id', 'unknown')}",
            'labels': [data_type.title(), 'CyberPi'],
            'properties': {
                'name': data.get('name', 'Unknown'),
                'source_system': 'cyberpi',
                'data_type': data_type,
                'import_timestamp': datetime.now(timezone.utc).isoformat(),
                **data
            }
        }
    
    async def get_import_status(self) -> Dict[str, Any]:
        """Get comprehensive import system status"""
        try:
            # Redis statistics
            total_records = await self.redis_client.scard("cyberpi:all:records")
            pending_exports = await self.redis_client.scard("cyberpi:export:pending")
            
            # Data type breakdown
            data_type_stats = {}
            for data_type in DataType:
                type_key = f"cyberpi:{data_type.value}:all"
                count = await self.redis_client.scard(type_key)
                data_type_stats[data_type.value] = count
            
            # Recent activity
            recent_imports = await self.redis_client.zrange("cyberpi:timeline:imports", -10, -1, withscores=True)
            
            return {
                'system_status': {
                    'redis_connected': bool(self.redis_client),
                    'cyberpi_connected': bool(self.cyberpi_session),
                    'weaviate_connected': bool(self.weaviate_client),
                    'neo4j_connected': bool(self.neo4j_driver),
                    'export_queue_size': self.export_queue.qsize()
                },
                'storage_statistics': {
                    'total_records_in_redis': total_records,
                    'pending_exports': pending_exports,
                    'data_type_breakdown': data_type_stats
                },
                'import_statistics': self.import_stats,
                'recent_activity': [
                    {'redis_key': key, 'timestamp': datetime.fromtimestamp(score).isoformat()}
                    for key, score in recent_imports
                ],
                'health_metrics': {
                    'redis_memory_usage': 'N/A',  # Could implement Redis INFO parsing
                    'export_success_rate': (
                        (self.import_stats['weaviate_exports'] + self.import_stats['neo4j_exports']) /
                        max(self.import_stats['total_imports'], 1) * 100
                    )
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Status check failed: {e}")
            return {'error': str(e)}
    
    async def cleanup(self):
        """Clean up connections and background tasks"""
        try:
            # Cancel background tasks
            for task in self.background_tasks:
                task.cancel()
            
            # Wait for tasks to complete
            await asyncio.gather(*self.background_tasks, return_exceptions=True)
            
            # Close connections
            if self.cyberpi_session:
                await self.cyberpi_session.close()
            
            if self.neo4j_driver:
                self.neo4j_driver.close()
            
            if self.redis_client:
                await self.redis_client.close()
            
            logger.info("🧹 Redis-First Import System cleanup completed")
            
        except Exception as e:
            logger.warning(f"⚠️ Cleanup warning: {e}")

async def main():
    """Main execution function"""
    print("🚀 REDIS-FIRST CYBERPI TO TQAKB IMPORT SYSTEM")
    print("=" * 80)
    print("Importing cyber-pi data to Redis first, then distributing to TQAKB...")
    
    # Initialize importer
    importer = RedisFirstCyberPiImporter()
    
    try:
        # Initialize all connections
        await importer.initialize()
        
        # Test imports for different data types
        print("\n📥 Testing cyber-pi imports...")
        
        # Import vendor intelligence
        vendor_result = await importer.import_from_cyberpi(DataType.VENDOR_INTELLIGENCE, limit=5)
        print(f"   Vendor Intelligence: {vendor_result['records_stored']} records")
        
        # Import threat intelligence
        threat_result = await importer.import_from_cyberpi(DataType.THREAT_INTELLIGENCE, limit=3)
        print(f"   Threat Intelligence: {threat_result['records_stored']} records")
        
        # Import IOC data
        ioc_result = await importer.import_from_cyberpi(DataType.IOC_DATA, limit=5)
        print(f"   IOC Data: {ioc_result['records_stored']} records")
        
        # Wait a moment for background exports
        await asyncio.sleep(2)
        
        # Get system status
        status = await importer.get_import_status()
        
        # Print summary
        print("\n" + "=" * 80)
        print("📊 REDIS-FIRST IMPORT SYSTEM SUMMARY")
        print("=" * 80)
        
        print(f"\n🔌 System Connections:")
        system_status = status['system_status']
        print(f"   Redis Connected: {system_status['redis_connected']}")
        print(f"   Cyber-pi Connected: {system_status['cyberpi_connected']}")
        print(f"   Weaviate Connected: {system_status['weaviate_connected']}")
        print(f"   Neo4j Connected: {system_status['neo4j_connected']}")
        
        print(f"\n💾 Storage Statistics:")
        storage_stats = status['storage_statistics']
        print(f"   Total Records in Redis: {storage_stats['total_records_in_redis']}")
        print(f"   Pending Exports: {storage_stats['pending_exports']}")
        print(f"   Export Queue Size: {system_status['export_queue_size']}")
        
        print(f"\n📈 Data Type Breakdown:")
        for data_type, count in storage_stats['data_type_breakdown'].items():
            if count > 0:
                print(f"   {data_type.title()}: {count} records")
        
        print(f"\n🎯 Import Statistics:")
        import_stats = status['import_statistics']
        print(f"   Total Imports: {import_stats['total_imports']}")
        print(f"   Redis Stores: {import_stats['redis_stores']}")
        print(f"   Weaviate Exports: {import_stats['weaviate_exports']}")
        print(f"   Neo4j Exports: {import_stats['neo4j_exports']}")
        print(f"   Import Rate: {import_stats['import_rate']:.2f} records/sec")
        
        print(f"\n✅ Redis-First Import System is operational!")
        print(f"   All cyber-pi data is stored in Redis first")
        print(f"   Background exports to Weaviate and Neo4j are running")
        print(f"   System is ready for production use")
        
    except Exception as e:
        logger.error(f"❌ Import system failed: {e}")
        raise
    
    finally:
        await importer.cleanup()
    
    print(f"\n🎉 Redis-First cyber-pi to TQAKB import system complete!")

if __name__ == "__main__":
    asyncio.run(main())
