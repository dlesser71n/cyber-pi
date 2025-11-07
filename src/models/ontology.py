#!/usr/bin/env python3
"""
Cyber-PI Ontology - Core Entity Models
STIX 2.1 compatible with MITRE ATT&CK integration

Built to Rickover standards: Type-safe, validated, production-ready
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field, field_validator, ConfigDict
from enum import Enum
import uuid


# ============================================================================
# ENUMS & CONSTANTS
# ============================================================================

class EntityType(str, Enum):
    """Core entity types in the ontology"""
    CVE = "cve"
    THREAT_ACTOR = "threat-actor"
    MALWARE = "malware"
    CAMPAIGN = "campaign"
    VENDOR = "vendor"
    PRODUCT = "product"
    ORGANIZATION = "organization"
    IOC = "indicator"
    VULNERABILITY = "vulnerability"
    MITRE_TACTIC = "mitre-tactic"
    MITRE_TECHNIQUE = "mitre-technique"
    INTEL_SOURCE = "intel-source"
    DARK_WEB_POST = "dark-web-post"
    NEWS_ARTICLE = "news-article"
    BREACH = "breach"


class RelationType(str, Enum):
    """Relationship types between entities"""
    # Threat Relationships
    EXPLOITS = "exploits"
    TARGETS = "targets"
    USES = "uses"
    ATTRIBUTED_TO = "attributed-to"
    
    # Product Relationships
    AFFECTS = "affects"
    MANUFACTURED_BY = "manufactured-by"
    DEPENDS_ON = "depends-on"
    
    # Technique Relationships
    IMPLEMENTS = "implements"
    PART_OF = "part-of"
    MITIGATES = "mitigates"
    
    # Evidence Relationships
    MENTIONS = "mentions"
    INDICATES = "indicates"
    OBSERVED_IN = "observed-in"
    
    # Temporal
    PRECEDES = "precedes"
    DERIVES_FROM = "derives-from"
    COMMUNICATES_WITH = "communicates-with"


class SeverityLevel(str, Enum):
    """Severity classification"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


class ConfidenceLevel(str, Enum):
    """Confidence in intelligence"""
    CONFIRMED = "confirmed"  # 90-100%
    HIGH = "high"  # 70-89%
    MEDIUM = "medium"  # 50-69%
    LOW = "low"  # 30-49%
    UNKNOWN = "unknown"  # <30%


# ============================================================================
# BASE CLASSES
# ============================================================================

class STIXEntity(BaseModel):
    """
    Base class for STIX 2.1 compatible entities
    All entities inherit from this
    """
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        populate_by_name=True
    )
    
    # STIX Core Properties
    type: str = Field(..., description="Entity type")
    spec_version: str = Field(default="2.1", description="STIX version")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier")
    created: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    modified: datetime = Field(default_factory=datetime.utcnow, description="Last modified timestamp")
    
    # Optional STIX Properties
    created_by_ref: Optional[str] = Field(None, description="Creator identity reference")
    revoked: bool = Field(default=False, description="Whether entity is revoked")
    labels: List[str] = Field(default_factory=list, description="Classification labels")
    confidence: Optional[int] = Field(None, ge=0, le=100, description="Confidence score 0-100")
    lang: str = Field(default="en", description="Language code")
    external_references: List[Dict[str, Any]] = Field(default_factory=list, description="External references")
    object_marking_refs: List[str] = Field(default_factory=list, description="TLP/marking references")
    
    @field_validator('confidence')
    @classmethod
    def validate_confidence(cls, v: Optional[int]) -> Optional[int]:
        """Ensure confidence is in valid range"""
        if v is not None and not (0 <= v <= 100):
            raise ValueError("Confidence must be between 0 and 100")
        return v


class CyberPIEntity(BaseModel):
    """
    Base class for Cyber-PI specific entities
    Lighter weight than STIX for internal use
    """
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True
    )
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str
    created: datetime = Field(default_factory=datetime.utcnow)
    modified: datetime = Field(default_factory=datetime.utcnow)
    
    # Metadata
    source: str = Field(default="cyber-pi", description="Data source")
    confidence: int = Field(default=50, ge=0, le=100, description="Confidence score")
    tags: List[str] = Field(default_factory=list, description="Tags for classification")


# ============================================================================
# THREAT INTELLIGENCE ENTITIES
# ============================================================================

