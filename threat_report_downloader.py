#!/usr/bin/env python3
"""
Cyber-PI Threat Intelligence Report Downloader
Downloads and parses major cybersecurity reports from CrowdStrike, Mandiant, etc.
"""

import asyncio
import aiohttp
import requests
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import json
import re
from urllib.parse import urljoin, urlparse
import time

# Add src to path
import sys
sys.path.append(str(Path(__file__).parent / "src"))

from src.graph.neo4j_schema import Neo4jSchemaManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ThreatReportDownloader:
    """Downloads and parses major threat intelligence reports"""

    def __init__(self):
        logger.info("🎯 Cyber-PI Threat Report Downloader Initialized")

        self.neo4j_manager = Neo4jSchemaManager()

        # Major threat intelligence reports to monitor
        self.report_sources = {
            "crowdstrike": {
                "name": "CrowdStrike Global Threat Report",
                "base_url": "https://www.crowdstrike.com",
                "report_urls": [
                    "https://www.crowdstrike.com/resources/reports/global-threat-report-2025/",
                    "https://www.crowdstrike.com/resources/reports/threat-hunting-report/",
                    "https://www.crowdstrike.com/resources/reports/2024-global-threat-report/",
                ],
                "parser": "crowdstrike_parser"
            },
            "mandiant": {
                "name": "Mandiant M-Trends Report",
                "base_url": "https://www.mandiant.com",
                "report_urls": [
                    "https://www.mandiant.com/resources/reports/m-trends",
                    "https://www.mandiant.com/resources/reports/mandiant-2024-threat-intelligence-review",
                ],
                "parser": "mandiant_parser"
            },
            "microsoft": {
                "name": "Microsoft Digital Defense Report",
                "base_url": "https://www.microsoft.com",
                "report_urls": [
                    "https://www.microsoft.com/en-us/security/blog/microsoft-digital-defense-report-2024/",
                ],
                "parser": "microsoft_parser"
            },
            "palo_alto": {
                "name": "Unit 42 Threat Reports",
                "base_url": "https://unit42.paloaltonetworks.com",
                "report_urls": [
                    "https://unit42.paloaltonetworks.com/threat-reports/",
                ],
                "parser": "unit42_parser"
            },
            "fireeye_mandiant": {
                "name": "FireEye/Mandiant APT Reports",
                "base_url": "https://www.mandiant.com",
                "report_urls": [
                    "https://www.mandiant.com/resources/insights/apt",
                    "https://www.mandiant.com/resources/insights/advanced-persistent-threat",
                ],
                "parser": "apt_parser"
            }
        }

        # Download statistics
        self.stats = {
            'reports_checked': 0,
            'reports_downloaded': 0,
            'reports_parsed': 0,
            'threat_actors_found': 0,
            'ttps_found': 0,
            'indicators_found': 0,
            'start_time': datetime.now()
        }

    async def download_all_reports(self) -> Dict[str, Any]:
        """Download and parse all configured threat intelligence reports"""
        logger.info("📥 Starting comprehensive threat report download...")

        all_results = {
            "download_summary": {
                "timestamp": datetime.now().isoformat(),
                "reports_processed": 0,
                "total_threat_actors": 0,
                "total_ttps": 0,
                "total_indicators": 0
            },
            "report_results": {}
        }

        for source_key, source_config in self.report_sources.items():
            logger.info(f"🔍 Processing {source_config['name']}...")

            try:
                report_data = await self._process_source(source_key, source_config)
                all_results["report_results"][source_key] = report_data

                # Update summary
                all_results["download_summary"]["reports_processed"] += 1
                all_results["download_summary"]["total_threat_actors"] += report_data.get("threat_actors_found", 0)
                all_results["download_summary"]["total_ttps"] += report_data.get("ttps_found", 0)
                all_results["download_summary"]["total_indicators"] += report_data.get("indicators_found", 0)

            except Exception as e:
                logger.error(f"❌ Failed to process {source_key}: {e}")
                all_results["report_results"][source_key] = {"error": str(e)}

        # Save comprehensive results
        self._save_download_results(all_results)

        return all_results

    async def _process_source(self, source_key: str, source_config: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single threat intelligence source"""
        source_results = {
            "source_name": source_config["name"],
            "reports_found": 0,
            "reports_downloaded": 0,
            "threat_actors_found": 0,
            "ttps_found": 0,
            "indicators_found": 0,
            "parsed_data": []
        }

        for report_url in source_config["report_urls"]:
            try:
                logger.info(f"📄 Checking: {report_url}")

                # Download report page/content
                report_content = await self._download_report_page(report_url)
                if not report_content:
                    continue

                source_results["reports_found"] += 1

                # Parse the report content
                parser_method = getattr(self, f"_{source_config['parser']}", self._generic_parser)
                parsed_data = await parser_method(report_content, report_url)

                if parsed_data:
                    source_results["reports_downloaded"] += 1
                    source_results["parsed_data"].extend(parsed_data)

                    # Count extracted intelligence
                    for item in parsed_data:
                        if item.get("type") == "threat_actor":
                            source_results["threat_actors_found"] += 1
                        elif item.get("type") == "ttp":
                            source_results["ttps_found"] += 1
                        elif item.get("type") == "indicator":
                            source_results["indicators_found"] += 1

                    # Integrate into Neo4j
                    await self._integrate_parsed_data(parsed_data)

            except Exception as e:
                logger.error(f"❌ Failed to process report {report_url}: {e}")

        return source_results

    async def _download_report_page(self, url: str) -> Optional[str]:
        """Download a report page or PDF content"""
        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                headers={'User-Agent': 'Mozilla/5.0 (Cyber-PI Threat Intelligence Collector)'}
            ) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        content = await response.text()
                        logger.debug(f"✅ Downloaded: {url} ({len(content)} chars)")
                        return content
                    else:
                        logger.warning(f"⚠️  Failed to download {url}: HTTP {response.status}")
                        return None
        except Exception as e:
            logger.error(f"❌ Download failed for {url}: {e}")
            return None

    async def _crowdstrike_parser(self, content: str, url: str) -> List[Dict[str, Any]]:
        """Parse CrowdStrike threat reports"""
        parsed_items = []

        # Extract threat actor information
        threat_actors = self._extract_threat_actors(content, "CrowdStrike")
        parsed_items.extend(threat_actors)

        # Extract TTPs
        ttps = self._extract_ttps(content, "CrowdStrike")
        parsed_items.extend(ttps)

        # Extract indicators
        indicators = self._extract_indicators(content, "CrowdStrike")
        parsed_items.extend(indicators)

        logger.info(f"🎯 CrowdStrike: {len(threat_actors)} actors, {len(ttps)} TTPs, {len(indicators)} indicators")
        return parsed_items

    async def _mandiant_parser(self, content: str, url: str) -> List[Dict[str, Any]]:
        """Parse Mandiant M-Trends and threat reports"""
        parsed_items = []

        # Mandiant often focuses on APT groups and advanced threats
        threat_actors = self._extract_threat_actors(content, "Mandiant")
        parsed_items.extend(threat_actors)

        ttps = self._extract_ttps(content, "Mandiant")
        parsed_items.extend(ttps)

        indicators = self._extract_indicators(content, "Mandiant")
        parsed_items.extend(indicators)

        logger.info(f"🎯 Mandiant: {len(threat_actors)} actors, {len(ttps)} TTPs, {len(indicators)} indicators")
        return parsed_items

    async def _apt_parser(self, content: str, url: str) -> List[Dict[str, Any]]:
        """Parse APT and advanced persistent threat reports"""
        parsed_items = []

        # Focus on APT group extraction
        apt_groups = self._extract_apt_groups(content)
        parsed_items.extend(apt_groups)

        # Extract associated TTPs
        ttps = self._extract_ttps(content, "APT Report")
        parsed_items.extend(ttps)

        logger.info(f"🎯 APT Report: {len(apt_groups)} APT groups, {len(ttps)} TTPs")
        return parsed_items

    async def _generic_parser(self, content: str, url: str) -> List[Dict[str, Any]]:
        """Generic parser for threat intelligence content"""
        parsed_items = []

        # Extract any threat-related content
        threat_actors = self._extract_threat_actors(content, "Generic")
        parsed_items.extend(threat_actors)

        ttps = self._extract_ttps(content, "Generic")
        parsed_items.extend(ttps)

        indicators = self._extract_indicators(content, "Generic")
        parsed_items.extend(indicators)

        return parsed_items

    def _extract_threat_actors(self, content: str, source: str) -> List[Dict[str, Any]]:
        """Extract threat actor information from content"""
        actors = []

        # Common threat actor patterns
        actor_patterns = [
            r'APT\s*\d+',  # APT 28, APT 41, etc.
            r'Group\s+\d+',  # Group 123
            r'State\s+Sponsored',  # State-sponsored actors
            r'Advanced\s+Persistent\s+Threat',  # APT descriptions
        ]

        found_actors = set()
        for pattern in actor_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            found_actors.update(matches)

        for actor_name in found_actors:
            actors.append({
                "type": "threat_actor",
                "name": actor_name.strip(),
                "source": source,
                "confidence": "medium",
                "description": f"Threat actor identified in {source} report",
                "first_seen": datetime.now().isoformat(),
                "last_seen": datetime.now().isoformat(),
                "category": "APT" if "APT" in actor_name.upper() else "Unknown"
            })

        return actors

    def _extract_ttps(self, content: str, source: str) -> List[Dict[str, Any]]:
        """Extract Tactics, Techniques, and Procedures"""
        ttps = []

        # MITRE ATT&CK technique patterns
        ttp_patterns = [
            r'T\d{4}',  # T1059, T1071, etc.
            r'spear\s+phishing',
            r'zero\s+day',
            r'supply\s+chain',
            r'lateral\s+movement',
            r'command\s+and\s+control',
            r'data\s+exfiltration'
        ]

        found_ttps = set()
        for pattern in ttp_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            found_ttps.update(matches)

        for ttp_name in found_ttps:
            ttps.append({
                "type": "ttp",
                "name": ttp_name.strip(),
                "source": source,
                "confidence": "medium",
                "description": f"TTP identified in {source} report",
                "category": self._categorize_ttp(ttp_name),
                "first_observed": datetime.now().isoformat()
            })

        return ttps

    def _extract_indicators(self, content: str, source: str) -> List[Dict[str, Any]]:
        """Extract threat indicators (IP addresses, domains, hashes, etc.)"""
        indicators = []

        # IP address pattern
        ip_pattern = r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'
        ips = re.findall(ip_pattern, content)
        for ip in set(ips):
            if not ip.startswith(('127.', '10.', '192.168.', '172.')):  # Skip private IPs
                indicators.append({
                    "type": "indicator",
                    "indicator_type": "ip_address",
                    "value": ip,
                    "source": source,
                    "confidence": "low",
                    "description": f"IP address found in {source} report"
                })

        # Domain pattern (basic)
        domain_pattern = r'\b[a-zA-Z0-9-]+\.[a-zA-Z]{2,}\b'
        domains = re.findall(domain_pattern, content)
        for domain in set(domains):
            if len(domain) > 4 and not any(skip in domain.lower() for skip in ['http', 'www.', 'com.', 'org.']):
                indicators.append({
                    "type": "indicator",
                    "indicator_type": "domain",
                    "value": domain,
                    "source": source,
                    "confidence": "low",
                    "description": f"Domain found in {source} report"
                })

        return indicators

    def _extract_apt_groups(self, content: str) -> List[Dict[str, Any]]:
        """Extract APT group information"""
        apt_groups = []

        # APT group patterns
        apt_patterns = [
            r'APT\s+\d+',
            r'UNC\d+',
            r'FIN\d+',
            r'UNC\d+',
            r'APT\s+[A-Z][a-z]+',  # APT Fancy Bear, etc.
        ]

        found_apts = set()
        for pattern in apt_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            found_apts.update(matches)

        for apt_name in found_apts:
            apt_groups.append({
                "type": "threat_actor",
                "name": apt_name.strip(),
                "source": "APT Report",
                "confidence": "high",
                "description": f"APT group identified in threat intelligence report",
                "first_seen": datetime.now().isoformat(),
                "last_seen": datetime.now().isoformat(),
                "category": "APT",
                "sophistication": "Advanced"
            })

        return apt_groups

    def _categorize_ttp(self, ttp_name: str) -> str:
        """Categorize a TTP based on its name"""
        ttp_lower = ttp_name.lower()

        if 'phishing' in ttp_lower or 'spear' in ttp_lower:
            return "Initial Access"
        elif 'lateral' in ttp_lower:
            return "Lateral Movement"
        elif 'command' in ttp_lower and 'control' in ttp_lower:
            return "Command and Control"
        elif 'exfiltrat' in ttp_lower:
            return "Exfiltration"
        elif 'supply' in ttp_lower and 'chain' in ttp_lower:
            return "Supply Chain"
        elif 'zero' in ttp_lower and 'day' in ttp_lower:
            return "Exploitation"
        else:
            return "General"

    async def _integrate_parsed_data(self, parsed_data: List[Dict[str, Any]]):
        """Integrate parsed threat intelligence into Neo4j"""
        for item in parsed_data:
            try:
                if item["type"] == "threat_actor":
                    await self.neo4j_manager.create_threat_actor_node(item)
                elif item["type"] == "ttp":
                    await self.neo4j_manager.create_ttp_node(item)
                elif item["type"] == "indicator":
                    await self.neo4j_manager.create_indicator_node(item)

                logger.debug(f"✅ Integrated: {item['type']} - {item.get('name', item.get('value', 'Unknown'))}")

            except Exception as e:
                logger.error(f"❌ Failed to integrate {item}: {e}")

    def _save_download_results(self, results: Dict[str, Any]):
        """Save comprehensive download results"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"data/threat_reports_download_{timestamp}.json"

        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)

        logger.info(f"📊 Download results saved: {output_file}")


