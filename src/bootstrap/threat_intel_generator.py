#!/usr/bin/env python3
"""
Threat Intelligence Generator
Creates realistic threat intelligence data for the unified graph
"""

import sys
import random
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from bootstrap.mitre_techniques import (
    MITRE_TECHNIQUES, 
    CWE_TECHNIQUE_MAPPINGS, 
    THREAT_TYPES, 
    THREAT_SOURCES
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ThreatIntelGenerator:
    """Generate realistic threat intelligence data"""
    
    def __init__(self, num_threats: int = 100, seed: int = 42):
        """Initialize the generator"""
        random.seed(seed)
        self.num_threats = num_threats
        self.cve_base_year = 2020
        self.cve_max_year = 2025
        
    def _generate_cve_id(self) -> str:
        """Generate a random CVE ID"""
        year = random.randint(self.cve_base_year, self.cve_max_year)
        number = random.randint(1000, 9999)
        return f"CVE-{year}-{number}"
    
    def _generate_date(self) -> str:
        """Generate a random date in the past 2 years"""
        days_ago = random.randint(1, 730)  # Up to 2 years ago
        date = datetime.now() - timedelta(days=days_ago)
        return date.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    def _select_random_techniques(self, num: int = 3) -> List[str]:
        """Select random MITRE techniques"""
        return random.sample(list(MITRE_TECHNIQUES.keys()), min(num, len(MITRE_TECHNIQUES)))
    
    def _get_tactics_from_techniques(self, techniques: List[str]) -> List[str]:
        """Get the tactics associated with techniques"""
        tactics = set()
        for technique in techniques:
            if technique in MITRE_TECHNIQUES:
                tactics.add(MITRE_TECHNIQUES[technique]["tactic"])
        return list(tactics)
    
    def _select_affected_products(self) -> List[str]:
        """Select random affected products"""
        products = [
            "windows_10", "windows_11", "office_365", "exchange_server",
            "linux_kernel", "apache_tomcat", "nginx", "mysql", "postgresql",
            "chrome", "firefox", "safari", "edge", "android", "ios",
            "macos", "ubuntu", "debian", "fedora", "centos"
        ]
        return random.sample(products, random.randint(1, 5))
    
    def _select_affected_vendors(self) -> List[str]:
        """Select random affected vendors"""
        vendors = [
            "microsoft", "apple", "google", "oracle", "ibm",
            "cisco", "vmware", "redhat", "canonical", "mozilla",
            "apache", "nginx", "dell", "hp", "lenovo"
        ]
        return random.sample(vendors, random.randint(1, 3))
    
    def _select_cwes(self) -> List[str]:
        """Select random CWEs"""
        cwes = list(CWE_TECHNIQUE_MAPPINGS.keys())
        return random.sample(cwes, random.randint(1, 3))
    
    def _select_cves(self, num: int = 5) -> List[str]:
        """Select random CVEs"""
        return [self._generate_cve_id() for _ in range(num)]
    
    def _generate_threat(self, threat_id: int) -> Dict[str, Any]:
        """Generate a single threat intelligence object"""
        # Select techniques and get associated tactics
        techniques = self._select_random_techniques(random.randint(2, 5))
        tactics = self._get_tactics_from_techniques(techniques)
        
        # Generate severity
        severity_options = ["critical", "high", "medium", "low"]
        severity_weights = [0.2, 0.3, 0.3, 0.2]
        severity = random.choices(severity_options, weights=severity_weights)[0]
        
        # Generate threat type
        threat_type = random.choice(THREAT_TYPES)
        
        # Generate source
        source = random.choice(THREAT_SOURCES)
        
        # Generate confidence score (0.5 to 1.0)
        confidence = round(0.5 + random.random() * 0.5, 2)
        
        # Create the threat object
        threat = {
            "id": f"threat-{threat_id:04d}",
            "title": f"{source.upper()} {threat_type.capitalize()} Campaign",
            "description": f"A {severity} severity {threat_type} campaign attributed to {source.upper()} "
                          f"targeting multiple systems using {len(techniques)} techniques.",
            "severity": severity,
            "type": threat_type,
            "source": source,
            "cves": self._select_cves(random.randint(3, 8)),
            "mitreTactics": tactics,
            "mitreTechniques": techniques,
            "affectedProducts": self._select_affected_products(),
            "affectedVendors": self._select_affected_vendors(),
            "cwes": self._select_cwes(),
            "publishedDate": self._generate_date(),
            "confidence": confidence
        }
        
        return threat
    
    def generate_threats(self) -> List[Dict[str, Any]]:
        """Generate multiple threat intelligence objects"""
        logger.info(f"Generating {self.num_threats} threat intelligence objects...")
        
        threats = []
        for i in range(1, self.num_threats + 1):
            threat = self._generate_threat(i)
            threats.append(threat)
            
        logger.info(f"✅ Generated {len(threats)} threat intelligence objects")
        return threats

def main():
    """Main function"""
    generator = ThreatIntelGenerator(num_threats=200)
    threats = generator.generate_threats()
    
    # Print a sample
    import json
    print(json.dumps(threats[0], indent=2))
    print(f"Total threats generated: {len(threats)}")

if __name__ == "__main__":
    main()