class ThreatActor(STIXEntity):
    """
    STIX 2.1 Threat Actor
    Represents adversaries, APT groups, cybercriminals
    """
    type: Literal["threat-actor"] = "threat-actor"
    name: str = Field(..., min_length=1, description="Threat actor name")
    description: Optional[str] = Field(None, description="Detailed description")
    
    # Threat Actor Specific
    threat_actor_types: List[str] = Field(
        default_factory=list,
        description="Types: nation-state, cybercrime, hacktivist, insider, competitor"
    )
    aliases: List[str] = Field(default_factory=list, description="Known aliases")
    first_seen: Optional[datetime] = Field(None, description="First observed")
    last_seen: Optional[datetime] = Field(None, description="Last observed")
    roles: List[str] = Field(default_factory=list, description="Roles: director, sponsor, agent")
    goals: List[str] = Field(default_factory=list, description="Known objectives")
    sophistication: Optional[str] = Field(
        None,
        description="Sophistication level: none, minimal, intermediate, advanced, expert, innovator, strategic"
    )
    resource_level: Optional[str] = Field(
        None,
        description="Resource level: individual, club, contest, team, organization, government"
    )
    primary_motivation: Optional[str] = Field(
        None,
        description="Motivation: ideology, financial, revenge, notoriety, etc."
    )


class Malware(STIXEntity):
    """
    STIX 2.1 Malware
    Represents malicious software, ransomware, trojans, etc.
    """
    type: Literal["malware"] = "malware"
    name: str = Field(..., min_length=1, description="Malware name")
    description: Optional[str] = Field(None, description="Detailed description")
    
    # Malware Specific
    malware_types: List[str] = Field(
        default_factory=list,
        description="Types: ransomware, trojan, worm, rootkit, spyware, etc."
    )
    is_family: bool = Field(default=False, description="Whether this is a malware family")
    aliases: List[str] = Field(default_factory=list, description="Known aliases")
    kill_chain_phases: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Kill chain phases"
    )
    first_seen: Optional[datetime] = Field(None, description="First observed")
    last_seen: Optional[datetime] = Field(None, description="Last observed")
    
    # Technical Details
    operating_system_refs: List[str] = Field(default_factory=list, description="Targeted OS")
    architecture_execution_envs: List[str] = Field(default_factory=list, description="Execution environments")
    implementation_languages: List[str] = Field(default_factory=list, description="Programming languages")
    capabilities: List[str] = Field(default_factory=list, description="Malware capabilities")


class Campaign(STIXEntity):
    """
    STIX 2.1 Campaign
    Represents coordinated attack campaigns
    """
    type: Literal["campaign"] = "campaign"
    name: str = Field(..., min_length=1, description="Campaign name")
    description: Optional[str] = Field(None, description="Detailed description")
    
    # Campaign Specific
    aliases: List[str] = Field(default_factory=list, description="Known aliases")
    first_seen: Optional[datetime] = Field(None, description="Campaign start")
    last_seen: Optional[datetime] = Field(None, description="Campaign end")
    objective: Optional[str] = Field(None, description="Campaign objective")


# ============================================================================
# VULNERABILITY ENTITIES
# ============================================================================

class CVE(CyberPIEntity):
    """
    CVE (Common Vulnerabilities and Exposures)
    Simplified from cve_models.py for ontology use
    """
    type: Literal["cve"] = "cve"
    cve_id: str = Field(..., pattern=r"^CVE-\d{4}-\d{4,}$", description="CVE ID")
    description: str = Field(default="No description available")
    
    # CVSS Scores
    cvss_v3_score: Optional[float] = Field(None, ge=0.0, le=10.0)
    cvss_v2_score: Optional[float] = Field(None, ge=0.0, le=10.0)
    severity: SeverityLevel = Field(default=SeverityLevel.NONE)
    
    # Temporal
    published: Optional[datetime] = None
    modified_date: Optional[datetime] = Field(None, alias="modified")
    
    # Affected Systems
    affected_vendors: List[str] = Field(default_factory=list)
    affected_products: List[str] = Field(default_factory=list)
    
    # Weaknesses
    cwes: List[str] = Field(default_factory=list, description="CWE identifiers")
    
    # References
    references: List[str] = Field(default_factory=list, description="External references")
    
    @field_validator('cve_id')
    @classmethod
    def validate_cve_id(cls, v: str) -> str:
        """Ensure CVE ID is uppercase"""
        return v.upper().strip()


class Vulnerability(CyberPIEntity):
    """
    Generic vulnerability (not necessarily a CVE)
    For 0-days, vendor-specific vulns, etc.
    """
    type: Literal["vulnerability"] = "vulnerability"
    name: str = Field(..., min_length=1)
    description: Optional[str] = None
    severity: SeverityLevel = Field(default=SeverityLevel.MEDIUM)
    
    # Context
    discovered_date: Optional[datetime] = None
    disclosed_date: Optional[datetime] = None
    patched_date: Optional[datetime] = None
    
    # Technical
    exploit_available: bool = Field(default=False)
    exploit_complexity: Optional[str] = Field(None, description="low, medium, high")
    
    # Affected
    affected_products: List[str] = Field(default_factory=list)
    affected_versions: List[str] = Field(default_factory=list)