async def main():
    """Main threat report download execution"""
    print("📥 CYBER-PI THREAT INTELLIGENCE REPORT DOWNLOADER")
    print("=" * 60)
    print("Downloading and parsing major cybersecurity threat reports...")
    print()

    downloader = ThreatReportDownloader()

    try:
        results = await downloader.download_all_reports()

        # Print summary
        summary = results["download_summary"]
        print("✅ DOWNLOAD COMPLETE")
        print("=" * 60)
        print(f"📄 Reports Processed: {summary['reports_processed']}")
        print(f"🎯 Threat Actors Found: {summary['total_threat_actors']}")
        print(f"🛠️  TTPs Identified: {summary['total_ttps']}")
        print(f"🔍 Indicators Extracted: {summary['total_indicators']}")

        print("\n🎯 SOURCES PROCESSED:")
        for source_key, source_data in results["report_results"].items():
            if "error" not in source_data:
                actors = source_data.get("threat_actors_found", 0)
                ttps = source_data.get("ttps_found", 0)
                indicators = source_data.get("indicators_found", 0)
                print(f"  • {source_data['source_name']}: {actors} actors, {ttps} TTPs, {indicators} indicators")

        print("\n🎉 Threat intelligence reports successfully downloaded and integrated!")
        print("📊 Data now available in Neo4j knowledge graph")

        return 0

    except Exception as e:
        print(f"❌ Download failed: {e}")
        return 1


if __name__ == "__main__":
    exit(asyncio.run(main()))
