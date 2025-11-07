"""
STIX 2.1 Converter for Cyber-PI Threat Intelligence
Converts between cyber-pi format and STIX 2.1 standard
"""

from typing import Dict, List, Any, Optional
import uuid
from datetime import datetime
import json

# We'll install stix2 library
try:
    from stix2 import (
        Indicator, Malware, ThreatActor, Vulnerability, 
        AttackPattern, Identity, Relationship, Bundle,
        Campaign, Infrastructure, Location
    )
    STIX2_AVAILABLE = True
except ImportError:
    STIX2_AVAILABLE = False
    print("⚠️  stix2 library not installed. Run: pip install stix2")


class STIXConverter:
    """
    Convert cyber-pi threat intelligence to/from STIX 2.1 format
    
    Philosophy: STIX is our PRIMARY format internally.
    Everything gets converted to STIX immediately upon ingestion.
    """
    
    # Map our industries to STIX sectors
    INDUSTRY_TO_SECTOR_MAP = {
        "Aviation & Airlines": "aerospace",
        "Healthcare & Medical": "healthcare",
        "Energy & Utilities": "energy",
        "Financial Services": "financial-services",
        "Manufacturing": "manufacturing",
        "Retail & E-commerce": "retail",
        "Technology": "technology",
        "Telecommunications": "telecommunications",
        "Government & Public Sector": "government-national",
        "Education": "education",
        "Transportation & Logistics": "transportation",
        "Hospitality & Entertainment": "hospitality-leisure",
        "Real Estate": "real-estate",
        "Agriculture": "agriculture",
        "Mining & Resources": "mining",
        "Professional Services": "services",
        "Media & Publishing": "communications",
        "Pharmaceuticals": "chemical"
    }
    
    # Reverse mapping
    SECTOR_TO_INDUSTRY_MAP = {v: k for k, v in INDUSTRY_TO_SECTOR_MAP.items()}
    
    def __init__(self):
        if not STIX2_AVAILABLE:
            raise ImportError("stix2 library required. Install with: pip install stix2")
    
    def threat_to_stix_bundle(self, threat: Dict[str, Any]) -> Bundle:
        """
        Convert a cyber-pi threat to complete STIX 2.1 bundle
        
        Returns:
            STIX Bundle containing all relevant objects and relationships
        """
        stix_objects = []
        
        # Determine primary STIX type based on threat characteristics
        primary_object = self._create_primary_object(threat)
        stix_objects.append(primary_object)
        
        # Create Identity objects for targeted industries
        industry_identities = self._create_industry_identities(threat)
        stix_objects.extend(industry_identities)
        
        # Create ThreatActor objects
        threat_actors = self._create_threat_actors(threat)
        stix_objects.extend(threat_actors)
        
        # Create Vulnerability objects (CVEs)
        vulnerabilities = self._create_vulnerabilities(threat)
        stix_objects.extend(vulnerabilities)
        
        # Create Indicator objects (IOCs)
        indicators = self._create_indicators(threat)
        stix_objects.extend(indicators)
        
        # Create AttackPattern objects (MITRE techniques)
        attack_patterns = self._create_attack_patterns(threat)
        stix_objects.extend(attack_patterns)
        
        # Create all relationships
        relationships = self._create_relationships(
            primary_object, 
            threat,
            industry_identities,
            threat_actors,
            vulnerabilities,
            indicators,
            attack_patterns
        )
        stix_objects.extend(relationships)
        
        # Create STIX bundle
        bundle = Bundle(objects=stix_objects)
        return bundle
    
    def _create_primary_object(self, threat: Dict) -> Any:
        """Determine and create the primary STIX object"""
        threat_types = threat.get('threatType', [])
        if isinstance(threat_types, str):
            threat_types = [threat_types]
        
        # If it's malware-related, create Malware object
        if any(t in ['malware', 'ransomware', 'trojan', 'backdoor', 'rootkit'] 
               for t in threat_types):
            return Malware(
                name=threat.get('title', 'Unknown Threat'),
                description=threat.get('content', ''),
                malware_types=threat_types or ['unknown'],
                is_family=True,
                created=self._parse_date(threat.get('publishedDate')),
                modified=self._parse_date(threat.get('lastUpdated') or threat.get('publishedDate')),
                confidence=int(threat.get('confidence', 50)),
                labels=threat.get('tags', [])
            )
        
        # If it's a campaign, create Campaign object
        elif 'campaign' in threat_types:
            return Campaign(
                name=threat.get('title', 'Unknown Campaign'),
                description=threat.get('content', ''),
                first_seen=self._parse_date(threat.get('publishedDate')),
                last_seen=self._parse_date(threat.get('lastUpdated')),
                confidence=int(threat.get('confidence', 50)),
                labels=threat.get('tags', [])
            )
        
        # Default: create as Indicator (observable pattern)
        else:
            # Create a simple indicator pattern
            pattern = self._create_indicator_pattern(threat)
            return Indicator(
                name=threat.get('title', 'Unknown Indicator'),
                description=threat.get('content', ''),
                pattern=pattern,
                pattern_type="stix",
                valid_from=self._parse_date(threat.get('publishedDate')),
                confidence=int(threat.get('confidence', 50)),
                indicator_types=threat_types or ['unknown'],
                labels=threat.get('tags', [])
            )
    
    def _create_industry_identities(self, threat: Dict) -> List[Identity]:
        """Create Identity objects for targeted industries"""
        identities = []
        industries = threat.get('industry', [])
        if isinstance(industries, str):
            industries = [industries]
        
        for industry in industries:
            sector = self.INDUSTRY_TO_SECTOR_MAP.get(industry, 'unknown')
            identity = Identity(
                name=industry,
                identity_class="class",
                sectors=[sector],
                description=f"Threat targeting {industry}"
            )
            identities.append(identity)
        
        return identities
    
    def _create_threat_actors(self, threat: Dict) -> List[ThreatActor]:
        """Create ThreatActor objects"""
        actors = []
        actor_names = threat.get('threatActors', [])
        if isinstance(actor_names, str):
            actor_names = [actor_names]
        
        for actor_name in actor_names:
            actor = ThreatActor(
                name=actor_name,
                threat_actor_types=["criminal-org"],  # Default, could be enhanced
                aliases=[],
                sophistication="expert",  # Based on severity
                resource_level="organization",
                primary_motivation="personal-gain"  # Could be derived from context
            )
            actors.append(actor)
        
        return actors
    
    def _create_vulnerabilities(self, threat: Dict) -> List[Vulnerability]:
        """Create Vulnerability objects for CVEs"""
        vulnerabilities = []
        cves = threat.get('cves', [])
        if isinstance(cves, str):
            cves = [cves]
        
        for cve_id in cves:
            vuln = Vulnerability(
                name=cve_id,
                description=f"Vulnerability {cve_id}",
                external_references=[{
                    "source_name": "cve",
                    "external_id": cve_id,
                    "url": f"https://cve.mitre.org/cgi-bin/cvename.cgi?name={cve_id}"
                }]
            )
            vulnerabilities.append(vuln)
        
        return vulnerabilities
    
    def _create_indicators(self, threat: Dict) -> List[Indicator]:
        """Create Indicator objects for IOCs"""
        indicators = []
        iocs = threat.get('iocs', [])
        if isinstance(iocs, str):
            iocs = [iocs]
        
        for ioc in iocs:
            # Determine IOC type and create appropriate pattern
            pattern = self._create_ioc_pattern(ioc)
            indicator = Indicator(
                name=f"IOC: {ioc}",
                pattern=pattern,
                pattern_type="stix",
                valid_from=self._parse_date(threat.get('publishedDate')),
                indicator_types=["malicious-activity"]
            )
            indicators.append(indicator)
        
        return indicators
    
    def _create_attack_patterns(self, threat: Dict) -> List[AttackPattern]:
        """Create AttackPattern objects for MITRE techniques"""
        patterns = []
        
        # MITRE techniques
        techniques = threat.get('mitreTechniques', [])
        if isinstance(techniques, str):
            techniques = [techniques]
        
        for technique_id in techniques:
            pattern = AttackPattern(
                name=technique_id,
                description=f"MITRE ATT&CK technique {technique_id}",
                external_references=[{
                    "source_name": "mitre-attack",
                    "external_id": technique_id,
                    "url": f"https://attack.mitre.org/techniques/{technique_id.replace('.', '/')}/"
                }]
            )
            patterns.append(pattern)
        
        return patterns
    
    def _create_relationships(
        self, 
        primary: Any, 
        threat: Dict,
        industries: List[Identity],
        actors: List[ThreatActor],
        vulns: List[Vulnerability],
        indicators: List[Indicator],
        patterns: List[AttackPattern]
    ) -> List[Relationship]:
        """Create all STIX relationships"""
        relationships = []
        
        # Primary object TARGETS industries
        for identity in industries:
            rel = Relationship(
                relationship_type="targets",
                source_ref=primary.id,
                target_ref=identity.id,
                description=f"{primary.name} targets {identity.name}"
            )
            relationships.append(rel)
        
        # Threat actors USE primary object (if malware)
        for actor in actors:
            if hasattr(primary, 'malware_types'):
                rel = Relationship(
                    relationship_type="uses",
                    source_ref=actor.id,
                    target_ref=primary.id,
                    description=f"{actor.name} uses {primary.name}"
                )
            else:
                rel = Relationship(
                    relationship_type="attributed-to",
                    source_ref=primary.id,
                    target_ref=actor.id,
                    description=f"{primary.name} attributed to {actor.name}"
                )
            relationships.append(rel)
        
        # Primary object EXPLOITS vulnerabilities
        for vuln in vulns:
            rel = Relationship(
                relationship_type="exploits",
                source_ref=primary.id,
                target_ref=vuln.id,
                description=f"{primary.name} exploits {vuln.name}"
            )
            relationships.append(rel)
        
        # Indicators INDICATE primary object
        for indicator in indicators:
            rel = Relationship(
                relationship_type="indicates",
                source_ref=indicator.id,
                target_ref=primary.id,
                description=f"Indicator for {primary.name}"
            )
            relationships.append(rel)
        
        # Primary object USES attack patterns
        for pattern in patterns:
            rel = Relationship(
                relationship_type="uses",
                source_ref=primary.id,
                target_ref=pattern.id,
                description=f"{primary.name} uses {pattern.name}"
            )
            relationships.append(rel)
        
        return relationships
    
    def _create_indicator_pattern(self, threat: Dict) -> str:
        """Create STIX pattern from threat data"""
        # Simple pattern - in production, would be more sophisticated
        title = threat.get('title', 'unknown')
        return f"[file:name = '{title}']"
    
    def _create_ioc_pattern(self, ioc: str) -> str:
        """Create STIX pattern for IOC"""
        # Detect IOC type and create appropriate pattern
        if '.' in ioc and ioc.replace('.', '').replace(':', '').replace('/', '').isalnum():
            # Looks like IP or domain
            if ioc.count('.') == 3 and all(p.isdigit() for p in ioc.split('.')):
                return f"[ipv4-addr:value = '{ioc}']"
            else:
                return f"[domain-name:value = '{ioc}']"
        elif len(ioc) in [32, 40, 64]:
            # Looks like hash (MD5, SHA1, SHA256)
            hash_type = {32: 'MD5', 40: 'SHA-1', 64: 'SHA-256'}.get(len(ioc), 'MD5')
            return f"[file:hashes.'{hash_type}' = '{ioc}']"
        else:
            # Generic pattern
            return f"[file:name = '{ioc}']"
    
    def _parse_date(self, date_str: Optional[str]):
        """Parse date to datetime object for STIX"""
        from datetime import timezone
        
        if not date_str:
            return datetime.now(timezone.utc)
        
        try:
            # Already a datetime
            if isinstance(date_str, datetime):
                return date_str if date_str.tzinfo else date_str.replace(tzinfo=timezone.utc)
            
            # Parse ISO format string
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except:
            return datetime.now(timezone.utc)
    
    def stix_bundle_to_threat(self, bundle: Bundle) -> Dict[str, Any]:
        """
        Convert STIX bundle back to cyber-pi threat format
        
        This allows us to import external STIX feeds
        """
        threat = {
            "threatId": "",
            "title": "",
            "content": "",
            "source": "STIX Feed",
            "industry": [],
            "severity": "medium",
            "threatType": [],
            "threatActors": [],
            "cves": [],
            "iocs": [],
            "mitreTechniques": [],
            "tags": [],
            "stixVersion": "2.1",
            "stixObject": bundle.serialize()
        }
        
        # Extract objects from bundle
        for obj in bundle.objects:
            if obj.type == "malware":
                threat["title"] = obj.name
                threat["content"] = getattr(obj, 'description', '')
                threat["threatType"] = getattr(obj, 'malware_types', [])
                threat["stixId"] = obj.id
                threat["stixType"] = "malware"
                threat["publishedDate"] = str(obj.created)
                threat["tags"] = getattr(obj, 'labels', [])
            
            elif obj.type == "indicator":
                if not threat["title"]:
                    threat["title"] = obj.name
                if not threat["content"]:
                    threat["content"] = getattr(obj, 'description', '')
                threat["iocs"].append(getattr(obj, 'pattern', ''))
                if not threat.get("stixId"):
                    threat["stixId"] = obj.id
                    threat["stixType"] = "indicator"
            
            elif obj.type == "threat-actor":
                threat["threatActors"].append(obj.name)
            
            elif obj.type == "identity":
                sector = getattr(obj, 'sectors', [None])[0]
                industry = self.SECTOR_TO_INDUSTRY_MAP.get(sector, obj.name)
                threat["industry"].append(industry)
            
            elif obj.type == "vulnerability":
                external_refs = getattr(obj, 'external_references', [])
                for ref in external_refs:
                    if ref.get('source_name') == 'cve':
                        threat["cves"].append(ref.get('external_id', obj.name))
            
            elif obj.type == "attack-pattern":
                external_refs = getattr(obj, 'external_references', [])
                for ref in external_refs:
                    if ref.get('source_name') == 'mitre-attack':
                        threat["mitreTechniques"].append(ref.get('external_id', obj.name))
        
        # Generate threat ID if not set
        if not threat["threatId"]:
            import hashlib
            content = threat['title'] + threat['content']
            threat["threatId"] = f"threat_{hashlib.sha256(content.encode()).hexdigest()[:16]}"
        
        return threat
    
    def export_stix_bundle_to_file(self, bundle: Bundle, filename: str):
        """Export STIX bundle to JSON file"""
        with open(filename, 'w') as f:
            f.write(bundle.serialize(pretty=True))
    
    def import_stix_bundle_from_file(self, filename: str) -> Bundle:
        """Import STIX bundle from JSON file"""
        from stix2 import parse
        with open(filename, 'r') as f:
            return parse(f.read())


# Convenience functions
def convert_threat_to_stix(threat: Dict) -> Bundle:
    """Quick conversion: cyber-pi threat → STIX bundle"""
    converter = STIXConverter()
    return converter.threat_to_stix_bundle(threat)


def convert_stix_to_threat(bundle: Bundle) -> Dict:
    """Quick conversion: STIX bundle → cyber-pi threat"""
    converter = STIXConverter()
    return converter.stix_bundle_to_threat(bundle)