# ============================================================================
# VENDOR & PRODUCT ENTITIES
# ============================================================================

class Vendor(CyberPIEntity):
    """
    Vendor/Organization entity
    Represents software/hardware vendors
    """
    type: Literal["vendor"] = "vendor"
    name: str = Field(..., min_length=1, description="Vendor name")
    aliases: List[str] = Field(default_factory=list, description="Alternative names")
    
    # Classification
    industry: List[str] = Field(default_factory=list, description="Industry sectors")
    size: Optional[str] = Field(None, description="enterprise, mid-market, smb")
    headquarters: Optional[str] = Field(None, description="HQ location")
    website: Optional[str] = Field(None, description="Official website")
    
    # Risk Metrics
    risk_score: float = Field(default=0.5, ge=0.0, le=1.0, description="Overall risk score")
    reputation_score: float = Field(default=0.5, ge=0.0, le=1.0, description="Reputation score")
    
    # Breach History
    known_breaches: List[str] = Field(default_factory=list, description="Breach IDs")
    last_breach_date: Optional[datetime] = Field(None, description="Most recent breach")
    total_breaches: int = Field(default=0, ge=0, description="Total breach count")
    
    # Compliance
    certifications: List[str] = Field(default_factory=list, description="SOC2, ISO27001, etc.")
    compliance_issues: List[str] = Field(default_factory=list, description="Known compliance problems")
    
    # Vulnerability Stats
    total_cves: int = Field(default=0, ge=0)
    critical_cves: int = Field(default=0, ge=0)
    unpatched_cves: int = Field(default=0, ge=0)


class Product(CyberPIEntity):
    """
    Software/Hardware Product
    """
    type: Literal["product"] = "product"
    name: str = Field(..., min_length=1, description="Product name")
    vendor_id: str = Field(..., description="Vendor reference")
    
    # Classification
    product_type: str = Field(default="software", description="software, hardware, service")
    category: List[str] = Field(default_factory=list, description="firewall, vpn, database, etc.")
    
    # Versions
    current_version: Optional[str] = Field(None, description="Latest version")
    supported_versions: List[str] = Field(default_factory=list, description="Supported versions")
    eol_date: Optional[datetime] = Field(None, description="End of life date")
    
    # Vulnerability Metrics
    cve_count: int = Field(default=0, ge=0, description="Total CVEs")
    critical_cve_count: int = Field(default=0, ge=0, description="Critical CVEs")
    unpatched_cve_count: int = Field(default=0, ge=0, description="Unpatched CVEs")
    
    # Dependencies
    dependency_refs: List[str] = Field(default_factory=list, description="Product dependencies")
    
    # CPE (Common Platform Enumeration)
    cpe: Optional[str] = Field(None, description="CPE identifier")


class Breach(CyberPIEntity):
    """
    Data Breach Event
    """
    type: Literal["breach"] = "breach"
    vendor_id: str = Field(..., description="Affected vendor")
    name: str = Field(..., min_length=1, description="Breach name/identifier")
    
    # Timeline
    breach_date: datetime = Field(..., description="When breach occurred")
    discovery_date: Optional[datetime] = Field(None, description="When discovered")
    disclosure_date: Optional[datetime] = Field(None, description="When publicly disclosed")
    
    # Impact
    records_affected: Optional[int] = Field(None, ge=0, description="Number of records")
    data_types: List[str] = Field(
        default_factory=list,
        description="pii, credentials, financial, health, etc."
    )
    severity: SeverityLevel = Field(default=SeverityLevel.MEDIUM)
    
    # Attribution
    threat_actor_refs: List[str] = Field(default_factory=list, description="Attributed actors")
    malware_refs: List[str] = Field(default_factory=list, description="Malware used")
    techniques_used: List[str] = Field(default_factory=list, description="MITRE technique IDs")
    
    # Response
    notification_sent: bool = Field(default=False, description="Breach notification sent")
    regulatory_action: Optional[str] = Field(None, description="Regulatory response")
    estimated_cost: Optional[float] = Field(None, ge=0.0, description="Estimated cost in USD")
    
    # Evidence
    sources: List[str] = Field(default_factory=list, description="Information sources")
    description: Optional[str] = Field(None, description="Breach details")


# ============================================================================
# INDICATOR OF COMPROMISE (IOC)
# ============================================================================

