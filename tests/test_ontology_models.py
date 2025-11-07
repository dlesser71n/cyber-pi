#!/usr/bin/env python3
"""
Cyber-PI Ontology Model Tests
Comprehensive test coverage for Pydantic models and validation
"""

import pytest
from datetime import datetime, timezone
from pydantic import ValidationError

from src.models.ontology import (
    CVE, ThreatActor, Malware, Campaign, Vendor, Product,
    EntityType, RelationType, SeverityLevel, ConfidenceLevel,
    Relationship, STIXEntity
)


class TestOntologyModels:
    """Test ontology model validation and behavior"""

    def test_cve_model_creation(self):
        """Test CVE model with valid data"""
        cve_data = {
            "cve_id": "CVE-2024-1234",
            "description": "Critical vulnerability in example software",
            "severity": SeverityLevel.CRITICAL,
            "cvss_score": 9.8,
            "published": datetime.now(timezone.utc),
            "affected_vendors": ["Example Corp"],
            "affected_products": ["Example Product 1.0"],
            "cwes": ["CWE-79"],
            "source": "NVD",
            "confidence": 100
        }

        cve = CVE(**cve_data)
        assert cve.cve_id == "CVE-2024-1234"
        assert cve.severity == SeverityLevel.CRITICAL
        assert cve.cvss_score == 9.8
        assert len(cve.affected_vendors) == 1

    def test_cve_validation(self):
        """Test CVE validation rules"""
        # Invalid CVE ID format
        with pytest.raises(ValidationError):
            CVE(cve_id="INVALID-1234", description="Test")

        # CVSS score out of range
        with pytest.raises(ValidationError):
            CVE(cve_id="CVE-2024-1234", description="Test", cvss_score=15.0)

        # Confidence out of range
        with pytest.raises(ValidationError):
            CVE(cve_id="CVE-2024-1234", description="Test", confidence=150)

    def test_threat_actor_model(self):
        """Test ThreatActor model"""
        actor_data = {
            "name": "APT29",
            "threat_actor_types": ["nation-state"],
            "sophistication": "expert",
            "primary_motivation": "espionage",
            "aliases": ["Cozy Bear", "The Dukes"],
            "source": "MITRE ATT&CK",
            "confidence": 95
        }

        actor = ThreatActor(**actor_data)
        assert actor.name == "APT29"
        assert "nation-state" in actor.threat_actor_types
        assert len(actor.aliases) == 2

    def test_malware_model(self):
        """Test Malware model"""
        malware_data = {
            "name": "WannaCry",
            "malware_types": ["ransomware", "worm"],
            "is_family": False,
            "source": "MITRE ATT&CK",
            "confidence": 100
        }

        malware = Malware(**malware_data)
        assert malware.name == "WannaCry"
        assert len(malware.malware_types) == 2
        assert not malware.is_family

    def test_relationship_model(self):
        """Test Relationship model"""
        relationship_data = {
            "source_id": "threat-actor-123",
            "target_id": "malware-456",
            "relation_type": RelationType.USES,
            "description": "APT29 uses WannaCry",
            "confidence": 90,
            "source": "MITRE ATT&CK"
        }

        rel = Relationship(**relationship_data)
        assert rel.relation_type == RelationType.USES
        assert rel.confidence == 90

    def test_vendor_product_models(self):
        """Test Vendor and Product models"""
        vendor_data = {
            "name": "Microsoft",
            "industry": "Technology",
            "country": "United States",
            "risk_score": 0.3,
            "reputation_score": 0.95,
            "source": "Vendor Intelligence",
            "confidence": 100
        }

        vendor = Vendor(**vendor_data)
        assert vendor.name == "Microsoft"
        assert vendor.risk_score == 0.3

        product_data = {
            "name": "Windows Server 2022",
            "vendor_name": "Microsoft",
            "version": "2022",
            "product_type": "Operating System",
            "end_of_life": False,
            "source": "Vendor Intelligence",
            "confidence": 100
        }

        product = Product(**product_data)
        assert product.name == "Windows Server 2022"
        assert product.vendor_name == "Microsoft"
        assert not product.end_of_life

    def test_enums_validation(self):
        """Test enum value validation"""
        # Valid severity levels
        assert SeverityLevel.CRITICAL.value == "critical"
        assert SeverityLevel.HIGH.value == "high"

        # Valid relation types
        assert RelationType.EXPLOITS.value == "exploits"
        assert RelationType.TARGETS.value == "targets"

        # Valid confidence levels
        assert ConfidenceLevel.CONFIRMED.value == "confirmed"
        assert ConfidenceLevel.HIGH.value == "high"

    def test_entity_type_enum(self):
        """Test entity type enum"""
        assert EntityType.CVE.value == "cve"
        assert EntityType.THREAT_ACTOR.value == "threat-actor"
        assert EntityType.MALWARE.value == "malware"

    def test_stix_entity_base(self):
        """Test STIX entity base class"""
        entity = STIXEntity()
        assert hasattr(entity, 'id')
        assert hasattr(entity, 'created')
        assert hasattr(entity, 'modified')

    def test_campaign_model(self):
        """Test Campaign model"""
        campaign_data = {
            "name": "SolarWinds Supply Chain Attack",
            "description": "Large-scale supply chain compromise",
            "first_seen": datetime(2020, 12, 1, tzinfo=timezone.utc),
            "last_seen": datetime(2021, 1, 15, tzinfo=timezone.utc),
            "objective": "Espionage",
            "source": "MITRE ATT&CK",
            "confidence": 95
        }

        campaign = Campaign(**campaign_data)
        assert campaign.name == "SolarWinds Supply Chain Attack"
        assert campaign.objective == "Espionage"
        assert campaign.first_seen.year == 2020

    def test_model_serialization(self):
        """Test model serialization/deserialization"""
        cve = CVE(
            cve_id="CVE-2024-1234",
            description="Test vulnerability",
            severity=SeverityLevel.HIGH,
            source="NVD",
            confidence=100
        )

        # Test JSON serialization
        json_data = cve.model_dump()
        assert json_data["cve_id"] == "CVE-2024-1234"
        assert json_data["severity"] == "high"

        # Test deserialization
        cve_copy = CVE(**json_data)
        assert cve_copy.cve_id == cve.cve_id
        assert cve_copy.severity == cve.severity

    def test_model_validation_edge_cases(self):
        """Test edge cases in model validation"""
        # Empty strings
        with pytest.raises(ValidationError):
            CVE(cve_id="", description="Test")

        # None values where required
        with pytest.raises(ValidationError):
            ThreatActor(name=None)

        # Invalid date types
        with pytest.raises(ValidationError):
            Campaign(first_seen="not-a-date")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
