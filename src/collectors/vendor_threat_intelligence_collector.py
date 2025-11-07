#!/usr/bin/env python3
"""
Vendor Threat Intelligence Collector
Researches all Nexum Inc. vendors for security vulnerabilities, threats, and risks
"""

import asyncio
import aiohttp
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

# Add project paths
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Import our intelligence components
from test_scraperapi_working import WorkingScraperAPIDemo

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RiskLevel(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

@dataclass
class VendorThreatIntelligence:
    """Vendor threat intelligence data structure"""
    vendor_name: str
    risk_level: RiskLevel
    vulnerabilities: List[Dict[str, Any]]
    security_incidents: List[Dict[str, Any]]
    reputation_score: float
    last_breach_date: Optional[str]
    compliance_issues: List[str]
    iocs: List[str]
    recommendations: List[str]
    research_sources: List[str]
    research_timestamp: str

class VendorThreatIntelligenceCollector:
    """
    Comprehensive vendor threat intelligence research system
    """
    
    def __init__(self, scraperapi_key: str):
        self.scraperapi_key = scraperapi_key
        self.base_search_urls = [
            "https://www.cvedetails.com/vendor/",
            "https://www.cisa.gov/news-events/cybersecurity-advisories",
            "https://threatpost.com/tag/",
            "https://www.securityweek.com/tag/",
            "https://www.helpnetsecurity.com/tag/"
        ]
        
        # Nexum Inc. vendor list from their website
        self.nexum_vendors = [
            "1Touch", "Abnormal", "Algosec", "Appdome", "AppviewX", "Arista", "Armis", 
            "Attivo Networks", "Aviatrix", "Axonius", "Backbox", "BitSight", "Broadcom", 
            "Bugcrowd", "Carbon Black", "Cato Networks", "Check Point", "Cisco", 
            "Cloudflare", "Code42", "Corelight", "Cribl", "Crowdstrike", "CyberArk", 
            "Cyera", "Cylance", "Devo", "Entrust", "Exabeam", "Extrahop", "F5 Networks", 
            "Fastly", "Fidelis", "Firemon", "Forescout", "Fortinet", "Fortra", "Gigamon", 
            "Google", "Grip Security", "HPE", "IBM", "Illumio", "Infoblox", "Ironscales", 
            "Ivanti", "Ixia", "Juniper Networks", "Keeper Security", "Keysight", "Lacework", 
            "Live Cyber", "LogRhythm", "Malwarebytes", "Menlo Security", "Microsoft", 
            "Morphisec", "NetScout", "Netskope", "Noname", "Nutanix", "Okta", "Orca", 
            "Palo Alto Networks", "Proofpoint", "Qualys", "Rapid7", "Recorded Future", 
            "RedSeal", "Riverbed", "RSA", "SecurityScorecard", "Seemplicity", "Semperis", 
            "SentinelOne", "Snyk", "StrongDM", "Sumo", "Swimlane", "Synopsys", "Tenable", 
            "Thales", "Trellix", "Trend Micro", "Tufin", "vArmour", "Varonis", "Veracode", 
            "Versa Networks", "Wiz", "Zscaler"
        ]
        
        self.research_results = {}
        self.collection_stats = {
            'total_vendors': len(self.nexum_vendors),
            'researched_vendors': 0,
            'high_risk_vendors': 0,
            'critical_vulnerabilities': 0,
            'security_incidents': 0
        }
        
        logger.info(f"🔍 Vendor Threat Intelligence Collector Initialized")
        logger.info(f"📊 Researching {len(self.nexum_vendors)} Nexum vendors")
    
    async def research_vendor(self, vendor_name: str) -> VendorThreatIntelligence:
        """Research a single vendor for threat intelligence"""
        logger.info(f"🔍 Researching vendor: {vendor_name}")
        
        try:
            # Initialize ScraperAPI for research
            scraperapi_demo = WorkingScraperAPIDemo(self.scraperapi_key)
            
            # Search for vendor-specific security information
            search_queries = [
                f"{vendor_name} security vulnerability",
                f"{vendor_name} data breach",
                f"{vendor_name} CVE security",
                f"{vendor_name} security incident"
            ]
            
            vulnerabilities = []
            security_incidents = []
            iocs = []
            research_sources = []
            
            # Research each query
            for query in search_queries:
                try:
                    # Simulate search results (in real implementation, would use search APIs)
                    search_results = await self._search_vendor_security_info(query, scraperapi_demo)
                    
                    for result in search_results:
                        if 'vulnerability' in result.get('title', '').lower() or 'cve' in result.get('title', '').lower():
                            vulnerabilities.append(result)
                        elif 'breach' in result.get('title', '').lower() or 'incident' in result.get('title', '').lower():
                            security_incidents.append(result)
                        
                        # Extract IOCs from content
                        content_iocs = self._extract_iocs_from_content(result.get('content', ''))
                        iocs.extend(content_iocs)
                        
                    research_sources.extend([r.get('source', '') for r in search_results])
                    
                except Exception as e:
                    logger.warning(f"⚠️ Search failed for {query}: {e}")
                    continue
            
            # Calculate risk level based on findings
            risk_level = self._calculate_vendor_risk_level(vulnerabilities, security_incidents)
            
            # Generate recommendations
            recommendations = self._generate_vendor_recommendations(vendor_name, risk_level, vulnerabilities, security_incidents)
            
            # Create vendor intelligence object
            vendor_intelligence = VendorThreatIntelligence(
                vendor_name=vendor_name,
                risk_level=risk_level,
                vulnerabilities=vulnerabilities,
                security_incidents=security_incidents,
                reputation_score=self._calculate_reputation_score(vulnerabilities, security_incidents),
                last_breach_date=self._get_last_breach_date(security_incidents),
                compliance_issues=self._identify_compliance_issues(vendor_name, vulnerabilities),
                iocs=list(set(iocs)),  # Remove duplicates
                recommendations=recommendations,
                research_sources=list(set(research_sources)),
                research_timestamp=datetime.now(timezone.utc).isoformat()
            )
            
            self.collection_stats['researched_vendors'] += 1
            if risk_level in [RiskLevel.CRITICAL, RiskLevel.HIGH]:
                self.collection_stats['high_risk_vendors'] += 1
            
            self.collection_stats['critical_vulnerabilities'] += len([v for v in vulnerabilities if v.get('severity') == 'critical'])
            self.collection_stats['security_incidents'] += len(security_incidents)
            
            logger.info(f"✅ Research complete for {vendor_name}: Risk Level {risk_level.value.upper()}")
            return vendor_intelligence
            
        except Exception as e:
            logger.error(f"❌ Research failed for {vendor_name}: {e}")
            # Return minimal intelligence on error
            return VendorThreatIntelligence(
                vendor_name=vendor_name,
                risk_level=RiskLevel.MEDIUM,
                vulnerabilities=[],
                security_incidents=[],
                reputation_score=0.5,
                last_breach_date=None,
                compliance_issues=["Research failed - manual review required"],
                iocs=[],
                recommendations=["Manual security assessment required"],
                research_sources=["Research failed"],
                research_timestamp=datetime.now(timezone.utc).isoformat()
            )
    
    async def _search_vendor_security_info(self, query: str, scraperapi_demo: WorkingScraperAPIDemo) -> List[Dict[str, Any]]:
        """Search for vendor security information using ScraperAPI
        
        TODO: Implement real search functionality using:
        - CVE Details API
        - CISA API
        - Vendor security advisories
        - Threat intelligence feeds
        
        This is a placeholder that returns empty results.
        """
        logger.warning(f"_search_vendor_security_info not implemented for: {query}")
        return []
    
    def _extract_iocs_from_content(self, content: str) -> List[str]:
        """Extract indicators of compromise from content"""
        import re
        
        iocs = []
        
        # IP addresses
        ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
        ips = re.findall(ip_pattern, content)
        iocs.extend(ips)
        
        # CVE numbers
        cve_pattern = r'CVE-\d{4}-\d{4,7}'
        cves = re.findall(cve_pattern, content.upper())
        iocs.extend(cves)
        
        # Domains
        domain_pattern = r'\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}\b'
        domains = re.findall(domain_pattern, content)
        iocs.extend(domains)
        
        return iocs
    
    def _calculate_vendor_risk_level(self, vulnerabilities: List[Dict], incidents: List[Dict]) -> RiskLevel:
        """Calculate risk level based on vulnerabilities and incidents"""
        critical_vulns = len([v for v in vulnerabilities if v.get('severity') == 'critical'])
        high_vulns = len([v for v in vulnerabilities if v.get('severity') == 'high'])
        recent_incidents = len([i for i in incidents if self._is_recent_incident(i.get('date', ''))])
        
        if critical_vulns > 0 or recent_incidents > 2:
            return RiskLevel.CRITICAL
        elif high_vulns > 2 or recent_incidents > 0:
            return RiskLevel.HIGH
        elif len(vulnerabilities) > 0 or len(incidents) > 0:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def _is_recent_incident(self, date_str: str) -> bool:
        """Check if incident is recent (within last 6 months)"""
        try:
            if not date_str:
                return False
            incident_date = datetime.strptime(date_str, '%Y-%m-%d')
            six_months_ago = datetime.now() - timedelta(days=180)
            return incident_date > six_months_ago
        except Exception:
            return False
    
    def _calculate_reputation_score(self, vulnerabilities: List[Dict], incidents: List[Dict]) -> float:
        """Calculate vendor reputation score (0.0 - 1.0)"""
        base_score = 0.8
        
        # Deduct points for critical issues
        critical_vulns = len([v for v in vulnerabilities if v.get('severity') == 'critical'])
        high_vulns = len([v for v in vulnerabilities if v.get('severity') == 'high'])
        recent_incidents = len([i for i in incidents if self._is_recent_incident(i.get('date', ''))])
        
        score = base_score - (critical_vulns * 0.15) - (high_vulns * 0.08) - (recent_incidents * 0.10)
        return max(0.0, min(1.0, score))
    
    def _get_last_breach_date(self, incidents: List[Dict]) -> Optional[str]:
        """Get the most recent breach date"""
        if not incidents:
            return None
        
        dates = []
        for incident in incidents:
            date_str = incident.get('date', '')
            if date_str:
                try:
                    dates.append(datetime.strptime(date_str, '%Y-%m-%d'))
                except Exception:
                    continue
        
        if dates:
            return max(dates).strftime('%Y-%m-%d')
        return None
    
    def _identify_compliance_issues(self, vendor_name: str, vulnerabilities: List[Dict]) -> List[str]:
        """Identify potential compliance issues"""
        issues = []
        
        critical_vulns = len([v for v in vulnerabilities if v.get('severity') == 'critical'])
        if critical_vulns > 0:
            issues.append("Critical vulnerabilities may impact compliance")
        
        if any("authentication" in v.get('content', '').lower() for v in vulnerabilities):
            issues.append("Authentication vulnerabilities may affect access control compliance")
        
        if any("data" in v.get('content', '').lower() for v in vulnerabilities):
            issues.append("Data protection compliance concerns")
        
        return issues
    
    def _generate_vendor_recommendations(self, vendor_name: str, risk_level: RiskLevel, vulnerabilities: List[Dict], incidents: List[Dict]) -> List[str]:
        """Generate specific recommendations for vendor"""
        recommendations = []
        
        if risk_level == RiskLevel.CRITICAL:
            recommendations.extend([
                "Immediate security review required",
                "Consider alternative vendors if possible",
                "Implement additional compensating controls",
                "Monitor vendor security advisories daily"
            ])
        elif risk_level == RiskLevel.HIGH:
            recommendations.extend([
                "Enhanced monitoring of vendor products",
                "Accelerated patch management",
                "Security assessment within 30 days",
                "Review service level agreements"
            ])
        elif risk_level == RiskLevel.MEDIUM:
            recommendations.extend([
                "Regular security monitoring",
                "Standard patch management",
                "Quarterly security reviews",
                "Maintain vendor contact for security issues"
            ])
        else:
            recommendations.extend([
                "Standard security monitoring",
                "Regular patch management",
                "Annual security reviews"
            ])
        
        # Add specific recommendations based on vulnerabilities
        if any("remote code execution" in v.get('content', '').lower() for v in vulnerabilities):
            recommendations.append("Implement network segmentation for vendor products")
        
        if any("authentication" in v.get('content', '').lower() for v in vulnerabilities):
            recommendations.append("Review and strengthen authentication mechanisms")
        
        if any("vpn" in v.get('content', '').lower() for v in vulnerabilities):
            recommendations.append("Enhance VPN monitoring and logging")
        
        return recommendations
    
    async def research_all_vendors(self) -> Dict[str, VendorThreatIntelligence]:
        """Research all Nexum vendors"""
        logger.info("🚀 Starting comprehensive vendor threat intelligence research")
        logger.info(f"📊 Researching {len(self.nexum_vendors)} vendors")
        
        start_time = time.time()
        
        # Create tasks for concurrent research (limit concurrency to avoid overwhelming)
        semaphore = asyncio.Semaphore(5)  # Limit to 5 concurrent requests
        
        async def research_with_semaphore(vendor):
            async with semaphore:
                return await self.research_vendor(vendor)
        
        tasks = [research_with_semaphore(vendor) for vendor in self.nexum_vendors]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for i, vendor in enumerate(self.nexum_vendors):
            if isinstance(results[i], VendorThreatIntelligence):
                self.research_results[vendor] = results[i]
            elif isinstance(results[i], Exception):
                logger.error(f"❌ Research failed for {vendor}: {results[i]}")
        
        duration = time.time() - start_time
        
        logger.info("=" * 80)
        logger.info("📊 VENDOR RESEARCH SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Total Vendors Researched: {self.collection_stats['researched_vendors']}/{self.collection_stats['total_vendors']}")
        logger.info(f"High-Risk Vendors: {self.collection_stats['high_risk_vendors']}")
        logger.info(f"Critical Vulnerabilities: {self.collection_stats['critical_vulnerabilities']}")
        logger.info(f"Security Incidents: {self.collection_stats['security_incidents']}")
        logger.info(f"Research Duration: {duration:.2f} seconds")
        
        return self.research_results
    
    def generate_vendor_risk_report(self) -> Dict[str, Any]:
        """Generate comprehensive vendor risk report"""
        logger.info("📊 Generating vendor risk report...")
        
        # Analyze risk distribution
        risk_distribution = {}
        high_risk_vendors = []
        critical_vulnerabilities = []
        recent_incidents = []
        compliance_concerns = []
        
        for vendor, intelligence in self.research_results.items():
            risk_level = intelligence.risk_level.value
            risk_distribution[risk_level] = risk_distribution.get(risk_level, 0) + 1
            
            if intelligence.risk_level in [RiskLevel.CRITICAL, RiskLevel.HIGH]:
                high_risk_vendors.append({
                    'vendor': vendor,
                    'risk_level': risk_level,
                    'reputation_score': intelligence.reputation_score,
                    'vulnerabilities': len(intelligence.vulnerabilities),
                    'incidents': len(intelligence.security_incidents),
                    'last_breach': intelligence.last_breach_date
                })
            
            critical_vulns = [v for v in intelligence.vulnerabilities if v.get('severity') == 'critical']
            critical_vulnerabilities.extend([
                {'vendor': vendor, 'vulnerability': vuln} for vuln in critical_vulns
            ])
            
            if intelligence.security_incidents:
                recent_incidents.extend([
                    {'vendor': vendor, 'incident': incident} for incident in intelligence.security_incidents
                ])
            
            if intelligence.compliance_issues:
                compliance_concerns.extend([
                    {'vendor': vendor, 'issues': intelligence.compliance_issues}
                ])
        
        # Sort high-risk vendors by risk
        high_risk_vendors.sort(key=lambda x: (x['vulnerabilities'] + x['incidents']), reverse=True)
        
        report = {
            'report_metadata': {
                'generated_at': datetime.now(timezone.utc).isoformat(),
                'total_vendors_analyzed': len(self.research_results),
                'analysis_scope': 'Nexum Inc. Technology Partners',
                'research_methodology': 'ScraperAPI-powered security intelligence gathering'
            },
            'executive_summary': {
                'total_vendors': len(self.nexum_vendors),
                'researched_vendors': self.collection_stats['researched_vendors'],
                'high_risk_vendors': len(high_risk_vendors),
                'critical_vulnerabilities': len(critical_vulnerabilities),
                'security_incidents': len(recent_incidents),
                'compliance_concerns': len(compliance_concerns),
                'overall_risk_assessment': self._calculate_overall_risk_assessment(risk_distribution)
            },
            'risk_distribution': risk_distribution,
            'high_risk_vendors': high_risk_vendors[:20],  # Top 20 high-risk vendors
            'critical_vulnerabilities': critical_vulnerabilities[:15],  # Top 15 critical vulns
            'recent_security_incidents': recent_incidents[:10],  # Top 10 recent incidents
            'compliance_concerns': compliance_concerns,
            'recommendations': self._generate_overall_recommendations(high_risk_vendors, critical_vulnerabilities),
            'vendor_intelligence': {
                vendor: {
                    'risk_level': intel.risk_level.value,
                    'reputation_score': intel.reputation_score,
                    'vulnerabilities': len(intel.vulnerabilities),
                    'incidents': len(intel.security_incidents),
                    'compliance_issues': intel.compliance_issues,
                    'recommendations': intel.recommendations[:3],  # Top 3 recommendations
                    'research_timestamp': intel.research_timestamp
                }
                for vendor, intel in self.research_results.items()
            }
        }
        
        logger.info("✅ Vendor risk report generated")
        return report
    
    def _calculate_overall_risk_assessment(self, risk_distribution: Dict[str, int]) -> str:
        """Calculate overall risk assessment"""
        total = sum(risk_distribution.values())
        if total == 0:
            return "Unable to assess"
        
        critical_percentage = (risk_distribution.get('critical', 0) / total) * 100
        high_percentage = (risk_distribution.get('high', 0) / total) * 100
        
        if critical_percentage > 10:
            return "CRITICAL - Immediate action required"
        elif critical_percentage > 5 or high_percentage > 20:
            return "HIGH - Enhanced monitoring needed"
        elif high_percentage > 10:
            return "MEDIUM - Regular monitoring required"
        else:
            return "LOW - Standard monitoring sufficient"
    
    def _generate_overall_recommendations(self, high_risk_vendors: List[Dict], critical_vulnerabilities: List[Dict]) -> List[str]:
        """Generate overall recommendations for Nexum"""
        recommendations = []
        
        if len(high_risk_vendors) > 10:
            recommendations.append("Implement comprehensive vendor risk management program")
        
        if len(critical_vulnerabilities) > 5:
            recommendations.append("Prioritize patch management for critical vulnerabilities")
        
        # Vendor-specific recommendations
        high_risk_names = [v['vendor'] for v in high_risk_vendors[:5]]
        if high_risk_names:
            recommendations.append(f"Immediate security review required for: {', '.join(high_risk_names)}")
        
        recommendations.extend([
            "Establish vendor security monitoring program",
            "Implement regular vendor security assessments",
            "Create vendor incident response procedures",
            "Review service level agreements for security requirements",
            "Consider diversifying critical vendor dependencies"
        ])
        
        return recommendations
    
    def save_vendor_intelligence_report(self, report: Dict[str, Any]) -> str:
        """Save vendor intelligence report"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"data/reports/nexum_vendor_threat_intelligence_{timestamp}.json"
        
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"📄 Vendor intelligence report saved: {filename}")
        return filename

async def main():
    """Main execution function"""
    print("🔍 NEXUM VENDOR THREAT INTELLIGENCE RESEARCH")
    print("=" * 80)
    print("Researching all Nexum Inc. technology partners for security risks...")
    
    # Initialize collector with API key from environment
    scraperapi_key = os.getenv('SCRAPERAPI_KEY')
    if not scraperapi_key:
        raise ValueError("SCRAPERAPI_KEY environment variable must be set")
    
    collector = VendorThreatIntelligenceCollector(scraperapi_key)
    
    try:
        # Research all vendors
        await collector.research_all_vendors()
        
        # Generate comprehensive report
        report = collector.generate_vendor_risk_report()
        
        # Save report
        filename = collector.save_vendor_intelligence_report(report)
        
        # Print summary
        print("\n" + "=" * 80)
        print("📊 NEXUM VENDOR THREAT INTELLIGENCE SUMMARY")
        print("=" * 80)
        
        exec_summary = report['executive_summary']
        print(f"\n🎯 Research Results:")
        print(f"   Total Vendors Analyzed: {exec_summary['total_vendors']}")
        print(f"   Successfully Researched: {exec_summary['researched_vendors']}")
        print(f"   High-Risk Vendors: {exec_summary['high_risk_vendors']}")
        print(f"   Critical Vulnerabilities: {exec_summary['critical_vulnerabilities']}")
        print(f"   Security Incidents: {exec_summary['security_incidents']}")
        print(f"   Compliance Concerns: {exec_summary['compliance_concerns']}")
        
        print(f"\n⚠️ Overall Risk Assessment: {exec_summary['overall_risk_assessment']}")
        
        print(f"\n🚨 Top High-Risk Vendors:")
        for i, vendor in enumerate(report['high_risk_vendors'][:10]):
            print(f"   {i+1}. {vendor['vendor']} - {vendor['risk_level'].upper()} ({vendor['vulnerabilities']} vulns, {vendor['incidents']} incidents)")
        
        print(f"\n💡 Key Recommendations:")
        for i, rec in enumerate(report['recommendations'][:5]):
            print(f"   {i+1}. {rec}")
        
        print(f"\n📄 Comprehensive Report: {filename}")
        
    except Exception as e:
        logger.error(f"❌ Vendor research failed: {e}")
        raise
    
    print(f"\n🎉 Nexum vendor threat intelligence research complete!")

if __name__ == "__main__":
    asyncio.run(main())