class IOC(CyberPIEntity):
    """
    Indicator of Compromise
    IP addresses, domains, hashes, URLs, etc.
    """
    type: Literal["indicator"] = "indicator"
    ioc_type: str = Field(..., description="ipv4, ipv6, domain, hash, email, url, etc.")
    value: str = Field(..., min_length=1, description="IOC value")
    
    # Classification
    threat_types: List[str] = Field(
        default_factory=list,
        description="malware, phishing, c2, exfiltration, etc."
    )
    malicious: bool = Field(default=False, description="Confirmed malicious")
    
    # Context
    first_seen: datetime = Field(default_factory=datetime.utcnow)
    last_seen: datetime = Field(default_factory=datetime.utcnow)
    observation_count: int = Field(default=1, ge=1, description="Times observed")
    
    # Relationships
    malware_refs: List[str] = Field(default_factory=list)
    campaign_refs: List[str] = Field(default_factory=list)
    threat_actor_refs: List[str] = Field(default_factory=list)
    
    # Enrichment (for IPs/domains)
    geolocation: Optional[Dict[str, Any]] = Field(None, description="Geo data")
    asn: Optional[str] = Field(None, description="Autonomous System Number")
    registrar: Optional[str] = Field(None, description="Domain registrar")
    
    # Metadata
    sources: List[str] = Field(default_factory=list, description="Intelligence sources")
    expires: Optional[datetime] = Field(None, description="IOC expiration")
    
    @field_validator('value')
    @classmethod
    def normalize_value(cls, v: str) -> str:
        """Normalize IOC value"""
        return v.strip().lower()


# ============================================================================
# MITRE ATT&CK ENTITIES
# ============================================================================

class MitreTactic(CyberPIEntity):
    """
    MITRE ATT&CK Tactic
    High-level adversary goals (Initial Access, Execution, etc.)
    """
    type: Literal["mitre-tactic"] = "mitre-tactic"
    tactic_id: str = Field(..., pattern=r"^TA\d{4}$", description="Tactic ID (TA0001)")
    name: str = Field(..., min_length=1, description="Tactic name")
    description: str = Field(..., description="Tactic description")
    url: str = Field(..., description="MITRE ATT&CK URL")
    
    # Metadata
    platforms: List[str] = Field(default_factory=list, description="Applicable platforms")
    version: str = Field(default="1.0", description="ATT&CK version")


class MitreTechnique(CyberPIEntity):
    """
    MITRE ATT&CK Technique
    Specific adversary behaviors (Phishing, PowerShell, etc.)
    """
    type: Literal["mitre-technique"] = "mitre-technique"
    technique_id: str = Field(..., pattern=r"^T\d{4}(\.\d{3})?$", description="Technique ID")
    name: str = Field(..., min_length=1, description="Technique name")
    description: str = Field(..., description="Technique description")
    url: str = Field(..., description="MITRE ATT&CK URL")
    
    # Relationships
    tactic_refs: List[str] = Field(default_factory=list, description="Associated tactic IDs")
    parent_technique: Optional[str] = Field(None, description="Parent technique (for sub-techniques)")
    sub_techniques: List[str] = Field(default_factory=list, description="Sub-technique IDs")
    
    # Detection & Mitigation
    detection: Optional[str] = Field(None, description="Detection guidance")
    mitigations: List[str] = Field(default_factory=list, description="Mitigation IDs")
    
    # Metadata
    platforms: List[str] = Field(default_factory=list, description="Applicable platforms")
    data_sources: List[str] = Field(default_factory=list, description="Detection data sources")
    is_subtechnique: bool = Field(default=False, description="Whether this is a sub-technique")
    version: str = Field(default="1.0", description="ATT&CK version")


# ============================================================================
# RELATIONSHIP MODEL
# ============================================================================

class Relationship(BaseModel):
    """
    Generic relationship between two entities
    Maps to Neo4j edges
    """
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    relationship_type: RelationType = Field(..., description="Type of relationship")
    
    # Source and Target
    source_ref: str = Field(..., description="Source entity ID")
    target_ref: str = Field(..., description="Target entity ID")
    
    # Context
    first_observed: datetime = Field(default_factory=datetime.utcnow)
    last_observed: datetime = Field(default_factory=datetime.utcnow)
    confidence: int = Field(default=50, ge=0, le=100)
    
    # Metadata
    description: Optional[str] = Field(None, description="Relationship description")
    sources: List[str] = Field(default_factory=list, description="Evidence sources")
    tags: List[str] = Field(default_factory=list)
    
    # Timestamps
    created: datetime = Field(default_factory=datetime.utcnow)
    modified: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# EXPORT
# ============================================================================

__all__ = [
    # Enums
    "EntityType",
    "RelationType",
    "SeverityLevel",
    "ConfidenceLevel",
    
    # Base Classes
    "STIXEntity",
    "CyberPIEntity",
    
    # Threat Intelligence
    "ThreatActor",
    "Malware",
    "Campaign",
    
    # Vulnerabilities
    "CVE",
    "Vulnerability",
    
    # Vendors & Products
    "Vendor",
    "Product",
    "Breach",
    
    # IOCs
    "IOC",
    
    # MITRE ATT&CK
    "MitreTactic",
    "MitreTechnique",
    
    # Relationships
    "Relationship",
]
