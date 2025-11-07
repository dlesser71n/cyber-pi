#!/usr/bin/env python3
"""
Cyber-PI Graph Operations Tests
Test Neo4j and Weaviate graph operations
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from neo4j import AsyncDriver

from src.models.ontology import CVE, Vendor, Product
from src.graph.query_library import QueryLibrary


class TestQueryLibrary:
    """Test query library operations"""

    @pytest.fixture
    def mock_driver(self):
        """Mock Neo4j driver"""
        driver = AsyncMock(spec=AsyncDriver)
        session = AsyncMock()
        driver.session.return_value.__aenter__ = AsyncMock(return_value=session)
        driver.session.return_value.__aexit__ = AsyncMock(return_value=None)
        return driver

    @pytest.fixture
    def query_lib(self, mock_driver):
        """Query library instance"""
        return QueryLibrary(mock_driver)

    @pytest.mark.asyncio
    async def test_get_vendor_risk_profile(self, query_lib, mock_driver):
        """Test vendor risk profile query"""
        # Mock the session run result
        mock_result = AsyncMock()
        mock_record = MagicMock()
        mock_record.__getitem__.side_effect = lambda key: {
            "vendor": "Microsoft",
            "risk_score": 0.3,
            "reputation_score": 0.95,
            "total_breaches": 2,
            "last_breach_date": "2023-01-15",
            "product_count": 15,
            "total_cves": 150,
            "critical_cves": 5,
            "high_cves": 25,
            "medium_cves": 45,
            "low_cves": 75
        }[key]

        mock_result.single.return_value = mock_record
        mock_driver.session.return_value.__aenter__.return_value.run.return_value = mock_result

        result = await query_lib.get_vendor_risk_profile("Microsoft")

        assert result["vendor"] == "Microsoft"
        assert result["risk_score"] == 0.3
        assert result["total_cves"] == 150
        assert result["critical_cves"] == 5

    @pytest.mark.asyncio
    async def test_get_vendors_by_risk(self, query_lib, mock_driver):
        """Test vendors by risk query"""
        mock_result = AsyncMock()
        mock_records = []

        # Create mock records
        for vendor_data in [
            {"vendor": "HighRisk Corp", "risk_score": 0.9, "industry": "Finance"},
            {"vendor": "MediumRisk Corp", "risk_score": 0.7, "industry": "Tech"}
        ]:
            mock_record = MagicMock()
            mock_record.__getitem__.side_effect = lambda key: vendor_data[key]
            mock_records.append(mock_record)

        mock_result.__aiter__ = AsyncMock(return_value=iter(mock_records))
        mock_driver.session.return_value.__aenter__.return_value.run.return_value = mock_result

        result = await query_lib.get_vendors_by_risk(min_risk=0.7, limit=5)

        assert len(result) == 2
        assert result[0]["vendor"] == "HighRisk Corp"
        assert result[0]["risk_score"] == 0.9

    @pytest.mark.asyncio
    async def test_vendor_not_found(self, query_lib, mock_driver):
        """Test vendor not found scenario"""
        mock_result = AsyncMock()
        mock_result.single.return_value = None
        mock_driver.session.return_value.__aenter__.return_value.run.return_value = mock_result

        result = await query_lib.get_vendor_risk_profile("NonExistentVendor")

        assert "error" in result
        assert "NonExistentVendor" in result["error"]

    @pytest.mark.asyncio
    async def test_get_threat_actor_profile(self, query_lib, mock_driver):
        """Test threat actor profile query"""
        mock_result = AsyncMock()
        mock_record = MagicMock()
        mock_record.__getitem__.side_effect = lambda key: {
            "threat_actor": "APT29",
            "actor_types": ["nation-state"],
            "sophistication": "expert",
            "motivation": "espionage",
            "aliases": ["Cozy Bear"],
            "malware_arsenal": ["WannaCry"],
            "techniques": ["T1566"],
            "tactics": ["Initial Access"],
            "campaigns": ["SolarWinds"],
            "targets": ["Microsoft"]
        }[key]

        mock_result.single.return_value = mock_record
        mock_driver.session.return_value.__aenter__.return_value.run.return_value = mock_result

        result = await query_lib.get_threat_actor_profile("APT29")

        assert result["threat_actor"] == "APT29"
        assert "nation-state" in result["actor_types"]
        assert result["sophistication"] == "expert"
        assert "WannaCry" in result["malware_arsenal"]


class TestOntologyIntegration:
    """Test ontology models integration"""

    def test_cve_vendor_relationship(self):
        """Test CVE can reference vendors and products"""
        cve = CVE(
            cve_id="CVE-2024-1234",
            description="Test vulnerability",
            severity="high",
            affected_vendors=["Microsoft", "Apple"],
            affected_products=["Windows 10", "macOS"],
            source="NVD",
            confidence=100
        )

        assert len(cve.affected_vendors) == 2
        assert len(cve.affected_products) == 2
        assert "Microsoft" in cve.affected_vendors
        assert "Windows 10" in cve.affected_products

    def test_full_threat_chain(self):
        """Test complete threat intelligence chain"""
        # Create entities
        actor = ThreatActor(
            name="APT29",
            threat_actor_types=["nation-state"],
            sophistication="expert",
            primary_motivation="espionage",
            source="MITRE ATT&CK",
            confidence=95
        )

        malware = Malware(
            name="WannaCry",
            malware_types=["ransomware", "worm"],
            source="MITRE ATT&CK",
            confidence=100
        )

        cve = CVE(
            cve_id="CVE-2017-0144",
            description="EternalBlue vulnerability",
            severity="critical",
            cvss_score=10.0,
            source="NVD",
            confidence=100
        )

        # Verify relationships can be established
        assert actor.name == "APT29"
        assert malware.name == "WannaCry"
        assert cve.cve_id == "CVE-2017-0144"
        assert cve.severity.value == "critical"

    def test_model_uuid_generation(self):
        """Test UUID generation for model instances"""
        cve1 = CVE(cve_id="CVE-2024-1234", description="Test", source="NVD", confidence=100)
        cve2 = CVE(cve_id="CVE-2024-5678", description="Test", source="NVD", confidence=100)

        # UUIDs should be unique
        assert cve1.id != cve2.id
        assert len(str(cve1.id)) > 0
        assert len(str(cve2.id)) > 0

    def test_model_timestamps(self):
        """Test automatic timestamp generation"""
        before = datetime.now()
        cve = CVE(cve_id="CVE-2024-1234", description="Test", source="NVD", confidence=100)
        after = datetime.now()

        # Timestamps should be set automatically
        assert before <= cve.created <= after
        assert before <= cve.modified <= after

    def test_model_tags_system(self):
        """Test tags system for categorization"""
        cve = CVE(
            cve_id="CVE-2024-1234",
            description="Test",
            source="NVD",
            confidence=100,
            tags=["ransomware", "critical", "eternalblue"]
        )

        assert len(cve.tags) == 3
        assert "ransomware" in cve.tags
        assert "critical" in cve.tags


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
