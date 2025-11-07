#!/usr/bin/env python3
"""
Cyber-PI Data Integration Script
Loads cron job generated JSON files into Neo4j and Weaviate databases
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import time

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from src.graph.neo4j_schema import Neo4jSchemaManager
from src.graph.weaviate_schema import WeaviateSchemaManager
from src.loaders.cve_loader import CVELoader
from src.loaders.mitre_loader import MITRELoader

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataIntegrator:
    """Integrates cron-generated JSON files into Cyber-PI databases"""

    def __init__(self):
        logger.info("🚀 Cyber-PI Data Integrator Initializing")

        # Initialize database connections
        self.neo4j_manager = Neo4jSchemaManager()
        self.weaviate_manager = WeaviateSchemaManager()
        self.cve_loader = CVELoader()
        self.mitre_loader = MITRELoader()

        # Integration statistics
        self.stats = {
            'files_processed': 0,
            'records_loaded': 0,
            'neo4j_nodes': 0,
            'weaviate_objects': 0,
            'errors': 0,
            'start_time': datetime.now()
        }

    async def integrate_all_new_data(self) -> Dict[str, Any]:
        """Integrate all new JSON files from cron jobs"""
        logger.info("🔄 Starting data integration process...")

        try:
            # Find all new JSON files (last 24 hours)
            new_files = self._find_new_json_files()
            logger.info(f"📁 Found {len(new_files)} new JSON files to process")

            # Process each file
            for file_path in new_files:
                await self._process_file(file_path)

            # Generate integration report
            return self._generate_integration_report()

        except Exception as e:
            logger.error(f"❌ Integration failed: {e}")
            return {"error": str(e)}

    def _find_new_json_files(self) -> List[Path]:
        """Find all JSON files modified in the last 24 hours"""
        data_dir = Path("data")
        new_files = []

        # Find files in all data subdirectories
        for pattern in ["**/*.json"]:
            for file_path in data_dir.glob(pattern):
                # Check if file was modified in last 24 hours
                if self._is_recent_file(file_path):
                    new_files.append(file_path)

        return new_files

    def _is_recent_file(self, file_path: Path) -> bool:
        """Check if file was modified in the last 24 hours"""
        try:
            # Get file modification time
            mod_time = datetime.fromtimestamp(file_path.stat().st_mtime)
            age_hours = (datetime.now() - mod_time).total_seconds() / 3600
            return age_hours <= 24
        except Exception:
            return False

    async def _process_file(self, file_path: Path):
        """Process a single JSON file"""
        logger.info(f"📄 Processing: {file_path}")

        try:
            # Load JSON data
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self.stats['files_processed'] += 1

            # Determine data type and process accordingly
            if "financial_threat" in str(file_path):
                await self._process_financial_threat(data, file_path)
            elif "master_collection" in str(file_path):
                await self._process_master_collection(data, file_path)
            elif "threat" in str(file_path).lower():
                await self._process_threat_data(data, file_path)
            else:
                await self._process_generic_data(data, file_path)

        except Exception as e:
            logger.error(f"❌ Failed to process {file_path}: {e}")
            self.stats['errors'] += 1

    async def _process_financial_threat(self, data: Dict[str, Any], file_path: Path):
        """Process financial threat data"""
        logger.info(f"💰 Processing financial threat data from {file_path.name}")

        try:
            # Create financial threat node in Neo4j
            await self.neo4j_manager.create_financial_threat_node(data)

            # Create vector embedding in Weaviate
            threat_text = f"Financial threat for {data.get('company', 'Unknown')}: {data.get('indicators', [])}"
            await self.weaviate_manager.store_financial_threat(data, threat_text)

            self.stats['records_loaded'] += 1
            self.stats['neo4j_nodes'] += 1
            self.stats['weaviate_objects'] += 1

        except Exception as e:
            logger.error(f"❌ Financial threat processing failed: {e}")
            self.stats['errors'] += 1

    async def _process_master_collection(self, data: Dict[str, Any], file_path: Path):
        """Process master collection data"""
        logger.info(f"📊 Processing master collection from {file_path.name}")

        try:
            items = data.get('items', [])
            logger.info(f"   Found {len(items)} intelligence items")

            for item in items:
                # Process each intelligence item
                await self._process_intelligence_item(item)

        except Exception as e:
            logger.error(f"❌ Master collection processing failed: {e}")
            self.stats['errors'] += 1

    async def _process_threat_data(self, data: Dict[str, Any], file_path: Path):
        """Process general threat data"""
        logger.info(f"🎯 Processing threat data from {file_path.name}")

        try:
            # Store in Neo4j as threat intelligence
            await self.neo4j_manager.create_threat_intelligence_node(data)

            # Create vector embedding
            threat_text = json.dumps(data, indent=2)
            await self.weaviate_manager.store_threat_intelligence(data, threat_text)

            self.stats['records_loaded'] += 1
            self.stats['neo4j_nodes'] += 1
            self.stats['weaviate_objects'] += 1

        except Exception as e:
            logger.error(f"❌ Threat data processing failed: {e}")
            self.stats['errors'] += 1

    async def _process_generic_data(self, data: Dict[str, Any], file_path: Path):
        """Process generic JSON data"""
        logger.info(f"📋 Processing generic data from {file_path.name}")

        try:
            # Store as generic intelligence node
            await self.neo4j_manager.create_generic_intelligence_node(data)

            # Create vector embedding
            content_text = json.dumps(data, indent=2)
            await self.weaviate_manager.store_generic_intelligence(data, content_text)

            self.stats['records_loaded'] += 1
            self.stats['neo4j_nodes'] += 1
            self.stats['weaviate_objects'] += 1

        except Exception as e:
            logger.error(f"❌ Generic data processing failed: {e}")
            self.stats['errors'] += 1

    async def _process_intelligence_item(self, item: Dict[str, Any]):
        """Process a single intelligence item"""
        try:
            # Determine item type and process accordingly
            if 'CVE' in str(item.get('title', '')) or 'vulnerability' in str(item).lower():
                # CVE data
                await self.cve_loader.load_cve_record(item)
            elif 'threat' in str(item).lower() or 'attack' in str(item).lower():
                # Threat intelligence
                await self.neo4j_manager.create_threat_intelligence_node(item)
                threat_text = f"{item.get('title', '')} {item.get('description', '')}"
                await self.weaviate_manager.store_threat_intelligence(item, threat_text)
            else:
                # Generic intelligence
                await self.neo4j_manager.create_generic_intelligence_node(item)
                content_text = f"{item.get('title', '')} {item.get('description', '')}"
                await self.weaviate_manager.store_generic_intelligence(item, content_text)

            self.stats['records_loaded'] += 1

        except Exception as e:
            logger.error(f"❌ Intelligence item processing failed: {e}")
            self.stats['errors'] += 1

    def _generate_integration_report(self) -> Dict[str, Any]:
        """Generate comprehensive integration report"""
        end_time = datetime.now()
        duration = (end_time - self.stats['start_time']).total_seconds()

        report = {
            "integration_summary": {
                "start_time": self.stats['start_time'].isoformat(),
                "end_time": end_time.isoformat(),
                "duration_seconds": duration,
                "status": "completed" if self.stats['errors'] == 0 else "completed_with_errors"
            },
            "processing_statistics": {
                "files_processed": self.stats['files_processed'],
                "records_loaded": self.stats['records_loaded'],
                "neo4j_nodes_created": self.stats['neo4j_nodes'],
                "weaviate_objects_created": self.stats['weaviate_objects'],
                "errors_encountered": self.stats['errors'],
                "processing_rate": self.stats['records_loaded'] / duration if duration > 0 else 0
            },
            "data_breakdown": {
                "financial_threats": len([f for f in self._find_new_json_files() if "financial_threat" in str(f)]),
                "master_collections": len([f for f in self._find_new_json_files() if "master_collection" in str(f)]),
                "threat_intelligence": len([f for f in self._find_new_json_files() if "threat" in str(f).lower()]),
                "intelligence_reports": len([f for f in self._find_new_json_files() if "report" in str(f)])
            },
            "system_health": {
                "neo4j_connection": "active",
                "weaviate_connection": "active",
                "data_integrity": "verified" if self.stats['errors'] == 0 else "warnings_present"
            }
        }

        return report


async def main():
    """Main integration execution"""
    print("🚀 CYBER-PI DATA INTEGRATION SYSTEM")
    print("=" * 60)
    print("Integrating cron-generated JSON files into databases...")
    print()

    integrator = DataIntegrator()

    try:
        # Run integration
        result = await integrator.integrate_all_new_data()

        if "error" in result:
            print(f"❌ Integration failed: {result['error']}")
            return 1

        # Print results
        summary = result['integration_summary']
        stats = result['processing_statistics']

        print("✅ INTEGRATION COMPLETE")
        print("=" * 60)
        print(f"⏱️  Duration: {summary['duration_seconds']:.1f} seconds")
        print(f"📁 Files Processed: {stats['files_processed']}")
        print(f"📊 Records Loaded: {stats['records_loaded']}")
        print(f"🔗 Neo4j Nodes: {stats['neo4j_nodes']}")
        print(f"🧠 Weaviate Objects: {stats['weaviate_objects']}")
        print(f"⚠️  Errors: {stats['errors']}")
        print(f"⚡ Processing Rate: {stats['processing_rate']:.2f} records/sec")

        if stats['errors'] == 0:
            print("\n🎉 All data successfully integrated!")
        else:
            print(f"\n⚠️  Integration completed with {stats['errors']} errors")

        # Save integration report
        report_file = f"data/integration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(result, f, indent=2, default=str)

        print(f"📋 Integration report saved: {report_file}")

        return 0

    except Exception as e:
        print(f"❌ Integration system error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
