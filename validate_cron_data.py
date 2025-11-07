#!/usr/bin/env python3
"""
Cyber-PI Data Validation & Cataloging Script
Validates and catalogs cron job generated JSON files without database integration
"""

import json
import logging
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
from collections import defaultdict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataValidator:
    """Validates and catalogs cron-generated JSON files"""

    def __init__(self):
        logger.info("🔍 Cyber-PI Data Validator Initializing")

        self.stats = {
            'files_processed': 0,
            'records_validated': 0,
            'data_types': defaultdict(int),
            'industries': defaultdict(int),
            'severity_levels': defaultdict(int),
            'time_range': {'earliest': None, 'latest': None},
            'errors': []
        }

    def validate_all_new_data(self) -> Dict[str, Any]:
        """Validate and catalog all new JSON files"""
        logger.info("🔄 Starting data validation process...")

        # Find all new JSON files (last 24 hours)
        new_files = self._find_new_json_files()
        logger.info(f"📁 Found {len(new_files)} new JSON files to validate")

        # Process each file
        for file_path in new_files:
            self._validate_file(file_path)

        # Generate validation report
        return self._generate_validation_report()

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
            mod_time = datetime.fromtimestamp(file_path.stat().st_mtime)
            age_hours = (datetime.now() - mod_time).total_seconds() / 3600
            return age_hours <= 24
        except Exception:
            return False

    def _validate_file(self, file_path: Path):
        """Validate a single JSON file"""
        logger.info(f"📄 Validating: {file_path}")

        try:
            # Load and validate JSON
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self.stats['files_processed'] += 1

            # Determine data type and validate accordingly
            if "financial_threat" in str(file_path):
                self._validate_financial_threat(data, file_path)
            elif "master_collection" in str(file_path):
                self._validate_master_collection(data, file_path)
            elif "threat" in str(file_path).lower():
                self._validate_threat_data(data, file_path)
            else:
                self._validate_generic_data(data, file_path)

            # Update time range
            if isinstance(data, dict) and 'timestamp' in data:
                timestamp = data['timestamp']
                if isinstance(timestamp, str):
                    try:
                        ts_dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        if self.stats['time_range']['earliest'] is None or ts_dt < self.stats['time_range']['earliest']:
                            self.stats['time_range']['earliest'] = ts_dt
                        if self.stats['time_range']['latest'] is None or ts_dt > self.stats['time_range']['latest']:
                            self.stats['time_range']['latest'] = ts_dt
                    except:
                        pass

        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON in {file_path}: {e}"
            logger.error(f"❌ {error_msg}")
            self.stats['errors'].append(error_msg)
        except Exception as e:
            error_msg = f"Failed to validate {file_path}: {e}"
            logger.error(f"❌ {error_msg}")
            self.stats['errors'].append(error_msg)

    def _validate_financial_threat(self, data: Dict[str, Any], file_path: Path):
        """Validate financial threat data"""
        required_fields = ['type', 'ticker', 'company', 'threat_score', 'confidence', 'indicators']

        # Check required fields
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            self.stats['errors'].append(f"Financial threat {file_path} missing fields: {missing_fields}")
            return

        # Validate data types
        if not isinstance(data.get('threat_score'), (int, float)):
            self.stats['errors'].append(f"Financial threat {file_path} has invalid threat_score type")
            return

        if not isinstance(data.get('indicators'), list):
            self.stats['errors'].append(f"Financial threat {file_path} has invalid indicators type")
            return

        # Update statistics
        self.stats['data_types']['financial_threat'] += 1
        self.stats['industries'][data.get('industry', 'unknown')] += 1
        self.stats['records_validated'] += 1

        logger.info(f"✅ Financial threat validated: {data.get('company')} ({data.get('threat_score')} score)")

    def _validate_master_collection(self, data: Dict[str, Any], file_path: Path):
        """Validate master collection data"""
        if 'items' not in data:
            self.stats['errors'].append(f"Master collection {file_path} missing 'items' field")
            return

        items = data['items']
        if not isinstance(items, list):
            self.stats['errors'].append(f"Master collection {file_path} has invalid items type")
            return

        logger.info(f"✅ Master collection validated: {len(items)} intelligence items")

        # Validate each item
        for item in items:
            if isinstance(item, dict):
                self.stats['records_validated'] += 1

                # Categorize by severity if available
                severity = item.get('severity', item.get('priority', 'unknown'))
                self.stats['severity_levels'][severity] += 1

        self.stats['data_types']['master_collection'] += 1

    def _validate_threat_data(self, data: Dict[str, Any], file_path: Path):
        """Validate threat data"""
        # Basic validation - threat data can vary widely
        if not isinstance(data, dict):
            self.stats['errors'].append(f"Threat data {file_path} is not a valid object")
            return

        self.stats['data_types']['threat_intelligence'] += 1
        self.stats['records_validated'] += 1

        # Check for common threat indicators
        threat_indicators = ['threat', 'attack', 'malware', 'vulnerability', 'exploit']
        title = str(data.get('title', '')).lower()
        description = str(data.get('description', '')).lower()

        has_threat_content = any(indicator in title or indicator in description for indicator in threat_indicators)

        if has_threat_content:
            logger.info(f"✅ Threat data validated: {data.get('title', 'Unknown threat')[:50]}...")
        else:
            logger.info(f"⚠️  Generic threat data validated (may need classification)")

    def _validate_generic_data(self, data: Dict[str, Any], file_path: Path):
        """Validate generic JSON data"""
        if not isinstance(data, dict):
            self.stats['errors'].append(f"Generic data {file_path} is not a valid object")
            return

        self.stats['data_types']['generic_intelligence'] += 1
        self.stats['records_validated'] += 1

        logger.info(f"✅ Generic intelligence validated: {len(data)} fields")

    def _generate_validation_report(self) -> Dict[str, Any]:
        """Generate comprehensive validation report"""
        report = {
            "validation_summary": {
                "timestamp": datetime.now().isoformat(),
                "files_processed": self.stats['files_processed'],
                "records_validated": self.stats['records_validated'],
                "validation_errors": len(self.stats['errors']),
                "data_quality_score": (self.stats['records_validated'] / max(self.stats['files_processed'], 1)) * 100
            },
            "data_breakdown": {
                "data_types": dict(self.stats['data_types']),
                "industries_affected": dict(self.stats['industries']),
                "severity_distribution": dict(self.stats['severity_levels']),
                "time_range": {
                    "earliest": self.stats['time_range']['earliest'].isoformat() if self.stats['time_range']['earliest'] else None,
                    "latest": self.stats['time_range']['latest'].isoformat() if self.stats['time_range']['latest'] else None
                }
            },
            "quality_assessment": {
                "validation_passed": len(self.stats['errors']) == 0,
                "data_integrity": "excellent" if len(self.stats['errors']) == 0 else "good" if len(self.stats['errors']) < self.stats['files_processed'] * 0.1 else "needs_attention",
                "collection_completeness": "complete" if self.stats['records_validated'] > 0 else "empty"
            },
            "errors": self.stats['errors'][:10],  # First 10 errors
            "recommendations": self._generate_recommendations()
        }

        return report

    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on validation results"""
        recommendations = []

        # Data quality recommendations
        if len(self.stats['errors']) > 0:
            recommendations.append(f"Fix {len(self.stats['errors'])} data validation errors")

        # Data type recommendations
        if self.stats['data_types']['financial_threat'] > 0:
            recommendations.append("Financial threat data detected - ensure proper classification")

        if self.stats['data_types']['threat_intelligence'] > 0:
            recommendations.append("General threat intelligence found - consider enrichment")

        # Volume recommendations
        if self.stats['records_validated'] > 1000:
            recommendations.append("High data volume detected - consider batch processing")

        # Time range recommendations
        if self.stats['time_range']['earliest'] and self.stats['time_range']['latest']:
            time_span = self.stats['time_range']['latest'] - self.stats['time_range']['earliest']
            if time_span.days > 30:
                recommendations.append("Wide time range detected - consider time-based partitioning")

        return recommendations


def main():
    """Main validation execution"""
    print("🔍 CYBER-PI DATA VALIDATION SYSTEM")
    print("=" * 60)
    print("Validating cron-generated JSON files...")
    print()

    validator = DataValidator()

    # Run validation
    result = validator.validate_all_new_data()

    # Print results
    summary = result['validation_summary']
    breakdown = result['data_breakdown']
    quality = result['quality_assessment']

    print("✅ VALIDATION COMPLETE")
    print("=" * 60)
    print(f"📁 Files Processed: {summary['files_processed']}")
    print(f"📊 Records Validated: {summary['records_validated']}")
    print(f"⚠️  Validation Errors: {summary['validation_errors']}")
    print(f"📊 Data Quality Score: {summary['data_quality_score']:.1f}%")
    print(f"🏥 Data Quality: {quality['data_integrity'].title()}")

    print("\n🎯 DATA BREAKDOWN")
    print("-" * 30)
    for data_type, count in breakdown['data_types'].items():
        print(f"  {data_type.title()}: {count} files")

    if breakdown['industries_affected']:
        print(f"\n🏭 INDUSTRIES AFFECTED")
        print("-" * 30)
        for industry, count in breakdown['industries_affected'].items():
            print(f"  {industry.title()}: {count} threats")

    if breakdown['severity_distribution']:
        print(f"\n🚨 SEVERITY DISTRIBUTION")
        print("-" * 30)
        for severity, count in breakdown['severity_distribution'].items():
            print(f"  {severity.title()}: {count} items")

    if result['recommendations']:
        print(f"\n💡 RECOMMENDATIONS")
        print("-" * 30)
        for rec in result['recommendations']:
            print(f"  • {rec}")

    # Save validation report
    report_file = f"data/validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(result, f, indent=2, default=str)

    print(f"\n📋 Validation report saved: {report_file}")

    if quality['validation_passed']:
        print("\n🎉 All data validation checks passed!")
        return 0
    else:
        print(f"\n⚠️  Validation completed with {summary['validation_errors']} issues")
        return 1


if __name__ == "__main__":
    exit(main())
